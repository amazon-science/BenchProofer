# P2 adversarial audit — matplotlib__matplotlib-20488

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl with a closing clean-axiom proof was found. The spec problem_spec_boundedRange is total and functional: it pins result.2 = bounds.2 for all inputs, result.1 = floor on (logScale∧lo≤0), and result.1 = bounds.1 on the complementary case, leaving no output component free. Every behaviorally-divergent impl therefore fails to close; the only impls that close are gold-equivalent (verified by resolve).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1 (prepatch bug / boundary): clamp only when STRICTLY negative.
+-- An exact-zero lower bound under a log scale is left untouched (the bug the
+-- gold patch fixes). Behaviourally divergent from gold at lo = 0.
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
   let sHi := bounds.2
-  if logScale = true ∧ sLo ≤ 0 then
-    sLo := floor
+  if logScale = true then
+    if sLo < 0 then
+      sLo := max sLo floor
   return (sLo, sHi)
 -- impl-end
 
@@ -60,11 +64,13 @@
     ∀ (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ), 0 < floor →
       problem_spec_boundedRange logScale floor bounds
         (implementation_boundedRange logScale floor bounds) := by
-  intro logScale floor bounds _hfloor
+  intro logScale floor bounds hfloor
   unfold implementation_boundedRange problem_spec_boundedRange
-  by_cases h : logScale = true ∧ bounds.1 ≤ 0
-  · rw [Id.run, if_pos h]
-    exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩
-  · rw [Id.run, if_neg h]
-    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
+  refine ⟨rfl, ?_, ?_⟩
+  · rintro ⟨hlog, hle⟩
+    subst hlog
+    simp only [if_pos rfl]
+    sorry
+  · intro h
+    sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2 (wrong constant): clamps to floor+1 instead of floor.
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
   let sHi := bounds.2
   if logScale = true ∧ sLo ≤ 0 then
-    sLo := floor
+    sLo := floor + 1
   return (sLo, sHi)
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3 (control-flow effect): when clamping it also overwrites the upper
+-- bound with floor, violating result.2 = bounds.2.
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
-  let sHi := bounds.2
+  let mut sHi := bounds.2
   if logScale = true ∧ sLo ≤ 0 then
     sLo := floor
+    sHi := floor
   return (sLo, sHi)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,11 +46,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4 (partial-domain / over-broad): clamps the lower bound to floor for
+-- ANY log scale, ignoring the sign guard; wrong for logScale ∧ lo > 0.
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
   let sHi := bounds.2
-  if logScale = true ∧ sLo ≤ 0 then
+  if logScale = true then
     sLo := floor
   return (sLo, sHi)
 -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,13 +46,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5 (gold-equivalent ECHO): same behaviour as gold, written as a pure
+-- conditional expression instead of Id.run mutation.
 def implementation_boundedRange
-    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
-  let mut sLo := bounds.1
-  let sHi := bounds.2
-  if logScale = true ∧ sLo ≤ 0 then
-    sLo := floor
-  return (sLo, sHi)
+    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ :=
+  if logScale = true ∧ bounds.1 ≤ 0 then (floor, bounds.2) else (bounds.1, bounds.2)
 -- impl-end
 
 -- proof-start
@@ -63,8 +61,8 @@
   intro logScale floor bounds _hfloor
   unfold implementation_boundedRange problem_spec_boundedRange
   by_cases h : logScale = true ∧ bounds.1 ≤ 0
-  · rw [Id.run, if_pos h]
+  · rw [if_pos h]
     exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩
-  · rw [Id.run, if_neg h]
+  · rw [if_neg h]
     exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,11 +46,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6 (reversed comparison): clamps when lo ≥ 0 instead of lo ≤ 0.
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
   let sHi := bounds.2
-  if logScale = true ∧ sLo ≤ 0 then
+  if logScale = true ∧ 0 ≤ sLo then
     sLo := floor
   return (sLo, sHi)
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,11 +46,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7 (gold-equivalent ECHO): guard conjuncts commuted (bounds.1 ≤ 0 first).
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
   let sHi := bounds.2
