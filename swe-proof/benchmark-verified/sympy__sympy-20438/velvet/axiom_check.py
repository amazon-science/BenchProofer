#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20438 (plan §4).

The only kind-A obligation in this bundle is an **A-reference**: the deep model
of three-valued conjunction in Solution.lean's `pure` region
(`tand2` / `triAll`) must equal the REAL three-valued conjunction primitive the
patch composes, `sympy.core.logic.fuzzy_and` (unchanged by the patch). There are
NO consumed axioms.

We execute the real `fuzzy_and` on fuzzed iterables of three-valued truths
(`{True, False, None}`) — including the empty conjunction, all-True, single
definite-False, single unknown, and mixed orders at every length up to 8 — and
assert it equals the deep model (`tri_all`, mirroring `triAll`). The binary
reducer `tand2` is checked separately on the full 3×3 table. Because
`fuzzy_and` internally applies `fuzzy_bool` to each argument and `fuzzy_bool`
is the identity on genuine `True/False/None`, feeding three-valued literals is
an exact bridge (mapping.md §3.1).

Imports only `sympy.core.logic.fuzzy_and` — the same primitive the gold patch
calls. Runs in-container (PYTHONPATH=/testbed). Exit 0 iff every obligation
holds. Seed pinned (mapping.md §4).
"""
import itertools
import random
import sys

THREE = [True, False, None]


# --- deep model: Python mirror of Solution.lean `tand2` / `triAll` -----------

def tand2(x, y):
    """Mirror of Solution.lean `tand2` over Option Bool == {True,False,None}.
    false dominates (even vs unknown); else unknown dominates; else true."""
    if x is False:
        return False
    if y is False:
        return False
    if x is None:
        return None
    if y is None:
        return None
    return True


def tri_all(xs):
    """Mirror of Solution.lean `triAll`: front-recursive fold, identity True."""
    acc = True
    for c in reversed(xs):      # right-fold; tand2 is commutative in result
        acc = tand2(c, acc)
    return acc


def main():
    from sympy.core.logic import fuzzy_and       # the REAL unchanged callee

    checked = 0
    disagreements = []

    # --- tand2 binary reducer: full 3x3 table vs fuzzy_and of the pair --------
    for x in THREE:
        for y in THREE:
            real = fuzzy_and([x, y])
            model = tand2(x, y)
            checked += 1
            if real != model:
                disagreements.append(("tand2", (x, y), model, real))

    # --- triAll fold: boundary lists ----------------------------------------
    boundary = [
        [],                       # empty conjunction -> True
        [True], [False], [None],
        [True, True], [True, False], [True, None],
        [False, None], [None, False],     # False must dominate None
        [True, True, True],
        [True, None, True],
        [True, False, None],
        [None, None, None],
        [False, False, False],
        [True] * 8,
    ]
    for xs in boundary:
        real = fuzzy_and(list(xs))
        model = tri_all(xs)
        checked += 1
        if real != model:
            disagreements.append(("triAll", tuple(xs), model, real))

    # --- triAll fold: exhaustive over all lengths up to 4 --------------------
    for n in range(0, 5):
        for combo in itertools.product(THREE, repeat=n):
            xs = list(combo)
            real = fuzzy_and(list(xs))
            model = tri_all(xs)
            checked += 1
            if real != model:
                disagreements.append(("triAll-exhaustive", combo, model, real))

    # --- triAll fold: randomized fuzz, lengths up to 8 -----------------------
    rng = random.Random(20438)
    for _ in range(20000):
        n = rng.randint(0, 8)
        xs = [rng.choice(THREE) for _ in range(n)]
        real = fuzzy_and(list(xs))
        model = tri_all(xs)
        checked += 1
        if real != model:
            disagreements.append(("triAll-fuzz", tuple(xs), model, real))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-AX FAIL: %d deep-model disagreement(s) over %d checks:"
              % (len(disagreements), checked))
        for who, inp, model, real in disagreements:
            print("  %s input=%r model=%r real_fuzzy_and=%r"
                  % (who, inp, model, real))
        return 1

    print("G-AX OK: tand2/triAll deep model (== sympy.core.logic.fuzzy_and) "
          "sound on the full binary table, all lists up to length 4, %d "
          "boundary lists, and 20000 fuzz lists (seed=20438); %d checks, 0 "
          "disagreements." % (len(boundary), checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
