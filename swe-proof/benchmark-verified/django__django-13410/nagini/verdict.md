# P2 adversarial audit — django__django-13410

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 32 admissible attacks re-run of 32 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 32 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 21 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_21.py`, `atk_22.py`, `atk_25.py`, `atk_27.py`, `atk_28.py`, `atk_29.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 11 | `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_16.py`, `atk_20.py`, `atk_23.py`, `atk_24.py`, `atk_26.py`, `atk_30.py`, `atk_31.py`, `atk_32.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (32):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -492,8 +492,10 @@
     # post-conditions-end
     # impl-start
     try:
-        primitive_lock(available)
-        return True
+        ret = primitive_lock(available)
+        if ret:
+            return True
+        return False
     except LockUnavailable:
         return False
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,11 +491,8 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
-    try:
-        primitive_lock(available)
-        return True
-    except LockUnavailable:
-        return False
+    ret = primitive_lock(available)
+    return ret == 0
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,6 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
-    primitive_release()
-    return True
+    ret = primitive_release()
+    return ret == 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,8 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
+    Fold(answerable_acquisition())
+    primitive_lock(True)
     primitive_release()
     return True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,7 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
+    acquire(True)
     primitive_release()
     return True
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -493,6 +493,7 @@
     # impl-start
     try:
         primitive_lock(available)
+        primitive_release()
         return True
     except LockUnavailable:
         return False
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -495,6 +495,7 @@
         primitive_lock(available)
         return True
     except LockUnavailable:
+        primitive_release()
         return False
     # impl-end
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -493,6 +493,7 @@
     # impl-start
     try:
         primitive_lock(available)
+        primitive_lock(available)
         return True
     except LockUnavailable:
         return False
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,11 +491,10 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
-    try:
+    if available:
         primitive_lock(available)
         return True
-    except LockUnavailable:
-        return False
+    return False
     # impl-end
 
 
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -540,5 +540,6 @@
     # post-conditions-end
     # impl-start
     primitive_release()
+    primitive_release()
     return True
     # impl-end
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -493,9 +493,9 @@
     # impl-start
     try:
         primitive_lock(available)
-        return True
+        return available
     except LockUnavailable:
-        return False
+        return available
     # impl-end
 
 
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -540,5 +540,8 @@
     # post-conditions-end
     # impl-start
     primitive_release()
+    while True:
+        Invariant(True)
+        pass
     return True
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,6 +491,7 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
+    Assert(False)
     try:
         primitive_lock(available)
         return True
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,5 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
-    primitive_release()
     return True
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,11 +491,8 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
-    try:
-        primitive_lock(available)
-        return True
-    except LockUnavailable:
-        return False
+    Fold(lock_state())
+    return available
     # impl-end
 
 
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -493,7 +493,7 @@
     # impl-start
     try:
         primitive_lock(available)
-        return True
+        return holds_lock()
     except LockUnavailable:
         return False
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,11 +491,7 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
-    try:
-        primitive_lock(available)
-        return True
-    except LockUnavailable:
-        return False
+    return available
     # impl-end
 
 
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,7 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
-    primitive_release()
+    Unfold(lock_state())
+    Fold(lock_state())
     return True
     # impl-end
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -495,7 +495,11 @@
         primitive_lock(available)
         return True
     except LockUnavailable:
-        return False
+        try:
+            primitive_lock(available)
+            return True
+        except LockUnavailable:
+            return False
     # impl-end
 
 
```

Attack 20 — `atk_20.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -492,8 +492,9 @@
     # post-conditions-end
     # impl-start
     try:
-        primitive_lock(available)
-        return True
+        if available:
+            primitive_lock(available)
+        return available
     except LockUnavailable:
         return False
     # impl-end
```

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,7 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
+    Assert(False)
     primitive_release()
     return True
     # impl-end
```

Attack 22 — `atk_22.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -492,6 +492,7 @@
     # post-conditions-end
     # impl-start
     try:
+        primitive_release()
         primitive_lock(available)
         return True
     except LockUnavailable:
```

Attack 23 — `atk_23.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -492,8 +492,8 @@
     # post-conditions-end
     # impl-start
     try:
-        primitive_lock(available)
-        return True
+        ret = primitive_lock(available)
+        return ret is None
     except LockUnavailable:
         return False
     # impl-end
```

Attack 24 — `atk_24.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,7 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
-    primitive_release()
+    if holds_lock():
+        primitive_release()
     return True
     # impl-end
```

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -495,7 +495,7 @@
         primitive_lock(available)
         return True
     except LockUnavailable:
-        return False
+        return holds_lock()
     # impl-end
 
 
```

