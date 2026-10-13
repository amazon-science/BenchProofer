# P2 adversarial audit — django__django-14999

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,6 @@
     (tailOps : List SchemaOp) : List SchemaOp := Id.run do
   if !allowMigrate then
     return []
-  if oldDbTable == newDbTable then
-    return []
   let mut acc : List SchemaOp := []
   acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
   acc := acc ++ tailOps
@@ -64,18 +62,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,15 +45,10 @@
 -- impl-start
 def implementation_renameModel
     (allowMigrate : Bool) (oldDbTable newDbTable : String)
-    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
-  if !allowMigrate then
-    return []
-  if oldDbTable == newDbTable then
-    return []
-  let mut acc : List SchemaOp := []
-  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
-  acc := acc ++ tailOps
-  return acc
+    (tailOps : List SchemaOp) : List SchemaOp :=
+  if allowMigrate && oldDbTable != newDbTable then
+    [SchemaOp.renameTable oldDbTable newDbTable]
+  else []
 -- impl-end
 
 -- proof-start
@@ -64,18 +59,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,15 +45,10 @@
 -- impl-start
 def implementation_renameModel
     (allowMigrate : Bool) (oldDbTable newDbTable : String)
-    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
-  if !allowMigrate then
-    return []
-  if oldDbTable == newDbTable then
-    return []
-  let mut acc : List SchemaOp := []
-  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
-  acc := acc ++ tailOps
-  return acc
+    (tailOps : List SchemaOp) : List SchemaOp :=
+  if allowMigrate && oldDbTable == newDbTable then
+    SchemaOp.renameTable oldDbTable newDbTable :: tailOps
+  else []
 -- impl-end
 
 -- proof-start
@@ -64,18 +59,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,15 +45,10 @@
 -- impl-start
 def implementation_renameModel
     (allowMigrate : Bool) (oldDbTable newDbTable : String)
-    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
-  if !allowMigrate then
-    return []
-  if oldDbTable == newDbTable then
-    return []
-  let mut acc : List SchemaOp := []
-  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
-  acc := acc ++ tailOps
-  return acc
+    (tailOps : List SchemaOp) : List SchemaOp :=
+  if allowMigrate && oldDbTable != newDbTable then
+    SchemaOp.renameTable newDbTable oldDbTable :: tailOps
+  else []
 -- impl-end
 
 -- proof-start
@@ -64,18 +59,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,15 +45,10 @@
 -- impl-start
 def implementation_renameModel
     (allowMigrate : Bool) (oldDbTable newDbTable : String)
-    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
-  if !allowMigrate then
-    return []
-  if oldDbTable == newDbTable then
-    return []
-  let mut acc : List SchemaOp := []
-  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
-  acc := acc ++ tailOps
-  return acc
+    (tailOps : List SchemaOp) : List SchemaOp :=
+  if allowMigrate && oldDbTable != newDbTable then
+    tailOps ++ [SchemaOp.renameTable oldDbTable newDbTable]
+  else []
 -- impl-end
 
 -- proof-start
@@ -64,18 +59,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,15 +45,10 @@
 -- impl-start
 def implementation_renameModel
     (allowMigrate : Bool) (oldDbTable newDbTable : String)
-    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
-  if !allowMigrate then
-    return []
-  if oldDbTable == newDbTable then
-    return []
-  let mut acc : List SchemaOp := []
-  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
-  acc := acc ++ tailOps
-  return acc
+    (tailOps : List SchemaOp) : List SchemaOp :=
+  if allowMigrate && oldDbTable != newDbTable then
+    SchemaOp.renameTable oldDbTable newDbTable :: (tailOps ++ [SchemaOp.other 0])
+  else []
 -- impl-end
 
 -- proof-start
@@ -64,18 +59,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,15 +45,10 @@
 -- impl-start
 def implementation_renameModel
     (allowMigrate : Bool) (oldDbTable newDbTable : String)
