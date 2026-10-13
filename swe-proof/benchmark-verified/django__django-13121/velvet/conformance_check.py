#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13121 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`dispatchNode`,
              the renderer selection of a generic binary arithmetic node)
              transliterated to Python, over the abstract carrier
              (native, connector, lt, rt) via the mapping.md bijection. There
              are NO A-tagged callees in the impl region (no axioms in this
              bundle); the operand output-type tags `lt`/`rt`, the connector,
              and the native-interval capability are R-tagged abstracted INPUTS
              supplied directly. So the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.models.expressions.CombinedExpression.as_sql` applied at
              base_commit, observed as the *renderer* the SQL-generation step
              selects (the F2P-observable dispatch decision: which of the generic
              combine / DurationExpression / TemporalSubtraction renders the
              node). The harness applies patch.diff before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only
(no live DB — we drive `as_sql` with a recording stub compiler/connection and
detect which renderer branch fires). The fuzz seed is pinned (mapping.md §4) for
a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 13121
N_FUZZ = 100_000

# ---- abstract carrier domains (Solution.lean inductives) --------------------
# FieldTag ∪ {None}: the resolved output-type tag of an operand, or None for
# "no resolvable output type" (the FieldError outcome).
FIELD_TAGS = ["date", "datetime", "time", "duration", "other", None]
CONNECTORS = ["+", "-"]            # Connector.plus / Connector.minus
NATIVE = [False, True]             # connection.features.has_native_duration_field

_TEMPORAL = {"date", "datetime", "time"}


# ---- the R/I shadow: dispatchNode transliterated to Python ------------------
def shadow_dispatch(native, conn, lt, rt):
    """`dispatchNode native conn lt rt` (Solution.lean pure region)."""
    # isIntervalMix lt rt: (lt or rt is duration) and lt != rt
    if (native is False) and ((lt == "duration" or rt == "duration") and lt != rt):
        return "duration"
    # conn = minus ∧ isTemporalTag lt ∧ lt = rt
    if conn == "-" and lt in _TEMPORAL and lt == rt:
        return "temporal"
    return "combined"


# ---- the oracle: the patched real CombinedExpression.as_sql -----------------
def _build_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={})
        django.setup()
    from django.db.models import expressions as exprmod
    from django.db.models.expressions import (
        CombinedExpression, DurationExpression, TemporalSubtraction, Value)
    from django.db.models import fields
    return exprmod, CombinedExpression, DurationExpression, TemporalSubtraction, Value, fields


def _operand(tag, Value, fields):
    """mapping.md §2 bijection: a FieldTag ↔ a resolved operand carrying that
    output type. `None` ↔ an operand whose `output_field` raises FieldError."""
    table = {
        "date": fields.DateField,
        "datetime": fields.DateTimeField,
        "time": fields.TimeField,
        "duration": fields.DurationField,
        "other": fields.IntegerField,
    }
    if tag is None:
        return Value(1)                 # no output_field -> .output_field raises FieldError -> None
    return Value(1, output_field=table[tag]())


class _Marker(Exception):
    """Carries which specialised renderer branch fired."""
    def __init__(self, kind):
        self.kind = kind


class _StubCompiler:
    def compile(self, node):
        return ("SQL", [])


class _StubOps:
    def combine_expression(self, connector, expressions):
        return "SQL"


class _StubFeatures:
    def __init__(self, native):
        self.has_native_duration_field = native


class _StubConnection:
    def __init__(self, native):
        self.features = _StubFeatures(native)
        self.ops = _StubOps()


def make_oracle(exprmod, CombinedExpression, DurationExpression, TemporalSubtraction, Value, fields):
    # Record which specialised renderer the patched as_sql dispatches to by
    # replacing their as_sql with a marker; the generic fall-through returns a
    # normal SQL tuple via the stub compiler/connection -> "combined".
    def _dur_as_sql(self, compiler, connection):
        raise _Marker("duration")

    def _tmp_as_sql(self, compiler, connection):
        raise _Marker("temporal")

    DurationExpression.as_sql = _dur_as_sql
    TemporalSubtraction.as_sql = _tmp_as_sql

    def oracle(native, conn, lt, rt):
        lhs = _operand(lt, Value, fields)
        rhs = _operand(rt, Value, fields)
        node = CombinedExpression(lhs, conn, rhs)
        compiler = _StubCompiler()
        connection = _StubConnection(native)
        try:
            node.as_sql(compiler, connection)
        except _Marker as m:
            return m.kind
        return "combined"

    return oracle


def all_configs():
    """The full abstract product (2*2*6*6 = 144) — boundary enumeration."""
    return list(itertools.product(NATIVE, CONNECTORS, FIELD_TAGS, FIELD_TAGS))


def fuzz_configs(n, rng):
    for _ in range(n):
        yield (rng.choice(NATIVE), rng.choice(CONNECTORS),
               rng.choice(FIELD_TAGS), rng.choice(FIELD_TAGS))


def main():
    rng = random.Random(SEED)
    bundle = _build_django()
    oracle = make_oracle(*bundle)
    disagreements = []
    count = 0
    for cfg in itertools.chain(all_configs(), fuzz_configs(N_FUZZ, rng)):
        count += 1
        shadow = shadow_dispatch(*cfg)
        truth = oracle(*cfg)
        if shadow != truth:
            disagreements.append((cfg, shadow, truth))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, tr in disagreements:
            print("  cfg=%r shadow=%r oracle=%r" % (cfg, sh, tr))
        return 1
    print("G-CONF OK: R/I shadow of selectRenderer (dispatchNode) agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
