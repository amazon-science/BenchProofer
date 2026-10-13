# P2 adversarial audit — django__django-13121

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl produced a closing clean-axiom proof, so no faithful patch was owed a resolve run.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,13 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
   if nativeDurationSupport = false ∧
-      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
+      (isDurationField lhs = true ∨ isDurationField rhs = true) then
     return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
   if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
     return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
   return ExprStrategy.genericArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +118,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,13 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
   if nativeDurationSupport = false ∧
-      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
+      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs = rhs then
     return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
   if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
     return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
   return ExprStrategy.genericArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +118,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,13 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
   if nativeDurationSupport = false ∧
       (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
     return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
-  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
+  if isDateTimeField lhs = true ∧ lhs = rhs then
     return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
   return ExprStrategy.genericArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +118,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,13 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
   if nativeDurationSupport = false ∧
       (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
-    return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
+    return ExprStrategy.genericArithmetic
   if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
     return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
-  return ExprStrategy.genericArithmetic
+  return ExprStrategy.durationArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +118,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,8 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
-  if nativeDurationSupport = false ∧
-      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
-    return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
-  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
-    return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
   return ExprStrategy.genericArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +113,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,13 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
   if nativeDurationSupport = false ∧
       (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
     return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
-  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
+  if isSubtraction = true ∧ isDateTimeField rhs = true ∧ lhs = rhs then
     return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
   return ExprStrategy.genericArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +118,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,19 +103,12 @@
 def implementation_expressionSqlStrategy
     (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType) :
     ExprStrategy := Id.run do
-  -- A duration mixed with a value of a different type, on a backend without
-  -- native duration support, uses the duration-arithmetic strategy.
-  if nativeDurationSupport = false ∧
-      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
+  if (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
     return ExprStrategy.durationArithmetic
-  -- Subtracting one date/time value from another of the same type yields a
-  -- duration via the date-subtraction strategy.
   if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
     return ExprStrategy.dateSubtraction
-  -- Everything else uses the ordinary arithmetic strategy.
   return ExprStrategy.genericArithmetic
 -- impl-end
-
 -- proof-start
 theorem correct_expressionSqlStrategy :
     ∀ (nativeDurationSupport isSubtraction : Bool) (lhs rhs : Option FieldType),
@@ -124,8 +117,11 @@
   intro nativeDurationSupport isSubtraction lhs rhs
   unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
   simp only [Id.run]
-  split_ifs with h1 h2
-  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
-  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+  split_ifs with h1 h2 <;>
+    first
+      | exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
+      | exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩
+      | (refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all)
+      | (constructor <;> intros <;> simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

same_spec check (swebench_unified.markers.same_spec, lean backend) = True for all 7 attacks (axioms/pure/pre/post byte-identical; only impl region edited). PC pc.lean is byte-identical to gold Solution.lean (diff = IDENTICAL).

COMMANDS: for each file X.lean: `bash scripts/lean_verify.sh X.lean` (run concurrently in ≤4 background batches).

### RESULTS (exit codes):
- pc.lean (=gold): exit 0 (verifies, no sorry; clean output; #print axioms per meta = [propext, Quot.sound]).
- atk_1 (prepatch bug: drop `lhs ≠ rhs` from branch1 — the real F2P bug, duration+duration mis-routed to durationArithmetic): exit 1, error 'unsolved goals' at postcond.
- atk_2 (boundary flip: branch1 guard uses `lhs = rhs`): exit 1, unsolved goals.
- atk_3 (control-flow: drop `isSubtraction` guard from date-sub branch): exit 1, unsolved goals.
- atk_4 (wrong output constants: branch1->generic, fallthrough->duration): exit 1, unsolved goals.
- atk_5 (ungrounded-oracle echo: always genericArithmetic): exit 1, `split_ifs failed: no if-then-else conditions to split`.
- atk_6 (side-swap: isDateTimeField rhs instead of lhs in branch2): exit 1, unsolved goals.
- atk_7 (drop `nativeDurationSupport = false` guard, fires even with native support): exit 1, unsolved goals.
All 7 failures are genuine proof errors (no sorry). No attack closed with clean axioms => no faithful patch materialized => no resolve run owed (patches={}).

WHY UNBREAKABLE: problem_spec_expressionSqlStrategy is a TOTAL biconditional over three mutually-exclusive & exhaustive decidable conditions (durationCond / ¬durationCond∧dateSubCond / ¬durationCond∧¬dateSubCond), uniquely pinning the ExprStrategy result on every one of the 6×6×2×2=144 inputs. Any verifying impl is therefore extensionally identical to gold; no distinct same-spec impl can close. verify ⇒ correct holds.

A-LEG / refinement.md AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[]. All 3 refinement legs tagged R (type-refinement), zero A-consumed / A-reference / kind-3 legs. Legitimate: the modeled CombinedExpression.as_sql strategy head consumes only plain data (two booleans + a faithful 5-way FieldType quotient of get_internal_type() strings) and observes the three downstream strategies (DurationExpression.as_sql / TemporalSubtraction.as_sql / generic combine_expression) SOLELY as the identity of which strategy is selected — no callee contract consumed, no opaque deep-model. No A-legs exist to falsify. Model↔patch correspondence holds: injective duration/date/time-kind quotient + exhaustive 144-pt finite domain (per G-PANEL-2), None(FieldError) excluded from both membership tests in spec and real. Correspondence audited and sound.

prepatch_reproduced=true: atk_1 IS the prepatch bug and fails to verify (matches Solution_prepatch.lean / G-DIFF).

VERDICT: SOUND — ≥5 (7) distinct same-spec wrong impls run through lean_verify.sh, none closes; PC verifies clean; A-legs (none) and R/I legs consistent; no verify⇏correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl produced a closing clean-axiom proof, so no faithful patch was owed a resolve run.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

same_spec check (swebench_unified.markers.same_spec, lean backend) = True for all 7 attacks (axioms/pure/pre/post byte-identical; only impl region edited). PC pc.lean is byte-identical to gold Solution.lean (diff = IDENTICAL).

COMMANDS: for each file X.lean: `bash scripts/lean_verify.sh X.lean` (run concurrently in ≤4 background batches).

### RESULTS (exit codes):
- pc.lean (=gold): exit 0 (verifies, no sorry; clean output; #print axioms per meta = [propext, Quot.sound]).
- atk_1 (prepatch bug: drop `lhs ≠ rhs` from branch1 — the real F2P bug, duration+duration mis-routed to durationArithmetic): exit 1, error 'unsolved goals' at postcond.
- atk_2 (boundary flip: branch1 guard uses `lhs = rhs`): exit 1, unsolved goals.
- atk_3 (control-flow: drop `isSubtraction` guard from date-sub branch): exit 1, unsolved goals.
- atk_4 (wrong output constants: branch1->generic, fallthrough->duration): exit 1, unsolved goals.
- atk_5 (ungrounded-oracle echo: always genericArithmetic): exit 1, `split_ifs failed: no if-then-else conditions to split`.
- atk_6 (side-swap: isDateTimeField rhs instead of lhs in branch2): exit 1, unsolved goals.
- atk_7 (drop `nativeDurationSupport = false` guard, fires even with native support): exit 1, unsolved goals.
All 7 failures are genuine proof errors (no sorry). No attack closed with clean axioms => no faithful patch materialized => no resolve run owed (patches={}).

WHY UNBREAKABLE: problem_spec_expressionSqlStrategy is a TOTAL biconditional over three mutually-exclusive & exhaustive decidable conditions (durationCond / ¬durationCond∧dateSubCond / ¬durationCond∧¬dateSubCond), uniquely pinning the ExprStrategy result on every one of the 6×6×2×2=144 inputs. Any verifying impl is therefore extensionally identical to gold; no distinct same-spec impl can close. verify ⇒ correct holds.

A-LEG / refinement.md AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[]. All 3 refinement legs tagged R (type-refinement), zero A-consumed / A-reference / kind-3 legs. Legitimate: the modeled CombinedExpression.as_sql strategy head consumes only plain data (two booleans + a faithful 5-way FieldType quotient of get_internal_type() strings) and observes the three downstream strategies (DurationExpression.as_sql / TemporalSubtraction.as_sql / generic combine_expression) SOLELY as the identity of which strategy is selected — no callee contract consumed, no opaque deep-model. No A-legs exist to falsify. Model↔patch correspondence holds: injective duration/date/time-kind quotient + exhaustive 144-pt finite domain (per G-PANEL-2), None(FieldError) excluded from both membership tests in spec and real. Correspondence audited and sound.

prepatch_reproduced=true: atk_1 IS the prepatch bug and fails to verify (matches Solution_prepatch.lean / G-DIFF).

VERDICT: SOUND — ≥5 (7) distinct same-spec wrong impls run through lean_verify.sh, none closes; PC verifies clean; A-legs (none) and R/I legs consistent; no verify⇏correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: CombinedExpression.as_sql strategy-selection head (django/db/models/expressions.py), post-patch. Verified by applying patch.diff to base worktree (ec5aa2161d) — code matches mapping.md/refinement.md exactly. Mechanical checks: Solution.lean compiles clean (lean_verify.sh exit 0); #print axioms = [propext, Quot.sound], NO sorryAx (proof genuine); same_spec(Solution,Solution_prepatch,lean)=True so spec region is byte-identical (proper G-DIFF). Faithfulness: spec's 3 clauses are exactly equivalent to the real callee under the string→FieldType quotient. (1) Duration branch: `not native ∧ 'DurationField'∈{lhs,rhs} ∧ lhs≠rhs` — quotient collapse of two non-special strings to `other` cannot create divergence because the branch requires ≥1 operand to be DurationField; any collapse-affected equality would require both sides DurationField (equal in Python too). (2) Date-sub branch: `SUB ∧ lhs∈datetime ∧ lhs=rhs` — lhs restricted to 3 date/time kinds mapping to distinct ctors, no collapse; dropped rhs_output truthiness guard preserved via isDateTimeField none=false. (3) Branches are mutually exclusive (lhs≠rhs vs lhs=rhs) so ordering is immaterial; generic fall-through faithful by complement. No diverging input exists. The spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean with impl AND proof regions elided to placeholders) was rendered via markers.spec_view and inspected line-by-line; leakage.screen(lean) also passes lexically (hard_failures=[]).

The spec view contains only: (a) the Mathlib import, (b) an abstract docstring describing a 3-way SQL-generation strategy selection, (c) the pure FieldType/ExprStrategy enums + isDurationField/isDateTimeField helpers, and (d) the problem_spec post-condition. Nothing in it names a Django file/function (no expressions.py, CombinedExpression.as_sql, DurationExpression, TemporalSubtraction, DurationValue, convert_durationfield_value), quotes any Python from the gold patch, or uses problem-statement phrasing (no 'SQLite/MySQL', 'timedelta', 'decimal.InvalidOperation', 'F(estimated_time)', 'crash', 'bug', 'fix', 'previously'). The Python↔Lean localization lives only in mapping.md/refinement.md, which are NOT part of the spec view.

The gold edit is the new `lhs_type != rhs_type` guard that routes a same-type duration+duration expression to the generic strategy instead of the duration strategy. The spec's post-condition does state the corrected discriminator ('two operands that share the duration type do NOT take this [duration] strategy'). But (1) a spec necessarily encodes post-patch/correct behavior — that is its function, not a leak; and (2) the discriminating case it pins (same-type duration → generic) is EXACTLY the failure scenario already made public in the problem_statement ('durations-only expressions doesn't work on SQLite and MySQL', F('estimated_time') + timedelta crashing in convert_durationfield_value). Combining the publicly-known broken case with the spec's statement of correct behavior does not disclose the edit's location, mechanism, or code beyond the public problem_statement. The abstract enum model would not let a reader reconstruct the concrete gold diff (the guard line, the DurationValue removal, the date_interval_sql cleanup) without the withheld mapping docs.

Verdict: faithful forward spec, no gold reconstruction beyond problem_statement. Not relaxed (no RELAXED_LEAKAGE.md needed).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
