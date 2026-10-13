# P2 adversarial audit — django__django-13128

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,19 +106,12 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
-  if selfKind ≠ ExprKind.combined then
-    return selfKind
-  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
-        ∧ lhsType ≠ rhsType then
-    return ExprKind.duration
-  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
-    return ExprKind.temporal
-  return ExprKind.combined
+  -- BUG (prepatch): resolution always copies the same kind, never reclassifies.
+  return selfKind
 -- impl-end
 
 -- proof-start
@@ -129,4 +122,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,18 +106,16 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
   if selfKind ≠ ExprKind.combined then
     return selfKind
   if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
         ∧ lhsType ≠ rhsType then
     return ExprKind.duration
-  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
-    return ExprKind.temporal
+  -- BUG: temporal-subtraction branch dropped; never emits `temporal`.
   return ExprKind.combined
 -- impl-end
 
@@ -129,4 +127,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,15 +106,14 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
   if selfKind ≠ ExprKind.combined then
     return selfKind
-  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
-        ∧ lhsType ≠ rhsType then
+  -- BUG: dropped the `lhsType ≠ rhsType` conjunct; both-duration now -> duration.
+  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration) then
     return ExprKind.duration
   if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
     return ExprKind.temporal
@@ -129,4 +128,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,18 +106,19 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
   if selfKind ≠ ExprKind.combined then
     return selfKind
+  -- BUG: swap in `isDateTimeField rhsType` instead of lhsType in temporal case,
+  -- and check temporal before duration. Diverges on mixed datetime/duration inputs.
+  if connector = Connector.sub ∧ isDateTimeField rhsType ∧ lhsType = rhsType then
+    return ExprKind.temporal
   if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
         ∧ lhsType ≠ rhsType then
     return ExprKind.duration
-  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
-    return ExprKind.temporal
   return ExprKind.combined
 -- impl-end
 
@@ -129,4 +130,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,18 +106,11 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
-  if selfKind ≠ ExprKind.combined then
-    return selfKind
-  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
-        ∧ lhsType ≠ rhsType then
-    return ExprKind.duration
-  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
-    return ExprKind.temporal
+  -- BUG: always ordinary combination regardless of inputs.
   return ExprKind.combined
 -- impl-end
 
@@ -129,4 +122,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,17 +106,17 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
   if selfKind ≠ ExprKind.combined then
     return selfKind
   if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
         ∧ lhsType ≠ rhsType then
     return ExprKind.duration
-  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
+  -- BUG: connector polarity flipped: fires temporal on NON-subtraction.
+  if connector = Connector.other ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
     return ExprKind.temporal
   return ExprKind.combined
 -- impl-end
