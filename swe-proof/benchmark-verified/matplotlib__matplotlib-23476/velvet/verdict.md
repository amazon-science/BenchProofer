# P2 adversarial audit — matplotlib__matplotlib-23476

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_prepatch.lean`, `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_14.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The prior pass's named counterexample (nontermination-vacuity) is REPAIRED and no longer reproduces. That counterexample depended on the spec carrying `set_option loom.semantics.termination "partial"` + `open PartialCorrectness`, under which a diverging impl discharges every postcondition vacuously. The FROZEN spec now under audit carries `termination "total"` + `open TotalCorrectness`, and I re-encoded the counterexample verbatim in all three of its prior forms: atk_1 (unconditional divergence + CORRECT return), atk_2 (the prior pass's DECISIVE witness: unconditional divergence guarding the blatantly wrong `resolution + 999.0`), and atk_3 (the surgical variant: diverge only on `baseline = some _`, the exact branch the F2P test test_unpickle_with_device_pixel_ratio drives). All three now FAIL to verify (lean_verify exit 1) with the on-point error `Decreasing annotations are required in total correctness semantics` (Loom/CaseStudies/Macro.lean's `decreasing` elaborator throws exactly when semantics=total and the annotation is absent). atk_19 confirms the obligation is genuinely discharged rather than rubber-stamped: supplying a bogus measure over Nat truncated subtraction leaves the live goal `0 - (x + 1) < 0 - x` (case «decreasing_1»), so the loop rule really does demand a well-founded measure. The one verifying same-spec attack (atk_14) is a structurally different CORRECT ECHO whose faithful patch RESOLVED under the official harness, which is not a spec weakness.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return snap
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,6 +61,11 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
+    let mut x : Nat := 0
+    while 0 ≤ x
+    invariant True
+    do
+      x := x + 1
     return { snap with resolution := snap.baseline.getD snap.resolution }
     -- impl-end
 
```

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,12 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    let mut x : Nat := 0
+    while 0 ≤ x
+    invariant True
+    do
+      x := x + 1
+    return { snap with resolution := snap.resolution + 999.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,15 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    match snap.baseline with
+    | none => return snap
+    | some v =>
+      let mut x : Nat := 0
+      while 0 ≤ x
+      invariant True
+      do
+        x := x + 1
+      return { snap with resolution := v }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,9 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    match snap.baseline with
+    | none => return { snap with resolution := snap.resolution }
+    | some _ => return { snap with resolution := snap.resolution }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,9 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { resolution := snap.baseline.getD snap.resolution,
+             baseline := snap.baseline,
+             payload := [] }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,9 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { resolution := snap.baseline.getD snap.resolution,
+             baseline := none,
+             payload := snap.payload }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    let r :| True
+    return { snap with resolution := r }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    let r ← finalizeSnapshot snap
+    return { r with resolution := r.resolution + 999.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 10 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    assert False
+    return { snap with resolution := snap.resolution + 999.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 11 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    let r :| False
+    return { snap with resolution := r }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 12 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { snap with
+             resolution := (snap.baseline.getD snap.resolution) * 1e308 / 1e308 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { snap with
+             resolution := (snap.baseline.getD snap.resolution) + 1e17 - 1e17 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 14 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    assert (1 = 0)
+    return { snap with resolution := snap.resolution + 999.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 15 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -61,7 +61,9 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    match snap.baseline with
+    | some v => return { snap with resolution := v }
+    | none => return { snap with resolution := snap.resolution }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 16 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { snap with resolution := 42.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 17 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { snap with resolution := snap.baseline.get! }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 18 — `atk_17.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    return { snap with resolution := snap.baseline.getD 0.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 19 — `atk_18.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,10 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    if snap.resolution == snap.resolution then
+      return { snap with resolution := snap.baseline.getD snap.resolution }
+    else
+      return { snap with resolution := 0.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

Attack 20 — `atk_19.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,13 @@
   ensures out.payload = snap.payload
   do
     -- impl-start
-    return { snap with resolution := snap.baseline.getD snap.resolution }
+    let mut x : Nat := 0
+    while 0 ≤ x
+    invariant True
+    decreasing (0 - x)
+    do
+      x := x + 1
+    return { snap with resolution := snap.resolution + 999.0 }
     -- impl-end
 
 prove_correct finalizeSnapshot by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The step under spec touches only values already
--  present in the assembled snapshot; it calls no outside routine whose
--  behaviour would have to be assumed. The whole effect — choosing which
--  resolution value the snapshot carries — is modeled directly below.)
-- axioms-end

-- pure-start
/- A serialized snapshot of a drawing surface, abstracted to the fields this
   step touches or must preserve:

   - `resolution` — the dots-per-inch value the snapshot currently carries.
   - `baseline` — an optional, separately recorded reference resolution. It is
     present when a reference value was captured for this surface and absent
     otherwise.
   - `payload` — the remainder of the assembled snapshot (everything else the
     surface contributes to its serialized form). It is opaque here and is not
     affected by the step under spec.

   Only these touched/observed parts are carried; the bijection to the real
   serialized-state mapping is in mapping.md §2. -/
structure SurfaceSnapshot where
  resolution : Float
  baseline : Option Float
  payload : List Char
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Finalize the resolution recorded in a serialized snapshot.

   A drawing surface's working resolution may differ from the reference
   resolution that was captured for it. The persisted snapshot must carry the
   reference value whenever one is available, so that reading the snapshot back
   reconstructs the surface at its reference resolution rather than at whatever
   transient working value happened to be in effect. When no reference value was
   captured, the current resolution is persisted unchanged.

   This step must disturb nothing else: the recorded reference value itself and
   the rest of the snapshot survive exactly as supplied (directive 5 frame —
   `snap` is read-only, not `mut`; the result is built freshly from it). The
   three guarantees together pin the behavior: the persisted resolution is the
   reference value when present and the current value otherwise, and every other
   part of the snapshot is preserved. -/
method finalizeSnapshot (snap : SurfaceSnapshot) return (out : SurfaceSnapshot)
  ensures out.resolution = snap.baseline.getD snap.resolution
  ensures out.baseline = snap.baseline
  ensures out.payload = snap.payload
  do
    -- impl-start
    return { snap with resolution := snap.baseline.getD snap.resolution }
    -- impl-end

prove_correct finalizeSnapshot by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) — matplotlib__matplotlib-23476 / velvet. VERDICT: SOUND.

