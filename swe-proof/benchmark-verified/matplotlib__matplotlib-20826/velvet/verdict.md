# P2 adversarial audit — matplotlib__matplotlib-20826

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -42,8 +42,8 @@
   ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
   do
     -- impl-start
-    majorKw := Function.update majorKw key majorVal
-    minorKw := Function.update minorKw key minorVal
+    majorKw := Function.update majorKw key minorVal
+    minorKw := Function.update minorKw key majorVal
     return
     -- impl-end
 
@@ -52,3 +52,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -43,7 +43,6 @@
   do
     -- impl-start
     majorKw := Function.update majorKw key majorVal
-    minorKw := Function.update minorKw key minorVal
     return
     -- impl-end
 
@@ -52,3 +51,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -42,8 +42,8 @@
   ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
   do
     -- impl-start
-    majorKw := Function.update majorKw key majorVal
-    minorKw := Function.update minorKw key minorVal
+    majorKw := Function.update majorKw "gridOff" majorVal
+    minorKw := Function.update minorKw "gridOff" minorVal
     return
     -- impl-end
 
@@ -52,3 +52,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -42,8 +42,6 @@
   ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
   do
     -- impl-start
-    majorKw := Function.update majorKw key majorVal
-    minorKw := Function.update minorKw key minorVal
     return
     -- impl-end
 
@@ -52,3 +50,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -42,7 +42,7 @@
   ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
   do
     -- impl-start
-    majorKw := Function.update majorKw key majorVal
+    majorKw := Function.update majorKw key (!majorVal)
     minorKw := Function.update minorKw key minorVal
     return
     -- impl-end
@@ -52,3 +52,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -42,7 +42,7 @@
   ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
   do
     -- impl-start
-    majorKw := Function.update majorKw key majorVal
+    majorKw := Function.update majorKw key (majorKw key)
     minorKw := Function.update minorKw key minorVal
     return
     -- impl-end
@@ -52,3 +52,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -42,7 +42,7 @@
   ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
   do
     -- impl-start
-    majorKw := Function.update majorKw key majorVal
+    majorKw := Function.update (Function.update majorKw "tick1On" true) key majorVal
     minorKw := Function.update minorKw key minorVal
     return
     -- impl-end
@@ -52,3 +52,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -43,7 +43,7 @@
   do
     -- impl-start
     majorKw := Function.update majorKw key majorVal
-    minorKw := Function.update minorKw key minorVal
+    minorKw := Function.update (fun _ => false) key minorVal
     return
     -- impl-end
 
@@ -52,3 +52,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. The only repository behaviour this bundle relies on is the
@@ -43,6 +43,7 @@
   do
     -- impl-start
     majorKw := Function.update majorKw key majorVal
+    majorKw := Function.update majorKw key (!majorVal)
     minorKw := Function.update minorKw key minorVal
     return
     -- impl-end
@@ -52,3 +53,8 @@
     first
       | exact Function.update_self _ _ _
       | (intro k hk; exact Function.update_of_ne hk _ _)
+      | (intro k hk; simp_all [Function.update])
+      | simp_all [Function.update]
+      | (intros; simp_all)
+      | tauto
+      | rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms. The only repository behaviour this bundle relies on is the
-- in-place update of one entry of a settings map while every other entry is
-- preserved (a pure data-structure property), modeled directly below. There is
-- no unchanged callee whose contract must be assumed. (mapping.md §3.)
-- axioms-end

-- pure-start
-- No pure helpers are required: the modeled behaviour is the single
-- `Function.update` of a total settings map, whose frame property
-- (`Function.update_of_ne`) is library knowledge `loom_solve` discharges.
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resetting an axis re-derives exactly one tick-keyword entry — the
   distinguished `key` (recomputed to `majorVal`/`minorVal` from the ambient
   configuration) — for each of the two tick-keyword settings maps, and leaves
   every other entry of both maps untouched. Modeling each map as a total
   function `String → Bool` from a setting name to its on/off flag: the
   per-side visibility flags that callers (e.g. linked axes) have set must
   survive a reset; only the recomputed entry changes. -/
