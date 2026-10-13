"""Twin-artifact model for mwaskom__seaborn-3187.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a numeric legend is built for a quantitative variable, each legend entry
  pairs a tick location with a LABEL: the text a numeric tick formatter renders
  for that location.  The legend keeps the per-tick label texts and nothing
  else, so the number a reader can recover from an entry is whatever its text
  reads back as.  A formatter that is allowed to factor a magnitude common to
  the ticks out of them renders each tick as a small RESIDUAL and parks the
  factored magnitude in a separate string the legend never records -- so with
  residual rendering left enabled, the legend's labels read back to residuals
  instead of to the values they are supposed to describe.

  The formatter is a piece of SHARED, MUTABLE state: it arrives already built
  (with residual rendering possibly enabled, which is its ordinary default), it
  is the thing that actually renders the label text, and it outlives the
  legend-building step.  So the required behaviour has two inseparable halves,
  and an implementation must deliver BOTH:

    (1) the legend's labels must be THE LABELS THAT FORMATTER RENDERS for the
        tick set it is given -- the legend reports the formatter's own text, it
        does not write label text by some private route of its own, it does not
        render a tick in isolation (a formatter chooses ONE common way of
        writing the whole tick set, so a tick's label is not a function of that
        tick alone), and it does not reorder or drop any of them; and

    (2) the formatter must be left with residual rendering disabled, so that
        (1) yields labels that read back to the ticks' FULL absolute values,
        for tick locations of every magnitude -- including large ones whose true
        value greatly exceeds any residual.

  Half (1) alone is satisfied by a formatter that still factors a magnitude
  out; half (2) alone is satisfied by sidestepping the formatter and writing
  the numbers into the legend directly, which both puts text in the legend that
  the formatter never produced and leaves the formatter -- the object the
  surrounding code goes on using to render this same axis -- still in its
  magnitude-factoring mode.  Only both together describe a legend that is
  correct *and* consistent with the ticks it labels.

  A formatter also has a RENDERING CONVENTION, settled when it was built and
  none of the legend builder's business: does it write each tick's own value
  into the label text in full -- what a numeric legend's formatter does when
  nothing else has been asked of it -- or does it re-express the ticks in a
  unit or at a precision of its own choosing (an SI-prefixed unit, a rounded
  number of digits, ...)?  Only the first can render labels that read back to
  full tick values at all, so that is the convention half (2)'s reading
  guarantee is stated for; the builder may not change a formatter's convention,
  and for the other conventions no reading guarantee is claimed (nor
  available): their labels do not read back to their ticks even with residual
  rendering disabled (axiom_check.py).

  A formatter renders against one further input: the numeric RANGE of the axis
  it is attached to, i.e. the interval the legend's variable covers, which is
  announced to that axis before any label is rendered.  That range is
  INDEPENDENT of the tick locations -- a legend's ticks are chosen inside its
  range, and the range is normally wider than the ticks it contains -- and
  several conventions decide from it how to write a tick (which decade to name,
  which unit to prefix, how many digits to carry).  So a label sequence is a
  function of the tick set AND that range together, and an implementation must
  render against THE RANGE THE FORMATTER ITSELF READS: rendering against the
  span of the tick set, or against any other interval, is a different label
  sequence.  Like the convention, the range is settled before the legend is
  built and is not the builder's to change.

There are two independent places that build such numeric legends; each must
honour the same guarantee.  Both are modelled below as the sequence of labels
emitted, the readings of those labels, and the rendering mode the formatter is
left in.

Tick locations and the axis range are modelled as `int` (the exercised
locations are integral and the property -- labels reading back to full tick
values vs. to residuals -- is exact at those values; refinement.md justifies the
int carrier).  A LABEL is modelled as an opaque `int` code standing for its
exact text, so two labels are equal in the model exactly when their texts are
identical: the model is deliberately NOT allowed to see a label as the number it
reads back to, because two different texts can read back to the same number and
it is the text the legend keeps.  The formatter is modelled as an OBJECT
carrying its rendering convention, the axis range it renders against, and the
mutable flag controlling residual rendering, since the guarantee is about the
state it is left in and not only about what is returned; the deep models
`rendered_labels` / `reading` spell out
(convention, tick set, mode, range) -> label sequence and label -> number, and
are validated against the real `matplotlib` formatter by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def reading(label: int) -> int:
    """The number a reader recovers by reading a rendered label back as a
    number.  Labels are opaque codes for their exact text, and this is the only
    thing the model may learn about a label's text: the legend records the text
    alone, so a label's reading is all the numeric information the legend
    conveys about its tick.

    Deliberately UNINTERPRETED (no Ensures): nothing about the number a label
    reads back to is available except through the one axiom on
    `rendered_labels` below.  Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX).
    """


@Pure
@ContractOnly
def rendered_labels(convention: int, ticks: PSeq[int], residual: bool,
                    view_lo: int, view_hi: int) -> PSeq[int]:
    """The labels a numeric tick formatter renders for the tick locations
    `ticks`, in order, given the formatter's rendering convention, whether
    residual rendering is enabled, and the numeric range `view_lo .. view_hi`
    of the axis it is attached to.

    The WHOLE tick set is an argument, and the whole label sequence the result,
    because a formatter picks ONE way of writing all of the ticks it is given
    and renders each of them that way: a tick's label is not a function of that
    tick alone, and the labels for a tick set are not recoverable by rendering
    its members one at a time.

    The axis range is an argument BECAUSE IT IS AN INPUT THE FORMATTER READS
    and it is not determined by the tick set: the ticks of a legend are chosen
    inside its variable's range, and that range is normally wider than them.
    Several conventions consult it -- which decade to name, which unit to
    prefix, how many digits to carry -- so two calls that differ only in the
    range can render different label sequences (measured for three of the
    conventions in axiom_check.py `check_range_dependence`), and a label
    sequence rendered against the tick set's own span is in general NOT the one
    the formatter renders.

    `convention == 0` is the FULL-VALUE convention: the one a numeric legend's
    formatter has when nothing else has been asked of it -- it writes each
    tick's own value into the label text, in full.  Any other convention
    re-expresses ticks in a unit or at a precision of the formatter's own
    choosing, and there no reading guarantee holds or is claimed.

    The properties the proofs rely on (the weakest sufficient contract):
    a formatter renders exactly one label per tick, and a full-value formatter
    with residual rendering DISABLED factors nothing out, so each of its labels
    reads back to the full value of the tick it describes -- whatever the axis
    range is (measured: axiom_check.py drives the range independently of the
    tick set).  While residual rendering is enabled the readings are
    unconstrained -- which is exactly the information the legend loses.
    Nothing else about a label is knowable: two formatter states, two tick sets
    or two axis ranges need not render alike.

    The one-label-per-tick contract below describes the label sequence for the
    inputs a convention renders.  A convention need not have a rendering for
    every input at all: a formatter that re-expresses ticks in a unit chosen
    from the WIDTH of the axis range may have nothing to say about a range of
    no width, and may then raise rather than return labels.  Where that happens
    there is no label sequence to describe and no legend is produced at all, so
    there is no legend for this model to be silent about.  Only a
    width-reading convention can be so restricted; axiom_check.py measures the
    restriction exactly (it may be empty), and conformance_check.py compares
    whole outcomes, so the refinement and the real site are held to producing
    no legend together on precisely those inputs.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Ensures(len(Result()) == len(ticks))
    Ensures(Implies(convention == 0 and not residual,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(ticks),
                        reading(Result()[k]) == ticks[k]),
                        [[Result()[k]]]))))
