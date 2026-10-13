"""Twin-artifact model for django__django-16082.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A binary combination of two operand field types under a connector resolves to
  a single result field type by consulting a registry of permitted
  ``(left operand type, right operand type) -> result type`` rows recorded per
  connector. Resolution scans the rows recorded for the connector in
  registration order and yields the result type of the FIRST row whose recorded
  left/right operand types are each a supertype of (or equal to) the queried
  operand types; if no recorded row matches — including when the connector has
  no rows recorded at all — resolution yields the "unresolved" sentinel.

  Matching is by SUBTYPING, not by identity: a queried operand type matches a
  recorded operand type whenever it is that type or ANY type below it. The
  integer field type has an open-ended family of field types below it (the
  wide, narrow, non-negative and auto-increment integer types, and any further
  type derived from the integer type), and every one of them matches a recorded
  integer operand exactly as the integer type itself does. The date-time type
  lies below the date type and matches a recorded date operand likewise. A
  queried type that lies below no recorded operand type matches no row.

  The registry records, for every connector:

  NUMERIC, operands of the same type — for each of the five arithmetic
  connectors {addition, subtraction, multiplication, division, remainder} and
  for exponentiation:
      (integer, integer) -> integer      (any two types below integer included)
      (float, float)     -> float
      (decimal, decimal) -> decimal

  NUMERIC, operands of different type — for EVERY arithmetic connector in
  {addition, subtraction, multiplication, division, remainder}, the remainder
  connector on the SAME footing as the other four, and NOT for exponentiation:
      (integer, decimal) -> decimal      (decimal, integer) -> decimal
      (integer, float)   -> float        (float, integer)   -> float
  i.e. mixed numeric operands resolve to the WIDER of the two types (decimal is
  wider than integer, float is wider than integer). There is deliberately NO
  row for the decimal/float mixes in either order — no widening between decimal
  and float is defined — so those resolve to the unresolved sentinel.

  NUMERIC with the null-literal type — for the same six connectors as the
  same-type numeric rows, and ONLY for the float type:
      (float, null) -> float             (null, float) -> float
  the integer and decimal types have no row against the null-literal type.

  BITWISE — for each of the five bitwise connectors {and, or, left shift,
  right shift, xor}, one row only:
      (integer, integer) -> integer
  so bitwise combinations of two integer-family operands resolve to integer,
  while every other bitwise operand pair resolves to the unresolved sentinel.

  DATE/TIME under addition:
      (date, duration) -> date-time      (duration, date) -> date-time
      (duration, duration) -> duration
      (time, duration) -> time           (duration, time) -> time

  DATE/TIME under subtraction:
      (date, duration) -> date-time      (date, date) -> duration
      (duration, duration) -> duration
      (time, duration) -> time           (time, time) -> duration

  Any connector outside those families has no recorded row, so every query
  under it resolves to the unresolved sentinel. The resolved result is always
  one of the RECORDED result types (or the sentinel) — never the queried
  operand's own type when that type merely lies below a recorded one.

Field types and connectors are modelled as small integer codes. The family of
types below the integer type is modelled as an OPEN, unbounded band of codes,
because the real hierarchy admits arbitrarily many such types and each of them
must resolve exactly as the integer type does; likewise a band of codes models
the types that lie below no recorded operand type. The per-connector row set is
modelled deeply as a straight-line cascade of the same subtype-matched row
tests, in registration order, returning the recorded result type of the first
matching row. The subtype relation is a pure relation. No callee is
axiomatized; resolution is pure registry/lookup logic spelled out in full. The
"unresolved" outcome is the sentinel ``0``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# Field-type codes (the carrier for the field classes the registry mentions).
T_NONE = 0   # the "unresolved" sentinel result; NOT an operand type
T_NULL = 1   # the null-literal type (an operand with no field type of its own)
T_DEC = 2    # decimal field type
T_FLT = 3    # float field type
T_DUR = 4    # duration field type
T_TIME = 5   # time field type
T_DATE = 6   # date field type
T_DTM = 7    # date-time field type: a type BELOW the date field type
T_INT = 8    # integer field type
# Codes at or above T_INT_SUB form the OPEN, unbounded family of field types
# that lie strictly BELOW the integer field type (wide/narrow/non-negative/
# auto-increment integers and any further integer-derived type). Each of them
# matches a recorded integer operand exactly as the integer type does. The band
# is open: it is not a finite list of special cases.
T_INT_SUB = 9
T_AUTO = 9   # the auto-increment integer type: one member of that open family
# Codes at or below T_UNREL_TOP form the OPEN, unbounded family of field types
# that lie below NO recorded operand type (character, boolean, uuid, binary,
# ... field types), so they match no recorded row.
T_UNREL_TOP = -1

# Connector codes (the carrier for the connectors the registry is keyed by).
C_ADD = 1
C_SUB = 2
C_MUL = 3
C_DIV = 4
C_MOD = 5    # the remainder connector
C_POW = 6    # the exponentiation connector
C_BITAND = 7
C_BITOR = 8
C_BITLSHIFT = 9
C_BITRSHIFT = 10
C_BITXOR = 11
# Every other connector code denotes a connector with NO recorded rows.


# axioms-start
# No consumed axioms: type resolution is pure registry/lookup logic, modelled
# deeply (the per-connector rows and the subtype relation are spelled out).
# The real registry-construction helper and the real subtype primitive
# (issubclass) are validated against this deep model out-of-band by
# axiom_check.py (G-AX) as A-references, not consumed here.
# axioms-end


# pure-start
@Pure
def is_int_kind(t: int) -> bool:
    """True iff field type ``t`` is the integer field type or ANY field type
    below it. The family below the integer type is open-ended, so this is a
    band test, not a finite enumeration of known integer variants."""
    return t == T_INT or t >= T_INT_SUB


@Pure
def is_date_kind(t: int) -> bool:
    """True iff field type ``t`` is the date field type or any field type below
    it; the date-time field type lies below the date field type."""
    return t == T_DATE or t == T_DTM


@Pure
def is_operand_type(t: int) -> bool:
    """The operand types a query may carry: every field type code. Only the
    "unresolved" sentinel is not an operand type."""
    return t != T_NONE


@Pure
def is_result_type(t: int) -> bool:
    """The values resolution may yield: the "unresolved" sentinel, or one of
    the RECORDED result types. A queried type that merely lies below a recorded
    operand type is never itself yielded as the result."""
    return (t == T_NONE or t == T_INT or t == T_DEC or t == T_FLT
            or t == T_DUR or t == T_TIME or t == T_DTM)


@Pure
def is_subtype(a: int, b: int) -> bool:
    """True iff field type ``a`` is the same as, or lies below, field type
    ``b``. Below the integer field type lies the whole open integer family;
    below the date field type lies the date-time field type; the remaining
    recorded operand types have nothing below them in this carrier."""
    if b == T_INT:
        return is_int_kind(a)
    if b == T_DATE:
        return is_date_kind(a)
    return a == b


@Pure
def row(clhs: int, crhs: int, lhs: int, rhs: int) -> bool:
    """A recorded row ``(clhs, crhs, _)`` matches a query ``(lhs, rhs)`` iff
    each queried operand type is that row's corresponding recorded type or lies
    below it."""
    return is_subtype(lhs, clhs) and is_subtype(rhs, crhs)


@Pure
def records_same_type_numeric(connector: int) -> bool:
    """The connectors for which the same-type numeric rows (and the
    float/null-literal rows) are recorded: the five arithmetic connectors and
    exponentiation."""
    return (connector == C_ADD or connector == C_SUB or connector == C_MUL
            or connector == C_DIV or connector == C_MOD
            or connector == C_POW)


@Pure
def records_mixed_numeric(connector: int) -> bool:
    """The connectors for which the MIXED-type numeric rows are recorded: every
    arithmetic connector — addition, subtraction, multiplication, division and
    the remainder connector, the last on the same footing as the others.
    Exponentiation records no mixed-type numeric row."""
    return (connector == C_ADD or connector == C_SUB or connector == C_MUL
            or connector == C_DIV or connector == C_MOD)


@Pure
def records_bitwise_integer(connector: int) -> bool:
    """The bitwise connectors, each of which records a single integer/integer
    row and nothing else: and, or, left shift, right shift, xor."""
    return (connector == C_BITAND or connector == C_BITOR
            or connector == C_BITLSHIFT or connector == C_BITRSHIFT
            or connector == C_BITXOR)


@Pure
def has_permitted_combination(connector: int, lhs: int, rhs: int) -> bool:
    """True iff SOME row recorded for ``connector`` matches the query — i.e.
    iff the registry permits this combination at all. When it does not,
    resolution yields the "unresolved" sentinel."""
    return (
        ((records_same_type_numeric(connector)
          or records_bitwise_integer(connector))
         and row(T_INT, T_INT, lhs, rhs))
        or (records_same_type_numeric(connector)
            and row(T_FLT, T_FLT, lhs, rhs))
        or (records_same_type_numeric(connector)
            and row(T_DEC, T_DEC, lhs, rhs))
        or (records_mixed_numeric(connector) and row(T_INT, T_DEC, lhs, rhs))
        or (records_mixed_numeric(connector) and row(T_DEC, T_INT, lhs, rhs))
        or (records_mixed_numeric(connector) and row(T_INT, T_FLT, lhs, rhs))
        or (records_mixed_numeric(connector) and row(T_FLT, T_INT, lhs, rhs))
        or (records_same_type_numeric(connector)
            and row(T_FLT, T_NULL, lhs, rhs))
        or (records_same_type_numeric(connector)
            and row(T_NULL, T_FLT, lhs, rhs))
        or (connector == C_ADD and row(T_DATE, T_DUR, lhs, rhs))
        or (connector == C_ADD and row(T_DUR, T_DATE, lhs, rhs))
        or (connector == C_ADD and row(T_DUR, T_DUR, lhs, rhs))
        or (connector == C_ADD and row(T_TIME, T_DUR, lhs, rhs))
        or (connector == C_ADD and row(T_DUR, T_TIME, lhs, rhs))
        or (connector == C_SUB and row(T_DATE, T_DUR, lhs, rhs))
        or (connector == C_SUB and row(T_DATE, T_DATE, lhs, rhs))
        or (connector == C_SUB and row(T_DUR, T_DUR, lhs, rhs))
        or (connector == C_SUB and row(T_TIME, T_DUR, lhs, rhs))
        or (connector == C_SUB and row(T_TIME, T_TIME, lhs, rhs))
    )
# pure-end


def resolve_combined_type(connector: int, lhs_type: int,
                          rhs_type: int) -> int:
    # pre-conditions-start
    # ANY connector code (registered or not) and any two operand field types.
    Requires(is_operand_type(lhs_type))
    Requires(is_operand_type(rhs_type))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (0) Resolution yields the unresolved sentinel or a RECORDED result type,
    # and it yields a real type exactly when the registry permits the
    # combination.
    Ensures(is_result_type(Result()))
    Ensures(has_permitted_combination(connector, lhs_type, rhs_type)
            == (Result() != T_NONE))
    # (1) Same-type numeric operands resolve to that same numeric type, for
    # every connector that records the same-type numeric rows. The integer
    # clause holds for EVERY pair drawn from the open family below the integer
    # type, and yields the integer type itself — not the queried operand type.
    Ensures(Implies(records_same_type_numeric(connector)
                    and is_int_kind(lhs_type) and is_int_kind(rhs_type),
                    Result() == T_INT))
    Ensures(Implies(records_same_type_numeric(connector)
                    and lhs_type == T_DEC and rhs_type == T_DEC,
                    Result() == T_DEC))
    Ensures(Implies(records_same_type_numeric(connector)
                    and lhs_type == T_FLT and rhs_type == T_FLT,
                    Result() == T_FLT))
    # (2) MIXED numeric operands resolve to the WIDER type, for EVERY
    # arithmetic connector — the remainder connector included, on the same
    # footing as the other four. Holds for every member of the open integer
    # family on the integer side.
    Ensures(Implies(records_mixed_numeric(connector)
                    and is_int_kind(lhs_type) and rhs_type == T_DEC,
                    Result() == T_DEC))
    Ensures(Implies(records_mixed_numeric(connector)
                    and lhs_type == T_DEC and is_int_kind(rhs_type),
                    Result() == T_DEC))
    Ensures(Implies(records_mixed_numeric(connector)
                    and is_int_kind(lhs_type) and rhs_type == T_FLT,
                    Result() == T_FLT))
    Ensures(Implies(records_mixed_numeric(connector)
                    and lhs_type == T_FLT and is_int_kind(rhs_type),
                    Result() == T_FLT))
    # (3) The decimal/float mixes have no recorded row under ANY connector, so
    # they resolve to the unresolved sentinel.
    Ensures(Implies(lhs_type == T_DEC and rhs_type == T_FLT,
                    Result() == T_NONE))
    Ensures(Implies(lhs_type == T_FLT and rhs_type == T_DEC,
                    Result() == T_NONE))
    # (4) Exponentiation records the same-type numeric rows but NO mixed-type
    # numeric row, so a mixed numeric query under it stays unresolved.
    Ensures(Implies(connector == C_POW
                    and ((is_int_kind(lhs_type) and rhs_type == T_DEC)
                         or (lhs_type == T_DEC and is_int_kind(rhs_type))
                         or (is_int_kind(lhs_type) and rhs_type == T_FLT)
                         or (lhs_type == T_FLT and is_int_kind(rhs_type))),
                    Result() == T_NONE))
    # (5) The null-literal type combines only with the float type, and only
    # under the connectors that record the numeric rows.
    Ensures(Implies(records_same_type_numeric(connector)
                    and ((lhs_type == T_FLT and rhs_type == T_NULL)
                         or (lhs_type == T_NULL and rhs_type == T_FLT)),
                    Result() == T_FLT))
    Ensures(Implies((is_int_kind(lhs_type) and rhs_type == T_NULL)
                    or (lhs_type == T_NULL and is_int_kind(rhs_type))
                    or (lhs_type == T_DEC and rhs_type == T_NULL)
                    or (lhs_type == T_NULL and rhs_type == T_DEC)
                    or (lhs_type == T_NULL and rhs_type == T_NULL),
                    Result() == T_NONE))
    # (6) A bitwise connector resolves two integer-family operands to the
    # integer type and leaves every other operand pair unresolved.
    Ensures(Implies(records_bitwise_integer(connector)
                    and is_int_kind(lhs_type) and is_int_kind(rhs_type),
                    Result() == T_INT))
    Ensures(Implies(records_bitwise_integer(connector)
                    and not (is_int_kind(lhs_type) and is_int_kind(rhs_type)),
                    Result() == T_NONE))
    # (7) The date/time rows, and their asymmetry between addition and
    # subtraction: subtraction of two date-family operands yields a duration
    # while addition of two date-family operands is unresolved; addition
    # accepts a duration on either side of a date/time operand while
    # subtraction accepts it only on the right.
    Ensures(Implies(connector == C_ADD
                    and ((is_date_kind(lhs_type) and rhs_type == T_DUR)
                         or (lhs_type == T_DUR and is_date_kind(rhs_type))),
                    Result() == T_DTM))
    Ensures(Implies(connector == C_SUB and is_date_kind(lhs_type)
                    and rhs_type == T_DUR,
                    Result() == T_DTM))
    Ensures(Implies(connector == C_SUB and is_date_kind(lhs_type)
                    and is_date_kind(rhs_type),
                    Result() == T_DUR))
    Ensures(Implies(connector == C_ADD and is_date_kind(lhs_type)
                    and is_date_kind(rhs_type),
                    Result() == T_NONE))
    Ensures(Implies((connector == C_ADD or connector == C_SUB)
                    and lhs_type == T_DUR and rhs_type == T_DUR,
                    Result() == T_DUR))
    Ensures(Implies(connector == C_ADD
                    and ((lhs_type == T_TIME and rhs_type == T_DUR)
                         or (lhs_type == T_DUR and rhs_type == T_TIME)),
                    Result() == T_TIME))
    Ensures(Implies(connector == C_SUB and lhs_type == T_TIME
                    and rhs_type == T_DUR,
                    Result() == T_TIME))
    Ensures(Implies(connector == C_SUB and lhs_type == T_TIME
                    and rhs_type == T_TIME,
                    Result() == T_DUR))
    Ensures(Implies(connector == C_SUB and lhs_type == T_DUR
                    and is_date_kind(rhs_type),
                    Result() == T_NONE))
    # (8) The date/time rows are recorded for addition and subtraction only;
    # under every other connector a date-family, duration or time operand is
    # unresolved.
    Ensures(Implies(connector != C_ADD and connector != C_SUB
                    and (is_date_kind(lhs_type) or lhs_type == T_DUR
                         or lhs_type == T_TIME or is_date_kind(rhs_type)
                         or rhs_type == T_DUR or rhs_type == T_TIME),
                    Result() == T_NONE))
    # (9) An operand type that lies below no recorded operand type matches no
    # row, and a connector with no recorded rows resolves nothing.
    Ensures(Implies(lhs_type <= T_UNREL_TOP or rhs_type <= T_UNREL_TOP,
                    Result() == T_NONE))
    Ensures(Implies(not records_same_type_numeric(connector)
                    and not records_bitwise_integer(connector),
                    Result() == T_NONE))
    # post-conditions-end
    # impl-start
    # Scan the rows recorded for this connector in registration order and
    # return the recorded result type of the first matching row, else the
    # unresolved sentinel. The rows are, per family:
    #   numeric same-type (five arithmetic connectors + exponentiation):
    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
    #   numeric mixed-type (every arithmetic connector, remainder included on
    #   the same footing; NOT exponentiation):
    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
    #   numeric with the null-literal type (same connectors as same-type):
    #       (flt,null)->flt  (null,flt)->flt
    #   bitwise (five bitwise connectors): (int,int)->int
    #   date/time under addition and under subtraction, as recorded.
    if records_same_type_numeric(connector):
        if row(T_INT, T_INT, lhs_type, rhs_type):
            return T_INT
        if row(T_FLT, T_FLT, lhs_type, rhs_type):
            return T_FLT
        if row(T_DEC, T_DEC, lhs_type, rhs_type):
            return T_DEC
    # Pre-patch registry construction: the mixed-type numeric rows are recorded
    # only for the addition/subtraction/multiplication/division connectors, NOT
    # for the remainder connector.
    if records_mixed_numeric(connector) and connector != C_MOD:
        if row(T_INT, T_DEC, lhs_type, rhs_type):
            return T_DEC
        if row(T_DEC, T_INT, lhs_type, rhs_type):
            return T_DEC
        if row(T_INT, T_FLT, lhs_type, rhs_type):
            return T_FLT
        if row(T_FLT, T_INT, lhs_type, rhs_type):
            return T_FLT
    if records_same_type_numeric(connector):
        if row(T_FLT, T_NULL, lhs_type, rhs_type):
            return T_FLT
        if row(T_NULL, T_FLT, lhs_type, rhs_type):
            return T_FLT
    if records_bitwise_integer(connector):
        if row(T_INT, T_INT, lhs_type, rhs_type):
            return T_INT
    if connector == C_ADD:
        if row(T_DATE, T_DUR, lhs_type, rhs_type):
            return T_DTM
        if row(T_DUR, T_DATE, lhs_type, rhs_type):
            return T_DTM
        if row(T_DUR, T_DUR, lhs_type, rhs_type):
            return T_DUR
        if row(T_TIME, T_DUR, lhs_type, rhs_type):
            return T_TIME
        if row(T_DUR, T_TIME, lhs_type, rhs_type):
            return T_TIME
    if connector == C_SUB:
        if row(T_DATE, T_DUR, lhs_type, rhs_type):
            return T_DTM
        if row(T_DATE, T_DATE, lhs_type, rhs_type):
            return T_DUR
        if row(T_DUR, T_DUR, lhs_type, rhs_type):
            return T_DUR
        if row(T_TIME, T_DUR, lhs_type, rhs_type):
            return T_TIME
        if row(T_TIME, T_TIME, lhs_type, rhs_type):
            return T_DUR
    return T_NONE
    # impl-end
