import Mathlib
-- imports-end

/-!
Narrowing a collection of records by a multi-word search query.

Each record reaches a set of related rows (through its multi-valued relations).
For one related row and one processed search word, the row either matches that
word or it does not (matching is the standard per-field test, abstracted here to
a per-row set of matched words). The search query is the list of processed words.

The desired behaviour, stated as an input→output relation: the narrowed
collection keeps a record exactly when a SINGLE one of its related rows matches
EVERY word of the query simultaneously. (When the query carries no words the
collection is returned unchanged.) Equivalently, the existential over related
rows sits inside the universal over words: one related row must account for the
whole query, not a different row per word.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behaviour is modeled
-- deeply with concrete operations over the per-(row, word) match matrix. The
-- word-splitting, per-field text comparison, and OR-over-fields combination are
-- unchanged here and are folded into the inputs (the processed word list and
-- each row's matched-word set), so no callee property is consumed by the proof.
-- axioms-end

-- pure-start
/-- One related row reachable from a record. `matched` is the set of processed
search words this row satisfies (under the OR over the configured search
fields). Words are carried as opaque ids: equal words have equal ids. -/
structure Row where
  matched : List Nat
deriving DecidableEq, Repr

/-- A record under consideration, identified by `id`, together with the related
rows it reaches through its multi-valued relations. -/
structure Parent where
  id : Nat
  rows : List Row
deriving DecidableEq, Repr

/-- A single related row matches the whole accumulated query when it matches
every word in it. -/
def rowMatchesAll (tqs : List Nat) (r : Row) : Bool :=
  tqs.all (fun t => r.matched.contains t)

/-- Whether a record is kept by the combined query `tqs`: with no words the
query is a no-op (every record is kept); otherwise the record is kept exactly
when ONE of its related rows matches every word. -/
def combinedMatch (tqs : List Nat) (p : Parent) : Bool :=
  match tqs with
  | []     => true
  | _ :: _ => p.rows.any (fun r => rowMatchesAll tqs r)
-- pure-end

-- post-conditions-start
/-- The narrowed collection is the input collection restricted to the records
the combined query keeps: order preserved, each record kept at most once, and a
record present exactly when a single related row matches every search word. -/
def problem_spec_searchFilter (terms : List Nat) (parents : List Parent)
    (result : List Parent) : Prop :=
  result = parents.filter (fun p => combinedMatch terms p)
-- post-conditions-end

-- impl-start
def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
    List Parent := Id.run do
  -- Accumulate the per-word queries, then apply ONE combined filter (a single
  -- join), so the surviving records are those a single related row satisfies
  -- across the whole query.
  let mut termQueries : List Nat := []
  for t in terms do
    termQueries := termQueries ++ [t]
  return parents.filter (fun p => combinedMatch termQueries p)
-- impl-end

-- proof-start
theorem correct_searchFilter :
    ∀ (terms : List Nat) (parents : List Parent),
      problem_spec_searchFilter terms parents
        (implementation_searchFilter terms parents) := by
  intro terms parents
  have helper : ∀ (xs : List Nat) (init : List Nat),
      (forIn (m := Id) xs init
        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
    intro xs
    induction xs with
    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [bind, pure] at ih ⊢
      rw [ih]
      simp
  unfold problem_spec_searchFilter implementation_searchFilter
  simp only [Id.run, bind]
  rw [helper, List.nil_append]
  rfl
-- proof-end
