"""Twin-artifact model for django__django-13128.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A binary database expression combining two operands with an arithmetic
  connector must, at the moment it is prepared for a query, classify itself by
  the (already-resolved) output types of its two operands and the connector,
  and become the specialised temporal form whenever the operands are temporal:

    * If the expression is ALREADY a specialised temporal/duration form, it is
      left as-is (it does not re-classify itself).
    * Otherwise, looking at the two resolved operand output types T_lhs, T_rhs
      (either of which may be UNKNOWN when an operand exposes no output type):
        - if exactly one of the two types is the duration type (a duration is
          present and the two types differ), the expression becomes the
          DURATION form;
        - otherwise, if the connector is subtraction and both operand types are
          the SAME date/time type (date, datetime or time), the expression
          becomes the TEMPORAL-SUBTRACTION form;
        - otherwise it stays the PLAIN combined form.

  The classification is decided from the operand types themselves, so a bare
  temporal subtraction (e.g. one date/time operand minus another of the same
  date/time type) is recognised as a temporal subtraction WITHOUT the caller
  having to wrap it and declare its output type by hand.

Operand output types are modelled as small integer codes (a finite enumeration
of the relevant field kinds); the expression classification is the integer
"kind" code the resolution produces. The connector is modelled by a boolean
"is this the subtraction connector".  See mapping.md for the bijection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the classification of a combined expression is modelled
#  DEEPLY below as the dispatch over the operand type codes. The operand output
#  types it inspects are produced by already-modelled resolution of the
#  sub-expressions, not by an opaque external callee.)
# axioms-end


# pure-start
# Operand output-type codes (a finite enumeration of the relevant field kinds).
# UNKNOWN models "this operand exposes no usable output type" (the resolution
# treats a missing/unresolvable output type as not matching any concrete type).
T_UNKNOWN = 0     # no usable output type
T_DATE = 1        # date-only field
T_DATETIME = 2    # date+time field
T_TIME = 3        # time-only field
T_DURATION = 4    # duration field
T_OTHER = 5       # any other concrete field (e.g. an integer field)

# Resolution outcome kinds (which specialised expression the resolution yields).
K_PLAIN = 0       # the generic combined expression (no temporal specialisation)
K_DURATION = 1    # the duration-arithmetic form
K_TEMPORAL = 2    # the temporal-subtraction form


@Pure
def is_datetime_type(t: int) -> bool:
    """Whether a type code denotes one of the three date/time field kinds."""
    return t == T_DATE or t == T_DATETIME or t == T_TIME


@Pure
def wants_duration(t_lhs: int, t_rhs: int) -> bool:
    """A duration operand is present and the two operand types differ."""
    return (t_lhs == T_DURATION or t_rhs == T_DURATION) and t_lhs != t_rhs


@Pure
def wants_temporal(is_sub: bool, t_lhs: int, t_rhs: int) -> bool:
    """Subtraction of two operands of the same date/time type."""
    return is_sub and is_datetime_type(t_lhs) and t_lhs == t_rhs


@Pure
def resolved_kind(is_already_temporal: bool, is_sub: bool,
                  t_lhs: int, t_rhs: int) -> int:
    """The kind of expression the resolution yields, as a function of whether
    the expression is already a specialised temporal form, the connector, and
    the two resolved operand output types. This is the deep model of the
    resolve-time classification."""
    if is_already_temporal:
        return K_PLAIN
    if wants_duration(t_lhs, t_rhs):
        return K_DURATION
    if wants_temporal(is_sub, t_lhs, t_rhs):
        return K_TEMPORAL
    return K_PLAIN
# pure-end


def resolve_kind(is_already_temporal: bool, is_sub: bool,
                 t_lhs: int, t_rhs: int) -> int:
    # pre-conditions-start
    # The operand type codes are within the modelled enumeration.
    Requires(T_UNKNOWN <= t_lhs and t_lhs <= T_OTHER)
    Requires(T_UNKNOWN <= t_rhs and t_rhs <= T_OTHER)
    # Termination obligation. The level is ARGUMENT-DEPENDENT (not the constant
    # 2) so that a self-call is provable at all: Nagini demands the caller's
    # level be STRICTLY GREATER than the callee's, which a constant level can
    # never satisfy for a recursive call on the same method. With the level
    # ordered by t_lhs + t_rhs, a self-call on strictly smaller operand codes
    # descends, and one on equal-or-larger codes is correctly rejected.
    Requires(MustTerminate(2 + t_lhs + t_rhs))
    # pre-conditions-end
    # post-conditions-start
    # The outcome is one of the three classification kinds.
    Ensures(Result() == K_PLAIN or Result() == K_DURATION or
            Result() == K_TEMPORAL)
    # An already-specialised temporal expression is never re-classified.
    Ensures(Implies(is_already_temporal, Result() == K_PLAIN))
    # A duration operand present with differing operand types => duration form,
    # but only when not already specialised.
    Ensures((Result() == K_DURATION) ==
            (not is_already_temporal and wants_duration(t_lhs, t_rhs)))
    # Subtraction of two equal date/time operands => temporal-subtraction form,
    # unless duration dispatch already fired (and not already specialised).
    Ensures((Result() == K_TEMPORAL) ==
            (not is_already_temporal and not wants_duration(t_lhs, t_rhs) and
             wants_temporal(is_sub, t_lhs, t_rhs)))
    # Full functional pinning: the outcome is exactly the modelled dispatch.
    Ensures(Result() == resolved_kind(is_already_temporal, is_sub,
                                      t_lhs, t_rhs))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the resolution performed NO temporal/duration
    # classification — it simply resolved the operands and returned the generic
    # combined form, leaving the temporal dispatch to a later (SQL) stage that a
    # bare, unwrapped temporal subtraction never reached. Hence every expression
    # resolves to the plain kind.
    return K_PLAIN
    # impl-end
