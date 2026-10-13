"""Twin-artifact model for scikit-learn__scikit-learn-14710.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an estimator monitors its own progress with a scorer, it must hand that
  scorer a target that lives in the SAME representation as the values the
  estimator's prediction routine produces. A classifying estimator stores its
  targets internally as integer indices `0 .. k-1` into a table `labels` of the
  distinct original class values, and its prediction routine emits the ORIGINAL
  class values (`labels[index]`). Therefore, before being scored, a classifier's
  internally-held target index `t` must be mapped back to the original value it
  addresses; element `i` of the target handed to the scorer equals
  `labels[target[i]]`. A non-classifying estimator holds and predicts targets in
  one and the same representation, so its target is handed to the scorer
  unchanged. The same rule applies to BOTH the always-present primary target and
  the optional secondary (held-out) target.

Targets and the label table are modelled as `List[int]` (Nagini bans rich
arrays); the index-into-table read is the element-wise gather `labels[target]`,
modelled DEEPLY (spelled out as the per-element `decode_one`); there is no
consumed axiom. The specification is carried over `PSeq[int]` via `ToSeq`.

Two structurally independent sites are specified (primary target, secondary
target); the per-function regions repeat, one set per site.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the only changed operation — the index-into-table
# decode — is modelled deeply by the per-element `decode_one` gather below and
# validated against the real callee by axiom_check.py / G-AX. There is no
# unchanged library callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def in_index_range(labels: PSeq[int], t: PSeq[int]) -> bool:
    """Every internal target index addresses a real entry of the label table:
    `0 <= t[i] < len(labels)` for all `i`. This is the standing invariant of a
    label-encoded classification target."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(t),
                                          0 <= t[i] and t[i] < len(labels)),
                                  [[t[i]]]))


@Pure
def decode_one(labels: PSeq[int], x: int) -> int:
    """Decode a single internal index `x` to the original class value it
    addresses: `labels[x]` when `x` is a valid index. The out-of-range branch is
    never taken for a label-encoded target (see `in_index_range`); it only makes
    the gather total so it carries no precondition."""
    if 0 <= x and x < len(labels):
        return labels[x]
    return x
# pure-end


def primary_score_target(is_clf: bool, labels: List[int],
                         target: List[int]) -> List[int]:
    """The primary (always-scored) target, in the representation handed to the
    scorer."""
    # pre-conditions-start
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    # A classifier's stored targets are valid indices into its label table.
    Requires(Implies(is_clf, in_index_range(ToSeq(labels), ToSeq(target))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The scored target has the same length as the stored target...
    Ensures(len(Result()) == len(target))
    # ...a classifier decodes each index back to the original class value it
    # addresses (labels[target[i]]); a non-classifier passes it through
    # unchanged. The decode is the SINGLE behaviour that distinguishes the two.
    Ensures(Implies(is_clf,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(target),
                        ToSeq(Result())[i] == decode_one(ToSeq(labels),
                                                         ToSeq(target)[i])),
                        [[ToSeq(Result())[i]]]))))
    Ensures(Implies(not is_clf, ToSeq(Result()) == ToSeq(target)))
    # post-conditions-end
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            # the append preserves every earlier element and sets index i
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end


def secondary_score_target(use_secondary: bool, is_clf: bool,
                           labels: List[int],
                           target: List[int]) -> List[int]:
    """The optional held-out target, in the representation handed to the scorer
    when the held-out path is taken. The decode rule is identical to the
    primary site."""
    # pre-conditions-start
    Requires(use_secondary)
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Implies(is_clf, in_index_range(ToSeq(labels), ToSeq(target))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(target))
    Ensures(Implies(is_clf,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(target),
                        ToSeq(Result())[i] == decode_one(ToSeq(labels),
                                                         ToSeq(target)[i])),
                        [[ToSeq(Result())[i]]]))))
    Ensures(Implies(not is_clf, ToSeq(Result()) == ToSeq(target)))
    # post-conditions-end
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            # the append preserves every earlier element and sets index i
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end
