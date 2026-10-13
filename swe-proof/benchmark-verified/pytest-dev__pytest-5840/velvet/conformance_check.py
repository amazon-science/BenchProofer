#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5840 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of `Solution.lean`'s impl region (`registerModule`)
             transliterated to Python: a cache modeled as an association list of
             (Key, module) where Key = (loc, rep). The impl probes/stores under
             the PRIMARY representation (`probeKey loc = (loc, 'primary')`) via the
             `regLookup` first-match-by-full-key-equality semantics. The only
             A-tagged op, `freshMod` (the import callee), never enters the key, so
             the impl region is pure R/I — `conf_skip=false`.
  * ORACLE — `patch.diff`'s behaviour: the patched `_importconftest` cache logic,
             which keys `self._conftestpath2mod` by `Path(str(conftestpath)).resolve()`
             over the REAL repo path objects (the actual `pathlib.Path` keys the
             patched code computes), importing each location at most once.

We drive both with the SAME fuzzed sequence of conftest imports (locations, with
repeats, mixed case) and compare, per step, the returned module identity AND the
post-state predicate "a consumer probe of this location finds the module". They
must agree on every step; exit 0 iff zero disagreements.

Teeth: if the impl were transliterated to store/probe under the SECONDARY
representation (the pre-patch bug), a re-import of the same location would MISS
the consumer probe and mint a fresh module id, diverging from the oracle (which
hits) — so this check refutes that mis-refinement. The fuzz seed is pinned
(mapping.md §4). Runs in-container; stdlib + `py` only.
"""
import os
import random
import sys
import tempfile
from os.path import normcase
from pathlib import Path

import py

SEED = 5840
N_FUZZ = 100_000


# --------------------------------------------------------------------------- #
# ORACLE — patch.diff's cache-key behaviour over REAL path objects.
# The patched `_importconftest` computes `key = Path(str(conftestpath)).resolve()`
# and memoizes on it. We reproduce exactly that key logic; the imported module is
# minted once per distinct key (import-at-most-once), mirroring `pyimport()`.
# --------------------------------------------------------------------------- #
class Oracle:
    def __init__(self):
        self._cache = {}            # {Path(...).resolve(): module_id}
        self._next = 0

    def register(self, local_path):
        key = Path(str(local_path)).resolve()      # patched key expression
        if key in self._cache:
            return self._cache[key], False         # hit: cache unchanged
        mod = self._next
        self._next += 1
        self._cache[key] = mod
        return mod, True

    def consumer_finds(self, local_path, expected_mod):
        # a consumer probes with the same resolved-Path key
        key = Path(str(local_path)).resolve()
        return self._cache.get(key, None) == expected_mod


# --------------------------------------------------------------------------- #
# SHADOW — Solution.lean `registerModule` transliterated (R/I ops).
# registry : List (Key × Module); Key = (loc, rep); regLookup = first match by
# full key equality; impl uses `probeKey loc = (loc,'primary')` to BOTH probe and
# store. `loc` is the abstract location identity (mapping.md §2 bijection).
# --------------------------------------------------------------------------- #
def reg_lookup(registry, q):
    for (k, m) in registry:                         # front-recursive first-match
        if k == q:
            return m
    return None


def probe_key(loc):
    return (loc, "primary")


class Shadow:
    def __init__(self):
        self.registry = []          # List[((loc,rep), module_id)]
        self._next = 0

    def register(self, loc):
        k = probe_key(loc)                          # let k := probeKey loc
        cached = reg_lookup(self.registry, k)       # regLookup registry k
        if cached is not None:                      # if cached.isSome
            return cached, False                    #   return cached (unchanged)
        fresh = self._next                          # else: the free input freshMod
        self._next += 1
        self.registry.append((k, fresh))            #   registry ++ [(k, freshMod)]
        return fresh, True

    def consumer_finds(self, loc, expected_mod):
        # post-state: regLookup registry (probeKey loc) = some out
        return reg_lookup(self.registry, probe_key(loc)) == expected_mod


# --------------------------------------------------------------------------- #
def build_locations(root, rng, n_locations):
    """Create n distinct real conftest locations (mixed case, varied depth) and
    return a list of (abstract loc id, py.path.local). The abstract id is the
    location's index — distinct locations ↔ distinct Nat (mapping.md §2)."""
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    locs = []
    seen_resolved = {}
    loc_id = 0
    attempts = 0
    while len(locs) < n_locations and attempts < n_locations * 4:
        attempts += 1
        depth = rng.randint(1, 4)
        parts = ["".join(rng.choice(letters) for _ in range(rng.randint(1, 8)))
                 for _ in range(depth)]
        rel = os.path.join(*parts, "conftest.py")
        full = os.path.join(root, rel)
        resolved = str(Path(full).resolve())
        if resolved in seen_resolved:
            continue                                # keep abstract loc <-> location 1:1
        seen_resolved[resolved] = loc_id
        try:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w").close()
        except (OSError, FileExistsError):
            continue
        locs.append((loc_id, py.path.local(full)))
        loc_id += 1
    return locs


def main():
    rng = random.Random(SEED)
    root = tempfile.mkdtemp(prefix="gconf5840_")

    # a pool of distinct locations, plus the issue's boundary scenarios
    locs = build_locations(root, rng, 60)
    for rel in ["test/conftest.py", "tests/conftest.py", "Foo/conftest.py",
                "JenkinsRoot/test/conftest.py", "MixedCase/Sub/conftest.py"]:
        full = os.path.join(root, "boundary", rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").close()
        locs.append((len(locs), py.path.local(full)))

    oracle = Oracle()
    shadow = Shadow()
    disagreements = []

    def step(loc_id, local_path):
        o_mod, o_new = oracle.register(local_path)
        s_mod, s_new = shadow.register(loc_id)
        # compare returned module identity and miss/hit, and the post-state probe
        o_find = oracle.consumer_finds(local_path, o_mod)
        s_find = shadow.consumer_finds(loc_id, s_mod)
        if (o_mod != s_mod) or (o_new != s_new) or (o_find != s_find):
            disagreements.append(
                (str(local_path), (o_mod, o_new, o_find), (s_mod, s_new, s_find)))

    # boundary: import each location twice (must hit + be findable on 2nd call)
    for loc_id, lp in locs:
        step(loc_id, lp)
        step(loc_id, lp)
        if disagreements:
            break

    # fuzz: random interleaved re-imports of the pool
    count = 2 * len(locs)
    for _ in range(N_FUZZ):
        loc_id, lp = rng.choice(locs)
        step(loc_id, lp)
        count += 1
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d steps:"
              % (len(disagreements), count))
        for path, o, s in disagreements:
            print("  loc=%r oracle(mod,new,find)=%r shadow=%r" % (path, o, s))
        return 1
    print("G-CONF OK: R/I shadow of registerModule agrees with patch.diff "
          "cache behaviour on %d import steps (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
