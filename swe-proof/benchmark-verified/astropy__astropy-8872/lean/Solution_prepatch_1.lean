import Mathlib
-- imports-end

/-!
Choosing the element type used to store a numeric array when a unit is attached
to it.

When no explicit element type is requested, the stored array keeps the element
type of its input, with one family of exceptions: inputs whose element type
cannot itself represent fractional values — the integer and unsigned-integer
types — are stored using the default floating type instead. On the general
construction path one further exception applies: an input whose elements are
held as generic Python objects is likewise stored using the default floating
type. Every floating element type (including the lower-precision ones) and every
complex element type is preserved exactly as given; on the general path a
structured/record element type is also preserved.

Two situations are described: the general construction of a freshly materialised
array, and the fast reuse of an input that already carries a unit. They differ
only in whether the generic-object exception applies.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- driven entirely by the element type's category (its `kind`), which is taken as
-- a direct observation of the input element type rather than computed by a
-- separate routine, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An element type of a numeric array, carrying exactly the observations the
storage-type decision depends on.
* `kind` — the category code of the element type: `'i'` signed integer, `'u'`
  unsigned integer, `'f'` floating, `'b'` boolean, `'c'` complex, `'O'` generic
  object, `'V'` structured/record, `'S'`/`'U'` text, etc.;
* `canHoldSingle` — whether the type can hold a single-precision floating value
  without loss;
* `structured` — whether the type is a structured/record type. -/
structure DType where
  kind : Char
  canHoldSingle : Bool
  structured : Bool
deriving DecidableEq, Repr

/-- The default floating element type used when an input must be promoted: a
floating type that holds a single-precision value and is not structured. -/
def floatDType : DType := { kind := 'f', canHoldSingle := true, structured := false }

/-- On the general construction path, an input element type is promoted to the
default floating type iff it is a signed integer, an unsigned integer, or a
generic-object type. Every other category — floating (of any precision),
boolean, complex, structured, text — is kept as given. -/
def promoteGeneral (dt : DType) : Bool :=
  dt.kind = 'i' || dt.kind = 'u' || dt.kind = 'O'

/-- On the fast reuse path, an input element type is promoted to the default
floating type iff it is a signed or unsigned integer. The generic-object
exception does not apply here. -/
def promoteReuse (dt : DType) : Bool :=
  dt.kind = 'i' || dt.kind = 'u'
-- pure-end

-- post-conditions-start
/-- General construction: the stored element type is the default floating type
when the input element type is promoted, and otherwise is exactly the input
element type. -/
def problem_spec_resolveDtype (dt : DType) (result : DType) : Prop :=
  result = if promoteGeneral dt then floatDType else dt
-- post-conditions-end

-- impl-start
def implementation_resolveDtype (dt : DType) : DType := Id.run do
  let mut result := dt
  -- pre-patch skeleton: promote unless the type can hold a single-precision
  -- value or is structured, OR the type is a generic-object type.
  if (!(dt.canHoldSingle || dt.structured)) || dt.kind = 'O' then
    result := floatDType
  return result
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against the
-- pre-patch impl it cannot close: a lower-precision floating type
-- (`kind = 'f'`, `canHoldSingle = false`) is NOT promoted by the spec's
-- `promoteGeneral` but IS promoted by this impl's gate, so the `Id.run` term and
-- the spec's `if`-expression disagree on that branch and `split <;> rfl` fails.
theorem correct_resolveDtype :
    ∀ (dt : DType),
      problem_spec_resolveDtype dt (implementation_resolveDtype dt) := by
  intro dt
  unfold problem_spec_resolveDtype implementation_resolveDtype
  simp only [Id.run]
  split <;> rfl
-- proof-end

-- post-conditions-start
/-- Fast reuse: the reused input keeps its element type unless that type is
promoted, in which case the default floating type is used. -/
def problem_spec_reuseDtype (dt : DType) (result : DType) : Prop :=
  result = if promoteReuse dt then floatDType else dt
-- post-conditions-end

-- impl-start
def implementation_reuseDtype (dt : DType) : DType := Id.run do
  let mut result := dt
  if promoteReuse dt then
    result := floatDType
  return result
-- impl-end

-- proof-start
theorem correct_reuseDtype :
    ∀ (dt : DType),
      problem_spec_reuseDtype dt (implementation_reuseDtype dt) := by
  intro dt
  unfold problem_spec_reuseDtype implementation_reuseDtype
  simp only [Id.run]
  split <;> rfl
-- proof-end
