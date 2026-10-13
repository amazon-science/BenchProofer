"""Twin-artifact model for matplotlib__matplotlib-24149.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A width-conversion helper picks one representative coordinate out of a
  non-empty sequence of coordinate values, used to anchor a unit-aware width
  addition. Each value is either finite or non-finite (a not-a-number /
  missing value). The representative is chosen as follows, and the choice must
  always succeed for a non-empty sequence:

    (1) If the sequence contains at least one finite value, the representative
        is the FIRST finite value (so a leading non-finite value is skipped in
        favour of a real coordinate). The representative is therefore finite.

    (2) If the sequence contains NO finite value at all (every value is
        non-finite), the representative is the FIRST value of the sequence
        unconditionally. The selection must still return a value in this case
        — an all-non-finite sequence yields a (non-finite) representative
        rather than failing — so that drawing an artifact whose coordinates
        are entirely non-finite remains a defined, total operation.

  The two coordinate sources fed to this helper (the original positions and
  their unit-converted form) are each selected by this same rule.

  Selection is a bounded, loop-free choice between two selectors: it MUST
  actually deliver the representative to its caller (total correctness,
  carried as a MustTerminate obligation in the preconditions). An
  implementation that diverges before returning would satisfy the value
  postconditions only vacuously and would never anchor the width addition.

A coordinate sequence is modelled as ``List[int]`` of per-element finiteness
flags (0 == the element is non-finite; non-zero == the element is finite). The
unchanged "first finite element" and "first element unconditionally" selectors
are axiomatized callees over ``PSeq[int]`` (their provenance + executable
soundness check live in mapping.md / axiom_check.py); the "is there any finite
element" predicate driving the choice is spelled out deeply as a front-recursive
fold (``any_finite``). The selection functions return the chosen flag.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def first_finite(s: PSeq[int]) -> int:
    """First finite element selector (unchanged community callee), restricted
    to the flag carrier. It returns a value only when a finite element exists;
    on a sequence with no finite element it does not return normally (the
    caller must guard that case). Weakest contract the proof needs: under the
    "some element is finite" precondition the returned value is THE first finite
    element of the sequence (which is therefore itself finite, i.e. non-zero) —
    the identity of the selected element, not merely the fact that it is finite.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(any_finite(s))
    Ensures(Result() == first_finite_value(s))


@Pure
@ContractOnly
def first_unconditional(s: PSeq[int]) -> int:
    """First element selector (unchanged community callee), restricted to the
    flag carrier. It returns the first element of a non-empty sequence
    unconditionally, regardless of finiteness. Weakest contract the proof needs:
    the returned flag equals the first element's flag.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(s) > 0)
    Ensures(Result() == s[0])
# axioms-end


# pure-start
@Pure
def any_finite(s: PSeq[int]) -> bool:
    """Whether the sequence contains at least one finite element (a flag that
    is non-zero). The empty sequence contains none (`False`). Front-recursive so
    one unfold is available to callers."""
    if len(s) == 0:
        return False
    return (s[0] != 0) or any_finite(s.drop(1))


@Pure
def first_finite_value(s: PSeq[int]) -> int:
    """The first finite element of the sequence — the leftmost element whose
    flag is non-zero — when one exists. Front-recursive over the input carrier
    (one unfold per leading non-finite element), so it is a structural function
    of the sequence itself, not an opaque oracle: it skips leading non-finite
    flags and yields the first finite one. Used to PIN the selected
    representative to the actual chosen element of the input (not merely to its
    finiteness)."""
    Requires(any_finite(s))
    if s[0] != 0:
        return s[0]
    return first_finite_value(s.drop(1))
# pure-end


def select_position_x0(seq: List[int]) -> int:
    """Pick the representative of the original-position coordinate sequence:
    the first finite value, or — when no value is finite — the first value
    unconditionally."""
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    Requires(len(seq) > 0)
    # TERMINATION: the selection is a bounded, loop-free choice between the
    # two selectors and MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body (e.g. an endless loop
    # before the return) satisfies the value postconditions only vacuously
    # yet never delivers the representative to the caller; the desired
    # selection always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # (1) when some value is finite, the representative is THE first finite
    #     value of the input — the actual selected element (identity), not just
    #     its finiteness. A constant of the asserted property (any finite flag)
    #     no longer discharges this: it must equal the input's own first finite
    #     element, which only the selector applied to the input produces.
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))
    # (2) when NO value is finite, the selection still returns a value: the
    #     first element unconditionally (which is itself non-finite). This is
    #     the total-selection guarantee the all-non-finite input demands.
    Ensures(len(ToSeq(seq)) == len(seq))
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
    # post-conditions-end
    # impl-start
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep
    # impl-end


def select_position_xconv(seq: List[int]) -> int:
    """Pick the representative of the unit-converted coordinate sequence by the
    same rule: the first finite value, or — when no value is finite — the first
    value unconditionally."""
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    Requires(len(seq) > 0)
    # TERMINATION: the selection is a bounded, loop-free choice between the
    # two selectors and MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body (e.g. an endless loop
    # before the return) satisfies the value postconditions only vacuously
    # yet never delivers the representative to the caller; the desired
    # selection always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # (1) when some value is finite, the representative is THE first finite
    #     value of the input — the actual selected element (identity), not just
    #     its finiteness. A constant of the asserted property (any finite flag)
    #     no longer discharges this: it must equal the input's own first finite
    #     element, which only the selector applied to the input produces.
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))
    # (2) when NO value is finite, the selection still returns a value: the
    #     first element unconditionally (which is itself non-finite).
    Ensures(len(ToSeq(seq)) == len(seq))
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
    # post-conditions-end
    # impl-start
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep
    # impl-end
