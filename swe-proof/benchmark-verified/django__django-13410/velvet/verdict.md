# P2 adversarial audit — django__django-13410

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 10 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The strongest wrong impl encoded was atk_3 (partial-domain: correct on `succeeded`, but reports a non-blocking CONTENDED acquisition as success -- exactly the F2P assertion `assertIs(locks.lock(f2, LOCK_EX|LOCK_NB), False)`); the spec REJECTS it (exit 1, unsolved goals at prove_correct). Every impl that verified had a faithful refined patch that RESOLVED under the official harness, so no verify-but-not-resolve witness exists.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
   do
     -- impl-start
     if outcome = LockOutcome.succeeded then
-      return true
+      return false
     else
       return false
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
   ensures out = true
   do
     -- impl-start
-    return true
+    return false
     -- impl-end
 
 prove_correct releaseLock by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
     if outcome = LockOutcome.succeeded then
       return true
     else
-      return false
+      return true
     -- impl-end
 
 prove_correct acquireLock by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,9 +56,9 @@
   do
     -- impl-start
     if outcome = LockOutcome.succeeded then
+      return false
+    else
       return true
-    else
-      return false
     -- impl-end
 
 prove_correct acquireLock by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,10 +55,7 @@
   ensures out = acquiredOk outcome
   do
     -- impl-start
-    if outcome = LockOutcome.succeeded then
-      return true
-    else
-      return false
+    return acquiredOk outcome
     -- impl-end
 
 prove_correct acquireLock by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,7 +56,10 @@
   do
     -- impl-start
     if outcome = LockOutcome.succeeded then
-      return true
+      if outcome = LockOutcome.succeeded then
+        return true
+      else
+        return false
     else
       return false
     -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,10 +55,9 @@
   ensures out = acquiredOk outcome
   do
     -- impl-start
-    if outcome = LockOutcome.succeeded then
-      return true
-    else
-      return false
+    match outcome with
+    | LockOutcome.succeeded => return true
+    | LockOutcome.contended => return false
     -- impl-end
 
 prove_correct acquireLock by
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,10 +55,7 @@
   ensures out = acquiredOk outcome
   do
     -- impl-start
-    if outcome = LockOutcome.succeeded then
-      return true
-    else
-      return false
+    return !(decide (outcome = LockOutcome.contended))
     -- impl-end
 
 prove_correct acquireLock by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,10 +55,7 @@
   ensures out = acquiredOk outcome
   do
     -- impl-start
-    if outcome = LockOutcome.succeeded then
-      return true
-    else
-      return false
+    return acquiredOk LockOutcome.succeeded
     -- impl-end
 
 prove_correct acquireLock by
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
   ensures out = true
   do
     -- impl-start
-    return true
+    return decide (LockOutcome.succeeded = LockOutcome.contended)
     -- impl-end
 
 prove_correct releaseLock by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The desired behaviour
   concerns only how a boolean success indicator is computed from the OUTCOME of
   the underlying operating-system lock primitive. That outcome is modeled
   directly as the input `LockOutcome` — an R-refinement of "the primitive
   completed normally" versus "under a non-blocking request the resource is
   already held". The primitive itself is unchanged; its outcome ↔ input
   correspondence, and the full decision, are validated against the real
   primitive by conformance_check.py (G-CONF). Nothing is axiomatized, so there
   is no axiom_check.py (G-AX = skip). -/
-- axioms-end

-- pure-start
/- The two observable outcomes of one call to the underlying operating-system
   lock primitive, as the caller perceives them:
   * `succeeded` — the primitive completed normally and the operation took
                   effect (on this path the primitive yields no value).
   * `contended` — under a non-blocking request the resource is already held,
                   so the primitive signals that the operation could not be
                   completed immediately. -/
inductive LockOutcome where
  | succeeded
  | contended
  deriving DecidableEq, Inhabited