-    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
-  if !allowMigrate then
-    return []
-  if oldDbTable == newDbTable then
-    return []
-  let mut acc : List SchemaOp := []
-  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
-  acc := acc ++ tailOps
-  return acc
+    (tailOps : List SchemaOp) : List SchemaOp :=
+  if oldDbTable != newDbTable then
+    SchemaOp.renameTable oldDbTable newDbTable :: tailOps
+  else []
 -- impl-end
 
 -- proof-start
@@ -64,18 +59,9 @@
   intro allowMigrate oldDbTable newDbTable tailOps
   unfold problem_spec_renameModel implementation_renameModel
   refine ⟨?_, ?_, ?_⟩
-  · intro hm
-    simp only [hm, Bool.not_false, Id.run, ite_true]
-    rfl
-  · intro hm heq
-    subst hm
-    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
-      if_false, Bool.false_eq_true]
-    rfl
-  · intro hm hne
-    subst hm
-    have hbeq : (oldDbTable == newDbTable) = false := by
-      simpa using hne
-    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
-    rfl
+  · intro hm; subst hm; simp
+  · intro hm heq; subst hm; subst heq; simp
+  · intro hm hne; subst hm
+    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
+    simp [hbeq]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The schema operations the
-- procedure issues are reified as `SchemaOp` data (below) and threaded through
-- structurally; nothing about the internal effect of issuing an operation is
-- modeled or assumed, so the proof consumes no callee axiom. The proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A schema-editor operation emitted while carrying a model rename to the
database. `renameTable old new` renames the main table from `old` to `new`; any
other emitted operation (the dependent-field / many-to-many follow-ups) is
represented opaquely as `other`. -/
inductive SchemaOp where
  | renameTable (old new : String) : SchemaOp
  | other (tag : Nat) : SchemaOp
  deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- The procedure issues a sequence of schema operations for a model rename.

Inputs: `allowMigrate` is the applicability guard; `oldDbTable` / `newDbTable`
are the stored table names before and after the rename; `tailOps` is the
sequence of dependent follow-up operations the rename would otherwise issue.

The emitted sequence is pinned in every case:
* when the operation is not applicable, nothing is emitted;
* when the stored table name is unchanged by the rename, nothing is emitted
  (the rename is a no-op at the database level);
* otherwise the main table rename is emitted first, followed by exactly the
  dependent follow-up operations, unchanged and in order. -/
def problem_spec_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) (result : List SchemaOp) : Prop :=
  (allowMigrate = false → result = []) ∧
  (allowMigrate = true → oldDbTable = newDbTable → result = []) ∧
  (allowMigrate = true → oldDbTable ≠ newDbTable →
      result = SchemaOp.renameTable oldDbTable newDbTable :: tailOps)
-- post-conditions-end

-- impl-start
def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp :=
  match allowMigrate, oldDbTable == newDbTable with
  | true, false => SchemaOp.renameTable oldDbTable newDbTable :: tailOps
  | _, _ => []
-- impl-end

-- proof-start
theorem correct_renameModel :
    ∀ (allowMigrate : Bool) (oldDbTable newDbTable : String) (tailOps : List SchemaOp),
      problem_spec_renameModel allowMigrate oldDbTable newDbTable tailOps
        (implementation_renameModel allowMigrate oldDbTable newDbTable tailOps) := by
  intro allowMigrate oldDbTable newDbTable tailOps
  unfold problem_spec_renameModel implementation_renameModel
  refine ⟨?_, ?_, ?_⟩
  · intro hm; subst hm; simp
  · intro hm heq; subst hm; subst heq; simp
  · intro hm hne; subst hm
    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
    simp [hbeq]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-14999 (lean). Spec problem_spec_renameModel is TOTAL and DETERMINISTIC: its three conjuncts partition the whole input domain (allowMigrate false; allowMigrate true & old=new; allowMigrate true & old!=new) and pin `result` to a UNIQUE concrete list in each case ([], [], and renameTable oldDbTable newDbTable :: tailOps). Hence any same-spec impl that closes correct_renameModel is extensionally equal to gold on every input, so no verifying same-spec impl can fail to resolve. I confirmed this by falsification.

 Each attack built by copying Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec('lean') == True for ALL 8 files (verified via swebench_unified.markers.same_spec + backends.get_backend). Every wrong impl carried an honest robust closing-shaped proof (intro/unfold/refine ⟨?_,?_,?_⟩ + per-branch simp) so failure is not a mismatched-proof artifact. Verifications run concurrently (2 batches of 4) via `bash scripts/lean_verify.sh <f>`.

