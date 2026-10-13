import Mathlib
-- imports-end

/-!
Classifying an arithmetic combination of two operands when it is resolved.

A query expression may combine two operands with an arithmetic operator (one of
which here is distinguished: subtraction). When such a combination is resolved,
it is sorted into one of three KINDS, and the chosen kind is what determines the
combination's value-type for the rest of the query:

  * a DURATION combination — used when exactly one of the two operands has a
    duration value-type while the other has a different value-type (a duration
    mixed with a non-duration);
  * a TEMPORAL-SUBTRACTION combination — used when the operator is subtraction
    and both operands share the same date/datetime/time value-type;
  * an ordinary combination otherwise.

The desired behavior is that resolving a combination assigns it the correct one
of these three kinds purely from the resolved operands' value-types and the
operator, so that a combination of two temporal operands acquires a determinate
duration value-type on its own — without the caller having to state the
value-type explicitly. The classification only applies to an ordinary
combination; a combination that has already been sorted into the duration or
temporal-subtraction kind keeps that kind when resolved. A value-type that
cannot be determined for an operand counts as a distinct "unknown" type, matching
neither the duration nor the date/datetime/time families.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operations
-- the classification consults — resolving the two operands, reading each
-- resolved operand's value-type, and testing whether the combination has already
-- been sorted into a non-ordinary kind — are UNCHANGED, and their results are
-- the inputs to the modeled decision (the combination's current kind, the
-- operator, and the two operand value-types). The classification itself is
-- modeled structurally over those inputs, so no `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
/-- The kind an arithmetic combination is sorted into. `combined` is the ordinary
combination (no determinate temporal value-type on its own); `duration` and
`temporal` are the two specialized kinds, each of which carries a determinate
value-type. -/
inductive ExprKind where
  | combined
  | duration
  | temporal
deriving DecidableEq, Repr

/-- An operand's value-type, as observed when the combination is resolved. The
families that participate in the classification are the duration type and the
three date/datetime/time types; `other` is any further type; `none` (via the
`Option`) is the case where the operand's value-type cannot be determined. -/
inductive FieldType where
  | duration
  | date
  | datetime
  | time
  | other
deriving DecidableEq, Repr

/-- The arithmetic operator joining the two operands. Only the distinction
between subtraction and any other operator is observable to the classification. -/
inductive Connector where
  | sub
  | other
deriving DecidableEq, Repr

/-- Whether a value-type belongs to the date/datetime/time family. An operand
whose value-type cannot be determined (`none`) is not in the family. -/
def isDateTimeField : Option FieldType → Bool
  | some FieldType.date => true
  | some FieldType.datetime => true
  | some FieldType.time => true
  | _ => false

/-- The kind a resolved combination is sorted into, as a total function of the
combination's current kind, the operator, and the two operands' value-types.
Only an ordinary combination (`combined`) is reclassified; an already-specialized
combination keeps its kind. -/
def classifyKind (selfKind : ExprKind) (connector : Connector)
    (lhsType rhsType : Option FieldType) : ExprKind :=
  if selfKind ≠ ExprKind.combined then
    selfKind
  else if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
            ∧ lhsType ≠ rhsType then
    ExprKind.duration
  else if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
    ExprKind.temporal
  else
    ExprKind.combined
-- pure-end

-- post-conditions-start
/-- The resolved combination's kind is fully pinned by the inputs. An
already-specialized combination keeps its kind. An ordinary combination becomes a
duration combination exactly when one operand (and not the other) has the
duration value-type; it becomes a temporal-subtraction combination exactly when
the operator is subtraction and both operands share one date/datetime/time
value-type; otherwise it stays an ordinary combination. The result is fully
determined; no component is left free. -/
def problem_spec_resolveKind (selfKind : ExprKind) (connector : Connector)
    (lhsType rhsType : Option FieldType) (result : ExprKind) : Prop :=
  result = classifyKind selfKind connector lhsType rhsType
-- post-conditions-end

-- impl-start
def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
    (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
  -- Resolving a combination only ever produces a copy of the same kind: the
  -- operand value-types and operator are never consulted, so an ordinary
  -- combination of two temporal operands is left an ordinary combination and
  -- never acquires a determinate value-type on its own.
  return selfKind
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: on an ordinary combination of two operands sharing one
-- date/datetime/time value-type under subtraction, this impl returns the ordinary
-- kind, whereas the spec requires the temporal-subtraction kind.
theorem correct_resolveKind :
    ∀ (selfKind : ExprKind) (connector : Connector) (lhsType rhsType : Option FieldType),
      problem_spec_resolveKind selfKind connector lhsType rhsType
        (implementation_resolveKind selfKind connector lhsType rhsType) := by
  intro selfKind connector lhsType rhsType
  unfold problem_spec_resolveKind implementation_resolveKind classifyKind
  simp only [Id.run, bind, pure]
-- proof-end
