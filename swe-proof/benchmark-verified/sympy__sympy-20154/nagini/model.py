"""Twin-artifact model for sympy__sympy-20154.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An enumerator walks a sequence of states, advancing a single working value as
  it goes, and hands out one record per step. The desired contract is that the
  sequence of records HANDED OUT, when gathered into a list, faithfully records
  the state at the moment of each step:

    * record number i, once gathered, reflects the working state AS IT WAS at
      step i -- not as it later became;
    * because successive steps genuinely change the working state, the gathered
      records have pairwise-different values: gathering an n-step walk yields n
      records that increase step by step, recovering the full per-step history.

  The defective behaviour this rules out is handing out a live alias of the
  working state on every step, so that every gathered record tracks the SAME
  evolving state. Under that defect, once the walk has finished all gathered
  records read back as the FINAL state, and the per-step history is lost
  (gathering an n-step walk would yield n identical records).

Gathering an n-step walk is a bounded computation: the gather MUST terminate
and actually deliver its list of records (a total-correctness obligation,
carried as MustTerminate in the precondition). Nagini is a partial-correctness
verifier by default, so without the obligation a non-terminating
implementation would satisfy every value postcondition only vacuously and
would never hand the gathered records to the caller.

The working state is modelled by an integer; the gathered records by a
`List[int]` whose element i is the value recorded for step i (`str` indexing
and rich containers are unavailable in Nagini; the multiplicity mapping the
real enumerator maintains is abstracted to its per-step changing value). The
walk's value at step i is pinned by a pure spec function `state_at`, chosen
strictly increasing so successive steps genuinely differ -- which is exactly
what an aliasing enumerator (whose gathered records all collapse to the final
value) cannot reproduce. No callee is axiomatized: gathering the walk and
recording an independent per-step snapshot are pure value/structure logic,
modelled deeply (the real-Python record-duplication primitive the enumerator
builds on is validated out-of-band by axiom_check.py / G-AX as an A-reference).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: gathering the walk and recording an independent per-step
# snapshot are pure value/structure logic, modelled deeply. The
# record-duplication primitive the enumerator builds on is validated against
# its real Python semantics out-of-band by axiom_check.py (G-AX) as an
# A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def state_at(i: int) -> int:
    """The working value recorded for step i. Successive steps genuinely change
    it, so the per-step values are pairwise distinct; modelled as the
    strictly-increasing identity i+1 so step i differs from step j."""
    Requires(i >= 0)
    Ensures(Result() == i + 1)
    return i + 1
# pure-end


def gather_walk(steps: int) -> List[int]:
    # pre-conditions-start
    Requires(steps >= 0)
    # TERMINATION: the gather must actually ANSWER — walking a finite number
    # of steps and recording one value per step is a bounded computation.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (e.g. an endless loop)
    # satisfies every Ensures vacuously; the real gather always returns the
    # collected records to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The gather list is fully owned, holding one record per step.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == steps)
    # Record i recovers the working state AT ITS OWN step. Because state_at is
    # strictly increasing, the gathered records are pairwise different: this is
    # precisely the per-step history that an aliasing enumerator -- whose
    # gathered records all collapse onto the final state -- cannot satisfy.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(Result()),
        Result()[i] == state_at(i)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # The live working value the walk advances IN PLACE across steps: it starts
    # before the first step and is incremented one step at a time (never
    # recomputed from scratch), exactly as the enumerator advances its single
    # working record from one state to the next.
    work = 0
    i = 0
    while i < steps:
        # invariants-start
        Invariant(0 <= i and i <= steps)
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == i)
        # The working value carries the running state from the previous step.
        Invariant(work == i)
        # Every already-gathered record holds the snapshot of its own step --
        # an INDEPENDENT value that subsequent steps never disturb.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == state_at(k)))))
        # The loop consumes the termination obligation: steps - i is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(steps - i + 1))
        # invariants-end
        # Advance the working state in place by one step (the enumerator's
        # mutation step): the record now holds the state for step i.
        work = work + 1
        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
        # step): the current value is recorded by value, so later mutations of
        # the working state leave this gathered record untouched.
        snap = work
        result.append(snap)
        i = i + 1
    return result
    # impl-end
