# P2 adversarial audit — matplotlib__matplotlib-20676

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -66,13 +66,7 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
-    let positions : Rat × Rat :=
-      match o with
-      | .horizontal => horizontalLimits
-      | .vertical   => verticalLimits
+    let positions : Rat × Rat := currentSpan
     return positions
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,10 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
     let positions : Rat × Rat :=
       match o with
-      | .horizontal => horizontalLimits
-      | .vertical   => verticalLimits
+      | .horizontal => verticalLimits
+      | .vertical   => horizontalLimits
     return positions
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,7 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
-    let positions : Rat × Rat :=
-      match o with
-      | .horizontal => horizontalLimits
-      | .vertical   => verticalLimits
+    let positions : Rat × Rat := horizontalLimits
     return positions
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,11 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
-    let positions : Rat × Rat :=
+    let base : Rat × Rat :=
       match o with
       | .horizontal => horizontalLimits
       | .vertical   => verticalLimits
+    let positions : Rat × Rat := (base.2, base.1)
     return positions
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,9 +66,9 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
+    let mut i : Nat := 1
+    while i > 0 do
+      i := i + 1
     let positions : Rat × Rat :=
       match o with
       | .horizontal => horizontalLimits
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,10 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
     let positions : Rat × Rat :=
       match o with
       | .horizontal => horizontalLimits
-      | .vertical   => verticalLimits
+      | .vertical   => currentSpan
     return positions
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,11 @@
   ensures out = initialMarkerSpec o horizontalLimits verticalLimits
   do
     -- impl-start
-    -- Choose the boundary-marker positions by orientation: the limits of the
-    -- horizontal axis for a horizontal picker, the limits of the vertical axis
-    -- otherwise. `currentSpan` is deliberately unused.
-    let positions : Rat × Rat :=
-      match o with
-      | .horizontal => horizontalLimits
-      | .vertical   => verticalLimits
+    let positions : Rat × Rat := if currentSpan = currentSpan then
+        (match o with
+         | .horizontal => horizontalLimits
+         | .vertical   => currentSpan)
+      else currentSpan
     return positions
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real marker-placement choice is a straight-line pure
   computation (an orientation dispatch over two already-known limit pairs)
   that always terminates and returns, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The two unchanged callees
   this slice relies on — the queries that report the lower/upper view limits of
   the two coordinate axes — are pure value sources whose results are taken as
   the inputs `horizontalLimits` / `verticalLimits` of the modeled operation
   (the order-preserving `(lower, upper)` pair of each axis). Their provenance
   and the input bijection are recorded in mapping.md; the end-to-end behaviour
   is differential-tested by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/- The two coordinate axes a planar drawing surface exposes. The orientation of
   an interactive range picker selects which axis its movable boundary markers
   live on. -/
inductive Orientation where
  | horizontal
  | vertical
  deriving DecidableEq

/- The intended initial placement of the two boundary markers: the markers must
   start on the limits of the axis that matches the picker's orientation — the
   lower/upper view limit pair of that axis — so that introducing the markers
   leaves the view of every axis exactly where it already was. The opposite
   axis's limits and the picker's current (possibly degenerate) selection span
   never enter this choice. -/
def initialMarkerSpec
    (o : Orientation) (horizontalLimits verticalLimits : Rat × Rat) : Rat × Rat :=
  match o with
  | .horizontal => horizontalLimits
  | .vertical   => verticalLimits

@[grind] lemma initialMarkerSpec_h (hl vl : Rat × Rat) :
    initialMarkerSpec .horizontal hl vl = hl := rfl
@[grind] lemma initialMarkerSpec_v (hl vl : Rat × Rat) :
    initialMarkerSpec .vertical hl vl = vl := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `currentSpan` is the picker's present selection span at the moment the
   markers are introduced. It is read-only and must NOT influence the initial
   marker placement; the postcondition pins the result to the orientation-
   matched axis limits alone, so any implementation that lets `currentSpan`
   leak into the result fails to verify. -/
method initialMarkerPositions
    (o : Orientation) (horizontalLimits : Rat × Rat) (verticalLimits : Rat × Rat)
    (currentSpan : Rat × Rat)
    return (out : Rat × Rat)
  ensures out = initialMarkerSpec o horizontalLimits verticalLimits
  do
    -- impl-start
    -- Choose the boundary-marker positions by orientation: the limits of the
    -- horizontal axis for a horizontal picker, the limits of the vertical axis
    -- otherwise. `currentSpan` is deliberately unused.
    let positions : Rat × Rat :=
      match o with
      | .horizontal => horizontalLimits
      | .vertical   => verticalLimits
    return positions
    -- impl-end

prove_correct initialMarkerPositions by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for matplotlib__matplotlib-20676 (velvet). verifier scripts/lean_verify.sh with.

