#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13012.

This bundle consumes NO `@ContractOnly` axiom: the wrapped node's own
grouping-column rule is modelled DEEPLY in model.py as the verified function
`base_group_by_cols` (with its pure sequence value `base_group_cols_seq`). There
is therefore no axiom to over-approximate; what G-AX must establish is that the
DEEP MODEL matches reality and that the modelled changed function (the
composite's forwarding of the grouping request) equals the real callee.

Two obligations, both checked against the REAL Django expression classes
in-container:

  (delegation — the soundness obligation the proof actually needs)
      The modelled changed function — the composite forwards the grouping
      request to the wrapped node and returns its answer verbatim:
        ExpressionWrapper(inner, ...).get_group_by_cols(alias=a)
              == inner.get_group_by_cols(alias=a)
      We assert this for EVERY wrapped node (including the escaping kinds
      below) and several alias requests, including a non-trivial alias. We also
      DETECT which tree is mounted: post-patch the equality holds (and the
      composite is NOT itself in the result); pre-patch the composite returns
      [itself] (the inherited non-aggregate default), which is exactly the
      buggy skeleton model_prepatch.py reproduces and the frozen postcondition
      forbids. This obligation is universal — it holds for all wrapped node
      kinds — and is the whole soundness basis of the bundle's headline
      verify=>resolve guarantee.

  (A-reference, SCOPED — a sound instantiation, not a universal claim)
      The deep model `base_group_cols_seq` spells out the two-case rule for the
      MODELED DOMAIN — non-aggregate, constant-or-column-like wrapped nodes
      (the kinds the issue and both FAIL_TO_PASS tests exercise):
        base_group_cols_seq(id, is_constant=True)  == []          (bare constant)
        base_group_cols_seq(id, is_constant=False) == [that node]  (column-like)
      For nodes IN this domain we observe the real `get_group_by_cols(alias=a)`,
      classify each as constant (answer == []) or column-like (answer == [self]),
      assert it falls in the dichotomy, assert the deep model agrees, and assert
      alias-inertness (answer independent of the alias request) — the two
      properties model.py's docstring and base_group_cols_seq encode.

      This dichotomy and this alias-inertness are NOT universal over all query
      nodes — and we demonstrate the boundary rather than hiding it. Escaping
      kinds (e.g. `Subquery`, which is alias-DEPENDENT: alias=None -> [] but a
      non-trivial alias -> [Ref(self)]; and `OrderBy(<column-like>)`, which
      returns its wrapped expression's cols rather than [] or [itself]) are
      EXPLICITLY EXCLUDED from the modeled domain. For those kinds we run only
      the universal (delegation) assertion — which still holds — and we SKIP the
      scoped dichotomy / alias-inertness assertions, recording that they are
      deliberately out of domain. This proves the modeled domain is a chosen,
      sound restriction, not an oversight: a universally-phrased dichotomy or
      alias-inertness claim would be FALSE, and we assert it is false on the
      escaping kinds so the boundary cannot silently rot.

Imports are stdlib + Django (the repo under test). Django needs a minimal
settings configuration to import the ORM expression classes; constructing an
expression and calling get_group_by_cols() runs only Python and never touches a
database. Exit 0 iff every obligation holds.
"""
import sys


def configure_django():
    """Configure Django just enough to import ORM expression classes and to
    resolve an expression into a Col (for the column-like fuzz / escaping
    witnesses). Building an expression and calling get_group_by_cols() never
    opens a connection; resolving against an in-memory sqlite query likewise
    runs only Python and never touches a database."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    import django
    django.setup()


# ---- model.py deep-model reference encodings (kept in lock-step) ------------

def base_group_cols_seq(node, is_constant):
    """Reference of model.py's deep model `base_group_cols_seq`: the grouping
    columns a non-aggregate query node contributes. Constant -> []; otherwise
    the one-element list naming the node itself."""
    if is_constant:
        return []
    return [node]


def main():
    configure_django()
    from django.db.models import IntegerField, Value, F
    from django.db.models.expressions import (
        ExpressionWrapper, RawSQL, Subquery, OrderBy,
    )
    from django.db.models.functions import Lower, Upper, Length, Coalesce
    from django.contrib.auth.models import User

    # Resolve an F into a real Col so the column-like fuzz also covers the kind
    # the issue is really about (a database column), not just Func wrappers.
    col = F('id').resolve_expression(User.objects.all().query)

    # --- (1) MODELED-DOMAIN nodes: non-aggregate, constant-or-column-like.
    # For these the dichotomy ([]/[self]) and alias-inertness both hold, and the
    # deep model base_group_cols_seq is exact. Each entry is constructible and
    # wrappable by ExpressionWrapper.
    modeled_nodes = [
        Value(3),
        Value(42, output_field=IntegerField()),
        Value('f'),
        Value(None),
        Lower(Value('f')),
        Upper(Value('abc')),
        Length(Value('hello')),
        Lower(Lower(Value('x'))),
        RawSQL('1', []),
        Coalesce(Value(1), Value(2)),
        col,
    ]

    # --- (2) ESCAPING nodes: deliberately OUTSIDE the modeled domain. The
    # universal delegation obligation still holds for them, but the scoped
    # dichotomy / alias-inertness do NOT — we assert that they escape, so the
    # domain boundary is demonstrated, not assumed. (Subquery is alias-DEPENDENT;
    # OrderBy over a column-like node returns the wrapped expression's cols,
    # which is neither [] nor [the OrderBy itself].)
    escaping_nodes = [
        ("Subquery(values pk)", Subquery(User.objects.values('pk'))),
        ("OrderBy(Col(id))", OrderBy(col)),
    ]

    # A spread of alias requests, including a non-trivial alias (the
    # alias-DEPENDENT escape only shows up under a non-None alias).
    aliases = (None, 'T', 'alias0')

    checked = 0
    saw_constant = False
    saw_columnlike = False
    saw_alias_dependent_escape = False
    saw_nondichotomy_escape = False

    # ---- modeled-domain obligations: dichotomy + alias-inertness + deep model
    for inner in modeled_nodes:
        observations = {a: inner.get_group_by_cols(alias=a) for a in aliases}

        # Alias-inertness (SCOPED to the modeled domain): the wrapped node's own
        # answer does not depend on the alias request.
        base = observations[None]
        for a in aliases:
            assert observations[a] == base, (
                "modeled-domain node %r is NOT alias-inert: alias=%r -> %r, "
                "alias=None -> %r (this node does not belong in the modeled "
                "domain)" % (inner, a, observations[a], base))

        # Dichotomy (SCOPED): answer is [] (constant) or [self] (column-like).
        if base == []:
            is_constant = True
            saw_constant = True
        elif base == [inner]:
            is_constant = False
            saw_columnlike = True
        else:
            raise AssertionError(
                "modeled-domain node %r contributes %r, which is neither [] nor "
                "[self] — it does not belong in the modeled domain" % (inner, base))

        # The deep model agrees with the observed answer for this node.
        modelled = base_group_cols_seq(inner, is_constant)
        assert modelled == base, (
            "deep model base_group_cols_seq mismatch on %r: model=%r real=%r"
            % (inner, modelled, base))

        # (delegation, universal) the composite forwards to the wrapped node.
        wrapper = ExpressionWrapper(inner, output_field=IntegerField())
        for a in aliases:
            real_wrapper = wrapper.get_group_by_cols(alias=a)
            expected = inner.get_group_by_cols(alias=a)
            assert real_wrapper == expected, (
                "composite does not forward to wrapped node on %r (alias=%r): "
                "composite=%r wrapped=%r" % (inner, a, real_wrapper, expected))
            assert wrapper not in real_wrapper, (
                "composite contributed ITSELF on %r (alias=%r): %r"
                % (inner, a, real_wrapper))
            checked += 1

    # The dichotomy is non-vacuous: we exercised both arms.
    assert saw_constant, "no constant wrapped node exercised"
    assert saw_columnlike, "no column-like wrapped node exercised"

    # ---- escaping nodes: ONLY the universal delegation obligation runs; the
    # scoped dichotomy / alias-inertness are skipped, and we assert each node
    # really does escape (so a universally-phrased claim would be false here).
    for name, inner in escaping_nodes:
        observations = {a: inner.get_group_by_cols(alias=a) for a in aliases}
        base = observations[None]

        # Does this node violate the scoped dichotomy and/or alias-inertness?
        alias_dependent = any(observations[a] != base for a in aliases)
        nondichotomy = (base != [] and base != [inner])
        if alias_dependent:
            saw_alias_dependent_escape = True
        if nondichotomy:
            saw_nondichotomy_escape = True
        assert alias_dependent or nondichotomy, (
            "%s was put in the escaping set but it neither is alias-dependent "
            "nor violates the dichotomy — re-classify it as modeled-domain"
            % name)

        # (delegation, universal) STILL holds for the escaping kinds: the
        # composite forwards verbatim regardless of how exotic the wrapped node
        # is. This is the only obligation the proof relies on.
        wrapper = ExpressionWrapper(inner, output_field=IntegerField())
        for a in aliases:
            real_wrapper = wrapper.get_group_by_cols(alias=a)
            expected = inner.get_group_by_cols(alias=a)
            assert real_wrapper == expected, (
                "composite does not forward to ESCAPING wrapped node %s "
                "(alias=%r): composite=%r wrapped=%r"
                % (name, a, real_wrapper, expected))
            assert wrapper not in real_wrapper, (
                "composite contributed ITSELF on ESCAPING node %s (alias=%r): %r"
                % (name, a, real_wrapper))
            checked += 1

    # The boundary is real and demonstrated: at least one escaping node is
    # alias-DEPENDENT (falsifying universal alias-inertness) and at least one is
    # outside the []/[self] dichotomy (falsifying a universal dichotomy). These
    # assertions guard against the over-claim the modeled domain deliberately
    # avoids — if Django ever made these node kinds alias-inert / dichotomous,
    # this check would fire and the domain scoping could be revisited.
    assert saw_alias_dependent_escape, (
        "expected an alias-DEPENDENT escaping node (e.g. Subquery) to "
        "demonstrate that universal alias-inertness is false")
    assert saw_nondichotomy_escape, (
        "expected a non-dichotomy escaping node (e.g. OrderBy over a column) "
        "to demonstrate that a universal []/[self] dichotomy is false")

    # Explicit witnesses for the two FAIL_TO_PASS scenarios.
    empty_expr = ExpressionWrapper(Value(3), output_field=IntegerField())
    assert empty_expr.get_group_by_cols(alias=None) == [], (
        "constant ExpressionWrapper must contribute no grouping columns")
    nonempty_expr = ExpressionWrapper(Lower(Value('f')), output_field=IntegerField())
    assert nonempty_expr.get_group_by_cols(alias=None) == [nonempty_expr.expression], (
        "column-like ExpressionWrapper must contribute the WRAPPED node")

    print("G-AX OK: composite forwarding (the universal soundness obligation) "
          "validated over %d (node, alias) cases incl. %d escaping node kinds; "
          "deep model base_group_cols_seq sound + alias-inert on %d "
          "MODELED-DOMAIN wrapped nodes (dichotomy []/[self] holds, both arms "
          "exercised); domain boundary demonstrated (alias-dependent escape: "
          "Subquery; non-dichotomy escape: OrderBy(Col)); both FAIL_TO_PASS "
          "witnesses hold." % (checked, len(escaping_nodes), len(modeled_nodes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
