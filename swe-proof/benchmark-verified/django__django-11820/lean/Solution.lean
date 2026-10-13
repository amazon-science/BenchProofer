import Mathlib
-- imports-end

/-!
Deciding whether a dotted field-lookup path is valid for a model in a model
graph.

A model graph is a collection of models indexed by natural numbers. Each model
exposes, by name, the fields declared on it; a field is either a *relation*
(it points at another model in the graph) or a plain value field. Every model
also has a distinguished *primary-key* field, reachable through the alias
`"pk"` (the alias is NOT one of the by-name declared fields — it is resolved
separately).

A lookup path is a list of name segments (the pieces of an `"a__b__c"` string).
Validity is decided by walking the path one segment at a time, starting at a
given model, while remembering the last field that was resolved:

  * To resolve a segment against the *current model*: the segment `"pk"`
    resolves to that model's primary-key field; any other segment resolves to
    the by-name field of that name, if one exists.
  * A resolved field that is a relation moves the walk onto the model it points
    at; a resolved field that is NOT a relation ends the walk — there is no
    current model for the remaining segments.
  * If a segment cannot be resolved (no current model, or the name is not a
    declared field of the current model), the path is acceptable at that
    segment ONLY when the most recently resolved field accepts the segment as a
    registered transform/lookup; otherwise the whole path is invalid. If no
    field has been resolved yet, the path is invalid.

The path is valid exactly when no segment makes it invalid.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The model graph is
-- supplied as data: each model's by-name field resolution, its primary-key
-- field, and per-field relation target / transform admissibility are carried by
-- `ModelInfo` / `FieldInfo` values. The behavior under spec is solely WHICH
-- paths are valid given that data, so the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
/-- A field declared on a model. `isRelation` says whether following it moves
the walk onto another model (`target`, an index into the model graph). For a
non-relation field these are irrelevant. `acceptsTransform name` says whether the
field accepts `name` as a registered transform/lookup (so a segment that is not
a declared field may still be acceptable). -/
structure FieldInfo where
  isRelation : Bool
  target : Nat
  acceptsTransform : String → Bool

/-- A model in the graph. `getField name` is the by-name field of that name, if
declared (`none` otherwise); the `"pk"` alias is NOT covered by `getField` and
is resolved through `primaryKey`. -/
structure ModelInfo where
  getField : String → Option FieldInfo
  primaryKey : FieldInfo

/-- Walk state: the current model (`none` once the walk has ended), the most
recently resolved field (`none` until one is resolved), and whether the path has
already been found invalid. -/
abbrev WalkState := Option Nat × Option FieldInfo × Bool

/-- Process one path segment. `fld` is the last resolved field; on a resolution
failure the segment is tolerated only when that field accepts it as a transform. -/
def stepPath (models : Nat → ModelInfo) (st : WalkState) (part : String) : WalkState :=
  let (cur, fld, invalid) := st
  match cur with
  | some c =>
      let resolved := if part == "pk" then some (models c).primaryKey
                      else (models c).getField part
      match resolved with
      | some f =>
          (if f.isRelation then some f.target else none, some f, invalid)
      | none =>
          let bad := match fld with
                     | some pf => !pf.acceptsTransform part
                     | none => true
          (cur, fld, invalid || bad)
  | none =>
      let bad := match fld with
                 | some pf => !pf.acceptsTransform part
                 | none => true
      (none, fld, invalid || bad)

/-- Validity of a whole path: fold the segments through `stepPath` from the
start model and report that no segment invalidated the path. -/
def pathValid (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool :=
  let (_, _, invalid) := parts.foldl (stepPath models) (some startModel, none, false)
  !invalid
-- pure-end

-- post-conditions-start
/-- The decision is fully pinned to the model graph, the start model, and the
path segments: the result is `true` exactly when walking the path leaves it
valid (no segment invalidates it). No output is left free. -/
def problem_spec_lookupPathValid
    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String)
    (result : Bool) : Prop :=
  result = pathValid models startModel parts
-- post-conditions-end

-- impl-start
def implementation_lookupPathValid
    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
  -- Walk the path one segment at a time from the start model, remembering the
  -- last resolved field; a non-relation field ends the walk, the "pk" alias
  -- resolves to the primary-key field, and an unresolved segment is tolerated
  -- only if the last field accepts it as a transform.
  let mut cur : Option Nat := some startModel
  let mut fld : Option FieldInfo := none
  let mut invalid : Bool := false
  for part in parts do
    match cur with
    | some c =>
        let resolved := if part == "pk" then some (models c).primaryKey
                        else (models c).getField part
        match resolved with
        | some f =>
            fld := some f
            if f.isRelation then
              cur := some f.target
            else
              cur := none
        | none =>
            match fld with
            | some pf => if !(pf.acceptsTransform part) then invalid := true
            | none => invalid := true
    | none =>
        match fld with
        | some pf => if !(pf.acceptsTransform part) then invalid := true
        | none => invalid := true
  return !invalid