SPEC SHAPE: The postcondition is a TOTAL FUNCTIONAL EQUALITY: `out = initialMarkerSpec o horizontalLimits verticalLimits`, where initialMarkerSpec is a total match over Orientation returning horizontalLimits (.horizontal) or verticalLimits (.vertical). This fully pins the output for every input, leaving no partial-domain, boundary, or oracle freedom. Termination is `total` + `demonic` choice, so a diverging body cannot vacuously discharge the ensures.

SAME-SPEC: all 7 attacks confirmed True via swebench_unified.markers.same_spec (velvet). Only the impl region (impl-start..impl-end) was edited; axioms/pure/pre/post byte-identical.

### ATTACKS (each verified with `bash scripts/lean_verify.sh <file>`):
- atk_1 (prepatch bug / ungrounded echo): positions := currentSpan. EXIT 1, error 'unsolved goals' (atk_1.lean:73). PREPATCH REPRODUCED — matches Solution_prepatch.lean, fails postcondition (currentSpan = initialMarkerSpec o hl vl unprovable).
- atk_2 (swapped orientation): .horizontal=>verticalLimits, .vertical=>horizontalLimits. EXIT 1, unsolved goals (atk_2.lean:76).
- atk_3 (partial-domain / constant): always horizontalLimits (correct for .horizontal, wrong for .vertical). EXIT 1, unsolved goals (atk_3.lean:73).
- atk_4 (boundary / pair-component swap): correct pair but (hi,lo). EXIT 1, unsolved goals (atk_4.lean:77).
- atk_5 (control-flow-effect / divergence): `while i>0 do i:=i+1` then correct value. EXIT 1 — rejected by total-correctness: 'Decreasing annotations are required in total correctness semantics' + WPGen assertion (atk_5.lean:80). Confirms total semantics blocks vacuous divergence, as refinement.md claims.
- atk_6 (ungrounded-oracle echo, partial): .horizontal=>horizontalLimits, .vertical=>currentSpan. EXIT 1, unsolved goals (atk_6.lean:76).
- atk_7 (nondeterministic/guarded echo): guarded choice leaking currentSpan into .vertical branch. EXIT 1, unsolved goals (atk_7.lean:77).

POSITIVE CONTROL: pos_control.lean = frozen Solution.lean verbatim → EXIT 0 (verifies, no sorry).

RESULT: 0 of 7 same-spec wrong impls verify. Therefore NO verifying-but-wrong impl exists to materialize a faithful refined patch for; the resolve step (protocol step 2) is vacuously satisfied — there is no verifying wrong patch that could fail to resolve. verify⇒correct holds for this spec on the attacked surface.

REFINEMENT.MD AUDIT: Section headings 'A.'/'B.'/'C.' are document sections; the leg-table tags are R (A1,A2,A3,A4,A6-part) and I (A5,A6-part) only — no kind-3 (inexpressible-changed-op) legs (explicitly stated in §B). mapping.md §3 confirms NO consumed axioms and NO deep-model A-references: get_xbound/get_ybound are unchanged pure value sources feeding inputs horizontalLimits/verticalLimits; ToolLineHandles is the unchanged consumer whose .positions returns the passed pair verbatim; self.extents ↔ currentSpan is a read-only unused input. All R/I legs are exercised live by G-CONF (conformance_check.py, seed 20676, ≥1e5 samples). G-AX = skip is justified (no axioms to trust). The single trust point is refinement fidelity, which the total functional postcondition + the frame on currentSpan enforce. No A-leg axiom correspondence exists to falsify.

VERDICT: SOUND — ≥5 distinct attacks (7 run: partial-domain, boundary, control-flow-effect/divergence, swapped-orientation, two ungrounded-oracle echoes incl. the prepatch bug) all fail to verify; positive control verifies; refinement.md legs are all R/A-reference-none/I with correct correspondence.

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
import Velvet.Std
-- imports-end

/- Total correctness: the real marker-placement choice is a straight-line pure
   computation (an orientation dispatch over two already-known limit pairs)
   that always terminates and returns, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The two unchanged callees
   this slice relies on — the queries that report the lower/upper view limits of
   the two coordinate axes — are pure value sources whose results are taken as
   the inputs `horizontalLimits` / `verticalLimits` of the modeled operation
   (the order-preserving `(lower, upper)` pair of each axis). Their provenance
   and the input bijection are recorded in mapping.md; the end-to-end behaviour
   is differential-tested by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/- The two coordinate axes a planar drawing surface exposes. The orientation of
   an interactive range picker selects which axis its movable boundary markers
   live on. -/
inductive Orientation where
  | horizontal
  | vertical
  deriving DecidableEq