method resetAxisTickKeywords
    (mut majorKw : String → Bool) (mut minorKw : String → Bool)
    (key : String) (majorVal : Bool) (minorVal : Bool)
    return (u : Unit)
  ensures majorKw key = majorVal
  ensures minorKw key = minorVal
  ensures ∀ k, k ≠ key → majorKw k = majorKwOld k
  ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
  do
    -- impl-start
    majorKw := (fun k => if k = key then majorVal else majorKw k)
    minorKw := (fun k => if k = key then minorVal else minorKw k)
    return
    -- impl-end

prove_correct resetAxisTickKeywords by
  loom_solve <;>
    first
      | exact Function.update_self _ _ _
      | (intro k hk; exact Function.update_of_ne hk _ _)
```

Prepatch bug re-encoded as an attack: `True`.

All commands were run from there (scripts/lean_verify.sh, swebench_unified.markers.same_spec via python).

SPEC SHAPE: resetAxisTickKeywords is a COMPLETE functional spec — four postconditions pin the entire post-state of BOTH mutated maps: value-at-key (`majorKw key = majorVal`, `minorKw key = minorVal`) AND the full frame (`∀ k ≠ key → majorKw k = majorKwOld k`, minor analogue). This leaves zero behavioral freedom for a verifying impl, so a verifying-but-wrong impl is structurally implausible. I attacked it anyway.

SAME-SPEC VALIDATION: same_spec discriminates correctly — perturbing a postcondition (majorVal→minorVal) flips it to False; perturbing only the proof body keeps it True. spec_view elides BOTH the impl region and the prove_correct body, so my attacks used an AGGRESSIVE proof tail (added simp_all[Function.update], tauto, rfl, intros;simp_all fallbacks) to maximize the chance a wrong impl false-verifies, while same_spec stayed True for all 10 files (confirmed).

### ATTACKS (all same_spec=True, all verify rc=1 = REJECTED; cmd: `bash scripts/lean_verify.sh <path>`):
- atk_2 value-swap (major↔minor vals) → rc=1, rejected by `ensures minorKw key = minorVal`.
- atk_3 partial-domain, omit minor update → rc=1, rejected by `ensures minorKw key = minorVal` (minorKwOld key ≠ minorVal).
- atk_4 boundary, wrong hardcoded key literal "gridOff" → rc=1, rejected by value clause + frame.
- atk_5 partial-domain, no-op (bare return) → rc=1.
- atk_6 boundary, negated value (!majorVal) → rc=1.
- atk_7 ungrounded-oracle echo, write current `majorKw key` instead of majorVal → rc=1, rejected by `majorKw key = majorVal`.
- atk_8 frame-corrupt, also set "tick1On":=true → rc=1, rejected precisely by major frame (unsolved goal `k="tick1On" → majorKwOld "tick1On" = true`).
- atk_9 control-flow-effect, blank minor map (fun _=>false) before write (prepatch bug on minor) → rc=1, rejected by minor frame.
- atk_10 control-flow, correct write then overwrite key with (!majorVal) (last-write-wins wrong) → rc=1.

POSITIVE CONTROL (non-vacuity): atk_pc uses a structurally-different correct impl `fun k => if k = key then val else map k` (if-then-else instead of Function.update) → rc=0 VERIFIES clean (only linter unreachable/unusedTactic warnings). Spec is satisfiable & non-vacuous.

PREPATCH: Solution_prepatch.lean (clear-then-write both maps via Function.update (fun x=>false) key val) → rc=1, rejected precisely on BOTH frame postconditions — the wiped map cannot equal its old value. This is exactly the real bug (dict.clear() wiping per-side visibility flags shared axes turned off). Bug reproduced.

STEP 2 (materialize faithful patch + run_resolve): NOT TRIGGERED. The protocol mandates a resolve run only for a wrong impl that VERIFIES. Zero wrong impls verified (all rc=1), so there is no verifying-wrong-impl whose faithful patch could fail to resolve. patches={} accordingly. No verify⇏correct witness exists.

REFINEMENT/A-LEG AUDIT (§4, refinement.md + mapping.md §3): NO axioms and NO A-reference deep model. Solution.lean declares no `axiom`; meta.json axioms:[] ; no axiom_check.py (G-AX=skip, correctly). Every refinement leg is R (dict[str,bool] ↔ total String→Bool map; 'gridOn' ↔ key; the rcParams expr ↔ majorVal/minorVal as method inputs) or I (the two in-place single-entry writes = Function.update). No kind-3 (inexpressible-changed-op) leg: the genuinely-changed op (clear-then-repopulate → in-place single-entry write) is modeled DIRECTLY by Function.update with the dropped frame pinned by the two frame postconditions. Function.update_of_ne / update_self are Mathlib library facts, not repo assumptions. There are no A-legs whose callee-correspondence could be broken, so the A-leg attack surface this reviewer targets is empty here. meta.json corroborates: G-CONF pass (100006 inputs, seed 20826, 0 disagreements), G-RESOLVE pass, G-EQ pass, G-PANEL pass.

VERDICT: SOUND. ≥5 distinct wrong impls (9 total, spanning value-swap, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, frame-corruption) plus prepatch were encoded, all same_spec=True, all verify-REJECTED; positive control verifies. No verifying wrong impl was found, so verify⇒correct holds for this frozen spec and no faithful-patch resolve run was required. Spec is tight (full frame + value clauses), axiom-free, no kind-3 refinement.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms. The only repository behaviour this bundle relies on is the
-- in-place update of one entry of a settings map while every other entry is
-- preserved (a pure data-structure property), modeled directly below. There is
-- no unchanged callee whose contract must be assumed. (mapping.md §3.)
-- axioms-end

-- pure-start
-- No pure helpers are required: the modeled behaviour is the single
-- `Function.update` of a total settings map, whose frame property
-- (`Function.update_of_ne`) is library knowledge `loom_solve` discharges.
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resetting an axis re-derives exactly one tick-keyword entry — the
   distinguished `key` (recomputed to `majorVal`/`minorVal` from the ambient
   configuration) — for each of the two tick-keyword settings maps, and leaves
   every other entry of both maps untouched. Modeling each map as a total
   function `String → Bool` from a setting name to its on/off flag: the
   per-side visibility flags that callers (e.g. linked axes) have set must
   survive a reset; only the recomputed entry changes. -/
method resetAxisTickKeywords
    (mut majorKw : String → Bool) (mut minorKw : String → Bool)
    (key : String) (majorVal : Bool) (minorVal : Bool)
    return (u : Unit)
  ensures majorKw key = majorVal
  ensures minorKw key = minorVal
  ensures ∀ k, k ≠ key → majorKw k = majorKwOld k
  ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
  do
    -- impl-start
    majorKw := (fun k => if k = key then majorVal else majorKw k)
    minorKw := (fun k => if k = key then minorVal else minorKw k)
    return
    -- impl-end

prove_correct resetAxisTickKeywords by
  loom_solve <;>
    first
      | exact Function.update_self _ _ _
      | (intro k hk; exact Function.update_of_ne hk _ _)
```

