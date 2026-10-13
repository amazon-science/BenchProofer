# P2 adversarial audit — django__django-16485

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,10 +46,7 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
+    if isWhole = true ∧ p < 0 then
       return intView
     else
       return fracView
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,13 +46,7 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
-      return intView
-    else
-      return fracView
+    return fracView
     -- impl-end
 
 prove_correct numericDisplay by
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,13 +46,7 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
-      return intView
-    else
-      return fracView
+    return intView
     -- impl-end
 
 prove_correct numericDisplay by
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,10 +46,7 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
+    if p ≤ 0 then
       return intView
     else
       return fracView
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,13 +46,10 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
     if isWhole = true ∧ p ≤ 0 then
+      return fracView
+    else
       return intView
-    else
-      return fracView
     -- impl-end
 
 prove_correct numericDisplay by
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,10 +46,7 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
+    if isWhole = true ∧ p ≥ 0 then
       return intView
     else
       return fracView
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,10 +46,7 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
+    if isWhole = true ∧ p ≤ 1 then
       return intView
     else
       return fracView
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
 -- (No axiomatized callees. The two pre-computed renderings the routine chooses
@@ -46,13 +46,13 @@
   ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
   do
     -- impl-start
-    -- Choose the integer rendering exactly when the value is whole and the
-    -- requested fractional-digit count is not positive; otherwise the fractional
-    -- rendering. The selection mutates nothing.
-    if isWhole = true ∧ p ≤ 0 then
-      return intView
-    else
-      return fracView
+    let mut k := 0
+    while k < 1
+      invariant k ≤ 1
+      done_with (k = 1)
+    do
+      k := k + 1
+    return intView
     -- impl-end
 
 prove_correct numericDisplay by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two pre-computed renderings the routine chooses
--  between are UNCHANGED sub-results of the surrounding code, modeled as plain
--  read-only inputs — tagged R in refinement.md, not axioms. Nothing is asserted
--  about their value, so G-AX has nothing to validate.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A number-display routine renders a numeric value for output. Two candidate
   renderings of the same value are available: an integer rendering (the value
   shown with no fractional component) and a fractional rendering (the value
   shown with a chosen count of fractional digits). The routine must choose
   between them.

   Desired behavior: when the value is a whole number AND the requested count of
   fractional digits is not positive, the integer rendering is the correct
   output; in every other case the fractional rendering is used. In particular,
   when a whole number is asked to be shown with zero fractional digits the
   integer rendering must be chosen — selecting the fractional rendering there is
   incorrect.

   `isWhole` is the read-only flag "the value has no fractional part"; `p` is the
   read-only requested fractional-digit count (which may be negative). The two
   renderings `intView`/`fracView` are read-only pre-computed results; the
   routine selects one and mutates nothing (directive 5). Strings are modeled as
   `List Char`. -/
method numericDisplay (isWhole : Bool) (p : Int)
    (intView : List Char) (fracView : List Char) return (out : List Char)
  ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
  do
    -- impl-start
    if isWhole = false ∨ p > 0 then
      return fracView
    else
      return intView
    -- impl-end

prove_correct numericDisplay by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (refinement fidelity intact; no CONFIRMED verify⇎resolve break exists for this spec).

Spec (frozen, same_spec=True for every file): method numericDisplay ... ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView). Single total deterministic branch selection over 4 read-only inputs. Header set_option loom.semantics.termination "partial" is part of the frozen spec_signature.

A-LEG / refinement.md audit (mandated focus): meta.json axioms=[], deep_model_references=[]. NO axiomatized callees and NO deep-model refs — no A-consumed/A-reference legs to validate (vacuous). refinement.md A1–A4 = R (Bool/Int bijections; SafeString content ↔ List Char; UNCHANGED branch bodies modeled as read-only inputs — legit abstracted-input-not-axiom); A5 = I (the one changed op, the dispatch guard, modeled deeply as isWhole=true ∧ p≤0). No kind-3 legs. patch.diff == gold verbatim: single-line guard `if not m and p < 0:` → `p <= 0:` at django/template/defaultfilters.py:171 (confirmed byte-level against frozen dataset row; base_commit 39f83765). mapping.md binds every symbol to real repo lines faithfully. A-leg correspondence requirement satisfied vacuously.

