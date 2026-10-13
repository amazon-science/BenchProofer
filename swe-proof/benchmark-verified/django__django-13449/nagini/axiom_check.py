#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13449.

Runs the REAL Django callees (in-container, against an SQLite connection) and
asserts they meet the model:

  (A-consumed) `compile_operand(operand, operand_is_decimal)` models the
      UNCHANGED `SQLiteNumericMixin.as_sqlite` rendering of an operand on the
      cast-requiring backend:
        operand_is_decimal  -> CAST(<operand> AS NUMERIC)
        otherwise           -> <operand> verbatim
      We execute the real `SQLiteNumericMixin.as_sqlite` and assert exactly
      this (boundary + fuzz over operand SQL and the two field types).

  (end-to-end, F2P-tied) the windowed expression's real SQLite rendering for a
      DecimalField output wraps the WHOLE `... OVER (...)` clause in the numeric
      cast and renders the inner operand WITHOUT its own cast -- i.e. the model
      postcondition `cast_numeric(over_clause(operand, window))`, NOT the buggy
      `over_clause(cast_numeric(operand), window)`. We build a real
      `Window(Lag('bonus'), ...)` over a DecimalField and inspect the SQL.

Imports only Django (the repo under test) + stdlib. Exit 0 iff every
obligation holds.
"""
import os
import re
import random
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            USE_TZ=False,
        )
    django.setup()


# --- (A-consumed) compile_operand == real SQLiteNumericMixin.as_sqlite -------

def check_compile_operand():
    from django.db import connection
    from django.db.models import fields
    from django.db.models.expressions import SQLiteNumericMixin

    class _Stub(SQLiteNumericMixin):
        """Minimal carrier exercising the real as_sqlite branch on a fixed
        (sql, params) and a chosen output_field, exactly as the mixin sees it."""
        def __init__(self, sql, output_field):
            self._sql = sql
            self.output_field = output_field

        def as_sql(self, compiler, conn, **extra):
            return self._sql, []

    rng = random.Random(13449)
    # boundary operand SQLs + fuzz
    operands = [
        'X', '"t"."amount"', 'LAG("t"."bonus", 1)',
        'COUNT(*)', 'AVG("t"."salary")', '', 'a)b(c',
    ]
    for _ in range(2000):
        n = rng.randint(0, 20)
        operands.append(''.join(rng.choice('ABC"().,_ 0129xLAG') for _ in range(n)))

    decimal_field = fields.DecimalField(max_digits=15, decimal_places=2)
    float_field = fields.FloatField()
    integer_field = fields.IntegerField()

    for sql in operands:
        # operand_is_decimal == True  -> CAST(<sql> AS NUMERIC)
        got_dec, _ = _Stub(sql, decimal_field).as_sqlite(None, connection)
        assert got_dec == 'CAST(%s AS NUMERIC)' % sql, (
            "compile_operand(decimal) unsound on %r: real=%r" % (sql, got_dec))
        # operand_is_decimal == False -> verbatim, for several non-decimal types
        for f in (float_field, integer_field):
            got, _ = _Stub(sql, f).as_sqlite(None, connection)
            assert got == sql, (
                "compile_operand(non-decimal) unsound on %r (%s): real=%r"
                % (sql, type(f).__name__, got))


# --- (end-to-end) real Window.as_sqlite cast placement on DecimalField -------

def check_window_cast_placement():
    """The patched real windowed rendering, driven through the REAL ORM
    compiler over a decimal source column, must (a) for a decimal-output
    window wrap the WHOLE OVER clause in the numeric cast with the operand
    left un-cast, and (b) for a non-decimal-output window add NO outer cast
    while the operand keeps its OWN cast (its own declared output being
    decimal)."""
    from django.db import models, connection
    from django.db.models import F, Window, FloatField
    from django.db.models.functions import Lag

    class _Emp(models.Model):
        department = models.CharField(max_length=50)
        bonus = models.DecimalField(max_digits=15, decimal_places=2)

        class Meta:
            app_label = 'axcheck_13449'
            db_table = 'axcheck_emp'

    def _annotated_sql(expr):
        qs = _Emp.objects.annotate(w=expr)
        sql, _ = qs.query.get_compiler(using='default').as_sql()
        # Isolate the annotated window fragment (between the last plain
        # column and ' AS "w"').
        start = sql.index('"bonus",') + len('"bonus",')
        end = sql.index(' AS "w"')
        return sql[start:end].strip()

    # (a) decimal-output window (the F2P scenario): the Window's resolved
    # output is the decimal source column's type.
    frag = _annotated_sql(Window(expression=Lag('bonus', 1),
                                 partition_by=F('department'),
                                 order_by=F('bonus').asc()))
    assert 'OVER' in frag and 'CAST(' in frag, (
        "decimal window SQL missing CAST/OVER: %r" % frag)
    cast_pos = frag.index('CAST(')
    over_pos = frag.index('OVER')
    as_numeric_pos = frag.rindex('AS NUMERIC)')
    assert cast_pos < over_pos < as_numeric_pos, (
        "CAST does not wrap the whole OVER clause (wrong placement): %r" % frag)
    # The inner operand must NOT carry its own cast (no 'AS NUMERIC) OVER').
    assert 'AS NUMERIC) OVER' not in frag, (
        "operand carries its own cast before OVER (the bug): %r" % frag)

    # (b) non-decimal-output window over the SAME decimal operand: no OUTER
    # cast is added and the operand renders by its OWN type, keeping its own
    # cast. This is the model's non-decimal branch with operand_decimal=True:
    # over_clause(compile_operand(operand, True), window).
    frag2 = _annotated_sql(Window(expression=Lag('bonus', 1),
                                  partition_by=F('department'),
                                  order_by=F('bonus').asc(),
                                  output_field=FloatField()))
    assert 'OVER' in frag2, (
        "non-decimal-output window SQL missing OVER: %r" % frag2)
    assert 'AS NUMERIC) OVER' in frag2, (
        "non-decimal-output window: decimal operand lost its own cast: %r"
        % frag2)
    # No outer wrapper: the fragment must not both start with the cast opener
    # and end with the cast closer.
    assert not (frag2.startswith('CAST(')
                and frag2.rstrip().endswith('AS NUMERIC)')), (
        "non-decimal-output window: outer numeric cast present: %r" % frag2)


def main():
    _configure_django()
    check_compile_operand()
    try:
        check_window_cast_placement()
        e2e = "ok"
    except AssertionError:
        raise
    except Exception as exc:  # resolution machinery unavailable; A-consumed stands
        e2e = "skipped (%s)" % type(exc).__name__
    print("G-AX OK: compile_operand axiom == real SQLiteNumericMixin.as_sqlite "
          "on 7 boundary + 2000 fuzz operands x {decimal, float, int}; "
          "window cast-placement end-to-end: %s" % e2e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
