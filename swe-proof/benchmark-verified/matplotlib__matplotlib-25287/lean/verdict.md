# P2 adversarial audit — matplotlib__matplotlib-25287

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,9 @@
 -- impl-start
 def implementation_horizOffsetTextColor
     (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
-  -- Decide the offset text's color from the label-color setting, falling back
-  -- to the tick-mark color only when that setting defers to the ticks.
+  -- ATTACK 1 (prepatch bug / partial-domain): always the tick-mark color,
+  -- ignoring the label-color setting entirely.
   let mut chosen := tickColor
-  match labelColor with
-  | none   => chosen := tickColor
-  | some c => chosen := c
   return chosen
 -- impl-end
 
@@ -71,7 +68,12 @@
         (implementation_horizOffsetTextColor tickColor labelColor) := by
   intro tickColor labelColor
   unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
-  cases labelColor <;> rfl
+  first
+    | rfl
+    | (cases labelColor <;> rfl)
+    | (cases labelColor <;> simp [Option.getD])
+    | (simp [Option.getD, Id.run])
+    | (cases labelColor <;> aesop)
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,13 +55,10 @@
 -- impl-start
 def implementation_horizOffsetTextColor
     (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
-  -- Decide the offset text's color from the label-color setting, falling back
-  -- to the tick-mark color only when that setting defers to the ticks.
-  let mut chosen := tickColor
+  -- ATTACK 2 (boundary): explicitly discard the label color and keep ticks.
   match labelColor with
-  | none   => chosen := tickColor
-  | some c => chosen := c
-  return chosen
+  | none   => return tickColor
+  | some _ => return tickColor
 -- impl-end
 
 -- proof-start
@@ -71,7 +68,12 @@
         (implementation_horizOffsetTextColor tickColor labelColor) := by
   intro tickColor labelColor
   unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
-  cases labelColor <;> rfl
+  first
+    | rfl
+    | (cases labelColor <;> rfl)
+    | (cases labelColor <;> simp [Option.getD])
+    | (simp [Option.getD, Id.run])
+    | (cases labelColor <;> aesop)
 -- proof-end
 
 -- post-conditions-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,13 @@
 -- impl-start
 def implementation_horizOffsetTextColor
     (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
-  -- Decide the offset text's color from the label-color setting, falling back
-  -- to the tick-mark color only when that setting defers to the ticks.
+  -- ATTACK 3 (control-flow-effect): compute the right value into `chosen`,
+  -- then a stray unconditional overwrite clobbers it back to the tick color.
   let mut chosen := tickColor
   match labelColor with
   | none   => chosen := tickColor
   | some c => chosen := c
+  chosen := tickColor
   return chosen
 -- impl-end
 
@@ -71,7 +72,12 @@
         (implementation_horizOffsetTextColor tickColor labelColor) := by
   intro tickColor labelColor
   unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
-  cases labelColor <;> rfl
+  first
+    | rfl
+    | (cases labelColor <;> rfl)
+    | (cases labelColor <;> simp [Option.getD])
+    | (simp [Option.getD, Id.run])
+    | (cases labelColor <;> aesop)
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,13 +55,9 @@
 -- impl-start
 def implementation_horizOffsetTextColor
     (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
-  -- Decide the offset text's color from the label-color setting, falling back
-  -- to the tick-mark color only when that setting defers to the ticks.
-  let mut chosen := tickColor
-  match labelColor with
-  | none   => chosen := tickColor
-  | some c => chosen := c
-  return chosen
+  -- ATTACK 4 (ungrounded-oracle echo): echoes getD but drops the real setting,
+  -- feeding a constant `none` so it always yields the tick color.
+  return (none : Option Color).getD tickColor
 -- impl-end
 
 -- proof-start
@@ -71,7 +67,12 @@
         (implementation_horizOffsetTextColor tickColor labelColor) := by
   intro tickColor labelColor
   unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
-  cases labelColor <;> rfl
+  first
+    | rfl
+    | (cases labelColor <;> rfl)
+    | (cases labelColor <;> simp [Option.getD])
+    | (simp [Option.getD, Id.run])
+    | (cases labelColor <;> aesop)
 -- proof-end
 
 -- post-conditions-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,13 +55,11 @@
 -- impl-start
 def implementation_horizOffsetTextColor
     (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
-  -- Decide the offset text's color from the label-color setting, falling back
-  -- to the tick-mark color only when that setting defers to the ticks.
-  let mut chosen := tickColor
-  match labelColor with
-  | none   => chosen := tickColor
-  | some c => chosen := c
-  return chosen
+  -- ATTACK 5 (control-flow): test isSome but both arms are wrong on `some`.
+  if labelColor.isSome then
+    return tickColor
+  else
+    return labelColor.getD tickColor
 -- impl-end
 
 -- proof-start
@@ -71,7 +69,12 @@
         (implementation_horizOffsetTextColor tickColor labelColor) := by
   intro tickColor labelColor
   unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
-  cases labelColor <;> rfl
+  first
+    | rfl
+    | (cases labelColor <;> rfl)
+    | (cases labelColor <;> simp [Option.getD])
+    | (simp [Option.getD, Id.run])
+    | (cases labelColor <;> aesop)
 -- proof-end
 
 -- post-conditions-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,13 +55,9 @@
 -- impl-start
 def implementation_horizOffsetTextColor
     (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
-  -- Decide the offset text's color from the label-color setting, falling back
-  -- to the tick-mark color only when that setting defers to the ticks.
-  let mut chosen := tickColor
-  match labelColor with
-  | none   => chosen := tickColor
-  | some c => chosen := c
-  return chosen
+  -- ATTACK 6 (partial-domain flip): correct only on the `none` sentinel; on an
+  -- explicit color it returns the WRONG input (falls back to ticks anyway).
+  return labelColor.elim tickColor (fun _ => tickColor)
 -- impl-end
 
 -- proof-start
@@ -71,7 +67,12 @@
         (implementation_horizOffsetTextColor tickColor labelColor) := by
   intro tickColor labelColor
   unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
-  cases labelColor <;> rfl
+  first
+    | rfl
+    | (cases labelColor <;> rfl)
+    | (cases labelColor <;> simp [Option.getD])
+    | (simp [Option.getD, Id.run])
+    | (cases labelColor <;> aesop)
 -- proof-end
 
 -- post-conditions-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the color of an axis's offset text (the small exponent / multiplier
label drawn at the end of a numeric axis).

An axis carries two independent color settings that can govern its annotations:

  * a tick-mark color — the color used for the tick marks themselves;
  * a label-color setting — the color used for the tick *labels*. This setting
    may instead hold a distinguished sentinel value meaning "I have no opinion;
    defer to the tick-mark color." We model that sentinel as the absence of a
    value (`none`); an explicit choice is `some c`.

The offset text is a tick label, so its color must follow the label-color
setting, not the tick-mark color. The desired behavior: when the label-color
setting holds an explicit color, the offset text takes that color; when the
label-color setting is at its defer-to-ticks sentinel, the offset text falls
back to the tick-mark color. In particular, when an explicit label color is set
the offset text must NOT be left at the tick-mark color.

Two coordinate axes (the horizontal and the vertical one) carry independent
copies of these two settings and resolve the offset-text color the same way, so
each direction is modeled by its own function with the identical contract.

A color is an opaque token: its internal structure is irrelevant here — what
matters is solely WHICH of the two input colors ends up on the offset text.
-/

-- axioms-start
/-- An opaque color token. Only the IDENTITY of the chosen color matters to the
behavior modeled here (which of the two candidate colors the offset text ends up
with), never how a color is represented or rendered. -/
opaque Color : Type
-- axioms-end

-- pure-start
-- No additional pure helpers are required: each modeled behavior is the single
-- choice between the explicit label color and the tick-mark fallback.
-- pure-end

-- post-conditions-start
/-- Resolving the offset-text color for the horizontal axis. The result is fully
pinned to the two inputs: it equals the explicit label color when one is set
(`labelColor = some c` ⇒ result `= c`), and falls back to the tick-mark color
when the label-color setting is at its defer-to-ticks sentinel
(`labelColor = none` ⇒ result `= tickColor`). No part of the result is left
free, and no color outside the two inputs may appear. -/
def problem_spec_horizOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) (result : Color) : Prop :=
  result = labelColor.getD tickColor
-- post-conditions-end

-- impl-start
def implementation_horizOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
  -- Decide the offset text's color from the label-color setting, falling back
  -- to the tick-mark color only when that setting defers to the ticks.
  let mut chosen := tickColor
  match labelColor with
  | none   => chosen := tickColor
  | some c => chosen := c
  return chosen
-- impl-end

-- proof-start
theorem correct_horizOffsetTextColor :
    ∀ (tickColor : Color) (labelColor : Option Color),
      problem_spec_horizOffsetTextColor tickColor labelColor
        (implementation_horizOffsetTextColor tickColor labelColor) := by
  intro tickColor labelColor
  unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
  cases labelColor <;> rfl
-- proof-end

-- post-conditions-start
/-- Resolving the offset-text color for the vertical axis. Symmetric to the
horizontal case: the result equals the explicit label color when one is set, and
falls back to the tick-mark color when the label-color setting is at its
defer-to-ticks sentinel — the result is fully pinned to the two inputs. -/
def problem_spec_vertOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) (result : Color) : Prop :=
  result = labelColor.getD tickColor
-- post-conditions-end

-- impl-start
def implementation_vertOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
  -- Decide the offset text's color from the label-color setting, falling back
  -- to the tick-mark color only when that setting defers to the ticks.
  let mut chosen := tickColor
  match labelColor with
  | none   => chosen := tickColor
  | some c => chosen := c
  return chosen
-- impl-end

-- proof-start
theorem correct_vertOffsetTextColor :
    ∀ (tickColor : Color) (labelColor : Option Color),
      problem_spec_vertOffsetTextColor tickColor labelColor
        (implementation_vertOffsetTextColor tickColor labelColor) := by
  intro tickColor labelColor
  unfold problem_spec_vertOffsetTextColor implementation_vertOffsetTextColor
  cases labelColor <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional equality `result = labelColor.getD tickColor` over an OPAQUE `Color` type, for both horiz and vert axes (byte-identical contracts). This fully pins the output; the only Color values an impl can construct are `tickColor` and a bound `c` from `some c`, and with Color opaque `tickColor = c` is unprovable for distinct free variables. Therefore any impl deviating from getD leaves an unclosable goal.

PROTOCOL (all in /tmp scratch dir; same_spec=True verified for all 7 files via swebench_unified.markers.same_spec on the lean backend):
- POSITIVE CONTROL pos_control.lean = shipped Solution.lean: `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (clean, no error/sorry). `#print axioms correct_horizOffsetTextColor`/`correct_vertOffsetTextColor` (axcheck.lean, exit 0) => BOTH 'does not depend on any axioms' (clean axioms).
- PREPATCH BUG reproduced: shipped Solution_prepatch.lean (horiz, prepatch_h.lean) exit 1 and Solution_prepatch_2.lean (vert, prepatch_v.lean) exit 1 -- both fail on the `some c` goal (impl returns tickColor while spec needs (some c).getD tickColor). atk_1 is the same horiz prepatch bug and also fails (exit 1).
- 6 DISTINCT same-spec wrong impls, each with an AGGRESSIVE proof block `first | rfl | (cases labelColor <;> rfl) | (cases labelColor <;> simp [Option.getD]) | (simp [Option.getD, Id.run]) | (cases labelColor <;> aesop)` (i.e. NOT just the gold `cases <;> rfl`) to ensure no closing proof is missed:
  atk_1 partial-domain/prepatch: `return tickColor` (ignores labelColor) -> exit 1, unsolved `tickColor = val`.
  atk_2 boundary: `match labelColor | none => tickColor | some _ => tickColor` -> exit 1.
  atk_3 control-flow-effect: computes correct `chosen` then stray unconditional overwrite `chosen := tickColor` clobbers it -> exit 1.
  atk_4 ungrounded-oracle echo: `(none : Option Color).getD tickColor` (echoes getD but feeds constant none) -> exit 1.
  atk_5 control-flow: `if labelColor.isSome then tickColor else labelColor.getD tickColor` (wrong on some) -> exit 1.
  atk_6 partial-domain flip: `labelColor.elim tickColor (fun _ => tickColor)` (correct only on none) -> exit 1.
  Every failure is the SAME genuine unsolved goal: `case some / tickColor val : Color / |- tickColor = val` -- unprovable because Color is opaque. Verification commands run concurrently (<=4 at a time): batch1 {pos_control,atk_1,atk_2,atk_3}, batch2 {atk_4,atk_5,atk_6}.

STEP 2 (materialize+resolve) is VACUOUS: no wrong impl closed with clean axioms, so there is no verifying attack to build a faithful refined patch from; patches={}.

REFINEMENT AUDIT: refinement.md legs are all R / I (op-correspondence rows tagged I, R, R/I; explicit 'no A row'). meta.json axioms=[] and deep_model_references=[]; axiom_check.py is a documented skip stub (no consumed callee axiom, no A-reference). No kind-3 legs. A-leg correspondence obligation is therefore vacuous and consistent. mapping.md 'inherit' string sentinel <-> none / explicit color <-> some v bijection matches `tick_color = rc[color] if rc[labelcolor]=='inherit' else rc[labelcolor]` (== labelColor.getD tickColor).

CONCLUSION: verify => correct holds; no verify-but-incorrect impl exists for this spec. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the color of an axis's offset text (the small exponent / multiplier
label drawn at the end of a numeric axis).

An axis carries two independent color settings that can govern its annotations:

  * a tick-mark color — the color used for the tick marks themselves;
  * a label-color setting — the color used for the tick *labels*. This setting
    may instead hold a distinguished sentinel value meaning "I have no opinion;
    defer to the tick-mark color." We model that sentinel as the absence of a
    value (`none`); an explicit choice is `some c`.

The offset text is a tick label, so its color must follow the label-color
setting, not the tick-mark color. The desired behavior: when the label-color
setting holds an explicit color, the offset text takes that color; when the
label-color setting is at its defer-to-ticks sentinel, the offset text falls
back to the tick-mark color. In particular, when an explicit label color is set
the offset text must NOT be left at the tick-mark color.

Two coordinate axes (the horizontal and the vertical one) carry independent
copies of these two settings and resolve the offset-text color the same way, so
each direction is modeled by its own function with the identical contract.

A color is an opaque token: its internal structure is irrelevant here — what
matters is solely WHICH of the two input colors ends up on the offset text.
-/

-- axioms-start
/-- An opaque color token. Only the IDENTITY of the chosen color matters to the
behavior modeled here (which of the two candidate colors the offset text ends up
with), never how a color is represented or rendered. -/
opaque Color : Type
-- axioms-end

-- pure-start
-- No additional pure helpers are required: each modeled behavior is the single
-- choice between the explicit label color and the tick-mark fallback.
-- pure-end

-- post-conditions-start
/-- Resolving the offset-text color for the horizontal axis. The result is fully
pinned to the two inputs: it equals the explicit label color when one is set
(`labelColor = some c` ⇒ result `= c`), and falls back to the tick-mark color
when the label-color setting is at its defer-to-ticks sentinel
(`labelColor = none` ⇒ result `= tickColor`). No part of the result is left
free, and no color outside the two inputs may appear. -/
def problem_spec_horizOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) (result : Color) : Prop :=
  result = labelColor.getD tickColor
-- post-conditions-end

-- impl-start
def implementation_horizOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
  -- Decide the offset text's color from the label-color setting, falling back
  -- to the tick-mark color only when that setting defers to the ticks.
  let mut chosen := tickColor
  match labelColor with
  | none   => chosen := tickColor
  | some c => chosen := c
  return chosen
-- impl-end

-- proof-start
theorem correct_horizOffsetTextColor :
    ∀ (tickColor : Color) (labelColor : Option Color),
      problem_spec_horizOffsetTextColor tickColor labelColor
        (implementation_horizOffsetTextColor tickColor labelColor) := by
  intro tickColor labelColor
  unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
  cases labelColor <;> rfl
-- proof-end

-- post-conditions-start
/-- Resolving the offset-text color for the vertical axis. Symmetric to the
horizontal case: the result equals the explicit label color when one is set, and
falls back to the tick-mark color when the label-color setting is at its
defer-to-ticks sentinel — the result is fully pinned to the two inputs. -/
def problem_spec_vertOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) (result : Color) : Prop :=
  result = labelColor.getD tickColor