Attacks (distinct wrong-impl classes), all FAIL with genuine 'error: unsolved goals' (exit 1):
- atk_1: prepatch bug — no old==new guard; emits renameTable::tailOps when old=new (violates conjunct 2). exit=1, unsolved goals @ proof.
- atk_2: partial-output — drops tailOps in the differ branch (violates conjunct 3). exit=1.
- atk_3: inverted/boundary guard — emits when old==new, [] otherwise. exit=1.
- atk_4: ungrounded/arg-swap — renameTable newDbTable oldDbTable (swapped names). exit=1.
- atk_5: control-flow/order — tailOps ++ [rename] (wrong emission order). exit=1.
- atk_6: extra-op injection — appends SchemaOp.other 0 to the tail. exit=1.
- atk_7: ignores allowMigrate entirely (violates conjunct 1). exit=1.
All failures are 'unsolved goals' (verified via grep on .out), i.e. the frozen spec rejects each — not syntax errors.

Positive control atk_pos: gold-EQUIVALENT written differently (match on allowMigrate, old==new). exit=0 (verifies, no sorry). Clean axioms confirmed: appended `#print axioms correct_renameModel` (atk_pos_ax.lean) → 'depends on axioms: [propext, Classical.choice, Quot.sound]' (no sorryAx/_prop). This establishes the model↔patch correspondence positively: a faithful re-encoding of the gold behavior closes cleanly.

prepatch_reproduced=true: atk_1 IS the prepatch impl (Solution_prepatch.lean skeleton) and its proof does not close against the frozen spec (G-DIFF signal reproduced).

Since NO same-spec wrong impl produced a closing clean-axiom proof, there is no patch to materialize/resolve — the mandatory resolve step is vacuous (no candidate qualifies). patches={} accordingly.

refinement.md audit: all legs R/A/I with NO kind-3. Rows: 1 R (allowMigrate Bool guard), 2 I (added old==new guard, the fix), 3 R (renameTable reification), 4 R (tailOps tail-abstraction of UNCHANGED related/m2m loops), 5 I (return). No A-consumed / A-reference rows; axioms region empty; axiom_check.py is a legitimate skip stub (self-contained structural control flow over reified SchemaOp data, no callee property assumed). The tail-abstraction is sound: the spec constrains only that the unchanged follow-ups are emitted in order after the main rename, never their contents. A-leg correspondence holds vacuously (no A-legs).

Verdict: SOUND — ≥5 distinct attacks (7 run) plus prepatch, none breaks the spec; positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The schema operations the
-- procedure issues are reified as `SchemaOp` data (below) and threaded through
-- structurally; nothing about the internal effect of issuing an operation is
-- modeled or assumed, so the proof consumes no callee axiom. The proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A schema-editor operation emitted while carrying a model rename to the
database. `renameTable old new` renames the main table from `old` to `new`; any
other emitted operation (the dependent-field / many-to-many follow-ups) is
represented opaquely as `other`. -/
inductive SchemaOp where
  | renameTable (old new : String) : SchemaOp
  | other (tag : Nat) : SchemaOp
  deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- The procedure issues a sequence of schema operations for a model rename.

Inputs: `allowMigrate` is the applicability guard; `oldDbTable` / `newDbTable`
are the stored table names before and after the rename; `tailOps` is the
sequence of dependent follow-up operations the rename would otherwise issue.

