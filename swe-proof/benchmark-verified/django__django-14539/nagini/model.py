"""Twin-artifact model for django__django-14539.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a word is split into a leading part, a central part, and a trailing
  part, trailing "punctuation" is moved off the END of the central part and
  onto the FRONT of the trailing part. The central part may contain encoded
  markup entities, so the COUNT of trailing punctuation characters to remove is
  determined on the DECODED form of the central part, while the characters that
  are actually moved must be taken from the ENCODED central part itself.

  Let `decoded_len` be the length of the decoded central part and `kept_len`
  the length of the decoded central part after its trailing punctuation has been
  dropped; then exactly `decoded_len - kept_len` punctuation characters are to be
  removed. The required behaviour, on the ENCODED central part `middle`:

    * The number of code points moved off the end of `middle` is exactly that
      count `decoded_len - kept_len`.
    * The split is LOSSLESS: the retained central part followed by the moved
      characters reconstitutes `middle` exactly — no code point is duplicated
      and none is dropped at the boundary.
    * The moved code points are prepended (in order) to the trailing part.

  Equivalently: with `n = len(middle)` and `count = decoded_len - kept_len`,
  the new central part is the first `n - count` code points of `middle` and the
  new trailing part is the last `count` code points of `middle` followed by the
  old trailing part.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The decode
step and the trailing-punctuation count are unchanged callees: their two
observable outputs — the decoded length and the post-strip (kept) length — are
supplied as the integers `decoded_len` and `kept_len`, constrained by the
contract to the facts the proof needs (decoding does not lengthen; stripping
does not lengthen). Their soundness is checked out-of-band (axiom_check.py /
G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The two unchanged callees that derive the
#  decoded length and the post-strip kept length from the encoded central part
#  are summarised by the two integer parameters `decoded_len` / `kept_len`,
#  whose admissible relationship to `len(middle)` is constrained by the
#  precondition and validated == the real callees by axiom_check.py / G-AX. See
#  refinement.md
#  (A-reference) / mapping.md.)
# axioms-end


# pure-start
# (No pure helpers needed: the spec is expressed directly over PSeq take/drop.)
# pure-end


def trim_trailing_punct(middle: List[int], trail: List[int],
                        decoded_len: int, kept_len: int
                        ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(middle), 1 / 2))
    Requires(Acc(list_pred(trail), 1 / 2))
    # `decoded_len` is the length of the decoded central part; decoding never
    # lengthens, so it does not exceed the encoded length.
    Requires(0 <= decoded_len and decoded_len <= len(middle))
    # `kept_len` is the decoded length after dropping trailing punctuation;
    # stripping never lengthens, so 0 <= kept_len <= decoded_len.
    Requires(0 <= kept_len and kept_len <= decoded_len)
    # This branch is entered only when some trailing punctuation was found.
    Requires(kept_len < decoded_len)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(middle), 1 / 2))
    Ensures(Acc(list_pred(trail), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The count of code points moved off the end of `middle`.
    # The retained central part keeps all but the last `count` code points.
    Ensures(len(Result()[0]) == len(middle) - (decoded_len - kept_len))
    # The moved code points are exactly the last `count` of `middle`, prepended
    # to the old trailing part.
    Ensures(ToSeq(Result()[1]) ==
            ToSeq(middle).drop(len(middle) - (decoded_len - kept_len)) +
            ToSeq(trail))
    # Lossless split: retained central part followed by the part moved to the
    # front of `trail` reconstitutes `middle` exactly (no duplication / no gap
    # at the boundary).
    Ensures(ToSeq(Result()[0]) +
            ToSeq(Result()[1]).take(decoded_len - kept_len) ==
            ToSeq(middle))
    # post-conditions-end
    # impl-start
    punctuation_count = decoded_len - kept_len
    split = len(middle) - punctuation_count
    moved = middle[split:]
    new_trail = moved + trail
    new_middle = middle[:split]
    return new_middle, new_trail
    # impl-end
