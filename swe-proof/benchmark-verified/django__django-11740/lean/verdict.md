# P2 adversarial audit — django__django-11740

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
fields = [{isRelation := true, fk := {swappableSetting := none, remoteAppLabel := "testapp", remoteObjectName := "Author", through := none}}]. Spec requires the emitted op carry dependencies = [{appLabel:="testapp", objectName:="Author", fieldName:=none, create:=true}]; every wrong impl (prepatch [], inverted guard, dropped-through, doubled, reversed order, filtered) yields a different result list, so `result = fields.map (...)` is FALSE. Machine-checked FALSE in disproof_1.lean (verifies exit 0, clean axioms [propext, Quot.sound]).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,14 +131,8 @@
     (fields : List AlteredField) : List AlterFieldOp := Id.run do
   let mut result := []
   for f in fields do
-    let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
-    if f.isRelation then
-      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
-    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
+    -- prepatch: emit every op with no dependency, even relation fields
+    result := result ++ [({ field := f, dependencies := ([] : List Dep) } : AlterFieldOp)]
   return result
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,12 +132,8 @@
   let mut result := []
   for f in fields do
     let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
-    if f.isRelation then
+    if !f.isRelation then
       dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
     result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
   return result
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,13 +131,8 @@
     (fields : List AlteredField) : List AlterFieldOp := Id.run do
   let mut result := []
   for f in fields do
-    let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
-    if f.isRelation then
-      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
+    -- ignore isRelation: always attach FK-induced deps
+    let dependencies := getDependenciesForForeignKey f.fk
     result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
   return result
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,13 +132,10 @@
   let mut result := []
   for f in fields do
     let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
     if f.isRelation then
       dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
-    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
+    -- prepend instead of append: reverses emission order
+    result := [({ field := f, dependencies := dependencies } : AlterFieldOp)] ++ result
   return result
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,12 +132,9 @@
   let mut result := []
   for f in fields do
     let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
     if f.isRelation then
-      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
+      -- keep only the first (base) dep, drop any through dep
+      dependencies := (getDependenciesForForeignKey f.fk).take 1
     result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
   return result
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,12 +132,8 @@
   let mut result := []
   for f in fields do
     let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
     if f.isRelation then
-      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
+      dependencies := getDependenciesForForeignKey f.fk ++ getDependenciesForForeignKey f.fk
     result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
   return result
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,14 +131,8 @@
     (fields : List AlteredField) : List AlterFieldOp := Id.run do
   let mut result := []
   for f in fields do
-    let mut dependencies := []
-    -- A relation alteration must carry the constraints induced by its reference
-    -- target, so the referenced model's application is ordered before it.
     if f.isRelation then
-      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
-    -- Emit the alteration operation for this field carrying the assembled
-    -- constraints.
-    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
+      result := result ++ [({ field := f, dependencies := getDependenciesForForeignKey f.fk } : AlterFieldOp)]
   return result
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the inter-application ordering constraints attached to a schema-change
operation that alters an existing field in place.

The setting: a schema migration is generated as a sequence of field-alteration
operations, one per field whose definition changed. Each such operation may
carry a list of ordering constraints ("dependencies"): other applications'
migrations that must be applied first, so that everything the altered field
refers to already exists when the alteration runs.

A field may be an ordinary value field, or it may be a RELATION — a field that
points at another model (a foreign-key-style reference). The desired behavior:

  * an alteration of an ordinary (non-relation) field needs no extra ordering
    constraint, so its operation carries an empty constraint list;

  * an alteration that makes the field a relation must carry the ordering
    constraints induced by that relation, so the referenced model's application
    is guaranteed to be migrated first. Otherwise the referenced model cannot be
    resolved when the alteration is applied.

The constraints induced by a relation are computed from the reference target:
* the application + object name of the referenced model — unless the reference
  targets a swap-configurable model, in which case the constraint names the
  configuration setting instead; and
* if the relation routes through an explicit intermediary model that was not
  auto-generated, an additional constraint naming that intermediary.

