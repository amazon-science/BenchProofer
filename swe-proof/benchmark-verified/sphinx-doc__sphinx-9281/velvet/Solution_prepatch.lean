import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under change — how a value is rendered to a
   short, human-readable piece of text for display in API documentation — is
   modeled DEEPLY in the `pure` region (`describe`). The classification of a
   value and the structured rendering of an enumerated value are concrete data
   and operations, validated against the real renderer by G-CONF; there is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The display-relevant shape of the value being rendered. Two cases matter to
   the desired behaviour:

   * `enumValue className memberName genericText` — a member of an enumerated
     type. It exposes the name of its type (`className`) and the name of the
     member (`memberName`); `genericText` is what the generic textual fallback
     would otherwise produce for it (carried so the unchanged fallback path is
     observable, mapping.md §2).
   * `plain genericText` — any other value; `genericText` is the generic textual
     description already produced for it (the existing, unchanged behaviour). -/
inductive Obj where
  | enumValue (className : String) (memberName : String) (genericText : String)
  | plain (genericText : String)
  deriving DecidableEq

/- The desired rendering. A member of an enumerated type renders as its type
   name and member name joined by a dot — a short, evaluable label — instead of
   the verbose generic fallback. Every other value keeps the generic textual
   description it already had. This is the only distinction the desired
   behaviour draws. -/
def describe : Obj → String
  | .enumValue className memberName _ => className ++ "." ++ memberName
  | .plain genericText                => genericText

@[grind] lemma describe_enum (cn mn g : String) :
    describe (.enumValue cn mn g) = cn ++ "." ++ mn := rfl
@[grind] lemma describe_plain (g : String) :
    describe (.plain g) = g := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a value to a short piece of text safe for display in API
   documentation. Desired behaviour: a member of an enumerated type is shown by
   its type name and member name joined with a dot (a concise, evaluable label),
   while every other value keeps the generic textual description it already
   received. -/
method objectDescription (obj : Obj) return (out : String)
  ensures out = describe obj
  do
    -- impl-start
    -- Pre-image skeleton: no special handling for members of an enumerated
    -- type. EVERY value falls through to the generic textual description, so a
    -- member of an enumerated type yields its verbose generic text rather than
    -- the `type.member` label the frozen spec requires. prove_correct MUST fail.
    let out : String :=
      match obj with
      | .enumValue _ _ genericText => genericText
      | .plain genericText         => genericText
    return out
    -- impl-end

prove_correct objectDescription by
  loom_solve
