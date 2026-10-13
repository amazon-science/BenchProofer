"""Twin-artifact model for scikit-learn__scikit-learn-13779.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ensemble meta-estimator holds a roster of named sub-estimators. Each entry
  of the roster is either ABSENT (a placeholder that has been cleared away and
  carries no sub-estimator at all) or PRESENT (it carries a real sub-estimator,
  which itself either does or does not accept per-sample weighting).

  When the caller supplies per-sample weights, the meta-estimator must first
  check that the configuration can honour them, by consulting each roster entry:

    * An ABSENT entry carries no sub-estimator, so there is nothing to consult.
      The capability probe — which inspects a sub-estimator's fitting interface —
      is meaningful ONLY for a present sub-estimator and must NOT be applied to an
      absent entry. An absent entry is simply skipped and can never, by itself,
      cause the check to fail or error.

    * A PRESENT entry is consulted via the capability probe. If the present
      sub-estimator does not accept per-sample weighting, the configuration
      cannot honour the supplied weights and the check rejects it.

  The behaviour pinned here: the weighted-fit pre-check returns normally exactly
  when every PRESENT sub-estimator accepts per-sample weighting (absent entries
  notwithstanding), and rejects (raises) exactly when some PRESENT sub-estimator
  does not. The probe is never consulted for an absent entry.

The roster is modelled as a `List[int]` of per-entry status tags: 0 = absent,
1 = present-and-accepts-weighting, 2 = present-and-rejects-weighting. The
capability probe is an unchanged callee the check invokes; it inspects a present
sub-estimator's interface, so it is meaningful only for a present entry — this is
encoded as its precondition (consulting it on an absent entry is out of contract,
exactly as the real probe dereferences an attribute that an absent entry lacks).
The rejection is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2). Nagini bans `str` indexing, so the
specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class WeightingUnsupported(Exception):
    """Signals a rejected weighted-fit configuration: some present sub-estimator
    does not accept per-sample weighting. Stands in for the `ValueError` the
    desired behaviour raises; a builtin exception in an `Exsures` crashes the
    Nagini translator (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def accepts_weighting(status: int) -> bool:
    """The capability probe applied to one roster entry: whether the carried
    sub-estimator accepts per-sample weighting. It inspects a PRESENT
    sub-estimator's fitting interface, so it is meaningful only for a present
    entry; consulting it on an absent entry is out of contract (the real probe
    dereferences an attribute an absent entry does not have). Hence its
    precondition admits only the present statuses {1, 2}, and it reports
    acceptance exactly on status 1. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(status == 1 or status == 2)
    Ensures(Result() == (status == 1))
# axioms-end


# pure-start
@Pure
def config_supports(roster: PSeq[int]) -> bool:
    """Whether the configuration can honour per-sample weights: every PRESENT
    entry accepts weighting. An absent entry (0) and a present-accepting entry
    (1) are both fine; only a present-rejecting entry (2) breaks support. Front-
    recursive over the sequence so a single unfold is available per loop step."""
    if len(roster) == 0:
        return True
    return roster[0] != 2 and config_supports(roster.drop(1))
# pure-end


def check_weighting_support(roster: List[int]) -> None:
    # pre-conditions-start
    # Every entry is a valid status tag: 0 absent, 1 present-accepts,
    # 2 present-rejects.
    Requires(Acc(list_pred(roster), 1 / 2))
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(roster),
                             0 <= roster[k] and roster[k] <= 2),
                     [[roster[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input: fractional permission, required and ensured (and returned
    # on the exceptional path too), so no caller can satisfy a postcondition
    # vacuously by overwriting the input.
    Ensures(Acc(list_pred(roster), 1 / 2))
    # Returns normally exactly when every PRESENT entry accepts weighting. Absent
    # entries are skipped: they do not appear in this condition.
    Ensures(config_supports(ToSeq(roster)))
    # Rejects (raises) exactly when some PRESENT entry does not accept weighting.
    Exsures(WeightingUnsupported,
            Acc(list_pred(roster), 1 / 2)
            and (not config_supports(ToSeq(roster))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the probe is consulted on EVERY entry, with no skip for
    # an absent entry. On an absent entry (status 0) the probe `accepts_weighting`
    # is invoked outside its contract (it admits only present statuses {1, 2}),
    # exactly as the real probe dereferences a fitting interface that an absent
    # entry lacks. Nagini reports the call-site precondition violation — the
    # formal face of the `'NoneType' object has no attribute 'fit'` crash.
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        # `supported` tracks support over the suffix already scanned.
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end
