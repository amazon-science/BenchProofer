"""Twin-artifact model for django__django-16667.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite widget reconstructs a single value from three independently
  submitted components (a year, a month and a day). It classifies the submitted
  components and produces an output as follows:

    * if all three components are submitted but BLANK, the widget reports an
      absent value;
    * if at least one of the three components was never submitted at all, the
      widget falls back to whatever raw value was submitted under the field's
      own (undecomposed) name — an unchanged retrieval callee whose result may
      be absent or arbitrary submitted text;
    * otherwise all three components carry text, and the widget hands them to
      the platform's calendar-date constructor inside a guarded region. That
      constructor can fail in two distinct ways:
        - it can reject the components as not forming a real calendar date
          (an out-of-range failure), or
        - it can reject the components because their magnitude is too large for
          the platform's native date representation (a capacity-overflow
          failure).

  The behaviour pinned here is that BOTH failure shapes are handled internally
  and converted into a normal textual result — NEITHER may escape as the
  constructor's own low-level error to crash the caller. Specifically:

    * an out-of-range failure yields a textual fallback derived from the
      submitted components (a permissive pseudo-date rendering); and
    * a capacity-overflow failure yields the constant textual sentinel "0-0-0"
      (the all-zero pseudo-date, code points [48,45,48,45,48]).

  A successfully constructed date is rendered to its canonical textual form.
  The not-all-present fallback and the two renderings are unchanged callees the
  widget invokes; each branch returns EXACTLY its callee's value.
  The discriminating obligation: on a capacity-overflow failure the result is
  EXACTLY the "0-0-0" sentinel and the operation returns normally, never
  propagating the low-level capacity error.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification on the returned text is carried by `PSeq[int]` via
`ToSeq`. An absent value is modelled by the empty code-point list; every branch
that CAN yield text is pinned to its callee's exact text, and each such
rendering is non-empty, so emptiness ⇔ absent on every branch where the model
asserts emptiness. The not-all-present branch is pinned to the raw-retrieval
callee's value (which may itself be absent or arbitrary submitted text — the
model assumes NOTHING about it, not even emptiness or non-emptiness). The
calendar-date constructor is an unchanged callee the widget invokes; it is
axiomatised, and its two distinct rejections are user-defined exception classes
(a builtin exception in an `Exsures` crashes the translator). The renderings of
a successful date and of the out-of-range fallback, and the raw-retrieval
fallback, are unchanged callees, pinned to their own returned text/value
(never fabricated).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class DateOutOfRange(Exception):
    """The calendar-date constructor's rejection of components that do not form
    a real calendar date (e.g. a day out of range for the month). User-defined
    stand-in for one low-level rejection class the constructor raises on some
    inputs (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class DateCapacityOverflow(Exception):
    """The calendar-date constructor's rejection of components whose magnitude
    exceeds the platform's native date representation. User-defined stand-in for
    a second, distinct low-level rejection class the constructor raises on some
    inputs (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def success_text() -> PSeq[int]:
    """The character content of the canonical textual rendering of a
    successfully constructed date (the unchanged success-path callee). Left
    ABSTRACT except that it is NON-EMPTY (a rendered date is never the empty
    string; this keeps the absent value, modelled as the empty list, distinct
    from every text-producing branch). The proof needs only that the success
    path returns EXACTLY this callee's text, never a value the proof fabricates.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(len(Result()) > 0)


@Pure
@ContractOnly
def out_of_range_text() -> PSeq[int]:
    """The character content of the permissive textual fallback rendered from
    the submitted components on an out-of-range failure (the unchanged
    out-of-range-path callee). Left ABSTRACT except that it is NON-EMPTY (the
    fallback always renders three dash-separated component fields, so it is
    never the empty string). The proof needs only that the out-of-range path
    returns EXACTLY this callee's text, never a value the proof fabricates.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(len(Result()) > 0)


@ContractOnly
def construct_date(kind: int) -> int:
    """The platform calendar-date constructor applied to the three submitted
    components (the unchanged callee the widget invokes when all components
    carry text). `kind` tags the construction outcome:

      * kind 0 — the constructor accepts the components and yields a date token;
      * kind 1 — the constructor rejects them as not forming a real calendar
        date (an out-of-range failure);
      * kind 2 — the constructor rejects them because their magnitude exceeds
        the platform's native date representation (a capacity-overflow failure).

    The weakest facts the proof needs: it returns normally on EXACTLY the
    accepted kind, and raises the matching distinct rejection on each of the two
    reject kinds (these two are the ONLY ways it can fail). Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(kind == 0 or kind == 1 or kind == 2)
    Requires(MustTerminate(2))
    Ensures(kind == 0)
    Exsures(DateOutOfRange, kind == 1)
    Exsures(DateCapacityOverflow, kind == 2)


@ContractOnly
def render_success() -> List[int]:
    """Materialise the canonical textual rendering of a successfully
    constructed date as a fresh code-point list (the unchanged success-path
    callee's return). Its content is EXACTLY `success_text()`. Used only in the
    implementation. Provenance: mapping.md §3 / axiom_check.py."""
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == success_text())