### Controls
- pos_control.lean = bundle Solution.lean, confirmed byte-identical (`cmp` -> IDENTICAL). `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0 (VERIFIES). Positive control good; it is a distinct file from every attack.
- atk_prepatch.lean (`return snap`, the pre-patch behaviour): lean_verify -> exit 1, unsolved goal «ensures_3: out.resolution = snap.baseline.getD snap.resolution» / `snap.resolution = snap.baseline.getD snap.resolution`. PREPATCH BUG REPRODUCED, failing exactly on the resolution clause (i.e. exactly when baseline = some _).
- SAME-SPEC: all 20 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec with the velvet backend (only the impl region was edited; axioms/pure/pre/post byte-identical).

=== ATTACKS (19 distinct wrong impls + 1 echo; command for each: `bash scripts/lean_verify.sh atk_N.lean`) ===
PRIOR-PASS COUNTEREXAMPLE RE-ENCODED (nontermination vacuity), all three forms:
- atk_1  uncond. divergence `while 0 <= x` + CORRECT return -> exit 1: 'Decreasing annotations are required in total correctness semantics'. REJECTED.
- atk_2  uncond. divergence + WRONG return (+999.0) — the prior pass's decisive vacuity witness -> exit 1, same error. REJECTED.
- atk_3  conditional divergence ONLY on baseline=some _ (the F2P branch), correct on none -> exit 1, same error. REJECTED.
PARTIAL-DOMAIN / BOUNDARY:
- atk_4  keep working value on BOTH branches (prepatch restricted to the some-branch) -> exit 1, unsolved «ensures_3» with hypothesis `snap.baseline = some i`. REJECTED.
- atk_17 wrong default on the absent branch (`getD 0.0`) -> exit 1, unsolved «ensures_3»: `snap.baseline.getD 0.0 = snap.baseline.getD snap.resolution`. REJECTED.
- atk_16 partial function / panic (`Option.get!`; faithful form is the bare `state['_original_dpi']` subscript -> KeyError) -> exit 1, unsolved «ensures_3». REJECTED.
FRAME / CONTROL-FLOW-EFFECT:
- atk_5  drops the opaque payload (`payload := []`) -> exit 1, unsolved «ensures_1: out.payload = snap.payload». REJECTED (frame is pinned).
- atk_6  erases the recorded reference value (`baseline := none`) -> exit 1, unsolved «ensures_2: out.baseline = snap.baseline». REJECTED (frame is pinned).
- atk_8  unbounded self-recursion then wrong value (the nagini-family guarded-self-call hole) -> exit 1, 'fail to show termination for finalizeSnapshot'. REJECTED.
### Ungrounded-oracle echo
- atk_15 hardcode the very value the F2P test asserts (`resolution := 42.0`) -> exit 1, unsolved «ensures_3»: `42.0 = snap.baseline.getD snap.resolution`. REJECTED. (Had this verified it would have been decisive: `state['_dpi'] = 42.0` passes the F2P test while destroying dpi for every other figure.)
- atk_7  demonic pick of an arbitrary resolution (`let r :| True`) -> exit 1, unsolved «choice_1» AND «ensures_3»: `i = snap.baseline.getD snap.resolution`. REJECTED — choice did not leak angelic.
SPEC-GADGET / VACUITY PROBES:
- atk_9 / atk_13  `assert False` / `assert (1 = 0)` — assertGadget's wp is literally `pure` (Loom/MonadAlgebras/WP/Gen.lean:80), so an unsatisfiable assertion cannot poison the VC context -> exit 1, 'Failed to parse an assertion'. REJECTED.
- atk_10 infeasible pick `let r :| False` -> exit 1, `Findable` synthesis failure. REJECTED.
- atk_19 diverging loop WITH a bogus `decreasing (0 - x)` measure over Nat truncated subtraction -> exit 1, live goal «decreasing_1»: `0 - (x + 1) < 0 - x`. REJECTED — proves the measure obligation is really discharged, so the total-correctness repair is load-bearing and not cosmetic.
I-LEG (Float <-> IEEE-754 double, mapping.md §2) — the deepest remaining trust point:
- atk_11 overflow round-trip `x * 1e308 / 1e308` (algebraically identity; in IEEE 42.0*1e308 -> +inf, inf/1e308 -> inf) -> exit 1, unsolved «ensures_3». REJECTED.
- atk_12 cancellation `x + 1e17 - 1e17` (algebraically identity; in IEEE 42.0 -> 48.0, verified in Python) -> exit 1, unsolved «ensures_3». REJECTED.
- atk_18 NaN reflexivity `if x == x then ... else 0.0` -> exit 1, unsolved «ensures_3» WITH the live hypothesis `if_neg : ¬(snap.resolution == snap.resolution) = true`. REJECTED, and notably Lean does NOT prove Float BEq reflexive — it keeps the NaN case open, i.e. the Float carrier is opaque (no ordered-field axioms to exploit) and faithfully models IEEE NaN. This is the strongest single piece of evidence that the R/I value-selection leg is sound.
### CORRECT ECHO (resolve discriminating-power control):
- atk_14 explicit `match` on baseline instead of `Option.getD` — behaviourally equal to gold, structurally different -> exit 0 VERIFIES. Per protocol I materialized its faithful refined patch (patch_atk_14.diff, transliterating the match to an if/else on `'_original_dpi' in state`) and RAN it through the official harness.

### RESOLVE RUN (mandatory for EVERY verifying attack)
Command: `python3 resolve_one.py atk_14`, calling swebench_unified.harness.run_resolve('matplotlib__matplotlib-23476', patch, timeout=1800, retries=0).
OBSERVED RESULT: {"attack": "atk_14", "resolved": true, "completed": true, "note": "resolved"} (saved at .../resolve_atk_14.json).
atk_14 is therefore a CORRECT ECHO of the gold, not a spec weakness — per docs/architecture.md §6 a candidate whose patch DOES resolve must not fail the gate. It was the ONLY verifying attack, so no verifying wrong impl exists to resolve-check, and there is no BROKEN finding. This run also establishes discriminating power for my oracle invocation: completed=True with a real report, unlike the prior pass whose three resolve runs all hung to the wall clock and produced completed=False (which is what made that pass INCONCLUSIVE rather than BROKEN).

### REFINEMENT.MD / MAPPING.MD AUDIT (A-legs, per assignment focus)
Leg kinds: A1 = R, A2 = I, A3 = I, A4 = R + I. Every leg is R or I; there is NO kind-3 (inexpressible-changed-op) leg, and §B states this explicitly and correctly — the one operation that genuinely changed (which dpi value the serialized state carries) is a concrete dict-lookup selection modeled directly as `Option.getD`, not hidden behind an axiom. A-LEGS: there are NONE, and I verified this mechanically rather than taking the doc's word: the axioms region of Solution.lean contains only comment lines (no `axiom` declaration), the pre-conditions and post-conditions regions are empty, and meta.json records axioms=[] and deep_model_references=[] with G-AX status=skip ('no axiom_check.py (no axioms in bundle)').

So there is no axiom-soundness trust point and no deep-model reference whose correspondence to a real callee could drift — consistent with mapping.md §3 ('None. ... invokes no repository or stdlib routine whose behaviour must be axiomatized'). The added gold line `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` genuinely performs only a dict read and a dict write over values already in `state`, so the claimed absence of callees is accurate.

MODEL<->PATCH CORRESPONDENCE: `dict.get(k, d)` <-> `Option.getD d` (some <-> key present, none <-> absent) is exact; key-assignment <-> record field update is exact; `state['_dpi']` is always present after `super().__getstate__()`, so the `dict.get` default operand is always well-defined and the `none` branch of the Lean model is reachable exactly when `_original_dpi` was never set by the canvas. The frame clauses pin 'nothing else changed', and atk_5/atk_6 confirm mechanically that both frame clauses bite. The Float carrier is opaque (atk_11/atk_12/atk_18), so the only I-leg with any semantic content — value selection, no arithmetic — cannot drift from IEEE-754 behaviour.

ONE DOC NOTE (not a defect, no gate impact): refinement.md §C's sentence 'any impl verifying against this frozen spec, refined per the map below, is behaviourally equal to the gold patch on the tested inputs, so it resolves' is now TRUE for the frozen artifact, but it is true only because the spec carries the total-correctness obligation. §C does not mention termination anywhere, so the argument as written omits the very hypothesis that makes it sound (and was false for the earlier partial-correctness version of this bundle, per the recorded G-EQ fail). Worth one clarifying clause in §C; it does not change any leg's kind or any verdict.

### Parallelism
Attack verifications were launched as concurrent background Bash jobs, <=4 at a time: batch1 = pos_control, atk_prepatch, atk_1, atk_2; batch2 = atk_3..atk_6; batch3 = atk_7..atk_10; batch4 = atk_11..atk_14; batch5 = atk_15..atk_17; batch6 = atk_18, atk_19. The atk_14 resolve run was launched as a detached background job and collected on completion. Schedule only — every attack was fully verified and the one needed resolve run fully executed and reported.

### Verdict
SOUND. 19 distinct same-spec wrong impls (spanning nontermination vacuity in all three prior-pass forms, partial-domain, boundary, frame, control-flow-effect, self-recursion, ungrounded-oracle echo, spec-gadget vacuity, infeasible choice, bogus measure, and three Float/IEEE I-leg attacks) were re-encoded and verified; ALL 19 were rejected by the verifier, each on the on-point postcondition or termination obligation. The prepatch bug reproduces, the byte-identical positive control verifies, and the single verifying same-spec impl is a correct echo whose faithful patch RESOLVED under the official harness (completed=True). No verifying wrong impl exists whose faithful refined patch fails to resolve, so no verify=>correct break was found; the prior pass's nontermination counterexample is genuinely repaired by the total-correctness semantics rather than merely masked.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_prepatch.lean`, `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_14.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The prior pass's named counterexample (nontermination-vacuity) is REPAIRED and no longer reproduces. That counterexample depended on the spec carrying `set_option loom.semantics.termination "partial"` + `open PartialCorrectness`, under which a diverging impl discharges every postcondition vacuously. The FROZEN spec now under audit carries `termination "total"` + `open TotalCorrectness`, and I re-encoded the counterexample verbatim in all three of its prior forms: atk_1 (unconditional divergence + CORRECT return), atk_2 (the prior pass's DECISIVE witness: unconditional divergence guarding the blatantly wrong `resolution + 999.0`), and atk_3 (the surgical variant: diverge only on `baseline = some _`, the exact branch the F2P test test_unpickle_with_device_pixel_ratio drives). All three now FAIL to verify (lean_verify exit 1) with the on-point error `Decreasing annotations are required in total correctness semantics` (Loom/CaseStudies/Macro.lean's `decreasing` elaborator throws exactly when semantics=total and the annotation is absent). atk_19 confirms the obligation is genuinely discharged rather than rubber-stamped: supplying a bogus measure over Nat truncated subtraction leaves the live goal `0 - (x + 1) < 0 - x` (case «decreasing_1»), so the loop rule really does demand a well-founded measure. The one verifying same-spec attack (atk_14) is a structurally different CORRECT ECHO whose faithful patch RESOLVED under the official harness, which is not a spec weakness.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_19.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The step under spec touches only values already
--  present in the assembled snapshot; it calls no outside routine whose
--  behaviour would have to be assumed. The whole effect — choosing which
--  resolution value the snapshot carries — is modeled directly below.)
-- axioms-end

-- pure-start
/- A serialized snapshot of a drawing surface, abstracted to the fields this
   step touches or must preserve:

   - `resolution` — the dots-per-inch value the snapshot currently carries.
   - `baseline` — an optional, separately recorded reference resolution. It is
     present when a reference value was captured for this surface and absent
     otherwise.
   - `payload` — the remainder of the assembled snapshot (everything else the
     surface contributes to its serialized form). It is opaque here and is not
     affected by the step under spec.

   Only these touched/observed parts are carried; the bijection to the real
   serialized-state mapping is in mapping.md §2. -/
structure SurfaceSnapshot where
  resolution : Float
  baseline : Option Float
  payload : List Char
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Finalize the resolution recorded in a serialized snapshot.

   A drawing surface's working resolution may differ from the reference
   resolution that was captured for it. The persisted snapshot must carry the
   reference value whenever one is available, so that reading the snapshot back
   reconstructs the surface at its reference resolution rather than at whatever
   transient working value happened to be in effect. When no reference value was
   captured, the current resolution is persisted unchanged.

   This step must disturb nothing else: the recorded reference value itself and
   the rest of the snapshot survive exactly as supplied (directive 5 frame —
   `snap` is read-only, not `mut`; the result is built freshly from it). The
   three guarantees together pin the behavior: the persisted resolution is the
   reference value when present and the current value otherwise, and every other
   part of the snapshot is preserved. -/
method finalizeSnapshot (snap : SurfaceSnapshot) return (out : SurfaceSnapshot)
  ensures out.resolution = snap.baseline.getD snap.resolution
  ensures out.baseline = snap.baseline
  ensures out.payload = snap.payload
  do
    -- impl-start
    return { snap with resolution := snap.baseline.getD snap.resolution }
    -- impl-end

prove_correct finalizeSnapshot by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) — matplotlib__matplotlib-23476 / velvet. VERDICT: SOUND.

### Controls
- pos_control.lean = bundle Solution.lean, confirmed byte-identical (`cmp` -> IDENTICAL). `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0 (VERIFIES). Positive control good; it is a distinct file from every attack.
- atk_prepatch.lean (`return snap`, the pre-patch behaviour): lean_verify -> exit 1, unsolved goal «ensures_3: out.resolution = snap.baseline.getD snap.resolution» / `snap.resolution = snap.baseline.getD snap.resolution`. PREPATCH BUG REPRODUCED, failing exactly on the resolution clause (i.e. exactly when baseline = some _).
- SAME-SPEC: all 20 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec with the velvet backend (only the impl region was edited; axioms/pure/pre/post byte-identical).

