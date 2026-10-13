# P2 adversarial audit — astropy__astropy-14096

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_12.py`, `atk_14.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_6.py`, `atk_9.py`, `atk_11.py`, `atk_13.py`, `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verify-but-not-resolve witness found. All 19 same-spec attacks reached a machine verdict: 14 rejected by the spec, 5 CANDIDATEs (atk_6, atk_9, atk_11, atk_13, atk_15), and every one of those 5 had its faithful refined patch materialized against base_commit 1a4462d72eb03f30dc83a879b1dd57aac8b2c18b and EXECUTED through the official harness (run_resolve) -> resolved=True, completed=True, attempts=1, flaky=False, F2P 1/1, P2P 426/426 for all five. Since BROKEN requires a verifying wrong impl whose faithful patch does NOT resolve, and no such patch exists among the executed runs, the spec is not shown broken. The closest approach to a break is atk_6 (see notes): it IS a genuine behavioural divergence from gold on real, untested inputs, but its patch resolves, so per the gate criterion it is not a counterexample.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,5 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    raise AttributeAccessError(name)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,5 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    raise AttributeAccessError(residual_step_subject(name))
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,5 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    return residual_step_value(name)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,8 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    try:
+        return residual_step(name)
+    except AttributeAccessError:
+        return alias_value
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -343,7 +343,8 @@
     if is_alias:
         return alias_value
     if is_frame_attr:
-        return frame_attr_step(name, frame_attr_value)
+        v = frame_attr_step(name, frame_attr_value)
+        raise AttributeAccessError(v)
     if is_frame_passthrough:
         return passthrough_step(name, passthrough_value)
     if is_transform:
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -343,10 +343,19 @@
     if is_alias:
         return alias_value
     if is_frame_attr:
-        return frame_attr_step(name, frame_attr_value)
+        try:
+            return frame_attr_step(name, frame_attr_value)
+        except AttributeAccessError:
+            raise AttributeAccessError(name)
     if is_frame_passthrough:
-        return passthrough_step(name, passthrough_value)
+        try:
+            return passthrough_step(name, passthrough_value)
+        except AttributeAccessError:
+            raise AttributeAccessError(name)
     if is_transform:
-        return transform_step(name, transform_value)
+        try:
+            return transform_step(name, transform_value)
+        except AttributeAccessError:
+            raise AttributeAccessError(name)
     return residual_step(name)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -344,9 +344,9 @@
         return alias_value
     if is_frame_attr:
         return frame_attr_step(name, frame_attr_value)
+    if is_transform:
+        return transform_step(name, transform_value)
     if is_frame_passthrough:
         return passthrough_step(name, passthrough_value)
-    if is_transform:
-        return transform_step(name, transform_value)
     return residual_step(name)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -347,6 +347,7 @@
     if is_frame_passthrough:
         return passthrough_step(name, passthrough_value)
     if is_transform:
-        return transform_step(name, transform_value)
+        r = residual_step(name)
+        return transform_value
     return residual_step(name)
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,8 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    try:
+        return residual_step(name)
+    except AttributeAccessError:
+        raise AttributeAccessError(residual_step_subject(name))
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -341,7 +341,7 @@
     # post-conditions-end
     # impl-start
     if is_alias:
-        return alias_value
+        raise AttributeAccessError(name)
     if is_frame_attr:
         return frame_attr_step(name, frame_attr_value)
     if is_frame_passthrough:
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -343,6 +343,10 @@
     if is_alias:
         return alias_value
     if is_frame_attr:
+        try:
+            t = transform_step(name, transform_value)
+        except AttributeAccessError:
+            t = 0
         return frame_attr_step(name, frame_attr_value)
     if is_frame_passthrough:
         return passthrough_step(name, passthrough_value)
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -344,8 +344,6 @@
         return alias_value
     if is_frame_attr:
         return frame_attr_step(name, frame_attr_value)
-    if is_frame_passthrough:
-        return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
     return residual_step(name)
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -347,6 +347,9 @@
     if is_frame_passthrough:
         return passthrough_step(name, passthrough_value)
     if is_transform:
-        return transform_step(name, transform_value)
+        try:
+            return transform_step(name, transform_value)
+        except AttributeAccessError:
+            raise AttributeAccessError(residual_step_subject(name))
     return residual_step(name)
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,8 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
+    i = 0
+    while i >= 0:
+        i = i + 1
     return residual_step(name)
     # impl-end
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,8 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    try:
+        return residual_step(name)
+    except AttributeAccessError:
+        return residual_step(name)
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -347,6 +347,9 @@
     if is_frame_passthrough:
         return passthrough_step(name, passthrough_value)
     if is_transform:
-        return transform_step(name, transform_value)
+        try:
+            return transform_step(name, transform_value)
+        except AttributeAccessError:
+            return transform_value
     return residual_step(name)
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,8 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    try:
+        return residual_step(name)
+    except AttributeAccessError:
+        return residual_step(alias_value)
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -343,10 +343,10 @@
     if is_alias:
         return alias_value
     if is_frame_attr:
-        return frame_attr_step(name, frame_attr_value)
+        return frame_attr_value
     if is_frame_passthrough:
-        return passthrough_step(name, passthrough_value)
+        return passthrough_value
     if is_transform:
