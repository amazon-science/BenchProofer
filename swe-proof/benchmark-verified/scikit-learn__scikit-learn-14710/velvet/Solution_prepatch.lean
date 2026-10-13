import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-element index→label lookup is the
--  ordinary table-indexing operation, modeled deeply as `gather` below; it is
--  not borrowed from any axiomatized callee, so there is no soundness to import
--  and no axiom_check.py. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- Look up each entry of `idxs` in `table` and collect the results in order.
   `idxs` carries integer codes, each an index into `table`; the result is the
   ordered, count-preserving sequence of the looked-up entries. Written as a
   front-to-back element-wise map so a single per-element fact discharges it. -/
def gather (table : List Int) (idxs : List Int) : List Int :=
  idxs.map (fun i => table[i.toNat]!)

@[grind] lemma gather_def (table idxs : List Int) :
    gather table idxs = idxs.map (fun i => table[i.toNat]!) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare the target sequence that is handed to the evaluation scorer.

   The targets `y` arrive as integer codes. When the estimation task is a
   CLASSIFICATION task, these codes index a table `labels` of the original
   class labels, and the score must be computed against those original labels:
   the prepared targets are obtained by looking each code up in `labels`, in
   order (an order- and count-preserving lookup). When the task is NOT a
   classification task, the targets are already in their final form and are
   handed to the scorer unchanged.

   Two guarantees pin the demanded behavior:
   - classification (`isClf = true`): the prepared targets are exactly the
     per-code lookups of `y` through `labels`, in order — the codes are mapped
     back to the original labels they stand for before scoring (so the scorer
     compares values from the same domain as its predictions);
   - non-classification (`isClf = false`): the prepared targets equal `y`
     exactly — the read-only input target sequence is passed through with
     nothing added, dropped, reordered, or transformed (directive-5 frame).

   `isClf`, `labels`, `y` are read-only inputs; a fresh sequence is produced and
   no input is mutated. The precondition records that every code is a valid
   index into `labels` (codes range over `0 … labels.length - 1`). -/
method prepareScorerTargets (isClf : Bool) (labels : List Int) (y : List Int)
    return (out : List Int)
  require ∀ i, i ∈ y → 0 ≤ i ∧ i.toNat < labels.length
  ensures isClf = true  → out = gather labels y
  ensures isClf = false → out = y
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: the prepared targets are handed to the scorer
    -- WITHOUT mapping the integer codes back through `labels` — the same raw
    -- code sequence `y` is returned for BOTH the classification and the
    -- non-classification task. On a classification task (`isClf = true`) this violates
    -- the frozen clause `out = gather labels y` whenever a code differs from the
    -- label it stands for, so prove_correct MUST fail.
    return y
    -- impl-end

prove_correct prepareScorerTargets by
  loom_solve