Attack 26 — `atk_26.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -540,5 +540,5 @@
     # post-conditions-end
     # impl-start
     primitive_release()
-    return True
+    return not holds_lock()
     # impl-end
```

Attack 27 — `atk_27.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,7 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
-    primitive_release()
+    if not holds_lock():
+        primitive_release()
     return True
     # impl-end
```

Attack 28 — `atk_28.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,6 +491,8 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
+    if holds_lock():
+        return True
     try:
         primitive_lock(available)
         return True
```

Attack 29 — `atk_29.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -493,6 +493,8 @@
     # impl-start
     try:
         primitive_lock(available)
+        primitive_release()
+        primitive_lock(available)
         return True
     except LockUnavailable:
         return False
```

Attack 30 — `atk_30.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,7 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
+    before = holds_lock()
     primitive_release()
-    return True
+    return before or True
     # impl-end
```

Attack 31 — `atk_31.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -491,6 +491,8 @@
     Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
     # post-conditions-end
     # impl-start
+    if holds_lock() and available:
+        return True
     try:
         primitive_lock(available)
         return True
```

Attack 32 — `atk_32.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -539,6 +539,8 @@
     Ensures(holds_lock() is False)
     # post-conditions-end
     # impl-start
-    primitive_release()
+    if holds_lock():
+        primitive_release()
+        return not holds_lock()
     return True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), A-legs + model<->patch correspondence. 32 same-spec attacks (all `adversary same-spec` exit 0, all admissible - zero 'assumes rather than establishes'); 11 verify; EVERY verifying attack's faithful refined patch was materialized and RUN through run_resolve; ALL 11 RESOLVE. Positive control pos_control.py (byte-identical to model.py, md5 b95fcc2c79690d4b9fd49d1a4cfd93d6) verifies in 12.61s. Gold control (patch.diff) run through run_resolve: resolved=True, F2P 2/2, P2P 40/40 - the oracle is FIT, so a non-resolve would have been the spec's.

**PRIOR-PASS COUNTEREXAMPLE RE-ENCODED AND NOW REJECTED.** The recorded G-EQ fail exploited `Ensures(Result() == EMPTY_RESULT)` with EMPTY_RESULT=-1 (truthiness/order of -1 vs None). atk_1 re-encodes that headline attack verbatim (`ret = primitive_lock(available); if ret: return True; return False`) -> exit 2, REJECTED. The live axioms now state `Ensures(Result() is None)` (model.py:363, :407) and EMPTY_RESULT is gone entirely (grep: no hits). The repair holds, and the A-leg is now GROUNDED rather than over-claimed: axiom_check.py asserts `ret is None` on the real fcntl.flock for LOCK_EX/LOCK_EX|NB/LOCK_SH/LOCK_SH|NB and LOCK_UN (RC=0), which is exactly the live clause. atk_23 is the discriminator: `return ret is None` - the one fact the axiom states - verifies AND resolves, so reading the value is legitimate; nothing pins truthiness or order any more.

**PREPATCH REPRODUCED AT BOTH SITES.** atk_2 (acquire: `ret = primitive_lock(available); return ret == 0`) and atk_3 (release: `ret = primitive_release(); return ret == 0`) both REJECTED, each on `The precondition of (ret == 0) might not hold` - `None == 0` is not even well-typed against the empty-value axiom, so the spec senses the headline bug at both independent hunks.

A-LEG / CAPABILITY LEGS HOLD (the mechanically-hard part). answerable_acquisition() is a genuine expendable resource, not a proposition: atk_4 (`Fold(answerable_acquisition())` inside release - conjure the capability) REJECTED; atk_5 (release implemented via `acquire(True)`) REJECTED on `insufficient permission to access answerable_acquisition()`; atk_8 (two acquisitions on one authorisation) and atk_19 (retry after refusal) both REJECTED on the same permission error. So the release-by-acquiring 'pending step' flank refinement.md D claims is closed IS closed, and one authorisation really buys one answered acquisition. Framing resource likewise opaque: atk_15 (`Fold(lock_state())` + bypass) and atk_18 (`Unfold`/`Fold(lock_state())` + bypass) both REJECTED.

STATE-DIMENSION FLANKS CLOSED, each failing on the RIGHT clause (raw verifier messages captured): atk_6 inverse effect (acquire then release, report True) -> `Postcondition of acquire ... Implies((Result() is True), holds_lock()) might not hold`; atk_7 frame break on the failure path (release inside the except, report False) -> `Implies((Result() is False), (holds_lock() == Old(holds_lock()))) might not hold`; atk_14 bypass (`return True`, never release) -> `Postcondition of release ... (holds_lock() is False) might not hold`; atk_17 acquire bypass, atk_22 pre-emptive release, atk_27 inverted oracle guard, atk_28 oracle-guarded skip-acquisition, atk_29 release-then-reacquire - all REJECTED. atk_12 divergence -> `Obligation leak check failed`, so MustTerminate is live at the method level. NO VACUITY: atk_13 (Assert(False) + gold acquire body) and atk_21 (Assert(False) + gold release body) BOTH REJECTED, so neither helper's precondition set is unsatisfiable and no obligation is discharged vacuously.

THE ONE REAL DEFECT I FOUND IS A PROSE/DOC DEFECT, NOT A SPEC HOLE - ROUTING, NOT A GATE FAIL. `holds_lock()` IS callable from the impl region, contradicting mapping.md §3.3 ('readable only inside contracts, so no implementation can compute or echo it'), refinement.md §C ('is not readable by any implementation (@Pure @ContractOnly), so it is not an oracle') and the model.py axiom comment ('never callable from an implementation'). Measured: atk_16 (`return holds_lock()`), atk_24 (`if holds_lock(): primitive_release()`), atk_26 (`return not holds_lock()`), atk_30, atk_31, atk_32 ALL verify with holds_lock() in the impl.

I then tried hard to convert that into verify=>NOT-correct and COULD NOT, which is why the verdict is SOUND: at every program point where a verifying body can read it, an axiom already PINS the observation to a constant (True after a granted acquisition, False after a release), so the faithful refinement of the read IS that constant and the body constant-folds onto gold. atk_9/11/16/20/26/30/31's diffs are byte-identical in payload to patch.diff (verified with a normalized +/- comparison), and all resolve. Where the read is at an unpinned point (atk_24/atk_32, guard on entry to release), the faithful per-description rendering also resolves (atk_24_perdesc, atk_32_perdesc: resolved=True, F2P 2/2, P2P 40/40).

I DISCARDED TWO APPARENT BREAKS AS MY OWN REFINEMENT BUGS - reporting these because they would each have been a false BROKEN. (a) atk_26_probe/atk_24_probe rendered holds_lock() as an independent descriptor's non-blocking probe and came back resolved=False; but that is the AGGREGATE reading, which mapping.md §3.3 and axiom_check.py EXPLICITLY exclude as not the modelled observable (they assert the two diverge precisely in the shared-holder test_shared_lock world). Refining a per-description observable to an aggregate probe is an unfaithful refinement, so it grades nothing.

(b) Worse, my first probe did `open(getattr(f,'name',f))` on what move.py passes as a RAW INT fd - `open(int_fd)` ADOPTS and closes the caller's descriptor (confirmed in isolation: Errno 9 after close), which is what actually broke P2P test_file_move_copystat_cifs. The fd-safe rerendering via /proc/self/fd (atk_24_probe2) RESOLVES, proving that failure was mine, not the model's. Only atk_26_probe2 still fails F2P test_shared_lock, and only under the disclaimed aggregate reading; under the mandated per-description reading atk_26_perdesc resolves. Per the retained-label rule I did not record either as a spec weakness.

RESIDUAL FOR THE OWNING ROLE (documentation, not correctness): (1) mapping.md §1/§2 still describe `EMPTY_RESULT = -1` with 'the only relied-on property is != 0', and §3.1/§3.2 still quote `Ensures(Result() != 0)`; refinement.md A2/B1 still say 'value != 0' and §189 'the != 0 sentinel'; axiom_check.py's docstring/line 70 still assert `(-1) != 0`. The LIVE axioms say `Result() is None` and there is no EMPTY_RESULT symbol. The prose is STALE in the SAFE direction (it describes a weaker axiom than the model states, and the model's actual clause is the one axiom_check.py grounds on the real callee), so the A-leg correspondence itself holds - but the A2/B1 clause lists do not match model.py byte-for-byte and should be refreshed. (2) mapping.md §3.3 / refinement.md §C / model.py's holds_lock() comment claim an implementation cannot read holds_lock(); measurably it can (atk_16 verifies, 19.43s). Harmless here for the reason above, but the claim as written is false and is load-bearing prose in the no-oracle argument, so it should be corrected or defended. Neither is a verify=>correct break: 11/11 verifying attacks resolve.

**EVIDENCE.** Per-attack: <n>.log (adversary weakness stdout + RC), raw_<n>.log (raw verifier messages for the key rejections), resolve_<name>.json (full harness report incl. patch_successfully_applied + tests_status). Commands: `python -m swebench_unified.adversary same-spec|weakness nagini django__django-13410 <atk>`, `bash scripts/nagini_verify.sh <atk>`, `run_resolve` via resolve.py. Every submitted .diff re-checked with `git apply --check` in a FRESH base_commit (580a4341cb) worktree: 11/11 APPLY. Worktrees removed and pruned; the nagini bundle is byte-unmodified (model.py md5 matches pos_control.py). Verifier runs were batched 3-at-a-time as instructed; every attack still individually verified and reported.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 32 admissible attacks re-run of 32 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 32 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 21 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_21.py`, `atk_22.py`, `atk_25.py`, `atk_27.py`, `atk_28.py`, `atk_29.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 11 | `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_16.py`, `atk_20.py`, `atk_23.py`, `atk_24.py`, `atk_26.py`, `atk_30.py`, `atk_31.py`, `atk_32.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (32):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 32 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22.py` → rejected (same spec, does not verify — good)

Attack 23 — `atk_23.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 24 — `atk_24.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good)

Attack 26 — `atk_26.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 27 — `atk_27.py` → rejected (same spec, does not verify — good)

