import Mathlib
-- imports-end

/-!
Building the list of inline editors to display for an admin page, given a
particular request and the object being edited.

An admin page may attach a number of *inline* editor classes. Which classes are
attached need not be constant: the set of inline classes selected for a page
can depend on the current request and the object being edited, so the page is
given the already-selected list of inline classes for this request/object rather
than reading a static attribute.

For each selected inline class the page constructs one editor. When the call is
made on behalf of a request, an editor is shown only if the viewer is allowed to
interact with it at all — that is, the viewer may view-or-change, add, or delete
through it; an editor the viewer can do none of these with is omitted entirely.
For a shown editor whose viewer may not add new rows through it, the editor's
maximum number of new rows is forced to zero. When there is no request in
context, every selected class yields an editor with no such restriction.

The resulting list preserves the order of the selected inline classes, with the
omitted ones removed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The list of
-- selected inline classes for this request/object enters as plain data
-- (`hookInlines`), as does the static attribute it may override (`selfInlines`).
-- Each inline class carries the three permission outcomes of its editor (view-or-
-- change / add / delete) as booleans, so the per-editor decision is modeled
-- directly from data rather than via a callee contract. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- An inline editor class together with the three permission outcomes its editor
reports for the current request/object. `id` is the class's identity (which class
it is). -/
structure Inline where
  id : Nat
  hasViewOrChange : Bool
  hasAdd : Bool
  hasDelete : Bool
deriving DecidableEq, Repr

/-- A constructed inline editor instance: the class it was built from (`id`) and
whether its maximum number of new rows was forced to zero. -/
structure InlineInstance where
  id : Nat
  maxNumZeroed : Bool
deriving DecidableEq, Repr

/-- Whether an inline class survives the per-request filtering: with no request in
context every class is kept; under a request a class is kept exactly when the
viewer may view-or-change, add, or delete through its editor. -/
def keepInline (hasRequest : Bool) (i : Inline) : Bool :=
  !hasRequest || i.hasViewOrChange || i.hasAdd || i.hasDelete

/-- The editor built for a kept inline class: its maximum number of new rows is
forced to zero exactly when a request is in context and the viewer may not add
through it. -/
def toInstance (hasRequest : Bool) (i : Inline) : InlineInstance :=
  { id := i.id, maxNumZeroed := hasRequest && !i.hasAdd }
-- pure-end

-- post-conditions-start
/-- The selection hook, by default, returns the page's own list of inline classes
unchanged. (It exists to be overridden so that the selected list may depend on the
request/object; its default identity behavior is what is pinned here.) -/
def problem_spec_getInlines
    (selfInlines : List Inline) (result : List Inline) : Prop :=
  result = selfInlines
-- post-conditions-end

-- impl-start
def implementation_getInlines (selfInlines : List Inline) : List Inline := Id.run do
  return selfInlines
-- impl-end

-- proof-start
theorem correct_getInlines :
    ∀ (selfInlines : List Inline),
      problem_spec_getInlines selfInlines (implementation_getInlines selfInlines) := by
  intro selfInlines
  rfl
-- proof-end

-- post-conditions-start
/-- The produced editor list is fully pinned to the inputs: it is exactly the
list of selected inline classes (`hookInlines`, in order), with the classes the
viewer can do nothing with under a request removed (`keepInline`), each surviving
class mapped to its editor with the max-rows restriction applied as appropriate
(`toInstance`). The static attribute `selfInlines` does NOT determine the result —
only the selected list does. -/
def problem_spec_getInlineInstances
    (hasRequest : Bool) (selfInlines hookInlines : List Inline)
    (result : List InlineInstance) : Prop :=
  result = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
-- post-conditions-end

-- impl-start
def implementation_getInlineInstances
    (hasRequest : Bool) (selfInlines hookInlines : List Inline) :
    List InlineInstance := Id.run do
  let mut inlineInstances : List InlineInstance := []
  for inlineClass in hookInlines do
    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
    if hasRequest then
      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
        continue
      if !inlineClass.hasAdd then
        inst := { inst with maxNumZeroed := true }
    inlineInstances := inlineInstances ++ [inst]
  return inlineInstances
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop body (proof scaffolding): definitionally equal to the
desugared `do`-block body of `implementation_getInlineInstances`, but written with
plain `if … then … else` and no `pure PUnit.unit` / `continue` desugaring noise so
it can be reasoned about by induction. -/
private def cleanBody_getInlineInstances
    (hasRequest : Bool) (inlineClass : Inline) (r : List InlineInstance) :
    Id (ForInStep (List InlineInstance)) :=
  if hasRequest then
    if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
      ForInStep.yield r
    else if !inlineClass.hasAdd then
      ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := true }])
    else
      ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := false }])
  else
    ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := false }])

/-- Closed form for the cleaned loop, generalized over the accumulator
(Route B helper): folding `cleanBody_getInlineInstances` over `xs` appends, to the
running accumulator, exactly the kept-and-mapped instances. -/
private theorem foldClean_getInlineInstances
    (hasRequest : Bool) (xs : List Inline) (init : List InlineInstance) :
    Id.run (forIn xs init (cleanBody_getInlineInstances hasRequest))
      = init ++ (xs.filter (keepInline hasRequest)).map (toInstance hasRequest) := by
  induction xs generalizing init with
  | nil =>
    simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, cleanBody_getInlineInstances, List.filter_cons, keepInline,
      toInstance] at ih ⊢
    by_cases h : hasRequest = true <;>
      simp only [h, Bool.not_true, Bool.not_false, Bool.true_and, Bool.false_and,
        Bool.false_or, Bool.true_or, if_true, if_false, ih] <;>
      rcases ha : a.hasViewOrChange <;> rcases hb : a.hasAdd <;> rcases hc : a.hasDelete <;>
        simp_all [toInstance, List.map_cons, List.map_nil, List.nil_append, List.cons_append]

theorem correct_getInlineInstances :
    ∀ (hasRequest : Bool) (selfInlines hookInlines : List Inline),
      problem_spec_getInlineInstances hasRequest selfInlines hookInlines
        (implementation_getInlineInstances hasRequest selfInlines hookInlines) := by
  intro hasRequest selfInlines hookInlines
  unfold problem_spec_getInlineInstances implementation_getInlineInstances
  -- The desugared loop body is definitionally equal to the cleaned body, so we can
  -- `show` the goal in cleaned form and discharge it with the closed-form helper.
  show Id.run (forIn hookInlines ([] : List InlineInstance)
        (cleanBody_getInlineInstances hasRequest))
      = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
  rw [foldClean_getInlineInstances, List.nil_append]
-- proof-end