-  if logScale = true ∧ sLo ≤ 0 then
+  if sLo ≤ 0 ∧ logScale = true then
     sLo := floor
   return (sLo, sHi)
 -- impl-end
@@ -62,9 +63,9 @@
         (implementation_boundedRange logScale floor bounds) := by
   intro logScale floor bounds _hfloor
   unfold implementation_boundedRange problem_spec_boundedRange
-  by_cases h : logScale = true ∧ bounds.1 ≤ 0
+  by_cases h : bounds.1 ≤ 0 ∧ logScale = true
   · rw [Id.run, if_pos h]
-    exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩
+    refine ⟨rfl, fun _ => rfl, fun hc => absurd ⟨h.2, h.1⟩ hc⟩
   · rw [Id.run, if_neg h]
-    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
+    refine ⟨rfl, fun hc => absurd ⟨hc.2, hc.1⟩ h, fun _ => rfl⟩
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,11 +46,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 8 (dropped flag guard): clamps whenever lo ≤ 0 even without log scale;
+-- wrong for logScale = false ∧ lo ≤ 0 (should pass lo through, returns floor).
 def implementation_boundedRange
     (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
   let mut sLo := bounds.1
   let sHi := bounds.2
-  if logScale = true ∧ sLo ≤ 0 then
+  if sLo ≤ 0 then
     sLo := floor
   return (sLo, sHi)
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Sanitising the lower/upper bounds of a value range before it is handed to a
logarithmic display scale.

A value range is a pair `(lo, hi)`. When a logarithmic display scale is in use,
a non-positive lower bound is not representable (the logarithm of a non-positive
number is undefined), so such a lower bound must be replaced by a small positive
floor value. The desired behaviour is:

* the upper bound is always passed through unchanged;
* when a logarithmic scale is in use AND the lower bound is non-positive, the
  lower bound is replaced by the supplied positive floor;
* in every other case (no logarithmic scale, or a strictly positive lower
  bound) the lower bound is passed through unchanged.

Only the sign/zero ordering of the lower bound against `0` matters here, so the
bounds are modeled with exact rationals (`ℚ`); the floor models a constant
positive machine-precision value.
-/

-- axioms-start
-- No unchanged repo callee is consumed as a Lean axiom. The only quantity read
-- from an unchanged library routine is the small positive floor value; it is
-- modeled as an explicit input with a positivity precondition (carried as a
-- hypothesis of `correct_boundedRange`), not as an axiomatized callee, so there
-- is no `opaque` declaration and no `_prop` axiom.
-- axioms-end

-- pure-start
-- No pure helpers are required; the modeled behaviour is a direct conditional
-- on the lower bound's sign/zero ordering.
-- pure-end

-- post-conditions-start
/-- The sanitised range: the upper bound is unchanged; the lower bound is
replaced by the positive `floor` exactly when a logarithmic scale is in use and
the original lower bound is non-positive, and is otherwise unchanged. -/
def problem_spec_boundedRange
    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) (result : ℚ × ℚ) : Prop :=
  result.2 = bounds.2 ∧
  ((logScale = true ∧ bounds.1 ≤ 0) → result.1 = floor) ∧
  (¬(logScale = true ∧ bounds.1 ≤ 0) → result.1 = bounds.1)
-- post-conditions-end

-- impl-start
def implementation_boundedRange
    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
  let mut sLo := bounds.1
  let sHi := bounds.2
  if logScale = true ∧ sLo ≤ 0 then
    sLo := floor
  return (sLo, sHi)
-- impl-end

-- proof-start
theorem correct_boundedRange :
    ∀ (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ), 0 < floor →
      problem_spec_boundedRange logScale floor bounds
        (implementation_boundedRange logScale floor bounds) := by
  intro logScale floor bounds _hfloor
  unfold implementation_boundedRange problem_spec_boundedRange
  by_cases h : logScale = true ∧ bounds.1 ≤ 0
  · rw [Id.run, if_pos h]
    exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩
  · rw [Id.run, if_neg h]
    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Header (imports/axioms/pure/post-conditions regions, lines 1-47) kept byte-identical for all attacks; same_spec=True for all 8 (verified). Attacks run concurrently in batches ≤4.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control (exact gold): exit 0. #print axioms correct_boundedRange => [propext] (clean, no sorryAx).
