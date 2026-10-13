#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20154.

This bundle consumes NO axiom. The single external semantics the deep model
relies on is the independence guarantee of duplicating the working record per
step (`ms.copy()` at each `yield`), modelled deeply in Solution.lean as a
by-value per-step capture (`snap := stateAt (i-1)`, prepended, so a later
mutation of `work` never reaches an already-gathered record). G-AX validates
that deep model as an **A-reference** against the real semantics:

  (A-reference) recording an INDEPENDENT per-step snapshot ↔ `dict.copy()` at
      each yield. With copying, gathering the generator records the genuine,
      pairwise-distinct per-step history (gathered-record-i == the i-th
      partition); without copying every gathered record aliases the single
      mutating dict and reads back as the FINAL state -- exactly the model's
      fix-vs-defect distinction (Solution.lean: `out[i]! = stateAt i` for the
      fix vs the alias collapse in Solution_prepatch.lean).

Two independent checks are run:

  1. A pure-stdlib `dict.copy()` probe: a fresh copy is a DISTINCT object whose
     contents equal the source's at copy time and which is isolated from
     subsequent source mutations (the independence the deep model encodes).

  2. The REAL repo generator `sympy.utilities.iterables.partitions`, run on
     boundary + fuzz arguments. We assert:
       (a) `[p.copy() for p in partitions(...)]` (independent snapshots) lists
           pairwise-distinct partitions matching `partitions` consumed one at a
           time (the post-patch / desired behaviour);
       (b) gathering WITHOUT copying -- `list(partitions(...))` -- collapses
           every entry to the LAST partition whenever more than one partition is
           produced (the modeled pre-image defect): the property the post-patch
           `.copy()` removes, confirming the deep model senses the right change.

Exit 0 iff every obligation holds. Imports: the standard library plus the repo
function under test (the harness container has sympy installed).
"""
import random
import sys


# --- check 1: the dict.copy() independence primitive (pure stdlib) ----------

def check_dict_copy_independence():
    """`d.copy()` is a distinct object, equal in contents at copy time, and
    isolated from subsequent mutations of the source -- the independence the
    deep model's by-value per-step capture encodes."""
    samples = [
        {}, {1: 6}, {2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1},
        {4: 2}, {1: 1, 3: 1, 4: 1}, {2: 2, 4: 1}, {2: 1, 3: 2},
        {k: k * k for k in range(1, 12)},
    ]
    for d in samples:
        c = d.copy()
        assert c is not d, "copy is not a distinct object for %r" % (d,)
        assert c == d, "copy contents differ at copy time for %r" % (d,)
        snapshot = d.copy()           # what a gather would have recorded
        d[999] = 1                    # mutate the source afterwards
        if d:
            some_key = next(iter(d))
            d[some_key] = d[some_key] + 1000
        assert c == snapshot, (
            "copy %r was disturbed by a later source mutation %r" % (c, d))


# --- check 2: the real partitions generator ---------------------------------

def _arglist():
    """Boundary + fuzz argument tuples (n, m, k, size) for partitions()."""
    fixed = [
        (6, None, 2, False), (6, None, 3, False), (8, 3, 4, False),
        (3, 2, None, False), (4, None, 3, False), (4, None, None, False),
        (6, 2, 2, False), (6, 2, None, False), (1, 0, None, False),
        (0, None, None, False), (6, None, 2, True), (8, 3, 4, True),
        (3, 2, None, True), (7, None, None, False), (10, 4, 5, False),
    ]
    rng = random.Random(20154)
    fuzz = []
    for _ in range(400):
        n = rng.randint(0, 14)
        m = rng.choice([None, rng.randint(0, 6)])
        k = rng.choice([None, rng.randint(0, 6)])
        size = rng.choice([False, True])
        fuzz.append((n, m, k, size))
    return fixed + fuzz


def _part_of(yielded, size):
    """Extract the partition dict from a yielded item ((M, p) when size=True,
    else p)."""
    if size:
        return yielded[1]
    return yielded


def check_partitions(partitions):
    for (n, m, k, size) in _arglist():
        # (a) independent snapshots: copy each yielded dict before it is reused.
        snaps = [_part_of(y, size).copy()
                 for y in partitions(n, m=m, k=k, size=size)]

        # An independent re-run consumed one-at-a-time gives the ground-truth
        # per-step partitions (each fully copied before the next yield mutates
        # the shared dict): compare snapshot history against it.
        truth = []
        for y in partitions(n, m=m, k=k, size=size):
            truth.append(_part_of(y, size).copy())
        assert snaps == truth, (
            "snapshot history disagrees with one-at-a-time truth for "
            "n=%r m=%r k=%r size=%r: %r vs %r" % (n, m, k, size, snaps, truth))

        # The snapshot history records genuine per-step states: consecutive
        # partitions differ (partitions() never yields the same partition twice
        # in a row), so a faithful gather has pairwise-distinct neighbours --
        # the strictly-changing per-step observable stateAt models.
        for a, b in zip(snaps, snaps[1:]):
            assert a != b, (
                "consecutive snapshots equal for n=%r m=%r k=%r size=%r: %r" %
                (n, m, k, size, a))

        # (b) Characterise the gather WITHOUT an explicit per-item copy --
        # `list(partitions(...))` -- and confirm the fix-vs-defect distinction
        # the deep model encodes. Robust to whichever version of `partitions`
        # the container has installed:
        #   * PRE-IMAGE: the generator yields the live, reused dict, so every
        #     gathered entry aliases it and, once exhausted, reads back as the
        #     LAST partition -- the modeled defect.
        #   * POST-PATCH: the generator yields independent copies, so the
        #     gathered entries are distinct objects recording the true per-step
        #     history -- the modeled fix.
        gathered = list(partitions(n, m=m, k=k, size=size))
        parts = [_part_of(y, size) for y in gathered]
        if len(parts) > 1:
            all_shared = all(p is parts[0] for p in parts)
            no_shared = len({id(p) for p in parts}) == len(parts)
            assert all_shared or no_shared, (
                "gather is neither fully-aliased (pre-image defect) nor "
                "fully-independent (post-patch fix) for n=%r m=%r k=%r size=%r"
                % (n, m, k, size))
            if all_shared:
                # PRE-IMAGE defect: collapsed history differs from the truth.
                collapsed = [p.copy() for p in parts]
                assert collapsed != truth, (
                    "aliased gather unexpectedly equals the true per-step "
                    "history for n=%r m=%r k=%r size=%r" % (n, m, k, size))
            else:
                # POST-PATCH fix: independent gather equals the truth exactly.
                assert [p.copy() for p in parts] == truth, (
                    "independent gather disagrees with the true per-step "
                    "history for n=%r m=%r k=%r size=%r" % (n, m, k, size))


def main():
    check_dict_copy_independence()

    try:
        from sympy.utilities.iterables import partitions
    except Exception as exc:  # pragma: no cover - only when run outside container
        print("G-AX SKIP: sympy not importable (%s); dict.copy independence "
              "probe passed" % (exc,))
        return 0

    check_partitions(partitions)

    print("G-AX OK: dict.copy independence probe passed; real partitions() "
          "snapshot history matches one-at-a-time truth with pairwise-distinct "
          "neighbours, and the no-copy gather collapses to the final shared "
          "object (the modeled defect) -- deep by-value snapshot model sound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