/- The boolean success indicator an acquisition reports: it reports success
   exactly when the underlying primitive completed normally, and reports failure
   when a non-blocking request found the resource already held. The indicator is
   a definite boolean — completing normally is reported as `true`, never
   conflated with the primitive's no-value normal-completion result. -/
def acquiredOk (outcome : LockOutcome) : Bool :=
  decide (outcome = LockOutcome.succeeded)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Acquire a lock and report, as a definite boolean, whether it was obtained.
   Given the outcome of the underlying lock primitive, the result is `true` when
   the primitive completed normally and `false` when a non-blocking request
   found the resource already held. A caller relying on non-blocking acquisition
   can therefore tell an already-held resource apart from a free one. -/
method acquireLock (outcome : LockOutcome) return (out : Bool)
  ensures out = acquiredOk outcome
  do
    -- impl-start
    if outcome = LockOutcome.succeeded then
      return true
    else
      return false
    -- impl-end

prove_correct acquireLock by
  loom_solve <;> cases outcome <;> simp_all [acquiredOk]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Release a held lock and report success as a definite boolean. Releasing a
   held lock is reported as having succeeded (`true`), again a real boolean
   rather than the primitive's no-value normal-completion result. -/
method releaseLock return (out : Bool)
  ensures out = true
  do
    -- impl-start
    return true
    -- impl-end

prove_correct releaseLock by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 10 same-spec attacks + positive control, all. same_spec == True for ALL 11 files (swebench_unified.markers.same_spec, get_backend('velvet')); only the two impl regions were edited, axioms/pure/pre/post byte-identical. Verified via `bash scripts/lean_verify.sh <f>`. Runs were batched 4-at-a-time as background jobs.

### VERIFY MATRIX (exit 0 = verifies):
- pos_control.lean (gold impl) -> 0  [POSITIVE CONTROL OK]
- atk_1 (prepatch lock: `ret == 0` collapses to always-false) -> 1 REJECTED  [PREPATCH BUG REPRODUCED]
- atk_2 (prepatch unlock: release reports failure) -> 1 REJECTED  [PREPATCH BUG REPRODUCED]
- atk_3 (PARTIAL-DOMAIN: contended reported as success) -> 1 REJECTED
- atk_4 (inverted polarity) -> 1 REJECTED
- atk_9 (UNGROUNDED-ORACLE ECHO at a FIXED point: `return acquiredOk LockOutcome.succeeded`, ignores input) -> 1 REJECTED
- atk_10 (BOUNDARY/release: constant-false dressed as a decide) -> 1 REJECTED
- atk_5 (ungrounded-oracle echo `return acquiredOk outcome`) -> 0 VERIFIES
- atk_6 (CONTROL-FLOW-EFFECT: nested double test of the stored outcome) -> 0 VERIFIES
- atk_7 (match reshape) -> 0 VERIFIES
- atk_8 (negation reshape `!(decide (outcome = contended))`) -> 0 VERIFIES
All 6 rejections failed at `prove_correct` with `error: unsolved goals` (genuine postcondition refutation, NOT syntax errors -- log lines confirmed).

MANDATORY RESOLVE STEP -- every impl that VERIFIED had its faithful refined patch materialized against the real base_commit 580a4341 locks.py and executed through the official harness (`swebench_unified.harness.run_resolve`, instance django__django-13410, timeout 3600):
- patch_atk_5.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_atk_6.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_atk_7.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_atk_8.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_gold.diff (control, from the frozen dataset) -> resolved TRUE
No verifying impl's faithful patch failed to resolve => NO verify-not-correct witness => not BROKEN.

A-LEG AUDIT (my assigned focus). meta.json confirms axioms == [] and deep_model_references == [], so there are NO A-consumed and NO A-reference legs to over-claim: G-AX = skip is correct, and refinement.md's 'no A rows' claim is accurate. Refinement legs are A1 (R: LockOutcome <-> the fcntl.flock outcome), A2/A3 (I: concrete booleans), B1 (I: unconditional True). Every leg is R or I; NO kind-3 (inexpressible-changed-op) leg. The changed operation -- how the wrapper turns the primitive's outcome into a bool -- is modeled DIRECTLY in the pure region (acquiredOk) rather than hidden behind an axiom, which is the honest encoding. The A1 R-refinement's correspondence to the real callee holds: I confirmed against CPython semantics and the gold hunk that `succeeded` <-> flock returning (yielding None, never int 0) and `contended` <-> BlockingIOError under LOCK_NB, matching the F2P tests test_exclusive_lock/test_shared_lock which assert `assertIs(..., True/False)`.

