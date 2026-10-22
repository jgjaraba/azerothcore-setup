// Offline pilot validation using the checkout's actual Detour and VMap readers.
// No worldserver, SQL, client or runtime writes. Query points use world XYZ.
#include "MapDefines.h"
#include "MapTree.h"
#include "ModelInstance.h"
#include "VMapMgr2.h"
#include "WorldModel.h"
#include "DetourNavMeshQuery.h"
#include <G3D/Vector3.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace fs = std::filesystem;

static std::vector<unsigned char> Read(fs::path const& path)
{
    std::ifstream input(path, std::ios::binary);
    if (!input)
        throw std::runtime_error("Cannot read " + path.string());
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(input), {});
}

static G3D::Vector3 Internal(float x, float y, float z)
{
    return VMAP::VMapMgr2::convertPositionToInternalRep(x, y, z);
}

static float Distance(float const* a, float const* b)
{
    return std::sqrt((a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]) + (a[2]-b[2])*(a[2]-b[2]));
}

// Same corridor-prefix mechanism as AzerothCore PathGenerator::FixupCorridor.
// This probe uses a denser step size and larger diagnostic buffers; it is not
// an execution of the live Unit movement generator.
static bool MergeCorridor(std::vector<dtPolyRef>& corridor, dtPolyRef const* visited, int count)
{
    for (int p = static_cast<int>(corridor.size())-1; p >= 0; --p)
    {
        for (int v = count-1; v >= 0; --v)
        {
            if (corridor[p] != visited[v])
                continue;
            std::vector<dtPolyRef> next;
            for (int j = count-1; j >= v; --j)
                next.push_back(visited[j]);
            next.insert(next.end(), corridor.begin()+p+1, corridor.end());
            corridor.swap(next);
            return true;
        }
    }
    return false;
}

