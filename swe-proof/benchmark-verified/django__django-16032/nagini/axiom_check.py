#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16032.

This bundle consumes NO axioms: the three modelled operations are pure
object/state logic, modelled deeply. What G-AX validates here are the
**A-reference** observations — that the deep model's behaviour matches the REAL
Django query machinery the operations build on, with the gold patch applied:

  (1) ``project_columns``  ~  ``Query.set_values([col])``: it restricts the
      query's selected output to exactly that one column AND sets the boolean
      ``has_select_fields`` to True AND re-derives the annotation-tracking
      masks for the newly-chosen columns — for an ordinary (non-annotation)
      column that leaves ``annotation_select_mask`` EMPTY (cleared), because
      ``set_values`` routes through ``set_annotation_mask(annotation_names)``
      with an empty annotation subset.

  (2) ``attach_auxiliary_expressions``  ~  ``.annotate(...)`` followed by
      ``.alias(...)``: this materializes the query's annotation tracking
      structures (``annotation_select_mask`` becomes a non-empty set) but must
      leave ``has_select_fields`` exactly as it was — in particular, on a query
      that was never restricted by ``values()``/``set_values``, the flag stays
      False even after both kinds of auxiliary expression are attached. (This
      is precisely the behaviour the gold patch establishes: ``has_select_fields``
      is a class attribute defaulting to False, no longer derived from the
      annotation mask.)

  (3) ``prepare_in_rhs``  ~  ``RelatedIn.get_prep_lookup``'s rhs-narrowing
      branch. The branch fires exactly when the rhs query has
      ``has_select_fields`` False AND the lhs relation's target field is NOT a
      primary key. When it fires, the rhs query the lookup holds is narrowed via
      ``set_values`` so that afterwards it selects the single target column AND
      ``has_select_fields`` is True. When the rhs is already projected, OR the
      target field is a primary key, the rhs is left untouched.

      IMPORTANT (the per-FK-branch + mutated-object subtleties this check must
      respect):
        * The narrowing guard ``not target_field.primary_key`` is only False for
          a primary-key target. A *reverse* FK (``parent.child__in=...``) has a
          pk target, so the branch does NOT fire there; a *forward* FK declared
          with a non-pk ``to_field`` (``child.parent__in=...`` where
          ``parent`` references a unique non-pk column) DOES fire it.
        * ``get_prep_lookup`` mutates the ``Query`` object the *lookup* holds
          (``RelatedIn.rhs``), which is a clone — NOT the caller's original
          queryset ``.query``. So the narrowed state must be observed on the
          lookup's own ``rhs``, reached by building the filter and walking the
          WHERE tree to the ``RelatedIn`` node.

