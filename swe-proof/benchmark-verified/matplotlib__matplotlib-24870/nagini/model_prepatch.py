"""Twin-artifact model for matplotlib__matplotlib-24870.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A contour routine must choose a default set of contour levels when the caller
  supplies neither an explicit level list nor an explicit level count. The data
  field being contoured has a known minimum and maximum value (`zmin`, `zmax`,
  with `zmin < zmax`) and is one of two kinds:

    * a two-valued field, whose every sample is one of exactly two distinct
      values (the lower value `zmin` and the upper value `zmax`); or
    * an ordinary continuous field.

  For an ordinary continuous field the default is the long-standing automatic
  selection that spreads several (more than one) interior levels across the data
  range. That choice is useless for a two-valued field: the only meaningful
  place to draw a boundary between the two regions is a single level strictly
  between the two values. So for a two-valued field the default levels MUST be:

    * for a line contour:  a single level, the midpoint of the two values (the
      value equidistant from both), which therefore lies strictly between them
      (so it survives the line-contour rule that drops any level not strictly
      inside the open data range);
    * for a filled contour: the three levels  [zmin, midpoint, zmax]  — the two
      extreme values bracketing the midpoint — which is a valid filled
      specification (a filled contour requires at least two levels).

  The choice depends only on (a) whether explicit levels were requested, (b)
  whether the field is two-valued, and (c) whether the contour is filled; it
  must NOT collapse the two-valued field onto the ordinary multi-level default.

The data extents and the chosen levels are interpreted real numbers (verified
with `--float-encoding=real`) because the behaviour at stake — a single level
lying strictly between the two values, equidistant from each — is a real-valued
relation the tests probe to floating tolerance. The midpoint enters pinned by
its linear defining equation (it is equidistant from the two values), which both
grounds it in the data extents and stays inside the verifier's linear real
fragment. The ordinary multi-level automatic selection (the unchanged path for
continuous fields) is the operation this routine delegates to; it is axiomatized
with the weakest sufficient contract (it yields more than one level) and
validated against the real selection out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def auto_levels(zmin: float, zmax: float) -> PSeq[float]:
    """The ordinary automatic level selection for a continuous field (the
    unchanged delegate). Across a well-resolved data range it produces more
    than one level — so a two-valued field, where a single boundary level is
    wanted, needs its own default rather than this multi-level spread. The
    weakest contract the proof needs (more than one level).

    The "more than one level" guarantee holds only when the data range is
    well-resolved: the span must clear an absolute floor AND a small fraction
    of each extent's magnitude. At an unresolvable range — a span at or below
    the floating-point spacing near the extents, or extents at the underflow
    floor — the automatic selection degenerates to a single tick, so the
    obligation is scoped (via Requires) to the resolved regime, which is the
    only regime the operation under specification is ever applied to (the
    tested two-valued range [0, 1] clears it with enormous margin). Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(zmin < zmax)
    # Well-resolved range: span clears an absolute floor and a small fraction of
    # each extent's magnitude. (Outside this the real selection can collapse to
    # a single tick; the proof never needs the multi-level fact there.)
    Requires(zmax - zmin >= 1e-6)
    Requires(zmax - zmin >= 1e-9 * zmax)
    Requires(zmax - zmin >= 1e-9 * (0.0 - zmin))
    Ensures(len(Result()) > 1)
# axioms-end


# pure-start
# (no pure helpers — the midpoint is pinned by its linear defining equation in
# the precondition, see `mid` below.)
# pure-end


def choose_default_levels(has_explicit: bool, two_valued: bool, filled: bool,
                          zmin: float, zmax: float, mid: float) -> List[float]:
    # pre-conditions-start
    # The branch under specification is the no-explicit-levels default; the data
    # range is non-degenerate (the two values differ).
    Requires(not has_explicit)
    Requires(zmin < zmax)
    # Well-resolved data range: the span clears an absolute floor and a small
    # fraction of each extent's magnitude. This excludes only an unresolvable
    # range (a span at or below the floating-point spacing near the extents, or
    # extents at the underflow floor), where the ordinary automatic selection
    # would degenerate to a single tick. Every meaningful contour range — in
    # particular the tested two-valued range [0, 1] — clears it with margin.
    Requires(zmax - zmin >= 1e-6)
    Requires(zmax - zmin >= 1e-9 * zmax)
    Requires(zmax - zmin >= 1e-9 * (0.0 - zmin))
    # `mid` is the midpoint of the two values: the value equidistant from each
    # (its distance below the upper value equals its distance above the lower
    # value). This linear defining equation grounds `mid` in the data extents.
    Requires(mid - zmin == zmax - mid)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A two-valued field gets the boundary-level default, NOT the ordinary
    # multi-level automatic selection.
    # Line contour over a two-valued field: exactly one level, the midpoint of
    # the two values, lying strictly between them.
    Ensures(Implies(two_valued and not filled, len(Result()) == 1))
    Ensures(Implies(two_valued and not filled, Result()[0] == mid))
    Ensures(Implies(two_valued and not filled,
                    zmin < Result()[0] and Result()[0] < zmax))
    # Filled contour over a two-valued field: the three levels
    # [zmin, midpoint, zmax] — at least two levels, the extremes bracketing the
    # strictly-interior midpoint.
    Ensures(Implies(two_valued and filled, len(Result()) == 3))
    Ensures(Implies(two_valued and filled, len(Result()) >= 2))
    Ensures(Implies(two_valued and filled,
                    Result()[0] == zmin and Result()[2] == zmax))
    Ensures(Implies(two_valued and filled, Result()[1] == mid))
    Ensures(Implies(two_valued and filled,
                    Result()[0] < Result()[1] and Result()[1] < Result()[2]))
    # An ordinary continuous field keeps the unchanged multi-level default
    # (more than one level), so the two regimes are not conflated.
    Ensures(Implies(not two_valued, len(Result()) > 1))
    Ensures(Implies(not two_valued, ToSeq(Result()) == auto_levels(zmin, zmax)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: with no explicit levels requested the default
    # is ALWAYS the ordinary multi-level automatic selection, regardless of
    # whether the field is two-valued — the two-valued case is never special
    # cased. This fails the two-valued postconditions (a single midpoint level
    # for a line contour; the three bracketing levels for a filled contour).
    result = []  # type: List[float]
    result = list(auto_levels(zmin, zmax))
    return result
    # impl-end
