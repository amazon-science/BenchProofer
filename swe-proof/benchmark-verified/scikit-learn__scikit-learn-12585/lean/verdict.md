# P2 adversarial audit — scikit-learn__scikit-learn-12585

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
@@ -113,7 +113,7 @@
       | .error _ => .error ()
       | .ok es' => .ok (.group kind es')
   | .node isBlueprint exposesConfig tag cfg =>
-      if (!exposesConfig) || isBlueprint then
+      if (!exposesConfig) then
         if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
       else
         if isBlueprint then .error ()
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
       | .ok es' => .ok (.group kind es')
   | .node isBlueprint exposesConfig tag cfg =>
       if (!exposesConfig) || isBlueprint then
-        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
+        .ok (.node isBlueprint exposesConfig tag cfg)
       else
         if isBlueprint then .error ()
         else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
 def implementation_duplicate (safe : Bool) : PyVal → Except Unit PyVal
   | .group kind es =>
       match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with
-      | .error _ => .error ()
+      | .error _ => .ok (.group kind [])
       | .ok es' => .ok (.group kind es')
   | .node isBlueprint exposesConfig tag cfg =>
       if (!exposesConfig) || isBlueprint then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
       | .error _ => .error ()
       | .ok es' => .ok (.group kind es')
   | .node isBlueprint exposesConfig tag cfg =>
-      if (!exposesConfig) || isBlueprint then
+      if exposesConfig && (!isBlueprint) then
         if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
       else
         if isBlueprint then .error ()
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -113,7 +113,7 @@
       | .error _ => .error ()
       | .ok es' => .ok (.group kind es')
   | .node isBlueprint exposesConfig tag cfg =>
-      if (!exposesConfig) || isBlueprint then
+      if configUnusable isBlueprint exposesConfig then
         if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
       else
         if isBlueprint then .error ()
@@ -189,23 +189,21 @@
   · -- case3: node, configUnusable, safe = true
     rename_i hguard
     conv_rhs => rw [reproduce]
-    simp only [configUnusable, hguard, if_true]
+    simp only [hguard, if_true]
   · -- case4: node, configUnusable, safe = false
     rename_i hguard hsafe
     conv_rhs => rw [reproduce]
-    simp only [configUnusable, hguard, if_true]
+    simp only [hguard, if_true]
     rw [if_neg hsafe]
   · -- case5: node, isBlueprint = true, contradictory guard
     rename_i hguard
-    simp at hguard
+    simp [configUnusable] at hguard
   · -- case6: node, realized config, mapM = error
     rename_i hguard hib a hmap ih
     conv_rhs => rw [reproduce]
-    simp only [configUnusable]
     rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]
   · -- case7: node, realized config, mapM = ok
     rename_i hguard hib cfg' hmap ih
     conv_rhs => rw [reproduce]
-    simp only [configUnusable]
     rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -118,7 +118,7 @@
       else
         if isBlueprint then .error ()
         else
-          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with
+          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate safe kv.2).map (fun v => (kv.1, v))) with
           | .error _ => .error ()
           | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
 termination_by v => sizeOf v
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,7 +120,7 @@
         else
           match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with
           | .error _ => .error ()
-          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
+          | .ok cfg' => .ok (.node isBlueprint exposesConfig (tag + 1) cfg')
 termination_by v => sizeOf v
 decreasing_by
   · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Faithfully duplicating a structured value without copying any attached data.

The value space has three observable shapes:

  * a homogeneous **group** (an ordered collection) — duplicated by duplicating
    every element in place and rebuilding a group of the same kind;
  * a configurable **node** — a value that *exposes a configuration interface*
    (its keyed configuration can be read back) and is rebuilt from a fresh copy
    of that configuration;
  * everything else — an opaque leaf that exposes no configuration interface.

A node additionally carries a flag, `isBlueprint`, distinguishing a *blueprint*
(a template/recipe value) from a fully realized value. A blueprint nominally
advertises the configuration interface, yet that interface is bound to realized
values and cannot actually be queried on a blueprint; querying it on a blueprint
is invalid.

