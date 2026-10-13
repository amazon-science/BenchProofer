import Mathlib
-- imports-end

/-!
Forming the canonical symbolic sum of a list of matrix-valued terms.

A symbolic sum of matrices is built from terms that are either matrix-valued
(a named matrix, or the additive-identity matrix of the common shape) and is
simplified to a canonical form. The simplification drops every additive-identity
term and orders the surviving named terms canonically.

The key property pinned here concerns what kind of object the simplified sum is:
the sum of matrix-valued terms is itself a *matrix-valued* result — in
particular, when every term is the identity matrix the result is the
identity *matrix* (which still carries a shape), never a shapeless scalar zero.
This matters because the result is consumed downstream as a matrix (its shape
is read); a scalar zero in its place has no shape and breaks that consumer.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the canonicalization of a
-- matrix sum (dropping identity terms, ordering the survivors) is spelled out
-- with concrete operations over the term list.
-- axioms-end

-- pure-start
/-- A term of a symbolic matrix sum: the additive-identity *scalar* (a shapeless
zero that may be injected as a seed), the additive-identity *matrix* (a zero
that carries a shape), or a named matrix. -/
inductive MatSumTerm where
  | scalarZero
  | zeroMatrix
  | named (name : String)
deriving DecidableEq, Repr

/-- The outcome of canonicalizing a matrix sum: either a shapeless scalar (the
degenerate, shape-losing outcome) or a matrix-valued result carrying the list of
surviving named terms (the empty list denotes the identity matrix). -/
inductive MatSum where
  | scalar
  | matrix (names : List String)
deriving DecidableEq, Repr

/-- The named matrices surviving identity-term elimination, in input order. -/
def survivingNames (terms : List MatSumTerm) : List String :=
  terms.filterMap (fun t => match t with | .named n => some n | _ => none)

/-- Canonical (codepoint) order on term names. -/
def nameLe (a b : String) : Bool := decide (a ≤ b)

/-- Canonicalize a symbolic matrix sum. Identity terms are removed; the surviving
named terms are placed in canonical order. The degenerate scalar result arises
ONLY when, after removing the named terms, nothing matrix-shaped remains and the
leading retained term is the *scalar* identity — i.e. a scalar zero was seeded
ahead of the matrix terms. With no scalar seed, an all-identity sum stays a
(shaped) identity matrix. -/
def canonicalizeMatrixSum (terms : List MatSumTerm) : MatSum :=
  match survivingNames terms with
  | [] =>
      match terms.head? with
      | some MatSumTerm.scalarZero => MatSum.scalar
      | _ => MatSum.matrix []
  | names => MatSum.matrix (names.mergeSort nameLe)
-- pure-end

-- post-conditions-start
/-- The canonical sum of a list of matrix-valued terms is the matrix-valued
result whose surviving named terms are those of the input in canonical order.
In particular it is always a matrix (never a shapeless scalar): an all-identity
input yields the identity matrix `matrix []`. -/
def problem_spec_matrixSum (terms : List MatSumTerm) (result : MatSum) : Prop :=
  result = MatSum.matrix ((survivingNames terms).mergeSort nameLe)
-- post-conditions-end

-- impl-start
def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do
  -- The terms are all matrix-valued (no scalar coefficient terms), so the sum is
  -- built directly from them, with no scalar identity seeded ahead of them.
  return canonicalizeMatrixSum terms
-- impl-end

-- proof-start
theorem correct_matrixSum :
    ∀ (terms : List MatSumTerm),
      terms ≠ [] →
      (∀ t ∈ terms, t ≠ MatSumTerm.scalarZero) →
      (survivingNames terms).Nodup →
      problem_spec_matrixSum terms (implementation_matrixSum terms) := by
  intro terms hne hns _
  unfold problem_spec_matrixSum implementation_matrixSum canonicalizeMatrixSum
  simp only [Id.run]
  cases hs : survivingNames terms with
  | nil =>
    simp only [List.mergeSort_nil]
    cases ht : terms with
    | nil => exact absurd ht hne
    | cons a as =>
      have ha : a ≠ MatSumTerm.scalarZero := hns a (by rw [ht]; exact List.mem_cons_self ..)
      cases a
      · exact absurd rfl ha
      · rfl
      · rfl
  | cons n ns =>
    rfl
-- proof-end
