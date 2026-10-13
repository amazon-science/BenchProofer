"""Twin-artifact model for django__django-15563.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a row in a concrete multi-table-inheritance tree is updated and the
  update touches fields living on more than one ancestor table, the engine
  first collects, for every ancestor it must touch, the set of primary-key
  values that identify the ancestor rows to change. Those values are read out
  of a single pre-selection that returns several columns per source row.

  Two facts pin the behaviour:

  (1) Column assignment. The pre-selection always returns the source model's
      own primary key as its first column (column 0). For each ancestor that
      must be touched, if every link on the path up to that ancestor is itself
      a primary-key link (so the ancestor's identifying value coincides with
      the source row's own primary key), that ancestor reuses column 0;
      otherwise the ancestor needs its own identifying column, which is
      appended as a fresh column at a positive index (never column 0).

  (2) Projection. The identifying values used to constrain each ancestor's
      update are then read from THAT ancestor's assigned column of every source
      row — not uniformly from column 0. An ancestor whose identifying value
      is genuinely distinct from the source row's own primary key is therefore
      constrained by its own positive column, while a primary-key-chain
      ancestor reuses column 0.

Tables and per-target metadata are modelled with `List[int]` carriers and the
pure sequence theory `PSeq[int]`; a per-target boolean ("the whole path up to
this ancestor is a primary-key chain") is modelled as an `int` flag 0/1, the
value of the unchanged path-classification callee, validated out of band
(axiom_check.py / G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the per-target path classification is an
#  input flag, modelled as an A-reference and validated against the real callee
#  by axiom_check.py / G-AX; the column-assignment and projection logic is
#  modelled deeply below.)
# axioms-end


# pure-start
@Pure
def count_fresh(s: PSeq[int]) -> int:
    """Total number of fresh (non-reuse) targets in `s`, i.e. the count of
    indices m with `s[m] == 0`. Front-recursive over the sequence (peeling the
    head, one auto-unfold per loop step), so the value is uniquely pinned. This
    is the number of source columns appended beyond column 0 — the maximum
    fresh column index, and one less than the pre-selection row width."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    elif s[0] == 0:
        return 1 + count_fresh(s.drop(1))
    else:
        return count_fresh(s.drop(1))
# pure-end


def assign_columns(chain: List[int]) -> List[int]:
    """Assign each ancestor target the index of the pre-selection column whose
    values identify the rows to update (the column-assignment fact, item (1)).

    `chain[k]` is 1 when the path up to target k is a full primary-key chain
    (so target k's identifying value coincides with the source row's own
    primary key, column 0) and 0 otherwise."""
    # pre-conditions-start
    Requires(Acc(list_pred(chain), 1 / 2))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                           ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(chain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(chain))
    # A full primary-key-chain target reuses column 0; any other target is
    # placed in a fresh column strictly past column 0 (column index >= 1, i.e.
    # NEVER column 0). This biconditional is the heart of the behaviour: a
    # non-chain ancestor is constrained by its own column, never by the source
    # row's own primary key (column 0).
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                          (Result()[k] == 0) == (ToSeq(chain)[k] == 1))))
    # Dense running column index — the load-bearing fact. A non-chain ancestor's
    # column is read by the consumer as a PHYSICAL OFFSET into a source row whose
    # width is exactly 1 + (total fresh ancestors): column 0 is the source pk,
    # then exactly one column per fresh ancestor in target order. So the fresh
    # ancestor at index k occupies column 1 + (number of fresh ancestors strictly
    # before k). That prefix count is written here as
    #   count_fresh(chain) - count_fresh(chain[k:])
    # (total fresh minus the fresh from k onward). This EXACT pin forces the
    # fresh columns to be the contiguous block 1, 2, ..., F (F = count_fresh) —
    # dense, distinct, in-bounds. A merely "positive and strictly increasing"
    # assignment (e.g. sparse columns 2, 4, 6, ...) does NOT satisfy it: such an
    # index over-runs the row width and would read past the end of every source
    # row.
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(chain) and ToSeq(chain)[k] == 0,
                  Result()[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the pre-selection returns only the source model's own
    # primary key (a single column), and every ancestor update is constrained
    # by that one column. So every target is assigned column 0, regardless of
    # whether its path up to the ancestor is a primary-key chain.
    result = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i, result[k] == 0)))
        # invariants-end
        result = result + [0]
        i = i + 1
    return result
    # impl-end
