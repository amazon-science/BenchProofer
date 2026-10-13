"""Twin-artifact model for sphinx-doc__sphinx-8621.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single inline keystroke description (a piece of literal text such as
  ``Control+X`` or ``Alt+^``) is divided into a flat sequence of *parts* that
  alternate keystroke / separator / keystroke / ... .  The recognised
  compound-key separators are the hyphen-minus ``-`` (U+002D), the plus sign
  ``+`` (U+002B), the circumflex ``^`` (U+005E) and a run of blank space.

  A separator splits the text into surrounding keystrokes ONLY when it actually
  stands BETWEEN two keystrokes — that is, only when it has at least one
  character before it AND at least one character after it.  A separator that
  sits at the very start or the very end of the text is NOT a separator: it
  belongs to the adjacent keystroke.  In particular a text consisting of a
  single separator character is one indivisible keystroke, and a keystroke that
  ends (or begins) with a separator character keeps that character as part of
  itself rather than introducing an empty keystroke beside it.

  The three single compound-key characters ``- + ^`` each form their own
  one-character separator token (two adjacent ones do not merge — an empty
  keystroke sits between them).  Blank space behaves differently: a maximal run
  of blank-space characters that is flanked on both sides collapses into ONE
  separator token, so a doubled blank between two keystrokes is a single
  separator, not two.

  Consequently the part sequence never contains an empty keystroke produced by
  a leading or trailing separator: ``-`` yields the single part ``-``;
  ``Alt+^`` yields exactly ``Alt`` / ``+`` / ``^`` (three parts), not a part
  sequence padded with empty keystrokes around the trailing ``^``.

  A text is rendered as a single, indivisible keystroke (no inner structure)
  exactly when this splitting produces a single part.

  Splitting a finite text is a bounded computation: both operations MUST
  terminate and return their answer (a total-correctness obligation, carried
  as MustTerminate in the precondition).  Nagini is a partial-correctness
  verifier by default, so without the obligation a diverging implementation
  (bare self-recursion, an endless loop) would satisfy every Ensures
  vacuously while sharing the spec; the real split always returns its parts.

Strings are modelled as `List[int]` / `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); the part sequence is a `PSeq[PSeq[int]]`.  The
modelled domain is printable ASCII (code points 32..126): the only blank-space
character in that range is the ordinary space U+0020, so blank runs are runs of
spaces and there is no interaction with line breaks.  The split is modelled
DEEPLY as the front-recursive fold `kparts` (a code point is a separator only
when flanked, with blank-space runs collapsing into a single token); its
equality to the real keystroke-splitting callee is checked out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the keystroke split is modelled deeply below
#  as `kparts` and validated == the real keystroke-splitting callee out-of-band
#  by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def is_sep(c: int) -> bool:
    """A single compound-key separator character: '-' (45), '+' (43) or
    '^' (94)."""
    return c == 45 or c == 43 or c == 94


@Pure
def is_space(c: int) -> bool:
    """A blank-space character.  On the modelled printable-ASCII domain the only
    blank-space code point is the ordinary space ' ' (32)."""
    return c == 32


@Pure
def in_domain(c: int) -> bool:
    """The modelled domain: printable ASCII, code points 32..126.  The only
    blank-space character in this range is the ordinary space (32)."""
    return 32 <= c and c <= 126


@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def single_part(p: PSeq[int]) -> PSeq[PSeq[int]]:
    """The one-element part sequence containing the single part `p`."""
    return PSeq(p)


@Pure
def emit_sep(c: int) -> PSeq[PSeq[int]]:
    """The two leading parts emitted when code point `c` is a flanked, standalone
    separator: a fresh empty keystroke followed by the separator token `[c]`."""
    return single_part(empty_seq()) + single_part(PSeq(c))


@Pure
def kparts(s: PSeq[int], lead: bool) -> PSeq[PSeq[int]]:
    """The keystroke/separator part sequence of `s`, where `lead` is True iff a
    character precedes `s[0]` in the full text.

    A code point splits only when flanked: it needs a character before (`lead`)
    and a character after (`len(s) >= 2`).  Front-recursive (one unfold per code
    point).  A flanked single separator ``- + ^`` becomes its own one-character
    token (emitting a fresh empty keystroke before it).  A flanked blank space
    also begins a fresh separator token, BUT when the following code point is
    itself a flanked blank space the two merge into one blank-run token (the
    space is prepended to the already-open blank token rather than opening a new
    one).  Any other code point is prepended to the first part of the split of
    the remainder.  The last code point never splits (no following character),
    so a lone or trailing separator stays inside its keystroke."""
    Ensures(len(Result()) >= 1)
    Ensures(Implies(len(s) >= 2 and lead and is_space(s[0]),
                    len(Result()) >= 2 and Result()[0] == empty_seq()))
    if len(s) == 0:
        return single_part(empty_seq())
    if len(s) == 1:
        return single_part(s)
    if lead and is_sep(s[0]):
        return emit_sep(s[0]) + kparts(s.drop(1), True)
    if lead and is_space(s[0]):
        rest = kparts(s.drop(1), True)  # type: PSeq[PSeq[int]]
        if len(s) >= 3 and is_space(s[1]):
            # The next code point is itself a flanked blank space, so the split
            # of the remainder already opens a blank token (rest[0] is the fresh
            # empty keystroke, rest[1] the blank token): merge this space in.
            return single_part(empty_seq()) + single_part(PSeq(s[0]) + rest[1]) + rest.drop(2)
        return emit_sep(s[0]) + rest
    rest2 = kparts(s.drop(1), True)  # type: PSeq[PSeq[int]]
    return single_part(PSeq(s[0]) + rest2[0]) + rest2.drop(1)


@Pure
def kparts_unfold(s: PSeq[int], lead: bool) -> bool:
    """Lemma: one-step unfold of `kparts` on a non-trivial suffix, exposing the
    relation between `kparts(s, lead)` and `kparts(s.drop(1), True)` used by the
    impl loop invariant (one equation per impl branch)."""
    Requires(len(s) >= 2)
    Ensures(Result())
    # flanked single separator
    Ensures(Implies(lead and is_sep(s[0]),
                    kparts(s, lead) == emit_sep(s[0]) + kparts(s.drop(1), True)))
    # flanked blank space that MERGES with a following flanked blank space
    Ensures(Implies(lead and is_space(s[0]) and len(s) >= 3 and is_space(s[1]),
                    kparts(s, lead)
                    == single_part(empty_seq())
                    + single_part(PSeq(s[0]) + kparts(s.drop(1), True)[1])
                    + kparts(s.drop(1), True).drop(2)))
    # flanked blank space that does NOT merge (next code point is not a flanked
    # blank space): a standalone blank token
    Ensures(Implies(lead and is_space(s[0])
                    and not (len(s) >= 3 and is_space(s[1])),
                    kparts(s, lead) == emit_sep(s[0]) + kparts(s.drop(1), True)))
    # any other code point: prepended to the first part of the remainder split
    Ensures(Implies(not (lead and (is_sep(s[0]) or is_space(s[0]))),
                    kparts(s, lead)
                    == single_part(PSeq(s[0]) + kparts(s.drop(1), True)[0])
                    + kparts(s.drop(1), True).drop(1)))
    return True
# pure-end


def split_keystrokes(text: List[int]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Modelled domain: every code point is printable ASCII (32..126); the only
    # blank-space character in this range is the ordinary space.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             in_domain(text[k])), [[text[k]]])))
    # TERMINATION: the split must actually ANSWER — splitting a finite text is
    # a bounded computation (one pass over the code points).  Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. bare self-recursion or an endless
    # loop) satisfies every Ensures vacuously; the real split always returns
    # its part sequence.  (Measure 1 < 2 lets keystroke_is_atomic, which holds
    # MustTerminate(2), call this function without leaking its obligation.)
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The returned part sequence is exactly the flanked-separator split of the
    # whole text (lead=False: nothing precedes the first code point).
    Ensures(Result() == kparts(ToSeq(text), False))
    # post-conditions-end
    # impl-start
    result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
    i = len(text)
    Assert(len(ToSeq(text).drop(i)) == 0)
    Assert(ToSeq(text).drop(i) == empty_seq())
    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(0 <= i and i <= len(text))
        Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        i = i - 1
        c = text[i]
        Assert(ToSeq(text).drop(i)[0] == c)
        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
        if i == len(text) - 1:
            # Last code point: the suffix has length 1, so kparts is the
            # single-part base case and `result` is the empty-suffix base.
            Assert(len(ToSeq(text).drop(i)) == 1)
            Assert(ToSeq(text).drop(i) == PSeq(c))
            Assert(result == single_part(empty_seq()))
            Assert(PSeq(c) + result[0] == PSeq(c))
            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
            result = single_part(PSeq(c) + result[0]) + result.drop(1)
        else:
            # Interior/leading code point: unfold kparts one step.
            Assert(len(ToSeq(text).drop(i)) >= 2)
            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
            if (i > 0) and is_sep(c):
                result = emit_sep(c) + result
            elif (i > 0) and is_space(c):
                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
                    # The next code point is a flanked blank space: `result`
                    # already opens a blank token, merge `c` into it.
                    Assert(len(ToSeq(text).drop(i)) >= 3)
                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
                    Assert(is_space(ToSeq(text).drop(i)[1]))
                    Assert(len(result) >= 2)
                    Assert(result[0] == empty_seq())
                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
                else:
                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
                    result = emit_sep(c) + result
            else:
                result = single_part(PSeq(c) + result[0]) + result.drop(1)
    return result
    # impl-end


def keystroke_is_atomic(text: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Modelled domain: every code point is printable ASCII (32..126); the only
    # blank-space character in this range is the ordinary space.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             in_domain(text[k])), [[text[k]]])))
    # TERMINATION: the atomicity decision must actually ANSWER — it is one
    # bounded split plus a length test.  Nagini is a partial-correctness
    # verifier by default, so without this obligation a non-terminating
    # implementation satisfies every Ensures vacuously; the real decision
    # always returns its truth value.  (Measure 2 > 1 covers the call to
    # split_keystrokes, whose own obligation is MustTerminate(1).)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The text renders as a single indivisible keystroke exactly when the
    # flanked-separator split yields a single part.
    Ensures(Result() == (len(kparts(ToSeq(text), False)) == 1))
    # post-conditions-end
    # impl-start
    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]
    return len(parts) == 1
    # impl-end
