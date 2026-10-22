#!/usr/bin/env python3
"""MPQ priority resolution for the turtle-wow-maps port.

Loads the listing files produced by `mpq list` and exposes the effective
(highest-priority) archive+size for any file, taking the client's MPQ load
order into account. A size of 0 marks a deletion/placeholder entry in a patch.

Legacy audit approximation only: the static order and cached listings below
do not implement all custom/root/locale resolution of the actual playing
client. See docs/turtle-wow/migration-guide.md before using it as evidence.
"""
import os, glob, collections

LISTDIR = os.path.join(os.path.dirname(__file__), '..', 'work', 'extract', 'listings')

# Highest priority first.
TURTLE_ORDER = ['patch-9', 'patch-8', 'patch-7', 'patch-6', 'patch-5', 'patch-4',
                'patch-3', 'patch-2', 'patch', 'Patch-F',
                'backup', 'base', 'dbc', 'fonts', 'interface', 'misc',
                'model', 'sound', 'speech', 'terrain', 'texture', 'wmo']
W335_ORDER = ['patch-Z', 'patch-esES-N', 'patch-enUS-N', 'patch-esES-M', 'patch-enUS-M',
              'patch-eses-3', 'patch-enUS-3', 'patch-eses-2', 'patch-enUS-2',
              'patch-eses', 'patch-enUS', 'patch-3', 'patch-2', 'patch',
              'locale-esES', 'locale-enUS', 'lichking', 'expansion',
              'common-2', 'common', 'Patch-F']

def _norm(name):
    return name.lower().replace('/', '\\')

def load(prefix):
    """Return dict: norm_name -> list of (mpq, size) in priority order."""
    data = collections.defaultdict(list)
    files = {}
    for path in glob.glob(os.path.join(LISTDIR, prefix + '-*.txt')):
        base = os.path.basename(path)
        tag = base[len(prefix) + 1:-4]
        with open(path, 'r', errors='replace') as f:
            for line in f:
                line = line.rstrip('\n')
                if '\t' not in line:
                    continue
                name, sz = line.rsplit('\t', 1)
                try:
                    size = int(sz)
                except ValueError:
                    continue
                files.setdefault(_norm(name), []).append((tag, size))
    return files

def _order_map(order):
    return {tag: i for i, tag in enumerate(order)}

def effective(files, name, order):
    omap = _order_map(order)
    entries = files.get(_norm(name), [])
    if not entries:
        return None
    # pick highest priority (smallest order index)
    best = min(entries, key=lambda e: omap.get(e[0], 10**9))
    return best  # (mpq, size)

def main():
    import sys
    if len(sys.argv) < 3:
        print('usage: mpq_priority.py <turtle|335> <filename> [...]')
        return
    kind = sys.argv[1]
    order = TURTLE_ORDER if kind == 'turtle' else W335_ORDER
    files = load(kind)
    for name in sys.argv[2:]:
        r = effective(files, name, order)
        print(f'{name}\t->\t{r}')

if __name__ == '__main__':
    main()
