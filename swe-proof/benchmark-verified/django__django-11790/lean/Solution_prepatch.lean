import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only computed value is
-- a total integer-valued selection over an optional configured bound (modeled
-- deeply as `usernameMaxLength`, below); the attribute store is modeled concretely
-- as an association list. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- A rendered text-input field carrying its effective maximum length and the
integer-valued HTML attributes of its widget (an association list keyed by
attribute name). Only the touched components are modeled. -/
structure UField where
  maxLength : Nat
  attrs : List (String × Nat)
  deriving Repr, DecidableEq

/-- The effective maximum length: the configured bound when it is present and
positive, otherwise the standard fallback of 254. A configured bound that is
absent or zero is treated as unset. -/
def usernameMaxLength : Option Nat → Nat
  | none        => 254
  | some 0      => 254
  | some (n+1)  => n + 1

/-- Look up an integer-valued attribute by name (the first binding wins). -/
def attrLookup (attrs : List (String × Nat)) (k : String) : Option Nat :=
  (attrs.find? (fun p => p.1 = k)).map (·.2)

/-- Set an integer-valued attribute, overwriting any existing binding for the
same name and otherwise inserting it. -/
def setAttr (attrs : List (String × Nat)) (k : String) (v : Nat) : List (String × Nat) :=
  attrs.filter (fun p => p.1 ≠ k) ++ [(k, v)]
-- pure-end

-- post-conditions-start
/-- Configuring the username field from an optional configured length bound and
the field's initial widget attributes yields a field whose effective maximum
length equals the resolved bound, and whose widget attributes are exactly the
input attributes with the `maxlength` attribute set to that same resolved bound
(overwriting any prior `maxlength` and preserving every other attribute). Pinning
the attribute map to this concrete update — rather than only its `maxlength`
lookup — frames the whole result against the input, so no implementation that
fails to perform the update can satisfy the spec. -/
def problem_spec_authUsernameField
    (configuredMax : Option Nat) (initAttrs : List (String × Nat))
    (result : UField) : Prop :=
  result.maxLength = usernameMaxLength configuredMax ∧
  result.attrs = setAttr initAttrs "maxlength" (usernameMaxLength configuredMax)
-- post-conditions-end

-- impl-start
def implementation_authUsernameField
    (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
  let umax := usernameMaxLength configuredMax
  let mut field : UField := { maxLength := 0, attrs := initAttrs }
  field := { field with maxLength := umax }
  return field
-- impl-end

-- proof-start
theorem correct_authUsernameField :
    ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
      problem_spec_authUsernameField configuredMax initAttrs
        (implementation_authUsernameField configuredMax initAttrs) := by
  intro configuredMax initAttrs
  refine ⟨rfl, ?_⟩
  -- carries the gold proof shape: the widget attribute map should be the input
  -- with `maxlength` set, but the buggy impl left the attributes untouched
  -- (`initAttrs`), so this clause is UNCLOSABLE — exactly the G-DIFF signal.
  rfl
-- proof-end