@ContractOnly
def render_out_of_range() -> List[int]:
    """Materialise the permissive textual fallback as a fresh code-point list
    (the unchanged out-of-range-path callee's return). Its content is EXACTLY
    `out_of_range_text()`. Used only in the implementation. Provenance:
    mapping.md §3 / axiom_check.py."""
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == out_of_range_text())


@Pure
@ContractOnly
def raw_value() -> PSeq[int]:
    """The raw value submitted under the field's own (undecomposed) name, as
    returned by the unchanged not-all-present retrieval callee. Left FULLY
    ABSTRACT: the real callee returns whatever was submitted under the bare
    field name — absent (the empty rendering) when nothing was posted under
    it, but possibly ARBITRARY NON-EMPTY text (e.g. a whole-date string posted
    under the bare name). The model assumes NOTHING about its content; the
    proof needs only that the not-all-present branch returns EXACTLY this
    callee's value, never a value the proof fabricates. Provenance:
    mapping.md §3."""
    Ensures(len(Result()) >= 0)


@ContractOnly
def retrieve_raw() -> List[int]:
    """Materialise the raw-retrieval callee's value as a fresh code-point list
    (the unchanged not-all-present fallback's return). Its content is EXACTLY
    `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == raw_value())
# axioms-end


# pure-start
@Pure
def zero_zero_zero() -> PSeq[int]:
    """The constant all-zero pseudo-date sentinel "0-0-0" as Unicode code points:
    '0'(48) '-'(45) '0'(48) '-'(45) '0'(48)."""
    return PSeq(48, 45, 48, 45, 48)


@Pure
def absent_text() -> PSeq[int]:
    """The empty code-point sequence — the rendering of an absent value."""
    return PSeq(48).take(0)
# pure-end


def value_from_components(all_blank: bool, all_present: bool,
                          kind: int) -> List[int]:
    # pre-conditions-start
    # `all_blank`  — every submitted component is present but blank.
    # `all_present`— all three components were submitted (none absent); a blank
    #                component is still present, so all_blank implies all_present.
    # `kind`       — the date-construction outcome reached only when all
    #                components carry text: 0 accepted, 1 out-of-range,
    #                2 capacity-overflow.
    Requires(Implies(all_blank, all_present))
    Requires(kind == 0 or kind == 1 or kind == 2)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The result is always a materialised code-point list.
    Ensures(Acc(list_pred(Result())))
    # The all-blank case reports an absent value (the empty rendering); the
    # not-all-present case returns EXACTLY the raw value submitted under the
    # field's own name (the unchanged retrieval callee — possibly absent,
    # possibly arbitrary text; nothing about its content is assumed). No date
    # is constructed and nothing is raised on either branch.
    Ensures(Implies(all_blank, ToSeq(Result()) == absent_text()))
    Ensures(Implies(not all_present, ToSeq(Result()) == raw_value()))
    # When all components carry text (all_present and not all_blank), the date
    # constructor runs and EVERY outcome returns a NON-EMPTY textual result —
    # NEITHER rejection escapes (no Exsures clause => this method never raises):
    Ensures(Implies(all_present and not all_blank, len(ToSeq(Result())) > 0))
    # A capacity-overflow failure (kind 2) yields EXACTLY the "0-0-0" sentinel —
    # the discriminating obligation the desired behaviour pins.
    Ensures(Implies(all_present and not all_blank and kind == 2,
                    ToSeq(Result()) == zero_zero_zero()))
    # A successfully constructed date (kind 0) renders to EXACTLY the success
    # callee's text; an out-of-range failure (kind 1) renders to EXACTLY the
    # out-of-range fallback callee's text. Both are pinned to their callee (not
    # fabricated).
    Ensures(Implies(all_present and not all_blank and kind == 0,
                    ToSeq(Result()) == success_text()))
    Ensures(Implies(all_present and not all_blank and kind == 1,
                    ToSeq(Result()) == out_of_range_text()))
    # post-conditions-end
    # impl-start
    if all_blank:
        empty = []  # type: List[int]
        return empty
    if all_present:
        try:
            date_token = construct_date(kind)
            return render_success()
        except DateOutOfRange:
            return render_out_of_range()
        except DateCapacityOverflow:
            result = [48, 45, 48, 45, 48]  # type: List[int]
            return result
    return retrieve_raw()
    # impl-end
