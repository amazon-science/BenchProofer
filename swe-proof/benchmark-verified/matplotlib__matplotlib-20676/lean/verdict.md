# P2 adversarial audit — matplotlib__matplotlib-20676

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_initialMarkers fully pins the output on both constructors of the 2-constructor SelectDirection type (horizontal -> result = xViewBounds; vertical -> result = yViewBounds), leaving no free output component. Every behaviorally-wrong impl is rejected by the proof; the only same-spec impl that verifies (atk_7) is behaviorally identical to gold and its faithful patch (= gold patch) resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,7 @@
 
 -- impl-start
 def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
-  let positions ←
-    if inp.axis = SelectDirection.horizontal then
-      pure inp.xViewBounds
-    else
-      pure inp.yViewBounds
+  let positions ← pure inp.selectorSpan
   return positions
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,9 +84,9 @@
 def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
   let positions ←
     if inp.axis = SelectDirection.horizontal then
+      pure inp.yViewBounds
+    else
       pure inp.xViewBounds
-    else
-      pure inp.yViewBounds
   return positions
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,12 +82,7 @@
 
 -- impl-start
 def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
-  let positions ←
-    if inp.axis = SelectDirection.horizontal then
-      pure inp.xViewBounds
-    else
-      pure inp.yViewBounds
-  return positions
+  return inp.xViewBounds
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,12 +82,7 @@
 
 -- impl-start
 def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
-  let positions ←
-    if inp.axis = SelectDirection.horizontal then
-      pure inp.xViewBounds
-    else
-      pure inp.yViewBounds
-  return positions
+  return inp.yViewBounds
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
     if inp.axis = SelectDirection.horizontal then
       pure inp.xViewBounds
     else
-      pure inp.yViewBounds
+      pure inp.selectorSpan
   return positions
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
 def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
   let positions ←
     if inp.axis = SelectDirection.horizontal then
-      pure inp.xViewBounds
+      pure (inp.xViewBounds.2, inp.xViewBounds.1)
     else
       pure inp.yViewBounds
   return positions
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -82,12 +82,7 @@
 
 -- impl-start
 def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
-  let positions ←
-    if inp.axis = SelectDirection.horizontal then
-      pure inp.xViewBounds
-    else
-      pure inp.yViewBounds
-  return positions
+  return initialMarkers inp
 -- impl-end
 
 -- proof-start
@@ -96,6 +91,6 @@
       problem_spec_initialMarkers inp
         (implementation_initialMarkers inp) := by
   intro inp
-  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [implementation_initialMarkers, Id.run, h, if_true, pure] <;> rfl
+  unfold problem_spec_initialMarkers implementation_initialMarkers initialMarkers
+  refine ⟨fun h => ?_, fun h => ?_⟩ <;> simp only [Id.run, h] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Placing the initial boundary markers of an interactive range selector.

An interactive one-dimensional range selector draws a pair of movable boundary
marker lines on a plotting axis. When the selector is first set up, those two
marker lines have to be given an initial pair of positions, expressed in the
axis' data coordinates along the selection direction (the horizontal axis for a
horizontal selector, the vertical axis for a vertical selector).

Each marker line is drawn at its given coordinate, and drawing a line at a
coordinate that lies outside the axis' current visible range would force the
visible range to grow to include it. The desired behavior is therefore that
setting up the selector must leave the axis' visible range exactly as it was: the
initial marker positions are chosen to be the axis' current view bounds (its
lower and upper visible limits) along the selection direction. Reading the marker
positions back then returns that same pair.

So the selected pair of initial marker positions equals:

  * the axis' current view bounds along the horizontal axis, for a horizontal
    selector;
  * the axis' current view bounds along the vertical axis, for a vertical
    selector.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The placement
