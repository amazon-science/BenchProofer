# P2 adversarial audit — matplotlib__matplotlib-23476

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,6 @@
 def implementation_serializedFigureDpi
     (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
   let mut value := currentDpi
-  match baselineDpi with
-  | some d => value := d
-  | none   => pure ()
   return value
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
     (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
   let mut value := currentDpi
   match baselineDpi with
-  | some d => value := d
+  | some d => value := d + 1
   | none   => pure ()
   return value
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
     (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
   let mut value := currentDpi
   match baselineDpi with
-  | some d => value := d
+  | some d => value := if d = 0 then currentDpi else d
   | none   => pure ()
   return value
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
   let mut value := currentDpi
   match baselineDpi with
   | some d => value := d
-  | none   => pure ()
+  | none   => value := 0
   return value
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,8 @@
 
 -- impl-start
 def implementation_serializedFigureDpi
-    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
-  let mut value := currentDpi
-  match baselineDpi with
-  | some d => value := d
-  | none   => pure ()
-  return value
+    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat :=
+  baselineDpi.getD 0
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
     (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
   let mut value := currentDpi
   match baselineDpi with
-  | some d => value := d
+  | some _ => value := currentDpi
   | none   => pure ()
   return value
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
     (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
   let mut value := currentDpi
   match baselineDpi with
-  | some d => value := d
+  | some d => value := -d
   | none   => pure ()
   return value
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing which resolution value to record when a figure's drawing state is
serialized for later restoration.

A figure has a current working resolution (dots per inch). On some display
surfaces this working resolution is temporarily rescaled to match the surface's
pixel density; when that happens the figure also keeps a record of its baseline
resolution — the resolution it had before any such rescaling. A figure that has
never been rescaled carries no such baseline record.

When the figure's state is captured for serialization, the resolution value
written into that state should be the figure that will be reconstructed from it.
The desired rule is:

  * if the figure carries a recorded baseline resolution, the serialized state
    records that baseline value;
  * otherwise (no baseline was ever recorded) the serialized state records the
    figure's current working resolution.

This keeps the resolution that round-trips through serialization equal to the
baseline whenever one is known, independent of any display-surface rescaling in
effect at the moment of capture.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The current
-- working resolution and the optional recorded baseline resolution both enter
-- as plain data (the baseline modeled as `Option`), and the only operation is
-- the baseline-or-current selection, modeled directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The recorded resolution value is fully pinned to the inputs:

  * if a baseline resolution `d` is recorded, the result is exactly `d`
    (the baseline is recorded, whatever the current working resolution is);
  * if no baseline is recorded, the result is exactly the current working
    resolution.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_serializedFigureDpi
    (currentDpi : Rat) (baselineDpi : Option Rat) (result : Rat) : Prop :=
  (∀ d, baselineDpi = some d → result = d) ∧
  (baselineDpi = none → result = currentDpi)
-- post-conditions-end

-- impl-start
def implementation_serializedFigureDpi
    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
  let mut value := currentDpi
  match baselineDpi with
  | some d => value := d
  | none   => pure ()
  return value
-- impl-end

-- proof-start
theorem correct_serializedFigureDpi :
    ∀ (currentDpi : Rat) (baselineDpi : Option Rat),
      problem_spec_serializedFigureDpi currentDpi baselineDpi
        (implementation_serializedFigureDpi currentDpi baselineDpi) := by
  intro currentDpi baselineDpi
  unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi
  cases baselineDpi with
  | none =>
    refine ⟨?_, ?_⟩
    · intro d h; exact absurd h (by simp)
    · intro _; rfl
  | some d =>
    refine ⟨?_, ?_⟩
    · intro d' h; simp only [Option.some.injEq] at h; subst h; rfl
    · intro h; exact absurd h (by simp)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_serializedFigureDpi(currentDpi, baselineDpi, result) := (∀ d, baselineDpi = some d → result = d) ∧ (baselineDpi = none → result = currentDpi). This TOTALLY and EXACTLY pins result in both branches (some d → exactly d; none → exactly currentDpi), so any extensionally-different impl cannot close correct_. Verified via python + swebench_unified.markers.same_spec: all 8 files (7 attacks + pos) return same_spec=True (impl region only edited; axioms/pure/pre/post byte-identical).

Attacks (all same_spec=True), verified with `bash scripts/lean_verify.sh <f>`, run concurrently ≤4 at a time:
- atk_1 (prepatch bug: always currentDpi, ignores baseline) → exit 1 (rfl failed at line 77 — the some-branch subgoal result=d becomes currentDpi=d, unprovable). REPRODUCES PREPATCH BUG (matches Solution_prepatch.lean impl).
- atk_2 (off-by: some d → d+1) → exit 1.
- atk_3 (boundary: some 0 → currentDpi) → exit 1.
- atk_4 (control-flow-effect: none → 0 instead of currentDpi) → exit 1.
- atk_5 (ungrounded oracle echo: baselineDpi.getD 0, none → 0) → exit 1 (rfl failed line 73).
- atk_6 (swapped: some _ → currentDpi, discards baseline) → exit 1.
- atk_7 (negate baseline: some d → -d) → exit 1.
All 7 fail with genuine `Tactic rfl failed` proof errors (not sorry, not timeout) because the fixed correct_ theorem no longer matches the spec-pinned result.

Positive control atk_pos (byte-identical to bundle Solution.lean impl) → exit 0, verifies clean. #print axioms correct_serializedFigureDpi → depends on axioms: [propext] only (no sorryAx, no custom axioms) — clean.

Since NO wrong impl produced a closing clean-axiom proof, there is no candidate to materialize/resolve; protocol step 2 (materialize+run_resolve faithful patches) is vacuously satisfied — patches={}. verify⇒correct holds for all exhibited candidates.

A-leg / refinement.md audit: refinement.md declares all 3 legs R/I (no A row): leg1 R (currentDpi ↔ state['_dpi'] fallback default), leg2 R (baselineDpi:Option Rat ↔ state.get('_original_dpi',…): some↔key present, none↔absent), leg3 I (return value ↔ state['_dpi']=… assignment). No kind-3 leg. Consistent with meta.json axioms=[] and deep_model_references=[] (verified), and axiom_check.py is a skip stub — no axiom/deep-model correspondence exists to falsify. G-CONF (R/I) mechanically differential-tests the shadow vs real patched Figure.__getstate__ per conformance_check.py (seed 23476, 1e5 inputs); shadow matches Lean impl op-for-op.

Verdict SOUND: ≥5 distinct wrong impls (7 total, all same_spec) attempted; none closes; positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing which resolution value to record when a figure's drawing state is
serialized for later restoration.

A figure has a current working resolution (dots per inch). On some display
surfaces this working resolution is temporarily rescaled to match the surface's
pixel density; when that happens the figure also keeps a record of its baseline
resolution — the resolution it had before any such rescaling. A figure that has
never been rescaled carries no such baseline record.

When the figure's state is captured for serialization, the resolution value
written into that state should be the figure that will be reconstructed from it.
The desired rule is:

  * if the figure carries a recorded baseline resolution, the serialized state
    records that baseline value;
  * otherwise (no baseline was ever recorded) the serialized state records the
    figure's current working resolution.

This keeps the resolution that round-trips through serialization equal to the
baseline whenever one is known, independent of any display-surface rescaling in
effect at the moment of capture.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The current
-- working resolution and the optional recorded baseline resolution both enter
-- as plain data (the baseline modeled as `Option`), and the only operation is
-- the baseline-or-current selection, modeled directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The recorded resolution value is fully pinned to the inputs:

  * if a baseline resolution `d` is recorded, the result is exactly `d`
    (the baseline is recorded, whatever the current working resolution is);
  * if no baseline is recorded, the result is exactly the current working
    resolution.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_serializedFigureDpi
    (currentDpi : Rat) (baselineDpi : Option Rat) (result : Rat) : Prop :=
  (∀ d, baselineDpi = some d → result = d) ∧
  (baselineDpi = none → result = currentDpi)
-- post-conditions-end

-- impl-start
def implementation_serializedFigureDpi
    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
  let mut value := currentDpi
  match baselineDpi with
  | some d => value := d
  | none   => pure ()
  return value
-- impl-end

-- proof-start
theorem correct_serializedFigureDpi :
    ∀ (currentDpi : Rat) (baselineDpi : Option Rat),
      problem_spec_serializedFigureDpi currentDpi baselineDpi
        (implementation_serializedFigureDpi currentDpi baselineDpi) := by
  intro currentDpi baselineDpi
  unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi
  cases baselineDpi with
  | none =>
    refine ⟨?_, ?_⟩
    · intro d h; exact absurd h (by simp)
    · intro _; rfl
  | some d =>
    refine ⟨?_, ?_⟩
    · intro d' h; simp only [Option.some.injEq] at h; subst h; rfl
    · intro h; exact absurd h (by simp)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_serializedFigureDpi(currentDpi, baselineDpi, result) := (∀ d, baselineDpi = some d → result = d) ∧ (baselineDpi = none → result = currentDpi). This TOTALLY and EXACTLY pins result in both branches (some d → exactly d; none → exactly currentDpi), so any extensionally-different impl cannot close correct_. Verified via python + swebench_unified.markers.same_spec: all 8 files (7 attacks + pos) return same_spec=True (impl region only edited; axioms/pure/pre/post byte-identical).

Attacks (all same_spec=True), verified with `bash scripts/lean_verify.sh <f>`, run concurrently ≤4 at a time:
- atk_1 (prepatch bug: always currentDpi, ignores baseline) → exit 1 (rfl failed at line 77 — the some-branch subgoal result=d becomes currentDpi=d, unprovable). REPRODUCES PREPATCH BUG (matches Solution_prepatch.lean impl).
- atk_2 (off-by: some d → d+1) → exit 1.
- atk_3 (boundary: some 0 → currentDpi) → exit 1.
- atk_4 (control-flow-effect: none → 0 instead of currentDpi) → exit 1.
- atk_5 (ungrounded oracle echo: baselineDpi.getD 0, none → 0) → exit 1 (rfl failed line 73).
- atk_6 (swapped: some _ → currentDpi, discards baseline) → exit 1.
- atk_7 (negate baseline: some d → -d) → exit 1.
All 7 fail with genuine `Tactic rfl failed` proof errors (not sorry, not timeout) because the fixed correct_ theorem no longer matches the spec-pinned result.

Positive control atk_pos (byte-identical to bundle Solution.lean impl) → exit 0, verifies clean. #print axioms correct_serializedFigureDpi → depends on axioms: [propext] only (no sorryAx, no custom axioms) — clean.

Since NO wrong impl produced a closing clean-axiom proof, there is no candidate to materialize/resolve; protocol step 2 (materialize+run_resolve faithful patches) is vacuously satisfied — patches={}. verify⇒correct holds for all exhibited candidates.

A-leg / refinement.md audit: refinement.md declares all 3 legs R/I (no A row): leg1 R (currentDpi ↔ state['_dpi'] fallback default), leg2 R (baselineDpi:Option Rat ↔ state.get('_original_dpi',…): some↔key present, none↔absent), leg3 I (return value ↔ state['_dpi']=… assignment). No kind-3 leg. Consistent with meta.json axioms=[] and deep_model_references=[] (verified), and axiom_check.py is a skip stub — no axiom/deep-model correspondence exists to falsify. G-CONF (R/I) mechanically differential-tests the shadow vs real patched Figure.__getstate__ per conformance_check.py (seed 23476, 1e5 inputs); shadow matches Lean impl op-for-op.

Verdict SOUND: ≥5 distinct wrong impls (7 total, all same_spec) attempted; none closes; positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Real callee is `state['_dpi'] = state.get('_original_dpi', state['_dpi'])` in Figure.__getstate__ (figure.py:3118, patched) — a pure baseline-or-current selection with no arithmetic. Model `problem_spec_serializedFigureDpi`: (some d → result=d) ∧ (none → result=currentDpi) matches the real op case-for-case. Verified: (1) Solution.lean compiles via lean_verify.sh (exit 0, no sorry); (2) `#print axioms correct_serializedFigureDpi` = [propext] only — no sorryAx, proof genuine; (3) same_spec(post, prepatch, lean)=True (spec region byte-identical); (4) differential test of Lean-shadow vs real op over edge inputs {42,294,0,-1,0.5,1e18,inf} × baseline present/absent → 0 divergences; conformance_check.py fuzzes 1e5 tuples against the real patched __getstate__. Option↔dict-presence and Rat↔dpi are exact identity bijections under pure selection. No input where spec disagrees with real repo; spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (leakage.screen: hard_failures=[]) and the spec region is byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec == True). Reviewed the full spec view (docstring + axioms/pure/post-conditions regions; impl and proof are elided in the consumer view). Findings:

1) No gold-patch line reproduced. The gold edit is `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` inside `Figure.__getstate__` (lib/matplotlib/figure.py). None of these tokens appear in the spec view: no `_dpi`, `_original_dpi`, `__getstate__`/`getstate`, `state`, `dict.get`, `figure.py`, or `matplotlib`. The changed symbol the screen extracts is `getstate` (len>=4) and it is absent from all spec-view identifiers and comments.

2) No patched file path or module path in the view.

3) No diff markers, no bug/fix narration words.

4) Semantic check (the part the lexical screen can miss): the spec describes the correct behavior purely abstractly as a baseline-or-current selection over two data items (currentDpi : Rat, baselineDpi : Option Rat), with post-condition `(∀ d, baselineDpi = some d → result = d) ∧ (baselineDpi = none → result = currentDpi)`. It never localizes the edit to the serialization routine's implementation detail, the private attributes, or the `dict.get` idiom. The behavioral content (dpi must round-trip to a baseline instead of growing across pickle cycles under high-dpi/pixel-ratio rescaling) is already fully public in problem_statement: the bug report shows dpi doubling every unpickle on M1 due to high-dpi handling, and the Expected-outcome block shows dpi held constant at 200. A verification spec must state the correct behavior it checks; here that statement adds no edit-localizing information beyond the public problem_statement. hints_text was not relied upon.

Conclusion: the spec view does not leak the gold edit beyond problem_statement. No RELAXED_LEAKAGE.md present and none needed (relaxed_leakage flag unset).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
