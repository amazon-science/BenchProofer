# P2 adversarial audit — pydata__xarray-6744

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
xs=[1,2,3], window=3, center=true: spec (centered) position 0 = [1,2], right-anchored prepatch impl position 0 = [1]. This discriminator refutes every non-centered/altered impl (atk_1..atk_5) — none closes the exact-equality theorem.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     (xs : List Int) (window : Nat) (center : Bool) :
     List (List Int) := Id.run do
   let n := xs.length
-  let offset := if center then (window + 1) / 2 else 1
+  let offset := 1
   let mut out : Array (List Int) := #[]
   for i in [0:n] do
     let stop := offset + i
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
   let offset := if center then (window + 1) / 2 else 1
   let mut out : Array (List Int) := #[]
   for i in [0:n] do
-    let stop := offset + i
+    let stop := offset + i + 1
     let start := if i + offset < window then 0 else stop - window
     out := out.push ((xs.drop start).take (stop - start))
   return out.toList
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     (xs : List Int) (window : Nat) (center : Bool) :
     List (List Int) := Id.run do
   let n := xs.length
-  let offset := if center then (window + 1) / 2 else 1
+  let offset := if center then window / 2 else 1
   let mut out : Array (List Int) := #[]
   for i in [0:n] do
     let stop := offset + i
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
   let mut out : Array (List Int) := #[]
   for i in [0:n] do
     let stop := offset + i
-    let start := if i + offset < window then 0 else stop - window
+    let start := if i + offset <= window then 0 else stop - window
     out := out.push ((xs.drop start).take (stop - start))
   return out.toList
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,7 +68,7 @@
     let stop := offset + i
     let start := if i + offset < window then 0 else stop - window
     out := out.push ((xs.drop start).take (stop - start))
-  return out.toList
+  return out.toList.reverse
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,15 +60,8 @@
 -- impl-start
 def implementation_rollingWindows
     (xs : List Int) (window : Nat) (center : Bool) :
-    List (List Int) := Id.run do
-  let n := xs.length
-  let offset := if center then (window + 1) / 2 else 1
-  let mut out : Array (List Int) := #[]
-  for i in [0:n] do
-    let stop := offset + i
-    let start := if i + offset < window then 0 else stop - window
-    out := out.push ((xs.drop start).take (stop - start))
-  return out.toList
+    List (List Int) :=
+  (List.range xs.length).map (windowAt xs window center)
 -- impl-end
 
 -- proof-start
@@ -79,10 +72,5 @@
         (implementation_rollingWindows xs window center) := by
   intro xs window center _
   unfold problem_spec_rollingWindows implementation_rollingWindows
-  simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]
-  norm_num
-  rw [← List.range_eq_range']
-  apply List.map_congr_left
-  intro i _
-  simp only [windowAt, winOffset, winStart]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Manually stepping through the moving windows of a one-dimensional sequence.

A moving-window view of a 1-D sequence of length `n`, with a given window
length `w` and an alignment flag, exposes one sub-window per position. The
exported behavior modeled here is *which contiguous slice of the input each
position sees*:

* When alignment is requested, each window is centered on its position: the
  positions are shifted so that the window straddles the position symmetrically
  (the leading half-window worth of positions are anchored at the start of the
  sequence).
* When alignment is not requested, each window is right-anchored: position `i`
  sees the slice ending just past `i`.

The slice for a position is taken from the input sequence in order, so the
resulting list of windows is fully determined by the input sequence, the window
length, and the alignment flag.
-/

-- axioms-start
-- (none) — the slice extraction is modeled directly as a list operation.
-- axioms-end

-- pure-start
/-- The forward shift applied to the window positions: half of the window
length (rounded up) under centered alignment, otherwise one. -/
def winOffset (window : Nat) (center : Bool) : Nat :=
  if center then (window + 1) / 2 else 1

/-- The start index of the window at position `i`: the right edge `offset + i`
pulled back by the window length, clamped to the start of the sequence for the
leading positions. -/
def winStart (window offset i : Nat) : Nat :=
  if i + offset < window then 0 else (offset + i) - window

/-- The contiguous slice of `xs` seen by the window at position `i`. -/
def windowAt (xs : List Int) (window : Nat) (center : Bool) (i : Nat) : List Int :=
  let offset := winOffset window center
  let stop := offset + i
  let start := winStart window offset i
  (xs.drop start).take (stop - start)
-- pure-end

-- post-conditions-start
/-- The list of moving windows: one entry per position of the input sequence,
in order, each entry the contiguous slice that position sees. Frame: the result
length equals the input length, and every window is a slice of the input taken
from the position dictated by the window length and the alignment flag, so the
whole result is determined by `xs`, `window`, and `center`. -/
def problem_spec_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool)
    (result : List (List Int)) : Prop :=
  result = (List.range xs.length).map (windowAt xs window center)
