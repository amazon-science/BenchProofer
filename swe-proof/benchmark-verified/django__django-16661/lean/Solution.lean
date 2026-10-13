import Mathlib
-- imports-end

/-!
Deciding whether an admin change-list may filter on a chained relational lookup.

A lookup is a chain of components (e.g. `a__b__c`) walked left-to-right over a
model graph. Walking accumulates the subset of components that name a genuine
relational HOP — the "relation parts". A component is dropped from the relation
parts when the value it names would already be reachable from the previous
model's own local column, so that two syntactically different chains that reach
the SAME stored value are treated as one.

Three situations make the previous relation's continuation collapse into the
local model (and so the component is NOT counted as a fresh hop):

  * the field is the link that realises concrete model inheritance (a parent
    link), so the child row already carries the parent's identity locally;
  * the field IS the model's own synthesised primary key, so its value is the
    local row's identity;
  * the model has a synthesised primary key AND the component names one of the
    previous relation's target columns, so the value is already reachable from
    the previous model's local column.

Crucially, when a relation's own primary key is itself a relation to another
model (a foreign key used as the primary key), that relation is a genuine hop:
none of the three collapsing situations applies, so the component MUST stay in
the relation parts. Otherwise the chain would be shortened to a form that is not
declarable as an allowed filter.

After the walk, a chain is permitted when it resolves to at most one relation
part (a purely local filter), or when the accumulated relation parts — with or
without the final trailing component — match one of the declared allowed
filters. A separate early allowance covers foreign-key raw-id popups.

MODELING. The model graph metadata resolved at each component is abstracted to a
`PathStep` record carrying only the booleans the walk branches on (mapping.md
gives the bijection to the real field metadata). Component names are identities
(`Nat`); a chain is a `List Nat`; the declared allowed filters are a
`List (List Nat)`. Only equality of chains is observed.
-/

-- axioms-start
-- No unchanged outside callee contributes a property this specification
-- consumes. The model-graph metadata that the walk reads at each component
-- (whether the component resolves to a field, whether the previous field is a
-- relation, whether the field is a parent link / the synthesised primary key,
-- whether the model has a synthesised primary key, whether the component is one
-- of the previous relation's target columns, and whether the walk continues) is
-- abstracted as the input `PathStep` record — a structure restricted to the
-- touched fields — not axiomatised. Hence there is no `opaque`/`axiom` callee.
-- axioms-end

-- pure-start
/-- The model-graph metadata resolved at one lookup component, restricted to the
booleans the walk branches on (mapping.md gives the bijection to the real field
metadata):
* `part` — the component's name identity;
* `exists_` — the component resolves to a field on the current model;
* `isRelation` — the resolved field is itself a relation (i.e. it would be the
  "previous relation" for the next component);
* `hasPathInfos` — the resolved field continues the walk to a further model;
* `inTargetFields` — the resolved field is one of the previous relation's target
  columns;
* `inParents` — the resolved field is the link realising concrete inheritance;
* `isAutoField` — the resolved field is the current model's synthesised primary
  key;
* `modelHasAutoField` — the current model has a synthesised primary key;
* `partInPrevToFields` — this component names one of the previous relation's
  declared target columns. -/
structure PathStep where
  part : Nat
  exists_ : Bool
  isRelation : Bool
  hasPathInfos : Bool
  inTargetFields : Bool
  inParents : Bool
  isAutoField : Bool
  modelHasAutoField : Bool
  partInPrevToFields : Bool
deriving DecidableEq, Inhabited

/-- The walk's running state:
* `relationParts` — the component names counted as genuine relational hops;
* `prev` — the previous field's `isRelation`, or `none` before the first hop;
* `lastPart` — the component name reached on the final processed step;
* `stopped` — the walk has halted (component did not resolve, or a non-relational
  field ended the chain). -/
structure LoopState where
  relationParts : List Nat
  prev : Option Bool
  lastPart : Nat
  stopped : Bool
deriving DecidableEq, Inhabited

/-- Whether a resolved relational field continues the previous relation's local
column — in which case the component is folded into the local model rather than
counted as a fresh hop. None of the three collapsing situations may apply. -/
def continuesLocal (step : PathStep) : Bool :=
  !step.inParents && !step.isAutoField &&
    (!step.modelHasAutoField || !step.partInPrevToFields)

/-- Process one lookup component, updating the walk state. Once halted the state
is unchanged. Otherwise the reached component becomes `lastPart`; if it does not
resolve the walk halts; if the previous field is `none` OR the previous field is
a relation whose continuation does not fold into the local model, the component
joins the relation parts; if the field does not continue the walk it halts,
otherwise the field's relational status is carried forward. -/
def stepFold (s : LoopState) (step : PathStep) : LoopState :=
  if s.stopped then s
  else
    let s := { s with lastPart := step.part }
    if !step.exists_ then { s with stopped := true }
    else
      let appendIt : Bool :=
        match s.prev with
        | none => true
        | some pr => pr && continuesLocal step
      let s := if appendIt then { s with relationParts := s.relationParts ++ [step.part] } else s
      if !step.hasPathInfos then { s with stopped := true }
      else { s with prev := some step.isRelation }

/-- Walk the whole chain from the initial state. -/
def runLoop (steps : List PathStep) : LoopState :=
  steps.foldl stepFold { relationParts := [], prev := none, lastPart := 0, stopped := false }

/-- The full decision. `fkeyAllowed` is the early foreign-key raw-id-popup
allowance; `validLookups` is the set of declared allowed filter chains. A chain
is permitted when the early allowance fires, when it resolves to at most one
relation part, or when the accumulated relation parts — with or without the
final trailing component — match a declared allowed filter. -/
def lookupDecision (steps : List PathStep) (validLookups : List (List Nat))
    (fkeyAllowed : Bool) : Bool :=
  if fkeyAllowed then true
  else
    let st := runLoop steps
    if st.relationParts.length ≤ 1 then true
    else (validLookups.contains st.relationParts) ||
         (validLookups.contains (st.relationParts ++ [st.lastPart]))
-- pure-end

-- post-conditions-start
/-- The decision is exactly the value produced by walking the chain and matching
the accumulated relation parts against the declared allowed filters. -/
def problem_spec_lookupAllowed
    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool)
    (result : Bool) : Prop :=
  result = lookupDecision steps validLookups fkeyAllowed