The emitted sequence is pinned in every case:
* when the operation is not applicable, nothing is emitted;
* when the stored table name is unchanged by the rename, nothing is emitted
  (the rename is a no-op at the database level);
* otherwise the main table rename is emitted first, followed by exactly the
  dependent follow-up operations, unchanged and in order. -/
def problem_spec_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) (result : List SchemaOp) : Prop :=
  (allowMigrate = false → result = []) ∧
  (allowMigrate = true → oldDbTable = newDbTable → result = []) ∧
  (allowMigrate = true → oldDbTable ≠ newDbTable →
      result = SchemaOp.renameTable oldDbTable newDbTable :: tailOps)
-- post-conditions-end

-- impl-start
def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp :=
  match allowMigrate, oldDbTable == newDbTable with
  | true, false => SchemaOp.renameTable oldDbTable newDbTable :: tailOps
  | _, _ => []
-- impl-end

-- proof-start
theorem correct_renameModel :
    ∀ (allowMigrate : Bool) (oldDbTable newDbTable : String) (tailOps : List SchemaOp),
      problem_spec_renameModel allowMigrate oldDbTable newDbTable tailOps
        (implementation_renameModel allowMigrate oldDbTable newDbTable tailOps) := by
  intro allowMigrate oldDbTable newDbTable tailOps
  unfold problem_spec_renameModel implementation_renameModel
  refine ⟨?_, ?_, ?_⟩
  · intro hm; subst hm; simp
  · intro hm heq; subst hm; subst heq; simp
  · intro hm hne; subst hm
    have hbeq : (oldDbTable == newDbTable) = false := by simpa using hne
    simp [hbeq]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-14999 (lean). Spec problem_spec_renameModel is TOTAL and DETERMINISTIC: its three conjuncts partition the whole input domain (allowMigrate false; allowMigrate true & old=new; allowMigrate true & old!=new) and pin `result` to a UNIQUE concrete list in each case ([], [], and renameTable oldDbTable newDbTable :: tailOps). Hence any same-spec impl that closes correct_renameModel is extensionally equal to gold on every input, so no verifying same-spec impl can fail to resolve. I confirmed this by falsification.

 Each attack built by copying Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec('lean') == True for ALL 8 files (verified via swebench_unified.markers.same_spec + backends.get_backend). Every wrong impl carried an honest robust closing-shaped proof (intro/unfold/refine ⟨?_,?_,?_⟩ + per-branch simp) so failure is not a mismatched-proof artifact. Verifications run concurrently (2 batches of 4) via `bash scripts/lean_verify.sh <f>`.

Attacks (distinct wrong-impl classes), all FAIL with genuine 'error: unsolved goals' (exit 1):
- atk_1: prepatch bug — no old==new guard; emits renameTable::tailOps when old=new (violates conjunct 2). exit=1, unsolved goals @ proof.
- atk_2: partial-output — drops tailOps in the differ branch (violates conjunct 3). exit=1.
- atk_3: inverted/boundary guard — emits when old==new, [] otherwise. exit=1.
- atk_4: ungrounded/arg-swap — renameTable newDbTable oldDbTable (swapped names). exit=1.
- atk_5: control-flow/order — tailOps ++ [rename] (wrong emission order). exit=1.
- atk_6: extra-op injection — appends SchemaOp.other 0 to the tail. exit=1.
- atk_7: ignores allowMigrate entirely (violates conjunct 1). exit=1.
All failures are 'unsolved goals' (verified via grep on .out), i.e. the frozen spec rejects each — not syntax errors.

Positive control atk_pos: gold-EQUIVALENT written differently (match on allowMigrate, old==new). exit=0 (verifies, no sorry). Clean axioms confirmed: appended `#print axioms correct_renameModel` (atk_pos_ax.lean) → 'depends on axioms: [propext, Classical.choice, Quot.sound]' (no sorryAx/_prop). This establishes the model↔patch correspondence positively: a faithful re-encoding of the gold behavior closes cleanly.

