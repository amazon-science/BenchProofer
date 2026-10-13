"""Twin-artifact model for django__django-14349.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual value is screened before it is accepted as a well-formed locator.
  Three control code points are categorically forbidden anywhere in the value:
  the horizontal tab (U+0009), the line feed (U+000A) and the carriage return
  (U+000D). Their presence must be reported as a rejection, and that rejection
  must take precedence over — and be independent of — the remaining structural
  validation of the value.

  The behaviour pinned here is therefore:

    * If the value contains ANY of the three forbidden control code points
      (anywhere, not only at the ends), the screen REJECTS the value
      (signals a validation failure), regardless of whether the rest of the
      value is otherwise well-formed. This must hold even for a value that the
      remaining structural validation would, on its own, have accepted.

    * If the value contains NONE of the three forbidden code points, the screen
      defers entirely to the remaining structural validation: it returns
      normally exactly when that validation accepts, and reports a rejection
      exactly when that validation rejects. The forbidden-character screen
      neither rescues nor rejects an otherwise-decided value in this case.

  Screening is a bounded scan of the value followed by the downstream verdict:
  the operation MUST actually deliver its answer — return normally or signal
  the rejection (a total-correctness obligation, carried as MustTerminate in
  the precondition). An implementation that diverges before answering would
  satisfy the value postconditions only vacuously and would never validate
  anything.

The value is modelled as a ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); membership of a forbidden code point is stated as an
existential over the code-point list.
The remaining structural validation is an unchanged callee whose only observable
datum is whether it accepts the value (``accepted``); it is axiomatized as a
contract-only function that returns normally iff it accepts and signals a
rejection otherwise. The rejection is a user-defined exception class (a builtin
exception in an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class InvalidValue(Exception):
    """The rejection the screen signals when the value is not accepted. A
    user-defined stand-in for the validation error the desired behaviour
    requires (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
@ContractOnly
def downstream_validate(accepted: bool) -> None:
    """The unchanged remaining structural validation of the value, the callee
    the screen defers to once the forbidden-character check has passed. Its
    only observable datum is ``accepted``: whether this validation accepts the
    value. It returns normally exactly when the value is accepted and signals a
    rejection (the same out-of-band rejection) exactly when it is not.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real downstream chain (scheme split, regex, IDN retry, IPv6 recheck)
    # is a bounded computation that always delivers its verdict — it returns
    # or raises, never diverges (exercised on every axiom_check.py input). It
    # therefore takes and discharges a termination obligation, so a caller
    # holding one may defer to it.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on the accepted case.
    Ensures(accepted is True)
    # Rejection is signalled out of band EXACTLY on the not-accepted case.
    Exsures(InvalidValue, accepted is False)
    # post-conditions-end
# axioms-end


# pure-start
@Pure
def is_forbidden(c: int) -> bool:
    """A single code point is forbidden iff it is the horizontal tab (9), the
    line feed (10) or the carriage return (13)."""
    return c == 9 or c == 10 or c == 13
# pure-end


def validate_url(value: List[int], accepted: bool) -> None:
    # pre-conditions-start
    # ``value`` is only READ (fractional permission, directive 5). ``accepted``
    # is the abstract world-state datum consumed by the remaining structural
    # validation: whether that validation accepts the value.
    Requires(Acc(list_pred(value), 1 / 2))
    # TERMINATION: the screen is a bounded scan of the value followed by the
    # downstream verdict; it must actually ANSWER (return or raise). Nagini is
    # a partial-correctness verifier by default, so without this obligation a
    # diverging implementation (e.g. `while True: pass` inserted after the
    # screen) satisfies every Ensures/Exsures vacuously; the real validator
    # always delivers its verdict.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The value is read-only: returned untouched at the same fractional
    # permission (so the screen cannot have mutated it, directive 5).
    Ensures(Acc(list_pred(value), 1 / 2))
    # Normal completion is reachable EXACTLY when the value has no forbidden
    # control code point AND the remaining structural validation accepts it.
    # The forbidden-character screen alone forces a rejection: a value carrying
    # a forbidden code point can NEVER return normally, even if it would
    # otherwise have been accepted.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
                                           not is_forbidden(value[k])))))
    Ensures(accepted is True)
    # Rejection is signalled EXACTLY when the value carries a forbidden code
    # point OR the remaining structural validation rejects it — the forbidden
    # screen taking precedence (its branch is independent of ``accepted``). The
    # read-only value is re-established on the rejecting path as well.
    Exsures(InvalidValue,
            Acc(list_pred(value), 1 / 2)
            and (Exists(int, lambda k: (0 <= k and k < len(value)
                                        and is_forbidden(value[k])))
                 or accepted is False))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the value is handed straight to the remaining
    # structural validation with NO forbidden-character screen. A value that
    # carries a forbidden control code point but is otherwise accepted by the
    # remaining validation therefore returns normally instead of being
    # rejected — exactly the behaviour the fix forbids.
    downstream_validate(accepted)
    # impl-end
