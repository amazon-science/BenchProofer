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
-- PRE-PATCH (buggy) skeleton. The zero test used here only rejects an entry that
-- is *literally* the zero constant; any other entry is accepted as a pivot even
-- when it is mathematically zero in a non-trivial form. On such a column this
-- selects a mathematically-zero entry as the pivot, violating the contract.
def implementation_firstNonzero
    (col : List PExpr) : Option (Nat × PExpr) := Id.run do
  let mut i := 0
  for x in col do
    if x ≠ PExpr.const 0 then
      return some (i, x)
    i := i + 1
  return none
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: on a
-- column whose first entry is a non-trivial-but-mathematically-zero expression
-- the impl returns that entry, contradicting `isMathZero val = false`.
theorem correct_firstNonzero :
    ∀ (col : List PExpr),
      problem_spec_firstNonzero col (implementation_firstNonzero col) := by
  sorry
-- proof-end