-- post-conditions-end

-- impl-start
def implementation_vertOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
  -- Decide the offset text's color from the label-color setting, falling back
  -- to the tick-mark color only when that setting defers to the ticks.
  let mut chosen := tickColor
  match labelColor with
  | none   => chosen := tickColor
  | some c => chosen := c
  return chosen
-- impl-end

-- proof-start
theorem correct_vertOffsetTextColor :
    ∀ (tickColor : Color) (labelColor : Option Color),
      problem_spec_vertOffsetTextColor tickColor labelColor
        (implementation_vertOffsetTextColor tickColor labelColor) := by
  intro tickColor labelColor
  unfold problem_spec_vertOffsetTextColor implementation_vertOffsetTextColor
  cases labelColor <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional equality `result = labelColor.getD tickColor` over an OPAQUE `Color` type, for both horiz and vert axes (byte-identical contracts). This fully pins the output; the only Color values an impl can construct are `tickColor` and a bound `c` from `some c`, and with Color opaque `tickColor = c` is unprovable for distinct free variables. Therefore any impl deviating from getD leaves an unclosable goal.

PROTOCOL (all in /tmp scratch dir; same_spec=True verified for all 7 files via swebench_unified.markers.same_spec on the lean backend):
- POSITIVE CONTROL pos_control.lean = shipped Solution.lean: `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (clean, no error/sorry). `#print axioms correct_horizOffsetTextColor`/`correct_vertOffsetTextColor` (axcheck.lean, exit 0) => BOTH 'does not depend on any axioms' (clean axioms).
- PREPATCH BUG reproduced: shipped Solution_prepatch.lean (horiz, prepatch_h.lean) exit 1 and Solution_prepatch_2.lean (vert, prepatch_v.lean) exit 1 -- both fail on the `some c` goal (impl returns tickColor while spec needs (some c).getD tickColor). atk_1 is the same horiz prepatch bug and also fails (exit 1).
- 6 DISTINCT same-spec wrong impls, each with an AGGRESSIVE proof block `first | rfl | (cases labelColor <;> rfl) | (cases labelColor <;> simp [Option.getD]) | (simp [Option.getD, Id.run]) | (cases labelColor <;> aesop)` (i.e. NOT just the gold `cases <;> rfl`) to ensure no closing proof is missed:
  atk_1 partial-domain/prepatch: `return tickColor` (ignores labelColor) -> exit 1, unsolved `tickColor = val`.
  atk_2 boundary: `match labelColor | none => tickColor | some _ => tickColor` -> exit 1.
  atk_3 control-flow-effect: computes correct `chosen` then stray unconditional overwrite `chosen := tickColor` clobbers it -> exit 1.
  atk_4 ungrounded-oracle echo: `(none : Option Color).getD tickColor` (echoes getD but feeds constant none) -> exit 1.
  atk_5 control-flow: `if labelColor.isSome then tickColor else labelColor.getD tickColor` (wrong on some) -> exit 1.
  atk_6 partial-domain flip: `labelColor.elim tickColor (fun _ => tickColor)` (correct only on none) -> exit 1.
  Every failure is the SAME genuine unsolved goal: `case some / tickColor val : Color / |- tickColor = val` -- unprovable because Color is opaque. Verification commands run concurrently (<=4 at a time): batch1 {pos_control,atk_1,atk_2,atk_3}, batch2 {atk_4,atk_5,atk_6}.