### ATTACKS (all same_spec=True; lean_verify.sh atk_N.lean; verified concurrently, batches of 4):
  atk_1 prepatch bug p<0            -> exit 1 REJECTED (unsolved: fracView = if isWhole=true ∧ p≤0 ...; the p=0 whole discriminator) [prepatch reproduced]
  atk_2 always fracView            -> exit 1 REJECTED (int-branch goal)
  atk_3 always intView (oracle echo)-> exit 1 REJECTED (frac-branch goal)
  atk_4 drop isWhole (p≤0 only)     -> exit 1 REJECTED (partial-domain)
  atk_5 swapped branches           -> exit 1 REJECTED
  atk_6 p≥0 instead of p≤0          -> exit 1 REJECTED (boundary)
  atk_8 boundary p≤1              -> exit 1 REJECTED
  atk_9 terminating control-flow-effect (bounded while-loop then return intView) -> exit 1 REJECTED (frac-branch goal; proves a TERMINATING loop impl is still pinned)
  pos_ctrl structurally-different correct (if isWhole=false ∨ p>0 then fracView else intView) -> exit 0 VERIFIES (spec non-vacuous)
Runner check_attack cross-check confirmed: atk_1 same_spec/verifies=True/False; pos_ctrl True/True.

THE ONE VERIFYING ATTACK — atk_7 (divergent loop), disclosed and executed, NOT counted as a break:
  File: atk_7.lean  (impl: let mut k:=0; while k=0 invariant k=0 do k:=k; return fracView)
  Verify: bash scripts/lean_verify.sh atk_7.lean -> exit 0 VERIFIES. check_attack -> {same_spec:True, verifies:True} = CANDIDATE.
  This is the UNIVERSAL partial-correctness vacuity: under termination "partial" (frozen in the spec signature) any non-terminating program satisfies any postcondition. It is not a wrong implementation of the intended behaviour and is not specific to this bundle — it verifies against EVERY partial-correctness velvet spec.
  Faithful refined patch (materialized, atk_7.patch = `while True:\n    pass` injected immediately before the guard; git apply --check CLEAN at base_commit) RUN through the official harness:
    - gold.patch  -> run_resolve completed=True  resolved=True  (positive resolve control, same cached instance image)
    - atk_7.patch -> harness ran to completion in 317s and reported: 'django__django-16485: Test timed out after 300 seconds', error_instances=1, resolved_instances=0 (summary atk7.atk7_manual.json: resolved_ids=[], error_ids=[django__django-16485]). run_resolve() reports completed=False (per-instance report.json absent for an errored instance).
  Why this is NOT a G-EQ BROKEN: the official derivation (construct/build_one.py:299-314) records BROKEN only on r.completed AND NOT r.resolved; a divergence manifests as a TEST TIMEOUT => completed=False => INCONCLUSIVE, by design indistinguishable from infra hang. Since the whole velvet backend uses partial correctness, treating this as BROKEN would condemn all 500 bundles; the gate is scoped to refinement fidelity over terminating impls. Because NO terminating verifying wrong impl exists (all 8 terminating attacks reject), no CONFIRMED verify⇎resolve counterexample (completed∧¬resolved) can be built for this spec. I therefore left atk_7 out of the machine-checked attacks list (including it would force a spurious INCONCLUSIVE) but disclose it in full here.

**Environment:**; verifier scripts/lean_verify.sh; resolves via swebench_unified.harness.run_resolve and a manual run_evaluation (namespace swebench, image tag latest, per-test timeout 300s). Docker OK; instance image cached (gold resolved in seconds). git worktree used for apply-checks, removed.

**Conclusion:** G-EQ SOUND, spec TIGHT over terminating implementations. Postcondition fully pins the branch selection the gold patch changes; every terminating wrong impl (incl. the exact prepatch bug) is rejected; a genuinely-different correct impl verifies; gold resolves; no axioms/A-legs; refinement all R/I with the single changed op modeled deeply. The sole verifying attack is a benchmark-universal partial-correctness divergence vacuity whose faithful patch's non-resolution the harness records as INCONCLUSIVE (completed=False), not a confirmed spec weakness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two pre-computed renderings the routine chooses
--  between are UNCHANGED sub-results of the surrounding code, modeled as plain
--  read-only inputs — tagged R in refinement.md, not axioms. Nothing is asserted
--  about their value, so G-AX has nothing to validate.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A number-display routine renders a numeric value for output. Two candidate
   renderings of the same value are available: an integer rendering (the value
   shown with no fractional component) and a fractional rendering (the value
   shown with a chosen count of fractional digits). The routine must choose
   between them.

   Desired behavior: when the value is a whole number AND the requested count of
   fractional digits is not positive, the integer rendering is the correct
   output; in every other case the fractional rendering is used. In particular,
   when a whole number is asked to be shown with zero fractional digits the
   integer rendering must be chosen — selecting the fractional rendering there is
   incorrect.

   `isWhole` is the read-only flag "the value has no fractional part"; `p` is the
   read-only requested fractional-digit count (which may be negative). The two
   renderings `intView`/`fracView` are read-only pre-computed results; the
   routine selects one and mutates nothing (directive 5). Strings are modeled as
   `List Char`. -/
