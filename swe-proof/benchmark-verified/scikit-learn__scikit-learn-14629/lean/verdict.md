# P2 adversarial audit — scikit-learn__scikit-learn-14629

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a pinned total equality result = some (subModels.map (·.classLabels)); it fixes the output exactly for every input. No wrong impl can satisfy it, so no verifying-yet-nonresolving counterexample exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,16 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  none
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,16 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  some ((subModels.map (·.classLabels)).reverse)
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,16 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  some ((subModels.map (·.classLabels)).dropLast)
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,16 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  some ((subModels.map (·.classLabels)).tail)
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,18 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  match subModels with
+  | [] => none
+  | _  => some (subModels.map (·.classLabels))
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,35 +52,15 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  some (subModels.map (·.classLabels))
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
-  unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,16 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  some (subModels.map (fun m => m.classLabels.eraseDups))
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,35 +52,16 @@
 
 -- impl-start
 def implementation_collectClasses
-    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
-  let mut acc : List (List Int) := []
-  for m in subModels do
-    acc := acc ++ [m.classLabels]
-  return some acc
+    (subModels : List SubModel) : Option (List (List Int)) :=
+  some (subModels.map (fun m => m.classLabels ++ m.classLabels))
 -- impl-end
 
 -- proof-start
-private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
-    Id.run (forIn xs init (fun m r => do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [m.classLabels])))) =
-      init ++ xs.map (·.classLabels) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_collectClasses :
     ∀ (subModels : List SubModel),
       problem_spec_collectClasses subModels
         (implementation_collectClasses subModels) := by
   intro subModels
   unfold problem_spec_collectClasses implementation_collectClasses
-  have key := collectClasses_forIn_eq subModels []
-  simp only [Id.run, bind, pure] at key ⊢
-  rw [key]
-  simp
+  simp_all [Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Exposing, per target, the class labels recognised by a multi-target model.

A multi-target classification model works by fitting one independent sub-model
per target column. Each fitted sub-model records the set of distinct class
labels it observed for its own target.

After the whole model has been fitted, it should expose — as a first-class,
queryable attribute — the per-target class labels: a list with one entry per
target, in target order, where the entry for a target is exactly the class
labels recorded by that target's sub-model.

The result is carried in `Option` to record whether this per-target view is
defined: a defined view is `some xss`; an undefined view (the attribute is
absent, so querying it is an error) is `none`. For a fitted multi-target model
the view is always defined and is the target-ordered collection of each
sub-model's class labels.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Fitting the
-- per-target sub-models is performed by the shared multi-target fitting routine;
-- its result — the ordered list of fitted sub-models, each carrying the class
-- labels it recorded — enters here as input data. The behavior modeled is the
-- collection of those per-sub-model class labels into a per-target view, which
-- reads only that input list, so there is no `opaque`/`axiom` callee contract to
-- declare.
-- axioms-end

-- pure-start
/-- One fitted sub-model, observed only through the class labels it recorded for
its target. Other attributes of a sub-model are irrelevant to the per-target
class-label view and are not modeled. -/
structure SubModel where
  /-- the distinct class labels this sub-model recorded for its target -/
  classLabels : List Int
deriving Repr
-- pure-end

-- post-conditions-start
/-- The per-target class-label view is defined and equals, in target order, the
class labels recorded by each sub-model (directive 5 frame: the entire result is
pinned to the input list of sub-models — length equals the number of sub-models
and entry `i` is sub-model `i`'s class labels; nothing is left free). -/
def problem_spec_collectClasses
    (subModels : List SubModel) (result : Option (List (List Int))) : Prop :=
  result = some (subModels.map (·.classLabels))
-- post-conditions-end

-- impl-start
def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels do
    acc := acc ++ [m.classLabels]
  return some acc
-- impl-end

-- proof-start
private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
    Id.run (forIn xs init (fun m r => do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ [m.classLabels])))) =
      init ++ xs.map (·.classLabels) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp

theorem correct_collectClasses :
    ∀ (subModels : List SubModel),
      problem_spec_collectClasses subModels
        (implementation_collectClasses subModels) := by
  intro subModels
  unfold problem_spec_collectClasses implementation_collectClasses
  have key := collectClasses_forIn_eq subModels []
  simp only [Id.run, bind, pure] at key ⊢
  rw [key]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: scikit-learn__scikit-learn-14629 (lean).

SPEC (byte-identical across all attacks; same_spec=True for atk_1..8): problem_spec_collectClasses subModels result := result = some (subModels.map (·.classLabels)). This is a total pinned equality — output uniquely determined for every input.

