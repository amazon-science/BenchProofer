# P2 adversarial audit — matplotlib__matplotlib-13989

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_1_boundary.lean`, `atk_2_wrongval.lean`, `atk_3_partialdomain.lean`, `atk_5_echo.lean`, `atk_6_dropbounds.lean`, `atk_7_swapguard.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4_cfsame.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -80,7 +80,7 @@
     let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
     let result : HistOptions :=
       if density && !accumulate then
-        { base with densityOpt := some density }
+        { boundsOpt := none, densityOpt := some density }
       else
         base
     return result
```

Attack 2 — `atk_1_boundary.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -79,7 +79,7 @@
     -- impl-start
     let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
     let result : HistOptions :=
-      if density && !accumulate then
+      if !accumulate then
         { base with densityOpt := some density }
       else
         base
```

Attack 3 — `atk_2_wrongval.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -80,7 +80,7 @@
     let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
     let result : HistOptions :=
       if density && !accumulate then
-        { base with densityOpt := some density }
+        { base with densityOpt := some (!density) }
       else
         base
     return result
```

Attack 4 — `atk_3_partialdomain.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -79,7 +79,7 @@
     -- impl-start
     let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
     let result : HistOptions :=
-      if density && !accumulate then
+      if density && !accumulate && boundsOpt.isSome then
         { base with densityOpt := some density }
       else
         base
```

Attack 5 — `atk_4_cfsame.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -77,12 +77,8 @@
   ensures ¬(density = true ∧ accumulate = false) → out.densityOpt = none
   do
     -- impl-start
-    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
-    let result : HistOptions :=
-      if density && !accumulate then
-        { base with densityOpt := some density }
-      else
-        base
+    let d : Option Bool := if density && !accumulate then some density else none
+    let result : HistOptions := { boundsOpt := boundsOpt, densityOpt := d }
     return result
     -- impl-end
 
```

Attack 6 — `atk_5_echo.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -77,13 +77,7 @@
   ensures ¬(density = true ∧ accumulate = false) → out.densityOpt = none
   do
     -- impl-start
-    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
-    let result : HistOptions :=
-      if density && !accumulate then
-        { base with densityOpt := some density }
-      else
-        base
-    return result
+    return buildHistOptions boundsOpt density accumulate
     -- impl-end
 
 prove_correct buildHistOptionsM by
```

Attack 7 — `atk_6_dropbounds.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -77,12 +77,11 @@
   ensures ¬(density = true ∧ accumulate = false) → out.densityOpt = none
   do
     -- impl-start
-    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
     let result : HistOptions :=
       if density && !accumulate then
-        { base with densityOpt := some density }
+        { boundsOpt := none, densityOpt := some density }
       else
-        base
+        { boundsOpt := boundsOpt, densityOpt := none }
     return result
     -- impl-end
 
```

Attack 8 — `atk_7_swapguard.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under specification is the pure
@@ -79,7 +79,7 @@
     -- impl-start
     let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
     let result : HistOptions :=
-      if density && !accumulate then
+      if density && accumulate then
         { base with densityOpt := some density }
       else
         base
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation under specification is the pure
--  assembly of the keyword-option mapping handed to the histogram routine; it
--  is modeled DEEPLY in the `pure` region below. The downstream histogram
--  computation that consumes these options is unchanged and is not modeled —
--  it owes no contract here.)
-- axioms-end

-- pure-start
/- The keyword-option mapping assembled for a single histogram computation,
   reduced to the two entries this assembly decides:
     * `boundsOpt`  — the explicit lower/upper data bounds entry, present
                      (`some`) when bounds were determined for this computation
                      and absent (`none`) otherwise;
     * `densityOpt` — the normalize-to-a-density entry, present (`some b`) when
                      the assembly records the density choice and absent
                      (`none`) when it does not.
   The two bounds are carried opaquely (their numeric values are never inspected
   here); only their presence and identity matter to this assembly. -/
structure HistOptions where
  boundsOpt  : Option (Float × Float)
  densityOpt : Option Bool
  deriving Inhabited

/- Assemble the option mapping. The mapping starts carrying whatever bounds
   entry was already determined (`boundsOpt`) and no density entry. When the
   density choice is recorded for a non-accumulated computation, the density
   entry is ADDED to that same mapping — the already-present bounds entry is
   carried through unchanged, never discarded. In every other case the mapping
   is left as it began. -/