-- is modeled DEEPLY as a pure selection between the two candidate coordinate
-- pairs (the axis' horizontal vs. vertical view bounds), governed only by the
-- selection direction, so no `opaque`/`axiom` callee contract is needed. The
-- marker container is an identity pass-through of the positions it is given
-- (reading them back returns the same pair), an `I` refinement, not an axiom.
-- axioms-end

-- pure-start
/-- The direction along which the range selector operates. -/
inductive SelectDirection where
  | horizontal
  | vertical
deriving DecidableEq, Repr

/-- The inputs the initial-position choice reads:

* `axis` — the selection direction;
* `selectorSpan` — the selector's own current span (its lower/upper extent);
* `xViewBounds` — the axis' current view bounds (lower, upper) along the
  horizontal axis;
* `yViewBounds` — the axis' current view bounds along the vertical axis.

Coordinates are exact rationals: the choice never does arithmetic on them, it
only selects which existing pair to use, so the exact ordered field keeps
equality decidable. -/
structure MarkerSetup where
  axis : SelectDirection
  selectorSpan : ℚ × ℚ
  xViewBounds : ℚ × ℚ
  yViewBounds : ℚ × ℚ
deriving Repr

/-- The initial marker positions: the axis' current view bounds along the
selection direction. -/
def initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=
  match inp.axis with
  | SelectDirection.horizontal => inp.xViewBounds
  | SelectDirection.vertical => inp.yViewBounds
-- pure-end

-- post-conditions-start
/-- The pair of initial marker positions is exactly the axis' current view bounds
along the selection direction — the horizontal view bounds for a horizontal
selector, the vertical view bounds for a vertical selector. Pinning it to a view
bound (rather than the selector's own span) is what leaves the axis' visible
range undisturbed. -/
def problem_spec_initialMarkers
    (inp : MarkerSetup) (result : ℚ × ℚ) : Prop :=
  (inp.axis = SelectDirection.horizontal → result = inp.xViewBounds) ∧
  (inp.axis = SelectDirection.vertical → result = inp.yViewBounds)
-- post-conditions-end

-- impl-start
def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
  let positions ←
    if inp.axis = SelectDirection.horizontal then
      pure inp.xViewBounds
    else
      pure inp.yViewBounds
  return positions
-- impl-end

-- proof-start
theorem correct_initialMarkers :
    ∀ (inp : MarkerSetup),
      problem_spec_initialMarkers inp
        (implementation_initialMarkers inp) := by
  intro inp
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    simp only [implementation_initialMarkers, Id.run, h, if_true, pure] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True for all 8 files (verified via swebench_unified.markers.same_spec, lean backend). Verification command: `bash scripts/lean_verify.sh <file>`.

### ATTACK RESULTS (all same_spec=True):
- atk_1 (prepatch bug: `pure inp.selectorSpan` unconditionally; == positions=self.extents): exit 1, does NOT verify. PREPATCH REPRODUCED — spec discriminates the reported bug (span (0,0) vs view bounds).
- atk_2 (swapped branches: horizontal->yViewBounds, vertical->xViewBounds): exit 1, does NOT verify.
- atk_3 (ungrounded/always xViewBounds, ignores direction): exit 1, does NOT verify (fails vertical clause).
- atk_4 (always yViewBounds): exit 1, does NOT verify (fails horizontal clause).
- atk_5 (partial-domain: horizontal ok, vertical->selectorSpan): exit 1, does NOT verify.
- atk_6 (boundary/tuple-swap: horizontal->(xViewBounds.2, xViewBounds.1), vertical ok): exit 1, does NOT verify.
- atk_7 (behavioral echo: `return initialMarkers inp`, == gold behavior): exit 0, VERIFIES, `#print axioms correct_initialMarkers` = [propext] (clean, no sorry, no custom axioms).
- atk_pc (gold impl, positive control): exit 0, verifies, axioms=[propext].

RESOLVE (protocol step 2, EXECUTED): atk_7 is behaviorally identical to gold, so its faithful refined patch IS the gold patch. run_resolve('matplotlib__matplotlib-20676', <gold patch>) => resolved=True, completed=True, note='resolved'. So the ONLY verifying same-spec attack has a materialized faithful patch that DOES resolve. No verify⇏correct gap.

REFINEMENT AUDIT (step 3): refinement.md legs = op1 R, op2 R, op3 I. No A-legs (axioms region byte-empty; G-AX skip is justified — the changed decision, which coordinate pair becomes the initial positions, is modeled DEEPLY as a pure selection on self.direction; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision). No kind-3 legs. The R legs (carried observations ax.get_xbound()/ax.get_ybound() -> xViewBounds/yViewBounds) and the I leg (ToolLineHandles pass-through identity, .positions == list(positions)) correspond to the real UNCHANGED callees at widgets.py:2158-2162. G-CONF (conformance_check.py, seed 20676, 120000 fuzz + edge cases) mechanically covers the R/I legs. Mapping.md callee provenance is consistent.

CONCLUSION: The spec is a maximally-tight full pin over a 2-constructor discriminant; no same-spec wrong impl both verifies AND fails to resolve. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_initialMarkers fully pins the output on both constructors of the 2-constructor SelectDirection type (horizontal -> result = xViewBounds; vertical -> result = yViewBounds), leaving no free output component. Every behaviorally-wrong impl is rejected by the proof; the only same-spec impl that verifies (atk_7) is behaviorally identical to gold and its faithful patch (= gold patch) resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Placing the initial boundary markers of an interactive range selector.

An interactive one-dimensional range selector draws a pair of movable boundary
marker lines on a plotting axis. When the selector is first set up, those two
marker lines have to be given an initial pair of positions, expressed in the
axis' data coordinates along the selection direction (the horizontal axis for a
horizontal selector, the vertical axis for a vertical selector).

Each marker line is drawn at its given coordinate, and drawing a line at a
coordinate that lies outside the axis' current visible range would force the
visible range to grow to include it. The desired behavior is therefore that
setting up the selector must leave the axis' visible range exactly as it was: the
initial marker positions are chosen to be the axis' current view bounds (its
lower and upper visible limits) along the selection direction. Reading the marker
positions back then returns that same pair.

