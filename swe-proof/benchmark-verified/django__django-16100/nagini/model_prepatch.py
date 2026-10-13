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
    # Pre-fix behaviour: the edits are NOT grouped. Each edit is applied (and
    # persisted) one at a time while the batch is walked; when an edit fails the
    # walk stops, but every replacement already applied before the failure has
    # ALREADY taken effect and stays in the store. So on a mid-batch failure the
    # committed store carries the replacement values for the rows processed
    # before the failure and the original values from the failing row onward — a
    # partial result, NOT all-or-nothing.
    result = []  # type: List[int]
    failed = False
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
        Invariant(len(ToSeq(result)) == j)
        Invariant(MustTerminate(len(original) - j + 1))
        # invariants-end
        if failed:
            # The batch already stopped at an earlier failure; rows from there
            # on were never reached, so they keep their original value.
            result = result + [original[j]]
        elif fails[j] == 1:
            # This edit fails: it does not apply, and the walk stops here.
            result = result + [original[j]]
            failed = True
        else:
            # This edit succeeds and is committed immediately (no grouping).
            result = result + [newvals[j]]
        j = j + 1
    return result
    # impl-end
