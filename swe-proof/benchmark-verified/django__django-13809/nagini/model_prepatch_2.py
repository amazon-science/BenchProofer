"""Twin-artifact model for django__django-13809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A long-running development command performs a one-off validation pass on
  start-up. Two coordinated guarantees let an operator suppress that pass for
  this command from the invocation:

  (1) This command always surfaces a "skip validation" request on its
      invocation, independently of whether it is the kind of command that the
      common machinery would otherwise validate automatically. (It validates
      itself explicitly on start-up rather than through the common pre-pass, so
      it must offer the request on its own account; the request is offered
      unconditionally.)

  (2) On start-up the command emits a determinate schedule of observable
      start-up actions. The validation pass contributes two such actions, as a
      unit: announcing that validation is being performed, and running the
      validation. BOTH of these actions are emitted if and only if no skip
      request is in force. A second, independent start-up action — re-checking
      pending data-shape migrations — is ALWAYS emitted, regardless of the skip
      request; it is not part of the suppressible validation pass.

  Consequently, when a skip request is in force the start-up schedule contains
  neither the validation announcement nor the validation run, but still
  contains the migration re-check; when no skip request is in force the schedule
  contains the announcement, the validation run, and the migration re-check, in
  that order.

The single boolean input is whether the invocation carried a skip request. The
schedule of start-up actions is modelled as a `List[int]` of action codes; no
callee is axiomatized — the gating decision is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: whether this command offers the skip request, and whether
# the validation actions are emitted on start-up, are decided by pure boolean
# gating, modelled deeply below.
# axioms-end


# pure-start
# Observable start-up action codes (their identity is irrelevant beyond being
# distinct; only their presence/absence and order in the schedule is observed).
ACTION_ANNOUNCE_VALIDATION = 1   # announce that the validation pass is running
ACTION_RUN_VALIDATION = 2        # perform the validation pass
ACTION_MIGRATION_RECHECK = 3     # re-check pending data-shape migrations
# pure-end


def offers_skip_request() -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (1) This command offers the skip request unconditionally — it does not
    # depend on the common machinery deciding to validate it automatically.
    Ensures(Result())
    # post-conditions-end
    # impl-start
    # PRE-FIX skeleton (site 1, the invocation exposure): this command does NOT
    # offer the skip request on its own account — it relies on the common
    # machinery, which only surfaces the request for commands the machinery
    # validates automatically. Because this command is not one of those, the
    # request is never offered. This FAILS the (1) postcondition Result(): the
    # request must be offered unconditionally.
    return False
    # impl-end


def startup_action_schedule(skip_checks: bool) -> List[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (2a) A skip request in force => neither validation action is emitted, but
    # the migration re-check still is: the schedule is exactly [migration-recheck].
    Ensures(Implies(skip_checks,
                    ToSeq(Result()) == PSeq(ACTION_MIGRATION_RECHECK)))
    # (2b) No skip request => the announcement, the validation run, and the
    # migration re-check are all emitted, in that order.
    Ensures(Implies(not skip_checks,
                    ToSeq(Result()) == PSeq(ACTION_ANNOUNCE_VALIDATION,
                                            ACTION_RUN_VALIDATION,
                                            ACTION_MIGRATION_RECHECK)))
    # The two exact-sequence clauses above pin the schedule completely for both
    # values of the skip request. The discriminating consequences they entail:
    # the announcement and the validation run are present exactly when no skip
    # request is in force (the validation pass is announced-then-run as a unit),
    # while the migration re-check is present regardless of the skip request.
    Ensures(Implies(skip_checks, len(Result()) == 1))
    Ensures(Implies(not skip_checks, len(Result()) == 3))
    # post-conditions-end
    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        # The suppressible validation pass: announce, then run it (as a unit).
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    # The migration re-check is not part of the suppressible validation pass; it
    # always runs.
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end
