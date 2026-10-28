// Offline native Map0 queries. No World, SQL connection or runtime writes.
// Detour XYZ = world YZX; VMap internal conversion is its own inverse.
#include "DBCStores.h"
#include "DBCfmt.h"
#include "GridTerrainData.h"
#include "MapDefines.h"
#include "MapTree.h"
#include "ModelInstance.h"
#include "VMapMgr2.h"
#include "WorldModel.h"
#include "DetourNavMeshQuery.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <tuple>
#include <vector>

// Dependencies of the existing GridTerrainData object: real native DBC stores,
// including the liquid override semantics in GetLiquidData.
DBCStorage<AreaTableEntry> sAreaTableStore(AreaTableEntryfmt);
DBCStorage<LiquidTypeEntry> sLiquidTypeStore(LiquidTypefmt);

namespace fs = std::filesystem;
constexpr float GridSize = 1600.0f / 3.0f;

static void Require(bool ok, std::string const& message)
{
    if (!ok)
        throw std::runtime_error(message);
}

static std::vector<unsigned char> Read(fs::path const& path)
{
    std::ifstream input(path, std::ios::binary);
    Require(bool(input), "Cannot read " + path.string());
    return {std::istreambuf_iterator<char>(input), {}};
}

static std::vector<fs::path> List(fs::path const& path)
{
    std::ifstream input(path);
    Require(bool(input), "Cannot read list " + path.string());
    std::vector<fs::path> result;
    for (std::string line; std::getline(input, line);)
        if (!line.empty())
            result.emplace_back(line);
    return result;
}

static G3D::Vector3 Internal(float x, float y, float z)
{
    return VMAP::VMapMgr2::convertPositionToInternalRep(x, y, z);
}

struct Cell
{
    int tx, ty, cx, cy, sourceArea, area;
    float x, y;
};

struct Sample
{
    float x, y, z, terrain, collision, ground;
    dtPolyRef ref;
    unsigned flags, liquidStatus, instance, groupFlags;
    int area, root, nameSet, group;
};

static float Planar(Sample const& a, Sample const& b)
{
    return std::hypot(a.x - b.x, a.y - b.y);
}

static std::string Status(dtStatus status)
{
    if (!status)
        return "NOT_CALLED";
    std::string text = dtStatusFailed(status) ? "FAILURE" : dtStatusSucceed(status) ? "SUCCESS" : "IN_PROGRESS";
    for (auto const& [flag, name] : std::array<std::pair<dtStatus, char const*>, 8>{{
        {DT_WRONG_MAGIC, "WRONG_MAGIC"}, {DT_WRONG_VERSION, "WRONG_VERSION"},
        {DT_OUT_OF_MEMORY, "OUT_OF_MEMORY"}, {DT_INVALID_PARAM, "INVALID_PARAM"},
        {DT_BUFFER_TOO_SMALL, "BUFFER_TOO_SMALL"}, {DT_OUT_OF_NODES, "OUT_OF_NODES"},
        {DT_PARTIAL_RESULT, "PARTIAL_RESULT"}, {DT_ALREADY_OCCUPIED, "ALREADY_OCCUPIED"}}})
        if (status & flag)
            text += std::string("|") + name;
    return text;
}