STEP 2 (materialize+resolve) is VACUOUS: no wrong impl closed with clean axioms, so there is no verifying attack to build a faithful refined patch from; patches={}.

REFINEMENT AUDIT: refinement.md legs are all R / I (op-correspondence rows tagged I, R, R/I; explicit 'no A row'). meta.json axioms=[] and deep_model_references=[]; axiom_check.py is a documented skip stub (no consumed callee axiom, no A-reference). No kind-3 legs. A-leg correspondence obligation is therefore vacuous and consistent. mapping.md 'inherit' string sentinel <-> none / explicit color <-> some v bijection matches `tick_color = rc[color] if rc[labelcolor]=='inherit' else rc[labelcolor]` (== labelColor.getD tickColor).

CONCLUSION: verify => correct holds; no verify-but-incorrect impl exists for this spec. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for matplotlib__matplotlib-25287 (lean). Gold patch, both axes: tick_color = rc['*tick.color'] if rc['*tick.labelcolor']=='inherit' else rc['*tick.labelcolor']; passed as color= to offsetText.set. Spec models this as `result = labelColor.getD tickColor` with the mapping.md bijection: rc[color]->tickColor, rc[labelcolor]=='inherit' -> none, any other color value v -> some v. This is an exact functional match over the whole domain (none -> tickColor; some c -> c); no input diverges. 'inherit' is not itself a valid matplotlib color, so the sentinel/color partition is clean with no overlap. Horizontal and vertical functions are byte-symmetric, matching the two byte-symmetric X/Y hunks. VERIFICATION: (1) spec region byte-identical — swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True; (2) scripts/lean_verify.sh exit 0 (compiles, no sorry); (3) #print axioms correct_horizOffsetTextColor / correct_vertOffsetTextColor both report 'does not depend on any axioms' — proof is genuine, no sorryAx. Spec is neither too strong nor too weak: it fully pins the result to the two inputs, exactly as the patch does. No defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the spec view (spec_view of Solution.lean) against the SOLVER-VISIBLE problem_statement only (not hints_text). Findings:

1) Mechanical screen: leakage.screen(src, lean, patch, problem_statement) returns PASSED=True, no hard failures, no warnings. No diff markers, no patched file path (lib/matplotlib/axis.py), no gold-diff line reproduced, no bug/fix narration, no spec identifier echoing a patched repo symbol (spec names are problem_spec_horiz/vertOffsetTextColor / tickColor / labelColor — none touch the changed Python symbols).

2) Semantic (the part the lexical screen can miss): decisively NO-LEAKAGE because the public problem_statement ALREADY publishes the entire gold fix. The bug report is titled 'offsetText is colored based on tick.color instead of tick.labelcolor' and embeds the reporter's diff containing the exact gold logic: color=mpl.rcParams['xtick.color'] if mpl.rcParams['xtick.labelcolor']=='inherit' else mpl.rcParams['xtick.labelcolor'] (and the ytick.* twin). The actual gold patch is the same conditional hoisted into a tick_color local, for both XAxis._init and YAxis._init.

Everything the spec view discloses is a subset of that public content: (a) offset text color must follow the label-color setting not the tick-mark color; (b) the label-color setting has a defer-to-ticks sentinel = 'inherit' (modeled as none); (c) explicit label color wins else fall back to tick color; (d) two symmetric axes. The 'inherit' sentinel semantics and the two-way choice are literally in problem_statement's diff. The spec adds only faithful modeling abstraction (opaque Color, Option, getD) and reveals nothing about the gold EDIT (the tick_color hoist / which file / which call site) beyond what the reporter already made public.

Conclusion: the spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
