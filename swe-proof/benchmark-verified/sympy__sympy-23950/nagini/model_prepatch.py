"""Twin-artifact model for sympy__sympy-23950.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership assertion is the proposition that a given element belongs to a
  given region (a set of values). Such an assertion has a canonical
  "set-of-values" view: the region of values for which the asserted membership
  is the stated one. For the assertion that ``element`` lies in ``region``, that
  view is exactly ``region`` itself — the very region whose membership the
  assertion is about.

  The behaviour pinned here: the set-of-values view of a membership assertion
  RETURNS NORMALLY (it is always defined for a single-element assertion) and the
  value it returns IS the region component of the assertion — not the element
  component, and not some freshly built object. Returning the region is what
  makes the view itself a region (so that, in turn, it supports the operations
  every region supports); a view that fails to produce the region — by deferring
  instead of returning, or by returning the element — is never permitted.

  Producing the view is a single bounded component selection: the operation
  MUST terminate and deliver its result (a total-correctness obligation,
  carried as ``MustTerminate`` in the precondition). An implementation that
  diverges before returning — e.g. by re-invoking the view on the same
  assertion, or spinning in a loop — would satisfy the value postconditions
  only vacuously and never deliver the view; the real operation always
  completes.

A membership assertion is modelled as a minimal class carrying only its two
touched components: the asserted ``element`` and the ``region`` it is asserted
to lie in, each an object reference (the payload of each component is irrelevant
to the view behaviour under specification). The returned view is required to be
the very ``region`` reference, identified by Nagini object identity (``is``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ViewNotProduced(Exception):
    """A deferral signal: declining to produce the set-of-values view (signalling
    "not yet defined") instead of returning the region. The specification forbids
    it — the view must always return the region for a single-element assertion —
    so no `Exsures` admits it (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""


class Region:
    """A region of values (a set), abstracted to an opaque object reference: the
    view behaviour under specification inspects no payload of the region, only
    which component object is returned."""

    def __init__(self) -> None:
        Ensures(True)


class MembershipAssertion:
    """The proposition that ``element`` belongs to ``region``, abstracted to its
    two touched components: the asserted element and the region it is asserted to
    lie in. Both are opaque object references; only which one the view returns is
    observable."""

    def __init__(self, element: Region, region: Region) -> None:
        Ensures(Acc(self.element, 1 / 2) and self.element is element)   # type: ignore
        Ensures(Acc(self.region, 1 / 2) and self.region is region)       # type: ignore
        self.element = element
        self.region = region


# axioms-start
# (no @ContractOnly axioms: the view is a direct selection of a stored component
#  object, modelled deeply as object-identity reasoning over the abstracted
#  components — see refinement.md, every row is R or I. No unchanged opaque
#  callee is consumed.)
# axioms-end


# pure-start
# (no @Pure helpers: the behaviour is a single component selection, expressed
#  directly in the contract.)
# pure-end


def solution_region(self: MembershipAssertion) -> Region:
    # pre-conditions-start
    # Read-only: the assertion is not mutated, so its components are held at
    # fractional permission (required and ensured) — directive 5.
    Requires(Acc(self.element, 1 / 2))
    Requires(Acc(self.region, 1 / 2))
    # Producing the view is a single bounded component selection: the operation
    # MUST terminate (total correctness). A diverging body — e.g. one that
    # re-invokes solution_region on the same assertion — satisfies the value
    # postconditions only vacuously and never delivers the view; measure 2
    # leaves no budget for a same-measure self-call.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.element, 1 / 2))
    Ensures(Acc(self.region, 1 / 2))
    # The view returns normally and the value it returns IS the region component
    # of the assertion — the very object asserted to contain the element.
    Ensures(Result() is self.region)
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: declines to produce the view (deferral) instead of
    # returning the region — so the spec's normal-return postcondition is never
    # established. (Reproduces the pre-patch "not yet defined" behaviour.)
    raise ViewNotProduced()
    # impl-end
