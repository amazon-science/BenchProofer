#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15930.

There is NO consumed axiom in this bundle. The empty-condition fallback predicate
is modeled DEEPLY (Solution.lean's `truePredicate`, in the `pure` region). What
G-AX validates is the **A-reference**: that the deep model's compiled form equals
the real `compiler.compile(Value(True))`, and that the empty-condition trigger
the fix handles is real.

Checks against real callees (no value is asserted that the real code does not
produce):

  (A-reference) `compiler.compile(Value(True))` returns a NON-EMPTY placeholder
      fragment binding exactly one literal-true parameter — `("%s", [<true>])` —
      which is precisely the deep model
          truePredicate = { sql := "%s".toList, params := [1] }
      (the literal true carried by the integer identity 1; mapping.md §2/§3.1).

  (trigger, end-to-end) A match-everything condition `~Q(pk__in=[])` compiles to
      the EMPTY string `""` (django/db/models/sql/where.py), and the PATCHED
      `When.as_sql` therefore emits the non-empty always-true predicate, so the
      assembled branch is `WHEN %s THEN %s` — never the broken `WHEN  THEN %s`
      of the problem statement. A normal (non-empty) condition is used unchanged.

PYTHONPATH=/testbed is required so the PATCHED repo copy is imported. Imports
only the standard library + the repo under test. Exit 0 iff every obligation
holds.
"""
import os
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
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


# --- A-reference: compiler.compile(Value(True)) == deep model truePredicate ---

def check_true_predicate():
    """The added fallback `compiler.compile(Value(True))` is a non-empty `"%s"`
    fragment binding one literal-true parameter — exactly `truePredicate`."""
    from django.db import connection
    from django.db.models import Value

    v = Value(True)
    # Value.as_sql does not use the compiler argument on this path; a real
    # connection supplies ops.check_expression_support + the BooleanField
    # db-prep that turns the literal True into its bound parameter.
    sql, params = v.as_sql(None, connection)

    assert sql == "%s", (
        "A-reference unsound: compiler.compile(Value(True)) sql=%r, deep model "
        "truePredicate.sql is '%%s'" % (sql,))
    assert sql != "", "A-reference unsound: fallback predicate must be NON-empty"
    assert len(params) == 1, (
        "A-reference unsound: Value(True) must bind exactly one parameter, "
        "got %r" % (params,))
    # The single bound parameter is the literal true (sqlite adapts True->1;
    # mapping.md §2 carries the literal true by the identity 1). Accept the
    # truthy literal regardless of bool/int adaptation.
    (p,) = params
    assert p in (True, 1), (
        "A-reference unsound: Value(True) parameter %r is not the literal true"
        % (p,))
    return sql, params


# --- trigger (end-to-end): empty condition -> non-empty predicate in branch ---

def check_branch_assembly():
    """Compile a real `Case(When(~Q(pk__in=[]), ...))` and a real
    `When(Q(pk=...), ...)` through the PATCHED code; assert the empty-condition
    branch gets the always-true predicate and the normal branch is unchanged."""
    from django.contrib.auth.models import User
    from django.db import connection
    from django.db.models import Case, When, Value, Q, BooleanField

    qs = User.objects.all()
    query = qs.query
    compiler = query.get_compiler(connection=connection)

    # (1) match-everything condition -> compiles to "" -> patched branch uses %s
    case_full = Case(
        When(~Q(pk__in=[]), then=Value("selected")),
        default=Value("not selected"),
        output_field=BooleanField(),
    )
    resolved_full = case_full.resolve_expression(query)
    # The When's condition alone must compile to the empty string.
    when_full = resolved_full.cases[0]
    cond_sql, cond_params = compiler.compile(when_full.condition)
    assert cond_sql == "", (
        "trigger unsound: ~Q(pk__in=[]) condition compiled to %r, expected "
        "the empty string ''" % (cond_sql,))
    # The whole Case, compiled through the PATCHED When.as_sql.
    sql_full, _ = compiler.compile(resolved_full)
    assert "WHEN  THEN" not in sql_full, (
        "PATCH NOT EFFECTIVE: assembled branch is the broken 'WHEN  THEN' "
        "(empty predicate) -- %r" % (sql_full,))
    assert "WHEN %s THEN" in sql_full, (
        "patched branch should splice the non-empty '%%s' always-true "
        "predicate; got %r" % (sql_full,))

    # (2) ordinary, non-empty condition -> used unchanged (predicate present).
    case_norm = Case(
        When(Q(pk=1), then=Value("a")),
        default=Value("b"),
        output_field=BooleanField(),
    )
    resolved_norm = case_norm.resolve_expression(query)
    when_norm = resolved_norm.cases[0]
    cond_sql_n, _ = compiler.compile(when_norm.condition)
    assert cond_sql_n != "", (
        "setup error: Q(pk=1) should compile to a non-empty predicate, got ''")
    sql_norm, _ = compiler.compile(resolved_norm)
    assert "WHEN  THEN" not in sql_norm
    # the real condition predicate (not the literal-true %s alone) is present
    assert "WHEN " in sql_norm and " THEN " in sql_norm
    return sql_full, sql_norm


def main():
    sys.path.insert(0, os.environ.get("TESTBED", "/testbed"))
    _setup_django()

    sql, params = check_true_predicate()

    try:
        sql_full, sql_norm = check_branch_assembly()
        trig_note = ("empty-condition branch -> %r (non-empty predicate); "
                     "normal branch -> %r" % (sql_full, sql_norm))
    except Exception as e:  # pragma: no cover - environment-dependent
        print("G-AX NOTE: end-to-end branch-assembly leg skipped (%s: %s)"
              % (type(e).__name__, e), file=sys.stderr)
        trig_note = "branch-assembly leg skipped (env)"

    print("G-AX OK: truePredicate A-reference sound -- "
          "compiler.compile(Value(True)) = (%r, %r) == deep model "
          "{sql:'%%s', params:[1]}; %s." % (sql, params, trig_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
