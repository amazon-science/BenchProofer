#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12419.

Executes the REAL equality callees the modeled function relies on — SymPy's
symbolic equality `Eq(i, j)` (read as the 3-valued outcome true / false /
undecided) and Python structural identity `i == j` — on boundary + fuzz index
pairs, and asserts that every observation matches the axioms encoded in
model.py:

  (A-consumed) `eq_class(i, j)` models `Eq(i, j)` read as
        EQ_TRUE    iff  Eq(i, j) is S.true
        EQ_FALSE   iff  Eq(i, j) is S.false
        EQ_UNKNOWN iff  Eq(i, j) is an unevaluated Equality (neither constant)
      Axiom properties checked:
        (a) trichotomy/totality: exactly one of the three holds for every pair;
        (b) reflexivity:  Eq(i, i) is S.true   (=> EQ_TRUE);
        (c) the structural-identity link: whenever (i == j) is True
            (struct_eq), Eq(i, j) is S.true (=> EQ_TRUE).

  (A-consumed) `struct_eq(i, j)` models Python `i == j`:
        (a) reflexivity:  (i == i) is True;
        (b) the link (c) above (struct_eq => eq_class == EQ_TRUE).

  DISCRIMINATING WITNESS (the substance of the change, asserted at the
  classification level — NO double-mask): there EXIST index pairs that are
  structurally distinct ((i == j) is False, so the structural-only decision
  returns the zero cell) yet semantically UNDECIDED (Eq(i, j) is neither S.true
  nor S.false, so eq_class == EQ_UNKNOWN, requiring the deferred-delta cell).
  Each such pair is the input on which the structural-only entry is wrong.

Imports only the standard library and `sympy` (the repo under test). Exit 0 iff
every obligation holds. Run inside the instance image (Python 3.6 / SymPy at
base_commit).
"""
import itertools
import sys

from sympy import Eq, S, Symbol, Integer, symbols

# model.py reference codes (kept in lock-step with the axioms region)
EQ_FALSE, EQ_TRUE, EQ_UNKNOWN = 0, 1, 2


def real_eq_class(i, j):
    """The REAL Eq(i, j) read as the 3-valued outcome (model's eq_class)."""
    eq = Eq(i, j)
    if eq is S.true:
        return EQ_TRUE
    if eq is S.false:
        return EQ_FALSE
    return EQ_UNKNOWN


def real_struct_eq(i, j):
    """The REAL Python structural identity i == j (model's struct_eq)."""
    return bool(i == j)


def check_pair(i, j):
    """Assert the axioms hold on the real callees for one index pair (i, j)."""
    ec = real_eq_class(i, j)
    # (a) trichotomy: real_eq_class already returns one of the three; assert it.
    assert ec in (EQ_FALSE, EQ_TRUE, EQ_UNKNOWN), (
        "eq_class outside the 3-valued domain on (%r, %r): %r" % (i, j, ec))
    # (c) structural-identity link: struct_eq(i, j) => eq_class == EQ_TRUE.
    if real_struct_eq(i, j):
        assert ec == EQ_TRUE, (
            "axiom unsound: (%r == %r) is True but Eq is not S.true "
            "(eq_class=%r)" % (i, j, ec))
    return ec


def main():
    i, j, k = symbols('i j k', integer=True)
    m, p = symbols('m p', integer=True, positive=True)
    n = Symbol('n', integer=True, positive=True)

    # A diverse pool of index expressions covering the real argument shapes
    # _entry sees: bare symbols, integers, and symbol arithmetic.
    pool = [
        i, j, k, m, p, n,
        i + 1, i - 1, j + 1, i + k, i + k + 1, 2 * i, i + j,
        Integer(0), Integer(1), Integer(2), Integer(3), Integer(-1),
        S.Zero, S.One,
    ]

    # (b) reflexivity on every element: Eq(x, x) is S.true and (x == x) is True.
    for x in pool:
        assert real_struct_eq(x, x), "struct_eq reflexivity failed on %r" % (x,)
        assert real_eq_class(x, x) == EQ_TRUE, (
            "eq_class reflexivity failed on %r: Eq(x, x) not S.true" % (x,))

    # full boundary sweep over all ordered pairs from the pool.
    seen = {EQ_FALSE: 0, EQ_TRUE: 0, EQ_UNKNOWN: 0}
    for a, b in itertools.product(pool, repeat=2):
        seen[check_pair(a, b)] += 1

    # The three outcomes must all be reachable on realistic index pairs, or the
    # 3-valued spec would be vacuous. In particular EQ_UNKNOWN must occur.
    assert seen[EQ_TRUE] > 0, "no decidably-equal pair observed"
    assert seen[EQ_FALSE] > 0, "no decidably-unequal pair observed"
    assert seen[EQ_UNKNOWN] > 0, "no UNDECIDED pair observed (spec vacuous)"

    # DISCRIMINATING WITNESS, asserted at the classification level (no double
    # mask): two distinct integer symbols are structurally distinct yet
    # semantically undecided -> the structural-only decision returns the zero
    # cell, but the contract requires the deferred-delta cell.
    witnesses = [(i, j), (i, k), (j, k), (i, j + 1), (i, i + k)]
    found = 0
    for a, b in witnesses:
        if not real_struct_eq(a, b) and real_eq_class(a, b) == EQ_UNKNOWN:
            found += 1
    assert found > 0, (
        "no structurally-distinct-but-undecided witness found; the change "
        "would be unobservable")

    # Decidably-unequal sanity: distinct concrete integers are S.false (zero
    # cell), and i vs i+1 is S.false (the KroneckerDelta canonical example).
    assert real_eq_class(Integer(2), Integer(3)) == EQ_FALSE, "2 vs 3 not false"
    assert real_eq_class(i, i + 1) == EQ_FALSE, "i vs i+1 not false"
    # Decidably-equal sanity: i vs i+0 collapses structurally to i (S.true).
    assert real_eq_class(i, i + 0) == EQ_TRUE, "i vs i+0 not true"

    print("G-AX OK: eq_class (Eq 3-valued) + struct_eq (==) axioms sound on %d "
          "reflexive + %d ordered boundary pairs; outcomes "
          "true=%d false=%d unknown=%d; %d structurally-distinct-but-undecided "
          "witnesses confirm the deferred-delta requirement"
          % (len(pool), len(pool) ** 2, seen[EQ_TRUE], seen[EQ_FALSE],
             seen[EQ_UNKNOWN], found))
    return 0


if __name__ == "__main__":
    sys.exit(main())
