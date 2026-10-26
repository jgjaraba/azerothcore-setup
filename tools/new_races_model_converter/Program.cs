// SPDX-License-Identifier: GPL-2.0-only
// Project driver for M2Lib by Koward and its credited contributors.
// See patches/third-party/m2lib/README.md and the pinned upstream LICENSE.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;
using M2Lib.m2;
using M2Lib.types;

internal static class Program
{
    const string Pin = "18c085632b12e8a19da40df3459f1f4620a30972";
    static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };
    static string Hash(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    static uint U32(byte[] b, int o) => BitConverter.ToUInt32(b, o);
    static int Main(string[] args)
    {
        try
        {
            if (args.Length == 1 && args[0] == "--help")
            {
                Console.WriteLine("convert --source INPUT.m2 --output FRESH.m2 --namespace 'Character\\Custom\\Turtle...' [--texture-map OLD=NEW ...]\n" +
                    "Writes M2 v264, adjacent NN.skin files and OUTPUT.m2.report.json. Maps affect type-0 textures only.\n" +
                    "Experimental client-stage conversion; native runtime NOT RUN. GPL-2.0; M2Lib by Koward.");
                return 0;
            }
            if (args.Length == 0 || args[0] != "convert") throw new ArgumentException("Expected convert; use --help.");
            var options = new Dictionary<string, string>();
            var maps = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 1; i < args.Length; i += 2)
            {
                if (i + 1 == args.Length) throw new ArgumentException("Missing option value.");
                if (args[i] == "--texture-map")
                {
                    var split = args[i + 1].Split('=', 2);
                    if (split.Length != 2) throw new ArgumentException("Texture map must be OLD=NEW.");
                    maps.Add(ClientPath(split[0]), ClientPath(split[1]));
                }
                else if (new[] { "--source", "--output", "--namespace" }.Contains(args[i])) options.Add(args[i], args[i + 1]);
                else throw new ArgumentException("Unknown option: " + args[i]);
            }
            ConvertModel(Path.GetFullPath(options["--source"]), Path.GetFullPath(options["--output"]), ClientPath(options["--namespace"]), maps);
            return 0;
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("Conversion failed: " + e);
            return 1;
        }
    }

    static string ClientPath(string value)
    {
        value = value.Replace('/', '\\');
        if (!Regex.IsMatch(value, @"^[A-Za-z0-9_ .-]+(\\[A-Za-z0-9_ .-]+)*$") ||
            value.Split('\\').Any(p => p == "." || p == "..")) throw new ArgumentException("Invalid client path: " + value);
        return value;
    }

    static void ConvertModel(string source, string output, string ns, Dictionary<string, string> maps)
    {
        if (!ns.StartsWith("Character\\Custom\\", StringComparison.OrdinalIgnoreCase))
            throw new ArgumentException("Namespace must be below Character\\Custom.");
        if (!output.EndsWith(".m2", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Output must end in .m2.");
        byte[] original = File.ReadAllBytes(source);
        if (original.Length < 324 || System.Text.Encoding.ASCII.GetString(original, 0, 4) != "MD20" || U32(original, 4) != 256)
            throw new ArgumentException("Only classic MD20 v256 input is supported.");
        // Reject unimplemented flipbooks, ribbons and particles instead of emitting a misleading conversion.
        foreach (int offset in new[] { 108, 308, 316 })
            if (U32(original, offset) != 0) throw new NotSupportedException("Nonempty classic block at header offset " + offset);
        var model = new M2();
        using (var reader = new BinaryReader(File.OpenRead(source))) model.Load(reader);
        model.PreserveSourceLookups = true;
        var destinations = new List<string> { output, output + ".report.json" };
        for (int i = 0; i < model.Views.Count; i++) destinations.Add(M2SkinProfile.SkinFileName(output, i));
        foreach (var path in destinations)
            if (File.Exists(path) || Directory.Exists(path)) throw new IOException("Output must be fresh: " + path);

        var issues = new List<object>();
        var tracks = Tracks(model).ToArray();
        var repairs = RepairHelperTracks(model, original, issues);
        int splineTracks = ValidateSplineLayouts(model, tracks);
        int originalSequences = model.Sequences.Count;
        // Classic has no external animation files. Do not reinterpret a legacy 0x40 as a Wrath alias.
        foreach (var seq in model.Sequences)
        {
            seq.Flags = (seq.Flags & ~M2Sequence.SequenceFlags.HasNext) | M2Sequence.SequenceFlags.Stored;
            seq.AliasNext = 0;
        }
        var aliases = MaterializeFallbacks(model, original, tracks, originalSequences, issues);
        ValidateSplineLayouts(model, tracks);
        var resources = new List<object>();
        var usedMaps = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var targets = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        for (int i = 0; i < model.Textures.Count; i++)
        {
            var tex = model.Textures[i];
            string old = tex.Name;
            if (tex.Type != M2Texture.TextureType.None || string.IsNullOrEmpty(old)) continue;
            string normalized = ClientPath(old);
            string target;
            if (maps.TryGetValue(normalized, out target)) usedMaps.Add(normalized);
            else target = ns + "\\Textures\\" + normalized.Split('\\').Last();
            if (!target.StartsWith(ns + "\\", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Type-0 texture target escapes namespace: " + target);
            if (targets.TryGetValue(target, out string previous) && !StringComparer.OrdinalIgnoreCase.Equals(previous, normalized))
                throw new ArgumentException("Texture basename collision; supply distinct --texture-map targets: " + target);
            targets[target] = normalized;
            tex.Name = target;
            resources.Add(new { textureIndex = i, type = 0, source = old, target });
        }
        if (maps.Keys.Any(k => !usedMaps.Contains(k))) throw new ArgumentException("Unused type-0 texture map: " + string.Join(", ", maps.Keys.Where(k => !usedMaps.Contains(k))));
        foreach (var view in model.Views)
        foreach (var section in view.Submeshes)
        {
            var positions = view.Indices.Skip(section.StartVertex).Take(section.NVertices).Select(i => model.GlobalVertexList[i].Position).ToArray();
            if (positions.Length == 0) throw new NotSupportedException("Empty skin section.");
            float x = (positions.Min(p => p.X) + positions.Max(p => p.X)) / 2;
            float y = (positions.Min(p => p.Y) + positions.Max(p => p.Y)) / 2;
            float z = (positions.Min(p => p.Z) + positions.Max(p => p.Z)) / 2;
            section.CenterBoundingBox = new C3Vector(x, y, z);
            section.Radius = (float)Math.Sqrt(positions.Max(p => (p.X-x)*(p.X-x) + (p.Y-y)*(p.Y-y) + (p.Z-z)*(p.Z-z)));
        }
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        using (var writer = new BinaryWriter(new FileStream(output, FileMode.CreateNew))) model.Save(writer, M2.Format.LichKing);
        var files = destinations.Where(p => p != output + ".report.json").Select(p => new {
            name = Path.GetFileName(p), bytes = new FileInfo(p).Length, sha256 = Hash(File.ReadAllBytes(p)) }).ToArray();
        var report = new {
            schema = 1, converter = "classic256-wrath264-source-preserving", m2libRevision = Pin,
            sourceSha256 = Hash(original), sourceVersion = 256, targetVersion = 264, clientNamespace = ns,
            sourceSequences = originalSequences, outputSequences = model.Sequences.Count,
            vertices = model.GlobalVertexList.Count, bones = model.Bones.Count, skins = model.Views.Count,
            embeddedAnimations = true, externalAnimations = Array.Empty<string>(),
            hardcodedResources = resources, sequenceAliases = aliases, unsupportedSemantics = issues,
            trackRepairs = repairs,
            splineLayoutValidation = new { status = "PASS", nonemptySplineTracks = splineTracks, policy = "Only native triple-coefficient camera track types; reject other nonempty spline payloads." },
            fullySupported = issues.Count == 0, nativeRuntime = "NOT RUN", stage = "experimental-manual-client-test-required",
            files
        };
        string json = JsonSerializer.Serialize(report, JsonOptions) + "\n";
        File.WriteAllText(output + ".report.json", json);
        Console.Write(json);
    }

    static List<object> RepairHelperTracks(M2 model, byte[] original, List<object> issues)
    {
        string sourceHash = Hash(original);
        // Pin both complete source identity and individual payload identity. Other ambiguous inputs fail closed.
        var allowlist = new[] {
            (source: "8dab731974fbaaa12201f81803726a32e5fd72b2153a366c64b08f7127643e42", bone: 80, track: "Scale", count: 1, values: "d6df51bc95c02dbbffb63bab802170482e2a7982f21fddbd52e71fd2abf017ff"),
            (source: "8dab731974fbaaa12201f81803726a32e5fd72b2153a366c64b08f7127643e42", bone: 126, track: "Translation", count: 2, values: "199089387c3962b0c6e26b217d35b6e9187f9fe0dd4471c68ec5003c7e0d9976"),
            (source: "ae5d9f09c7ec560f6518a7a62fa27ca079b2b051a522a11fee84d2983fb9633f", bone: 90, track: "Scale", count: 1, values: "d6df51bc95c02dbbffb63bab802170482e2a7982f21fddbd52e71fd2abf017ff")
        };
        var result = new List<object>();
        foreach (var entry in allowlist.Where(e => e.source == sourceHash))
        {
            int trackIndex = Array.IndexOf(new[] { "Translation", "Rotation", "Scale" }, entry.track);
            int raw = checked((int)U32(original, 56) + entry.bone * 108 + 12 + trackIndex * 28);
            int nt = checked((int)U32(original, raw + 12)), pt = checked((int)U32(original, raw + 16));
            int nv = checked((int)U32(original, raw + 20)), pv = checked((int)U32(original, raw + 24));
            string valuesHash = Hash(original.AsSpan(pv, checked(nv * 12)).ToArray());
            if (BitConverter.ToUInt16(original, raw) != 2 || nv != entry.count || nt != nv || valuesHash != entry.values)
                throw new InvalidDataException("Allowlisted helper track provenance mismatch.");
            object audit = AuditBoneReferences(model, original, entry.bone);
            var bone = model.Bones[entry.bone];
            if (entry.track == "Scale") bone.Scale.InterpolationType = M2Track<C3Vector>.InterpolationTypes.Linear;
            else bone.Translation.InterpolationType = M2Track<C3Vector>.InterpolationTypes.Linear;
            result.Add(new { code = "allowlisted-helper-linearization", bone = entry.bone, track = entry.track,
                sourceInterpolation = 2, targetInterpolation = 1, sourceSha256 = sourceHash,
                sourceTimestampCount = nt, sourceValueCount = nv, sourceValueBytesSha256 = valuesHash,
                sourceTimestampBytesSha256 = Hash(original.AsSpan(pt, checked(nt * 4)).ToArray()),
                reason = "Classic payload has one vector per timestamp, not Wrath's three spline coefficients. Preserve all keys/times; linear interpolation bounds native reads. No guessed tangents or skeleton changes.",
                sourceCurve = "Approximation limited to this explicit helper track; source interpolation-2 semantics unknown.", references = audit });
            issues.Add(new { code = "helper-source-curve-approximation", bone = entry.bone, track = entry.track,
                sourceInterpolation = 2, targetInterpolation = 1,
                disposition = "Bounded, valid linear payload with original keys and times. Original helper curvature is not established; manual preview remains unaccepted / NOT RUN." });
        }
        return result;
    }

    static object AuditBoneReferences(M2 model, byte[] source, int bone)
    {
        HashSet<int> Ancestors(int root)
        {
            var chain = new HashSet<int>();
            while (root != -1)
            {
                if (root < 0 || root >= model.Bones.Count || !chain.Add(root)) throw new InvalidDataException("Invalid/cyclic bone parent chain.");
                root = model.Bones[root].ParentBone;
            }
            return chain;
        }
        var ancestry = Enumerable.Range(0, model.Bones.Count).Select(Ancestors).ToArray();
        var weighted = new HashSet<int>();
        int count = checked((int)U32(source, 68)), offset = checked((int)U32(source, 72));
        for (int i = 0; i < count; i++)
        for (int j = 0; j < 4; j++)
            if (source[offset + i * 48 + 12 + j] != 0) weighted.Add(source[offset + i * 48 + 16 + j]);
        bool Depends(int root) => root != -1 && Ancestors(root).Contains(bone);
        int[] weightedDependents = weighted.Where(Depends).OrderBy(i => i).ToArray();
        var attachments = model.Attachments.Select((a, i) => new { index = i, id = a.Id, root = checked((int)a.Bone) }).Where(a => Depends(a.root)).ToArray();
        var events = model.Events.Select((e, i) => new { index = i, identifier = e.Identifier, root = (int)e.Bone }).Where(e => Depends(e.root)).ToArray();
        var lights = model.Lights.Select((l, i) => new { index = i, root = (int)l.Bone }).Where(l => Depends(l.root)).ToArray();
        var keys = model.Bones.Select((b, i) => new { bone = i, keyBoneId = (int)b.KeyBoneId }).Where(b => b.keyBoneId >= 0 && Depends(b.bone)).ToArray();
        var keyLookup = model.SourceKeyBoneLookup.Select((b, i) => new { slot = i, root = (int)b }).Where(b => Depends(b.root)).ToArray();
        bool referenced = weightedDependents.Length + attachments.Length + events.Length + lights.Length + keys.Length + keyLookup.Length != 0;
        return new { directlyWeighted = weighted.Contains(bone),
            directChildren = Enumerable.Range(0, model.Bones.Count).Where(i => model.Bones[i].ParentBone == bone).ToArray(),
            descendants = Enumerable.Range(0, model.Bones.Count).Where(i => i != bone && ancestry[i].Contains(bone)).ToArray(),
            weightedBoneParentClosure = weighted.SelectMany(i => Ancestors(i)).Distinct().OrderBy(i => i).ToArray(),
            weightedDependents, attachments, events, lights, keyBones = keys, keyBoneLookup = keyLookup,
            cameras = new { count = model.Cameras.Count, boneBindings = "None: classic/v264 cameras are model-space, with no bone index." },
            particles = new { count = model.Particles.Count, boneBindings = "Empty; nonempty emitters are rejected before conversion." },
            ribbons = new { count = model.Ribbons.Count, boneBindings = "Empty; nonempty emitters are rejected before conversion." },
            referencedThroughAnyParentClosure = referenced, audit = "All weighted bones, descendants, attachment/event/light roots and key-bone roots/lookups; full ancestry traversal without bone-flag pruning." };
    }

    static int ValidateSplineLayouts(M2 model, object[] tracks)
    {
        var nativeSplines = new HashSet<object>();
        foreach (var camera in model.Cameras)
        {
            nativeSplines.Add(camera.Positions); // C33Matrix = value/in/out C3Vector (36 bytes).
            nativeSplines.Add(camera.TargetPositions);
            nativeSplines.Add(camera.Roll); // C3Vector = value/in/out float (12 bytes).
        }
        int count = 0;
        foreach (object track in tracks)
        {
            var type = track.GetType();
            int interpolation = System.Convert.ToInt32(type.GetProperty("InterpolationType").GetValue(track));
            if (interpolation < 2) continue;
            var times = (IList)type.GetProperty("Timestamps").GetValue(track);
            if (!times.Cast<IList>().Any(row => row.Count != 0)) continue;
            if (interpolation > 3 || !nativeSplines.Contains(track))
                throw new NotSupportedException("Unsafe nonempty spline payload: " + type + "; only explicitly pinned helper repairs or native triple-coefficient camera tracks are supported.");
            var values = (IList)type.GetProperty("Values").GetValue(track);
            if (times.Count != values.Count) throw new InvalidDataException("Spline row count mismatch.");
            for (int i = 0; i < times.Count; i++)
                if (((IList)times[i]).Count != ((IList)values[i]).Count) throw new InvalidDataException("Spline timestamp/coefficient-key count mismatch.");
            count++;
        }
        return count;
    }

    // Enumerate every public track on all animated model blocks, including event-only tracks.
    static IEnumerable<object> Tracks(M2 model)
    {
        foreach (var collection in model.GetType().GetProperties().Select(p => p.GetValue(model)).OfType<IEnumerable>())
        foreach (var item in collection)
        {
            if (item == null || !item.GetType().Namespace.StartsWith("M2Lib.m2")) continue;
            foreach (var prop in item.GetType().GetProperties())
            {
                // In v256 and v264 the field of view is a scalar, not an animated track.
                if (item is M2Camera && prop.Name == "FieldOfView") continue;
                if (prop.PropertyType == typeof(M2TrackBase) ||
                    (prop.PropertyType.IsGenericType && prop.PropertyType.GetGenericTypeDefinition() == typeof(M2Track<>)))
                    yield return prop.GetValue(item);
            }
        }
    }

    static List<object> MaterializeFallbacks(M2 model, byte[] source, object[] tracks, int count, List<object> issues)
    {
        int records = checked((int)U32(source, 44)), offset = checked((int)U32(source, 48));
        if (offset < 0 || (long)offset + records * 4L > source.Length) throw new InvalidDataException("Invalid playable lookup.");
        var result = new List<object>();
        for (int request = 0; request < records; request++)
        {
            if (model.Sequences.Take(count).Any(s => s.AnimationId == request)) continue;
            ushort fallback = BitConverter.ToUInt16(source, offset + request * 4);
            ushort flags = BitConverter.ToUInt16(source, offset + request * 4 + 2);
            int[] originals = Enumerable.Range(0, count).Where(i => model.Sequences[i].AnimationId == fallback).ToArray();
            if (originals.Length == 0 || (flags != 0 && flags != 1 && flags != 3))
            {
                issues.Add(new { code = "playable-fallback-unresolved", request, fallback, flags });
                continue;
            }
            int start = model.Sequences.Count;
            foreach (int index in originals)
            {
                var old = model.Sequences[index];
                // Copy the complete sequence record, including private padding, without sharing mutable track headers.
                using var bytes = new MemoryStream();
                using (var writer = new BinaryWriter(bytes, System.Text.Encoding.UTF8, true)) old.Save(writer, M2.Format.LichKing);
                bytes.Position = 0;
                var seq = new M2Sequence();
                using (var reader = new BinaryReader(bytes, System.Text.Encoding.UTF8, true)) seq.Load(reader, M2.Format.LichKing);
                seq.AnimationId = checked((ushort)request);
                seq.NextAnimation = old.NextAnimation < 0 ? (short)-1 : checked((short)(start + Array.IndexOf(originals, (int)old.NextAnimation)));
                if (old.NextAnimation >= 0 && !originals.Contains(old.NextAnimation)) throw new InvalidDataException("Cross-animation variation chain.");
                if (flags == 3) seq.Length = 1;
                foreach (object track in tracks) DuplicateTrack(track, index, model.Sequences.Count, old.Length, flags, issues, request);
                model.Sequences.Add(seq);
            }
            result.Add(new { request, fallback, legacyFlags = flags, firstSequence = start, variations = originals.Length,
                transformation = flags == 1 ? "reverse-keys-and-local-time" : flags == 3 ? "hold-last-key" : "copy-source-clip" });
        }
        return result;
    }

    static void DuplicateTrack(object track, int from, int target, uint length, ushort flags, List<object> issues, int request)
    {
        Type type = track.GetType();
        if ((short)type.GetProperty("GlobalSequence").GetValue(track) >= 0) return;
        var times = (IList)type.GetProperty("Timestamps").GetValue(track);
        if (times.Count == 0) return;
        var valuesProp = type.GetProperty("Values");
        IList values = valuesProp == null ? null : (IList)valuesProp.GetValue(track);
        if (from >= times.Count) throw new InvalidDataException($"Track {type} request={request} source={from} target={target} rows={times.Count} global={type.GetProperty("GlobalSequence").GetValue(track)}");
        var sourceTimes = (IList)times[from];
        IList sourceValues = values == null ? null : (IList)values[from];
        var newTimes = new M2Array<uint>();
        IList newValues = sourceValues == null ? null : (IList)Activator.CreateInstance(sourceValues.GetType());
        int interpolation = System.Convert.ToInt32(type.GetProperty("InterpolationType").GetValue(track));
        if (flags != 0 && interpolation > 1 && sourceTimes.Count > 0)
            issues.Add(new { code = "transformed-spline-fallback-unresolved", request, interpolation, legacyFlags = flags });
        if (flags == 3)
        {
            if (sourceValues != null && sourceTimes.Count > 0)
            {
                newTimes.Add(0);
                newValues.Add(sourceValues[sourceValues.Count - 1]);
            }
            // A held pose must not replay one-shot events.
        }
        else
        {
            var indexes = Enumerable.Range(0, sourceTimes.Count);
            if (flags == 1) indexes = indexes.Reverse();
            foreach (int i in indexes)
            {
                newTimes.Add(flags == 1 ? checked(length - (uint)sourceTimes[i]) : (uint)sourceTimes[i]);
                newValues?.Add(sourceValues[i]);
            }
        }
        if (times.Count != target) throw new InvalidDataException("Unexpected per-sequence track count.");
        times.Add(newTimes);
        values?.Add(newValues);
    }
}