Prepatch bug re-encoded as an attack: `True`.

All commands were run from there (scripts/lean_verify.sh, swebench_unified.markers.same_spec via python).

SPEC SHAPE: resetAxisTickKeywords is a COMPLETE functional spec — four postconditions pin the entire post-state of BOTH mutated maps: value-at-key (`majorKw key = majorVal`, `minorKw key = minorVal`) AND the full frame (`∀ k ≠ key → majorKw k = majorKwOld k`, minor analogue). This leaves zero behavioral freedom for a verifying impl, so a verifying-but-wrong impl is structurally implausible. I attacked it anyway.

SAME-SPEC VALIDATION: same_spec discriminates correctly — perturbing a postcondition (majorVal→minorVal) flips it to False; perturbing only the proof body keeps it True. spec_view elides BOTH the impl region and the prove_correct body, so my attacks used an AGGRESSIVE proof tail (added simp_all[Function.update], tauto, rfl, intros;simp_all fallbacks) to maximize the chance a wrong impl false-verifies, while same_spec stayed True for all 10 files (confirmed).

### ATTACKS (all same_spec=True, all verify rc=1 = REJECTED; cmd: `bash scripts/lean_verify.sh <path>`):
- atk_2 value-swap (major↔minor vals) → rc=1, rejected by `ensures minorKw key = minorVal`.
- atk_3 partial-domain, omit minor update → rc=1, rejected by `ensures minorKw key = minorVal` (minorKwOld key ≠ minorVal).
- atk_4 boundary, wrong hardcoded key literal "gridOff" → rc=1, rejected by value clause + frame.
- atk_5 partial-domain, no-op (bare return) → rc=1.
- atk_6 boundary, negated value (!majorVal) → rc=1.
- atk_7 ungrounded-oracle echo, write current `majorKw key` instead of majorVal → rc=1, rejected by `majorKw key = majorVal`.
- atk_8 frame-corrupt, also set "tick1On":=true → rc=1, rejected precisely by major frame (unsolved goal `k="tick1On" → majorKwOld "tick1On" = true`).
- atk_9 control-flow-effect, blank minor map (fun _=>false) before write (prepatch bug on minor) → rc=1, rejected by minor frame.
- atk_10 control-flow, correct write then overwrite key with (!majorVal) (last-write-wins wrong) → rc=1.

