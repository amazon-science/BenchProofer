# P2 adversarial audit — matplotlib__matplotlib-24637

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,13 +87,11 @@
   if !visible || !posResolvable then
     return []
   let mut trace : List RenderOp := []
-  trace := trace ++ [RenderOp.groupStart clsName gid]
   -- position resolution happens here and emits no marker
   if hasArrow then
     trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
   trace := trace ++ [RenderOp.drawOffsetbox]
-  trace := trace ++ [RenderOp.groupEnd clsName]
   return trace
 -- impl-end
 
@@ -105,7 +103,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,8 +87,6 @@
   if !visible || !posResolvable then
     return []
   let mut trace : List RenderOp := []
-  trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
   if hasArrow then
     trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
@@ -105,7 +103,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,10 @@
     return []
   let mut trace : List RenderOp := []
   trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
   if hasArrow then
     trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
   trace := trace ++ [RenderOp.drawOffsetbox]
-  trace := trace ++ [RenderOp.groupEnd clsName]
   return trace
 -- impl-end
 
@@ -105,7 +103,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,8 +87,7 @@
   if !visible || !posResolvable then
     return []
   let mut trace : List RenderOp := []
-  trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
+  trace := trace ++ [RenderOp.groupStart clsName none]
   if hasArrow then
     trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