- atk_1 (PREPATCH BUG / boundary: clamp only when sLo<0, exact-zero lo left untouched — reproduces the fixed bug; also redundant max sLo floor): exit 1 (unprovable — fails at lo=0 log-scale where spec requires floor). prepatch_reproduced=true.
- atk_2 (wrong constant: clamp to floor+1): exit 1.
- atk_3 (control-flow effect: also clobbers upper bound sHi:=floor, violating result.2=bounds.2): exit 1.
- atk_4 (over-broad partial-domain: clamp for ANY logScale ignoring sign guard): exit 1.
- atk_6 (reversed comparison: clamp on 0≤sLo instead of sLo≤0): exit 1.
- atk_8 (dropped flag guard: clamp on sLo≤0 regardless of logScale): exit 1.
  All six failures are genuine proof/rewrite goal failures (type mismatch on the absurd/⟨rfl,...⟩ witness, or 'rewrite failed: did not find occurrence' because the impl's if-guard differs from the spec's), NOT spurious compile errors — confirming the spec is behaviorally discriminating and total.
- atk_5 (GOLD-EQUIVALENT ECHO, if-then-else expression form): exit 0. #print axioms => [propext] (clean).
- atk_7 (GOLD-EQUIVALENT ECHO, commuted-conjunction guard sLo≤0 ∧ logScale): exit 0. #print axioms => [propext] (clean).

RESOLVE RESULTS (run_resolve, official Docker harness) for every closing clean-axiom attack — faithful refined patch equals the gold post-patch guard because atk_5/atk_7 are behaviorally identical to gold:
- atk_5 faithful patch: resolved=True, completed=True, note='resolved', flaky=False.
- atk_7 faithful patch: resolved=True, completed=True, note='resolved', flaky=False.
No closing impl has a non-resolving faithful patch => verify⇏correct NOT exhibited => spec not broken.

REFINEMENT AUDIT (refinement.md): 5 legs, all tagged R (exact-rational refinement of float s_vmin/s_vmax and the eps floor). NO A-consumed, NO A-reference, NO kind-3 legs, NO I claim mismatch. axioms-start/pure-start regions declare no opaque and no `axiom … _prop`; G-AX correctly skips. #print axioms on all closing proofs shows only [propext] (Mathlib-standard), confirming no axiomatized-callee dependency to falsify. floor modeled as explicit positive input (0<floor hypothesis) rather than an axiomatized callee — correct per SPEC_GUIDE §3 (deeply-modeled changed decision must not be axiomatized); there is no deep-model↔callee correspondence claim to break. mapping.md symbol bindings (image.py:532-541 @ base b7ce415c) are consistent with patch.diff.

≥5 distinct wrong impls attacked (6 wrong + prepatch + 2 echoes = 8 same-spec attacks), all verified & reported; none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl with a closing clean-axiom proof was found. The spec problem_spec_boundedRange is total and functional: it pins result.2 = bounds.2 for all inputs, result.1 = floor on (logScale∧lo≤0), and result.1 = bounds.1 on the complementary case, leaving no output component free. Every behaviorally-divergent impl therefore fails to close; the only impls that close are gold-equivalent (verified by resolve).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Sanitising the lower/upper bounds of a value range before it is handed to a
logarithmic display scale.

A value range is a pair `(lo, hi)`. When a logarithmic display scale is in use,
a non-positive lower bound is not representable (the logarithm of a non-positive
number is undefined), so such a lower bound must be replaced by a small positive
floor value. The desired behaviour is:

* the upper bound is always passed through unchanged;
* when a logarithmic scale is in use AND the lower bound is non-positive, the
  lower bound is replaced by the supplied positive floor;
* in every other case (no logarithmic scale, or a strictly positive lower
  bound) the lower bound is passed through unchanged.

