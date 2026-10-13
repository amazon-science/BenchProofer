#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19783 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `daggerProduct` /
              `identityProduct` impl regions, transliterated to Python over the
              *real* repo objects, via the mapping.md bijection
              (QExpr ↔ symbolic quantum object). The kind-membership tests the
              dispatch consults (is `other` an operator? a conjugate object? the
              identity?) are A-reference deep models; in the shadow they are left
              as the REAL repo callee (`isinstance` against the real classes),
              per §4.1. The fall-through product is realized as the real
              constructor CALL `Mul(self, other)` with default evaluation —
              the result-side realization of `QExpr.mul` (mapping.md §2) —
              so any normalization the real constructor applies is inherited.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched `Dagger.__mul__` and
              `IdentityOperator.__mul__`, invoked directly on the same operands
              (the real correctness oracle, G-RESOLVE).

They must agree (sympy `==`) on the resulting expression for every input. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), sympy +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 19783
N_FUZZ = 100_000

from sympy import Mul
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger


# --- the mapping.md bijection: QExpr value  ->  real sympy object -------------
# QExpr.op name   <->  Operator(name)
# QExpr.ident     <->  IdentityOperator()
# QExpr.dag (op)  <->  Dagger(Operator(name))   (dag wraps a plain operator so
#                       the image is a genuine conjugate object; mapping.md §2)
# QExpr.mul a b   <->  Mul(<a>, <b>, evaluate=False) as INPUT data;
#                       as a dispatch RESULT it is the real constructor call
#                       Mul(<a>, <b>) with default evaluation (mapping.md §2)
def gen_qexpr(rng, depth):
    """Generate a random sympy object drawn from the QExpr carrier image."""
    kinds = ["op", "ident", "dag", "mul"] if depth > 0 else ["op", "ident", "dag"]
    k = rng.choice(kinds)
    if k == "op":
        return Operator(rng.choice(["A", "B", "C", "O", "X"]))
    if k == "ident":
        return IdentityOperator()
    if k == "dag":
        # dag wraps a plain operator -> a genuine Dagger object
        return Dagger(Operator(rng.choice(["A", "B", "C", "O", "X"])))
    # mul: unevaluated product of two sub-expressions
    a = gen_qexpr(rng, depth - 1)
    b = gen_qexpr(rng, depth - 1)
    return Mul(a, b, evaluate=False)


# --- the R/I shadow: the do blocks, transliterated ---------------------------
def shadow_dagger_product(self_, other):
    """R/I shadow of `daggerProduct` (self is a conjugate object): collapse to
    `self` when `other` is the identity operator, else the ordinary product
    (real constructor call, default evaluation — result-side `QExpr.mul`).
    `isIdentityClass other` is the A-reference, left as the real callee."""
    if isinstance(other, IdentityOperator):          # isIdentityClass other
        return self_
    return Mul(self_, other)                          # QExpr.mul self other


def shadow_identity_product(self_, other):
    """R/I shadow of `identityProduct` (self is the identity operator): collapse
    to `other` when `other` is an operator OR a conjugate object, else the
    ordinary product (real constructor call, default evaluation).
    `isOperatorClass`/`isDaggerClass` are A-references, left as real callees."""
    if isinstance(other, (Operator, Dagger)):        # isOperatorClass||isDaggerClass
        return other
    return Mul(self_, other)


# --- the oracle: patch.diff's gold __mul__ dispatch --------------------------
def oracle_dagger_product(self_, other):
    """patch.diff's `Dagger.__mul__` (the conjugate object's product)."""
    return self_.__mul__(other)


def oracle_identity_product(self_, other):
    """patch.diff's `IdentityOperator.__mul__` (the identity's product)."""
    return self_.__mul__(other)


def main():
    rng = random.Random(SEED)
    disagreements = []

    # boundary inputs covering every kind-class of `other`
    O = Operator("A")
    I = IdentityOperator()
    dO = Dagger(Operator("A"))
    boundary = [O, I, dO, Mul(O, O, evaluate=False), Dagger(Operator("B"))]

    n = 0

    def check(self_, other, shadow_fn, oracle_fn, tag):
        nonlocal n
        n += 1
        s = shadow_fn(self_, other)
        o = oracle_fn(self_, other)
        if s != o:
            disagreements.append((tag, repr(self_), repr(other), repr(s), repr(o)))

    # boundary sweep for both methods
    for other in boundary:
        check(dO, other, shadow_dagger_product, oracle_dagger_product, "dagger")
        check(I, other, shadow_identity_product, oracle_identity_product, "ident")

    # randomized fuzz
    while n < N_FUZZ:
        other = gen_qexpr(rng, 3)
        self_d = Dagger(Operator(rng.choice(["A", "B", "C"])))
        check(self_d, other, shadow_dagger_product, oracle_dagger_product, "dagger")
        if n >= N_FUZZ:
            break
        check(I, other, shadow_identity_product, oracle_identity_product, "ident")

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) (seed=%d):" % (len(disagreements), SEED))
        for d in disagreements[:20]:
            print("  ", d)
        sys.exit(1)

    print("G-CONF OK: R/I shadow of daggerProduct/identityProduct agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements." % (n, SEED))
    sys.exit(0)


if __name__ == "__main__":
    main()
