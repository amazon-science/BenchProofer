# P2 adversarial audit — django__django-15380

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,15 +77,9 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
-    let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
-    let oldState := lookupState priorModels (app, priorName)
-    let newState := lookupState currentModels (app, curModelName)
-    return (oldState, newState)
+
+    return (lookupState priorModels (app, renameLookup renamed (app, curModelName)),
+            lookupState currentModels (app, curModelName))
     -- impl-end
 
 prove_correct frameRenamedField by
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,14 +77,10 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
+
+    let newState := lookupState currentModels (app, curModelName)
     let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
     let oldState := lookupState priorModels (app, priorName)
-    let newState := lookupState currentModels (app, curModelName)
     return (oldState, newState)
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,14 +77,10 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
+
     let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
     let oldState := lookupState priorModels (app, priorName)
-    let newState := lookupState currentModels (app, curModelName)
+    let newState := lookupState currentModels (app, priorName)
     return (oldState, newState)
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,15 +77,11 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
+
     let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
     let oldState := lookupState priorModels (app, priorName)
     let newState := lookupState currentModels (app, curModelName)
-    return (oldState, newState)
+    return (newState, oldState)
     -- impl-end
 
 prove_correct frameRenamedField by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,13 +77,8 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
-    let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
-    let oldState := lookupState priorModels (app, priorName)
+
+    let oldState := lookupState priorModels (app, curModelName)
     let newState := lookupState currentModels (app, curModelName)
     return (oldState, newState)
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,14 +77,10 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
+
     let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
     let oldState := lookupState priorModels (app, priorName)
-    let newState := lookupState currentModels (app, curModelName)
+    let newState := lookupState priorModels (app, curModelName)
     return (oldState, newState)
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,14 +77,12 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
+
     let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
     let oldState := lookupState priorModels (app, priorName)
-    let newState := lookupState currentModels (app, curModelName)
+    let newState := match renamed.find? (fun kv => keyEq kv.1 (app, curModelName)) with
+      | some _ => lookupState priorModels (app, curModelName)
+      | none   => lookupState currentModels (app, curModelName)
     return (oldState, newState)
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axiom. The only foreign computation — resolving a model entry out
@@ -77,14 +77,12 @@
   ensures out.2 = lookupState currentModels (app, curModelName)
   do
     -- impl-start
-    -- The model's prior name: its rename source, or its current name if it was
-    -- not renamed.
+
     let priorName := renameLookup renamed (app, curModelName)
-    -- The prior-state entry is keyed by the prior name; the current-state entry
-    -- is keyed by the current name (the current-state map is keyed by current
-    -- names).
     let oldState := lookupState priorModels (app, priorName)
     let newState := lookupState currentModels (app, curModelName)
+    if app == "" then
+      return (none, none)
     return (oldState, newState)
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign computation — resolving a model entry out
   of a name-keyed state map, and resolving a model's prior name through the
   rename record — is modeled DEEPLY by `lookupState` / `renameLookup` (pure
   region). The state maps and the rename record are association lists; the
   lookups are the per-key accesses the routine performs. Those deep models are
   validated against the real Django state maps and rename record by
   axiom_check.py (G-AX, an A-reference; mapping.md §3.1), not consumed as an
   axiom. -/
-- axioms-end

-- pure-start
/- A model entry, identified by its object name. Only its identity is observed
   (the routine selects WHICH entry to read), so the carrier records the name. -/
structure ModelEntry where
  name : String
deriving DecidableEq, Inhabited, Repr

/- Two keys (app label, model name) are equal componentwise. -/
def keyEq (a b : String × String) : Bool := a.1 == b.1 && a.2 == b.2

/- Resolve a model entry out of a name-keyed state map: the entry stored under
   the given (app label, model name), or none when no such key is present
   (the empty result that, in the repository, manifests as a missing key). -/