THREE ADDITIONAL STRUCTURAL PROBES of the two genuine modeling gaps I identified, all executed through the harness (these probe correspondence, not spec strength):
1. probe_noeffect (patch_probe_noeffect.diff): `releaseLock` takes NO input and carries NO mutable frame, so the spec `out = true` cannot force the `fcntl.flock(_fd(f), LOCK_UN)` CALL. I dropped the release effect entirely (`def unlock(f): return True`). It RESOLVED (true) -- so this real under-specification is NOT observable by the F2P/P2P suite and cannot yield a break here. Recorded as a latent modeling gap: leg B1's effect is asserted by prose, not pinned by the spec.
2. probe_flags (patch_probe_flags.diff): mapping.md §2 declares `flags` unobservable; I ignored the caller's flags and always passed LOCK_SH|LOCK_NB. This did NOT resolve (3 attempts, consistent). Importantly this is NOT a spec break -- it is not a faithful refinement of any verifying impl (the model has no flags carrier, so the flag choice is fixed by the unchanged surrounding code, not by the impl region). It instead CONFIRMS that the mapping's 'flags unobservable beyond the resulting LockOutcome' abstraction is load-bearing and that the harness is sensitive here.
3. probe_oserror (patch_probe_oserror.diff): LockOutcome has only two constructors, so a third real outcome (a non-BlockingIOError OSError, e.g. EBADF) is inexpressible; I folded every OSError into the contended branch. RESOLVED (true) -- the domain gap is not test-observable.

CONCLUSION: 10 attacks encoded and fully verified, >= 5 distinct wrong-impl kinds (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, inverted, both prepatch bugs) all correctly REJECTED; positive control verifies; all 4 verifying reshapes' faithful patches RESOLVE. verify => correct holds on all evidence gathered. Verdict SOUND.

CAVEAT FOR THE RUNNER (not a G-EQ failure, but a bundle-integrity issue outside my gate): `patch.diff` is ABSENT from the bundle directory benchmark-verified/django__django-13410/velvet even though meta.json records G-RESOLVE = pass and patch_is_gold = true. gates/resolve.py returns `error: patch.diff missing` when it is absent, so a re-run of G-RESOLVE on this bundle as-shipped will ERROR. I sourced the gold patch from the frozen dataset (data/swe_bench_verified/test.jsonl) and confirmed it resolves; the bundle should have patch.diff restored before release.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 10 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The strongest wrong impl encoded was atk_3 (partial-domain: correct on `succeeded`, but reports a non-blocking CONTENDED acquisition as success -- exactly the F2P assertion `assertIs(locks.lock(f2, LOCK_EX|LOCK_NB), False)`); the spec REJECTS it (exit 1, unsolved goals at prove_correct). Every impl that verified had a faithful refined patch that RESOLVED under the official harness, so no verify-but-not-resolve witness exists.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The desired behaviour
   concerns only how a boolean success indicator is computed from the OUTCOME of
   the underlying operating-system lock primitive. That outcome is modeled
   directly as the input `LockOutcome` — an R-refinement of "the primitive
   completed normally" versus "under a non-blocking request the resource is
   already held". The primitive itself is unchanged; its outcome ↔ input
   correspondence, and the full decision, are validated against the real
   primitive by conformance_check.py (G-CONF). Nothing is axiomatized, so there
   is no axiom_check.py (G-AX = skip). -/
-- axioms-end

