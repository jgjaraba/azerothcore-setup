#!/usr/bin/env python3
"""Build the WotLK-native tw800crypt family from pinned, extracted WMO files.

No archive/client/runtime access. Only group 000 changes, by removing faces,
not vertices or flags. All validation completes before output is written.
"""

import argparse
from bisect import bisect_left
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


SOURCE_PREFIX = "__home__dev__wow-335__Data__common-2.MPQ__World__wmo__Dungeon__MD_Crypt__MD_Crypt_D"
TURTLE_NAME = "__home__dev__wow-turtle__Data__wmo.MPQ__World__wmo__Dungeon__MD_Crypt__MD_Crypt_D_000.wmo"
TURTLE_SHA256 = "a80180b03e7a45d976b9f64421a460141133640f694febab328b85a4cad7c281"
# Observed extracted common-2.MPQ baseline; 000 also matches the supplied hash.
SOURCE_SHA256 = (
    "b89d5f5abc7b24c57ea32f5b6ea659796a5fbd8c6467454df08783cca0120b1b",
    "10966c10cc65a82ab3796e17798bd144af481c66a5073a160363ee1dd14336a3",
    "73389b4c16706ca805c0705b9980cb16578e67f681c6af6b10df0860ee194f16",
    "079ed95a88a0a3acc5c984938b14582d863074b4aec4057844ca60a99fbd7602",
    "e7954cf9801b4c71f4f0a2f311b338be55215eeb43289d928455e80c2b19c394",
    "c57a0bc84f69ed5cbc0be71d7e63fc59edfbec3f1b2e529ee7f0eb02dfe2f4e4",
    "b6930cefd7c5ee7e61237dea47e6d7e27f2f4ed2aaa3b1c9d5cb8b87d2716016",
    "ec6cc520128fee688abdcdc1c83a5f7f9740644be8db185fec6ecf6338241706",
    "7ba56138a1f9eda281363d46725f6b1b7322ccd6e769ecd3ddd870aa309271f4",
    "441ab49822d9d007b268c4052cc4ec8b2ec5e2569c975d82797823d5e7ed447c",
    "97fcb88f885291a425066334fc69feddd290305848288349052d40127b3d4dd6",
    "07ef5eaa9e8666adaff372314e1176fb6c74dd0d97d2af2eb557076f0d663791",
    "af00c8b920a36034f93dd4626b62bc36790b7368335d40634b3c1ef091064226",
    "41f8ebce7ef79b19498d18c7f4992ea76c969246eb00e497d9b8b942c650098c",
    "0f16e09321276e31f3bb307ee6de6353ed25fd90951e1181aaa60237e8d5c122",
    "3675285d4bb9d7a6d82ba9e39256e6f1b7747689ecc2f5f5fbe83f872dfa254e",
    "307d19031c34d8680408e1aef7ba131ef6704145ee021847be3cd227b13f81a6",
    "45af435dc6037a2604510e58a50df07649d746cbc74077c09e23ef0d6374b49c",
    "8781044d73a85e77a626ce5a9f0efa8b93def819cc22a4a20173eb362072fa3f",
    "de60bef1460587e303bc663b3d2d5d5fa2714e868066f3688d0c518fce4d2b47",
)
REMOVED = tuple(range(792, 804))
FAMILY_PATH = Path("World/wmo/Custom/Turtle800")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def pinned(path, expected):
    data = path.read_bytes()
    require(sha256(data) == expected, f"Unexpected source SHA256: {path}")
    return data


def chunks(data):
    """Strict chunk boundaries; preserve original order and payload bytes."""
    result = {}
    offset = 0
    while offset < len(data):
        require(offset + 8 <= len(data), "Truncated chunk header")
        tag, size = struct.unpack_from("<4sI", data, offset)
        name = tag[::-1].decode("ascii")
        offset += 8
        require(offset + size <= len(data), f"Truncated {name}")
        require(name not in result, f"Duplicate chunk {name}")
        result[name] = data[offset:offset + size]
        offset += size
    return result


def pack_chunks(parts):
    return b"".join(name.encode("ascii")[::-1] + struct.pack("<I", len(data)) + data
                    for name, data in parts.items())


def records(data, fmt):
    require(len(data) % struct.calcsize(fmt) == 0, f"Misaligned records: {fmt}")
    return list(struct.iter_unpack(fmt, data))


def group(data):
    outer = chunks(data)
    require(list(outer) == ["MVER", "MOGP"], "Unexpected group envelope")
    require(outer["MVER"] == struct.pack("<I", 17), "Expected WMO v17")
    require(len(outer["MOGP"]) >= 68, "Truncated MOGP header")
    return outer, outer["MOGP"][:68], chunks(outer["MOGP"][68:])


