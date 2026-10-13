import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The output-type tag a resolved operand can carry. The four temporal/interval
   tags are distinguished; every other concrete tag (and the "no resolvable
   type" outcome, carried as `none` on the `Option`) collapses to `otherType`,
   since only these four participate in the selection below. -/
inductive FieldTag where
  | dateTag
  | dateTimeTag
  | timeTag
  | durationTag
  | otherType
  deriving DecidableEq, Inhabited

/- The binary connector joining the two operands. Only the difference connector
   participates in the temporal branch; every other connector behaves the same
   for the selection. -/
inductive Connector where
  | plus
  | minus
  deriving DecidableEq, Inhabited

/- The node kind of a binary expression. `combined` is the generic node; the
   other two are the specialised interval / temporal-difference nodes. -/
inductive NodeKind where
  | combined
  | durationNode
  | temporalNode
  deriving DecidableEq, Inhabited

/- The three tags whose pairwise difference denotes a point-in-time difference. -/
def isTemporalTag (t : Option FieldTag) : Prop :=
  t = some FieldTag.dateTag ∨ t = some FieldTag.dateTimeTag ∨ t = some FieldTag.timeTag

instance (t : Option FieldTag) : Decidable (isTemporalTag t) := by
  unfold isTemporalTag; infer_instance

/- The interval-mix predicate: exactly one operand carries the interval tag (the
   two tags differ and at least one of them is the interval tag). -/
def isIntervalMix (lt rt : Option FieldTag) : Prop :=
  (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) ∧ lt ≠ rt

instance (lt rt : Option FieldTag) : Decidable (isIntervalMix lt rt) := by
  unfold isIntervalMix; infer_instance

/- The resolve-time selection of the result node kind from the operand type
   tags and the connector. A generic node is re-tagged to the interval node when
   the operands mix an interval with a non-interval type; otherwise to the
   temporal-difference node when the connector is a difference of two equal
   point-in-time types; otherwise it stays generic. A node that is already one
   of the specialised kinds keeps its kind. This is the deep model of the
   resolve-time selection (refinement.md A1; mapping.md §2/§3). -/
def dispatchKind (selfKind : NodeKind) (conn : Connector)
    (lt rt : Option FieldTag) : NodeKind :=
  if selfKind ≠ NodeKind.combined then selfKind
  else if isIntervalMix lt rt then NodeKind.durationNode
  else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then NodeKind.temporalNode
  else NodeKind.combined
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveCombined (selfKind : NodeKind) (conn : Connector) (lt : Option FieldTag) (rt : Option FieldTag) return (out : NodeKind)
  ensures out = dispatchKind selfKind conn lt rt
  do
    -- impl-start
    let mut out := selfKind
    if selfKind = NodeKind.combined then
      if isIntervalMix lt rt then
        out := NodeKind.durationNode
      else
        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
          out := NodeKind.temporalNode
        else
          out := NodeKind.combined
    return out
    -- impl-end

prove_correct resolveCombined by
  loom_solve <;> simp_all [dispatchKind]
