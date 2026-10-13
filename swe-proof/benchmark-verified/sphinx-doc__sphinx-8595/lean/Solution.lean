import Mathlib
-- imports-end

/-!
Choosing which members of a module to document.

When every member of a module is to be considered, an explicit export list (the
module's `__all__`) governs the selection:

* if the module declares no export list at all, every discovered member is kept
  and documentation proceeds over all of them (an implicit check on origin is
  left to a later stage);
* if the module declares an export list — *including one that names nothing* —
  the selection is restricted to exactly the named members: every discovered
  member is kept in the result but any member whose name is not in the export
  list is marked as skipped.

When members are instead requested by name, only the requested names that are
actually present as members are returned, in the order requested.

The result is a pair: a flag saying whether the caller should still apply the
implicit origin check, together with the list of discovered members each tagged
with whether it is skipped.

A present-but-naming-nothing export list therefore keeps no member: every
discovered member is marked skipped, so the module contributes no documented
entries. This is the behavior that must hold for any export list, regardless of
how many names it carries.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The member
-- selection — the export-list-driven skipped tagging and the by-name lookup —
-- is modeled DEEPLY over the observable inputs (the export list, the discovered
-- member names, the requested names), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Select the members to document.

`wantAll` is true when every member is to be considered. `allAttr` is the
module's export list: `none` when the module declares none, `some names` when it
declares one (possibly naming nothing). `members` are the discovered member
names, in order. `requested` are the member names explicitly asked for (used
only when `wantAll` is false).

Returns `(check, tagged)` where `check` is the flag asking the caller to still
apply the implicit origin check, and `tagged` pairs each kept member name with
its skipped flag. -/
def selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) :=
  if wantAll then
    match allAttr with
    | none => (true, members.map (fun n => (n, false)))
    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
  else
    (false, requested.filterMap
      (fun name => if members.contains name then some (name, false) else none))
-- pure-end

-- post-conditions-start
/-- The selection produces exactly the pair dictated by the rule above: the
correct origin-check flag, and the discovered members each tagged with the right
skipped flag (or, when members are requested by name, exactly the present
requested names). -/
def problem_spec_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String)
    (result : Bool × List (String × Bool)) : Prop :=
  result = selectMembers wantAll allAttr members requested
-- post-conditions-end

-- impl-start
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)
-- impl-end


-- proof-start
theorem correct_selectMembers :
    ∀ (wantAll : Bool) (allAttr : Option (List String))
      (members : List String) (requested : List String),
      problem_spec_selectMembers wantAll allAttr members requested
        (implementation_selectMembers wantAll allAttr members requested) := by
  intro wantAll allAttr members requested
  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
    intro f xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
      rw [ih]; simp
  have fmKey : ∀ (xs : List String) (acc),
      (forIn (m := Id) xs acc
        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
          else pure (ForInStep.yield r))) =
        acc ++ xs.filterMap
          (fun name => if name ∈ members then some (name, false) else none) := by
    intro xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      by_cases hh : h ∈ members
      · simp only [hh, if_true]
        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
        rw [ih]; simp [hh]
      · simp only [hh, if_false]
        show (forIn (m:=Id) t acc _) = _
        rw [ih]; simp [hh]
  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
  cases wantAll
  · simp only [Bool.false_eq_true, if_false]
    simp [fmKey]
    rfl
  · simp only [if_true]
    cases allAttr <;> simp [mapKey] <;> rfl

-- proof-end