-- post-conditions-end

-- impl-start
def implementation_lookupAllowed
    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool) : Bool :=
  Id.run do
    if fkeyAllowed then
      return true
    let mut relationParts : List Nat := []
    let mut prev : Option Bool := none
    let mut lastPart : Nat := 0
    let mut stopped : Bool := false
    for step in steps do
      if !stopped then
        lastPart := step.part
        if !step.exists_ then
          stopped := true
        else
          let appendIt : Bool :=
            match prev with
            | none => true
            | some pr =>
                pr && !step.inParents && !step.isAutoField &&
                  (!step.modelHasAutoField || !step.partInPrevToFields)
          if appendIt then
            relationParts := relationParts ++ [step.part]
          if !step.hasPathInfos then
            stopped := true
          else
            prev := some step.isRelation
    if relationParts.length ≤ 1 then
      return true
    return (validLookups.contains relationParts) ||
           (validLookups.contains (relationParts ++ [lastPart]))
-- impl-end

-- proof-start
-- @decl:phi_stateProj-start
/-- Projection from the spec's record state to the impl's anonymous 4-tuple
accumulator. Component order matches the do-elaborator's packing of the four
`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
  (s.relationParts, s.prev, s.lastPart, s.stopped)
-- @decl:phi_stateProj-end

-- @decl:loopBody_tuple-start
/-- The tuple-threading form of one loop iteration, read directly off
`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
destructured into its four components. This is what the impl's `forIn` reduces
to under `Id`. -/
def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
    List Nat × Option Bool × Nat × Bool :=
  let relationParts := acc.1
  let prev := acc.2.1
  let stopped := acc.2.2.2
  if stopped then acc
  else
    let lastPart := step.part
    if !step.exists_ then (relationParts, prev, lastPart, true)
    else
      let appendIt : Bool :=
        match prev with
        | none => true
        | some pr =>
            pr && !step.inParents && !step.isAutoField &&
              (!step.modelHasAutoField || !step.partInPrevToFields)
      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
      else (relationParts, some step.isRelation, lastPart, false)
-- @decl:loopBody_tuple-end

-- @ns:forIn_to_foldl-start
-- @decl:forIn_to_foldl-start
/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
tuple init. -/
theorem forIn_to_foldl (steps : List PathStep) :
    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
      = steps.foldl loopBody_tuple ([], none, 0, false) := by
  simp only [Id.run, List.forIn_yield_eq_foldl]
-- @decl:forIn_to_foldl-end
-- @ns:forIn_to_foldl-end

