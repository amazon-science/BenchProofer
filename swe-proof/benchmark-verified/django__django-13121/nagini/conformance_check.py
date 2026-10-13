#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13121 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (KIND_*/PATH_* code
constants, is_kind, is_temporal_kind) are copied over as plain functions.
There are no @ContractOnly callees.

ORACLE: the REAL patched repo functions the model models per mapping.md:

  (1) select_arithmetic_path <-> the rendering-class dispatch inside
      ``django.db.models.expressions.CombinedExpression.as_sql``. The gate
      applies patch.diff to /testbed before this script runs, so the imported
      class carries the patched body. Which rendering class the real dispatch
      chooses is observed by temporarily replacing the two subclass renderers
      (``DurationExpression.as_sql`` / ``TemporalSubtraction.as_sql``) with
      sentinel returners; the plain-combination body runs to completion
      against a minimal compiler/connection double. The observed target is
      mapped to the model's PATH_* code.

  (2) operand_format_flag <-> the per-operand decision inside the REAL
      ``DurationExpression.compile`` (left unpatched by the sentinels, which
      only replace ``as_sql``). Whether the duration-format wrapper was
      applied to the operand is observed through a marking
      ``format_for_duration_arithmetic`` on the connection double, and mapped
      to the model's 0/1 flag.

Type bridge (mapping.md section 2):
  * KIND_* int codes <-> ``output_field.get_internal_type()`` names, with
    KIND_NONE <-> "the output_field access raises FieldError". Operands are
    realized as either a column-reference-shaped double exposing a REAL
    django field instance, or a REAL literal ``Value(...)`` expression
    carrying a matching python value — the ``is_literal`` bool of the model
    maps to which of the two operand shapes is presented. KIND_OTHER covers
    every non-temporal/non-duration internal type; several distinct real
    field classes are sampled for it (the dispatch reads kinds only through
    equality and finite-set membership, so the collapse is faithful).
  * is_subtract <-> ``connector == Combinable.SUB``; False is exercised over
    several non-SUB connectors (ADD/MUL/DIV).
  * native_duration <-> ``connection.features.has_native_duration_field``.
  * PATH_* int codes <-> which of the three rendering bodies runs.

Input domain: the preconditions demand only is_kind(...) on each kind code,
so every draw from the 6-value kind sets (with any bools/connectors/shapes)
is Requires-satisfying. Boundary layer: exhaustive over all
(lhs_kind, rhs_kind, connector in {SUB, ADD}, native) for the dispatch and
all (operand_kind, is_literal) for the format flag. Fuzz layer: 100000 draws,
each checking one dispatch input AND one format-flag input, with randomized
operand shapes, OTHER-field identities, and non-SUB connectors.

