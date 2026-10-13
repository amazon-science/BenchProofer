# P2 adversarial audit — django__django-14500

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition problem_spec_unapplyMigration mig result := result = mig.replaces ++ [(mig.appLabel, mig.name)] is a TOTAL FUNCTIONAL EQUATION pinning the output to exactly one value on every input. Any implementation whose correct_ proof closes must equal mig.replaces ++ [own] everywhere, which is exactly gold post-patch behavior. 6 distinct wrong impls (prepatch else-branch bug, reversed replaces, own-id-first, partial-domain replaces-only-when-nonempty, duplicated own id, dropLast off-by-one) all FAILED to close with genuine unsolved-goals errors (no sorry). The 2 impls that closed (atk_7 literal spec RHS echo, atk_pos foldl) are behaviorally identical to gold; their faithful refined patch IS the gold patch, which RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,20 +54,12 @@
   if mig.replaces ≠ [] then
     for r in mig.replaces do
       recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
+  else
+    recorded := recorded ++ [(mig.appLabel, mig.name)]
   return recorded
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
   intro mig
@@ -75,17 +67,16 @@
   simp only [Id.run]
   by_cases h : mig.replaces ≠ []
   · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
     have h2 : (do
         let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
             pure PUnit.unit
             pure (ForInStep.yield (r_1 ++ [r]))
         pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
+        pure r : Id (List MigrationId))
       = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+          (fun r acc => (ForInStep.yield (acc ++ [r])))) := rfl
+    rw [h2]
+    -- goal reduces to: replaces = replaces ++ [own]; false in general
+    simp
+  · rw [if_neg h]; push_neg at h; rw [h]; rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,43 +49,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
-  let mut recorded : List MigrationId := []
-  if mig.replaces ≠ [] then
-    for r in mig.replaces do
-      recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
-  return recorded
+def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
+  mig.replaces.reverse ++ [(mig.appLabel, mig.name)]
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
   intro mig
   unfold problem_spec_unapplyMigration implementation_unapplyMigration
-  simp only [Id.run]
-  by_cases h : mig.replaces ≠ []
-  · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
-    have h2 : (do
-        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r_1 ++ [r]))
-        pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
-      = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,43 +49,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
-  let mut recorded : List MigrationId := []
-  if mig.replaces ≠ [] then
-    for r in mig.replaces do
-      recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
-  return recorded
+def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
+  [(mig.appLabel, mig.name)] ++ mig.replaces
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
   intro mig
   unfold problem_spec_unapplyMigration implementation_unapplyMigration
-  simp only [Id.run]
-  by_cases h : mig.replaces ≠ []
-  · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
-    have h2 : (do
-        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r_1 ++ [r]))
-        pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
-      = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+  simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,43 +49,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
-  let mut recorded : List MigrationId := []
-  if mig.replaces ≠ [] then
-    for r in mig.replaces do
-      recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
-  return recorded
+def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
+  if mig.replaces = [] then [(mig.appLabel, mig.name)] else mig.replaces
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
   intro mig
   unfold problem_spec_unapplyMigration implementation_unapplyMigration
-  simp only [Id.run]
-  by_cases h : mig.replaces ≠ []
-  · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
-    have h2 : (do
-        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r_1 ++ [r]))
-        pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
-      = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+  by_cases h : mig.replaces = []
+  · rw [if_pos h, h]; rfl
+  · rw [if_neg h]; simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,43 +49,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
-  let mut recorded : List MigrationId := []
-  if mig.replaces ≠ [] then
-    for r in mig.replaces do
-      recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
-  return recorded
+def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
+  mig.replaces ++ [(mig.appLabel, mig.name), (mig.appLabel, mig.name)]
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
   intro mig
   unfold problem_spec_unapplyMigration implementation_unapplyMigration
-  simp only [Id.run]
-  by_cases h : mig.replaces ≠ []
-  · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
-    have h2 : (do
-        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r_1 ++ [r]))
-        pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
-      = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+  simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,43 +49,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
-  let mut recorded : List MigrationId := []
-  if mig.replaces ≠ [] then
-    for r in mig.replaces do
-      recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
-  return recorded
+def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
+  mig.replaces.dropLast ++ [(mig.appLabel, mig.name)]
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
   intro mig
   unfold problem_spec_unapplyMigration implementation_unapplyMigration
-  simp only [Id.run]
-  by_cases h : mig.replaces ≠ []
-  · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
-    have h2 : (do
-        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r_1 ++ [r]))
-        pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
-      = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+  simp
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,43 +49,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
-  let mut recorded : List MigrationId := []
-  if mig.replaces ≠ [] then
-    for r in mig.replaces do
-      recorded := recorded ++ [r]
-  recorded := recorded ++ [(mig.appLabel, mig.name)]
-  return recorded
+def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
+  mig.replaces ++ [(mig.appLabel, mig.name)]
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, collects the visited
-identifiers in order: it appends `xs` to the initial accumulator. -/
-private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
-    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-
 theorem correct_unapplyMigration : ∀ mig : Migration,
     problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
