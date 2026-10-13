#!/usr/bin/env python3
"""G-AX soundness check for sympy__sympy-19783 (plan §4, SPEC_GUIDE §3).

This bundle ships NO consumed axioms. The only borrowed facts are the
A-reference deep models of the object-hierarchy membership tests that the
product dispatch consults:

    isOperatorClass(e)  ==  isinstance(<e>, (Operator,))-as-an-operator
    isDaggerClass(e)    ==  isinstance(<e>, Dagger)
    isIdentityClass(e)  ==  isinstance(<e>, IdentityOperator)

where `<e>` is the real sympy object the QExpr value `e` maps to (mapping.md §2).
G-AX validates the A-reference: each deep-model predicate equals the real
library membership test on every kind in the carrier image, over boundary +
fuzz. stdlib + sympy only; exit 0 iff every observation matches.
"""
import random
import sys

SEED = 19783
N_FUZZ = 20_000

from sympy import Mul
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger


# --- the Lean deep models (transliterated) -----------------------------------
def is_operator_class(e):
    # QExpr.op _ => true ; QExpr.ident => true ; _ => false
    return e[0] in ("op", "ident")


def is_dagger_class(e):
    return e[0] == "dag"


def is_identity_class(e):
    return e[0] == "ident"


# --- QExpr value -> real sympy object (mapping.md §2 bijection) ---------------
def realize(e):
    k = e[0]
    if k == "op":
        return Operator(e[1])
    if k == "ident":
        return IdentityOperator()
    if k == "dag":
        return Dagger(Operator(e[1]))
    if k == "mul":
        return Mul(realize(e[1]), realize(e[2]), evaluate=False)
    raise ValueError(k)


def gen(rng, depth):
    kinds = ["op", "ident", "dag", "mul"] if depth > 0 else ["op", "ident", "dag"]
    k = rng.choice(kinds)
    if k == "op":
        return ("op", rng.choice(["A", "B", "C", "O", "X"]))
    if k == "ident":
        return ("ident",)
    if k == "dag":
        return ("dag", rng.choice(["A", "B", "C", "O", "X"]))
    return ("mul", gen(rng, depth - 1), gen(rng, depth - 1))


def main():
    rng = random.Random(SEED)
    failures = []

    boundary = [
        ("op", "A"), ("ident",), ("dag", "A"),
        ("mul", ("op", "A"), ("op", "B")),
        ("mul", ("dag", "A"), ("ident",)),
    ]

    def check(e):
        obj = realize(e)
        # The real membership tests the dispatch branches on. The identity
        # operator IS an operator (subclass), so the operator-class test is true
        # for it too; that is exactly what is_operator_class models.
        real_op = isinstance(obj, Operator)
        real_dag = isinstance(obj, Dagger)
        real_id = isinstance(obj, IdentityOperator)
        if is_operator_class(e) != real_op:
            failures.append(("isOperatorClass", e, is_operator_class(e), real_op))
        if is_dagger_class(e) != real_dag:
            failures.append(("isDaggerClass", e, is_dagger_class(e), real_dag))
        if is_identity_class(e) != real_id:
            failures.append(("isIdentityClass", e, is_identity_class(e), real_id))

    for e in boundary:
        check(e)
    for _ in range(N_FUZZ):
        check(gen(rng, 3))

    if failures:
        print("G-AX FAIL: %d membership mismatch(es) (seed=%d):" % (len(failures), SEED))
        for f in failures[:20]:
            print("  ", f)
        sys.exit(1)

    print("G-AX OK: isOperatorClass/isDaggerClass/isIdentityClass deep models "
          "(A-reference) match real library isinstance on %d boundary + fuzz "
          "objects (seed=%d)." % (len(boundary) + N_FUZZ, SEED))
    sys.exit(0)


if __name__ == "__main__":
    main()
