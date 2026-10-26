#!/usr/bin/env python3
"""Independent binary integration checks; requires extracted, licensed source models.

Run: DOTNET=/path/to/dotnet python3 tools/test_new_races_models.py --source-root DIR
Outputs are confined to work/new-races-models (or --output below that directory).
No MPQ, DBC, server, or live client access.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    ("GoblinMale", r"Character\Goblin\Male\GoblinMale.m2"),
    ("GoblinFemale", r"Character\Goblin\Female\GoblinFemale.m2"),
    ("HighElfMale", r"Character\BloodElf\Male\BloodElfMale.m2"),
    ("HighElfFemale", r"Character\BloodElf\Female\BloodElfFemale.M2"),
]


def pair(b, o):
    return struct.unpack_from("<II", b, o)


def array(b, o, width):
    n, p = pair(b, o)
    assert p + n * width <= len(b), (o, n, p, width, len(b))
    return [b[p+i*width:p+(i+1)*width] for i in range(n)]


def uints(b):
    return list(struct.unpack("<" + "I" * (len(b)//4), b))


def shorts(b):
    return list(struct.unpack("<" + "H" * (len(b)//2), b))


def audit_references(a, bone):
    bones = array(a,52,108)
    def ancestry(root):
        result = set()
        while root != -1:
            assert 0 <= root < len(bones) and root not in result
            result.add(root)
            root = struct.unpack_from("<h",bones[root],8)[0]
        return result
    chains = [ancestry(i) for i in range(len(bones))]
    weighted = {b for v in array(a,68,48) for w,b in zip(v[12:16],v[16:20]) if w}
    def depends(root):
        return root != -1 and bone in ancestry(root)
    return dict(
        directlyWeighted=bone in weighted,
        directChildren=[i for i,b in enumerate(bones) if struct.unpack_from("<h",b,8)[0] == bone],
        descendants=[i for i,c in enumerate(chains) if i != bone and bone in c],
        weightedBoneParentClosure=sorted(set().union(*(ancestry(i) for i in weighted))),
        weightedDependents=sorted(i for i in weighted if depends(i)),
        attachments=[dict(index=i,id=struct.unpack_from("<I",r)[0],root=struct.unpack_from("<I",r,4)[0])
                     for i,r in enumerate(array(a,260,48)) if depends(struct.unpack_from("<I",r,4)[0])],
        events=[dict(index=i,identifier=r[:4].decode(),root=struct.unpack_from("<H",r,8)[0])
                for i,r in enumerate(array(a,276,44)) if depends(struct.unpack_from("<H",r,8)[0])],
        lights=[dict(index=i,root=struct.unpack_from("<h",r,2)[0])
                for i,r in enumerate(array(a,284,212)) if depends(struct.unpack_from("<h",r,2)[0])],
        keyBones=[dict(bone=i,keyBoneId=struct.unpack_from("<i",r)[0])
                  for i,r in enumerate(bones) if struct.unpack_from("<i",r)[0] >= 0 and depends(i)],
        keyBoneLookup=[dict(slot=i,root=struct.unpack("<h",r)[0])
                       for i,r in enumerate(array(a,60,2)) if depends(struct.unpack("<h",r)[0])])


def validate(source, target):
    a, b = source.read_bytes(), target.read_bytes()
    report = json.loads(Path(str(target) + ".report.json").read_text())
    assert a[:8] == b"MD20\x00\x01\x00\x00"
    assert b[:8] == b"MD20\x08\x01\x00\x00"
    assert report["sourceSha256"] == hashlib.sha256(a).hexdigest()
    for entry in report["files"]:
        blob = target.with_name(entry["name"]).read_bytes()
        assert len(blob) == entry["bytes"]
        assert hashlib.sha256(blob).hexdigest() == entry["sha256"]
    av, bv = array(a, 68, 48), array(b, 60, 48)
    assert av == bv
    ab, bb = array(a, 52, 108), array(b, 44, 88)
    assert len(ab) == len(bb)
    seq, converted = array(a, 28, 68), array(b, 28, 64)
    count = len(seq)
    assert len(converted) == report["outputSequences"]
    for old, new in zip(seq, converted):
        assert old[:4] == new[:4]
        start, end = pair(old, 4)
        assert struct.unpack_from("<I", new, 4)[0] == end-start
        assert old[12:16] == new[8:12]  # moving speed
        old_flags = struct.unpack_from("<I", old, 16)[0]
        assert struct.unpack_from("<I", new, 12)[0] == (old_flags & ~0x40) | 0x100
        assert old[20:66] == new[16:62]  # probability, replay, blend, bounds, next
    assert a[180:236] == b[160:216]  # model bounds and collision bounds
    for x, y, width in [(20,20,4), (60,52,2), (132,112,4), (140,120,2),
                        (148,128,2), (156,136,2), (164,144,2), (172,152,2),
                        (236,216,2), (244,224,12), (252,232,12), (268,248,2), (300,280,2)]:
        assert array(a, x, width) == array(b, y, width), (source, x)

    # Validate all skins, including palettes, batches, and newly required enclosing spheres.
    combos = shorts(b"".join(array(b, 120, 2)))
    source_views = array(a, 76, 44)
    assert len(source_views) == struct.unpack_from("<I", b, 68)[0]
    sections_count = 0
    for view_id, view in enumerate(source_views):
        sk = target.with_name(target.stem + f"{view_id:02}.skin").read_bytes()
        assert sk[:4] == b"SKIN"
        for so, to, width in [(0,4,2), (8,12,2), (16,20,4), (32,36,24)]:
            assert array(a, struct.unpack_from("<I", a, 80)[0] + view_id*44 + so, width) == array(sk, to, width)
        lookup = shorts(b"".join(array(sk, 4, 2)))
        triangles = shorts(b"".join(array(sk, 12, 2)))
        properties = array(sk, 20, 4)
        sections = array(sk, 28, 48)
        original_sections = array(a, struct.unpack_from("<I", a, 80)[0]+view_id*44+24, 32)
        assert len(sections) == len(original_sections)
        for original_section, section in zip(original_sections, sections):
            assert original_section == section[:32]
            _, _, vs, vc, ts, tc, bc, bs, _, _ = struct.unpack_from("<10H", section)
            assert vs+vc <= len(lookup) and ts+tc <= len(triangles) and bs+bc <= len(combos)
            assert all(vs <= t < vs+vc for t in triangles[ts:ts+tc])
            x, y, z, radius = struct.unpack_from("<4f", section, 32)
            assert radius > 0
            for i in range(vs, vs+vc):
                vertex = bv[lookup[i]]
                px, py, pz = struct.unpack_from("<3f", vertex)
                assert (px-x)**2 + (py-y)**2 + (pz-z)**2 <= (radius+1e-5)**2
                for weight, bone, local in zip(vertex[12:16], vertex[16:20], properties[i]):
                    if weight:
                        assert local < bc and combos[bs+local] == bone
            sections_count += 1
        for batch in array(sk, 36, 24):
            _, _, _, si, si2, _, mi, _, ntex, tex, _, _, _ = struct.unpack("<BBhHHhHHHHHHH", batch)
            assert si < len(sections) and si2 < len(sections)
            assert mi < len(array(b, 112, 4)) and tex+ntex <= len(array(b, 128, 2))

    max_quaternion_error = 0
    vector_keys = 0
    all_tracks = []
    repaired_pairs = set()
    native_spline_pairs = set()
    expected_repairs = {"8dab731974fbaaa12201f81803726a32e5fd72b2153a366c64b08f7127643e42": {(80,2),(126,0)},
                        "ae5d9f09c7ec560f6518a7a62fa27ca079b2b051a522a11fee84d2983fb9633f": {(90,2)}}.get(report["sourceSha256"],set())
    repairs = {(r["bone"], ["Translation","Rotation","Scale"].index(r["track"])):r for r in report["trackRepairs"]}
    assert repairs.keys() == expected_repairs
    for bone,(old, new) in enumerate(zip(ab, bb)):
        assert old[:12] == new[:12] and old[-12:] == new[-12:]
        for j in range(3):
            sa,tb = old[12+28*j:40+28*j],new[16+20*j:36+20*j]
            if (bone,j) in expected_repairs:
                assert struct.unpack_from("<H",sa)[0] == 2 and struct.unpack_from("<H",tb)[0] == 1
                assert sa[2:4] == tb[2:4]
                repaired_pairs.add((sa,tb))
                repair = repairs[bone,j]
                assert repair["sourceInterpolation"] == 2 and repair["targetInterpolation"] == 1
                nv,pv = pair(sa,20)
                nt,pt = pair(sa,12)
                assert repair["sourceSha256"] == hashlib.sha256(a).hexdigest()
                assert repair["sourceValueCount"] == nv and repair["sourceTimestampCount"] == nt
                assert repair["sourceValueBytesSha256"] == hashlib.sha256(a[pv:pv+nv*12]).hexdigest()
                assert repair["sourceTimestampBytesSha256"] == hashlib.sha256(a[pt:pt+nt*4]).hexdigest()
                refs = audit_references(a,bone)
                for key,value in refs.items():
                    assert repair["references"][key] == value, (bone,key)
                used = any(refs[k] for k in ["weightedDependents","attachments","events","lights","keyBones","keyBoneLookup"])
                assert repair["references"]["referencedThroughAnyParentClosure"] == used
                assert repair["references"]["cameras"]["count"] == len(array(a,292,124))
                assert repair["references"]["particles"]["count"] == pair(a,316)[0] == 0
                assert repair["references"]["ribbons"]["count"] == pair(a,308)[0] == 0
            else:
                assert sa[:4] == tb[:4]
            all_tracks.append((sa,tb,16 if j == 1 else 12,j == 1))
    for old, new in zip(array(a,84,56), array(b,72,40)):
        all_tracks += [(old[:28],new[:20],12,False), (old[28:],new[20:],2,False)]
    all_tracks += [(x,y,2,False) for x,y in zip(array(a,100,28), array(b,88,20))]
    for x,y in zip(array(a,116,84), array(b,96,60)):
        all_tracks += [(x[j*28:(j+1)*28], y[j*20:(j+1)*20],16 if j == 1 else 12,False) for j in range(3)]
    for old, new in zip(array(a,260,48), array(b,240,40)):
        assert old[:20] == new[:20]
        all_tracks.append((old[20:],new[20:],1,False))
    for old, new in zip(array(a,276,44), array(b,256,36)):
        assert old[:24] == new[:24]
        all_tracks.append((old[24:],new[24:],0,False))
    assert not array(a,284,212)  # Light conversion not covered by this fixture validator.
    for old, new in zip(array(a,292,124), array(b,272,100)):
        assert old[:16] == new[:16] and old[44:56] == new[36:48] and old[84:96] == new[68:80]
        all_tracks += [(old[16:44],new[16:36],36,False), (old[56:84],new[48:68],36,False), (old[96:],new[80:],12,False)]
        native_spline_pairs.update([(old[16:44],new[16:36]),(old[56:84],new[48:68]),(old[96:],new[80:])])
    spline_tracks = spline_keys = 0
    for old, new, width, quat in all_tracks:
        assert old[:4] == new[:4] or (old,new) in repaired_pairs
        interpolation, glob = struct.unpack_from("<Hh", old)
        target_interpolation = struct.unpack_from("<H",new)[0]
        nt, pt = pair(old,12)
        times = uints(a[pt:pt+nt*4])
        nrows, prows = pair(new,4)
        if not nt:
            assert nrows == 0
            continue
        assert nrows == (1 if glob >= 0 else len(converted))
        if width:
            nv, pv = pair(old,20)
            assert nv == nt
            nvalues, pvalues = pair(new,12)
            assert nvalues == nrows
        rows = []
        is_spline = target_interpolation in (2,3)
        if is_spline:
            assert (old,new) in native_spline_pairs and width in (12,36)
            spline_tracks += 1
        for index in range(nrows):
            nk, pk = pair(b,prows+index*8)
            ts = uints(b[pk:pk+nk*4])
            if width:
                nvk, pvalue = pair(b,pvalues+index*8)
                assert nvk == nk
                target_width = 8 if quat else width
                assert pvalue + nvk * target_width <= len(b)
                if is_spline:
                    # Every logical key must contain value/in/out coefficients, not a lone vector/scalar.
                    scalar_width = 12 if width == 36 else 4
                    payload = b[pvalue:pvalue+nvk*target_width]
                    assert len(payload) // scalar_width == nk * 3
                    spline_keys += nk
                vals = [b[pvalue+k*target_width:pvalue+(k+1)*target_width] for k in range(nk)]
            else:
                vals = []
            rows.append((ts, vals))
            if index >= count and glob < 0:
                continue
            start, end = pair(seq[index],4) if glob < 0 else (0, 2**32-1)
            singleton_constant = width and nt == 1 and glob < 0
            selected = [0] if singleton_constant else [i for i,t in enumerate(times) if start <= t <= end]
            assert ts == ([0] if singleton_constant else [times[i]-start for i in selected])
            for k,i in enumerate(selected):
                if not width:
                    continue
                value = a[pv+i*width:pv+(i+1)*width]
                if quat:
                    original_q = struct.unpack("<4f",value)
                    compressed = struct.unpack("<4h",vals[k])
                    decoded = [1 if q == -1 else ((q-32767) if q > 0 else (q+32767))/32767 for q in compressed]
                    error = max(abs(x-y) for x,y in zip(original_q,decoded))
                    assert error <= 1/32767 + 1e-12
                    max_quaternion_error = max(max_quaternion_error,error)
                else:
                    assert value == vals[k]
                    vector_keys += 1
        if glob >= 0:
            continue
        for alias in report["sequenceAliases"]:
            originals = [i for i,s in enumerate(seq) if struct.unpack_from("<H",s)[0] == alias["fallback"]]
            for variation,index in enumerate(originals):
                ts, vals = rows[index]
                out_ts, out_vals = rows[alias["firstSequence"]+variation]
                flags = alias["legacyFlags"]
                if flags == 0:
                    assert out_ts == ts and out_vals == vals
                elif flags == 1:
                    start,end = pair(seq[index],4)
                    assert out_ts == [end-start-t for t in reversed(ts)] and out_vals == vals[::-1]
                elif flags == 3:
                    assert out_ts == ([0] if width and ts else [])
                    assert out_vals == (vals[-1:] if width else [])
    lookup = shorts(b"".join(array(b,36,2)))
    for alias in report["sequenceAliases"]:
        request = alias["request"]
        assert lookup[request] == alias["firstSequence"]
        assert struct.unpack_from("<H",converted[lookup[request]])[0] == request
    resource_by_index = {r["textureIndex"]: r for r in report["hardcodedResources"]}
    if target.stem == "HighElfFemale":
        # Independently identified regression: used opacity ~0.6 is static at classic t=0,
        # outside every clip. Assert its value survives rather than repeating a time-window filter.
        old_weights, new_weights = array(a,100,28), array(b,88,20)
        constants = []
        for old,new in zip(old_weights,new_weights):
            n,p = pair(old,12)
            nv,pv = pair(old,20)
            if n == nv == 1 and uints(a[p:p+4]) == [0]:
                value = a[pv:pv+2]
                constants.append(struct.unpack("<h",value)[0]/32767)
                nr,pr = pair(new,12)
                assert nr == len(converted)
                for i in range(nr):
                    nk,pk = pair(b,pr+i*8)
                    assert nk == 1 and b[pk:pk+2] == value
        assert any(abs(v-0.6) < 1e-4 for v in constants), constants
    for i,(old,new) in enumerate(zip(array(a,92,16),array(b,80,16))):
        assert old[:8] == new[:8]
        n,p = pair(old,8)
        nn,pp = pair(new,8)
        old_name, new_name = a[p:p+n], b[pp:pp+nn]
        if i in resource_by_index:
            assert old_name.decode().rstrip("\0") == resource_by_index[i]["source"]
            assert new_name.decode().rstrip("\0") == resource_by_index[i]["target"]
        else:
            assert old_name == new_name
    assert all(struct.unpack_from("<I",s,12)[0] & 0x130 for s in converted)
    assert report["splineLayoutValidation"]["status"] == "PASS"
    assert report["splineLayoutValidation"]["nonemptySplineTracks"] == spline_tracks
    assert not list(target.parent.glob("*.anim"))
    return dict(model=target.stem, source_sha256=report["sourceSha256"], files=report["files"],
                vertices=len(av), bones=len(ab), original_sequences=count, output_sequences=len(converted),
                sections=sections_count, tracks=len(all_tracks), exact_nonquaternion_keys=vector_keys,
                max_quaternion_error=max_quaternion_error, unsupported_semantics=report["unsupportedSemantics"],
                track_repairs=report["trackRepairs"], native_spline_tracks=spline_tracks, native_spline_keys=spline_keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT/"work/new-races-models/validation")
    parser.add_argument("--dotnet", default=os.environ.get("DOTNET", "dotnet"))
    parser.add_argument("--converter", type=Path, default=ROOT/"work/toolchains/new-races-model-converter/NewRacesModelConverter.dll")
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT/"work/new-races-models")
    assert not output.exists(), "Choose a fresh --output directory"
    results = []
    for name, path in MODELS:
        source = args.source_root/path
        ns = "Character\\Custom\\Turtle" + name
        outputs = []
        for iteration in (1,2):
            target = output/f"pass{iteration}"/name/(name+".m2")
            command = [args.dotnet, str(args.converter), "convert", "--source", str(source),
                       "--output", str(target), "--namespace", ns]
            process = subprocess.run(command, capture_output=True, text=True)
            assert process.returncode == 0, process.stderr
            outputs.append(target)
        report = validate(source,outputs[0])
        validate(source,outputs[1])
        first = {p.name:p.read_bytes() for p in outputs[0].parent.iterdir()}
        second = {p.name:p.read_bytes() for p in outputs[1].parent.iterdir()}
        assert first == second, "Nondeterministic model, skin, or report"
        refused = subprocess.run(command, capture_output=True, text=True)
        assert refused.returncode != 0 and "fresh" in refused.stderr
        assert second == {p.name:p.read_bytes() for p in outputs[1].parent.iterdir()}
        resources = json.loads(Path(str(outputs[0])+".report.json").read_text())["hardcodedResources"]
        if resources:
            mapped = output/"explicit-maps"/name/(name+".m2")
            command = [args.dotnet, str(args.converter), "convert", "--source", str(source),
                       "--output", str(mapped), "--namespace", ns]
            for resource in resources:
                command += ["--texture-map", resource["source"]+"="+ns+"\\Mapped\\"+resource["source"].split("\\")[-1]]
            process = subprocess.run(command,capture_output=True,text=True)
            assert process.returncode == 0, process.stderr
            validate(source,mapped)
            mapped_resources = json.loads(Path(str(mapped)+".report.json").read_text())["hardcodedResources"]
            assert all(r["target"].startswith(ns+"\\Mapped\\") for r in mapped_resources)
        # A replaceable type-8 string must never be accepted as a hardcoded dependency.
        invalid = output/"invalid-map"/name/(name+".m2")
        command = [args.dotnet,str(args.converter),"convert","--source",str(source),
                   "--output",str(invalid),"--namespace",ns,"--texture-map",
                   "unused-type8-name.blp="+ns+"\\unused.blp"]
        process = subprocess.run(command,capture_output=True,text=True)
        assert process.returncode != 0 and "Unused type-0" in process.stderr
        assert not invalid.exists()
        if report["track_repairs"]:
            # A different source identity must not inherit the allowlist even with the same bone numbers.
            changed = bytearray(source.read_bytes())
            n,p = pair(changed,8)
            assert n > 1
            changed[p] = ord('X') if changed[p] != ord('X') else ord('Y')
            variant = output/"unknown-source"/name/(name+".m2")
            variant.parent.mkdir(parents=True)
            variant.write_bytes(changed)
            rejected = variant.with_name("Rejected.m2")
            process = subprocess.run([args.dotnet,str(args.converter),"convert","--source",str(variant),
                                      "--output",str(rejected),"--namespace",ns],capture_output=True,text=True)
            assert process.returncode != 0 and "Unsafe nonempty spline payload" in process.stderr
            assert not rejected.exists()
        report["deterministic"] = True
        results.append(report)
        print(name, "PASS", "vertices", report["vertices"], "quaternion error",report["max_quaternion_error"])
    # Real source cameras are empty spline tracks. Exercise actual native triple layouts
    # using a derived fixture, never changing the original extracted model.
    fixture = bytearray((args.source_root/MODELS[2][1]).read_bytes())
    cameras,camera_offset = pair(fixture,292)
    assert cameras > 0
    sequence = array(fixture,28,68)[0]
    start,end = pair(sequence,4)
    for offset,width,interpolation in [(16,36,2),(56,36,3),(96,12,2)]:
        times_offset = len(fixture)
        fixture.extend(struct.pack("<II",start,end))
        values_offset = len(fixture)
        fixture.extend(struct.pack("<"+"f"*(2*width//4),*[0.125*(i+1) for i in range(2*width//4)]))
        struct.pack_into("<HhIIIIII",fixture,camera_offset+offset,interpolation,-1,0,0,2,times_offset,2,values_offset)
    fixture_source = output/"native-spline-fixture"/"Source.m2"
    fixture_source.parent.mkdir(parents=True)
    fixture_source.write_bytes(fixture)
    fixture_target = fixture_source.with_name("NativeSpline.m2")
    process = subprocess.run([args.dotnet,str(args.converter),"convert","--source",str(fixture_source),
                              "--output",str(fixture_target),"--namespace",r"Character\Custom\TurtleSplineFixture"],
                             capture_output=True,text=True)
    assert process.returncode == 0, process.stderr
    fixture_validation = validate(fixture_source,fixture_target)
    assert fixture_validation["native_spline_tracks"] == 3 and fixture_validation["native_spline_keys"] >= 6
    print("Native spline fixture PASS",fixture_validation["native_spline_keys"],"triple-coefficient keys")
    summary = dict(schema=1, native_runtime="NOT RUN", models=results, native_spline_fixture=fixture_validation)
    (output/"validation.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(output/"validation.json")


if __name__ == "__main__":
    main()
