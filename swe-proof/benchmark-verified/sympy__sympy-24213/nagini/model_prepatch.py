"""Twin-artifact model for sympy__sympy-24213.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the magnitude of a sum is reduced to its overall physical dimension, the
  dimensions contributed by the individual addends must agree.  The agreement
  that is required is *physical equivalence of dimensions*, NOT identity of the
  way a dimension happens to be written.

  Every dimension has a canonical reduction to a multiset of base dimensions
  raised to integer powers (its dimensional dependencies).  Two dimensions are
  physically equivalent exactly when these canonical reductions coincide, even
  if their surface descriptions differ (for instance a "velocity" written
  directly versus the same physical quantity written as "acceleration times
  time").  The reduction-to-base-dimensions step is the unchanged engine the
  comparison consults; its weakest relevant guarantees are that it is a genuine
  function of the dimension (equal surface descriptions reduce equally) and that
  it agrees with the engine the rest of the system already uses (validated
  against the real engine out-of-band by axiom_check.py / G-AX).

  Desired behaviour of reducing a sum's dimension:

    * If every addend's dimension is physically equivalent to the first
      addend's dimension, the reduction succeeds and reports the common
      dimension; the addends' magnitudes are combined.

    * If some addend's dimension is NOT physically equivalent to the first
      addend's dimension, the reduction is rejected (it signals a dimension
      mismatch).

  The point that matters: a later addend whose surface description differs from
  the first but whose canonical reduction is the same must be ACCEPTED, not
  rejected.  Rejection is driven by inequivalent canonical reductions, never by
  differing surface descriptions alone.

  Reducing a sum's dimension is a bounded pass over its finitely many addends:
  the operation MUST terminate, either returning the common dimension or
  signalling the mismatch (a total-correctness obligation, carried as
  MustTerminate in the precondition).  An implementation that diverges before
  returning or raising would satisfy the value postconditions only vacuously
  and would never deliver a verdict to the caller.

Modelling choices (Nagini fragment):
  * A dimension is modelled by two observable facets carried in parallel lists,
    one entry per addend of the sum:
      - ``red[i]`` (an ``int``): the identity of the dimension's canonical
        reduction to base dimensions.  Two dimensions are physically equivalent
        iff their reduction identities are equal; this is exactly what the
        equivalence test consults via the reduction engine.
      - ``surf[i]`` (an ``int``): the identity of the dimension's surface
        description, which a naive identity comparison consults.
    The engine is a genuine function of the surface description, so equal
    surface descriptions reduce equally: ``surf[i] == surf[j] ==> red[i] ==
    red[j]`` (the model's standing well-formedness assumption).  The converse
    does NOT hold -- two different surface descriptions may reduce to the same
    base dimensions -- and that is the discriminating case.
  * The reduction engine ``reduction_of`` is the unchanged callee; the
    equivalence test is the deep model ``equivalent`` (reduction identities
    equal).
  * The sum has at least one addend; the first establishes the reference
    dimension every other addend is compared against.

No string indexing is used (Nagini bans it).  List access under quantifiers is
guarded by explicit in-bounds conjuncts.  Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class DimensionMismatch(Exception):
    """Signalled when a sum mixes dimensions that are not physically
    equivalent (the rejection the reduction performs)."""
    pass


# axioms-start
@Pure
@ContractOnly
def reduction_of(surface: int) -> int:
    """The unchanged reduction engine: maps a dimension's surface description to
    the identity of its canonical reduction to base dimensions.  As a pure
    function it is automatically a genuine function of the surface description --
    the only guarantee the proof needs -- so a dimension always reduces the same
    way and the rest of the system's notion of "same base dimensions" is shared.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX)."""
    pass
# axioms-end


# pure-start
@Pure
def equivalent(red_a: int, red_b: int) -> bool:
    """Physical equivalence of two dimensions: their canonical reductions to
    base dimensions coincide.  The reductions are obtained from the surface
    descriptions via the reduction engine; equivalence consults the reductions
    ONLY -- never the surface descriptions directly.  This is the whole content
    of the comparison the desired behaviour requires."""
    return red_a == red_b
# pure-end


def collect_sum_dimension(surf: List[int], red: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(surf), 1 / 2))
    Requires(Acc(list_pred(red), 1 / 2))
    # The two facets describe the same addends, and there is at least one.
    Requires(len(surf) == len(red))
    Requires(len(surf) >= 1)
    # The reduction engine is a genuine function of the surface description:
    # each addend's reduction identity is what the engine yields for its
    # surface description.
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(surf),
                                            red[i] == reduction_of(surf[i])))))
    # Reducing a sum's dimension is a bounded pass over its finitely many
    # addends: the operation MUST terminate, either returning the common
    # dimension or signalling the mismatch (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously and
    # would never deliver a verdict to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(surf), 1 / 2))
    Ensures(Acc(list_pred(red), 1 / 2))
    Ensures(len(surf) == len(red) and len(red) >= 1)
    # Success path: the reduction reports the common reduction identity, which
    # it reaches exactly when EVERY addend is physically equivalent to the first
    # (equal canonical reduction), regardless of differing surface descriptions.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(red),
                                           red[i] == red[0]))))
    Ensures(Result() == red[0])
    # Rejection path: signalled exactly when some addend is NOT physically
    # equivalent to the first (its canonical reduction differs).
    Exsures(DimensionMismatch,
            Acc(list_pred(surf), 1 / 2) and Acc(list_pred(red), 1 / 2) and
            len(surf) == len(red) and len(red) >= 1 and
            Exists(int, lambda i: (0 <= i and i < len(red) and red[i] != red[0])))
    # post-conditions-end
    # impl-start
    # Pre-patch (buggy) skeleton: rejection is driven by the SURFACE
    # descriptions -- a naive identity comparison of how each dimension is
    # written -- rather than by the canonical reductions.  Two addends that are
    # physically equivalent but written differently are therefore rejected.
    i = 1
    while i < len(surf):
        # invariants-start
        Invariant(Acc(list_pred(surf), 1 / 2))
        Invariant(Acc(list_pred(red), 1 / 2))
        Invariant(len(surf) == len(red))
        Invariant(len(surf) >= 1)
        Invariant(1 <= i and i <= len(surf))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 surf[k] == surf[0]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                 red[k] == reduction_of(surf[k])))))
        # the addend loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(surf) - i), discharging
        # MustTerminate(2) from the precondition; the prepatch must keep
        # failing on the SPEC (the Exsures), not on an obligation leak.
        Invariant(MustTerminate(len(surf) - i + 1))
        # invariants-end
        # Reject iff this addend's surface description differs from the first.
        if surf[i] != surf[0]:
            raise DimensionMismatch()
        i = i + 1
    return red[0]
    # impl-end