def buildHistOptions
    (boundsOpt : Option (Float × Float)) (density accumulate : Bool) : HistOptions :=
  let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
  if density && !accumulate then { base with densityOpt := some density } else base

@[grind] lemma buildHistOptions_bounds
    (boundsOpt : Option (Float × Float)) (density accumulate : Bool) :
    (buildHistOptions boundsOpt density accumulate).boundsOpt = boundsOpt := by
  unfold buildHistOptions
  cases density <;> cases accumulate <;> simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the keyword-option mapping for a single histogram computation.

   The desired behaviour the issue demands: recording the density choice must
   NOT cause the explicitly-determined bounds entry to be lost. Concretely:

   - the bounds entry of the assembled mapping is ALWAYS exactly the bounds
     entry that was already determined (`out.boundsOpt = boundsOpt`) — adding
     the density entry never discards or alters it;
   - the density entry is present and records the density choice exactly when
     the density choice applies to this computation (a density computation that
     is not accumulated); otherwise the density entry is absent.

   None of the inputs are mutated (directive 5): `boundsOpt`, `density`, and
   `accumulate` are read-only carriers and the assembly returns a fresh mapping. -/
method buildHistOptionsM
    (boundsOpt : Option (Float × Float)) (density : Bool) (accumulate : Bool)
    return (out : HistOptions)
  ensures out = buildHistOptions boundsOpt density accumulate
  ensures out.boundsOpt = boundsOpt
  ensures (density = true ∧ accumulate = false) → out.densityOpt = some density
  ensures ¬(density = true ∧ accumulate = false) → out.densityOpt = none
  do
    -- impl-start
    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
    let result : HistOptions :=
      if density && !accumulate then
        { base with densityOpt := some density }
      else
        base
    return result
    -- impl-end

prove_correct buildHistOptionsM by
  loom_solve
  cases density <;> cases accumulate <;> simp_all [buildHistOptions]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Same_spec=True verified for all 9 files via swebench_unified.markers.same_spec (velvet).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean -> EXIT 0 (verifies). Positive control OK.