def string_ref(table, offset):
    require(0 <= offset < len(table) and table.find(b"\0", offset) >= 0,
            f"Invalid string offset {offset}")


def validate_root(data):
    root = chunks(data)
    require(root["MVER"] == struct.pack("<I", 17), "Expected root v17")
    require(len(root["MOHD"]) == 64, "Invalid MOHD size")
    mats, groups, portals, lights, models, doodads, sets = struct.unpack_from("<7I", root["MOHD"])
    require(groups == 19, "Expected 19 groups")
    for name, count, size in (("MOMT", mats, 64), ("MOGI", groups, 32),
                              ("MOPT", portals, 20), ("MOLT", lights, 48),
                              ("MODS", sets, 32)):
        require(len(root[name]) == count * size, f"Invalid {name} count")
    actual_doodads = len(records(root["MODD"], "<I8fI"))
    # Pinned upstream root has a stale informational count. Do not repair it:
    # actual array bounds and all consuming references are checked below.
    require((doodads, actual_doodads) == (658, 641), "Unexpected root doodad counts")
    vertices = records(root["MOPV"], "<3f")
    for start, count, *_ in records(root["MOPT"], "<HH4f"):
        require(start + count <= len(vertices), "Invalid portal vertices")
    for portal, target, side, pad in records(root["MOPR"], "<HHhH"):
        require(portal < portals and target < groups and side in (-1, 1), "Invalid portal reference")
    for row in records(root["MOGI"], "<I6fi"):
        if row[-1] != -1:  # Native WMO sentinel: no group name.
            string_ref(root["MOGN"], row[-1])
    for row in records(root["MOMT"], "<16I"):
        for offset in (row[3], row[6]):  # WotLK's two texture offsets.
            string_ref(root["MOTX"], offset)
    names = {offset for offset in range(len(root["MODN"]))
             if root["MODN"][offset] and (offset == 0 or root["MODN"][offset - 1] == 0)}
    require(len(names) == models, "Invalid model name count")
    for name, *_ in records(root["MODD"], "<I8fI"):
        require(name & 0xffffff in names, "Invalid doodad name reference")
    for _, start, count, _ in records(root["MODS"], "<20sIII"):
        require(start + count <= actual_doodads, "Invalid doodad set range")
    records(root["MFOG"], "<I11f")
    return root