=== ATTACKS (19 distinct wrong impls + 1 echo; command for each: `bash scripts/lean_verify.sh atk_N.lean`) ===
PRIOR-PASS COUNTEREXAMPLE RE-ENCODED (nontermination vacuity), all three forms:
- atk_1  uncond. divergence `while 0 <= x` + CORRECT return -> exit 1: 'Decreasing annotations are required in total correctness semantics'. REJECTED.
- atk_2  uncond. divergence + WRONG return (+999.0) — the prior pass's decisive vacuity witness -> exit 1, same error. REJECTED.
- atk_3  conditional divergence ONLY on baseline=some _ (the F2P branch), correct on none -> exit 1, same error. REJECTED.
PARTIAL-DOMAIN / BOUNDARY:
- atk_4  keep working value on BOTH branches (prepatch restricted to the some-branch) -> exit 1, unsolved «ensures_3» with hypothesis `snap.baseline = some i`. REJECTED.
- atk_17 wrong default on the absent branch (`getD 0.0`) -> exit 1, unsolved «ensures_3»: `snap.baseline.getD 0.0 = snap.baseline.getD snap.resolution`. REJECTED.
- atk_16 partial function / panic (`Option.get!`; faithful form is the bare `state['_original_dpi']` subscript -> KeyError) -> exit 1, unsolved «ensures_3». REJECTED.
FRAME / CONTROL-FLOW-EFFECT:
- atk_5  drops the opaque payload (`payload := []`) -> exit 1, unsolved «ensures_1: out.payload = snap.payload». REJECTED (frame is pinned).
- atk_6  erases the recorded reference value (`baseline := none`) -> exit 1, unsolved «ensures_2: out.baseline = snap.baseline». REJECTED (frame is pinned).
- atk_8  unbounded self-recursion then wrong value (the nagini-family guarded-self-call hole) -> exit 1, 'fail to show termination for finalizeSnapshot'. REJECTED.
### Ungrounded-oracle echo
- atk_15 hardcode the very value the F2P test asserts (`resolution := 42.0`) -> exit 1, unsolved «ensures_3»: `42.0 = snap.baseline.getD snap.resolution`. REJECTED. (Had this verified it would have been decisive: `state['_dpi'] = 42.0` passes the F2P test while destroying dpi for every other figure.)
- atk_7  demonic pick of an arbitrary resolution (`let r :| True`) -> exit 1, unsolved «choice_1» AND «ensures_3»: `i = snap.baseline.getD snap.resolution`. REJECTED — choice did not leak angelic.
SPEC-GADGET / VACUITY PROBES:
- atk_9 / atk_13  `assert False` / `assert (1 = 0)` — assertGadget's wp is literally `pure` (Loom/MonadAlgebras/WP/Gen.lean:80), so an unsatisfiable assertion cannot poison the VC context -> exit 1, 'Failed to parse an assertion'. REJECTED.
- atk_10 infeasible pick `let r :| False` -> exit 1, `Findable` synthesis failure. REJECTED.
- atk_19 diverging loop WITH a bogus `decreasing (0 - x)` measure over Nat truncated subtraction -> exit 1, live goal «decreasing_1»: `0 - (x + 1) < 0 - x`. REJECTED — proves the measure obligation is really discharged, so the total-correctness repair is load-bearing and not cosmetic.
I-LEG (Float <-> IEEE-754 double, mapping.md §2) — the deepest remaining trust point:
- atk_11 overflow round-trip `x * 1e308 / 1e308` (algebraically identity; in IEEE 42.0*1e308 -> +inf, inf/1e308 -> inf) -> exit 1, unsolved «ensures_3». REJECTED.
- atk_12 cancellation `x + 1e17 - 1e17` (algebraically identity; in IEEE 42.0 -> 48.0, verified in Python) -> exit 1, unsolved «ensures_3». REJECTED.
- atk_18 NaN reflexivity `if x == x then ... else 0.0` -> exit 1, unsolved «ensures_3» WITH the live hypothesis `if_neg : ¬(snap.resolution == snap.resolution) = true`. REJECTED, and notably Lean does NOT prove Float BEq reflexive — it keeps the NaN case open, i.e. the Float carrier is opaque (no ordered-field axioms to exploit) and faithfully models IEEE NaN. This is the strongest single piece of evidence that the R/I value-selection leg is sound.
### CORRECT ECHO (resolve discriminating-power control):
- atk_14 explicit `match` on baseline instead of `Option.getD` — behaviourally equal to gold, structurally different -> exit 0 VERIFIES. Per protocol I materialized its faithful refined patch (patch_atk_14.diff, transliterating the match to an if/else on `'_original_dpi' in state`) and RAN it through the official harness.

