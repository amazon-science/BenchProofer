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
      -- PRE-PATCH (buggy): adopt the composed column list by mutating the part
      -- itself in place, instead of deriving a fresh copy. The part's definition
      -- is therefore overwritten with the composed column list and carried
      -- forward in that altered state — so a later evaluation that wants a
      -- different column list sees the stale one.
      let part := { part with columns := composedColumns }
      out := out ++ [(part, part)]
    else
      out := out ++ [(part, part)]
  return out
-- impl-end

-- proof-start
-- Gold proof body carried over verbatim. It is sound against the FIXED impl
-- (each adopting part carries its ORIGINAL definition forward), but the buggy
-- impl here carries the ALTERED part forward, so the `Prod.snd` frame clause is
-- false and the `hb` reduction / the final `id`-rewrite cannot close — the file
-- fails to verify (G-DIFF).
theorem loop_eq (composedColumns : List String) :
    ∀ (ps : List QueryPart) (acc : List (QueryPart × QueryPart)),
      (Id.run (forIn ps acc (fun part out =>
        (if part.columns = [] ∧ composedColumns ≠ []
         then ForInStep.yield (out ++ [({ part with columns := composedColumns }, part)])
         else ForInStep.yield (out ++ [(part, part)]) : Id (ForInStep (List (QueryPart × QueryPart))))))) =
      acc ++ ps.map (fun part =>
        if part.columns = [] ∧ composedColumns ≠ []
        then ({ part with columns := composedColumns }, part)
        else (part, part)) := by
  intro ps
  induction ps with
  | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    intro acc
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.columns = [] ∧ composedColumns ≠ []
    · rw [if_pos h]; simp only []; rw [ih]; rw [List.map_cons, if_pos h]; simp [List.append_assoc]
    · rw [if_neg h]; simp only []; rw [ih]; rw [List.map_cons, if_neg h]; simp [List.append_assoc]

theorem correct_propagateColumns :
    ∀ (parts : List QueryPart) (composedColumns : List String),
      problem_spec_propagateColumns parts composedColumns
        (implementation_propagateColumns parts composedColumns) := by
  intro parts composedColumns
  have hb : implementation_propagateColumns parts composedColumns
      = Id.run (forIn parts ([] : List (QueryPart × QueryPart)) (fun part out =>
        (if part.columns = [] ∧ composedColumns ≠ []
         then ForInStep.yield (out ++ [({ part with columns := composedColumns }, part)])
         else ForInStep.yield (out ++ [(part, part)]) : Id (ForInStep (List (QueryPart × QueryPart)))))) := rfl
  unfold problem_spec_propagateColumns
  rw [hb, loop_eq]
  simp only [List.nil_append, List.map_map]
  refine ⟨by simp, ?_, ?_⟩
  · rw [List.map_eq_map_iff.mpr]
    intro part _
    by_cases h : part.columns = [] ∧ composedColumns ≠ [] <;> simp [Function.comp, h]
  · rw [show (List.map (Prod.snd ∘ fun part : QueryPart =>
        if part.columns = [] ∧ composedColumns ≠ []
        then ({ part with columns := composedColumns }, part) else (part, part)) parts)
      = List.map id parts from ?_, List.map_id]
    rw [List.map_eq_map_iff.mpr]
    intro part _
    by_cases h : part.columns = [] ∧ composedColumns ≠ [] <;> simp [Function.comp, h]
-- proof-end
