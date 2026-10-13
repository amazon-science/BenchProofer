"""Twin-artifact model for django__django-13121.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An arithmetic combination of two query operands is rendered to backend SQL
  along one of three code paths, chosen from the declared result kinds of the
  two operands, the operator, and whether the backend stores durations
  natively:

  (1) DURATION-arithmetic path — selected (only when the backend lacks a native
      duration storage type) exactly when the two operand kinds differ and at
      least one of them is a duration (e.g. a date/datetime kind paired with a
      duration kind). A pairing whose two operand kinds are equal is never on
      this path, including the case where both kinds are durations.

  (2) TEMPORAL-subtraction path — selected for the subtraction of two operands
      of the same temporal kind (date/datetime/time).

  (3) PLAIN combination path — every other pairing.

  Independently, when an operand is rendered ON the duration-arithmetic path,
  the per-operand format flag is set for an operand exactly when that operand's
  result kind is a duration. The flag depends only on the operand's result
  kind; it does not depend on whether the operand is a literal value or a
  stored column reference.

Field result kinds and the chosen path are modelled as small integer codes
(an int refinement of the finite set of `get_internal_type()` names and of the
expression-class dispatch); see refinement.md / mapping.md for the bijection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: both behaviours are modelled deeply over the
#  finite integer abstraction of field-kind codes and dispatch-path codes.)
# axioms-end


# pure-start
# Result-kind codes (int refinement of output_field.get_internal_type()):
@Pure
def KIND_NONE() -> int:
    # no resolvable result kind (operand has no output field)
    return 0


@Pure
def KIND_DURATION() -> int:
    return 1


@Pure
def KIND_DATE() -> int:
    return 2


@Pure
def KIND_DATETIME() -> int:
    return 3


@Pure
def KIND_TIME() -> int:
    return 4


@Pure
def KIND_OTHER() -> int:
    # any non-temporal, non-duration kind (integer, char, ...)
    return 5


# Dispatch-path codes (int refinement of the chosen rendering class):
@Pure
def PATH_DURATION() -> int:
    return 0


@Pure
def PATH_TEMPORAL() -> int:
    return 1


@Pure
def PATH_PLAIN() -> int:
    return 2


@Pure
def is_kind(k: int) -> bool:
    return k == 0 or k == 1 or k == 2 or k == 3 or k == 4 or k == 5


@Pure
def is_temporal_kind(k: int) -> bool:
    # date / datetime / time form the temporal-subtraction family
    return k == 2 or k == 3 or k == 4
# pure-end


def select_arithmetic_path(lhs_kind: int, rhs_kind: int,
                           is_subtract: bool, native_duration: bool) -> int:
    # pre-conditions-start
    Requires(is_kind(lhs_kind))
    Requires(is_kind(rhs_kind))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
            or Result() == PATH_PLAIN())
    # (1) duration-arithmetic ONLY for a mixed pairing: exactly one operand a
    #     duration AND the two kinds differ, on a non-native backend.
    Ensures(Implies(
        (not native_duration)
        and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
        and lhs_kind != rhs_kind,
        Result() == PATH_DURATION()))
    # A both-duration pairing is NOT the duration path (the discriminator).
    Ensures(Implies(
        lhs_kind == KIND_DURATION() and rhs_kind == KIND_DURATION(),
        Result() != PATH_DURATION()))
    # (2) temporal subtraction for same-kind temporal operands under SUB.
    Ensures(Implies(
        (not (
            (not native_duration)
            and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
            and lhs_kind != rhs_kind))
        and is_subtract and is_temporal_kind(lhs_kind)
        and lhs_kind == rhs_kind,
        Result() == PATH_TEMPORAL()))
    # (3) everything else is the plain path.
    Ensures(Implies(
        not (
            (not native_duration)
            and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
            and lhs_kind != rhs_kind)
        and not (
            is_subtract and is_temporal_kind(lhs_kind)
            and lhs_kind == rhs_kind),
        Result() == PATH_PLAIN()))
    # post-conditions-end
    # impl-start
    if (not native_duration) and \
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()):
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()
    # impl-end


def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
    # pre-conditions-start
    Requires(is_kind(operand_kind))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 0 or Result() == 1)
    # The duration-format wrapper is applied to EVERY duration-kind operand,
    # uniformly — independent of whether the operand is a literal value.
    Ensures(Result() == 1 if operand_kind == KIND_DURATION() else Result() == 0)
    # post-conditions-end
    # impl-start
    if operand_kind == KIND_DURATION():
        return 1
    return 0
    # impl-end
