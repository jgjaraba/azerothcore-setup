#!/usr/bin/env python3
"""Build a WotLK 335 asset existence index and remap references.

Loads the 335 listing set and answers: does a given texture/model/WMO filename
exist in the 335 client, and under what effective name (for .mdx->.m2 and path
normalisation)?
"""
import os, sys, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mpq_priority import load, effective, W335_ORDER

# Files that matter for ADT references. Normalise to lowercase forward-slash.
def _norm(name):
    return name.lower().replace('\\', '/')

class AssetIndex:
    def __init__(self):
        self.files = load('335')

    def exists(self, name):
        e = effective(self.files, name.replace('/', '\\'), W335_ORDER)
        return e is not None and e[1] != 0

    def effective_name(self, name):
        """Return the effective archive name (normalised) if present, else None."""
        if self.exists(name):
            return _norm(name)
        return None

    def resolve_model(self, mdx_name):
        """Given a vanilla .mdx path, return the .m2 path if it exists in 335."""
        candidates = [mdx_name]
        # .mdx -> .m2
        if mdx_name.lower().endswith('.mdx'):
            candidates.append(mdx_name[:-4] + '.m2')
        # try both path styles (vanilla lowercase vs wotlk mixed)
        for c in candidates:
            if self.exists(c):
                return c
        # case-insensitive lookup
        norm = _norm(mdx_name)
        for key in self.files:
            if _norm(key).replace('\\', '/') == norm.replace('.mdx', '.m2') or \
               _norm(key).replace('\\', '/') == norm:
                return key.replace('\\', '/')
        return None

def main():
    import sys
    idx = AssetIndex()
    for name in sys.argv[1:]:
        print(f'{name}\t->\t{idx.resolve_model(name) if name.lower().endswith((".mdx",".m2")) else idx.effective_name(name)}')

if __name__ == '__main__':
    main()
