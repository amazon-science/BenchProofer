"""Twin-artifact model for django__django-11603.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A family of summary-computation constructors share a common construction
  prologue. The prologue takes a *deduplicate* request (a boolean asking that
  repeated input values be collapsed before the summary is computed) together
  with a per-family *capability* flag stating whether that family is permitted
  to honour deduplication. The prologue's decision is:

    * if deduplication is requested by a family that is NOT permitted to honour
      it, the constructor refuses — it signals the caller with a capability
      error instead of building the object; otherwise
    * the constructor proceeds and records the deduplicate request as the
      object's state, so that a later request reads back exactly what was asked.

  The behaviour pinned here is which families are permitted to honour the
  deduplicate request. Two specific families — the arithmetic-mean family and
  the running-total family — MUST be permitted to honour it: constructing
  either with deduplication requested must succeed and record the request,
  never refuse. (A third family, the plain tally, was already permitted.)
  Families with the capability disabled must still refuse a deduplicate
  request.

The deduplicate request and the capability flag are plain booleans; no string
or heap modelling is needed. The capability error is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator). The
shared prologue is modelled deeply as its own contracted function; each family
constructor is modelled as a separate function that invokes the prologue with
its family's capability flag, so the per-family capability is the discriminating
datum.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CapabilityError(Exception):
    """Signals that the requested deduplication is not permitted for this
    family. Stands in for the `TypeError` the desired behaviour raises (a
    builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the shared prologue is modelled deeply as
# construct_dedup below; the only operations the family constructors perform
# that this specification observes are that prologue's decision and the state
# it records. Everything else the real constructor delegates to is unchanged,
# independent of the capability/deduplicate decision, and unobserved here.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the decision is a boolean predicate
# stated inline in the contracts.)
# pure-end


def construct_dedup(allow_dedup: bool, dedup: bool) -> bool:
    # pre-conditions-start
    # Both inputs are plain booleans (no heap permission needed). `allow_dedup`
    # is the per-family capability; `dedup` is the caller's deduplicate request.
    # TERMINATION: the prologue is a bounded, loop-free decision — every call
    # either returns the recorded request or raises the capability error; it
    # never diverges. The strictly smaller measure (1 < 2) lets a family
    # constructor holding MustTerminate(2) invoke the prologue without leaking
    # its own obligation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY when the request is honourable: either no
    # deduplication was requested, or the family is permitted to honour it.
    Ensures(dedup is False or allow_dedup is True)
    # When the constructor proceeds, the recorded state is EXACTLY the request
    # that was made (read-back fidelity).
    Ensures(Result() == dedup)
    # The capability error is raised on EXACTLY the refused case: a deduplicate
    # request from a family that is not permitted to honour it.
    Exsures(CapabilityError, dedup is True and allow_dedup is False)
    # post-conditions-end
    # impl-start
    if dedup and not allow_dedup:
        raise CapabilityError()
    stored = dedup
    return stored
    # impl-end


def build_mean(dedup: bool) -> bool:
    # pre-conditions-start
    # `dedup` is the caller's deduplicate request for the arithmetic-mean family.
    # TERMINATION: constructing the family object is bounded straight-line work
    # and MUST actually complete (total correctness). Under partial-correctness
    # semantics a diverging body (e.g. an endless loop before the return)
    # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
    # the constructed object to its caller; the real constructor always
    # returns. This obligation rejects any such implementation.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # The arithmetic-mean family MUST honour a deduplicate request: construction
    # always succeeds (no Exsures clause => never raises) and records the
    # request exactly, for EVERY value of `dedup` including a request to
    # deduplicate.
    Ensures(Result() == dedup)
    # post-conditions-end
    # impl-start
    return construct_dedup(True, dedup)
    # impl-end


def build_total(dedup: bool) -> bool:
    # pre-conditions-start
    # `dedup` is the caller's deduplicate request for the running-total family.
    # TERMINATION: constructing the family object is bounded straight-line work
    # and MUST actually complete (total correctness). Under partial-correctness
    # semantics a diverging body (e.g. an endless loop before the return)
    # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
    # the constructed object to its caller; the real constructor always
    # returns. This obligation rejects any such implementation.
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # The running-total family MUST honour a deduplicate request: construction
    # always succeeds (no Exsures clause => never raises) and records the
    # request exactly, for EVERY value of `dedup` including a request to
    # deduplicate.
    Ensures(Result() == dedup)
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the running-total family as it stood before the
    # change — it does NOT carry the capability, so it invokes the shared
    # prologue with the capability DISABLED. A deduplicate request then takes
    # the refusing branch and raises, violating Ensures(Result() == dedup)
    # (the function declares no Exsures, so it must always return normally).
    # This module MUST FAIL verification (G-DIFF).
    return construct_dedup(False, dedup)
    # impl-end
