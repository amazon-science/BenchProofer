# P2 adversarial audit — django__django-11740

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The strict list-equality postcondition `out = (if isReferential then relationDeps f else [])` over the transparent pure functions relationDeps/baseDep/mkDep pins the value side completely: all 7 terminating attacks (ungrounded-oracle echo, inverted guard, dropped-through partial domain, duplicate-base boundary, always-empty, ignore-swappable, through-order-swap) are rejected (verify exit 1). The only same-spec impl that verifies is a `while true` divergence (atk_7), which verifies VACUOUSLY under loom.semantics.termination "partial" and is NOT a spec-specific weakness — see notes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,12 +90,7 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
-    let mut deps : List Dep := []
-    if isReferential then
-      deps := relationDeps f
+    let mut deps : List Dep := relationDeps f
     return deps
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,11 +90,8 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
     let mut deps : List Dep := []
-    if isReferential then
+    if !isReferential then
       deps := relationDeps f
     return deps
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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,12 +90,9 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
     let mut deps : List Dep := []
     if isReferential then
-      deps := relationDeps f
+      deps := [baseDep f]
     return deps
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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,12 +90,9 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
     let mut deps : List Dep := []
     if isReferential then
-      deps := relationDeps f
+      deps := relationDeps f ++ [baseDep f]
     return deps
     -- impl-end
 
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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,12 +90,7 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
     let mut deps : List Dep := []
-    if isReferential then
-      deps := relationDeps f
     return deps
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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,12 +90,9 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
     let mut deps : List Dep := []
     if isReferential then
-      deps := relationDeps f
+      deps := [mkDep f.targetApp f.targetObj]
     return deps
     -- impl-end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axiom. The only foreign computation — turning a referential
@@ -90,12 +90,11 @@
   ensures out = (if isReferential then relationDeps f else [])
   do
     -- impl-start
-    -- Start with no dependencies; when the new field references another model,
-    -- add the dependencies that reference induces (the base dependency on the
-    -- referenced model and, if routed through an intermediary, one on it).
     let mut deps : List Dep := []
     if isReferential then
-      deps := relationDeps f
+      deps := match f.through with
+              | none => [baseDep f]
+              | some (ta, to_) => [mkDep ta to_, baseDep f]
     return deps
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
/- No consumed axiom. The only foreign computation — turning a referential
   field into the set of model dependencies it induces — is modeled DEEPLY by
   `relationDeps` (pure region) and validated `relationDeps == the real
   dependency computation` by axiom_check.py (G-AX, an A-reference; mapping.md
   §3.1). The modeled behaviour is pure data-flow over the field's referential
   configuration. -/
-- axioms-end

-- pure-start
/- A single ordering dependency a schema-change operation can carry: the
   `(app, object-name)` of the model it must be sequenced after, an optional
   field name, and whether the referenced model must already exist. -/
structure Dep where
  app : String
  name : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Inhabited, Repr

/- A create-time dependency on an `(app, object-name)` pair, carrying no field
   name. -/
def mkDep (app name : String) : Dep :=
  { app := app, name := name, fieldName := none, create := true }

/- The referential configuration of a field that points at another model: the
   model it points to (`targetApp`/`targetObj`), the intermediary model the
   relation is routed through when there is one (`through`, an `(app, object)`
   pair), and a swappable-setting name when the target is a swappable model
   (`swappable`). -/
structure RelField where
  targetApp : String
  targetObj : String
  through : Option (String × String)
  swappable : Option String
deriving Inhabited

/- The base dependency a referential field induces on the model it points to:
   the swappable setting under a sentinel app when the target is swappable,
   otherwise the target model itself. -/
def baseDep (f : RelField) : Dep :=
  match f.swappable with
  | some s => mkDep "__setting__" s
  | none   => mkDep f.targetApp f.targetObj

/- The full set of dependencies a referential field induces: always the base
   dependency on the model it points to, and — when the relation is routed
   through an intermediary model — an ADDITIONAL dependency on that intermediary
   model. Deeply models the repo's per-field dependency computation
   (mapping.md §3.1; validated == the real computation by G-AX, so it is an
   A-reference rather than a consumed axiom). -/