>= 1e5 Requires-satisfying inputs. Pinned seed: 13121.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (runs in-container with PYTHONPATH=/testbed).
"""
import datetime
import itertools
import random
import sys
from unittest import mock

SEED = 13121
N_FUZZ = 100000


# --- pure helpers + impl region of model.py, verbatim, contracts stripped ----

def KIND_NONE() -> int:
    # no resolvable result kind (operand has no output field)
    return 0


def KIND_DURATION() -> int:
    return 1


def KIND_DATE() -> int:
    return 2


def KIND_DATETIME() -> int:
    return 3


def KIND_TIME() -> int:
    return 4


def KIND_OTHER() -> int:
    # any non-temporal, non-duration kind (integer, char, ...)
    return 5


def PATH_DURATION() -> int:
    return 0


def PATH_TEMPORAL() -> int:
    return 1


def PATH_PLAIN() -> int:
    return 2


def is_kind(k: int) -> bool:
    return k == 0 or k == 1 or k == 2 or k == 3 or k == 4 or k == 5


def is_temporal_kind(k: int) -> bool:
    # date / datetime / time form the temporal-subtraction family
    return k == 2 or k == 3 or k == 4


def select_arithmetic_path(lhs_kind: int, rhs_kind: int,
                           is_subtract: bool, native_duration: bool) -> int:
    if (not native_duration) and \
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()


def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
    if operand_kind == KIND_DURATION():
        return 1
    return 0


# --- real patched repo under test ---------------------------------------------

import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(USE_TZ=False)
django.setup()

from django.core.exceptions import FieldError  # noqa: E402
from django.db.models import fields  # noqa: E402
from django.db.models.expressions import (  # noqa: E402
    Combinable, CombinedExpression, DurationExpression, TemporalSubtraction,
    Value,
)


# --- operand construction (the KIND <-> internal-type-name bridge) ------------

def _other_field(rng):
    """A real field instance from the (open) non-temporal/non-duration family;
    several distinct classes are sampled so the two sides of a pairing can
    carry distinct OTHER names."""
    cls = rng.choice((fields.IntegerField, fields.CharField, fields.FloatField,
                      fields.BooleanField, fields.TextField,
                      fields.DecimalField, fields.UUIDField))
    return cls()


def _field_for_kind(kind, rng):
    """Real django field instance for a kind code; None for KIND_NONE."""
    if kind == KIND_NONE():
        return None
    if kind == KIND_DURATION():
        return fields.DurationField()
    if kind == KIND_DATE():
        return fields.DateField()
    if kind == KIND_DATETIME():
        return fields.DateTimeField()
    if kind == KIND_TIME():
        return fields.TimeField()
    return _other_field(rng)


_LITERAL_VALUE = {
    # a python literal matching each resolvable kind, for the Value(...) shape
    KIND_DURATION(): datetime.timedelta(days=1, seconds=7, microseconds=5),
    KIND_DATE(): datetime.date(2001, 2, 3),
    KIND_DATETIME(): datetime.datetime(2001, 2, 3, 4, 5, 6),
    KIND_TIME(): datetime.time(4, 5, 6),
}


class _ColRef:
    """Column-reference-shaped operand double: exposes a real field instance
    as output_field, or raises FieldError when there is none (KIND_NONE)."""

    def __init__(self, field):
        self._field = field

    @property
    def output_field(self):
        if self._field is None:
            raise FieldError("cannot resolve an output field for this operand")
        return self._field


def _make_operand(kind, is_literal, rng):
    """Realize a kind code as a concrete operand. is_literal selects the
    real-literal Value(...) shape; KIND_NONE has no resolvable field under
    either shape, so it always uses the field-less double."""
    field = _field_for_kind(kind, rng)
    if field is None:
        return _ColRef(None)
    if is_literal:
        if kind == KIND_OTHER():
            # keep the literal's python type aligned with a concrete field
            return Value(42, output_field=fields.IntegerField())
        return Value(_LITERAL_VALUE[kind], output_field=field)
    return _ColRef(field)


# --- compiler / connection doubles --------------------------------------------

_FMT_MARK = "\x00FMT\x00"


class _Compiler:
    def compile(self, node):
        return "OPERAND_SQL", []


class _Features:
    def __init__(self, native):
        self.has_native_duration_field = native


class _Ops:
    def combine_expression(self, connector, expressions):
        return (" %s " % connector).join(expressions)

    def combine_duration_expression(self, connector, expressions):
        return (" %s " % connector).join(expressions)

    def format_for_duration_arithmetic(self, sql):
        # marking wrapper: lets the driver observe the per-operand decision
        return _FMT_MARK + sql

    def check_expression_support(self, expression):
        pass


class _Conn:
    def __init__(self, native):
        self.features = _Features(native)
        self.ops = _Ops()


# --- oracle drivers ------------------------------------------------------------

_SENTINEL_DUR = "\x00PATH_DURATION\x00"
_SENTINEL_TMP = "\x00PATH_TEMPORAL\x00"

_NON_SUB = (Combinable.ADD, Combinable.MUL, Combinable.DIV)


def real_dispatch_path(lhs, rhs, connector, native):
    """PATH_* code the REAL patched CombinedExpression.as_sql dispatches to.
    Assumes the subclass-renderer sentinels are installed (see main)."""
    expr = CombinedExpression(lhs, connector, rhs)
    sql, _params = expr.as_sql(_Compiler(), _Conn(native))
    if sql == _SENTINEL_DUR:
        return PATH_DURATION()
    if sql == _SENTINEL_TMP:
        return PATH_TEMPORAL()
    return PATH_PLAIN()


_DUR_EXPR = None  # a DurationExpression instance to bind .compile to (lazy)


def real_format_flag(side):
    """0/1: did the REAL patched DurationExpression.compile apply the
    duration-format wrapper to this operand? (compile is untouched by the
    as_sql sentinels.)"""
    global _DUR_EXPR
    if _DUR_EXPR is None:
        _DUR_EXPR = DurationExpression(
            _ColRef(fields.DurationField()), Combinable.ADD,
            _ColRef(fields.DurationField()))
    sql, _params = _DUR_EXPR.compile(side, _Compiler(), _Conn(False))
    return 1 if sql.startswith(_FMT_MARK) else 0


# --- differential driver --------------------------------------------------------

def check_dispatch(lhs_kind, rhs_kind, is_subtract, connector,
                   lhs_lit, rhs_lit, native, rng):
    shadow = select_arithmetic_path(lhs_kind, rhs_kind, is_subtract, native)
    lhs = _make_operand(lhs_kind, lhs_lit, rng)
    rhs = _make_operand(rhs_kind, rhs_lit, rng)
    try:
        real = real_dispatch_path(lhs, rhs, connector, native)
    except Exception as e:  # the shadow never raises; a raise is a divergence
        return ("DISAGREEMENT (dispatch) on lhs_kind=%d rhs_kind=%d "
                "is_subtract=%r connector=%r lhs_literal=%r rhs_literal=%r "
                "native=%r:\n  shadow (impl region) = %r\n  real dispatch "
                "raised %r" % (lhs_kind, rhs_kind, is_subtract, connector,
                               lhs_lit, rhs_lit, native, shadow, e))
    if shadow != real:
        return ("DISAGREEMENT (dispatch) on lhs_kind=%d rhs_kind=%d "
                "is_subtract=%r connector=%r lhs_literal=%r rhs_literal=%r "
                "native=%r:\n  shadow (impl region) = %r\n  real dispatch "
                "= %r" % (lhs_kind, rhs_kind, is_subtract, connector,
                          lhs_lit, rhs_lit, native, shadow, real))
    return None


def check_format(operand_kind, is_literal, rng):
    shadow = operand_format_flag(operand_kind, is_literal)
    side = _make_operand(operand_kind, is_literal, rng)
    try:
        real = real_format_flag(side)
    except Exception as e:
        return ("DISAGREEMENT (format) on operand_kind=%d is_literal=%r:\n"
                "  shadow (impl region) = %r\n  real compile raised %r"
                % (operand_kind, is_literal, shadow, e))
    if shadow != real:
        return ("DISAGREEMENT (format) on operand_kind=%d is_literal=%r:\n"
                "  shadow (impl region) = %r\n  real format decision = %r"
                % (operand_kind, is_literal, shadow, real))
    return None


ALL_KINDS = (KIND_NONE(), KIND_DURATION(), KIND_DATE(), KIND_DATETIME(),
             KIND_TIME(), KIND_OTHER())


def main():
    rng = random.Random(SEED)
    checked = 0

    # sentinel renderers: observe the real dispatch target without running
    # the (I/O-free but compiler-heavy) subclass bodies
    patches = [
        mock.patch.object(
            DurationExpression, "as_sql",
            lambda self, compiler, connection: (_SENTINEL_DUR, [])),
        mock.patch.object(
            TemporalSubtraction, "as_sql",
            lambda self, compiler, connection: (_SENTINEL_TMP, [])),
    ]
    for p in patches:
        p.start()
    try:
        # boundary: exhaustive dispatch domain (both operand shapes covered
        # deterministically via the two literal-flag axes)
        n_boundary = 0
        for lhs_k, rhs_k, sub, native, lhs_lit, rhs_lit in itertools.product(
                ALL_KINDS, ALL_KINDS, (False, True), (False, True),
                (False, True), (False, True)):
            connector = Combinable.SUB if sub else Combinable.ADD
            err = check_dispatch(lhs_k, rhs_k, sub, connector,
                                 lhs_lit, rhs_lit, native, rng)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1
        # boundary: exhaustive format-flag domain
        for kind, is_lit in itertools.product(ALL_KINDS, (False, True)):
            err = check_format(kind, is_lit, rng)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

        # fuzz: randomized shapes, OTHER-field identities, non-SUB connectors
        for _ in range(N_FUZZ):
            lhs_k = rng.choice(ALL_KINDS)
            rhs_k = rng.choice(ALL_KINDS)
            sub = rng.random() < 0.5
            connector = Combinable.SUB if sub else rng.choice(_NON_SUB)
            native = rng.random() < 0.5
            lhs_lit = rng.random() < 0.5
            rhs_lit = rng.random() < 0.5
            err = check_dispatch(lhs_k, rhs_k, sub, connector,
                                 lhs_lit, rhs_lit, native, rng)
            if err:
                print(err)
                return 1
            checked += 1

            kind = rng.choice(ALL_KINDS)
            is_lit = rng.random() < 0.5
            err = check_format(kind, is_lit, rng)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        for p in patches:
            p.stop()

    print("G-CONF OK: shadow impl == real patched dispatch/format decisions "
          "on %d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, 2 * N_FUZZ, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