int main(int argc, char** argv)
{
    try
    {
        Require(argc == 3, "usage: high_elf_nav_probe RUNTIME OUTPUT_WITH_INPUT_LISTS");
        fs::path runtime(argv[1]), out(argv[2]);
        Require(sAreaTableStore.Load((runtime / "dbc/AreaTable.dbc").c_str()), "AreaTable native load failed");
        Require(sLiquidTypeStore.Load((runtime / "dbc/LiquidType.dbc").c_str()), "LiquidType native load failed");
        DBCStorage<WMOAreaTableEntry> wmoStore(WMOAreaTableEntryfmt);
        Require(wmoStore.Load((runtime / "dbc/WMOAreaTable.dbc").c_str()), "WMOAreaTable native load failed");

        std::map<std::pair<int, int>, std::unique_ptr<GridTerrainData>> maps;
        std::ofstream loads(out / "loads.tsv");
        loads << "kind\tfile\tstatus\n";
        for (auto const& path : List(out / "maps.txt"))
        {
            auto name = path.filename().string();
            int gy = std::stoi(name.substr(3, 2)), gx = std::stoi(name.substr(5, 2));
            auto data = std::make_unique<GridTerrainData>();
            auto status = data->Load(path.string());
            loads << "map\t" << name << '\t' << int(status) << '\n';
            Require(status == TerrainMapDataReadResult::Success, "Native Map load failed " + name);
            maps[{gx, gy}] = std::move(data);
        }

        VMAP::StaticMapTree tree(0, (runtime / "vmaps").string() + "/");
        Require(tree.InitMap("000.vmtree"), "Native VMap tree init failed");
        auto vmapFiles = List(out / "vmaps.txt");
        Require(vmapFiles.size() == 374, "Expected complete 374-tile VMap set");
        // All continent BIH slots must have real models, including placements
        // outside the custom region which share this assembly tree.
        for (auto const& path : vmapFiles)
        {
            auto name = path.filename().string();
            int x = std::stoi(name.substr(4, 2)), y = std::stoi(name.substr(7, 2));
            Require(VMAP::StaticMapTree::CanLoadMap((runtime / "vmaps").string(), 0, y, x) ==
                VMAP::LoadResult::Success && tree.LoadMapTile(y, x), "VMap load failed " + name);
            loads << "vmap\t" << name << "\tloaded\n";
        }
        VMAP::ModelInstance* models = nullptr;
        uint32 modelCount = 0;
        tree.GetModelInstances(models, modelCount);
        std::map<std::string, unsigned> modelFiles;
        for (uint32 i = 0; i < modelCount; ++i)
        {
            Require(models[i].getWorldModel() != nullptr, "Unpopulated VMap BIH slot " + std::to_string(i));
            // WorldModel::readFile ultimately uses fopen: embedded trailing NUL
            // names resolve to a .m2 file, not to the appended .vmo suffix.
            ++modelFiles[std::string((models[i].name + ".vmo").c_str())];
        }
        std::ofstream modelReport(out / "models.tsv");
        modelReport << "file\tinstances\n";
        for (auto const& [name, count] : modelFiles)
            modelReport << name << '\t' << count << '\n';

        auto paramsBytes = Read(runtime / "mmaps/000.mmap");
        Require(paramsBytes.size() == sizeof(dtNavMeshParams), "Native mmap params size mismatch");
        dtNavMeshParams params;
        std::memcpy(&params, paramsBytes.data(), sizeof(params));
        std::unique_ptr<dtNavMesh, decltype(&dtFreeNavMesh)> mesh(dtAllocNavMesh(), dtFreeNavMesh);
        Require(mesh && dtStatusSucceed(mesh->init(&params)), "Detour mesh init failed");
        auto mmapFiles = List(out / "mmaps.txt");
        Require(mmapFiles.size() == 522, "Expected all 522 installed Map0 MMaps");
        for (auto const& path : mmapFiles)
        {
            auto bytes = Read(path);
            Require(bytes.size() >= sizeof(MmapTileHeader), "Truncated MMap header " + path.string());
            MmapTileHeader header;
            std::memcpy(&header, bytes.data(), sizeof(header));
            Require(header.mmapMagic == MMAP_MAGIC && header.mmapVersion == MMAP_VERSION &&
                header.dtVersion == DT_NAVMESH_VERSION && header.size >= sizeof(dtMeshHeader) &&
                bytes.size() == sizeof(header) + header.size, "MMap version/size mismatch " + path.string());
            auto* payload = static_cast<unsigned char*>(dtAlloc(header.size, DT_ALLOC_PERM));
            Require(payload != nullptr, "Detour allocation failed");
            std::memcpy(payload, bytes.data() + sizeof(header), header.size);
            auto status = mesh->addTile(payload, header.size, DT_TILE_FREE_DATA, 0, nullptr);
            if (dtStatusFailed(status))
                dtFree(payload);
            loads << "mmap\t" << path.filename().string() << '\t' << Status(status) << '\n';
            Require(dtStatusSucceed(status), "Detour rejected " + path.string());
        }
        std::unique_ptr<dtNavMeshQuery, decltype(&dtFreeNavMeshQuery)> query(dtAllocNavMeshQuery(), dtFreeNavMeshQuery);
        Require(query && dtStatusSucceed(query->init(mesh.get(), 65535)), "Detour query init failed");

        std::map<std::pair<int, int>, Cell> cells;
        std::ifstream cellInput(out / "cells.txt");
        Cell cell;
        while (cellInput >> cell.tx >> cell.ty >> cell.cx >> cell.cy >> cell.sourceArea >> cell.area
            >> cell.x >> cell.y)
            cells[{cell.tx * 16 + cell.cx, cell.ty * 16 + cell.cy}] = cell;
        Require(!cells.empty(), "Missing source MCNK anchors");
        std::ofstream anchors(out / "anchors.tsv");
        anchors << std::setprecision(9) << "area\tx\ty\tnative_map_height\tmap_area\n";
        for (auto const& [key, c] : cells)
        {
            auto const& grid = maps.at({c.tx, c.ty});
            auto const* area = sAreaTableStore.LookupEntry(c.area);
            Require(area && area->ID == grid->getArea(c.x, c.y),
                "Source MCNK/native Map area mismatch " + std::to_string(c.area));
            anchors << c.area << '\t' << c.x << '\t' << c.y << '\t' << grid->getHeight(c.x, c.y)
                    << '\t' << grid->getArea(c.x, c.y) << '\n';
        }

        std::vector<Sample> samples;
        std::set<std::tuple<int, int, int, int, int, int, int>> bins;
        std::ofstream sampleFile(out / "samples.tsv");
        sampleFile << std::setprecision(9)
            << "index\tarea\tx\ty\tnav_z\tpoly\tflags\tmap_height\tvmap_height\tground\troot\tname_set\tgroup"
            << "\tliquid_status\tinstance\tmogp_flags\n";
        for (int t = 0; t < mesh->getMaxTiles(); ++t)
        {
            auto const* tile = static_cast<dtNavMesh const*>(mesh.get())->getTile(t);
            if (!tile || !tile->header)
                continue;
            for (int i = 0; i < tile->header->polyCount; ++i)
            {
                auto const& poly = tile->polys[i];
                if (poly.getType() == DT_POLYTYPE_OFFMESH_CONNECTION ||
                    !(poly.flags & (NAV_GROUND | NAV_WATER)) ||
                    (poly.flags & (NAV_MAGMA | NAV_SLIME | NAV_GROUND_STEEP)))
                    continue;
                float center[3]{};
                for (int v = 0; v < poly.vertCount; ++v)
                    for (int k = 0; k < 3; ++k)
                        center[k] += tile->verts[poly.verts[v] * 3 + k] / poly.vertCount;
                float x = center[2], y = center[0];
                auto found = cells.find({int(std::floor((32 - y / GridSize) * 16)),
                                         int(std::floor((32 - x / GridSize) * 16))});
                if (found == cells.end())
                    continue;
                dtPolyRef ref = mesh->getPolyRefBase(tile) | static_cast<dtPolyRef>(i);
                if (dtStatusFailed(query->getPolyHeight(ref, center, &center[1])))
                    continue;
                auto const& c = found->second;
                auto const& grid = maps.at({c.tx, c.ty});
                float z = center[1], terrain = grid->getHeight(x, y);
                float collision = tree.getHeight(Internal(x, y, z + 1), 4);
                float ground = terrain;
                if (std::isfinite(collision) && collision > ground && collision <= z + 1)
                    ground = collision;
                VMAP::LocationInfo info;
                bool located = tree.GetLocationInfo(Internal(x, y, z + 1), info);
                int root = located ? info.rootId : -1;
                int nameSet = located && info.hitInstance ? info.hitInstance->adtId : -1;
                int group = located && info.hitModel ? int(info.hitModel->GetWmoID()) : -1;
                unsigned instance = located && info.hitInstance ? info.hitInstance->ID : 0;
                unsigned groupFlags = located && info.hitModel ? info.hitModel->GetMogpFlags() : 0;
                // Spatial thinning only; no selection based on path success.
                // Retain every inn polygon, including separate stacked floors.
                if (root != 6002 && !bins.emplace(c.area, root, group, int(poly.flags),
                    int(std::floor(x / 20)), int(std::floor(y / 20)), int(std::floor(z / 5))).second)
                    continue;
                auto liquid = grid->GetLiquidData(x, y, z, 2.0f, {});
                Sample s{x, y, z, terrain, collision, ground, ref, poly.flags, liquid.Status,
                         instance, groupFlags, c.area, root, nameSet, group};
                sampleFile << samples.size() << '\t' << c.area << '\t' << x << '\t' << y << '\t' << z << '\t'
                    << ref << '\t' << poly.flags << '\t' << terrain << '\t' << collision << '\t' << ground << '\t'
                    << root << '\t' << nameSet << '\t' << group << '\t' << liquid.Status << '\t'
                    << instance << '\t' << groupFlags << '\n';
                samples.push_back(s);
            }
        }
        Require(!samples.empty(), "No regional navmesh samples");

        std::ofstream paths(out / "paths.tsv");
        paths << std::setprecision(9)
            << "label\tmode\tstart_index\tend_index\tdistance\tnearest_start_status\tnearest_end_status"
            << "\tstart_ref\tend_ref\tstart_snap\tend_snap\tpath_status\tpath_status_text\tpolys\tcomplete"
            << "\tstraight_status\tstraight_points\tlos"
            << "\tlast_ref\treason\n";
        unsigned completeCount = 0, partialCount = 0, queryCount = 0;
        auto runPath = [&](std::string const& label, std::string const& mode, std::size_t ai, std::size_t bi)
        {
            auto const& a = samples[ai];
            auto const& b = samples[bi];
            float start[3]{a.y, a.z, a.x}, end[3]{b.y, b.z, b.x};
            float nearA[3]{}, nearB[3]{}, extents[3]{1.5f, 2.0f, 1.5f};
            dtQueryFilter filter;
            filter.setIncludeFlags(mode == "water_only" ? NAV_WATER : mode == "walk_swim" ?
                NAV_GROUND | NAV_WATER : NAV_GROUND);
            filter.setExcludeFlags(NAV_MAGMA | NAV_SLIME | NAV_GROUND_STEEP);
            dtPolyRef ar = 0, br = 0;
            auto na = query->findNearestPoly(start, extents, &filter, &ar, nearA);
            auto nb = query->findNearestPoly(end, extents, &filter, &br, nearB);
            std::array<dtPolyRef, 16384> corridor{};
            int count = 0;
            dtStatus status = 0;
            if (dtStatusSucceed(na) && dtStatusSucceed(nb) && ar && br)
                status = query->findPath(ar, br, nearA, nearB, &filter, corridor.data(), &count, corridor.size());
            bool complete = dtStatusSucceed(status) && count && corridor[count - 1] == br &&
                !(status & (DT_PARTIAL_RESULT | DT_OUT_OF_NODES | DT_BUFFER_TOO_SMALL));
            std::array<float, 16384 * 3> straight{};
            int straightCount = 0;
            dtStatus straightStatus = 0;
            if (count)
            {
                float target[3]{};
                // Partial corridors end on the actual final reachable polygon.
                auto projection = query->closestPointOnPoly(corridor[count - 1], nearB, target, nullptr);
                if (dtStatusSucceed(projection))
                    straightStatus = query->findStraightPath(nearA, target, corridor.data(), count,
                        straight.data(), nullptr, nullptr, &straightCount, straight.size() / 3);
            }
            auto snap = [](float const* p, float const* q)
            {
                return std::sqrt((p[0] - q[0]) * (p[0] - q[0]) + (p[1] - q[1]) * (p[1] - q[1]) +
                    (p[2] - q[2]) * (p[2] - q[2]));
            };
            bool los = tree.isInLineOfSight(Internal(a.x, a.y, a.z + 1.5f),
                Internal(b.x, b.y, b.z + 1.5f), VMAP::ModelIgnoreFlags::Nothing);
            paths << label << '\t' << mode << '\t' << ai << '\t' << bi << '\t' << Planar(a, b) << '\t'
                << na << '\t' << nb << '\t' << ar << '\t' << br << '\t' << (ar ? snap(start, nearA) : -1) << '\t'
                << (br ? snap(end, nearB) : -1) << '\t' << status << '\t' << Status(status) << '\t' << count << '\t'
                << complete << '\t' << straightStatus << '\t' << straightCount << '\t' << los << '\t'
                << (count ? corridor[count - 1] : 0) << '\t'
                << (!ar || !br ? "missing_endpoint_poly" : complete ? "reached_end_poly" : "incomplete_corridor")
                << '\n';
            ++queryCount;
            complete ? ++completeCount : ++partialCount;
        };

        // Fixed geometric selection: nearest sample to the source MCNK area's
        // centroid, then nearest sample to offsets of 60/150/300 units on X.
        // Connectivity is measured AFTER selection, never an acceptance gate.
        std::map<int, std::pair<double, double>> sums;
        std::map<int, unsigned> counts;
        for (auto const& [key, c] : cells)
        {
            sums[c.area].first += c.x;
            sums[c.area].second += c.y;
            ++counts[c.area];
        }
        std::map<int, std::size_t> starts;
        auto choose = [&](int area, unsigned required, int root, float x, float y, std::size_t exclude)
        {
            std::size_t best = samples.size();
            float distance = std::numeric_limits<float>::infinity();
            for (std::size_t i = 0; i < samples.size(); ++i)
            {
                auto const& s = samples[i];
                if (i == exclude || s.area != area || !(s.flags & required) || (root != -2 && s.root != root))
                    continue;
                float d = std::hypot(s.x - x, s.y - y);
                if (d < distance)
                {
                    best = i;
                    distance = d;
                }
            }
            return best;
        };
        for (auto const& [area, sum] : sums)
        {
            for (auto const& mode : {std::string("walk"), std::string("water_only")})
            {
                unsigned required = mode == "walk" ? NAV_GROUND : NAV_WATER;
                auto a = choose(area, required, -2, sum.first / counts[area], sum.second / counts[area],
                    samples.size());
                if (a == samples.size())
                {
                    std::cout << "NO_SAMPLE area=" << area << " mode=" << mode << '\n';
                    continue;
                }
                if (mode == "walk")
                    starts[area] = a;
                for (int distance : {60, 150, 300})
                {
                    auto b = choose(area, required, -2, samples[a].x + distance, samples[a].y, a);
                    if (b != samples.size())
                    {
                        auto label = std::to_string(area) + "_offset" + std::to_string(distance);
                        runPath(label, mode, a, b);
                        if (mode == "water_only")
                        {
                            runPath(label + "_combined", "walk_swim", a, b);
                            runPath(label + "_walk_control", "walk", a, b);
                        }
                    }
                }
            }
        }
        for (auto const& [a, b] : std::array<std::pair<int, int>, 3>{{{2040, 5533}, {5533, 5225}, {2040, 5225}}})
            if (starts.contains(a) && starts.contains(b))
                for (auto const& mode : {std::string("walk"), std::string("walk_swim")})
                    runPath(std::to_string(a) + "_to_" + std::to_string(b), mode, starts[a], starts[b]);

        // Exact native WMO key, not root wildcard/group -1. Sample physical inn
        // collision as well as checking its installed DBC metadata.
        auto const* innRow = wmoStore.LookupEntry(60017);
        Require(innRow && innRow->rootId == 6002 && innRow->adtId == 0 && innRow->groupId == 0,
            "Installed inn row 60017 is not exact root6002/nameSet0/group0");
        std::vector<std::size_t> inn;
        for (std::size_t i = 0; i < samples.size(); ++i)
            if (samples[i].root == 6002 && samples[i].nameSet == 0 && samples[i].group == 0 &&
                (samples[i].flags & NAV_GROUND) && std::abs(samples[i].collision - samples[i].z) < 1)
                inn.push_back(i);
        if (inn.size() >= 2)
        {
            auto a = inn.front(), b = inn.back();
            runPath("inn_exact_6002_0_0", "walk", a, b);
            if (starts.contains(samples[a].area))
                runPath("inn_to_area_centroid", "walk", a, starts.at(samples[a].area));
        }
        // Additional local inn queries on the same placement and near the same
        // floor. Targets are selected geometrically, regardless of connectivity.
        for (unsigned ordinal = 0; ordinal < 3 && ordinal < inn.size(); ++ordinal)
        {
            auto a = inn[ordinal * (inn.size() - 1) / 3];
            for (int offset : {5, 15, 30})
            {
                std::size_t best = samples.size();
                float distance = std::numeric_limits<float>::infinity();
                for (auto b : inn)
                {
                    if (a == b || samples[a].instance != samples[b].instance ||
                        std::abs(samples[a].z - samples[b].z) > 2)
                        continue;
                    float d = std::hypot(samples[b].x - samples[a].x - offset, samples[b].y - samples[a].y);
                    if (d < distance)
                    {
                        best = b;
                        distance = d;
                    }
                }
                if (best != samples.size())
                    runPath("inn_local_" + std::to_string(ordinal) + "_offset" + std::to_string(offset),
                        "walk", a, best);
            }
        }
        std::cout << "INN exact_row=60017 root=6002 nameSet=0 group=0 area=" << innRow->areaId
                  << " walk_collision_samples=" << inn.size() << '\n';

        // A group match by itself also includes roofs. Identify low inn floors
        // with real overhead collision, and expose the ceiling hit explicitly.
        std::ofstream interiors(out / "interiors.tsv");
        interiors << std::setprecision(9) << "sample\tinstance\troot\tname_set\tgroup\tnav_z\tfloor\tceiling_z\n";
        std::vector<std::size_t> covered;
        for (auto i : inn)
        {
            auto const& s = samples[i];
            VMAP::LocationInfo info;
            if (!tree.GetLocationInfo(Internal(s.x, s.y, s.z + 1), info) || !info.hitInstance)
                continue;
            G3D::Vector3 hit;
            float top = info.hitInstance->GetBounds().high().z + 5;
            if (!tree.GetObjectHitPos(Internal(s.x, s.y, s.z + 2), Internal(s.x, s.y, top), hit, 0))
                continue;
            interiors << i << '\t' << s.instance << "\t6002\t0\t0\t" << s.z << '\t' << s.collision
                << '\t' << hit.z << '\n';
            covered.push_back(i);
        }
        if (!covered.empty())
        {
            auto low = *std::min_element(covered.begin(), covered.end(), [&](auto a, auto b)
            {
                return samples[a].z < samples[b].z;
            });
            for (int offset : {5, 15, 30})
            {
                std::size_t best = samples.size();
                float distance = std::numeric_limits<float>::infinity();
                for (auto b : covered)
                {
                    if (low == b || samples[low].instance != samples[b].instance ||
                        std::abs(samples[low].z - samples[b].z) > 2)
                        continue;
                    float d = std::hypot(samples[b].x - samples[low].x - offset, samples[b].y - samples[low].y);
                    if (d < distance)
                    {
                        best = b;
                        distance = d;
                    }
                }
                if (best != samples.size())
                    runPath("inn_covered_low_floor_offset" + std::to_string(offset), "walk", low, best);
                else
                {
                    float start[3]{samples[low].y, samples[low].z, samples[low].x};
                    float projected[3]{}, extent[3]{1.5f, 2, 1.5f};
                    dtQueryFilter filter;
                    filter.setIncludeFlags(NAV_GROUND);
                    filter.setExcludeFlags(NAV_MAGMA | NAV_SLIME | NAV_GROUND_STEEP);
                    dtPolyRef ref = 0;
                    auto status = query->findNearestPoly(start, extent, &filter, &ref, projected);
                    float snap = std::sqrt((projected[0] - start[0]) * (projected[0] - start[0]) +
                        (projected[1] - start[1]) * (projected[1] - start[1]) +
                        (projected[2] - start[2]) * (projected[2] - start[2]));
                    paths << "inn_covered_low_floor_offset" << offset << "\twalk\t" << low << "\t-1\t" << offset
                        << '\t' << status << "\t0\t" << ref << "\t0\t" << (ref ? snap : -1)
                        << "\t-1\t0\tNOT_CALLED\t0\t0\t0\t0\t-1\t0\tno_same_floor_destination\n";
                    ++queryCount;
                    ++partialCount;
                }
            }
            // A separate, explicitly higher covered floor: do not misrepresent
            // these queries as evidence for the isolated lowest-floor sample.
            auto upper = std::find_if(covered.begin(), covered.end(), [&](auto a)
            {
                return samples[a].z > samples[low].z + 2;
            });
            if (upper != covered.end())
                for (int offset : {5, 15, 30})
                {
                    auto a = *upper;
                    std::size_t best = samples.size();
                    float distance = std::numeric_limits<float>::infinity();
                    for (auto b : covered)
                    {
                        if (a == b || samples[a].instance != samples[b].instance ||
                            std::abs(samples[a].z - samples[b].z) > 2)
                            continue;
                        float d = std::hypot(samples[b].x - samples[a].x - offset, samples[b].y - samples[a].y);
                        if (d < distance)
                        {
                            best = b;
                            distance = d;
                        }
                    }
                    if (best != samples.size())
                        runPath("inn_covered_upper_floor_offset" + std::to_string(offset), "walk", a, best);
                }
        }
        std::cout << "INN overhead_collision_floor_samples=" << covered.size() << '\n';

        std::ofstream rays(out / "rays.tsv");
        rays << std::setprecision(9)
            << "sample\troot\tgroup\tx\ty\tstart_z\tend_z\theight\thit\thit_x\thit_y\thit_z\tlos\n";
        unsigned rayHits = 0, rayCount = 0;
        std::map<int, unsigned> raysByRoot;
        // Vertical rays cross real WMO floor/roof geometry; upper points come
        // from placed bounding boxes rather than an arbitrary synthetic target.
        for (std::size_t i = 0; i < samples.size(); ++i)
        {
            auto const& s = samples[i];
            if (s.root < 6000 || s.root > 6002 || raysByRoot[s.root] >= 30)
                continue;
            VMAP::LocationInfo info;
            if (!tree.GetLocationInfo(Internal(s.x, s.y, s.z + 1), info) || !info.hitInstance)
                continue;
            float top = info.hitInstance->GetBounds().high().z + 5;
            auto start = Internal(s.x, s.y, top), end = Internal(s.x, s.y, s.z - 3);
            G3D::Vector3 hit;
            bool didHit = tree.GetObjectHitPos(start, end, hit, 0);
            auto worldHit = Internal(hit.x, hit.y, hit.z);
            float height = tree.getHeight(start, top - s.z + 4);
            bool los = tree.isInLineOfSight(start, end, VMAP::ModelIgnoreFlags::Nothing);
            rays << i << '\t' << s.root << '\t' << s.group << '\t' << s.x << '\t' << s.y << '\t' << top << '\t'
                << s.z - 3 << '\t' << height << '\t' << didHit << '\t' << worldHit.x << '\t' << worldHit.y << '\t'
                << worldHit.z << '\t' << los << '\n';
            ++rayCount;
            ++raysByRoot[s.root];
            rayHits += didHit;
        }

        std::ofstream teleports(out / "teleports.tsv");
        teleports << std::setprecision(9)
            << "area\tsample\tx\ty\tground\ttele_z\tnav_z\tpoly\tflags\theadroom_los"
            << "\tnearest_status\tnearest_ref\tfootprint_checks\n";
        auto terrainAt = [&](float x, float y)
        {
            auto found = maps.find({int(std::floor(32 - y / GridSize)), int(std::floor(32 - x / GridSize))});
            return found == maps.end() ? INVALID_HEIGHT : found->second->getHeight(x, y);
        };
        for (int area : {5533, 2040})
        {
            std::size_t best = samples.size();
            float bestDistance = std::numeric_limits<float>::infinity();
            for (std::size_t i = 0; i < samples.size(); ++i)
            {
                auto const& s = samples[i];
                if (s.area != area || !(s.flags & NAV_GROUND) || (s.flags & NAV_WATER) ||
                    !std::isfinite(s.ground) || s.ground < -500 || std::abs(s.ground - s.z) > 0.6f ||
                    (s.liquidStatus != LIQUID_MAP_NO_WATER && s.liquidStatus != LIQUID_MAP_ABOVE_WATER))
                    continue;
                // Require terrain/surface agreement to reject roofs/underground
                // floors, plus a clear body-height vertical segment.
                if (std::abs(s.terrain - s.ground) > 0.6f ||
                    !tree.isInLineOfSight(Internal(s.x, s.y, s.ground + 0.3f),
                        Internal(s.x, s.y, s.ground + 4), VMAP::ModelIgnoreFlags::Nothing))
                    continue;
                bool footprint = true;
                for (float dx : {-0.75f, 0.0f, 0.75f})
                    for (float dy : {-0.75f, 0.0f, 0.75f})
                    {
                        float h = terrainAt(s.x + dx, s.y + dy);
                        float v = tree.getHeight(Internal(s.x + dx, s.y + dy, s.ground + 1), 4);
                        if (std::isfinite(v) && v > h)
                            h = v;
                        if (!std::isfinite(h) || std::abs(h - s.ground) > 0.75f ||
                            !tree.isInLineOfSight(Internal(s.x, s.y, s.ground + 1),
                                Internal(s.x + dx, s.y + dy, s.ground + 1), VMAP::ModelIgnoreFlags::Nothing))
                            footprint = false;
                    }
                float point[3]{s.y, s.ground + 2, s.x}, projected[3]{}, extent[3]{0.5f, 3, 0.5f};
                dtQueryFilter filter;
                filter.setIncludeFlags(NAV_GROUND);
                filter.setExcludeFlags(NAV_WATER | NAV_MAGMA | NAV_SLIME | NAV_GROUND_STEEP);
                dtPolyRef ref = 0;
                auto status = query->findNearestPoly(point, extent, &filter, &ref, projected);
                if (!footprint || dtStatusFailed(status) || ref != s.ref ||
                    std::hypot(projected[0] - s.y, projected[2] - s.x) > 0.01f)
                    continue;
                float distance = std::hypot(s.x - sums[area].first / counts[area],
                                            s.y - sums[area].second / counts[area]);
                if (distance < bestDistance)
                {
                    best = i;
                    bestDistance = distance;
                }
            }
            if (best != samples.size())
            {
                auto const& s = samples[best];
                float point[3]{s.y, s.ground + 2, s.x}, projected[3]{}, extent[3]{0.5f, 3, 0.5f};
                dtQueryFilter filter;
                filter.setIncludeFlags(NAV_GROUND);
                filter.setExcludeFlags(NAV_WATER | NAV_MAGMA | NAV_SLIME | NAV_GROUND_STEEP);
                dtPolyRef ref = 0;
                auto status = query->findNearestPoly(point, extent, &filter, &ref, projected);
                teleports << area << '\t' << best << '\t' << s.x << '\t' << s.y << '\t' << s.ground << '\t'
                    << s.ground + 2 << '\t' << s.z << '\t' << s.ref << '\t' << s.flags << "\t1\t"
                    << status << '\t' << ref << "\t9\n";
            }
        }
        std::cout << "LOADED maps=" << maps.size() << " vmaps=" << tree.numLoadedTiles() << " models=" << modelCount
                  << " mmaps=" << mmapFiles.size() << " source_cells=" << cells.size()
                  << " samples=" << samples.size() << '\n'
                  << "QUERIES total=" << queryCount << " complete=" << completeCount
                  << " incomplete=" << partialCount << '\n'
                  << "COLLISION rays=" << rayCount << " hits=" << rayHits << '\n'
                  << "Offline evidence only. Complete Detour corridors do not prove gameplay traversability.\n";
    }
    catch (std::exception const& error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