This is run inside the official SWE-bench container for the instance (with the
gold patch applied), where Django is importable and a sqlite test database is
available. It configures an in-memory sqlite database and minimal models on a
real installed app, then drives the REAL ``Query`` objects. Exit 0 iff every
A-reference observation matches the deep model; any configuration failure or
skipped assertion exits NON-zero (fail-closed). It imports only Django (the
code under test); nothing else.
"""
import sys


class _Unavailable(Exception):
    """Django itself (the code under test) is not importable in this env."""


def _configure_django():
    # The ONLY condition under which this check may decline to run is genuine
    # unavailability of the code under test (Django not importable). Any other
    # error — misconfiguration, app registry problems, schema failures — must
    # propagate and fail the check (fail-closed).
    try:
        import django  # noqa: F401
        from django.conf import settings
    except ImportError as exc:  # the code under test is absent
        raise _Unavailable(repr(exc))

    if not settings.configured:
        # Attach the test models to a REAL installed app (auth) — do NOT invent
        # a nonexistent app module, which would make django.setup() raise and
        # silently skip the whole check.
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()


def main():
    try:
        _configure_django()
    except _Unavailable as exc:
        # Fail-closed: a SKIP is NOT a pass. If the code under test is absent
        # the check cannot certify anything, so it must NOT exit 0.
        print("G-AX FAIL: code under test (Django) not importable: %s" % (exc,))
        return 2

    from django.db import connection, models
    from django.db.models import Value
    from django.db.models.fields.related_lookups import RelatedIn
    from django.db.models.sql.where import WhereNode

    # Minimal models attached to a real installed app. ``Child.parent`` is a
    # FORWARD FK declared with a non-pk ``to_field`` (Parent.code, unique but
    # not the primary key), so the related-IN narrowing branch (which requires
    # a non-pk target field) is reachable. The pk-target case is covered by a
    # reverse FK below.
    class Parent(models.Model):
        code = models.IntegerField(unique=True)
        n = models.IntegerField()

        class Meta:
            app_label = "auth"

    class Child(models.Model):
        pages = models.IntegerField()
        parent = models.ForeignKey(
            Parent, to_field="code", on_delete=models.CASCADE
        )

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(Parent)
        editor.create_model(Child)

    def find_related_in(clause):
        """Locate the RelatedIn lookup the WHERE tree built (the object whose
        ``rhs`` ``get_prep_lookup`` actually mutates)."""
        stack = [clause]
        while stack:
            node = stack.pop()
            for child in node.children:
                if isinstance(child, WhereNode):
                    stack.append(child)
                elif isinstance(child, RelatedIn):
                    return child
        return None

    obs = 0

    # --- (A-reference 1) project_columns ~ Query.set_values([col]) -----------
    # A fresh query has has_select_fields False (the gold-patch class default).
    for fld in ["id", "n"]:
        q = models.sql.Query(Parent)
        assert q.has_select_fields is False, (
            "fresh Query.has_select_fields must default False, got %r"
            % (q.has_select_fields,))
        q.set_values([fld])
        # set_values restricts the selected output to exactly that one column ...
        assert list(q.values_select) == [fld], (
            "set_values([%r]) selected %r" % (fld, list(q.values_select)))
        # ... AND establishes has_select_fields True (the gold-patch line).
        assert q.has_select_fields is True, (
            "set_values must set has_select_fields True, got %r"
            % (q.has_select_fields,))
        # ... AND leaves the annotation mask EMPTY (re-derived for the chosen
        # ordinary column): set_values clears it via set_annotation_mask([]).
        assert not q.annotation_select_mask, (
            "set_values([%r]) must leave an empty annotation_select_mask, "
            "got %r" % (fld, q.annotation_select_mask,))
        obs += 1

    # --- (A-reference 2) attach_auxiliary_expressions ~ annotate + alias -----
    # The reported-bug witness: annotate() then alias() materializes the
    # annotation mask, yet has_select_fields stays False on a query that was
    # never restricted by values()/set_values.
    base_qs_builders = [
        lambda: Parent.objects.filter(n__gt=0),
        lambda: Child.objects.filter(pages__gt=400),
        lambda: Parent.objects.all(),
    ]
    for build in base_qs_builders:
        base_q = build().query
        assert base_q.has_select_fields is False, (
            "unrestricted query must have has_select_fields False, got %r"
            % (base_q.has_select_fields,))

        # annotate (returned-column kind) then alias (non-returned helper kind).
        qs = build().annotate(ann=Value(1)).alias(al=Value(1))
        q = qs.query
        # the annotation tracking structure is materialized (non-empty mask) ...
        assert q.annotation_select_mask, (
            "annotate+alias must materialize a non-empty annotation_select_mask, "
            "got %r" % (q.annotation_select_mask,))
        # ... but the explicit-projection property is unchanged: still False,
        # because no values()/set_values projection occurred.
        assert q.has_select_fields is False, (
            "annotate+alias must NOT set has_select_fields; got %r"
            % (q.has_select_fields,))
        obs += 1

        # And if such a query is THEN projected, the flag flips True (op 1 again)
        # AND the annotation mask is CLEARED by the projection: set_values
        # re-derives it for the chosen ordinary column via
        # set_annotation_mask(annotation_names=[]). This is the post-projection
        # frame the model's project_columns encodes (aux cleared, not preserved).
        qs2 = build().annotate(ann=Value(1)).alias(al=Value(1)).values("id")
        assert qs2.query.has_select_fields is True, (
            "values() after annotate+alias must set has_select_fields True, got %r"
            % (qs2.query.has_select_fields,))
        assert not qs2.query.annotation_select_mask, (
            "values('id') after annotate+alias must CLEAR the "
            "annotation_select_mask (set_values re-derives it empty), got %r"
            % (qs2.query.annotation_select_mask,))
        obs += 1

    # --- (A-reference 3) prepare_in_rhs ~ RelatedIn rhs-narrowing ------------
    # (3a) Narrowing FIRES: a FORWARD FK with a non-pk to_field (Child.parent ->
    # Parent.code) against an unprojected annotate+alias rhs. The branch narrows
    # the lookup's OWN rhs query (a clone) to the single target column. We
    # inspect that mutated rhs object, NOT the caller's original .query.
    long_parents = (
        Parent.objects.filter(n__gt=0).annotate(ann=Value(1)).alias(al=Value(1))
    )
    assert long_parents.query.has_select_fields is False, (
        "annotate+alias rhs must start unprojected, got %r"
        % (long_parents.query.has_select_fields,))
    child_query = Child.objects.all().query
    clause, _ = child_query.build_filter(
        ("parent__in", long_parents), can_reuse=set()
    )
    lk = find_related_in(clause)
    assert lk is not None, "expected a RelatedIn lookup for parent__in"
    rhs_q = lk.rhs.query if hasattr(lk.rhs, "query") else lk.rhs
    # The lookup's rhs must now be narrowed to a single explicit column ...
    assert rhs_q.has_select_fields is True, (
        "related __in must narrow an unprojected, non-pk-target rhs via "
        "set_values (has_select_fields True), got %r" % (rhs_q.has_select_fields,))
    assert list(rhs_q.values_select) == ["code"], (
        "related __in narrowing must restrict the rhs to the single target "
        "column 'code', got %r" % (list(rhs_q.values_select),))
    # ... AND the narrowing (which IS set_values) clears the rhs's annotation
    # mask that annotate+alias had materialized: the narrowed sub-select
    # returns exactly the one target column, not the annotation too.
    assert not rhs_q.annotation_select_mask, (
        "related __in narrowing must CLEAR the rhs annotation_select_mask "
        "(set_values re-derives it empty), got %r"
        % (rhs_q.annotation_select_mask,))
    obs += 1

    # (3b) Narrowing does NOT fire when the rhs is ALREADY projected
    # (has_select_fields True): the rhs is left untouched.
    projected = Parent.objects.filter(n__gt=0).values("code")
    assert projected.query.has_select_fields is True, (
        "values('code') rhs must be projected, got %r"
        % (projected.query.has_select_fields,))
    cq2 = Child.objects.all().query
    clause2, _ = cq2.build_filter(("parent__in", projected), can_reuse=set())
    lk2 = find_related_in(clause2)
    assert lk2 is not None, "expected a RelatedIn lookup for the projected rhs"
    rhs2 = lk2.rhs.query if hasattr(lk2.rhs, "query") else lk2.rhs
    assert rhs2.has_select_fields is True, (
        "an already-projected rhs must be left projected, got %r"
        % (rhs2.has_select_fields,))
    obs += 1

    # (3c) Narrowing does NOT fire when the target field is a PRIMARY KEY: a
    # reverse FK (child__in) has a pk target, so the guard `not primary_key`
    # is False and the branch is skipped — the rhs is left untouched (still
    # unprojected). This is the "left untouched" half of prepare_in_rhs.
    long_children = (
        Child.objects.filter(pages__gt=400).annotate(ann=Value(1)).alias(al=Value(1))
    )
    pq = Parent.objects.all().query
    clause3, _ = pq.build_filter(("child__in", long_children), can_reuse=set())
    lk3 = find_related_in(clause3)
    assert lk3 is not None, "expected a RelatedIn lookup for child__in"
    rhs3 = lk3.rhs.query if hasattr(lk3.rhs, "query") else lk3.rhs
    # The attributable observable for "the RelatedIn branch was skipped" is
    # has_select_fields staying False: had the branch fired, its set_values
    # call would have set it True. (NOTE the boundary: AFTER the skipped
    # branch, the generic In.get_prep_lookup pk-narrowing — unchanged code in
    # lookups.py, outside the modeled RelatedIn branch — still runs
    # clear_select_clause()+add_fields(['pk']) on a Query rhs, which empties
    # the annotation mask without setting the flag. So the mask state here is
    # NOT attributable to the modeled branch and is deliberately not asserted.)
    assert rhs3.has_select_fields is False, (
        "a pk-target rhs must be left untouched by the RelatedIn branch "
        "(has_select_fields stays False), got %r" % (rhs3.has_select_fields,))
    obs += 1

    # Fail-closed on a vacuous run: if no observation actually executed, that
    # is a config/skip path, not a pass.
    if obs == 0:
        print("G-AX FAIL: no A-reference observations executed (vacuous run).")
        return 3

    print("G-AX OK: %d A-reference observations match the deep model against the "
          "real Django Query machinery (set_values sets has_select_fields and "
          "narrows to one column; annotate+alias leave has_select_fields False; "
          "a related __in with a non-pk-target, unprojected rhs narrows the "
          "lookup's rhs clone to the single target column, while an "
          "already-projected rhs and a pk-target rhs are left untouched)." % (obs,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
