"""Twin-artifact model for sympy__sympy-13798.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A LaTeX printer accepts a multiplication-separator selector that may be the
  unset value (modelled here as ``None``) or a token string. Four selector
  tokens are *recognised* and map to a constant LaTeX separator each; the unset
  value behaves like the blank separator. From the selector the printer derives
  two separators:

    (1) the general separator used between non-numeric factors;
    (2) the separator used between two numeric factors.

  Desired behaviour:

    * For a recognised selector (the unset value, or one of the four tokens)
      BOTH derived separators are the constant LaTeX string associated with that
      selector — except that for the unset value the *numeric* separator is the
      one associated with the centred-dot token (numbers are never juxtaposed
      with only a blank between them).

    * For an UNRECOGNISED selector token the general separator is the selector
      string verbatim (the caller's own choice is honoured). The numeric
      separator is then the centred-dot string when the selector — with leading
      and trailing blanks removed — is one of the recognised "spacing only"
      tokens (the empty token, a single space, or one of the bare LaTeX spacing
      commands), and otherwise is again the selector string verbatim.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]``. The unset
selector is modelled by ``None`` (an ``Optional`` carrier). The whitespace-
trimming callee used by the numeric branch is an unchanged library operation
and is axiomatised (``trimmed``); its soundness is checked against the real
callee out of band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def trimmed(s: PSeq[int]) -> PSeq[int]:
    """Whitespace-trim of a token (the unchanged library ``str.strip`` callee),
    restricted to the property the numeric branch relies on: a token that has
    no leading or trailing ASCII blank is returned unchanged. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(no_outer_blank(s), Result() == s))
# axioms-end


# pure-start
@Pure
def tok_ldot() -> PSeq[int]:
    # "ldot"
    return PSeq(108, 100, 111, 116)


@Pure
def tok_dot() -> PSeq[int]:
    # "dot"
    return PSeq(100, 111, 116)


@Pure
def tok_times() -> PSeq[int]:
    # "times"
    return PSeq(116, 105, 109, 101, 115)


@Pure
def sep_blank() -> PSeq[int]:
    # " "  (separator for the unset selector)
    return PSeq(32)


@Pure
def sep_ldot() -> PSeq[int]:
    # r" \,.\, "
    return PSeq(32, 92, 44, 46, 92, 44, 32)


@Pure
def sep_dot() -> PSeq[int]:
    # r" \cdot "  (the centred-dot separator)
    return PSeq(32, 92, 99, 100, 111, 116, 32)


@Pure
def sep_times() -> PSeq[int]:
    # r" \times "
    return PSeq(32, 92, 116, 105, 109, 101, 115, 32)


@Pure
def is_known_token(s: PSeq[int]) -> bool:
    """A non-unset selector that is one of the four recognised tokens."""
    return s == tok_dot() or s == tok_times() or s == tok_ldot()


@Pure
def token_sep(s: PSeq[int]) -> PSeq[int]:
    """The constant LaTeX separator associated with a recognised non-unset
    token. (Only consulted under is_known_token(s).)"""
    if s == tok_dot():
        return sep_dot()
    if s == tok_times():
        return sep_times()
    return sep_ldot()


@Pure
def is_spacing_only(t: PSeq[int]) -> bool:
    """A trimmed token that consists solely of LaTeX spacing: the empty token,
    a single space, or a bare spacing command."""
    return (t == PSeq(0).take(0)            # ""
            or t == PSeq(32)                # " "
            or t == PSeq(92)                # "\\"
            or t == PSeq(92, 44)            # "\\,"
            or t == PSeq(92, 58)            # "\\:"
            or t == PSeq(92, 59)            # "\\;"
            or t == PSeq(92, 113, 117, 97, 100))   # "\\quad"


@Pure
def is_visible_ascii(c: int) -> bool:
    """A printable ASCII code point other than the space (33..126). No code
    point trimmed by the library whitespace-trim falls in this range, so a token
    bounded by such code points is returned unchanged by the trim."""
    return 33 <= c and c <= 126


@Pure
def no_outer_blank(s: PSeq[int]) -> bool:
    """A token the whitespace-trim leaves unchanged: empty, or bounded on both
    ends by a printable non-space ASCII code point (conservatively excludes
    every code point the trim could strip)."""
    return (len(s) == 0) or (is_visible_ascii(s[0])
                             and is_visible_ascii(s[len(s) - 1]))


@Pure
def general_sep_of(sym: Optional[List[int]]) -> PSeq[int]:
    """Desired general separator: blank for the unset selector, the constant
    separator for a recognised token, the selector verbatim otherwise."""
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 4)))
    if sym is None:
        return sep_blank()
    if is_known_token(ToSeq(sym)):
        return token_sep(ToSeq(sym))
    return ToSeq(sym)


@Pure
def numeric_sep_of(sym: Optional[List[int]]) -> PSeq[int]:
    """Desired numeric separator: centred dot for the unset selector, the
    constant separator for a recognised token, otherwise centred dot when the trimmed
    selector is spacing-only and the selector verbatim when it is not."""
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 4)))
    if sym is None:
        return sep_dot()
    if is_known_token(ToSeq(sym)):
        return token_sep(ToSeq(sym))
    if is_spacing_only(trimmed(ToSeq(sym))):
        return sep_dot()
    return ToSeq(sym)
# pure-end


def general_separator(sym: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The general separator is exactly the desired derivation of the selector.
    Ensures(ToSeq(Result()) == general_sep_of(sym))
    # post-conditions-end
    # impl-start
    if sym is None:
        return [32]
    s = ToSeq(sym)
    Assert(s == ToSeq(sym))
    if s == tok_dot():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 44, 46, 92, 44, 32]
    Assert(not is_known_token(s))
    Assert(general_sep_of(sym) == ToSeq(sym))
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        # invariants-start
        Invariant(Acc(list_pred(sym), 1 / 2))
        Invariant(Acc(list_pred(res)))
        Invariant(0 <= i and i <= len(sym))
        Invariant(ToSeq(res) == ToSeq(sym).take(i))
        Invariant(general_sep_of(sym) == ToSeq(sym))
        Invariant(MustTerminate(len(sym) - i + 1))
        # invariants-end
        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
        res = res + [sym[i]]
        i = i + 1
    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
    return res
    # impl-end


def numeric_separator(sym: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The numeric separator is exactly the desired derivation of the selector.
    Ensures(ToSeq(Result()) == numeric_sep_of(sym))
    # post-conditions-end
    # impl-start
    if sym is None:
        return [32, 92, 99, 100, 111, 116, 32]
    s = ToSeq(sym)
    Assert(s == ToSeq(sym))
    if s == tok_dot():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 44, 46, 92, 44, 32]
    Assert(not is_known_token(s))
    t = trimmed(s)
    if is_spacing_only(t):
        Assert(numeric_sep_of(sym) == sep_dot())
        return [32, 92, 99, 100, 111, 116, 32]
    Assert(numeric_sep_of(sym) == ToSeq(sym))
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        # invariants-start
        Invariant(Acc(list_pred(sym), 1 / 2))
        Invariant(Acc(list_pred(res)))
        Invariant(0 <= i and i <= len(sym))
        Invariant(ToSeq(res) == ToSeq(sym).take(i))
        Invariant(numeric_sep_of(sym) == ToSeq(sym))
        Invariant(MustTerminate(len(sym) - i + 1))
        # invariants-end
        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
        res = res + [sym[i]]
        i = i + 1
    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
    return res
    # impl-end
