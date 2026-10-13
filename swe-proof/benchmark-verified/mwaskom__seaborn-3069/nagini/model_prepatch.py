"""Twin-artifact model for mwaskom__seaborn-3069.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a figure is finalized, each coordinate axis carries a scale that is
  either categorical (a discrete, unordered scale whose positions are the
  integer slots 0, 1, ..., n-1 of its n categories) or ordinary (continuous).
  An axis whose scale is categorical must be drawn like the established
  categorical axes:

    (1) the visible data range is pinned to exactly half a slot beyond the
        first and last category position, i.e. the closed interval whose lower
        edge sits half a slot below position 0 and whose upper edge sits half a
        slot above the last position n-1 (so for n categories the span is from
        -0.5 to n-0.5), rather than the ordinary automatic-margin range;

    (2) when the axis is the vertical one, that range is reversed (top edge
        first), so the first category appears at the top;

    (3) the grid lines are turned off for such an axis, whatever visibility
        they had before finalization.

  The range tweaks (1)-(2) apply ONLY when the caller has not pinned an
  explicit range for that axis: if the caller supplied an explicit (lo, hi)
  range, that range is used verbatim and the categorical range/inversion is
  NOT applied. The grid tweak (3) applies to every categorical axis,
  explicit range or not. An ordinary (non-categorical) axis is left entirely
  alone by the finalizer: it keeps the ordinary automatic-margin range AND
  whatever grid visibility it already had going into finalization.

The axis range is a pair of interpreted real numbers (verified with
`--float-encoding=real`) because the behaviour at stake — edges sitting exactly
half a slot beyond the extreme category positions, and that pair reversed on the
vertical axis — is a real-valued relation the tests probe to floating tolerance.
The half-slot offset enters as the literal 0.5; the number of category slots `n`
is supplied by the unchanged tick-counting routine the finalizer queries, which
is axiomatized with the weakest sufficient contract (it returns the count of
category positions, at least one) and validated against the real routine
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def slot_count() -> int:
    """The number of category slots on a categorical axis: the count of major
    tick positions the unchanged tick-querying routine reports for the axis.
    A categorical axis always has at least one category, so the count is
    positive. The weakest contract the proof needs (a positive count).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() >= 1)
# axioms-end


# pure-start
# (no pure helpers — the half-slot edges are pinned by their linear defining
# equations in the postcondition.)
# pure-end


def finalize_axis_range(is_categorical: bool, has_explicit: bool, is_vertical: bool,
                        user_lo: float, user_hi: float) -> Tuple[float, float]:
    # pre-conditions-start
    # No mutable reference inputs; all parameters are read-only scalars.
    # The caller-supplied edges are genuine numbers (reflexivity excludes NaN).
    Requires(user_lo == user_lo and user_hi == user_hi)
    # An explicit caller range is modeled only when it is non-singular
    # (lo != hi). A singular pair is reshaped by the unchanged, pre-existing
    # range-sanitization machinery of the underlying axis object before it
    # lands as the visible range — behaviour orthogonal to the change under
    # specification, identical before and after it, so it sits outside the
    # modeled slice (mapping.md §2).
    Requires(Implies(has_explicit, user_lo != user_hi))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A categorical axis WITHOUT an explicit caller range gets the categorical
    # range: edges exactly half a slot beyond the extreme category positions.
    # n = slot_count() >= 1; positions run 0 .. n-1; the lower edge sits half a
    # slot below position 0 (i.e. -0.5) and the upper edge half a slot above
    # position n-1 (i.e. n-1 + 0.5 == n - 0.5). On the horizontal axis the pair
    # is (low, high); on the vertical axis it is reversed (high first).
    #
    # Pin the two edges by their linear defining equations grounded in the slot
    # count, then pin orientation, so the result must be PRODUCED by the
    # categorical branch, not merely equal to a constant.
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[0] + 0.5 == 0.0))
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[1] + 0.5 == slot_count()))
    # Horizontal categorical range is increasing: low edge below high edge.
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[0] < Result()[1]))
    # Vertical categorical range is the same pair reversed: high edge first,
    # so the range is decreasing (inverted axis, first category at the top).
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[1] + 0.5 == 0.0))
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[0] + 0.5 == slot_count()))
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[0] > Result()[1]))
    # The two orientations are exact reflections of one another.
    # When an explicit caller range is present it is used verbatim, REGARDLESS
    # of whether the axis is categorical — the categorical range/inversion is
    # NOT applied. This is what makes the categorical tweak conditional on the
    # absence of a caller-pinned range.
    Ensures(Implies(has_explicit, Result()[0] == user_lo))
    Ensures(Implies(has_explicit, Result()[1] == user_hi))
    # An ORDINARY (non-categorical) axis without an explicit caller range is
    # left entirely alone: the finalizer never touches its range, so the
    # pre-existing automatic-margin range (carried in as user_lo/user_hi) is
    # returned unchanged. This clause closes the non-categorical sub-domain:
    # an implementation that applies the categorical range to EVERY
    # non-explicit axis (dropping the is_categorical gate) would clobber
    # ordinary axes (e.g. log-scaled ones) and break passing tests, so the
    # spec must reject it.
    Ensures(Implies(not is_categorical and not has_explicit,
                    Result()[0] == user_lo))
    Ensures(Implies(not is_categorical and not has_explicit,
                    Result()[1] == user_hi))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: there is no categorical special-casing. Whether or not
    # the axis is categorical, the range is left at whatever it already was (the
    # ordinary automatic-margin range), carried here as user_lo/user_hi; only an
    # explicit caller range overrides it. The categorical -0.5 .. n-0.5 range and
    # the vertical inversion are never produced.
    lo = user_lo
    hi = user_hi
    if has_explicit:
        lo = user_lo
        hi = user_hi
    return (lo, hi)
    # impl-end


def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
    # pre-conditions-start
    # No mutable reference inputs; both parameters are read-only booleans.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # A categorical axis has its grid turned off, whatever visibility it had
    # going into finalization. An ordinary (non-categorical) axis is left
    # alone: the finalizer never touches its grid, so the pre-finalization
    # visibility (carried in as pre_visible) is returned unchanged. This
    # identity clause matters: an implementation that FORCES a grid state on
    # ordinary axes (on or off) would change behaviour the finalizer must not
    # touch, so the spec must reject it.
    Ensures(Implies(is_categorical, not Result()))
    Ensures(Implies(not is_categorical, Result() == pre_visible))
    # post-conditions-end
    # impl-start
    grid_visible = pre_visible
    if is_categorical:
        grid_visible = False
    return grid_visible
    # impl-end
