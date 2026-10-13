#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19783 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (is_kind /
is_operator_like / is_identity / is_conjugate) copy over as plain functions;
the Product record becomes a plain Python class with the same four fields.
There are no @ContractOnly callees in this bundle (axioms region is empty),
so the shadow is fully executable as-is. No PSeq shim is needed (the model
carries only ints and bools).

ORACLE: the REAL repo methods the model models per mapping.md —
`sympy.physics.quantum.operator.IdentityOperator.__mul__` (site 1) and
`sympy.physics.quantum.dagger.Dagger.__mul__` (site 2). The gate applies the
diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
package importable. This script never applies any diff itself. The methods
are invoked unbound (Cls.__mul__(left, other)) so the check exercises exactly
the modeled functions, independent of Python's binary-operator dispatch.

Type bridge (mapping.md section 2):
  real operand  -> integer kind tag via the same type tests the real methods
                   perform: IdentityOperator -> 1 (checked first: it is an
                   Operator subclass), Dagger -> 2 (NOT an Operator subclass),
                   any other Operator -> 0, everything else -> 3.
  real return   -> Product record: a collapse (the method returned one
                   operand) corresponds to is_mul == False with result_kind
                   the surviving operand's kind; the generic symbolic product
                   corresponds to is_mul == True and concretely equals
                   Mul(left, other) (any downstream canonicalization of that
                   Mul, e.g. same-factor powers, applies identically to the
                   predicted expression, so equality comparison is exact).
  survivor      -> for site 1 the surviving operand of a collapse is the
                   RIGHT operand; for site 2 it is the LEFT operand. The
                   shadow's result_kind is cross-checked against the real
                   survivor's kind on every collapse.
The Requires (is_kind(other_kind)) holds by construction: the classifier
returns only tags in {0,1,2,3}.