def validate_group(data, root):
    _, header, parts = group(data)
    vertices = records(parts["MOVT"], "<3f")
    triangles = records(parts["MOVI"], "<3H")
    materials = records(parts["MOPY"], "<BB")
    require(len(triangles) == len(materials), "MOVI/MOPY count mismatch")
    require(all(i < len(vertices) for tri in triangles for i in tri), "Invalid MOVI vertex")
    mat_count = len(root["MOMT"]) // 64
    require(all(mat == 255 or mat < mat_count for _, mat in materials), "Invalid MOPY material")
    for name, size in (("MONR", 12), ("MOTV", 8), ("MOCV", 4)):
        if name in parts:
            require(len(parts[name]) == len(vertices) * size, f"Invalid {name} count")
    batches = records(parts["MOBA"], "<12sIHHHBB")
    require(sum(struct.unpack_from("<3H", header, 40)) == len(batches), "Invalid batch count")
    for _, start, count, low, high, _, mat in batches:
        require(start % 3 == count % 3 == 0 and start + count <= len(triangles) * 3,
                "Invalid MOBA index range")
        require(low <= high < len(vertices) and mat < mat_count, "Invalid MOBA vertex/material")
        require(all(low <= v <= high for tri in triangles[start // 3:(start + count) // 3]
                    for v in tri), "MOBA vertex range does not enclose its indices")
    refs = [r[0] for r in records(parts["MOBR"], "<H")]
    require(all(r < len(triangles) for r in refs), "Invalid MOBR face")
    nodes = records(parts["MOBN"], "<HhhHIf")
    for flags, left, right, count, start, distance in nodes:
        require(start + count <= len(refs), "Invalid MOBN face range")
        require(all(c == -1 or 0 <= c < len(nodes) for c in (left, right)), "Invalid BSP child")
        require(flags in (0, 1, 2, 4), "Unknown BSP node type")
        require(flags != 4 or (left == right == -1), "Leaf has children")
    visited, active = set(), set()

    def walk(index):
        if index == -1:
            return
        require(index not in active and index not in visited, "BSP cycle/shared child")
        active.add(index)
        for child in nodes[index][1:3]:
            walk(child)
        active.remove(index)
        visited.add(index)

    walk(0)
    require(len(visited) == len(nodes), "Unreachable BSP nodes")
    for name, limit in (("MODR", len(root["MODD"]) // 40), ("MOLR", len(root["MOLT"]) // 48)):
        require(all(r[0] < limit for r in records(parts.get(name, b""), "<H")), f"Invalid {name}")
    for offset in (0, 4):
        string_ref(root["MOGN"], struct.unpack_from("<I", header, offset)[0])
    start, count = struct.unpack_from("<HH", header, 36)
    require(start + count <= len(root["MOPR"]) // 8, "Invalid MOGP portal range")
    require(all(f < len(root["MFOG"]) // 48 for f in header[48:52]), "Invalid fog reference")
    if "MLIQ" in parts:
        liquid = parts["MLIQ"]
        require(len(liquid) >= 30, "Truncated liquid header")
        xv, yv, xt, yt = struct.unpack_from("<4I", liquid)
        require(xv == xt + 1 and yv == yt + 1, "Invalid liquid grid dimensions")
        require(len(liquid) == 30 + xv * yv * 8 + xt * yt, "Invalid liquid array ranges")
        require(struct.unpack_from("<H", liquid, 28)[0] < mat_count, "Invalid liquid material")
    return {"vertices": len(vertices), "triangles": len(triangles),
            "bsp_nodes": len(nodes), "bsp_references": len(refs), "batches": len(batches)}


def geometry(parts):
    vertices = records(parts["MOVT"], "<3f")
    triangles = [tuple(vertices[i] for i in tri) for tri in records(parts["MOVI"], "<3H")]
    # Cyclic rotations preserve winding; sorting all three would hide reversal.
    return [min(tri, tri[1:] + tri[:1], tri[2:] + tri[:2]) for tri in triangles]


def fix(data, turtle):
    outer, header, original = group(data)
    parts = original.copy()
    old_geometry = geometry(original)
    turtle_geometry = geometry(group(turtle)[2])
    removed_geometry = [old_geometry[i] for i in REMOVED]
    require(Counter(old_geometry) - Counter(turtle_geometry) == Counter(removed_geometry)
            and not Counter(turtle_geometry) - Counter(old_geometry),
            "Turtle geometry differs beyond the expected 12 faces")
    require(all(original["MOPY"][2 * i + 1] == 255 for i in REMOVED), "Box is not material 255")
    bbox = [[min(v[k] for tri in removed_geometry for v in tri),
             max(v[k] for tri in removed_geometry for v in tri)] for k in range(3)]
    expected = ((14.772541, 23.687963), (3.926101, 7.811986), (-12.425611, -2.050285))
    require(all(abs(a - b) < 0.000001 for pair, target in zip(bbox, expected)
                for a, b in zip(pair, target)), "Unexpected box bbox")
    edges = Counter(tuple(sorted((tri[a], tri[b]))) for tri in removed_geometry
                    for a, b in ((0, 1), (1, 2), (2, 0)))
    require(len({v for tri in removed_geometry for v in tri}) == 8
            and len(edges) == 18 and set(edges.values()) == {2}, "Expected closed 8-corner box")
    for name, stride in (("MOVI", 6), ("MOPY", 2)):
        parts[name] = b"".join(original[name][i:i + stride]
                               for i in range(0, len(original[name]), stride)
                               if i // stride not in REMOVED)
    old_refs = [r[0] for r in records(original["MOBR"], "<H")]
    prefix = [0]
    new_refs = []
    for face in old_refs:
        if face not in REMOVED:
            new_refs.append(face - bisect_left(REMOVED, face))
        prefix.append(len(new_refs))
    parts["MOBR"] = b"".join(struct.pack("<H", r) for r in new_refs)
    nodes = bytearray(original["MOBN"])
    for i, (_, _, _, count, start, _) in enumerate(records(nodes, "<HhhHIf")):
        struct.pack_into("<HI", nodes, 16 * i + 6, prefix[start + count] - prefix[start], prefix[start])
    parts["MOBN"] = bytes(nodes)
    batches = bytearray(original["MOBA"])
    changed_batches = []
    for i, (_, start, count, *_) in enumerate(records(batches, "<12sIHHHBB")):
        begin = start // 3 - bisect_left(REMOVED, start // 3)
        end = (start + count) // 3 - bisect_left(REMOVED, (start + count) // 3)
        struct.pack_into("<IH", batches, 24 * i + 12, begin * 3, (end - begin) * 3)
        if batches[24 * i:24 * (i + 1)] != original["MOBA"][24 * i:24 * (i + 1)]:
            changed_batches.append(i)
    parts["MOBA"] = bytes(batches)
    outer["MOGP"] = header + pack_chunks(parts)
    output = pack_chunks(outer)
    # Preservation checks independent of the serialized envelope sizes.
    _, new_header, actual = group(output)
    require(new_header == header and list(actual) == list(original), "Changed group header/order")
    changed = [name for name in original if original[name] != actual[name]]
    require(set(changed) <= {"MOVI", "MOPY", "MOBR", "MOBN", "MOBA"}, "Changed unrelated chunk")
    require(geometry(actual) == [tri for i, tri in enumerate(old_geometry) if i not in REMOVED],
            "Changed retained geometry/order")
    require(Counter(geometry(actual)) == Counter(turtle_geometry), "Output is not Turtle-equivalent")
    for old, new in zip(records(original["MOBN"], "<HhhHIf"), records(actual["MOBN"], "<HhhHIf")):
        require(old[:3] == new[:3] and old[5] == new[5], "Changed BSP tree/planes")
        expected_refs = [f - bisect_left(REMOVED, f) for f in old_refs[old[4]:old[4] + old[3]]
                         if f not in REMOVED]
        require(new_refs[new[4]:new[4] + new[3]] == expected_refs, "Changed retained BSP membership")
    return output, {"removed_faces_zero_based": list(REMOVED), "removed_bbox_xyz": bbox,
                    # Stable coordinate listing; comparisons above retain winding.
                    "removed_triangles_xyz": [tuple(sorted(tri)) for tri in removed_geometry],
                    "changed_chunks": changed,
                    "removed_bsp_references": len(old_refs) - len(new_refs),
                    "changed_batches": changed_batches,
                    "turtle_geometry_exact_multiset_match": True,
                    "retained_geometry_and_order_unchanged": True,
                    "bsp_tree_planes_and_retained_membership_unchanged": True}


def build(source_dir, output_dir):
    suffixes = [""] + [f"_{i:03d}" for i in range(19)]
    sources = [pinned(source_dir / f"{SOURCE_PREFIX}{suffix}.wmo", digest)
               for suffix, digest in zip(suffixes, SOURCE_SHA256)]
    turtle = pinned(source_dir / TURTLE_NAME, TURTLE_SHA256)
    root = validate_root(sources[0])
    before = [validate_group(data, root) for data in sources[1:]]
    fixed, evidence = fix(sources[1], turtle)
    outputs = [sources[0], fixed] + sources[2:]
    after = [validate_group(data, root) for data in outputs[1:]]
    manifest = {"format": "WotLK WMO v17", "family": str(FAMILY_PATH / "tw800crypt.wmo"),
                "preserved_source_anomalies": [
                    "Root MOHD nDoodads=658 but MODD and default set contain 641; "
                    "all references validated against actual 641 records; root unchanged."],
                "turtle_reference_sha256": TURTLE_SHA256, "evidence": evidence,
                "group000_before": before[0], "group000_after": after[0], "files": []}
    for i, (suffix, original, data) in enumerate(zip(suffixes, sources, outputs)):
        require(i == 1 or data == original, "Changed root/other group")
        relative = FAMILY_PATH / f"tw800crypt{suffix}.wmo"
        manifest["files"].append({"path": str(relative), "source_sha256": sha256(original),
                                  "sha256": sha256(data), "bytes": len(data)})
    # Refuse to overwrite unrelated work; allow deterministic rebuilds.
    files = {entry["path"]: data for entry, data in zip(manifest["files"], outputs)}
    files["validation.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    files["SHA256SUMS"] = "".join(f"{entry['sha256']}  {entry['path']}\n"
                                  for entry in manifest["files"]).encode()
    for name, data in files.items():
        path = output_dir / name
        require(not path.exists() or path.read_bytes() == data, f"Refusing to overwrite different output: {path}")
    for name, data in files.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        require(path.read_bytes() == data, f"Output readback mismatch: {path}")
    print(json.dumps({"output_dir": str(output_dir), "group000_sha256": sha256(fixed),
                      "before": before[0], "after": after[0],
                      "removed_bsp_references": evidence["removed_bsp_references"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("/tmp/opencode/crypt-research"))
    parser.add_argument("--output-dir", type=Path, default=Path("work/crypt-fix/wmo"))
    args = parser.parse_args()
    try:
        build(args.source_dir, args.output_dir)
    except (ValueError, OSError, KeyError, struct.error) as error:
        parser.exit(1, f"crypt collision fix: {error}\n")


if __name__ == "__main__":
    main()
