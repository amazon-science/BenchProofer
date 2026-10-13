#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-19783.

There is NO consumed @ContractOnly axiom in this bundle: both binary-product
operations are modelled DEEPLY as integer-kind dispatch (model.py). This check
validates the two A-reference deep models against the REAL sympy classes /
methods, in-container, on the gold-patched tree:

  (1) the kind classification (model.py `is_operator_like` / `is_identity` /
      `is_conjugate`) agrees with the real Python type tests
      `isinstance(x, (Operator, Dagger))` / `isinstance(x, IdentityOperator)` /
      `isinstance(x, Dagger)` that the two real `__mul__` methods perform; and

  (2) the dispatch result of `identity_mul(kind)` / `dagger_mul(kind)`
      (model.py) — collapse-to-an-operand vs. an unevaluated symbolic product,
      and WHICH operand survives — matches the actual result of the real
      `IdentityOperator.__mul__` / `Dagger.__mul__` on a representative member
      of every operand kind.

The model's kind tags:
  0 plain operator   1 identity element   2 Hermitian conjugate   3 other
A representative SymPy object is constructed for each kind and fed to the real
operators. The observed result is classified back into the model's `Product`
record and compared field-by-field with the model's prediction.

Imports only `sympy` (the very package the gold patch edits) and stdlib. Exit 0
iff every observation matches the model. This is the real correctness anchor
for the deep models that the proof relies on.
"""
import sys

from sympy import Mul, Symbol
from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum.operator import Operator, IdentityOperator


# ---- model.py deep-model reference encodings (kept in lock-step) -----------

KIND_OPERATOR = 0
KIND_IDENTITY = 1
KIND_CONJUGATE = 2
KIND_OTHER = 3
KINDS = [KIND_OPERATOR, KIND_IDENTITY, KIND_CONJUGATE, KIND_OTHER]


def m_is_operator_like(k):
    return k == 0 or k == 1


def m_is_identity(k):
    return k == 1


def m_is_conjugate(k):
    return k == 2


def model_identity_mul(other_kind):
    """Mirror of model.py identity_mul: (is_mul, result_kind)."""
    if m_is_operator_like(other_kind) or m_is_conjugate(other_kind):
        return (False, other_kind)
    return (True, other_kind)


def model_dagger_mul(other_kind):
    """Mirror of model.py dagger_mul: (is_mul, result_kind)."""
    if m_is_identity(other_kind):
        return (False, KIND_CONJUGATE)
    return (True, KIND_CONJUGATE)


def predicted_expr(left, right, prediction):
    """Turn a model (is_mul, result_kind) prediction into the concrete SymPy
    expression the real __mul__ must return. Collapse -> the surviving operand
    (left or right, identified by result_kind); non-collapse -> the generic
    product Mul(left, right) (which SymPy may canonicalize, e.g. x*x -> x**2)."""
    is_mul, result_kind = prediction
    if is_mul:
        return Mul(left, right)
    # collapse: the surviving operand is whichever of the two operands has the
    # predicted result_kind. (For identity_mul it is the right operand; for
    # dagger_mul it is the left operand. We resolve by kind to stay generic.)
    if real_kind(left) == result_kind and real_kind(right) != result_kind:
        return left
    if real_kind(right) == result_kind and real_kind(left) != result_kind:
        return right
    # operands share the predicted kind (e.g. identity*identity): either is the
    # same expression; return the right one (the model's identity_mul survivor).
    return right


# ---- real SymPy objects, one representative per model kind -----------------

O = Operator('O')
Ident = IdentityOperator()
Dag = Dagger(O)                 # a Hermitian-conjugate factor
Scalar = Symbol('x')            # an "other" factor (non-operator scalar symbol)

REPRESENTATIVES = {
    KIND_OPERATOR: O,
    KIND_IDENTITY: Ident,
    KIND_CONJUGATE: Dag,
    KIND_OTHER: Scalar,
}


def real_kind(expr):
    """Classify a real SymPy expression into the model's kind tag, by the same
    type tests the real __mul__ methods use. Order matters: IdentityOperator is
    a subclass of Operator, and Dagger is NOT an Operator."""
    if isinstance(expr, IdentityOperator):
        return KIND_IDENTITY
    if isinstance(expr, Dagger):
        return KIND_CONJUGATE
    if isinstance(expr, Operator):
        return KIND_OPERATOR
    return KIND_OTHER


def check_classification():
    """A-reference (1): the model kind predicates match the real type tests."""
    for k, rep in REPRESENTATIVES.items():
        assert real_kind(rep) == k, (
            "representative for kind %d misclassified as %d"
            % (k, real_kind(rep)))
        # the membership predicates the real __mul__ methods rely on:
        # IdentityOperator.__mul__ absorbs Operator or Dagger:
        absorbs_in_identity = isinstance(rep, (Operator, Dagger))
        assert absorbs_in_identity == (m_is_operator_like(k) or m_is_conjugate(k)), (
            "isinstance(rep_kind=%d, (Operator, Dagger)) disagrees with model"
            % k)
        # Dagger.__mul__ absorbs IdentityOperator:
        assert isinstance(rep, IdentityOperator) == m_is_identity(k), (
            "isinstance(rep_kind=%d, IdentityOperator) disagrees with model" % k)


def check_identity_mul():
    """A-reference (2a): IdentityOperator.__mul__ matches identity_mul. The
    real returned expression must equal the model's predicted expression."""
    for k, rep in REPRESENTATIVES.items():
        observed = Ident * rep                      # the REAL left __mul__
        prediction = model_identity_mul(k)
        want = predicted_expr(Ident, rep, prediction)
        assert observed == want, (
            "identity_mul(kind=%d): real I*rep = %r, model predicts %r "
            "(is_mul=%s)" % (k, observed, want, prediction[0]))
        # cross-check the generic-product/collapse classification is consistent
        # (a collapse must NOT coincidentally equal the generic product unless
        #  the operands are equal, e.g. identity*identity).
        if not prediction[0]:
            assert observed != Mul(Ident, rep) or Ident == rep, (
                "identity_mul(kind=%d): claimed collapse but equals the generic "
                "product Mul(I, rep)=%r" % (k, Mul(Ident, rep)))


