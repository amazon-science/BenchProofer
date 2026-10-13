"""Twin-artifact model for psf__requests-1766.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an HTTP Digest authorization credential carries a quality-of-protection
  ("qop") directive, the value of that directive must be a QUOTED string: the
  token `auth` is delimited by a double-quote code point immediately before it
  and immediately after it, so the emitted directive reads `qop="auth"` rather
  than the bare `qop=auth`. (RFC 2617 specifies the qop-options value as a
  quoted string of tokens.)

  Concretely, assembling the credential appends, to the already-built prefix, a
  constant directive segment that is the ordered concatenation of:

    (1) the literal `, qop="auth"` — the directive name, then the value `auth`
        wrapped in double quotes;
    (2) the literal `, nc=` followed by the caller-supplied count token,
        emitted bare (no surrounding quotes);
    (3) the literal `, cnonce="` followed by the caller-supplied client-nonce
        token and a closing double quote.

  The assembled credential is the prefix followed by exactly that segment; in
  particular the quoted value token `"auth"` (a double quote, the four code
  points of `auth`, a closing double quote) occurs contiguously in the result.

Textual values are modelled as ``List[int]`` of Unicode code points (Nagini
bans ``str`` indexing); the specification is carried over ``PSeq[int]``. The
segment is assembled DEEPLY (spelled out as a verified concatenation of literal
code-point sequences with the two interpolated caller tokens), so no opaque
callee is consumed and there are no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the directive segment is assembled deeply from input code-point
#  sequences and constant literals; it invokes no opaque library callee, so there
#  is nothing to axiomatize or G-AX-check.)
# axioms-end


# pure-start
@Pure
def quoted_value_token() -> PSeq[int]:
    """The quality-of-protection value emitted as a QUOTED string: a double
    quote (34), the four code points of the token `auth` (97,117,116,104), and
    a closing double quote (34)."""
    return PSeq(34, 97, 117, 116, 104, 34)  # '"auth"'


@Pure
def directive_head() -> PSeq[int]:
    """The literal head of the directive segment up to the count value:
    `, qop=` then the QUOTED value token then `, nc=`."""
    #   ','  ' '  'q'  'o'  'p'  '='  ('"auth"')          ','  ' '  'n'  'c'  '='
    return PSeq(44, 32, 113, 111, 112, 61) + quoted_value_token() + PSeq(44, 32, 110, 99, 61)


@Pure
def directive_mid() -> PSeq[int]:
    """The literal between the count value and the client-nonce value:
    `, cnonce="` (the client-nonce being a quoted string as well)."""
    #   ','  ' '  'c'  'n'  'o'  'n'  'c'  'e'  '='  '"'
    return PSeq(44, 32, 99, 110, 111, 110, 99, 101, 61, 34)


@Pure
def directive_tail() -> PSeq[int]:
    """The literal closing the client-nonce value: a single double quote."""
    return PSeq(34)


@Pure
def qop_segment(ncvalue: PSeq[int], cnonce: PSeq[int]) -> PSeq[int]:
    """The whole directive segment appended when a quality-of-protection token
    is present: the literal head (carrying the QUOTED value token `"auth"`), the
    count value, the literal mid, the client-nonce value, the closing quote."""
    return directive_head() + ncvalue + directive_mid() + cnonce + directive_tail()
# pure-end


def append_qop_directive(base: List[int], ncvalue: List[int],
                         cnonce: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ncvalue), 1 / 2))
    Requires(Acc(list_pred(cnonce), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ncvalue), 1 / 2))
    Ensures(Acc(list_pred(cnonce), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled credential is the prefix followed by exactly the directive
    # segment, whose value token is the QUOTED form `"auth"`.
    Ensures(ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)))
    # Discriminating structural property: immediately after the prefix the
    # segment opens with the literal head, which carries the quoted value token
    # `"auth"` contiguously (a bare `auth` would not match this head).
    Ensures(ToSeq(Result()).drop(len(base)).take(len(directive_head())) == directive_head())
    Ensures(directive_head().take(6 + len(quoted_value_token())).drop(6) == quoted_value_token())
    # post-conditions-end
    # impl-start
    result = list(base)  # type: List[int]
    # PRE-PATCH skeleton: the quality-of-protection value is emitted BARE
    # (`, qop=auth, nc=`), without the surrounding double quotes.
    result = result + [44, 32, 113, 111, 112, 61, 97, 117, 116, 104, 44, 32, 110, 99, 61]
    # the count value, bare
    result = result + ncvalue
    # ', cnonce="'
    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
    # the client-nonce value
    result = result + cnonce
    # closing double quote
    result = result + [34]
    return result
    # impl-end
