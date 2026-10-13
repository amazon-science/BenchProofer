"""Twin-artifact model for psf__requests-2317.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request method token may arrive either as a native text string or as a
  byte string carrying the ASCII characters of the method name (for example a
  caller passing ``b'GET'`` after having ASCII-encoded its arguments). The
  operation produces the NATIVE TEXT representation of that token: the
  sequence of characters of the method itself.

    - For a native text token the representation is the token unchanged.
    - For a byte-string token the representation is the ASCII decoding of the
      bytes, i.e. each ASCII byte becomes the character with the same value.

  In particular the representation of a byte-string token is its decoded
  content, NOT a textual rendering of the byte-string object (which would
  prepend a marker and wrap the content in quotes, turning ``b'GET'`` into the
  five-character text ``b'GET'`` and making the method unusable). The result
  is therefore the method's own characters, of the same length as the token,
  regardless of whether the token was text or bytes.

Text and byte tokens are modelled as `List[int]` of character / byte values
(Nagini bans `str` indexing); the specification is carried by the pure
sequence theory `PSeq[int]`. The method tokens of interest are ASCII (every
value < 128), so byte and character values coincide and ASCII decoding is the
identity on the carried sequence.

The coercion is the *changed* operation; it is modelled DEEPLY as a verified
sequence copy. The agreement of the deep model with the real library coercion
is checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# pure-end


def native_method(content: List[int], is_bytes: bool) -> List[int]:
    """The native text representation of a method token (`content` are its
    ASCII character / byte values; `is_bytes` records whether the token was a
    byte string). Read-only input.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(content), 1 / 2))
    # ASCII method tokens: every value is a 7-bit code, with no embedded quote
    # (39) or backslash (92) -- the regime in which a byte token's textual
    # object rendering is exactly the `b'...'` wrapping.
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(content),
                             0 <= content[k] and content[k] < 128
                             and content[k] != 39 and content[k] != 92))))
    # The representation must actually be delivered: this termination
    # obligation forbids implementations that would satisfy the value
    # postcondition only vacuously by never returning.
    Requires(MustTerminate(len(content) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the method's own characters: the carried sequence exactly,
    # of the same length, whether the token was text or bytes. For a byte token
    # this means the method characters are recovered (the token decoded), not a
    # longer textual description of the byte-string object.
    Ensures(ToSeq(Result()) == ToSeq(content))
    Ensures(len(Result()) == len(content))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result
    # impl-end
