#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model of the array-form composition
against the REAL repo callee `Permutation.__mul__(...).array_form`.

The proof of `correct_mul` consumes NO callee axiom (the axioms region of
Solution.lean is empty). But the array-form composition is modeled DEEPLY in Lean
(`completeTo` / `composeArr`) rather than concretely re-derived elsewhere, so it
is an A-reference (refinement.md rows 4-5): the Lean composition is asserted to
agree, element-for-element, with the real `Permutation.__mul__` array form on
boundaries + fuzz. This guards the deep model against drift from the real product.

Runs INSIDE the instance image (PYTHONPATH=/testbed). stdlib + sympy only.
exit 0 iff the property holds on every observation.
"""
import random
import sys

SEED = 12489


def compose_model(a, b):
    """The Lean `composeArr a b`.

    completeTo b n := b ++ [len(b) .. n-1]      (identity pad up to n)
    composeArr a b := a                              if b == []
                    := [bc[i] for i in a] + bc[len(a):]   where bc = completeTo b len(a)
    `bc.getD i 0` for an in-range index i is just bc[i]; for a valid permutation
    `a` over range(len(a)) every i < len(bc), so the default never fires.
    """
    if not b:
        return list(a)
    n = len(a)
    bc = list(b) + list(range(len(b), n))  # completeTo b n (no-op if len(b) >= n)
    return [bc[i] if i < len(bc) else 0 for i in a] + bc[n:]


def real_compose(a, b):
    """REAL repo callee: the array form of Permutation(a) * Permutation(b)."""
    from sympy.combinatorics.permutations import Permutation
    pa = Permutation(list(a))
    pb = Permutation(list(b))
    return list((pa * pb).array_form)


def rand_perm(rng, n):
    p = list(range(n))
    rng.shuffle(p)
    return p


def main() -> int:
    rng = random.Random(SEED)

    cases = []
    # Boundary: empty, singletons, identity, swaps, mismatched sizes.
    cases += [
        ([], []),
        ([0], [0]),
        ([1, 0], [1, 0]),
        ([0, 1, 2], [2, 1, 0]),
        ([1, 0, 2], [0, 2, 1]),
        ([1, 2, 3, 0], [3, 2, 1, 0]),
        ([1, 0, 2], [1, 0]),         # right shorter (needs identity pad)
        ([1, 0], [2, 1, 0, 3]),      # right longer
        ([0, 1, 2, 3, 4], []),       # empty right operand
    ]
    # Fuzz: random valid permutations of varied (possibly unequal) sizes.
    for _ in range(50_000):
        na = rng.randint(0, 8)
        nb = rng.randint(0, 8)
        cases.append((rand_perm(rng, na), rand_perm(rng, nb)))

    mismatches = 0
    examples = []
    for a, b in cases:
        try:
            want = real_compose(a, b)
        except Exception as e:
            # The real callee should not raise on valid permutations; if it does,
            # that is itself a model-boundary signal.
            mismatches += 1
            if len(examples) < 10:
                examples.append((a, b, "EXC:" + type(e).__name__, None))
            continue
        got = compose_model(a, b)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append((a, b, got, want))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs real Permutation.__mul__")
        for a, b, g, w in examples:
            print(f"  a={a} b={b} model={g} real={w}")
        return 1

    print(f"G-AX OK: composeArr == Permutation.__mul__().array_form on "
          f"{len(cases)} probes (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