def lookupState (m : List ((String × String) × ModelEntry))
    (key : String × String) : Option ModelEntry :=
  (m.find? (fun kv => keyEq kv.1 key)).map Prod.snd

/- Resolve a model's name in the prior state from the rename record: when the
   model was renamed, the record maps its current key to its prior name; when it
   was not, its prior name equals its current name. -/
def renameLookup (renamed : List ((String × String) × String))
    (key : String × String) : String :=
  match renamed.find? (fun kv => keyEq kv.1 key) with
  | some kv => kv.2
  | none    => key.2
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the maps and names are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve the prior-state and current-state model entries a field operation
   acts on, for a model whose current name is `curModelName` in app `app`.

   Desired behavior: the model's PRIOR name is its rename source recorded in
   `renamed` (or its current name when it was not renamed). The PRIOR-state entry
   is the one stored in the prior-state map under that prior name. The
   CURRENT-state entry is the one stored in the current-state map under the
   model's CURRENT name — the current-state map is keyed by current names, so a
   model whose name changed is found there under its new name, independently of
   its prior name.

   `priorModels` / `currentModels` are the prior- and current-state model maps;
   `renamed` is the rename record; all three and both names are read-only inputs
   (not `mut`): the routine only reads them (directive 5). -/
method frameRenamedField
    (priorModels : List ((String × String) × ModelEntry))
    (currentModels : List ((String × String) × ModelEntry))
    (renamed : List ((String × String) × String))
    (app : String)
    (curModelName : String)
    return (out : Option ModelEntry × Option ModelEntry)
  ensures out.1 = lookupState priorModels (app, renameLookup renamed (app, curModelName))
  ensures out.2 = lookupState currentModels (app, curModelName)
  do
    -- impl-start
    -- The model's prior name: its rename source, or its current name if it was
    -- not renamed.
    let priorName := renameLookup renamed (app, curModelName)
    -- The prior-state entry is keyed by the prior name; the current-state entry
    -- is keyed by the current name (the current-state map is keyed by current
    -- names).
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState currentModels (app, curModelName)
    return (oldState, newState)
    -- impl-end

prove_correct frameRenamedField by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: frameRenamedField carries TWO equality postconditions that FULLY pin both output components: `out.1 = lookupState priorModels (app, renameLookup renamed (app, curModelName))` and `out.2 = lookupState currentModels (app, curModelName)`. This is a maximally tight functional spec — any verifying impl must produce the exact gold output pair. Impl region byte-identical outside markers for every attack (same_spec=True confirmed via swebench_unified.markers.same_spec for all 8 attacks + positive control).

### VERIFY RESULTS (scripts/lean_verify.sh, 300s cap; run concurrently ≤4):
- atk_1 (ungrounded-oracle ECHO: return postcondition RHS literally): EXIT 0 VERIFIES. Computes gold values.
- atk_2 (reordered lets, same values): EXIT 0 VERIFIES. Computes gold values.
- atk_3 (PREPATCH BUG: current-state entry keyed by prior name): EXIT 1 FAILS (unsolved goal on out.2 clause — same as bundle Solution_prepatch.lean). prepatch reproduced.
- atk_4 (swapped returned pair): EXIT 1 FAILS.
- atk_5 (out.1 ignores rename record, uses current name for prior lookup): EXIT 1 FAILS.
- atk_6 (out.2 reads PRIOR-state map instead of current-state map): EXIT 1 FAILS.
- atk_7 (partial-domain: wrong only when a rename record exists for the key): EXIT 1 FAILS.
- atk_8 (control-flow-effect: returns (none,none) on app=="" boundary): EXIT 1 FAILS.
- pos_control (exact gold impl): EXIT 0 VERIFIES.