@@ -129,4 +129,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,12 +106,12 @@
   result = classifyKind selfKind connector lhsType rhsType
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
     (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
-  -- An already-specialized combination keeps its kind (the reclassification
-  -- guard); only an ordinary combination is sorted further.
-  if selfKind ≠ ExprKind.combined then
+  -- BUG: guard inverted — reclassifies only when ALREADY specialized.
+  if selfKind = ExprKind.combined then
     return selfKind
   if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
         ∧ lhsType ≠ rhsType then
@@ -129,4 +129,9 @@
   intro selfKind connector lhsType rhsType
   unfold problem_spec_resolveKind implementation_resolveKind classifyKind
   simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (cases selfKind <;> cases connector <;> cases lhsType <;>
+        first | rfl | (rename_i a; cases a <;> rfl) | simp_all)
+    | (try cases lhsType) <;> (try cases rhsType) <;> simp_all <;> aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
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
  -- An already-specialized combination keeps its kind (the reclassification
  -- guard); only an ordinary combination is sorted further.
  if selfKind ≠ ExprKind.combined then
    return selfKind
  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
        ∧ lhsType ≠ rhsType then
    return ExprKind.duration
  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
    return ExprKind.temporal
  return ExprKind.combined
-- impl-end

-- proof-start
theorem correct_resolveKind :
    ∀ (selfKind : ExprKind) (connector : Connector) (lhsType rhsType : Option FieldType),
      problem_spec_resolveKind selfKind connector lhsType rhsType
        (implementation_resolveKind selfKind connector lhsType rhsType) := by
  intro selfKind connector lhsType rhsType
  unfold problem_spec_resolveKind implementation_resolveKind classifyKind
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-13128 / lean.

SPEC SHAPE: exact-equality postcondition `problem_spec_resolveKind ... result := result = classifyKind selfKind connector lhsType rhsType`, where `classifyKind` is a TRANSPARENT TOTAL function over FINITE DECIDABLE inductive types (ExprKind x3, Connector x2, Option FieldType x6, Option FieldType x6 = 216 inputs). NO axioms region (empty; axiom_check.py is a skip stub). The two changed dispatch branches (refinement.md legs 3,4 — the 'A-legs' of the audit focus) are modeled DEEPLY as classifyKind's duration/temporal arms (tag: I / deep-model), NOT axiomatized; the consulted callees (resolve_expression, get_internal_type, isinstance) are UNCHANGED and feed the modeled inputs.

CONSEQUENCE: any impl whose correct_resolveKind closes must be pointwise-equal to classifyKind on all 216 inputs, i.e. behaviorally identical to gold's classification. Zero slack for a closing-but-divergent impl.

### Protocol executed
- same_spec check via swebench_unified.markers.same_spec + backends.get_backend('lean'): all 7 attacks -> True (impl region only edited; axioms/pure/pre/post byte-identical).
- Verify cmd (run concurrently, <=4 at a time as bg Bash jobs): `bash scripts/lean_verify.sh <file>`.
- Each attack carried an ESCALATING closing-proof attempt (gold body then `first | rfl | (cases selfKind <;> cases connector <;> cases lhsType <;> first | rfl | (rename_i a; cases a <;> rfl) | simp_all) | (cases lhsType <;> cases rhsType <;> simp_all <;> aesop)`), so a closable wrong impl would have closed.

### Results
- positive_control.lean (= gold Solution.lean impl): exit 0; `#print axioms correct_resolveKind` -> [propext] only (clean, no sorryAx). [pc.log, pc_axioms.log]
- atk_1 prepatch bug `return selfKind`: exit 1, genuine residual `case combined.sub.none ... ExprKind.combined = if ... then ExprKind.duration ...`. (prepatch reproduced: fails on the temporal-subtraction discriminating case.)
- atk_2 partial-domain (temporal branch dropped): exit 1, unsolved goals.
- atk_3 boundary (dropped `lhsType != rhsType` conjunct on duration case): exit 1, unsolved goals.
- atk_4 control-flow-effect (temporal checked before duration + isDateTimeField rhsType instead of lhsType): exit 1, unsolved goals.
- atk_5 ungrounded-oracle echo (`return ExprKind.combined`): exit 1, unsolved goals.
- atk_6 connector-polarity flip (Connector.other instead of sub in temporal case): exit 1, unsolved goals.
- atk_7 guard inversion (reclassify only the already-specialized case): exit 1, unsolved goals.

All 7 same-spec wrong impls FAIL to verify (exit 1) with genuine false-equality residual goals (verified not tactic/parse artifacts). => NO closing-but-non-resolving impl exists; protocol step 2 (materialize+resolve patches for closing wrong impls) is vacuous — 0 patches to run, correctly, not skipped.

REFINEMENT.MD AUDIT: legs 1,2,5 = R; legs 3,4 = I (deep model of the changed dispatch decision); abstracted row = A-reference (gold hunks 1&3 as_sql relocation / native-duration short-circuit — downstream SQL-compilation effects that do not change the resolved KIND the FAIL_TO_PASS tests observe). NO kind-3 (consumed-but-unmodeled) leg. A-reference correspondence to the real callees holds. G-CONF (conformance_check.py) differential-tests the R/I shadow vs an in-process replica of the post-patch dispatch over all 216 + 120k fuzz (bundle records checked=120216, disagreements=0).

VERDICT: SOUND — >=5 (7) distinct same-spec wrong impls run, positive control verifies with clean axioms, none of the wrong impls closes, so verify=>correct holds; no BROKEN evidence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
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
  -- An already-specialized combination keeps its kind (the reclassification
  -- guard); only an ordinary combination is sorted further.
  if selfKind ≠ ExprKind.combined then
    return selfKind
  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
        ∧ lhsType ≠ rhsType then
    return ExprKind.duration
  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
    return ExprKind.temporal
  return ExprKind.combined
-- impl-end

-- proof-start
theorem correct_resolveKind :
    ∀ (selfKind : ExprKind) (connector : Connector) (lhsType rhsType : Option FieldType),
      problem_spec_resolveKind selfKind connector lhsType rhsType
        (implementation_resolveKind selfKind connector lhsType rhsType) := by
  intro selfKind connector lhsType rhsType
  unfold problem_spec_resolveKind implementation_resolveKind classifyKind
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-13128 / lean.

SPEC SHAPE: exact-equality postcondition `problem_spec_resolveKind ... result := result = classifyKind selfKind connector lhsType rhsType`, where `classifyKind` is a TRANSPARENT TOTAL function over FINITE DECIDABLE inductive types (ExprKind x3, Connector x2, Option FieldType x6, Option FieldType x6 = 216 inputs). NO axioms region (empty; axiom_check.py is a skip stub). The two changed dispatch branches (refinement.md legs 3,4 — the 'A-legs' of the audit focus) are modeled DEEPLY as classifyKind's duration/temporal arms (tag: I / deep-model), NOT axiomatized; the consulted callees (resolve_expression, get_internal_type, isinstance) are UNCHANGED and feed the modeled inputs.

CONSEQUENCE: any impl whose correct_resolveKind closes must be pointwise-equal to classifyKind on all 216 inputs, i.e. behaviorally identical to gold's classification. Zero slack for a closing-but-divergent impl.

### Protocol executed
- same_spec check via swebench_unified.markers.same_spec + backends.get_backend('lean'): all 7 attacks -> True (impl region only edited; axioms/pure/pre/post byte-identical).
- Verify cmd (run concurrently, <=4 at a time as bg Bash jobs): `bash scripts/lean_verify.sh <file>`.
- Each attack carried an ESCALATING closing-proof attempt (gold body then `first | rfl | (cases selfKind <;> cases connector <;> cases lhsType <;> first | rfl | (rename_i a; cases a <;> rfl) | simp_all) | (cases lhsType <;> cases rhsType <;> simp_all <;> aesop)`), so a closable wrong impl would have closed.

### Results
- positive_control.lean (= gold Solution.lean impl): exit 0; `#print axioms correct_resolveKind` -> [propext] only (clean, no sorryAx). [pc.log, pc_axioms.log]
- atk_1 prepatch bug `return selfKind`: exit 1, genuine residual `case combined.sub.none ... ExprKind.combined = if ... then ExprKind.duration ...`. (prepatch reproduced: fails on the temporal-subtraction discriminating case.)
- atk_2 partial-domain (temporal branch dropped): exit 1, unsolved goals.
- atk_3 boundary (dropped `lhsType != rhsType` conjunct on duration case): exit 1, unsolved goals.
- atk_4 control-flow-effect (temporal checked before duration + isDateTimeField rhsType instead of lhsType): exit 1, unsolved goals.
- atk_5 ungrounded-oracle echo (`return ExprKind.combined`): exit 1, unsolved goals.
- atk_6 connector-polarity flip (Connector.other instead of sub in temporal case): exit 1, unsolved goals.
- atk_7 guard inversion (reclassify only the already-specialized case): exit 1, unsolved goals.

All 7 same-spec wrong impls FAIL to verify (exit 1) with genuine false-equality residual goals (verified not tactic/parse artifacts). => NO closing-but-non-resolving impl exists; protocol step 2 (materialize+resolve patches for closing wrong impls) is vacuous — 0 patches to run, correctly, not skipped.

REFINEMENT.MD AUDIT: legs 1,2,5 = R; legs 3,4 = I (deep model of the changed dispatch decision); abstracted row = A-reference (gold hunks 1&3 as_sql relocation / native-duration short-circuit — downstream SQL-compilation effects that do not change the resolved KIND the FAIL_TO_PASS tests observe). NO kind-3 (consumed-but-unmodeled) leg. A-reference correspondence to the real callees holds. G-CONF (conformance_check.py) differential-tests the R/I shadow vs an in-process replica of the post-patch dispatch over all 216 + 120k fuzz (bundle records checked=120216, disagreements=0).

VERDICT: SOUND — >=5 (7) distinct same-spec wrong impls run, positive control verifies with clean axioms, none of the wrong impls closes, so verify=>correct holds; no BROKEN evidence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) audit for django__django-13128, modeled function CombinedExpression.resolve_expression classification dispatch (post-gold-patch).

