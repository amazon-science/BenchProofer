import Velvet.Std
-- imports-end

-- Total-correctness semantics: building the iterator load plan must COMPLETE
-- (the real closure body is a straight-line chain of queryset calls that
-- always terminates), so the spec must also rule out diverging
-- implementations — under partial correctness a non-terminating body would
-- vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Abstract model of the load-plan a relation iterator hands to the database
   when it is about to read related rows for serialization.

   Background (the public issue): a relation's default queryset may already
   carry a *restricted* related-object selection — i.e. it asks the database to
   follow specific named relations while fetching. Building an iterator that
   ALSO immediately loads only the primary key defers every other column. When
   a related selection is restricted to named relations AND one of those named
   relations is deferred, the database layer refuses the plan ("a field cannot
   be both deferred and traversed using a related selection at the same time").

   The desired behaviour: producing the primary-key-only iterator over a
   relation must never run into that conflict, whatever related selection the
   relation's default queryset arrived with — while still keeping the
   primary-key-only immediate-load optimisation. -/

-- axioms-start
-- (none consumed: the load-plan transformers below are modeled deeply as
--  A-reference state transformers in the `pure` region; G-AX validates each
--  against the real queryset machinery it stands for.)
-- axioms-end

-- pure-start
/- How a load plan selects related objects to follow while reading rows.
   `unrestricted` is any plan that does not name particular relations (it
   covers both "no relation-following requested" and "follow relations without
   restriction" — the two are indistinguishable here, since only a plan
   restricted to NAMED relations can collide with deferral); `restricted fs`
   names exactly the relations `fs` to follow. -/
inductive RelatedPlan where
  | unrestricted
  | restricted : List String → RelatedPlan
deriving Inhabited, Repr

/- The observable load plan of a relation iterator:
     * `related`   — how related objects are selected (above);
     * `immediate` — the immediate-load mask: `none` means "load every field
       immediately"; `some fs` means "load exactly `fs` immediately and defer
       the rest". -/
structure QState where
  related   : RelatedPlan
  immediate : Option (List String)
deriving Inhabited

/- Whether the related selection is restricted to named relations (the only
   form that can conflict with deferral). -/
@[grind] def isRestricted : RelatedPlan → Bool
  | .unrestricted  => false
  | .restricted _  => true

/- The relations a plan asks to follow (empty unless restricted to names). -/
@[grind] def requestedRelations : RelatedPlan → List String
  | .unrestricted  => []
  | .restricted fs => fs

/- Whether a given relation is deferred by the immediate-load mask: with no
   mask nothing is deferred; with a mask, a relation is deferred iff it is not
   among the immediately-loaded fields. -/
@[grind] def relationDeferred (q : QState) (f : String) : Bool :=
  match q.immediate with
  | none    => false
  | some fs => !(fs.contains f)

/- The database refuses the plan iff the related selection is restricted to
   named relations and at least one of those relations is deferred. This is the
   "deferred and traversed at the same time" conflict, as a predicate on the
   plan. -/
@[grind] def planRejected (q : QState) : Bool :=
  isRestricted q.related && (requestedRelations q.related).any (fun f => relationDeferred q f)

/- Discard any named-relation restriction on the related selection, leaving it
   unrestricted. Deep model of an unchanged queryset transformer — A-reference
   (mapping.md §3.1). -/
@[grind] def selectAllRelated (q : QState) : QState := { q with related := .unrestricted }

/- Restrict the immediate-load mask to exactly the primary key (deferring every
   other field). Deep model of an unchanged queryset transformer —
   A-reference (mapping.md §3.2). -/
@[grind] def loadOnlyPk (q : QState) : QState := { q with immediate := some ["pk"] }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the primary-key-only iterator load plan over a relation whose default
   queryset arrived as `q` (carrying any related selection at all). -/
method queryIterPlan (q : QState) return (out : QState)
  -- the resulting plan is never refused by the database, for ANY input plan
  ensures planRejected out = false
  -- any named-relation restriction the queryset arrived with must not survive
  -- (a surviving restriction is what makes deferral able to collide, and would
  -- join the named relations into the read — regressing the pk-only read the
  -- optimisation promises)
  ensures isRestricted out.related = false
  -- the primary-key-only immediate-load optimisation is preserved
  ensures out.immediate = some ["pk"]
  do
    -- impl-start
    -- Pre-image skeleton: the iterator restricts the immediate load to the
    -- primary key WITHOUT first resetting the related selection. When the
    -- incoming plan carries a restricted related selection naming a relation
    -- that the primary-key-only mask now defers, `planRejected` holds — so the
    -- `ensures planRejected out = false` clause cannot be met and prove_correct
    -- MUST fail (G-DIFF).
    let q2 := loadOnlyPk q
    return q2
    -- impl-end

prove_correct queryIterPlan by
  loom_solve