-        return transform_step(name, transform_value)
+        return transform_value
     return residual_step(name)
     # impl-end
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -348,5 +348,6 @@
         return passthrough_step(name, passthrough_value)
     if is_transform:
         return transform_step(name, transform_value)
-    return residual_step(name)
+    v = frame_attr_step(name, frame_attr_value)
+    return residual_step_value(name)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, astropy__astropy-14096 (nagini). Bundle model.py sha256=b007674d454894f20364695400dae3a36a458d9bcd064dee18bf91cd62205fb6, md5=44de90bab439c24be372e26649f513b0. All 19 attacks + the positive control were authored by copying model.py and editing ONLY the impl region (generator gen.py splits on the `# impl-start`/`# impl-end` markers, so axioms/@Pure/Requires/Ensures/Exsures are byte-identical by construction), and all 20 were independently confirmed byte-identical-spec via `python -m swebench_unified.adversary same-spec nagini astropy__astropy-14096 <path>` (exit 0) BEFORE verification. Verifications were run 3 concurrently as background jobs (JVM+Z3 per check); no timeouts, no crashes, no INCONCLUSIVE outcomes.

**POSITIVE CONTROL:** pos_control.py (byte-identical to bundle model.py) -> `adversary weakness` = CANDIDATE, i.e. VERIFIES in 16.3s. The spec is satisfiable and not over-fitted against its own gold impl.

