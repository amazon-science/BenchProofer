import Mathlib
-- imports-end

/-!
Evaluating a composed query to project a chosen list of columns.

A composed query is built from several query parts. When the composed query is
evaluated to project a specific list of columns, each part that does NOT itself
specify a column list adopts the composed query's column list for THIS evaluation;
a part that already specifies its own column list is used as given.

The contract that matters here: producing one evaluation's column projection must
leave the underlying part definitions exactly as they were. The parts are shared,
so if an evaluation altered a part while adopting the composed column list, a
LATER evaluation of the same composed query for a DIFFERENT column list would see
the stale list and be unable to change its columns. Hence each evaluation derives
the per-part query it builds from, while the part definitions themselves are
carried through unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is deep-modeled.
-- The per-evaluation step reads one thing off each part — whether it already
-- specifies a column list — and produces two things: the query used to build that
-- part for this evaluation, and the part's definition carried forward. A query
-- part is observed solely by the list of columns it projects, modeled directly
-- as `QueryPart.columns`, so the bundle needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- A query part, observed only by the list of column names it projects
(empty ⇔ it specifies no particular column list of its own). -/
structure QueryPart where
  columns : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Evaluating the composed query (column list `composedColumns`) over its
`parts` is fully pinned to the inputs. Each result entry corresponds to one part:
its first component is the query actually built for this evaluation, its second
component is the part's definition carried forward.

  * there is exactly one result entry per part;
  * the query built for a part adopts the composed column list precisely when the
    part specifies no column list of its own AND the composed query requests a
    specific column list (`composedColumns ≠ []`); otherwise the part is used as
    given (directive-5 frame: the used-as-given branch pins it to its input);
  * EVERY part definition is carried forward exactly equal to its input
    (directive-5 frame): producing this evaluation never alters a part, so a
    later evaluation may choose a different column list.

Both output components are pinned for every part, so no incorrect evaluator can
fill a free hole — in particular it may not leave a part altered. -/
def problem_spec_propagateColumns
    (parts : List QueryPart) (composedColumns : List String)
    (result : List (QueryPart × QueryPart)) : Prop :=
  result.length = parts.length ∧
  (result.map Prod.fst = parts.map (fun part =>
      if part.columns = [] ∧ composedColumns ≠ []
      then { part with columns := composedColumns }
      else part)) ∧
  (result.map Prod.snd = parts)
-- post-conditions-end

-- impl-start
def implementation_propagateColumns
    (parts : List QueryPart) (composedColumns : List String)
    : List (QueryPart × QueryPart) := Id.run do
  let mut out : List (QueryPart × QueryPart) := []
  for part in parts do
    if part.columns = [] ∧ composedColumns ≠ [] then
      -- This part fixes no column list of its own and the composed query requests
      -- one: build this evaluation's query from a fresh copy carrying the composed
      -- column list, while carrying the part's own definition forward unchanged.
      let derived := { part with columns := composedColumns }
      out := out ++ [(derived, part)]
    else
      -- The part already fixes its own columns (or none are requested): use it as
      -- given and carry it forward unchanged.
      out := out ++ [(part, part)]
  return out
-- impl-end

-- proof-start
theorem correct_propagateColumns :
    ∀ (parts : List QueryPart) (composedColumns : List String),
      problem_spec_propagateColumns parts composedColumns
        (implementation_propagateColumns parts composedColumns) := by
  intro parts cc
  have helper : ∀ (init : List (QueryPart × QueryPart)),
      Id.run (forIn parts init (fun part r =>
        (if part.columns = [] ∧ cc ≠ [] then
          pure (ForInStep.yield (r ++ [(({ part with columns := cc } : QueryPart), part)]))
        else
          pure (ForInStep.yield (r ++ [(part, part)]))) : Id _))
        = init ++ parts.map (fun part =>
            ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
    intro init
    induction parts generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a.columns = [] ∧ cc ≠ []
      · rw [if_pos h]
        simp only [ih, if_pos h, List.map_cons]
        rw [List.append_assoc]; rfl
      · rw [if_neg h]
        simp only [ih, if_neg h, List.map_cons]
        rw [List.append_assoc]; rfl
  have himpl : implementation_propagateColumns parts cc
      = parts.map (fun part =>
          ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
    have hb := helper []
    rw [List.nil_append] at hb
    rw [← hb]
    rfl
  unfold problem_spec_propagateColumns
  rw [himpl]
  refine ⟨?_, ?_, ?_⟩
  · simp [List.length_map]
  · simp only [List.map_map, Function.comp_def]
  · simp only [List.map_map, Function.comp_def]
    exact List.map_id_fun' ▸ rfl
-- proof-end
