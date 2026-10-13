import Mathlib
-- imports-end

/-!
Expanding a model's *default ordering specification* into a flat list of concrete
column ordering directives.

A default ordering specification is an ordered list of items. Two kinds of item
occur:

  * a plain **field reference** — a textual name (possibly a multi-part lookup)
    that still has to be resolved against the model into one or more concrete
    column ordering directives; and
  * an already-formed **ordering expression** — a directive that has *already*
    been built and therefore needs no further resolution.

The desired behavior is: walk the specification in order and expand each item.
A field reference is expanded by the (unchanged) name-resolution routine, which
turns it into its concrete directives. An ordering expression is *not* a name and
must NOT be sent through name resolution; it is already a directive, so it is
emitted directly — paired with the flag `false`, meaning the surrounding sort
direction is not re-applied to it — and the result list is the in-order
concatenation of all per-item expansions.

The point pinned by the specification is the per-item dispatch: every ordering
expression in the specification contributes exactly itself (with flag `false`),
and only field references are routed through name resolution.
-/

-- axioms-start
/-- An already-formed ordering directive (an "ordering expression"). Opaque: only
its identity is observed by the modeled behavior — it is carried through
unchanged. The mapping file gives the bijection with the repository object. -/
opaque OrderExpr : Type

/-- A single item of a default ordering specification: either a textual field
reference that still needs resolving, or an already-formed ordering expression. -/
inductive OrderingItem where
  | fieldRef  (name : String)
  | expression (e : OrderExpr)

/-- The (UNCHANGED) name-resolution routine: it expands a single specification
item into its concrete column ordering directives, each paired with its
descending flag. It is referenced identically in the specification and in the
implementation — the modeled behavior does not change *how* a field reference is
resolved, only *which* items are sent to it. Declared `opaque` so it can appear
in the executable implementation. -/
opaque resolveFieldRef : OrderingItem → List (OrderExpr × Bool)
-- axioms-end

-- pure-start
/-- The expansion of a single specification item:

  * an ordering expression is already a directive, so it contributes exactly
    itself paired with `false` (the surrounding direction is not re-applied);
  * a field reference is contributed via the unchanged name-resolution routine. -/
def expandOrderingItem (item : OrderingItem) : List (OrderExpr × Bool) :=
  match item with
  | .expression e => [(e, false)]
  | .fieldRef _   => resolveFieldRef item
-- pure-end

-- post-conditions-start
/-- The expanded ordering is the in-order concatenation of the per-item
expansions: every ordering expression contributes exactly itself (flagged
`false`), and every field reference contributes its name-resolved directives.
Nothing is dropped, reordered, or invented; the whole result is pinned to the
input specification. -/
def problem_spec_expandOrdering
    (items : List OrderingItem) (result : List (OrderExpr × Bool)) : Prop :=
  result = items.flatMap expandOrderingItem
-- post-conditions-end

-- impl-start
def implementation_expandOrdering
    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
  let mut results : List (OrderExpr × Bool) := []
  for item in items do
    match item with
    | .expression e =>
        -- Already a directive: emit it directly (flagged `false`) and move on,
        -- skipping name resolution.
        results := results ++ [(e, false)]
    | .fieldRef _ =>
        results := results ++ resolveFieldRef item
  return results
-- impl-end

-- proof-start
theorem helper_expandOrdering (items : List OrderingItem)
    (init : List (OrderExpr × Bool)) :
    Id.run (forIn items init (fun item r =>
        (match item with
          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
          : Id (ForInStep (List (OrderExpr × Bool))))))
      = init ++ items.flatMap expandOrderingItem := by
  induction items generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
  | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      cases a with
      | expression e =>
          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
      | fieldRef name =>
          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]

theorem correct_expandOrdering :
    ∀ (items : List OrderingItem),
      problem_spec_expandOrdering items (implementation_expandOrdering items) := by
  intro items
  unfold problem_spec_expandOrdering implementation_expandOrdering
  have h2 : (Id.run do
        let r ← forIn items [] fun item r =>
            match item with
            | OrderingItem.expression e => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(e, false)]))
            | OrderingItem.fieldRef _ => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ resolveFieldRef item))
        pure r)
      = Id.run (forIn items [] (fun item r =>
        (match item with
          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
  rw [h2, helper_expandOrdering]
  simp
-- proof-end