@@ -105,7 +104,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,11 +84,10 @@
 def implementation_drawAnnotationBbox
     (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :
     List RenderOp := Id.run do
-  if !visible || !posResolvable then
+  if !visible && !posResolvable then
     return []
   let mut trace : List RenderOp := []
   trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
   if hasArrow then
     trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
@@ -105,7 +104,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,11 @@
     return []
   let mut trace : List RenderOp := []
   trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
   if hasArrow then
     trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
+  trace := trace ++ [RenderOp.groupEnd clsName]
   trace := trace ++ [RenderOp.drawOffsetbox]
-  trace := trace ++ [RenderOp.groupEnd clsName]
   return trace
 -- impl-end
 
@@ -105,7 +104,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,9 +88,7 @@
     return []
   let mut trace : List RenderOp := []
   trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
-  if hasArrow then
-    trace := trace ++ [RenderOp.drawArrow]
+  trace := trace ++ [RenderOp.drawArrow]
   trace := trace ++ [RenderOp.drawPatch]
   trace := trace ++ [RenderOp.drawOffsetbox]
   trace := trace ++ [RenderOp.groupEnd clsName]
@@ -105,7 +103,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -86,15 +86,10 @@
     List RenderOp := Id.run do
   if !visible || !posResolvable then
     return []
-  let mut trace : List RenderOp := []
-  trace := trace ++ [RenderOp.groupStart clsName gid]
-  -- position resolution happens here and emits no marker
-  if hasArrow then
-    trace := trace ++ [RenderOp.drawArrow]
-  trace := trace ++ [RenderOp.drawPatch]
-  trace := trace ++ [RenderOp.drawOffsetbox]
-  trace := trace ++ [RenderOp.groupEnd clsName]
-  return trace
+  else
+    let arrowSeg := if hasArrow then [RenderOp.drawArrow] else []
+    return ([RenderOp.groupStart clsName gid] ++ arrowSeg
+              ++ [RenderOp.drawPatch, RenderOp.drawOffsetbox, RenderOp.groupEnd clsName])
 -- impl-end
 
 -- proof-start
@@ -105,7 +100,6 @@
   intro visible posResolvable hasArrow clsName gid
   unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
   simp only [Id.run, bind, pure]
-  by_cases h : (!visible || !posResolvable) = true <;>
-    by_cases ha : hasArrow = true <;>
-    simp [h, ha]
+  cases visible <;> cases posResolvable <;> cases hasArrow <;>
+    simp_all [List.append_assoc]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Emitting a grouping marker so an annotation-box artist's gid reaches the output.

When a composite annotation-box artist is drawn onto a renderer it produces an
ordered sequence of drawing operations. The artist can carry an optional group
id (gid); for that id to survive into a structured output document (e.g. an SVG),
the artist must surround the drawing of its parts with a group-start marker that
carries the gid and a matching group-end marker.

The artist draws as follows:

* if it is not visible, or its position cannot be resolved, it draws nothing;
* otherwise it draws, in order:
  * a group-start marker tagged with the artist's class name and carrying its
    optional gid;
  * the connecting arrow, but only when the artist has one;
  * its background box;
  * the wrapped offset box;
  * a group-end marker tagged with the same class name.

The desired behavior is that the whole sequence of part-draws is enclosed
between the group-start (carrying the gid) and the group-end, so the gid labels
the group as a whole. Position resolution happens before any part is drawn and
contributes no marker of its own.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The drawing
-- behavior is modeled DEEPLY as the ordered trace of emitted operations over the
-- observable flags of the artist (visible, position-resolvable, has-an-arrow),
-- its class name, and its optional group id, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A single drawing operation emitted onto the renderer while drawing the
artist.

* `groupStart gname gid` — open a named group tagged with the optional group id;
* `groupEnd gname` — close the group with the matching name;
* `drawArrow` — draw the connecting arrow;
* `drawPatch` — draw the background box;
* `drawOffsetbox` — draw the wrapped offset box. -/
inductive RenderOp where
  | groupStart (gname : String) (gid : Option String)
  | groupEnd (gname : String)
  | drawArrow
  | drawPatch
  | drawOffsetbox
deriving DecidableEq, Repr

/-- The ordered sequence of drawing operations the artist emits.

* `visible` — the artist is visible;
* `posResolvable` — the artist's position could be resolved;
* `hasArrow` — the artist has a connecting arrow;
* `clsName` — the artist's class name (used to tag the group markers);
* `gid` — the artist's optional group id. -/
def drawTrace (visible posResolvable hasArrow : Bool)
    (clsName : String) (gid : Option String) : List RenderOp :=
  if !visible || !posResolvable then
    []
  else
    [RenderOp.groupStart clsName gid]
      ++ (if hasArrow then [RenderOp.drawArrow] else [])
      ++ [RenderOp.drawPatch, RenderOp.drawOffsetbox]
      ++ [RenderOp.groupEnd clsName]
-- pure-end

-- post-conditions-start
/-- The emitted trace is exactly the ordered sequence above: nothing when the
artist is not drawn, otherwise the part-draws enclosed between a group-start
carrying the gid and a matching group-end. -/
def problem_spec_drawAnnotationBbox
    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String)
    (result : List RenderOp) : Prop :=
  result = drawTrace visible posResolvable hasArrow clsName gid
-- post-conditions-end

-- impl-start
def implementation_drawAnnotationBbox
    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :
    List RenderOp := Id.run do
  if !visible || !posResolvable then
    return []
  let mut trace : List RenderOp := []
  trace := trace ++ [RenderOp.groupStart clsName gid]
  -- position resolution happens here and emits no marker
  if hasArrow then
    trace := trace ++ [RenderOp.drawArrow]
  trace := trace ++ [RenderOp.drawPatch]
  trace := trace ++ [RenderOp.drawOffsetbox]
  trace := trace ++ [RenderOp.groupEnd clsName]
  return trace
-- impl-end

-- proof-start
theorem correct_drawAnnotationBbox :
    ∀ (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String),
      problem_spec_drawAnnotationBbox visible posResolvable hasArrow clsName gid
        (implementation_drawAnnotationBbox visible posResolvable hasArrow clsName gid) := by
  intro visible posResolvable hasArrow clsName gid
  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
  simp only [Id.run, bind, pure]
  by_cases h : (!visible || !posResolvable) = true <;>
    by_cases ha : hasArrow = true <;>
    simp [h, ha]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_drawAnnotationBbox = exact functional equality to the total oracle drawTrace, universally quantified over all inputs (result = drawTrace visible posResolvable hasArrow clsName gid). This is the tightest possible spec in the modeled domain: any verifying impl is forced to be extensionally equal to drawTrace over every input tuple. axioms region is EMPTY (G-AX skips), so there are NO A-legs to attack — the model↔patch correspondence audit reduces to the R/I legs (mechanically G-CONF territory).