-- pure-start
/- The two observable outcomes of one call to the underlying operating-system
   lock primitive, as the caller perceives them:
   * `succeeded` — the primitive completed normally and the operation took
                   effect (on this path the primitive yields no value).
   * `contended` — under a non-blocking request the resource is already held,
                   so the primitive signals that the operation could not be
                   completed immediately. -/
inductive LockOutcome where
  | succeeded
  | contended
  deriving DecidableEq, Inhabited

/- The boolean success indicator an acquisition reports: it reports success
   exactly when the underlying primitive completed normally, and reports failure
   when a non-blocking request found the resource already held. The indicator is
   a definite boolean — completing normally is reported as `true`, never
   conflated with the primitive's no-value normal-completion result. -/
def acquiredOk (outcome : LockOutcome) : Bool :=
  decide (outcome = LockOutcome.succeeded)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Acquire a lock and report, as a definite boolean, whether it was obtained.
   Given the outcome of the underlying lock primitive, the result is `true` when
   the primitive completed normally and `false` when a non-blocking request
   found the resource already held. A caller relying on non-blocking acquisition
   can therefore tell an already-held resource apart from a free one. -/
method acquireLock (outcome : LockOutcome) return (out : Bool)
  ensures out = acquiredOk outcome
  do
    -- impl-start
    if outcome = LockOutcome.succeeded then
      return true
    else
      return false
    -- impl-end

prove_correct acquireLock by
  loom_solve <;> cases outcome <;> simp_all [acquiredOk]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Release a held lock and report success as a definite boolean. Releasing a
   held lock is reported as having succeeded (`true`), again a real boolean
   rather than the primitive's no-value normal-completion result. -/
method releaseLock return (out : Bool)
  ensures out = true
  do
    -- impl-start
    return true
    -- impl-end

prove_correct releaseLock by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 10 same-spec attacks + positive control, all. same_spec == True for ALL 11 files (swebench_unified.markers.same_spec, get_backend('velvet')); only the two impl regions were edited, axioms/pure/pre/post byte-identical. Verified via `bash scripts/lean_verify.sh <f>`. Runs were batched 4-at-a-time as background jobs.

### VERIFY MATRIX (exit 0 = verifies):
- pos_control.lean (gold impl) -> 0  [POSITIVE CONTROL OK]
- atk_1 (prepatch lock: `ret == 0` collapses to always-false) -> 1 REJECTED  [PREPATCH BUG REPRODUCED]
- atk_2 (prepatch unlock: release reports failure) -> 1 REJECTED  [PREPATCH BUG REPRODUCED]
- atk_3 (PARTIAL-DOMAIN: contended reported as success) -> 1 REJECTED
- atk_4 (inverted polarity) -> 1 REJECTED
- atk_9 (UNGROUNDED-ORACLE ECHO at a FIXED point: `return acquiredOk LockOutcome.succeeded`, ignores input) -> 1 REJECTED
- atk_10 (BOUNDARY/release: constant-false dressed as a decide) -> 1 REJECTED
- atk_5 (ungrounded-oracle echo `return acquiredOk outcome`) -> 0 VERIFIES
- atk_6 (CONTROL-FLOW-EFFECT: nested double test of the stored outcome) -> 0 VERIFIES
- atk_7 (match reshape) -> 0 VERIFIES
- atk_8 (negation reshape `!(decide (outcome = contended))`) -> 0 VERIFIES
All 6 rejections failed at `prove_correct` with `error: unsolved goals` (genuine postcondition refutation, NOT syntax errors -- log lines confirmed).

MANDATORY RESOLVE STEP -- every impl that VERIFIED had its faithful refined patch materialized against the real base_commit 580a4341 locks.py and executed through the official harness (`swebench_unified.harness.run_resolve`, instance django__django-13410, timeout 3600):
- patch_atk_5.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_atk_6.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_atk_7.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_atk_8.diff -> {completed:true, resolved:TRUE, attempts:1, flaky:false}
- patch_gold.diff (control, from the frozen dataset) -> resolved TRUE
No verifying impl's faithful patch failed to resolve => NO verify-not-correct witness => not BROKEN.

