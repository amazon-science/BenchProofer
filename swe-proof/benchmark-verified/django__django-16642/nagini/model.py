"""Twin-artifact model for django__django-16642.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a file response derives its content type automatically, the content type
  guessed from the file name is paired with a detected compression scheme (the
  "encoding"). Serving a compressed payload under the underlying (uncompressed)
  content type lets user agents silently decompress it, which is undesirable.
  The desired behaviour is therefore: every recognised compression scheme is
  mapped to its OWN dedicated content type, and the originally guessed content
  type is used only when no compression scheme was recognised.

  The set of recognised compression schemes that must each be mapped to a
  dedicated content type is exactly:

      "br"       -> "application/x-brotli"
      "bzip2"    -> "application/x-bzip"
      "compress" -> "application/x-compress"
      "gzip"     -> "application/gzip"
      "xz"       -> "application/x-xz"

  For any other encoding token (including the empty token meaning "no
  compression detected") the guessed content type passes through unchanged.

Strings (the encoding token and the content-type values) are modelled as
`List[int]` of Unicode code points (Nagini bans `str` indexing); the
specification is carried by the pure sequence theory `PSeq[int]`.

There are no axiomatized callees: the modelled operation is the table lookup
itself, which is fully expressible. The function receives the already-guessed
(content_type, encoding) pair as inputs; how that pair is obtained is unchanged
by the behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none: the modelled table-lookup operation is fully expressible; the
#  unchanged producer of the (content_type, encoding) pair is not consumed.)
# axioms-end


# pure-start
@Pure
def tok_br() -> PSeq[int]:
    # "br"
    return PSeq(98, 114)


@Pure
def tok_bzip2() -> PSeq[int]:
    # "bzip2"
    return PSeq(98, 122, 105, 112, 50)


@Pure
def tok_compress() -> PSeq[int]:
    # "compress"
    return PSeq(99, 111, 109, 112, 114, 101, 115, 115)


@Pure
def tok_gzip() -> PSeq[int]:
    # "gzip"
    return PSeq(103, 122, 105, 112)


@Pure
def tok_xz() -> PSeq[int]:
    # "xz"
    return PSeq(120, 122)


@Pure
def ct_brotli() -> PSeq[int]:
    # "application/x-brotli"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105)


@Pure
def ct_bzip() -> PSeq[int]:
    # "application/x-bzip"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112)


@Pure
def ct_compress() -> PSeq[int]:
    # "application/x-compress"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115)


@Pure
def ct_gzip() -> PSeq[int]:
    # "application/gzip"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112)


@Pure
def ct_xz() -> PSeq[int]:
    # "application/x-xz"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122)


@Pure
def is_known_encoding(enc: PSeq[int]) -> bool:
    """True iff the encoding token is one of the recognised compression
    schemes that must each receive a dedicated content type."""
    return (enc == tok_br() or enc == tok_bzip2() or enc == tok_compress()
            or enc == tok_gzip() or enc == tok_xz())


@Pure
def dedicated_type(enc: PSeq[int]) -> PSeq[int]:
    """The dedicated content type for a recognised compression scheme.

    Defined (non-empty) on exactly the five recognised tokens; the empty
    sequence stands for "no dedicated type" on any other token."""
    if enc == tok_br():
        return ct_brotli()
    if enc == tok_bzip2():
        return ct_bzip()
    if enc == tok_compress():
        return ct_compress()
    if enc == tok_gzip():
        return ct_gzip()
    if enc == tok_xz():
        return ct_xz()
    return PSeq(0).take(0)


@Pure
def resolved_type(content_type: PSeq[int], enc: PSeq[int]) -> PSeq[int]:
    """The content type after applying the compression-scheme table: the
    dedicated type for a recognised scheme, otherwise the guessed type."""
    if is_known_encoding(enc):
        return dedicated_type(enc)
    return content_type
# pure-end


def select_content_type(content_type: List[int], encoding: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(content_type), 1 / 2))
    Requires(Acc(list_pred(encoding), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content_type), 1 / 2))
    Ensures(Acc(list_pred(encoding), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the table lookup: dedicated type if the encoding is one of
    # the recognised compression schemes, otherwise the guessed content type.
    Ensures(ToSeq(Result()) == resolved_type(ToSeq(content_type), ToSeq(encoding)))
    # Every recognised compression scheme maps to its dedicated, non-empty
    # content type (so a compressed payload is never served under the guessed
    # uncompressed type). The two clauses for "br" and "compress" carry the
    # discriminating behaviour.
    Ensures(Implies(ToSeq(encoding) == tok_br(),
                    ToSeq(Result()) == ct_brotli()))
    Ensures(Implies(ToSeq(encoding) == tok_bzip2(),
                    ToSeq(Result()) == ct_bzip()))
    Ensures(Implies(ToSeq(encoding) == tok_compress(),
                    ToSeq(Result()) == ct_compress()))
    Ensures(Implies(ToSeq(encoding) == tok_gzip(),
                    ToSeq(Result()) == ct_gzip()))
    Ensures(Implies(ToSeq(encoding) == tok_xz(),
                    ToSeq(Result()) == ct_xz()))
    # When the encoding is not a recognised scheme the guessed type is kept.
    Ensures(Implies(not is_known_encoding(ToSeq(encoding)),
                    ToSeq(Result()) == ToSeq(content_type)))
    # post-conditions-end
    # impl-start
    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result
    # impl-end
