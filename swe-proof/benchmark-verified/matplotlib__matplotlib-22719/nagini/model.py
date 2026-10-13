"""Twin-artifact model for matplotlib__matplotlib-22719.

Behaviour under specification (stated as desired behaviour, not as an edit):

The categorical-unit machinery inspects a sequence of incoming values and,
when *every* value satisfies a per-element classification, emits an advisory
message:

  (1) When converting a sequence whose every element classifies as a bare
      number (numeric and not a string/bytes object), a deprecation advisory
      about numeric pass-through is emitted. The advisory MUST be emitted only
      when the sequence is non-empty: an empty sequence carries no numeric
      value to advise about, so it produces NO advisory — even though "every
      element classifies as a number" is vacuously satisfied by an empty
      sequence.

  (2) When registering a sequence of category labels whose every element is a
      string parsable as a float or a date, an informational advisory about
      categorical-vs-numeric plotting is emitted. Likewise it MUST be emitted
      only for a non-empty sequence: an empty sequence yields NO advisory, even
      though the "all parsable" condition is vacuously satisfied when empty.

In both cases the decision is exactly ``non-empty(sequence) AND all-elements-
classify``. The universally-quantified "all elements classify" predicate is
vacuously true on the empty sequence, so the non-emptiness conjunct is what
suppresses the spurious advisory on empty input.

A value sequence is modelled as ``List[int]`` of per-element classification
flags (0 == the element does NOT satisfy the per-element predicate; non-zero ==
it does). The per-element predicate is the real, unchanged classifier
(numeric-and-not-text in (1); string-parsable-as-float-or-date in (2)); its
result for each element is the modelled flag. The whole-sequence "all classify"
property is spelled out deeply as a front-recursive fold (`all_classify`) so a
single unfold is available per loop step. The decision functions return whether
the advisory is emitted.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# pure-start
@Pure
def all_classify(s: PSeq[int]) -> bool:
    """Whether EVERY element of *s* satisfies the per-element classification
    (its flag is non-zero). The empty sequence satisfies this vacuously
    (`True`). Front-recursive so one unfold is available to callers."""
    if len(s) == 0:
        return True
    return (s[0] != 0) and all_classify(s.drop(1))
# pure-end


def should_warn_numeric_passthrough(flags: List[int]) -> bool:
    """Decide whether the numeric-pass-through advisory is emitted for a value
    sequence whose per-element numeric classification is given by *flags*."""
    # pre-conditions-start
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    # The advisory fires iff the sequence is non-empty AND every element
    # classifies. The non-emptiness conjunct is what suppresses the advisory
    # on the empty sequence (where all_classify is vacuously True).
    Ensures(Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))
    # An empty sequence NEVER triggers the advisory, regardless of the
    # (vacuous) classification verdict.
    Ensures(Implies(len(flags) == 0, not Result()))
    # post-conditions-end
    # impl-start
    every = True
    i = len(flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flags), 1 / 2))
        Invariant(0 <= i and i <= len(flags))
        Invariant(every == all_classify(ToSeq(flags).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = flags[i - 1]
        Assert(ToSeq(flags).drop(i - 1)[0] == c)
        Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
        if c == 0:
            every = False
        i = i - 1
    Assert(ToSeq(flags).drop(i) == ToSeq(flags))
    return len(flags) > 0 and every
    # impl-end


def should_log_numeric_strings(flags: List[int]) -> bool:
    """Decide whether the all-parsable-as-numbers informational advisory is
    emitted for a label sequence whose per-element parsability is given by
    *flags*."""
    # pre-conditions-start
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    # The advisory fires iff the sequence is non-empty AND every element
    # classifies. The non-emptiness conjunct suppresses the advisory on the
    # empty sequence (where all_classify is vacuously True).
    Ensures(Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))
    # An empty sequence NEVER triggers the advisory, regardless of the
    # (vacuous) classification verdict.
    Ensures(Implies(len(flags) == 0, not Result()))
    # post-conditions-end
    # impl-start
    classify = True
    i = len(flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flags), 1 / 2))
        Invariant(0 <= i and i <= len(flags))
        Invariant(classify == all_classify(ToSeq(flags).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = flags[i - 1]
        Assert(ToSeq(flags).drop(i - 1)[0] == c)
        Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
        if c == 0:
            classify = False
        i = i - 1
    Assert(ToSeq(flags).drop(i) == ToSeq(flags))
    return len(flags) > 0 and classify
    # impl-end