prepatch_reproduced=true: atk_1 IS the prepatch impl (Solution_prepatch.lean skeleton) and its proof does not close against the frozen spec (G-DIFF signal reproduced).

Since NO same-spec wrong impl produced a closing clean-axiom proof, there is no patch to materialize/resolve — the mandatory resolve step is vacuous (no candidate qualifies). patches={} accordingly.

refinement.md audit: all legs R/A/I with NO kind-3. Rows: 1 R (allowMigrate Bool guard), 2 I (added old==new guard, the fix), 3 R (renameTable reification), 4 R (tailOps tail-abstraction of UNCHANGED related/m2m loops), 5 I (return). No A-consumed / A-reference rows; axioms region empty; axiom_check.py is a legitimate skip stub (self-contained structural control flow over reified SchemaOp data, no callee property assumed). The tail-abstraction is sound: the spec constrains only that the unchanged follow-ups are emitted in order after the main rename, never their contents. A-leg correspondence holds vacuously (no A-legs).

Verdict: SOUND — ≥5 distinct attacks (7 run) plus prepatch, none breaks the spec; positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Preconditions verified: scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry); #print axioms correct_renameModel -> [propext, Classical.choice, Quot.sound] (clean, no sorryAx/_prop); swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean-backend) -> True (spec region byte-identical).

Real callee comparison: RenameModel.database_forwards, base_commit a754b82... (verified against repos_cache/django__django). Pre-patch has NO table-name guard; gold patch afeafd6036 (Fixed #33201) adds the local-var extraction + `if old_db_table == new_db_table: return` between the allow_migrate guard and alter_db_table. Confirmed patched source: guard-false -> body skipped -> no ops; guard-true & old==new -> return -> no ops; guard-true & old!=new -> alter_db_table(new_model, old, new) emitted FIRST then the (unchanged) related_objects + m2m loops.

Spec (problem_spec_renameModel) matches on the whole input domain: conjunct 1 (allowMigrate=false -> []) <-> allow_migrate false; conjunct 2 (true, old=new -> []) <-> the added early-return (F2P assertNumQueries(0)); conjunct 3 (true, old!=new -> renameTable old new :: tailOps) <-> main rename emitted first, then the unchanged follow-ups abstracted as free input tailOps.

Faithfulness checks for drift: (a) String equality - Python str `==` on _meta.db_table (always a computed str, never None) <-> Lean BEq String, both exact; no divergence. (b) Ordering - real emits the main rename unconditionally before any loop op, matching `:: tailOps`; nothing is emitted before the main rename. (c) Tail abstraction is sound and non-strengthening: tailOps is universally quantified, so for any concrete emission of the unchanged loops there is a matching tailOps; the spec constrains only that the tail follows the main rename in order, never its contents, so it cannot over-constrain the real behavior. (d) Conjuncts are guarded by allowMigrate and partition the domain disjointly (no case pins result to two conflicting values). The spec is total & deterministic, and on every input the pinned result equals the real callee's observable op sequence at the modeled abstraction. No diverging input exists; the spec is not too strong and does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen over the lean spec view PASSES (no hard failures): no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment naming a patched repo symbol (db_table / database_forwards / alter_db_table / allow_migrate_model), no narration terms. same_spec(patched, prepatch)=True — the discriminator lives only in the elided impl/proof regions. Spec identifiers are fully abstracted (allowMigrate, oldDbTable, newDbTable, tailOps, SchemaOp.renameTable). Semantically, the post-condition's noop clause ('when the stored table name is unchanged, nothing is emitted; the rename is a no-op at the database level') only restates behavior ALREADY public in problem_statement ('RenameModel with db_table should be a noop... must be a noop'), so it does not leak the gold edit beyond the problem statement. The 'buggy' narration is confined to the prepatch impl region, which is elided from the spec view. No dependence on hints_text (empty).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
