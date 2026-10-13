"""Twin-artifact model for pydata__xarray-3151.

Behavioural contract (the result a correct interpretation must produce):

  After several datasets have been arranged and joined together, a final
  consistency guard inspects the global ordering of the combined result. The
  guard concerns the dimensions along which the datasets were actually joined:
  for each such dimension the combined coordinate must run monotonically (it
  may run either upward or downward). If any joined dimension's combined
  coordinate is non-monotonic, the guard rejects the result.

  Dimensions whose coordinate did NOT vary between the inputs (and so were
  carried through untouched, not joined along) are NOT subject to this guard.
  Such a carried-through coordinate is allowed to be in any order — including
  non-monotonic — because the join did not reorder it. The documented promise
  is that coordinate dimensions which do not vary between the inputs are left
  alone.

  Each dimension of the combined result is modelled by two parallel flags,
  indexed by dimension position:

    * `is_joined`    — whether the datasets were concatenated along this
                       dimension (i.e. its coordinate varied between inputs);
    * `is_monotonic` — whether this dimension's combined coordinate is
                       monotonic (increasing OR decreasing).

  The contract on the result (a boolean: whether the guard rejects), formalised
  by the `Ensures` clauses below:

    * the guard rejects exactly when some JOINED dimension is non-monotonic,
      i.e. `Result()` equals `any_joined_nonmonotonic(is_joined, is_monotonic)`;
    * equivalently, a non-monotonic dimension that was NOT joined along never
      causes rejection.

  The two flag lists are the type-refinement carrier of the combined result's
  dimensions and their inferred-order metadata; the unchanged monotonicity test
  on a single coordinate and the unchanged join machinery are the refinement
  boundary documented in mapping.md.

Dimensions are modelled as parallel `List[int]` of 0/1 flags (Nagini bans the
rich result object and `str` dimension names); the specification is carried by
`PSeq[int]` via `ToSeq`. The over-the-dimensions existential is spelled out as a
front-recursive `@Pure` fold so a single unfold is available per loop step.

The guard is a bounded scan over the finite dimension metadata: it MUST
terminate and actually ANSWER (return its verdict, so the caller can either
reject or hand the combined result on). This total-correctness
obligation is carried as `MustTerminate` in the precondition. Nagini is a
partial-correctness verifier by default, so without the obligation a
non-terminating implementation (e.g. a loop that never advances) satisfies
every `Ensures` vacuously; the real guard always completes its scan.

Note `any_joined_nonmonotonic` is FULLY GROUNDED in the two input carriers —
it is a computable existential over the flag lists, not an opaque answer-key
oracle. An implementation that returns it directly therefore computes the
correct verdict (it is a positive control, equivalent to the gold loop), not
an ungrounded echo.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The per-dimension
#  monotonicity test and the join machinery that produces the dimension
#  metadata are the refinement boundary, documented in mapping.md, not axioms.
#  The selection rule that decides WHICH dimensions the guard inspects is the
#  changed behaviour and is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def any_joined_nonmonotonic(is_joined: PSeq[int], is_mono: PSeq[int]) -> bool:
    """True iff some dimension that was joined along is non-monotonic.

    Front-recursive existential over the dimensions: a dimension contributes a
    violation iff it was joined along (`is_joined == 1`) AND its combined
    coordinate is non-monotonic (`is_mono == 0`). Carried-through dimensions
    (`is_joined == 0`) never contribute, regardless of their monotonicity.
    Front-recursive so a single unfold is available to the loop per step.
    """
    Requires(len(is_joined) == len(is_mono))
    if len(is_joined) == 0:
        return False
    head_violates = is_joined[0] == 1 and is_mono[0] == 0
    return head_violates or any_joined_nonmonotonic(is_joined.drop(1),
                                                    is_mono.drop(1))
# pure-end


def guard_rejects(is_joined: List[int], is_monotonic: List[int]) -> bool:
    # pre-conditions-start
    # The two flag lists are read-only metadata of the combined result, one
    # entry per dimension, aligned by position. Each flag is 0 or 1.
    Requires(Acc(list_pred(is_joined), 1 / 2))
    Requires(Acc(list_pred(is_monotonic), 1 / 2))
    Requires(len(is_joined) == len(is_monotonic))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_joined),
                                            is_joined[k] == 0 or is_joined[k] == 1),
                                     [[is_joined[k]]])))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_monotonic),
                                            is_monotonic[k] == 0 or is_monotonic[k] == 1),
                                     [[is_monotonic[k]]])))
    # TERMINATION: the guard is a bounded scan over the finite dimension
    # metadata and must actually ANSWER (return its verdict so the caller can
    # raise or proceed). Nagini is a partial-correctness verifier by default;
    # without this obligation a non-terminating implementation (e.g. a loop
    # that never advances) satisfies every Ensures vacuously. The real guard
    # always completes its scan.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_joined), 1 / 2))
    Ensures(Acc(list_pred(is_monotonic), 1 / 2))
    Ensures(len(ToSeq(is_joined)) == len(is_joined))
    Ensures(len(ToSeq(is_monotonic)) == len(is_monotonic))
    Ensures(len(ToSeq(is_joined)) == len(ToSeq(is_monotonic)))
    # The guard rejects exactly when some JOINED dimension is non-monotonic.
    Ensures(Result() == any_joined_nonmonotonic(ToSeq(is_joined),
                                                ToSeq(is_monotonic)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: inspect EVERY coordinate dimension present in the
    # combined result and reject if any is non-monotonic — without restricting
    # to the dimensions that were actually joined along. A carried-through
    # (bystander) coordinate that happens to be non-monotonic therefore
    # triggers a spurious rejection. Walk right-to-left as in model.py.
    rejected = False  # type: bool
    i = len(is_joined)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(is_joined), 1 / 2))
        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
        Invariant(len(is_joined) == len(is_monotonic))
        Invariant(0 <= i and i <= len(is_joined))
        Invariant(len(ToSeq(is_joined)) == len(is_joined))
        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                      ToSeq(is_monotonic).drop(i)))
        # discharge the termination obligation identically to model.py, so the
        # reject stays on the SPEC (the any_joined_nonmonotonic invariant), not
        # an obligation leak.
        Invariant(MustTerminate(i))
        # invariants-end
        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
        if is_monotonic[i - 1] == 0:
            rejected = True
        i = i - 1
    return rejected
    # impl-end
