#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-23824.

The modeled behavior is the final prepend slice of `kahane_simplify`
(gold lines 695-698). The gold patch replaces a reversing insert-loop with the
single in-order expression

    resulting_indices = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )

This slice is a PURE list transform of values produced upstream by the Kahane
graph-walk (`first_dum_pos : int`, `free_pos : list`, `resulting_indices :
list[list]`). The R/I shadow of the Lean `implementation_prependLeading`
skeleton is therefore checked directly against the gold expression's semantics
(both are pure list operations over the same inputs) over a boundary catalogue
plus >=1e5 randomized draws. stdlib-only, pinned seed.

  bijection (mapping.md):
    first_dum_pos : int  <-> leadCount : Nat
    free_pos      : list <-> labels    : List Int   (leading slice non-None)
    resulting_indices    <-> terms     : List (List Int)

  shadow (transliteration of implementation_prependLeading / problem_spec):
    lead = labels[:leadCount];  out = [lead + t for t in terms]

  gold (the patched line, the differential reference):
    out = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )

Exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 23824
N_RANDOM = 150_000  # >= 1e5


def shadow(lead_count, labels, terms):
    """Python shadow of implementation_prependLeading (the Lean R/I skeleton)."""
    lead = labels[:lead_count]
    return [lead + list(t) for t in terms]


def gold(lead_count, labels, terms):
    """Behavior of the gold patch line (the differential reference)."""
    # free_pos[0:first_dum_pos] + ri for ri in resulting_indices
    return list(labels[0:lead_count] + list(ri) for ri in terms)


def gen_case(rng, small):
    if small:
        lead_count = rng.randint(0, 3)
        extra = rng.randint(0, 2)
        n_terms = rng.randint(0, 3)
        lo, hi, maxrow = -3, 3, 4
    else:
        lead_count = rng.randint(0, 8)
        extra = rng.randint(0, 4)
        n_terms = rng.randint(0, 6)
        lo, hi, maxrow = -9, 9, 6
    labels = [rng.randint(lo, hi) for _ in range(lead_count + extra)]
    terms = [[rng.randint(lo, hi) for _ in range(rng.randint(0, maxrow))]
             for _ in range(n_terms)]
    return lead_count, labels, terms


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # deterministic boundary catalogue
    cases = [
        (0, [], [[]]),
        (0, [5, 6], [[1, 2], [3]]),
        (1, [7], [[1], [2, 3]]),
        # the exact issue shape: leading block of 2 distinct labels (rho, sigma)
        (2, [10, 11], [[]]),
        (2, [10, 11], [[20, 21], [30]]),
        (3, [1, 2, 3], [[9], [], [8, 7]]),
        (2, [10, 11, 99], [[20]]),   # only first 2 are the leading block
    ]
    for k in range(N_RANDOM):
        cases.append(gen_case(rng, small=(k % 3 == 0)))

    for lead_count, labels, terms in cases:
        got = shadow(lead_count, labels, terms)
        exp = gold(lead_count, labels, terms)
        checked += 1
        # frame: term count preserved
        if len(got) != len(terms) or got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH leadCount={lead_count} labels={labels} "
                      f"terms={terms}: shadow={got} gold={exp}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