/- The intended initial placement of the two boundary markers: the markers must
   start on the limits of the axis that matches the picker's orientation — the
   lower/upper view limit pair of that axis — so that introducing the markers
   leaves the view of every axis exactly where it already was. The opposite
   axis's limits and the picker's current (possibly degenerate) selection span
   never enter this choice. -/
def initialMarkerSpec
    (o : Orientation) (horizontalLimits verticalLimits : Rat × Rat) : Rat × Rat :=
  match o with
  | .horizontal => horizontalLimits
  | .vertical   => verticalLimits

@[grind] lemma initialMarkerSpec_h (hl vl : Rat × Rat) :
    initialMarkerSpec .horizontal hl vl = hl := rfl
@[grind] lemma initialMarkerSpec_v (hl vl : Rat × Rat) :
    initialMarkerSpec .vertical hl vl = vl := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `currentSpan` is the picker's present selection span at the moment the
   markers are introduced. It is read-only and must NOT influence the initial
   marker placement; the postcondition pins the result to the orientation-
   matched axis limits alone, so any implementation that lets `currentSpan`
   leak into the result fails to verify. -/
method initialMarkerPositions
    (o : Orientation) (horizontalLimits : Rat × Rat) (verticalLimits : Rat × Rat)
    (currentSpan : Rat × Rat)
    return (out : Rat × Rat)
  ensures out = initialMarkerSpec o horizontalLimits verticalLimits
  do
    -- impl-start
    -- Choose the boundary-marker positions by orientation: the limits of the
    -- horizontal axis for a horizontal picker, the limits of the vertical axis
    -- otherwise. `currentSpan` is deliberately unused.
    let positions : Rat × Rat :=
      match o with
      | .horizontal => horizontalLimits
      | .vertical   => verticalLimits
    return positions
    -- impl-end

prove_correct initialMarkerPositions by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for matplotlib__matplotlib-20676 (velvet). verifier scripts/lean_verify.sh with.

SPEC SHAPE: The postcondition is a TOTAL FUNCTIONAL EQUALITY: `out = initialMarkerSpec o horizontalLimits verticalLimits`, where initialMarkerSpec is a total match over Orientation returning horizontalLimits (.horizontal) or verticalLimits (.vertical). This fully pins the output for every input, leaving no partial-domain, boundary, or oracle freedom. Termination is `total` + `demonic` choice, so a diverging body cannot vacuously discharge the ensures.

SAME-SPEC: all 7 attacks confirmed True via swebench_unified.markers.same_spec (velvet). Only the impl region (impl-start..impl-end) was edited; axioms/pure/pre/post byte-identical.

### ATTACKS (each verified with `bash scripts/lean_verify.sh <file>`):
- atk_1 (prepatch bug / ungrounded echo): positions := currentSpan. EXIT 1, error 'unsolved goals' (atk_1.lean:73). PREPATCH REPRODUCED — matches Solution_prepatch.lean, fails postcondition (currentSpan = initialMarkerSpec o hl vl unprovable).
- atk_2 (swapped orientation): .horizontal=>verticalLimits, .vertical=>horizontalLimits. EXIT 1, unsolved goals (atk_2.lean:76).
- atk_3 (partial-domain / constant): always horizontalLimits (correct for .horizontal, wrong for .vertical). EXIT 1, unsolved goals (atk_3.lean:73).
- atk_4 (boundary / pair-component swap): correct pair but (hi,lo). EXIT 1, unsolved goals (atk_4.lean:77).
- atk_5 (control-flow-effect / divergence): `while i>0 do i:=i+1` then correct value. EXIT 1 — rejected by total-correctness: 'Decreasing annotations are required in total correctness semantics' + WPGen assertion (atk_5.lean:80). Confirms total semantics blocks vacuous divergence, as refinement.md claims.
- atk_6 (ungrounded-oracle echo, partial): .horizontal=>horizontalLimits, .vertical=>currentSpan. EXIT 1, unsolved goals (atk_6.lean:76).
- atk_7 (nondeterministic/guarded echo): guarded choice leaking currentSpan into .vertical branch. EXIT 1, unsolved goals (atk_7.lean:77).

POSITIVE CONTROL: pos_control.lean = frozen Solution.lean verbatim → EXIT 0 (verifies, no sorry).

RESULT: 0 of 7 same-spec wrong impls verify. Therefore NO verifying-but-wrong impl exists to materialize a faithful refined patch for; the resolve step (protocol step 2) is vacuously satisfied — there is no verifying wrong patch that could fail to resolve. verify⇒correct holds for this spec on the attacked surface.