-- post-conditions-end

-- impl-start
def implementation_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool) :
    List (List Int) := Id.run do
  let n := xs.length
  let offset := if center then (window + 1) / 2 else 1
  let mut out : Array (List Int) := #[]
  for i in [0:n] do
    let stop := offset + i
    let start := if i + offset < window then 0 else stop - window
    out := out.push ((xs.drop start).take (stop - start))
  return out.toList
-- impl-end

-- proof-start
theorem correct_rollingWindows :
    ∀ (xs : List Int) (window : Nat) (center : Bool),
      1 ≤ window →
      problem_spec_rollingWindows xs window center
        (implementation_rollingWindows xs window center) := by
  intro xs window center _
  unfold problem_spec_rollingWindows implementation_rollingWindows
  simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]
  norm_num
  rw [← List.range_eq_range']
  apply List.map_congr_left
  intro i _
  simp only [windowAt, winOffset, winStart]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is an EXACT functional equality: problem_spec_rollingWindows result := result = (List.range xs.length).map (windowAt xs window center), sole precondition 1 <= window. This uniquely pins the whole output list for every input, leaving no free region.

All 7 files pass swebench_unified.markers.same_spec == True (byte-identical axioms/pure/pre/post regions), verified with the lean backend. Refinement has NO axiom/opaque declarations => purely R (ops 1-5) + I (op 6); no A-legs to audit. axiom_check.py is a legitimate skip stub (nothing to validate). mapping/refinement A-leg correspondence: N/A (no A-legs). G-CONF (conformance_check.py) differential-tests the R legs against the patched isel slice arithmetic; fuzz domain matches mapping.md.

Attack verifications (scripts/lean_verify.sh, timeout 300, run concurrently <=4 at a time):
- pos_control (exact gold impl+proof): exit 0. #print axioms correct_rollingWindows => [propext, Classical.choice, Quot.sound] (clean, no sorryAx).
- atk_1 partial/prepatch bug (offset fixed to 1, center ignored -> right-anchored): exit 1. Spec refutes it (this is exactly the prepatch bug the gold fixes). prepatch_reproduced=true.
- atk_2 boundary (stop := offset+i+1, off-by-one window length): exit 1, refuted.
- atk_3 wrong center offset (window/2 instead of (window+1)/2): exit 1, refuted.
- atk_4 clamp boundary off-by-one (i+offset <= window instead of <): exit 1, refuted.
- atk_5 control-flow effect (out.toList.reverse -> wrong position order): exit 1, refuted.
- atk_6 ungrounded oracle echo (impl := (List.range xs.length).map (windowAt xs window center), proof: unfold; rfl): exit 0. #print axioms => 'does not depend on any axioms' (clean). This is the ONLY closing wrong-shaped impl, and it is extensionally identical to gold.

MANDATORY resolve for every clean-closing impl: atk_6 is the only impl closing with clean axioms. Its faithful refined patch is the gold centered-window arithmetic (materialized as atk_6_patch.diff = benchmark patch.diff, since the impl computes exactly the centered slices). run_resolve('pydata__xarray-6744', <atk_6 patch>, timeout=1800) => RESOLVED=True, COMPLETED=True, NOTE='resolved' (bench swe_bench_verified, Docker oracle). So the sole closing impl RESOLVES — no verify-does-not-imply-resolve wedge.

Conclusion: the exact-equality spec admits no closes-but-does-not-resolve counterexample. Every deviating impl (atk_1..atk_5) fails to close; the only impl that closes (atk_6) is extensionally gold and its patch resolves. >=5 distinct attacks run (partial-domain/prepatch, boundary, control-flow-effect, ungrounded-oracle-echo, plus wrong-offset variants), none breaks it. VERDICT: SOUND.

Commands:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." => True for all 7.
- verify: bash scripts/lean_verify.sh <file>
- axioms: appended '#print axioms correct_rollingWindows' to atk_6_ax.lean / pos_control_ax.lean and re-ran lean_verify.sh.
- resolve: SBU_BENCHMARK=swe_bench_verified python -c 'run_resolve(...)'.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
xs=[1,2,3], window=3, center=true: spec (centered) position 0 = [1,2], right-anchored prepatch impl position 0 = [1]. This discriminator refutes every non-centered/altered impl (atk_1..atk_5) — none closes the exact-equality theorem.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Manually stepping through the moving windows of a one-dimensional sequence.

A moving-window view of a 1-D sequence of length `n`, with a given window
length `w` and an alignment flag, exposes one sub-window per position. The
exported behavior modeled here is *which contiguous slice of the input each
position sees*:

* When alignment is requested, each window is centered on its position: the
  positions are shifted so that the window straddles the position symmetrically
  (the leading half-window worth of positions are anchored at the start of the
  sequence).
* When alignment is not requested, each window is right-anchored: position `i`
  sees the slice ending just past `i`.

The slice for a position is taken from the input sequence in order, so the
resulting list of windows is fully determined by the input sequence, the window
length, and the alignment flag.
-/

-- axioms-start
-- (none) — the slice extraction is modeled directly as a list operation.
-- axioms-end

-- pure-start
/-- The forward shift applied to the window positions: half of the window
length (rounded up) under centered alignment, otherwise one. -/
def winOffset (window : Nat) (center : Bool) : Nat :=
  if center then (window + 1) / 2 else 1

/-- The start index of the window at position `i`: the right edge `offset + i`
pulled back by the window length, clamped to the start of the sequence for the
leading positions. -/
def winStart (window offset i : Nat) : Nat :=
  if i + offset < window then 0 else (offset + i) - window

/-- The contiguous slice of `xs` seen by the window at position `i`. -/
def windowAt (xs : List Int) (window : Nat) (center : Bool) (i : Nat) : List Int :=
  let offset := winOffset window center
  let stop := offset + i
  let start := winStart window offset i
  (xs.drop start).take (stop - start)
-- pure-end

-- post-conditions-start
/-- The list of moving windows: one entry per position of the input sequence,
in order, each entry the contiguous slice that position sees. Frame: the result
length equals the input length, and every window is a slice of the input taken
from the position dictated by the window length and the alignment flag, so the
whole result is determined by `xs`, `window`, and `center`. -/
def problem_spec_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool)
    (result : List (List Int)) : Prop :=
  result = (List.range xs.length).map (windowAt xs window center)
