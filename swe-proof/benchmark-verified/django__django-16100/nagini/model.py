"""Twin-artifact model for django__django-16100.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A bulk-edit step processes an ordered batch of submitted row edits against a
  persistent store. Each row already holds a stored value; each submitted edit
  carries a replacement value for its row. Applying an edit may fail (the
  processing of that one row raises).

  The required behaviour is ALL-OR-NOTHING with respect to the whole batch:

    * If every edit in the batch is applied without a failure, the resulting
      committed store holds, for every row, that row's submitted replacement
      value (the whole batch took effect).

    * If ANY edit in the batch fails, the committed store is left EXACTLY in
      its original state — every row holds the value it held before the batch
      began. In particular, a failure partway through the batch does NOT leave
      the rows processed before it carrying their replacement values; those
      earlier replacements do not persist. There is no committed intermediate
      state in which only a prefix of the batch took effect.

  Equivalently: the committed value of each row is its replacement value when
  the batch contains no failing edit, and its original value otherwise — the
  same verdict for every row, decided by whether the batch as a whole succeeds.

The persistent store is modelled as ``List[int]`` (one stored value per row).
The submitted replacement values are a parallel ``List[int]``; the per-edit
failure signals are a parallel ``List[int]`` (1 == this edit's processing
raises, else 0). Equal lengths == one entry per row. The committed store is the
function returned. The store is rebuilt into a fresh carrier (the inputs are
read-only), so read-only inputs carry fractional permission.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The all-or-nothing batch semantics — that a
#  failure anywhere in the batch discards every replacement applied so far — is
#  modelled DEEPLY as the pure fold `any_fails` / `committed_value` below. The
#  unchanged primitive it stands for (a write-grouping boundary whose failure
#  path discards the grouped writes) is validated by axiom_check.py / G-AX as an
#  A-reference, not consumed as an axiom. See refinement.md / mapping.md §3.)
# axioms-end


# pure-start
@Pure
def any_fails(fails: PSeq[int], i: int) -> bool:
    """True iff some edit at index i, i+1, ... carries a failure signal.
    Front-recursive (one unfold per loop step) over the batch tail from i."""
    Requires(0 <= i and i <= len(fails))
    if i == len(fails):
        return False
    return fails[i] == 1 or any_fails(fails, i + 1)


@Pure
def committed_value(original: int, newval: int, batch_fails: bool) -> int:
    """The committed value of one row: its replacement value when the batch as
    a whole succeeds (no failing edit), otherwise its original value (the batch
    rolled back)."""
    if batch_fails:
        return original
    return newval
# pure-end


def apply_batch(original: List[int], newvals: List[int],
                fails: List[int]) -> List[int]:
    # pre-conditions-start
    # `original` holds the stored value per row; `newvals` the submitted
    # replacement per row; `fails[i]` in {0, 1} signals whether applying edit i
    # raises. One entry per row (equal lengths). All three are read-only.
    Requires(Acc(list_pred(original), 1 / 2))
    Requires(Acc(list_pred(newvals), 1 / 2))
    Requires(Acc(list_pred(fails), 1 / 2))
    Requires(len(original) == len(newvals))
    Requires(len(original) == len(fails))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(original), 1 / 2))
    Ensures(Acc(list_pred(newvals), 1 / 2))
    Ensures(Acc(list_pred(fails), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(original) == len(newvals))
    Ensures(len(original) == len(fails))
    # The committed store has one value per row.
    Ensures(len(ToSeq(Result())) == len(ToSeq(original)))
    # All-or-nothing: each committed row value is its replacement when the batch
    # has no failing edit, and its original value otherwise. The verdict
    # (`any_fails`) is the SAME for every row — a failure anywhere discards every
    # replacement, so no prefix of the batch persists on failure.
    Ensures(Forall(int, lambda k: (Implies(
        0 <= k and k < len(ToSeq(Result())),
        ToSeq(Result())[k] == committed_value(
            ToSeq(original)[k], ToSeq(newvals)[k],
            any_fails(ToSeq(fails), 0))),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    # Apply the batch atomically: stage each row's replacement while walking the
    # forms, and only let the staged writes take effect if the whole batch
    # completes without a failure. A failure aborts the batch as a unit.
    failed = False
    i = 0
    while i < len(fails):
        # invariants-start
        Invariant(Acc(list_pred(original), 1 / 2))
        Invariant(Acc(list_pred(newvals), 1 / 2))
        Invariant(Acc(list_pred(fails), 1 / 2))
        Invariant(len(original) == len(newvals))
        Invariant(len(original) == len(fails))
        Invariant(0 <= i and i <= len(fails))
        # `failed` records whether any edit in the prefix already walked failed;
        # equivalently the not-yet-walked tail decides the rest of the verdict.
        Invariant(failed == (any_fails(ToSeq(fails), 0) and not any_fails(ToSeq(fails), i)))
        Invariant(Implies(not failed, any_fails(ToSeq(fails), 0) == any_fails(ToSeq(fails), i)))
        Invariant(MustTerminate(len(fails) - i + 1))
        # invariants-end
        if fails[i] == 1:
            # This edit's processing raises: the batch fails as a whole and the
            # grouped writes are discarded.
            failed = True
            break
        i = i + 1
    Assert(failed == any_fails(ToSeq(fails), 0))
    # Commit: replacement values iff the batch fully succeeded, otherwise the
    # original values (rollback). The same verdict applies to every row.
    result = []  # type: List[int]
    j = 0
    while j < len(original):
        # invariants-start
        Invariant(Acc(list_pred(original), 1 / 2))
        Invariant(Acc(list_pred(newvals), 1 / 2))
        Invariant(Acc(list_pred(fails), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(original) == len(newvals))
        Invariant(len(original) == len(fails))
        Invariant(0 <= j and j <= len(original))
        Invariant(failed == any_fails(ToSeq(fails), 0))
        Invariant(len(ToSeq(result)) == j)
        Invariant(Forall(int, lambda k: (Implies(
            0 <= k and k < j,
            ToSeq(result)[k] == committed_value(
                ToSeq(original)[k], ToSeq(newvals)[k],
                any_fails(ToSeq(fails), 0))),
            [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(len(original) - j + 1))
        # invariants-end
        old_seq = ToSeq(result)
        if failed:
            result = result + [original[j]]
        else:
            result = result + [newvals[j]]
        Assert(ToSeq(result) == old_seq + PSeq(committed_value(
            ToSeq(original)[j], ToSeq(newvals)[j], any_fails(ToSeq(fails), 0))))
        # The new element lands at index j; the prefix 0..j-1 is unchanged.
        Assert(ToSeq(result)[j] == committed_value(
            ToSeq(original)[j], ToSeq(newvals)[j], any_fails(ToSeq(fails), 0)))
        Assert(Forall(int, lambda k: (Implies(
            0 <= k and k < j, ToSeq(result)[k] == old_seq[k]),
            [[ToSeq(result)[k]]])))
        j = j + 1
    return result
    # impl-end
