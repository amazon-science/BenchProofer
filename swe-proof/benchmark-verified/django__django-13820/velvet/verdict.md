# P2 adversarial audit — django__django-13820

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `prepatch.lean`, `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verify-but-wrong counterexample exists. The postcondition `ensures out = loadable hasFile hasPath pathIsList` combined with EMPTY preconditions totally pins the output as an exact function over the full Bool^3 domain, so any same-spec impl that verifies must equal `loadable = hasPath && (hasFile || pathIsList)` at every one of the 8 points — i.e. be behaviorally identical to the gold patch's post-patch load_disk classification. Divergence on any single point leaves an unsolved `<impl> = loadable ...` goal and loom_solve fails (observed for all 8 wrong impls).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,16 +51,13 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
+    -- PREPATCH: skip any module with no __file__ before package check
+    let noFile : Bool := !hasFile
     let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
     let out : Bool :=
-      if notPackage then false
+      if noFile then false
       else
-        if isNamespace then false
+        if notPackage then false
         else true
     return out
     -- impl-end
```

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,7 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    let out : Bool := hasPath && hasFile
     return out
     -- impl-end
 
```

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,7 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    let out : Bool := hasPath && (hasFile && pathIsList)
     return out
     -- impl-end
 
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,8 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
     let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    let out : Bool := if isNamespace then false else true
     return out
     -- impl-end
 
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,7 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    let out : Bool := if hasPath then true else false
     return out
     -- impl-end
 
```

Attack 6 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,18 +51,7 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
-    return out
+    return loadable hasFile hasPath pathIsList
     -- impl-end
 
 prove_correct migrationsModuleLoadable by
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,7 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    let out : Bool := hasPath && pathIsList
     return out
     -- impl-end
 
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,7 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    let out : Bool := hasPath && (hasFile || !pathIsList)
     return out
     -- impl-end
 