Duplication is parameterized by a `safe` flag. For any value that does NOT have
a usable configuration interface — because it exposes none at all, OR because it
is a blueprint (whose advertised interface is not usable) — duplication must NOT
attempt to read a configuration: when `safe = false` it returns the value
unchanged (a leaf duplicate that shares identity), and when `safe = true` it
reports a failure (the value is not a configurable node). Only a realized,
configuration-exposing node has its configuration read and each configuration
entry duplicated (unsafely) before the node is rebuilt.

The behavior to pin: the choice of whether to read a value's configuration
depends on whether that configuration is actually usable, NOT merely on whether
the value advertises the interface. A blueprint advertises it but is handled by
the no-configuration path, exactly like a leaf.
-/

-- axioms-start
-- No unchanged outside callee contributes a property the specification consumes.
-- Every routing decision — whether a value's configuration interface is usable,
-- and the consequent branch — is modeled structurally over the value's own
-- observable flags (`exposesConfig`, `isBlueprint`), and the rebuild is the
-- structural reconstruction `reproduce`. So no `opaque`/`axiom` callee is needed.
-- axioms-end

-- pure-start
/-- A structured value, restricted to the touched shape.

* `group kind elems` — an ordered collection of sub-values; `kind` records which
  collection variety it is (only equality of kinds is observed).
* `node isBlueprint exposesConfig tag config` — a value that may expose a keyed
  configuration. `exposesConfig` is whether the configuration-query interface is
  advertised; `isBlueprint` marks a template value whose advertised interface is
  not actually usable; `tag` is the value's class identity; `config` is the keyed
  configuration (each entry a `(key, sub-value)` pair). A leaf is a node with
  `exposesConfig = false`. -/
inductive PyVal where
  | group (kind : Nat) (elems : List PyVal)
  | node (isBlueprint : Bool) (exposesConfig : Bool) (tag : Nat) (config : List (Nat × PyVal))

/-- A value's configuration interface is usable for duplication iff the value
exposes the interface AND is not a blueprint. The no-configuration path is taken
in the complementary case: the value exposes nothing, OR it is a blueprint. -/
def configUnusable (isBlueprint exposesConfig : Bool) : Bool :=
  (!exposesConfig) || isBlueprint

/-- Structural duplication.

* A group is duplicated element-wise, preserving its kind and element order; if
  any element fails, the whole duplication fails.
* A value whose configuration interface is unusable (`configUnusable`) is on the
  no-configuration path: returned unchanged when `safe = false`, reported as a
  failure when `safe = true`.
* A realized, configuration-exposing node has each configuration entry
  duplicated (unsafely) and is then rebuilt with the duplicated configuration. -/
def reproduce (safe : Bool) : PyVal → Except Unit PyVal
  | .group kind es =>
      match es.attach.mapM (fun ⟨e, _⟩ => reproduce safe e) with
      | .error _ => .error ()
      | .ok es' => .ok (.group kind es')
  | .node isBlueprint exposesConfig tag cfg =>
      if configUnusable isBlueprint exposesConfig then
        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
      else
        -- Reached only for a realized configuration-exposing node; querying a
        -- blueprint's advertised interface here would be invalid.
        if isBlueprint then .error ()
        else
          match cfg.attach.mapM (fun ⟨kv, _⟩ => (reproduce false kv.2).map (fun v => (kv.1, v))) with
          | .error _ => .error ()
          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
termination_by v => sizeOf v
decreasing_by
  · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
    simp_wf; omega
  · have h1 := List.sizeOf_lt_of_mem (by assumption : kv ∈ cfg)
    have h2 : sizeOf kv.2 < sizeOf kv := by cases kv; simp_wf
    simp_wf; omega
-- pure-end

-- post-conditions-start
/-- The duplicate is exactly the structural reproduction of the input under the
`safe` flag: groups duplicated element-wise, configuration-unusable values routed
to the no-configuration path (unchanged when unsafe, failure when safe), and only
realized configuration-exposing nodes rebuilt from a duplicated configuration. -/
def problem_spec_duplicate (safe : Bool) (v : PyVal) (result : Except Unit PyVal) : Prop :=
  result = reproduce safe v
