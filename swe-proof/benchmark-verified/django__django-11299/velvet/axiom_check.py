#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11299.

This bundle declares **no consumed axioms** and exactly **one A-reference deep
model of an unchanged callee** (SPEC_GUIDE §3): the column-reference machinery
`_get_col(target, field, alias, simple_col)` (django/db/models/sql/query.py
:71-74). The changed function `Query._add_q` CALLS `_get_col` (transitively, via
`build_filter`) but does NOT change it — the patch only forwards the existing
`simple_col` selector into the recursive branch. Rather than axiomatize
`_get_col` behind an opaque `ensures`, Solution.lean models its selector→column-
form behavior DEEPLY and CONCRETELY (`formOf` / `columnForm` / `columnForms` over
the `Cond`/`ResolvedCond`/`ColForm` carriers). Per §3 that makes `_get_col` an
A-reference: a deep model whose fidelity must be validated == the real callee by
G-AX (the `escapedSeq == html.escape` pattern of the exemplar bundle).

The R/I structural-propagation legs are differential-tested by G-CONF
(conformance_check.py); THIS script validates the one A-reference. To keep the
gate MEANINGFUL (SPEC_GUIDE §0.7/§0.8 — not a silent vacuous pass) it:

  1. asserts the bundle declares NO consumed axioms and exactly ONE A-reference
     (`_get_col`) — so a future edit that smuggles in an unchecked axiom, or a
     second unvalidated deep-model reference, is caught here; and

  2. exercises the real `_get_col` callee on every selector value and confirms
     the bare/qualified column-form semantics the deep model `formOf` encodes:
       * `simple_col` truthy  -> a `SimpleCol`, whose SQL is the BARE column
         name (no table/alias qualification)        <-> `ColForm.bare`;
       * `simple_col` falsy   -> a `Col`,        whose SQL is the table-/alias-
         QUALIFIED `alias.column`                    <-> `ColForm.qualified`.
     This is exactly the bare-vs-qualified distinction the patch (and the F2P
     test `test_simplecol_query`) turns on, grounding the `formOf` deep model
     against the live callee rather than asserting it on faith.

Imports Django (present in the SWE-Bench instance image) + stdlib only. Exit 0
iff the no-consumed-axiom / single-A-reference claim holds AND the real
`_get_col` callee's bare/qualified semantics match the deep model on every
selector value.
"""
import json
import os
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django.db import models
from django.db.models.expressions import Col, SimpleCol
from django.db.models.sql.query import _get_col


HERE = os.path.dirname(os.path.abspath(__file__))


def _check_meta_kinds():
    """Guard: the bundle must declare NO consumed axioms and exactly ONE
    A-reference deep model — the `_get_col` column-form callee validated below.
    Catches a future edit that smuggles in an unchecked consumed axiom, or a
    second deep-model reference this script does not validate."""
    meta = json.load(open(os.path.join(HERE, "meta.json")))
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], f"meta.json declares consumed axioms but G-AX has no checks: {axioms!r}"
    assert len(refs) == 1, (
        f"expected exactly 1 A-reference deep model (_get_col), got {len(refs)}: {refs!r}")
    ref = refs[0]
    models = ref.get("models", "")
    assert "_get_col" in models, (
        f"the single A-reference must model `_get_col`, got models={models!r}")
    return len(axioms), len(refs)


class _Qn:
    """A stand-in for a compiler's quote_name_unless_alias: identity quoting,
    enough to read back whether the rendered SQL is table-qualified."""

    def quote_name_unless_alias(self, name):
        return name


def _render(col):
    """Render a column reference's SQL fragment via its real `as_sql`."""
    sql, params = col.as_sql(_Qn(), connection=None)
    return sql


def _check_get_col():
    """Exercise the real `_get_col` callee and confirm the bare/qualified
    semantics the deep model `formOf` encodes (the bijection in mapping.md §3)."""
    # A real model field is the `target`/`field`; `get_col` needs it bound to a
    # model (it reads `self.model._meta.db_table`), so define one.
    class _AxModel(models.Model):
        num = models.IntegerField()

        class Meta:
            app_label = "auth"  # any installed app

    field = _AxModel._meta.get_field("num")
    column = field.column          # 'num'
    alias = "myalias"              # the table alias a qualified Col carries

    observations = 0

    # simple_col=True  ->  SimpleCol  ->  bare (unqualified) column SQL.
    bare_col = _get_col(field, field, alias, True)
    assert isinstance(bare_col, SimpleCol), (
        f"_get_col(simple_col=True) returned {type(bare_col).__name__}, expected SimpleCol")
    bare_sql = _render(bare_col)
    assert bare_sql == column, (
        f"SimpleCol SQL {bare_sql!r} is not the bare column {column!r}")
    assert alias not in bare_sql, (
        f"SimpleCol SQL {bare_sql!r} leaks the table alias {alias!r} (should be unqualified)")
    observations += 1

    # simple_col=False ->  Col       ->  table-qualified `alias.column` SQL.
    qual_col = _get_col(field, field, alias, False)
    assert isinstance(qual_col, Col), (
        f"_get_col(simple_col=False) returned {type(qual_col).__name__}, expected Col")
    qual_sql = _render(qual_col)
    assert qual_sql == f"{alias}.{column}", (
        f"Col SQL {qual_sql!r} is not the qualified {alias}.{column!r}")
    assert alias in qual_sql and "." in qual_sql, (
        f"Col SQL {qual_sql!r} is not table-qualified")
    observations += 1

    # The two forms must be DISTINCT (the bug is that nested leaves silently got
    # the qualified form): bare != qualified.
    assert bare_sql != qual_sql, "bare and qualified column SQL must differ"

    return observations


def main():
    n_ax, n_ref = _check_meta_kinds()
    obs = _check_get_col()
    result = {
        "instance": "django__django-11299",
        "status": "ok",
        "axioms_checked": n_ax,
        "deep_model_references_checked": n_ref,
        "callee_observations": obs,
        "callee": "django.db.models.sql.query._get_col",
        "note": ("no consumed axioms; validated the single A-reference deep "
                 "model (formOf) == the real _get_col callee: simple_col True -> "
                 "SimpleCol (bare), False -> Col (alias-qualified)"),
    }
    print(json.dumps(result))
    print("G-AX OK: no consumed axioms; the formOf deep model is validated == "
          "the real _get_col callee on both selector values (A-reference sound).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(json.dumps({"instance": "django__django-11299",
                          "status": "fail", "error": str(e)}))
        print(f"G-AX FAIL: {e}")
        sys.exit(1)
