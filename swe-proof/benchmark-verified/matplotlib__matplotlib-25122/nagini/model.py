"""Twin-artifact model for matplotlib__matplotlib-25122.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a windowed segment of a signal is turned into a spectral estimate, the
  estimate is divided by a normalisation factor that compensates for the energy
  the analysis window removes. Two such normalisation factors are formed from
  the window's per-sample weights:

    (1) the AMPLITUDE normalisation -- the running total of the window's
        per-sample weights, taken with their sign. A window weight may be
        negative, and a negative weight must SUBTRACT from the total: the factor
        is the algebraic sum of the weights, NOT the sum of their magnitudes.
        (For a window that dips below zero these two totals disagree; the
        algebraic sum is the correct one.)

    (2) the POWER normalisation -- the running total of the SQUARES of the
        window's per-sample weights. Because squaring discards sign, this total
        is unaffected by whether each weight is taken with its sign or by its
        magnitude: the two readings of (2) always coincide.

  The desired behaviour: factor (1) is the signed running total of the weights;
  factor (2) is the running total of their squares. The amplitude factor is the
  locus that a window with negative weights makes observable.

The window weights are modelled as `List[int]` (the specification is carried by
`PSeq[int]`): the distinguishing behaviour is purely a question of SIGN
handling in the running total -- whether a negative weight subtracts or its
magnitude is added -- which is independent of the weights' real magnitudes, so
signed integers (which already carry both signs) are a faithful, precision-free
carrier (refinement.md states the bijection). The two totals are spelled out as
front-recursive folds so a single unfold is available per loop step.

Each divisor is a bounded, straight-line reduction over one window and MUST
terminate and actually DELIVER its total to the caller (a total-correctness
obligation, carried as ``MustTerminate`` in the preconditions). Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation (e.g. an unbounded loop before the return)
satisfies every ``Ensures`` vacuously; the real normalisation divisor is
always computed and used by ``_spectral_helper``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: both normalisation totals are the changed operations
#  themselves and are modelled DEEPLY as spelled-out folds below; they are
#  validated == the real array reductions out-of-band by axiom_check.py / G-AX,
#  not consumed as @ContractOnly contracts.)
# axioms-end


# pure-start
@Pure
def signed_sum(w: PSeq[int]) -> int:
    """The signed (algebraic) running total of the window weights: each weight
    contributes with its own sign, so a negative weight subtracts. Front-
    recursive (one unfold per loop step)."""
    if len(w) == 0:
        return 0
    return w[0] + signed_sum(w.drop(1))


@Pure
def magnitude(x: int) -> int:
    """The magnitude of a single weight (its sign discarded)."""
    if x < 0:
        return -x
    return x


@Pure
def magnitude_sum(w: PSeq[int]) -> int:
    """The running total of the weight MAGNITUDES (each weight's sign discarded
    before adding). Coincides with `signed_sum` only when no weight is negative;
    it is the quantity the desired amplitude factor must NOT use."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) + magnitude_sum(w.drop(1))


@Pure
def square_sum(w: PSeq[int]) -> int:
    """The running total of the SQUARES of the window weights. Front-recursive."""
    if len(w) == 0:
        return 0
    return w[0] * w[0] + square_sum(w.drop(1))


@Pure
def magnitude_square_sum(w: PSeq[int]) -> int:
    """The running total of the squares of the weight MAGNITUDES."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) * magnitude(w[0]) + magnitude_square_sum(w.drop(1))


@Pure
def squares_are_sign_blind(w: PSeq[int]) -> bool:
    """Lemma: squaring discards sign pointwise, so the squared-weight total
    reads the same whether each weight is taken with its sign or by its
    magnitude. This pins WHY the power factor (2) is insensitive to the sign
    treatment. Always holds; proven by induction on the front of the sequence.
    """
    Ensures(Result())
    Ensures(square_sum(w) == magnitude_square_sum(w))
    if len(w) == 0:
        return True
    return squares_are_sign_blind(w.drop(1))
# pure-end


def amplitude_loss_divisor(window: List[int]) -> int:
    # pre-conditions-start
    # The window weights are read, never mutated: fractional permission.
    Requires(Acc(list_pred(window), 1 / 2))
    # TERMINATION: the divisor must actually ANSWER (deliver the signed total
    # to the normalisation) -- it is one bounded pass over the window. Nagini
    # is a partial-correctness verifier by default, so without this obligation
    # a non-terminating implementation (an unbounded loop before the return)
    # would satisfy the value postcondition vacuously; the real reduction
    # always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window), 1 / 2))
    # The amplitude normalisation factor is the SIGNED running total of the
    # window weights -- negative weights subtract. Grounded structurally in the
    # input weights via the spelled-out signed fold, not pinned to an oracle.
    Ensures(Result() == signed_sum(ToSeq(window)))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(window)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window), 1 / 2))
        Invariant(0 <= i and i <= len(window))
        Invariant(total == signed_sum(ToSeq(window).drop(i)))
        # the loop consumes the caller's termination obligation with a
        # strictly decreasing measure (i), discharging MustTerminate(2)
        # from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        weight = window[i - 1]
        Assert(ToSeq(window).drop(i - 1)[0] == weight)
        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
        total = weight + total
        i = i - 1
    return total
    # impl-end


def power_loss_divisor(window: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(window), 1 / 2))
    # TERMINATION: the divisor must actually ANSWER (deliver the squared total
    # to the normalisation) -- one bounded pass over the window; a diverging
    # implementation satisfies the value postconditions only vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window), 1 / 2))
    # The power normalisation factor is the running total of the SQUARED window
    # weights.
    Ensures(Result() == square_sum(ToSeq(window)))
    # Squaring is sign-blind, so this factor reads the same whether the weights
    # are taken with their sign or by their magnitude -- the power factor is not
    # the locus of the negative-weight observation.
    Ensures(square_sum(ToSeq(window)) == magnitude_square_sum(ToSeq(window)))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(window)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window), 1 / 2))
        Invariant(0 <= i and i <= len(window))
        Invariant(total == square_sum(ToSeq(window).drop(i)))
        # the loop consumes the caller's termination obligation with a
        # strictly decreasing measure (i), discharging MustTerminate(2)
        # from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        weight = window[i - 1]
        Assert(ToSeq(window).drop(i - 1)[0] == weight)
        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
        total = weight * weight + total
        i = i - 1
    Assert(squares_are_sign_blind(ToSeq(window)))
    return total
    # impl-end
