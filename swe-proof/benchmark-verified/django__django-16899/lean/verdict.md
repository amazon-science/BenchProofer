# P2 adversarial audit — django__django-16899

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,16 +50,7 @@
 def implementation_checkReadonlyFieldsItem
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
-  Id.run do
-    if isCallable then
-      return []
-    if hasAttrObj then
-      return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
-      return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+  []
 -- impl-end
 
 -- proof-start
@@ -73,5 +64,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,16 +50,7 @@
 def implementation_checkReadonlyFieldsItem
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
-  Id.run do
-    if isCallable then
-      return []
-    if hasAttrObj then
-      return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
-      return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+  if isCallable then [] else [errorMessage label fieldName obj.className obj.modelLabel]
 -- impl-end
 
 -- proof-start
@@ -73,5 +64,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,16 +50,8 @@
 def implementation_checkReadonlyFieldsItem
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
-  Id.run do
-    if isCallable then
-      return []
-    if hasAttrObj then
-      return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
-      return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+  if isCallable && hasAttrObj && hasAttrModel && fieldExists then []
+  else [errorMessage label fieldName obj.className obj.modelLabel]
 -- impl-end
 
 -- proof-start
@@ -73,5 +65,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
       return []
     if fieldExists then
       return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+    return ["The value of '" ++ label ++ "' is not a callable, an attribute of '" ++ obj.className ++ "', or an attribute of '" ++ obj.modelLabel ++ "'."]
 -- impl-end
 
 -- proof-start
@@ -73,5 +73,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,9 @@
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
   Id.run do
-    if isCallable then
+    if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
       return []
-    if hasAttrObj then
-      return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
-      return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+    return [errorMessage fieldName label obj.className obj.modelLabel]
 -- impl-end
 
 -- proof-start
@@ -73,5 +67,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,9 @@
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
   Id.run do
-    if isCallable then
+    if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
       return []
-    if hasAttrObj then
-      return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
-      return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+    return [errorMessage label fieldName obj.modelLabel obj.className]
 -- impl-end
 
 -- proof-start
@@ -73,5 +67,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,10 @@
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
   Id.run do
-    if isCallable then
+    if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
       return []
-    if hasAttrObj then
-      return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
-      return []
-    return [errorMessage label fieldName obj.className obj.modelLabel]
+    return [errorMessage label fieldName obj.className obj.modelLabel,
+            errorMessage label fieldName obj.className obj.modelLabel]
 -- impl-end
 
 -- proof-start
