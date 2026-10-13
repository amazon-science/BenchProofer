import Mathlib
-- imports-end

/-!
Choosing the SQL-generation strategy for a binary arithmetic expression.

A query can build a binary arithmetic expression out of two operands joined by an
operator (addition, subtraction, …). Each operand either carries a known field
type or has no resolvable type. When the expression is turned into SQL on a
backend, one of three generation strategies is selected, based only on the two
operand field types and the operator:

  * `durationArithmetic`  — the strategy for arithmetic that mixes a duration
    value with a value of a different type (e.g. shifting a moment by a
    duration), used on backends that have no native duration support;
  * `dateSubtraction`     — the strategy for subtracting one date/time value from
    another value of the very same date/time type, yielding the elapsed amount;
  * `genericArithmetic`   — the ordinary strategy used for every other case,
    including arithmetic between two values that already share the same type.

This bundle models that strategy-selection decision.

Inputs:
  * `nativeDurationSupport` — whether the backend natively supports duration
    values (when it does, the special duration strategy is never needed);
  * `isSubtraction`         — whether the operator is subtraction;
  * `lhs`, `rhs`            — the field type of each operand, or `none` when the
    operand has no resolvable type.

The relevant field types are durations and the three date/time kinds; any other
field type is modeled as `other`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The strategy is
-- selected purely from the two operand field types, whether the operator is
-- subtraction, and whether the backend natively supports durations — all of which
-- enter as plain data. The downstream production of the SQL string by the chosen
-- strategy is observed only as WHICH strategy is selected, never by its internals,
-- so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The field type carried by an operand. The duration and the three date/time
kinds are the only types that influence the strategy decision; every other field
type collapses to `other`. -/
inductive FieldType
  | durationField
  | dateField
  | dateTimeField
  | timeField
  | other
deriving DecidableEq, BEq, Repr

/-- The SQL-generation strategy selected for the expression. -/
inductive ExprStrategy
  | durationArithmetic
  | dateSubtraction
  | genericArithmetic
deriving DecidableEq, BEq, Repr

/-- Whether an operand's type is the duration type (an operand with no resolvable
type is not a duration). -/
def isDurationField : Option FieldType → Bool
  | some FieldType.durationField => true
  | _ => false

/-- Whether an operand's type is one of the three date/time kinds. -/
def isDateTimeField : Option FieldType → Bool
  | some FieldType.dateField => true
  | some FieldType.dateTimeField => true
  | some FieldType.timeField => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- The selected strategy is fully pinned by the inputs (the decision is total —
no case leaves the result free):

  * the duration-arithmetic strategy is chosen exactly when the backend lacks
    native duration support, at least one operand is a duration, and the two
    operands do NOT have the same type (mixing a duration with a value of a
    different type); in particular two operands that share the duration type do
    NOT take this strategy;
  * otherwise, the date-subtraction strategy is chosen exactly when the operator
    is subtraction and both operands have the very same date/time type;
  * otherwise the generic arithmetic strategy is chosen. -/
def problem_spec_expressionSqlStrategy
    (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType)
    (result : ExprStrategy) : Prop :=
  let durationCond : Prop :=
    nativeDurationSupport = false ∧
    (isDurationField lhs = true ∨ isDurationField rhs = true) ∧
    lhs ≠ rhs
  let dateSubCond : Prop :=
    isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs
  (durationCond → result = ExprStrategy.durationArithmetic) ∧
  (¬ durationCond → dateSubCond → result = ExprStrategy.dateSubtraction) ∧
  (¬ durationCond → ¬ dateSubCond → result = ExprStrategy.genericArithmetic)
-- post-conditions-end

-- impl-start
def implementation_expressionSqlStrategy
    (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
    ExprStrategy := Id.run do
  -- A duration mixed with a value of a different type, on a backend without
  -- native duration support, uses the duration-arithmetic strategy.
  if nativeDurationSupport = false ∧
      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
    return ExprStrategy.durationArithmetic
  -- Subtracting one date/time value from another of the same type yields a
  -- duration via the date-subtraction strategy.
  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
    return ExprStrategy.dateSubtraction
  -- Everything else uses the ordinary arithmetic strategy.
  return ExprStrategy.genericArithmetic
-- impl-end

-- proof-start
theorem correct_expressionSqlStrategy :
    ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
      problem_spec_expressionSqlStrategy nativeDurationSupport isSubtraction lhs rhs
        (implementation_expressionSqlStrategy nativeDurationSupport isSubtraction lhs rhs) := by
  intro nativeDurationSupport isSubtraction lhs rhs
  unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
  simp only [Id.run]
  split_ifs with h1 h2
  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
-- proof-end