-- post-conditions-end

-- impl-start
def implementation_duplicate (safe : Bool) : PyVal → Except Unit PyVal
  | .group kind es =>
      match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with
      | .error _ => .error ()
      | .ok es' => .ok (.group kind es')
  | .node isBlueprint exposesConfig tag cfg =>
      if (!exposesConfig) || isBlueprint then
        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
      else
        if isBlueprint then .error ()
        else
          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with
          | .error _ => .error ()
          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
termination_by v => sizeOf v
decreasing_by
  · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
    simp_wf; omega
  · have h1 := List.sizeOf_lt_of_mem (by assumption : kv ∈ cfg)
    have h2 : sizeOf kv.2 < sizeOf kv := by cases kv; simp_wf
    simp_wf; omega
-- impl-end

-- proof-start
-- @ns:configUnusable_eq_inline-start
-- @decl:configUnusable_eq_inline-start
theorem configUnusable_eq_inline (isBlueprint exposesConfig : Bool) :
    configUnusable isBlueprint exposesConfig = ((!exposesConfig) || isBlueprint) := rfl
-- @decl:configUnusable_eq_inline-end
-- @ns:configUnusable_eq_inline-end

-- @ns:attach_mapM_fun_eq-start
-- @decl:attach_mapM_fun_eq-start
theorem attach_mapM_fun_eq (s : Bool) (l : List PyVal)
    (h : ∀ x, x ∈ l → implementation_duplicate s x = reproduce s x) :
    l.attach.mapM (fun (p : {x // x ∈ l}) => implementation_duplicate s p.1)
      = l.attach.mapM (fun (p : {x // x ∈ l}) => reproduce s p.1) := by
  have hfun : (fun (p : {x // x ∈ l}) => implementation_duplicate s p.1)
      = (fun (p : {x // x ∈ l}) => reproduce s p.1) := by
    funext p
    exact h p.1 p.2
  rw [hfun]
-- @decl:attach_mapM_fun_eq-end
-- @ns:attach_mapM_fun_eq-end

-- @ns:attach_mapM_fun_eq_config-start
-- @decl:attach_mapM_fun_eq_config-start
theorem attach_mapM_fun_eq_config (l : List (Nat × PyVal))
    (h : ∀ x, x ∈ l → implementation_duplicate false x.2 = reproduce false x.2) :
    l.attach.mapM (fun (p : {x // x ∈ l}) =>
        (implementation_duplicate false p.1.2).map (fun v => (p.1.1, v)))
      = l.attach.mapM (fun (p : {x // x ∈ l}) =>
        (reproduce false p.1.2).map (fun v => (p.1.1, v))) := by
  have hfun :
      (fun (p : {x // x ∈ l}) =>
        (implementation_duplicate false p.1.2).map (fun v => (p.1.1, v)))
        = (fun (p : {x // x ∈ l}) =>
        (reproduce false p.1.2).map (fun v => (p.1.1, v))) := by
    funext p
    rw [h p.1 p.2]
  rw [hfun]
-- @decl:attach_mapM_fun_eq_config-end
-- @ns:attach_mapM_fun_eq_config-end


theorem correct_duplicate :
    ∀ (safe : Bool) (v : PyVal),
      problem_spec_duplicate safe v (implementation_duplicate safe v) := by
  intro safe v
  simp only [problem_spec_duplicate]
  fun_induction implementation_duplicate safe v
  · -- case1: group, mapM = error
    rename_i hmap ih
    conv_rhs => rw [reproduce]
    rw [← attach_mapM_fun_eq _ _ ih, hmap]
  · -- case2: group, mapM = ok
    rename_i hmap ih
    conv_rhs => rw [reproduce]
    rw [← attach_mapM_fun_eq _ _ ih, hmap]
  · -- case3: node, configUnusable, safe = true
    rename_i hguard
    conv_rhs => rw [reproduce]
    simp only [configUnusable, hguard, if_true]
  · -- case4: node, configUnusable, safe = false
    rename_i hguard hsafe
    conv_rhs => rw [reproduce]
    simp only [configUnusable, hguard, if_true]
    rw [if_neg hsafe]
  · -- case5: node, isBlueprint = true, contradictory guard
    rename_i hguard
    simp at hguard
  · -- case6: node, realized config, mapM = error
    rename_i hguard hib a hmap ih
    conv_rhs => rw [reproduce]
    simp only [configUnusable]
    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]
  · -- case7: node, realized config, mapM = ok
    rename_i hguard hib cfg' hmap ih
    conv_rhs => rw [reproduce]
    simp only [configUnusable]
    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND — verify⇒correct holds; no falsification found. Spec is exact pointwise functional equality: problem_spec_duplicate safe v result := (result = reproduce safe v), with `reproduce` frozen byte-identical (same_spec=True for all 7 attacks). PROTOCOL RESULTS (project root; verify cmd `bash scripts/lean_verify.sh <file>`):

Positive control pos_control.lean: exit 0; `#print axioms correct_duplicate` = [propext, Classical.choice, Quot.sound] (clean).

6 BEHAVIORALLY-WRONG impls, all fail to close with GENUINE unsolved goals (impl provably differs from reproduce), all exit 1:
- atk_1 = PREPATCH bug (drop `|| isBlueprint`, i.e. guard `if (!exposesConfig)` only) — reproduces pre-fix `not hasattr(...,'get_params')`. exit 1, 3× unsolved goals. => prepatch_reproduced=True (bug is caught: the carried gold proof cannot close against the buggy impl).
- atk_2 = ignore `safe` on no-config branch (always .ok unchanged): exit 1, unsolved goals.
- atk_3 = control-flow-effect (group element error salvaged to `.ok (.group kind [])`): exit 1, unsolved goals.
- atk_4 = reversed guard sense (`exposesConfig && !isBlueprint`): exit 1, 3× unsolved goals.
- atk_6 = boundary/flag-dep (recurse config with `safe` instead of `false`): exit 1, unsolved goals.
- atk_7 = structural-corruption/ungrounded rebuild (`.node ... (tag+1) cfg'`): exit 1, unsolved goals.

1 BEHAVIORAL ECHO closes with clean axioms:
- atk_5 = guard via `configUnusable isBlueprint exposesConfig` (definitionally = inline `(!exposesConfig)||isBlueprint`, proven by configUnusable_eq_inline := rfl). Proof re-adapted (drop premature `configUnusable` unfolds in case3/4/6/7; `simp [configUnusable] at hguard` in case5). Verifies exit 0; `#print axioms correct_duplicate` = [propext, Classical.choice, Quot.sound] (clean, identical to control). Behaviorally identical to gold => faithful refined patch IS the gold patch. MANDATORY resolve EXECUTED: swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-12585', <gold patch>, timeout=2400, retries=1) => COMPLETED=True, RESOLVED=True, NOTE='resolved', ATTEMPTS=1 (Docker via `docker`). So the only closing impl also resolves — consistent, no break.

REFINEMENT AUDIT: Solution.lean has NO `axiom`/`opaque` declarations; meta.json axioms=[], deep_model_references=[], conf_skip=False, modeled_functions=['duplicate']. refinement.md legs 1-9 are all R/I (no A-consumed, no A-reference, no kind-3-inexpressible). copy.deepcopy modeled as identity no-op of the no-config branch (op 6) validated by G-CONF, not axiomatized — correct per SPEC_GUIDE §3. No A-leg correspondence to attack. Nothing falsifiable on the A legs.

CONCLUSION: every same-spec impl whose correct_duplicate closes with clean axioms is behaviorally equal to reproduce (spec is exact functional equality); the one such impl found (atk_5) has a materialized faithful patch that RESOLVES under the official harness. No verifying-but-non-resolving impl exists. SOUND.

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
Faithfully duplicating a structured value without copying any attached data.

The value space has three observable shapes:

  * a homogeneous **group** (an ordered collection) — duplicated by duplicating
    every element in place and rebuilding a group of the same kind;
  * a configurable **node** — a value that *exposes a configuration interface*
    (its keyed configuration can be read back) and is rebuilt from a fresh copy
    of that configuration;
  * everything else — an opaque leaf that exposes no configuration interface.

A node additionally carries a flag, `isBlueprint`, distinguishing a *blueprint*
(a template/recipe value) from a fully realized value. A blueprint nominally
advertises the configuration interface, yet that interface is bound to realized
values and cannot actually be queried on a blueprint; querying it on a blueprint
is invalid.

Duplication is parameterized by a `safe` flag. For any value that does NOT have
a usable configuration interface — because it exposes none at all, OR because it
is a blueprint (whose advertised interface is not usable) — duplication must NOT
attempt to read a configuration: when `safe = false` it returns the value
unchanged (a leaf duplicate that shares identity), and when `safe = true` it
reports a failure (the value is not a configurable node). Only a realized,
configuration-exposing node has its configuration read and each configuration
entry duplicated (unsafely) before the node is rebuilt.

The behavior to pin: the choice of whether to read a value's configuration
depends on whether that configuration is actually usable, NOT merely on whether
the value advertises the interface. A blueprint advertises it but is handled by
the no-configuration path, exactly like a leaf.
-/

-- axioms-start
-- No unchanged outside callee contributes a property the specification consumes.
-- Every routing decision — whether a value's configuration interface is usable,
-- and the consequent branch — is modeled structurally over the value's own
-- observable flags (`exposesConfig`, `isBlueprint`), and the rebuild is the
-- structural reconstruction `reproduce`. So no `opaque`/`axiom` callee is needed.
-- axioms-end

-- pure-start
/-- A structured value, restricted to the touched shape.

* `group kind elems` — an ordered collection of sub-values; `kind` records which
  collection variety it is (only equality of kinds is observed).
* `node isBlueprint exposesConfig tag config` — a value that may expose a keyed
  configuration. `exposesConfig` is whether the configuration-query interface is
  advertised; `isBlueprint` marks a template value whose advertised interface is
  not actually usable; `tag` is the value's class identity; `config` is the keyed
  configuration (each entry a `(key, sub-value)` pair). A leaf is a node with
  `exposesConfig = false`. -/
inductive PyVal where
  | group (kind : Nat) (elems : List PyVal)
  | node (isBlueprint : Bool) (exposesConfig : Bool) (tag : Nat) (config : List (Nat × PyVal))

/-- A value's configuration interface is usable for duplication iff the value
exposes the interface AND is not a blueprint. The no-configuration path is taken
in the complementary case: the value exposes nothing, OR it is a blueprint. -/
def configUnusable (isBlueprint exposesConfig : Bool) : Bool :=
  (!exposesConfig) || isBlueprint

/-- Structural duplication.

* A group is duplicated element-wise, preserving its kind and element order; if
  any element fails, the whole duplication fails.
* A value whose configuration interface is unusable (`configUnusable`) is on the
  no-configuration path: returned unchanged when `safe = false`, reported as a
  failure when `safe = true`.
* A realized, configuration-exposing node has each configuration entry
  duplicated (unsafely) and is then rebuilt with the duplicated configuration. -/
def reproduce (safe : Bool) : PyVal → Except Unit PyVal
  | .group kind es =>
      match es.attach.mapM (fun ⟨e, _⟩ => reproduce safe e) with
      | .error _ => .error ()
      | .ok es' => .ok (.group kind es')
  | .node isBlueprint exposesConfig tag cfg =>
      if configUnusable isBlueprint exposesConfig then
        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
      else
        -- Reached only for a realized configuration-exposing node; querying a
        -- blueprint's advertised interface here would be invalid.
        if isBlueprint then .error ()
        else
          match cfg.attach.mapM (fun ⟨kv, _⟩ => (reproduce false kv.2).map (fun v => (kv.1, v))) with
          | .error _ => .error ()
          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
termination_by v => sizeOf v
decreasing_by
  · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
    simp_wf; omega
  · have h1 := List.sizeOf_lt_of_mem (by assumption : kv ∈ cfg)
    have h2 : sizeOf kv.2 < sizeOf kv := by cases kv; simp_wf
    simp_wf; omega
-- pure-end

-- post-conditions-start
/-- The duplicate is exactly the structural reproduction of the input under the
`safe` flag: groups duplicated element-wise, configuration-unusable values routed
to the no-configuration path (unchanged when unsafe, failure when safe), and only
realized configuration-exposing nodes rebuilt from a duplicated configuration. -/
def problem_spec_duplicate (safe : Bool) (v : PyVal) (result : Except Unit PyVal) : Prop :=
  result = reproduce safe v
-- post-conditions-end

-- impl-start
def implementation_duplicate (safe : Bool) : PyVal → Except Unit PyVal
  | .group kind es =>
      match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with
      | .error _ => .error ()
      | .ok es' => .ok (.group kind es')
  | .node isBlueprint exposesConfig tag cfg =>
      if (!exposesConfig) || isBlueprint then
        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
      else
        if isBlueprint then .error ()
        else
          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with
          | .error _ => .error ()
          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
termination_by v => sizeOf v
decreasing_by
  · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
    simp_wf; omega
  · have h1 := List.sizeOf_lt_of_mem (by assumption : kv ∈ cfg)
    have h2 : sizeOf kv.2 < sizeOf kv := by cases kv; simp_wf
    simp_wf; omega
-- impl-end

-- proof-start
-- @ns:configUnusable_eq_inline-start
-- @decl:configUnusable_eq_inline-start
theorem configUnusable_eq_inline (isBlueprint exposesConfig : Bool) :
    configUnusable isBlueprint exposesConfig = ((!exposesConfig) || isBlueprint) := rfl
-- @decl:configUnusable_eq_inline-end
-- @ns:configUnusable_eq_inline-end

-- @ns:attach_mapM_fun_eq-start
-- @decl:attach_mapM_fun_eq-start
theorem attach_mapM_fun_eq (s : Bool) (l : List PyVal)
    (h : ∀ x, x ∈ l → implementation_duplicate s x = reproduce s x) :
    l.attach.mapM (fun (p : {x // x ∈ l}) => implementation_duplicate s p.1)
      = l.attach.mapM (fun (p : {x // x ∈ l}) => reproduce s p.1) := by
  have hfun : (fun (p : {x // x ∈ l}) => implementation_duplicate s p.1)
      = (fun (p : {x // x ∈ l}) => reproduce s p.1) := by
    funext p
    exact h p.1 p.2
  rw [hfun]
-- @decl:attach_mapM_fun_eq-end
-- @ns:attach_mapM_fun_eq-end

-- @ns:attach_mapM_fun_eq_config-start
-- @decl:attach_mapM_fun_eq_config-start
theorem attach_mapM_fun_eq_config (l : List (Nat × PyVal))
    (h : ∀ x, x ∈ l → implementation_duplicate false x.2 = reproduce false x.2) :
    l.attach.mapM (fun (p : {x // x ∈ l}) =>
        (implementation_duplicate false p.1.2).map (fun v => (p.1.1, v)))
      = l.attach.mapM (fun (p : {x // x ∈ l}) =>
        (reproduce false p.1.2).map (fun v => (p.1.1, v))) := by
  have hfun :
      (fun (p : {x // x ∈ l}) =>
        (implementation_duplicate false p.1.2).map (fun v => (p.1.1, v)))
        = (fun (p : {x // x ∈ l}) =>
        (reproduce false p.1.2).map (fun v => (p.1.1, v))) := by
    funext p
    rw [h p.1 p.2]
  rw [hfun]
-- @decl:attach_mapM_fun_eq_config-end
-- @ns:attach_mapM_fun_eq_config-end


theorem correct_duplicate :
    ∀ (safe : Bool) (v : PyVal),
      problem_spec_duplicate safe v (implementation_duplicate safe v) := by
  intro safe v
  simp only [problem_spec_duplicate]
  fun_induction implementation_duplicate safe v
  · -- case1: group, mapM = error
    rename_i hmap ih
    conv_rhs => rw [reproduce]
    rw [← attach_mapM_fun_eq _ _ ih, hmap]
  · -- case2: group, mapM = ok
    rename_i hmap ih
    conv_rhs => rw [reproduce]
    rw [← attach_mapM_fun_eq _ _ ih, hmap]
  · -- case3: node, configUnusable, safe = true
    rename_i hguard
    conv_rhs => rw [reproduce]
    simp only [configUnusable, hguard, if_true]
  · -- case4: node, configUnusable, safe = false
    rename_i hguard hsafe
    conv_rhs => rw [reproduce]
    simp only [configUnusable, hguard, if_true]
    rw [if_neg hsafe]
  · -- case5: node, isBlueprint = true, contradictory guard
    rename_i hguard
    simp at hguard
  · -- case6: node, realized config, mapM = error
    rename_i hguard hib a hmap ih
    conv_rhs => rw [reproduce]
    simp only [configUnusable]
    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]
  · -- case7: node, realized config, mapM = ok
    rename_i hguard hib cfg' hmap ih
    conv_rhs => rw [reproduce]
    simp only [configUnusable]
    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND — verify⇒correct holds; no falsification found. Spec is exact pointwise functional equality: problem_spec_duplicate safe v result := (result = reproduce safe v), with `reproduce` frozen byte-identical (same_spec=True for all 7 attacks). PROTOCOL RESULTS (project root; verify cmd `bash scripts/lean_verify.sh <file>`):

Positive control pos_control.lean: exit 0; `#print axioms correct_duplicate` = [propext, Classical.choice, Quot.sound] (clean).

6 BEHAVIORALLY-WRONG impls, all fail to close with GENUINE unsolved goals (impl provably differs from reproduce), all exit 1:
- atk_1 = PREPATCH bug (drop `|| isBlueprint`, i.e. guard `if (!exposesConfig)` only) — reproduces pre-fix `not hasattr(...,'get_params')`. exit 1, 3× unsolved goals. => prepatch_reproduced=True (bug is caught: the carried gold proof cannot close against the buggy impl).
- atk_2 = ignore `safe` on no-config branch (always .ok unchanged): exit 1, unsolved goals.
- atk_3 = control-flow-effect (group element error salvaged to `.ok (.group kind [])`): exit 1, unsolved goals.
- atk_4 = reversed guard sense (`exposesConfig && !isBlueprint`): exit 1, 3× unsolved goals.
- atk_6 = boundary/flag-dep (recurse config with `safe` instead of `false`): exit 1, unsolved goals.
- atk_7 = structural-corruption/ungrounded rebuild (`.node ... (tag+1) cfg'`): exit 1, unsolved goals.

1 BEHAVIORAL ECHO closes with clean axioms:
- atk_5 = guard via `configUnusable isBlueprint exposesConfig` (definitionally = inline `(!exposesConfig)||isBlueprint`, proven by configUnusable_eq_inline := rfl). Proof re-adapted (drop premature `configUnusable` unfolds in case3/4/6/7; `simp [configUnusable] at hguard` in case5). Verifies exit 0; `#print axioms correct_duplicate` = [propext, Classical.choice, Quot.sound] (clean, identical to control). Behaviorally identical to gold => faithful refined patch IS the gold patch. MANDATORY resolve EXECUTED: swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-12585', <gold patch>, timeout=2400, retries=1) => COMPLETED=True, RESOLVED=True, NOTE='resolved', ATTEMPTS=1 (Docker via `docker`). So the only closing impl also resolves — consistent, no break.

REFINEMENT AUDIT: Solution.lean has NO `axiom`/`opaque` declarations; meta.json axioms=[], deep_model_references=[], conf_skip=False, modeled_functions=['duplicate']. refinement.md legs 1-9 are all R/I (no A-consumed, no A-reference, no kind-3-inexpressible). copy.deepcopy modeled as identity no-op of the no-config branch (op 6) validated by G-CONF, not axiomatized — correct per SPEC_GUIDE §3. No A-leg correspondence to attack. Nothing falsifiable on the A legs.

CONCLUSION: every same-spec impl whose correct_duplicate closes with clean axioms is behaviorally equal to reproduce (spec is exact functional equality); the one such impl found (atk_5) has a materialized faithful patch that RESOLVES under the official harness. No verifying-but-non-resolving impl exists. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function clone(estimator, safe=True) in sklearn/base.py, verified against real source at base_commit bfc4a566. Solution.lean compiles clean (lean_verify.sh exit 0, no sorry); #print axioms correct_duplicate = [propext, Classical.choice, Quot.sound] — no sorryAx, genuine proof. Spec region byte-identical: same_spec(Solution, Solution_prepatch, LeanBackend.language) = True; spec is problem_spec_duplicate := (result = reproduce safe v).

Branch-by-branch faithfulness of reproduce vs real clone:
- group: es.attach.mapM (reproduce safe) order-preserving + error-propagating == estimator_type([clone(e,safe=safe) for e in estimator]); empty group -> .ok. Faithful.
- guard configUnusable = (!exposesConfig) || isBlueprint == post-patch guard `not hasattr(estimator,'get_params') or isinstance(estimator,type)`. safe=true -> .error() (TypeError); safe=false -> .ok unchanged. deepcopy modeled as identity is sound because for values reaching this branch under safe=False (leaves and class objects) deepcopy is observationally identical to the input, and PyVal observes only flags/tag/config. Faithful.
- realized-node rebuild: each config entry cloned with safe=false, node rebuilt tag-preserved == get_params(deep=False)/clone(param,False)/klass(**params). Faithful. Inner `if isBlueprint then .error()` is dead under configUnusable=false (isBlueprint => configUnusable=true); shape-only, no observable divergence.
- All four realizable (isBlueprint, exposesConfig) combos handled per mapping table; F2P case clone(MyEstimator(empty=MyEstimator)) returns .ok in Solution and .error in prepatch, matching the real fix.

Searched for a diverging input. The only unmodeled real-callee behavior is the post-construction sanity-check RuntimeError loop (base.py lines 64-73). In principle this makes the spec slightly 'too strong' (asserts .ok where a misbehaving constructor could raise), but NO PyVal input can witness the divergence: PyVal carries no field encoding a param-dropping/mutating constructor, so no input in the model's domain maps to that scenario. The loop is also orthogonal to the patched branch and the F2P test (well-behaved estimators round-trip params unchanged), and it is explicitly declared out-of-scope in mapping.md under the touched-fields discipline. This is a legitimate, documented faithful abstraction rather than spec drift. No diverging input exists within the modeled domain. Verdict: FAITHFUL (no defect).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction assessment for scikit-learn__scikit-learn-12585 (lean).

Spec-region integrity: same_spec(Solution.lean, Solution_prepatch.lean) = True under LeanBackend.language markers. The spec view (docstring + PyVal type + configUnusable + reproduce + problem_spec_duplicate) is byte-identical across patched/prepatch; both impl-start..impl-end and proof-start..proof-end are elided in the spec view, so the differentiating guard change ((!exposesConfig) vs (!exposesConfig)||isBlueprint) lives ONLY in the elided impl, not the spec view. meta G-LEAK recorded 'spec view clean' (no failures).

Beyond-problem_statement test: the gold patch is exactly `elif not hasattr(estimator,'get_params') or isinstance(estimator,type):`. The PUBLIC problem_statement already discloses this verbatim under 'Possible fix': "Change base.py, line 51 to: elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):" plus the exact reproducer clone(StandardScaler(with_mean=StandardScaler)) and the TypeError traceback. Thus the entire one-line gold edit is public knowledge.

The spec view encodes the correct post-fix routing abstractly (configUnusable = (!exposesConfig)||isBlueprint, with exposesConfig<->hasattr get_params, isBlueprint<->isinstance(_,type)). This restates the fix that the problem_statement already hands over literally; it reveals nothing about the gold edit that a reader of the public problem_statement does not already have. No spec-view line exposes gold-patch specifics (file/line delta, prepatch weakening, or a solution the problem_statement withholds). Any correct spec must encode the correct branch; the 'beyond problem_statement' bar is not crossed here because the problem_statement itself specifies the exact fix.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