ATTACKS (built by copying Solution.lean, editing ONLY impl+proof regions; axioms/pure/pre/post untouched). same_spec verified True for all 8. Verify cmd: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently, 4-at-a-time). Results:
- atk_1 (prepatch bug: none): EXIT 1 — proof cannot close (goal reduces to ⊢ False). Prepatch reproduced.
- atk_2 (control-flow: .reverse): EXIT 1.
- atk_3 (boundary: .dropLast): EXIT 1.
- atk_4 (boundary: .tail): EXIT 1.
- atk_5 (partial-domain: none on []): EXIT 1.
- atk_6 (ungrounded-oracle echo: some (subModels.map (·.classLabels))): EXIT 0 — CLOSES. #print axioms correct_collectClasses => 'does not depend on any axioms' (clean, no sorryAx).
- atk_7 (dedup: eraseDups): EXIT 1.
- atk_8 (duplicate: classLabels ++ classLabels): EXIT 1.
Positive control (pos_control.lean = gold Solution.lean): EXIT 0; #print axioms => [propext, Quot.sound] (clean).

RESOLVE (protocol step 2 — every closing clean-axiom impl's faithful patch run through official harness): atk_6 is the only closing wrong impl. Its faithful refined patch is behaviorally identical to gold (self.classes_ = [estimator.classes_ for estimator in self.estimators_]). run_resolve('scikit-learn__scikit-learn-14629', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So the one verifying impl also resolves — no verify⇏correct.

REFINEMENT.MD AUDIT: 3 legs, all tagged R; NO A-consumed, NO A-reference, NO kind-3. Honest: super().fit (MultiOutputEstimator.fit) is an unchanged callee whose estimators_ result enters as input data (subModels) — not an axiom contract — so no A-leg correspondence is required and none is claimed; the [e.classes_ for e in estimators_] comprehension is modeled deeply as List.map. No inexpressible changed op is hidden. axioms=[], deep_model_references=[], conf_skip=false consistent with impl being all-R.

CONCLUSION: Because the post-condition is an exact equality to a fully-determined value, any impl whose correct proof closes returns exactly some (subModels.map (·.classLabels)) = gold behavior, hence its refined patch resolves. The only closing wrong-impl was the gold echo (atk_6), which resolved. >=5 distinct wrong impls attempted (prepatch, control-flow, 2x boundary, partial-domain, dedup, duplicate, echo); none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a pinned total equality result = some (subModels.map (·.classLabels)); it fixes the output exactly for every input. No wrong impl can satisfy it, so no verifying-yet-nonresolving counterexample exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Exposing, per target, the class labels recognised by a multi-target model.

A multi-target classification model works by fitting one independent sub-model
per target column. Each fitted sub-model records the set of distinct class
labels it observed for its own target.

After the whole model has been fitted, it should expose — as a first-class,
queryable attribute — the per-target class labels: a list with one entry per
target, in target order, where the entry for a target is exactly the class
labels recorded by that target's sub-model.

The result is carried in `Option` to record whether this per-target view is
defined: a defined view is `some xss`; an undefined view (the attribute is
absent, so querying it is an error) is `none`. For a fitted multi-target model
the view is always defined and is the target-ordered collection of each
sub-model's class labels.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Fitting the
-- per-target sub-models is performed by the shared multi-target fitting routine;
-- its result — the ordered list of fitted sub-models, each carrying the class
-- labels it recorded — enters here as input data. The behavior modeled is the
-- collection of those per-sub-model class labels into a per-target view, which
-- reads only that input list, so there is no `opaque`/`axiom` callee contract to
-- declare.
-- axioms-end

-- pure-start
/-- One fitted sub-model, observed only through the class labels it recorded for
its target. Other attributes of a sub-model are irrelevant to the per-target
class-label view and are not modeled. -/
structure SubModel where
  /-- the distinct class labels this sub-model recorded for its target -/
  classLabels : List Int
deriving Repr
-- pure-end

-- post-conditions-start
/-- The per-target class-label view is defined and equals, in target order, the
class labels recorded by each sub-model (directive 5 frame: the entire result is
pinned to the input list of sub-models — length equals the number of sub-models
and entry `i` is sub-model `i`'s class labels; nothing is left free). -/
def problem_spec_collectClasses
    (subModels : List SubModel) (result : Option (List (List Int))) : Prop :=
  result = some (subModels.map (·.classLabels))
-- post-conditions-end

-- impl-start
def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels do
    acc := acc ++ [m.classLabels]
  return some acc
-- impl-end

-- proof-start
private theorem collectClasses_forIn_eq (xs : List SubModel) (init : List (List Int)) :
    Id.run (forIn xs init (fun m r => do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ [m.classLabels])))) =
      init ++ xs.map (·.classLabels) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp

theorem correct_collectClasses :
    ∀ (subModels : List SubModel),
      problem_spec_collectClasses subModels
        (implementation_collectClasses subModels) := by
  intro subModels
  unfold problem_spec_collectClasses implementation_collectClasses
  have key := collectClasses_forIn_eq subModels []
  simp only [Id.run, bind, pure] at key ⊢
  rw [key]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: scikit-learn__scikit-learn-14629 (lean).

SPEC (byte-identical across all attacks; same_spec=True for atk_1..8): problem_spec_collectClasses subModels result := result = some (subModels.map (·.classLabels)). This is a total pinned equality — output uniquely determined for every input.