POSITIVE CONTROL (non-vacuity): atk_pc uses a structurally-different correct impl `fun k => if k = key then val else map k` (if-then-else instead of Function.update) → rc=0 VERIFIES clean (only linter unreachable/unusedTactic warnings). Spec is satisfiable & non-vacuous.

PREPATCH: Solution_prepatch.lean (clear-then-write both maps via Function.update (fun x=>false) key val) → rc=1, rejected precisely on BOTH frame postconditions — the wiped map cannot equal its old value. This is exactly the real bug (dict.clear() wiping per-side visibility flags shared axes turned off). Bug reproduced.

STEP 2 (materialize faithful patch + run_resolve): NOT TRIGGERED. The protocol mandates a resolve run only for a wrong impl that VERIFIES. Zero wrong impls verified (all rc=1), so there is no verifying-wrong-impl whose faithful patch could fail to resolve. patches={} accordingly. No verify⇏correct witness exists.

REFINEMENT/A-LEG AUDIT (§4, refinement.md + mapping.md §3): NO axioms and NO A-reference deep model. Solution.lean declares no `axiom`; meta.json axioms:[] ; no axiom_check.py (G-AX=skip, correctly). Every refinement leg is R (dict[str,bool] ↔ total String→Bool map; 'gridOn' ↔ key; the rcParams expr ↔ majorVal/minorVal as method inputs) or I (the two in-place single-entry writes = Function.update). No kind-3 (inexpressible-changed-op) leg: the genuinely-changed op (clear-then-repopulate → in-place single-entry write) is modeled DIRECTLY by Function.update with the dropped frame pinned by the two frame postconditions. Function.update_of_ne / update_self are Mathlib library facts, not repo assumptions. There are no A-legs whose callee-correspondence could be broken, so the A-leg attack surface this reviewer targets is empty here. meta.json corroborates: G-CONF pass (100006 inputs, seed 20826, 0 disagreements), G-RESOLVE pass, G-EQ pass, G-PANEL pass.

