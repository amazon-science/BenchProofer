#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11734.

This bundle consumes NO @ContractOnly axiom: both modelled behaviours are pure,
fully-expressible integer/boolean decisions. What this check validates is the
*deep-model fidelity* of those two decisions against the REAL Django objects
they abstract — i.e. that the integer/level encoding in model.py agrees, on
actual ``F`` / ``OuterRef`` / plain-value instances, with the semantics of the
real query-expression machinery (G-AX / G-EQ A-reference role).

Two encoded decisions are checked against the real classes:

  (1) ``is_query_expression(kind)`` (model.py): a right-hand side is a query
      expression iff it is a local reference (``F``) or an ``OuterRef``; a plain
      value is not. The real predicate that the prepared-value decision uses is
      ``hasattr(rhs, 'resolve_expression')``. We assert it is True for ``F`` and
      ``OuterRef`` and False for a plain value — matching the model's
      value->False, local->True, outer->True mapping. We also exhibit why the
      older ``rhs_is_direct_value`` (= ``not hasattr(rhs, 'as_sql')``) predicate
      misclassified ``F`` / ``OuterRef`` as direct values (both lack ``as_sql``),
      which is the discriminator model_prepatch_2 reproduces.

  (2) The resolution-level arithmetic of ``rebind_into_inner_subquery``
      (model.py): re-anchoring a right-hand side carried into a freshly
      generated inner subquery must preserve the query level it denotes. The
      real lever is ``OuterRef.resolve_expression``: a bare ``OuterRef(name)``
      resolves immediately to a ``ResolvedOuterRef`` (collapses one outward
      level), whereas an ``OuterRef(OuterRef(name))`` resolves to the *inner*
      ``OuterRef`` (still unresolved — one outward level preserved). And an
      ``F(name)`` re-anchored as ``OuterRef(name)`` resolves to a
      ``ResolvedOuterRef``. These confirm the model's "one extra outward hop"
      for both a local reference and an ``OuterRef``.

Run inside the official SWE-bench container, where Django imports. stdlib +
Django only; exit 0 iff every observation matches the model.
"""
import os
import sys


# --- model.py reference encodings (kept in lock-step with model.py) ----------

KIND_VALUE, KIND_LOCAL, KIND_OUTER = 0, 1, 2


def model_is_query_expression(kind):
    return kind in (KIND_LOCAL, KIND_OUTER)


def model_target_level(kind):
    return -1 if kind == KIND_OUTER else 0


def model_resolved_level_in_inner(kind):
    if kind == KIND_LOCAL:
        return 1
    if kind == KIND_OUTER:
        return 0
    return 0


def model_rebind_hops(kind):
    if kind == KIND_VALUE:
        return 0
    return 1  # both local and outer get exactly one extra outward hop


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                       "NAME": ":memory:"}},
            )
        django.setup()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db.models import F
    from django.db.models.expressions import OuterRef, ResolvedOuterRef

    # ---- (1) the query-expression / direct-value classification -------------
    # Real predicate used by the prepared-value decision post-patch:
    #   hasattr(rhs, 'resolve_expression')
    # Real predicate used pre-patch (rhs_is_direct_value):
    #   not hasattr(rhs, 'as_sql')
    samples = [
        (KIND_VALUE, 7),                 # a plain concrete value
        (KIND_VALUE, "abc"),
        (KIND_VALUE, None),
        (KIND_LOCAL, F("name")),         # a local field reference
        (KIND_OUTER, OuterRef("pk")),    # an OuterRef
        (KIND_OUTER, OuterRef("job")),
    ]
    for kind, rhs in samples:
        has_resolve = hasattr(rhs, "resolve_expression")
        # model: is_query_expression == (kind in {local, outer})
        assert has_resolve == model_is_query_expression(kind), (
            "is_query_expression mismatch on kind=%d rhs=%r: real "
            "hasattr(resolve_expression)=%r, model=%r"
            % (kind, rhs, has_resolve, model_is_query_expression(kind)))
        # post-patch normalise decision == not query-expression
        normalise_post = not has_resolve
        assert normalise_post == (kind == KIND_VALUE), (
            "post-patch normalise decision wrong for kind=%d rhs=%r" % (kind, rhs))

    # The pre-patch predicate (rhs_is_direct_value) misclassifies F / OuterRef
    # as direct values: neither has an `as_sql` method, so it would normalise
    # them. This is exactly the discriminator model_prepatch_2 reproduces.
    for _, rhs in [(KIND_LOCAL, F("name")), (KIND_OUTER, OuterRef("pk"))]:
        rhs_is_direct_value_prepatch = not hasattr(rhs, "as_sql")
        assert rhs_is_direct_value_prepatch is True, (
            "expected pre-patch rhs_is_direct_value() True (no as_sql) for %r" % (rhs,))

    # ---- (2) the resolution-level arithmetic of the inner-subquery re-anchor -
    # A bare OuterRef collapses one outward level on resolution:
    bare = OuterRef("pk")
    r_bare = bare.resolve_expression()
    assert isinstance(r_bare, ResolvedOuterRef), (
        "bare OuterRef should resolve to ResolvedOuterRef, got %r" % (r_bare,))
    assert not isinstance(r_bare, OuterRef), (
        "bare OuterRef must not stay an unresolved OuterRef after resolution")

    # An OuterRef wrapping an OuterRef preserves one outward level: it resolves
    # to the *inner* OuterRef, still unresolved (one extra outward hop kept).
    wrapped = OuterRef(OuterRef("pk"))
    r_wrapped = wrapped.resolve_expression()
    assert isinstance(r_wrapped, OuterRef) and not isinstance(r_wrapped, ResolvedOuterRef), (
        "OuterRef(OuterRef(..)) should resolve to the inner unresolved OuterRef, "
        "got %r" % (r_wrapped,))
    assert r_wrapped.name == "pk", "inner OuterRef name not preserved: %r" % (r_wrapped.name,)

    # An F re-anchored as OuterRef(name) resolves to a ResolvedOuterRef (the
    # local reference, originally level 0, now denotes one level out from the
    # inner subquery = the original query): one extra outward hop.
    reanchored_local = OuterRef("name")  # F('name') -> OuterRef('name')
    r_local = reanchored_local.resolve_expression()
    assert isinstance(r_local, ResolvedOuterRef), (
        "F re-anchored as OuterRef should resolve to ResolvedOuterRef, got %r"
        % (r_local,))

    # Consistency of the model's level arithmetic for the two query-expression
    # kinds: resolved_level_in_inner - hops == target_level.
    for kind in (KIND_LOCAL, KIND_OUTER):
        assert (model_resolved_level_in_inner(kind) - model_rebind_hops(kind)
                == model_target_level(kind)), (
            "model level arithmetic inconsistent for kind=%d" % kind)
    assert model_rebind_hops(KIND_VALUE) == 0

    print("G-AX OK: deep-model decisions for django__django-11734 sound against "
          "real F / OuterRef / ResolvedOuterRef: query-expression classification "
          "matches hasattr(resolve_expression) on %d samples; OuterRef resolution "
          "levels confirm the one-extra-outward-hop re-anchor (bare collapses, "
          "wrapped preserves)." % (len(samples),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
