"""Twin-artifact model for sympy__sympy-14711.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A free vector is a formal sum of components, each living in some component
  family (a "frame"); it is represented by a list of component-family tags.
  Adding a right operand to a left vector is defined as:

    (1) When the right operand is the additive identity (the scalar zero, the
        seed an iterated sum starts from), the sum is the left vector itself,
        unchanged: the component list of the result equals the component list of
        the left operand. This must hold and RETURN NORMALLY: the scalar zero is
        a permitted right operand, never rejected as a non-vector.

    (2) When the right operand is itself a vector, the sum is the re-normalised
        combination of BOTH operands' components: it equals the normal form of
        the two component lists concatenated together. Re-normalisation (the
        normal form) folds same-family components and drops a family whose
        combined contribution vanishes; it never invents a component. The result
        is the normal form of self's components followed by the other's
        components -- so the other operand's components are genuinely combined
        in, not discarded. (The result is NOT, in general, the verbatim
        concatenation: same-family components fold together and cancelling
        families disappear, so the list can only get shorter -- but it is the
        normal form of BOTH operands together, which is not the normal form of
        self alone unless the other operand contributes nothing.)

    (3) A right operand that is neither the scalar zero nor a vector is rejected
        (signalled as not-a-vector). Rejection is MANDATORY: a normal return is
        only permitted when the operand is the scalar zero or a genuine vector
        (clause (3a) in the postconditions) -- such an operand is never
        silently accepted.

A vector is modelled as a minimal class carrying only the touched facet, its
component list ``terms`` (``List[int]``: each entry is an opaque int tag
identifying the component family the term belongs to). The right operand is
modelled by two discriminators: ``is_scalar_zero`` (the additive identity) and
``is_vector`` (a genuine vector). The "operand must be a vector" guard is an
unchanged callee (``vector_guard``), axiomatized: it returns the operand when it
is a vector and signals ``NotAVector`` otherwise. The vector-constructing
normaliser is modelled by ``normal_form`` -- a deterministic, opaque function of
the WHOLE component list (equal lists give equal normal forms; lists that differ
are not provably equal). Its faithful "never grows the list" length bound and
its determinism are validated against the real constructor by axiom_check.py /
G-AX. The reject signal is a user-defined exception class (a builtin exception in
an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NotAVector(Exception):
    """Signals that an operand is not a vector. Stands in for the `TypeError`
    the unchanged operand guard raises (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


class Vec:
    """A vector, carrying only its component-family tag list. Construction is a
    NORMALISING operation: the stored list is the normal form of the input
    (same-family components folded together, a family whose combined contribution
    vanishes dropped), so it is not the verbatim input -- it can only get SHORTER
    (the constructor never invents a component), never longer."""
    def __init__(self, terms: List[int]) -> None:
        Requires(Acc(list_pred(terms), 1 / 2))
        # The normalising construction terminates. Level 2: strictly above
        # `normalise` (level 1), which this body calls.
        Requires(MustTerminate(2))
        Ensures(Acc(self.terms))  # type: ignore
        Ensures(Acc(list_pred(self.terms)))  # type: ignore
        Ensures(Acc(list_pred(terms), 1 / 2))
        # Normalising constructor: the stored list is the normal form of the
        # input; the merge/cancel can only shrink it.
        Ensures(ToSeq(self.terms) == normal_form(ToSeq(terms)))  # type: ignore
        Ensures(len(self.terms) <= len(terms))  # type: ignore
        self.terms = normalise(terms)  # type: List[int]


class Operand:
    """The right-hand operand of the sum. `is_scalar_zero` flags the additive
    identity; `is_vector` flags a genuine vector (carrying `terms`). An operand
    that is neither is an unsupported addend."""
    def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
        Requires(Acc(list_pred(terms), 1 / 2))
        # Two flag stores plus one list copy: terminating. Level 2 so the
        # `list(terms)` copy (which carries its own obligation) has room below.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
        Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
        Ensures(Acc(self.terms))  # type: ignore
        Ensures(Acc(list_pred(self.terms)))  # type: ignore
        Ensures(Acc(list_pred(terms), 1 / 2))
        Ensures(ToSeq(self.terms) == ToSeq(terms))  # type: ignore
        self.is_scalar_zero = is_scalar_zero
        self.is_vector = is_vector
        self.terms = list(terms)


# axioms-start
@Pure
@ContractOnly
def normal_form(s: PSeq[int]) -> PSeq[int]:
    """The vector-constructing normaliser as a deterministic pure function of
    the WHOLE component sequence (A-reference). It folds same-family components
    and drops a family whose combined contribution vanishes, so it never invents
    a component: the normal form is no longer than the input (and may be strictly
    shorter when families merge or cancel). Being a function, equal inputs give
    equal normal forms and inputs that differ are NOT provably equal -- so the
    normal form of BOTH operands' components together is not provably the normal
    form of self's components alone. G-AX validates the length bound and the
    determinism against the real constructor (mapping.md §3.2)."""
    Ensures(len(Result()) <= len(s))


@ContractOnly
def vector_guard(other: Operand) -> Vec:
    """The operand guard: returns the operand as a vector when it IS a vector,
    and signals `NotAVector` otherwise (the scalar zero is not a vector). The
    weakest contract the proof needs (mapping.md §3); G-AX runs the real callee
    against it."""
    Requires(Acc(other.is_vector, 1 / 2))
    Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    # The guard is a single isinstance test: bounded, loop-free work that either
    # returns or raises. Level 1, strictly below every caller.
    Requires(MustTerminate(1))
    Ensures(Acc(other.is_vector, 1 / 2))
    Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(other.is_vector)
    Ensures(Acc(Result().terms, 1 / 2))
    Ensures(Acc(list_pred(Result().terms), 1 / 2))
    Ensures(ToSeq(Result().terms) == ToSeq(other.terms))
    Exsures(NotAVector,
            Acc(other.is_vector, 1 / 2)
            and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
            and not other.is_vector)


@ContractOnly
def normalise(terms: List[int]) -> List[int]:
    """The vector-constructing normaliser (impl helper): builds a vector's
    stored component list from a raw concatenated component list by applying the
    `normal_form` merge. The stored list's contents are exactly the normal form
    of the input, and it is no longer than the input (the merge/cancel can only
    shrink it). G-AX validates this against the real constructor (mapping.md
    §3.2)."""
    Requires(Acc(list_pred(terms), 1 / 2))
    # The frame-merging normaliser walks its argument once and terminates.
    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
    Requires(MustTerminate(1))
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
    Ensures(len(Result()) <= len(terms))
# axioms-end


# pure-start
# (no module-level pure helpers required: the behaviour is stated directly over
# the component-family lists via ToSeq and the normal_form function.)
# pure-end


def vec_add(self: Vec, other: Operand) -> Vec:
    # pre-conditions-start
    Requires(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
    Requires(Acc(other.is_scalar_zero, 1 / 2))
    Requires(Acc(other.is_vector, 1 / 2))
    Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    # The scalar zero and a vector are distinct kinds of operand.
    Requires(Implies(other.is_scalar_zero, not other.is_vector))
    # The sum terminates. Level 3: strictly above vector_guard / normalise
    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
    # enough that the `list(self.terms)` copy has room below the caller.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
    Ensures(Acc(other.is_scalar_zero, 1 / 2))
    Ensures(Acc(other.is_vector, 1 / 2))
    Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(Acc(Result().terms, 1 / 4))
    Ensures(Acc(list_pred(Result().terms), 1 / 4))
    # (1) Adding the scalar zero returns the left vector unchanged (and returns
    #     NORMALLY for it: the scalar zero is a well-defined right operand).
    Ensures(Implies(other.is_scalar_zero,
                    ToSeq(Result().terms) == ToSeq(self.terms)))
    # (2) Adding a genuine vector yields the normal form of BOTH operands'
    #     components concatenated together: the result combines self's components
    #     WITH the other operand's components, then re-normalises (folds
    #     same-family components, drops a vanishing family). It is the normal form
    #     of self.terms ++ other.terms -- NOT the normal form of self alone (that
    #     would discard the other operand) and NOT the verbatim concatenation.
    Ensures(Implies(other.is_vector,
                    ToSeq(Result().terms)
                    == normal_form(ToSeq(self.terms) + ToSeq(other.terms))))
    # (3a) A NORMAL return happens ONLY for the scalar zero or a genuine
    #      vector: an operand that is neither MUST raise (clause (3) below) --
    #      the real guard raises TypeError on it, it is never silently
    #      accepted. Without this clause both Implies above are vacuous on the
    #      neither-operand state and a swallowing normal return would verify.
    Ensures(other.is_scalar_zero or other.is_vector)
    # post-conditions-end
    # (3) An operand that is neither the scalar zero nor a vector is rejected.
    Exsures(NotAVector,
            Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4)
            and Acc(other.is_scalar_zero, 1 / 2)
            and Acc(other.is_vector, 1 / 2)
            and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
            and not other.is_scalar_zero and not other.is_vector)
    # impl-start
    if other.is_scalar_zero:
        return self
    checked = vector_guard(other)  # type: Vec
    combined = list(self.terms)  # type: List[int]
    j = 0
    while j < len(checked.terms):
        # invariants-start
        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
        Invariant(Acc(other.is_scalar_zero, 1 / 2))
        Invariant(not other.is_scalar_zero)
        Invariant(Acc(other.is_vector, 1 / 2))
        Invariant(other.is_vector)
        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
        Invariant(Acc(list_pred(combined)))
        Invariant(0 <= j and j <= len(checked.terms))
        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
        # `j` rises by one per pass and the bound len(checked.terms) is fixed
        # (checked.terms is held read-only at 1/2 and never written), so
        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
        # j < len(checked.terms).
        Invariant(MustTerminate(len(checked.terms) - j + 1))
        # invariants-end
        combined.append(checked.terms[j])
        Assert(ToSeq(checked.terms).take(j + 1)
               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
        j = j + 1
    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
    result = Vec(combined)  # type: Vec
    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
    # function, so this is exactly clause (2).
    Assert(ToSeq(result.terms)
           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
    return result
    # impl-end
