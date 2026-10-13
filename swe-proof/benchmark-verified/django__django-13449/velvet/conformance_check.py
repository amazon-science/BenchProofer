#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13449 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`windowSql`,
              the SQL rendered for a windowed expression on a backend whose
              fixed-precision decimal results must be coerced with a numeric
              cast) transliterated to Python, over the abstract carrier
              (isDecimal, innerBase, win) via the mapping.md bijection. There are
              NO A-tagged callees in the impl region (no axioms in this bundle):
              the decimal flag, the operand SQL, and the assembled window clause
              are R-tagged abstracted INPUTS supplied directly, and the two
              string ops (`numericCast`, `overClause`) are I-tagged concrete
              transliterations. So the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.models.expressions.Window.as_sqlite` applied at
              base_commit, observed as the SQL STRING it renders. The harness
              applies patch.diff before this runs. We drive the real
              `Window.as_sqlite` through a recording stub compiler/connection
              (no live DB); the operand is a real `SQLiteNumericMixin`
              expression whose self-cast is governed by its output_field, so the
              fix's actual mechanism — forcing the operand to a float output so
              it does NOT self-cast, then casting the whole OVER expression — is
              exercised end to end.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. (At unpatched base_commit the inner
operand self-casts -> `CAST(LAG(...) AS NUMERIC) OVER (...)`, which disagrees
with the shadow's `CAST(LAG(...) OVER (...) AS NUMERIC)`: G-CONF validates the
PATCHED behaviour only, as intended.)

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=True,
    )
import django                                                # noqa: E402
django.setup()

from django.db.models import fields                          # noqa: E402
from django.db.models.expressions import (                   # noqa: E402
    Expression, SQLiteNumericMixin, Window,
)

SEED = 13449
N_FUZZ = 100_000


# ---- the R/I shadow: windowSql transliterated to Python ---------------------
def numeric_cast(sql):
    """`numericCast` (Solution.lean pure region)."""
    return "CAST(" + sql + " AS NUMERIC)"


def over_clause(expr, win):
    """`overClause` (Solution.lean pure region)."""
    return expr + " OVER (" + win + ")"


def shadow_window_sql(is_decimal, inner_base, win):
    """`windowSql is_decimal inner_base win` (Solution.lean pure region)."""
    if is_decimal:
        return numeric_cast(over_clause(inner_base, win))
    return over_clause(inner_base, win)


# ---- the oracle: the patched real Window.as_sqlite --------------------------
class _StubSource(SQLiteNumericMixin, Expression):
    """A real window-compatible operand whose rendered SQL is fixed (`base`) and
    whose self-cast is governed by `output_field` exactly like `Lag`/`Func`
    (both are `SQLiteNumericMixin`). This is the operand the window is computed
    over; the fix rewrites its `output_field` to a float so it does NOT
    self-cast (mapping.md §3)."""
    window_compatible = True

    def __init__(self, base, output_field):
        super().__init__(output_field=output_field)
        self.base = base

    def as_sql(self, compiler, connection, **extra_context):
        return self.base, []


class _StubClause:
    """Stands in for an already-assembled window clause: `Window.as_sql` calls
    `partition_by.as_sql(compiler=..., connection=..., template=...)` and
    `window_sql.extend(sql_expr)`; we return exactly `[win]` so the assembled
    window text is `win` (mapping.md §2: `win` is the R-input window clause)."""
    def __init__(self, win):
        self.win = win

    def as_sql(self, *args, **kwargs):
        return [self.win], []


class _StubFeatures:
    supports_over_clause = True


class _StubOps:
    def check_expression_support(self, expr):
        return None


class _StubConnection:
    vendor = "sqlite"
    features = _StubFeatures()
    ops = _StubOps()


class _StubCompiler:
    def __init__(self, connection):
        self.connection = connection

    def compile(self, node):
        # Mirror SQLCompiler.compile: dispatch to the vendor impl when present.
        vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
        if vendor_impl:
            return vendor_impl(self, self.connection)
        return node.as_sql(self, self.connection)


def _output_field(tag):
    """mapping.md §2 bijection: the windowed expression's result type."""
    return {
        "decimal": fields.DecimalField,
        "float": fields.FloatField,
        "integer": fields.IntegerField,
        "bigint": fields.BigIntegerField,
    }[tag]()


def oracle_window_sql(tag, inner_base, win):
    """Drive the patched real `Window.as_sqlite` and return the rendered SQL."""
    connection = _StubConnection()
    compiler = _StubCompiler(connection)
    # Fresh objects per call: the patch mutates the (shallow-shared) operand's
    # output_field on its copy, so reuse across calls would leak state.
    source = _StubSource(inner_base, _output_field(tag))
    win_node = Window(source)               # window_compatible source accepted
    win_node.partition_by = _StubClause(win)
    win_node.order_by = None
    win_node.frame = None
    sql, _params = win_node.as_sqlite(compiler, connection)
    return sql


# ---- inputs: the F2P scenario + boundary + broad fuzz -----------------------
NON_DECIMAL = ["float", "integer", "bigint"]
ALL_TAGS = ["decimal"] + NON_DECIMAL


def _rand_sql(rng):
    """A plausible operand-SQL fragment (content is opaque to the model)."""
    n = rng.randint(0, 18)
    alphabet = string.ascii_letters + string.digits + '_(), ."'
    body = "".join(rng.choice(alphabet) for _ in range(n))
    return rng.choice(['LAG(%s, 1)', 'LEAD(%s)', 'FIRST_VALUE(%s)',
                       '%s', 'SUM(%s)']) % body


def _rand_win(rng):
    """An already-assembled window clause (no leading/trailing whitespace, since
    `Window.as_sql` strips it; the model's `win` is the stripped text)."""
    parts = []
    if rng.random() < 0.7:
        parts.append('PARTITION BY "t"."d"')
    if rng.random() < 0.7:
        parts.append('ORDER BY "t"."b" ASC')
    return " ".join(parts)


def boundary_inputs():
    # The F2P scenario: a decimal Lag over a partition+order window.
    base = 'LAG("expressions_window_employee"."bonus", 1)'
    win = ('PARTITION BY "expressions_window_employee"."department" '
           'ORDER BY "expressions_window_employee"."bonus" ASC, '
           '"expressions_window_employee"."name" ASC')
    cases = [("decimal", base, win)]
    for tag in ALL_TAGS:
        cases.append((tag, base, win))
        cases.append((tag, "LAG(x)", ""))                 # empty window clause
        cases.append((tag, "", "ORDER BY y"))             # empty operand
        cases.append((tag, "", ""))                       # both empty
    return cases


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for tag, base, win in boundary_inputs():
        count += 1
        is_decimal = (tag == "decimal")
        shadow = shadow_window_sql(is_decimal, base, win)
        try:
            oracle = oracle_window_sql(tag, base, win)
        except Exception as e:                             # noqa: BLE001
            disagreements.append(((tag, base, win), "ORACLE-CRASH:" + repr(e), shadow))
            continue
        if shadow != oracle:
            disagreements.append(((tag, base, win), shadow, oracle))
        if len(disagreements) >= 8:
            break

    if not disagreements:
        for _ in range(N_FUZZ):
            tag = rng.choice(ALL_TAGS)
            base = _rand_sql(rng)
            win = _rand_win(rng)
            count += 1
            is_decimal = (tag == "decimal")
            shadow = shadow_window_sql(is_decimal, base, win)
            try:
                oracle = oracle_window_sql(tag, base, win)
            except Exception as e:                         # noqa: BLE001
                disagreements.append(((tag, base, win), "ORACLE-CRASH:" + repr(e), shadow))
            else:
                if shadow != oracle:
                    disagreements.append(((tag, base, win), shadow, oracle))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, orc in disagreements:
            print("  cfg=%r shadow=%r oracle=%r" % (cfg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of windowNumericSql (windowSql) agrees with "
          "patch.diff behaviour through the real patched Window.as_sqlite on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
