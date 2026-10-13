"""Twin-artifact model for django__django-16877.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A "per-element marking" transform for a SEQUENCE of textual items. Given an
  ordered sequence of items, it produces an ordered sequence of the SAME length,
  aligned one-to-one with the input, where the i-th output item is the
  *escape-when-needed* form of the i-th input item:

    (1) An item that has NOT yet been marked as safe for HTML output has each of
        the five HTML-significant code points replaced by its constant entity
        sequence (the ampersand handled first so the ampersands inside emitted
        entities are not themselves re-escaped; the apostrophe U+0027 encoded as
        `&#x27;`), and every other code point passes through unchanged. Such an
        item is escaped exactly once.

    (2) An item that has ALREADY been marked as safe for HTML output is left
        byte-for-byte unchanged -- it is NOT escaped again (no double escaping).

  Every output item is marked safe for HTML output, and the output sequence has
  exactly as many items as the input, in the same order. This makes the result
  independent of any surrounding auto-escaping context: each item already
  carries its final HTML form.

An item is modelled as a minimal object exposing only the two touched aspects:
its character content (`chars`, the Unicode code points; Nagini bans `str`
indexing, so strings are sequences of code points carried by `PSeq[int]`) and
whether it has already been marked safe for HTML output (`is_safe`). The
sequence of items is a `List[Elem]`.

The per-item escape-when-needed transform is modelled as its own contracted
function (`escape_when_unsafe_item`); the sequence transform (`escape_each`)
calls it and uses its contract directly (it is under specification, not an
axiom). The HTML escape of an item's content is modelled DEEPLY as a verified
per-code-point substitution (`escaped_seq`), whose equality to the real stdlib
escaper is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom. No callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Elem:
    """One item of the sequence. Carries only the two touched aspects: the
    character content (`chars`) and whether the item has already been marked
    safe for HTML output (`is_safe`)."""

    def __init__(self, chars: PSeq[int], is_safe: bool) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.chars) and Acc(self.is_safe))  # type: ignore
        Ensures(self.chars == chars)
        Ensures(self.is_safe == is_safe)
        # post-conditions-end
        # impl-start
        self.chars = chars      # type: PSeq[int]
        self.is_safe = is_safe  # type: bool
        # impl-end


# axioms-start
# (no axioms: the per-item escape-when-needed transform is modelled deeply -- the
# HTML escape of an item's content is the spelled-out per-code-point fold
# `escaped_seq`, validated == the real stdlib escaper out-of-band by axiom_check.py
# (G-AX); the safe-passthrough branch is the identity on the content; and the
# sequence transform uses the per-item function's contract, not an axiom.)
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_hex() -> PSeq[int]:
    # '&#x27;'  (the apostrophe entity required of the escaper)
    return PSeq(38, 35, 120, 50, 55, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point: the five significant
    ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"  -> &#x27;
        return seq_apos_hex()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The HTML escape of a whole sequence: concatenate the per-code-point
    entity sequences. Front-recursive so a single unfold is available to
    callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_codepoints(text: PSeq[int]) -> PSeq[int]:
    """The HTML escape of an item's character content: the per-code-point entity
    substitution (deep model of the real stdlib escaper; A-reference, G-AX)."""
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The escaped output is the per-code-point entity substitution.
    Ensures(Result() == escaped_seq(text))
    # post-conditions-end
    # impl-start
    result = PSeq(0).take(0)  # type: PSeq[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(text))
        Invariant(result == escaped_seq(text.drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(text.drop(i - 1)[0] == c)
        Assert(text.drop(i - 1).drop(1) == text.drop(i))
        result = entity(c) + result
        i = i - 1
    return result
    # impl-end


def escape_when_unsafe_item(item: Elem) -> Elem:
    # pre-conditions-start
    Requires(Acc(item.chars, 1 / 4) and Acc(item.is_safe, 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(item.chars, 1 / 4) and Acc(item.is_safe, 1 / 4))
    Ensures(Acc(Result().chars) and Acc(Result().is_safe))
    # The produced item is marked safe for HTML output.
    Ensures(Result().is_safe)
    # (2) An already-safe item is left byte-for-byte unchanged (no re-escaping).
    Ensures(Implies(item.is_safe, Result().chars == item.chars))
    # (1) An item not yet marked safe is escaped exactly once: its content is the
    # per-code-point entity substitution.
    Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
    # post-conditions-end
    # impl-start
    # Pre-patch bug: merely MARK each item safe without escaping its content --
    # a not-yet-safe item keeps its raw HTML-significant characters instead of
    # being escaped, violating the escape-exactly-once clause for unsafe items.
    return Elem(item.chars, True)
    # impl-end


def escape_each(value: List[Elem]) -> List[Elem]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
             Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
    Ensures(Acc(list_pred(Result())))
    # The result is aligned one-to-one with the input, IN ORDER, same length.
    Ensures(len(Result()) == len(value))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Acc(Result()[k].chars) and Acc(Result()[k].is_safe)))))
    # Every output item is marked safe ...
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Result()[k].is_safe))))
    # ... an already-safe input item passes through unchanged ...
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value) and value[k].is_safe,
            Result()[k].chars == value[k].chars))))
    # ... a not-yet-safe input item is escaped exactly once.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value) and not value[k].is_safe,
            Result()[k].chars == escaped_seq(value[k].chars)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Elem]
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
                  Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  Acc(result[k].chars) and Acc(result[k].is_safe)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i, result[k].is_safe))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and value[k].is_safe,
                  result[k].chars == value[k].chars))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not value[k].is_safe,
                  result[k].chars == escaped_seq(value[k].chars)))))
        # invariants-end
        result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result
    # impl-end
