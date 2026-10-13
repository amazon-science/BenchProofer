import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model references. The decision of WHICH entries
-- to drop is taken by a separate comparison over the collection (unchanged by
-- this slice) and reaches the operation modeled here as the read-only input
-- `removeFlags`. The operation under specification — dropping the flagged
-- entries from several index-aligned parallel lists — is modeled DEEPLY by
-- `keepByMask` (pure region); there is no unchanged library callee whose
-- behaviour the proof must axiomatize. Provenance and the value bijection are in
-- mapping.md; the end-to-end behaviour is differential-tested by
-- conformance_check.py (G-CONF).
-- axioms-end

-- pure-start
/- Drop the flagged entries from one list, by POSITION. A removal flag of `true`
   at a position discards the entry at that position; a flag of `false` keeps it.
   The result is the ordered subsequence of entries whose position carries a
   `false` flag. Front-recursive (flag and entry consumed together from the
   front) so a single unfold is available per step. -/
def keepByMask : List Int → List Bool → List Int
  | [],      _       => []
  | _ :: _,  []      => []
  | x :: xs, b :: bs => (if b then ([] : List Int) else [x]) ++ keepByMask xs bs

@[grind] lemma keepByMask_nil_left (m : List Bool) : keepByMask [] m = [] := by
  cases m <;> rfl

@[grind] lemma keepByMask_nil_right (xs : List Int) : keepByMask xs [] = [] := by
  cases xs <;> rfl

@[grind] lemma keepByMask_cons (x : Int) (xs : List Int) (b : Bool) (bs : List Bool) :
    keepByMask (x :: xs) (b :: bs) = (if b then ([] : List Int) else [x]) ++ keepByMask xs bs :=
  rfl

/- The number of positions a mask keeps (the count of `false` flags). The length
   of any masked list whose length matches the mask is exactly this count — so it
   depends ONLY on the mask, not on the entries. This is why filtering several
   equal-length lists by the SAME mask leaves them all of equal length, i.e.
   still index-aligned. -/
def numKept : List Bool → Nat
  | []      => 0
  | b :: bs => (if b then 0 else 1) + numKept bs

/- A list filtered by a mask of matching length has length `numKept mask` —
   independent of the list's entries. -/
lemma keepByMask_length (xs : List Int) (m : List Bool) (h : xs.length = m.length) :
    (keepByMask xs m).length = numKept m := by
  induction xs generalizing m with
  | nil =>
    cases m with
    | nil => rfl
    | cons b bs => simp at h
  | cons x xs ih =>
    cases m with
    | nil => simp at h
    | cons b bs =>
      have h' : xs.length = bs.length := by simpa using h
      rw [keepByMask_cons, numKept]
      cases b with
      | true  => simpa using ih bs h'
      | false => simp [ih bs h']; omega

/- Two equal-length lists filtered by the same mask come out equal-length: the
   positional, mask-driven filter preserves the index-alignment of parallel
   lists. -/
lemma keepByMask_length_eq (xs ys : List Int) (m : List Bool)
    (hx : xs.length = m.length) (hy : ys.length = m.length) :
    (keepByMask xs m).length = (keepByMask ys m).length := by
  rw [keepByMask_length xs m hx, keepByMask_length ys m hy]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A collection of items is tracked by several index-aligned parallel lists:
   for each item, a first per-position attribute (`listA`), a second
   (`listB`) and a third (`listC`) sit at the SAME position across the three
   lists, so the three lists always have equal length. A separate comparison over
   the collection has decided which positions are no longer wanted; that decision
   arrives as the per-position flags `removeFlags` (read-only), one flag per
   position.

   The wanted entries must be retained, and the unwanted ones dropped, from EVERY
   list by position, so that the surviving entries keep their mutual
   correspondence and the lists remain index-aligned (equal length). The three
   input lists are read-only — fresh result lists are produced; none of the
   inputs is mutated (directive 5). -/
method pruneParallelSystems
    (listA : List Int) (listB : List Int) (listC : List Int)
    (removeFlags : List Bool)
    return (out : (List Int) × (List Int) × (List Int))
  require listA.length = listB.length
  require listB.length = listC.length
  require listC.length = removeFlags.length
  ensures out.1   = keepByMask listA removeFlags
  ensures out.2.1 = keepByMask listB removeFlags
  ensures out.2.2 = keepByMask listC removeFlags
  ensures out.1.length   = out.2.1.length
  ensures out.2.1.length = out.2.2.length
  do
    -- impl-start
    -- Pre-image skeleton: only the third list is pruned by the flags;
    -- the other two are touched inconsistently as the flagged positions are
    -- encountered, so they do NOT end up filtered by the same flags. Their
    -- survivors therefore lose positional correspondence with the pruned
    -- third list. The frozen spec requires ALL THREE filtered by the
    -- same flags (and the lengths to stay equal), so prove_correct MUST fail.
    let keptA := listA
    let keptB := listB
    let keptC := keepByMask listC removeFlags
    return (keptA, keptB, keptC)
    -- impl-end

prove_correct pruneParallelSystems by
  loom_solve
  all_goals
    first
    | rfl
    | exact keepByMask_length_eq listA listB removeFlags (by omega) (by omega)
    | exact keepByMask_length_eq listB listC removeFlags (by omega) (by omega)
