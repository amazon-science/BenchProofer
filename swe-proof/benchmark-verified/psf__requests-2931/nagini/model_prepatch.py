"""Twin-artifact model for psf__requests-2931.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) When a textual-or-binary value is serialized to become the outgoing
      HTTP request body, its representation is preserved exactly: a value that
      arrives as a binary octet string stays a binary octet string (its type
      tag and its octet content are unchanged), and a value that arrives as a
      native text string stays native text. In particular a binary payload
      whose octets are not all ASCII-decodable is carried through verbatim
      rather than being run through a native-string decoder that would change
      its type (and would be undefined on non-ASCII octets).

  (2) A textual-or-binary value supplied as the query component of a URL is, by
      contrast, normalized to a native text string before being appended to the
      query: a binary octet string of ASCII octets becomes native text with the
      same characters, and a native text string is left as native text. This is
      the long-standing behaviour for query parameters and must be retained.

A value is modelled as a small object carrying a type tag (`is_bytes`) and its
content as `PSeq[int]` (octet values for a binary string, code points for text;
Nagini bans `str`/`bytes` indexing). The native-string decoder used for query
normalization is the unchanged utility callee, axiomatized as `to_native`: it
is defined only on ASCII octets for a binary input and returns the same content
as a native string there. The body path does NOT use it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def to_native(v_is_bytes: bool, v_data: PSeq[int]) -> PSeq[int]:
    """The unchanged native-string decoder (utility callee). For a native-text
    input it is the identity; for a binary input it ASCII-decodes, which is
    defined ONLY when every octet is ASCII (< 128) and yields the same content
    as native text. The result is always native text (the caller drops the
    binary tag). Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX runs the real callee against this contract).
    """
    Requires(Implies(v_is_bytes, is_ascii(v_data)))
    Ensures(Result() == v_data)
# axioms-end


# pure-start
@Pure
def is_ascii(b: PSeq[int]) -> bool:
    """Every element of the content is an ASCII octet (< 128)."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(b), b[i] < 128),
                                  [[b[i]]]))
# pure-end


class Value:
    """A textual-or-binary string value: a type tag plus its content."""

    def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_bytes) and Acc(self.data))
        Ensures(self.is_bytes == is_bytes)
        Ensures(self.data == data)
        # post-conditions-end
        # impl-start
        self.is_bytes = is_bytes  # type: bool
        self.data = data  # type: PSeq[int]
        # impl-end


def serialize_request_body(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().is_bytes) and Acc(Result().data))
    # The representation is preserved exactly: same type tag, same content.
    # A binary payload (incl. one with non-ASCII octets) stays binary.
    Ensures(Result().is_bytes == v.is_bytes)
    Ensures(Result().data == v.data)
    # post-conditions-end
    # impl-start
    nd = to_native(v.is_bytes, v.data)
    r = Value(False, nd)
    return r
    # impl-end


def normalize_query_string(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    # A binary query value must be ASCII (the long-standing contract for the
    # query component) so the native-string decoder is defined on it.
    Requires(Implies(v.is_bytes, is_ascii(v.data)))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().is_bytes) and Acc(Result().data))
    # The query value is normalized to native text with the same characters.
    Ensures(Result().is_bytes == False)
    Ensures(Result().data == v.data)
    # post-conditions-end
    # impl-start
    nd = to_native(v.is_bytes, v.data)
    r = Value(False, nd)
    return r
    # impl-end