### RESOLVE RUN (mandatory for EVERY verifying attack)
Command: `python3 resolve_one.py atk_14`, calling swebench_unified.harness.run_resolve('matplotlib__matplotlib-23476', patch, timeout=1800, retries=0).
OBSERVED RESULT: {"attack": "atk_14", "resolved": true, "completed": true, "note": "resolved"} (saved at .../resolve_atk_14.json).
atk_14 is therefore a CORRECT ECHO of the gold, not a spec weakness — per docs/architecture.md §6 a candidate whose patch DOES resolve must not fail the gate. It was the ONLY verifying attack, so no verifying wrong impl exists to resolve-check, and there is no BROKEN finding. This run also establishes discriminating power for my oracle invocation: completed=True with a real report, unlike the prior pass whose three resolve runs all hung to the wall clock and produced completed=False (which is what made that pass INCONCLUSIVE rather than BROKEN).

### REFINEMENT.MD / MAPPING.MD AUDIT (A-legs, per assignment focus)
Leg kinds: A1 = R, A2 = I, A3 = I, A4 = R + I. Every leg is R or I; there is NO kind-3 (inexpressible-changed-op) leg, and §B states this explicitly and correctly — the one operation that genuinely changed (which dpi value the serialized state carries) is a concrete dict-lookup selection modeled directly as `Option.getD`, not hidden behind an axiom. A-LEGS: there are NONE, and I verified this mechanically rather than taking the doc's word: the axioms region of Solution.lean contains only comment lines (no `axiom` declaration), the pre-conditions and post-conditions regions are empty, and meta.json records axioms=[] and deep_model_references=[] with G-AX status=skip ('no axiom_check.py (no axioms in bundle)').

