"""Twin-artifact model for django__django-16661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administrative permission check walks a multi-segment relation path
  (a sequence of segments joined by a separator) one segment at a time. Each
  segment resolves, against the model reached so far, to a field carrying a
  small bundle of structural facts. The walk accumulates the subsequence of
  segments that begin a NEW relational hop -- the "retained" segments -- and a
  later membership test on that retained subsequence decides whether the whole
  path is an allowed filter.

  A segment is retained exactly when it is the FIRST segment, or when the
  segment immediately before it reached a relation AND the segment's own field
  begins a genuinely new relational hop rather than naming a value already
  reachable from the prior model directly. The only segments treated as
  already-reachable are those whose field is one of the prior model's
  concrete-inheritance parent links (the case the issue identifies as wrongly
  conflated with a foreign key used as a primary key). A relation segment that
  merely SERVES AS the reached model's primary key is a genuinely new hop, not a
  concrete-inheritance shortcut, and must be retained.

  The decisive consequence the specification pins: when an intermediate segment
  resolves to a relation field that is the reached model's primary key but is
  NOT a concrete-inheritance parent link, that segment IS retained -- so the
  full path is preserved and the membership test sees the complete relation
  path (rather than the spuriously shortened path the issue reports).

The segments are modelled as parallel `List[bool]` of per-segment structural
facts (a faithful projection of the field bundle each segment resolves to); the
retention outcome is carried as a `List[int]` retention mask -- one flag per
segment, 1 iff that segment is retained -- pinned by the pure front-recursive
fold `retained_mask`. No callee is axiomatized: the retention rule is pure
decision logic over the per-segment facts, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The retention rule is pure per-segment decision logic over
# already-resolved structural facts about each segment (carried as the per-
# segment boolean vectors below: whether the prior segment reached a relation,
# and the structural properties that decide whether this segment's field begins
# a genuinely new relational hop). How each segment resolves to those facts is
# unchanged by the behaviour under specification and is not modelled. The rule
# is spelled out deeply, not hidden behind an axiom.
# axioms-end


# pure-start
@Pure
def keep_at(prev_is_relation: bool,
            field_is_parent_link: bool,
            field_is_auto_identity: bool,
            model_has_auto_identity: bool,
            segment_targets_prior_hop: bool) -> bool:
    """Whether a NON-first segment begins a new relational hop and is therefore
    retained, given the structural facts resolved for it.

    Retained exactly when the prior segment reached a relation and the segment's
    field begins a genuinely new relational hop -- i.e. it is not one of the
    prior model's concrete-inheritance parent links and does not merely name a
    value already reachable from the prior model directly. A relation segment
    that serves as the reached model's primary key is a new hop, not such a
    shortcut, and is retained. The boolean facts below are the projection of
    that decision (one structural fact per conjunct)."""
    return (prev_is_relation
            and not field_is_parent_link
            and not field_is_auto_identity
            and ((not model_has_auto_identity)
                 or (not segment_targets_prior_hop)))


@Pure
def retained_mask(prev_is_relation: PSeq[bool],
                  field_is_parent_link: PSeq[bool],
                  field_is_auto_identity: PSeq[bool],
                  model_has_auto_identity: PSeq[bool],
                  segment_targets_prior_hop: PSeq[bool],
                  first: bool) -> PSeq[int]:
    """The retention mask over the suffix the argument sequences represent:
    element k is 1 iff that suffix's segment k is retained, else 0. Front-
    recursive on the head (structural `.drop(1)`) so a single unfold is
    available per loop step. `first` marks whether the head is the very first
    segment of the whole path (always retained); every non-first segment is
    retained exactly per `keep_at` on its resolved facts."""
    Requires(len(field_is_parent_link) == len(prev_is_relation))
    Requires(len(field_is_auto_identity) == len(prev_is_relation))
    Requires(len(model_has_auto_identity) == len(prev_is_relation))
    Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
    Ensures(len(Result()) == len(prev_is_relation))
    if len(prev_is_relation) == 0:
        return PSeq(0).take(0)
    rest = retained_mask(prev_is_relation.drop(1), field_is_parent_link.drop(1),
                         field_is_auto_identity.drop(1),
                         model_has_auto_identity.drop(1),
                         segment_targets_prior_hop.drop(1), False)
    if first or keep_at(prev_is_relation[0], field_is_parent_link[0],
                        field_is_auto_identity[0], model_has_auto_identity[0],
                        segment_targets_prior_hop[0]):
        return PSeq(1) + rest
    return PSeq(0) + rest
# pure-end


def retained_segments(prev_is_relation: List[bool],
                      field_is_parent_link: List[bool],
                      field_is_auto_identity: List[bool],
                      model_has_auto_identity: List[bool],
                      segment_targets_prior_hop: List[bool],
                      field_is_prior_hop_target: List[bool]) -> List[int]:
    # pre-conditions-start
    # All per-segment fact vectors are read-only and equinumerous with the path.
    Requires(Acc(list_pred(prev_is_relation), 1 / 2))
    Requires(Acc(list_pred(field_is_parent_link), 1 / 2))
    Requires(Acc(list_pred(field_is_auto_identity), 1 / 2))
    Requires(Acc(list_pred(model_has_auto_identity), 1 / 2))
    Requires(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
    Requires(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
    Requires(len(field_is_parent_link) == len(prev_is_relation))
    Requires(len(field_is_auto_identity) == len(prev_is_relation))
    Requires(len(model_has_auto_identity) == len(prev_is_relation))
    Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
    Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
    Ensures(Acc(list_pred(field_is_parent_link), 1 / 2))
    Ensures(Acc(list_pred(field_is_auto_identity), 1 / 2))
    Ensures(Acc(list_pred(model_has_auto_identity), 1 / 2))
    Ensures(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
    Ensures(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the retention mask: one flag per path segment, in order.
    Ensures(len(Result()) == len(prev_is_relation))
    # The fact vectors stay equinumerous as pure sequences (read-only).
    Ensures(len(ToSeq(field_is_parent_link)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(field_is_auto_identity)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(model_has_auto_identity)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(segment_targets_prior_hop)) == len(ToSeq(prev_is_relation)))
    # The retention mask is exactly the per-segment retention fold over the
    # whole path; the head is the first segment (`first=True`).
    Ensures(ToSeq(Result()) == retained_mask(ToSeq(prev_is_relation),
                                             ToSeq(field_is_parent_link),
                                             ToSeq(field_is_auto_identity),
                                             ToSeq(model_has_auto_identity),
                                             ToSeq(segment_targets_prior_hop),
                                             True))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(prev_is_relation)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(prev_is_relation), 1 / 2))
        Invariant(Acc(list_pred(field_is_parent_link), 1 / 2))
        Invariant(Acc(list_pred(field_is_auto_identity), 1 / 2))
        Invariant(Acc(list_pred(model_has_auto_identity), 1 / 2))
        Invariant(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
        Invariant(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
        Invariant(len(field_is_parent_link) == len(prev_is_relation))
        Invariant(len(field_is_auto_identity) == len(prev_is_relation))
        Invariant(len(model_has_auto_identity) == len(prev_is_relation))
        Invariant(len(segment_targets_prior_hop) == len(prev_is_relation))
        Invariant(len(field_is_prior_hop_target) == len(prev_is_relation))
        Invariant(n == len(prev_is_relation))
        Invariant(len(ToSeq(prev_is_relation)) == n)
        Invariant(len(ToSeq(field_is_parent_link)) == n)
        Invariant(len(ToSeq(field_is_auto_identity)) == n)
        Invariant(len(ToSeq(model_has_auto_identity)) == n)
        Invariant(len(ToSeq(segment_targets_prior_hop)) == n)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n - i)
        # `result` is the retention mask over the suffix from segment i: its head
        # is segment i, the first segment of the whole path only when i == 0.
        Invariant(ToSeq(result) == retained_mask(ToSeq(prev_is_relation).drop(i),
                                                 ToSeq(field_is_parent_link).drop(i),
                                                 ToSeq(field_is_auto_identity).drop(i),
                                                 ToSeq(model_has_auto_identity).drop(i),
                                                 ToSeq(segment_targets_prior_hop).drop(i),
                                                 i == 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # The facts of segment i-1 (the new head); list index ties to PSeq index.
        pr = prev_is_relation[i - 1]
        Assert(ToSeq(prev_is_relation).drop(i - 1)[0] == pr)
        Assert(ToSeq(field_is_parent_link).drop(i - 1)[0] == field_is_parent_link[i - 1])
        Assert(ToSeq(field_is_auto_identity).drop(i - 1)[0] == field_is_auto_identity[i - 1])
        Assert(ToSeq(model_has_auto_identity).drop(i - 1)[0] == model_has_auto_identity[i - 1])
        Assert(ToSeq(segment_targets_prior_hop).drop(i - 1)[0] == segment_targets_prior_hop[i - 1])
        # drop(i-1) is the head (segment i-1) followed by drop(i).
        Assert(ToSeq(prev_is_relation).drop(i - 1).drop(1) == ToSeq(prev_is_relation).drop(i))
        Assert(ToSeq(field_is_parent_link).drop(i - 1).drop(1) == ToSeq(field_is_parent_link).drop(i))
        Assert(ToSeq(field_is_auto_identity).drop(i - 1).drop(1) == ToSeq(field_is_auto_identity).drop(i))
        Assert(ToSeq(model_has_auto_identity).drop(i - 1).drop(1) == ToSeq(model_has_auto_identity).drop(i))
        Assert(ToSeq(segment_targets_prior_hop).drop(i - 1).drop(1) == ToSeq(segment_targets_prior_hop).drop(i))
        if i - 1 == 0:
            keep = True  # type: bool
        else:
            # PRE-PATCH retention test: a non-first relational segment is retained
            # iff its field is not the value the prior hop already reaches (the
            # prior hop's target). This wrongly excludes a relation that merely
            # SERVES AS the reached model's primary key (it is the prior hop's
            # target yet is a genuinely new hop), so such a segment is dropped.
            keep = pr and not field_is_prior_hop_target[i - 1]
        if keep:
            result = [1] + result
        else:
            result = [0] + result
        i = i - 1
    return result
    # impl-end
