#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-12481.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_permFromCycles` skeleton and diffs it against the REAL patched
routine `sympy.combinatorics.Permutation(cycles).array_form` over a discrete
catalogue of cyclic inputs plus >=1e5 randomized cycle lists (including the
non-disjoint cycles the patch newly accepts, and the degenerate shape where
cycles are supplied but name no point, on which the routine declines to build).

Modeled path: the cyclic-form (`is_cycle = True`) branch of `Permutation.__new__`
— the branch the gold patch edits. Input is a list of cycles, each a list of
distinct nonnegative ints; the cycles are composed left-to-right and the array
form returned.

Bridge (mapping.md): a Lean cycle list `List (List Nat)` <-> a Python list of
lists of ints; Lean `some aform` <-> `Permutation(cycles).array_form`, and Lean
`none` <-> the constructor declining to build (a ValueError).

Exit 0 iff zero disagreements. stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_permFromCycles (post-patch R/I leg) -----

def apply_cycle(c, x):
    """Image of x under a single cycle c = [a0,...,a_{k-1}]: a_t -> a_{(t+1)%k},
    others fixed. Mirrors Lean `applyCycle`."""
    if x in c:
        i = c.index(x)
        return c[(i + 1) % len(c)]
    return x


def perm_size(cycles):
    """One past the largest named point (0 if none). Mirrors Lean `permSize`."""
    m = 0
    for c in cycles:
        for x in c:
            m = max(m, x + 1)
    return m


def size_undetermined(cycles):
    """At least one cycle supplied, yet no point named between them, so the width
    of the array form is not determined. Mirrors Lean `sizeUndetermined`."""
    return len(cycles) != 0 and perm_size(cycles) == 0


def shadow_perm_from_cycles(cycles):
    """Transliteration of implementation_permFromCycles: `None` on the degenerate
    shape (nothing returned), else the array form of the left-to-right
    composition of `cycles` as a list of ints."""
    if size_undetermined(cycles):
        return None
    sz = perm_size(cycles)
    aform = []
    for i in range(sz):
        v = i
        for c in cycles:
            v = apply_cycle(c, v)
        aform.append(v)
    return aform


# ---- real callee observation ------------------------------------------------

def real_perm_from_cycles(cycles):
    """Run the REAL patched Permutation constructor on cyclic input and return
    its array form as a list of plain ints, or `None` if it declines to build
    (a ValueError) -- the observation the Lean `Option` carrier's `none` models.
    Every OTHER exception type propagates: only the documented refusal is
    folded into the carrier, so a crash cannot masquerade as agreement."""
    from sympy.combinatorics import Permutation
    # deep-copy the cycles: the constructor mutates nothing but be safe.
    try:
        p = Permutation([list(c) for c in cycles])
    except ValueError as e:
        # ONLY the width-undetermined refusal is folded into the carrier's `none`.
        # Any other ValueError is a different behavior the model does not claim, so
        # it propagates and fails the gate rather than being absorbed as agreement.
        if 'empty Cycle' in str(e):
            return None
        raise
    return [int(v) for v in p.array_form]


def main():
    disagreements = 0
    checked = 0
    skipped = 0

    rng = random.Random(SEED)

    cases = []

    # discrete catalogue: the issue's cases + assorted disjoint/non-disjoint.
    discrete = [
        [[0, 1], [0, 1]],          # issue: identity
        [[0, 1], [0, 2]],          # new F2P: == Permutation(0,1,2) -> [1,2,0]
        [[1], [1, 2]],             # old raises(...) case, now accepted
        [[1, 2]],
        [[2, 3], [4, 5]],          # disjoint
        [[1, 4], [3, 5, 2]],       # disjoint, gaps
        [[0, 1, 2], [1, 3]],       # non-disjoint chain
        [[1], [4, 2]],             # singleton + transposition
        [[0, 1, 2, 3]],
        [[5, 0], [0, 5]],          # inverse pair -> identity over 0..5
        [[3]],                     # singleton only
        [[0]],                     # narrowest determined width (1 entry)
        [],                        # no cycle supplied at all -> empty array form
        [[]],                      # supplied but pointless -> declines to build
        [[], []],                  # ditto, several
        [[], [0, 1]],              # a pointless cycle alongside a real one
        [[0, 1], []],              # ditto, other order
        [[], [], [0]],             # ditto, several
    ]
    cases.extend(discrete)

    def rand_cycle(rng, pool):
        """A cycle of distinct points sampled from `pool`."""
        k = rng.randint(1, min(4, len(pool)))
        return rng.sample(pool, k)

    # `ncyc` starts at 0 and cycles are EMPTY 15% of the time, so the degenerate
    # family (every supplied cycle pointless) and the no-cycle case are both drawn
    # instead of being unreachable by construction.
    for _ in range(N_RANDOM):
        maxpt = rng.randint(0, 7)
        pool = list(range(maxpt + 1))
        ncyc = rng.randint(0, 4)
        cycles = [[] if rng.random() < 0.15 else rand_cycle(rng, pool)
                  for _ in range(ncyc)]
        cases.append(cycles)

    # NOTHING is carved out: the degenerate shape (cycles supplied, no point named)
    # is part of the modeled behavior now, so it is CHECKED rather than skipped --
    # a `None` on both sides is an agreement about declining to build, not a gap.
    for cycles in cases:
        # the Lean precondition: each cycle lists DISTINCT points. The generators
        # only ever build such cycles; assert it so a generator change cannot
        # silently push out-of-domain inputs through the comparison.
        assert all(len(set(c)) == len(c) for c in cycles), cycles
        got = real_perm_from_cycles(cycles)
        exp = shadow_perm_from_cycles(cycles)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH cycles={cycles}: real={got!r} shadow={exp!r}")

    print(f"checked={checked} skipped={skipped} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
