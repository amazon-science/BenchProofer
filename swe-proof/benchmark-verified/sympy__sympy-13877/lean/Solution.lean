import Mathlib
-- imports-end

/-!
Selecting a pivot from a column of symbolic expressions.

During fraction-free Gaussian elimination one repeatedly takes the first column
of a (sub)matrix and chooses a *pivot*: the first entry of that column that is
not zero. The subtlety is that the entries are symbolic expressions, and an
expression can be written in a structurally non-trivial form yet still be
mathematically equal to zero (for example a difference of two products that
cancels completely). A pivot must be a *genuinely* nonzero entry; choosing an
entry that is mathematically zero corrupts the elimination.

We model a column entry as an integer-coefficient polynomial expression in a
single indeterminate. "Mathematically zero" means the expression evaluates to
the zero polynomial (every coefficient is `0`).

The desired behavior, stated as an input→output relation:

* if the column contains some mathematically-nonzero entry, the result is the
  position and value of the *first* such entry (and every earlier entry is
  mathematically zero);
* if every entry is mathematically zero, the result is nothing.

The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The zero test that decides
-- whether an entry may serve as a pivot is spelled out concretely below
-- (`eval` / `isMathZero`, an A-reference): an expression is mathematically zero
-- exactly when it evaluates to the zero polynomial. There is nothing to
-- axiomatize — the modeled behavior is validated directly against the real
-- routine by the differential conformance check.
-- axioms-end

-- pure-start
/-- A symbolic expression: an integer-coefficient polynomial in one
indeterminate, built from integer constants, the indeterminate, addition,
multiplication and negation. This is the carrier for a single column entry. -/
inductive PExpr where
  | const : Int → PExpr
  | sym   : PExpr
  | add   : PExpr → PExpr → PExpr
  | mul   : PExpr → PExpr → PExpr
  | neg   : PExpr → PExpr
deriving Repr, DecidableEq

/-- Add two coefficient lists (little-endian, index `i` = coefficient of `xⁱ`). -/
def addC : List Int → List Int → List Int
  | [], ys => ys
  | xs, [] => xs
  | x :: xs, y :: ys => (x + y) :: addC xs ys

/-- Multiply two coefficient lists (polynomial convolution). -/
def mulC : List Int → List Int → List Int
  | [], _ => []
  | x :: xs, ys => addC (ys.map (· * x)) (0 :: mulC xs ys)

/-- Evaluate an expression to its little-endian list of integer coefficients. -/
def eval : PExpr → List Int
  | .const c => [c]
  | .sym      => [0, 1]
  | .add a b  => addC (eval a) (eval b)
  | .mul a b  => mulC (eval a) (eval b)
  | .neg a    => (eval a).map (fun c => -c)

/-- An expression is *mathematically zero* when it evaluates to the zero
polynomial — every coefficient is `0`. -/
def isMathZero (e : PExpr) : Bool := (eval e).all (· == 0)
-- pure-end

-- post-conditions-start
/-- The pivot-selection contract on a column `col`:

* `some (pos, val)`: `pos` is a valid index, `val` is exactly the entry there,
  that entry is mathematically nonzero, and every strictly-earlier entry is
  mathematically zero (so `pos` is the *first* genuinely nonzero position);
* `none`: every entry of the column is mathematically zero. -/
def problem_spec_firstNonzero
    (col : List PExpr) (result : Option (Nat × PExpr)) : Prop :=
  match result with
  | some (pos, val) =>
      pos < col.length ∧
      col[pos]? = some val ∧
      isMathZero val = false ∧
      (∀ k e, k < pos → col[k]? = some e → isMathZero e = true)
  | none =>
      ∀ e ∈ col, isMathZero e = true
-- post-conditions-end

-- impl-start
def implementation_firstNonzero
    (col : List PExpr) : Option (Nat × PExpr) := Id.run do
  let mut i := 0
  for x in col do
    if isMathZero x = false then
      return some (i, x)
    i := i + 1
  return none
-- impl-end


-- proof-start
/-- Pure recursive de-monadified form of the scanning loop: returns the first
index/value pair whose entry is mathematically nonzero, carrying the current
global index as the second argument. -/
def go : List PExpr → Nat → Option (Nat × PExpr)
  | [], _ => none
  | x :: xs, i => if isMathZero x = false then some (i, x) else go xs (i + 1)

theorem go_spec_general :
    ∀ (col : List PExpr) (i : Nat),
      (match go col i with
        | some (pos, val) =>
            i ≤ pos ∧ pos - i < col.length ∧ col[pos - i]? = some val ∧
              isMathZero val = false ∧
              (∀ k e, k < pos - i → col[k]? = some e → isMathZero e = true)
        | none => ∀ e ∈ col, isMathZero e = true) := by
  intro col
  induction col with
  | nil => intro i; simp [go]
  | cons x xs ih =>
    intro i
    simp only [go]
    split_ifs with hx
    · -- isMathZero x = false, result = some (i, x)
      refine ⟨le_refl i, ?_, ?_, hx, ?_⟩
      · simp
      · simp
      · intro k e hk _; simp only [Nat.sub_self] at hk; omega
    · -- isMathZero x = true, result = go xs (i+1)
      have hx' : isMathZero x = true := by
        simp only [Bool.not_eq_false] at hx; exact hx
      have this' := ih (i + 1)
      cases hgo : go xs (i + 1) with
      | none =>
        rw [hgo] at this'
        intro e he
        rcases List.mem_cons.mp he with rfl | he'
        · exact hx'
        · exact this' e he'
      | some pv =>
        obtain ⟨pos, val⟩ := pv
        rw [hgo] at this'
        obtain ⟨h1, h2, h3, h4, h5⟩ := this'
        refine ⟨by omega, ?_, ?_, h4, ?_⟩
        · simp only [List.length_cons]; omega
        · have hpi : pos - i = (pos - (i + 1)) + 1 := by omega
          rw [hpi, List.getElem?_cons_succ]; exact h3
        · intro k e hk he
          cases k with
          | zero =>
            simp only [List.getElem?_cons_zero, Option.some.injEq] at he
            subst he; exact hx'
          | succ k' =>
            rw [List.getElem?_cons_succ] at he
            have hk' : k' < pos - (i + 1) := by omega
            exact h5 k' e hk' he

theorem loop_eq_go :
    ∀ (col : List PExpr),
      implementation_firstNonzero col = go col 0 := by
  intro col
  simp only [implementation_firstNonzero, Id.run]
  generalize (0 : Nat) = i
  induction col generalizing i with
  | nil => rfl
  | cons x xs ih =>
      simp only [List.forIn_cons, go]
      by_cases hx : isMathZero x = false
      · simp only [hx, if_true]
        rfl
      · simp only [hx]
        exact ih (i + 1)

theorem go_spec_zero :
    ∀ (col : List PExpr), problem_spec_firstNonzero col (go col 0) := by
  intro col
  have h := go_spec_general col 0
  simp only [Nat.sub_zero] at h
  unfold problem_spec_firstNonzero
  cases hg : go col 0 with
  | none => rw [hg] at h; exact h
  | some p =>
      obtain ⟨pos, val⟩ := p
      rw [hg] at h
      exact ⟨h.2.1, h.2.2.1, h.2.2.2.1, h.2.2.2.2⟩

theorem correct_firstNonzero :
    ∀ (col : List PExpr),
      problem_spec_firstNonzero col (implementation_firstNonzero col) := by
  intro col
  rw [loop_eq_go col]
  exact go_spec_zero col

-- proof-end