So there is no axiom-soundness trust point and no deep-model reference whose correspondence to a real callee could drift — consistent with mapping.md §3 ('None. ... invokes no repository or stdlib routine whose behaviour must be axiomatized'). The added gold line `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` genuinely performs only a dict read and a dict write over values already in `state`, so the claimed absence of callees is accurate.

MODEL<->PATCH CORRESPONDENCE: `dict.get(k, d)` <-> `Option.getD d` (some <-> key present, none <-> absent) is exact; key-assignment <-> record field update is exact; `state['_dpi']` is always present after `super().__getstate__()`, so the `dict.get` default operand is always well-defined and the `none` branch of the Lean model is reachable exactly when `_original_dpi` was never set by the canvas. The frame clauses pin 'nothing else changed', and atk_5/atk_6 confirm mechanically that both frame clauses bite. The Float carrier is opaque (atk_11/atk_12/atk_18), so the only I-leg with any semantic content — value selection, no arithmetic — cannot drift from IEEE-754 behaviour.

ONE DOC NOTE (not a defect, no gate impact): refinement.md §C's sentence 'any impl verifying against this frozen spec, refined per the map below, is behaviourally equal to the gold patch on the tested inputs, so it resolves' is now TRUE for the frozen artifact, but it is true only because the spec carries the total-correctness obligation. §C does not mention termination anywhere, so the argument as written omits the very hypothesis that makes it sound (and was false for the earlier partial-correctness version of this bundle, per the recorded G-EQ fail). Worth one clarifying clause in §C; it does not change any leg's kind or any verdict.