A-LEG AUDIT (my assigned focus). meta.json confirms axioms == [] and deep_model_references == [], so there are NO A-consumed and NO A-reference legs to over-claim: G-AX = skip is correct, and refinement.md's 'no A rows' claim is accurate. Refinement legs are A1 (R: LockOutcome <-> the fcntl.flock outcome), A2/A3 (I: concrete booleans), B1 (I: unconditional True). Every leg is R or I; NO kind-3 (inexpressible-changed-op) leg. The changed operation -- how the wrapper turns the primitive's outcome into a bool -- is modeled DIRECTLY in the pure region (acquiredOk) rather than hidden behind an axiom, which is the honest encoding. The A1 R-refinement's correspondence to the real callee holds: I confirmed against CPython semantics and the gold hunk that `succeeded` <-> flock returning (yielding None, never int 0) and `contended` <-> BlockingIOError under LOCK_NB, matching the F2P tests test_exclusive_lock/test_shared_lock which assert `assertIs(..., True/False)`.

THREE ADDITIONAL STRUCTURAL PROBES of the two genuine modeling gaps I identified, all executed through the harness (these probe correspondence, not spec strength):
1. probe_noeffect (patch_probe_noeffect.diff): `releaseLock` takes NO input and carries NO mutable frame, so the spec `out = true` cannot force the `fcntl.flock(_fd(f), LOCK_UN)` CALL. I dropped the release effect entirely (`def unlock(f): return True`). It RESOLVED (true) -- so this real under-specification is NOT observable by the F2P/P2P suite and cannot yield a break here. Recorded as a latent modeling gap: leg B1's effect is asserted by prose, not pinned by the spec.
2. probe_flags (patch_probe_flags.diff): mapping.md §2 declares `flags` unobservable; I ignored the caller's flags and always passed LOCK_SH|LOCK_NB. This did NOT resolve (3 attempts, consistent). Importantly this is NOT a spec break -- it is not a faithful refinement of any verifying impl (the model has no flags carrier, so the flag choice is fixed by the unchanged surrounding code, not by the impl region). It instead CONFIRMS that the mapping's 'flags unobservable beyond the resulting LockOutcome' abstraction is load-bearing and that the harness is sensitive here.
3. probe_oserror (patch_probe_oserror.diff): LockOutcome has only two constructors, so a third real outcome (a non-BlockingIOError OSError, e.g. EBADF) is inexpressible; I folded every OSError into the contended branch. RESOLVED (true) -- the domain gap is not test-observable.

CONCLUSION: 10 attacks encoded and fully verified, >= 5 distinct wrong-impl kinds (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, inverted, both prepatch bugs) all correctly REJECTED; positive control verifies; all 4 verifying reshapes' faithful patches RESOLVE. verify => correct holds on all evidence gathered. Verdict SOUND.

CAVEAT FOR THE RUNNER (not a G-EQ failure, but a bundle-integrity issue outside my gate): `patch.diff` is ABSENT from the bundle directory benchmark-verified/django__django-13410/velvet even though meta.json records G-RESOLVE = pass and patch_is_gold = true. gates/resolve.py returns `error: patch.diff missing` when it is absent, so a re-run of G-RESOLVE on this bundle as-shipped will ERROR. I sourced the gold patch from the frozen dataset (data/swe_bench_verified/test.jsonl) and confirmed it resolves; the bundle should have patch.diff restored before release.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec is too strong / drifts from real repo behavior. I could not produce a diverging input inside the modeled domain. Verdict FAITHFUL.

