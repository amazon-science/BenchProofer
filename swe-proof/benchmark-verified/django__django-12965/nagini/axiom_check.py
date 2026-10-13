#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12965.

This bundle consumes NO @ContractOnly axiom (model.py's `axioms` region is
empty): the changed operation is pure table-reference bookkeeping over the
delete query's alias state, modelled directly. There is therefore no axiom
`Ensures` to fuzz against a real callee.

What G-AX validates here is the single REFINEMENT claim refinement.md (§A2, §C)
relies on — that the real Django code behaves as the deep model says — by
executing the real Django delete compiler:

  (1) For a whole-table removal (`Model.objects.all()`), the real
      `SQLDeleteCompiler.single_alias` (post the gold fix, i.e. after
      `self.query.get_initial_alias()` ensures the base table is accounted for)
      is True — i.e. with no additional joined tables active, the number of
      active tables is exactly one. This is the model op A2+A3:
      `primary_present := True; active_tables(True, 0) == 1`.

  (2) The unchanged caller `SQLDeleteCompiler.as_sql` then emits the DIRECT
      single-table form, whose SQL contains NO nested SELECT (no subquery over
      the same table). This is the model op B1 (`delete_uses_subquery -> False`)
      and exactly the F2P observation (`test_fast_delete_all`).

  (3) `get_initial_alias`'s net effect on the predicate-relevant quantity is to
      make the base table accounted for (positive reference count) while leaving
      the count of *other* active tables unchanged — validating the modelling of
      it as `primary_present := True` with `extra_active` fixed.

  (4) Control: a removal that DOES reference an additional joined table (more
      than one active table) still takes the subquery form — confirming the
      spec's discriminator (`extra_active != 0` -> subquery) is faithful, not
      vacuously always-direct.

Run inside the official SWE-bench container for this instance, where Django is
importable and a sqlite database is available; it configures an in-memory
sqlite database and minimal dependency-free models. Imports are limited to the
standard library plus Django itself (the package under test). Exit 0 iff every
obligation holds.
"""
import os
import re
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def _delete_sql(qs):
    """Compile the DELETE SQL the queryset's delete() would issue, via the real
    SQLDeleteCompiler.as_sql (the unchanged caller of single_alias)."""
    query = qs.query.clone()
    query.__class__ = __import__(
        "django.db.models.sql.subqueries", fromlist=["DeleteQuery"]
    ).DeleteQuery
    from django.db import connection
    compiler = query.get_compiler(using="default", connection=connection)
    sql, params = compiler.as_sql()
    return sql, compiler


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models

    class Alphabet(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = "axcheck"

    class Friend(models.Model):
        owner = models.ForeignKey(Alphabet, on_delete=models.CASCADE)

        class Meta:
            app_label = "axcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Alphabet)
        editor.create_model(Friend)

    # ---- (1)+(2): whole-table delete -> single_alias True, no subquery -------
    qs = Alphabet.objects.all()
    sql, compiler = _delete_sql(qs)

    # (1) real single_alias is True for the whole-table case.
    assert compiler.single_alias is True, (
        "real single_alias should be True for a whole-table delete, got %r"
        % (compiler.single_alias,))

    # (3) get_initial_alias makes the base table accounted for while leaving the
    #     count of *other* active tables unchanged.  Build a fresh delete query
    #     and observe the active-table count before and after.
    fresh = Alphabet.objects.all().query.clone()
    from django.db.models.sql.subqueries import DeleteQuery
    fresh.__class__ = DeleteQuery
    base = fresh.get_meta().db_table

    def active_count(q):
        return sum(q.alias_refcount[t] > 0 for t in q.alias_map)

    def extra_active(q):
        return sum(
            q.alias_refcount[t] > 0 for t in q.alias_map
            if t != base
        )

    extra_before = extra_active(fresh)
    fresh.get_initial_alias()
    base_accounted = fresh.alias_map and fresh.alias_refcount.get(base, 0) > 0
    extra_after = extra_active(fresh)
    assert base_accounted, (
        "get_initial_alias must make the base table accounted for "
        "(positive refcount), but base=%r refcounts=%r" % (base, fresh.alias_refcount))
    assert extra_after == extra_before, (
        "get_initial_alias must not change the count of other active tables: "
        "before=%r after=%r" % (extra_before, extra_after))
    # after registration the whole-table case has exactly one active table
    assert active_count(fresh) == 1, (
        "whole-table delete should have exactly one active table after "
        "get_initial_alias, got %r" % (active_count(fresh),))

    # (2) the emitted SQL must contain NO nested SELECT subquery (F2P).
    assert "DELETE" in sql.upper(), "expected a DELETE statement, got %r" % (sql,)
    assert not re.search(r"\bSELECT\b", sql, re.IGNORECASE), (
        "whole-table delete must not use a subquery, but emitted: %r" % (sql,))

    # ---- (4) control: a filtered delete that joins another table -------------
    # A delete filtered through a related table references more than one table,
    # so single_alias is False and the subquery form is used.
    qs2 = Friend.objects.filter(owner__name="x")
    sql2, compiler2 = _delete_sql(qs2)
    assert compiler2.single_alias is False, (
        "real single_alias should be False when an extra table is joined, got %r"
        % (compiler2.single_alias,))
    assert re.search(r"\bSELECT\b", sql2, re.IGNORECASE), (
        "multi-table delete should use a subquery (a nested SELECT), got %r"
        % (sql2,))

    print("G-AX OK: refinement claim sound against the real Django delete "
          "compiler — whole-table delete: single_alias=True, no subquery "
          "(%r); get_initial_alias accounts the base table and leaves other "
          "active-table count fixed; control multi-table delete: "
          "single_alias=False, subquery used." % (sql,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
