#!/usr/bin/env python3
"""G-CONF for matplotlib__matplotlib-26342.

The gold patch is already applied to /testbed when this runs (so the base
`Collection.set_paths` actually installs the path list instead of raising). We
compare the R/I Python shadow of `implementation_setPaths` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`matplotlib.collections.Collection.set_paths`, over >=1e5 fuzzed replacement
lists. Zero disagreements => exit 0.

Type bijection (mapping.md):
  coll     : PathContainer Path        <->  a Collection instance
                                            (.paths<->self._paths, .stale<->self.stale,
                                             .rest<->frame of all other attributes)
  newPaths : List Path                 <->  the `paths` argument (a Python list)
  result   : Except Unit (PathContainer)<->  Except.ok  <-> the call returned and
                                                            self now holds (paths,stale)
                                            Except.error<-> the call raised

stdlib-only.
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.collections import Collection


def oracle(initial_paths, initial_stale, new_paths):
    """Real patched behavior: build a Collection, seed its path list / stale
    flag, call the REAL set_paths, and read back (_paths, stale, raised)."""
    c = Collection()
    c._paths = list(initial_paths)
    c.stale = initial_stale
    try:
        c.set_paths(new_paths)
    except NotImplementedError:
        return ("error",)
    # identity: set_paths stores the SAME list object
    return ("ok", c._paths is new_paths, bool(c.stale))


def shadow(initial_paths, initial_stale, new_paths):
    """R/I transliteration of implementation_setPaths (Lean).
       c := { c with paths := newPaths }   -> store the new list
       c := { c with stale := true }       -> raise the flag
       return Except.ok c                  -> never raises
    """
    paths = new_paths          # `c.paths := newPaths`  (wholesale replace, same obj)
    stale = True               # `c.stale := true`
    return ("ok", paths is new_paths, stale)


def main():
    rng = random.Random(26342)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    # opaque path tokens (the operation is agnostic to element type)
    for i in range(N):
        init_len = rng.randint(0, 6)
        initial_paths = [("p_init", j) for j in range(init_len)]
        initial_stale = rng.random() < 0.5
        new_len = rng.randint(0, 8)
        new_paths = [("p_new", i, j) for j in range(new_len)]
        o = oracle(initial_paths, initial_stale, new_paths)
        s = shadow(initial_paths, initial_stale, new_paths)
        if o != s:
            disagreements += 1
            if first is None:
                first = (initial_paths, initial_stale, new_paths, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