Each constraint records the target application label, the target object name, an
optional field name (here always absent), and a flag (here always set) marking
it as a "must exist before" ordering constraint.
-/

-- axioms-start
-- No opaque/axiom callee contract is consumed by this specification. The
-- relation-induced constraint computation is modeled DEEPLY as the pure helper
-- `getDependenciesForForeignKey` over the reference-target data (swap setting,
-- referenced application/object name, optional intermediary model), and is
-- validated == the real callee by G-AX. The per-operation constraint assembly
-- is modeled structurally over the field list, so no callee axiom is needed.
-- axioms-end

-- pure-start
/-- One ordering constraint: the target application label, the target object
name, an optional field name, and a flag marking it a "must exist before"
constraint (vs a "must be removed after"). -/
structure Dep where
  appLabel : String
  objectName : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Repr

/-- The reference-target data of a relation field, restricted to what the
constraint computation reads:
* `swappableSetting` — `some name` when the reference targets a swap-configurable
  model (the constraint then names the configuration setting), else `none`;
* `remoteAppLabel` / `remoteObjectName` — the referenced model's application
  label and object name (used when not swap-configurable);
* `through` — `some (app, obj, autoCreated)` when the relation routes through an
  explicit intermediary model, carrying that model's application label, object
  name, and whether it was auto-generated; `none` otherwise. -/
structure FKInfo where
  swappableSetting : Option String
  remoteAppLabel : String
  remoteObjectName : String
  through : Option (String × String × Bool)
deriving DecidableEq

/-- One altered field, restricted to the touched aspects:
* `isRelation` — whether the new field definition is a relation (points at a
  model);
* `fk` — the reference-target data (consulted only when `isRelation`; for a
  non-relation field its contents are irrelevant and never read). -/
structure AlteredField where
  isRelation : Bool
  fk : FKInfo
deriving DecidableEq

/-- One emitted field-alteration operation, restricted to the touched aspect:
* `field` — the altered field this operation alters (its identity);
* `dependencies` — the ordering constraints attached to this operation. The
  operation's other attributes are unchanged by the desired behavior and are not
  modeled. -/
structure AlterFieldOp where
  field : AlteredField
  dependencies : List Dep
deriving DecidableEq

/-- The ordering constraints induced by a relation's reference target. The base
constraint names the referenced model's application + object name, unless the
reference targets a swap-configurable model, in which case it names the
configuration setting. If the relation routes through an explicit, non
auto-generated intermediary model, a second constraint naming that intermediary
is appended. Both constraints carry no field name and are "must exist before"
constraints. -/
def getDependenciesForForeignKey (fk : FKInfo) : List Dep := Id.run do
  let base : Dep :=
    match fk.swappableSetting with
    | some s => { appLabel := "__setting__", objectName := s, fieldName := none, create := true }
    | none   => { appLabel := fk.remoteAppLabel, objectName := fk.remoteObjectName,
                  fieldName := none, create := true }
  let mut deps := [base]
  match fk.through with
  | some (tApp, tObj, autoCreated) =>
      if !autoCreated then
        deps := deps ++ [{ appLabel := tApp, objectName := tObj, fieldName := none, create := true }]
  | none => pure ()
  return deps
-- pure-end

-- post-conditions-start
/-- Exactly one alteration operation is emitted per altered field, in order, and
each operation alters precisely its field and carries: the relation-induced
ordering constraints when that field is a relation, and no constraint otherwise.
The result is element-wise pinned to the input field list — both which field
each operation alters AND the constraints it carries. -/
def problem_spec_generateAlteredFields
    (fields : List AlteredField)
    (result : List AlterFieldOp) : Prop :=
  result = fields.map (fun f =>
    { field := f,
      dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else [] })
-- post-conditions-end

-- impl-start
def implementation_generateAlteredFields
    (fields : List AlteredField) : List AlterFieldOp := Id.run do
  let mut result := []
  for f in fields do
    let mut dependencies := []
    -- A relation alteration must carry the constraints induced by its reference
    -- target, so the referenced model's application is ordered before it.
    if f.isRelation then
      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
    -- Emit the alteration operation for this field carrying the assembled
    -- constraints.
    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
  return result
