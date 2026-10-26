#!/usr/bin/env python3
"""Build a fresh pinned native-3.3.5 GlueXML payload (not an MPQ/install)."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from patch_new_races_client import CUSTOM_GLUE_SHA, ROOT, require, safe_output, sha

ASSETS = ROOT / 'tools/new-races-ui'
NATIVE_PINS = {
    'CharacterCreate.lua': 'f041474fa333e063bc8b30919c9a85ddc663e86e799f59505be2d911b90cff73',
    'CharacterCreate.xml': '5492a4dccfc414fe1a7e8bb3f3b994d2382e65e182759a082c6d5c212cb13a1d',
    'GlueParent.lua': '503d2363655a4b3145332a4024ee24240a0ab04b87724b6a6b0ec97fd75d8d31',
}
TURTLE_PINS = {
    'CharacterCreate.lua': '322370bd6987df50e27db5e231648b04656da28a123e5544fc87a872c4c3b6c1',
    'RaceIcons.blp': 'ac9fcae5b16d096d5308ad528fe7427f464cee0df89e7d7d1cd9d407a754d6f7',
}
PICKER_IDS = [1, 3, 4, 7, 11, 22, 2, 5, 6, 8, 10, 23]
NS = '{http://www.blizzard.com/wow/ui/}'


def pinned(raw, digest, label):
    require(sha(raw) == digest, f'Unknown baseline hash: {label}: {sha(raw)}')
    return raw


def extract(mpq, archive, member):
    """Existing project read-only StormLib CLI; no Python package dependency."""
    with tempfile.TemporaryDirectory(prefix='new-races-extract-') as temp:
        dest = Path(temp) / 'member'
        proc = subprocess.run([str(mpq), 'extract-one', str(archive), member, str(dest)],
                              capture_output=True, text=True)
        if proc.returncode:
            # Only a genuine absent member is a candidate miss; corrupt archives fail.
            require('file not found' in proc.stderr.lower() or 'cannot open file' in proc.stderr.lower(),
                    f'MPQ extraction failed: {archive}: {proc.stderr.strip()}')
            return None
        require(dest.exists(), 'MPQ extractor did not write member')
        return dest.read_bytes()


def load_sources(native_root, turtle_archive, mpq, source_dir=None, turtle_dir=None,
                 glueparent_archive=None):
    provenance = {}
    sources = {}
    for name, digest in NATIVE_PINS.items():
        member = 'Interface\\GlueXML\\' + name
        if source_dir:
            raw = (source_dir / name).read_bytes()
            provenance[name] = {'source': str(source_dir / name)}
        else:
            if name == 'GlueParent.lua' and glueparent_archive:
                candidates = [glueparent_archive]
            elif name == 'GlueParent.lua':
                candidates = [native_root / 'Data/enUS' / a for a in
                              ('patch-enUS-3.MPQ', 'patch-enUS-2.MPQ', 'patch-enUS.MPQ', 'locale-enUS.MPQ')]
            else:
                # Explicit researched baseline, not a claim about active MPQ priority.
                candidates = [native_root / 'Data/enUS/patch-enUS-2.MPQ']
            observations = []
            raw = None
            for archive in candidates:
                require(archive.is_file(), f'Missing baseline archive: {archive}')
                candidate = extract(mpq, archive, member)
                observations.append({'archive': str(archive), 'sha256': sha(candidate) if candidate is not None else None})
                if raw is None and candidate is not None:
                    raw = candidate
            require(raw is not None, f'No baseline member: {name}')
            provenance[name] = {'candidates_highest_first': observations}
        sources[name] = pinned(raw, digest, name)
        provenance[name]['sha256'] = digest
    turtle = {}
    for name, digest in TURTLE_PINS.items():
        if turtle_dir:
            raw = (turtle_dir / name).read_bytes()
            origin = str(turtle_dir / name)
        else:
            member = (r'Interface\GlueXML\CharacterCreate.lua' if name.endswith('.lua') else
                      r'Interface\Glues\CharacterCreate\UI-CHARACTERCREATE-RACES.BLP')
            raw = extract(mpq, turtle_archive, member)
            require(raw is not None, f'Missing Turtle asset: {member}')
            origin = str(turtle_archive) + ':' + member
        turtle[name] = pinned(raw, digest, 'Turtle ' + name)
        provenance['Turtle/' + name] = {'source': origin, 'sha256': digest}
    return sources, turtle, provenance


def replace_once(text, old, new):
    require(text.count(old) == 1, f'Expected one source anchor: {old[:100]}')
    return text.replace(old, new, 1)


def icon_coordinates(turtle_lua):
    coords = {}
    for target, source in [('TURTLEHIGHELF', 'BLOODELF'), ('TURTLEGOBLIN', 'GOBLIN')]:
        for sex in ('MALE', 'FEMALE'):
            key = source + '_' + sex
            match = re.search(r'\["' + key + r'"\]\s*=\s*\{([^}]+)\}', turtle_lua)
            require(match is not None, f'Missing source icon coordinates: {key}')
            numbers = [float(n.strip()) for n in match[1].split(',')]
            require(len(numbers) == 4 and all(0 <= n <= 1 for n in numbers) and
                    numbers[0] < numbers[1] and numbers[2] < numbers[3], 'Invalid source UV table')
            coords[target + '_' + sex] = numbers
    return coords


def transform(sources, turtle):
    for name, digest in NATIVE_PINS.items():
        pinned(sources[name], digest, name)
    for name, digest in TURTLE_PINS.items():
        pinned(turtle[name], digest, 'Turtle ' + name)
    lua = sources['CharacterCreate.lua'].decode('utf-8').replace('\r\n', '\n')
    lua = replace_once(lua, 'MAX_RACES = 10;', 'MAX_RACES = 12;')
    for suffix in ('NormalTexture', 'PushedTexture'):
        line = f'\t\t_G["CharacterCreateRaceButton"..index.."{suffix}"]:SetTexCoord'
        lua = replace_once(lua, line,
                           f'\t\tNewRaces_SetIcon(_G["CharacterCreateRaceButton"..index.."{suffix}"], select(i+1, ...));\n' + line)
    portrait = '\tCharacterCreateRaceIcon:SetTexCoord(coords[1], coords[2], coords[3], coords[4]);'
    require(lua.count(portrait) == 2, 'Expected both native sex/race portrait refreshes')
    lua = lua.replace(portrait, '\tNewRaces_SetIcon(CharacterCreateRaceIcon, fileString);\n' + portrait)
    coords = icon_coordinates(turtle['CharacterCreate.lua'].decode('utf-8'))
    extension = (ASSETS / 'NewRaces.lua').read_text()
    assignments = '\n'.join(f'RACE_ICON_TCOORDS["{key}"] = {{{", ".join(str(n) for n in value)}}};'
                            for key, value in coords.items())
    lua += '\n' + replace_once(extension, '@RACE_COORDINATES@', assignments)

    xml = sources['CharacterCreate.xml'].decode('utf-8').replace('\r\n', '\n')
    pattern = r'<CheckButton name="CharacterCreateRaceButton\d+"\s+inherits="CharacterCreateRaceButtonTemplate" id="\d+">.*?</CheckButton>'
    matches = list(re.finditer(pattern, xml, re.S))
    require(len(matches) == 10, 'Expected ten original race buttons')
    require([int(re.search(r'id="(\d+)"', m[0])[1]) for m in matches] == list(range(1, 11)), 'Wrong stock button IDs')
    buttons = []
    for i in range(1, 13):
        x, y = (-50 if i <= 6 else 50), -61 - ((i-1) % 6)*51
        buttons.append(f'<CheckButton name="CharacterCreateRaceButton{i}" inherits="CharacterCreateRaceButtonTemplate" id="{i}">\n'
                       f'  <Anchors><Anchor point="TOP" relativePoint="TOP" x="{x}" y="{y}"/></Anchors>\n'
                       '</CheckButton>')
    # Replace only the race button block; retain all other native XML byte text.
    require(not re.sub(pattern, '', xml[matches[0].start():matches[-1].end()], flags=re.S).strip(),
            'Unexpected content between race buttons')
    xml = xml[:matches[0].start()] + '\n'.join(buttons) + xml[matches[-1].end():]
    ET.fromstring(xml)
    parent = sources['GlueParent.lua'].decode('utf-8').replace('\r\n', '\n')
    parent = replace_once(parent, 'function SetBackgroundModel(model, name)\n',
                          'function SetBackgroundModel(model, name)\n'
                          '    -- Reversible preview scene aliases; not starting zones or factions.\n'
                          '    local newRaceScenes = { TURTLEHIGHELF = "BloodElf", TURTLEGOBLIN = "Orc" };\n'
                          '    name = newRaceScenes[strupper(name)] or name;\n')
    payload = {'Interface/GlueXML/CharacterCreate.lua': lua.encode(),
               'Interface/GlueXML/CharacterCreate.xml': xml.encode(),
               'Interface/GlueXML/GlueParent.lua': parent.encode(),
               'Interface/Custom/NewRaces/RaceIcons.blp': turtle['RaceIcons.blp']}
    return payload, coords


def build(output, native_root=Path('/home/dev/wow-335'),
          turtle_archive=Path('/home/dev/wow-turtle/Data/patch-9.mpq'),
          mpq=ROOT / 'tools/mpq', source_dir=None, turtle_dir=None, glueparent_archive=None):
    output = safe_output(output)
    for source in (native_root, source_dir, turtle_dir):
        if source:
            require(not output.is_relative_to(source.resolve()), 'Output inside source directory')
    sources, turtle, provenance = load_sources(native_root, turtle_archive, mpq, source_dir,
                                               turtle_dir, glueparent_archive)
    payload, coords = transform(sources, turtle)
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in payload.items():
        dest = output / 'payload' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as handle:
            handle.write(raw)
    report = dict(status='STATIC payload validation only', modified_GlueXML_acceptance='NOT RUN',
                  windows_startup='NOT RUN', in_game_preview='NOT RUN', integrity_bypass='NONE',
                  required_executable_profile='cache-plus-custom-gluexml (--allow-custom-gluexml)',
                  required_executable_sha256=CUSTOM_GLUE_SHA,
                  native_gluexml_gate='STRICT; cache-only derivative rejects changed XML/Lua graph digest',
                  integrity_note='UI builder changes no executable; required executable profile permits local GlueXML digest mismatch only',
                  sources=provenance, expected_picker_race_ids=PICKER_IDS,
                  picker_order_status='INFERRED from native enumerator, not runtime observed',
                  file_strings={'22': 'TurtleHighElf', '23': 'TurtleGoblin'},
                  race_buttons=12, class_buttons=10, source_icon_uv=coords,
                  scene_aliases={'TurtleHighElf': 'BloodElf', 'TurtleGoblin': 'Orc'},
                  scene_note='Temporary native scenes, camera/lighting/ambience inherited; visual framing NOT RUN',
                  additional_texture_files=['Interface/Custom/NewRaces/RaceIcons.blp'],
                  payload={name: sha(raw) for name, raw in payload.items()},
                  installation='Manual parent packager merge with additive DBC/model resources; no MPQ emitted')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-root', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--turtle-archive', type=Path, default=Path('/home/dev/wow-turtle/Data/patch-9.mpq'))
    parser.add_argument('--mpq', type=Path, default=ROOT / 'tools/mpq')
    parser.add_argument('--source-dir', type=Path, help='Explicit extracted native baseline: three files, pinned hashes')
    parser.add_argument('--turtle-dir', type=Path, help='Explicit Turtle CharacterCreate.lua and RaceIcons.blp, pinned hashes')
    parser.add_argument('--glueparent-archive', type=Path, help='Explicit baseline archive; disables candidate resolution')
    args = parser.parse_args()
    try:
        print(json.dumps(build(**vars(args)), indent=2))
    except (ValueError, OSError, ET.ParseError) as error:
        parser.exit(1, f'error: {error}\n')


if __name__ == '__main__':
    main()