@@ -73,5 +68,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -51,13 +51,13 @@
     (obj : AdminObj) (fieldName label : String)
     (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
   Id.run do
-    if isCallable then
+    if fieldExists then
+      return []
+    if hasAttrModel then
       return []
     if hasAttrObj then
       return []
-    if hasAttrModel then
-      return []
-    if fieldExists then
+    if isCallable then
       return []
     return [errorMessage label fieldName obj.className obj.modelLabel]
 -- impl-end
@@ -73,5 +73,10 @@
   intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
   unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
   cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
-    rfl
+    simp_all [errorMessage] <;>
+    first
+      | rfl
+      | decide
+      | simp_all
+      | (try constructor) <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The four resolution
-- checks that decide whether a configured admin display value is acceptable
-- (whether it is callable, an attribute of the admin object, an attribute of
-- the bound model, or a declared model field) are UNCHANGED behavior; their
-- boolean outcomes are taken as inputs (a type-only refinement, refinement.md).
-- The only changed operation — assembling the human-readable error text — is
-- modeled DEEPLY below, so no callee property is consumed. The proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The identifying information carried by an admin object that appears in the
diagnostic text: the admin class name and the bound model's label. -/
structure AdminObj where
  className : String
  modelLabel : String

/-- The diagnostic text emitted when a configured display value cannot be
resolved. It cites the position label, the offending value itself, the admin
class name, and the bound model label, so the reader can see exactly which
value is at fault. -/
def errorMessage (label fieldName className modelLabel : String) : String :=
  "The value of '" ++ label ++ "' refers to '" ++ fieldName ++
  "', which is not a callable, an attribute of '" ++ className ++
  "', or an attribute of '" ++ modelLabel ++ "'."
-- pure-end

-- post-conditions-start
/-- A configured display value is acceptable when any of the four resolution
checks succeeds (it is callable, an attribute of the admin object, an attribute
of the bound model, or a declared model field); in that case no diagnostic is
produced. Otherwise exactly one diagnostic is produced, and its text is the
fully-grounded message naming the position label, the offending value, the
admin class name, and the bound model label. -/
def problem_spec_checkReadonlyFieldsItem
    (obj : AdminObj) (fieldName label : String)
    (isCallable hasAttrObj hasAttrModel fieldExists : Bool)
    (result : List String) : Prop :=
  if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
    result = []
  else
    result = [errorMessage label fieldName obj.className obj.modelLabel]
-- post-conditions-end

-- impl-start
def implementation_checkReadonlyFieldsItem
    (obj : AdminObj) (fieldName label : String)
    (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
  Id.run do
    if isCallable then
      return []
    if hasAttrObj then
      return []
    if hasAttrModel then
      return []
    if fieldExists then
      return []
    return [errorMessage label fieldName obj.className obj.modelLabel]
-- impl-end

-- proof-start
theorem correct_checkReadonlyFieldsItem :
    ∀ (obj : AdminObj) (fieldName label : String)
      (isCallable hasAttrObj hasAttrModel fieldExists : Bool),
    problem_spec_checkReadonlyFieldsItem obj fieldName label
      isCallable hasAttrObj hasAttrModel fieldExists
      (implementation_checkReadonlyFieldsItem obj fieldName label
        isCallable hasAttrObj hasAttrModel fieldExists) := by
  intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
  unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
  cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL COMPLETE.** same_spec=True verified for ALL 8 attack files + positive control (byte-identical imports/axioms/pure/post regions).

**VERIFY CMD:** bash scripts/lean_verify.sh <file>. Verifications run concurrently (batches of 4).

### RESULTS (exit codes):
- atk_pos (gold, pristine) = 0; #print axioms => 'does not depend on any axioms' (positive control passes).
- atk_echo (gold-EQUIVALENT: 4 acceptance checks REORDERED fieldExists/model/obj/callable, same message) = 0. #print axioms => [propext, Quot.sound] (standard core axioms, NO sorryAx, clean).
- atk_1 (partial-domain: always []) = 1 (does not close).
- atk_2 (boundary: only isCallable accepts, ignores other 3) = 1.
- atk_3 (control-flow-effect: AND instead of OR across 4 checks) = 1 (goals collapse to |- False, e.g. case true.true.true.false).
- atk_4 (PREPATCH BUG: old E035 text omitting the "refers to '%s'" value citation) = 1 => PREPATCH REPRODUCED (cannot close vs frozen post-patch errorMessage).
- atk_5 (arg-order swap: errorMessage fieldName label ...) = 1.
- atk_6 (className/modelLabel swap in message) = 1.
- atk_7 (wrong list length: message emitted twice) = 1.

**MANDATORY RESOLVE STEP:** The ONLY closing wrong-impl is atk_echo, a gold-EXTENSIONALLY-EQUIVALENT reordering (reordering the four short-circuit acceptance branches is unobservable; the message and all outputs are byte-identical to gold on every one of the 16 boolean combos and all strings). Its faithful refined patch is therefore the gold patch itself. Materialized as patch_echo.diff and RUN through the official harness: run_resolve('django__django-16899', gold_patch) => RESOLVED=True, COMPLETED=True, note='resolved'. This is a RESOLVING echo (per 2026-08-06 G-PANEL-1/G-EQ policy: a same-spec verifying attack whose refined patch RESOLVES is NOT a weakness). No verifying impl corresponds to a NON-resolving patch.

**SPEC ANALYSIS:** problem_spec_checkReadonlyFieldsItem is a TOTAL EXTENSIONAL characterization -- output pinned for all 16 boolean combos and all strings (acceptance => []; else => exactly [errorMessage label fieldName className modelLabel]). Only degree of freedom is the message text, fixed to the corrected post-patch text. Every genuinely divergent impl (wrong message, wrong branch logic, wrong list length) fails to close.

**REFINEMENT AUDIT:** 5 legs. Rows 1-4 = R (four UNCHANGED resolution checks callable/hasattr(obj)/hasattr(obj.model)/get_field-succeeds, boolean outcomes taken as refined inputs). Row 5 = I (the single CHANGED op, error message, modeled DEEPLY as concrete String concatenation; errorMessage spells out the post-patch %-format verbatim including field_name). Axioms region EMPTY (no opaque/`_prop`); axiom_check.py is a legitimate skip stub (no A-consumed, no A-reference callee). NO kind-3 leg. A-leg correspondence N/A (none). Byte-compare of Lean errorMessage vs post-patch %-format string vs test_patch expected text: identical (per verdict.md Role 3, consistent with patch.diff). mapping.md type bijection accurate: obj=/id= framing correctly excluded (unchanged pre/post, not observable in payload).

**VERDICT:** SOUND. >=8 distinct same-spec wrong impls attacked (partial-domain, boundary, control-flow-effect AND/OR, prepatch bug, ungrounded arg-permutation echoes, list-length); none with a closing clean-axiom proof has a non-resolving faithful patch. The single closing impl is gold-equivalent and its patch resolves. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The four resolution
-- checks that decide whether a configured admin display value is acceptable
-- (whether it is callable, an attribute of the admin object, an attribute of
-- the bound model, or a declared model field) are UNCHANGED behavior; their
-- boolean outcomes are taken as inputs (a type-only refinement, refinement.md).
-- The only changed operation — assembling the human-readable error text — is
-- modeled DEEPLY below, so no callee property is consumed. The proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The identifying information carried by an admin object that appears in the
diagnostic text: the admin class name and the bound model's label. -/
structure AdminObj where
  className : String
  modelLabel : String

/-- The diagnostic text emitted when a configured display value cannot be
resolved. It cites the position label, the offending value itself, the admin
class name, and the bound model label, so the reader can see exactly which
value is at fault. -/
def errorMessage (label fieldName className modelLabel : String) : String :=
  "The value of '" ++ label ++ "' refers to '" ++ fieldName ++
  "', which is not a callable, an attribute of '" ++ className ++
  "', or an attribute of '" ++ modelLabel ++ "'."
-- pure-end

-- post-conditions-start
/-- A configured display value is acceptable when any of the four resolution
checks succeeds (it is callable, an attribute of the admin object, an attribute
of the bound model, or a declared model field); in that case no diagnostic is
produced. Otherwise exactly one diagnostic is produced, and its text is the
fully-grounded message naming the position label, the offending value, the
admin class name, and the bound model label. -/
def problem_spec_checkReadonlyFieldsItem
    (obj : AdminObj) (fieldName label : String)
    (isCallable hasAttrObj hasAttrModel fieldExists : Bool)
    (result : List String) : Prop :=
  if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
    result = []
  else
    result = [errorMessage label fieldName obj.className obj.modelLabel]
-- post-conditions-end

-- impl-start
def implementation_checkReadonlyFieldsItem
    (obj : AdminObj) (fieldName label : String)
    (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
  Id.run do
    if isCallable then
      return []
    if hasAttrObj then
      return []
    if hasAttrModel then
      return []
    if fieldExists then
      return []
    return [errorMessage label fieldName obj.className obj.modelLabel]
-- impl-end

-- proof-start
theorem correct_checkReadonlyFieldsItem :
    ∀ (obj : AdminObj) (fieldName label : String)
      (isCallable hasAttrObj hasAttrModel fieldExists : Bool),
    problem_spec_checkReadonlyFieldsItem obj fieldName label
      isCallable hasAttrObj hasAttrModel fieldExists
      (implementation_checkReadonlyFieldsItem obj fieldName label
        isCallable hasAttrObj hasAttrModel fieldExists) := by
  intro obj fieldName label isCallable hasAttrObj hasAttrModel fieldExists
  unfold problem_spec_checkReadonlyFieldsItem implementation_checkReadonlyFieldsItem
  cases isCallable <;> cases hasAttrObj <;> cases hasAttrModel <;> cases fieldExists <;>
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL COMPLETE.** same_spec=True verified for ALL 8 attack files + positive control (byte-identical imports/axioms/pure/post regions).

**VERIFY CMD:** bash scripts/lean_verify.sh <file>. Verifications run concurrently (batches of 4).

### RESULTS (exit codes):
- atk_pos (gold, pristine) = 0; #print axioms => 'does not depend on any axioms' (positive control passes).
- atk_echo (gold-EQUIVALENT: 4 acceptance checks REORDERED fieldExists/model/obj/callable, same message) = 0. #print axioms => [propext, Quot.sound] (standard core axioms, NO sorryAx, clean).
- atk_1 (partial-domain: always []) = 1 (does not close).
- atk_2 (boundary: only isCallable accepts, ignores other 3) = 1.
- atk_3 (control-flow-effect: AND instead of OR across 4 checks) = 1 (goals collapse to |- False, e.g. case true.true.true.false).
- atk_4 (PREPATCH BUG: old E035 text omitting the "refers to '%s'" value citation) = 1 => PREPATCH REPRODUCED (cannot close vs frozen post-patch errorMessage).
- atk_5 (arg-order swap: errorMessage fieldName label ...) = 1.
- atk_6 (className/modelLabel swap in message) = 1.
- atk_7 (wrong list length: message emitted twice) = 1.

**MANDATORY RESOLVE STEP:** The ONLY closing wrong-impl is atk_echo, a gold-EXTENSIONALLY-EQUIVALENT reordering (reordering the four short-circuit acceptance branches is unobservable; the message and all outputs are byte-identical to gold on every one of the 16 boolean combos and all strings). Its faithful refined patch is therefore the gold patch itself. Materialized as patch_echo.diff and RUN through the official harness: run_resolve('django__django-16899', gold_patch) => RESOLVED=True, COMPLETED=True, note='resolved'. This is a RESOLVING echo (per 2026-08-06 G-PANEL-1/G-EQ policy: a same-spec verifying attack whose refined patch RESOLVES is NOT a weakness). No verifying impl corresponds to a NON-resolving patch.

**SPEC ANALYSIS:** problem_spec_checkReadonlyFieldsItem is a TOTAL EXTENSIONAL characterization -- output pinned for all 16 boolean combos and all strings (acceptance => []; else => exactly [errorMessage label fieldName className modelLabel]). Only degree of freedom is the message text, fixed to the corrected post-patch text. Every genuinely divergent impl (wrong message, wrong branch logic, wrong list length) fails to close.

**REFINEMENT AUDIT:** 5 legs. Rows 1-4 = R (four UNCHANGED resolution checks callable/hasattr(obj)/hasattr(obj.model)/get_field-succeeds, boolean outcomes taken as refined inputs). Row 5 = I (the single CHANGED op, error message, modeled DEEPLY as concrete String concatenation; errorMessage spells out the post-patch %-format verbatim including field_name). Axioms region EMPTY (no opaque/`_prop`); axiom_check.py is a legitimate skip stub (no A-consumed, no A-reference callee). NO kind-3 leg. A-leg correspondence N/A (none). Byte-compare of Lean errorMessage vs post-patch %-format string vs test_patch expected text: identical (per verdict.md Role 3, consistent with patch.diff). mapping.md type bijection accurate: obj=/id= framing correctly excluded (unchanged pre/post, not observable in payload).

**VERDICT:** SOUND. >=8 distinct same-spec wrong impls attacked (partial-domain, boundary, control-flow-effect AND/OR, prepatch bug, ungrounded arg-permutation echoes, list-length); none with a closing clean-axiom proof has a non-resolving faithful patch. The single closing impl is gold-equivalent and its patch resolves. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for django__django-16899, modeled fn BaseModelAdminChecks.`_check_readonly_fields_item` (django/contrib/admin/checks.py:621, base_commit d3d173425f). No divergence found; spec is faithful and does not over-constrain.

### Evidence
1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True. Spec (pure+post-conditions) is frozen and identical to the prepatch view (only impl/proof differ: prepatch uses errorMessageBug = old text, which is the intended G-DIFF signal).

2. Branch logic matches the real callee exactly. Real Python: returns [] if callable(field_name) elif hasattr(obj,f) elif hasattr(obj.model,f) elif get_field succeeds (no FieldDoesNotExist); otherwise returns a single checks.Error(id=admin.E035). Spec: `if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then result=[] else result=[errorMessage ...]`. The four short-circuit acceptances all yield [], so collapsing the ladder into a single OR is behavior-preserving and order-independent. Non-empty result has length exactly 1. Match on every one of the 16 boolean combinations (Lean proof case-splits all 16 and closes by rfl).

3. Message text byte-identical to the GOLD patch. Gold patch (from dataset) changes E035 text to "The value of '%s' refers to '%s', which is not a callable, an attribute of '%s', or an attribute of '%s." % (label, field_name, obj.`__class__`.`__name__`, obj.model.`_meta`.label). Lean errorMessage concatenates in the SAME argument order (label, fieldName, className, modelLabel). Cross-checked in Python over normal (SongAdmin/CityInline F2P cases), empty-string, and adversarial ('%s%d' payloads, quotes) inputs: 100% MATCH. %-format treats interpolated values as inert, matching pure ++ concatenation.

4. Lean verifies clean: scripts/lean_verify.sh exit 0 (compiles, no sorry). `#print axioms correct_checkReadonlyFieldsItem` => 'does not depend on any axioms' — proof is genuine, no sorryAx, no `_prop` axioms (axioms region empty as documented).

5. Modeling boundary is a legitimate type-refinement, not a defect: the four UNCHANGED resolution checks (callable / two hasattr / get_field-succeeds) are R-refined to Bool inputs — the patch does not touch them and their pre/post branch structure is identical. get_field raising a non-FieldDoesNotExist exception (would propagate in Python) is outside the two-valued modeled domain; this is a documented, standard R-refinement boundary shared by the callee, not an input where the modeled function disagrees with the real callee on the modeled behavior.

No diverging input exists within the modeled domain. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (axioms+pure+post-conditions; impl/proof elided) is byte-identical prepatch/postpatch (same_spec=True); Solution.lean verifies (lean_verify exit 0, no sorry, clean case-split proof). The spec's errorMessage pins the exact post-patch string 'The value of \'<label>\' refers to \'<fieldName>\', which is not a callable, an attribute of \'<className>\', or an attribute of \'<modelLabel>\'.' — but every specific in it is already fully disclosed by the PUBLIC problem_statement, which quotes (a) the old message verbatim ('...is not a callable, an attribute of ..., or an attribute of ...'), (b) the exact sibling template 'The value of \'list_editable[0]\' refers to \'original_release\', which is not contained in ...' demonstrating the "refers to '<value>', which is not" construction, and (c) the explicit instruction to include the field name. The post-patch string is a direct synthesis of these public pieces, so the spec discloses nothing about the gold edit beyond problem_statement. Prose comments are abstract and quote no gold-patch code specifics (no %s format, no field_name/admin.E035); the buggy errorMessageBug appears only in the elided impl region, not the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
