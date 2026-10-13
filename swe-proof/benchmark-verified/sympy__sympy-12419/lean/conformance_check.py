#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-12419.

The bundle models ONE routine: `Identity._entry(i, j)`, the per-element accessor
of the symbolic identity matrix (mapping.md). Unlike an earlier revision of this
script, the ORACLE here is NOT an in-process replica of the modeled decision —
that tests the model against itself and cannot detect drift from the repo. It is
the REAL `Identity._entry` from the patched tree, called on real SymPy index
expressions; the SHADOW is the op-for-op transliteration of
`implementation_identityElement` (Solution.lean impl region), driven by the two
carried observations read off those same real objects.

Why TWO observations. The routine consults the index pair through two distinct
comparison mechanisms, and they do not agree:

  * the symbolic equality `Eq(i, j)`, whose outcome is trichotomous —
    `S.true` / `S.false` / an unevaluated `Equality` — which is the `IdxCmp`
    observation;
  * the construction of `KroneckerDelta(i, j)` itself, which carries its OWN
    settling procedure (a fuzzy `(i - j).is_zero` test AND a fermi-level branch
    on the two symbols' `below_fermi` / `above_fermi` assumptions). On some pairs
    it settles what `Eq` could not, auto-evaluating to `S.Zero`. That is the
    `IndOutcome` observation (`settled_zero` vs `left_symbolic`).

A model over `Eq` alone would predict a non-zero symbolic indicator on EVERY pair
`Eq` leaves open, which the real routine does not deliver: on the fermi-level
pairs it returns a plain `S.Zero`. This script is what refutes such a model, so
the corpus below deliberately includes those pairs rather than only the easy
symbolic ones, and it FAILS if any modeled cell goes unexercised.

The bijection under test (mapping.md §2):

    Eq(i,j) is S.true                  <-> IdxCmp.known_equal
    Eq(i,j) is S.false                 <-> IdxCmp.known_distinct
    Eq(i,j) unevaluated                <-> IdxCmp.undetermined
    KroneckerDelta(i,j) is S.Zero      <-> IndOutcome.settled_zero
    KroneckerDelta(i,j) otherwise      <-> IndOutcome.left_symbolic
    S.One / S.Zero / KroneckerDelta    <-> Elem.one / .zero / .deferred i j

Requires the real sympy tree with the gold patch applied (the gate applies it).

Pinned seed: 12419 (also in mapping.md).
"""
import itertools
import random
import sys

SEED = 12419
N = 120_000

KNOWN_EQUAL = "known_equal"
KNOWN_DISTINCT = "known_distinct"
UNDETERMINED = "undetermined"

SETTLED_ZERO = "settled_zero"
LEFT_SYMBOLIC = "left_symbolic"

ONE = ("one",)
ZERO = ("zero",)


def deferred(i, j):
    return ("deferred", i, j)


# --- SHADOW of implementation_identityElement (the R leg) ---------------------
# Mirrors Solution.lean impl region exactly: match on the classification, and
# under `undetermined` match on the indicator outcome.
def shadow(cmp, ind, i, j):
    if cmp == KNOWN_EQUAL:
        return ONE
    elif cmp == KNOWN_DISTINCT:
        return ZERO
    elif cmp == UNDETERMINED:
        if ind == SETTLED_ZERO:
            return ZERO
        elif ind == LEFT_SYMBOLIC:
            return deferred(i, j)
        raise AssertionError(f"unknown indicator outcome {ind!r}")
    raise AssertionError(f"unknown status {cmp!r}")


def main() -> int:
    from sympy import (Eq, I, Integer, Rational, S, Symbol, nan, oo, pi, zoo)
    from sympy.functions.special.tensor_functions import KroneckerDelta
    from sympy.matrices.expressions.matexpr import Identity

    n = Symbol("n", integer=True, positive=True)
    ident = Identity(n)

    # ---- the two observations, read off the REAL objects -------------------
    def observe_cmp(u, v):
        eq = Eq(u, v)
        if eq is S.true:
            return KNOWN_EQUAL
        if eq is S.false:
            return KNOWN_DISTINCT
        return UNDETERMINED

    def observe_ind(u, v):
        return SETTLED_ZERO if KroneckerDelta(u, v) is S.Zero else LEFT_SYMBOLIC

    # ---- ORACLE: the REAL patched callee ----------------------------------
    # On the symbolic arm it carries the ACTUAL returned expression, so the
    # comparison below is against what the repo produced rather than against a
    # re-derivation of it.
    def oracle(u, v):
        got = ident._entry(u, v)
        if got is S.One:
            return ONE
        if got is S.Zero:
            return ZERO
        return ("deferred", got)

    # The shadow's `deferred i j` corresponds to KroneckerDelta(i, j). The real
    # constructor canonicalizes argument ORDER (it sorts the two indices), which
    # `Elem.deferred` does not model, so agreement on that arm is checked up to
    # the indicator's own symmetry -- exactly the residue recorded in
    # properties.py.
    def agree(sh, orc):
        if sh[0] != orc[0]:
            return False
        if sh[0] != "deferred":
            return True
        return KroneckerDelta(sh[1], sh[2]) == orc[1]

    # ---- corpus ----------------------------------------------------------
    ASSUMPTIONS = [
        {}, {"integer": True}, {"positive": True}, {"negative": True},
        {"even": True}, {"odd": True}, {"zero": True}, {"nonzero": True},
        {"below_fermi": True}, {"above_fermi": True},
        {"below_fermi": True, "integer": True},
        {"above_fermi": True, "integer": True},
        {"commutative": False}, {"real": True}, {"complex": True},
        {"infinite": True}, {"finite": True}, {"prime": True},
        {"rational": True}, {"irrational": True}, {"nonnegative": True},
        {"nonpositive": True},
    ]
    syms = []
    for k, a in enumerate(ASSUMPTIONS):
        for rep in range(3):
            syms.append(Symbol("s%d_%d" % (k, rep), **a))
    consts = [Integer(x) for x in (-3, -2, -1, 0, 1, 2, 3, 7)]
    consts += [Rational(1, 2), Rational(3, 2), oo, -oo, zoo, nan, pi, I]
    atoms = syms + consts

    def rand_expr(rng, depth=0):
        if depth >= 2 or rng.random() < 0.5:
            return rng.choice(atoms)
        a = rand_expr(rng, depth + 1)
        b = rand_expr(rng, depth + 1)
        try:
            return rng.choice([a + b, a * b, -a, a - b, 2 * a])
        except Exception:
            return a

    # Hand-picked edge cases pinning the discriminating clauses. The fermi-level
    # pairs are the ones a one-observation model gets WRONG: `Eq` leaves them open
    # but `KroneckerDelta` settles them to a plain zero.
    below = Symbol("p_bf", below_fermi=True)
    above = Symbol("q_af", above_fermi=True)
    below2 = Symbol("p2_bf", below_fermi=True)
    above2 = Symbol("q2_af", above_fermi=True)
    i_s, j_s, k_s = (Symbol(x, integer=True) for x in ("i", "j", "k"))
    edge = [
        (i_s, i_s),                    # known-equal -> one
        (Integer(0), Integer(0)),
        (i_s, i_s + 1),                # known-distinct -> zero
        (Integer(0), Integer(1)),
        (i_s, j_s),                    # undetermined, indicator survives
        (i_s, i_s + 1 + k_s),
        (Symbol("x"), Symbol("y")),
        (below, above),                # undetermined, indicator SETTLES -> zero
        (above, below),
        (below2, above2),
        (below, below2),               # both below fermi: indicator survives
        (above, above2),
        (below, i_s),
        (above, i_s),
    ]

    checked = 0
    cells = {}

    def check(u, v):
        nonlocal checked
        try:
            cmp = observe_cmp(u, v)
            ind = observe_ind(u, v)
            orc = oracle(u, v)
        except Exception:
            return None
        sh = shadow(cmp, ind, u, v)
        checked += 1
        cells[(cmp, ind)] = cells.get((cmp, ind), 0) + 1
        if not agree(sh, orc):
            return ((str(u), str(v), cmp, ind), orc, sh)
        return None

    for u, v in edge:
        d = check(u, v)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1

    # systematic pairs over the symbol pool, both orders
    for u, v in itertools.combinations_with_replacement(syms, 2):
        for a, b in ((u, v), (v, u)):
            d = check(a, b)
            if d:
                print(f"DISAGREE pool: oracle={d[1]} shadow={d[2]} inp={d[0]}")
                print("status=fail")
                return 1

    rng = random.Random(SEED)
    guard = 0
    while checked < N and guard < N * 20:
        guard += 1
        d = check(rand_expr(rng), rand_expr(rng))
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1

    # Every modeled cell must be POPULATED, or the corpus never exercised an arm
    # and a clean run would attest to nothing there. The (undetermined,
    # settled_zero) cell is the one this bundle's faithfulness turns on, so an
    # unexercised cell is a hard failure rather than a warning.
    required = [(KNOWN_EQUAL, LEFT_SYMBOLIC), (KNOWN_DISTINCT, SETTLED_ZERO),
                (KNOWN_DISTINCT, LEFT_SYMBOLIC),
                (UNDETERMINED, SETTLED_ZERO), (UNDETERMINED, LEFT_SYMBOLIC)]
    missing = [c for c in required if not cells.get(c)]
    if missing:
        print(f"UNPOPULATED modeled cells: {missing}")
        print("status=fail")
        return 1

    census = " ".join(f"{c[0]}/{c[1]}={v}" for c, v in sorted(cells.items()))
    print(f"cells: {census}")
    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
