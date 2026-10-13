import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The permutation a random source yields for a block of the given size, taking
   into account that the source has already been consumed to permute every
   earlier block. The arguments are: an integer configuration value selecting the
   source; the (ordered) list of earlier block sizes already drawn from this
   source — the residue that determines where the source currently stands; and
   the size of the block to permute now. Permuting a block of size `sz` after
   earlier blocks `prev` therefore depends on ALL THREE — the source is consumed
   in sequence, never restarted for each block. UNCHANGED community callee (a
   standard pseudo-random generator), left fully opaque; its soundness (this
   residue model == the real source's sequential behaviour) is validated by
   axiom_check.py (G-AX, an A-reference). Provenance: mapping.md. -/
axiom shuffleAfter : Int → List Nat → Nat → List Nat
-- axioms-end

-- pure-start
/- The block size used for one class: a class with `count` members is permuted
   as a block of `max count nSplits` positions (so a block is never smaller than
   the number of requested splits). -/
def blockSize (nSplits : Nat) (count : Nat) : Nat := max count nSplits

/- Fold one class into the running result: it contributes the permutation its
   block receives from the shared source AFTER all earlier classes have been
   permuted (`prev` = earlier block sizes), and then records its own block size
   so the next class is permuted from the advanced source. The accumulator pairs
   the permutations produced so far with the residue (`prev`) of the source. -/
noncomputable def threadStep (nSplits : Nat) (s : Int)
    (acc : List (List Nat) × List Nat) (count : Nat) : List (List Nat) × List Nat :=
  let sz := blockSize nSplits count
  (acc.1 ++ [shuffleAfter s acc.2 sz], acc.2 ++ [sz])

/- The whole per-class shuffle pass: thread the single shared source through the
   classes in order. Each class is permuted from the source as advanced by every
   earlier class, so distinct configuration values produce distinct per-class
   shuffles (the source is never restarted per class). Front of the pair = the
   per-class permutations in class order; back = the consumed block sizes. -/
noncomputable def threadAll (nSplits : Nat) (s : Int) (counts : List Nat) :
    List (List Nat) × List Nat :=
  counts.foldl (threadStep nSplits s) ([], [])

/- Forward-fold step: extending the consumed prefix by one class folds that
   class into the result built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
@[grind] lemma threadAll_take_step (nSplits : Nat) (s : Int) (counts : List Nat)
    (i : Nat) (hi : i < counts.length) :
    (counts.take (i + 1)).foldl (threadStep nSplits s) ([], [])
      = threadStep nSplits s ((counts.take i).foldl (threadStep nSplits s) ([], []))
          counts[i]! := by
  have hcons : counts.take (i + 1) = counts.take i ++ [counts[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce, for each class in order, the permutation of its block of positions
   used to assign the class's members to splits.

   `counts` (the per-class member counts), `nSplits` (the number of requested
   splits) and `s` (the integer configuration value selecting the random source)
   are read-only inputs (none is `mut`). Desired behaviour: the classes share a
   SINGLE random source consumed in sequence — each class is permuted from the
   source as already advanced by every earlier class — so two different
   configuration values yield different per-class shuffles. The source is never
   restarted for each class. The result lists the per-class permutations in
   class order. -/
noncomputable section
method perClassShuffles (counts : List Nat) (nSplits : Nat) (s : Int)
    return (out : List (List Nat))
  ensures out = (threadAll nSplits s counts).1
  do
    -- impl-start
    -- Pre-image skeleton: the random source is RESTARTED for every class — each
    -- class is permuted from the source in its initial state (residue `[]`),
    -- never from the source as advanced by earlier classes. The frozen spec
    -- requires the THREADED permutations (`shuffleAfter s prev sz` with the
    -- accumulating residue `prev`), so prove_correct MUST fail.
    let mut result : List (List Nat) := []
    let mut i := 0
    while i < counts.length
      invariant i ≤ counts.length
      invariant result = (counts.take i).map (fun count => shuffleAfter s [] (blockSize nSplits count))
      done_with i = counts.length
      decreasing counts.length - i
    do
      let count := counts[i]!
      let sz := blockSize nSplits count
      result := result ++ [shuffleAfter s [] sz]
      i := i + 1
    return result
    -- impl-end
end

prove_correct perClassShuffles by
  loom_solve
