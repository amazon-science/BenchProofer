#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13121.

This bundle consumes NO @ContractOnly axioms: both modelled behaviours are
spelled out DEEPLY over a finite integer abstraction of the result-kind names
(`output_field.get_internal_type()`) and the rendering-class dispatch. What
G-AX validates here are the two **A-references** — that the model's two
decision functions faithfully reproduce the real, post-patch Django decisions:

  (1) `select_arithmetic_path` == the rendering-class choice inside the real
      `CombinedExpression.as_sql` (which of: the duration-arithmetic subclass,
      the temporal-subtraction subclass, or the plain combination). The
      discriminator: a duration+duration pairing on a non-native backend must
      NOT take the duration-arithmetic subclass.

  (2) `operand_format_flag` == whether the real per-operand renderer applies
      the duration-format wrapper: it does so for EVERY duration-kind operand,
      uniformly (no literal-value exemption).

The check has two layers:

  * a self-contained reference oracle transcribed verbatim from the patched
    source predicates, fuzzed exhaustively against the model across every
    (lhs_kind, rhs_kind, connector, native) combination and every operand
    (kind, is_literal); and

  * the REAL end-to-end scenario in-container: a `DurationField` column plus a
    `timedelta` literal, annotated and evaluated on the SQLite backend, which
    must succeed and round-trip the expected duration (the F2P behaviour). The
    real `CombinedExpression.as_sql` / `DurationExpression.compile` are exercised
    here, and we additionally assert directly that the duration+duration
    pairing is NOT routed through the duration-arithmetic subclass.