PER-ATTACK RESULTS (command for each: `python -m swebench_unified.adversary weakness nagini astropy__astropy-14096 atk_N.py`; logs at w_N.log):
- atk_1.py  PREPATCH BUG re-encoded (`raise AttributeAccessError(name)` on leg 5) -> rc=2 does not verify. PREPATCH REPRODUCED + rejected; the spec senses the change (G-DIFF).
- atk_2.py  UNGROUNDED-ORACLE ECHO, the prior pass's named counterexample re-encoded (`raise AttributeAccessError(residual_step_subject(name))`, never performs the step) -> rc=2 rejected. The bodyless capability predicate holds.
- atk_3.py  VALUE-ORACLE ECHO on leg 5's returning path (`return residual_step_value(name)`) -> rc=2 rejected.
- atk_4.py  CONTROL-FLOW-EFFECT swallow on leg 5: genuinely performs the step (legitimately HOLDS residual_step_performed) then catches and returns alias_value -> rc=2 rejected on the Ensures' residual_step_succeeds selector. Confirms the selector conjunct is load-bearing and the token alone cannot see this.
- atk_5.py  CONTROL-FLOW-EFFECT invert on leg 2: performs frame_attr_step, then raises even where it SUCCEEDED -> rc=2 rejected on the negated selector in the Exsures.
- atk_6.py  A-LEG SUBJECT SUBSTITUTION on all three PARTIAL DOMAIN legs (2/3/4): performs each step (so holds every token and every negated selector legitimately) but discards the step's own failure and raises a fresh failure blaming the REQUESTED name -> CANDIDATE (verifies 22.8s). Admitted because the Exsures pins RaisedException().subject ONLY on leg 5; legs 2-4's failing arms constrain selector+token but leave the subject free.
- atk_7.py  BOUNDARY priority swap (transform tried before the passthrough) -> rc=2 rejected.
- atk_8.py  BORROWED TOKEN: leg 4 performs the RESIDUAL step (another leg's work) then returns transform_value -> rc=2 rejected. Per-leg capabilities hold.
- atk_9.py  CONTROL-FLOW-EFFECT laundering on leg 5: performs the step, discards its exception OBJECT, raises a fresh one carrying the same echoed subject -> CANDIDATE (verifies 23.1s).
- atk_10.py ALIAS-LEG-MADE-PARTIAL: a failure escapes the one TOTAL leg -> rc=2 rejected. Confirms leg 1's totality was not relaxed along with the others.
- atk_11.py EXTRA ABSORBED CROSS-LEG STEP: leg 2 first performs the TRANSFORM step and swallows its outcome, then does its own work -> CANDIDATE (verifies 23.8s).
- atk_12.py PARTIAL-DOMAIN drop: the passthrough leg removed entirely -> rc=2 rejected.
- atk_13.py A-LEG SUBJECT SUBSTITUTION on the transform leg alone, blaming residual_step_subject(name) instead of its own failure -> CANDIDATE (verifies 17.2s).
- atk_14.py DIVERGENCE: unbounded loop before the residual step, clauses discharged only by an unreachable tail -> rc=2 rejected by method-level MustTerminate(10).
- atk_15.py RETRY leg 5: performs the residual step, catches, performs it AGAIN so the second failure propagates -> CANDIDATE (verifies 20.1s).
- atk_16.py SWALLOW the TRANSFORM step's failure and return the leg's own value -> rc=2 rejected on the transform leg's selector. Confirms the swallow guard is present on a PARTIAL DOMAIN leg, not only on leg 5.
- atk_17.py A-LEG NAME-INDEXING: performs residual_step(name) (so legitimately holds the token for `name`) but then surfaces residual_step(alias_value)'s outcome, i.e. a DIFFERENT name's -> rc=2 rejected. Confirms the token and the subject oracle are genuinely indexed by `name` and not harvestable from any lookup.
- atk_18.py UNGROUNDED ORACLE across legs 2-4: returns each leg's value WITHOUT performing the step (no token, no selector fact) -> rc=2 rejected.
- atk_19.py CROSS-LEG BORROWED TOKEN on the returning path: leg 5 performs leg 2's step then echoes residual_step_value(name) -> rc=2 rejected.

MANDATORY RESOLVE RUNS -- all 5 CANDIDATEs, faithful refined patches materialized against base_commit 1a4462d72eb03f30dc83a879b1dd57aac8b2c18b (generator work/mkpatch.py; each patch confirmed `git apply --check -p1` clean; the same generator's gold control diff is textually identical to the bundle patch.diff modulo the hunk-header function context, proving the diff machinery faithful), executed via the official harness `python work/resolve.py patch_atk_N.diff` -> swebench_unified.harness.run_resolve under `docker`:
- patch_atk_6.diff  -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1 success 0 failure, P2P 426/426 success 0 failure.
- patch_atk_9.diff  -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
- patch_atk_11.diff -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
- patch_atk_13.diff -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
- patch_atk_15.diff -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
Every candidate's faithful patch RESOLVES, so no attack exhibited verify AND not-resolve.

WHY atk_9/11/15 ARE GENUINELY CORRECT: each only adds an idempotent, side-effect-free re-performance of a step whose outcome is discarded or re-raised with the same blamed subject; the surfaced outcome is unchanged, which is why F2P (match="random_attr") and all 426 P2P pass. Correctly admitted -- they ARE behaviourally equal on the tested inputs, which is exactly refinement.md's G-EQ claim.

HONEST CAVEAT ON atk_6 / atk_13 (the sharpest finding, reported because it is a real gap in the spec's strength even though it does not meet the BROKEN criterion). These are NOT behaviourally equal to gold. I measured the divergence inside the instance image (probe.py, run under `docker` on swebench/sweb.eval.x86_64.astropy_1776_astropy-14096): with the GOLD patch applied, SkyCoord.`__getattr__`(SkyCoord(1d,2d,icrs), name) surfaces altaz -> AttributeError("'NoneType' object has no attribute 'to_geodetic'"), hadec -> same, teme -> AttributeError(...

'scale'), galactocentric -> ConvertError("...requires a 3D coordinate..."), hcrs -> UnitsError("...do not have length units..."); with patch_atk_6 applied the SAME five inputs instead all surface AttributeError("'SkyCoord' object has no attribute '<name>'"). So atk_6 destroys the transform leg's diagnostic (and CHANGES THE EXCEPTION TYPE for galactocentric ConvertError and hcrs UnitsError, converting non-AttributeError failures into AttributeError -- a genuinely observable difference).

It resolves only because no F2P/P2P test in the frozen set observes a failing outcome of legs 2-4: I grepped the base test file (2167 lines, all 426 P2P + the 1 F2P live in astropy/coordinates/tests/test_sky_coord.py) and found zero attribute-style accesses to altaz/hadec/teme/lsr*/galactocentric/hcrs/heliocentric*, no ConvertError expectations, and the only bare `pytest.raises(AttributeError)` uses (test_immutable, test_set_attribute_exceptions) exercise `__setattr__`, not this branch. Consequence for refinement.md's §C claim: read as "behaviourally equal to the gold patch ON THE TESTED INPUTS, so it resolves" the claim survives and is what the gate scores; read as unqualified behavioural equality it is too strong, since atk_6 verifies and diverges off the tested set.

The spec could be tightened by pinning each partial domain leg's surfaced subject the way leg 5's is pinned. This is a strength-margin observation, not a gate failure: the leg that the patch actually CHANGES (leg 5, the residual delegation) is pinned tightly on both paths -- subject, value, selector and token -- and every attack aimed at it (atk_1/2/3/4/9-shape/17/19) is either rejected or resolves.

REFINEMENT.MD AUDIT (§A table tags mechanically extracted): A1=R, A2=R+I, A3=R+A-consumed, A4=R+A-consumed, A5=R+A-consumed, A6=A-consumed. Every leg is R / A-consumed / I -- NO kind-3 (unexpressible-changed-op) step, so §B's claim holds: the single genuinely-changed operation (the fail branch's delegation) is A-consumed about the UNCHANGED callee object.`__getattribute__`, and there is no axiom about the function under change (`__getattr__` is modelled deeply as resolve_missing). Note the §A table header text says A2-A5 are "R + I" in prose while the table cells for A3-A5 correctly read "R + A-consumed"; the cells are the operative tags and they are right.

A-LEG / DEEP-MODEL CORRESPONDENCE verified against the real repo source at base_commit (sky_coordinate.py:869-900, fetched from the upstream repository): the four domain guards and their exact priority order map onto A2-A5 (`_is_name`:875-876, `attr in frame_transform_graph.frame_attributes`:881-885, `not attr.startswith("_") and hasattr(self._sky_coord_frame, attr)`:889-890, `frame_cls is not None and self.frame.is_transformable_to(frame_cls)`:893-895), and A6's gold op `return self.__getattribute__(attr)` is a RETURN OF A CALL, so both callee paths become `__getattr__`'s own -- which is why the axiom correctly states two paths rather than a counterfactual totality.

I independently RE-MEASURED every mapping.md §3.1 claim inside the instance image (work/probe2.py, gold patch applied): leg 2 partiality -- a subclass property `_equinox` that raises gives SkyCoord.`__getattr__`(c,"equinox") -> TypeError('descriptor blew up'), exactly as claimed; leg 5 failing path -- the F2P scenario `prop` -> AttributeError("'D' object has no attribute 'random_attr'"), i.e. residual_step_subject(prop)=random_attr != prop, confirming the discriminating observable; leg 5 degenerate case -- a plain missing name blames itself (nothing_here -> "...no attribute 'nothing_here'"); leg 5 SUCCEEDING path is real -- with all four guards False, SkyCoord.`__getattr__`(e,"CLASS_CONST") returns 12345, so the conditional (not Ensures(False)) leg-5 return path is faithful and mapping.md is right that a total-failure axiom would be unsound; leg 3 guard type-bridge edge -- radial_velocity -> ValueError, pm_dec -> TypeError raised out of the GUARD, matching mapping.md's documented outside-the-bridge set rather than being silently dropped.

The transform-leg partiality claims were likewise re-measured (probe.py, above) and all five named failure modes reproduced with the stated exception types. So the A-legs' correspondence to the real callees holds in both the failing and the succeeding direction.

**VERDICT:** SOUND (advisory). 19 same-spec attacks all executed to a machine verdict, 14 rejected by the spec, 5 candidates each shown by an EXECUTED official-harness resolve run to resolve (F2P 1/1, P2P 426/426, attempts=1, non-flaky). Positive control verifies; prepatch bug reproduced and rejected. No verify-but-not-resolve witness; no timeouts or INCONCLUSIVE outcomes. Filed with the atk_6/atk_13 strength-margin caveat above as the one thing a maintainer should know.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_12.py`, `atk_14.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_6.py`, `atk_9.py`, `atk_11.py`, `atk_13.py`, `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verify-but-not-resolve witness found. All 19 same-spec attacks reached a machine verdict: 14 rejected by the spec, 5 CANDIDATEs (atk_6, atk_9, atk_11, atk_13, atk_15), and every one of those 5 had its faithful refined patch materialized against base_commit 1a4462d72eb03f30dc83a879b1dd57aac8b2c18b and EXECUTED through the official harness (run_resolve) -> resolved=True, completed=True, attempts=1, flaky=False, F2P 1/1, P2P 426/426 for all five. Since BROKEN requires a verifying wrong impl whose faithful patch does NOT resolve, and no such patch exists among the executed runs, the spec is not shown broken. The closest approach to a break is atk_6 (see notes): it IS a genuine behavioural divergence from gold on real, untested inputs, but its patch resolves, so per the gate criterion it is not a counterexample.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, astropy__astropy-14096 (nagini). Bundle model.py sha256=b007674d454894f20364695400dae3a36a458d9bcd064dee18bf91cd62205fb6, md5=44de90bab439c24be372e26649f513b0. All 19 attacks + the positive control were authored by copying model.py and editing ONLY the impl region (generator gen.py splits on the `# impl-start`/`# impl-end` markers, so axioms/@Pure/Requires/Ensures/Exsures are byte-identical by construction), and all 20 were independently confirmed byte-identical-spec via `python -m swebench_unified.adversary same-spec nagini astropy__astropy-14096 <path>` (exit 0) BEFORE verification. Verifications were run 3 concurrently as background jobs (JVM+Z3 per check); no timeouts, no crashes, no INCONCLUSIVE outcomes.

**POSITIVE CONTROL:** pos_control.py (byte-identical to bundle model.py) -> `adversary weakness` = CANDIDATE, i.e. VERIFIES in 16.3s. The spec is satisfiable and not over-fitted against its own gold impl.

PER-ATTACK RESULTS (command for each: `python -m swebench_unified.adversary weakness nagini astropy__astropy-14096 atk_N.py`; logs at w_N.log):
- atk_1.py  PREPATCH BUG re-encoded (`raise AttributeAccessError(name)` on leg 5) -> rc=2 does not verify. PREPATCH REPRODUCED + rejected; the spec senses the change (G-DIFF).
- atk_2.py  UNGROUNDED-ORACLE ECHO, the prior pass's named counterexample re-encoded (`raise AttributeAccessError(residual_step_subject(name))`, never performs the step) -> rc=2 rejected. The bodyless capability predicate holds.
- atk_3.py  VALUE-ORACLE ECHO on leg 5's returning path (`return residual_step_value(name)`) -> rc=2 rejected.
- atk_4.py  CONTROL-FLOW-EFFECT swallow on leg 5: genuinely performs the step (legitimately HOLDS residual_step_performed) then catches and returns alias_value -> rc=2 rejected on the Ensures' residual_step_succeeds selector. Confirms the selector conjunct is load-bearing and the token alone cannot see this.
- atk_5.py  CONTROL-FLOW-EFFECT invert on leg 2: performs frame_attr_step, then raises even where it SUCCEEDED -> rc=2 rejected on the negated selector in the Exsures.
- atk_6.py  A-LEG SUBJECT SUBSTITUTION on all three PARTIAL DOMAIN legs (2/3/4): performs each step (so holds every token and every negated selector legitimately) but discards the step's own failure and raises a fresh failure blaming the REQUESTED name -> CANDIDATE (verifies 22.8s). Admitted because the Exsures pins RaisedException().subject ONLY on leg 5; legs 2-4's failing arms constrain selector+token but leave the subject free.
- atk_7.py  BOUNDARY priority swap (transform tried before the passthrough) -> rc=2 rejected.
- atk_8.py  BORROWED TOKEN: leg 4 performs the RESIDUAL step (another leg's work) then returns transform_value -> rc=2 rejected. Per-leg capabilities hold.
- atk_9.py  CONTROL-FLOW-EFFECT laundering on leg 5: performs the step, discards its exception OBJECT, raises a fresh one carrying the same echoed subject -> CANDIDATE (verifies 23.1s).
- atk_10.py ALIAS-LEG-MADE-PARTIAL: a failure escapes the one TOTAL leg -> rc=2 rejected. Confirms leg 1's totality was not relaxed along with the others.
- atk_11.py EXTRA ABSORBED CROSS-LEG STEP: leg 2 first performs the TRANSFORM step and swallows its outcome, then does its own work -> CANDIDATE (verifies 23.8s).
- atk_12.py PARTIAL-DOMAIN drop: the passthrough leg removed entirely -> rc=2 rejected.
- atk_13.py A-LEG SUBJECT SUBSTITUTION on the transform leg alone, blaming residual_step_subject(name) instead of its own failure -> CANDIDATE (verifies 17.2s).
- atk_14.py DIVERGENCE: unbounded loop before the residual step, clauses discharged only by an unreachable tail -> rc=2 rejected by method-level MustTerminate(10).
- atk_15.py RETRY leg 5: performs the residual step, catches, performs it AGAIN so the second failure propagates -> CANDIDATE (verifies 20.1s).
- atk_16.py SWALLOW the TRANSFORM step's failure and return the leg's own value -> rc=2 rejected on the transform leg's selector. Confirms the swallow guard is present on a PARTIAL DOMAIN leg, not only on leg 5.
- atk_17.py A-LEG NAME-INDEXING: performs residual_step(name) (so legitimately holds the token for `name`) but then surfaces residual_step(alias_value)'s outcome, i.e. a DIFFERENT name's -> rc=2 rejected. Confirms the token and the subject oracle are genuinely indexed by `name` and not harvestable from any lookup.
- atk_18.py UNGROUNDED ORACLE across legs 2-4: returns each leg's value WITHOUT performing the step (no token, no selector fact) -> rc=2 rejected.
- atk_19.py CROSS-LEG BORROWED TOKEN on the returning path: leg 5 performs leg 2's step then echoes residual_step_value(name) -> rc=2 rejected.

MANDATORY RESOLVE RUNS -- all 5 CANDIDATEs, faithful refined patches materialized against base_commit 1a4462d72eb03f30dc83a879b1dd57aac8b2c18b (generator work/mkpatch.py; each patch confirmed `git apply --check -p1` clean; the same generator's gold control diff is textually identical to the bundle patch.diff modulo the hunk-header function context, proving the diff machinery faithful), executed via the official harness `python work/resolve.py patch_atk_N.diff` -> swebench_unified.harness.run_resolve under `docker`:
- patch_atk_6.diff  -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1 success 0 failure, P2P 426/426 success 0 failure.
- patch_atk_9.diff  -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
- patch_atk_11.diff -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
- patch_atk_13.diff -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
- patch_atk_15.diff -> resolved=True, completed=True, note=resolved, attempts=1, flaky=False, F2P 1/1, P2P 426/426.
Every candidate's faithful patch RESOLVES, so no attack exhibited verify AND not-resolve.

WHY atk_9/11/15 ARE GENUINELY CORRECT: each only adds an idempotent, side-effect-free re-performance of a step whose outcome is discarded or re-raised with the same blamed subject; the surfaced outcome is unchanged, which is why F2P (match="random_attr") and all 426 P2P pass. Correctly admitted -- they ARE behaviourally equal on the tested inputs, which is exactly refinement.md's G-EQ claim.

HONEST CAVEAT ON atk_6 / atk_13 (the sharpest finding, reported because it is a real gap in the spec's strength even though it does not meet the BROKEN criterion). These are NOT behaviourally equal to gold. I measured the divergence inside the instance image (probe.py, run under `docker` on swebench/sweb.eval.x86_64.astropy_1776_astropy-14096): with the GOLD patch applied, SkyCoord.`__getattr__`(SkyCoord(1d,2d,icrs), name) surfaces altaz -> AttributeError("'NoneType' object has no attribute 'to_geodetic'"), hadec -> same, teme -> AttributeError(...

'scale'), galactocentric -> ConvertError("...requires a 3D coordinate..."), hcrs -> UnitsError("...do not have length units..."); with patch_atk_6 applied the SAME five inputs instead all surface AttributeError("'SkyCoord' object has no attribute '<name>'"). So atk_6 destroys the transform leg's diagnostic (and CHANGES THE EXCEPTION TYPE for galactocentric ConvertError and hcrs UnitsError, converting non-AttributeError failures into AttributeError -- a genuinely observable difference).

It resolves only because no F2P/P2P test in the frozen set observes a failing outcome of legs 2-4: I grepped the base test file (2167 lines, all 426 P2P + the 1 F2P live in astropy/coordinates/tests/test_sky_coord.py) and found zero attribute-style accesses to altaz/hadec/teme/lsr*/galactocentric/hcrs/heliocentric*, no ConvertError expectations, and the only bare `pytest.raises(AttributeError)` uses (test_immutable, test_set_attribute_exceptions) exercise `__setattr__`, not this branch. Consequence for refinement.md's §C claim: read as "behaviourally equal to the gold patch ON THE TESTED INPUTS, so it resolves" the claim survives and is what the gate scores; read as unqualified behavioural equality it is too strong, since atk_6 verifies and diverges off the tested set.

The spec could be tightened by pinning each partial domain leg's surfaced subject the way leg 5's is pinned. This is a strength-margin observation, not a gate failure: the leg that the patch actually CHANGES (leg 5, the residual delegation) is pinned tightly on both paths -- subject, value, selector and token -- and every attack aimed at it (atk_1/2/3/4/9-shape/17/19) is either rejected or resolves.

REFINEMENT.MD AUDIT (§A table tags mechanically extracted): A1=R, A2=R+I, A3=R+A-consumed, A4=R+A-consumed, A5=R+A-consumed, A6=A-consumed. Every leg is R / A-consumed / I -- NO kind-3 (unexpressible-changed-op) step, so §B's claim holds: the single genuinely-changed operation (the fail branch's delegation) is A-consumed about the UNCHANGED callee object.`__getattribute__`, and there is no axiom about the function under change (`__getattr__` is modelled deeply as resolve_missing). Note the §A table header text says A2-A5 are "R + I" in prose while the table cells for A3-A5 correctly read "R + A-consumed"; the cells are the operative tags and they are right.

A-LEG / DEEP-MODEL CORRESPONDENCE verified against the real repo source at base_commit (sky_coordinate.py:869-900, fetched from the upstream repository): the four domain guards and their exact priority order map onto A2-A5 (`_is_name`:875-876, `attr in frame_transform_graph.frame_attributes`:881-885, `not attr.startswith("_") and hasattr(self._sky_coord_frame, attr)`:889-890, `frame_cls is not None and self.frame.is_transformable_to(frame_cls)`:893-895), and A6's gold op `return self.__getattribute__(attr)` is a RETURN OF A CALL, so both callee paths become `__getattr__`'s own -- which is why the axiom correctly states two paths rather than a counterfactual totality.

I independently RE-MEASURED every mapping.md §3.1 claim inside the instance image (work/probe2.py, gold patch applied): leg 2 partiality -- a subclass property `_equinox` that raises gives SkyCoord.`__getattr__`(c,"equinox") -> TypeError('descriptor blew up'), exactly as claimed; leg 5 failing path -- the F2P scenario `prop` -> AttributeError("'D' object has no attribute 'random_attr'"), i.e. residual_step_subject(prop)=random_attr != prop, confirming the discriminating observable; leg 5 degenerate case -- a plain missing name blames itself (nothing_here -> "...no attribute 'nothing_here'"); leg 5 SUCCEEDING path is real -- with all four guards False, SkyCoord.`__getattr__`(e,"CLASS_CONST") returns 12345, so the conditional (not Ensures(False)) leg-5 return path is faithful and mapping.md is right that a total-failure axiom would be unsound; leg 3 guard type-bridge edge -- radial_velocity -> ValueError, pm_dec -> TypeError raised out of the GUARD, matching mapping.md's documented outside-the-bridge set rather than being silently dropped.

The transform-leg partiality claims were likewise re-measured (probe.py, above) and all five named failure modes reproduced with the stated exception types. So the A-legs' correspondence to the real callees holds in both the failing and the succeeding direction.

**VERDICT:** SOUND (advisory). 19 same-spec attacks all executed to a machine verdict, 14 rejected by the spec, 5 candidates each shown by an EXECUTED official-harness resolve run to resolve (F2P 1/1, P2P 426/426, attempts=1, non-flaky). Positive control verifies; prepatch bug reproduced and rejected. No verify-but-not-resolve witness; no timeouts or INCONCLUSIVE outcomes. Filed with the atk_6/atk_13 strength-margin caveat above as the one thing a maintainer should know.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No diverging input found. The spec is NOT too strong; every clause was measured against the real patched SkyCoord.`__getattr__` and holds.

SETUP. Reference = swebench/sweb.eval.x86_64.astropy_1776_astropy-14096 image at base_commit 06c74e6ae/1a4462d72e with patch.diff APPLIED (container gp2b_14096, /testbed, conda env `testbed`). Confirmed the applied hunk is exactly the gold change (`raise AttributeError(...)` -> `return self.__getattribute__(attr)`), so I compared against the fixed behavior, not the base version. Also confirmed  carries the same one-hunk diff.

### Baseline facts
* `bash scripts/nagini_verify.sh` on the bundle model.py: exit 0 (verifies).
* `adversary same-spec` on my byte copy: exit 0 (SAME) — spec region confirmed identical, so I audited the frozen spec.
* Bundle model_prepatch.py: verifier exit 1, failing exactly `Assertion (not residual_step_succeeds(name)) might not hold` — the spec senses the patch (G-DIFF), i.e. it describes post-patch behavior as the brief states.

INDEPENDENT PROBE (mine, not the bundle's). For each (object, name) I evaluated the four repo guards in the repo's own priority order, derived the leg the spec selects, ran THAT leg's own repo step expression, ran the real `__getattr__`, and checked the exact spec clause for the leg (selector direction + value equality; on leg 5 also the blamed-subject equality). One shared object per input, since getattr is non-mutating — my first run's `VALUE` reports were a harness artifact of comparing bound methods from two different instances, and vanished once corrected (a real defect would not).
* Sweep A: 12 objects x 490 names = 5828 in-bridge inputs. 0 violations. Legs hit 10/160/116/270/5272; step-failing per leg {2:1, 3:0, 4:113, 5:5171}, step-succeeding {2:159, 3:116, 4:157, 5:101}. Surfaced exception kinds include ConvertError/UnitsError/TypeError/ValueError out of leg 4 — i.e. the non-AttributeError partiality the spec's two-path form allows and a total form would have wrongly rejected.
* Sweep B (randomized, seed 99991): 51 builders (every instantiable registered frame, with and without obstime+location) x 1552 names = 79152 inputs. 0 violations, 0 guard-raised.
* Leg 1 (the ONLY clause the spec asserts as TOTAL — its strongest claim, and the natural place for over-strength): swept 53 objects across every registered frame, 106 alias inputs where `_is_name(attr)` is True. Real function never raised and always returned `self`. Leg 1's totality is sound.
* Leg 2/3 failing paths (thinnest coverage in Sweep A, so targeted directly): 48 constructed leg-2 step failures via `_<frame_attr>` descriptors raising TypeError/ValueError/RuntimeError, and 8 constructed leg-3 step failures via a one-shot data descriptor that passes the hasattr guard then raises on the step read (all four exception kinds). Real outcome matched the step outcome in every case. 0 violations.
* Adversarial leg-5 edges: property raising a non-AttributeError (TypeError), self-recursive property (RecursionError), property blaming the requested name itself (degenerate subject==name), a property that RESOLVES (777), and resolving names `__class__`/`_sky_coord_frame`/`__dict__`. Real and step agreed on path and subject throughout, including subject=None when no name is blamed. Notably the spec does NOT assume subject==name, and a genuinely non-deterministic descriptor (alternating read) is the only place real and step differ — that is callee non-determinism, not a spec claim, and the spec's oracles are only ever applied per-call.

CORROBORATION (bundle's own checkers, run by me inside the image): axiom_check.py exit 0 (leg-5 subject blames the inner missing name on 9 boundary + 300 fuzz pairs; resolving path returns normally; 10 transform targets succeed and 11 fail, so no leg may be total). conformance_check.py exit 0: 102183 inputs, 0 disagreements, with the 12 velocity/differential inputs reported as outside-the-type-bridge rather than silently dropped — an honest, checkable coverage claim, since for those the repo's passthrough GUARD itself raises and no boolean input exists to supply.

**ASSESSMENT.** The spec's central design choice — every leg but the alias is PARTIAL, stated as two paths keyed to that leg's own `*_step_succeeds(name)` selector — is exactly what the real function does; a total form would be unfaithful and refinement.md documents that it was corrected in the honest direction, which my leg-4 measurements independently reproduce (altaz/hadec/teme/lsr/galactocentric/hcrs all raise). The selector conjuncts and the bodyless per-leg `*_step_performed` capabilities add discriminating strength without asserting anything false about the callees. No input was found on which the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** NO RELAXATION IS IN PLAY — checked directly, not inherited. meta.json has no `relaxed_leakage` key (python `'relaxed_leakage' in meta` -> False), RELAXED_LEAKAGE.md does not exist anywhere under benchmark-verified/astropy__astropy-14096/ (find -iname '*RELAX*' -> empty), and gates.G-LEAK.status == "pass" with detail "spec view clean" (not "relaxed"). So there is no unavoidability argument for me to credit or reject; I judged this spec view against the strict §0.6 standard, and it passes on that standard. No file in the bundle addresses the panel, tells me how to record, or asserts which verdict is honest — I grepped model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py for panel/attacker/reviewer/verdict/NO-LEAKAGE/submit_result/"record this as"/"do not flag": the only hit is properties.py's "clauses (the things an attacker must defeat)", which is a rival-design comment in a non-spec-view file, not reviewer direction. Nothing to report as bundle-to-reviewer instruction.

**PROVENANCE.** I derived the spec view myself via swebench_unified.markers.spec_view with the nagini LanguageTables (not from any stamp). sha256(model.py)=b007674d454894f20364695400dae3a36a458d9bcd064dee18bf91cd62205fb6, sha256(spec_view)=bdcc35410eae02b0336a64057c0bacdaeef3ccf12b1419999a824e431dd5d66a, 344 lines, spec_view idempotent (spec_view(spec_view(src))==spec_view(src)), impl region correctly collapsed to the elision placeholder, and the gold added line's idiom `__getattribute__` is absent from the whole view (count 0). Positive control: bash scripts/nagini_verify.sh on the bundle model.py -> exit 0; `adversary same-spec nagini astropy__astropy-14096` on it -> exit 0 ("SAME").

THE PRIOR G-PANEL-3 fail DOES NOT APPLY TO THIS TEXT — and I re-measured rather than assuming. verdict.md records a LEAKAGE at model.py digest 2e8a8d11..., citing prose that told the solver the fallback "must re-enter the ordinary attribute-lookup mechanism for that same name and surface whatever that mechanism produces". Every token of that disclosure is gone at the current digest b007674d...: counts in the spec view for 're-enter'=0, 'reenter'=0, 'ordinary'=0, 'mechanism'=0, 'lookup mechanism'=0, 'ordinary_lookup'=0, 'reentered'=0, 'standard_lookup'=0, 'getattribute'=0, 'delegat'=0. The identifiers were renamed to residual_step / residual_step_succeeds / residual_step_value / residual_step_subject / residual_step_performed and the prose to "the residual resolution of that same name", which names a position in the candidate list (leg 5 of 5), not Python's attribute-lookup machinery and not the gold idiom. The recorded G-PANEL-3 fail is a stale-digest artifact for this text.

MECHANICAL SCREEN, INCLUDING THE HARD CASE. leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. I also ran it with problem_statement="" so that NOTHING could be excused as already-public: still hard_failures=[]. So the pass is not resting on the PS excusing a symbol echo.

Component checks: no diff marker in the view; no gold changed line reproduced (the six changed lines are '# Fail', 'raise AttributeError(', the f-string, ')', '# Call `__getattribute__`; this will give correct exception.', 'return self.`__getattribute__`(attr)' — none appear normalized in the view); patched file path 'astropy/coordinates/sky_coordinate.py' and dotted module absent; patch changed-symbol set is {'getattr'} and it does not occur in the view; `_NARRATION_RE` over view comments/docstrings -> empty (no bug/fix/patched/regression/previously/incorrectly/wrong/broken). Absent by direct grep: SkyCoord, sky_coordinate, AttributeError, transform_to, `_is_name`, frame_transform_graph, `__getattribute__`, random_attr, gh-8340, 'pre-patch', 'the change', 'no longer', 'used to'. The only 'swallow' hits describe a forbidden consumer behaviour, not a repo edit.

HINTS-ONLY VOCABULARY (the failure mode §0.6 calls most common) IS CLEAN. Set-differenced spec-view words (len>=5) against problem_statement and hints_text: the words present in hints_text and the view but not the PS are exactly ['about','another','different','exception','other','since','which'] — all generic English, no diagnosis. Notably the hints' actual proposed approach ("catch the AttributeError in the property and raise another exception", "`__getattr__` does not know about the other errors") is nowhere echoed, and neither is the gold's opposite approach.

STRIP-THE-NARRATION TEST — RUN, NOT ASSERTED (lab, bundle untouched). I built v_denarr_gold.py: module docstring reduced to """Model.""", every function/class docstring removed, every non-marker comment removed, EVERY contract conjunct left byte-identical, gold impl kept. Results with scripts/nagini_verify.sh: v_denarr_gold exit=0 (the de-narrated spec is neither vacuous nor broken); v_denarr_prepatch (de-narrated spec + pre-change behaviour `raise AttributeAccessError(name)`) exit=1, failing on `Assertion (not residual_step_succeeds(name)) might not hold`; v_denarr_echo (the pure-oracle cheat `if residual_step_succeeds(name): return residual_step_value(name)` else `raise AttributeAccessError(residual_step_subject(name))`, never invoking residual_step) exit=1.

So the entire discriminating power lives in the CONTRACT (selector, subject equality, and the bodyless capability predicate) and ZERO of it lives in prose — which is the direction that matters here: it means the surviving prose is not a forced disclosure propping up a clause, and equally that there is nothing left in it to trim, because the mechanism vocabulary is already gone. Independently re-confirmed G-DIFF on the shipped artifact: bundle model_prepatch.py exit=1 on the same `(not residual_step_succeeds(name))` assertion.

WHAT THE VIEW DOES DISCLOSE, AND WHY IT IS WITHIN THE PUBLIC PS. The discriminating observable stated in the view is that leg 5's surfaced failure blames `residual_step_subject(name)` — "the name the residual resolution found missing", explicitly NOT assumed equal to the requested name. That is verbatim the problem_statement: "the error message is misleading because it says `prop` doesn't exist, where it should say `random_attr` doesn't exist", and it is exactly what the F2P test reads (pytest.raises(AttributeError, match="random_attr")). So this is a PS-derivable requirement, not a hidden discriminator.

The view's other non-public-looking content is leg 5 having a SUCCEEDING path (residual_step_succeeds / residual_step_value) and the four partial domain legs; that is contract SHAPE required for faithfulness to the real function (verified against the real source at base_commit: sky_coordinate.py:869-898 shows the four unchanged guarded branches and the final fallback), and §0.6 targets quoted gold lines, patched-symbol echoes, and prose narration of the bug->fix mechanism — none of which is present. A solver given this view learns "a fifth fallback exists whose failure must blame the inner missing name", which the issue already demands; it is not handed the `return self.__getattribute__(attr)` idiom the issue withheld.

**SCOPE.** My verdict covers leakage only. meta.json also records G-PANEL-2 fail (spec-too-strong at the partial legs); that is a different gate and I neither re-ran nor credited it — this cell may not be green for reasons outside my finding. All work in /tmp (,); the bundle was read-only and unmodified (verified by sha256 of model.py matching before and after).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