### Parallelism
Attack verifications were launched as concurrent background Bash jobs, <=4 at a time: batch1 = pos_control, atk_prepatch, atk_1, atk_2; batch2 = atk_3..atk_6; batch3 = atk_7..atk_10; batch4 = atk_11..atk_14; batch5 = atk_15..atk_17; batch6 = atk_18, atk_19. The atk_14 resolve run was launched as a detached background job and collected on completion. Schedule only — every attack was fully verified and the one needed resolve run fully executed and reported.

### Verdict
SOUND. 19 distinct same-spec wrong impls (spanning nontermination vacuity in all three prior-pass forms, partial-domain, boundary, frame, control-flow-effect, self-recursion, ungrounded-oracle echo, spec-gadget vacuity, infeasible choice, bogus measure, and three Float/IEEE I-leg attacks) were re-encoded and verified; ALL 19 were rejected by the verifier, each on the on-point postcondition or termination obligation. The prepatch bug reproduces, the byte-identical positive control verifies, and the single verifying same-spec impl is a correct echo whose faithful patch RESOLVED under the official harness (completed=True). No verifying wrong impl exists whose faithful refined patch fails to resolve, so no verify=>correct break was found; the prior pass's nontermination counterexample is genuinely repaired by the total-correctness semantics rather than merely masked.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-derived; did not inherit the prior verdict.md Role-3 label.

### Mechanical preliminaries
- Spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; spec_signature sha256 prefix bd44f533341edd2f on BOTH files. The only delta is inside impl-start/impl-end and the prove_correct body, i.e. inside the admissible variant scope.
- Solution.lean verifies: scripts/lean_verify.sh exit 0.
- patch.diff applies clean at base_commit 33a0599711d26dc2b79f851c6daed4947df7c167; it is the gold hunk verbatim (2 added lines at figure.py:3026).
- Bundle's own conformance_check.py re-run: exit 0, 100010 inputs, 0 disagreements.

### THE MODELED STEP vs THE REAL CODE
Real step (gold): state["_dpi"] = state.get('_original_dpi', state['_dpi'])
Spec: out.resolution = snap.baseline.getD snap.resolution; out.baseline = snap.baseline; out.payload = snap.payload
dict.get(k, d) IS Option.getD under the mapping.md §2 bijection (some v <=> key present; none <=> absent). No arithmetic is performed on the dpi at this step -- only a selection between two values already in the dict -- so the Float carrier only has to preserve selection, not arithmetic.

### ATTACKS RUN TO FIND A DIVERGING INPUT (all failed to find one)
1. Differential fuzz, 200000 inputs, independent of the bundle's harness and its pinned seed: spec model vs the verbatim gold line over state dicts, with bitwise (struct.pack '>d') float comparison so NaN, +/-0.0, subnormals (5e-324, 1e-320), +/-inf, DBL_MAX, and int/bool dpi values are all distinguished rather than collapsed by ==. Also injected the adjacent-looking key '_original_dpi_backup' to try to make the payload frame clause false. Result: 0 disagreements.
2. Live repo anchor at the real step boundary: built a real Figure(dpi=42), raised the canvas device pixel ratio (ratio in {1,2,7}), assembled state exactly as __getstate__ does up to the added line, then applied the gold line. All three ensures hold, checked with bitwise float compare and object-IDENTITY comparison for every payload entry (not just ==, so a silently substituted equal-but-new object would have been caught). ratio=7 gives live _dpi=294, persisted _dpi=42 = _original_dpi -- the exact F2P scenario (test_unpickle_with_device_pixel_ratio).
3. Spec-too-strong probe on the frame / aliasing: confirmed the real hook does NOT mutate the live figure (fig.__dict__['_dpi'] stays 294 across the call) and that state is a distinct object from fig.__dict__. So modeling snap as read-only (not mut) and rebuilding out freshly is not stronger than reality.
4. NaN / Float-equality hazard, the most likely way this spec could be too strong. Wrote and verified a probe Lean file (identical spec region shape, ensures out.resolution = snap.resolution, impl `return snap`): it verifies (exit 0), proving `=` on Float in an ensures clause is propositional Eq and is reflexive on NaN, NOT fp.eq. Therefore the reflexive/preservation clauses cannot become unsatisfiable on a NaN dpi. Cross-checked the real side: Figure(dpi=nan) keeps _dpi IS _original_dpi (same object), so the real selection also agrees.
5. Int-carrier width probe: real dpi can be a Python int (Figure(dpi=42) stores int 42, and ratio*_original_dpi can stay int). float(2**53+1) collapses to 2**53, so the Float carrier is lossy on huge ints -- but this is NOT a divergence, because the step only SELECTS a slot; both sides return the same slot's value, and dpi is never compared or arithmetically combined on the added line. Verified explicitly: with {_dpi: 2**53+1, _original_dpi: 2**53} both sides persist 2**53.
6. Reachability of both branches: _original_dpi is set by FigureCanvasBase.__init__ (backend_bases.py:1656), and Figure.__init__ installs a canvas, so `some` is the common case; the `none` branch is defensive but harmless -- and crucially the spec handles it the same way the real dict.get default does. Grepped all of lib/ for _original_dpi (3 sites) to confirm no other writer changes the semantics.