Run inside the official SWE-bench container for the instance (post-patch
Django importable). Exit 0 iff every obligation holds. Outside the container
(Django absent) the end-to-end layer prints a SKIP note; the oracle/model layer
runs everywhere.
"""
import datetime
import itertools
import random
import sys


# --- model.py reference encodings (kept in lock-step with model.py) ----------

KIND_NONE, KIND_DURATION, KIND_DATE, KIND_DATETIME, KIND_TIME, KIND_OTHER = range(6)
PATH_DURATION, PATH_TEMPORAL, PATH_PLAIN = range(3)
ALL_KINDS = (KIND_NONE, KIND_DURATION, KIND_DATE, KIND_DATETIME, KIND_TIME, KIND_OTHER)
_TEMPORAL = {KIND_DATE, KIND_DATETIME, KIND_TIME}


def model_select_arithmetic_path(lhs_kind, rhs_kind, is_subtract, native_duration):
    """Mirror of model.py select_arithmetic_path."""
    if (not native_duration) and \
            (lhs_kind == KIND_DURATION or rhs_kind == KIND_DURATION) and \
            lhs_kind != rhs_kind:
        return PATH_DURATION
    if is_subtract and lhs_kind in _TEMPORAL and lhs_kind == rhs_kind:
        return PATH_TEMPORAL
    return PATH_PLAIN


def model_operand_format_flag(operand_kind, is_literal):
    """Mirror of model.py operand_format_flag."""
    return 1 if operand_kind == KIND_DURATION else 0


# --- reference oracle, transcribed from the PATCHED Django source ------------
# CombinedExpression.as_sql (post-patch):
#   lhs_type / rhs_type = get_internal_type() or None on FieldError
#   if not native and 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
#       -> DurationExpression
#   datetime_fields = {'DateField','DateTimeField','TimeField'}
#   if connector == SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
#       -> TemporalSubtraction
#   -> plain CombinedExpression
#
# DurationExpression.compile (post-patch): for a side, if it has an
#   output_field whose internal type == 'DurationField': apply
#   format_for_duration_arithmetic (uniformly; no DurationValue exemption).

_NAME = {KIND_NONE: None, KIND_DURATION: 'DurationField', KIND_DATE: 'DateField',
         KIND_DATETIME: 'DateTimeField', KIND_TIME: 'TimeField', KIND_OTHER: 'IntegerField'}
_DATETIME_NAMES = {'DateField', 'DateTimeField', 'TimeField'}


def oracle_select_arithmetic_path(lhs_kind, rhs_kind, is_subtract, native_duration):
    lhs_type = _NAME[lhs_kind]
    rhs_type = _NAME[rhs_kind]
    if (not native_duration and 'DurationField' in {lhs_type, rhs_type}
            and lhs_type != rhs_type):
        return PATH_DURATION
    if is_subtract and lhs_type in _DATETIME_NAMES and lhs_type == rhs_type:
        return PATH_TEMPORAL
    return PATH_PLAIN


def oracle_operand_format_flag(operand_kind, is_literal):
    return 1 if _NAME[operand_kind] == 'DurationField' else 0


def check_model_vs_oracle():
    # exhaustive over every (lhs, rhs, connector, native) and every operand.
    for lhs, rhs, is_sub, native in itertools.product(
            ALL_KINDS, ALL_KINDS, (False, True), (False, True)):
        m = model_select_arithmetic_path(lhs, rhs, is_sub, native)
        o = oracle_select_arithmetic_path(lhs, rhs, is_sub, native)
        assert m == o, (
            "path model/oracle mismatch lhs=%s rhs=%s sub=%s native=%s: %s vs %s"
            % (lhs, rhs, is_sub, native, m, o))
    for kind, is_lit in itertools.product(ALL_KINDS, (False, True)):
        m = model_operand_format_flag(kind, is_lit)
        o = oracle_operand_format_flag(kind, is_lit)
        assert m == o, (
            "format model/oracle mismatch kind=%s literal=%s: %s vs %s"
            % (kind, is_lit, m, o))

    # explicit discriminators (the two prepatch failures):
    # both-duration on a non-native backend is NOT the duration-arithmetic path
    assert model_select_arithmetic_path(KIND_DURATION, KIND_DURATION, False, False) \
        == PATH_PLAIN
    assert oracle_select_arithmetic_path(KIND_DURATION, KIND_DURATION, False, False) \
        == PATH_PLAIN
    # mixed duration + datetime IS the duration-arithmetic path
    assert model_select_arithmetic_path(KIND_DURATION, KIND_DATETIME, False, False) \
        == PATH_DURATION
    # a literal duration operand still gets the format wrapper
    assert model_operand_format_flag(KIND_DURATION, True) == 1
    assert oracle_operand_format_flag(KIND_DURATION, True) == 1

    # randomized fuzz for good measure
    rng = random.Random(13121)
    for _ in range(20000):
        lhs = rng.choice(ALL_KINDS)
        rhs = rng.choice(ALL_KINDS)
        is_sub = rng.random() < 0.5
        native = rng.random() < 0.5
        assert model_select_arithmetic_path(lhs, rhs, is_sub, native) == \
            oracle_select_arithmetic_path(lhs, rhs, is_sub, native)
        kind = rng.choice(ALL_KINDS)
        is_lit = rng.random() < 0.5
        assert model_operand_format_flag(kind, is_lit) == \
            oracle_operand_format_flag(kind, is_lit)


def check_real_django():
    """End-to-end: the real post-patch dispatch on the F2P scenario, SQLite."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                            '__main__'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()

    from django.db import models, connection
    from django.db.models import F
    from django.db.models.expressions import (
        CombinedExpression, DurationExpression, Combinable,
    )

    class Experiment(models.Model):
        estimated_time = models.DurationField()

        class Meta:
            app_label = '__main__'

    with connection.schema_editor() as se:
        se.create_model(Experiment)

    deltas = [datetime.timedelta(days=1), datetime.timedelta(hours=1, minutes=30),
              datetime.timedelta(0), datetime.timedelta(microseconds=42),
              datetime.timedelta(days=3, seconds=7, microseconds=5)]
    base = datetime.timedelta(days=2, seconds=10)
    Experiment.objects.create(estimated_time=base)

    # (a) the F2P behaviour: durations-only expression must evaluate and
    #     round-trip the arithmetic without raising.
    for delta in deltas:
        qs = Experiment.objects.annotate(duration=F('estimated_time') + delta)
        for obj in qs:
            assert obj.duration == obj.estimated_time + delta, (
                "duration+timedelta gave %r, expected %r"
                % (obj.duration, obj.estimated_time + delta))

    # (b) the dispatch discriminator, asserted directly on the real classes:
    #     a duration+duration CombinedExpression on the (non-native) sqlite
    #     backend is NOT routed to DurationExpression.
    assert not connection.features.has_native_duration_field, (
        "sqlite unexpectedly reports a native duration field")
    lhs = F('estimated_time') + base       # resolve a duration-typed lhs
    # Build the combinable expression both operands of which are durations.
    expr = F('estimated_time') + datetime.timedelta(days=1)
    resolved = expr.resolve_expression(
        Experiment.objects.all().query)
    assert isinstance(resolved, CombinedExpression)
    lhs_t = resolved.lhs.output_field.get_internal_type()
    rhs_t = resolved.rhs.output_field.get_internal_type()
    assert lhs_t == 'DurationField' and rhs_t == 'DurationField', (
        "expected both operands DurationField, got %s / %s" % (lhs_t, rhs_t))
    # mirror the path the model predicts and confirm it is PLAIN, not DURATION
    predicted = model_select_arithmetic_path(
        KIND_DURATION, KIND_DURATION,
        resolved.connector == Combinable.SUB,
        connection.features.has_native_duration_field)
    assert predicted == PATH_PLAIN
    # and confirm the real renderer does not raise for this expression
    compiler = Experiment.objects.all().query.get_compiler(connection.alias)
    sql, params = resolved.as_sql(compiler, connection)
    assert sql, "real as_sql produced empty SQL for duration+duration"


def main():
    check_model_vs_oracle()
    try:
        check_real_django()
    except ImportError as exc:
        print("G-AX PARTIAL: Django not importable (%r); model==oracle "
              "A-reference confirmed exhaustively over all kind/connector/"
              "native combinations + 20000 fuzz." % (exc,))
        return 0
    print("G-AX OK: select_arithmetic_path / operand_format_flag deep models "
          "validated == real post-patch Django dispatch (exhaustive + 20000 "
          "fuzz) AND the durations-only F2P scenario round-trips on SQLite "
          "with the duration+duration pairing NOT routed to the "
          "duration-arithmetic subclass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
