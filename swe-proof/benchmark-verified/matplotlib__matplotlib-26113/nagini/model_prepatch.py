"""Twin-artifact model for matplotlib__matplotlib-26113.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A two-dimensional binning routine groups input samples into a predetermined
  list of bins.  Each bin holds some number of samples; let that number be the
  bin's *occupancy*.  A minimum-occupancy threshold `t` decides, per bin,
  whether the bin is *populated* (it carries an aggregated value) or *cleared*
  (it carries the empty / missing marker and is later discarded).

  There are two accumulation regimes:

    * the bare-count regime, where each bin only knows its occupancy, and
    * the value-aggregation regime, where each bin additionally aggregates a
      per-sample payload.

  The desired behaviour is that the populated/cleared decision is *identical*
  in both regimes for one and the same threshold: a bin is populated iff its
  occupancy is at least the threshold.  In particular a threshold of one keeps
  exactly those bins that hold at least one sample, regardless of regime.

  Modeled domain: the documented positive-threshold regime (the routine
  documents its minimum-occupancy threshold as a positive integer; the
  behaviour under specification is observed at threshold one).  The
  unset-threshold default
  (threshold resolved to zero) is OUTSIDE the modeled boundary: there an
  *empty* bin passes the occupancy comparison,
  so whether it is observably populated additionally depends on the
  aggregator's value on an empty sample list (the default mean of an empty
  list is the missing marker — cleared — while a sum of an empty list is a
  real zero — populated), a payload-dependent effect the changed comparison
  does not pin and the occupancy-only abstraction cannot carry.  On the
  modeled domain (threshold >= 1) every bin passing the comparison holds at
  least one sample, the aggregate of a nonempty finite-payload sample list is
  a real value, and the populated decision is exactly the occupancy
  comparison in both regimes.

This bundle models that per-bin decision over a whole list of bins.  A bin is
described by its occupancy (an `int`); the result is the list of per-bin
populated-flags (a `List[bool]`).  The discriminating clause is that the
value-aggregation regime's decision (`decision_agg`) equals the bare-count
regime's decision (`decision_count`) for every bin.

The aggregation payload itself is an opaque passthrough irrelevant to the
decision, so the model carries only occupancies and decisions (no floats).
Each result element is pinned to the per-bin decision by an index-wise
postcondition.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms — the changed per-bin decision is modeled deeply below;
#  see refinement.md / mapping.md for the A-reference validated by axiom_check.py)
# axioms-end


# pure-start
@Pure
def decision_count(occ: int, t: int) -> bool:
    """Per-bin populated decision in the bare-count regime: a bin with the
    given occupancy is populated unless its occupancy falls below the
    threshold.  (i.e. populated iff occ >= t.)"""
    return not (occ < t)


@Pure
def decision_agg(occ: int, t: int) -> bool:
    """Per-bin populated decision in the value-aggregation regime: a bin is
    populated iff its occupancy reaches the threshold."""
    return occ >= t
# pure-end


def populated_bins(occupancies: List[int], threshold: int) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(occupancies), 1 / 2))
    # Modeled boundary: the documented positive-threshold regime (the
    # library documents the threshold as `int > 0`; the behaviour under
    # specification is observed at threshold one).  At threshold zero /
    # unset the observable
    # populated decision additionally depends on the aggregator's value on
    # an EMPTY sample list (default mean: missing marker; sum: real zero),
    # which the occupancy-only abstraction cannot carry — see module
    # docstring and mapping.md.
    Requires(threshold >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(occupancies), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(occupancies))
    # Each bin's result is the value-aggregation regime's per-bin decision,
    # which must equal the bare-count regime's decision for the same bin.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(occupancies),
                Result()[k] == decision_agg(occupancies[k], threshold) and
                Result()[k] == decision_count(occupancies[k], threshold))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(occupancies):
        # invariants-start
        Invariant(Acc(list_pred(occupancies), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(occupancies))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i,
                    result[k] == decision_agg(occupancies[k], threshold))))
        # invariants-end
        occ = occupancies[i]
        flag = occ > threshold
        result.append(flag)
        i = i + 1
    return result
    # impl-end
