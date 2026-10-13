import Mathlib
-- imports-end

/-!
Targeting the right rows when an update must cascade to a model's inheritance
ancestors.

When a model inherits from several base models, a single update may have to be
propagated to one update per ancestor. The set of identifiers used to target an
ancestor's rows must be that ancestor's *own* identifiers, read from a
materialized table of identifier rows. An ancestor that shares the
model's primary key reuses the model's identifier column (column `0`); an
ancestor that does not has its own dedicated identifier column, gathered
independently. Each ancestor is then paired, in order, with the identifiers read
from the column dedicated to it.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the surrounding query machinery
-- (identifier materialization, inheritance-path inspection) is abstracted into
-- this function's inputs — the table of identifier rows and the per-ancestor
-- flag recording whether the ancestor shares the model's primary key.
-- axioms-end

-- pure-start
/-- Assign each ancestor the column of the identifier-row table that carries its
identifiers. An ancestor that shares the model's primary key (`sharesPrimaryKey`)
reuses column `0`; otherwise it is given the next dedicated column, numbered from
`next`. Front-recursive companion of the accumulating loop in the impl. -/
def columnAssignment (sharesPrimaryKey : Nat → Bool) : List Nat → Nat → List (Nat × Nat)
  | [], _ => []
  | a :: rest, next =>
      if sharesPrimaryKey a then
        (a, 0) :: columnAssignment sharesPrimaryKey rest next
      else
        (a, next) :: columnAssignment sharesPrimaryKey rest (next + 1)
-- pure-end

-- post-conditions-start
/-- Correct targeting: each ancestor is paired, in its original order, with the
identifiers read from the table column dedicated to it — column `0` when the
ancestor shares the model's primary key, otherwise its own dedicated column,
numbered consecutively from `1` across the non-sharing ancestors. -/
def problem_spec_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) (result : List (Nat × List Int)) : Prop :=
  result =
    (columnAssignment sharesPrimaryKey ancestors 1).map
      (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))
-- post-conditions-end

-- impl-start
def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) : List (Nat × List Int) := Id.run do
  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
  let mut nextCol := 1
  let mut assignment : List (Nat × Nat) := []
  for ancestor in ancestors do
    if sharesPrimaryKey ancestor then
      assignment := assignment ++ [(ancestor, 0)]
    else
      assignment := assignment ++ [(ancestor, nextCol)]
      nextCol := nextCol + 1
  -- Pair each ancestor with the identifiers gathered from its dedicated column.
  let mut result : List (Nat × List Int) := []
  for ac in assignment do
    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
  return result
-- impl-end


-- proof-start
/-- Closed form of loop 1's `assignment` accumulator: the first projection of the
tail-accumulating fold over `ancestors` with paired state `(assignment, nextCol)`. -/
def assignFold (sharesPrimaryKey : Nat → Bool) (ancestors : List Nat) : List (Nat × Nat) :=
  Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
    if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
    else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)

/-- Closed form of loop 2's `result` accumulator on an assignment list `L`. -/
def resultFold (rows : List (List Int)) (L : List (Nat × Nat)) : List (Nat × List Int) :=
  List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) [] L

/-- Do-notation state bridge for loop 1: the impl's `for` loop desugars to a fold over
the `MProd`-valued loop state.  Its first projection equals the first projection of the
`Prod`-valued `assignFold`-style closed form, generalized over the initial state. -/
theorem loop1_mprod (sharesPrimaryKey : Nat → Bool) :
    ∀ (L : List Nat) (init : MProd (List (Nat × Nat)) Nat),
      (forIn (m := Id) L init fun ancestor r =>
        if sharesPrimaryKey ancestor = true then
          ForInStep.yield (⟨r.fst ++ [(ancestor, 0)], r.snd⟩ : MProd (List (Nat × Nat)) Nat)
        else ForInStep.yield ⟨r.fst ++ [(ancestor, r.snd)], r.snd + 1⟩).fst
      = (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
          if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
          else (st.1 ++ [(a, st.2)], st.2 + 1)) (init.fst, init.snd) L).1 := by
  intro L
  induction L with
  | nil => intro init; rfl
  | cons a rest ih =>
      intro init
      simp only [List.forIn_cons, List.foldl_cons]
      split
      · exact ih ⟨init.fst ++ [(a, 0)], init.snd⟩
      · exact ih ⟨init.fst ++ [(a, init.snd)], init.snd + 1⟩

theorem loops_to_folds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) :
    implementation_relatedTargetIds ancestors sharesPrimaryKey rows =
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) []
        (Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
          if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
          else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)) := by
  simp only [implementation_relatedTargetIds, Id.run, bind, pure]
  simp only [List.forIn_yield_eq_foldl]
  rw [← loop1_mprod sharesPrimaryKey ancestors ⟨[], 1⟩]
  rfl

theorem foldl_assign_eq_columnAssignment_gen (sharesPrimaryKey : Nat → Bool) :
    ∀ (as : List Nat) (acc : List (Nat × Nat)) (next : Nat),
      Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
        if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
        else (st.1 ++ [(a, st.2)], st.2 + 1)) (acc, next) as)
        = acc ++ columnAssignment sharesPrimaryKey as next := by
  intro as
  induction as with
  | nil => intro acc next; simp [columnAssignment]
  | cons a rest ih =>
      intro acc next
      simp only [List.foldl_cons, columnAssignment]
      cases h : sharesPrimaryKey a with
      | true => simp only [h, if_true]; rw [ih]; simp [List.append_assoc]
      | false => simp only [h, if_false, Bool.false_eq_true]; rw [ih]; simp [List.append_assoc]

theorem foldl_assign_eq_columnAssignment (sharesPrimaryKey : Nat → Bool)
    (ancestors : List Nat) :
    Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
      if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
      else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)
      = columnAssignment sharesPrimaryKey ancestors 1 := by
  simpa using foldl_assign_eq_columnAssignment_gen sharesPrimaryKey ancestors [] 1

theorem foldl_append_singleton_eq_map (rows : List (List Int)) :
    ∀ (L : List (Nat × Nat)) (acc : List (Nat × List Int)),
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) acc L
        = acc ++ L.map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0))) := by
  intro L
  induction L with
  | nil => intro acc; simp
  | cons a rest ih =>
      intro acc
      simp only [List.foldl_cons, List.map_cons, ih, List.append_assoc, List.cons_append,
        List.nil_append]

theorem resultFold_eq_map (rows : List (List Int)) :
    ∀ (L : List (Nat × Nat)),
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) [] L
        = L.map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0))) := by
  intro L
  have h := foldl_append_singleton_eq_map rows L []
  simpa using h

theorem correct_relatedTargetIds : ∀ (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)),
    -- ancestors are distinct keys (they model an insertion-ordered key set), and
    -- every row carries exactly one column per gathered identifier (no defaulted
    -- reads): the abstracted inputs the surrounding machinery is guaranteed to
    -- supply.
    ancestors.Nodup →
    (∀ r ∈ rows, r.length = 1 + (ancestors.filter (fun a => !sharesPrimaryKey a)).length) →
    problem_spec_relatedTargetIds ancestors sharesPrimaryKey rows
      (implementation_relatedTargetIds ancestors sharesPrimaryKey rows) := by
  intro ancestors sharesPrimaryKey rows _ _
  unfold problem_spec_relatedTargetIds
  rw [loops_to_folds, resultFold_eq_map, foldl_assign_eq_columnAssignment]

-- proof-end