-  intro mig
-  unfold problem_spec_unapplyMigration implementation_unapplyMigration
-  simp only [Id.run]
-  by_cases h : mig.replaces ≠ []
-  · rw [if_pos h]
-    -- bridge the desugared `do` body to the clean `forIn` form of the helper
-    have h2 : (do
-        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r_1 ++ [r]))
-        pure PUnit.unit
-        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
-      = Id.run (forIn mig.replaces ([] : List MigrationId)
-          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
-    rw [h2, unapplyMigration_forIn]; simp
-  · rw [if_neg h]
-    push_neg at h
-    rw [h]; rfl
+  intro mig; rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rolling back a migration that stands in for (replaces) a set of earlier
migrations.

A migration carries its own identifier (an application label together with a
migration name) and, optionally, a list of identifiers of the earlier
migrations it stands in for. When such a migration is rolled back, the rollback
must record, as no-longer-applied, every identifier the migration represents:
both each identifier it stands in for AND the migration's own identifier. A
migration that stands in for nothing records only its own identifier.

The behavior is stated abstractly as the ordered sequence of identifiers
recorded as no-longer-applied; the implementation and correctness proof are
supplied separately.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the operation under spec
-- merely decides WHICH identifiers are recorded as no-longer-applied and in
-- what order. The recording sink itself (which removes an identifier from the
-- applied set) is unchanged and order-independent, so its effect is modeled as
-- collecting the ordered argument sequence; nothing about it is assumed.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A migration identifier: an application label paired with a migration name. -/
abbrev MigrationId := String × String

/-- The pieces of a migration the rollback reads: its own identifier and the
list of identifiers it stands in for (empty when it stands in for nothing). -/
structure Migration where
  appLabel : String
  name : String
  replaces : List MigrationId
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered sequence of identifiers recorded as
no-longer-applied: each identifier the migration stands in for, in order,
followed by the migration's own identifier. (When the migration stands in for
nothing, this is just its own identifier.) -/
def problem_spec_unapplyMigration (mig : Migration) (result : List MigrationId) : Prop :=
  result = mig.replaces ++ [(mig.appLabel, mig.name)]
-- post-conditions-end

-- impl-start
def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
  mig.replaces.foldl (fun acc r => acc ++ [r]) [] ++ [(mig.appLabel, mig.name)]
-- impl-end

-- proof-start
theorem correct_unapplyMigration : ∀ mig : Migration,
    problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
  intro mig
  unfold problem_spec_unapplyMigration implementation_unapplyMigration
  have : ∀ (xs : List MigrationId) (init : List MigrationId),
      xs.foldl (fun acc r => acc ++ [r]) init = init ++ xs := by
    intro xs
    induction xs with
    | nil => intro init; simp
    | cons a as ih => intro init; simp [List.foldl_cons, ih]
  rw [this]; simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files (atk_1..atk_7, atk_pos) same_spec==True vs Solution.lean via swebench_unified.markers.same_spec (lean backend). Prefix = spec regions byte-identical through -- post-conditions-end; only impl+proof edited.

### VERIFY (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 PREPATCH BUG (own-id only in else, full closing attempt no sorry) -> exit 1; error at :80 simp made no progress; goal replaces = replaces ++ [own]. prepatch_reproduced=True.
- atk_2 reversed replaces -> exit 1; goal replaces.reverse ++ [own] = replaces ++ [own].
- atk_3 own-id-first control-flow-effect -> exit 1; goal (own)::replaces = replaces ++ [own].
- atk_4 partial-domain (replaces-only when nonempty) -> exit 1; case neg goal False.
- atk_5 boundary duplicate own id -> exit 1; goal False.
- atk_6 boundary dropLast off-by-one -> exit 1; goal replaces.dropLast = replaces.
All six exit 1 with GENUINE unsolved goals (grep sorry == 0 across all attack files).