def check_dagger_mul():
    """A-reference (2b): Dagger.__mul__ matches dagger_mul. The real returned
    expression must equal the model's predicted expression."""
    for k, rep in REPRESENTATIVES.items():
        observed = Dag * rep                        # the REAL left __mul__
        prediction = model_dagger_mul(k)
        want = predicted_expr(Dag, rep, prediction)
        assert observed == want, (
            "dagger_mul(kind=%d): real Dag*rep = %r, model predicts %r "
            "(is_mul=%s)" % (k, observed, want, prediction[0]))
        if not prediction[0]:
            assert observed != Mul(Dag, rep) or Dag == rep, (
                "dagger_mul(kind=%d): claimed collapse but equals the generic "
                "product Mul(Dag, rep)=%r" % (k, Mul(Dag, rep)))


def check_f2p_witnesses():
    """The exact discriminating equalities the hidden F2P tests assert. Fail
    loud if any does not hold (no silent skip)."""
    # test_identity: two-sided absorption of the conjugate factor.
    assert Ident * Dag == Dag, "I * Dagger(O) should simplify to Dagger(O)"
    assert Dag * Ident == Dag, "Dagger(O) * I should simplify to Dagger(O)"
    # test_identity: unchanged operator absorption + non-absorption.
    assert Ident * O == O
    assert O * Ident == O
    assert isinstance(Ident * Ident, IdentityOperator)
    assert isinstance(3 * Ident, Mul)
    assert isinstance(Ident * Scalar, Mul)
    # test_dagger_mul: Dagger(I) == I, so Dagger(O)*Dagger(I) absorbs to Dagger(O).
    assert Dagger(Ident) == Ident, "Dagger(IdentityOperator()) should be I"
    assert Dag * Dagger(Ident) == Dag, "Dagger(O) * Dagger(I) should be Dagger(O)"
    assert Dag * Dag == Dag ** 2, "Dagger(O) * Dagger(O) should be Dagger(O)**2"


def main():
    check_classification()
    check_identity_mul()
    check_dagger_mul()
    check_f2p_witnesses()
    print("G-AX OK: kind classification + identity_mul + dagger_mul deep models "
          "match the real IdentityOperator.__mul__ / Dagger.__mul__ on all %d "
          "operand kinds; F2P discriminating equalities hold." % len(KINDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
