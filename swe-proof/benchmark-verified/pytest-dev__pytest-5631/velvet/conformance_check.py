#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5631 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List ArgEntry` ↔ `function.patchings`; `valueId == marker` ↔
              `p.new is sentinel`; `isAttribute` ↔ truthy `p.attribute_name`).
              `sentinelCount` = count of non-attribute entries whose value IS one
              of the two sentinels (decided by IDENTITY — never raises), and
              `out.err` is always False. There is NO A-tagged callee.
  * ORACLE  — `patch.diff`'s behaviour: the patched `num_mock_patch_args` from
              `_pytest.compat` applied at base_commit (the real correctness
              oracle, G-RESOLVE).

For each fuzzed input we compare BOTH observables of CountResult:
  (n)   the returned count, and
  (err) whether a ValueError was raised (the shadow says: never).
They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import types

SEED = 5631
N_FUZZ = 100_000


# --- repo-faithful fixtures --------------------------------------------------

class FakePatch:
    """One element of `function.patchings` (a `_patch`-shaped object): only the
    two fields the function reads — `attribute_name` and `new`."""

    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new


class FakeFunc:
    def __init__(self, patchings):
        self.patchings = patchings


class ArrayLike:
    """A value whose __eq__ is NON-total: comparing it for truth raises, exactly
    like a numpy array of length > 1 (problem statement / F2P NumpyLike)."""

    def __eq__(self, other):
        raise ValueError("truth value of an array with more than one element is ambiguous")

    __hash__ = None


def install_sentinels(rng):
    """Mirror the post-patch sentinel resolution: `mock`/`unittest.mock` modules
    may be present (their `.DEFAULT`) or absent (a fresh object()). Returns the
    list of *real* sentinel objects currently reachable by identity."""
    import sys as _sys
    sentinels = []
    # `unittest.mock` is always importable on py3; its DEFAULT is a real sentinel
    try:
        import unittest.mock as _utmock
        sentinels.append(_utmock.DEFAULT)
    except Exception:
        pass
    # `mock` (the standalone backport) is usually absent in this image; install a
    # fake one part of the time so we exercise both `getattr(..., DEFAULT, ...)`
    # branches.
    if rng.random() < 0.5 and "mock" not in _sys.modules:
        m = types.ModuleType("mock")
        m.DEFAULT = object()
        _sys.modules["mock"] = m
        sentinels.append(m.DEFAULT)
    else:
        got = _sys.modules.get("mock")
        if got is not None and hasattr(got, "DEFAULT"):
            sentinels.append(got.DEFAULT)
    return sentinels


# --- the R/I shadow: Solution.lean hitsMarker/sentinelCount, transliterated --

def shadow_count(func, sentinels):
    """sentinelCount over func.patchings, by IDENTITY. Returns (err, n).
    err is always False — identity never inspects value contents, never raises."""
    patchings = getattr(func, "patchings", None)
    if not patchings:
        return (False, 0)
    n = 0
    for p in patchings:
        if (not p.attribute_name) and any(p.new is s for s in sentinels):
            n += 1
    return (False, n)


def oracle_count(func):
    """patch.diff's behaviour: the patched num_mock_patch_args. Returns (err, n)
    where err records whether it raised (it must not, for any input)."""
    from _pytest.compat import num_mock_patch_args
    try:
        return (False, num_mock_patch_args(func))
    except Exception:
        return (True, None)


# --- fuzzing -----------------------------------------------------------------

def make_entry(rng, sentinels):
    """Build one FakePatch. With some probability the value is a real sentinel
    (counted), an array-like (the bug trigger), or an ordinary object."""
    attr = rng.choice([None, None, None, "attr_name"])  # mostly positional
    roll = rng.random()
    if roll < 0.35 and sentinels:
        new = rng.choice(sentinels)            # a counted sentinel (by identity)
    elif roll < 0.6:
        new = ArrayLike()                      # non-total __eq__ (numpy-like)
    else:
        new = object()                         # ordinary distinct object
    return FakePatch(attr, new)


def fuzz_funcs(n, rng, sentinels):
    # boundary cases first
    yield FakeFunc(None)                       # no patchings -> 0
    yield FakeFunc([])                         # empty -> 0
    yield FakeFunc([FakePatch(None, ArrayLike())])          # single array-like
    yield FakeFunc([FakePatch("x", ArrayLike())])           # array-like but attr (skipped)
    if sentinels:
        yield FakeFunc([FakePatch(None, sentinels[0])])     # single sentinel -> 1
        yield FakeFunc([FakePatch("x", sentinels[0])])      # sentinel but attr -> 0
    yield FakeFunc([FakePatch(None, ArrayLike()),
                    FakePatch(None, ArrayLike())])          # two array-likes
    for _ in range(n):
        k = rng.randint(0, 8)
        yield FakeFunc([make_entry(rng, sentinels) for _ in range(k)])


def main():
    rng = random.Random(SEED)
    sentinels = install_sentinels(rng)
    disagreements = []
    count = 0
    for func in fuzz_funcs(N_FUZZ, rng, sentinels):
        count += 1
        shadow = shadow_count(func, sentinels)
        oracle = oracle_count(func)
        if shadow != oracle:
            disagreements.append((len(func.patchings or []), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for k, sh, orc in disagreements:
            print("  npatchings=%d shadow=%r oracle=%r" % (k, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of countSentinelArgs agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
