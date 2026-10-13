"""Twin-artifact model for sphinx-doc__sphinx-9602.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (B1) When a constant value appears as an argument of a parametrised type
       annotation, it is rendered as its textual *representation*. For a value
       that is itself a piece of text, that representation carries the
       surrounding quote marks (the apostrophe U+0027 on each side); for a
       numeric or boolean value the representation is its plain textual form.

  (B2) When a parametrised type annotation enumerates concrete values (a
       "one-of these literal values" annotation), each enumerated value is
       presented as plain text and is NOT turned into a class cross-reference,
       so a tool that audits cross-references for a documented class never
       flags an enumerated value as a missing class. Every argument of an
       ordinary (non-enumerated) parametrised annotation is still turned into a
       cross-reference.

A rendered annotation is a flat list of presentation nodes. Each node is
abstracted to an integer KIND: 1 = a non-blank text node (a candidate for
cross-referencing), 2 = structural punctuation, 3 = a resolved cross-reference,
4 = a text node wrapped so the resolver leaves it as plain text. Text content
is modelled as `List[int]` of Unicode code points (Nagini bans `str` indexing);
node lists are modelled as `List[int]` of kind codes. Specifications are
carried by `PSeq[int]` via `ToSeq`.

`resolve_subscript` models the body of a parametrised annotation — the
enumerated arguments and their separators, between the opening and closing
bracket. The name being parametrised (the subscript head) is unchanged by this
behaviour and is not part of the modelled body.

No callee is consumed as a `@ContractOnly` axiom: both changed behaviours are
modelled deeply (the rendering of a constant, and the per-node kind decision of
the resolver), and validated == the real callees out-of-band by axiom_check.py
(G-AX) — they are A-references, not consumed axioms.

Both functions carry a termination obligation in their preconditions: each
must actually DELIVER its result (Nagini is a partial-correctness verifier by
default, so without the obligation a diverging implementation would satisfy
the value postconditions vacuously); the real operations always return.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: every changed operation is modelled deeply;
#  the unchanged textual-representation operation and the cross-reference
#  constructor are validated as A-references by axiom_check.py, not consumed
#  here.)
# axioms-end


# pure-start
# Kind codes for presentation nodes.
#   1 NAME  : a non-blank text node (candidate for cross-referencing)
#   2 PUNCT : structural punctuation (never resolved)
#   3 XREF  : a resolved cross-reference
#   4 LIT   : a text node wrapped so the resolver keeps it as plain text

@Pure
def quote() -> PSeq[int]:
    # the apostrophe U+0027 that the textual representation of a piece of text
    # places on each side
    return PSeq(39)


@Pure
def wrap1(k: int, is_lit: bool) -> int:
    """One body node under the enumeration-wrap step: a text node (NAME) in an
    enumerated subscript becomes a wrapped node (LIT); every other node, and
    every node in a non-enumerated subscript, is unchanged."""
    if is_lit and k == 1:
        return 4
    return k


@Pure
def resolve1(k: int) -> int:
    """One node under the final resolution step: a wrapped node (LIT) becomes a
    plain text node (NAME); a non-blank text node (NAME) becomes a
    cross-reference (XREF); punctuation and already-resolved references pass
    through."""
    if k == 4:
        return 1
    if k == 1:
        return 3
    return k


@Pure
def wrap_seq(ks: PSeq[int], is_lit: bool) -> PSeq[int]:
    """Enumeration-wrap of the whole body node list (front-recursive so a single
    unfold is available per loop step)."""
    if len(ks) == 0:
        return PSeq(0).take(0)
    return PSeq(wrap1(ks[0], is_lit)) + wrap_seq(ks.drop(1), is_lit)


@Pure
def resolve_seq(ks: PSeq[int]) -> PSeq[int]:
    """Final resolution of the whole body node list (front-recursive)."""
    if len(ks) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve1(ks[0])) + resolve_seq(ks.drop(1))
# pure-end


def render_literal_value(value: List[int], is_str: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # The renderer must actually DELIVER a representation (a total-correctness
    # obligation): without it a diverging implementation would satisfy the
    # value postconditions vacuously; the real renderer always returns.
    Requires(MustTerminate(2))
    # A textual value is drawn from the simple printable-ASCII domain (no
    # apostrophe U+0027, no reverse solidus U+005C, no control character): the
    # text content of the constants these parametrised annotations carry. On
    # this domain a piece of text's representation is exactly that text framed
    # by an apostrophe on each side.
    Requires(Implies(is_str,
                     Forall(int, lambda j: (Implies(0 <= j and j < len(value),
                                                     32 <= value[j]
                                                     and value[j] <= 126
                                                     and value[j] != 39
                                                     and value[j] != 92),
                                            [[value[j]]]))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A textual value is represented WITH its surrounding quote marks; a
    # non-textual value is represented by its plain textual form unchanged.
    Ensures(Implies(is_str, ToSeq(Result()) == quote() + ToSeq(value) + quote()))
    Ensures(Implies(not is_str, ToSeq(Result()) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    if is_str:
        result = [39] + value + [39]  # type: List[int]
        return result
    else:
        out = []  # type: List[int]
        i = len(value)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(out) == ToSeq(value).drop(i))
            # the loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure i.
            Invariant(MustTerminate(i + 1))
            # invariants-end
            out = [value[i - 1]] + out
            i = i - 1
        return out
    # impl-end


def resolve_subscript(kinds: List[int], is_literal: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    # The resolver must actually DELIVER the resolved node list (a
    # total-correctness obligation): without it a diverging implementation
    # would satisfy the value postconditions vacuously; the real resolver
    # always returns.
    Requires(MustTerminate(2))
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(kinds),
                                            1 <= kinds[j] and kinds[j] <= 4),
                                    [[kinds[j]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(kinds))
    # The full pipeline on the body is wrap-then-resolve over the node list.
    Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (B2 reverted): the enumeration-wrap step (hunk 2) is absent, so
    # no body node is ever wrapped; the resolver then turns every non-blank
    # text node — including an enumerated value — into a cross-reference.
    wrapped = []  # type: List[int]
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(wrapped)))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(len(wrapped) == len(kinds) - i)
        # strictly decreasing, bounded-below measure i consumes the caller's
        # termination obligation.
        Invariant(MustTerminate(i + 1))
        Invariant(ToSeq(wrapped) == ToSeq(kinds).drop(i))
        # invariants-end
        k = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == k)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        wrapped = [k] + wrapped
        i = i - 1
    Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
    out = []  # type: List[int]
    j = len(wrapped)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(wrapped)))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(wrapped))
        Invariant(len(wrapped) == len(kinds))
        # strictly decreasing, bounded-below measure j consumes the caller's
        # termination obligation.
        Invariant(MustTerminate(j + 1))
        Invariant(len(out) == len(wrapped) - j)
        Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
        # invariants-end
        w = wrapped[j - 1]
        Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
        Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
        if w == 4:
            out = [1] + out
        elif w == 1:
            out = [3] + out
        else:
            out = [w] + out
        j = j - 1
    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
    return out
    # impl-end
