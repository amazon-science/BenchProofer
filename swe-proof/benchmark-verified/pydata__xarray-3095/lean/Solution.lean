import Mathlib
-- imports-end

/-!
Copying an index-backed array value.

An index-backed array is a wrapper around a sequence of element values together
with an explicitly recorded element type (its `dtype`). The element type is a
distinct, stored attribute of the wrapper: it can be finer-grained than what one
would re-derive purely from the underlying sequence (for instance a fixed-width
text element type carries information that a re-derivation would flatten to the
generic catch-all element type).

Copying such a wrapper — whether a deep copy (its values are duplicated) or a
shallow copy (its values are shared) — must reproduce the value faithfully: the
copy carries the same element values, the same underlying-sequence element type,
and crucially the same *stored* element type as the original. Copying never
re-derives the element type from the sequence; it preserves the one that was
recorded. Surrounding metadata of the containing variable (its dimension names
and its attributes) is likewise carried over unchanged.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Copying is spelled out
-- concretely: the value sequence is carried over (content-preserving for both
-- deep and shallow copies) and every recorded attribute is reproduced verbatim.
-- axioms-end

-- pure-start
/-- A recorded element type. `unicode w` is a fixed-width text element type of
width `w`; `object` is the generic catch-all element type; `other code` is any
other concrete element type (identified by a code). -/
inductive Dtype
  | unicode (width : Nat)
  | object
  | other (code : Nat)
  deriving DecidableEq

/-- An index-backed array value: a sequence of element values, the element type
reported by the underlying sequence (`native`), and the separately recorded
element type of the wrapper (`dtype`). -/
structure IndexData where
  values : List String
  native : Dtype
  dtype  : Dtype

/-- A variable wrapping an index-backed array, with its dimension names and
attributes alongside the data. -/
structure IVar where
  dims  : List String
  attrs : List (String × String)
  data  : IndexData
-- pure-end

-- post-conditions-start
/-- A copy (`deep` or shallow) of an index-backed variable reproduces every
component of the original: same dimension names, same attributes, same element
values, same underlying-sequence element type, and the same *stored* element
type. The stored element type is preserved as recorded — never re-derived from
the sequence. -/
def problem_spec_copy (deep : Bool) (v : IVar) (result : IVar) : Prop :=
  result.dims = v.dims ∧
  result.attrs = v.attrs ∧
  result.data.values = v.data.values ∧
  result.data.native = v.data.native ∧
  result.data.dtype = v.data.dtype
-- post-conditions-end

-- impl-start
def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
  -- it on a shallow copy (content is identical either way), and re-attach the
  -- ORIGINAL stored element type rather than re-deriving one.
  let mut arr := v.data.values
  if deep then
    arr := v.data.values
  let newData : IndexData :=
    { values := arr, native := v.data.native, dtype := v.data.dtype }
  return { dims := v.dims, attrs := v.attrs, data := newData }
-- impl-end

-- proof-start
theorem correct_copy :
    ∀ (deep : Bool) (v : IVar),
      problem_spec_copy deep v (implementation_copy deep v) := by
  intro deep v
  unfold problem_spec_copy implementation_copy
  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