### SCOPE NOTE (disclosed, not scored as a defect, no diverging input)
meta.json modeled_functions names repo_symbol "matplotlib.figure.Figure.__getstate__" while repo_location and carrier_type scope it to the added line (figure.py:3026), and mapping.md §1 says snap is "the in-progress state dict". Under the scoped reading the frame clause out.payload = snap.payload is exactly true. Under a naive WHOLE-function reading it would be false -- the full __getstate__ pops 'canvas', adds '__mpl_version__', and may add '_restore_to_pylab' (I measured this: keys added ['__mpl_version__'], removed ['canvas']). That is an artifact of the repo_symbol label being the enclosing method rather than the step; the two other bundle docs and the carrier_type disambiguate it, so it yields no input on which the modeled function disagrees with the step it declares to model. Flagging it as a wording tightening for the bundle author, not a faithfulness break.

G-DIFF sanity: Solution_prepatch.lean (`return snap`) fails against this frozen spec, and it fails precisely on baseline = some v with v != resolution -- so the spec's discriminating clause really is the one the gold patch changed; the spec is not vacuous and not satisfied by pre-patch behavior.

CONCLUSION: no input found on which finalizeSnapshot disagrees with the real gold step under the mapping.md bijection. The spec is neither too strong (probes 3, 4, 5) nor drifted (probes 1, 2, 6). FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: leakage / gold-reconstruction on the consumer spec view only. Verdict reached independently; I did not defer to the retained gates.G-PANEL-3='pass' label in meta.json.

GOLD EDIT (what must not be reconstructible): lib/matplotlib/figure.py, Figure.__getstate__, added line `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` plus the comment `# discard any changes to the dpi due to pixel ratio changes`.

1. SPEC REGION IDENTITY (required check): markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True. Stronger than required: markers.spec_view() output is BYTE-identical between the two files, and spec_view is idempotent. The prepatch's bug narration ('Pre-patch skeleton...', 'MUST fail') lives entirely inside the impl region and is correctly collapsed to '-- implementation elided'. Confirmed Solution.lean is live: lean_verify.sh exit 0.

2. MECHANICAL SCREEN: leakage.screen(Solution.lean, velvet.language, gold_patch, problem_statement, test_patch) => passed=True, hard_failures=[], warnings=[]. Ran with the real frozen row from data/swe_bench_verified/test.jsonl.

3. MANUAL SWEEP (the mechanical screen only derives symbols from def/class regexes, so bare ATTRIBUTE names like `_original_dpi` would slip past it — I checked these by hand). Absent from the spec view: `_original_dpi`, `original_dpi`, `original`, `_dpi`, `dpi`, `__getstate__`, `getstate`, `setstate`, `figure`, `figure.py`, `pickle`, `unpickl`, `canvas`, `matplotlib`, `pixel`, `ratio`, `device`, `renderer`, `_cachedRenderer`, `__mpl_version__`, `discard`, `doubl`. Only substring hits were benign ('dots-per-inch', 'serialized-state', and 'mpl' inside 'impl-start').

4. HINTS-ONLY TERMS (the pilot lesson — judged against problem_statement, NEVER hints_text): hints_text here says 'high-dpi', 'doubling the dpi', 'saving the doubled dpi', 'doubled again', 'easy fix'. NONE of these appear in the spec view. Also confirmed build_task(mode 1) does not ship hints_text (include_hints defaults False).

5. HIDDEN-TEST TERMS: `test_unpickle_with_device_pixel_ratio`, `_set_device_pixel_ratio`, `device_pixel_ratio`, the literals 42 and 7, `test_figure` — all absent.

6. IDENTIFIER SET is fully abstracted, no repo-symbol echo: SurfaceSnapshot, finalizeSnapshot, resolution, baseline, payload, snap, out. The gold's dpi/_original_dpi selection is re-expressed as `snap.baseline.getD snap.resolution` — an abstract Option carrier, not the dict-get form.

7. GOLD-LINE REPRODUCTION: neither changed gold line (nor any >=8-char normalized fragment) appears in the normalized spec view; no diff markers.

TWO ITEMS DELIBERATELY RULED NOT-LEAKAGE, recorded for transparency:

(a) The spec view's pure-region docstring ends '...the bijection to the real serialized-state mapping is in mapping.md §2.' mapping.md DOES contain the gold line verbatim and the full bug diagnosis. But I confirmed mapping.md is never shipped to the consumer: eval/dataset.as_dict ships only {instance_id, repo, base_commit, mode, backend, problem_statement, localization, changed_files, spec_view, modeled_functions}, and eval/audit.py explicitly classes a read of `/mapping.md` as 'our-bundle-access' private-bundle exfiltration. So the pointer is a DANGLING reference from the consumer's position, disclosing nothing. Minor hygiene nit only (a consumer-facing docstring should not cite an author-private file), not a leak, and not a gate fail.