Only the sign/zero ordering of the lower bound against `0` matters here, so the
bounds are modeled with exact rationals (`ℚ`); the floor models a constant
positive machine-precision value.
-/

-- axioms-start
-- No unchanged repo callee is consumed as a Lean axiom. The only quantity read
-- from an unchanged library routine is the small positive floor value; it is
-- modeled as an explicit input with a positivity precondition (carried as a
-- hypothesis of `correct_boundedRange`), not as an axiomatized callee, so there
-- is no `opaque` declaration and no `_prop` axiom.
-- axioms-end

-- pure-start
-- No pure helpers are required; the modeled behaviour is a direct conditional
-- on the lower bound's sign/zero ordering.
-- pure-end

-- post-conditions-start
/-- The sanitised range: the upper bound is unchanged; the lower bound is
replaced by the positive `floor` exactly when a logarithmic scale is in use and
the original lower bound is non-positive, and is otherwise unchanged. -/
def problem_spec_boundedRange
    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) (result : ℚ × ℚ) : Prop :=
  result.2 = bounds.2 ∧
  ((logScale = true ∧ bounds.1 ≤ 0) → result.1 = floor) ∧
  (¬(logScale = true ∧ bounds.1 ≤ 0) → result.1 = bounds.1)
-- post-conditions-end

-- impl-start
def implementation_boundedRange
    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
  let mut sLo := bounds.1
  let sHi := bounds.2
  if logScale = true ∧ sLo ≤ 0 then
    sLo := floor
  return (sLo, sHi)
-- impl-end

-- proof-start
theorem correct_boundedRange :
    ∀ (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ), 0 < floor →
      problem_spec_boundedRange logScale floor bounds
        (implementation_boundedRange logScale floor bounds) := by
  intro logScale floor bounds _hfloor
  unfold implementation_boundedRange problem_spec_boundedRange
  by_cases h : logScale = true ∧ bounds.1 ≤ 0
  · rw [Id.run, if_pos h]
    exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩
  · rw [Id.run, if_neg h]
    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Header (imports/axioms/pure/post-conditions regions, lines 1-47) kept byte-identical for all attacks; same_spec=True for all 8 (verified). Attacks run concurrently in batches ≤4.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control (exact gold): exit 0. #print axioms correct_boundedRange => [propext] (clean, no sorryAx).
- atk_1 (PREPATCH BUG / boundary: clamp only when sLo<0, exact-zero lo left untouched — reproduces the fixed bug; also redundant max sLo floor): exit 1 (unprovable — fails at lo=0 log-scale where spec requires floor). prepatch_reproduced=true.
- atk_2 (wrong constant: clamp to floor+1): exit 1.
- atk_3 (control-flow effect: also clobbers upper bound sHi:=floor, violating result.2=bounds.2): exit 1.
- atk_4 (over-broad partial-domain: clamp for ANY logScale ignoring sign guard): exit 1.
- atk_6 (reversed comparison: clamp on 0≤sLo instead of sLo≤0): exit 1.
- atk_8 (dropped flag guard: clamp on sLo≤0 regardless of logScale): exit 1.
  All six failures are genuine proof/rewrite goal failures (type mismatch on the absurd/⟨rfl,...⟩ witness, or 'rewrite failed: did not find occurrence' because the impl's if-guard differs from the spec's), NOT spurious compile errors — confirming the spec is behaviorally discriminating and total.
- atk_5 (GOLD-EQUIVALENT ECHO, if-then-else expression form): exit 0. #print axioms => [propext] (clean).
- atk_7 (GOLD-EQUIVALENT ECHO, commuted-conjunction guard sLo≤0 ∧ logScale): exit 0. #print axioms => [propext] (clean).

RESOLVE RESULTS (run_resolve, official Docker harness) for every closing clean-axiom attack — faithful refined patch equals the gold post-patch guard because atk_5/atk_7 are behaviorally identical to gold:
- atk_5 faithful patch: resolved=True, completed=True, note='resolved', flaky=False.
- atk_7 faithful patch: resolved=True, completed=True, note='resolved', flaky=False.
No closing impl has a non-resolving faithful patch => verify⇏correct NOT exhibited => spec not broken.

