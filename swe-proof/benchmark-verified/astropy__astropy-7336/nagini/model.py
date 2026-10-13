"""Twin-artifact model for astropy__astropy-7336.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A units-checking wrapper, after calling the wrapped function and obtaining its
  return value, decides how to finalise that value according to the wrapped
  function's declared return target:

    * If the wrapped function declares NO return target (the "unspecified"
      sentinel), the wrapper yields the return value untouched.
    * If the wrapped function declares its return target to be the "no value"
      target (i.e. it is annotated as producing nothing), the wrapper ALSO
      yields the return value untouched. In particular it must NOT attempt the
      unit conversion in this case — the returned object may be the no-value
      object, which carries no unit and cannot be converted.
    * Only when the wrapped function declares a genuine unit target does the
      wrapper convert the return value into that target unit; the finalised
      value is then a quantity expressed in that target unit.

  The discriminating behaviour: the "no value" target is treated exactly like
  the "unspecified" sentinel (pass through), NOT like a genuine unit target.

The return value is modelled as a small object carrying whether it is the
no-value object and, when it is a quantity, its current unit id (an int). The
declared return target is an int code: a distinguished "unspecified" sentinel,
a distinguished "no value" sentinel, and any other value denoting a genuine
unit. The conversion of a quantity into a target unit is modelled deeply as a
pure operation that is only defined on a genuine quantity (never on the
no-value object) — exactly the operation whose misuse the desired behaviour
must avoid. No library callee is consumed inside a postcondition (the axioms
region is empty; see mapping.md §3); the decision is validated against the real
wrapper by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class RetVal:
    """The value returned by the wrapped function, then finalised by the
    wrapper. `is_none` marks the no-value object (which carries no unit and
    cannot be converted); `unit` is the current unit id when it is a quantity."""

    def __init__(self, is_none: bool, unit: int) -> None:
        Requires(Implies(is_none, unit == NO_UNIT()))
        # Terminates: two field assignments, no loop and no call. Level 1 leaves
        # room strictly below finalize_return's level 6, which constructs RetVal.
        Requires(MustTerminate(1))
        Ensures(Acc(self.is_none) and Acc(self.unit))
        Ensures(self.is_none == is_none and self.unit == unit)
        self.is_none = is_none  # type: bool
        self.unit = unit  # type: int


# axioms-start
# (none — the modelled delta is a pure decision over the declared return target
# plus a deep model of the unit conversion; no opaque library callee is consumed
# inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def TARGET_UNSPECIFIED() -> int:
    # the "no return target was declared" sentinel
    return -1


@Pure
def TARGET_NOVALUE() -> int:
    # the "declared to produce nothing" target
    return -2


@Pure
def NO_UNIT() -> int:
    # the unit id carried by the no-value object (it has none)
    return -3


@Pure
def is_genuine_target(target: int) -> bool:
    """A declared return target is a genuine unit target exactly when it is
    neither the unspecified sentinel nor the no-value target."""
    return target != TARGET_UNSPECIFIED() and target != TARGET_NOVALUE()
# pure-end


@Pure
def convert_unit(q_unit: int, target: int) -> int:
    Requires(is_genuine_target(target))
    # The unit id of a quantity after converting it into `target`: the target
    # unit. (`q_unit` is the source unit; conversion re-expresses the same
    # physical value in `target`.) Only ever applied to a genuine quantity and a
    # genuine unit target — never to the no-value object.
    Ensures(Result() == target)
    return target


def finalize_return(ret: RetVal, target: int) -> RetVal:
    # pre-conditions-start
    Requires(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
    # Domain fact (real semantics, mapping.md §4): the no-value object carries
    # no unit; a genuine quantity carries a genuine unit id (not the no-value
    # placeholder). A genuine unit target is never one of the two sentinels.
    Requires(ret.is_none == (ret.unit == NO_UNIT()))
    # Total, not merely partial, correctness: the postconditions below are
    # claimed of every call, not only of runs that happen to reach the return.
    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
    # so level 6 leaves ample room strictly beneath it.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().unit))
    # When no genuine unit target is declared (unspecified sentinel OR the
    # no-value target), the value passes through untouched: same object kind,
    # same unit. In particular the no-value object is returned as-is and is
    # NOT subjected to a conversion.
    Ensures(Implies(not is_genuine_target(target),
                    Result().is_none == ret.is_none
                    and Result().unit == ret.unit))
    # When a genuine unit target is declared, the value is converted into that
    # target: the finalised value is a quantity (not the no-value object) whose
    # unit is the declared target unit.
    Ensures(Implies(is_genuine_target(target),
                    (not Result().is_none)
                    and Result().unit == convert_unit(ret.unit, target)))
    # post-conditions-end
    # impl-start
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)
    # impl-end