PROTOCOL RUN (project root;; all same_spec=True; verified concurrently ≤4 via `bash scripts/lean_verify.sh <f>`; axioms via appended `#print axioms correct_drawAnnotationBbox`):
- pos_control.lean (shipped Solution): EXIT 0; axioms = [propext] (clean, no sorryAx). Positive control PASSES.
- shipped_prepatch (Solution_prepatch.lean, the bug — drops both group markers): EXIT 1 (rfl failed / unsolved goals). PREPATCH BUG REPRODUCED — spec correctly rejects the buggy behavior.
- atk_1 (prepatch-bug re-encode: drop BOTH group markers): EXIT 1, unsolved goals @102:90.
- atk_2 (drop groupStart only): EXIT 1, unsolved goals @102:90.
- atk_3 (drop groupEnd only): EXIT 1, unsolved goals @102:90.
- atk_4 (ungrounded-oracle echo: groupStart clsName none — gid stripped): EXIT 1, unsolved goals @103:90. THE gid is exactly the bug's payload; spec pins it.
- atk_5 (boundary: guard `&&` instead of `||`): EXIT 1, unsolved goals @103:90.
- atk_6 (control-flow-effect: reorder groupEnd before drawOffsetbox): EXIT 1, unsolved goals @103:90.
- atk_7 (partial-domain: always emit drawArrow, drop hasArrow guard): EXIT 1, unsolved goals @102:90.
All 7 wrong impls fail with GENUINE `error: unsolved goals` (spec violations), not tactic-syntax artifacts (proof strengthened to `cases … <;> simp_all`).
- atk_8 (alt-correct reformulation: list-literal build with `arrowSeg`, gid PRESERVED, correct order/trace): EXIT 0; axioms = [propext] (clean). This is the ONLY same-spec closing candidate that is not the shipped impl, and it is BEHAVIORALLY IDENTICAL to the gold (same trace on every input). Its faithful patch is therefore the gold patch.

MANDATORY RESOLVE (protocol step 2): every closing clean-axiom same-spec impl must have its faithful patch materialized and run through the official harness. atk_8 closed → materialized its faithful patch (=benchmark-verified/matplotlib__matplotlib-24637/lean/patch.diff, gold-equivalent) → run_resolve("matplotlib__matplotlib-24637", patch, timeout=1800, retries=1) via swebench_unified.harness → RESOLVED: True (Docker oracle, benchmark swe_bench_verified). So the closing candidate's patch RESOLVES — no verify⇏correct break.

REFINEMENT.MD AUDIT: axioms region empty → NO A-legs (G-AX skips, correctly documented). Every leg is R (ops 1,2,4,5,6,7) or I (op 3 update_positions = no-op in trace; return trace / self.stale=False). No kind-3 dangling-axiom legs. The R-abstraction (each child <c>.draw(renderer) → one opaque marker drawArrow/drawPatch/drawOffsetbox) is legitimate: the fix concerns only the ENCLOSING gid-group, children unchanged; their PRESENCE and RELATIVE ORDER are pinned by the exact-equality spec — confirmed empirically since all 7 trace-mutating impls (drop/reorder/strip-gid/guard-swap) failed to close. Frame discipline holds: result = drawTrace pins the FULL ordered trace, leaving no output component free.

CONCLUSION: SOUND. ≥5 distinct wrong impls (8 attempted) run; none with a closing clean-axiom proof; the sole non-gold closing candidate (atk_8) is gold-equivalent and its faithful patch RESOLVES=True. Spec correctly excludes prepatch bug and all trace mutations. verify⇒correct upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Emitting a grouping marker so an annotation-box artist's gid reaches the output.