REFINEMENT AUDIT (refinement.md): 5 legs, all tagged R (exact-rational refinement of float s_vmin/s_vmax and the eps floor). NO A-consumed, NO A-reference, NO kind-3 legs, NO I claim mismatch. axioms-start/pure-start regions declare no opaque and no `axiom … _prop`; G-AX correctly skips. #print axioms on all closing proofs shows only [propext] (Mathlib-standard), confirming no axiomatized-callee dependency to falsify. floor modeled as explicit positive input (0<floor hypothesis) rather than an axiomatized callee — correct per SPEC_GUIDE §3 (deeply-modeled changed decision must not be axiomatized); there is no deep-model↔callee correspondence claim to break. mapping.md symbol bindings (image.py:532-541 @ base b7ce415c) are consistent with patch.diff.

≥5 distinct wrong impls attacked (6 wrong + prepatch + 2 echoes = 8 same-spec attacks), all verified & reported; none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-behavior) audit of matplotlib__matplotlib-20488 lean bundle.

Spec region byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — the post-conditions region (problem_spec_boundedRange) is identical between patched and prepatch bundles, so the discriminator is impl/proof only, as required.

Compilation + axioms: scripts/lean_verify.sh on Solution.lean exits 0 (compiles, no sorry). #print axioms correct_boundedRange => [propext] only (subset of STANDARD_AXIOMS); NO sorryAx, so the proof is genuine.

Real repo callee (base_commit b7ce415c / verified worktree at image.py _make_image lines 532-541, gold post-patch): s_vmin,s_vmax = vrange; if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0: s_vmin = np.finfo(scaled_dtype).eps; s_vmax untouched.

Case-by-case agreement of problem_spec_boundedRange with the real post-patch behavior:
- logScale=True & lo<=0: spec requires result.1=floor; real sets s_vmin=eps (floor models eps as a free positive input, 0<floor precondition). AGREE.
- logScale=True & lo>0: guard false, real passes lo through; spec's ¬(...)→result.1=bounds.1 branch. AGREE.
- logScale=False (any lo): isinstance false, real passes lo through; spec pass-through. AGREE.
- Upper bound: real never modifies s_vmax; spec pins result.2 = bounds.2 unconditionally. AGREE.

Over/under-strength check: floor is modeled as a free positive parameter (not pinned to a specific rational), so the clamp branch is not over-constrained to a particular epsilon value; it only asserts result.1 equals whatever positive floor is supplied — matching the real 'set to eps' semantics. The <= 0 (non-strict) boundary correctly captures the exact fix (the prepatch/buggy strict < 0 guard is what problem_spec REJECTS, driving the unclosable prepatch proof). No output component is left free. Rationals soundly capture the sign/zero-order-only decision.

No diverging input found across all four input classes and the boundary lo=0. Spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (import + docstring + `problem_spec_boundedRange` postcondition; impl and proof regions ELIDED) verified: same_spec(post,pre)=True and computed spec_view hash ea02937e... matches recorded G-HYGIENE hash. The spec describes the target behavior only abstractly — 'value range (lo,hi)', 'logarithmic display scale', 'non-positive lower bound replaced by a small positive floor'. It does NOT (a) quote any patch text, (b) name Python symbols (s_vmin, LogNorm, mcolors, np.finfo, image.py, vrange), or (c) render the specific `s_vmin < 0` → `s_vmin <= 0` source diff. The postcondition encodes the target correctness condition (clamp lower bound to floor iff logScale ∧ bounds.1 ≤ 0), which is the intended specification, not a leaked reconstruction of the edit — this is inherent to any spec-based benchmark. The problem_statement already discloses the LogNorm 'Invalid vmin or vmax' failure and the _make_image call path. Concrete gold-edit details (the `< 0` vs `<= 0` guard, the exact-zero slip-through, np.finfo(scaled_dtype).eps) appear ONLY in auditor docs mapping.md and refinement.md, which are not part of the spec view an author sees. No leakage beyond public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