So the selected pair of initial marker positions equals:

  * the axis' current view bounds along the horizontal axis, for a horizontal
    selector;
  * the axis' current view bounds along the vertical axis, for a vertical
    selector.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The placement
-- is modeled DEEPLY as a pure selection between the two candidate coordinate
-- pairs (the axis' horizontal vs. vertical view bounds), governed only by the
-- selection direction, so no `opaque`/`axiom` callee contract is needed. The
-- marker container is an identity pass-through of the positions it is given
-- (reading them back returns the same pair), an `I` refinement, not an axiom.
-- axioms-end

-- pure-start
/-- The direction along which the range selector operates. -/
inductive SelectDirection where
  | horizontal
  | vertical
deriving DecidableEq, Repr

/-- The inputs the initial-position choice reads:

* `axis` — the selection direction;
* `selectorSpan` — the selector's own current span (its lower/upper extent);
* `xViewBounds` — the axis' current view bounds (lower, upper) along the
  horizontal axis;
* `yViewBounds` — the axis' current view bounds along the vertical axis.

Coordinates are exact rationals: the choice never does arithmetic on them, it
only selects which existing pair to use, so the exact ordered field keeps
equality decidable. -/
structure MarkerSetup where
  axis : SelectDirection
  selectorSpan : ℚ × ℚ
  xViewBounds : ℚ × ℚ
  yViewBounds : ℚ × ℚ
deriving Repr

/-- The initial marker positions: the axis' current view bounds along the
selection direction. -/
def initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=
  match inp.axis with
  | SelectDirection.horizontal => inp.xViewBounds
  | SelectDirection.vertical => inp.yViewBounds
-- pure-end

-- post-conditions-start
/-- The pair of initial marker positions is exactly the axis' current view bounds
along the selection direction — the horizontal view bounds for a horizontal
selector, the vertical view bounds for a vertical selector. Pinning it to a view
bound (rather than the selector's own span) is what leaves the axis' visible
range undisturbed. -/
def problem_spec_initialMarkers
    (inp : MarkerSetup) (result : ℚ × ℚ) : Prop :=
  (inp.axis = SelectDirection.horizontal → result = inp.xViewBounds) ∧
  (inp.axis = SelectDirection.vertical → result = inp.yViewBounds)
-- post-conditions-end

-- impl-start
def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
  let positions ←
    if inp.axis = SelectDirection.horizontal then
      pure inp.xViewBounds
    else
      pure inp.yViewBounds
  return positions
-- impl-end

-- proof-start
theorem correct_initialMarkers :
    ∀ (inp : MarkerSetup),
      problem_spec_initialMarkers inp
        (implementation_initialMarkers inp) := by
  intro inp
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    simp only [implementation_initialMarkers, Id.run, h, if_true, pure] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True for all 8 files (verified via swebench_unified.markers.same_spec, lean backend). Verification command: `bash scripts/lean_verify.sh <file>`.

### ATTACK RESULTS (all same_spec=True):
- atk_1 (prepatch bug: `pure inp.selectorSpan` unconditionally; == positions=self.extents): exit 1, does NOT verify. PREPATCH REPRODUCED — spec discriminates the reported bug (span (0,0) vs view bounds).
- atk_2 (swapped branches: horizontal->yViewBounds, vertical->xViewBounds): exit 1, does NOT verify.
- atk_3 (ungrounded/always xViewBounds, ignores direction): exit 1, does NOT verify (fails vertical clause).
- atk_4 (always yViewBounds): exit 1, does NOT verify (fails horizontal clause).
- atk_5 (partial-domain: horizontal ok, vertical->selectorSpan): exit 1, does NOT verify.
- atk_6 (boundary/tuple-swap: horizontal->(xViewBounds.2, xViewBounds.1), vertical ok): exit 1, does NOT verify.
- atk_7 (behavioral echo: `return initialMarkers inp`, == gold behavior): exit 0, VERIFIES, `#print axioms correct_initialMarkers` = [propext] (clean, no sorry, no custom axioms).
- atk_pc (gold impl, positive control): exit 0, verifies, axioms=[propext].

RESOLVE (protocol step 2, EXECUTED): atk_7 is behaviorally identical to gold, so its faithful refined patch IS the gold patch. run_resolve('matplotlib__matplotlib-20676', <gold patch>) => resolved=True, completed=True, note='resolved'. So the ONLY verifying same-spec attack has a materialized faithful patch that DOES resolve. No verify⇏correct gap.

REFINEMENT AUDIT (step 3): refinement.md legs = op1 R, op2 R, op3 I. No A-legs (axioms region byte-empty; G-AX skip is justified — the changed decision, which coordinate pair becomes the initial positions, is modeled DEEPLY as a pure selection on self.direction; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision). No kind-3 legs. The R legs (carried observations ax.get_xbound()/ax.get_ybound() -> xViewBounds/yViewBounds) and the I leg (ToolLineHandles pass-through identity, .positions == list(positions)) correspond to the real UNCHANGED callees at widgets.py:2158-2162. G-CONF (conformance_check.py, seed 20676, 120000 fuzz + edge cases) mechanically covers the R/I legs. Mapping.md callee provenance is consistent.

CONCLUSION: The spec is a maximally-tight full pin over a 2-constructor discriminant; no same-spec wrong impl both verifies AND fails to resolve. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the modeled routine: the choice of initial boundary-marker positions in SpanSelector._setup_edge_handle(s). Spec problem_spec_initialMarkers pins result=xViewBounds on horizontal and result=yViewBounds on vertical. Real callee (base worktree, matplotlib v3.6.0 post-fix `_setup_edge_handles`): `positions = ax.get_xbound()` if horizontal else `ax.get_ybound()`, then `ToolLineHandles(ax, positions,...).positions` reads back get_xdata()[0]/get_ydata()[0] per line — an EXACT ordered identity pass-through (axvline(p) stores xdata [p,p], read back as p). So the modeled result IS precisely the pair (xViewBounds/yViewBounds) the real code produces; xViewBounds/yViewBounds are carried observations = actual get_xbound()/get_ybound() outputs. The spec fully determines the result on both direction branches and matches the real repo on every input — it constrains nothing the real code leaves free and never over-strengthens: no diverging input exists. ℚ modeling is sound because the fix is a pure SELECTION with no arithmetic on values, so exact-ℚ equality coincides with the real float equality. Corroboration: lean_verify.sh exit 0; `#print axioms correct_initialMarkers` = [propext] only (no sorryAx, genuine proof); same_spec(Solution, Solution_prepatch)=True (spec view byte-identical, differs only in impl); conformance_check.py checked=120005 disagreements=0. G-AX legitimately skips (deeply-modeled changed decision, no consumed callee axiom). No drift, no spec-too-strong defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes with 0 hard failures (verified independently via leakage.screen). Spec view contains no diff markers, no reproduced gold-patch line, no patched file/module path (lib/matplotlib/widgets.py absent), and no patched changed symbol (`new_axes`). No gold-mechanism identifiers leak: get_xbound/get_ybound/extents/ToolLineHandles/_edge_handles/_setup_edge_handle/SpanSelector/axvline/axhline all absent from the spec view; only the generic word 'interactive' appears (in prose 'interactive range selector', not a gold identifier). No narration keywords in spec-view comments — the 'Pre-patch bug' narration lives only in Solution_prepatch.lean's impl region, which the spec-view projection elides. Semantic check: the post-condition (result = axis' current view bounds along the selection direction) formalizes the behavior ALREADY public in problem_statement ('xlimits should remain at (10,20)+margins', must not be forced to include 0 — i.e. leave the view undisturbed). It reveals the required output contract (the 'what'), derivable from the public expected-outcome, but not the gold edit's 'how' (the self.extents -> ax.get_xbound()/get_ybound() accessor swap inside _setup_edge_handle). Impl and proof regions are elided; the solver must still implement the fix. same_spec(Solution, Solution_prepatch)=True and Solution.lean compiles clean (lean_verify exit 0). Leakage judged against problem_statement only, never hints_text. No leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