-- impl-end


-- proof-start
/-- The pure `WalkState → String → WalkState` transformer obtained by reading
the `for`-loop body of `implementation_lookupPathValid` as a single state update
on the tuple `(cur, fld, invalid)`. Extensionally the same recursion as
`stepPath`; the difference is only the surface `if _ then true else invalid`
vs. `invalid || bad` shape, discharged by `loopBody_eq_stepPath`. -/
def loopBody (models : Nat → ModelInfo) (st : WalkState) (part : String) : WalkState :=
  let (cur, fld, invalid) := st
  match cur with
  | some c =>
      let resolved := if part == "pk" then some (models c).primaryKey
                      else (models c).getField part
      match resolved with
      | some f =>
          (if f.isRelation then some f.target else none, some f, invalid)
      | none =>
          match fld with
          | some pf => (cur, fld, if !(pf.acceptsTransform part) then true else invalid)
          | none => (cur, fld, true)
  | none =>
      match fld with
      | some pf => (cur, fld, if !(pf.acceptsTransform part) then true else invalid)
      | none => (cur, fld, true)

/-- The `for`-loop of `implementation_lookupPathValid` run from an ARBITRARY
initial walk-state `st` (rather than the fixed `(some startModel, none, false)`).
Abstracting the start state is exactly what lets the fold-equivalence be proved
by a straightforward induction on `parts`; the fixed-start impl is the `st =
(some startModel, none, false)` instance (`impl_eq_implLoop`). -/
def implLoop (models : Nat → ModelInfo) (parts : List String) (st : WalkState) : Bool := Id.run do
  let mut cur : Option Nat := st.1
  let mut fld : Option FieldInfo := st.2.1
  let mut invalid : Bool := st.2.2
  for part in parts do
    match cur with
    | some c =>
        let resolved := if part == "pk" then some (models c).primaryKey
                        else (models c).getField part
        match resolved with
        | some f =>
            fld := some f
            if f.isRelation then cur := some f.target else cur := none
        | none =>
            match fld with
            | some pf => if !(pf.acceptsTransform part) then invalid := true
            | none => invalid := true
    | none =>
        match fld with
        | some pf => if !(pf.acceptsTransform part) then invalid := true
        | none => invalid := true
  return !invalid

/-- `implementation_lookupPathValid` is `implLoop` at the fixed start state.
Holds by `rfl` (the `for`-loop bodies are syntactically identical). -/
theorem impl_eq_implLoop (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) :
    implementation_lookupPathValid models startModel parts
      = implLoop models parts (some startModel, none, false) := by rfl

/-- One unfolding of `implLoop`: running the loop on `p :: ps` from `st` equals
running it on `ps` from `loopBody models st p`. This is the single-step bridge
between the imperative `for` body and the pure `loopBody`; prove it by casing on
`st` and reducing the (single) `forIn` step. -/
theorem implLoop_cons (models : Nat → ModelInfo) (p : String) (ps : List String) (st : WalkState) :
    implLoop models (p :: ps) st = implLoop models ps (loopBody models st p) := by
  obtain ⟨cur, fld, invalid⟩ := st
  simp only [implLoop, loopBody, List.forIn_cons]
  repeat' split
  all_goals rfl

/-- `implLoop` computes exactly the negated `invalid` flag of the `loopBody`
fold. Prove by induction on `parts` (generalizing `st`): `nil` is `rfl`, `cons`
is `implLoop_cons` + `List.foldl_cons` + the IH. -/
theorem implLoop_eq_foldl (models : Nat → ModelInfo) (parts : List String) (st : WalkState) :
    implLoop models parts st = !((parts.foldl (loopBody models) st).2.2) := by
  induction parts generalizing st with
  | nil => rfl
  | cons p ps ih =>
      rw [implLoop_cons, List.foldl_cons, ih]

theorem impl_as_foldl (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) :
    implementation_lookupPathValid models startModel parts
      = !((parts.foldl (loopBody models) (some startModel, none, false)).2.2) := by
  rw [impl_eq_implLoop, implLoop_eq_foldl]

theorem loopBody_eq_stepPath (models : Nat → ModelInfo) (st : WalkState) (part : String) :
    loopBody models st part = stepPath models st part := by
  obtain ⟨cur, fld, invalid⟩ := st
  simp only [loopBody, stepPath]
  cases cur <;> cases fld <;> split <;> simp_all [Bool.or_comm]

theorem correct_lookupPathValid :
    ∀ (models : Nat → ModelInfo) (startModel : Nat) (parts : List String),
      problem_spec_lookupPathValid models startModel parts
        (implementation_lookupPathValid models startModel parts) := by
  intro models startModel parts
  unfold problem_spec_lookupPathValid
  rw [impl_as_foldl models startModel parts]
  have hfun : loopBody models = stepPath models := by
    funext st part
    exact loopBody_eq_stepPath models st part
  rw [hfun]
  simp only [pathValid]

-- proof-end