When a composite annotation-box artist is drawn onto a renderer it produces an
ordered sequence of drawing operations. The artist can carry an optional group
id (gid); for that id to survive into a structured output document (e.g. an SVG),
the artist must surround the drawing of its parts with a group-start marker that
carries the gid and a matching group-end marker.

The artist draws as follows:

* if it is not visible, or its position cannot be resolved, it draws nothing;
* otherwise it draws, in order:
  * a group-start marker tagged with the artist's class name and carrying its
    optional gid;
  * the connecting arrow, but only when the artist has one;
  * its background box;
  * the wrapped offset box;
  * a group-end marker tagged with the same class name.

The desired behavior is that the whole sequence of part-draws is enclosed
between the group-start (carrying the gid) and the group-end, so the gid labels
the group as a whole. Position resolution happens before any part is drawn and
contributes no marker of its own.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The drawing
-- behavior is modeled DEEPLY as the ordered trace of emitted operations over the
-- observable flags of the artist (visible, position-resolvable, has-an-arrow),
-- its class name, and its optional group id, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A single drawing operation emitted onto the renderer while drawing the
artist.

* `groupStart gname gid` — open a named group tagged with the optional group id;
* `groupEnd gname` — close the group with the matching name;
* `drawArrow` — draw the connecting arrow;
* `drawPatch` — draw the background box;
* `drawOffsetbox` — draw the wrapped offset box. -/
inductive RenderOp where
  | groupStart (gname : String) (gid : Option String)
  | groupEnd (gname : String)
  | drawArrow
  | drawPatch
  | drawOffsetbox
deriving DecidableEq, Repr

/-- The ordered sequence of drawing operations the artist emits.

* `visible` — the artist is visible;
* `posResolvable` — the artist's position could be resolved;
* `hasArrow` — the artist has a connecting arrow;
* `clsName` — the artist's class name (used to tag the group markers);
* `gid` — the artist's optional group id. -/
def drawTrace (visible posResolvable hasArrow : Bool)
    (clsName : String) (gid : Option String) : List RenderOp :=
  if !visible || !posResolvable then
    []
  else
    [RenderOp.groupStart clsName gid]
      ++ (if hasArrow then [RenderOp.drawArrow] else [])
      ++ [RenderOp.drawPatch, RenderOp.drawOffsetbox]
      ++ [RenderOp.groupEnd clsName]
-- pure-end

-- post-conditions-start
/-- The emitted trace is exactly the ordered sequence above: nothing when the
artist is not drawn, otherwise the part-draws enclosed between a group-start
carrying the gid and a matching group-end. -/
def problem_spec_drawAnnotationBbox
    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String)
    (result : List RenderOp) : Prop :=
  result = drawTrace visible posResolvable hasArrow clsName gid
-- post-conditions-end

-- impl-start
def implementation_drawAnnotationBbox
    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :
    List RenderOp := Id.run do
  if !visible || !posResolvable then
    return []
  let mut trace : List RenderOp := []
  trace := trace ++ [RenderOp.groupStart clsName gid]
  -- position resolution happens here and emits no marker
  if hasArrow then
    trace := trace ++ [RenderOp.drawArrow]
  trace := trace ++ [RenderOp.drawPatch]
  trace := trace ++ [RenderOp.drawOffsetbox]
  trace := trace ++ [RenderOp.groupEnd clsName]
  return trace
-- impl-end

