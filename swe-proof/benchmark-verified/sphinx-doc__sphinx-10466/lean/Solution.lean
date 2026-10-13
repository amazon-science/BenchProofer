import Mathlib
-- imports-end

/-!
Collecting the source positions at which a single translatable text was seen.

Each time the text is encountered, an occurrence record is appended: a source
name, a line number within that source, and an opaque per-occurrence
identifier. The same `(source, line)` position can be recorded many times — the
text may genuinely appear there more than once, or the same physical location
may be revisited — and the per-occurrence identifier differs every time, so
naive collection of the positions yields repeats.

The desired output is the list of positions that should be reported for the
text: every distinct `(source, line)` that was recorded, each listed exactly
once, in ascending order. Ascending order is the lexicographic order on
positions — by source name first, then by line number — matching how a pair of
(string, integer) is ordered. The opaque identifiers do not appear in this
output; they only witness that a position was recorded.

We model an occurrence record as a `String × Int × String` (source, line,
identifier) and a reported position as a `String × Int` (source, line).
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The whole computation — mapping
-- each occurrence to its position, removing repeats, and ordering — is modeled
-- directly with total Lean operations, so there are no `opaque`/`axiom` decls.
-- axioms-end

-- pure-start
/-- Lexicographic "≤" on positions: order by source name, tie-broken by line.
Mirrors the order used to compare a pair of (string, integer) ascending. -/
def lexLe (a b : String × Int) : Bool :=
  if a.1 = b.1 then decide (a.2 ≤ b.2) else decide (a.1 < b.1)

/-- Strict lexicographic order on positions (the irreflexive core of `lexLe`):
a smaller source name, or an equal source name with a smaller line. Used to
state that the output is strictly ascending — simultaneously ordered and
repeat-free. -/
def lexLt (a b : String × Int) : Prop :=
  a.1 < b.1 ∨ (a.1 = b.1 ∧ a.2 < b.2)
-- pure-end

-- post-conditions-start
/-- The positions reported for a text whose occurrences are `triples`
(each `(source, line, identifier)`):

  * the result is strictly ascending in lexicographic position order — which
    forces both that it is sorted and that no position repeats; and
  * a position is reported iff it was recorded by some occurrence — i.e. there
    exists an occurrence with that source and line (its identifier is
    irrelevant).

Together these pin the result to exactly the distinct recorded positions, in
ascending order. -/
def problem_spec_dedupSort
    (triples : List (String × Int × String)) (result : List (String × Int)) : Prop :=
  List.Sorted lexLt result ∧
  (∀ p : String × Int, p ∈ result ↔ ∃ u : String, (p.1, p.2, u) ∈ triples)
-- post-conditions-end

-- impl-start
def implementation_dedupSort
    (triples : List (String × Int × String)) : List (String × Int) := Id.run do
  let mut pairs : List (String × Int) := []
  for t in triples do
    pairs := pairs ++ [(t.1, t.2.1)]
  return pairs.dedup.mergeSort lexLe
-- impl-end


-- proof-start
/-- The list of positions the mutable loop actually computes before dedup/sort:
each occurrence triple projected to its `(source, line)`. -/
def mappedPairs (triples : List (String × Int × String)) : List (String × Int) :=
  triples.map (fun t => (t.1, t.2.1))

theorem loop_eq_map (triples : List (String × Int × String)) :
    implementation_dedupSort triples = (mappedPairs triples).dedup.mergeSort lexLe := by
  simp only [implementation_dedupSort, mappedPairs, Id.run]
  have key : (List.map (fun x2 : String × Int × String => [(x2.1, x2.2.1)]) triples).flatten
      = List.map (fun t => (t.1, t.2.1)) triples := by
    induction triples with
    | nil => rfl
    | cons h t ih => simp only [List.map_cons, List.flatten_cons, List.singleton_append, ih]
  simp
  rw [key]
  rfl

theorem mem_result_iff (triples : List (String × Int × String)) :
    ∀ p : String × Int,
      p ∈ (mappedPairs triples).dedup.mergeSort lexLe ↔
        ∃ u : String, (p.1, p.2, u) ∈ triples := by
  intro p
  simp only [List.mem_mergeSort, List.mem_dedup, mappedPairs, List.mem_map]
  constructor
  · rintro ⟨⟨a, b, c⟩, ht, hpt⟩
    subst hpt
    exact ⟨c, ht⟩
  · rintro ⟨u, hu⟩
    exact ⟨(p.1, p.2, u), hu, rfl⟩

theorem lexLe_total (a b : String × Int) :
    lexLe a b = true ∨ lexLe b a = true := by
  unfold lexLe
  by_cases h : a.1 = b.1
  · simp [h]
    omega
  · rcases lt_trichotomy a.1 b.1 with hlt | heq | hgt
    · left; simp [h, hlt]
    · exact absurd heq h
    · right
      have hne : b.1 ≠ a.1 := fun e => h e.symm
      simp [hne, hgt]

theorem lexLe_trans (a b c : String × Int) :
    lexLe a b = true → lexLe b c = true → lexLe a c = true := by
  unfold lexLe
  intro hab hbc
  split_ifs at hab hbc ⊢ <;> simp_all <;> first | omega | order

theorem lexLe_to_lexLt_of_ne (a b : String × Int) :
    a ≠ b → lexLe a b = true → lexLt a b := by
  intro hne hle
  unfold lexLe at hle
  unfold lexLt
  by_cases h : a.1 = b.1
  · simp [h] at hle
    right
    refine ⟨h, ?_⟩
    have hne2 : a.2 ≠ b.2 := fun heq => hne (Prod.ext h heq)
    omega
  · rw [if_neg h] at hle
    left
    exact of_decide_eq_true hle

theorem mergeSort_sorted_lexLe (triples : List (String × Int × String)) :
    List.Sorted (fun a b => lexLe a b = true)
      ((mappedPairs triples).dedup.mergeSort lexLe) := by
  exact List.sorted_mergeSort lexLe_trans
    (fun a b => by simp only [Bool.or_eq_true]; exact lexLe_total a b) _

theorem dedup_mergeSort_nodup (triples : List (String × Int × String)) :
    ((mappedPairs triples).dedup.mergeSort lexLe).Nodup :=
  (List.mergeSort_perm _ _).nodup_iff.mpr (List.nodup_dedup _)

theorem strict_upgrade (L : List (String × Int)) :
    List.Sorted (fun a b => lexLe a b = true) L → L.Nodup → List.Sorted lexLt L := by
  intro hsort hnodup
  exact (hsort.and hnodup).imp (fun h => lexLe_to_lexLt_of_ne _ _ h.2 h.1)

theorem correct_dedupSort :
    ∀ triples : List (String × Int × String),
      problem_spec_dedupSort triples (implementation_dedupSort triples) := by
  intro triples
  rw [loop_eq_map]
  refine ⟨?_, ?_⟩
  · exact strict_upgrade _ (mergeSort_sorted_lexLe triples) (dedup_mergeSort_nodup triples)
  · exact mem_result_iff triples

-- proof-end