ATTACKS (built by copying Solution.lean, editing ONLY impl+proof regions; axioms/pure/pre/post untouched). same_spec verified True for all 8. Verify cmd: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently, 4-at-a-time). Results:
- atk_1 (prepatch bug: none): EXIT 1 — proof cannot close (goal reduces to ⊢ False). Prepatch reproduced.
- atk_2 (control-flow: .reverse): EXIT 1.
- atk_3 (boundary: .dropLast): EXIT 1.
- atk_4 (boundary: .tail): EXIT 1.
- atk_5 (partial-domain: none on []): EXIT 1.
- atk_6 (ungrounded-oracle echo: some (subModels.map (·.classLabels))): EXIT 0 — CLOSES. #print axioms correct_collectClasses => 'does not depend on any axioms' (clean, no sorryAx).
- atk_7 (dedup: eraseDups): EXIT 1.
- atk_8 (duplicate: classLabels ++ classLabels): EXIT 1.
Positive control (pos_control.lean = gold Solution.lean): EXIT 0; #print axioms => [propext, Quot.sound] (clean).

RESOLVE (protocol step 2 — every closing clean-axiom impl's faithful patch run through official harness): atk_6 is the only closing wrong impl. Its faithful refined patch is behaviorally identical to gold (self.classes_ = [estimator.classes_ for estimator in self.estimators_]). run_resolve('scikit-learn__scikit-learn-14629', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So the one verifying impl also resolves — no verify⇏correct.

REFINEMENT.MD AUDIT: 3 legs, all tagged R; NO A-consumed, NO A-reference, NO kind-3. Honest: super().fit (MultiOutputEstimator.fit) is an unchanged callee whose estimators_ result enters as input data (subModels) — not an axiom contract — so no A-leg correspondence is required and none is claimed; the [e.classes_ for e in estimators_] comprehension is modeled deeply as List.map. No inexpressible changed op is hidden. axioms=[], deep_model_references=[], conf_skip=false consistent with impl being all-R.

CONCLUSION: Because the post-condition is an exact equality to a fully-determined value, any impl whose correct proof closes returns exactly some (subModels.map (·.classLabels)) = gold behavior, hence its refined patch resolves. The only closing wrong-impl was the gold echo (atk_6), which resolved. >=5 distinct wrong impls attempted (prepatch, control-flow, 2x boundary, partial-domain, dedup, duplicate, echo); none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of scikit-learn__scikit-learn-14629 lean bundle (modeled function: MultiOutputClassifier.fit post-super().fit body).

Mechanical checks:
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_collectClasses -> [propext, Quot.sound] only; NO sorryAx, so the proof is genuine.
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) -> True (spec region byte-identical between patch/prepatch).
- G-CONF conformance_check.py: shadow (transliterated R impl) vs faithful in-process oracle of the comprehension over 7 edges + 120k fuzz cases, 0 disagreements.

Spec vs real callee: The gold patch is one line: self.classes_ = [estimator.classes_ for estimator in self.estimators_]; return self. super().fit is the unchanged callee whose result (self.estimators_, ordered fitted sub-model list) enters as input data subModels (documented in mapping.md/refinement.md, correctly axioms=[], deep model). Spec: result = some (subModels.map (.classLabels)). This is an exact, order-preserving, length-preserving map -> identical to the Python comprehension on every input (empty list [] -> some [], single sub-model, empty/dup label lists all match). classes_ label arrays refined to List Int is sound because the spec only collects labels, never inspects values. Post-patch fit ALWAYS assigns classes_, so the attribute is always defined -> unconditional `some` is correct; `none` (AttributeError/undefined) is the prepatch behavior, correctly quarantined to Solution_prepatch.lean and confirmed failing by G-DIFF.

No diverging input exists. The spec is neither too strong nor drifted from real repo behavior; it is an exact structural translation of the gold-patch body. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) passes: hard_failures=[], warnings=[]. same_spec(Solution, Solution_prepatch)=True — spec region byte-identical across the patched/prepatch pair, so the impl swap (some acc vs none) is the only difference and lives outside the spec view.

Spec-view content assessed against the PUBLIC problem_statement only (not hints_text): the problem_statement already discloses the full diagnosis — the AttributeError: 'MultiOutputClassifier' object has no attribute 'classes_', and explicitly that 'To obtain the classes_ attribute of a MultiOutputClassifier, you need mo_clf.estimators_[i].classes_'. The spec view describes precisely this intended behavior abstractly: after fitting, expose the per-target class labels as a queryable attribute, being the target-ordered collection of each sub-model's class labels, with Option recording defined (some) vs absent/AttributeError (none). All of this is publicly derivable from the problem statement.

No leak of the gold EDIT beyond the public statement: no diff markers, no patched file path (sklearn/multioutput.py) or dotted module, no narration terms (bug/fix/patch/regression), and no spec-view identifier or comment echoing a patched repo symbol (fit / classes_ / estimators_). Modeled names are abstracted (SubModel.classLabels, subModels, collectClasses, problem_spec_collectClasses). The gold edit is the addition of a fit override; nothing in the spec view reveals that the fix is a new fit method — it only states the intended post-fit attribute behavior, which is public. No RELAXED_LEAKAGE.md present and none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
