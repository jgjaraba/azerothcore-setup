#!/usr/bin/env python3
"""Compare ADT/WDT/WDL tile sets between the Turtle (source) and 335 (dest)
clients, and produce per-map inventories.

Reads the listing files under work/extract/listings/{turtle-*.txt,335-*.txt}
that were produced by `mpq list`. A listing line is:
    World\\Maps\\Kalimdor\\Kalimdor_28_40.adt<TAB>12345

Usage:
  adt_inventory.py diff <mapdir>      - show new/common/335-only tiles
  adt_inventory.py maps               - summary of map dir -> tile count (both)
"""
import os, sys, glob, re, collections

LISTDIR = os.path.join(os.path.dirname(__file__), '..', 'work', 'extract', 'listings')

TILE_RE = re.compile(r'^(?:world|World)\\Maps\\([^\\]+)\\([^\\]+\.(?:adt|wdt|wdl))', re.I)

def collect(prefix):
    """Return dict mapdir(lower) -> set of tile filenames(lower)."""
    result = collections.defaultdict(set)
    for path in glob.glob(os.path.join(LISTDIR, prefix + '-*.txt')):
        with open(path, 'r', errors='replace') as f:
            for line in f:
                line = line.rstrip('\n')
                m = TILE_RE.match(line)
                if not m:
                    continue
                mapdir = m.group(1).lower()
                tile = m.group(2).lower()
                result[mapdir].add(tile)
    return result

def main():
    args = sys.argv[1:]
    if len(args) < 1:
        print(__doc__)
        return
    turtle = collect('turtle')
    d335 = collect('335')

    if args[0] == 'maps':
        allmaps = sorted(set(turtle) | set(d335))
        print('mapdir\tturtle_tiles\t335_tiles')
        for m in allmaps:
            print(f'{m}\t{len(turtle.get(m,()))}\t{len(d335.get(m,()))}')
        return

    if args[0] == 'diff' and len(args) >= 2:
        m = args[1].lower()
        t = turtle.get(m, set())
        d = d335.get(m, set())
        only_turtle = sorted(t - d)
        only_335 = sorted(d - t)
        common = sorted(t & d)
        print(f'== map {m} ==')
        print(f'turtle-only tiles ({len(only_turtle)}):')
        for x in only_turtle:
            print('  NEW   ', x)
        print(f'335-only tiles ({len(only_335)}):')
        for x in only_335:
            print('  335ONLY', x)
        print(f'common tiles ({len(common)})')
        return

    print('unknown command', args)

if __name__ == '__main__':
    main()