-- impl-end

-- proof-start
theorem correct_generateAlteredFields :
    ∀ (fields : List AlteredField),
      problem_spec_generateAlteredFields fields
        (implementation_generateAlteredFields fields) := by
  intro fields
  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields
  simp only [Id.run, bind, pure]
  -- Route B: helper over the cleaned `forIn`, generalized over the accumulator.
  have helper : ∀ (init : List AlterFieldOp),
      (forIn (m := Id) fields init (fun f r =>
        (if f.isRelation = true then
            ForInStep.yield (r ++ [({ field := f, dependencies := [] ++ getDependenciesForForeignKey f.fk } : AlterFieldOp)])
          else
            ForInStep.yield (r ++ [({ field := f, dependencies := [] } : AlterFieldOp)]))))
        = init ++ fields.map (fun f =>
            ({ field := f, dependencies := if f.isRelation = true then getDependenciesForForeignKey f.fk else [] } : AlterFieldOp)) := by
    intro init
    induction fields generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, List.nil_append] at ih ⊢
        by_cases h : a.isRelation = true <;>
          simp [h, ih, List.append_assoc]
  rw [helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is EXACT element-wise equality: result = fields.map (fun f => {field := f, dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else []}). This pins field identity, emission order, AND the exact dep list per element — maximally tight; no behaviorally-distinct impl can satisfy it. same_spec=True confirmed for all 7 attacks + positive control.

### ATTACKS (all; cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 prepatch bug (always [] deps): EXIT=1 (unsolved/rewrite error).
- atk_2 boundary/inverted guard (deps on NON-relation): EXIT=1.
- atk_3 control-flow effect (drop isRelation guard, always attach deps): EXIT=1.
- atk_4 order (prepend => reversed emission order): EXIT=1.
- atk_5 subtle-wrong echo (.take 1 => drops the through dep): EXIT=1.
- atk_6 doubled deps (deps ++ deps): EXIT=1.
- atk_7 partial-domain (skip non-relation fields => fewer ops): EXIT=1.
All 7 fail with genuine `error: Tactic rewrite failed / unsolved goals` (NOT syntax errors). No wrong impl closed => no faithful patch materialized/resolve-run needed (per protocol, resolve is only required for a wrong impl whose proof CLOSES with clean axioms; none did).

POSITIVE CONTROL: pos_control.lean (= real Solution.lean impl) EXIT=0; `#print axioms correct_generateAlteredFields` => [propext, Quot.sound] (clean, no sorry).

DISPROOF (rigor beyond carried-tactic failure): disproof_1.lean re-encodes the prepatch impl and proves `¬ ∀ fields, problem_spec ... (impl ...)` via the [rf] counterexample; verifies EXIT=0 with clean axioms [propext, Quot.sound] — establishing the wrong-impl theorem is genuinely FALSE, not merely that the bundle's tactic script happened not to close.

REFINEMENT AUDIT: all 7 legs are R / A-reference / I; NO A-consumed axiom, NO kind-3 ungrounded oracle (RHS computed structurally from input, not echoed from an answer-key). Sole A-reference (getDependenciesForForeignKey ↔ _get_dependencies_for_foreign_key) is G-AX-validated by axiom_check.py, which drives the REAL callee `MigrationAutodetector._get_dependencies_for_foreign_key` over plain-FK/self-FK/swappable(AUTH_USER_MODEL)/auto-created-through/explicit-through fields and asserts equality with the deep model. The A-reference helper lives in the frozen pure region (byte-identical across spec/impl/attacks), so it cannot be gamed by an impl-region edit. Correspondence holds.

VERDICT: SOUND. ≥5 distinct same-spec attacks run; none produced a closing clean-axiom proof, so verify⇒correct is not falsified for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
fields = [{isRelation := true, fk := {swappableSetting := none, remoteAppLabel := "testapp", remoteObjectName := "Author", through := none}}]. Spec requires the emitted op carry dependencies = [{appLabel:="testapp", objectName:="Author", fieldName:=none, create:=true}]; every wrong impl (prepatch [], inverted guard, dropped-through, doubled, reversed order, filtered) yields a different result list, so `result = fields.map (...)` is FALSE. Machine-checked FALSE in disproof_1.lean (verifies exit 0, clean axioms [propext, Quot.sound]).
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the inter-application ordering constraints attached to a schema-change
operation that alters an existing field in place.

The setting: a schema migration is generated as a sequence of field-alteration
operations, one per field whose definition changed. Each such operation may
carry a list of ordering constraints ("dependencies"): other applications'
migrations that must be applied first, so that everything the altered field
refers to already exists when the alteration runs.

A field may be an ordinary value field, or it may be a RELATION — a field that
points at another model (a foreign-key-style reference). The desired behavior:

  * an alteration of an ordinary (non-relation) field needs no extra ordering
    constraint, so its operation carries an empty constraint list;

  * an alteration that makes the field a relation must carry the ordering
    constraints induced by that relation, so the referenced model's application
    is guaranteed to be migrated first. Otherwise the referenced model cannot be
    resolved when the alteration is applied.

The constraints induced by a relation are computed from the reference target:
* the application + object name of the referenced model — unless the reference
  targets a swap-configurable model, in which case the constraint names the
  configuration setting instead; and
* if the relation routes through an explicit intermediary model that was not
  auto-generated, an additional constraint naming that intermediary.

Each constraint records the target application label, the target object name, an
optional field name (here always absent), and a flag (here always set) marking
it as a "must exist before" ordering constraint.
-/

-- axioms-start
-- No opaque/axiom callee contract is consumed by this specification. The
-- relation-induced constraint computation is modeled DEEPLY as the pure helper
-- `getDependenciesForForeignKey` over the reference-target data (swap setting,
-- referenced application/object name, optional intermediary model), and is
-- validated == the real callee by G-AX. The per-operation constraint assembly
-- is modeled structurally over the field list, so no callee axiom is needed.
-- axioms-end

-- pure-start
/-- One ordering constraint: the target application label, the target object
name, an optional field name, and a flag marking it a "must exist before"
constraint (vs a "must be removed after"). -/
structure Dep where
  appLabel : String
  objectName : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Repr

/-- The reference-target data of a relation field, restricted to what the
constraint computation reads:
* `swappableSetting` — `some name` when the reference targets a swap-configurable
  model (the constraint then names the configuration setting), else `none`;
* `remoteAppLabel` / `remoteObjectName` — the referenced model's application
  label and object name (used when not swap-configurable);
* `through` — `some (app, obj, autoCreated)` when the relation routes through an
  explicit intermediary model, carrying that model's application label, object
  name, and whether it was auto-generated; `none` otherwise. -/
structure FKInfo where
  swappableSetting : Option String
  remoteAppLabel : String
  remoteObjectName : String
  through : Option (String × String × Bool)
deriving DecidableEq

/-- One altered field, restricted to the touched aspects:
* `isRelation` — whether the new field definition is a relation (points at a
  model);
* `fk` — the reference-target data (consulted only when `isRelation`; for a
  non-relation field its contents are irrelevant and never read). -/
structure AlteredField where
  isRelation : Bool
  fk : FKInfo
deriving DecidableEq

/-- One emitted field-alteration operation, restricted to the touched aspect:
* `field` — the altered field this operation alters (its identity);
* `dependencies` — the ordering constraints attached to this operation. The
  operation's other attributes are unchanged by the desired behavior and are not
  modeled. -/
structure AlterFieldOp where
  field : AlteredField
  dependencies : List Dep
deriving DecidableEq

/-- The ordering constraints induced by a relation's reference target. The base
constraint names the referenced model's application + object name, unless the
reference targets a swap-configurable model, in which case it names the
configuration setting. If the relation routes through an explicit, non
auto-generated intermediary model, a second constraint naming that intermediary
is appended. Both constraints carry no field name and are "must exist before"
constraints. -/
def getDependenciesForForeignKey (fk : FKInfo) : List Dep := Id.run do
  let base : Dep :=
    match fk.swappableSetting with
    | some s => { appLabel := "__setting__", objectName := s, fieldName := none, create := true }
    | none   => { appLabel := fk.remoteAppLabel, objectName := fk.remoteObjectName,
                  fieldName := none, create := true }
  let mut deps := [base]
  match fk.through with
  | some (tApp, tObj, autoCreated) =>
      if !autoCreated then
        deps := deps ++ [{ appLabel := tApp, objectName := tObj, fieldName := none, create := true }]
  | none => pure ()
  return deps
-- pure-end

-- post-conditions-start
/-- Exactly one alteration operation is emitted per altered field, in order, and
each operation alters precisely its field and carries: the relation-induced
ordering constraints when that field is a relation, and no constraint otherwise.
The result is element-wise pinned to the input field list — both which field
each operation alters AND the constraints it carries. -/
def problem_spec_generateAlteredFields
    (fields : List AlteredField)
    (result : List AlterFieldOp) : Prop :=
  result = fields.map (fun f =>
    { field := f,
      dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else [] })
-- post-conditions-end

-- impl-start
def implementation_generateAlteredFields
    (fields : List AlteredField) : List AlterFieldOp := Id.run do
  let mut result := []
  for f in fields do
    let mut dependencies := []
    -- A relation alteration must carry the constraints induced by its reference
    -- target, so the referenced model's application is ordered before it.
    if f.isRelation then
      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
    -- Emit the alteration operation for this field carrying the assembled
    -- constraints.
    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
  return result
-- impl-end

-- proof-start
theorem correct_generateAlteredFields :
    ∀ (fields : List AlteredField),
      problem_spec_generateAlteredFields fields
        (implementation_generateAlteredFields fields) := by
  intro fields
  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields
  simp only [Id.run, bind, pure]
  -- Route B: helper over the cleaned `forIn`, generalized over the accumulator.
  have helper : ∀ (init : List AlterFieldOp),
      (forIn (m := Id) fields init (fun f r =>
        (if f.isRelation = true then
            ForInStep.yield (r ++ [({ field := f, dependencies := [] ++ getDependenciesForForeignKey f.fk } : AlterFieldOp)])
          else
            ForInStep.yield (r ++ [({ field := f, dependencies := [] } : AlterFieldOp)]))))
        = init ++ fields.map (fun f =>
            ({ field := f, dependencies := if f.isRelation = true then getDependenciesForForeignKey f.fk else [] } : AlterFieldOp)) := by
    intro init
    induction fields generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, List.nil_append] at ih ⊢
        by_cases h : a.isRelation = true <;>
          simp [h, ih, List.append_assoc]
  rw [helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is EXACT element-wise equality: result = fields.map (fun f => {field := f, dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else []}). This pins field identity, emission order, AND the exact dep list per element — maximally tight; no behaviorally-distinct impl can satisfy it. same_spec=True confirmed for all 7 attacks + positive control.

### ATTACKS (all; cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 prepatch bug (always [] deps): EXIT=1 (unsolved/rewrite error).
- atk_2 boundary/inverted guard (deps on NON-relation): EXIT=1.
- atk_3 control-flow effect (drop isRelation guard, always attach deps): EXIT=1.
- atk_4 order (prepend => reversed emission order): EXIT=1.
- atk_5 subtle-wrong echo (.take 1 => drops the through dep): EXIT=1.
- atk_6 doubled deps (deps ++ deps): EXIT=1.
- atk_7 partial-domain (skip non-relation fields => fewer ops): EXIT=1.
All 7 fail with genuine `error: Tactic rewrite failed / unsolved goals` (NOT syntax errors). No wrong impl closed => no faithful patch materialized/resolve-run needed (per protocol, resolve is only required for a wrong impl whose proof CLOSES with clean axioms; none did).

POSITIVE CONTROL: pos_control.lean (= real Solution.lean impl) EXIT=0; `#print axioms correct_generateAlteredFields` => [propext, Quot.sound] (clean, no sorry).

DISPROOF (rigor beyond carried-tactic failure): disproof_1.lean re-encodes the prepatch impl and proves `¬ ∀ fields, problem_spec ... (impl ...)` via the [rf] counterexample; verifies EXIT=0 with clean axioms [propext, Quot.sound] — establishing the wrong-impl theorem is genuinely FALSE, not merely that the bundle's tactic script happened not to close.

REFINEMENT AUDIT: all 7 legs are R / A-reference / I; NO A-consumed axiom, NO kind-3 ungrounded oracle (RHS computed structurally from input, not echoed from an answer-key). Sole A-reference (getDependenciesForForeignKey ↔ _get_dependencies_for_foreign_key) is G-AX-validated by axiom_check.py, which drives the REAL callee `MigrationAutodetector._get_dependencies_for_foreign_key` over plain-FK/self-FK/swappable(AUTH_USER_MODEL)/auto-created-through/explicit-through fields and asserts equality with the deep model. The A-reference helper lives in the frozen pure region (byte-identical across spec/impl/attacks), so it cannot be gamed by an impl-region edit. Correspondence holds.

VERDICT: SOUND. ≥5 distinct same-spec attacks run; none produced a closing clean-axiom proof, so verify⇒correct is not falsified for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. (1) same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with LeanBackend — spec region byte-identical (only impl/proof differ). (2) Solution.lean compiles (lean_verify exit 0); #print axioms correct_generateAlteredFields = [propext, Quot.sound], no sorryAx — proof genuine. (3) getDependenciesForForeignKey matches base_commit 003bb34b _get_dependencies_for_foreign_key exactly: swappable_setting != None -> ('__setting__', setting, None, True); else (remote app_label, remote object_name, None, True); through-dep appended iff through and not through._meta.auto_created. (4) generate_altered_fields loop: per-iteration dependencies=[], .extend(_get_dependencies_for_foreign_key(new_field)) only inside relation guard (hasattr remote_field and remote_field.model truthiness -> modeled by isRelation:Bool), then add_operation sets _auto_deps=dependencies or []. Lean models this as fields.map (fun f => {field:=f, dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else []}). Unmodeled branches (rename adjustment, m2m<->concrete else, not-null questioner) are legitimately folded into the input abstraction: List AlteredField = fields reaching the AlterField branch carrying the post-rename FK target; they do not touch the dependencies list. Result pinned element-wise (both which field each op alters AND its deps), matching real per-operation emission. No input where modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view, lean flavor) passes clean: no diff markers (L1), no changed gold-patch line reproduced, no patched file/module path (L2), no narration terms (L3). The only distinctive patch-changed symbol is `generate_altered_fields`; no spec-view identifier embeds it (idents are Dep/FKInfo/AlteredField/AlterFieldOp/getDependenciesForForeignKey) and no comment names it (L2/L5, L2/L3 clean). Semantic gold-reconstruction check: the public problem_statement already discloses the exact phenomenon and fix direction ('change field from UUID to FK does not create any dependencies for App2 … the correct solution will be create dependency for App2'). The spec view models precisely that public behavior — a relation-altering operation carries the relation-induced ordering dependencies, a non-relation carries none — computed structurally, not echoed from an answer key. The FK-dependency details (swappable setting / through intermediary) are deep modeling of the UNCHANGED callee _get_dependencies_for_foreign_key (A-reference, G-AX-validated), not disclosure of the one-line gold edit (threading dependencies=dependencies into add_operation). The spec reveals no edit localization (file/function/line) beyond what the problem statement already makes public. Solution.lean compiles under lean_verify.sh (exit 0); same_spec self-check True; region_hashes present. Leakage judged against problem_statement only, not hints_text (hints present but excluded per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
