import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only facts the modeled decision consults about a
--  non-modeled operation — "does this neighbouring operation touch my model?"
--  and "is it marked elidable?" — are UNCHANGED and are carried as FREE INPUTS
--  (`OtherOp.generic refsSelf elidable`), so the spec makes no behavioural
--  claim about them and holds for every value. Nothing requires validation
--  against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The two flavours of "together" model-option an operation may target. Only the
   flavour is ever observed (whether two such operations target the SAME flavour
   or DIFFERENT flavours of the same model). -/
inductive TogetherKind where
  | unique
  | index
  deriving DecidableEq, Inhabited, BEq

/- A neighbouring migration operation, abstracted to exactly the features the
   eligibility decision observes:
   * `together name kind` — an Alter{Unique,Index}Together operation on model
     `name` of flavour `kind` (such operations are never marked elidable);
   * `deleteModel name`   — a delete-model operation on model `name` (never
     marked elidable);
   * `generic refsSelf elidable` — any other operation, carrying only the two
     (free, unchanged) answers the decision observes: "does it touch my
     model?" and "is it marked elidable?" (an elidable neighbour is one the
     optimizer may silently drop, collapsing the pair to my operation alone —
     a merge). -/
inductive OtherOp where
  | together (name : Nat) (kind : TogetherKind)
  | deleteModel (name : Nat)
  | generic (refsSelf : Bool) (elidable : Bool)
  deriving DecidableEq, Inhabited

/- The result of asking whether one operation can be combined with / advanced
   past a neighbouring one:
   * `merge`       — the two collapse into one;
   * `reorderable` — they are independent, so the first may be advanced past the
     second while the optimizer keeps looking for a merge;
   * `blocked`     — neither; a boundary the optimizer cannot cross. -/
inductive OptimizeOutcome where
  | merge
  | reorderable
  | blocked
  deriving DecidableEq, Inhabited

/- "Does the neighbouring operation touch my model `selfName`?" For an
   Alter…Together operation this is name identity (model names compared for
   equality). A delete-model operation conservatively touches EVERY model (a
   deleted model may reference any other through its relations), so it always
   answers yes. For any other operation it is the free, unchanged answer carried
   on the operation. -/
def affectsModel (selfName : Nat) : OtherOp → Bool
  | .together name _    => name == selfName
  | .deleteModel _      => true
  | .generic refsSelf _ => refsSelf

/- Is the neighbouring operation one of the together-option operations? -/
def isTogetherOp : OtherOp → Bool
  | .together _ _ => true
  | _             => false

/- Is the neighbouring operation a together-option operation of the SAME flavour
   as mine? -/
def sameKind (selfKind : TogetherKind) : OtherOp → Bool
  | .together _ kind => kind == selfKind
  | _                => false

/- Do my operation and the neighbour collapse into one? This happens exactly
   when the neighbour is a together-option operation of MY flavour on MY model,
   a delete of MY model, or any other operation marked elidable (the optimizer
   silently drops an elidable neighbour, leaving just my operation — the pair
   becomes one). Together-option and delete-model operations are never marked
   elidable, so the elidable answer is carried only on `generic`. -/
def mergeable (selfName : Nat) (selfKind : TogetherKind) : OtherOp → Bool
  | .together name kind  => kind == selfKind && name == selfName
  | .deleteModel name    => name == selfName
  | .generic _ elidable  => elidable
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The baseline independence test shared by every model operation: an operation
   may be advanced past a neighbour exactly when that neighbour does not touch
   its model. `selfName`, `other` are read-only (directive 5). -/
method reorderableBase (selfName : Nat) (other : OtherOp) return (result : Bool)
  ensures result = (!affectsModel selfName other)
  do
    -- impl-start
    return !affectsModel selfName other
    -- impl-end

prove_correct reorderableBase by
  loom_solve

/- The independence test specialised to a together-option operation. It widens
   the baseline test: such an operation is ALSO independent of a together-option
   neighbour of a DIFFERENT flavour on the same model — the two constrain
   disjoint kinds of model option, so the optimizer may advance one past the
   other (which is what later lets a remove/re-add pair on each flavour collapse
   to a single operation). `selfName`, `selfKind`, `other` are read-only. -/
method reorderableTogether (selfName : Nat) (selfKind : TogetherKind) (other : OtherOp)
    return (result : Bool)
  ensures result = ((!affectsModel selfName other) ||
                    (isTogetherOp other && !sameKind selfKind other))
  do
    -- impl-start
    let base ← reorderableBase selfName other
    return base || (isTogetherOp other && !sameKind selfKind other)
    -- impl-end

prove_correct reorderableTogether by
  loom_solve

/- The full eligibility verdict an Alter…Together operation reaches against a
   neighbour: it merges with a same-flavour together (or a delete) on its model;
   otherwise it is reorderable iff the independence test above holds; otherwise
   it is blocked. `selfName`, `selfKind`, `other` are read-only. -/
method optimizeAgainst (selfName : Nat) (selfKind : TogetherKind) (other : OtherOp)
    return (result : OptimizeOutcome)
  ensures result = (if mergeable selfName selfKind other then OptimizeOutcome.merge
                    else (if ((!affectsModel selfName other) ||
                              (isTogetherOp other && !sameKind selfKind other))
                          then OptimizeOutcome.reorderable
                          else OptimizeOutcome.blocked))
  do
    -- impl-start
    let canReorder ← reorderableTogether selfName selfKind other
    let r := if mergeable selfName selfKind other then OptimizeOutcome.merge
             else (if canReorder then OptimizeOutcome.reorderable
                   else OptimizeOutcome.blocked)
    return r
    -- impl-end

prove_correct optimizeAgainst by
  loom_solve