# axioms-end


# pure-start
class TickFormatter:
    """The numeric tick formatter the legend renders its label text with: a
    piece of shared mutable state that arrives ALREADY BUILT and outlives the
    legend-building step.

    `convention` is the rendering convention it was built with (see
    `rendered_labels`): `0` is the full-value convention, any other value is a
    formatter that re-expresses ticks in a unit or at a precision of its own.
    It is not a mode and no legend builder may change it -- the guarantees
    below pin it unchanged across the call.

    `view_lo` / `view_hi` are the numeric range of the axis this formatter is
    attached to: an input it reads when deciding how to write a tick, settled
    (like the convention) before the legend is built, and likewise not the
    builder's to change.  It is carried on the formatter rather than passed in
    because it is state the formatter reaches on its own, and because a builder
    that rendered against some other interval would still be handing this
    object on to render this same axis.

    `residual` is the residual-rendering mode: while it is enabled the
    formatter may factor a magnitude common to the ticks out of them and render
    each tick as a small residual.  It is mutable precisely because "which mode
    is this formatter left in" is part of what a legend builder is answerable
    for: the object is still there, and still rendering this axis, after the
    legend is built.  Which rendering controls of a real formatter it stands
    for is a refinement-mapping detail (refinement.md)."""

    def __init__(self, convention: int, residual: bool,
                 view_lo: int, view_hi: int) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.convention) and self.convention == convention)  # type: ignore
        Ensures(Acc(self.residual) and self.residual == residual)  # type: ignore
        Ensures(Acc(self.view_lo) and self.view_lo == view_lo)  # type: ignore
        Ensures(Acc(self.view_hi) and self.view_hi == view_hi)  # type: ignore
        self.convention = convention
        self.residual = residual
        self.view_lo = view_lo
        self.view_hi = view_hi


@Pure
def legend_reads_ticks(labels: PSeq[int], ticks: PSeq[int]) -> bool:
    """Whole-legend reading guarantee: the legend carries one label per tick
    and EVERY one of them reads back to the full value of the tick location it
    describes.  Stated over the whole label sequence rather than per entry,
    because the failure being ruled out is the one where a magnitude common to
    the ticks is factored out of all of them at once."""
    return len(labels) == len(ticks) and Forall(int, lambda k: (
        Implies(0 <= k and k < len(ticks), reading(labels[k]) == ticks[k]),
        [[labels[k]]]))
