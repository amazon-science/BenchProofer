"""Twin-artifact model for django__django-13346.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test against a stored-collection key must, on the relevant
  backends, compare each candidate value through the SAME per-value form that a
  direct equality test against the key already uses. The comparison string
  produced for a membership test of N candidate values is the comma-space
  joined list of N per-value comparison slots, and every slot must be the
  per-value comparison form (an opaque backend-specific token that surrounds
  the bind placeholder, given below as a code-point literal) — NOT the bare
  bind placeholder.

  The desired behaviour, derived from the problem statement (a single-element
  membership test `key__in=[v]` must select exactly the rows that the direct
  test `key=v` selects, rather than a disjoint or empty set), is: the produced
  comparison string is the per-slot expansion in which every one of the N
  candidate slots is the per-value comparison form, the slots joined by the
  comma-space separator, with no slot left as the bare placeholder. The bind
  parameters themselves are unchanged.

The comparison string is modelled as `List[int]` of code points (Nagini bans
`str` indexing); the specification is carried by `PSeq[int]`. The right-hand
side is modelled as a list of value slots; the per-slot form is spelled out
deeply as a front-recursive fold (`slots_sql`). The unchanged base-class
placeholder production (one bare placeholder per value, comma-joined) is the
type-refinement boundary documented in mapping.md; the per-value comparison
form is a constant backend token spelled out below as an opaque code-point
literal, not a callee the proof axiomatizes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The base-class
#  placeholder string -- one bind placeholder per value, comma-joined -- is a
#  type refinement documented in mapping.md, NOT an axiom. The per-value
#  comparison form is a constant backend token spelled out below as an opaque
#  code-point literal, not a function whose behaviour the proof must
#  over-approximate.)
# axioms-end


# pure-start
@Pure
def sep() -> PSeq[int]:
    # ', '  -- the separator between comparison slots
    return PSeq(44, 32)


@Pure
def wrapped_slot() -> PSeq[int]:
    # The per-value comparison form: an opaque backend constant (constant code
    # points) that every slot must take. Its content is load-bearing for the
    # proof; its textual meaning is deliberately not narrated here.
    return PSeq(74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                40, 37, 115, 44, 32, 39, 36, 39, 41)


@Pure
def bare_slot() -> PSeq[int]:
    # The bare bind placeholder -- a slot in the un-formed shape. A slot left in
    # this shape is exactly the slot that the desired behaviour forbids.
    return PSeq(37, 115)


@Pure
def slots_sql(n: int) -> PSeq[int]:
    """The comparison string for `n` value slots: the per-value comparison form
    (`wrapped_slot`) repeated `n` times, joined by `sep` (', '). Front-recursive
    so a single unfold is available to callers per step.

    n == 0 -> empty; n == 1 -> one formed slot; n >= 2 -> formed slot then
    separator then the rest.
    """
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    if n == 1:
        return wrapped_slot()
    return wrapped_slot() + sep() + slots_sql(n - 1)
# pure-end


def process_membership_rhs(num_values: int) -> List[int]:
    # pre-conditions-start
    # `num_values` is the count of right-hand-side values (>= 1: an empty
    # membership set never reaches comparison-string production).
    Requires(num_values >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The comparison string is the per-slot expansion in which EVERY one of the
    # num_values slots is the per-value comparison form (`wrapped_slot`), joined
    # by the comma-space separator -- no slot is left as a bare bind placeholder.
    Ensures(ToSeq(Result()) == slots_sql(num_values))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        # `result` already holds the expansion of the trailing `num_values - i`
        # slots (built back-to-front so the front-recursive slots_sql unfolds
        # one slot per step).
        Invariant(ToSeq(result) == slots_sql(num_values - i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            # Last slot: no trailing separator.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            # Earlier slot: wrapped slot, then separator, then the rest.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result
    # impl-end