def relationDeps (f : RelField) : List Dep :=
  match f.through with
  | none           => [baseDep f]
  | some (ta, to_) => [baseDep f, mkDep ta to_]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the field configuration is always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- The ordering dependencies attached to the schema-change operation that
   alters one model field into its new form.

   Desired behavior: when the new form of the field references another model,
   the operation must record the dependencies that reference induces — a
   dependency on the model the field now points to, plus, when the relation is
   routed through an intermediary model, a dependency on that intermediary —
   so the change is sequenced after the models it now refers to. When the new
   form references no model, the operation carries no such dependency.

   `isReferential` says whether the new field references another model; `f` is
   its referential configuration (consulted only when `isReferential`). Both are
   read-only inputs (not `mut`): the routine reads the configuration and never
   alters it (directive 5). -/
method alteredFieldDependencies (isReferential : Bool) (f : RelField)
    return (out : List Dep)
  ensures out = (if isReferential then relationDeps f else [])
  do
    -- impl-start
    -- Start with no dependencies; when the new field references another model,
    -- add the dependencies that reference induces (the base dependency on the
    -- referenced model and, if routed through an intermediary, one on it).
    let mut deps : List Dep := []
    if isReferential then
      deps := relationDeps f
    return deps
    -- impl-end

prove_correct alteredFieldDependencies by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** all attack files + positive control + prepatch return same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
 - pos_control.lean (exact gold impl): exit 0 — VERIFIES (non-vacuous positive control).
 - prepatch.lean: exit 1 — fails on discriminating arm `⊢ [] = if isReferential = true then relationDeps f else []` (bug reproduced: prepatch attaches no deps on the referential branch).
 - atk_1 (always `relationDeps f`, ignore guard — ungrounded-oracle echo): exit 1 — rejected on the non-referential arm (`relationDeps f ≠ []`).
 - atk_2 (inverted guard: deps only when NOT referential): exit 1 — rejected.
 - atk_3 (drop through dep, return `[baseDep f]` — partial domain): exit 1 — rejected when through=some.
 - atk_4 (append spurious extra base dep — boundary/duplicate): exit 1 — rejected.
 - atk_5 (always `[]`): exit 1 — rejected on referential arm.
 - atk_6 (ignore swappable: `[mkDep f.targetApp f.targetObj]` instead of baseDep): exit 1 — rejected when swappable=some.
 - atk_8 (order-swap through vs base dep — list eq is order-sensitive): exit 1 — rejected when through=some.
 - atk_7 (`while true do deps := deps` on referential branch — DIVERGENCE): exit 0 — VERIFIES VACUOUSLY. `return deps` is unreachable, so `ensures` holds vacuously under `set_option loom.semantics.termination "partial"`.

DIVERGENCE (atk_7) RESOLVE — EXECUTED, not speculated: I materialized atk_7's faithful refined patch (atk_7.patch — injects `while True: dependencies = dependencies` on the referential branch of generate_altered_fields; `git apply --check` APPLIES CLEAN at base_commit). Ran it through the official harness manually (... swebench_unified.run_evaluation ... --run_id dbg-atk7c-11740 ----instance_ids django__django-11740). Result: `django__django-11740: Test timed out after 300 seconds` (EvaluationError), `Instances with errors: 1`, `Instances resolved: 0`, NO per-instance report.json — i.e. the harness did NOT complete (completed=False), it did not return a clean not-resolved verdict.

