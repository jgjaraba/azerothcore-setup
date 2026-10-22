#!/usr/bin/env python3
"""Extract effective (highest-priority) ADT tiles from the Turtle client that do
not exist in the 335 client, then scan their area IDs and map them to area names.

Used to attribute new continent tiles to named regions for the inventory.

Usage:
  extract_tiles.py kalimdor azeroth
"""
import os, sys, re, subprocess, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mpq_priority import load, effective, TURTLE_ORDER, W335_ORDER
from dbc import read_dbc
from adt import parse_adt

TURTLE_DATA = '/home/dev/wow-turtle/Data'
OUTROOT = os.path.join(HERE, '..', 'work', 'extract', 'turtle', 'newtiles')
MPQ_BIN = os.path.join(HERE, 'mpq')
LF = os.path.join(HERE, 'listfile-focused.txt')

def area_names():
    fc, recs, get_string = read_dbc(os.path.join(HERE, '..', 'work', 'extract', 'turtle', 'dbc', 'AreaTable.dbc'))
    return {r[0]: get_string(r[11]) for r in recs}

def collect_new_tiles(mapdirs, turtle, d335):
    out = {}
    for mapdir in mapdirs:
        pat = re.compile(r'^world\\maps\\' + re.escape(mapdir) + r'\\([^\\]+\.adt)$')
        for name in turtle:
            m = pat.match(name)
            if not m:
                continue
            te = effective(turtle, name, TURTLE_ORDER)
            if te is None or te[1] == 0:
                continue
            de = effective(d335, name, W335_ORDER)
            if de is not None and de[1] != 0:
                continue
            out[name] = te[0]
    return out

def main():
    mapdirs = sys.argv[1:] or ['kalimdor', 'azeroth']
    turtle = load('turtle')
    d335 = load('335')
    tiles = collect_new_tiles(mapdirs, turtle, d335)
    print(f'# {len(tiles)} new tiles to extract', file=sys.stderr)

    by_mpq = collections.defaultdict(list)
    for name, mpq in tiles.items():
        by_mpq[mpq].append(name)

    os.makedirs(OUTROOT, exist_ok=True)
    for mpq, names in by_mpq.items():
        arc = os.path.join(TURTLE_DATA, mpq + '.mpq')
        if not os.path.exists(arc):
            arc = os.path.join(TURTLE_DATA, mpq + '.MPQ')
        listf = os.path.join(OUTROOT, f'_list_{mpq}.txt')
        with open(listf, 'w') as f:
            for n in names:
                f.write(n.replace('/', '\\') + '\n')
        print(f'# extracting {len(names)} from {mpq}', file=sys.stderr)
        subprocess.run([MPQ_BIN, 'extract-list', arc, listf, OUTROOT, LF],
                       check=False)

    names_map = area_names()
    print('mapdir\ttile\tmpq\tareas')
    for name in sorted(tiles):
        mapdir = name.split('\\')[2]
        tile = name.split('\\')[3]
        mpq = tiles[name]
        outpath = os.path.join(OUTROOT, name.replace('/', '\\'))
        if not os.path.exists(outpath):
            print(f'{mapdir}\t{tile}\t{mpq}\t<MISSING>')
            continue
        try:
            r = parse_adt(outpath)
        except Exception as e:
            print(f'{mapdir}\t{tile}\t{mpq}\t<ERR {e}>')
            continue
        areas = sorted(set(a for a in r['area_ids'] if a))
        anames = '; '.join(f'{a}:{names_map.get(a, "?")}' for a in areas)
        print(f'{mapdir}\t{tile}\t{mpq}\t{anames}')

if __name__ == '__main__':
    main()
