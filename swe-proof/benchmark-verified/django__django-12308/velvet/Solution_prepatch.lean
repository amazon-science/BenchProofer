import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The display choice for a JSON-typed value is modeled
   DEEPLY in the `pure` region (`jsonDisplay`): the outcomes of the two
   surrounding helpers the choice consults — preparing the value as JSON text,
   and the generic textual rendering — are carried as observable fields of the
   value view and validated against the real helpers by axiom_check.py (G-AX);
   there is no module-level `axiom` the proof consumes. -/
-- axioms-end

-- pure-start
/- The outcome of preparing a value as JSON text: either a successfully
   serialized JSON string, or a failure because the value has no JSON
   serialization (a non-serializable value). -/
inductive PrepResult where
  | json (text : String)
  | unserializable
  deriving DecidableEq

/- The observable facts about the value being rendered that the display choice
   depends on:
   * `present`  — whether the value counts as present (non-empty);
   * `prep`     — the outcome of preparing the value as JSON text;
   * `generic`  — the generic textual rendering used when no JSON form applies
                  (which renders an absent value as the empty marker).
   These are produced by the surrounding helpers; choosing among them is the
   modeled behaviour. The Lean↔repo bijection is in mapping.md §2. -/
structure ValueView where
  present : Bool
  prep : PrepResult
  generic : String
  deriving DecidableEq

/- The display chosen for a JSON-typed field's value when rendered read-only.
   Desired behaviour: a present value is shown as its JSON text; a present value
   with no JSON serialization falls back to the generic rendering; an absent
   value also uses the generic rendering. -/
def jsonDisplay (v : ValueView) : String :=
  if v.present then
    match v.prep with
    | PrepResult.json text => text
    | PrepResult.unserializable => v.generic
  else v.generic
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a JSON-typed field's stored value for read-only display. A present
   value is shown as its JSON text; a present value that cannot be serialized to
   JSON, and an absent value, are shown via the generic rendering instead. -/
method displayJson (v : ValueView) return (out : String)
  ensures out = jsonDisplay v
  do
    -- impl-start
    -- Pre-image skeleton: a JSON-typed value has no dedicated arm and falls
    -- through to the generic rendering unconditionally — so a present,
    -- serializable value is shown via `generic` instead of its JSON text. The
    -- frozen spec requires `jsonDisplay`, so prove_correct MUST fail.
    let out : String := v.generic
    return out
    -- impl-end

prove_correct displayJson by
  loom_solve
  simp [jsonDisplay]
