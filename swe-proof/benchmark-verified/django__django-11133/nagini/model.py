"""Twin-artifact model for django__django-11133.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A value is coerced to the response body's output bytestring according to its
  runtime representation:

  (1) A value that already carries a raw octet buffer -- whether it is an
      immutable octet string or a buffer view exposing the same underlying
      octets -- is carried through as exactly those octets, with no decoding,
      re-encoding, or textual rendering. The two buffer-bearing representations
      are treated identically: the output is the buffer's octets verbatim.

  (2) A native text value is encoded to octets in the output charset.

  (3) Any other value is first rendered to its native-text form and that text is
      then encoded to octets in the output charset.

A value is modelled as a small object carrying a representation tag (`kind`),
its raw octet buffer (`buf`, meaningful for the two buffer-bearing kinds), and
the code points that are charset-encoded for the text and other kinds (`cps`;
for an "other" value these are the code points of its native-text rendering).
The output bytestring is carried in `data`. Octets and code points are
`PSeq[int]` (Nagini bans `str`/`bytes` indexing).

The charset encoder is the unchanged utility callee, axiomatized as
`charset_encode`; the buffer path does NOT use it. The text and "other" kinds
are observationally identical here (both encode their code points), so the
specification distinguishes only buffer-bearing values from the rest.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Representation tags.
KIND_OCTETS = 0   # an immutable octet string
KIND_VIEW = 1     # a buffer view exposing the same underlying octets
KIND_TEXT = 2     # a native text string
KIND_OTHER = 3    # any other value


# axioms-start
@Pure
@ContractOnly
def charset_encode(cps: PSeq[int]) -> PSeq[int]:
    """The unchanged charset encoder (utility callee): maps a sequence of code
    points to the octet sequence of its encoding in the output charset. A pure,
    deterministic function of its argument (Nagini derives determinism from
    @Pure, which is all the proof needs). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX runs the real callee against this
    contract).
    """
    Ensures(True)
# axioms-end


# pure-start
@Pure
def is_buffer_kind(kind: int) -> bool:
    """The two buffer-bearing representations: an immutable octet string and a
    buffer view exposing the same underlying octets."""
    return kind == KIND_OCTETS or kind == KIND_VIEW
# pure-end


class Value:
    """A value to be coerced to the output bytestring: a representation tag, its
    raw octet buffer, the code points encoded for text/other kinds, and the
    resulting output octets (`data`, meaningful on a result)."""

    def __init__(self, kind: int, buf: PSeq[int], cps: PSeq[int],
                 data: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
                and Acc(self.data))
        Ensures(self.kind == kind)
        Ensures(self.buf == buf)
        Ensures(self.cps == cps)
        Ensures(self.data == data)
        # post-conditions-end
        # impl-start
        self.kind = kind  # type: int
        self.buf = buf    # type: PSeq[int]
        self.cps = cps    # type: PSeq[int]
        self.data = data  # type: PSeq[int]
        # impl-end


def coerce_to_octets(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
             and Acc(v.data, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
            and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().buf) and Acc(Result().cps)
            and Acc(Result().data))
    # A buffer-bearing value (octet string OR buffer view, treated identically)
    # is carried through as exactly its underlying octets.
    Ensures(Implies(is_buffer_kind(v.kind), Result().data == v.buf))
    # A text value, and any other value (via its native-text rendering), is
    # encoded to octets in the output charset.
    Ensures(Implies(not is_buffer_kind(v.kind),
                    Result().data == charset_encode(v.cps)))
    # post-conditions-end
    # impl-start
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
    # impl-end
