"""Twin-artifact model for sympy__sympy-13372.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric evaluator splits an expression into its real and imaginary parts
  and assembles a result that pairs each part with a PRECISION component
  describing how that part was evaluated. Each part independently falls into
  exactly one of three cases:

    * EXACT-ZERO  — the part is the exact zero. Its precision component is
      ABSENT (there is no working precision attached to an exact zero).

    * NUMERIC     — the part is a concrete number. Its precision component is
      the supplied working precision.

    * OTHER       — the part is neither an exact zero nor a concrete number
      (it is still symbolic). There is NO precision component defined for such
      a part.

  The behaviour pinned here: a result is assembled — pairing each part with a
  precision component — ONLY when BOTH parts are exact-zero or numeric, in
  which case each precision component is ABSENT for an exact-zero part and the
  working precision for a numeric part. If EITHER part is the OTHER case, no
  result can be assembled (there is no precision component for that part); the
  evaluation must DEFER instead of assembling a result with a missing precision
  component. Deferral lets the caller fall back to an alternative evaluation;
  assembling a result around a missing precision component is never permitted.

Each part's case is modelled as an integer tag (0 = exact-zero, 1 = numeric,
2 = other). The assembled result is a minimal object carrying only the two
touched precision components, each an `Optional[int]` (absent = None). The
deferral is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class EvalfDeferred(Exception):
    """Signals that a result cannot be assembled because some part is neither
    an exact zero nor a concrete number, so no precision component is defined
    for it. Stands in for the `NotImplementedError` the desired behaviour
    raises to defer to an alternative evaluation; a builtin exception in an
    `Exsures` crashes the Nagini translator (mapping.md §2)."""


class EvalfResult:
    """The assembled result: the two touched precision components. Each is the
    working precision for a numeric part, or absent (None) for an exact-zero
    part. A result is assembled only when both precision components are
    defined."""

    def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
        # Terminates outright (two field writes, no loop, no call). Level 1 sits
        # strictly below every caller level so the caller can hand its
        # obligation down without leaking it.
        Requires(MustTerminate(1))
        Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
        Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
        self.reprec = reprec
        self.imprec = imprec


# axioms-start
# (no axioms: the precision-component selection per part is concrete integer
# control flow, modelled directly — no unchanged opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def part_precision(kind: int, prec: int) -> Optional[int]:
    """The precision component for one part: absent (None) for an exact-zero
    part (kind 0), the working precision for a numeric part (kind 1). Defined
    only for the two cases that yield a precision component; the OTHER case
    (kind 2) has no precision component and is excluded by the precondition."""
    Requires(kind == 0 or kind == 1)
    if kind == 0:
        return None
    return prec
# pure-end


def assemble_evalf_result(re_kind: int, im_kind: int, prec: int) -> EvalfResult:
    # pre-conditions-start
    # Each part is classified into exactly one of the three cases.
    Requires(0 <= re_kind and re_kind <= 2)
    Requires(0 <= im_kind and im_kind <= 2)
    Requires(MustTerminate(6 - re_kind))
    # pre-conditions-end
    # post-conditions-start
    # A result is assembled (returns normally) only when BOTH parts are
    # exact-zero or numeric — never when either part is the OTHER case.
    Ensures(re_kind != 2 and im_kind != 2)
    Ensures(Acc(Result().reprec) and Acc(Result().imprec))
    # Each assembled precision component is exactly the one its part's case
    # demands: absent for exact-zero, the working precision for numeric.
    Ensures(Result().reprec is part_precision(re_kind, prec))
    Ensures(Result().imprec is part_precision(im_kind, prec))
    # The evaluation DEFERS exactly when some part is the OTHER case: no result
    # can be assembled because a precision component would be missing.
    Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the precision component is set only in the exact-zero
    # and numeric cases; the OTHER case has NO branch, so the precision local
    # keeps the placeholder it was given before the classification — there is
    # no precision component for an OTHER part. The evaluation then assembles a
    # result around that missing component instead of deferring. Nagini reports
    # the postcondition `Result().reprec is part_precision(re_kind, prec)` (and
    # the `re_kind != 2` guard) unprovable on an OTHER part — the formal face of
    # reading the unset precision component (the `reprec`/`imprec` referenced
    # before assignment).
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    return EvalfResult(reprec, imprec)
    # impl-end