-- proof-start
theorem correct_drawAnnotationBbox :
    ∀ (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String),
      problem_spec_drawAnnotationBbox visible posResolvable hasArrow clsName gid
        (implementation_drawAnnotationBbox visible posResolvable hasArrow clsName gid) := by
  intro visible posResolvable hasArrow clsName gid
  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
  simp only [Id.run, bind, pure]
  by_cases h : (!visible || !posResolvable) = true <;>
    by_cases ha : hasArrow = true <;>
    simp [h, ha]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_drawAnnotationBbox = exact functional equality to the total oracle drawTrace, universally quantified over all inputs (result = drawTrace visible posResolvable hasArrow clsName gid). This is the tightest possible spec in the modeled domain: any verifying impl is forced to be extensionally equal to drawTrace over every input tuple. axioms region is EMPTY (G-AX skips), so there are NO A-legs to attack — the model↔patch correspondence audit reduces to the R/I legs (mechanically G-CONF territory).

PROTOCOL RUN (project root;; all same_spec=True; verified concurrently ≤4 via `bash scripts/lean_verify.sh <f>`; axioms via appended `#print axioms correct_drawAnnotationBbox`):
- pos_control.lean (shipped Solution): EXIT 0; axioms = [propext] (clean, no sorryAx). Positive control PASSES.
- shipped_prepatch (Solution_prepatch.lean, the bug — drops both group markers): EXIT 1 (rfl failed / unsolved goals). PREPATCH BUG REPRODUCED — spec correctly rejects the buggy behavior.
- atk_1 (prepatch-bug re-encode: drop BOTH group markers): EXIT 1, unsolved goals @102:90.
- atk_2 (drop groupStart only): EXIT 1, unsolved goals @102:90.
- atk_3 (drop groupEnd only): EXIT 1, unsolved goals @102:90.
- atk_4 (ungrounded-oracle echo: groupStart clsName none — gid stripped): EXIT 1, unsolved goals @103:90. THE gid is exactly the bug's payload; spec pins it.
- atk_5 (boundary: guard `&&` instead of `||`): EXIT 1, unsolved goals @103:90.
- atk_6 (control-flow-effect: reorder groupEnd before drawOffsetbox): EXIT 1, unsolved goals @103:90.
- atk_7 (partial-domain: always emit drawArrow, drop hasArrow guard): EXIT 1, unsolved goals @102:90.
All 7 wrong impls fail with GENUINE `error: unsolved goals` (spec violations), not tactic-syntax artifacts (proof strengthened to `cases … <;> simp_all`).
- atk_8 (alt-correct reformulation: list-literal build with `arrowSeg`, gid PRESERVED, correct order/trace): EXIT 0; axioms = [propext] (clean). This is the ONLY same-spec closing candidate that is not the shipped impl, and it is BEHAVIORALLY IDENTICAL to the gold (same trace on every input). Its faithful patch is therefore the gold patch.

MANDATORY RESOLVE (protocol step 2): every closing clean-axiom same-spec impl must have its faithful patch materialized and run through the official harness. atk_8 closed → materialized its faithful patch (=benchmark-verified/matplotlib__matplotlib-24637/lean/patch.diff, gold-equivalent) → run_resolve("matplotlib__matplotlib-24637", patch, timeout=1800, retries=1) via swebench_unified.harness → RESOLVED: True (Docker oracle, benchmark swe_bench_verified). So the closing candidate's patch RESOLVES — no verify⇏correct break.

REFINEMENT.MD AUDIT: axioms region empty → NO A-legs (G-AX skips, correctly documented). Every leg is R (ops 1,2,4,5,6,7) or I (op 3 update_positions = no-op in trace; return trace / self.stale=False). No kind-3 dangling-axiom legs. The R-abstraction (each child <c>.draw(renderer) → one opaque marker drawArrow/drawPatch/drawOffsetbox) is legitimate: the fix concerns only the ENCLOSING gid-group, children unchanged; their PRESENCE and RELATIVE ORDER are pinned by the exact-equality spec — confirmed empirically since all 7 trace-mutating impls (drop/reorder/strip-gid/guard-swap) failed to close. Frame discipline holds: result = drawTrace pins the FULL ordered trace, leaving no output component free.

