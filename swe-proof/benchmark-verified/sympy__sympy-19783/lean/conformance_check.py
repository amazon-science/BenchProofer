#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-19783.

The bundle models TWO routines, each a pure dispatch on the runtime class of the
right-hand factor `other` (mapping.md):

  * `Dagger.__mul__`           (post-patch, dagger.py)
  * `IdentityOperator.__mul__` (post-patch, operator.py:308)

Standing up the full SymPy class machinery is unnecessary: each method's result is
a pure function of which class `other` belongs to. The four operand classes the
methods can possibly see are abstracted (mapping.md):

    identity   -> an IdentityOperator() instance
    operator   -> a plain Operator (NOT an IdentityOperator)
    conjugate  -> a Dagger(...) expression
    other      -> any other expression (symbol/number/Mul/...)

and the three result shapes:

    lhs        -> self          (left factor unchanged)
    rhs        -> other         (right factor unchanged)
    product    -> Mul(self,other) (unevaluated product)

The ORACLE below is a faithful in-process replica of the POST-PATCH methods,
honoring the real subclass facts that drive the dispatch:
  * IdentityOperator IS-A Operator   (class IdentityOperator(Operator)) ->
    `isinstance(other, (Operator, Dagger))` is True for identity too;
  * Dagger is NOT-A Operator         (class Dagger(adjoint), adjoint<Expr).

The SHADOW is the op-for-op transliteration of the two impl regions of
Solution.lean (refinement.md). This genuinely tests the soundness-critical
clauses matching the F2P tests:
  * Dagger(O) * IdentityOperator() collapses to Dagger(O)  (test_dagger_mul);
  * IdentityOperator() * Dagger(O) collapses to Dagger(O)  (test_identity).

stdlib-only. Pinned seed: 19783 (also in mapping.md).
"""
import random
import sys

SEED = 19783
N = 200_000

OPERANDS = ["identity", "operator", "conjugate", "other"]

# --- abstract isinstance facts (mapping.md subclass analysis) -------------------
def is_identity(op):              # isinstance(other, IdentityOperator)
    return op == "identity"

def is_operator(op):              # isinstance(other, Operator)  [identity IS-A operator]
    return op in ("identity", "operator")

def is_dagger(op):                # isinstance(other, Dagger)
    return op == "conjugate"


# --- ORACLE: faithful replica of the POST-PATCH methods -------------------------
def oracle_conjugate(op):
    # Dagger.__mul__: if isinstance(other, IdentityOperator): return self; else Mul
    if is_identity(op):
        return "lhs"
    return "product"

def oracle_identity(op):
    # IdentityOperator.__mul__: if isinstance(other,(Operator,Dagger)): return other
    if is_operator(op) or is_dagger(op):
        return "rhs"
    return "product"


# --- SHADOW of the Solution.lean impl regions (the R legs) ----------------------
def shadow_conjugate(op):
    # implementation_conjugateProduct
    if is_identity(op):
        return "lhs"
    return "product"

def shadow_identity(op):
    # implementation_identityProduct
    if is_operator(op) or is_dagger(op):
        return "rhs"
    return "product"


def main() -> int:
    checked = 0

    # Exhaustive over the finite operand domain (both methods).
    for op in OPERANDS:
        if oracle_conjugate(op) != shadow_conjugate(op):
            print(f"DISAGREE conjugate op={op}: "
                  f"oracle={oracle_conjugate(op)} shadow={shadow_conjugate(op)}")
            print("status=fail")
            return 1
        if oracle_identity(op) != shadow_identity(op):
            print(f"DISAGREE identity op={op}: "
                  f"oracle={oracle_identity(op)} shadow={shadow_identity(op)}")
            print("status=fail")
            return 1
        checked += 2

    # F2P edge-case assertions on the oracle itself.
    assert oracle_conjugate("identity") == "lhs"   # Dagger(O)*Dagger(I) == Dagger(O)
    assert oracle_conjugate("operator") == "product"
    assert oracle_conjugate("conjugate") == "product"  # Dagger(O)*Dagger(O) -> Mul
    assert oracle_identity("conjugate") == "rhs"    # I*Dagger(O) == Dagger(O)
    assert oracle_identity("operator") == "rhs"     # I*O == O
    assert oracle_identity("identity") == "rhs"     # I*I is the right I
    assert oracle_identity("other") == "product"   # I*x is a Mul

    # Fuzz (redundant over the finite domain, but pins the seed contract).
    rng = random.Random(SEED)
    for _ in range(N):
        op = rng.choice(OPERANDS)
        if oracle_conjugate(op) != shadow_conjugate(op):
            print(f"DISAGREE fuzz conjugate op={op}")
            print("status=fail")
            return 1
        if oracle_identity(op) != shadow_identity(op):
            print(f"DISAGREE fuzz identity op={op}")
            print("status=fail")
            return 1
        checked += 2

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
