"""Twin-artifact model for scikit-learn__scikit-learn-14496.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A neighbourhood-size parameter may be given either as an absolute count or as
  a fraction of the number of samples. When it is given as a fraction, the
  repository first scales it by the number of samples — an ordinary,
  UNCHANGED floating-point multiplication that happens upstream of the
  behaviour under specification. What is under specification starts with that
  already-scaled value: it must be turned into a concrete neighbourhood SIZE, a
  whole-number count of samples. The size is the scaled value raised to a
  floor of two samples, and then reduced to a whole number that does not
  exceed that scaled-and-clamped value.

  The two properties that make the result a usable size are therefore:

    (1) it is a whole number (an integral value) -- a count of samples, never a
        fractional quantity; and
    (2) it is the largest whole number that is no greater than the
        scaled-and-clamped value (so it lies in the unit interval just below
        that value), and it is at least two.

  A fractional result is not a valid neighbourhood size: the downstream
  neighbour search counts samples and admits only whole-number sizes.

The model's input `scaled` is the scaled value EXACTLY as the repository
computed it. The repository's multiplication is a floating-point operation and
is not changed by the behaviour under specification, so it stays OUTSIDE the
model boundary; every value it can produce is an exact rational, carried here
losslessly as an interpreted real (verified with `--float-encoding=real`).
The reduction of that value to a whole number is the changed operation, so it
is modelled DEEPLY (a verified loop establishing the floor relation), never
axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the changed real-to-whole-number reduction is
#  modelled deeply, and the only other operation -- a real maximum against the
#  floor of two -- is spelled out as a @Pure helper below.)
# axioms-end


# pure-start
@Pure
def clamp_low(scaled: float) -> float:
    """The scaled value raised to a floor of two: it is at least two, it is
    no less than the scaled value, and it equals one of the two."""
    if scaled >= 2.0:
        return scaled
    return 2.0


@Pure
def is_whole(v: float) -> bool:
    """A real value is a whole number when it equals some integer."""
    return Exists(int, lambda k: v == k)
# pure-end


def neighborhood_size(scaled: float) -> float:
    # pre-conditions-start
    # `scaled` is the repository's already-computed product of a fractional
    # parameter in (0, 1] with the sample count (the absolute-count branch is
    # not under specification here). That product is strictly positive; no
    # other property of the upstream multiplication is assumed.
    Requires(scaled > 0.0)
    # pre-conditions-end
    # post-conditions-start
    # (1) The result is a whole number -- a count of samples, never fractional.
    Ensures(is_whole(Result()))
    # (2) It is at least two ...
    Ensures(Result() >= 2.0)
    # ... and it is the largest whole number no greater than the
    # scaled-and-clamped value: it does not exceed that value, and that
    # value is strictly below the next whole number. This pins the result to
    # the genuine floor of the scaled-and-clamped quantity.
    Ensures(Result() <= clamp_low(scaled))
    Ensures(clamp_low(scaled) < Result() + 1.0)
    # post-conditions-end
    # impl-start
    clamped = clamp_low(scaled)     # type: float
    # Reduce the value to the largest whole number not exceeding it.
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= clamped:
        # invariants-start
        Invariant(count >= 0)
        Invariant(acc <= clamped)
        Invariant(acc == count)
        # invariants-end
        count = count + 1
        acc = acc + 1.0
    return acc
    # impl-end