CONCLUSION: SOUND. ≥5 distinct wrong impls (8 attempted) run; none with a closing clean-axiom proof; the sole non-gold closing candidate (atk_8) is gold-equivalent and its faithful patch RESOLVES=True. Spec correctly excludes prepatch bug and all trace mutations. verify⇒correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real repo) — no divergence found.

### Verification performed
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) -> True (spec region byte-identical between patched and pre-patch).
- lean_verify.sh exit 0 (compiles, no sorry). `#print axioms correct_drawAnnotationBbox` -> [propext] only; NO sorryAx, proof is genuine.
- Pre-patch impl region omits both group markers (groupStart/groupEnd absent) => would NOT satisfy the identical spec; spec genuinely captures the fix, not trivially satisfiable.
- conformance_check.py: checked=120012, disagreements=0, status=pass.

MODEL vs REAL AnnotationBbox.draw (offsetbox.py:1472-1485 post-patch), input tuple (visible, posResolvable, hasArrow, clsName, gid):
- guard `not get_visible() or not _check_xy() -> return` == `if !visible || !posResolvable then []` (empty trace). ✓
- ADDED line `open_group(__class__.__name__, gid=get_gid())` (unconditional after guard) == groupStart clsName gid emitted first. ✓
- update_positions(renderer): repositions via set_offset/get_extent/get_window_extent; emits no renderer drawing op => no marker. ✓
- `if arrow_patch is not None: [figure fixup emits nothing]; arrow_patch.draw()` == `if hasArrow then [drawArrow]`. ✓
- patch.draw() unconditional == drawPatch always; offsetbox.draw() unconditional == drawOffsetbox always. ✓
- ADDED line `close_group(__class__.__name__)` (name only, no gid) == groupEnd clsName. ✓ (gid correctly carried only on the start marker, matching real open/close signatures).
- stale=False is bookkeeping, not an emitted op. ✓

ABSTRACTION ASSESSMENT (is the spec too strong?): The postcondition is an exact equality result = drawTrace(...). The three child draws (arrow/patch/offsetbox) are abstracted to single opaque markers whose PRESENCE and RELATIVE ORDER are pinned inside the enclosing group. This is a legitimate framing: the gold patch touches ONLY the enclosing group (the two added open/close lines); the children's internal sub-traces are unchanged by the patch and orthogonal to the fix. The pinned facts (group brackets carrying gid around arrow?->patch->offsetbox) exactly mirror the real emitted order. No real input produces a trace at this granularity that diverges from drawTrace. The spec is neither too strong (matches real emission order/conditions exactly) nor too weak (full ordered trace pinned; prepatch fails it).

VERDICT: FAITHFUL — the modeled function agrees with the real callee on all inputs at the modeled abstraction granularity.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical screen (swebench_unified.leakage.screen, lean flavor) passes cleanly: no diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file path (lib/matplotlib/offsetbox.py) or dotted module path, no narration terms (bug/fix/patched/...), and the only distinctive patched symbol 'draw' is already public in the problem_statement. Spec region verified byte-identical vs Solution_prepatch.lean (markers.same_spec = True). Solution.lean compiles clean (lean_verify.sh exit 0). Semantic review: the spec-view prose describes the desired correct post-patch behavior (enclosing the part-draws between a group-start marker carrying the gid and a matching group-end marker so the gid labels the group). This is exactly what a faithful behavioral spec must encode and is derivable from the PUBLIC problem_statement, which already states the AnnotationBbox gid is 'not passed to renderer', should appear in the saved SVG, and references PR #15087's group-wrapping fix for missing gids. The gold-edit specifics are NOT disclosed: no verbatim renderer.open_group(...)/close_group(...) lines, no repo callee names (open_group/close_group/get_gid), no __class__.__name__/stale, no file path, and no bug->fix diff narration; the trace uses abstract markers (groupStart/groupEnd). The group-wrapping mechanism echoes hints_text, but G-LEAK is judged against problem_statement only and the observable requirement is already public there. No leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
