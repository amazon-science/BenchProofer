"""Twin-artifact model for django__django-16145.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the development server announces the address it is listening on, the
  address that is shown to the operator is derived from the bound address as
  follows:

    * If the bound address is a bracketed literal IPv6 address, the shown
      address is that address enclosed in square brackets (so it reads as a
      valid host part of a URL).

    * Otherwise, if the bound address is the single-character wildcard "0",
      the shown address is its fully-written unspecified-IPv4 equivalent
      "0.0.0.0" — because "0" binds every IPv4 interface yet is not a host a
      browser can follow, whereas "0.0.0.0" denotes the same binding and is a
      usable URL host.

    * Otherwise the shown address is the bound address unchanged.

  These cases are tried in this priority order; in particular the bracketing
  rule takes precedence over the wildcard-expansion rule.

Addresses are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
single code point '0' is U+0030 (48); '.' is U+002E (46); '[' is U+005B (91);
']' is U+005D (93). No callee is axiomatized: the shown address is a pure
piecewise transcription of the bound address, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the shown address is a pure, piecewise transcription of
# the bound address (bracket-wrap / wildcard-expand / identity) over code
# points. Nothing is an unchanged opaque callee whose contract the proof needs.
# axioms-end


# pure-start
@Pure
def wildcard_short() -> PSeq[int]:
    # "0"  (the single-character wildcard form)
    return PSeq(48)


@Pure
def wildcard_dotted() -> PSeq[int]:
    # "0.0.0.0"  (the fully-written unspecified-IPv4 form)
    return PSeq(48, 46, 48, 46, 48, 46, 48)


@Pure
def shown_address(addr: PSeq[int], raw_ipv6: bool) -> PSeq[int]:
    """The address shown to the operator, derived from the bound address.

    Priority order: bracketed-IPv6 first, then the "0" -> "0.0.0.0" wildcard
    expansion, then the bound address unchanged.
    """
    if raw_ipv6:
        return PSeq(91) + addr + PSeq(93)        # "[" + addr + "]"
    if addr == wildcard_short():
        return wildcard_dotted()
    return addr
# pure-end


def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(addr), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(addr), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The shown address is the piecewise transcription of the bound address.
    Ensures(ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    c = 0
    if raw_ipv6:
        result = [91]
        i = 0
        while i < len(addr):
            # invariants-start
            Invariant(Acc(list_pred(addr), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(addr))
            Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
            Invariant(MustTerminate(len(addr) - i + 1))
            # invariants-end
            c = addr[i]
            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
            result = result + [c]
            i = i + 1
        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
        result = result + [93]
        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
    elif ToSeq(addr) == wildcard_short():
        result = [48, 46, 48, 46, 48, 46, 48]
        Assert(ToSeq(result) == wildcard_dotted())
        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
    else:
        i = 0
        while i < len(addr):
            # invariants-start
            Invariant(Acc(list_pred(addr), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(addr))
            Invariant(ToSeq(addr) != wildcard_short())
            Invariant(ToSeq(result) == ToSeq(addr).take(i))
            Invariant(MustTerminate(len(addr) - i + 1))
            # invariants-end
            c = addr[i]
            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
            result = result + [c]
            i = i + 1
        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
        Assert(ToSeq(result) == ToSeq(addr))
        Assert(ToSeq(addr) != wildcard_short())
        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
    return result
    # impl-end