-- post-conditions-end

-- impl-start
def implementation_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool) :
    List (List Int) := Id.run do
  let n := xs.length
  let offset := if center then (window + 1) / 2 else 1
  let mut out : Array (List Int) := #[]
  for i in [0:n] do
    let stop := offset + i
    let start := if i + offset < window then 0 else stop - window
    out := out.push ((xs.drop start).take (stop - start))
  return out.toList
-- impl-end

-- proof-start
theorem correct_rollingWindows :
    ∀ (xs : List Int) (window : Nat) (center : Bool),
      1 ≤ window →
      problem_spec_rollingWindows xs window center
        (implementation_rollingWindows xs window center) := by
  intro xs window center _
  unfold problem_spec_rollingWindows implementation_rollingWindows
  simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]
  norm_num
  rw [← List.range_eq_range']
  apply List.map_congr_left
  intro i _
  simp only [windowAt, winOffset, winStart]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is an EXACT functional equality: problem_spec_rollingWindows result := result = (List.range xs.length).map (windowAt xs window center), sole precondition 1 <= window. This uniquely pins the whole output list for every input, leaving no free region.

All 7 files pass swebench_unified.markers.same_spec == True (byte-identical axioms/pure/pre/post regions), verified with the lean backend. Refinement has NO axiom/opaque declarations => purely R (ops 1-5) + I (op 6); no A-legs to audit. axiom_check.py is a legitimate skip stub (nothing to validate). mapping/refinement A-leg correspondence: N/A (no A-legs). G-CONF (conformance_check.py) differential-tests the R legs against the patched isel slice arithmetic; fuzz domain matches mapping.md.

Attack verifications (scripts/lean_verify.sh, timeout 300, run concurrently <=4 at a time):
- pos_control (exact gold impl+proof): exit 0. #print axioms correct_rollingWindows => [propext, Classical.choice, Quot.sound] (clean, no sorryAx).
- atk_1 partial/prepatch bug (offset fixed to 1, center ignored -> right-anchored): exit 1. Spec refutes it (this is exactly the prepatch bug the gold fixes). prepatch_reproduced=true.
- atk_2 boundary (stop := offset+i+1, off-by-one window length): exit 1, refuted.
- atk_3 wrong center offset (window/2 instead of (window+1)/2): exit 1, refuted.
- atk_4 clamp boundary off-by-one (i+offset <= window instead of <): exit 1, refuted.
- atk_5 control-flow effect (out.toList.reverse -> wrong position order): exit 1, refuted.
- atk_6 ungrounded oracle echo (impl := (List.range xs.length).map (windowAt xs window center), proof: unfold; rfl): exit 0. #print axioms => 'does not depend on any axioms' (clean). This is the ONLY closing wrong-shaped impl, and it is extensionally identical to gold.

MANDATORY resolve for every clean-closing impl: atk_6 is the only impl closing with clean axioms. Its faithful refined patch is the gold centered-window arithmetic (materialized as atk_6_patch.diff = benchmark patch.diff, since the impl computes exactly the centered slices). run_resolve('pydata__xarray-6744', <atk_6 patch>, timeout=1800) => RESOLVED=True, COMPLETED=True, NOTE='resolved' (bench swe_bench_verified, Docker oracle). So the sole closing impl RESOLVES — no verify-does-not-imply-resolve wedge.

Conclusion: the exact-equality spec admits no closes-but-does-not-resolve counterexample. Every deviating impl (atk_1..atk_5) fails to close; the only impl that closes (atk_6) is extensionally gold and its patch resolves. >=5 distinct attacks run (partial-domain/prepatch, boundary, control-flow-effect, ungrounded-oracle-echo, plus wrong-offset variants), none breaks it. VERDICT: SOUND.

Commands:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." => True for all 7.
- verify: bash scripts/lean_verify.sh <file>
- axioms: appended '#print axioms correct_rollingWindows' to atk_6_ax.lean / pos_control_ax.lean and re-ran lean_verify.sh.
- resolve: SBU_BENCHMARK=swe_bench_verified python -c 'run_resolve(...)'.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/too-strong) audit for pydata__xarray-6744 lean bundle. Modeled fn: DataArrayRolling.__iter__ start/stop slice arithmetic (xarray/core/rolling.py). Findings: (1) Spec region byte-identical Solution vs Solution_prepatch via same_spec (Lean backend) = True. (2) Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry); #print axioms correct_rollingWindows = [propext, Classical.choice, Quot.sound] only — no sorryAx, proof is genuine. (3) Validated the model against the REAL patched repo: fresh clone at base_commit 7cc6cc99, gold patch applied cleanly, installed editable into venv (numpy<2/pandas<2), ran conformance_check.py differential test — TWO independent full runs of 100009 cases each completed exit 0 = zero disagreements. (4) Independent adversarial edge tests: exhaustive n in 0..10 x w in {1,2,3,4,5,7,12,15} x center in {T,F} = 128 cases, 0 mismatches; plus 20000 small-n/large-window random cases, 0 mismatches. Covered window>n, window==n, n=0/1, both center flags. (5) Clamp equivalence verified: Lean winStart 'if i+offset<window then 0 else (offset+i)-window' matches gold 'starts[:window0-offset]=0' exactly (i<window0-offset iff i+offset<window0), and unclamped positions have offset+i>=window so start>=0 — no Nat-subtraction truncation gap. Downstream count/where min_periods masking is correctly out of modeling scope; G-CONF compares pre-mask isel slices, i.e. the exact arithmetic the fix changes. No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no narration, changed-symbol set = {'iter'} which is absent). Semantic review of the spec view (pure + post-conditions regions): the target centered-window behavior is FULLY PUBLIC in problem_statement — the title is '"center" kwarg ignored when manually iterating over DataArrayRolling', it explicitly requests 'center-justified windows' for manual iteration, and it supplies the worked example window=3/len=9 -> [nan,2,3,4,5,6,7,8,nan] contrasting centered vs right-anchored output including the boundary nan. The spec's winOffset := if center then (window+1)/2 else 1 is the natural mathematical formalization of 'centered window' derivable from that public example, not a disclosure of the edit; winStart's leading clamp mirrors the publicly shown boundary behavior; comments describe behavior abstractly ('centered on its position', 'right-anchored') with no bug/fix narration. Decisively, same_spec(Solution.lean, Solution_prepatch.lean) = True: the spec view is byte-identical pre/post fix, so the gold delta lives entirely in the elided impl region and the spec view merely asserts the correct behavior the task already asks for. Spec region integrity confirmed (spec_view hash matches meta.json). No spec-view line leaks the gold edit beyond the public problem_statement (hints_text is empty).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
