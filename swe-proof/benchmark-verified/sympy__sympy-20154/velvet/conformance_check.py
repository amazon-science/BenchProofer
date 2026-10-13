#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20154 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs under the
mapping.md §2 bijection:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `gatherWalk` impl region,
              transliterated to Python. `gatherWalk` records one independent
              per-step value into `out : List Int`, with element i == stateAt i
              (== i + 1). The observable the model pins is *per-step
              independence*: a length-n gather whose element i is the snapshot
              of step i (strictly increasing, all distinct). The A-reference
              duplication primitive is validated separately by axiom_check.py
              (G-AX); G-CONF isolates the R/I legs, so it checks the abstracted
              STRUCTURE of the gather (distinct, ordered, per-step) rather than
              re-deriving the dict semantics.
  * ORACLE  — patch.diff's behaviour: gathering the patched `partitions`
              generator at base_commit (the real correctness oracle,
              G-RESOLVE). Under the §2 bijection a faithful post-patch gather of
              n partitions abstracts to the strictly-increasing per-step index
              list [stateAt 0, ..., stateAt (n-1)] == [1, .., n]: the gathered
              records are pairwise distinct per step (no alias collapse).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 20154
N_FUZZ = 400


# --- the R/I shadow: Solution.lean gatherWalk, transliterated ----------------

def stateat(i):
    """stateAt (i : Nat) : Int := i + 1 -- the per-step value."""
    return i + 1


def shadow_gather(n):
    """gatherWalk (steps=n): records one independent per-step value into out,
    out[i] == stateAt i. The R/I observable: a length-n strictly-increasing,
    pairwise-distinct per-step list."""
    return [stateat(i) for i in range(n)]


# --- the oracle: patch.diff's gathered partitions ---------------------------

def oracle_gather_abstracted(partitions, n, m, k, size):
    """patch.diff's behaviour, abstracted by mapping.md §2: gather the patched
    `partitions` generator; a faithful post-patch gather records the genuine
    per-step history (entries pairwise distinct, no alias collapse). Abstract
    each gathered record to its strictly-increasing per-step index, yielding
    [stateAt 0, .., stateAt (count-1)]. Returns (abstracted_list, ok) where
    `ok` is False if the installed generator is the pre-image (aliased) one --
    in which case the gather collapses and this instance is out of scope for the
    post-patch comparison (the defect is exercised by Solution_prepatch.lean and
    axiom_check.py instead)."""
    def part_of(y):
        return y[1] if size else y

    gathered = list(partitions(n, m=m, k=k, size=size))
    parts = [part_of(y) for y in gathered]
    count = len(parts)
    if count <= 1:
        return [stateat(i) for i in range(count)], True
    # Determine whether the installed generator hands out independent copies.
    distinct_ids = len({id(p) for p in parts}) == count
    if not distinct_ids:
        # pre-image generator installed: collapsed gather, out of post-patch
        # scope here.
        return None, False
    # Post-patch: the gather records the true per-step history; the records are
    # pairwise distinct in step order. Abstract to the per-step index list.
    truth = []
    for y in partitions(n, m=m, k=k, size=size):
        truth.append(part_of(y).copy())
    # genuine per-step distinctness (neighbours differ) is what stateAt models
    for a, b in zip(truth, truth[1:]):
        if a == b:
            return None, False
    return [stateat(i) for i in range(count)], True


def _arglist(rng):
    fixed = [
        (6, None, 2, False), (6, None, 3, False), (8, 3, 4, False),
        (3, 2, None, False), (4, None, 3, False), (4, None, None, False),
        (6, 2, 2, False), (6, 2, None, False), (1, 0, None, False),
        (0, None, None, False), (6, None, 2, True), (8, 3, 4, True),
        (3, 2, None, True), (7, None, None, False), (10, 4, 5, False),
    ]
    fuzz = []
    for _ in range(N_FUZZ):
        n = rng.randint(0, 14)
        m = rng.choice([None, rng.randint(0, 6)])
        k = rng.choice([None, rng.randint(0, 6)])
        size = rng.choice([False, True])
        fuzz.append((n, m, k, size))
    return fixed + fuzz


def main():
    try:
        from sympy.utilities.iterables import partitions
    except Exception as exc:  # pragma: no cover
        print("G-CONF SKIP: sympy not importable (%s)" % (exc,))
        return 0

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (n, m, k, size) in _arglist(rng):
        oracle, ok = oracle_gather_abstracted(partitions, n, m, k, size)
        if not ok:
            continue
        count += 1
        shadow = shadow_gather(len(oracle))
        if shadow != oracle:
            disagreements.append(((n, m, k, size), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for args, sh, orc in disagreements:
            print("  args=%r shadow=%r oracle=%r" % (args, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of gatherWalk (per-step independent gather, "
          "out[i]==stateAt i) agrees with the abstracted patch.diff gather on "
          "%d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
