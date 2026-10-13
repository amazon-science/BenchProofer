import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure decision over the resolved output-type tags of two operands, the
   joining connector, and whether the backend exposes a native interval type.
   The downstream renderers reached on each branch (the generic combine, the
   interval renderer, the point-in-time-difference renderer) are a shared
   continuation reached once a renderer is chosen, so nothing about them is
   assumed: no consumed axiom, no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- The resolved output-type tag an operand can carry. The four temporal/interval
   tags are distinguished; every other concrete tag collapses to `otherType`
   (only these four ever participate in the selection below). An operand whose
   output type cannot be resolved is carried as `none` on the surrounding
   `Option`. -/
inductive FieldTag where
  | dateTag
  | dateTimeTag
  | timeTag
  | durationTag
  | otherType
  deriving DecidableEq, Inhabited

/- The binary connector joining the two operands. Only the difference connector
   participates in the point-in-time-difference branch; every other connector is
   indistinguishable for this selection, so they all collapse to `plus`. -/
inductive Connector where
  | plus
  | minus
  deriving DecidableEq, Inhabited

/- Which renderer is selected for a binary arithmetic node. `combined` is the
   generic renderer; the other two are the specialised interval renderer and the
   point-in-time-difference renderer. -/
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

/- The interval-mix predicate: the operands MIX an interval-typed operand with a
   differently-typed one — at least one operand carries the interval tag AND the
   two tags differ. The key consequence is that two interval-typed operands do
   NOT mix (their tags are equal), so a sum/difference of two intervals is left
   to the generic renderer, not the interval renderer. -/
def isIntervalMix (lt rt : Option FieldTag) : Prop :=
  (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) ∧ lt ≠ rt

instance (lt rt : Option FieldTag) : Decidable (isIntervalMix lt rt) := by
  unfold isIntervalMix; infer_instance

/- The renderer selected for a generic binary arithmetic node, from the backend
   capability, the connector, and the two operand type tags.

   * When the backend has no native interval type AND the operands mix an
     interval with a non-interval operand, the interval renderer is selected.
     Two interval-typed operands do NOT mix, so they fall through to the generic
     renderer rather than the interval renderer.
   * Otherwise, when the connector is a difference of two equal point-in-time
     types, the point-in-time-difference renderer is selected.
   * Otherwise the generic renderer is selected.

   `native = true` (a backend with a native interval type) disables the first
   branch entirely. This is the deep model of the selection (refinement.md §A;
   mapping.md §2/§3). -/
def dispatchNode (native : Bool) (conn : Connector)
    (lt rt : Option FieldTag) : NodeKind :=
  if native = false ∧ isIntervalMix lt rt then NodeKind.durationNode
  else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then NodeKind.temporalNode
  else NodeKind.combined
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the renderer for a generic binary arithmetic node. All four inputs are
   read-only and unchanged by the selection (none is `mut`): `native` reports the
   backend's native-interval capability; `conn` is the connector; `lt`/`rt` are
   the resolved output-type tags of the left and right operands (`none` when an
   operand has no resolvable output type).

   Desired behaviour: the interval renderer is chosen only when the backend lacks
   a native interval type and the operands MIX an interval-typed operand with a
   differently-typed operand — so two interval-typed operands are summed by the
   generic renderer; the point-in-time-difference renderer is chosen for a
   difference of two equal point-in-time types; otherwise the generic renderer is
   chosen. The selected renderer is the one that finally produces the node's SQL,
   so it fully determines the rendering. -/
method selectRenderer (native : Bool) (conn : Connector)
    (lt : Option FieldTag) (rt : Option FieldTag) return (out : NodeKind)
  ensures out = dispatchNode native conn lt rt
  do
    -- impl-start
    let mut out := NodeKind.combined
    if native = false ∧ isIntervalMix lt rt then
      out := NodeKind.durationNode
    else
      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
        out := NodeKind.temporalNode
      else
        out := NodeKind.combined
    return out
    -- impl-end

prove_correct selectRenderer by
  loom_solve <;> simp only [dispatchNode] <;> split_ifs <;> simp_all
