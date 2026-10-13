#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12481 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (`entries : List (List Nat)` ↔ the argument list, `grouped` ↔ the
              flag that selects the reading, `ValueError` ↔ `Except.error`, the
              array form ↔ `_array_form`):

                temp = flatten(entries)
                if has_dups(temp) and not grouped:      -> error   (A4, I)
                elif not grouped and not covered(temp): -> error   (A5, I)
                elif grouped:                           -> ok arrayForm(entries)
                else:                                   -> ok temp (A7, I)

              `arrayForm`/`composePoint` are the deep model (A-reference); they
              are I/R-transliterated here so G-CONF exercises the whole computed
              result, not merely the screens.
  * ORACLE  — patch.diff's behaviour: the gold-patched constructor applied at
              base_commit (the real correctness oracle, G-RESOLVE). A raised
              ValueError ↔ error, a constructed permutation ↔ ok `.array_form`.

BOTH READINGS ARE FUZZED, because `grouped` is a free Bool in the contract and
the two readings disagree exactly where the change lands (a repeated point is
composed for the grouped reading and refused for the flat one). The oracle call
follows the repo's own dispatch (`is_cycle = args and is_sequence(args[0])`):

  * grouped=True  -> `Permutation([list(c) for c in entries])` (a list of lists,
                     so the constructor takes the grouped reading);
  * grouped=False -> `Permutation(list(entries[0]))` (a flat list of ints, so it
                     takes the other reading). The model carries the flat
                     argument as `entries.flatten`, and the two consumers of it
                     (the screens and the returned form) depend on the flattened
                     points alone, so the single-group encoding `[ps]` is the
                     canonical representative of its whole fiber — see
                     mapping.md §3.

Grouped inputs must satisfy the one Requires clause (some point named, no group
naming a point twice — mapping.md §3); flat inputs are UNCONSTRAINED, which is
the point: every flat argument, admissible or not, is specified by the contract's
two `grouped = false` clauses and so must agree with the oracle here.
Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff applied),
stdlib + sympy only. The fuzz seed is pinned (mapping.md §5).
"""
import random
import sys

SEED = 12481
N_FUZZ = 50_000          # per reading, so >= 10^5 inputs overall


# --- the R/I shadow: Solution.lean composePoint/arrayForm + the two screens ---

def succ_in_cycle(first, cyc, x):
    # image of x under one elementary mapping written as the list `cyc`
    if not cyc:
        return x
    if len(cyc) == 1:
        return first if x == cyc[0] else x
    a, b = cyc[0], cyc[1]
    if x == a:
        return b
    return succ_in_cycle(first, cyc[1:], x)


def cycle_step(cyc, x):
    if not cyc:
        return x
    return succ_in_cycle(cyc[0], cyc, x)


def compose_point(cycles, x):
    # left-to-right composite: leftmost group acts first
    for c in cycles:
        x = cycle_step(c, x)
    return x


def max_elem(cycles):
    m = 0
    for c in cycles:
        for v in c:
            if v > m:
                m = v
    return m


def array_form_shadow(cycles):
    n = max_elem(cycles) + 1
    return [compose_point(cycles, i) for i in range(n)]


def points_distinct(seq):
    """Solution.lean `pointsDistinct`: no point named twice."""
    return len(set(seq)) == len(seq)


def range_covered(seq):
    """Solution.lean `rangeCovered`: no gap below the count of DISTINCT points
    (`l.dedup.length` ↔ `len(set(temp))`)."""
    n = len(set(seq))
    return all(i in seq for i in range(n))


def shadow(entries, grouped):
    """The R/I shadow result: ('error',) or ('ok', list)."""
    temp = [x for c in entries for x in c]           # flatten
    if not points_distinct(temp) and not grouped:    # A4, the changed screen
        return ("error",)
    if not grouped and not range_covered(temp):      # A5, the coverage screen
        return ("error",)
    if grouped:
        return ("ok", array_form_shadow(entries))    # A6
    return ("ok", list(temp))                        # A7


# --- the oracle: the gold-patched constructor, on the matching reading --------

def oracle(entries, grouped):
    from sympy.combinatorics.permutations import Permutation
    if grouped:
        arg = [list(c) for c in entries]             # list of lists -> grouped
    else:
        arg = [int(x) for c in entries for x in c]   # flat list of ints
    try:
        p = Permutation(arg)
        return ("ok", list(p.array_form))
    except ValueError:
        return ("error",)


# --- fuzzing -----------------------------------------------------------------

def random_group(rng):
    k = rng.randint(0, 5)
    # sample without replacement -> no group names a point twice (eachValid)
    pool = list(range(0, 9))
    rng.shuffle(pool)
    return pool[:k]


def grouped_inputs(n, rng):
    """Requires-satisfying grouped arguments: some point is named and no group
    names a point twice. Empty groups are allowed alongside a non-empty one."""
    # boundary / issue cases first
    yield [[0, 1], [0, 2]]          # the discriminator == Permutation(0,1,2)
    yield [[0, 1], [0, 1]]          # the identity via a repeated group
    yield [[1, 2], [2, 3]]
    yield [[1], [4, 2]]
    yield [[5]]
    yield [[0, 1, 2], [3, 4]]
    yield [[0, 1], [2, 3], [0, 2]]
    yield [[1], [1, 2]]
    yield [[2, 3], [3, 2]]
    yield [[0, 1], [1, 2], [2, 0]]
    yield [[0, 1], []]              # an empty group beside a non-empty one
    yield [[], [0, 1]]
    yield [[4, 5]]                  # points that skip 0..3 (grouped: fine)
    emitted = 0
    while emitted < n:
        g = rng.randint(1, 4)
        cand = [random_group(rng) for _ in range(g)]
        if not any(cand):           # every group empty -> outside Requires
            continue
        emitted += 1
        yield cand


def flat_inputs(n, rng):
    """UNCONSTRAINED flat arguments, carried as the canonical one-group encoding
    `[ps]`. Both the accepted and the refused sub-domains are covered."""
    for ps in ([0, 2, 1], [1, 0], [0], [], [1, 1, 0], [4, 5], [5],
               [0, 1, 1], [2, 0, 1], [0, 1, 2, 3], [3, 2, 1, 0], [1, 2],
               [0, 0], [7, 0, 1]):
        yield [list(ps)]
    for _ in range(n):
        k = rng.randint(0, 6)
        # deliberately biased: half the draws are permutations of range(k) (the
        # accepted sub-domain), half are arbitrary points (mostly refused).
        if rng.random() < 0.5:
            ps = list(range(k))
            rng.shuffle(ps)
        else:
            ps = [rng.randint(0, 8) for _ in range(k)]
        yield [ps]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for grouped, gen in ((True, grouped_inputs(N_FUZZ, rng)),
                         (False, flat_inputs(N_FUZZ, rng))):
        for entries in gen:
            count += 1
            sh = shadow(entries, grouped)
            orc = oracle(entries, grouped)
            if sh != orc:
                disagreements.append((entries, grouped, sh, orc))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, g, sh, orc in disagreements:
            print("  entries=%r grouped=%r shadow=%r oracle=%r"
                  % (e, g, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildExplicitForm (both screens, both "
          "readings, and the arrayForm deep model) agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
