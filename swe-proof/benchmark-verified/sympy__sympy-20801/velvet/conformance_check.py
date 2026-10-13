#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20801 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`equalsOperand` / `floatEq`) transliterated to Python over the
              *real* repo types, via the mapping.md bijection:
                self  : Float          ↔ selfVal : Int   (exact value; 0 ⇔ zero)
                other : SymPy object   ↔ o : Operand     (logical/numeric/symbolic)
              classified by exactly the predicates `Float.__eq__` uses
              (`isinstance(other, Boolean)` / `is_Number*`). No callee is
              axiomatized (mapping.md §3) — the whole impl region is R/I, so the
              shadow is pure R/I and there is no A leg to exclude.
  * ORACLE  — `patch.diff`'s behaviour: the patched `sympy ...Float.__eq__`
              applied at base_commit (the real correctness oracle, G-RESOLVE).
              The harness applies patch.diff before this runs; we import sympy.

They must agree on every modeled input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 20801
N_FUZZ = 100_000

# --- the type bijection (mapping.md §2) --------------------------------------
# An operand is classified into one of three kinds by exactly the predicates the
# method dispatches on, carrying the field floatEq reads:
#   logical  -> (kind="logical",  t=bool(other))      isinstance(other, Boolean)
#   numeric  -> (kind="numeric",  m=int(other))       other.is_Number (+NumberSymbol)
#   symbolic -> (kind="symbolic", t=bool(other))      everything else (tail)
#
# We only construct numeric operands with exact integer value so the Int proxy
# `selfVal`/`m` is a faithful bijection of the mpf value (mapping.md §2: distinct
# mpf -> distinct Int; the comparison is exact).


def classify(other):
    """Bridge a real SymPy operand to its Operand ctor by the SAME predicates
    Float.__eq__ uses, returning (kind, payload)."""
    from sympy.logic.boolalg import Boolean
    from sympy.core.numbers import Number
    if isinstance(other, Boolean):
        return ("logical", bool(other))
    # is_NumberSymbol / is_Float / is_Rational / is_Number  -> the numeric ladder.
    # We restrict the fuzz corpus to integer-valued numerics so int() is exact.
    if getattr(other, "is_Number", False) or getattr(other, "is_NumberSymbol", False):
        return ("numeric", int(other))
    return ("symbolic", bool(other))


# --- the R/I shadow: equalsOperand / floatEq, transliterated -----------------
def shadow_eq(self_val, other):
    """floatEq selfVal o, transliterated. selfVal = int(self) (the exact value;
    0 iff the zero float)."""
    kind, payload = classify(other)
    if kind == "logical":
        return False                      # .logical _ => false
    if kind == "numeric":
        return self_val == payload        # .numeric m => decide (selfVal = m)
    # .symbolic t => if selfVal = 0 then !t else false
    if self_val == 0:
        return not payload
    return False


def oracle_eq(self_float, other):
    """patch.diff's behaviour: the patched Float.__eq__ at base_commit."""
    return bool(self_float == other)


# --- fuzz corpus -------------------------------------------------------------
def operand_corpus():
    """Real SymPy operands spanning all three kinds + boundaries.

    The numeric kind is restricted to operands with an EXACT integer value: the
    `numeric m : Int` carrier (mapping.md §2) is the integer-valued-number
    fragment, where the Int proxy is a faithful bijection of the mpf value
    (distinct value -> distinct Int). Irrational NumberSymbols (pi, GoldenRatio)
    have no integer exact value, so they are outside this Int model and are
    deliberately NOT bridged here (int(other) would be lossy). The patch does not
    touch the numeric branch, so this modeled-domain boundary hides no behavior.
    """
    from sympy import S, Integer, Rational, Float, Symbol, sqrt
    ops = []
    # logical constants (isinstance(other, Boolean))
    ops.append(S.true)
    ops.append(S.false)
    # numerics with exact integer value (Int proxy faithful: is_Number ladder)
    for v in (-3, -1, 0, 1, 2, 5, 7):
        ops.append(Integer(v))
        ops.append(Float(float(v)))
    # Rationals that are integer-valued keep the Int bijection exact
    ops.append(Rational(4, 2))   # == 2
    ops.append(Rational(-6, 3))  # == -2
    # symbolic (non-Boolean, non-Number): falls to the tail
    ops.append(Symbol("x"))
    ops.append(Symbol("y"))
    ops.append(sqrt(2))          # is_Number=False, is_NumberSymbol=False
    return ops


def self_values():
    """Integer-valued Floats whose exact value is the Int proxy selfVal."""
    return [0, 1, -1, 2, -2, 5, 7, -3]


def main():
    try:
        from sympy import Float, Integer, sqrt, pi
    except Exception as e:  # pragma: no cover
        print("G-CONF ERROR: sympy import failed: %r" % (e,))
        return 2

    rng = random.Random(SEED)
    operands = operand_corpus()
    selves = self_values()
    self_floats = {v: Float(float(v)) for v in selves}

    disagreements = []
    count = 0

    # 1. exhaustive boundary matrix: every (self, operand) pair
    pairs = [(v, o) for v in selves for o in operands]

    # 2. fuzz: random (self, operand) draws to N_FUZZ
    while len(pairs) < N_FUZZ:
        v = rng.choice(selves)
        o = rng.choice(operands)
        pairs.append((v, o))

    for v, o in pairs:
        count += 1
        self_f = self_floats[v]
        try:
            shadow = shadow_eq(v, o)
            oracle = oracle_eq(self_f, o)
        except Exception as e:
            disagreements.append((v, o, "EXC:%r" % (e,), None))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((v, o, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, o, sh, orc in disagreements:
            print("  selfVal=%r operand=%r shadow=%r oracle=%r" % (v, o, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of equalsOperand agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