METHOD: Reconstructed the real post-patch dispatch (gold patch confirmed from test.jsonl; bundle patch.diff was empty but the gold patch and refinement/mapping agree). Built a Python replica returning the resolved-expression KIND and compared it against the Lean model classifyKind over (a) ALL 216 modeled inputs (selfKind×3, connector×2, lhsType×6, rhsType×6) and (b) distinct real 'other' internal-type strings (otherA/otherB) mixed with the recognized strings and None to confirm the 'other'-collapse and none-collapse are safe. Result: 0 mismatches on every input.

BRANCH-BY-BRANCH: reclassification guard selfKind≠combined ⇔ isinstance(self,(DurationExpression,TemporalSubtraction)) guard — modeled return selfKind is faithful to the recursion re-entry (the freshly-built subclass re-enters, hits its own isinstance guard, and returns a plain copy of that same class, i.e. same kind). Duration branch: (lhsType=some duration ∨ rhsType=some duration) ∧ lhsType≠rhsType ⇔ 'DurationField' in {lhs_type,rhs_type} and lhs_type!=rhs_type (no connector predicate, matching real code). Temporal branch: connector=sub ∧ isDateTimeField lhsType ∧ lhsType=rhsType ⇔ SUB and lhs_type in {DateField,DateTimeField,TimeField} and lhs_type==rhs_type. Default ⇔ plain copy (combined). None (AttributeError/FieldError) ⇔ none: correctly not in datetime family, not equal-to-duration.