MANDATORY RESOLVE STEP: The only two verifying attacks (atk_1, atk_2) both compute the exact gold output pair, so their faithful refined patch is the gold key choice `new_model_state = self.to_state.models[app_label, model_name]` (identical for both). Materialized as faithful.patch and EXECUTED through the official harness via swebench_unified.harness.run_resolve('django__django-15380', patch, timeout=1800): RESULT completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. The verifying-wrong-impl patch RESOLVES => no verify⇏correct break.

### Commands
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." -> True for all
  verify:   bash scripts/lean_verify.sh atk_N.lean
  resolve:  python: run_resolve('django__django-15380', open('.../faithful.patch').read(), run_id='sbu-audit-eq-15380-faithful', timeout=1800)

REFINEMENT.md AUDIT: All legs classified R / A-reference / I; no consumed axioms (meta.json axioms==[]) => no A-consumed, no kind-3. The two A-reference legs are lookupState (models the [app_label,name] ProjectState.models dict subscription / KeyError) and renameLookup (models renamed_models.get((app_label,model_name), model_name), autodetector.py:825). Their correspondence to the real callees is validated by axiom_check.py (G-AX pass, 6010 obligations incl. behavioural crux: renamed model keyed under CURRENT name, prior-name lookup raises KeyError). I re-read axiom_check.py: rename_lookup transliterates renamed.get(key,key[1]); lookup_state transliterates real dict subscription with KeyError->None; the behavioural crux (check_rename_keying) builds real ProjectStates and confirms gold key resolves while prepatch key raises. Correspondence holds. Discriminating content of the change (current-state entry under current name, not prior name) lives directly in the out.2 postcondition (A6 in refinement.md §A), expressed, not axiom-hidden.

VERDICT: SOUND. 8 same-spec attacks run (2 verifying, 6 failing including the prepatch bug); positive control verifies; prepatch reproduced; the faithful patch of every verifying attack was EXECUTED through run_resolve and RESOLVED. No verifying wrong impl breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign computation — resolving a model entry out
   of a name-keyed state map, and resolving a model's prior name through the
   rename record — is modeled DEEPLY by `lookupState` / `renameLookup` (pure
   region). The state maps and the rename record are association lists; the
   lookups are the per-key accesses the routine performs. Those deep models are
   validated against the real Django state maps and rename record by
   axiom_check.py (G-AX, an A-reference; mapping.md §3.1), not consumed as an
   axiom. -/
-- axioms-end

-- pure-start
/- A model entry, identified by its object name. Only its identity is observed
   (the routine selects WHICH entry to read), so the carrier records the name. -/
structure ModelEntry where
  name : String
deriving DecidableEq, Inhabited, Repr

/- Two keys (app label, model name) are equal componentwise. -/
def keyEq (a b : String × String) : Bool := a.1 == b.1 && a.2 == b.2

/- Resolve a model entry out of a name-keyed state map: the entry stored under
   the given (app label, model name), or none when no such key is present
   (the empty result that, in the repository, manifests as a missing key). -/
def lookupState (m : List ((String × String) × ModelEntry))
    (key : String × String) : Option ModelEntry :=
  (m.find? (fun kv => keyEq kv.1 key)).map Prod.snd

/- Resolve a model's name in the prior state from the rename record: when the
   model was renamed, the record maps its current key to its prior name; when it
   was not, its prior name equals its current name. -/
def renameLookup (renamed : List ((String × String) × String))
    (key : String × String) : String :=
  match renamed.find? (fun kv => keyEq kv.1 key) with
  | some kv => kv.2
  | none    => key.2
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the maps and names are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve the prior-state and current-state model entries a field operation
   acts on, for a model whose current name is `curModelName` in app `app`.

   Desired behavior: the model's PRIOR name is its rename source recorded in
   `renamed` (or its current name when it was not renamed). The PRIOR-state entry
   is the one stored in the prior-state map under that prior name. The
   CURRENT-state entry is the one stored in the current-state map under the
   model's CURRENT name — the current-state map is keyed by current names, so a
   model whose name changed is found there under its new name, independently of
   its prior name.

   `priorModels` / `currentModels` are the prior- and current-state model maps;
   `renamed` is the rename record; all three and both names are read-only inputs
   (not `mut`): the routine only reads them (directive 5). -/
