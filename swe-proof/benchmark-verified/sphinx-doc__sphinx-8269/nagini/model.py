"""Twin-artifact model for sphinx-doc__sphinx-8269.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a hyperlink that carries a fragment is checked against a live server
  while fragment-checking is enabled, the responsibility of the checker is to
  classify the link's outcome. The classification it produces must reflect the
  TRANSPORT outcome whenever the server answered with an error status, in
  exactly the same way as the no-fragment path already does:

    * an error status in the client range (>= 400, < 500) other than the
      "authorization required" status, and any error status in the server
      range (>= 500, < 600) other than the "service unavailable" status, is a
      FAILED result whose accompanying datum is the transport error;
    * the "authorization required" client status is a WORKING result;
    * the "service unavailable" server status is an IGNORED result;
    * a non-error status (< 400) leaves the fragment question to be answered:
      the result is WORKING when the fragment is present in the document and
      FAILED (with the fragment-absent datum) when it is not.

  The point pinned here is that the transport error is consulted BEFORE the
  document is searched for the fragment, so a server error is never mis-reported
  as a missing fragment. The datum that accompanies a failed error-status result
  is the transport error, never the fragment-absent datum.

The HTTP status is modelled as an ``int``; whether the fragment is present is a
single observable bit (the verdict of the unchanged document scanner, abstracted
to a boolean). The transport-status gate (the callee that raises on an error
status) is the unchanged library routine, axiomatized as a contract-only
function whose raise/no-raise behaviour is keyed on the status range. The
transport error it raises is a user-defined exception class (a builtin exception
in an ``Exsures`` crashes the Nagini translator).

The classification is returned as a pair of small integer codes: a status class
(WORKING / FAILED / IGNORED) and a datum kind (none / transport-error /
fragment-absent), so the discriminating observation -- a server-error link is
FAILED with the TRANSPORT-ERROR datum rather than the FRAGMENT-ABSENT datum --
is expressible.

Classifying one link is a bounded, straight-line computation: the checker MUST
actually deliver its classification (a total-correctness obligation, carried as
MustTerminate in the precondition). Nagini is a partial-correctness verifier by
default, so without this obligation an implementation that diverges before
returning (e.g. an inserted ``while True: pass``) would satisfy every value
postcondition vacuously while the real checker thread hangs and never reports
the link.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TransportError(Exception):
    """The out-of-band signal raised by the transport-status gate when the
    server answered with an error status. A user-defined stand-in for the
    library's HTTP error (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md s2)."""
    pass


class FragmentAbsent(Exception):
    """The fragment-absent signal raised after the document scan when the
    fragment is not present (the generic 'fragment not found' path). Distinct
    from the transport error so the two failed data are not conflated."""
    pass


# axioms-start
@ContractOnly
def raise_on_error_status(status: int) -> None:
    """The unchanged transport-status gate. Its only observable is whether the
    answered status falls in the error ranges: it returns normally on a
    non-error status (< 400 or >= 600) and signals the SAME out-of-band
    transport error on any status in [400, 600). Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real gate is a pair of range checks followed by a return or a raise —
    # a bounded computation that always delivers its verdict (exercised on
    # every axiom_check.py input). It therefore takes and discharges a
    # termination obligation, so a caller holding one may defer to it.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on a non-error status.
    Ensures(status < 400 or status >= 600)
    # The transport error is signalled EXACTLY on an error status.
    Exsures(TransportError, 400 <= status and status < 600)
    # post-conditions-end
# axioms-end


# pure-start
@Pure
def is_error_status(status: int) -> bool:
    """A status in [400, 600) is a transport error."""
    return 400 <= status and status < 600


@Pure
def WORKING() -> int:
    return 0


@Pure
def FAILED() -> int:
    return 1


@Pure
def IGNORED() -> int:
    return 2


@Pure
def DATUM_NONE() -> int:
    return 0


@Pure
def DATUM_TRANSPORT() -> int:
    return 1


@Pure
def DATUM_FRAGMENT_ABSENT() -> int:
    return 2
# pure-end


def classify_fragment_link(status: int, fragment_present: bool) -> Tuple[int, int]:
    # pre-conditions-start
    # TERMINATION: classifying one link is a bounded, straight-line dispatch
    # and must actually ANSWER. Nagini is a partial-correctness verifier by
    # default, so without this obligation a non-terminating implementation
    # (e.g. `while True: pass` before the return) satisfies every Ensures
    # vacuously; the real checker always returns its classification.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is a (status-class, datum-kind) pair.
    # (1) An "authorization required" client status (401) is WORKING.
    Ensures(Implies(status == 401, Result() == (WORKING(), DATUM_NONE())))
    # (2) A "service unavailable" server status (503) is IGNORED, carrying the
    #     transport datum.
    Ensures(Implies(status == 503, Result() == (IGNORED(), DATUM_TRANSPORT())))
    # (3) Any OTHER error status is FAILED, and its datum is the TRANSPORT error
    #     -- never the fragment-absent datum, regardless of fragment_present.
    #     This is the property the change establishes: the transport error is
    #     consulted before the document is searched.
    Ensures(Implies(is_error_status(status) and status != 401 and status != 503,
                    Result() == (FAILED(), DATUM_TRANSPORT())))
    # (4) A non-error status defers to the fragment verdict: WORKING when the
    #     fragment is present, FAILED (fragment-absent datum) when it is not.
    Ensures(Implies(not is_error_status(status) and fragment_present,
                    Result() == (WORKING(), DATUM_NONE())))
    Ensures(Implies(not is_error_status(status) and not fragment_present,
                    Result() == (FAILED(), DATUM_FRAGMENT_ABSENT())))
    # (5) A failed error-status result NEVER carries the fragment-absent datum.
    Ensures(Implies(is_error_status(status) and Result()[0] == FAILED(),
                    Result()[1] == DATUM_TRANSPORT()))
    # post-conditions-end
    # impl-start
    try:
        # Read the whole document and obtain the fragment verdict.
        found = fragment_present
        # The transport-status gate is consulted BEFORE acting on the verdict.
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())
    # impl-end