(b) The rendered mode-1 prompt does contain `matplotlib.figure.Figure.__getstate__` and `lib/matplotlib/figure.py` — but these come from the SEPARATE 'Modeled function(s):' localization block that eval/prompts._spec_block renders from meta.json, i.e. the same edit-localization every localization mode grants by design. They are NOT spec-view content (verified: the string inside the ```lean fence is byte-equal to markers.spec_view output, which contains neither). Out of scope for this gate; flagging only so it is not mistaken for a spec-view defect. (`figure.py` and `__setstate__` are in the public problem_statement's traceback anyway.)

RESIDUAL JUDGMENT: the spec view does convey the fix's LOGIC ('persist the reference value when one is available, else the current value'). That is inherent to spec-aided modes 1/2 (the spec IS the deliverable), not leakage — directive 6 bans quoting the edit, naming the patched file/symbol, and narrating the bug->fix mechanism, all of which are clean here. The de-narration is exactly the intended M1 pattern: an abstract 'optional recorded reference resolution' in place of the callee/attribute name `_original_dpi`. A solver reading only the spec view still has to locate the site and discover the real `_original_dpi` attribute itself. No G-LEAK relaxation is needed or claimed (meta gates.G-LEAK.status is 'pass', not 'relaxed').

GOLD EDIT (what must not be reconstructible): lib/matplotlib/figure.py, Figure.__getstate__, added line `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` plus the comment `# discard any changes to the dpi due to pixel ratio changes`.

1. SPEC REGION IDENTITY (required check): markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True. Stronger than required: markers.spec_view() output is BYTE-identical between the two files, and spec_view is idempotent. The prepatch's bug narration ('Pre-patch skeleton...', 'MUST fail') lives entirely inside the impl region and is correctly collapsed to '-- implementation elided'. Confirmed Solution.lean is live: lean_verify.sh exit 0.

2. MECHANICAL SCREEN: leakage.screen(Solution.lean, velvet.language, gold_patch, problem_statement, test_patch) => passed=True, hard_failures=[], warnings=[]. Ran with the real frozen row from data/swe_bench_verified/test.jsonl.

3. MANUAL SWEEP (the mechanical screen only derives symbols from def/class regexes, so bare ATTRIBUTE names like `_original_dpi` would slip past it — I checked these by hand). Absent from the spec view: `_original_dpi`, `original_dpi`, `original`, `_dpi`, `dpi`, `__getstate__`, `getstate`, `setstate`, `figure`, `figure.py`, `pickle`, `unpickl`, `canvas`, `matplotlib`, `pixel`, `ratio`, `device`, `renderer`, `_cachedRenderer`, `__mpl_version__`, `discard`, `doubl`. Only substring hits were benign ('dots-per-inch', 'serialized-state', and 'mpl' inside 'impl-start').

4. HINTS-ONLY TERMS (the pilot lesson — judged against problem_statement, NEVER hints_text): hints_text here says 'high-dpi', 'doubling the dpi', 'saving the doubled dpi', 'doubled again', 'easy fix'. NONE of these appear in the spec view. Also confirmed build_task(mode 1) does not ship hints_text (include_hints defaults False).

5. HIDDEN-TEST TERMS: `test_unpickle_with_device_pixel_ratio`, `_set_device_pixel_ratio`, `device_pixel_ratio`, the literals 42 and 7, `test_figure` — all absent.

6. IDENTIFIER SET is fully abstracted, no repo-symbol echo: SurfaceSnapshot, finalizeSnapshot, resolution, baseline, payload, snap, out. The gold's dpi/_original_dpi selection is re-expressed as `snap.baseline.getD snap.resolution` — an abstract Option carrier, not the dict-get form.

7. GOLD-LINE REPRODUCTION: neither changed gold line (nor any >=8-char normalized fragment) appears in the normalized spec view; no diff markers.

TWO ITEMS DELIBERATELY RULED NOT-LEAKAGE, recorded for transparency:

(a) The spec view's pure-region docstring ends '...the bijection to the real serialized-state mapping is in mapping.md §2.' mapping.md DOES contain the gold line verbatim and the full bug diagnosis. But I confirmed mapping.md is never shipped to the consumer: eval/dataset.as_dict ships only {instance_id, repo, base_commit, mode, backend, problem_statement, localization, changed_files, spec_view, modeled_functions}, and eval/audit.py explicitly classes a read of `/mapping.md` as 'our-bundle-access' private-bundle exfiltration. So the pointer is a DANGLING reference from the consumer's position, disclosing nothing. Minor hygiene nit only (a consumer-facing docstring should not cite an author-private file), not a leak, and not a gate fail.

(b) The rendered mode-1 prompt does contain `matplotlib.figure.Figure.__getstate__` and `lib/matplotlib/figure.py` — but these come from the SEPARATE 'Modeled function(s):' localization block that eval/prompts._spec_block renders from meta.json, i.e. the same edit-localization every localization mode grants by design. They are NOT spec-view content (verified: the string inside the ```lean fence is byte-equal to markers.spec_view output, which contains neither). Out of scope for this gate; flagging only so it is not mistaken for a spec-view defect. (`figure.py` and `__setstate__` are in the public problem_statement's traceback anyway.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
