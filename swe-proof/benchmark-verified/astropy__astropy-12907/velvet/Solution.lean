import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Dependency-matrix assembly for the parallel composition of two transforms.

   Each transform is described by a 0/1 dependency matrix of shape
   (outputs × inputs): row r, column c is 1 iff output r depends on input c.
   The parallel composition stacks the two transforms so they act on disjoint
   input/output blocks: the combined matrix is block-diagonal, the upper-left
   block being the left transform's matrix and the lower-right block being the
   right transform's matrix, with the off-diagonal blocks all zero.

   The model below assembles that block-diagonal matrix abstractly; no callee
   is axiomatized because the assembly is the only computation. -/

-- axioms-start
-- axioms-end

-- pure-start
/- Widen a left-block row to full width by appending `rc` zero columns on the
   right (the right transform's inputs are independent of left outputs). -/
def widenRight (rc : Nat) (row : List Int) : List Int :=
  row ++ List.replicate rc 0

/- Widen a right-block row to full width by prepending `lc` zero columns on the
   left (the left transform's inputs are independent of right outputs). -/
def widenLeft (lc : Nat) (row : List Int) : List Int :=
  List.replicate lc 0 ++ row

/- The block-diagonal dependency matrix of the parallel composition: every
   left row widened on the right, then every right row widened on the left.
   Each block keeps its own internal dependency structure; the off-diagonal
   blocks are zero. -/
def blockDiag (left right : List (List Int)) (lc rc : Nat) : List (List Int) :=
  (left.map (widenRight rc)) ++ (right.map (widenLeft lc))

@[grind] lemma blockDiag_eq (left right : List (List Int)) (lc rc : Nat) :
    blockDiag left right lc rc = (left.map (widenRight rc)) ++ (right.map (widenLeft lc)) :=
  rfl
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine the dependency matrices of two transforms into the block-diagonal
   matrix of their parallel composition. `left`/`right` are the operand
   matrices (rows are dependency rows over `lc`/`rc` input columns
   respectively); `lc`/`rc` are the operand input widths. -/
method combineParallel (left : List (List Int)) (right : List (List Int))
    (lc : Nat) (rc : Nat) return (out : List (List Int))
  require ∀ r ∈ left,  r.length = lc
  require ∀ r ∈ right, r.length = rc
  ensures out = blockDiag left right lc rc
  do
    -- impl-start
    -- Upper block: each left row keeps its own columns, zero-padded on the
    -- right so the right transform's inputs do not appear to affect it.
    let upper : List (List Int) := left.map (widenRight rc)
    -- Lower block: each right row is zero-padded on the left, then carries its
    -- OWN dependency columns — NOT a constant fill, so the right transform's
    -- internal structure is preserved across the composition.
    let lower : List (List Int) := right.map (widenLeft lc)
    return upper ++ lower
    -- impl-end

prove_correct combineParallel by
  loom_solve