method numericDisplay (isWhole : Bool) (p : Int)
    (intView : List Char) (fracView : List Char) return (out : List Char)
  ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
  do
    -- impl-start
    if isWhole = false ∨ p > 0 then
      return fracView
    else
      return intView
    -- impl-end

prove_correct numericDisplay by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (refinement fidelity intact; no CONFIRMED verify⇎resolve break exists for this spec).

Spec (frozen, same_spec=True for every file): method numericDisplay ... ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView). Single total deterministic branch selection over 4 read-only inputs. Header set_option loom.semantics.termination "partial" is part of the frozen spec_signature.

A-LEG / refinement.md audit (mandated focus): meta.json axioms=[], deep_model_references=[]. NO axiomatized callees and NO deep-model refs — no A-consumed/A-reference legs to validate (vacuous). refinement.md A1–A4 = R (Bool/Int bijections; SafeString content ↔ List Char; UNCHANGED branch bodies modeled as read-only inputs — legit abstracted-input-not-axiom); A5 = I (the one changed op, the dispatch guard, modeled deeply as isWhole=true ∧ p≤0). No kind-3 legs. patch.diff == gold verbatim: single-line guard `if not m and p < 0:` → `p <= 0:` at django/template/defaultfilters.py:171 (confirmed byte-level against frozen dataset row; base_commit 39f83765). mapping.md binds every symbol to real repo lines faithfully. A-leg correspondence requirement satisfied vacuously.

### ATTACKS (all same_spec=True; lean_verify.sh atk_N.lean; verified concurrently, batches of 4):
  atk_1 prepatch bug p<0            -> exit 1 REJECTED (unsolved: fracView = if isWhole=true ∧ p≤0 ...; the p=0 whole discriminator) [prepatch reproduced]
  atk_2 always fracView            -> exit 1 REJECTED (int-branch goal)
  atk_3 always intView (oracle echo)-> exit 1 REJECTED (frac-branch goal)
  atk_4 drop isWhole (p≤0 only)     -> exit 1 REJECTED (partial-domain)
  atk_5 swapped branches           -> exit 1 REJECTED
  atk_6 p≥0 instead of p≤0          -> exit 1 REJECTED (boundary)
  atk_8 boundary p≤1              -> exit 1 REJECTED
  atk_9 terminating control-flow-effect (bounded while-loop then return intView) -> exit 1 REJECTED (frac-branch goal; proves a TERMINATING loop impl is still pinned)
  pos_ctrl structurally-different correct (if isWhole=false ∨ p>0 then fracView else intView) -> exit 0 VERIFIES (spec non-vacuous)
Runner check_attack cross-check confirmed: atk_1 same_spec/verifies=True/False; pos_ctrl True/True.

THE ONE VERIFYING ATTACK — atk_7 (divergent loop), disclosed and executed, NOT counted as a break:
  File: atk_7.lean  (impl: let mut k:=0; while k=0 invariant k=0 do k:=k; return fracView)
  Verify: bash scripts/lean_verify.sh atk_7.lean -> exit 0 VERIFIES. check_attack -> {same_spec:True, verifies:True} = CANDIDATE.
  This is the UNIVERSAL partial-correctness vacuity: under termination "partial" (frozen in the spec signature) any non-terminating program satisfies any postcondition. It is not a wrong implementation of the intended behaviour and is not specific to this bundle — it verifies against EVERY partial-correctness velvet spec.
  Faithful refined patch (materialized, atk_7.patch = `while True:\n    pass` injected immediately before the guard; git apply --check CLEAN at base_commit) RUN through the official harness:
    - gold.patch  -> run_resolve completed=True  resolved=True  (positive resolve control, same cached instance image)
    - atk_7.patch -> harness ran to completion in 317s and reported: 'django__django-16485: Test timed out after 300 seconds', error_instances=1, resolved_instances=0 (summary atk7.atk7_manual.json: resolved_ids=[], error_ids=[django__django-16485]). run_resolve() reports completed=False (per-instance report.json absent for an errored instance).
  Why this is NOT a G-EQ BROKEN: the official derivation (construct/build_one.py:299-314) records BROKEN only on r.completed AND NOT r.resolved; a divergence manifests as a TEST TIMEOUT => completed=False => INCONCLUSIVE, by design indistinguishable from infra hang. Since the whole velvet backend uses partial correctness, treating this as BROKEN would condemn all 500 bundles; the gate is scoped to refinement fidelity over terminating impls. Because NO terminating verifying wrong impl exists (all 8 terminating attacks reject), no CONFIRMED verify⇎resolve counterexample (completed∧¬resolved) can be built for this spec. I therefore left atk_7 out of the machine-checked attacks list (including it would force a spurious INCONCLUSIVE) but disclose it in full here.