CLOSING + CLEAN AXIOMS (#print axioms correct_unapplyMigration appended, re-verified):
- atk_7 ungrounded-oracle echo (returns spec RHS literally) -> exit 0; 'does not depend on any axioms'.
- atk_pos foldl positive control -> exit 0; depends on [propext] only. No sorryAx in either. Clean.

RESOLVE (protocol step 2, EXECUTED): both closing impls compute exactly mig.replaces ++ [(appLabel,name)] = gold post-patch recording stream, so the faithful refined patch is the gold diff (hoist record_unapplied(own) out of else -> unconditional). run_resolve('django__django-14500', gold_patch, timeout=1200) -> RESOLVED: True, COMPLETED: True, note 'resolved', flaky False. verify AND resolve agree; no verify⇏correct break.

refinement.md AUDIT: 5 legs, all tagged I (rows 1,3,4,5) / R (row 2 truthiness-of-replaces bijection). No A-consumed, no A-reference (axioms region genuinely empty — record_unapplied is UNCHANGED, order-independent/idempotent sink, framed out; effect modeled as ordered arg stream). NO kind-3 (changed-inexpressible) leg. Correspondence holds: fix is pure control flow (own-id record moved out of else, made unconditional), row 4 maps it directly to the discriminating replacement case. G-DIFF discriminant valid: prepatch omits own id when replaces nonempty (confirmed via atk_1). No A-leg callee correspondence to check since none present.

CONCLUSION: total functional-equation post-condition rejects every genuinely-wrong impl (6 distinct falsification attempts, all fail-to-close with real goals) and admits only gold-behavior impls, whose faithful patch resolves. verify ⇒ correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition problem_spec_unapplyMigration mig result := result = mig.replaces ++ [(mig.appLabel, mig.name)] is a TOTAL FUNCTIONAL EQUATION pinning the output to exactly one value on every input. Any implementation whose correct_ proof closes must equal mig.replaces ++ [own] everywhere, which is exactly gold post-patch behavior. 6 distinct wrong impls (prepatch else-branch bug, reversed replaces, own-id-first, partial-domain replaces-only-when-nonempty, duplicated own id, dropLast off-by-one) all FAILED to close with genuine unsolved-goals errors (no sorry). The 2 impls that closed (atk_7 literal spec RHS echo, atk_pos foldl) are behaviorally identical to gold; their faithful refined patch IS the gold patch, which RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rolling back a migration that stands in for (replaces) a set of earlier
migrations.

A migration carries its own identifier (an application label together with a
migration name) and, optionally, a list of identifiers of the earlier
migrations it stands in for. When such a migration is rolled back, the rollback
must record, as no-longer-applied, every identifier the migration represents:
both each identifier it stands in for AND the migration's own identifier. A
migration that stands in for nothing records only its own identifier.

The behavior is stated abstractly as the ordered sequence of identifiers
recorded as no-longer-applied; the implementation and correctness proof are
supplied separately.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the operation under spec
-- merely decides WHICH identifiers are recorded as no-longer-applied and in
-- what order. The recording sink itself (which removes an identifier from the
-- applied set) is unchanged and order-independent, so its effect is modeled as
-- collecting the ordered argument sequence; nothing about it is assumed.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A migration identifier: an application label paired with a migration name. -/
abbrev MigrationId := String × String

/-- The pieces of a migration the rollback reads: its own identifier and the
list of identifiers it stands in for (empty when it stands in for nothing). -/
structure Migration where
  appLabel : String
  name : String
  replaces : List MigrationId
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered sequence of identifiers recorded as
no-longer-applied: each identifier the migration stands in for, in order,
followed by the migration's own identifier. (When the migration stands in for
nothing, this is just its own identifier.) -/
def problem_spec_unapplyMigration (mig : Migration) (result : List MigrationId) : Prop :=
  result = mig.replaces ++ [(mig.appLabel, mig.name)]
-- post-conditions-end

-- impl-start
def implementation_unapplyMigration (mig : Migration) : List MigrationId :=
  mig.replaces.foldl (fun acc r => acc ++ [r]) [] ++ [(mig.appLabel, mig.name)]
-- impl-end

-- proof-start
theorem correct_unapplyMigration : ∀ mig : Migration,
    problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
  intro mig
  unfold problem_spec_unapplyMigration implementation_unapplyMigration
  have : ∀ (xs : List MigrationId) (init : List MigrationId),
      xs.foldl (fun acc r => acc ++ [r]) init = init ++ xs := by
    intro xs
    induction xs with
    | nil => intro init; simp
    | cons a as ih => intro init; simp [List.foldl_cons, ih]
  rw [this]; simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files (atk_1..atk_7, atk_pos) same_spec==True vs Solution.lean via swebench_unified.markers.same_spec (lean backend). Prefix = spec regions byte-identical through -- post-conditions-end; only impl+proof edited.

### VERIFY (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 PREPATCH BUG (own-id only in else, full closing attempt no sorry) -> exit 1; error at :80 simp made no progress; goal replaces = replaces ++ [own]. prepatch_reproduced=True.
- atk_2 reversed replaces -> exit 1; goal replaces.reverse ++ [own] = replaces ++ [own].
- atk_3 own-id-first control-flow-effect -> exit 1; goal (own)::replaces = replaces ++ [own].
- atk_4 partial-domain (replaces-only when nonempty) -> exit 1; case neg goal False.
- atk_5 boundary duplicate own id -> exit 1; goal False.
- atk_6 boundary dropLast off-by-one -> exit 1; goal replaces.dropLast = replaces.
All six exit 1 with GENUINE unsolved goals (grep sorry == 0 across all attack files).

