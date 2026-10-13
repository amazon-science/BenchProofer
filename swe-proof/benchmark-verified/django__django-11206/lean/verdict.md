# P2 adversarial audit — django__django-11206

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,14 +75,8 @@
     (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
     (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
     (useL10n : Option Bool) : String := Id.run do
-  let mut n := number
-  match decimalPos with
-  | some d =>
-      let cutoff := cutoffOf d
-      if |n| < cutoff then
-        n := 0
-  | none => pure ()
-  return renderDecimal n decimalSep decimalPos grouping thousandSep
+  -- WRONG: no smallness adjustment (prepatch bug)
+  return renderDecimal number decimalSep decimalPos grouping thousandSep
     forceGrouping useL10n
 -- impl-end
 
@@ -97,11 +91,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   match decimalPos with
   | some d =>
       let cutoff := cutoffOf d
-      if |n| < cutoff then
+      if |n| ≤ cutoff then      -- WRONG: <= instead of <
         n := 0
   | none => pure ()
   return renderDecimal n decimalSep decimalPos grouping thousandSep
@@ -97,11 +97,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
   let mut n := number
   match decimalPos with
   | some d =>
-      let cutoff := cutoffOf d
+      let cutoff : ℚ := 1 / 10 ^ d    -- WRONG: no max d 1
       if |n| < cutoff then
         n := 0
   | none => pure ()
@@ -97,11 +97,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,10 +77,11 @@
     (useL10n : Option Bool) : String := Id.run do
   let mut n := number
   match decimalPos with
-  | some d =>
-      let cutoff := cutoffOf d
+  | some (Nat.succ d') =>
+      let cutoff := cutoffOf (Nat.succ d')
       if |n| < cutoff then
         n := 0
+  | some 0 => pure ()            -- WRONG: d=0 never snaps
   | none => pure ()
   return renderDecimal n decimalSep decimalPos grouping thousandSep
     forceGrouping useL10n
@@ -97,11 +98,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
   | some d =>
       let cutoff := cutoffOf d
       if |n| < cutoff then
-        n := 0
+        n := cutoff             -- WRONG: sets to cutoff, not 0
   | none => pure ()
   return renderDecimal n decimalSep decimalPos grouping thousandSep
     forceGrouping useL10n
@@ -97,11 +97,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
       if |n| < cutoff then
         n := 0
   | none => pure ()
-  return renderDecimal n decimalSep decimalPos grouping thousandSep
+  return renderDecimal n thousandSep decimalPos grouping decimalSep
     forceGrouping useL10n
 -- impl-end
 
@@ -97,11 +97,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,9 @@
       let cutoff := cutoffOf d
       if |n| < cutoff then
         n := 0
-  | none => pure ()
+  | none =>
+      if |n| < cutoffOf 0 then   -- WRONG: snaps even when decimalPos = none
+        n := 0
   return renderDecimal n decimalSep decimalPos grouping thousandSep
     forceGrouping useL10n
 -- impl-end
@@ -97,11 +99,15 @@
           thousandSep forceGrouping useL10n) := by
   intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
   unfold problem_spec_formatNumber implementation_formatNumber snapValue
-  cases decimalPos with
-  | none => rfl
-  | some d =>
-      simp only [Id.run, bind, pure]
-      by_cases h : |number| < cutoffOf d
-      · simp only [h, if_true]
-      · simp only [h, if_false]
+  first
+  | rfl
+  | (cases decimalPos with
+     | none => simp_all [Id.run, bind, pure]
+     | some d =>
+        simp only [Id.run, bind, pure]
+        by_cases h : |number| < cutoffOf d
+        · simp_all [h]
+        · simp_all [h])
+  | simp_all [Id.run, bind, pure]
+
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a specified-precision numeric value as a display string.

A value is rendered to a string under a chosen number of visible decimal places
(`decimalPos`) together with the usual presentation options (decimal separator,
digit grouping, thousands separator, grouping toggles, localization toggle).

When a number of visible decimal places is requested, there is a smallest
magnitude that can still influence any of those visible places: one unit in the
least significant requested place. A value whose absolute magnitude is strictly
below that smallest representable unit cannot affect any visible digit, so for
display purposes it is indistinguishable from zero and is rendered exactly as
zero would be. A value whose magnitude is at least that unit, or any value when
no specific number of decimal places is requested, is rendered on its own.

Everything about turning a (possibly zeroed) value into its final string — the
choice of presentation, truncation/padding to the requested places, sign, and
grouping — is the standard rendering procedure, applied to the value after the
above smallness adjustment.
-/

-- axioms-start
-- `renderDecimal` is the standard, unchanged value-to-string rendering procedure
-- (presentation choice, truncation/padding to the requested number of places,
-- sign, grouping). It is declared `opaque` so it can appear in the executable
-- implementation; the behavior modeled here is solely the smallness adjustment
-- applied to its argument, so NO property of `renderDecimal` is consumed (the
-- result is the renderer applied to the adjusted value, and the implementation
-- computes exactly that). Hence there is no `renderDecimal_prop` axiom; the
-- binding of `renderDecimal` to the real rendering procedure is validated by the
-- conformance check (G-CONF), not assumed in the proof.
opaque renderDecimal :
    ℚ → String → Option Nat → Int → String → Bool → Option Bool → String
-- axioms-end

-- pure-start
/-- The smallest magnitude that still affects a visible decimal place when
`d` decimal places are requested: one unit in the least significant place,
i.e. `10^(-max d 1)` (requesting zero places still uses the tenths place as the
threshold). -/
def cutoffOf (d : Nat) : ℚ := 1 / 10 ^ (max d 1)

/-- The smallness adjustment: when a specific number of decimal places is requested
and the value's magnitude is strictly below the smallest representable unit at
that precision, the value is treated as zero; otherwise it is left unchanged.
When no specific number of decimal places is requested, the value is left
unchanged. -/
def snapValue (number : ℚ) (decimalPos : Option Nat) : ℚ :=
  match decimalPos with
  | none => number
  | some d => if |number| < cutoffOf d then 0 else number
-- pure-end

-- post-conditions-start
/-- The rendered string is the standard rendering procedure applied to the value
AFTER the smallness adjustment: a value below the smallest representable unit at
the requested precision is rendered exactly as zero is, and every other value
(and every value when no precision is requested) is rendered on its own.
The result is fully pinned to the inputs — nothing is left free, since both the
adjustment and the rendering procedure are functions of the inputs. -/
def problem_spec_formatNumber
    (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
    (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
    (useL10n : Option Bool) (result : String) : Prop :=
  result =
    renderDecimal (snapValue number decimalPos) decimalSep decimalPos
      grouping thousandSep forceGrouping useL10n
-- post-conditions-end

-- impl-start
def implementation_formatNumber
    (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
    (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
    (useL10n : Option Bool) : String := Id.run do
  let mut n := number
  match decimalPos with
  | some d =>
      let cutoff := cutoffOf d
      if |n| < cutoff then
        n := 0
  | none => pure ()
  return renderDecimal n decimalSep decimalPos grouping thousandSep
    forceGrouping useL10n
-- impl-end

-- proof-start
theorem correct_formatNumber :
    ∀ (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
      (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
      (useL10n : Option Bool),
      problem_spec_formatNumber number decimalSep decimalPos grouping
        thousandSep forceGrouping useL10n
        (implementation_formatNumber number decimalSep decimalPos grouping
          thousandSep forceGrouping useL10n) := by
  intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
  unfold problem_spec_formatNumber implementation_formatNumber snapValue
  cases decimalPos with
  | none => rfl
  | some d =>
      simp only [Id.run, bind, pure]
      by_cases h : |number| < cutoffOf d
      · simp only [h, if_true]
      · simp only [h, if_false]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: post-condition `result = renderDecimal (snapValue number decimalPos) decimalSep decimalPos grouping thousandSep forceGrouping useL10n`, where `renderDecimal` is declared `opaque` and the proof consumes NO property of it (axiom_check.py = skip stub, meta.json axioms=[]). Consequence: every verifying impl must feed `renderDecimal` an argument PROPOSITIONALLY EQUAL to `snapValue number decimalPos` with byte-identical pass-through args. Any behaviorally-distinct impl leaves an unclosable residual `renderDecimal X … = renderDecimal Y …` (opaque fn, no congruence available beyond arg-equality). This is a tight A-reference pinning — the model↔patch correspondence is enforced structurally.

SAME-SPEC: all 7 attacks + positive_control verified same_spec=True via swebench_unified.markers.same_spec (lean backend); only impl+proof regions edited, axioms/pure/pre/post byte-identical.

COMMANDS (from project root, run concurrently ≤4 at a time): `bash scripts/lean_verify.sh <file>.lean`.

### Results
- pos_control.lean (gold impl+proof, unchanged): EXIT=0 VERIFIES. `#print axioms correct_formatNumber` => [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx.
- atk_1 (prepatch bug: no snap, raw number → renderDecimal): EXIT=1. Residual goal `renderDecimal number … = renderDecimal (match … => if |number|<cutoffOf d then 0 else number) …`. Hardened attempt (atk_1_hard.lean with congr) collapses to `⊢ number = 0` — UNCLOSABLE. PREPATCH REPRODUCED.
- atk_2 (boundary flip |n| ≤ cutoff instead of <): EXIT=1, unsolved goals at 97:48.
- atk_3 (wrong cutoff 1/10^d, drops max d 1): EXIT=1, unsolved goals at 97:48.
- atk_4 (partial domain: d=0 never snaps): EXIT=1, unsolved goals at 98:48.
- atk_5 (control-flow-effect: snaps to cutoff value instead of 0): EXIT=1, residual `renderDecimal (cutoffOf d) … = renderDecimal 0 …`.
- atk_6 (pass-through swap: decimalSep/thousandSep swapped into renderDecimal): EXIT=1, residual `renderDecimal 0 thousandSep … decimalSep … = renderDecimal 0 decimalSep … thousandSep …`.
- atk_7 (ungrounded-oracle echo: snaps even when decimalPos=none): EXIT=1, unsolved goals at 99:48.

Each attack that was verified used a maximal best-effort proof (rfl | case-split + by_cases + simp_all). ZERO wrong impls closed with clean axioms, so NO faithful patch needed to be materialized/resolved (patches={} is correct — there is no verifying-but-wrong candidate to run through run_resolve).

REFINEMENT.MD AUDIT: legs op1=I, op2=R, op3=R, op4=R (the snap: precision-gated magnitude-to-zero), op5=A-reference (renderDecimal = unchanged rendering tail, numberformat.py:32 onward). No kind-3 (ungrounded-oracle) leg. A-reference correspondence holds: renderDecimal is bound to the REAL base-commit rendering tail in G-CONF (conformance_check.py strips the inserted guard from the patched source and differential-tests base_format(snapValue(number)) vs the real patched format over 1e5 seeded inputs); the proof consumes no property of it, so opaqueness is not exploitable to admit a wrong impl. meta.json axioms=[] and deep_model_references=[renderDecimal …] are consistent with the skip-stub axiom_check.py.

VERDICT: SOUND. verify⇒correct holds — every behaviorally-distinct same-spec wrong impl fails to verify; the only closing proof is the faithful gold impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a specified-precision numeric value as a display string.

A value is rendered to a string under a chosen number of visible decimal places
(`decimalPos`) together with the usual presentation options (decimal separator,
digit grouping, thousands separator, grouping toggles, localization toggle).

When a number of visible decimal places is requested, there is a smallest
magnitude that can still influence any of those visible places: one unit in the
least significant requested place. A value whose absolute magnitude is strictly
below that smallest representable unit cannot affect any visible digit, so for
display purposes it is indistinguishable from zero and is rendered exactly as
zero would be. A value whose magnitude is at least that unit, or any value when
no specific number of decimal places is requested, is rendered on its own.

Everything about turning a (possibly zeroed) value into its final string — the
choice of presentation, truncation/padding to the requested places, sign, and
grouping — is the standard rendering procedure, applied to the value after the
above smallness adjustment.
-/

-- axioms-start
-- `renderDecimal` is the standard, unchanged value-to-string rendering procedure
-- (presentation choice, truncation/padding to the requested number of places,
-- sign, grouping). It is declared `opaque` so it can appear in the executable
-- implementation; the behavior modeled here is solely the smallness adjustment
-- applied to its argument, so NO property of `renderDecimal` is consumed (the
-- result is the renderer applied to the adjusted value, and the implementation
-- computes exactly that). Hence there is no `renderDecimal_prop` axiom; the
-- binding of `renderDecimal` to the real rendering procedure is validated by the
-- conformance check (G-CONF), not assumed in the proof.
opaque renderDecimal :
    ℚ → String → Option Nat → Int → String → Bool → Option Bool → String
-- axioms-end

-- pure-start
/-- The smallest magnitude that still affects a visible decimal place when
`d` decimal places are requested: one unit in the least significant place,
i.e. `10^(-max d 1)` (requesting zero places still uses the tenths place as the
threshold). -/
def cutoffOf (d : Nat) : ℚ := 1 / 10 ^ (max d 1)

/-- The smallness adjustment: when a specific number of decimal places is requested
and the value's magnitude is strictly below the smallest representable unit at
that precision, the value is treated as zero; otherwise it is left unchanged.
When no specific number of decimal places is requested, the value is left
unchanged. -/
def snapValue (number : ℚ) (decimalPos : Option Nat) : ℚ :=
  match decimalPos with
  | none => number
  | some d => if |number| < cutoffOf d then 0 else number
-- pure-end

-- post-conditions-start
/-- The rendered string is the standard rendering procedure applied to the value
AFTER the smallness adjustment: a value below the smallest representable unit at
the requested precision is rendered exactly as zero is, and every other value
(and every value when no precision is requested) is rendered on its own.
The result is fully pinned to the inputs — nothing is left free, since both the
adjustment and the rendering procedure are functions of the inputs. -/
def problem_spec_formatNumber
    (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
    (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
    (useL10n : Option Bool) (result : String) : Prop :=
  result =
    renderDecimal (snapValue number decimalPos) decimalSep decimalPos
      grouping thousandSep forceGrouping useL10n
-- post-conditions-end

-- impl-start
def implementation_formatNumber
    (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
    (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
    (useL10n : Option Bool) : String := Id.run do
  let mut n := number
  match decimalPos with
  | some d =>
      let cutoff := cutoffOf d
      if |n| < cutoff then
        n := 0
  | none => pure ()
  return renderDecimal n decimalSep decimalPos grouping thousandSep
    forceGrouping useL10n
-- impl-end

-- proof-start
theorem correct_formatNumber :
    ∀ (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
      (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
      (useL10n : Option Bool),
      problem_spec_formatNumber number decimalSep decimalPos grouping
        thousandSep forceGrouping useL10n
        (implementation_formatNumber number decimalSep decimalPos grouping
          thousandSep forceGrouping useL10n) := by
  intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
  unfold problem_spec_formatNumber implementation_formatNumber snapValue
  cases decimalPos with
  | none => rfl
  | some d =>
      simp only [Id.run, bind, pure]
      by_cases h : |number| < cutoffOf d
      · simp only [h, if_true]
      · simp only [h, if_false]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: post-condition `result = renderDecimal (snapValue number decimalPos) decimalSep decimalPos grouping thousandSep forceGrouping useL10n`, where `renderDecimal` is declared `opaque` and the proof consumes NO property of it (axiom_check.py = skip stub, meta.json axioms=[]). Consequence: every verifying impl must feed `renderDecimal` an argument PROPOSITIONALLY EQUAL to `snapValue number decimalPos` with byte-identical pass-through args. Any behaviorally-distinct impl leaves an unclosable residual `renderDecimal X … = renderDecimal Y …` (opaque fn, no congruence available beyond arg-equality). This is a tight A-reference pinning — the model↔patch correspondence is enforced structurally.

SAME-SPEC: all 7 attacks + positive_control verified same_spec=True via swebench_unified.markers.same_spec (lean backend); only impl+proof regions edited, axioms/pure/pre/post byte-identical.

COMMANDS (from project root, run concurrently ≤4 at a time): `bash scripts/lean_verify.sh <file>.lean`.

### Results
- pos_control.lean (gold impl+proof, unchanged): EXIT=0 VERIFIES. `#print axioms correct_formatNumber` => [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx.
- atk_1 (prepatch bug: no snap, raw number → renderDecimal): EXIT=1. Residual goal `renderDecimal number … = renderDecimal (match … => if |number|<cutoffOf d then 0 else number) …`. Hardened attempt (atk_1_hard.lean with congr) collapses to `⊢ number = 0` — UNCLOSABLE. PREPATCH REPRODUCED.
- atk_2 (boundary flip |n| ≤ cutoff instead of <): EXIT=1, unsolved goals at 97:48.
- atk_3 (wrong cutoff 1/10^d, drops max d 1): EXIT=1, unsolved goals at 97:48.
- atk_4 (partial domain: d=0 never snaps): EXIT=1, unsolved goals at 98:48.
- atk_5 (control-flow-effect: snaps to cutoff value instead of 0): EXIT=1, residual `renderDecimal (cutoffOf d) … = renderDecimal 0 …`.
- atk_6 (pass-through swap: decimalSep/thousandSep swapped into renderDecimal): EXIT=1, residual `renderDecimal 0 thousandSep … decimalSep … = renderDecimal 0 decimalSep … thousandSep …`.
- atk_7 (ungrounded-oracle echo: snaps even when decimalPos=none): EXIT=1, unsolved goals at 99:48.

Each attack that was verified used a maximal best-effort proof (rfl | case-split + by_cases + simp_all). ZERO wrong impls closed with clean axioms, so NO faithful patch needed to be materialized/resolved (patches={} is correct — there is no verifying-but-wrong candidate to run through run_resolve).

REFINEMENT.MD AUDIT: legs op1=I, op2=R, op3=R, op4=R (the snap: precision-gated magnitude-to-zero), op5=A-reference (renderDecimal = unchanged rendering tail, numberformat.py:32 onward). No kind-3 (ungrounded-oracle) leg. A-reference correspondence holds: renderDecimal is bound to the REAL base-commit rendering tail in G-CONF (conformance_check.py strips the inserted guard from the patched source and differential-tests base_format(snapValue(number)) vs the real patched format over 1e5 seeded inputs); the proof consumes no property of it, so opaqueness is not exploitable to admit a wrong impl. meta.json axioms=[] and deep_model_references=[renderDecimal …] are consistent with the skip-stub axiom_check.py.

VERDICT: SOUND. verify⇒correct holds — every behaviorally-distinct same-spec wrong impl fails to verify; the only closing proof is the faithful gold impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Lean: lean_verify.sh exit 0; #print axioms correct_formatNumber -> [propext, Classical.choice, Quot.sound] only, no sorryAx (proof is genuine, not fake). same_spec(Solution, Solution_prepatch, lean) = True (spec region byte-identical; prepatch differs only in impl+proof). Faithfulness: the gold fix is a precision-gated magnitude-to-zero snap inserted at the top of the isinstance(number,Decimal) branch; the model deeply models it as snapValue/cutoffOf and leaves the unchanged rendering tail as an opaque A-reference (renderDecimal), deferred to G-CONF. The proof consumes NO property of renderDecimal (both sides of problem_spec apply the same renderer to the same snapped argument), so the spec is not too strong. Independent differential test (not the bundle's own conformance_check.py) against the patched gold source: 0/400000 disagreements. The strict '<' boundary (abs(number)==cutoff => no snap) matches; -0.0, None-decimal_pos identity path, and large-decimal_pos all match. The Decimal->ℚ abstraction is sound here precisely because the value-dependent snap is the only changed behavior and the exponent/trailing-zero-dependent rendering is left opaque rather than claimed. Verdict: FAITHFUL — spec accurately reflects real repo behavior, neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over lean spec_view) passes with zero hard failures; meta G-LEAK status=pass, no relaxed_leakage flag / no RELAXED_LEAKAGE.md; same_spec(patched, prepatch)=True. Semantic review: (1) no diff markers or gold-patch Python lines reproduced (spec uses abstract Lean cutoffOf/snapValue vs gold's Decimal('0.'+'1'.rjust(...))/abs(number)<cutoff); (2) patched file path django/utils/numberformat.py absent; (3) only changed repo symbol 'format' is already public in problem_statement (utils.numberformat.format); (4) no bug/fix/patch narration — the only prepatch narration lives in impl/proof regions, which the spec_view elides. The postcondition/pure regions (cutoffOf = 1/10^(max d 1), snapValue) encode the CORRECT behavior, which is exactly what the public problem_statement already mandates ('number smaller than what can be encoded using decimal_pos → 0.0000...000'); specifying correct behavior is a spec's job and is not a disclosure of the gold edit beyond the problem_statement. The behavior-changing impl (n := 0 snap) and proof are elided. No line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
