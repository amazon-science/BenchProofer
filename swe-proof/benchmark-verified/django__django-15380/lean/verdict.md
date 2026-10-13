# P2 adversarial audit — django__django-15380

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,8 @@
     let modelName := entry.2.1
     let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
     let priorState   := priorStates.lookup (appLabel, priorName)
-    let currentState := currentStates.lookup (appLabel, modelName)
+    -- ATTACK1 prepatch bug: current snapshot indexed by PRIOR name
+    let currentState := currentStates.lookup (appLabel, priorName)
     acc := acc ++ [(priorState, currentState)]
   return acc
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,8 +99,9 @@
     let appLabel  := entry.1
     let modelName := entry.2.1
     let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
-    let priorState   := priorStates.lookup (appLabel, priorName)
-    let currentState := currentStates.lookup (appLabel, modelName)
+    -- ATTACK2: prior/current indices swapped
+    let priorState   := priorStates.lookup (appLabel, modelName)
+    let currentState := currentStates.lookup (appLabel, priorName)
     acc := acc ++ [(priorState, currentState)]
   return acc
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     (entries : List (String × String × String)) :
     List (Option ModelState × Option ModelState) := Id.run do
   let mut acc := []
-  for entry in entries do
+  for entry in entries.tail do
     let appLabel  := entry.1
     let modelName := entry.2.1
     let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,8 @@
     let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
     let priorState   := priorStates.lookup (appLabel, priorName)
     let currentState := currentStates.lookup (appLabel, modelName)
-    acc := acc ++ [(priorState, currentState)]
+    -- ATTACK4: prepend -> reversed order
+    acc := [(priorState, currentState)] ++ acc
   return acc
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,16 +93,11 @@
     (renameMap : List (ModelKey × String))
     (priorStates currentStates : List (ModelKey × ModelState))
     (entries : List (String × String × String)) :
-    List (Option ModelState × Option ModelState) := Id.run do
-  let mut acc := []
-  for entry in entries do
+    List (Option ModelState × Option ModelState) := entries.map (fun entry =>
     let appLabel  := entry.1
     let modelName := entry.2.1
     let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
-    let priorState   := priorStates.lookup (appLabel, priorName)
-    let currentState := currentStates.lookup (appLabel, modelName)
-    acc := acc ++ [(priorState, currentState)]
-  return acc
+    (priorStates.lookup (appLabel, priorName), currentStates.lookup (appLabel, modelName)))
 -- impl-end
 
 -- proof-start
@@ -113,33 +108,6 @@
       problem_spec_resolveFieldModels renameMap priorStates currentStates entries
         (implementation_resolveFieldModels renameMap priorStates currentStates entries) := by
   intro renameMap priorStates currentStates entries
-  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels
-  simp only [Id.run]
-  have helper : ∀ (es : List (String × String × String)) (init : List (Option ModelState × Option ModelState)),
-      (forIn (m := Id) es init (fun entry r =>
-            pure (ForInStep.yield
-              (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
-                      List.lookup (entry.1, entry.2.1) currentStates)]))))
-        = init ++ es.map (resolveOne renameMap priorStates currentStates) := by
-    intro es
-    induction es with
-    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, List.map_cons]
-      rw [ih]
-      simp only [resolveOne, List.append_assoc, List.cons_append, List.nil_append]
-  have h2 : (forIn (m := Id) entries [] (fun entry r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield
-                (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
-                        List.lookup (entry.1, entry.2.1) currentStates)])))))
-        = forIn (m := Id) entries [] (fun entry r =>
-            pure (ForInStep.yield
-              (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
-                      List.lookup (entry.1, entry.2.1) currentStates)]))) := rfl
-  rw [h2, helper, List.nil_append]
+  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels resolveOne
   rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,16 +93,7 @@
     (renameMap : List (ModelKey × String))
     (priorStates currentStates : List (ModelKey × ModelState))
     (entries : List (String × String × String)) :