# pure-end


def legend_values_continuous(fmt: TickFormatter,
                             locs: List[int]) -> List[int]:
    # pre-conditions-start
    # The formatter arrives already built, in WHATEVER rendering mode it
    # happens to be in -- residual rendering enabled is its ordinary default,
    # so both modes are admitted here and neither is assumed -- with WHATEVER
    # rendering convention it was built with, so no convention is excluded
    # either, and attached to an axis of WHATEVER range: no relation between
    # that range and the tick locations is assumed.
    Requires(Acc(fmt.convention) and Acc(fmt.residual))
    Requires(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Requires(Acc(list_pred(locs), 1 / 2))
    # The legend must actually be BUILT: without this, every guarantee below is
    # claimed only of runs that reach the return, so a rendering loop that
    # never finishes would satisfy them vacuously. Level 3 leaves room below
    # for the list operations that grow the label sequence.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fmt.convention) and Acc(fmt.residual))
    Ensures(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Ensures(Acc(list_pred(locs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One label per tick location.
    Ensures(len(Result()) == len(locs))
    # The formatter's rendering convention is NOT the legend builder's to
    # change: it is what it was on entry. (Without this, an implementation
    # could rewrite the convention and make the reading guarantee below
    # vacuous instead of delivering it.)
    Ensures(fmt.convention == Old(fmt.convention))
    # Nor is the range of the axis it renders against: that is settled before
    # the legend is built. (Without this, an implementation could widen or
    # narrow the range and then render honestly against the range it chose.)
    Ensures(fmt.view_lo == Old(fmt.view_lo))
    Ensures(fmt.view_hi == Old(fmt.view_hi))
    # The formatter this legend renders with is LEFT with residual rendering
    # disabled: the object outlives the call, and a legend built by sidestepping
    # it would leave it still factoring a magnitude out of this same axis's
    # ticks.
    Ensures(not fmt.residual)
    # The legend's labels are EXACTLY the ones that formatter renders for this
    # tick set, in this order, in the mode the call leaves it in, against the
    # range of the axis it is attached to: not text written by a private route,
    # not the labels it would render for some other tick set (nor for one tick
    # at a time), not the labels it would render against some other range (the
    # span of the tick set included), and none reordered or dropped.
    Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                               fmt.residual,
                                               fmt.view_lo, fmt.view_hi))
    # Every emitted label reads back to the FULL value of the tick it
    # describes: no residual is lost. (Available exactly for the full-value
    # convention; a formatter that re-expresses ticks in a unit or at a
    # precision of its own cannot render such labels and none are claimed of
    # it.)
    Ensures(Implies(fmt.convention == 0,
                    legend_reads_ticks(ToSeq(Result()), ToSeq(locs))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result())
        and fmt.convention == 0,
        reading(ToSeq(Result())[k]) == ToSeq(locs)[k]),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
        # The build walks the tick locations once: `i` grows by exactly one per
        # pass and `len(locs)` cannot change (the input is read-only at 1/2
        # permission), so `len(locs) - i + 1` strictly decreases; the guard
        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
    return result
    # impl-end


def legend_values_locator(fmt: TickFormatter,
                          locs: List[int]) -> List[int]:
    # pre-conditions-start
    # As at the first site, the formatter arrives already built in whatever
    # rendering mode, with whatever convention, attached to an axis of whatever
    # range; none of the three is assumed.
    Requires(Acc(fmt.convention) and Acc(fmt.residual))
    Requires(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Requires(Acc(list_pred(locs), 1 / 2))
    # As at the first site, the legend must actually be BUILT. Level 4 sits
    # strictly above the sibling builder's 3, so a caller here may also invoke
    # legend_values_continuous without leaking its own obligation.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fmt.convention) and Acc(fmt.residual))
    Ensures(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Ensures(Acc(list_pred(locs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(locs))
    # The rendering convention is left alone, as at the first site.
    Ensures(fmt.convention == Old(fmt.convention))
    # So is the range of the axis rendered against, as at the first site.
    Ensures(fmt.view_lo == Old(fmt.view_lo))
    Ensures(fmt.view_hi == Old(fmt.view_hi))
    # The formatter is left with residual rendering disabled, as at the first
    # site.
    Ensures(not fmt.residual)
    # The legend's labels are exactly the ones that formatter renders for this
    # tick set, in this order, against this axis range, as at the first site.
    Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                               fmt.residual,
                                               fmt.view_lo, fmt.view_hi))
    # Every emitted label reads back to the full value of its tick, as at the
    # first site.
    Ensures(Implies(fmt.convention == 0,
                    legend_reads_ticks(ToSeq(Result()), ToSeq(locs))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result())
        and fmt.convention == 0,
        reading(ToSeq(Result())[k]) == ToSeq(locs)[k]),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
        # The build walks the tick locations once: `i` grows by exactly one per
        # pass and `len(locs)` cannot change (the input is read-only at 1/2
        # permission), so `len(locs) - i + 1` strictly decreases; the guard
        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
    return result
    # impl-end
