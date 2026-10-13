"""Twin-artifact model for astropy__astropy-7606.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Equality of a unit value against an arbitrary operand. The operation first
  tries to coerce the operand into a unit using the silent-parse path of the
  unit factory; that coercion is a PARTIAL operation — it succeeds for some
  operands (strings, existing units, numbers) and is undefined for others (for
  example the ``None`` object, or any object that simply cannot denote a unit).

  The desired behaviour is that the comparison is TOTAL: it must produce an
  answer for EVERY operand and must never propagate a failure to the caller.
  When the operand cannot be coerced into a unit, the comparison declines to
  decide and yields the "not-applicable" sentinel (the value that asks Python
  to let the other operand try, which for ``==`` collapses to "not equal" and
  for membership/``!=`` to the expected result) — it does NOT yield a definite
  decision and it does NOT fail. When the operand CAN be coerced, the
  comparison decides definitely: it is equal exactly when the coerced operand
  is a unit of the same kind carrying the same name (for the unparsed-name
  unit) or, more generally, when the two units are dimensionally the same unit.

  The single behaviour pinned here for the unparsed-name unit is that
  comparison against a non-coercible operand (e.g. ``None``) must yield the
  not-applicable sentinel rather than failing, while comparison against a
  coercible operand still decides equality by same-kind-and-name; and the
  general unit comparison likewise yields the not-applicable sentinel — not a
  definite "not equal" — for an operand that cannot be coerced into a unit.

The three-valued outcome of a comparison (definitely-equal, definitely-not-
equal, or not-applicable/defer) is modelled by a small integer tag. The
partial coercion is characterised by its OBSERVABLE predicates on the operand
(whether the silent parse succeeds, and, when it does, the same-kind / equal-
name / convertibility predicates of the coerced unit) — exactly the predicates
the comparison reads — so the discriminating observable is purely WHICH outcome
the comparison produces, never that it fails.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized library callee: the comparison reads only the observable
#  predicates of the operand's silent unit-coercion — whether that partial
#  coercion succeeds, and, when it does, the same-kind / equal-name /
#  convertibility predicates of the resulting unit. These are modelled
#  abstractly as the input predicates, exactly as the comparison reads them;
#  the coercion factory and the dimensional-comparison helper are unchanged and
#  appear only as the operand predicates, not as consumed axioms. Their fidelity
#  to the real callees is validated out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# The three-valued comparison outcome (a single integer tag):
#   RES_FALSE   — the comparison decided the operands are NOT equal;
#   RES_TRUE    — the comparison decided the operands ARE equal;
#   RES_NOTIMPL — the comparison declined to decide (the not-applicable
#                 sentinel asking Python to let the other operand try). This is
#                 the outcome required for an operand the coercion cannot handle.
RES_FALSE = 0
RES_TRUE = 1
RES_NOTIMPL = 2
# pure-end


def eq_unparsed_name(parse_succeeds: bool, parsed_same_kind: bool,
                     names_equal: bool) -> int:
    # pre-conditions-start
    # The operand is characterised by the observable predicates the comparison
    # reads off it (plain booleans, no heap permission):
    #   parse_succeeds    — the silent unit-coercion of the operand returns
    #                       normally (False for an operand it cannot denote,
    #                       e.g. None);
    #   parsed_same_kind  — when the coercion succeeds, the coerced operand is a
    #                       unit of the same (unparsed-name) kind as self;
    #   names_equal       — when the coercion succeeds and yields a same-kind
    #                       unit, that unit carries the same name as self.
    # TERMINATION: this comparison must RETURN for every operand — the
    # postconditions below are claimed of a run that reaches the return, so
    # without this the spec would be satisfied vacuously by a run that never
    # does. Level 7 (not 2) because the obligation level must strictly exceed
    # that of any obligated callee, and a call to eq_unit (level 6) on this
    # method's own argument shape must remain admissible.
    Requires(MustTerminate(7))
    # pre-conditions-end
    # post-conditions-start
    # TOTAL: a definite answer is produced for EVERY operand; the result is
    # always one of the three tags and the comparison never fails.
    Ensures(Result() == RES_FALSE or Result() == RES_TRUE
            or Result() == RES_NOTIMPL)
    # NON-COERCIBLE operand -> the not-applicable sentinel, NEVER a failure and
    # NEVER a definite decision. (The discriminating clause: an operand the
    # coercion cannot handle, such as None, defers instead of raising.)
    Ensures(Implies(not parse_succeeds, Result() == RES_NOTIMPL))
    # COERCIBLE operand -> a DEFINITE decision: equal exactly when the coerced
    # operand is a same-kind unit carrying the same name; not equal otherwise.
    Ensures(Implies(parse_succeeds and parsed_same_kind and names_equal,
                    Result() == RES_TRUE))
    Ensures(Implies(parse_succeeds and not (parsed_same_kind and names_equal),
                    Result() == RES_FALSE))
    # A definite decision is reached ONLY for a coercible operand; conversely a
    # non-coercible operand never yields a definite decision.
    Ensures((Result() == RES_TRUE or Result() == RES_FALSE) == parse_succeeds)
    # post-conditions-end
    # impl-start
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than fail.
        return RES_NOTIMPL
    if parsed_same_kind and names_equal:
        return RES_TRUE
    return RES_FALSE
    # impl-end


def eq_unit(is_same: bool, parse_succeeds: bool, parsed_is_unit: bool,
            convertible: bool, effectively_unity: bool) -> int:
    # pre-conditions-start
    # The general unit comparison reads these observable predicates:
    #   is_same           — the operand is the very same unit object as self;
    #   parse_succeeds    — the silent unit-coercion of the operand returns
    #                       normally (False for a non-coercible operand, e.g.
    #                       None);
    #   parsed_is_unit    — when coercion succeeds, the coerced operand is a
    #                       genuine unit value (vs. some other unit-like object);
    #   convertible       — when the coerced operand is a unit, it is
    #                       dimensionally convertible to self (no conversion
    #                       failure);
    #   effectively_unity — when convertible, the conversion factor is unity,
    #                       i.e. the two are the same unit.
    Requires(Implies(effectively_unity, convertible))
    # TERMINATION: the comparison must RETURN for every operand, so that the
    # postconditions below are total correctness and not merely partial.
    # Level 6 leaves room beneath for any obligated callee.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # TOTAL: a definite answer for EVERY operand; one of the three tags; never
    # fails.
    Ensures(Result() == RES_FALSE or Result() == RES_TRUE
            or Result() == RES_NOTIMPL)
    # The same object is equal to itself.
    Ensures(Implies(is_same, Result() == RES_TRUE))
    # NON-COERCIBLE operand (and not the same object) -> the not-applicable
    # sentinel; NEVER a definite "not equal" and NEVER a failure. (The
    # discriminating clause: a non-coercible operand such as None defers — it
    # does not collapse to a definite decision.)
    Ensures(Implies(not is_same and not parse_succeeds,
                    Result() == RES_NOTIMPL))
    # A coercible operand that is not a genuine unit value -> defer as well
    # (let the operand try).
    Ensures(Implies(not is_same and parse_succeeds and not parsed_is_unit,
                    Result() == RES_NOTIMPL))
    # A coercible genuine unit -> a DEFINITE decision: equal iff the conversion
    # factor is unity; a conversion failure means not equal.
    Ensures(Implies(not is_same and parse_succeeds and parsed_is_unit
                    and convertible and effectively_unity,
                    Result() == RES_TRUE))
    Ensures(Implies(not is_same and parse_succeeds and parsed_is_unit
                    and not (convertible and effectively_unity),
                    Result() == RES_FALSE))
    # post-conditions-end
    # impl-start
    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than return a definite (and wrong) "not equal".
        return RES_NOTIMPL
    if not parsed_is_unit:
        return RES_NOTIMPL
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE
    # impl-end