VERDICT: SOUND. ≥5 distinct wrong impls (9 total, spanning value-swap, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, frame-corruption) plus prepatch were encoded, all same_spec=True, all verify-REJECTED; positive control verifies. No verifying wrong impl was found, so verify⇒correct holds for this frozen spec and no faithful-patch resolve run was required. Spec is tight (full frame + value clauses), axiom-free, no kind-3 refinement.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attempt failed to break the spec. Solution.lean verifies (lean_verify.sh exit 0). Modeled resetAxisTickKeywords: majorKw/minorKw : String->Bool total maps, key='gridOn', majorVal/minorVal = recomputed rcParams flags supplied as inputs. Gold patch replaces _reset_{major,minor}_tick_kw() (dict.clear()+rewrite gridOn) with in-place self._{major,minor}_tick_kw['gridOn']=(grid and which in ('both',side)); Lean models this as Function.update at key. Spec postconditions: majorKw key=majorVal, minorKw key=minorVal, and frame (all k!=key preserved). Empirically verified against the REAL patched Axis.clear (installed mpl 3.6.3 carries the identical fix hunk; base-commit patch applies cleanly): differential test of 2000 fuzzed inputs (seed 20826; keys gridOn/tick1On/tick2On/label1On/label2On/_customFlagA/_customFlagB, grid in {T,F}, which in {both,major,minor}) comparing the real clear() output dicts against the Function.update-at-gridOn shadow -> 0 mismatches. gridOn recomputed to exactly grid and which in ('both',side); every other entry preserved, none added/dropped. Frame clause matches real behavior; recomputed value read from same rcParams. No diverging input exists within the modeled boundary (the tick-keyword reset inside clear); other clear() side-effects are correctly out of scope per mapping.md. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction), matplotlib__matplotlib-20826 velvet. Spec view judged = markers.spec_view(Solution.lean, VelvetBackend): impl region -> 'implementation elided', prove_correct body elided, method header + docstring + all ensures kept. Auditor docs (mapping.md, refinement.md) are NOT part of the consumer view and were excluded. Verified mechanically: leakage.screen() passes with zero hard failures; same_spec(post, prepatch)=True (spec frozen; discriminator lives in the mut-frame ensures, not the impl); no relaxed_leakage flag and no RELAXED_LEAKAGE.md, so this is a strict NO-LEAKAGE judgment, not a deferral.

Gold edit (patch.diff): inside Axis.clear (lib/matplotlib/axis.py), replace self._reset_major_tick_kw()/_reset_minor_tick_kw() (each dict.clear() then re-set only gridOn) with in-place writes self._major_tick_kw['gridOn'] = (mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','major')) and the minor analogue; discriminating content = every non-gridOn tick-keyword entry (tick1On/tick2On/label1On/label2On visibility flags) is preserved.

What the public problem_statement already reveals: ax.clear() on shared axes un-hides tick labels and shows ticks that should be hidden; axes stay linked; regression 3.4.1->3.4.2. I.e. clear() is destroying shared-axis visibility state it should preserve.

Leakage findings beyond problem_statement: NONE.
- Concrete gold anchors ABSENT from the spec view: no patched file path (axis.py), no patched function (Axis.clear), no removed callees (_reset_major_tick_kw/_reset_minor_tick_kw), no dict-key literal 'gridOn', no rcParams['axes.grid']/axes.grid.which expression, no gold-diff line, no diff markers. These live only in the non-consumer auditor docs.
- Spec-view identifiers (resetAxisTickKeywords, majorKw, minorKw, key, majorVal, minorVal) are abstract model names; none embeds a patched repo symbol. Patched changed-symbol set reduces to 'clear', which is already public in the problem_statement (ax.clear()).
- The docstring states desired behavior abstractly ('re-derive exactly one distinguished entry key, leave every other entry untouched; per-side visibility flags set by linked axes must survive a reset'), which is what a spec must state and is consistent with the public symptom. It does NOT reproduce the hint-level mechanism verbatim and does NOT localize the edit.

Gold-reconstruction assessment: a solver holding only this spec view cannot reconstruct the gold PATCH (no file/function localization, no 'gridOn' key, no rcParams expression, no callee names). The spec reveals correct behavior at the abstract model level only, which is inherent to any spec and does not exceed what the public problem_statement implies. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