Attack 28 — `atk_28.py` → rejected (same spec, does not verify — good)

Attack 29 — `atk_29.py` → rejected (same spec, does not verify — good)

Attack 30 — `atk_30.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 31 — `atk_31.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 32 — `atk_32.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), A-legs + model<->patch correspondence. 32 same-spec attacks (all `adversary same-spec` exit 0, all admissible - zero 'assumes rather than establishes'); 11 verify; EVERY verifying attack's faithful refined patch was materialized and RUN through run_resolve; ALL 11 RESOLVE. Positive control pos_control.py (byte-identical to model.py, md5 b95fcc2c79690d4b9fd49d1a4cfd93d6) verifies in 12.61s. Gold control (patch.diff) run through run_resolve: resolved=True, F2P 2/2, P2P 40/40 - the oracle is FIT, so a non-resolve would have been the spec's.

**PRIOR-PASS COUNTEREXAMPLE RE-ENCODED AND NOW REJECTED.** The recorded G-EQ fail exploited `Ensures(Result() == EMPTY_RESULT)` with EMPTY_RESULT=-1 (truthiness/order of -1 vs None). atk_1 re-encodes that headline attack verbatim (`ret = primitive_lock(available); if ret: return True; return False`) -> exit 2, REJECTED. The live axioms now state `Ensures(Result() is None)` (model.py:363, :407) and EMPTY_RESULT is gone entirely (grep: no hits). The repair holds, and the A-leg is now GROUNDED rather than over-claimed: axiom_check.py asserts `ret is None` on the real fcntl.flock for LOCK_EX/LOCK_EX|NB/LOCK_SH/LOCK_SH|NB and LOCK_UN (RC=0), which is exactly the live clause. atk_23 is the discriminator: `return ret is None` - the one fact the axiom states - verifies AND resolves, so reading the value is legitimate; nothing pins truthiness or order any more.

**PREPATCH REPRODUCED AT BOTH SITES.** atk_2 (acquire: `ret = primitive_lock(available); return ret == 0`) and atk_3 (release: `ret = primitive_release(); return ret == 0`) both REJECTED, each on `The precondition of (ret == 0) might not hold` - `None == 0` is not even well-typed against the empty-value axiom, so the spec senses the headline bug at both independent hunks.

A-LEG / CAPABILITY LEGS HOLD (the mechanically-hard part). answerable_acquisition() is a genuine expendable resource, not a proposition: atk_4 (`Fold(answerable_acquisition())` inside release - conjure the capability) REJECTED; atk_5 (release implemented via `acquire(True)`) REJECTED on `insufficient permission to access answerable_acquisition()`; atk_8 (two acquisitions on one authorisation) and atk_19 (retry after refusal) both REJECTED on the same permission error. So the release-by-acquiring 'pending step' flank refinement.md D claims is closed IS closed, and one authorisation really buys one answered acquisition. Framing resource likewise opaque: atk_15 (`Fold(lock_state())` + bypass) and atk_18 (`Unfold`/`Fold(lock_state())` + bypass) both REJECTED.

STATE-DIMENSION FLANKS CLOSED, each failing on the RIGHT clause (raw verifier messages captured): atk_6 inverse effect (acquire then release, report True) -> `Postcondition of acquire ... Implies((Result() is True), holds_lock()) might not hold`; atk_7 frame break on the failure path (release inside the except, report False) -> `Implies((Result() is False), (holds_lock() == Old(holds_lock()))) might not hold`; atk_14 bypass (`return True`, never release) -> `Postcondition of release ... (holds_lock() is False) might not hold`; atk_17 acquire bypass, atk_22 pre-emptive release, atk_27 inverted oracle guard, atk_28 oracle-guarded skip-acquisition, atk_29 release-then-reacquire - all REJECTED. atk_12 divergence -> `Obligation leak check failed`, so MustTerminate is live at the method level. NO VACUITY: atk_13 (Assert(False) + gold acquire body) and atk_21 (Assert(False) + gold release body) BOTH REJECTED, so neither helper's precondition set is unsatisfiable and no obligation is discharged vacuously.

THE ONE REAL DEFECT I FOUND IS A PROSE/DOC DEFECT, NOT A SPEC HOLE - ROUTING, NOT A GATE FAIL. `holds_lock()` IS callable from the impl region, contradicting mapping.md §3.3 ('readable only inside contracts, so no implementation can compute or echo it'), refinement.md §C ('is not readable by any implementation (@Pure @ContractOnly), so it is not an oracle') and the model.py axiom comment ('never callable from an implementation'). Measured: atk_16 (`return holds_lock()`), atk_24 (`if holds_lock(): primitive_release()`), atk_26 (`return not holds_lock()`), atk_30, atk_31, atk_32 ALL verify with holds_lock() in the impl.

I then tried hard to convert that into verify=>NOT-correct and COULD NOT, which is why the verdict is SOUND: at every program point where a verifying body can read it, an axiom already PINS the observation to a constant (True after a granted acquisition, False after a release), so the faithful refinement of the read IS that constant and the body constant-folds onto gold. atk_9/11/16/20/26/30/31's diffs are byte-identical in payload to patch.diff (verified with a normalized +/- comparison), and all resolve. Where the read is at an unpinned point (atk_24/atk_32, guard on entry to release), the faithful per-description rendering also resolves (atk_24_perdesc, atk_32_perdesc: resolved=True, F2P 2/2, P2P 40/40).

I DISCARDED TWO APPARENT BREAKS AS MY OWN REFINEMENT BUGS - reporting these because they would each have been a false BROKEN. (a) atk_26_probe/atk_24_probe rendered holds_lock() as an independent descriptor's non-blocking probe and came back resolved=False; but that is the AGGREGATE reading, which mapping.md §3.3 and axiom_check.py EXPLICITLY exclude as not the modelled observable (they assert the two diverge precisely in the shared-holder test_shared_lock world). Refining a per-description observable to an aggregate probe is an unfaithful refinement, so it grades nothing.

(b) Worse, my first probe did `open(getattr(f,'name',f))` on what move.py passes as a RAW INT fd - `open(int_fd)` ADOPTS and closes the caller's descriptor (confirmed in isolation: Errno 9 after close), which is what actually broke P2P test_file_move_copystat_cifs. The fd-safe rerendering via /proc/self/fd (atk_24_probe2) RESOLVES, proving that failure was mine, not the model's. Only atk_26_probe2 still fails F2P test_shared_lock, and only under the disclaimed aggregate reading; under the mandated per-description reading atk_26_perdesc resolves. Per the retained-label rule I did not record either as a spec weakness.

RESIDUAL FOR THE OWNING ROLE (documentation, not correctness): (1) mapping.md §1/§2 still describe `EMPTY_RESULT = -1` with 'the only relied-on property is != 0', and §3.1/§3.2 still quote `Ensures(Result() != 0)`; refinement.md A2/B1 still say 'value != 0' and §189 'the != 0 sentinel'; axiom_check.py's docstring/line 70 still assert `(-1) != 0`. The LIVE axioms say `Result() is None` and there is no EMPTY_RESULT symbol. The prose is STALE in the SAFE direction (it describes a weaker axiom than the model states, and the model's actual clause is the one axiom_check.py grounds on the real callee), so the A-leg correspondence itself holds - but the A2/B1 clause lists do not match model.py byte-for-byte and should be refreshed. (2) mapping.md §3.3 / refinement.md §C / model.py's holds_lock() comment claim an implementation cannot read holds_lock(); measurably it can (atk_16 verifies, 19.43s). Harmless here for the reason above, but the claim as written is false and is load-bearing prose in the no-oracle argument, so it should be corrected or defended. Neither is a verify=>correct break: 11/11 verifying attacks resolve.

**EVIDENCE.** Per-attack: <n>.log (adversary weakness stdout + RC), raw_<n>.log (raw verifier messages for the key rejections), resolve_<name>.json (full harness report incl. patch_successfully_applied + tests_status). Commands: `python -m swebench_unified.adversary same-spec|weakness nagini django__django-13410 <atk>`, `bash scripts/nagini_verify.sh <atk>`, `run_resolve` via resolve.py. Every submitted .diff re-checked with `git apply --check` in a FRESH base_commit (580a4341cb) worktree: 11/11 APPLY. Worktrees removed and pruned; the nagini bundle is byte-unmodified (model.py md5 matches pos_control.py). Verifier runs were batched 3-at-a-time as instructed; every attack still individually verified and reported.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 (faithfulness / spec-too-strong) for django__django-13410 nagini. Reference built by me: fresh worktree of the upstream repository at base_commit 580a4341cb0b4cbfc215a70afc004875a7e815f4 with the dataset's patch.diff APPLIED (per instructions the patched tree is the reference for the modelled functions; base is reference only for the axiomatized callee fcntl.flock). Test patch applied too. bundle not modified.

**SPEC INTEGRITY:** `adversary same-spec nagini django__django-13410 gold_model.py` -> exit 0, 'SAME — attack shares the bundle's exact specification'; `diff` against the bundle model.py is byte-identical (I audited the shipped bytes, not a paraphrase).

**POSITIVE CONTROL:** scripts/nagini_verify.sh on the bundle model.py -> 'Verification successful' (10.63s). F2P pair on my patched worktree -> 2 passed (test_exclusive_lock, test_shared_lock). So gold is admitted and the oracle is fit — the spec is not vacuously over-strong.

**NO DIVERGING INPUT FOUND IN THE MODELLED DOMAIN.** I drove the real patched locks.lock/locks.unlock directly and checked each helper postcondition (Result()==available; Implies(Result is True, holds_lock()); Implies(Result is False, holds_lock()==Old(holds_lock())); release's Result() is True and holds_lock() is False), with holds_lock() instantiated as the PER-OPEN-FILE-DESCRIPTION reading mapping.md §1/§3.3 specifies (drain other holders, then probe):
  * exhaustive boundary sweep: holder in {none,SH,EX} x subject-pre-state in {none,SH,EX} x request in {EX, SH, EX|NB, SH|NB}, skipping requests the kernel would leave PENDING (explicitly outside the modelled scope) -> 0 violations.
  * randomized sweep, seed 13410, 2229 in-domain trials over the same space -> 0 violations.
  * release sweep over subject-pre-state x other-holder (incl. the shared-holder test_shared_lock world) -> 0 violations; unlock returns True and the SUBJECT's claim is gone in every case.

AXIOMS RE-DERIVED ON THE REAL CALLEE (base-commit-unchanged fcntl.flock), independently of the bundle's script: every granted acquisition (EX, SH, EX|NB, SH|NB) returns None — so `Ensures(Result() is None)` is exact, not an over-claim; non-blocking contention raises BlockingIOError (errno 11, a subclass of OSError); a refused request leaves the subject's standing in the REQUESTED lock unmoved; LOCK_UN returns None, never raises, and ends the subject's claim even with nothing held. The per-description vs aggregate distinction the model leans on is real and is the correct (weaker) reading: in the shared-holder world an aggregate probe still answers 'held' while the subject's claim is genuinely gone, so the model does NOT assert the stronger 'nobody holds it'. I also reran the bundle's own axiom_check.py (exit 0) and conformance_check.py against MY worktree (exit 0, 100020 trials, 0 disagreements) — both reproduce.

### RESIDUAL EDGES EXAMINED AND JUDGED OUT-OF-DOMAIN (not drift):
  (a) lock(f, LOCK_UN): real patched lock returns True while the subject holds nothing, which would falsify Implies(Result is True, holds_lock()). But LOCK_UN is NOT in locks.`__all__` ('LOCK_EX','LOCK_SH','LOCK_NB','lock','unlock') and not an attribute of the module, and no repo caller passes it (all six call sites — testcases.py:1569, filebased.py:65, storage.py:270, move.py:61, plus the two F2P tests — pass LOCK_EX or LOCK_SH optionally |LOCK_NB). Spelling a release as an acquisition is not a lock REQUEST, so it is outside the stated R-refinement '(f,flags) -> available = was the requested lock operation granted'.
  (b) lock(f, 0) raises a non-BlockingIOError OSError (EINVAL) which real gold propagates, whereas the model's LockUnavailable would absorb it into False. mapping.md §2/§3.1 states the refinement carrier explicitly as LockUnavailable <-> BlockingIOError (contention), and flags=0 is not a value any caller in the POSIX branch supplies. Documented scope, not undocumented drift.
Neither edge is reachable from repo behavior, so I do not treat either as a faithfulness defect; both are disclosed here so a future pass can weigh them.

OVER-STRENGTH OBSERVATION FOR THE SIBLING LANE (not a faithfulness break, no diverging input): a double-acquisition impl (`primitive_lock(available)` twice, then return True) is REJECTED by the spec — `adversary weakness` -> exit non-candidate, 'attack does not verify' — because primitive_lock CONSUMES answerable_acquisition() and acquire is handed exactly one. On the real callee a second flock(fd, LOCK_EX) on the same description succeeds and is value- and state-identical to gold, so that impl would plausibly resolve. This is the answerability capability rejecting a would-be-correct rival, i.e. a candidate SPEC-TOO-STRONG-for-rivals point, but it is not a disagreement between the modelled function and the real callee on any input, and gold still verifies, so it does not make the spec unfaithful. Flagging it for G-EQ/G-PANEL-1 rather than claiming it here.

STALENESS NOTE (important for reading verdict.md): the recorded G-EQ and G-PANEL-1 fails both rest on `Ensures(Result() == EMPTY_RESULT)` with EMPTY_RESULT = -1 letting an impl distinguish -1 from None. The model.py I audited no longer contains that clause — both primitives now carry `Ensures(Result() is None)` (model.py:363 and :407) and there is no numeric sentinel in the axioms region. Those two recorded fails therefore judge a spec that has since been repaired; my pass is against the current bytes (sha per meta.json G-AX/G-CONF sources: 4df519d4e6c5...).

**CONCLUSION:** FAITHFUL. No input exists in the modelled domain on which the specified acquire/release disagrees with the real patched django.core.files.locks.lock/unlock; every axiom clause is met exactly by the unchanged fcntl.flock; gold verifies and the F2P pair passes. I am submitting FAITHFUL rather than manufacturing a divergence from out-of-domain flag spellings.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** leakage / gold-reconstruction, django__django-13410 nagini. Live model.py sha256[:12]=4df519d4e6c5.

(0) NO RELAXATION IS ON OFFER. meta.json has NO `relaxed_leakage` key (keys: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and no RELAXED_LEAKAGE.md exists under the instance dir. So there is no unavoidability argument to re-derive and no disposition to inherit — the verdict below is my own measurement, not an inherited one.

(0b) NOTHING IN THE BUNDLE ADDRESSES ME. Grepped model.py/mapping.md/refinement.md/axiom_check.py/conformance_check.py for G-PANEL|attacker|panel|reviewer|submit_result|NO-LEAKAGE|you must|honest verdict -> zero hits; leakage.reviewer_directed() returns [] on model.py, mapping.md, refinement.md AND verdict.md. The only text speaking to my role is a PRIOR G-PANEL-3 note embedded in verdict.md/meta.json; it describes rather than instructs, and I treated it strictly as a claim. Notably it stamps model.py as 582e74d351a7 while the live file is 4df519d4e6c5, i.e. the prior leakage pass judged superseded bytes — which is why I re-derived everything from scratch rather than adopting it.

(1) SPEC VIEW RENDERS AND ELIDES. markers.spec_view(model.py, nagini) = 539 lines; BOTH impl regions are replaced by `...  # implementation elided`. The gold edit is exactly and only the two helper bodies, so the discriminating bytes are structurally absent from what the consumer sees.