LEAN: scripts/lean_verify.sh Solution.lean exit 0 (compiles, no sorry). #print axioms correct_resolveKind => [propext] only — no sorryAx, proof is genuine.

SPEC STRENGTH: problem_spec pins result to full ExprKind equality with the total input-grounded function classifyKind — no free component, no ungrounded oracle. Not too strong (agrees with real callee everywhere) and not too weak (exact equality). No diverging input exists.

VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean) = True (verified via swebench_unified.markers with lean LanguageTables); the spec region — docstring, pure block (ExprKind/FieldType/Connector/isDateTimeField/classifyKind), and post-conditions (problem_spec_resolveKind) — is byte-identical between patched and prepatch; only impl+proof differ (patched=full classification, prepatch='return selfKind'). Public problem_statement is a terse bug report: F('end')-F('start')+Value(timedelta(),output_field=DurationField()) raises 'FieldError: Expression contains mixed types: DateTimeField, DurationField. You must set output_field.', goal 'make temporal subtraction work without ExpressionWrapper'. The spec view is more detailed than problem_statement, but that detail is the legitimate behavioral correctness contract (three-way classification of a resolved combination into duration/temporal/ordinary kinds as a total function of operand value-types + operator + current kind). It does NOT leak gold-edit specifics: (1) no mention of relocating the type-dispatch from as_sql/compile-time to resolve_expression/resolve-time (that mechanism appears only in refinement.md/mapping.md, not the spec view); (2) no gold-patch code, method/class names (DurationExpression, TemporalSubtraction, has_native_duration_field, get_internal_type) in the spec view — it uses abstract 'duration combination'/'temporal-subtraction combination' prose; (3) the classification conditions state the semantics any correct fix must produce, not the gold implementation strategy. A solver reading only the spec view learns the required behavior, not how the gold patch achieves it. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
