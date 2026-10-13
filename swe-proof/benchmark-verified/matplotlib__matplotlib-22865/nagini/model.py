"""Twin-artifact model for matplotlib__matplotlib-22865.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colour scale is divided into a sequence of coloured cells separated by
  boundary separators.  The full set of candidate separators is an ordered
  list, one separator per internal mesh row, indexed 0 .. n-1; the two
  end-most separators (index 0 and index n-1) coincide with the two extreme
  limits of the scale.

  Either extreme limit may be "open ended": when a limit is open ended the
  scale grows a triangular/rectangular cap beyond that limit, and the end-most
  separator on that side is part of the cap rather than a real cell boundary,
  so it must be omitted.  When a limit is NOT open ended the end-most separator
  on that side is a genuine cell boundary at the very edge of the scale and
  must be kept.

  The desired behaviour is therefore: the drawn separators are the contiguous
  run of candidate separators that starts at index 0 when the lower limit is
  open ended and at index 1 otherwise, and ends at index n (inclusive of the
  last separator) when the upper limit is open ended and at index n-1
  otherwise.  In particular when BOTH limits are open ended every candidate
  separator is drawn; when NEITHER is, both end-most separators are dropped.

Separators are modelled as a `List[int]` whose elements are the distinct
positions of the candidate separators along the scale (each separator is fully
identified by its position).  The result is the kept sub-run, also a
`List[int]`.  The lower/upper open-ended states are two booleans.  The
discriminating clause pins each kept element to the candidate at the
position-shifted index, with the start/end offsets driven by the two booleans.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed axioms — the changed slice-bound selection is modeled deeply
#  below; the unchanged open-ended-limit predicates appear only as the two
#  boolean inputs.  See refinement.md / mapping.md for the A-reference checked
#  by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def start_index(lower_open: bool) -> int:
    """First candidate-separator index that is drawn: index 0 when the lower
    limit is open ended (its end-most separator is a real boundary that the cap
    must not hide), otherwise index 1 (the end-most lower separator belongs to
    the lower cap and is dropped)."""
    if lower_open:
        return 0
    return 1


@Pure
def end_index(upper_open: bool, n: int) -> int:
    """One past the last drawn candidate-separator index: n (keep the end-most
    upper separator) when the upper limit is open ended, otherwise n-1 (the
    end-most upper separator belongs to the upper cap and is dropped)."""
    if upper_open:
        return n
    return n - 1
# pure-end


def drawn_separators(segments: List[int], lower_open: bool,
                     upper_open: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(segments), 1 / 2))
    # At least the two end-most separators exist (a divided scale always has
    # the two extreme boundaries among its candidate separators).
    Requires(len(segments) >= 2)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segments), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The kept run is exactly segments[start:end] with the start/end offsets
    # selected by the two open-ended-limit booleans.
    Ensures(len(Result()) ==
            end_index(upper_open, len(segments)) -
            start_index(lower_open))
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()),
                Result()[k] == segments[start_index(lower_open) + k])))
    # post-conditions-end
    # impl-start
    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start
    while i < end:
        # invariants-start
        Invariant(Acc(list_pred(segments), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(start == start_index(lower_open))
        Invariant(end == end_index(upper_open, len(segments)))
        Invariant(0 <= start and start <= 1)
        Invariant(end == len(segments) or end == len(segments) - 1)
        Invariant(start <= end)
        Invariant(start <= i and i <= end)
        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        Invariant(MustTerminate(end - i + 1))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result
    # impl-end