- atk_prepatch.lean -> EXIT 1. Reproduces the gold bug (`hist_kwargs = dict(density=density)` -> {boundsOpt:=none,...}); fails frozen spec with goal `none = boundsOpt` unprovable + the `out = buildHistOptions ...` clause. G-DIFF confirmed.
- atk_1_boundary.lean (drops `density &&` guard) -> EXIT 1 (rejected).
- atk_2_wrongval.lean (some (!density)) -> EXIT 1 (rejected).
- atk_3_partialdomain.lean (density only when boundsOpt.isSome) -> EXIT 1 (rejected).
- atk_5_echo.lean (ungrounded-oracle echo: return buildHistOptions ...) -> EXIT 1 (frozen prove_correct tactic script doesn't discharge the echo form; behaviorally identical to gold but does not verify — a proof-script artifact, not a spec weakness).
- atk_6_dropbounds.lean (unconditional bounds drop) -> EXIT 1 (rejected).
- atk_7_swapguard.lean (guard uses accumulate instead of !accumulate) -> EXIT 1 (rejected).
- atk_4_cfsame.lean (control-flow-effect variant: rebuild the whole HistOptions record { boundsOpt := boundsOpt, densityOpt := (if density && !accumulate then some density else none) }; behaviorally identical to gold) -> EXIT 0 (VERIFIES).

MANDATORY RESOLVE of the one verifying wrong impl (atk_4_cfsame): materialized faithful patch atk_4_faithful.patch (Python transliteration of the record-rebuild: capture existing 'range' entry, rebind hist_kwargs to a fresh dict, re-add 'range' if present, then add 'density'). git apply --check OK on clean base worktree (@ a3e2897bfa). RAN through the official harness; result = RESOLVED. Evidence: my own fresh direct harness run report atk4_report.json (run_id sbu-audit-ucq-atk4-loop1) -> patch_successfully_applied=True, resolved=True, FAIL_TO_PASS success=['lib/matplotlib/tests/test_axes.py::test_hist_range_and_density'], F2P failure=[], PASS_TO_PASS failure=[].

Independently corroborated by an earlier run_resolve run (run_id ...-p859040) whose report.json for the BYTE-IDENTICAL patch (sha 9c84edc4b8) also showed resolved=true. NOTE on harness flakiness: two run_resolve invocations (p894970, p1039098) returned resolved=False with note 'no report ... harness error or image pull failure'. Root cause diagnosed (direct_run*.out): swebench harness crashed in list_images() with docker.errors.ImageNotFound (404 on an image sha that a concurrent process deleted mid-enumeration) — a docker contention race, the fail-closed-to-INCONCLUSIVE class the audit protocol documents, NOT a patch non-resolve. Docker + the eval image (swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-13989:latest) are present and responsive. Retrying the harness directly produced the clean resolved=True report above.

refinement.md AUDIT: meta.json axioms=[] and deep_model_references=[] -> NO A-legs (no axioms, no A-reference deep models). The A-leg / deep-model correspondence concern is moot for this bundle. All legs A1-A6 are R (type refinement) or I (identical concrete op), modeled deeply as buildHistOptions. Verified the model<->patch correspondence against the real source _axes.py: hist_kwargs=dict(), hist_kwargs['range']=bin_range (:6685 else-branch, single-dataset path), density=bool(density) or bool(normed) + `if density and not stacked:`, gold hunk `hist_kwargs['density'] = density` (:6689 post-image). Leg A4 (`{ base with densityOpt := ... }` <-> in-place key add) and the prepatch model (`hist_kwargs = dict(density=density)` -> {boundsOpt:=none,...}) both match. No kind-3 (inexpressible-changed-op) legs. mapping.md bijection ('range' in d <-> boundsOpt=some, 'density' in d <-> densityOpt=some) is sound; downstream np.histogram is the unchanged G-RESOLVE oracle, correctly not modeled.

WHY SOUND: the frozen spec's FIRST postcondition `out = buildHistOptions boundsOpt density accumulate` fully pins the output to the total deep model on every input, so any verifying impl returns exactly the gold output over the whole finite control space. The only verifying same-spec wrong impl (atk_4, a mere control-flow rearrangement) is behaviorally gold-equivalent and its faithful refined patch RESOLVES under the harness. No verifying impl produces a non-resolving faithful patch. verify => correct holds. G-CONF (conformance_check.py) additionally cross-checks the R/I shadow vs the patched assembly over the full finite control space + fuzz (seed 13989).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_1_boundary.lean`, `atk_2_wrongval.lean`, `atk_3_partialdomain.lean`, `atk_5_echo.lean`, `atk_6_dropbounds.lean`, `atk_7_swapguard.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4_cfsame.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_boundary.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_wrongval.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_partialdomain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_cfsame.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_5_echo.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_dropbounds.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_swapguard.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation under specification is the pure
--  assembly of the keyword-option mapping handed to the histogram routine; it
--  is modeled DEEPLY in the `pure` region below. The downstream histogram
--  computation that consumes these options is unchanged and is not modeled —
--  it owes no contract here.)
-- axioms-end

-- pure-start
/- The keyword-option mapping assembled for a single histogram computation,
   reduced to the two entries this assembly decides:
     * `boundsOpt`  — the explicit lower/upper data bounds entry, present
                      (`some`) when bounds were determined for this computation
                      and absent (`none`) otherwise;
     * `densityOpt` — the normalize-to-a-density entry, present (`some b`) when
                      the assembly records the density choice and absent
                      (`none`) when it does not.
   The two bounds are carried opaquely (their numeric values are never inspected
   here); only their presence and identity matter to this assembly. -/
structure HistOptions where
  boundsOpt  : Option (Float × Float)
  densityOpt : Option Bool
  deriving Inhabited

/- Assemble the option mapping. The mapping starts carrying whatever bounds
   entry was already determined (`boundsOpt`) and no density entry. When the
   density choice is recorded for a non-accumulated computation, the density
   entry is ADDED to that same mapping — the already-present bounds entry is
   carried through unchanged, never discarded. In every other case the mapping
   is left as it began. -/
def buildHistOptions
    (boundsOpt : Option (Float × Float)) (density accumulate : Bool) : HistOptions :=
  let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
  if density && !accumulate then { base with densityOpt := some density } else base

@[grind] lemma buildHistOptions_bounds
    (boundsOpt : Option (Float × Float)) (density accumulate : Bool) :
    (buildHistOptions boundsOpt density accumulate).boundsOpt = boundsOpt := by
  unfold buildHistOptions
  cases density <;> cases accumulate <;> simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the keyword-option mapping for a single histogram computation.

   The desired behaviour the issue demands: recording the density choice must
   NOT cause the explicitly-determined bounds entry to be lost. Concretely:

   - the bounds entry of the assembled mapping is ALWAYS exactly the bounds
     entry that was already determined (`out.boundsOpt = boundsOpt`) — adding
     the density entry never discards or alters it;
   - the density entry is present and records the density choice exactly when
     the density choice applies to this computation (a density computation that
     is not accumulated); otherwise the density entry is absent.

   None of the inputs are mutated (directive 5): `boundsOpt`, `density`, and
   `accumulate` are read-only carriers and the assembly returns a fresh mapping. -/
