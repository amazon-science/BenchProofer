#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13449 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Assert and the access predicates) stripped. The @Pure
helpers (kw_over / kw_over_close / cast_open / cast_close / cast_numeric /
over_clause) copy over as plain functions on an immutable-tuple PSeq shim;
they are contract-side but serve here as an internal cross-check of the
shadow. The one @ContractOnly callee of the model (`compile_operand`) is
referenced by the impl region only inside Assert(...) calls, which are
stripped, so the shadow has no axiom call sites; the callee itself is
validated against the real repo method by axiom_check.py (G-AX).

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.db.models.expressions.Window.as_sqlite`. The gate applies patch.diff
to /testbed before this script runs, so the method exists and is the patched
rendering. Each trial builds a real `Window` over a minimal source-expression
carrier (a `SQLiteNumericMixin` expression whose `as_sql` returns a chosen
SQL fragment, exactly the shape the mixin dispatch sees), drives it through a
real SQLite compiler/connection, and compares the returned SQL text against
the shadow.

Type bridge (mapping.md section 2): SQL fragment `str` <-> `List[int]` of
token code points via ord/chr (a bijection); generation happens over `str`
and is lowered per call. `decimal_out` is read off the real window object the
same way the repo guard reads it (its declared output field being the
fixed-precision decimal type); `operand_decimal` is the corresponding
property of the operand carrier's own declared field. The `window` argument
is the real object's own already-built window text (captured by rendering the
window-substitution slot alone), so both sides see the identical fragment.

Input domain: the model's preconditions demand only readable token lists, so
every `str` lowers to a Requires-satisfying input. Generation stresses the
decision boundary: both output-field flags in all four combinations
(including the case where the two declared outputs differ), an explicit vs. a
source-resolved window output field, empty/degenerate fragments, fragments
containing the cast/OVER literal substrings and unbalanced parens/quotes, and
several non-decimal field types.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz trials.
Pinned fuzz seed: 13449.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. Imports only Django (the repo under test) + stdlib.
"""
import json
import random
import sys

SEED = 13449
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def kw_over():
    # the token sequence ' OVER (' (space O V E R space open-paren)
    return PSeq(32, 79, 86, 69, 82, 32, 40)


def kw_over_close():
    # the closing ')'
    return PSeq(41)


def cast_open():
    # 'CAST('
    return PSeq(67, 65, 83, 84, 40)


def cast_close():
    # ' AS NUMERIC)'
    return PSeq(32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41)


def cast_numeric(x):
    """Wrap a fragment in the numeric cast: CAST(<x> AS NUMERIC)."""
    return cast_open() + x + cast_close()


def over_clause(inner, window):
    """The windowed fragment without any cast: <inner> OVER (<window>)."""
    return inner + kw_over() + window + kw_over_close()


# --- SHADOW: impl region of model.py, contracts stripped ----------------------
# (Requires/Ensures/Acc/Assert lines removed; executable statements verbatim.)

def render_windowed_with_numeric_cast(operand, window, decimal_out,
                                      operand_decimal):
    if decimal_out:
        # The operand is compiled with a non-decimal output: the decimal cast
        # it would otherwise carry is absorbed by the outer cast, so verbatim.
        inner = list(operand)  # type: List[int]
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        result = [67, 65, 83, 84, 40] + over + \
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    else:
        # No outer cast: the operand renders by its own declared type.
        raw = list(operand)  # type: List[int]
        inner2 = raw  # type: List[int]
        if operand_decimal:
            inner2 = [67, 65, 83, 84, 40] + raw + \
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
# --- end shadow ---------------------------------------------------------------


def shadow_render(op_sql, window_sql, decimal_out, operand_decimal):
    """str -> List[int] bridge in, List[int] -> str bridge out."""
    res = render_windowed_with_numeric_cast(
        [ord(c) for c in op_sql], [ord(c) for c in window_sql],
        decimal_out, operand_decimal)
    return ''.join(chr(t) for t in res)


def shadow_spec_crosscheck(op_sql, window_sql, decimal_out, operand_decimal):
    """Internal sanity: the stripped impl equals the pure-region composition
    it was proven against (catches a bad strip, not a repo disagreement)."""
    op = ToSeq([ord(c) for c in op_sql])
    win = ToSeq([ord(c) for c in window_sql])
    got = ToSeq([ord(c) for c in shadow_render(op_sql, window_sql,
                                               decimal_out, operand_decimal)])
    if decimal_out:
        want = cast_numeric(over_clause(op, win))
    else:
        inner = cast_numeric(op) if operand_decimal else op
        want = over_clause(inner, win)
    assert got == want, "shadow strip inconsistent with pure region"


# --- ORACLE plumbing ----------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes'],
            USE_TZ=False,
        )
    django.setup()


def main():
    _configure_django()
    from django.db import connection, models
    from django.db.models import fields
    from django.db.models.expressions import (
        Expression, SQLiteNumericMixin, Window,
    )

    class _Frag(SQLiteNumericMixin, Expression):
        """Minimal window-compatible source-expression carrier: its as_sql
        returns a chosen SQL fragment, and the inherited mixin dispatch gives
        it exactly the operand-side rendering the model abstracts."""
        window_compatible = True

        def __init__(self, sql, output_field):
            super(_Frag, self).__init__(output_field=output_field)
            self._sql = sql

        def as_sql(self, compiler, conn, **extra):
            return self._sql, []

    class _M(models.Model):
        class Meta:
            app_label = 'conf13449'

    compiler = _M.objects.all().query.get_compiler(using='default')

    def dec_field():
        return fields.DecimalField(max_digits=15, decimal_places=2)

    NONDEC_FIELDS = (fields.FloatField, fields.IntegerField, fields.CharField)

    def one_trial(op_sql, op_decimal, out_kind, part_sql, order_sql):
        """out_kind: 'dec' explicit decimal output, 'nondec' explicit
        non-decimal output, 'resolve' no explicit output (resolved from the
        operand's own field). Returns (decimal_out, window_text, real, shadow)."""
        op_field = dec_field() if op_decimal else random.choice(NONDEC_FIELDS)()
        op = _Frag(op_sql, op_field)
        kwargs = {}
        if part_sql is not None:
            kwargs['partition_by'] = _Frag(part_sql, fields.FloatField())
        if order_sql is not None:
            kwargs['order_by'] = _Frag(order_sql, fields.FloatField())
        if out_kind == 'dec':
            kwargs['output_field'] = dec_field()
        elif out_kind == 'nondec':
            kwargs['output_field'] = fields.FloatField()
        w = Window(expression=op, **kwargs)
        # The real object's own already-built window text: render only the
        # window-substitution slot, so both sides see the identical fragment.
        window_text, _ = w.as_sql(compiler, connection, template='%(window)s')
        decimal_out = isinstance(w.output_field, fields.DecimalField)
        real, _ = w.as_sqlite(compiler, connection)
        shad = shadow_render(op_sql, window_text, decimal_out, op_decimal)
        return decimal_out, window_text, real, shad

    rng = random.Random(SEED)
    random.seed(SEED)  # NONDEC_FIELDS choice above uses the module RNG

    boundary_ops = [
        '', 'X', '"t"."amount"', 'LAG("t"."bonus", 1)', 'COUNT(*)',
        'AVG("t"."salary")', 'a)b(c', 'CAST(', ' AS NUMERIC)',
        'x OVER (y)', 'CAST(z AS NUMERIC)', '((', '))', '%s', "'quoted'",
    ]
    boundary_parts = [None, '', '"p"', '"t"."department"', 'a, b', ')(']
    boundary_orders = [None, '"t"."bonus" ASC', 'x DESC', '']

    checked = 0
    disagreements = 0

    def check(op_sql, op_decimal, out_kind, part_sql, order_sql):
        nonlocal checked, disagreements
        decimal_out, window_text, real, shad = one_trial(
            op_sql, op_decimal, out_kind, part_sql, order_sql)
        shadow_spec_crosscheck(op_sql, window_text, decimal_out, op_decimal)
        checked += 1
        if real != shad:
            disagreements += 1
            print("DISAGREEMENT")
            print("  operand=%r operand_decimal=%r out_kind=%r "
                  "partition=%r order=%r" % (op_sql, op_decimal, out_kind,
                                             part_sql, order_sql))
            print("  window_text=%r decimal_out=%r" % (window_text,
                                                       decimal_out))
            print("  real  =%r" % real)
            print("  shadow=%r" % shad)

    # Boundary grid: every operand x output-kind x operand-type x a rotating
    # window shape (full cross on the flags, sampled cross on window parts).
    for op_sql in boundary_ops:
        for op_decimal in (False, True):
            for out_kind in ('dec', 'nondec', 'resolve'):
                for part_sql in boundary_parts:
                    for order_sql in boundary_orders:
                        check(op_sql, op_decimal, out_kind, part_sql,
                              order_sql)
                        if disagreements >= 10:
                            break
                    if disagreements >= 10:
                        break
                if disagreements >= 10:
                    break
            if disagreements >= 10:
                break
        if disagreements >= 10:
            break

    # Fuzz: random SQL-ish fragments over a token alphabet that includes the
    # cast/OVER literal characters, quotes, parens and separators.
    alphabet = 'ABCOVERSTNUMIC"().,_ %0129xy\''
    i = 0
    while i < N_FUZZ and disagreements < 10:
        op_sql = ''.join(rng.choice(alphabet)
                         for _ in range(rng.randint(0, 24)))
        op_decimal = rng.random() < 0.5
        out_kind = rng.choice(('dec', 'nondec', 'resolve'))
        part_sql = (None if rng.random() < 0.2 else
                    ''.join(rng.choice(alphabet)
                            for _ in range(rng.randint(0, 16))))
        order_sql = (None if rng.random() < 0.5 else
                     ''.join(rng.choice(alphabet)
                             for _ in range(rng.randint(0, 16))))
        check(op_sql, op_decimal, out_kind, part_sql, order_sql)
        i += 1

    report = {"disagreements": disagreements, "checked": checked,
              "seed": SEED,
              "shadow": "direct (contract-stripped impl region)"}
    print(json.dumps(report))
    return 0 if disagreements == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
