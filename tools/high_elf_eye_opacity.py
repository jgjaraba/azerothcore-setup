"""Pinned Wrath High Elf postprocess: native 6553 eye weight, no other edits.

The converter intermediate and frozen NEW archive remain source-preserved.
Whole-file input/output pins also protect blocks not traversed by this parser.
"""
import hashlib
import struct
from bisect import bisect_left

from high_elf_eye_selectors import eye_models, require

PINS = {
    'Male': ('13c646380a76d0b54c3ea468f8273eb086fc24c0cdbfd978f83a9b50f31f1738',
             '1d89037e33959eef4ee1f6973bea64231c09fa977f6427b556586b6d6fa0f751', 409, 816, 1624),
    'Female': ('91a8f99f2127818d31180d0ff6408c0abf68ae0ee8301bd635133f68503dcf83',
               'c1be1f8c45c4bebc951d20508c7ca660318a461db5ff9a0e3c14cf32a3747c1a', 410, 410, 820),
}
SKIN_PINS = {'Male': '68b719e4c0766da91747b71f84166f685f5414202bc2f1b458aca38bd33e97b6',
             'Female': 'de666b9baa84d1abcfc1020b42777a8a087319694d6135d992c505a29acea21d'}


def member(sex):
    return f'Character/Custom/TurtleHighElf/{sex}/TurtleHighElf{sex}.m2'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalize_eye_opacity(model, skin, sex):
    require(sex in PINS, 'Unknown High Elf sex')
    original, final, tracks, keys, delta = PINS[sex]
    source_sha = sha(model)
    require(source_sha in (original, final), 'Unknown High Elf opacity model/layout')
    base = member(sex)[:-3]
    eye_models({base+'.m2': model, base+'00.skin': skin}, sexes=(sex,))
    require(sha(skin) == SKIN_PINS[sex], 'Unknown High Elf opacity SKIN/layout')
    protected = [(0, 304)]

    def array(offset, width):
        require(0 <= offset <= len(model)-8, 'Opacity array header outside M2')
        count, start = struct.unpack_from('<2I', model, offset)
        require((not count or start >= 304) and start+count*width <= len(model),
                'Opacity array outside M2')
        if count:
            protected.append((start, start+count*width))
        return count, start

    # Static M2 arrays, including full vertex records (XYZ/bones/normal/UV).
    for offset, width in ((8, 1), (20, 4), (28, 64), (36, 2), (52, 2),
                          (60, 48), (80, 16), (104, 2), (112, 4), (120, 2),
                          (128, 2), (136, 2), (144, 2), (152, 2), (216, 2),
                          (224, 12), (232, 12), (248, 2), (280, 2)):
        array(offset, width)

    def protect_track(pos, width):
        interpolation, _ = struct.unpack_from('<hh', model, pos)
        nt, times = array(pos+4, 8)
        nk, vals = array(pos+12, 8)
        require(nt == nk, 'Other animation descriptor count mismatch')
        for i in range(nt):
            tn, _ = array(times+i*8, 4)
            kn, _ = array(vals+i*8, width*(3 if interpolation in (2, 3) else 1))
            require(tn == kn, 'Other animation time/key count mismatch')

    # Check unrelated nested animations too, rather than only weight0/2. Their
    # data must never alias the bytes we are about to normalize.
    n, start = array(44, 88)
    for i in range(n):
        for offset, width in ((16, 12), (36, 8), (56, 12)):
            protect_track(start+i*88+offset, width)
    n, start = array(72, 40)
    for i in range(n):
        protect_track(start+i*40, 12)
        protect_track(start+i*40+20, 2)
    n, start = array(96, 60)
    for i in range(n):
        for offset, width in ((0, 12), (20, 8), (40, 12)):
            protect_track(start+i*60+offset, width)
    n, start = array(240, 40)
    for i in range(n):
        protect_track(start+i*40+20, 1)
    n, start = array(256, 36)
    for i in range(n):
        nt, times = array(start+i*36+28, 8)
        for j in range(nt):
            array(times+j*8, 4)
    n, start = array(272, 100)
    for i in range(n):
        for offset, width in ((16, 12), (48, 12), (80, 4)):
            protect_track(start+i*100+offset, width)
    for offset in (264, 288, 296):
        require(struct.unpack_from('<I', model, offset)[0] == 0, 'Unexpected light/ribbon/particle blocks')
    n, start = array(80, 16)
    for i in range(n):
        array(start+i*16+8, 1)  # named texture strings
    count, weight_start = array(88, 20)
    require(count == 3, 'Expected three texture-weight tracks')
    combo_count, combo_start = array(144, 2)
    combos = struct.unpack_from(f'<{combo_count}H', model, combo_start)
    require(combo_count > 1 and combos[1] == 1, 'Eye weight combo1 must resolve track1')
    n, start = struct.unpack_from('<2I', skin, 36)
    require(start >= 48 and start+n*24 <= len(skin), 'Eye batch range outside SKIN')
    owners = []
    for i in range(n):
        batch = struct.unpack_from('<BBhHHhHHHHHHH', skin, start+i*24)
        require(batch[11] < combo_count, 'Invalid batch weight combo')
        if combos[batch[11]] == 1:
            owners.append((i, batch[3], batch[11]))
    section = 53 if sex == 'Male' else 5
    require(owners == [(section, section, 1)], 'Weight track1 is not eye-exclusive')
    values = []
    other = []
    for track in range(count):
        pos = weight_start+track*20
        expected = (0, -1) if track < 2 else (1, 4 if sex == 'Male' else 0)
        require(struct.unpack_from('<hh', model, pos) == expected, 'Unexpected weight interpolation/global sequence')
        nt, times = array(pos+4, 8)
        nv, vals = array(pos+12, 8)
        require(nt == nv == (tracks if track < 2 else 1), 'Unexpected weight animation track count')
        for i in range(nv):
            tn, ts = array(times+i*8, 4)
            # Key ranges are separately checked for overlaps below.
            kn, ks = struct.unpack_from('<2I', model, vals+i*8)
            require(tn == kn and ks >= 304 and ks+kn*2 <= len(model), 'Invalid weight key range/count')
            target = values if track == 1 else other
            target.extend(range(ks, ks+kn*2, 2))
    require(len(values) == len(set(values)) == keys, 'Aliased/unexpected eye key count')
    allowed = {p+j for p in values for j in (0, 1)}
    require(not allowed.intersection(p+j for p in other for j in (0, 1)), 'Eye keys overlap other weights')
    ordered = sorted(allowed)
    for a, b in protected:
        i = bisect_left(ordered, a)
        require(i == len(ordered) or ordered[i] >= b, 'Eye keys overlap another M2 block')
    before = [struct.unpack_from('<h', model, p)[0] for p in values]
    require(set(before) <= ({6553, 32767} if sex == 'Male' else {6553, 19660}), 'Unexpected eye values')
    result = bytearray(model)
    for p in values:
        struct.pack_into('<h', result, p, 6553)
    result = bytes(result)
    changed = [i for i, (a, b) in enumerate(zip(model, result)) if a != b]
    require(set(changed) <= allowed and len(changed) == (delta if source_sha == original else 0),
            'Non-allowlisted opacity delta')
    require(sha(result) == final, 'Unexpected final High Elf opacity hash')
    return result, {'source_sha256': source_sha, 'final_sha256': final, 'track': 1,
                    'animation_tracks': tracks, 'keys': keys, 'value': 6553,
                    'changed_bytes': len(changed), 'key_offsets': values,
                    'all_other_bytes_exact': True}