method buildHistOptionsM
    (boundsOpt : Option (Float × Float)) (density : Bool) (accumulate : Bool)
    return (out : HistOptions)
  ensures out = buildHistOptions boundsOpt density accumulate
  ensures out.boundsOpt = boundsOpt
  ensures (density = true ∧ accumulate = false) → out.densityOpt = some density
  ensures ¬(density = true ∧ accumulate = false) → out.densityOpt = none
  do
    -- impl-start
    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
    let result : HistOptions :=
      if density && !accumulate then
        { base with densityOpt := some density }
      else
        base
    return result
    -- impl-end

prove_correct buildHistOptionsM by
  loom_solve
  cases density <;> cases accumulate <;> simp_all [buildHistOptions]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Same_spec=True verified for all 9 files via swebench_unified.markers.same_spec (velvet).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean -> EXIT 0 (verifies). Positive control OK.
- atk_prepatch.lean -> EXIT 1. Reproduces the gold bug (`hist_kwargs = dict(density=density)` -> {boundsOpt:=none,...}); fails frozen spec with goal `none = boundsOpt` unprovable + the `out = buildHistOptions ...` clause. G-DIFF confirmed.
- atk_1_boundary.lean (drops `density &&` guard) -> EXIT 1 (rejected).
- atk_2_wrongval.lean (some (!density)) -> EXIT 1 (rejected).
- atk_3_partialdomain.lean (density only when boundsOpt.isSome) -> EXIT 1 (rejected).
- atk_5_echo.lean (ungrounded-oracle echo: return buildHistOptions ...) -> EXIT 1 (frozen prove_correct tactic script doesn't discharge the echo form; behaviorally identical to gold but does not verify — a proof-script artifact, not a spec weakness).
- atk_6_dropbounds.lean (unconditional bounds drop) -> EXIT 1 (rejected).
- atk_7_swapguard.lean (guard uses accumulate instead of !accumulate) -> EXIT 1 (rejected).
- atk_4_cfsame.lean (control-flow-effect variant: rebuild the whole HistOptions record { boundsOpt := boundsOpt, densityOpt := (if density && !accumulate then some density else none) }; behaviorally identical to gold) -> EXIT 0 (VERIFIES).

MANDATORY RESOLVE of the one verifying wrong impl (atk_4_cfsame): materialized faithful patch atk_4_faithful.patch (Python transliteration of the record-rebuild: capture existing 'range' entry, rebind hist_kwargs to a fresh dict, re-add 'range' if present, then add 'density'). git apply --check OK on clean base worktree (@ a3e2897bfa). RAN through the official harness; result = RESOLVED. Evidence: my own fresh direct harness run report atk4_report.json (run_id sbu-audit-ucq-atk4-loop1) -> patch_successfully_applied=True, resolved=True, FAIL_TO_PASS success=['lib/matplotlib/tests/test_axes.py::test_hist_range_and_density'], F2P failure=[], PASS_TO_PASS failure=[].

Independently corroborated by an earlier run_resolve run (run_id ...-p859040) whose report.json for the BYTE-IDENTICAL patch (sha 9c84edc4b8) also showed resolved=true. NOTE on harness flakiness: two run_resolve invocations (p894970, p1039098) returned resolved=False with note 'no report ... harness error or image pull failure'. Root cause diagnosed (direct_run*.out): swebench harness crashed in list_images() with docker.errors.ImageNotFound (404 on an image sha that a concurrent process deleted mid-enumeration) — a docker contention race, the fail-closed-to-INCONCLUSIVE class the audit protocol documents, NOT a patch non-resolve. Docker + the eval image (swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-13989:latest) are present and responsive. Retrying the harness directly produced the clean resolved=True report above.

refinement.md AUDIT: meta.json axioms=[] and deep_model_references=[] -> NO A-legs (no axioms, no A-reference deep models). The A-leg / deep-model correspondence concern is moot for this bundle. All legs A1-A6 are R (type refinement) or I (identical concrete op), modeled deeply as buildHistOptions. Verified the model<->patch correspondence against the real source _axes.py: hist_kwargs=dict(), hist_kwargs['range']=bin_range (:6685 else-branch, single-dataset path), density=bool(density) or bool(normed) + `if density and not stacked:`, gold hunk `hist_kwargs['density'] = density` (:6689 post-image). Leg A4 (`{ base with densityOpt := ... }` <-> in-place key add) and the prepatch model (`hist_kwargs = dict(density=density)` -> {boundsOpt:=none,...}) both match. No kind-3 (inexpressible-changed-op) legs. mapping.md bijection ('range' in d <-> boundsOpt=some, 'density' in d <-> densityOpt=some) is sound; downstream np.histogram is the unchanged G-RESOLVE oracle, correctly not modeled.

WHY SOUND: the frozen spec's FIRST postcondition `out = buildHistOptions boundsOpt density accumulate` fully pins the output to the total deep model on every input, so any verifying impl returns exactly the gold output over the whole finite control space. The only verifying same-spec wrong impl (atk_4, a mere control-flow rearrangement) is behaviorally gold-equivalent and its faithful refined patch RESOLVES under the harness. No verifying impl produces a non-resolving faithful patch. verify => correct holds. G-CONF (conformance_check.py) additionally cross-checks the R/I shadow vs the patched assembly over the full finite control space + fuzz (seed 13989).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: NO divergence found. Modeled function buildHistOptions (Option(Float×Float) -> Bool -> Bool -> HistOptions) faithfully models the option-mapping assembly in matplotlib.axes._axes.Axes.hist. Verified against the REAL repo at base_commit a3e2897bfaf9eaac1d6649da535c4e721c89fa69 (freshly cloned to): BASE line 6689 `hist_kwargs = dict(density=density)` (rebinds, drops 'range') vs POST 3.6.0 `hist_kwargs['density'] = density` (in-place add, keeps 'range') — the real fix. Bijection (mapping.md §2): boundsOpt<->'range' entry, density<->coerced density local, accumulate<->stacked. Over the FULL modeled domain the spec's three post-conditions match the real post-patch callee: (1) out.boundsOpt = boundsOpt always (matches in-place add preserving 'range'); (2) densityOpt present iff density∧¬accumulate (matches `if density and not stacked`); (3) else none. G-CONF differential test (conformance_check.py, seed 13989) ran 100,012 inputs (12 exhaustive control-space + seeded fuzz) with 0 disagreements between the R/I shadow and the verbatim-transliterated patched assembly block. Probed drift candidates: multi-dataset branch (range routed via histogram_bin_edges) is faithfully collapsed into boundsOpt=none and is not the bug site; the all-nan `hist_kwargs['range']=None` case maps to 'entry present, opaque' and does not affect the assembly's decision; the `bool(density) or bool(normed)` coercion correctly sits at the abstraction boundary. same_spec(Solution, Solution_prepatch, velvet)=True (spec region intact). Solution.lean verifies (lean_verify RC=0); Solution_prepatch.lean FAILS precisely on `none = boundsOpt` in the density=true,accumulate=false case (spec is discriminating, not vacuous, not too-strong-and-uninhabited). The spec is exactly as strong as the real behavior — no input makes the model disagree with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True), so the frozen spec view carries no add-vs-replace signal; the gold discriminator lives in the elided impl/proof. Mechanical leakage.screen also passes (no hard failures).

Semantic judgment (spec view vs PUBLIC problem_statement, not hints_text): NO LEAKAGE. The public problem_statement already fully discloses the desired behavior: title 'hist() no longer respects range=... when density=True', repro plt.hist(np.random.rand(10), 'auto', range=(0,1), density=True) with expected bins[0]==0 / bins[-1]==1, and the explicit note 'this bug doesn't happen if density=False'. That is the complete behavioral requirement — preserve the requested range/bounds even on the density path.

The spec view only re-expresses that same publicly-known requirement in an abstract model (HistOptions{boundsOpt, densityOpt}) with postconditions out.boundsOpt = boundsOpt and density recorded iff density && !accumulate. Crucially the spec view contains NONE of the gold-patch specifics: no hist_kwargs, no dict(density=density), no hist_kwargs['density']=density, no np.histogram, no file/line references — those Python-level details appear only in refinement.md/mapping.md, which are not part of the spec view. The prose word 'ADDED / carried through unchanged, never discarded' describes abstract preserve-bounds behavior identical in content to what the bug report demands, not the literal replace-vs-add source syntax. An auditor could reconstruct the required behavior from the public bug report alone; the spec view leaks nothing about the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
