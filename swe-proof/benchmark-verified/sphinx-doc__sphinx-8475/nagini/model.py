"""Twin-artifact model for sphinx-doc__sphinx-8475.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reachability probe for a single network locator first attempts a light
  probe form, then -- if that light probe fails in a way that some servers
  exhibit only for the light form -- falls back to a full probe form. The
  outcome the surrounding reporter observes is an OUTCOME KIND:

    0  the probe succeeded (the reporter records the locator as reachable);
    1  the probe failed with a status-level error;
    2  the probe failed because the light form was bounced through an
       unbounded chain of relocations (a failure mode produced ONLY by the
       light form on certain servers -- the full form does not loop);
    3  the probe failed for any other reason.

  The desired behaviour: the light probe is retried with the full probe
  whenever the light probe fails with EITHER a status-level error (kind 1) OR
  an unbounded-relocation failure (kind 2) -- both are failure modes a server
  may exhibit for the light form yet not for the full form, so the full form is
  the authoritative outcome. Any OTHER light-probe failure (kind 3) is taken as
  authoritative and is NOT retried.

  Consequently, for a locator whose light probe is bounced through an unbounded
  relocation chain (kind 2) but whose full probe succeeds, the observed outcome
  is success (kind 0), NOT the unbounded-relocation failure -- the locator is
  recorded as reachable.

The outcome of each probe form is modelled as an integer OUTCOME KIND in
{0,1,2,3} (an abstraction of the response-or-raised-condition the real probe
produces); the function returns the effective outcome kind handed to the
reporter. No callee is axiomatized: the retried-failure classification is the
operation under specification and is modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def is_retryable(kind: int) -> bool:
    """A light-probe outcome kind is retried with the full probe iff it is a
    status-level error (kind 1) OR an unbounded-relocation failure (kind 2):
    both are failure modes that the light form may show yet the full form may
    not, so the full form's outcome is authoritative. Every other failure
    (kind 3) is taken as authoritative and not retried."""
    return kind == 1 or kind == 2
# pure-end


def probe_outcome(head_kind: int, get_kind: int) -> int:
    # pre-conditions-start
    # head_kind / get_kind are the outcome kinds (0=success, 1=status error,
    # 2=unbounded-relocation, 3=other) of the light and full probe forms.
    Requires(0 <= head_kind and head_kind <= 3)
    Requires(0 <= get_kind and get_kind <= 3)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # If the light probe already succeeds, that is the outcome (no full probe).
    Ensures(Implies(head_kind == 0, Result() == 0))
    # If the light probe fails with a RETRYABLE kind (status error OR unbounded
    # relocation), the effective outcome is the FULL probe's outcome -- so a
    # locator bounced through an unbounded relocation chain on the light form
    # but reachable on the full form is reported as reachable (Result()==0
    # whenever get_kind==0), not as the failure.
    Ensures(Implies(head_kind != 0 and is_retryable(head_kind), Result() == get_kind))
    # A non-retryable light-probe failure (kind 3) is authoritative: it is the
    # effective outcome and the full probe is never consulted.
    Ensures(Implies(head_kind != 0 and not is_retryable(head_kind), Result() == head_kind))
    # The effective outcome is always one of the two probes' kinds (no
    # invented outcome), hence still in range.
    Ensures(Result() == head_kind or Result() == get_kind)
    Ensures(0 <= Result() and Result() <= 3)
    # post-conditions-end
    # impl-start
    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
    # light probe failed with a retryable kind (is_retryable is false for a
    # success, kind 0); otherwise the light-probe outcome (a success, or a
    # non-retryable failure) stands.
    if is_retryable(head_kind):
        result = get_kind
    else:
        result = head_kind
    return result
    # impl-end
