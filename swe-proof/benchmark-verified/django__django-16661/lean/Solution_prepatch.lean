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
            | some pr => pr && !step.inTargetFields
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
theorem correct_lookupAllowed :
    ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
      problem_spec_lookupAllowed steps validLookups fkeyAllowed
        (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
  sorry
-- proof-end