-    List (Option ModelState × Option ModelState) := Id.run do
-  let mut acc := []
-  for entry in entries do
-    let appLabel  := entry.1
-    let modelName := entry.2.1
-    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
-    let priorState   := priorStates.lookup (appLabel, priorName)
-    let currentState := currentStates.lookup (appLabel, modelName)
-    acc := acc ++ [(priorState, currentState)]
-  return acc
+    List (Option ModelState × Option ModelState) := entries.map (fun _ => (none, none))
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,8 +98,8 @@
   for entry in entries do
     let appLabel  := entry.1
     let modelName := entry.2.1
-    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
-    let priorState   := priorStates.lookup (appLabel, priorName)
+    -- ATTACK7: prior snapshot indexed by CURRENT name (rename map ignored)
+    let priorState   := priorStates.lookup (appLabel, modelName)
     let currentState := currentStates.lookup (appLabel, modelName)
     acc := acc ++ [(priorState, currentState)]
   return acc
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Locating the owning model states for candidate renamed fields.

A schema-change detector compares two snapshots of a set of models: a PRIOR
snapshot and a CURRENT snapshot. Models may have been renamed between the two
snapshots, recorded by a rename map sending a model's `(app label, current name)`
to the name that same model had in the prior snapshot.

When considering whether a field that is present in the current snapshot but
absent in the prior one is in fact a rename of an existing field, the detector
must locate, for each such candidate field key `(app label, model name, field
name)`, the state of the field's owning model in BOTH snapshots:

  * in the PRIOR snapshot the owning model is found under the name it had THEN —
    i.e. its current name translated back through the rename map (falling back to
    the current name when the model was not renamed);
  * in the CURRENT snapshot the owning model is found under its CURRENT name.

The key correctness point is that each snapshot is indexed by the name the model
carries IN THAT snapshot: the prior snapshot by the prior name, the current
snapshot by the current name. Using the prior name to index the current snapshot
would fail to locate a model that was renamed in this same step.

Inputs: `renameMap` (current key → prior model name), `priorStates` and
`currentStates` (each maps an `(app label, model name)` key to that model's
state in the respective snapshot), and `entries` (the candidate field keys, each
an `(app label, model name, field name)`). The result is, per entry and in the
same order, the pair of located owning-model states — `(prior, current)` — each
absent when no model is recorded under the looked-up key.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The three map indexings
-- used by this computation (the rename-map translation and the two snapshot
-- lookups) are key→value association lookups, modeled DEEPLY and concretely as
-- total `List.lookup`s over the input carriers (I-tagged in refinement.md). The
-- downstream per-field selection step lies outside the modeled behavior, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An `(app label, model name)` lookup key into a snapshot or the rename map. -/
abbrev ModelKey := String × String

/-- The state of a model within one snapshot. Only the touched surface is
modeled: the model's name and its field-name set. -/
structure ModelState where
  name : String
  fields : List String
deriving DecidableEq, Repr, Inhabited

/-- Locate the owning-model states for a single candidate field key.

`entry` is `(app label, model name, field name)`. The field name selects the
field downstream of this computation (an unchanged step, out of model scope), so
only the `(app label, model name)` pair participates here.

The model's PRIOR name is its current name translated back through the rename map
(or the current name itself when it was not renamed). The prior snapshot is
indexed by that prior name; the current snapshot is indexed by the CURRENT
name. -/
def resolveOne
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entry : String × String × String) : Option ModelState × Option ModelState :=
  let appLabel  := entry.1
  let modelName := entry.2.1
  let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
  let priorState   := priorStates.lookup (appLabel, priorName)
  let currentState := currentStates.lookup (appLabel, modelName)
  (priorState, currentState)
-- pure-end

-- post-conditions-start
/-- The result is, entry-for-entry and in order, the pair of owning-model states
located for each candidate field key: the prior-snapshot state (found under the
model's prior name) paired with the current-snapshot state (found under the
model's current name). Both result components are fully pinned to the inputs;
neither is left free. -/
def problem_spec_resolveFieldModels
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entries : List (String × String × String))
    (result : List (Option ModelState × Option ModelState)) : Prop :=
  result = entries.map (resolveOne renameMap priorStates currentStates)
