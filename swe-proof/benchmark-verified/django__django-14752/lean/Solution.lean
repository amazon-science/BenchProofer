import Mathlib
-- imports-end

/-!
Assembling the JSON payload of a search-results handler.

The handler answers a lookup request by producing a response carrying two parts:

  * `results`: a list of per-item entries, one for each object selected by the
    query, in the same order as the selected objects;
  * `more`: a single flag reporting whether further pages of results remain.

The way a single selected object is turned into its entry is supplied as a
dedicated per-item rendering step, applied uniformly to every selected object.
Modeling that step as an arbitrary function pins the behavior below to exactly
"each entry is the per-item rendering applied to the corresponding object, in
order, and the more-flag is reported verbatim" — independent of what any
particular rendering produces.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two steps are modeled as
-- arbitrary function parameters:
--   * `render : Obj → String → E` — the per-item rendering that turns one
--     selected object (together with the field key identifying which attribute
--     names the entry) into its response entry. Supplied as a parameter so the
--     spec holds for EVERY rendering, the modeled behavior being solely that the
--     results list is this rendering applied per object, in order.
-- The objects and the entry type are likewise abstract carriers (`Obj`, `E`):
-- the handler never inspects an object except through `render`, and never
-- inspects an entry at all. Hence the spec needs no `opaque`/`axiom` contract.
-- axioms-end

-- pure-start
/-- The response payload: the per-item entries and the has-more flag. -/
structure Resp (E : Type) where
  results : List E
  more : Bool
-- pure-end

-- post-conditions-start
/-- The response is fully pinned to the inputs (directive 5 frame):

  * `results` is the per-item rendering applied to each selected object, in the
    same order as the selected objects (no entry added, dropped, reordered, or
    computed by any means other than `render`);
  * `more` equals the supplied has-more flag verbatim.

No output component is left free: every entry is `render` of the corresponding
object, and the flag is the input flag. -/
def problem_spec_get {Obj E : Type}
    (render : Obj → String → E)
    (objects : List Obj) (fieldKey : String) (hasMore : Bool)
    (result : Resp E) : Prop :=
  result.results = objects.map (fun o => render o fieldKey) ∧
  result.more = hasMore
-- post-conditions-end

-- impl-start
def implementation_get {Obj E : Type}
    (render _defaultRender : Obj → String → E)
    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
  -- Build the results list by applying the per-item rendering to each selected
  -- object in turn. The per-item rendering used is `render` — the dispatched,
  -- hence overridable, step — applied uniformly to every selected object.
  let mut results : List E := []
  for o in objects do
    results := results ++ [render o fieldKey]
  -- Report the has-more flag verbatim.
  return { results := results, more := hasMore }
-- impl-end

-- proof-start
theorem correct_get {Obj E : Type} :
    ∀ (render defaultRender : Obj → String → E)
      (objects : List Obj) (fieldKey : String) (hasMore : Bool),
      problem_spec_get render objects fieldKey hasMore
        (implementation_get render defaultRender objects fieldKey hasMore) := by
  intro render defaultRender objects fieldKey hasMore
  -- Helper: the cleaned `forIn` accumulation appends the per-item renderings.
  have helper : ∀ (os : List Obj) (init : List E),
      Id.run (forIn os init (fun o r => pure (ForInStep.yield (r ++ [render o fieldKey]))))
        = init ++ os.map (fun o => render o fieldKey) := by
    intro os
    induction os with
    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
        intro init; rw [List.forIn_cons]
        simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
  refine ⟨?_, rfl⟩
  show (implementation_get render defaultRender objects fieldKey hasMore).results = _
  unfold implementation_get
  simp only [Id.run, bind]
  have := helper objects []
  simp only [Id.run] at this
  rw [this]
  rfl
-- proof-end