CLOSING + CLEAN AXIOMS (#print axioms correct_unapplyMigration appended, re-verified):
- atk_7 ungrounded-oracle echo (returns spec RHS literally) -> exit 0; 'does not depend on any axioms'.
- atk_pos foldl positive control -> exit 0; depends on [propext] only. No sorryAx in either. Clean.

RESOLVE (protocol step 2, EXECUTED): both closing impls compute exactly mig.replaces ++ [(appLabel,name)] = gold post-patch recording stream, so the faithful refined patch is the gold diff (hoist record_unapplied(own) out of else -> unconditional). run_resolve('django__django-14500', gold_patch, timeout=1200) -> RESOLVED: True, COMPLETED: True, note 'resolved', flaky False. verify AND resolve agree; no verify⇏correct break.

refinement.md AUDIT: 5 legs, all tagged I (rows 1,3,4,5) / R (row 2 truthiness-of-replaces bijection). No A-consumed, no A-reference (axioms region genuinely empty — record_unapplied is UNCHANGED, order-independent/idempotent sink, framed out; effect modeled as ordered arg stream). NO kind-3 (changed-inexpressible) leg. Correspondence holds: fix is pure control flow (own-id record moved out of else, made unconditional), row 4 maps it directly to the discriminating replacement case. G-DIFF discriminant valid: prepatch omits own id when replaces nonempty (confirmed via atk_1). No A-leg callee correspondence to check since none present.

CONCLUSION: total functional-equation post-condition rejects every genuinely-wrong impl (6 distinct falsification attempts, all fail-to-close with real goals) and admits only gold-behavior impls, whose faithful patch resolves. verify ⇒ correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14500 (lean). RESULT: FAITHFUL — no diverging input found.

Modeled fn: MigrationExecutor.unapply_migration recording path. Spec: problem_spec_unapplyMigration mig result := result = mig.replaces ++ [(mig.appLabel, mig.name)].

Real post-patch callee (django/db/migrations/executor.py, commit 3219dd3, lines 245-262):
  if migration.replaces:
      for app_label, name in migration.replaces:
          self.recorder.record_unapplied(app_label, name)
  self.recorder.record_unapplied(migration.app_label, migration.name)   # UNCONDITIONAL
Observable ordered record_unapplied sequence = replaces ++ [(app_label,name)] for empty and non-empty replaces alike — exactly the spec. Verified 'unconditional own-record present: True' via inspect.getsource.

Differential test (spec model vs real callee driven fake=True with a capture recorder, __new__ bypass): 200k+ random inputs (pinned seed 14500) + boundary/edge cases (empty list, None, empty tuple, squashed multi-replaces, own-id-appearing-in-replaces, duplicate replaces) → 0 mismatches. The falsy-collapse (None/()/[] ⇔ empty list) in the type bijection holds; append-order = call-order holds.

Modeling boundary is legitimate: the unchanged record_unapplied sink is order-independent/idempotent and correctly framed out; the fake=True path (schema-editor/state-mutation) is orthogonal to the recording decision. No over-strengthening: the spec does not assert anything the real callee violates.

Hygiene checks: same_spec(Solution, Solution_prepatch, lean tables) = True (spec region byte-identical). lean_verify.sh Solution.lean exit 0. #print axioms correct_unapplyMigration → [propext, Classical.choice, Quot.sound] only — no sorryAx, proof is genuine.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified via markers.spec_view; same_spec(post,pre)=True, spec region byte-identical) discloses only the DESIRED behavior, which is already public in the problem_statement: 'Squashed migration is not marked as unapplied ... mark the squash migration as unapplied, too, not only the replaced migrations.' The spec view: (1) docstring — 'record, as no-longer-applied, every identifier the migration represents: both each identifier it stands in for AND the migration's own identifier' — restates that public requirement; (2) post-condition `result = mig.replaces ++ [(mig.appLabel, mig.name)]` is a faithful abstraction of the stated correct behavior, not an edit disclosure; (3) impl-start/proof regions are ELIDED ('supplied by the consumer'), so the actual gold edit (moving record_unapplied out of the else branch) is not shown. Mechanical leak.py screen passes (no diff markers, no patched file path django/db/migrations/executor.py, no patched symbol unapply_migration in identifiers/comments, no bug/fix narration). The replaced-first-then-own ordering is a canonical modeling choice (record_unapplied is order-independent per mapping.md), not localization of the diff. Nothing in the spec view reveals the if/else-restructuring edit beyond what problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