(2) LEXICAL SCREEN, RE-RUN MYSELF (not read off the stamp). leakage.screen(model.py, nagini, frozen patch, frozen problem_statement) -> passed=True, hard_failures=[], warnings=[]. Independently: narration-vocabulary hits = [] (no bug/fix/patch/pre-patch/previously/incorrectly/wrong anywhere in the spec view); diff markers present = [] (no @@, `diff --git`, `+++ `, `--- `, `\nindex`).

(3) IDENTIFIER / SYMBOL DISJOINTNESS, MEASURED. AST identifiers of the spec view = {ContractOnly, Ensures, Exception, Exsures, Implies, LockUnavailable, MustTerminate, Old, Optional, Predicate, Pure, Requires, Result, acquire, answerable_acquisition, available, bool, holds_lock, int, lock_state, primitive_lock, primitive_release, release}. Intersection with the token set of the gold patch = EMPTY. No repo symbol (lock, unlock, `_fd`, flock), no exception class, no path.

(4) THE DISCRIMINATOR IS ONLY IN THE PUBLIC TEXT, NOT THE SPEC. Per-term presence (spec_view | problem_statement): fcntl F|T, flock F|T, OSError F|T, LOCK_UN F|T, `_fd` F|T, 'ret == 0' F|T, 'locks.py' F|T, 'django/core' F|T, BlockingIOError F|F. The public problem_statement is STRICTLY MORE EXPLICIT than the spec view — it contains the literal proposed diff. So there is no fact the spec view supplies beyond it; the direction of leakage is reversed.