### PRELIMINARIES (all passed)
- same_spec byte-identity (swebench_unified.markers.same_spec, VelvetBackend): Solution.lean vs Solution_prepatch_lock.lean = True; vs Solution_prepatch_unlock.lean = True. Spec regions are byte-identical; rivals differ only in impl regions.
- scripts/lean_verify.sh: Solution.lean exit=0 (0 error/sorry). Solution_prepatch_lock.lean exit=1, Solution_prepatch_unlock.lean exit=1, both 'error: unsolved goals' at the prove_correct lines (70:26 / 88:26) -- genuine postcondition violations, NOT syntax/elaboration failures. G-DIFF is real.
- G-CONF (conformance_check.py, in-worktree): OK, 100000 inputs, seed=13410, 0 disagreements.
- F2P tests in the worktree: files.tests test_exclusive_lock + test_shared_lock -> 2 passed.

### REAL-REPO PROBING (worktree @ 580a4341cb, patch applied to django/core/files/locks.py:109-118)
- Confirmed the soundness crux mapping.md 3.1 rests on: fcntl.flock returns None on success (repr checked), never integer 0. Contention raises BlockingIOError, errno=11 EAGAIN (==EWOULDBLOCK), subclass of OSError. mapping.md is accurate here.
- Exhaustive sweep over every RETURNING outcome (holder in {none,EX,SH} x request in {EX,SH} x {blocking,LOCK_NB}): only True/False ever observed, every value matching acquiredOk. Blocking-on-held cases confirmed non-returning (block forever), so they legitimately have no LockOutcome representative -- mapping.md 2 excludes them explicitly and correctly.
- Tried to break acquiredOk via odd-but-returning paths: same-fd EX->EX relock, EX->SH downgrade, SH->EX upgrade, SH|NB while self-holding EX, LOCK_UN passed through lock(), garbage flags(=99) -> all return True, all consistent with 'succeeded'. 200 reps of contended-acquire + release across fresh fds: 0 mismatches vs spec.
- Prepatch fidelity of the rivals verified against the exact pre-patch bodies: pre_lock(free,EX)=False (spec demands true), pre_unlock(held)=False (spec demands true), and pre_lock(contended,EX|NB) raises BlockingIOError UNCAUGHT. The rivals' always-false modeling is a faithful abstraction of the pre-patch bug.

### STRONGEST SURVIVING OBJECTION (recorded, judged NOT a defect)
releaseLock takes no argument and asserts 'out = true' unconditionally, but the real unlock(f) is not infallible: I confirmed unlock on a CLOSED fd raises OSError EBADF (errno 9) rather than returning True, and lock on a closed fd likewise raises EBADF. So there IS a real-repo input on which the real callee does not return true.
Why this does not carry an UNFAITHFUL verdict:
1. It is not a diverging input on a MODELED input. The model's domain is LockOutcome = {succeeded, contended}, an R-refinement of the outcomes of a RETURNING call. There is no LockOutcome that refines 'raises EBADF', so the spec makes no claim there. This is domain restriction (partiality of R), not an over-strong postcondition on a covered input.
2. It is not discriminating. Pre-patch and post-patch code propagate EBADF IDENTICALLY (verified both bodies: neither catches anything but BlockingIOError, and pre-patch unlock catches nothing). The patch's entire content is the boolean translation, so the raise path is not a behavior change and cannot be exploited to slip a non-resolving impl past the spec.
3. EBADF requires violating the wrapper's implicit contract (pass a valid open file/fd); no F2P test exercises it.
Residual, logged for the record rather than as a defect: refinement.md C's blanket claim 'no kind-3 (inexpressible-changed-op) steps' is defensible only because the exception path is an UNCHANGED op -- the Lean fragment has no exception mechanism, so the raise path is genuinely inexpressible, but it is also untouched by the patch.

SCOPING CHECKED: spec covers only the POSIX/fcntl branch (locks.py:109+), which is the only branch the patch touches; the nt and dummy-fallback branches are unmodified and correctly out of scope (G-CONF also self-skips when LOCK_NB==0).

