#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26342 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `setPaths` impl region
              transliterated to Python over the *real* repo state (a
              `Collection` restricted to its path-replacement-relevant carrier),
              via the mapping.md bijection
              (`PathContainer ↔ ⟨coll.get_paths(), coll.stale⟩`; the supplied
              collection is carried through by object identity; an `Except.ok ()`
              outcome ↔ a normal return). The branch is pure R/I; there is no
              consumed axiom in the computed state, so the shadow is exact.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `matplotlib.collections.Collection.set_paths` applied at
              base_commit (the real correctness oracle, G-RESOLVE), invoked on a
              freshly built container.

An "input" is a supplied collection of opaque path identities (varying length
and content) plus the container's prior `stale` flag. The observables compared
are: the outcome (completed normally vs refused), the stored collection (by
object identity — `get_paths()` must return the very object supplied), and the
post `stale` flag. They must agree on every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + matplotlib
(Agg backend). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 26342
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean setPaths, transliterated ------------------
def shadow_set_paths(prior_stale, supplied):
    """`setPaths` run on a container with the given prior `stale`, supplying
    `supplied`. Returns (outcome, stored, stale).

    Transliteration of the impl `do` block:
        coll := { coll with paths := newPaths, stale := true }
        return Except.ok ()
    The supplied collection is stored wholesale (carried by identity); `stale`
    becomes True; the outcome is a normal completion."""
    # coll := { coll with paths := newPaths, stale := true }
    stored = supplied
    stale = True
    # return Except.ok ()
    outcome = "ok"
    return (outcome, stored, stale)


# --- the oracle: patch.diff's behaviour --------------------------------------
def _make_collection():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.collections import Collection
    try:
        return Collection()
    except TypeError:
        class _C(Collection):
            pass
        return _C()


def oracle_set_paths(prior_stale, supplied):
    """patch.diff's behaviour: the patched Collection.set_paths invoked on a
    fresh container. The harness applies patch.diff before this runs, so the
    imported Collection has the new `set_paths` body. Returns
    (outcome, stored, stale)."""
    c = _make_collection()
    c.stale = prior_stale
    try:
        c.set_paths(supplied)
    except Exception as e:
        return ("raised:%s" % type(e).__name__, None, None)
    return ("ok", c.get_paths(), c.stale)


def _observe_equal(shadow, oracle, supplied):
    """Compare the two observation tuples. The `stored` leg is compared by
    object IDENTITY against the supplied collection (the op stores it wholesale,
    not a copy)."""
    s_out, s_stored, s_stale = shadow
    o_out, o_stored, o_stale = oracle
    if s_out != o_out:
        return False
    if s_out != "ok":
        return True  # both refused identically
    # both completed: stored object must be the very supplied collection
    if not (s_stored is supplied and o_stored is supplied):
        return False
    return bool(s_stale) == bool(o_stale)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield (False, [])
    yield (True, [])
    yield (False, [object()])
    yield (True, [object(), object()])
    yield (False, list(range(5)))
    yield (False, tuple())
    yield (True, (object(), object()))
    for _ in range(n):
        prior = rng.random() < 0.5
        k = rng.randint(0, 10)
        supplied = [object() for _ in range(k)]
        yield (prior, supplied)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for prior, supplied in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_set_paths(prior, supplied)
        oracle = oracle_set_paths(prior, supplied)
        if not _observe_equal(shadow, oracle, supplied):
            disagreements.append(((prior, "len=%d" % len(supplied)),
                                  shadow[0], oracle[0]))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of setPaths agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
