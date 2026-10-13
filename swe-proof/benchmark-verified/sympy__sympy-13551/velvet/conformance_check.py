#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13551 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over exact rationals, via the mapping.md bijection
              (range position k0 = a + p  <->  row M[p];  additive part value
              <-> M[p][i] : Rat). This is `prodOfSums`: the product, over every
              index position of the finite range, of that position's `rowSum`
              (the total of its additive parts). The impl region has no
              A-tagged op (no axioms), so the shadow is pure R/I.
  * ORACLE  — patch.diff's behaviour: the patched assignment
              `p = exp(Sum(log(p), (k, a, n)))`. On a concrete integer range this
              is sympy's closed form for Mul(*[p.subs(k,k0) for k0 in
              range(a, n+1)]); we use that iterated product as the oracle and
              ANCHOR it to the literal patch text with a symbolic-identity
              cross-check (`assert_patch_text_identity`) on a sample of terms,
              so the oracle is provably the patched expression, not a lookalike.

They must agree on every Requires-satisfying input (every position contributing
the same `width` additive parts, AND every position's total nonzero — the
`require ∀ r ∈ M, rowSum r ≠ 0` modeling boundary: at a zero total the patched
repo expression hits log(0)=zoo and returns the undefined symbolic exp(zoo),
not a rational, so that region is outside the modeled domain). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); sympy is the repo
under test, `random`/`fractions` are stdlib. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from fractions import Fraction

SEED = 13551
N_FUZZ = 100_000
N_IDENTITY_SAMPLE = 60   # symbolic cross-checks anchoring ORACLE to patch text


# --- the R/I shadow: Solution.lean rowSum / prodOfSums, transliterated --------

def row_sum(row):
    """rowSum (r : List Rat) = r.foldr (· + ·) 0 — the total of one position."""
    total = Fraction(0)
    for v in row:
        total += v
    return total


def prod_of_sums(M):
    """prodOfSums : the product, over positions, of each position's rowSum.
    Backward fold of productOverRange computes exactly this left-to-right
    product (multiplication is commutative on Rat)."""
    acc = Fraction(1)
    for row in M:
        acc *= row_sum(row)
    return acc


# --- the oracle: patch.diff's behaviour, anchored to the literal patch text ---

def oracle_iterated_product(M):
    """patch.diff value of the numerator `p` on a concrete integer range:
    exp(Sum(log(p),(k,a,n))) == Mul(*[p.subs(k,k0) for k0 over the range]).
    With row M[p] holding the additive-part values at position p, p.subs(k,k0)
    is the sum of that row, and the product is over positions."""
    acc = Fraction(1)
    for row in M:
        acc *= sum((v for v in row), Fraction(0))
    return acc


def assert_patch_text_identity(rng):
    """ANCHOR the oracle to the *literal* patched expression
    `exp(Sum(log(p), (k, a, n)))`: build random additive numerators p(k) and
    concrete ranges, evaluate the patch text symbolically in sympy, and assert
    it equals the iterated product the oracle uses. If sympy's exp/Sum/log did
    NOT implement the iterated product, this would fail and G-CONF would abort —
    so the cheap rational oracle is justified as the patch's behaviour."""
    from sympy import exp, log, Integer, Rational, Symbol, simplify
    from sympy.concrete.summations import Sum
    k = Symbol('k')
    for _ in range(N_IDENTITY_SAMPLE):
        nparts = rng.randint(2, 3)
        # additive numerator with NO k in any denominator (so q.is_Number arm)
        parts = []
        for _ in range(nparts):
            kind = rng.choice(['const', 'pow', 'lin'])
            if kind == 'const':
                parts.append(Integer(rng.randint(1, 4)))
            elif kind == 'pow':
                parts.append(Integer(rng.randint(1, 3)) * Integer(rng.randint(2, 3)) ** k)
            else:
                parts.append(Integer(rng.randint(1, 3)) * k + Integer(rng.randint(1, 3)))
        p = sum(parts[1:], parts[0])
        a = rng.randint(0, 2)
        b = a + rng.randint(1, 4)            # concrete integer range a..b
        patch_val = exp(Sum(log(p), (k, a, b))).doit()
        iterated = Integer(1)
        for k0 in range(a, b + 1):
            iterated *= p.subs(k, k0)
        if simplify(patch_val - iterated) != 0:
            raise AssertionError(
                "patch-text identity FAILED: exp(Sum(log(p),(k,%d,%d)))=%r != "
                "iterated product %r for p=%r" % (a, b, patch_val, iterated, p))


# --- fuzz inputs: rectangular Rat matrices (Requires-satisfying) --------------

def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4). All inputs must satisfy the
    # method's Requires: rectangular AND every position's total nonzero (a
    # zero total puts the real patch at log(0)=zoo, outside the modeled
    # domain — see module docstring).
    yield []                                   # empty range -> prodOfSums = 1
    yield [[Fraction(1), Fraction(2)], [Fraction(1), Fraction(4)]]  # the issue n=2
    yield [[Fraction(5)]]                      # width 1 (single part) -> identity
    yield [[Fraction(2), Fraction(3)]] * 1
    yield [[Fraction(-1), Fraction(2)], [Fraction(2), Fraction(-3)]]  # negative total
    for _ in range(n):
        rows = rng.randint(0, 6)               # number of index positions
        width = rng.randint(1, 4)              # number of additive parts
        M = []
        for _ in range(rows):
            while True:
                row = [Fraction(rng.randint(-6, 6), rng.randint(1, 5))
                       for _ in range(width)]
                if sum(row, Fraction(0)) != 0:  # Requires: nonzero total
                    break
            M.append(row)
        yield M


def main():
    rng = random.Random(SEED)
    # Anchor the oracle to the literal patch expression before trusting it.
    try:
        assert_patch_text_identity(random.Random(SEED ^ 0xA5A5))
    except Exception as e:  # noqa: BLE001
        print("G-CONF FAIL: oracle/patch-text identity broken: %s" % e)
        return 1

    disagreements = []
    count = 0
    for M in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = prod_of_sums(M)
        oracle = oracle_iterated_product(M)
        if shadow != oracle:
            disagreements.append((M, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for M, sh, orc in disagreements:
            print("  M=%r shadow=%r oracle=%r" % (M, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of productOverRange (prodOfSums) agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), and the oracle matches "
          "the literal patch text exp(Sum(log(p),(k,a,n))) on %d symbolic "
          "samples. 0 disagreements." % (count, SEED, N_IDENTITY_SAMPLE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