(5) MANUAL GOLD-CHANGED-LINE CHECK. Whitespace-normalized, of the 11 added/removed gold lines the only substring collision is `try:` (4 chars), and I located it: it falls inside the normalized comment text "...operations' asymmetry:the ACQUISITION helper..." — a normalization artifact spanning "asymmetry:"+"the", not a reproduced code line, and below the screen's own 8-char threshold. No gold line is reproduced.

(6) GOLD IS NOT RECONSTRUCTIBLE — THE STRONGEST MEASUREMENT. The gold patch and the problem_statement's proposed patch DISAGREE on the release helper: gold writes bare `flock(...LOCK_UN); return True`, the public text proposes `try: ... except OSError: return False`. If the spec leaked gold's shape it would have to reject the public shape. It does not. I built two same-spec attacks (spec region untouched) and ran the toolkit:
  - atk_ps_release.py (release body = the problem_statement's try/except shape): `adversary same-spec` -> exit 0 "SAME"; `adversary weakness` -> exit 0 "CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (14.2s)".
  - atk_var_acquire.py (acquire rewritten through an explicit bool variable): same-spec exit 0; weakness exit 0 "shares spec AND verifies (14.4s)".
  I also confirmed byte-identity directly with markers.same_spec(gold, atk) = True and sha256(spec_view(gold)) == sha256(spec_view(atk)) for both. So the spec admits gold's shape AND the public-text shape AND a third rewrite: a consumer reading only the spec view cannot recover which one gold chose.

(7) CONTROLS, so "admits both" is not "admits everything". Positive: `scripts/nagini_verify.sh` on the live gold model.py -> "Verification successful" (13.70s). Negative: neg_prepatch.py (acquire reverted to `ret = primitive_lock(available); return ret == 0`) -> `adversary weakness` exit 2, "NOT-A-COUNTEREXAMPLE: attack does not verify — the spec rejected this impl". The spec is discriminating, and it discriminates on the abstract control-flow-vs-value axis without naming the edit.

(8) SCOPE OF THE VIEW CONFIRMED FROM THE HARNESS, not assumed. eval/prompts.py::initial_user assembles problem_statement + optional hints + localization block + `_spec_block`(task.spec_view) only; grep for refinement|mapping in prompts.py and agent.py -> zero hits. refinement.md and mapping.md DO quote the gold diff verbatim (refinement.md:25-34, 61-65; mapping.md:8-25 name locks.py, fcntl.flock, BlockingIOError), but they are audit-side artifacts, never handed to a solver, and eval/adapter.py::spec_view hard-guards that impl elision actually happened before exposing anything. Solver-visible meta fields (modeled_functions repo_symbol/repo_location, changed_files) give edit LOCALIZATION only — `locks.py:109/:113`, lock/unlock — which is the deliberate localization aid also present in mode 0 and already in the public problem_statement; it names WHERE, never the try/except-vs-`ret == 0` discriminator.

RESIDUALS FOR THE OWNING ROLE, NOT LEAKAGE FINDINGS (routing only): (a) meta.json top-level region_hashes are STALE against the live bytes for axioms (live 548dd49b / meta 2711f2f4), post-conditions (abd7bec8 / 571c371b), pure (41072923 / aa3505b5) and spec_view (7a3cdf27 / d50184ef); only impl (25f420c2) and pre-conditions (4af38839) agree — freshness checks keyed on the top-level ledger will misread the current spec. (b) G-PANEL-3's recorded stamp carries an EMPTY source_digests map and its note cites a model.py digest (582e74d351a7) that matches neither the live bytes nor the ledger, so that pass is not attributable to any artifact. Neither affects leakage: the gates my disposition actually leans on I re-ran or re-derived myself (G-LEAK screen re-run clean; spec_view elision verified; same-spec byte identity verified; gold verification and the prepatch rejection both re-measured on the live bytes).

**VERDICT:** NO-LEAKAGE. The spec view names no file, no repo symbol, no exception class, and no before/after code shape from the gold edit; its identifier set is disjoint from the gold patch's tokens; every discriminating term it could have used appears only in the strictly-more-explicit public problem_statement; and I measured that the spec still admits both the gold release shape and the problem_statement's competing release shape while rejecting the pre-patch shape — the opposite of gold-reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
