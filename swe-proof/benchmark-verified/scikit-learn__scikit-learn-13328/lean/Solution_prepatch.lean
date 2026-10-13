import Mathlib
-- imports-end

/-!
An input feature array carries an *element type* (its numeric storage kind).
Before numerical processing, a fitting routine normalizes that element type
against a predetermined set of accepted floating-point types.

The behavior modeled here is that normalization. There is a set of accepted
floating-point element types (single- and double-precision). If the array's
original element type is already one of the accepted floating types, it is left
unchanged. Otherwise — for any non-accepted element type, including a boolean or
integer storage kind — the element type is converted to the default
double-precision floating type. In particular the normalized element type is
always one of the accepted floating types, so subsequent signed arithmetic on the
array is well defined regardless of how the input was originally stored.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom by this specification. The
-- element-type normalization is the substantive behavior and is modeled DEEPLY
-- below (an A-reference, validated against the real routine by axiom_check.py),
-- not axiomatized. Hence no `opaque`/`axiom` declaration.
-- axioms-end

-- pure-start
/-- The storage element type of an input array (the representative kinds reached
by the public input contract). -/
inductive NpKind where
  | float64
  | float32
  | bool
  | int64
  | object
  deriving DecidableEq, Repr

/-- The accepted floating-point element types, in priority order. The first is the
default chosen when a conversion is required. -/
def acceptedKinds : List NpKind := [NpKind.float64, NpKind.float32]

/-- The double-precision floating type used as the default conversion target. -/
def defaultKind : NpKind := NpKind.float64

/-- An element type is floating iff it is one of the accepted kinds. -/
def isFloating (k : NpKind) : Bool := k ∈ acceptedKinds
-- pure-end

-- post-conditions-start
/-- Element-type normalization against the accepted floating set. If the original
element type is already accepted, the result equals it unchanged (frame: an
already-floating input is not touched). Otherwise the result is the default
double-precision floating type. Both branches are pinned to the input, so a
non-accepted input — e.g. a boolean storage kind — must yield the floating
default, never its unconverted original type. -/
def problem_spec_prepareInput (orig : NpKind) (result : NpKind) : Prop :=
  (orig ∈ acceptedKinds → result = orig) ∧
  (orig ∉ acceptedKinds → result = defaultKind)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy): the generic "numeric" request converts only an object
-- storage kind to floating; every other non-floating kind (in particular a
-- boolean array) is left with its original element type — no conversion happens.
def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
  let mut dt := orig
  if orig = NpKind.object then
    dt := defaultKind
  return dt
-- impl-end

-- proof-start
theorem correct_prepareInput :
    ∀ (orig : NpKind),
      problem_spec_prepareInput orig (implementation_prepareInput orig) := by
  intro orig
  unfold problem_spec_prepareInput implementation_prepareInput
  simp only [Id.run]
  by_cases h : orig ∈ acceptedKinds
  · refine ⟨fun _ => ?_, fun hc => absurd h hc⟩
    simp only [h, if_true]; rfl
  · refine ⟨fun hc => absurd hc h, fun _ => ?_⟩
    simp only [h, if_false]; rfl
-- proof-end