```

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -51,17 +51,9 @@
   ensures out = loadable hasFile hasPath pathIsList
   do
     -- impl-start
-    -- A module that is not a package contributes nothing; a package that
-    -- advertises no concrete file location and whose search path is not an
-    -- ordinary list is an implicit namespace package and is also skipped; every
-    -- other package is scanned.
-    let notPackage : Bool := !hasPath
-    let isNamespace : Bool := (!hasFile) && (!pathIsList)
-    let out : Bool :=
-      if notPackage then false
-      else
-        if isNamespace then false
-        else true
+    -- Attempt to exploit partial-correctness: return a constant wrong value
+    -- but guard via a demonic/partial construct. Simplest wrong constant:
+    let out : Bool := false
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to unchanged callees. The
   operations this slice relies on — testing whether an imported module carries a
   concrete file location, exposes an ordinary search path, and whether that
   search path is an ordinary list — are language-level attribute observations,
   modeled directly here as the three boolean inputs (concrete I-ops) and
   refinement-checked against the real behaviour by conformance_check.py
   (G-CONF), mapping.md §3. -/
-- axioms-end

-- pure-start
/- Whether a candidate module's on-disk migrations directory should be scanned
   and its migrations loaded.

   The inputs describe the module by three observations:
   * `hasFile`     — it advertises a concrete file location;
   * `hasPath`     — it exposes a package search path (i.e. it is a package, not
                     a plain module);
   * `pathIsList`  — that search path is an ordinary list.

   A module contributes on-disk migrations exactly when it is a package
   (`hasPath`) that is not an implicit namespace package. The implicit namespace
   case — and the ONLY case excluded among packages — is the one that advertises
   no concrete file location AND whose search path is not an ordinary list
   (`!hasFile && !pathIsList`). In particular a package that omits a file
   location yet still uses an ordinary list search path is scanned like any other
   package. -/
def loadable (hasFile hasPath pathIsList : Bool) : Bool :=
  hasPath && (hasFile || pathIsList)

@[simp, grind] lemma loadable_def (hasFile hasPath pathIsList : Bool) :
    loadable hasFile hasPath pathIsList = (hasPath && (hasFile || pathIsList)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method migrationsModuleLoadable (hasFile : Bool) (hasPath : Bool) (pathIsList : Bool)
    return (out : Bool)
  ensures out = loadable hasFile hasPath pathIsList
  do
    -- impl-start
    -- POSITIVE CONTROL: correct, computes loadable directly
    let out : Bool := hasPath && (hasFile || pathIsList)
    return out
    -- impl-end

prove_correct migrationsModuleLoadable by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. verifier scripts/lean_verify.sh (wrap, 300s cap); same_spec via swebench_unified.markers with velvet backend (all attacks + pos = True, only impl region edited, axioms/pure/pre/post byte-identical). Attacks verified concurrently in background batches of <=4.

### RESULTS (exit 0=verifies, 1=fails with divergence goal):
- pos.lean (POSITIVE CONTROL, correct `hasPath && (hasFile||pathIsList)`): EXIT 0 -> VERIFIES. Good.
- prepatch.lean (prepatch bug: skip file-less module before package check): EXIT 1. Unsolved goal `(if !hasFile then false else if !hasPath then false else true) = loadable`. Diverges at (F,T,T). Reproduces prepatch behavior.
- atk_1 (partial-domain: `hasPath && hasFile`, drops pathIsList disjunct): EXIT 1. Wrong at (F,T,T).
- atk_2 (boundary: `hasPath && (hasFile && pathIsList)`, conjunction not disjunction): EXIT 1. Wrong at (F,T,T),(T,T,F).
- atk_3 (control-flow: only namespace guard, drops notPackage guard): EXIT 1. Wrong at (*,F,*) non-package cases e.g. (T,F,T).
- atk_4 (control-flow-effect: package => always loaded, drops namespace exclusion): EXIT 1. Wrong at (F,T,F).
- atk_5 (ungrounded-oracle echo: `return loadable hasFile hasPath pathIsList`): EXIT 0 -> VERIFIES. This is behaviorally CORRECT (equals loadable exactly). Per protocol its faithful refined patch was materialized = gold patch.diff verbatim (atk_5 computes the exact modeled decision, so the gold post-patch load_disk is its faithful refinement) and RUN through the official harness: run_resolve('django__django-13820', patch) under SBU_BENCHMARK=swe_bench_verified, Docker oracle available (docker-ok) => RESOLVED: True, note 'resolved'. So the sole verifying attack's patch RESOLVES — does NOT break the spec. This matches the G-PANEL-1/G-EQ echo policy: a resolving echo of gold is not a weakness.
- atk_6 (boundary: `hasPath && pathIsList`, ignores hasFile): EXIT 1. Wrong at (T,T,F).
- atk_7 (negation flip: `hasPath && (hasFile || !pathIsList)`): EXIT 1. Wrong at (F,T,T),(T,T,F).
- atk_8 (partial-correctness escape probe: constant `out=false`): EXIT 1, goal `false = loadable`. No vacuous/demonic escape — the ensures obligation is discharged non-vacuously over all inputs; a constant wrong value fails. Confirms partial+demonic settings do NOT admit a divergence loophole here (impl is a pure total expression).

EXACT COMMANDS: for each atk: `bash scripts/lean_verify.sh <file>.lean`; resolve: python -c run_resolve with SBU_BENCHMARK=swe_bench_verified, => resolved True.

REFINEMENT.MD AUDIT: legs A1-A3 = R (three attribute observations getattr(__file__)/hasattr(__path__)/isinstance(__path__,list) <-> the three Bool params, per mapping.md §2 bijection); A4-A6 = I (the two-guard control flow notPackage-then-namespace mirroring the post-patch load_disk ordering, __path__ dereferenced only after existence check). ZERO A-consumed and ZERO A-reference legs (axioms region empty; the only real load_disk callees import_module/pkgutil.iter_modules/reload are UNCHANGED by the patch and outside the modeled decision — correctly declared neither axiomatized nor deep-modeled, mapping.md §3, G-AX skip). ZERO kind-3 (inexpressible-changed-op) legs: the changed op is a finite boolean classification modeled directly. Model<->patch correspondence holds: `loadable = hasPath && (hasFile||pathIsList)` is exactly the negation of the disjunction of the two post-patch skip guards (`!hasPath` OR `!hasFile && !pathIsList`), and the discriminating case (F,T,T) flips prepatch->postpatch as documented.

CONCLUSION: Spec is a tight total pin over Bool^3; verify => behaviorally-equal-to-gold => resolves. The single verifying same-spec impl's faithful patch RESOLVED under the executed official harness. No verify-but-not-resolve witness found across 9 wrong/echo attacks + positive control. VERDICT: SOUND (verify does NOT imply incorrect here — verify implies correct).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `prepatch.lean`, `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verify-but-wrong counterexample exists. The postcondition `ensures out = loadable hasFile hasPath pathIsList` combined with EMPTY preconditions totally pins the output as an exact function over the full Bool^3 domain, so any same-spec impl that verifies must equal `loadable = hasPath && (hasFile || pathIsList)` at every one of the 8 points — i.e. be behaviorally identical to the gold patch's post-patch load_disk classification. Divergence on any single point leaves an unsolved `<impl> = loadable ...` goal and loom_solve fails (observed for all 8 wrong impls).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to unchanged callees. The
   operations this slice relies on — testing whether an imported module carries a
   concrete file location, exposes an ordinary search path, and whether that
   search path is an ordinary list — are language-level attribute observations,
   modeled directly here as the three boolean inputs (concrete I-ops) and
   refinement-checked against the real behaviour by conformance_check.py
   (G-CONF), mapping.md §3. -/
