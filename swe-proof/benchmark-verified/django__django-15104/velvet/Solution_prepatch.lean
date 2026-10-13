import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-observations the routine consults are modeled as FREE inputs of
   each field record (see `FieldDef`): whether a field points at another model
   (`relational : Bool`) and the field's already-canonicalized definition
   bindings (`kwargs`). The postcondition holds for EVERY value of both, so
   neither is owed a contract — each is strictly weaker than any concrete
   producer of those values (directive 7). The behaviour this bundle pins — how
   the relation-target binding is elided when assembling the comparison view —
   is modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- One field's canonicalized definition, reduced to exactly the two facts the
   relation-agnostic view distinguishes:
     * `relational` — whether the field references another model (so its target
       binding must be dropped before comparison);
     * `kwargs` — the field's keyword bindings, each a name paired with an opaque
       identity token for its value (the values are never inspected, only carried
       and keyed). The relation-target binding is the entry keyed `"to"`.
   Every other facet of a field is orthogonal to this view (mapping.md §2). -/
structure FieldDef where
  relational : Bool
  kwargs : List (String × Int)
  deriving Inhabited, DecidableEq

/- The relation-target binding name. -/
def targetKey : String := "to"

/- Drop the relation-target binding from a set of keyword bindings: keep every
   binding whose name differs from the target key. Removing an absent key is a
   no-op — the result is well-defined whether or not the binding is present. -/
def dropTarget (kw : List (String × Int)) : List (String × Int) :=
  kw.filter (fun p => p.1 != targetKey)

/- The comparison view of a single field: a field that references another model
   has its relation-target binding elided (so two fields differing only in what
   they relate to compare equal); a non-relational field is carried unchanged. -/
def fieldView (f : FieldDef) : List (String × Int) :=
  if f.relational then dropTarget f.kwargs else f.kwargs

/- The relation-agnostic definitions of a whole field collection: the per-field
   comparison view of each field, in order. Front-recursive so a single unfold
   is available per loop step (the fold pattern, plan §5.4). -/
def viewAll : List FieldDef → List (List (String × Int))
  | []      => []
  | f :: fs => fieldView f :: viewAll fs

@[grind] lemma viewAll_nil : viewAll [] = [] := rfl
@[grind] lemma viewAll_cons (f : FieldDef) (fs : List FieldDef) :
    viewAll (f :: fs) = fieldView f :: viewAll fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the relation-agnostic definitions of a field collection, used to
   detect renames (where what related fields point at changes, so the relation
   target must be ignored). `fields` is read-only.

   Desired behaviour: the routine ALWAYS succeeds (it never reports failure —
   carried by `Except.ok`) and returns, in order, the per-field comparison view
   of each field; a field that references another model has its relation-target
   binding elided, a non-relational field is carried unchanged. Crucially this
   must hold for EVERY field collection, including one in which a relational
   field carries no explicit relation-target binding at all — such a field still
   yields its remaining bindings, with no failure reported. -/
method fieldDefsIgnoringRelationTargets (fields : List FieldDef)
    return (out : Except Unit (List (List (String × Int))))
  ensures out = Except.ok (viewAll fields)
  do
    -- impl-start
    -- Pre-image skeleton: eliding a relational field's target binding is done by
    -- an UNCONDITIONAL removal that signals failure when that binding is absent
    -- (the binding name is required to be present). A relational field carrying
    -- no explicit target binding therefore makes the routine report failure
    -- (`Except.error ()`) instead of yielding its remaining bindings — so it
    -- fails the spec's `out = Except.ok (viewAll fields)`, and prove_correct
    -- MUST fail (G-DIFF).
    let mut result : List (List (String × Int)) := []
    let mut raised : Bool := false
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      let missing := f.relational && !(f.kwargs.any (fun p => p.1 == targetKey))
      raised := raised || missing
      result := fieldView f :: result
      i := i - 1
    let out : Except Unit (List (List (String × Int))) :=
      if raised then Except.error () else Except.ok result
    return out
    -- impl-end

/- The backward-fold step: dropping one fewer field exposes the field at `i-1`
   on the front, so `viewAll` peels one `fieldView`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma viewAll_drop_step (fields : List FieldDef) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    viewAll (fields.drop (i - 1)) = fieldView fields[i - 1]! :: viewAll (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, viewAll_cons]

prove_correct fieldDefsIgnoringRelationTargets by
  loom_solve
  rw [viewAll_drop_step fields i (by omega) (by omega)]
  simp_all