int main(int argc, char** argv)
{
    try
    {
        if (argc < 3)
            throw std::runtime_error("usage: crypt_nav_probe DATA_ROOT MMAPS_DIR [--samples]; stdin: label sx sy sz ex ey ez walk|swim");
        fs::path root(argv[1]), mmaps(argv[2]);
        bool samples = argc == 4 && std::string(argv[3]) == "--samples";
        bool segments = argc == 4 && std::string(argv[3]) == "--segments";
        auto paramsBytes = Read(mmaps / "800.mmap");
        if (paramsBytes.size() != sizeof(dtNavMeshParams))
            throw std::runtime_error("Wrong native mmap params size");
        dtNavMeshParams params;
        std::memcpy(&params, paramsBytes.data(), sizeof(params));
        std::unique_ptr<dtNavMesh, decltype(&dtFreeNavMesh)> mesh(dtAllocNavMesh(), dtFreeNavMesh);
        if (dtStatusFailed(mesh->init(&params)))
            throw std::runtime_error("Detour init failed");
        VMAP::StaticMapTree tree(800, (root / "vmaps").string() + "/");
        if (!tree.InitMap("800.vmtree"))
            throw std::runtime_error("Cannot initialize native VMap tree");
        unsigned loaded = 0;
        float climbTolerance = 0;
        for (int x = 34; x <= 36; ++x)
        {
            for (int y = 52; y <= 53; ++y)
            {
                // ADT/generator X,Y are reversed relative to server grid X,Y.
                // StaticMapTree itself reverses them in its filename formatter.
                if (VMAP::StaticMapTree::CanLoadMap((root / "vmaps").string(), 800, y, x) != VMAP::LoadResult::Success ||
                    !tree.LoadMapTile(y, x))
                    throw std::runtime_error("VMap tile load failed");
                char name[64];
                std::snprintf(name, sizeof(name), "800%02d%02d.mmtile", y, x);
                fs::path file = mmaps / name;
                if (!fs::exists(file))
                    continue;
                auto bytes = Read(file);
                if (bytes.size() < sizeof(MmapTileHeader))
                    throw std::runtime_error("Truncated MMap header");
                MmapTileHeader header;
                std::memcpy(&header, bytes.data(), sizeof(header));
                if (header.mmapMagic != MMAP_MAGIC || header.mmapVersion != MMAP_VERSION ||
                    header.dtVersion != DT_NAVMESH_VERSION || header.size < sizeof(dtMeshHeader) ||
                    bytes.size() != sizeof(header) + header.size)
                    throw std::runtime_error("MMap native version/size mismatch");
                auto* payload = static_cast<unsigned char*>(dtAlloc(header.size, DT_ALLOC_PERM));
                if (!payload)
                    throw std::runtime_error("Detour tile allocation failed");
                std::memcpy(payload, bytes.data()+sizeof(header), header.size);
                climbTolerance = std::max(climbTolerance, reinterpret_cast<dtMeshHeader const*>(payload)->walkableClimb);
                auto status = mesh->addTile(payload, header.size, DT_TILE_FREE_DATA, 0, nullptr);
                if (dtStatusFailed(status))
                {
                    dtFree(payload);
                    throw std::runtime_error("Detour rejected tile " + file.string());
                }
                ++loaded;
            }
        }
        std::unique_ptr<dtNavMeshQuery, decltype(&dtFreeNavMeshQuery)> query(dtAllocNavMeshQuery(), dtFreeNavMeshQuery);
        if (dtStatusFailed(query->init(mesh.get(), 65535)))
            throw std::runtime_error("Detour query init failed");
        std::cerr << "Loaded Detour tiles=" << loaded << ", VMap tiles=" << tree.numLoadedTiles() << '\n';
        VMAP::ModelInstance* models = nullptr;
        uint32 modelCount = 0;
        tree.GetModelInstances(models, modelCount);
        for (uint32 i = 0; i < modelCount; ++i)
            if (models[i].ID && !models[i].getWorldModel())
                throw std::runtime_error("Missing native collision model: " + models[i].name);
        std::cout << std::setprecision(9);
        if (samples)
        {
            std::cout << "group\tx\ty\tz\tpoly\tflags\tfloor\n";
            for (int t = 0; t < mesh->getMaxTiles(); ++t)
            {
                dtMeshTile const* tile = static_cast<dtNavMesh const*>(mesh.get())->getTile(t);
                if (!tile || !tile->header)
                    continue;
                for (int i = 0; i < tile->header->polyCount; ++i)
                {
                    auto const& poly = tile->polys[i];
                    if (poly.getType() == DT_POLYTYPE_OFFMESH_CONNECTION || !(poly.flags & NAV_GROUND))
                        continue;
                    float center[3]{};
                    for (int v = 0; v < poly.vertCount; ++v)
                        for (int k = 0; k < 3; ++k)
                            center[k] += tile->verts[poly.verts[v]*3+k] / poly.vertCount;
                    dtPolyRef ref = mesh->getPolyRefBase(tile) | static_cast<dtPolyRef>(i);
                    if (dtStatusFailed(query->getPolyHeight(ref, center, &center[1])))
                        continue;
                    float x = center[2], y = center[0], z = center[1];
                    if (x < -11330 || x > -10900 || y < -2050 || y > -1200 || z < -250 || z > 120)
                        continue;
                    VMAP::LocationInfo info;
                    if (tree.GetLocationInfo(Internal(x, y, z+1), info) && info.rootId == 3833 && info.hitModel &&
                        std::abs(info.ground_Z-z) < 1)
                        std::cout << info.hitModel->GetWmoID() << '\t' << x << '\t' << y << '\t' << z << '\t'
                                  << ref << '\t' << poly.flags << '\t' << info.ground_Z << '\n';
                }
            }
            return 0;
        }
        std::cout << "label\tcomplete\tstatus\tstart_ref\tend_ref\tstart_snap\tend_snap\tpolys\tstraight_points\tlength\tlos\tstart_floor\tend_floor\tstraight_vmap_blocked_segments\tsampled_vmap_blocked\tsampled_failed\tsampled_steps\theight_edge_fallbacks\n";
        std::string line;
        while (std::getline(std::cin, line))
        {
            if (line.empty() || line[0] == '#')
                continue;
            std::istringstream input(line);
            std::string label, mode;
            float sx, sy, sz, ex, ey, ez;
            if (!(input >> label >> sx >> sy >> sz >> ex >> ey >> ez >> mode) || (mode != "walk" && mode != "swim"))
                throw std::runtime_error("Invalid query line: " + line);
            float start[3]{sy, sz, sx}, end[3]{ey, ez, ex};
            float nearStart[3]{}, nearEnd[3]{};
            float extents[3]{1.5f, 2.0f, 1.5f};
            dtPolyRef a = 0, b = 0;
            dtQueryFilter filter;
            filter.setIncludeFlags(mode == "swim" ? NAV_GROUND | NAV_WATER : NAV_GROUND);
            filter.setExcludeFlags(NAV_MAGMA | NAV_SLIME | NAV_GROUND_STEEP);
            query->findNearestPoly(start, extents, &filter, &a, nearStart);
            query->findNearestPoly(end, extents, &filter, &b, nearEnd);
            std::array<dtPolyRef, 16384> path{};
            int count = 0;
            dtStatus status = DT_FAILURE;
            if (a && b)
                status = query->findPath(a, b, nearStart, nearEnd, &filter, path.data(), &count, path.size());
            bool complete = dtStatusSucceed(status) && count && path[count-1] == b &&
                !(status & (DT_PARTIAL_RESULT | DT_OUT_OF_NODES | DT_BUFFER_TOO_SMALL));
            std::array<float, 16384*3> straight{};
            std::array<unsigned char, 16384> flags{};
            std::array<dtPolyRef, 16384> refs{};
            int points = 0;
            if (complete)
            {
                auto straightStatus = query->findStraightPath(nearStart, nearEnd, path.data(), count,
                    straight.data(), flags.data(), refs.data(), &points, refs.size(), DT_STRAIGHTPATH_ALL_CROSSINGS);
                complete = dtStatusSucceed(straightStatus) && !(straightStatus & DT_BUFFER_TOO_SMALL);
            }
            float length = 0;
            unsigned blocked = 0;
            for (int i = 1; i < points; ++i)
            {
                float const* p = straight.data()+(i-1)*3;
                float const* q = straight.data()+i*3;
                length += Distance(p, q);
                if (!tree.isInLineOfSight(Internal(p[2], p[0], p[1]+1.5f),
                                         Internal(q[2], q[0], q[1]+1.5f), VMAP::ModelIgnoreFlags::Nothing))
                {
                    ++blocked;
                    if (segments)
                    {
                        G3D::Vector3 hit;
                        tree.GetObjectHitPos(Internal(p[2], p[0], p[1]+1.5f),
                                             Internal(q[2], q[0], q[1]+1.5f), hit, 0);
                        auto worldHit = Internal(hit.x, hit.y, hit.z);
                        std::cerr << std::setprecision(9) << "BLOCK " << label << " "
                                  << p[2] << " " << p[0] << " " << p[1] << " -> "
                                  << q[2] << " " << q[0] << " " << q[1] << " hit "
                                  << worldHit.x << " " << worldHit.y << " " << worldHit.z << '\n';
                    }
                }
            }
            // A straight corridor's interpolated endpoint heights can cut
            // through detailed sloped floors. Follow the native surface in
            // small steps and query its detail height before testing body LOS.
            float previous[3]{nearStart[0], nearStart[1], nearStart[2]};
            unsigned sampledBlocked = 0, sampledFailed = 0, sampledSteps = 0, heightFallbacks = 0;
            std::vector<dtPolyRef> corridor(path.begin(), path.begin()+count);
            bool reached = false;
            while (complete && !reached && !sampledFailed && sampledSteps < 20000)
            {
                if (std::hypot(previous[0]-nearEnd[0], previous[2]-nearEnd[2]) < 0.3f &&
                    std::abs(previous[1]-nearEnd[1]) < 1.0f)
                {
                    reached = true;
                    break;
                }
                std::array<float, 9> steering{};
                std::array<unsigned char, 3> steeringFlags{};
                std::array<dtPolyRef, 3> steeringRefs{};
                int corners = 0;
                auto steerStatus = query->findStraightPath(previous, nearEnd, corridor.data(), corridor.size(),
                    steering.data(), steeringFlags.data(), steeringRefs.data(), &corners, 3);
                if (dtStatusFailed(steerStatus) || !corners)
                {
                    ++sampledFailed;
                    break;
                }
                int index = 0;
                while (index < corners && !(steeringFlags[index] & DT_STRAIGHTPATH_END) &&
                       std::hypot(steering[index*3]-previous[0], steering[index*3+2]-previous[2]) < 0.3f)
                    ++index;
                if (index == corners || (steeringFlags[index] & DT_STRAIGHTPATH_OFFMESH_CONNECTION))
                {
                    ++sampledFailed;
                    break;
                }
                float const* corner = steering.data()+index*3;
                float dx = corner[0]-previous[0], dz = corner[2]-previous[2];
                float planar = std::hypot(dx, dz);
                float factor = std::min(1.0f, 0.4f/std::max(planar, 0.00001f));
                float target[3]{previous[0]+dx*factor, previous[1], previous[2]+dz*factor};
                {
                    float next[3]{};
                    std::array<dtPolyRef, 32> visited{};
                    int visitedCount = 0;
                    auto surfaceStatus = query->moveAlongSurface(corridor.front(), previous, target, &filter,
                        next, visited.data(), &visitedCount, visited.size());
                    float nextHeight = next[1];
                    dtStatus heightStatus = visitedCount ? query->getPolyHeight(visited[visitedCount-1], next, &nextHeight) : DT_FAILURE;
                    if (visitedCount && dtStatusFailed(heightStatus))
                    {
                        // Native getPolyHeight rejects some exact boundary
                        // points. Only allow a tightly bounded reprojection,
                        // not a broad nearest-poly search across floors/walls.
                        float projected[3]{};
                        auto projectedStatus = query->closestPointOnPoly(visited[visitedCount-1], next, projected, nullptr);
                        if (dtStatusSucceed(projectedStatus) &&
                            std::hypot(projected[0]-next[0], projected[2]-next[2]) < 0.01f &&
                            std::abs(projected[1]-next[1]) <= climbTolerance+0.001f)
                        {
                            std::copy(projected, projected+3, next);
                            nextHeight = projected[1];
                            heightStatus = DT_SUCCESS;
                            ++heightFallbacks;
                        }
                        else if (segments)
                            std::cerr << "EDGE_PROJECT_REJECT " << label << " delta_xy "
                                      << std::hypot(projected[0]-next[0], projected[2]-next[2])
                                      << " delta_z " << projected[1]-next[1] << '\n';
                    }
                    next[1] = nextHeight;
                    if (dtStatusFailed(surfaceStatus) || !visitedCount || (surfaceStatus & DT_BUFFER_TOO_SMALL) ||
                        dtStatusFailed(heightStatus) ||
                        std::hypot(previous[0]-next[0], previous[2]-next[2]) < 0.0001f ||
                        std::abs(previous[1]-next[1]) > climbTolerance+0.001f)
                    {
                        ++sampledFailed;
                        if (segments)
                            std::cerr << "SURFACE_FAIL " << label << " previous " << previous[2] << ' ' << previous[0] << ' ' << previous[1]
                                      << " target " << target[2] << ' ' << target[0] << ' ' << target[1]
                                      << " next " << next[2] << ' ' << next[0] << ' ' << next[1]
                                      << " visited " << visitedCount << " status " << surfaceStatus
                                      << " height_status " << heightStatus << '\n';
                        break;
                    }
                    if (!tree.isInLineOfSight(Internal(previous[2], previous[0], previous[1]+1.5f),
                                             Internal(next[2], next[0], next[1]+1.5f), VMAP::ModelIgnoreFlags::Nothing))
                        ++sampledBlocked;
                    std::copy(next, next+3, previous);
                    if (!MergeCorridor(corridor, visited.data(), visitedCount))
                        ++sampledFailed;
                    ++sampledSteps;
                }
            }
            if (complete && !reached && !sampledFailed)
                ++sampledFailed;
            bool los = tree.isInLineOfSight(Internal(sx, sy, sz+1.5f), Internal(ex, ey, ez+1.5f), VMAP::ModelIgnoreFlags::Nothing);
            float floorStart = tree.getHeight(Internal(sx, sy, sz+1), 4);
            float floorEnd = tree.getHeight(Internal(ex, ey, ez+1), 4);
            std::cout << label << '\t' << complete << '\t' << status << '\t' << a << '\t' << b << '\t'
                      << (a ? Distance(start, nearStart) : -1) << '\t' << (b ? Distance(end, nearEnd) : -1) << '\t'
                      << count << '\t' << points << '\t' << length << '\t' << los << '\t'
                      << floorStart << '\t' << floorEnd << '\t' << blocked << '\t'
                      << sampledBlocked << '\t' << sampledFailed << '\t' << sampledSteps << '\t' << heightFallbacks << '\n';
        }
    }
    catch (std::exception const& error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
