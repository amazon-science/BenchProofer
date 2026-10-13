"""Twin-artifact model for django__django-13023.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A field-level coercion turns an externally-supplied value into the field's
  canonical numeric form. The coercion recognises three benign shapes of input
  directly: an absent value (passed straight through), a value already in
  floating form (converted through the field's rounding context), and any other
  value that the canonical numeric constructor accepts. For a value the
  constructor cannot accept, the coercion must report a single, uniform
  *validation* failure to its caller.

  The coercion reaches that constructor only for a value it did NOT route to
  the floating conversion. Those are two DISTINCT callees with distinct
  behaviour, and the coercion's uniform-failure obligation is placed around the
  constructor only: the floating conversion is invoked outside it. A value the
  coercion routes to the floating conversion but which that conversion will not
  accept therefore has its low-level error reach the caller unchanged, exactly
  as for the unclassified constructor shape below. The floating conversion has
  TWO such refusals, not one, and they are distinct low-level classes: it
  refuses a value that is not one of the operand types it converts, and it
  separately refuses a value it does accept as an operand but whose magnitude
  its own rounding context cannot represent. Both escape the coercion.

  The behaviour pinned here is the uniformity of that failure across the
  rejection shapes the coercion classifies. The underlying numeric constructor
  rejects an unacceptable value in one of several distinct ways depending on the
  value's shape (some shapes it reports as a malformed numeric literal, others
  as a wrong-typed operand, others as an out-of-domain argument). Regardless of
  WHICH of those ways the constructor chose, the coercion must surface the SAME
  validation failure to its caller: none of those rejection shapes may escape as
  the constructor's own low-level error.

  The coercion's classification is not exhaustive over the rejection space of
  the callees it invokes, and this spec does not pretend otherwise. The
  constructor has a further rejection shape — it reports that a component of
  the value lies outside the internal range its representation can hold — that
  the coercion does NOT classify. On that shape the constructor's own low-level error
  propagates to the caller unchanged; the coercion neither converts it to the
  validation failure nor returns normally. Stating this is what keeps the spec's
  claim equal to the real coercion's guarantee rather than stronger than it: the
  uniform-failure obligation is total over the classified shapes and silent
  nowhere.

  Only genuinely acceptable inputs return normally: absent, floating-and-
  convertible, or constructor-accepted. A value the floating conversion refuses
  — as a wrong-typed operand, or as an operand out of its context's
  representable range — does NOT return normally either, even though the
  coercion routed it to the floating branch.

The supplied value is modelled abstractly by an integer *acceptance kind* (a
stable tag per distinct rejection/acceptance shape); Nagini bans `str` indexing
and the discriminating observable is purely WHICH outcome the coercion produces,
not the value's characters. The canonical numeric constructor is an unchanged
callee the coercion invokes; it is axiomatised, and its several distinct
rejections are user-defined exception classes (a builtin exception in an
`Exsures` crashes the translator). The uniform validation failure the coercion
raises is itself a user-defined exception class. The produced numeric value is
modelled as an `Optional[int]` (a non-null token for a constructed value, the
null token for the absent input).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ConstructorMalformedError(Exception):
    """The canonical numeric constructor's rejection of a malformed numeric
    literal. User-defined stand-in for one low-level rejection class the
    constructor raises on some inputs (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


class ConstructorOperandError(Exception):
    """A callee's rejection of a wrong-typed operand. User-defined stand-in for a
    second, distinct low-level rejection class — the SAME low-level class BOTH
    the canonical constructor and the floating conversion raise when the operand
    they are handed is of a type they cannot accept, so one stand-in denotes it
    for both callees (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


class ConstructorDomainError(Exception):
    """The canonical numeric constructor's rejection of an out-of-domain
    argument. User-defined stand-in for a third, distinct low-level rejection
    class the constructor raises on some inputs (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class ConstructorRangeError(Exception):
    """The canonical numeric constructor's rejection of a value one of whose
    components lies outside the internal range its representation can hold.
    User-defined stand-in for a fourth, distinct low-level rejection class the
    constructor raises on some inputs — the one the coercion does NOT classify,
    so it propagates to the coercion's caller unchanged (a builtin exception in
    an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class ConversionRangeError(Exception):
    """The floating conversion's rejection of a value whose magnitude lies
    outside the range that conversion's own rounding context can represent.
    User-defined stand-in for a distinct low-level rejection class raised by the
    floating-path callee — NOT the same class the canonical constructor raises
    for its out-of-representable-range shape, and caught by neither of them, so
    it too reaches the coercion's caller unchanged (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class ValidationFailure(Exception):
    """The single uniform validation failure the coercion surfaces to its caller
    whenever the value is unacceptable in one of the CLASSIFIED rejection
    shapes. User-defined stand-in for the validation error the desired behaviour
    requires (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def value_kind() -> int:
    """The acceptance kind of THE value the coercion was handed — the single
    value every axiomatized callee below is applied to. The callees are
    functions of that value, not of a tag the implementation may choose: each
    one is the real call the coercion makes ON THE VALUE IN SCOPE, so `kind`
    names which acceptance shape that value has. A call whose tag is not
    `value_kind()` therefore denotes NO call the coercion could make — it would
    read a callee's contract at one acceptance shape while the callee is applied
    to a value of another, which is exactly the mismatch the executable
    refinement forbids (both callee bridges apply the real call to the value in
    scope and ignore the tag). Left ABSTRACT: the proof needs only that the
    value in scope HAS an acceptance shape, within the total kind range.
    Provenance + executable soundness check: mapping.md §3.4 / axiom_check.py."""
    Ensures(0 <= Result() and Result() <= 8)


@Pure
@ContractOnly
def from_floating() -> int:
    """The constructed numeric token the floating conversion yields for a
    floating value it accepts, via the field's rounding context — a VALUE
    accessor over the unchanged floating-path callee, exactly analogous to
    `accepted_value` over the constructor. Its value is left ABSTRACT — the
    proof needs only that the floating path returns EXACTLY this callee's token
    (so the floating result is pinned to the floating callee, not an arbitrary
    literal), never a value the proof fabricates. Provenance + executable
    soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(True)


@ContractOnly
def convert_floating(kind: int) -> int:
    """The floating conversion applied to the supplied value (the unchanged
    callee the coercion invokes for a value it routes to the floating branch).
    This callee is DISTINCT from the canonical constructor and is invoked
    OUTSIDE the coercion's uniform-failure handling, so its own rejection is not
    converted. `kind` tags the value's acceptance shape on this branch:

      * kind 1 — the conversion accepts the value and yields a constructed
        numeric token, namely `from_floating()`;
      * kind 7 — the conversion rejects the value as a wrong-typed operand,
        because the value satisfies the coercion's floating-branch test without
        being one of the operand types this conversion accepts;
      * kind 8 — the conversion accepts the value's TYPE as an operand but
        refuses its magnitude, which lies outside the range its own rounding
        context can represent. This is a DISTINCT low-level rejection class from
        the wrong-typed-operand one above, and distinct also from the
        constructor's out-of-representable-range class.

    Enumerating BOTH reject kinds is what keeps this axiom no stronger than the
    callee: a contract claiming the conversion NEVER rejects would claim the
    callee accepts every value the coercion routes to it, and a contract with
    only the wrong-typed-operand refusal would claim that is the callee's ONLY
    rejection — both false of it. The coercion routes on a test that is
    satisfiable by values this conversion refuses in either of two ways.

    The weakest facts the proof needs: it returns normally on EXACTLY the
    accepted kind — and that return is EXACTLY this callee's token
    `from_floating()` (pinned to the callee, not an arbitrary literal) — and it
    raises the MATCHING distinct rejection on each of its two reject kinds.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(kind == 1 or kind == 7 or kind == 8)
    Requires(kind == value_kind())
    Requires(MustTerminate(2))
    Ensures(kind == 1)
    Ensures(Implies(kind == 1, Result() == from_floating()))
    Exsures(ConstructorOperandError, kind == 7)
    Exsures(ConversionRangeError, kind == 8)


@Pure
@ContractOnly
def accepted_value(kind: int) -> int:
    """The constructed numeric token the canonical constructor yields for an
    accepted value (kind 2), via the field's rounding context — the unchanged
    callee on the accepted path, analogous to `from_floating` on the float path.
    Its value is left ABSTRACT — the proof needs only that the accepted path
    returns EXACTLY this callee's token (so the accepted result is pinned to the
    constructor's own token, not an arbitrary non-null literal), never a value
    the proof fabricates. Provenance + executable soundness check: mapping.md §3
    / axiom_check.py."""
    Requires(kind == 2)
    Ensures(Result() is not None)


@ContractOnly
def construct_numeric(kind: int) -> int:
    """The canonical numeric constructor applied to the supplied value (the
    unchanged callee the coercion invokes for any value that is neither absent
    nor floating). `kind` tags the value's acceptance shape:

      * kind 2 — the constructor accepts the value and yields a constructed
        numeric token (a non-null int here);
      * kind 3 — the constructor rejects the value as a malformed numeric
        literal;
      * kind 4 — the constructor rejects the value as a wrong-typed operand;
      * kind 5 — the constructor rejects the value as an out-of-domain argument;
      * kind 6 — the constructor rejects the value because a component of it
        lies outside the internal range its representation can hold.

    The four rejection kinds are distinct observable outcomes of the real
    constructor; enumerating the fourth is what keeps this axiom no stronger
    than the callee (a three-way rejection contract would claim the callee
    rejects in only three ways, which is false of it).

    The weakest facts the proof needs: it returns normally on EXACTLY the
    accepted kind — and the accepted return is EXACTLY this constructor's token
    `accepted_value(2)` (pinned to the callee, not an arbitrary literal) — and it
    raises the matching distinct rejection on each of the four reject kinds.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(kind == 2 or kind == 3 or kind == 4 or kind == 5 or kind == 6)
    Requires(kind == value_kind())
    Requires(MustTerminate(2))
    Ensures(kind == 2)
    Ensures(Implies(kind == 2, Result() == accepted_value(2)))
    Exsures(ConstructorMalformedError, kind == 3)
    Exsures(ConstructorOperandError, kind == 4)
    Exsures(ConstructorDomainError, kind == 5)
    Exsures(ConstructorRangeError, kind == 6)
# axioms-end


# pure-start
# (no module-level pure helpers required: the coercion's decision is stated
# inline over the integer acceptance kind.)
# pure-end


def coerce_to_numeric(kind: int) -> Optional[int]:
    # pre-conditions-start
    # `kind` is a plain integer acceptance tag (no heap permission needed):
    #   0 — absent value;            1 — floating, conversion-accepted;
    #   2 — constructor-accepted;    3 — malformed-literal rejection;
    #   4 — wrong-typed-operand rejection;  5 — out-of-domain rejection;
    #   6 — out-of-representable-range rejection (an UNCLASSIFIED shape);
    #   7 — floating-branch value the floating conversion refuses as a
    #       wrong-typed operand (an UNCLASSIFIED shape);
    #   8 — floating-branch value the floating conversion accepts by operand
    #       type but refuses as out of its context's representable range (the
    #       third UNCLASSIFIED shape, a distinct rejection class from 6 and 7).
    # The domain covers every shape either callee can exhibit; no rejection
    # shape is excluded from the coercion's input domain.
    Requires(0 <= kind and kind <= 8)
    Requires(kind == value_kind())
    Requires(MustTerminate(8))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY for an acceptable value: absent,
    # floating-and-convertible, or constructor-accepted. Every unacceptable
    # value (any rejection shape, from either callee, classified or not) must
    # NOT return normally.
    Ensures(kind == 0 or kind == 1 or kind == 2)
    # The absent value is passed straight through as the null token; every other
    # acceptable value yields a constructed (non-null) numeric token, pinned to
    # the callee that produced it (not an arbitrary literal): the floating
    # value's token is EXACTLY the float callee's token, and the
    # constructor-accepted value's token is EXACTLY the constructor's token. Both
    # accepted branches are value-pinned symmetrically.
    Ensures(Implies(kind == 0, Result() is None))
    Ensures(Implies(kind == 1, Result() is not None and Result() == from_floating()))
    Ensures(Implies(kind == 2, Result() is not None and Result() == accepted_value(kind)))
    # The pinned behaviour: EVERY CLASSIFIED rejection shape — malformed literal
    # (3), wrong-typed operand (4), or out-of-domain argument (5) — is surfaced
    # as the SAME uniform validation failure, never as the constructor's own
    # low-level rejection. Those kinds raise this and ONLY this exception, and
    # the validation failure is raised on NO OTHER kind.
    Exsures(ValidationFailure, kind == 3 or kind == 4 or kind == 5)
    # The one rejection shape the coercion does not classify (6) is NOT converted:
    # the constructor's own low-level error reaches the caller unchanged. Pinning
    # this leg is what makes the spec state the coercion's real guarantee — an
    # impl that swallowed this shape into the validation failure, or returned
    # normally on it, does not match the coercion and does not verify.
    Exsures(ConstructorRangeError, kind == 6)
    # The floating branch's own unclassified shape (7) is likewise NOT converted:
    # the floating conversion is invoked outside the uniform-failure handling, so
    # its wrong-typed-operand rejection reaches the caller unchanged. Because that
    # is the SAME low-level class the constructor raises on kind 4 — which the
    # coercion DOES convert — this leg also pins the boundary between them: the
    # low-level operand rejection may escape on 7 and on NO other kind, so an impl
    # that let it escape from the constructor path (kind 4) does not verify.
    Exsures(ConstructorOperandError, kind == 7)
    # The floating branch's SECOND unclassified shape (8) is likewise NOT
    # converted: the floating conversion refuses a value whose magnitude its own
    # context cannot represent, with a rejection class DISTINCT from every class
    # the coercion classifies and from the constructor's out-of-range class, and
    # that call sits outside the uniform-failure handling, so it reaches the
    # caller unchanged. Pinning this leg is what keeps the spec's claim equal to
    # the real coercion's guarantee on the whole floating branch rather than
    # stronger than it: the branch has three outcomes, not two.
    Exsures(ConversionRangeError, kind == 8)
    # post-conditions-end
    # impl-start
    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    # impl-end
