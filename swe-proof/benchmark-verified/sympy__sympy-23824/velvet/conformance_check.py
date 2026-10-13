#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23824 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo carrier (the per-term restoration,
              via the mapping.md bijection `List Int` ↔ a `list` of gamma-factor
              index labels). The `restoreLeading` impl region initialises
              `result = tail` and prepends the leading factors in descending
              index order (last leading factor first, front factor last), whose
              net effect is the order-preserving concatenation `leading ++ tail`.
              There is no consumed axiom in the impl region, so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour at the restore-leading site: the rebuilt
              `resulting_indices` entry `free_pos[0:first_dum_pos] + ri`
              (the real correctness oracle, G-RESOLVE), evaluated on the same
              leading run / core term.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

stdlib only; the fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. This site is pure list concatenation, so no repo import is required —
the oracle is the gold hunk's `+` evaluated directly over the carrier.
"""
import random
import sys

SEED = 23824
N_FUZZ = 100_000


def shadow_restore(leading, tail):
    """restoreLeading's impl region transliterated to Python over the carrier:
    start from the core term, then prepend the leading factors in DESCENDING
    index order (i = len(leading) .. 1), each `result = [c] + result`. The net
    effect is the leading run in its original left-to-right order followed by the
    core term."""
    result = list(tail)
    i = len(leading)
    while i > 0:
        c = leading[i - 1]
        result = [c] + result
        i = i - 1
    return result


def oracle_restore(leading, tail):
    """patch.diff's behaviour at the restore-leading site: the rebuilt entry
    `free_pos[0:first_dum_pos] + ri`. Here `leading` plays `free_pos[0:fdp]`
    and `tail` plays `ri`; the gold patch concatenates them with list `+`."""
    return leading[0:len(leading)] + tail


def fuzz_inputs(n, rng):
    # boundary cases first
    yield ([], [])                       # empty leading, empty term
    yield ([], [7, 8])                   # empty leading run (no trailing free)
    yield ([3], [])                      # single leading factor, empty term
    yield ([3, 4], [])                   # multi leading, empty term
    yield ([10, 11], [20, 21])           # the F2P-flavoured witness: rho,sigma
    yield ([11, 10], [20, 21])           # the same factors, swapped
    yield ([1, 2, 3, 4, 5], [9])
    yield (list(range(20)), list(range(20, 25)))
    yield (list(range(20))[::-1], [])
    for _ in range(n):
        kl = rng.randint(0, 30)
        kt = rng.randint(0, 30)
        leading = [rng.randint(-50, 50) for _ in range(kl)]
        tail = [rng.randint(-50, 50) for _ in range(kt)]
        yield (leading, tail)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for leading, tail in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_restore(leading, tail)
        oracle = oracle_restore(leading, tail)
        if shadow != oracle:
            disagreements.append((leading, tail, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ld, tl, sh, orc in disagreements:
            print("  leading=%r tail=%r shadow=%r oracle=%r" % (ld, tl, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of restoreLeading agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