method frameRenamedField
    (priorModels : List ((String × String) × ModelEntry))
    (currentModels : List ((String × String) × ModelEntry))
    (renamed : List ((String × String) × String))
    (app : String)
    (curModelName : String)
    return (out : Option ModelEntry × Option ModelEntry)
  ensures out.1 = lookupState priorModels (app, renameLookup renamed (app, curModelName))
  ensures out.2 = lookupState currentModels (app, curModelName)
  do
    -- impl-start
    -- The model's prior name: its rename source, or its current name if it was
    -- not renamed.
    let priorName := renameLookup renamed (app, curModelName)
    -- The prior-state entry is keyed by the prior name; the current-state entry
    -- is keyed by the current name (the current-state map is keyed by current
    -- names).
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState currentModels (app, curModelName)
    return (oldState, newState)
    -- impl-end

prove_correct frameRenamedField by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: frameRenamedField carries TWO equality postconditions that FULLY pin both output components: `out.1 = lookupState priorModels (app, renameLookup renamed (app, curModelName))` and `out.2 = lookupState currentModels (app, curModelName)`. This is a maximally tight functional spec — any verifying impl must produce the exact gold output pair. Impl region byte-identical outside markers for every attack (same_spec=True confirmed via swebench_unified.markers.same_spec for all 8 attacks + positive control).

### VERIFY RESULTS (scripts/lean_verify.sh, 300s cap; run concurrently ≤4):
- atk_1 (ungrounded-oracle ECHO: return postcondition RHS literally): EXIT 0 VERIFIES. Computes gold values.
- atk_2 (reordered lets, same values): EXIT 0 VERIFIES. Computes gold values.
- atk_3 (PREPATCH BUG: current-state entry keyed by prior name): EXIT 1 FAILS (unsolved goal on out.2 clause — same as bundle Solution_prepatch.lean). prepatch reproduced.
- atk_4 (swapped returned pair): EXIT 1 FAILS.
- atk_5 (out.1 ignores rename record, uses current name for prior lookup): EXIT 1 FAILS.
- atk_6 (out.2 reads PRIOR-state map instead of current-state map): EXIT 1 FAILS.
- atk_7 (partial-domain: wrong only when a rename record exists for the key): EXIT 1 FAILS.
- atk_8 (control-flow-effect: returns (none,none) on app=="" boundary): EXIT 1 FAILS.
- pos_control (exact gold impl): EXIT 0 VERIFIES.

MANDATORY RESOLVE STEP: The only two verifying attacks (atk_1, atk_2) both compute the exact gold output pair, so their faithful refined patch is the gold key choice `new_model_state = self.to_state.models[app_label, model_name]` (identical for both). Materialized as faithful.patch and EXECUTED through the official harness via swebench_unified.harness.run_resolve('django__django-15380', patch, timeout=1800): RESULT completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. The verifying-wrong-impl patch RESOLVES => no verify⇏correct break.

### Commands
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." -> True for all
  verify:   bash scripts/lean_verify.sh atk_N.lean
  resolve:  python: run_resolve('django__django-15380', open('.../faithful.patch').read(), run_id='sbu-audit-eq-15380-faithful', timeout=1800)