REFINEMENT.MD AUDIT: Section headings 'A.'/'B.'/'C.' are document sections; the leg-table tags are R (A1,A2,A3,A4,A6-part) and I (A5,A6-part) only — no kind-3 (inexpressible-changed-op) legs (explicitly stated in §B). mapping.md §3 confirms NO consumed axioms and NO deep-model A-references: get_xbound/get_ybound are unchanged pure value sources feeding inputs horizontalLimits/verticalLimits; ToolLineHandles is the unchanged consumer whose .positions returns the passed pair verbatim; self.extents ↔ currentSpan is a read-only unused input. All R/I legs are exercised live by G-CONF (conformance_check.py, seed 20676, ≥1e5 samples). G-AX = skip is justified (no axioms to trust). The single trust point is refinement fidelity, which the total functional postcondition + the frame on currentSpan enforce. No A-leg axiom correspondence exists to falsify.

VERDICT: SOUND — ≥5 distinct attacks (7 run: partial-domain, boundary, control-flow-effect/divergence, swapped-orientation, two ungrounded-oracle echoes incl. the prepatch bug) all fail to verify; positive control verifies; refinement.md legs are all R/A-reference-none/I with correct correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness/spec-too-strong) = FAITHFUL. Independently verified against the real repo at base_commit a302267 (worktree).

Spec integrity: same_spec(Solution, Solution_prepatch, velvet)=True (spec region byte-identical); spec_view renders cleanly; scripts/lean_verify.sh Solution.lean exit 0.

Model vs real callee (SpanSelector._setup_edge_handles, lib/matplotlib/widgets.py:2381):
1) Dispatch is 1:1 — real: `if self.direction=='horizontal': positions=self.ax.get_xbound() else: positions=self.ax.get_ybound()`; spec: `match o | .horizontal => horizontalLimits | .vertical => verticalLimits`, under bijection horizontalLimits<->get_xbound(), verticalLimits<->get_ybound().
2) Domain totality: direction guarded by _api.check_in_list(['horizontal','vertical'],...) in ToolLineHandles.__init__ (widgets.py:2659); the Python `else` fires only for 'vertical', so the 2-constructor Orientation carrier is total — no reachable third value that would spuriously take the vertical branch.
3) Observable is verbatim pass-through: ToolLineHandles.positions returns [get_xdata()/get_ydata()[0] for line in axvline(p)/axhline(p)], i.e. exactly the input positions — no arithmetic/transformation, so the Rat x Rat carrier introduces zero divergence (float precision irrelevant, nothing computed).
4) currentSpan frame faithful, not invented: the patch REMOVES self.extents from this call site; the spec models it as an explicit read-only input the postcondition forbids. The spec forbids only the removed dependency; it does not add any.
5) F2P test test_span_selector_bound asserts exactly tool._edge_handles.positions == list(get_xbound()/get_ybound()) by direction — precisely the postcondition.

Searched for a diverging input (third direction value, bound order inversion, float precision, currentSpan leakage) and found none: the modeled function agrees with the real callee on every reachable input. The spec is not too strong and does not drift.

(Note: meta records G-PANEL-1 = fail 'same-spec impl verifies' — a spec-too-WEAK finding, outside this gate's scope; it does not bear on faithfulness/spec-too-strong.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region integrity: same_spec(Solution.lean, Solution_prepatch.lean) = True under the velvet backend — the frozen spec view (imports, axioms prose, Orientation, initialMarkerSpec + lemmas, initialMarkerPositions signature/ensures, elided impl+proof) is byte-identical between post- and pre-patch; only the elided impl differs. Mechanical leakage.screen passes with zero hard failures.

Public baseline: problem_statement already discloses (a) subject = SpanSelector, (b) defect = axis view forced to include 0, (c) expected = axis limits remain where they were (10,20)+margins on introducing the selector. Leakage judged against problem_statement ONLY (not hints_text).

Spec-view audit (manual): no diff markers; patched file path lib/matplotlib/widgets.py and module path absent; no gold-patch changed line reproduced; NO repo symbol echoed — _setup_edge_handle, ToolLineHandles, get_xbound, get_ybound, self.extents, _edge_handles, SpanSelector, direction, new_axes all absent from the view. No narration tokens (bug/fix/incorrectly/wrong/patch) in any spec-view comment; comments are abstract ('range picker', 'boundary markers', 'coordinate axes', 'view limit pair').

Semantic check: the postcondition out = initialMarkerSpec o horizontalLimits verticalLimits (orientation-matched axis-limit pair) plus the 'currentSpan is read-only, must not influence result' framing encode exactly the publicly-stated expected behavior (limits stay put, not forced to include 0). They do NOT reveal the gold edit's mechanics — that the pre-patch passed self.extents to ToolLineHandles, or that the fix branches on self.direction to select get_xbound()/get_ybound(). The changed-symbol screen surfaced only 'new_axes' (a hunk section-header artifact, not the modeled function), which does not appear in the view. No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