-- axioms-end

-- pure-start
/- Whether a candidate module's on-disk migrations directory should be scanned
   and its migrations loaded.

   The inputs describe the module by three observations:
   * `hasFile`     — it advertises a concrete file location;
   * `hasPath`     — it exposes a package search path (i.e. it is a package, not
                     a plain module);
   * `pathIsList`  — that search path is an ordinary list.

   A module contributes on-disk migrations exactly when it is a package
   (`hasPath`) that is not an implicit namespace package. The implicit namespace
   case — and the ONLY case excluded among packages — is the one that advertises
   no concrete file location AND whose search path is not an ordinary list
   (`!hasFile && !pathIsList`). In particular a package that omits a file
   location yet still uses an ordinary list search path is scanned like any other
   package. -/
def loadable (hasFile hasPath pathIsList : Bool) : Bool :=
  hasPath && (hasFile || pathIsList)

@[simp, grind] lemma loadable_def (hasFile hasPath pathIsList : Bool) :
    loadable hasFile hasPath pathIsList = (hasPath && (hasFile || pathIsList)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method migrationsModuleLoadable (hasFile : Bool) (hasPath : Bool) (pathIsList : Bool)
    return (out : Bool)
  ensures out = loadable hasFile hasPath pathIsList
  do
    -- impl-start
    -- POSITIVE CONTROL: correct, computes loadable directly
    let out : Bool := hasPath && (hasFile || pathIsList)
    return out
    -- impl-end

prove_correct migrationsModuleLoadable by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. verifier scripts/lean_verify.sh (wrap, 300s cap); same_spec via swebench_unified.markers with velvet backend (all attacks + pos = True, only impl region edited, axioms/pure/pre/post byte-identical). Attacks verified concurrently in background batches of <=4.

### RESULTS (exit 0=verifies, 1=fails with divergence goal):
- pos.lean (POSITIVE CONTROL, correct `hasPath && (hasFile||pathIsList)`): EXIT 0 -> VERIFIES. Good.
- prepatch.lean (prepatch bug: skip file-less module before package check): EXIT 1. Unsolved goal `(if !hasFile then false else if !hasPath then false else true) = loadable`. Diverges at (F,T,T). Reproduces prepatch behavior.
- atk_1 (partial-domain: `hasPath && hasFile`, drops pathIsList disjunct): EXIT 1. Wrong at (F,T,T).
- atk_2 (boundary: `hasPath && (hasFile && pathIsList)`, conjunction not disjunction): EXIT 1. Wrong at (F,T,T),(T,T,F).
- atk_3 (control-flow: only namespace guard, drops notPackage guard): EXIT 1. Wrong at (*,F,*) non-package cases e.g. (T,F,T).
- atk_4 (control-flow-effect: package => always loaded, drops namespace exclusion): EXIT 1. Wrong at (F,T,F).
- atk_5 (ungrounded-oracle echo: `return loadable hasFile hasPath pathIsList`): EXIT 0 -> VERIFIES. This is behaviorally CORRECT (equals loadable exactly). Per protocol its faithful refined patch was materialized = gold patch.diff verbatim (atk_5 computes the exact modeled decision, so the gold post-patch load_disk is its faithful refinement) and RUN through the official harness: run_resolve('django__django-13820', patch) under SBU_BENCHMARK=swe_bench_verified, Docker oracle available (docker-ok) => RESOLVED: True, note 'resolved'. So the sole verifying attack's patch RESOLVES — does NOT break the spec. This matches the G-PANEL-1/G-EQ echo policy: a resolving echo of gold is not a weakness.
- atk_6 (boundary: `hasPath && pathIsList`, ignores hasFile): EXIT 1. Wrong at (T,T,F).
- atk_7 (negation flip: `hasPath && (hasFile || !pathIsList)`): EXIT 1. Wrong at (F,T,T),(T,T,F).
- atk_8 (partial-correctness escape probe: constant `out=false`): EXIT 1, goal `false = loadable`. No vacuous/demonic escape — the ensures obligation is discharged non-vacuously over all inputs; a constant wrong value fails. Confirms partial+demonic settings do NOT admit a divergence loophole here (impl is a pure total expression).

EXACT COMMANDS: for each atk: `bash scripts/lean_verify.sh <file>.lean`; resolve: python -c run_resolve with SBU_BENCHMARK=swe_bench_verified, => resolved True.

REFINEMENT.MD AUDIT: legs A1-A3 = R (three attribute observations getattr(__file__)/hasattr(__path__)/isinstance(__path__,list) <-> the three Bool params, per mapping.md §2 bijection); A4-A6 = I (the two-guard control flow notPackage-then-namespace mirroring the post-patch load_disk ordering, __path__ dereferenced only after existence check). ZERO A-consumed and ZERO A-reference legs (axioms region empty; the only real load_disk callees import_module/pkgutil.iter_modules/reload are UNCHANGED by the patch and outside the modeled decision — correctly declared neither axiomatized nor deep-modeled, mapping.md §3, G-AX skip). ZERO kind-3 (inexpressible-changed-op) legs: the changed op is a finite boolean classification modeled directly. Model<->patch correspondence holds: `loadable = hasPath && (hasFile||pathIsList)` is exactly the negation of the disjunction of the two post-patch skip guards (`!hasPath` OR `!hasFile && !pathIsList`), and the discriminating case (F,T,T) flips prepatch->postpatch as documented.

CONCLUSION: Spec is a tight total pin over Bool^3; verify => behaviorally-equal-to-gold => resolves. The single verifying same-spec impl's faithful patch RESOLVED under the executed official harness. No verify-but-not-resolve witness found across 9 wrong/echo attacks + positive control. VERDICT: SOUND (verify does NOT imply incorrect here — verify implies correct).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13820 velvet.

Modeled decision: the `else:` block of MigrationLoader.load_disk (django/db/migrations/loader.py) reached after a successful import_module — whether a candidate module's on-disk migrations are scanned (app -> migrated_apps) vs skipped (app -> unmigrated_apps, continue).

Spec: `loadable hasFile hasPath pathIsList = hasPath && (hasFile || pathIsList)`, ensures out = loadable.

Real post-patch control flow (verified worktree; gold patch applied to base 98ad327864):
  1. if not hasattr(module,'__path__'): skip            # not a package
  2. if getattr(module,'__file__',None) is None and not isinstance(module.__path__,list): skip   # implicit namespace
  3. else: scanned
Equivalently scanned <=> hasPath && !((!hasFile) && (!pathIsList)) = hasPath && (hasFile || pathIsList).

Enumerated the full Bool^3 cube (8 points) real-vs-model: ALL AGREE, no divergence.
  hasFile=F hasPath=F pathIsList=F : F=F
  hasFile=F hasPath=F pathIsList=T : F=F
  hasFile=F hasPath=T pathIsList=F : F=F  (namespace skip fires in both)
  hasFile=F hasPath=T pathIsList=T : T=T  (the discriminating post-patch case: file-less package with ordinary-list __path__ is now scanned)
  hasFile=T hasPath=F pathIsList=* : F=F
  hasFile=T hasPath=T pathIsList=F : T=T
  hasFile=T hasPath=T pathIsList=T : T=T

Short-circuit ordering is preserved: the model checks notPackage (!hasPath) before consulting pathIsList, mirroring the real code's dereference-safety (module.__path__ only accessed when hasattr(__path__)). When hasPath=false, pathIsList is unobservable in the repo; the spec is total over the cube and returns false there regardless of pathIsList, consistent with the real non-package `continue`.

Unchanged callees (import_module, pkgutil.iter_modules, reload) run outside the modeled classification decision and are correctly excluded from the slice; the earlier module_name-None / ModuleNotFoundError guards are unchanged and out of the else-block slice.

spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(Solution, prepatch, VelvetBackend) = True. Solution.lean verifies via scripts/lean_verify.sh (exit 0); the prepatch impl differs (file-less skip before package check) and correctly disagrees on (F,T,T).

No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage baseline = public problem_statement (NOT hints_text). Independently verified:

(1) markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True — the spec region is byte-identical between gold and prepatch; the two differ ONLY in the elided impl/proof, so nothing that distinguishes the gold implementation bleeds into the frozen spec view.

(2) Computed the actual consumer spec_view: impl region is a placeholder ('implementation elided — supplied by the consumer') and the prove_correct body is a placeholder ('proof elided'). The visible spec is: the signature migrationsModuleLoadable (hasFile hasPath pathIsList : Bool) return (out : Bool); the pure helper loadable = hasPath && (hasFile || pathIsList); a docstring describing the namespace-exclusion criterion !hasFile && !pathIsList; and the ensures out = loadable ... contract.

(3) Ran the mechanical leakage.screen over the spec view: PASSED, hard_failures == [] (no diff markers, no reproduced gold-patch line, no patched file path, no identifier/comment echoing a patched repo symbol beyond the problem_statement, no narration). Consistent with meta.json G-LEAK 'spec view clean' (pass).

The public problem_statement ALREADY discloses the entire gold edit, and more concretely than the spec view does. It names: the exact file+method (django.db.migrations.loader.MigrationLoader.load_disk); the exact current guard (getattr(m,'__file__',None) is false); the exact discriminator ("Namespace packages do not use an ordinary list for their __path__"); and the exact fix VERBATIM ("I propose to augment getattr(m,'__file__',None) with and isinstance(m.__path__, list)"). The spec view's pathIsList observation and the !hasFile && !pathIsList exclusion are precisely this publicly-stated proposal, expressed as a boolean abstraction that is LESS concrete than the literal Python API calls in the problem_statement. The hasPath package check corresponds to pre-existing repo logic (hasattr(module,'__path__')), not the gold edit. No spec-view line reveals any gold-edit detail beyond what the public problem_statement states. Bundle is not relaxed (relaxed_leakage absent, no RELAXED_LEAKAGE.md), so no deferral needed — a genuine NO-LEAKAGE.

VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
