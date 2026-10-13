"""Twin-artifact model for django__django-11292.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A management command can be told from its invocation to forgo its validation
  pass before the work is done. Two coordinated guarantees express this:

  (1) The command line surfaces a "skip validation" request exactly for the
      commands that would otherwise perform validation. That is, the invocation
      parser accepts the skip request precisely when the command is one that
      requires validation; for a command that never validates, no such request
      is offered.

  (2) Whether the validation pass actually runs is decided as: it runs if and
      only if the command requires validation AND no effective skip request is
      in force. The skip request is *effective* exactly when the parser accepted
      it (guarantee 1); a skip request that the parser does not accept has no
      effect. Consequently, for a command that requires validation, a skip
      request supplied at invocation is honoured: the validation pass does not
      run.

The two boolean inputs are: whether the command requires validation, and
whether the invocation carried a skip request. No callee is axiomatized; the
decision is pure boolean logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the parser-exposure and the run/skip decision are pure
# boolean logic, modelled deeply.
# axioms-end


# pure-start
@Pure
def skip_request_offered(requires_validation: bool) -> bool:
    """Whether the invocation parser offers (accepts) a skip request. The skip
    request is offered exactly for commands that require validation."""
    return requires_validation


@Pure
def effective_skip(requires_validation: bool, requested_skip: bool) -> bool:
    """The skip request that is actually in force: a request supplied at
    invocation takes effect only when the parser offered it; otherwise it is
    dropped (treated as no request)."""
    if skip_request_offered(requires_validation):
        return requested_skip
    return False
# pure-end


def parser_offers_skip(requires_validation: bool) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (1) The skip request is offered precisely when validation is required.
    Ensures(Result() == requires_validation)
    Ensures(Result() == skip_request_offered(requires_validation))
    # post-conditions-end
    # impl-start
    # PRE-FIX skeleton: the invocation parser never offers the skip request, so
    # a request supplied at invocation is dropped for every command. This fails
    # the (1) postcondition for a command that requires validation, and in turn
    # causes will_run_validation to run validation even when a skip was asked.
    return False
    # impl-end


def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # (2) Validation runs iff it is required AND no effective skip is in force.
    Ensures(Result() == (requires_validation and not effective_skip(requires_validation, requested_skip)))
    # A command that does not require validation never runs it.
    Ensures(Implies(not requires_validation, not Result()))
    # The discriminating clause: for a command that requires validation, a skip
    # request supplied at invocation is honoured (validation does NOT run). This
    # is exactly what a pre-fix gating that drops the request fails to satisfy.
    Ensures(Implies(requires_validation and requested_skip, not Result()))
    # And without a skip request, a command that requires validation runs it.
    Ensures(Implies(requires_validation and not requested_skip, Result()))
    # post-conditions-end
    # impl-start
    skip = parser_offers_skip(requires_validation) and requested_skip
    if requires_validation and not skip:
        return True
    return False
    # impl-end