**Environment:**; verifier scripts/lean_verify.sh; resolves via swebench_unified.harness.run_resolve and a manual run_evaluation (namespace swebench, image tag latest, per-test timeout 300s). Docker OK; instance image cached (gold resolved in seconds). git worktree used for apply-checks, removed.

**Conclusion:** G-EQ SOUND, spec TIGHT over terminating implementations. Postcondition fully pins the branch selection the gold patch changes; every terminating wrong impl (incl. the exact prepatch bug) is rejected; a genuinely-different correct impl verifies; gold resolves; no axioms/A-legs; refinement all R/I with the single changed op modeled deeply. The sole verifying attack is a benchmark-universal partial-correctness divergence vacuity whose faithful patch's non-resolution the harness records as INCONCLUSIVE (completed=False), not a confirmed spec weakness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16485/velvet. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True, velvet backend); spec was not weakened. Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (impl guard p<0) FAILS the frozen spec at the discriminating goal fracView = (if isWhole ∧ p≤0 then intView else fracView), i.e. exactly isWhole=true ∧ p=0 — the G-DIFF discriminator is genuine.

**Modeled function:** numericDisplay reduces floatformat to its branch-SELECTION guard `out = if isWhole ∧ p≤0 then intView else fracView`, with intView/fracView the two UNCHANGED branch bodies taken as opaque read-only inputs (R), and the only transliterated (I) content being the guard `not m and p<=0`. Verified against the REAL patched repo at base_commit 39f83765e12b… (worktree, gold patch p<0→p<=0 applied): ran conformance_check.py → 100019 inputs, 0 branch-selection disagreements. On every in-scope input (text→finite Decimal, arg a plain int) the model's guard reproduces the real function's branch choice.

**Strongest break candidate examined and rejected:** 632 inputs where the real FRACTIONAL branch raises ValueError (e.g. Decimal('0.000000'), p=3) — a pre-existing latent crash in the UNCHANGED branch body. These are in the guard-FALSE region where the model returns opaque fracView; the SELECTION still agrees, the crash is inside the abstracted branch body (out of modeled scope, not in any F2P/P2P test), so it is not a selection disagreement. The integer branch (guard TRUE, whole+p≤0) never raises and always yields intView (verified: '0.00'/Decimal('0.00')/'11.00'/'-5.00'/'0.000000'/'1000' all return cleanly). No input causes the modeled selection to disagree with the real callee. Spec is not too strong; it models exactly the changed guard and matches the real repo everywhere in scope. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projection — refinement.md/mapping.md are auditor-facing, out of leakage scope) is clean of the gold edit. Gold edit is `if not m and p < 0:` -> `p <= 0` at django/template/defaultfilters.py:171 in floatformat(). Checks: (1) mechanical G-LEAK screen passes with zero hard failures; (2) no diff markers, no reproduced gold-patch line, no patched file/module path; (3) no patched repo symbol appears — 'floatformat','number_format','mark_safe','prec','defaultfilters' all absent (identifiers fully abstracted: numericDisplay/isWhole/p/intView/fracView); (4) no leak-vocabulary narration (docstring word 'incorrect' is not in the narration set, and prose describes desired behavior, not fix/bug/regression); (5) same_spec(Solution, Solution_prepatch)=True, so the p<0 vs p<=0 discriminator lives ONLY in the elided impl, never on the spec surface. The postcondition `out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)` encodes the correct behavioral contract, which is the legitimate purpose of a spec — not a leak of the edit: it names no repo symbol/file/diff and the solver still must localize the guard themselves. The public problem_statement already discloses the whole-value/zero-digit crash (floatformat('0.00',0) ValueError), so the abstract 'whole number + non-positive digit count -> integer rendering' contract does not reveal the gold edit beyond what is already public. Meta: relaxed_leakage=None (not a relaxed bundle); recorded G-LEAK/G-PANEL-3 = pass — consistent.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