>= 1e5 Requires-satisfying inputs: structured boundary cases (every operand
kind against both sites, including same-kind operand pairs and evaluated
adjoints that fold back into other kinds) plus 100000 fuzz rounds over pools
of randomly-built operands of every kind, each round checking BOTH sites.
Pinned fuzz seed: 197830. Exit 0 iff zero disagreements; on disagreement
prints the input and both outcomes and exits 1. stdlib + sympy only.
"""
import json
import random
import sys

SEED = 197830
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped --------------------------

def is_kind(k):
    """A valid operand kind tag."""
    return 0 <= k and k <= 3


def is_operator_like(k):
    """The operand belongs to the operator family (a plain operator or the
    identity element). The conjugate family is deliberately excluded here."""
    return k == 0 or k == 1


def is_identity(k):
    """The operand is the identity element."""
    return k == 1


def is_conjugate(k):
    """The operand is a Hermitian-conjugate factor."""
    return k == 2


# --- the Product record, contracts stripped ----------------------------------

class Product:
    def __init__(self, is_mul, result_kind, left_kind, right_kind):
        self.is_mul = is_mul
        self.result_kind = result_kind
        self.left_kind = left_kind
        self.right_kind = right_kind


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def identity_mul(other_kind):
    """Identity element on the LEFT times an operand of kind ``other_kind``."""
    if is_operator_like(other_kind) or is_conjugate(other_kind):
        return Product(False, other_kind, 1, other_kind)
    return Product(True, other_kind, 1, other_kind)


def dagger_mul(other_kind):
    """Hermitian-conjugate factor (kind 2) on the LEFT times an operand of
    kind ``other_kind``."""
    if is_identity(other_kind):
        return Product(False, 2, 2, other_kind)
    return Product(True, 2, 2, other_kind)


# --- bridge: real SymPy operand <-> model kind tag ---------------------------

def make_real_kind(Operator, IdentityOperator, Dagger):
    def real_kind(expr):
        """Classify a real expression by the same type tests the real methods
        use. Order matters: the identity is itself an Operator subclass, and
        the conjugate wrapper is NOT an Operator subclass."""
        if isinstance(expr, IdentityOperator):
            return 1
        if isinstance(expr, Dagger):
            return 2
        if isinstance(expr, Operator):
            return 0
        return 3
    return real_kind


def check_site(site_name, real_mul, shadow_fn, left, other,
               survivor_side, Mul, real_kind):
    """Run one real product step and diff it against the shadow.

    real_mul: the unbound real method; left: the fixed LHS operand of this
    site; other: the RHS operand; survivor_side: which operand a collapse
    keeps ('left' or 'right'). Returns an error string on disagreement."""
    other_kind = real_kind(other)
    assert is_kind(other_kind)               # Requires holds by construction
    prod = shadow_fn(other_kind)

    # field consistency of the shadow record against the bridge
    left_kind = real_kind(left)
    if prod.left_kind != left_kind or prod.right_kind != other_kind:
        return ("DISAGREEMENT (%s): operand-kind fields\n  left=%r other=%r\n"
                "  shadow (left_kind=%r right_kind=%r) vs real (%r, %r)"
                % (site_name, left, other, prod.left_kind, prod.right_kind,
                   left_kind, other_kind))

    observed = real_mul(left, other)
    if prod.is_mul:
        want = Mul(left, other)
        what = "generic product Mul(left, other)"
    else:
        survivor = left if survivor_side == "left" else other
        want = survivor
        what = "collapse to the %s operand" % survivor_side
        if real_kind(survivor) != prod.result_kind:
            return ("DISAGREEMENT (%s): surviving-operand kind\n"
                    "  left=%r other=%r\n  shadow result_kind=%r vs real "
                    "survivor kind=%r" % (site_name, left, other,
                                          prod.result_kind,
                                          real_kind(survivor)))
    if observed != want:
        return ("DISAGREEMENT (%s):\n  left=%r other=%r (other_kind=%d)\n"
                "  shadow predicts %s = %r\n  real method returned %r"
                % (site_name, left, other, other_kind, what, want, observed))
    return None


def build_pools(rng, real_kind):
    """Pools of real operands, bucketed by their ACTUAL kind tag (some
    constructions fold: an adjoint of the identity IS the identity; an
    adjoint of a Hermitian operator folds back to the operator)."""
    from sympy import (Add, Float, Integer, Rational, Symbol, pi, oo,
                       I as imag_unit, S)
    from sympy.physics.quantum.dagger import Dagger
    from sympy.physics.quantum.operator import (
        Operator, IdentityOperator, HermitianOperator, UnitaryOperator)

    pools = {0: [], 1: [], 2: [], 3: []}

    def add(expr):
        pools[real_kind(expr)].append(expr)

    # operator family, varied names and flavors
    for i in range(24):
        add(Operator("A%d" % i))
    for i in range(6):
        add(HermitianOperator("H%d" % i))
        add(UnitaryOperator("U%d" % i))
    x = Symbol("x")
    add(Operator("P", x))                      # operator with an argument

    # identity element (with and without an explicit dimension; adjoint of
    # the identity folds back to the identity and lands here via real_kind)
    add(IdentityOperator())
    add(IdentityOperator(2))
    add(IdentityOperator(4))
    add(Dagger(IdentityOperator()))

    # conjugate factors (unevaluated adjoints of plain operators; adjoints
    # of Hermitian operators fold back to kind 0 and are bucketed there)
    for i in range(24):
        add(Dagger(Operator("B%d" % i)))
    add(Dagger(Operator("P", x)))
    add(Dagger(HermitianOperator("H0")))       # folds -> kind 0
    add(Dagger(Dagger(Operator("C"))))         # double adjoint folds -> kind 0

    # everything else: scalars, symbols, composite commutative expressions
    add(Symbol("x"))
    add(Symbol("n", commutative=False))
    add(Integer(0))
    add(Integer(1))
    add(Integer(-3))
    add(Rational(1, 2))
    add(Float(2.5))
    add(pi)
    add(imag_unit)
    add(oo)
    add(S.Half)
    add(Add(Symbol("x"), 1))
    add(Symbol("x") * Symbol("y"))
    for i in range(12):
        add(Symbol("s%d" % i))
        add(Integer(rng.randint(-1000, 1000)))
        add(Rational(rng.randint(-99, 99), rng.randint(1, 99)))

    for k in pools:
        assert pools[k], "empty pool for kind %d" % k
    return pools


def main():
    # REAL repo symbols (the methods the model models, per mapping.md):
    from sympy import Mul
    from sympy.physics.quantum.dagger import Dagger
    from sympy.physics.quantum.operator import Operator, IdentityOperator

    real_kind = make_real_kind(Operator, IdentityOperator, Dagger)
    rng = random.Random(SEED)
    pools = build_pools(rng, real_kind)

    id_lefts = [e for e in pools[1]]                     # LHS pool for site 1
    dag_lefts = [e for e in pools[2] if isinstance(e, Dagger)]  # site 2 LHS

    checked = 0
    n_boundary = 0

    # -- structured boundary cases: every LHS variant x every pooled operand
    for left in id_lefts:
        for kind in (0, 1, 2, 3):
            for other in pools[kind]:
                err = check_site("identity-left", IdentityOperator.__mul__,
                                 identity_mul, left, other, "right",
                                 Mul, real_kind)
                if err:
                    print(err)
                    return 1
                checked += 1
                n_boundary += 1
    for left in dag_lefts:
        for kind in (0, 1, 2, 3):
            for other in pools[kind]:
                err = check_site("conjugate-left", Dagger.__mul__,
                                 dagger_mul, left, other, "left",
                                 Mul, real_kind)
                if err:
                    print(err)
                    return 1
                checked += 1
                n_boundary += 1
    # same-object pairs (operand equal to the LHS itself)
    for left in id_lefts:
        for site, real_mul, shadow_fn, side in (
                ("identity-left", IdentityOperator.__mul__, identity_mul,
                 "right"),):
            err = check_site(site, real_mul, shadow_fn, left, left, side,
                             Mul, real_kind)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1
    for left in dag_lefts:
        err = check_site("conjugate-left", Dagger.__mul__, dagger_mul,
                         left, left, "left", Mul, real_kind)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # -- fuzz: random LHS variant and random operand kind/member, both sites
    kinds = (0, 1, 2, 3)
    for _ in range(N_FUZZ):
        kind = rng.choice(kinds)
        other = rng.choice(pools[kind])
        err = check_site("identity-left", IdentityOperator.__mul__,
                         identity_mul, rng.choice(id_lefts), other,
                         "right", Mul, real_kind)
        if err:
            print(err)
            return 1
        checked += 1
        err = check_site("conjugate-left", Dagger.__mul__, dagger_mul,
                         rng.choice(dag_lefts), other, "left",
                         Mul, real_kind)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real product steps on %d checks "
          "(%d boundary + %d fuzz rounds x 2 sites, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