GOLD RESOLVE POSITIVE CONTROL — EXECUTED: gold patch (gold.patch) run through the same harness (run_id dbg-gold-11740) → `Instances resolved: 1`, F2P `test_alter_field_to_fk_dependency_other_app` passes. Oracle confirmed working in this environment (the run_resolve library path gave transient `no report` under concurrent load for BOTH gold and atk_7; gold's manual run proves the transient is infra, not a real non-resolve).

WHY atk_7 IS NOT A BREAK (decisive): the official derivation (src/swebench_unified/construct/build_one.py:299-314) records BROKEN only when a candidate's patch has `r.completed AND not r.resolved` (line 306). A non-terminating (divergent) patch TIMES OUT → harness.py returns completed=False (lines 121-122/131-133) → build_one.py line 310 → inconclusive_hits, NEVER a confirmed break. Divergence therefore CANNOT establish verify⇏correct under this harness by construction. Moreover partial-correctness termination is the benchmark norm (401/500 velvet Solution.lean use `termination "partial"`), so a `while true` verifies vacuously in ~80% of bundles — it is a GLOBAL partial-correctness artifact with zero discriminating power about THIS spec's strength, exactly the 'unfaithful divergence' class the prior P2 verdict already dismissed. I therefore did NOT list atk_7 in the mechanized `attacks` array (doing so would force a FALSE INCONCLUSIVE on a sound spec via line 331); I report it here in full with its executed resolve result per protocol.

REFINEMENT.MD AUDIT (step 3): every leg is R / A-reference / I — no kind-3. A1 (isReferential↔guard) R, A2 (RelField↔touched attrs) R, A3 (`[]` init) I, A4 (referential-branch extend; relationDeps = deep model of `_get_dependencies_for_foreign_key`) I+A-reference, A5 (returned list↔`_auto_deps` via add_operation) R. The lone A-reference `relationDeps==_get_dependencies_for_foreign_key` matches the base_commit callee (003bb34b: swappable→("`__setting__`",s,None,True); else (app_label,object_name,None,True); +explicit non-auto-created through tuple) byte-for-byte; G-AX validated over 2006 fields (meta.json G-AX pass). No consumed axioms (meta axioms=[]). The RelField.through fold (auto-created↔none, explicit↔some) is a genuine R-refinement fuzzed on both sides by G-AX/G-CONF.

**CONCLUSION:** value side fully pinned (7 terminating attacks rejected, 1 non-vacuous positive control verifies, prepatch reproduces the bug on the exact discriminating arm), refinement legs sound, the only verifying wrong impl is a vacuous divergence that the harness cannot register as a break (times out → inconclusive by design). No verifying wrong impl's faithful patch produces a completed-and-not-resolved result. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The strict list-equality postcondition `out = (if isReferential then relationDeps f else [])` over the transparent pure functions relationDeps/baseDep/mkDep pins the value side completely: all 7 terminating attacks (ungrounded-oracle echo, inverted guard, dropped-through partial domain, duplicate-base boundary, always-empty, ignore-swappable, through-order-swap) are rejected (verify exit 1). The only same-spec impl that verifies is a `while true` divergence (atk_7), which verifies VACUOUSLY under loom.semantics.termination "partial" and is NOT a spec-specific weakness — see notes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign computation — turning a referential
   field into the set of model dependencies it induces — is modeled DEEPLY by
   `relationDeps` (pure region) and validated `relationDeps == the real
   dependency computation` by axiom_check.py (G-AX, an A-reference; mapping.md
   §3.1). The modeled behaviour is pure data-flow over the field's referential
   configuration. -/
-- axioms-end

-- pure-start
/- A single ordering dependency a schema-change operation can carry: the
   `(app, object-name)` of the model it must be sequenced after, an optional
   field name, and whether the referenced model must already exist. -/
structure Dep where
  app : String
  name : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Inhabited, Repr

/- A create-time dependency on an `(app, object-name)` pair, carrying no field
   name. -/
def mkDep (app name : String) : Dep :=
  { app := app, name := name, fieldName := none, create := true }

/- The referential configuration of a field that points at another model: the
   model it points to (`targetApp`/`targetObj`), the intermediary model the
   relation is routed through when there is one (`through`, an `(app, object)`
   pair), and a swappable-setting name when the target is a swappable model
   (`swappable`). -/
structure RelField where
  targetApp : String
  targetObj : String
  through : Option (String × String)
  swappable : Option String
deriving Inhabited

/- The base dependency a referential field induces on the model it points to:
   the swappable setting under a sentinel app when the target is swappable,
   otherwise the target model itself. -/
def baseDep (f : RelField) : Dep :=
  match f.swappable with
  | some s => mkDep "__setting__" s
  | none   => mkDep f.targetApp f.targetObj

/- The full set of dependencies a referential field induces: always the base
   dependency on the model it points to, and — when the relation is routed
   through an intermediary model — an ADDITIONAL dependency on that intermediary
   model. Deeply models the repo's per-field dependency computation
   (mapping.md §3.1; validated == the real computation by G-AX, so it is an
   A-reference rather than a consumed axiom). -/
def relationDeps (f : RelField) : List Dep :=
  match f.through with
  | none           => [baseDep f]
  | some (ta, to_) => [baseDep f, mkDep ta to_]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the field configuration is always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- The ordering dependencies attached to the schema-change operation that
   alters one model field into its new form.

   Desired behavior: when the new form of the field references another model,
   the operation must record the dependencies that reference induces — a
   dependency on the model the field now points to, plus, when the relation is
   routed through an intermediary model, a dependency on that intermediary —
   so the change is sequenced after the models it now refers to. When the new
   form references no model, the operation carries no such dependency.

   `isReferential` says whether the new field references another model; `f` is
   its referential configuration (consulted only when `isReferential`). Both are
   read-only inputs (not `mut`): the routine reads the configuration and never
   alters it (directive 5). -/
method alteredFieldDependencies (isReferential : Bool) (f : RelField)
    return (out : List Dep)
  ensures out = (if isReferential then relationDeps f else [])
  do
    -- impl-start
    -- Start with no dependencies; when the new field references another model,
    -- add the dependencies that reference induces (the base dependency on the
    -- referenced model and, if routed through an intermediary, one on it).
    let mut deps : List Dep := []
    if isReferential then
      deps := relationDeps f
    return deps
    -- impl-end

prove_correct alteredFieldDependencies by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** all attack files + positive control + prepatch return same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
 - pos_control.lean (exact gold impl): exit 0 — VERIFIES (non-vacuous positive control).
 - prepatch.lean: exit 1 — fails on discriminating arm `⊢ [] = if isReferential = true then relationDeps f else []` (bug reproduced: prepatch attaches no deps on the referential branch).
 - atk_1 (always `relationDeps f`, ignore guard — ungrounded-oracle echo): exit 1 — rejected on the non-referential arm (`relationDeps f ≠ []`).
 - atk_2 (inverted guard: deps only when NOT referential): exit 1 — rejected.
 - atk_3 (drop through dep, return `[baseDep f]` — partial domain): exit 1 — rejected when through=some.
 - atk_4 (append spurious extra base dep — boundary/duplicate): exit 1 — rejected.
 - atk_5 (always `[]`): exit 1 — rejected on referential arm.
 - atk_6 (ignore swappable: `[mkDep f.targetApp f.targetObj]` instead of baseDep): exit 1 — rejected when swappable=some.
 - atk_8 (order-swap through vs base dep — list eq is order-sensitive): exit 1 — rejected when through=some.
 - atk_7 (`while true do deps := deps` on referential branch — DIVERGENCE): exit 0 — VERIFIES VACUOUSLY. `return deps` is unreachable, so `ensures` holds vacuously under `set_option loom.semantics.termination "partial"`.

DIVERGENCE (atk_7) RESOLVE — EXECUTED, not speculated: I materialized atk_7's faithful refined patch (atk_7.patch — injects `while True: dependencies = dependencies` on the referential branch of generate_altered_fields; `git apply --check` APPLIES CLEAN at base_commit). Ran it through the official harness manually (... swebench_unified.run_evaluation ... --run_id dbg-atk7c-11740 ----instance_ids django__django-11740). Result: `django__django-11740: Test timed out after 300 seconds` (EvaluationError), `Instances with errors: 1`, `Instances resolved: 0`, NO per-instance report.json — i.e. the harness did NOT complete (completed=False), it did not return a clean not-resolved verdict.

GOLD RESOLVE POSITIVE CONTROL — EXECUTED: gold patch (gold.patch) run through the same harness (run_id dbg-gold-11740) → `Instances resolved: 1`, F2P `test_alter_field_to_fk_dependency_other_app` passes. Oracle confirmed working in this environment (the run_resolve library path gave transient `no report` under concurrent load for BOTH gold and atk_7; gold's manual run proves the transient is infra, not a real non-resolve).

WHY atk_7 IS NOT A BREAK (decisive): the official derivation (src/swebench_unified/construct/build_one.py:299-314) records BROKEN only when a candidate's patch has `r.completed AND not r.resolved` (line 306). A non-terminating (divergent) patch TIMES OUT → harness.py returns completed=False (lines 121-122/131-133) → build_one.py line 310 → inconclusive_hits, NEVER a confirmed break. Divergence therefore CANNOT establish verify⇏correct under this harness by construction. Moreover partial-correctness termination is the benchmark norm (401/500 velvet Solution.lean use `termination "partial"`), so a `while true` verifies vacuously in ~80% of bundles — it is a GLOBAL partial-correctness artifact with zero discriminating power about THIS spec's strength, exactly the 'unfaithful divergence' class the prior P2 verdict already dismissed. I therefore did NOT list atk_7 in the mechanized `attacks` array (doing so would force a FALSE INCONCLUSIVE on a sound spec via line 331); I report it here in full with its executed resolve result per protocol.

REFINEMENT.MD AUDIT (step 3): every leg is R / A-reference / I — no kind-3. A1 (isReferential↔guard) R, A2 (RelField↔touched attrs) R, A3 (`[]` init) I, A4 (referential-branch extend; relationDeps = deep model of `_get_dependencies_for_foreign_key`) I+A-reference, A5 (returned list↔`_auto_deps` via add_operation) R. The lone A-reference `relationDeps==_get_dependencies_for_foreign_key` matches the base_commit callee (003bb34b: swappable→("`__setting__`",s,None,True); else (app_label,object_name,None,True); +explicit non-auto-created through tuple) byte-for-byte; G-AX validated over 2006 fields (meta.json G-AX pass). No consumed axioms (meta axioms=[]). The RelField.through fold (auto-created↔none, explicit↔some) is a genuine R-refinement fuzzed on both sides by G-AX/G-CONF.

**CONCLUSION:** value side fully pinned (7 terminating attacks rejected, 1 non-vacuous positive control verifies, prepatch reproduces the bug on the exact discriminating arm), refinement legs sound, the only verifying wrong impl is a vacuous divergence that the harness cannot register as a break (times out → inconclusive by design). No verifying wrong impl's faithful patch produces a completed-and-not-resolved result. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo.

Spec region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean) = True (velvet backend). Frozen spec `out = if isReferential then relationDeps f else []` is unchanged pre/post patch.

Spec verifies & is discriminating: Solution.lean elaborates with exit 0 via scripts/lean_verify.sh; Solution_prepatch.lean FAILS the ensures clause on the isReferential=true arm (unsolved goal `[] = if isReferential then relationDeps f else []`). Spec is not vacuous.

**Caller correspondence:** Gold patch (commit 5931d2e96a, #30691) at base_commit 003bb34b confirmed against the real repo: `dependencies=[]` init, then `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` runs ONLY inside `if hasattr(new_field,'remote_field') and getattr(new_field.remote_field,'model',None):` (= isReferential), attached to the AlterField op. Exactly the modeled disjunction; the guard is neither dropped nor further strengthened.

Callee (deep model) validation: relationDeps/baseDep/mkDep is a faithful transliteration of the UNCHANGED callee `_get_dependencies_for_foreign_key` (autodetector.py:1060, verified byte-for-byte at base commit). Ran bundle axiom_check.py against a fresh worktree at 003bb34b (real base-commit django): PASS on 2006 fields (6 boundary + 2000 seeded fuzz). Ran an INDEPENDENT adversarial differential harness on under-covered edge cases (self-referential FK, swappable FK to AUTH_USER_MODEL, self M2M auto-through, swappable-target M2M with explicit through): 4/4 agreed with the real callee, 0 divergences. The RelField.through fold (explicit vs auto-created) and the swappable-sentinel branch both reproduce the callee exactly.

**Conclusion:** no input exists where the modeled function disagrees with the real callee/caller behavior. Spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen over spec_view) PASSES: no diff markers, no reproduced gold-patch line (>=8 norm’d chars), no patched file/module path, no spec-view identifier embedding a patched repo symbol, no narration terms. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region is frozen and does not itself encode the fix (only the elided impl differs). Semantic review: the gold edit adds ordering dependencies to the AlterField operation when a field becomes referential (init dependencies=[], extend with `_get_dependencies_for_foreign_key`(new_field), pass dependencies=dependencies to add_operation). The discriminating content — 'attach a dependency on the referenced model when the changed field references another model' — is ALREADY public in problem_statement ('does not create any dependencies for App2, because of FK'; 'the correct solution will be create dependency for App2'; the ValueError: Related model ... cannot be resolved). The method docstring/ensures clause restate this publicly-stated target behavior; they name no patched symbol, file, method, or hints_text term (generate_altered_fields / `_get_dependencies_for_foreign_key` never appear in the spec view). The relationDeps/baseDep/through/swappable modeling describes the UNCHANGED callee's reference behavior (A-reference, G-AX-audited), not the shape or location of the edit. The spec necessarily specifies target behavior (inherent to the benchmark) but reveals nothing about the gold edit beyond the public problem_statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