-- post-conditions-end

-- impl-start
def implementation_resolveFieldModels
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entries : List (String × String × String)) :
    List (Option ModelState × Option ModelState) := Id.run do
  let mut acc := []
  for entry in entries do
    let appLabel  := entry.1
    let modelName := entry.2.1
    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
    let priorState   := priorStates.lookup (appLabel, priorName)
    let currentState := currentStates.lookup (appLabel, modelName)
    acc := acc ++ [(priorState, currentState)]
  return acc
-- impl-end

-- proof-start
theorem correct_resolveFieldModels :
    ∀ (renameMap : List (ModelKey × String))
      (priorStates currentStates : List (ModelKey × ModelState))
      (entries : List (String × String × String)),
      problem_spec_resolveFieldModels renameMap priorStates currentStates entries
        (implementation_resolveFieldModels renameMap priorStates currentStates entries) := by
  intro renameMap priorStates currentStates entries
  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels
  simp only [Id.run]
  have helper : ∀ (es : List (String × String × String)) (init : List (Option ModelState × Option ModelState)),
      (forIn (m := Id) es init (fun entry r =>
            pure (ForInStep.yield
              (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
                      List.lookup (entry.1, entry.2.1) currentStates)]))))
        = init ++ es.map (resolveOne renameMap priorStates currentStates) := by
    intro es
    induction es with
    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [bind, List.map_cons]
      rw [ih]
      simp only [resolveOne, List.append_assoc, List.cons_append, List.nil_append]
  have h2 : (forIn (m := Id) entries [] (fun entry r =>
            (do
              pure PUnit.unit
              pure (ForInStep.yield
                (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
                        List.lookup (entry.1, entry.2.1) currentStates)])))))
        = forIn (m := Id) entries [] (fun entry r =>
            pure (ForInStep.yield
              (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
                      List.lookup (entry.1, entry.2.1) currentStates)]))) := rfl
  rw [h2, helper, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact functional equation. problem_spec_resolveFieldModels pins result = entries.map (resolveOne renameMap priorStates currentStates), with resolveOne byte-frozen in the spec region (indexes currentStates by CURRENT name modelName; priorStates by prior name (renameMap.lookup key).getD modelName). Axioms region EMPTY, verified byte-identical (sha256 0f8f958b...) across all 7 attacks + gold => same_spec integrity. No A-legs to exploit. spec_view collapses BOTH impl and proof regions to placeholders, so attacks were free to rewrite impl AND proof.

SAME_SPEC: all 7 attacks return True; pos_control (identical gold copy) True.

### ATTACKS (all; cmd: bash scripts/lean_verify.sh <f>.lean):
- atk_1 PREPATCH BUG: currentStates indexed by priorName (base-commit). exit=1 (rewrite tactic failed @144 — genuine proof-closure failure, not sorry). Does NOT verify.
- atk_2 SWAP: prior<->current indices swapped. exit=1.
- atk_3 BOUNDARY: iterate entries.tail (drops first). exit=1.
- atk_4 CONTROL-FLOW: prepend instead of append (reversed order). exit=1.
- atk_5 ECHO (correct behavior via entries.map, closing rfl proof): exit=0. #print axioms correct_resolveFieldModels => 'does not depend on any axioms' (clean, no sorryAx). This is the fixed behavior, NOT a wrong impl.
- atk_6 UNGROUNDED ORACLE: entries.map (fun _ => (none,none)). exit=1 (simp made no progress @108).
- atk_7 boundary/model-ref: priorStates indexed by CURRENT name (rename map ignored for prior). exit=1.

POSITIVE CONTROL pos_control.lean (gold): exit=0; #print axioms => [propext, Quot.sound] clean.

CLOSERS => RESOLVE (protocol step 2): the ONLY closing proofs are pos_control (gold) and atk_5. atk_5 computes exactly entries.map (resolveOne ...) i.e. the fixed function, so its faithful refined patch IS the gold patch (currentStates indexed by current name). run_resolve('django__django-15380', gold_patch, timeout=1800, retries=1) => RESOLVED=True, completed=True, note='resolved'. No verified-but-non-resolving witness exists.

PREPATCH REPRODUCED: atk_1 mirrors Solution_prepatch.lean and fails to close. Independent refutation refute.lean proves implBuggy rm pr cu en != en.map (resolveOne rm pr cu) by decide (exit=0) on the renamed-model witness rm=[((app,mymodel2),mymodel)], pr=[((app,mymodel),<mymodel,[f]>)], cu=[((app,mymodel2),<mymodel2,[f2]>)], en=[(app,mymodel2,f2)] => buggy yields (some, none), spec yields (some, some). So prepatch correct_ is UNCLOSABLE.

REFINEMENT.MD AUDIT: 6 legs. Rows 1,2,6 = R (iteration/tuple-unpack/pair-accumulation type refinements); rows 3,4,5 = I (rename-map .get + two snapshot subscripts, reproduced concretely as List.lookup/.getD). NO A-consumed, NO A-reference (axioms region empty; axiom_check.py is a legitimate skip stub — the map ops are Python dict builtins reproduced concretely, not axiomatized callees; downstream get_field/rename-scan unchanged and out of scope). No kind-3 leg. A-leg correspondence vacuously holds (none present).

CONCLUSION: The postcondition is a total functional equation over an empty-axiom model; any impl that closes correct_ is forced extensionally equal to the fixed function, so it must resolve. All 6 genuinely-wrong impls fail to verify; the sole non-gold closer is a correct echo whose patch resolves. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Locating the owning model states for candidate renamed fields.

A schema-change detector compares two snapshots of a set of models: a PRIOR
snapshot and a CURRENT snapshot. Models may have been renamed between the two
snapshots, recorded by a rename map sending a model's `(app label, current name)`
to the name that same model had in the prior snapshot.

When considering whether a field that is present in the current snapshot but
absent in the prior one is in fact a rename of an existing field, the detector
must locate, for each such candidate field key `(app label, model name, field
name)`, the state of the field's owning model in BOTH snapshots:

  * in the PRIOR snapshot the owning model is found under the name it had THEN —
    i.e. its current name translated back through the rename map (falling back to
    the current name when the model was not renamed);
  * in the CURRENT snapshot the owning model is found under its CURRENT name.

The key correctness point is that each snapshot is indexed by the name the model
carries IN THAT snapshot: the prior snapshot by the prior name, the current
snapshot by the current name. Using the prior name to index the current snapshot
would fail to locate a model that was renamed in this same step.

Inputs: `renameMap` (current key → prior model name), `priorStates` and
`currentStates` (each maps an `(app label, model name)` key to that model's
state in the respective snapshot), and `entries` (the candidate field keys, each
an `(app label, model name, field name)`). The result is, per entry and in the
same order, the pair of located owning-model states — `(prior, current)` — each
absent when no model is recorded under the looked-up key.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The three map indexings
-- used by this computation (the rename-map translation and the two snapshot
-- lookups) are key→value association lookups, modeled DEEPLY and concretely as
-- total `List.lookup`s over the input carriers (I-tagged in refinement.md). The
-- downstream per-field selection step lies outside the modeled behavior, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An `(app label, model name)` lookup key into a snapshot or the rename map. -/
abbrev ModelKey := String × String

/-- The state of a model within one snapshot. Only the touched surface is
modeled: the model's name and its field-name set. -/
structure ModelState where
  name : String
  fields : List String
deriving DecidableEq, Repr, Inhabited

/-- Locate the owning-model states for a single candidate field key.

`entry` is `(app label, model name, field name)`. The field name selects the
field downstream of this computation (an unchanged step, out of model scope), so
only the `(app label, model name)` pair participates here.

The model's PRIOR name is its current name translated back through the rename map
(or the current name itself when it was not renamed). The prior snapshot is
indexed by that prior name; the current snapshot is indexed by the CURRENT
name. -/
def resolveOne
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entry : String × String × String) : Option ModelState × Option ModelState :=
  let appLabel  := entry.1
  let modelName := entry.2.1
  let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
  let priorState   := priorStates.lookup (appLabel, priorName)
  let currentState := currentStates.lookup (appLabel, modelName)
  (priorState, currentState)