REFINEMENT.md AUDIT: All legs classified R / A-reference / I; no consumed axioms (meta.json axioms==[]) => no A-consumed, no kind-3. The two A-reference legs are lookupState (models the [app_label,name] ProjectState.models dict subscription / KeyError) and renameLookup (models renamed_models.get((app_label,model_name), model_name), autodetector.py:825). Their correspondence to the real callees is validated by axiom_check.py (G-AX pass, 6010 obligations incl. behavioural crux: renamed model keyed under CURRENT name, prior-name lookup raises KeyError). I re-read axiom_check.py: rename_lookup transliterates renamed.get(key,key[1]); lookup_state transliterates real dict subscription with KeyError->None; the behavioural crux (check_rename_keying) builds real ProjectStates and confirms gold key resolves while prepatch key raises. Correspondence holds. Discriminating content of the change (current-state entry under current name, not prior name) lives directly in the out.2 postcondition (A6 in refinement.md §A), expressed, not axiom-hidden.

VERDICT: SOUND. 8 same-spec attacks run (2 verifying, 6 failing including the prepatch bug); positive control verifies; prepatch reproduced; the faithful patch of every verifying attack was EXECUTED through run_resolve and RESOLVED. No verifying wrong impl breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical (same_spec(post,pre)=True via velvet backend); only the impl body differs between Solution.lean and Solution_prepatch.lean. The spec faithfully models generate_renamed_fields' state-resolution prologue: out.1 = old_model_state = from_state.models[app, renamed_models.get((app,model_name),model_name)]; out.2 = to_state.models[app, model_name] (the post-patch current-name key). The discriminating gold change (current-state entry keyed by curModelName, not priorName) lives directly in the out.2 ensures clause. Deep models lookupState/renameLookup were run against the REAL Django worktree at base_commit (71e7c8e737) via axiom_check.py: 6010 obligations pass (boundary + 3000 fuzz), confirming lookupState==ProjectState.models subscription (present->some, KeyError->none) and renameLookup==renamed_models.get(key,key[1]), plus the crux that a renamed model is keyed under its CURRENT name (prior-name lookup raises KeyError). Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean fails exactly the out.2 clause (unsolved goal: lookupState currentModels (app, renameLookup ...) = lookupState currentModels (app, curModelName)), confirming the spec is neither over- nor under-strong relative to the gold. The only candidate divergence considered — real dict subscription raises KeyError while lookupState returns none — is the documented, consistently-applied abstraction boundary (mapping.md §2) validated by G-AX for presence/absence, and on the real usage domain (model_name from new_field_keys, always present in to_state) the values agree. No input found where the modeled function disagrees with the real callee. Not a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures); spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True). Gold edit is a one-token key change: `new_model_state = self.to_state.models[app_label, old_model_name]` -> `[app_label, model_name]` in generate_renamed_fields.

Assessed each spec-view element against the PUBLIC problem_statement (not hints_text; hints empty here):

1. Edit SITE is already fully public: the problem_statement traceback names generate_renamed_fields, autodetector.py, and reproduces the buggy line `new_model_state = self.to_state.models[app_label, old_model_name]` plus `KeyError: ('test_one','mymodel')`. Nothing in the spec view reveals the location beyond what the task already gives.

2. The postconditions (`out.2 = lookupState currentModels (app, curModelName)` under CURRENT name vs `out.1 = lookupState priorModels (app, renameLookup ...)` under PRIOR name) encode the DESIRED correct behavior. A spec necessarily encodes the correct answer; that is its purpose, not leakage. No pre-patch/post-patch framing, no diff markers, no gold-line reproduction (screen confirms cn>=8 collisions absent), no patched file path, no echo of the patched symbol `generate_renamed_fields` (modeled method renamed frameRenamedField; helpers lookupState/renameLookup/ModelEntry are abstract).

3. Doc-comment describes behavior ("the current-state map is keyed by current names, so a model whose name changed is found there under its new name") without bug/fix narration — _NARRATION_RE terms absent. The only prose that narrates the pre-patch failure / KeyError lives in refinement.md and mapping.md, which are NOT part of the consumer spec view.

4. same_spec True with prepatch confirms the discriminator is in impl/postcondition SATISFACTION, not in a spec crafted to expose the fix: the prepatch impl fails the identical frozen spec.

Conclusion: faithful specification of desired behavior; no leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