CONCLUSION: no diverging input inside the modeled domain; the spec neither over-claims nor drifts on any input it covers. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ARTIFACT LIVE + SPEC REGION IDENTICAL. scripts/lean_verify.sh: Solution.lean exit=0; Solution_prepatch_lock.lean exit=1; Solution_prepatch_unlock.lean exit=1. markers.same_spec(Solution, each prepatch)=True and spec_view() byte-identical for both variants. Live region_hashes reproduce meta.json G-HYGIENE exactly (spec_view=9b4dd58c6398f462..., pure=44497eb4f92d0fee..., impl=00206038c71b43f5...), so the view I judged is the shipped one. leakage.screen(velvet) re-run live: passed=True, 0 hard failures, 0 warnings.

SCOPE. Consumer-visible spec surface per eval/prompts.py _spec_block = spec_view + modeled_functions only; mapping.md / refinement.md are NOT shown. This matters: mapping.md §1 quotes the removed pre-patch expression `ret = fcntl.flock(_fd(f), flags); return ret == 0` verbatim and self-labels it "refinement audit only, not in the consumer spec view" — correctly outside scope (and public anyway, see below).

BASELINE IS UNUSUALLY WIDE. The public problem_statement for this instance embeds a complete proposed diff (try/except around fcntl.flock, return True / return False, for both lock and unlock), states outright that "cpython fcntl module returns None if successful, and raises an OSError to indicate failure", names locks.LOCK_NB non-blocking acquisition, and gives the file path django/core/files/locks.py. Judged against problem_statement only (never the hints_text, which is just "Would you like to prepare a pull request?").

CHANNEL-BY-CHANNEL, judged manually rather than trusting the screen:
1. Repo tokens absent from the view: grep for fcntl, flock, BlockingIO, OSError, None, LOCK_NB/LOCK_UN, _fd, locks.py, django, 'try', 'except', 'ret == 0', assertIs — all 0 hits. No diff markers, no file/module path.
2. Identifiers acquireLock/releaseLock do embed the patched symbol `lock` (len>=4, so it is in _patch_changed_symbols and was screened, not accidentally exempt). G-LEAK skipped it via the `sl in problem` branch, which is correct here: problem_statement's title and diff name `def lock(f, flags)` and `def unlock(f)` explicitly. Public.
3. Postcondition `out = acquiredOk outcome` with acquiredOk succeeded = true — the success-reports-True contract is the literal content of the public proposed diff.
4. LockOutcome = succeeded | contended, and the comment "under a non-blocking request the resource is already held" — the LOCK_NB contention case, explicitly public.
5. "never conflated with the primitive's no-value normal-completion result" is the most narration-adjacent line in the view, but it is a restatement of the public sentence "cpython fcntl module returns None if successful"; no banned narration vocabulary (bug/fix/patch/wrong/incorrectly/previously) appears anywhere in the view.

WHAT IS DELIBERATELY WITHHELD (the strongest evidence against leakage). The one detail of the gold patch that is NOT public is the narrowing from the proposal's `except OSError` to gold's `except BlockingIOError`. The spec view never names an exception type, saying only "the primitive signals that the operation could not be completed immediately." The genuinely non-public discriminator of the gold edit is not disclosed.

ONE OBSERVATION, sub-threshold, recorded for completeness. releaseLock takes no LockOutcome and is `ensures out = true`, whereas the public proposal's unlock is a SYMMETRIC try/except returning False on error; gold's unlock is the asymmetric unconditional `flock(...); return True`. So the view's asymmetry is a weak nudge toward gold's exact shape beyond problem_statement. I did not score this as LEAKAGE: it is not resolution-bearing (both unlock variants satisfy the F2P assertIs(locks.unlock(f1), True), since LOCK_UN on a held fd does not raise), the view never says "omit the try/except", and a solver writing the try/except unlock still satisfies the Lean obligation (releaseLock has no input with which to observe a raise). It states a behavioral contract — release reports success — that follows directly from the public statement's stated goal of returning True on success. Behavioral contract, not edit reconstruction.

OUT OF MY LANE, flagged for the panel: meta.json records G-EQ status=fail, "eq: INCONCLUSIVE — only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control". That is a separate gate's deficit and does not bear on the leakage verdict, but the bundle is not releasable on G-EQ as recorded.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
