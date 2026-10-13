# P2 adversarial audit — matplotlib__matplotlib-25287

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_ctrl_match.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies (the total-equality postcondition out = offsetColor tickColor labelColor fully pins the output). The only verifying wrong impl is a NON-TERMINATING one (atk_9), whose faithful patch TIMES OUT under the harness (completed=False, INCONCLUSIVE) rather than being graded completed AND not-resolved, so it does not meet the operational verify-not-correct (BROKEN) bar. See notes.
```

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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,12 +55,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return tickColor
     -- impl-end
 
 prove_correct xAxisOffsetColor by
@@ -76,10 +71,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return tickColor
     -- impl-end
 
 prove_correct yAxisOffsetColor by
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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,12 +55,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return labelColor
     -- impl-end
 
 prove_correct xAxisOffsetColor by
@@ -76,10 +71,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return labelColor
     -- impl-end
 
 prove_correct yAxisOffsetColor by
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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,12 +55,10 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
     if labelColor = "inherit" then
+      return labelColor
+    else
       return tickColor
-    else
-      return labelColor
     -- impl-end
 
 prove_correct xAxisOffsetColor by
@@ -77,9 +75,9 @@
   do
     -- impl-start
     if labelColor = "inherit" then
+      return labelColor
+    else
       return tickColor
-    else
-      return labelColor
     -- impl-end
 
 prove_correct yAxisOffsetColor by
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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,12 +55,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return ""
     -- impl-end
 
 prove_correct xAxisOffsetColor by
@@ -76,10 +71,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return ""
     -- impl-end
 
 prove_correct yAxisOffsetColor by
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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,9 +55,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
-    if labelColor = "inherit" then
+    if tickColor = "inherit" then
       return tickColor
     else
       return labelColor
@@ -76,7 +74,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
+    if tickColor = "inherit" then
       return tickColor
     else
       return labelColor
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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,9 +55,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
-    if labelColor = "inherit" then
+    if labelColor = "inherited" then
       return tickColor
     else
       return labelColor
@@ -76,7 +74,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
+    if labelColor = "inherited" then
       return tickColor
     else
       return labelColor
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,8 +55,6 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
     if labelColor = "inherit" then
       return tickColor
     else
@@ -76,10 +74,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
-      return tickColor
-    else
-      return labelColor
+    return tickColor
     -- impl-end
 
 prove_correct yAxisOffsetColor by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed pure decision
@@ -55,9 +55,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    -- Follow the configured tick-label color, falling back to the tick color
-    -- only when the label color is left at the inherit sentinel.
-    if labelColor = "inherit" then
+    if labelColor ≠ "inherit" then
       return tickColor
     else
       return labelColor
@@ -76,7 +74,7 @@
   ensures out = offsetColor tickColor labelColor
   do
     -- impl-start
-    if labelColor = "inherit" then
+    if labelColor ≠ "inherit" then
       return tickColor
     else
       return labelColor
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl_match.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed pure decision
--  over two configured color settings — the axis's tick color and its tick-label
--  color — yielding the color used to paint the secondary exponent (offset) text
--  for that axis. The downstream consumer that actually paints the text with the
--  chosen color is an UNCHANGED continuation reached identically on both branches,
--  so nothing about it is assumed: it is neither consumed as a contract nor
--  deep-modeled. There is no `axiom` declaration and no A-reference. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The color used to paint an axis's secondary exponent (offset) text, given the
   axis's tick color and its tick-label color.

   A tick-label color of the sentinel value "inherit" means "no distinct label
   color was configured — take the color from the tick color." Any other value
   is an explicitly configured label color and governs directly.

   This is the single behaviour at issue: the exponent text must follow
   the configured tick-LABEL color, falling back to the tick color only when the
   label color is left at the inherit sentinel — rather than always following the
   tick color and ignoring an explicitly configured label color. Grounded
   entirely in the two input color settings (directive 8): the result is one of
   them, selected by whether the label color is the inherit sentinel. -/
def offsetColor (tickColor labelColor : String) : String :=
  if labelColor = "inherit" then tickColor else labelColor
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the color of the secondary exponent (offset) text shown at the end
   of the horizontal axis. `tickColor` is the axis's configured tick color and
   `labelColor` is its configured tick-label color; both are read-only color
   settings (neither is `mut`) and neither is altered.

   Desired behaviour: an explicitly configured tick-label color governs the
   exponent text directly; the inherit sentinel falls back to — and therefore
   follows — the tick color. Always using the tick color, ignoring a configured
   label color, is the defect this pins out. -/
method xAxisOffsetColor (tickColor : String) (labelColor : String)
    return (out : String)
  ensures out = offsetColor tickColor labelColor
  do
    -- impl-start
    match labelColor with
    | "inherit" => return tickColor
    | _ => return labelColor
    -- impl-end

prove_correct xAxisOffsetColor by
  loom_solve <;> simp only [offsetColor] <;> split <;> simp_all

/- Determine the color of the secondary exponent (offset) text shown at the end
   of the vertical axis. Same desired behaviour as the horizontal axis: the
   configured tick-label color governs, and the inherit sentinel falls back to
   the tick color. `tickColor` and `labelColor` are read-only color settings
   (neither `mut`); neither is altered. -/
method yAxisOffsetColor (tickColor : String) (labelColor : String)
    return (out : String)
  ensures out = offsetColor tickColor labelColor
  do
    -- impl-start
    match labelColor with
    | "inherit" => return tickColor
    | _ => return labelColor
    -- impl-end

prove_correct yAxisOffsetColor by
  loom_solve <;> simp only [offsetColor] <;> split <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Verifier: scripts/lean_verify.sh.

### 1. TERMINATING WRONG-IMPL BATTERY (8 distinct, all same_spec=True)
Command per file: `bash scripts/lean_verify.sh <f>.lean`. same_spec via swebench_unified.markers.same_spec (velvet) = True for ALL.
  atk_1  both axes `return tickColor` (= prepatch bug / control-flow) -> exit 1 (REJECTED; error: simp_all made no progress on explicit-label clause)
  atk_2  both `return labelColor` (ungrounded echo of one input)      -> exit 1 (REJECTED; unsolved on inherit branch)
  atk_3  both branches swapped                                        -> exit 1 (REJECTED)
  atk_4  both `return ""` (partial-domain/empty)                      -> exit 1 (REJECTED)
  atk_5  sentinel tests tickColor instead of labelColor (boundary)    -> exit 1 (REJECTED)
  atk_6  sentinel string typo "inherited" (boundary)                  -> exit 1 (REJECTED)
  atk_7  correct x, buggy y `return tickColor` (mixed-axis)           -> exit 1 (REJECTED; fails on y method)
  atk_8  negated test `labelColor ≠ "inherit"` then swapped       -> exit 1 (REJECTED)
No terminating wrong impl verifies. The postcondition `ensures out = offsetColor tickColor labelColor` is a TOTAL equality with no preconditions, so it pins the output exactly for any terminating impl.

### 2. Positive controls
pos_ctrl.lean (byte-identical Solution) -> exit 0. pos_ctrl_match.lean (STRUCTURALLY DISTINCT correct impl using `match labelColor with | "inherit" => tickColor | _ => labelColor`, same_spec=True) -> exit 0. Spec is satisfiable, non-vacuous, tight.

### 3. DIVERGENCE PROBE (atk_9) — the one verifying wrong impl, EXECUTED through harness
atk_9.lean impl (x-axis): `let mut r := tickColor; while true do r := r; return r`; y-axis correct. same_spec=True. `bash scripts/lean_verify.sh atk_9.lean` -> exit 0 (VERIFIES). It verifies VACUOUSLY: under `set_option loom.semantics.termination "partial"` a non-terminating program satisfies any postcondition (verifier output: 'Invariant annotations are not specified, so the loop invariant is assumed to be just True'; the `simp only [offsetColor] <;> split <;> simp_all` tactics are reported 'never executed').

Faithful refined patch materialized at patch_atk9.diff (verified to `patch -p1` cleanly against real base-commit axis.py extracted from the eval image): x-site becomes `_atk9_xtick_color = mpl.rcParams['xtick.color']` followed by `while True: _atk9_xtick_color = _atk9_xtick_color` before `offsetText.set(..., color=_atk9_xtick_color)`; y-site is the gold selection. EXECUTED via harness.run_resolve twice (run_ids sbu-eqrev-ayp27-atk9 / -atk9b) AND once raw (run_id sbu-eqrev-ayp27-atk9-raw, timeout=300, dir preserved). Raw run_instance.log: patch 'Applied ... cleanly', eval.sh written, then `pytest -rA lib/matplotlib/tests/test_axes.py` -> 'collected 854 items' -> HANG -> 'EvaluationError: matplotlib__matplotlib-25287: Test timed out after 300 seconds'. NO report.json produced.

Under run_resolve this surfaces as resolved=False, completed=False, note='no report ... harness error'. => atk_9 does NOT satisfy the derivation's BROKEN condition, which is `r.completed and not r.resolved` (build_one.py _derive_audit_verdict). A diverging patch TIMES OUT (completed=False) and is routed to inconclusive_hits, never to a completed-and-not-resolved fail. The harness cannot grade non-termination as 'did not resolve'. Therefore atk_9 is NOT an admissible operational counterexample and is deliberately NOT listed among the counting attacks (listing it would only fail-close the gate to INCONCLUSIVE on a ground unrelated to this bundle's refinement fidelity). It is a SYSTEMIC partial-correctness artifact: 401/500 velvet bundles use `"partial"` termination (spec_guide.md sanctions it), so a divergence 'escape' would nominally apply board-wide and is out of scope for refinement-fidelity G-EQ.

### 4. Harness validation
Gold patch.diff run through run_resolve (run_id sbu-resolve...matplotlib-25287-dfab8bf8f1): resolved=True, FAIL_TO_PASS test_xaxis_offsetText_color + test_yaxis_offsetText_color both success. Confirms the harness/image are functional so a genuine completed-and-not-resolved would have been observable.

### 5. REFINEMENT.MD AUDIT (protocol step 3)
All legs R or I, ZERO kind-3, no axioms, no A-references (§C; meta axioms:[]). A1/A2/A4,B1/B2/B4 = R (str<->String; the unchanged set/get-color continuation is identity-on-content, G-CONF-exercised, not assumed). A3/B3 = I: the color-selection decision (the op that genuinely changed) is DEEP-modeled as `offsetColor t l = if l="inherit" then t else l`, corresponding exactly to gold `tick_color = (color if labelcolor=='inherit' else labelcolor)` at XAxis._init (lib/matplotlib/axis.py:2252) and YAxis._init (:2516). No A-leg to validate; correspondence holds. prepatch_reproduced: atk_1 reproduces the always-tickColor prepatch bug and correctly FAILS verification (matches bundled Solution_prepatch_1/2).

VERDICT: G-EQ = SOUND. ≥5 same-spec terminating attacks run, none breaks the spec; the only verifying impl is a vacuous divergence whose faithful patch times out (inconclusive, not completed-and-not-resolved) — a systemic partial-correctness property, not a refinement defect; positive control(s) verify; refinement.md is R/I-clean with faithful model<->patch correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_ctrl_match.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies (the total-equality postcondition out = offsetColor tickColor labelColor fully pins the output). The only verifying wrong impl is a NON-TERMINATING one (atk_9), whose faithful patch TIMES OUT under the harness (completed=False, INCONCLUSIVE) rather than being graded completed AND not-resolved, so it does not meet the operational verify-not-correct (BROKEN) bar. See notes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl_match.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed pure decision
--  over two configured color settings — the axis's tick color and its tick-label
--  color — yielding the color used to paint the secondary exponent (offset) text
--  for that axis. The downstream consumer that actually paints the text with the
--  chosen color is an UNCHANGED continuation reached identically on both branches,
--  so nothing about it is assumed: it is neither consumed as a contract nor
--  deep-modeled. There is no `axiom` declaration and no A-reference. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The color used to paint an axis's secondary exponent (offset) text, given the
   axis's tick color and its tick-label color.

   A tick-label color of the sentinel value "inherit" means "no distinct label
   color was configured — take the color from the tick color." Any other value
   is an explicitly configured label color and governs directly.

   This is the single behaviour at issue: the exponent text must follow
   the configured tick-LABEL color, falling back to the tick color only when the
   label color is left at the inherit sentinel — rather than always following the
   tick color and ignoring an explicitly configured label color. Grounded
   entirely in the two input color settings (directive 8): the result is one of
   them, selected by whether the label color is the inherit sentinel. -/
def offsetColor (tickColor labelColor : String) : String :=
  if labelColor = "inherit" then tickColor else labelColor
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the color of the secondary exponent (offset) text shown at the end
   of the horizontal axis. `tickColor` is the axis's configured tick color and
   `labelColor` is its configured tick-label color; both are read-only color
   settings (neither is `mut`) and neither is altered.

   Desired behaviour: an explicitly configured tick-label color governs the
   exponent text directly; the inherit sentinel falls back to — and therefore
   follows — the tick color. Always using the tick color, ignoring a configured
   label color, is the defect this pins out. -/
method xAxisOffsetColor (tickColor : String) (labelColor : String)
    return (out : String)
  ensures out = offsetColor tickColor labelColor
  do
    -- impl-start
    match labelColor with
    | "inherit" => return tickColor
    | _ => return labelColor
    -- impl-end

prove_correct xAxisOffsetColor by
  loom_solve <;> simp only [offsetColor] <;> split <;> simp_all

/- Determine the color of the secondary exponent (offset) text shown at the end
   of the vertical axis. Same desired behaviour as the horizontal axis: the
   configured tick-label color governs, and the inherit sentinel falls back to
   the tick color. `tickColor` and `labelColor` are read-only color settings
   (neither `mut`); neither is altered. -/
method yAxisOffsetColor (tickColor : String) (labelColor : String)
    return (out : String)
  ensures out = offsetColor tickColor labelColor
  do
    -- impl-start
    match labelColor with
    | "inherit" => return tickColor
    | _ => return labelColor
    -- impl-end

prove_correct yAxisOffsetColor by
  loom_solve <;> simp only [offsetColor] <;> split <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Verifier: scripts/lean_verify.sh.

### 1. TERMINATING WRONG-IMPL BATTERY (8 distinct, all same_spec=True)
Command per file: `bash scripts/lean_verify.sh <f>.lean`. same_spec via swebench_unified.markers.same_spec (velvet) = True for ALL.
  atk_1  both axes `return tickColor` (= prepatch bug / control-flow) -> exit 1 (REJECTED; error: simp_all made no progress on explicit-label clause)
  atk_2  both `return labelColor` (ungrounded echo of one input)      -> exit 1 (REJECTED; unsolved on inherit branch)
  atk_3  both branches swapped                                        -> exit 1 (REJECTED)
  atk_4  both `return ""` (partial-domain/empty)                      -> exit 1 (REJECTED)
  atk_5  sentinel tests tickColor instead of labelColor (boundary)    -> exit 1 (REJECTED)
  atk_6  sentinel string typo "inherited" (boundary)                  -> exit 1 (REJECTED)
  atk_7  correct x, buggy y `return tickColor` (mixed-axis)           -> exit 1 (REJECTED; fails on y method)
  atk_8  negated test `labelColor ≠ "inherit"` then swapped       -> exit 1 (REJECTED)
No terminating wrong impl verifies. The postcondition `ensures out = offsetColor tickColor labelColor` is a TOTAL equality with no preconditions, so it pins the output exactly for any terminating impl.

### 2. Positive controls
pos_ctrl.lean (byte-identical Solution) -> exit 0. pos_ctrl_match.lean (STRUCTURALLY DISTINCT correct impl using `match labelColor with | "inherit" => tickColor | _ => labelColor`, same_spec=True) -> exit 0. Spec is satisfiable, non-vacuous, tight.

### 3. DIVERGENCE PROBE (atk_9) — the one verifying wrong impl, EXECUTED through harness
atk_9.lean impl (x-axis): `let mut r := tickColor; while true do r := r; return r`; y-axis correct. same_spec=True. `bash scripts/lean_verify.sh atk_9.lean` -> exit 0 (VERIFIES). It verifies VACUOUSLY: under `set_option loom.semantics.termination "partial"` a non-terminating program satisfies any postcondition (verifier output: 'Invariant annotations are not specified, so the loop invariant is assumed to be just True'; the `simp only [offsetColor] <;> split <;> simp_all` tactics are reported 'never executed').

Faithful refined patch materialized at patch_atk9.diff (verified to `patch -p1` cleanly against real base-commit axis.py extracted from the eval image): x-site becomes `_atk9_xtick_color = mpl.rcParams['xtick.color']` followed by `while True: _atk9_xtick_color = _atk9_xtick_color` before `offsetText.set(..., color=_atk9_xtick_color)`; y-site is the gold selection. EXECUTED via harness.run_resolve twice (run_ids sbu-eqrev-ayp27-atk9 / -atk9b) AND once raw (run_id sbu-eqrev-ayp27-atk9-raw, timeout=300, dir preserved). Raw run_instance.log: patch 'Applied ... cleanly', eval.sh written, then `pytest -rA lib/matplotlib/tests/test_axes.py` -> 'collected 854 items' -> HANG -> 'EvaluationError: matplotlib__matplotlib-25287: Test timed out after 300 seconds'. NO report.json produced.

Under run_resolve this surfaces as resolved=False, completed=False, note='no report ... harness error'. => atk_9 does NOT satisfy the derivation's BROKEN condition, which is `r.completed and not r.resolved` (build_one.py _derive_audit_verdict). A diverging patch TIMES OUT (completed=False) and is routed to inconclusive_hits, never to a completed-and-not-resolved fail. The harness cannot grade non-termination as 'did not resolve'. Therefore atk_9 is NOT an admissible operational counterexample and is deliberately NOT listed among the counting attacks (listing it would only fail-close the gate to INCONCLUSIVE on a ground unrelated to this bundle's refinement fidelity). It is a SYSTEMIC partial-correctness artifact: 401/500 velvet bundles use `"partial"` termination (spec_guide.md sanctions it), so a divergence 'escape' would nominally apply board-wide and is out of scope for refinement-fidelity G-EQ.

### 4. Harness validation
Gold patch.diff run through run_resolve (run_id sbu-resolve...matplotlib-25287-dfab8bf8f1): resolved=True, FAIL_TO_PASS test_xaxis_offsetText_color + test_yaxis_offsetText_color both success. Confirms the harness/image are functional so a genuine completed-and-not-resolved would have been observable.

### 5. REFINEMENT.MD AUDIT (protocol step 3)
All legs R or I, ZERO kind-3, no axioms, no A-references (§C; meta axioms:[]). A1/A2/A4,B1/B2/B4 = R (str<->String; the unchanged set/get-color continuation is identity-on-content, G-CONF-exercised, not assumed). A3/B3 = I: the color-selection decision (the op that genuinely changed) is DEEP-modeled as `offsetColor t l = if l="inherit" then t else l`, corresponding exactly to gold `tick_color = (color if labelcolor=='inherit' else labelcolor)` at XAxis._init (lib/matplotlib/axis.py:2252) and YAxis._init (:2516). No A-leg to validate; correspondence holds. prepatch_reproduced: atk_1 reproduces the always-tickColor prepatch bug and correctly FAILS verification (matches bundled Solution_prepatch_1/2).

VERDICT: G-EQ = SOUND. ≥5 same-spec terminating attacks run, none breaks the spec; the only verifying impl is a vacuous divergence whose faithful patch times out (inconclusive, not completed-and-not-resolved) — a systemic partial-correctness property, not a refinement defect; positive control(s) verify; refinement.md is R/I-clean with faithful model<->patch correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of velvet spec for matplotlib__matplotlib-25287. (1) Spec region byte-identity: swebench_unified.markers.same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True under the velvet backend; the frozen region (offsetColor def + both method/ensures headers) is signature-identical across variants. (2) Model↔repo fidelity: the modeled rule offsetColor(tickColor,labelColor) = (if labelColor="inherit" then tickColor else labelColor) is a character-for-character transliteration of the gold patch's `tick_color = xtick.color if xtick.labelcolor=='inherit' else xtick.labelcolor` at XAxis._init (axis.py:2252) and the analogous YAxis._init (2516). (3) The single R-refinement trust point — that offsetText.set(color=...)/get_color() is verbatim identity on the color spec — was tested against real matplotlib and holds: named colors, hex (upper/lower, #abc/#abcdef), grayscale floats '0.5'/'0.50'/'1.0', and C0/xkcd:/tab: forms all round-trip identically through rcParams assignment and get_color(); invalid specs (e.g. 'red ') raise on rcParam assignment and thus lie outside the modeled valid-color domain. No rcParams normalization observed on any tested valid input. (4) Discrimination: Solution.lean verifies (lean_verify exit 0); both prepatches FAIL prove_correct on the explicit-label clause (simp_all made no progress), confirming the spec is strong yet not over-strong. No diverging input found between the modeled function and the real patched callee over the modeled domain (valid matplotlib color-spec strings + the 'inherit' sentinel).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage / gold-reconstruction judgment for matplotlib__matplotlib-25287 (velvet).

Spec-region byte-identity verified: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch_1.lean) = True and same_spec(..., Solution_prepatch_2.lean) = True. Spec view is stable across the pre-patch variants.

What the spec view discloses: the pure region defines offsetColor tickColor labelColor = if labelColor = "inherit" then tickColor else labelColor, and the docstrings state the exponent (offset) text must follow the configured tick-LABEL color, falling back to the tick color only when the label color is the 'inherit' sentinel, applied at both the horizontal and vertical axis sites. This is exactly the gold edit (patch.diff: color=tick_color where tick_color = xtick.color if xtick.labelcolor=='inherit' else xtick.labelcolor, and the ytick analogue).

However, the controlling test is whether the spec leaks beyond the PUBLIC problem_statement (not hints_text). It does NOT. The public problem_statement already contains the complete fix verbatim: the title 'offsetText is colored based on tick.color instead of tick.labelcolor', and the reporter's own suggested patch for both axes — color=mpl.rcParams['xtick.color'] if mpl.rcParams['xtick.labelcolor']=='inherit' else mpl.rcParams['xtick.labelcolor'] (and the ytick.* analogue). Every element the spec view reveals (the 'inherit' sentinel, the fall-back semantics, the else-branch taking the explicit labelcolor, the two-site x/y structure) is already fully public in problem_statement. hints_text is only PR-coordination chatter and carries no fix content.

Since the gold edit is fully reconstructable from the public problem_statement alone, the spec view provides no gold-reconstruction advantage over the public baseline. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.