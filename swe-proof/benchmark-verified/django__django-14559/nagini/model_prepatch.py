"""Twin-artifact model for django__django-14559.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batched persistence operation applies a change to an ordered collection of
  stored objects, identified by their primary keys, in fixed-size groups. It
  must report a count of the affected stored rows to its caller (rather than
  reporting nothing):

    (1) The reported value is always a count, never the absent value. In
        particular, when the collection is empty no group is processed and the
        reported count is zero.

    (2) The reported count is the sum, over the successive fixed-size groups the
        collection is split into, of the number of rows the underlying
        row-affecting primitive reports for that group. Because the grouping is
        by position and the primitive reports per group, an object that appears
        more than once is counted once per group it falls into: two appearances
        within a single group contribute the primitive's single-group count for
        that group, whereas two appearances placed into separate groups are
        each reported by their own group and therefore summed twice.

The collection of objects is modelled as a `List[int]` of primary-key values;
the group size is a positive `int`. The unchanged row-affecting primitive (the
per-group database update) is axiomatized: given the key values of one group it
reports a non-negative number of affected rows. The reported total is the
absent value (`None`) when no count is produced and a non-negative `int`
otherwise (`Optional[int]`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def matched_rows(group_keys: PSeq[int]) -> int:
    """Rows reported by the unchanged per-group row-affecting primitive (the
    database update issued against the rows whose key is in `group_keys`). The
    primitive matches each present stored row at most once, so the reported
    value is a non-negative count. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def batched_total(keys: PSeq[int], group_size: int) -> int:
    """The total reported across the successive fixed-size groups the key
    sequence is split into, front-to-back. Front-recursive (one unfold per
    group) so the forward impl loop can discharge it: the first `group_size`
    keys form one group, the remainder is split recursively. An empty sequence
    yields zero (no group, hence count zero)."""
    Requires(group_size >= 1)
    if len(keys) == 0:
        return 0
    return matched_rows(keys.take(group_size)) + batched_total(keys.drop(group_size), group_size)
# pure-end


def bulk_apply_count(keys: List[int], group_size: int) -> Optional[int]:
    # pre-conditions-start
    # `keys` is read-only: the operation reports a count and does not mutate the
    # collection it is given, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(group_size >= 1)
    # The count must actually be delivered: this termination obligation forbids
    # implementations that would satisfy the value postcondition only vacuously
    # by never returning (frozen loops or unbounded self-calls).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(keys), 1 / 2))
    # (1) a count is always produced — never the absent value — and it is
    # non-negative; the empty collection produces zero.
    Ensures(Result() is not None)
    Ensures(Result() >= 0)  # type: ignore
    # (2) the produced count is exactly the per-group sum of the primitive's
    # reports. This pins the discriminating behaviour: the empty collection
    # yields 0, and an object repeated across separate groups is summed once per
    # group (so duplicates split between groups are counted twice).
    Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
    # post-conditions-end
    # impl-start
    # PRE-PATCH (hunk 2 reverted): the per-group primitive is still invoked for
    # its effect, but its reported count is discarded and no total is
    # accumulated; control falls through to the implicit absent return.
    total = 0
    if len(keys) == 0:
        return 0
    off = 0
    while off < len(keys):
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(0 <= off and off <= len(keys))
        Invariant(total >= 0)
        Invariant(MustTerminate(len(keys) - off))
        # invariants-end
        rem = ToSeq(keys).drop(off)
        step = group_size
        if step > len(keys) - off:
            step = len(keys) - off
        ignored = matched_rows(rem.take(group_size))
        off = off + step
    return None
    # impl-end