-- pure-end

-- post-conditions-start
/-- The result is, entry-for-entry and in order, the pair of owning-model states
located for each candidate field key: the prior-snapshot state (found under the
model's prior name) paired with the current-snapshot state (found under the
model's current name). Both result components are fully pinned to the inputs;
neither is left free. -/
def problem_spec_resolveFieldModels
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entries : List (String × String × String))
    (result : List (Option ModelState × Option ModelState)) : Prop :=
  result = entries.map (resolveOne renameMap priorStates currentStates)
-- post-conditions-end

-- impl-start
def implementation_resolveFieldModels
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entries : List (String × String × String)) :
    List (Option ModelState × Option ModelState) := Id.run do
  let mut acc := []
  for entry in entries do
    let appLabel  := entry.1
    let modelName := entry.2.1
    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
    let priorState   := priorStates.lookup (appLabel, priorName)
    let currentState := currentStates.lookup (appLabel, modelName)
    acc := acc ++ [(priorState, currentState)]
  return acc
-- impl-end

-- proof-start
theorem correct_resolveFieldModels :
    ∀ (renameMap : List (ModelKey × String))
      (priorStates currentStates : List (ModelKey × ModelState))
      (entries : List (String × String × String)),
      problem_spec_resolveFieldModels renameMap priorStates currentStates entries
        (implementation_resolveFieldModels renameMap priorStates currentStates entries) := by
  intro renameMap priorStates currentStates entries
  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels
  simp only [Id.run]
  have helper : ∀ (es : List (String × String × String)) (init : List (Option ModelState × Option ModelState)),
      (forIn (m := Id) es init (fun entry r =>
            pure (ForInStep.yield
              (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
                      List.lookup (entry.1, entry.2.1) currentStates)]))))
        = init ++ es.map (resolveOne renameMap priorStates currentStates) := by
    intro es
    induction es with
    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [bind, List.map_cons]
      rw [ih]
      simp only [resolveOne, List.append_assoc, List.cons_append, List.nil_append]
  have h2 : (forIn (m := Id) entries [] (fun entry r =>
            (do
              pure PUnit.unit
              pure (ForInStep.yield
                (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
                        List.lookup (entry.1, entry.2.1) currentStates)])))))
        = forIn (m := Id) entries [] (fun entry r =>
            pure (ForInStep.yield
              (r ++ [(List.lookup (entry.1, (List.lookup (entry.1, entry.2.1) renameMap).getD entry.2.1) priorStates,
                      List.lookup (entry.1, entry.2.1) currentStates)]))) := rfl
  rw [h2, helper, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact functional equation. problem_spec_resolveFieldModels pins result = entries.map (resolveOne renameMap priorStates currentStates), with resolveOne byte-frozen in the spec region (indexes currentStates by CURRENT name modelName; priorStates by prior name (renameMap.lookup key).getD modelName). Axioms region EMPTY, verified byte-identical (sha256 0f8f958b...) across all 7 attacks + gold => same_spec integrity. No A-legs to exploit. spec_view collapses BOTH impl and proof regions to placeholders, so attacks were free to rewrite impl AND proof.

SAME_SPEC: all 7 attacks return True; pos_control (identical gold copy) True.

### ATTACKS (all; cmd: bash scripts/lean_verify.sh <f>.lean):
- atk_1 PREPATCH BUG: currentStates indexed by priorName (base-commit). exit=1 (rewrite tactic failed @144 — genuine proof-closure failure, not sorry). Does NOT verify.
- atk_2 SWAP: prior<->current indices swapped. exit=1.
- atk_3 BOUNDARY: iterate entries.tail (drops first). exit=1.
- atk_4 CONTROL-FLOW: prepend instead of append (reversed order). exit=1.
- atk_5 ECHO (correct behavior via entries.map, closing rfl proof): exit=0. #print axioms correct_resolveFieldModels => 'does not depend on any axioms' (clean, no sorryAx). This is the fixed behavior, NOT a wrong impl.
- atk_6 UNGROUNDED ORACLE: entries.map (fun _ => (none,none)). exit=1 (simp made no progress @108).
- atk_7 boundary/model-ref: priorStates indexed by CURRENT name (rename map ignored for prior). exit=1.

POSITIVE CONTROL pos_control.lean (gold): exit=0; #print axioms => [propext, Quot.sound] clean.

CLOSERS => RESOLVE (protocol step 2): the ONLY closing proofs are pos_control (gold) and atk_5. atk_5 computes exactly entries.map (resolveOne ...) i.e. the fixed function, so its faithful refined patch IS the gold patch (currentStates indexed by current name). run_resolve('django__django-15380', gold_patch, timeout=1800, retries=1) => RESOLVED=True, completed=True, note='resolved'. No verified-but-non-resolving witness exists.

PREPATCH REPRODUCED: atk_1 mirrors Solution_prepatch.lean and fails to close. Independent refutation refute.lean proves implBuggy rm pr cu en != en.map (resolveOne rm pr cu) by decide (exit=0) on the renamed-model witness rm=[((app,mymodel2),mymodel)], pr=[((app,mymodel),<mymodel,[f]>)], cu=[((app,mymodel2),<mymodel2,[f2]>)], en=[(app,mymodel2,f2)] => buggy yields (some, none), spec yields (some, some). So prepatch correct_ is UNCLOSABLE.

REFINEMENT.MD AUDIT: 6 legs. Rows 1,2,6 = R (iteration/tuple-unpack/pair-accumulation type refinements); rows 3,4,5 = I (rename-map .get + two snapshot subscripts, reproduced concretely as List.lookup/.getD). NO A-consumed, NO A-reference (axioms region empty; axiom_check.py is a legitimate skip stub — the map ops are Python dict builtins reproduced concretely, not axiomatized callees; downstream get_field/rename-scan unchanged and out of scope). No kind-3 leg. A-leg correspondence vacuously holds (none present).

CONCLUSION: The postcondition is a total functional equation over an empty-axiom model; any impl that closes correct_ is forced extensionally equal to the fixed function, so it must resolve. All 6 genuinely-wrong impls fail to verify; the sole non-gold closer is a correct echo whose patch resolves. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-15380, lean backend.

### Verification performed
- lean_verify.sh on Solution.lean: EXIT 0 (compiles, no sorry/error).
- #print axioms correct_resolveFieldModels -> [propext, Quot.sound] only; NO sorryAx. Proof is genuine.
- same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True (spec region byte-identical).
- Real repo worktree created at base_commit 71e7c8e737; confirmed generate_renamed_fields body and gold patch.

### MODEL vs REAL PATCHED CODE (generate_renamed_fields loop head):
- Gold patch: new_model_state = self.to_state.models[app_label, old_model_name] -> [app_label, model_name] (single-line index fix).
- Spec resolveOne pins, per entry:
  * priorName = (renameMap.lookup (appLabel,modelName)).getD modelName  == renamed_models.get((app,model), model)  [.get w/ default -> .getD, exact]
  * priorState = priorStates.lookup (appLabel, priorName)               == from_state.models[app, old_model_name]
  * currentState = currentStates.lookup (appLabel, modelName)           == PATCHED to_state.models[app, model_name] (current name)
- Order preserved via entries.map. Prepatch impl indexes current snapshot by priorName (the bug) so its proof cannot close -> correct G-DIFF signal, matching the F2P KeyError crash.

NO SPEC-TOO-STRONG / NO DRIFT:
The only modeling boundary is Python dict-subscript [] (raises KeyError on absent key) modeled as List.lookup -> Option (returns none). This is a documented partial->total totalization (mapping.md: 'a real run reaches the line only with a present key'). On the reachable domain (present keys - the only state a non-crashing real run occupies), List.lookup returns `some state` equal to the subscript value, and .getD equals dict.get-with-default; so the modeled function AGREES with the real callee on every reachable input. dict->List key bijection preserves uniqueness, so no first/last-match divergence for genuine inputs. The absent-key case (real raises vs model=none) is outside the reachable domain and is a standard, disclosed modeling choice, not over-strengthening or drift.

Conclusion: The spec is neither too strong nor drifted; it faithfully models the patched real behavior. No diverging input exists on the reachable domain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Role: leakage / gold-reconstruction (attacker 3). Verdict NO-LEAKAGE — the consumer spec view does not leak the gold edit beyond the public problem_statement.

GOLD EDIT (from instance.patch, byte-identical to the traceback in problem_statement): one-token index change in MigrationAutodetector.generate_renamed_fields (autodetector.py:824 @ base 71e7c8e737). The current-snapshot lookup changes from the model's PRIOR name to its CURRENT name: `new_model_state = self.to_state.models[app_label, old_model_name]` -> `... [app_label, model_name]`. Fixes a KeyError when a model AND a field are renamed in the same makemigrations step.

PUBLIC BASELINE: hints_text is EMPTY. problem_statement already discloses everything the spec relies on, VERBATIM: (a) the exact buggy line `new_model_state = self.to_state.models[app_label, old_model_name]` at autodetector.py:823 inside a full traceback; (b) the trigger scenario (rename a model AND a field in one step); (c) the concrete failure `KeyError: ('test_one', 'mymodel')`; (d) the regressing commit aa4acc164. From the quoted buggy line + the KeyError the fix (index the current snapshot by the current name) is directly deducible from public info alone. The public statement is close to a full public leak on its own.

SPEC-VIEW ANALYSIS: Rendered the authoritative consumer spec_view via swebench_unified.markers.spec_view with the LeanBackend. impl -> 'implementation elided', proof -> 'proof elided'. Consumer-facing spec = abstract docstring + pure `resolveOne` + post-condition `problem_spec_resolveFieldModels`. It describes correct behavior ABSTRACTLY (prior snapshot indexed by prior name via renameMap+getD fallback; current snapshot indexed by CURRENT name). Token scan of the lowercased spec view found NONE of the repo-specific gold-edit identifiers: old_model_name, model_name, to_state, from_state, renamed_models, autodetector, generate_renamed_fields, line numbers 823/824, keyerror, get_field, makemigrations, .models[, dict.get, test_one, mymodel, aa4acc164 — all absent.

The discriminating sentence ('Using the prior name to index the current snapshot would fail to locate a model that was renamed in this same step') is a strictly-less-specific restatement of the already-public KeyError failure and is the unavoidable content of any correctness spec for this fix; it adds nothing beyond problem_statement. refinement.md and mapping.md DO carry Python identifiers and buggy-vs-patched lines, but they are audit artifacts, NOT the consumer-facing spec view, so out of leakage scope.

### MECHANICAL CHECKS (all independently re-run this session):
- Mechanical leak screen (leakage.screen over spec view vs patch+problem_statement): passed=True, hard_failures=[].
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/admit).
- #print axioms correct_resolveFieldModels -> [propext, Quot.sound]; NO sorryAx -> proof is GENUINE.
- spec_view sha256 = b2a333930e8e3886769e9c488d644840d7f2cad69a00861898c313f024bad591 -> MATCHES recorded G-HYGIENE spec_view hash (analyzed region is authoritative).
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True -> spec region byte-identical between gold and prepatch; they differ only in the elided impl/proof, so the visible spec is impl-agnostic and does not encode which index the impl uses.
- No relaxed_leakage flag / no RELAXED_LEAKAGE.md; strict path applies.

CONCLUSION: No line of the consumer spec view leaks the gold edit beyond what problem_statement already makes public. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.