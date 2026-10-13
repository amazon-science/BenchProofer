"""Twin-artifact model for django__django-13279.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A small key-value record is serialized to a transportable frame so that it
  can be reconstructed later. Two on-the-wire frame formats coexist during a
  compatibility window:

    * a legacy frame, which a legacy reader can invert; and
    * a modern frame, which the legacy reader does NOT accept.

  A configuration flag selects the compatibility regime. When the flag selects
  the legacy regime, the serializer MUST emit a frame that the legacy reader can
  read back to the original record -- i.e. the round trip "serialize then
  legacy-read" is the identity on the record. When the flag selects the modern
  regime, the serializer emits the modern frame carrying the record, so the
  round trip "serialize then modern-read" is likewise the identity: the modern
  reader accepts a modern frame whose carried digest matches the freshly
  recomputed modern digest of the payload and returns that payload.

  The legacy frame carries a keyed digest of the record's payload alongside the
  payload itself; the legacy reader accepts a frame only when it is a legacy
  frame whose carried digest matches the freshly recomputed digest of the
  payload, in which case it returns that payload, and otherwise yields the empty
  record. Because the modern frame is not a legacy frame, feeding a modern frame
  to the legacy reader yields the empty record -- which is why, in the legacy
  regime, emitting a modern frame would lose the record on read-back.

A frame is modelled as a small object carrying a format tag (`tag`), the carried
keyed digest (`mac`), and the payload code units (`payload`). The payload is a
`PSeq[int]` of octet/code values (Nagini bans `bytes`/`str` indexing). The two
digest utilities and the modern serializer are unchanged utility callees,
axiomatized as `keyed_digest`, `modern_digest` and `modern_serialize`; the
legacy framing and both readers are modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Frame format tags.
FMT_LEGACY = 0   # a legacy frame the legacy reader can invert
FMT_MODERN = 1   # a modern frame the legacy reader does not accept

# Compatibility-regime selector values.
ALGO_LEGACY = 0  # the flag value selecting the legacy regime
ALGO_MODERN = 1  # the flag value selecting the modern regime


# axioms-start
@Pure
@ContractOnly
def keyed_digest(payload: PSeq[int]) -> PSeq[int]:
    """The unchanged keyed-MAC hex digest utility (a salted keyed hash, rendered
    as hex). A pure, deterministic function of its argument -- Nagini derives the
    one property the proof needs (equal payloads give equal digests) from @Pure.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)


@Pure
@ContractOnly
def modern_digest(payload: PSeq[int]) -> PSeq[int]:
    """The unchanged modern keyed digest utility (the signature the modern
    serializer computes over the carried payload). A pure, deterministic
    function of its argument -- Nagini derives the one property the proof needs
    (equal payloads give equal digests) from @Pure.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)


@ContractOnly
def modern_serialize(payload: PSeq[int]) -> 'Frame':
    """The unchanged modern signed-serializer callee. Its output is a modern
    frame -- NOT a legacy frame, so the legacy reader does not accept it --
    carrying exactly the given payload together with that payload's freshly
    computed modern digest, so the modern reader recovers exactly that payload.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(2))
    Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
    Ensures(Result().tag == FMT_MODERN)
    Ensures(Result().mac == modern_digest(payload))
    Ensures(Result().payload == payload)
# axioms-end


# pure-start
@Pure
def empty_payload() -> PSeq[int]:
    """The empty record's payload."""
    return PSeq(0).take(0)


@Pure
def legacy_read(tag: int, mac: PSeq[int], payload: PSeq[int]) -> PSeq[int]:
    """The legacy reader, on a frame's fields: accept the frame only when it is a
    legacy frame whose carried digest matches the recomputed digest of the
    payload, returning that payload; otherwise yield the empty record."""
    if tag == FMT_LEGACY and mac == keyed_digest(payload):
        return payload
    return empty_payload()


@Pure
def modern_read(tag: int, mac: PSeq[int], payload: PSeq[int]) -> PSeq[int]:
    """The modern reader, on a frame's fields: accept the frame only when it is a
    modern frame whose carried digest matches the freshly recomputed modern
    digest of the payload, returning that payload; otherwise yield the empty
    record."""
    if tag == FMT_MODERN and mac == modern_digest(payload):
        return payload
    return empty_payload()
# pure-end


class Frame:
    """A serialized frame: a format tag, the carried keyed digest, and the
    payload code units."""

    def __init__(self, tag: int, mac: PSeq[int], payload: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.tag) and Acc(self.mac) and Acc(self.payload))
        Ensures(self.tag == tag)
        Ensures(self.mac == mac)
        Ensures(self.payload == payload)
        # post-conditions-end
        # impl-start
        self.tag = tag          # type: int
        self.mac = mac          # type: PSeq[int]
        self.payload = payload  # type: PSeq[int]
        # impl-end


def serialize(payload: List[int], algorithm: int) -> Frame:
    # pre-conditions-start
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
    # In the legacy regime, the round trip "serialize then legacy-read" recovers
    # the original record exactly: the emitted frame is read back to the input
    # payload by the legacy reader.
    Ensures(Implies(algorithm == ALGO_LEGACY,
                    legacy_read(Result().tag, Result().mac, Result().payload)
                    == ToSeq(payload)))
    # In the modern regime, the emitted frame is a modern frame (so the legacy
    # reader would not accept it) and the round trip "serialize then
    # modern-read" recovers the original record exactly: the emitted frame is
    # read back to the input payload by the modern reader.
    Ensures(Implies(algorithm != ALGO_LEGACY,
                    Result().tag == FMT_MODERN))
    Ensures(Implies(algorithm != ALGO_LEGACY,
                    modern_read(Result().tag, Result().mac, Result().payload)
                    == ToSeq(payload)))
    # post-conditions-end
    # impl-start
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))
    # impl-end
