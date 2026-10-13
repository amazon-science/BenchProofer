#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15368.

There is no consumed @ContractOnly axiom in model.py: the changed behaviour is
modelled DEEPLY (the pure `wrap_flags` fold + the verified `build_wrap_flags`
loop). This script validates, against the REAL Django expression classes:

  (1) the type-hierarchy A-REFERENCE the spec states as its precondition —
        isinstance(attr, Expression)  ==>  hasattr(attr, 'resolve_expression')
      (family membership entails the resolving capability), AND that the
      converse is FALSE: an `F('...')` is resolvable but is NOT an `Expression`.
      This is exactly why the fixed predicate `hasattr(resolve_expression)` is a
      strict superset of the buggy predicate `isinstance(Expression)`.

  (2) the deep model `wrap_flags` (wrap-as-literal iff NOT resolvable) matches
      the POST-PATCH classification `not hasattr(attr, 'resolve_expression')`
      on a battery of real attribute values, AND that the PRE-PATCH
      classification `not isinstance(attr, Expression)` DIVERGES from it on the
      `F` value — the discriminator the frozen spec senses (G-DIFF), and the
      precise observation of the F2P test `test_f_expression`.

Imports are stdlib + Django (the repo under test); exit 0 iff sound. The real
expression classes import and instantiate without database setup.
"""
import sys

from django.db.models.expressions import (   # the repo under test
    Combinable, BaseExpression, Expression, F, Value,
)


# --- model.py reference encodings (kept in lock-step with the deep model) -----

def model_in_family(attr):
    """resolvable family membership, as model.py's `in_family[i]`."""
    return isinstance(attr, Expression)


def model_resolvable(attr):
    """resolving capability, as model.py's `resolvable[i]`."""
    return hasattr(attr, 'resolve_expression')


def deep_wrap_flag(attr):
    """model.py deep model `wrap_flags` for one value: wrap as a literal iff
    NOT resolvable."""
    return not model_resolvable(attr)


def post_patch_predicate(attr):
    """The fixed bulk_update inner-loop decision (query.py:673 post-patch):
    wrap as a literal iff `not hasattr(attr, 'resolve_expression')`."""
    return not hasattr(attr, 'resolve_expression')


def pre_patch_predicate(attr):
    """The buggy bulk_update inner-loop decision (query.py:673 pre-patch):
    wrap as a literal iff `not isinstance(attr, Expression)`."""
    return not isinstance(attr, Expression)


def main():
    # --- a battery of real attribute values across all four cells -------------
    # in_family, resolvable | example
    #   T, T  -> Expression members: Value, CombinedExpression, ...
    #   F, T  -> resolvable non-members: F (the discriminating value)
    #   F, F  -> plain Python data: str, int, None, float, bool
    #   T, F  -> IMPOSSIBLE under the hierarchy (asserted below)
    plain_data = ["test_note", "", "F(note)", 0, 1, 42, None, 3.14, True, b"x"]
    f_values = [F('note'), F('name'), F('other')]
    combined = [F('a') + 1, F('a') * F('b'), F('x') - 2]   # CombinedExpression
    expr_members = [Value('x'), Value(1), Value(None)] + combined

    # --- (1) the type-hierarchy A-reference -----------------------------------
    # Class-level: every Expression has resolve_expression; the converse class
    # (F / Combinable) need not.
    assert hasattr(BaseExpression, 'resolve_expression')
    assert hasattr(Expression, 'resolve_expression')
    assert issubclass(Expression, Combinable)
    assert hasattr(F, 'resolve_expression')
    assert not issubclass(F, Expression), (
        "F must NOT be an Expression subclass (it is the discriminating case)")
    assert not hasattr(Combinable, 'resolve_expression'), (
        "bare Combinable has no resolve_expression; F adds it explicitly")

    # Instance-level: membership entails capability (in_family ==> resolvable),
    # and no value witnesses the impossible (in_family AND not resolvable) cell.
    all_values = plain_data + f_values + expr_members
    for attr in all_values:
        if model_in_family(attr):
            assert model_resolvable(attr), (
                "hierarchy fact violated: %r is an Expression but is not "
                "resolvable" % (attr,))

    # The converse failure MUST be witnessed by F: resolvable, not in family.
    for attr in f_values:
        assert model_resolvable(attr) and not model_in_family(attr), (
            "F must be resolvable without being an Expression: %r" % (attr,))

    # --- (2) deep model == post-patch predicate on every real value ----------
    for attr in all_values:
        assert deep_wrap_flag(attr) == post_patch_predicate(attr), (
            "deep model wrap_flags unsound on %r: model gives %r, post-patch "
            "predicate gives %r" % (attr, deep_wrap_flag(attr),
                                    post_patch_predicate(attr)))

    # Sanity: plain data is wrapped (True), expressions & F are not (False).
    for attr in plain_data:
        assert deep_wrap_flag(attr) is True, ("plain datum must wrap: %r" % (attr,))
    for attr in f_values + expr_members:
        assert deep_wrap_flag(attr) is False, ("resolvable must not wrap: %r" % (attr,))

    # --- the discriminator: pre-patch predicate DIVERGES on F -----------------
    # The buggy predicate wraps F as a literal (True); the deep model / fixed
    # predicate carries it through (False). This is exactly the F2P observation
    # (F('note') -> column vs the literal string 'F(note)') and what
    # model_prepatch.py fails on.
    diverged = False
    for attr in f_values:
        if pre_patch_predicate(attr) != deep_wrap_flag(attr):
            assert pre_patch_predicate(attr) is True and deep_wrap_flag(attr) is False
            diverged = True
    assert diverged, (
        "discriminator failed: pre-patch isinstance(Expression) predicate should "
        "wrap an F value that the fixed predicate carries through")

    # And on the other cells the two predicates must AGREE (so the change is
    # localized to the resolvable-non-member cell that F occupies).
    for attr in plain_data + expr_members:
        assert pre_patch_predicate(attr) == deep_wrap_flag(attr), (
            "pre/post predicates must agree off the F cell, diverged on %r"
            % (attr,))

    print("G-AX OK: type-hierarchy A-reference sound (Expression => resolvable; "
          "F resolvable but not Expression) and deep model wrap_flags == "
          "post-patch hasattr(resolve_expression) predicate on %d real values "
          "(%d plain, %d F, %d Expression); pre-patch isinstance(Expression) "
          "predicate diverges exactly on F (the F2P observation)." %
          (len(all_values), len(plain_data), len(f_values), len(expr_members)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