-- @ns:step_correspondence-start
-- @decl:step_correspondence-start
/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
result equals applying the tuple loop body to the projected state. -/
theorem step_correspondence (s : LoopState) (step : PathStep) :
    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
  cases s with
  | mk relationParts prev lastPart stopped =>
    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
    repeat' (first | rfl | simp_all | split)
-- @decl:step_correspondence-end
-- @ns:step_correspondence-end

-- @ns:runLoop_proj_eq-start
-- @decl:runLoop_proj_eq-start
/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
tuple foldl from the tuple init. -/
theorem runLoop_proj_eq (steps : List PathStep) :
    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
  unfold runLoop
  have key : ∀ (l : List PathStep) (s : LoopState),
      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
    intro l
    induction l with
    | nil => intro s; rfl
    | cons a t ih =>
      intro s
      simp only [List.foldl_cons]
      rw [ih (stepFold s a), step_correspondence]
  exact key steps _
-- @decl:runLoop_proj_eq-end
-- @ns:runLoop_proj_eq-end

-- @ns:impl_loopBridge-start
-- @decl:impl_loopBridge-start
/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
tuple accumulator, and its post-loop tail decision — equals the closed
`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
decision read off the tuple components. This isolates the monad/do-elaboration
reduction (prove by exposing the always-`yield` `forIn` and applying the
`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
    (fkeyAllowed : Bool) :
    implementation_lookupAllowed steps validLookups fkeyAllowed
      = (if fkeyAllowed then true
         else
           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
           if acc.1.length ≤ 1 then true
           else validLookups.contains acc.1 ||
                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
  unfold implementation_lookupAllowed
  split
  · rfl
  · simp only [Id.run, bind, pure]
    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
          (fun step r =>
            if (!r.snd.snd.snd) = true then
              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
              else
                if
                    (match r.snd.fst with
                      | none => true
                      | some pr =>
                        pr && !step.inParents && !step.isAutoField &&
                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
                      true then
                  if (!step.hasPathInfos) = true then
                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
                else
                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
      intro l
      induction l with
      | nil => intro lp pv rp st; rfl
      | cons a t ih =>
        intro lp pv rp st
        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
        by_cases hst : st = true
        · subst hst
          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
          exact ih lp pv rp true
        · simp only [Bool.not_eq_true] at hst
          subst hst
          simp only [Bool.not_false, if_true]
          by_cases hex : a.exists_ = true
          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
            by_cases happ :
                (match pv with
                  | none => true
                  | some pr =>
                    pr && !a.inParents && !a.isAutoField &&
                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
            · simp only [happ, if_true]
              by_cases hpath : a.hasPathInfos = true
              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
              · simp only [Bool.not_eq_true] at hpath
                simp only [hpath, Bool.not_false, if_true]
                exact ih a.part pv (rp ++ [a.part]) true
            · simp only [happ, Bool.false_eq_true, if_false]
              by_cases hpath : a.hasPathInfos = true
              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
                exact ih a.part (some a.isRelation) rp false
              · simp only [Bool.not_eq_true] at hpath
                simp only [hpath, Bool.not_false, if_true]
                exact ih a.part pv rp true
          · simp only [Bool.not_eq_true] at hex
            simp only [hex, Bool.not_false, if_true]
            exact ih a.part pv rp true
    generalize hR : (forIn steps _ _ : Id _) = R
    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
      hR.symm.trans (key steps 0 none [] false)
    rw [hkey]
-- @decl:impl_loopBridge-end
-- @ns:impl_loopBridge-end

-- @ns:tail_match-start
-- @decl:tail_match-start
/-- DecisionTail: the post-loop decision computed from the projected tuple
components equals the decision computed from the record's fields. -/
theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
    (if (phi_stateProj st).1.length ≤ 1 then true
     else validLookups.contains (phi_stateProj st).1 ||
          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
      = (if st.relationParts.length ≤ 1 then true
         else validLookups.contains st.relationParts ||
              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
-- @decl:tail_match-end
-- @ns:tail_match-end


theorem correct_lookupAllowed :
    ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
      problem_spec_lookupAllowed steps validLookups fkeyAllowed
        (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
  intro steps validLookups fkeyAllowed
  unfold problem_spec_lookupAllowed
  rw [impl_loopBridge]
  by_cases h : fkeyAllowed
  · simp [h, lookupDecision]
  · simp only [h, if_false]
    rw [← runLoop_proj_eq]
    unfold lookupDecision
    simp only [h, if_false]
    exact tail_match validLookups (runLoop steps)
-- proof-end
