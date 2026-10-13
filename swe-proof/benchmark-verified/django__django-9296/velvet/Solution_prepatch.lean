import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-index sub-view selector `pageOf`
--  (pure region) is the object's UNCHANGED accessor that, given an index the
--  object names, returns the contents of the sub-view at that index. It is
--  modeled as an opaque map ON ITS DOMAIN — its concrete result is never pinned,
--  only that the SAME map is applied to every index in order — and validated
--  against the real accessor, domain included, by axiom_check.py (G-AX): an
--  A-reference, not a consumed axiom.)
-- axioms-end

-- pure-start
/- How many sub-views the object presents: an attribute of the object under
   specification, constant for the duration of one traversal. It delimits both
   of the object's derived notions — the index
   sequence names exactly the indices `1 … numPages`, and the per-index accessor
   is defined at exactly those indices — so it is what the index carrier below is
   cut out of. Opaque: no concrete count is ever relied upon, and because it
   belongs to the OBJECT it is not readable off the accessor's argument (a domain
   taken from the argument's length would be widened by any longer argument). -/
opaque numPages : Nat

/- An index the object NAMES: a 1-based position within the object's own count.
   The per-index accessor is a PARTIAL operation on the integers — it yields a
   sub-view at an index only while `1 ≤ n ≤ numPages` and refuses every other
   index — so the carrier of indices IS that domain, carried with each index.
   Applying the accessor at an index the object does not name is therefore not
   expressible, which is what makes the accessor's refusal part of the modeled
   behaviour rather than a detail the model has to totalize away. -/
def PageIdx : Type := {n : Nat // 1 ≤ n ∧ n ≤ numPages}

/- The per-index sub-view selector: the object's existing accessor that, given an
   index the object names, returns the contents of the sub-view at that index.
   The behaviour under specification does not depend on HOW a sub-view is
   produced, only that each index is mapped through this SAME accessor, in
   order; so it is modeled as an opaque map on the index carrier (its concrete
   result is never relied upon). -/
opaque pageOf : PageIdx → List Int

/- The ordered family of sub-views named by a sequence of indices: select the
   sub-view at each index, in the exact order the indices appear. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def pageSeq : List PageIdx → List (List Int)
  | []      => []
  | p :: ps => pageOf p :: pageSeq ps

@[grind] lemma pageSeq_nil : pageSeq [] = [] := rfl
@[grind] lemma pageSeq_cons (p : PageIdx) (ps : List PageIdx) :
    pageSeq (p :: ps) = pageOf p :: pageSeq ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Iterating the object walks its index sequence in order and produces, for each
   index, the object's sub-view at that index. The result is therefore the ordered
   family of sub-views named by the index sequence: it has the same length as the
   index sequence, and its k-th element is the sub-view at the k-th index, in the
   same order. Every index in that sequence is one the object names, so each step
   is an accessor application the object admits — and no other application is
   available to the operation at all. The index sequence is read-only and the
   operation mutates none of its inputs (directive 5: `pageRange` is not `mut`). -/
method enumeratePages (pageRange : List PageIdx) return (out : List (List Int))
  ensures out = pageSeq pageRange
  do
    -- impl-start
    -- Pre-patch skeleton: the object exposes NO iteration protocol, so nothing
    -- is produced — walking it yields the empty family of sub-views regardless
    -- of the index sequence. The frozen spec requires the ordered family
    -- `pageSeq pageRange`, so prove_correct MUST fail whenever the index
    -- sequence is non-empty.
    let result : List (List Int) := []
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the index at
   `i-1` on the front, so `pageSeq` peels one `pageOf`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma pageSeq_drop_step (pageRange : List PageIdx) (i : Nat)
    (hi : 0 < i) (hle : i ≤ pageRange.length) :
    pageSeq (pageRange.drop (i - 1))
      = ((pageRange[i - 1]?).map pageOf).toList ++ pageSeq (pageRange.drop i) := by
  have hlt : i - 1 < pageRange.length := by omega
  have hcons : pageRange.drop (i - 1) = pageRange[i - 1] :: pageRange.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, pageSeq_cons, List.getElem?_eq_getElem hlt]
  simp

prove_correct enumeratePages by
  loom_solve
  -- Leaves the unsolved discriminating goal `[] = pageSeq pageRange`: the empty
  -- result cannot equal the ordered family of sub-views for a non-empty index
  -- sequence. No tactic closes it without the missing iteration protocol.
  simp_all
