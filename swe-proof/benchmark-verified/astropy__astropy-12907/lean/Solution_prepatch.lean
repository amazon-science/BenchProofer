import Mathlib
-- imports-end

/-!
Combining the correlation matrices of two independent sub-transforms that are
placed side by side (each acting on its own block of inputs to produce its own
block of outputs). The combined matrix relates the concatenated outputs to the
concatenated inputs: a top-left block carrying the first sub-transform's own
correlations, a bottom-right block carrying the second's, and zeros elsewhere
(the two sub-transforms share neither inputs nor outputs).

A correlation matrix is modeled as `List (List Nat)`: one inner list per output
row, all rows sharing one width (the input count); an entry is `0` (independent)
or nonzero (dependent). `lin`/`rin` are the input widths of the two blocks.
-/

-- axioms-start
-- No unchanged callees are consumed: the combinator is modeled deeply.
-- axioms-end

-- pure-start
/-- A row of `n` independent (zero) entries. -/
def zeroRow (n : Nat) : List Nat := List.replicate n 0
-- pure-end

-- post-conditions-start
/-- The combined matrix is the block-diagonal (direct-sum) arrangement of the
two input matrices:
* it has one row per output of the two blocks together;
* the first `left.length` rows reproduce `left`'s own row, then `rin` zeros;
* the remaining rows are `lin` zeros, then `right`'s corresponding row. -/
def problem_spec_direct_sum
    (lin rin : Nat) (left right : List (List Nat)) (result : List (List Nat)) : Prop :=
  result.length = left.length + right.length ∧
  (∀ i, i < left.length →
      result.getD i [] = left.getD i [] ++ zeroRow rin) ∧
  (∀ i, left.length ≤ i → i < left.length + right.length →
      result.getD i [] = zeroRow lin ++ right.getD (i - left.length) [])
-- post-conditions-end

-- impl-start
def implementation_direct_sum
    (lin rin : Nat) (left right : List (List Nat)) : List (List Nat) := Id.run do
  let lout := left.length
  let rout := right.length
  let noutp := lout + rout
  let mut result : List (List Nat) := []
  for i in [0:noutp] do
    let cleftRow := if i < lout then left.getD i [] else zeroRow lin
    let crightRow := if lout ≤ i then List.replicate rin 1 else zeroRow rin
    result := result ++ [cleftRow ++ crightRow]
  return result
-- impl-end

-- proof-start
theorem correct_direct_sum :
    ∀ (lin rin : Nat) (left right : List (List Nat)),
      (∀ r ∈ left, r.length = lin) → (∀ r ∈ right, r.length = rin) →
      problem_spec_direct_sum lin rin left right
        (implementation_direct_sum lin rin left right) := by
  sorry
-- proof-end
