import Mathlib
-- imports-end

/-!
Making an enumerated-choices class usable as a value inside a template.

An enumerated-choices class bundles a set of members; each member carries a
stored value together with a human-readable label, and the class exposes the
value→label association built from its members.

A template engine, when it resolves a name to a value and finds that value is
callable, will by default INVOKE it with no arguments and substitute the result.
An enumerated-choices class is itself callable — invoking it performs a value
lookup and therefore demands an argument — so invoking it with no arguments
fails, and the member/attribute the template actually wanted (e.g. a member and
then its label or value) can never be reached.

A value may carry a flag that tells the engine NOT to invoke it. The desired
behavior is that the constructed class carries this flag, so that when the engine
encounters the class as a resolved value it leaves the class untouched instead of
calling it — letting the subsequent member and attribute lookups proceed. The
value→label association the class exposes is unchanged by this.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The members'
-- (value, label) entries enter as plain data, the value→label association is
-- that same data carried through unchanged, the "do not invoke" flag is a
-- literal, and the engine's invoke decision is modeled directly as a boolean over
-- the three observables it reads (is the value callable, does it carry the
-- "do not invoke" flag, does it alter data). Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The constructed enumerated-choices class, restricted to the touched
observables:
* `value2label` — the value→label association built from the class's members;
* `doNotCallInTemplates` — whether the class is flagged so a template engine must
  NOT invoke it when it is encountered as a resolved value. -/
structure ChoicesClass where
  value2label : List (Int × String)
  doNotCallInTemplates : Bool

/-- A template engine's decision, when a resolved value is encountered, of whether
to INVOKE it with no arguments: it invokes exactly the values that are callable,
not flagged against invocation, and that do not alter data. Mirrors the engine's
resolution arm. -/
def templateWouldCall (isCallable doNotCall altersData : Bool) : Bool :=
  isCallable && !doNotCall && !altersData
-- pure-end

-- post-conditions-start
/-- The constructed class is pinned at every observable:

  * its value→label association is exactly the one built from the supplied
    members (unchanged — directive 5 frame: this component equals its input);
  * it is flagged so that a template engine encountering the class as a resolved
    value would NOT invoke it. Because such a class is callable and does not alter
    data, "would not be invoked" forces the flag to be set, which is precisely
    what lets the engine leave the class intact and resolve a member and its
    attribute against it. -/
def problem_spec_buildChoicesClass
    (memberValues : List (Int × String)) (result : ChoicesClass) : Prop :=
  result.value2label = memberValues ∧
  templateWouldCall (isCallable := true) result.doNotCallInTemplates
      (altersData := false) = false
-- post-conditions-end

-- impl-start
def implementation_buildChoicesClass
    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
  -- The value→label association is built from the class's members.
  cls := { cls with value2label := memberValues }
  -- Flag the class so a template engine leaves it intact instead of invoking it.
  cls := { cls with doNotCallInTemplates := true }
  return cls
-- impl-end

-- proof-start
theorem correct_buildChoicesClass :
    ∀ (memberValues : List (Int × String)),
      problem_spec_buildChoicesClass memberValues
        (implementation_buildChoicesClass memberValues) := by
  intro memberValues
  refine ⟨rfl, rfl⟩
-- proof-end
