# P2 adversarial audit — matplotlib__matplotlib-25960

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,16 +88,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
     List (List Rect) := Id.run do
-  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
-  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
-  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
-  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
+  let lefts := (List.range ncols).map (fun i => colLeft ncols 0 i)
+  let rights := (List.range ncols).map (fun i => colRight ncols 0 i)
+  let bottoms := (List.range nrows).map (fun j => rowBottom nrows 0 j)
+  let tops := (List.range nrows).map (fun j => rowTop nrows 0 j)
   let mut grid : List (List Rect) := []
   for j in [0:nrows] do
     let bottom := bottoms[j]!
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,16 +88,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
     List (List Rect) := Id.run do
   let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
   let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
-  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
-  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
+  let bottoms := (List.range nrows).map (fun j => rowBottom nrows 0 j)
+  let tops := (List.range nrows).map (fun j => rowTop nrows 0 j)
   let mut grid : List (List Rect) := []
   for j in [0:nrows] do
     let bottom := bottoms[j]!
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,14 +88,10 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
     List (List Rect) := Id.run do
-  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
-  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
+  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace (i+1))
+  let rights := (List.range ncols).map (fun i => colRight ncols wspace (i+1))
   let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
   let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
   let mut grid : List (List Rect) := []
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,10 +88,6 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
     List (List Rect) := Id.run do
   let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
@@ -106,7 +102,7 @@
     for i in [0:ncols] do
       let left := lefts[i]!
       let right := rights[i]!
-      row := row ++ [Rect.ofExtents left bottom right top]
+      row := [Rect.ofExtents left bottom right top] ++ row
     grid := grid ++ [row]
   return grid
 -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,27 +88,9 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
-    List (List Rect) := Id.run do
-  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
-  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
-  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
-  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
-  let mut grid : List (List Rect) := []
-  for j in [0:nrows] do
-    let bottom := bottoms[j]!
-    let top := tops[j]!
-    let mut row : List Rect := []
-    for i in [0:ncols] do
-      let left := lefts[i]!
-      let right := rights[i]!
-      row := row ++ [Rect.ofExtents left bottom right top]
-    grid := grid ++ [row]
-  return grid
+    List (List Rect) :=
+  gridRects nrows ncols wspace hspace
 -- impl-end
 
 
@@ -119,23 +101,5 @@
       problem_spec_subfigureGrid nrows ncols wspace hspace
         (implementation_subfigureGrid nrows ncols wspace hspace) := by
   intro nrows ncols wspace hspace h1 h2 h3 h4
-  have hf : ∀ {α β : Type} (f : α → β) (l : List α),
-      (l.map (fun x => [f x])).flatten = l.map f := by
-    intro α β f l
-    induction l with
-    | nil => rfl
-    | cons a t ih => simp [ih]
-  unfold problem_spec_subfigureGrid implementation_subfigureGrid gridRects
-  simp only [Id.run]
-  simp only [List.range_eq_range']
-  simp [hf]
-  apply List.map_congr_left
-  intro j hj
-  rw [List.mem_range'] at hj
-  apply List.map_congr_left
-  intro i hi
-  rw [List.mem_range'] at hi
-  rw [List.getElem?_range' (by omega : j < nrows), List.getElem?_range' (by omega : i < ncols)]
-  simp
-
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,16 +88,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
     List (List Rect) := Id.run do
-  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
-  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
-  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
-  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
+  let lefts := (List.range ncols).map (fun i => colLeft ncols hspace i)
+  let rights := (List.range ncols).map (fun i => colRight ncols hspace i)
+  let bottoms := (List.range nrows).map (fun j => rowBottom nrows wspace j)
+  let tops := (List.range nrows).map (fun j => rowTop nrows wspace j)
   let mut grid : List (List Rect) := []
   for j in [0:nrows] do
     let bottom := bottoms[j]!
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,10 +88,6 @@
 -- post-conditions-end
 
 -- impl-start
--- Faithful skeleton of the fix: first obtain the grid line positions
--- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
--- columns building, for each panel, the rectangle from those four extents
--- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
 def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
     List (List Rect) := Id.run do
   let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
@@ -100,8 +96,8 @@
   let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
   let mut grid : List (List Rect) := []
   for j in [0:nrows] do
-    let bottom := bottoms[j]!
-    let top := tops[j]!
+    let bottom := bottoms[nrows-1-j]!
+    let top := tops[nrows-1-j]!
     let mut row : List Rect := []
     for i in [0:ncols] do
       let left := lefts[i]!
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Arranging a regular grid of sub-panels inside a figure with requested spacing
between them.

A figure is divided into `nrows × ncols` sub-panels of equal share. The caller
may request a horizontal spacing `wspace` and a vertical spacing `hspace`, each a
non-negative fraction of the average panel width/height, to be left as gaps
between adjacent panels. The panels together with the gaps exactly fill the unit
square of figure-fraction coordinates `[0,1] × [0,1]`.

For a requested spacing the layout is determined as follows. Along a direction
with `k` panels and spacing `s`, every panel has the same extent
`c = 1 / (k + s·(k-1))` and consecutive panels are separated by a gap `s·c`, so
panel `i` (counting from the left/no-gap edge) starts at `i·(c + s·c)` and ends a
panel-extent later. Vertically the rows are placed from the top downwards (row
`0` is the topmost). The result lists, for each panel, its rectangle
`(x0, y0, x1, y1)` — left, bottom, right, top — in figure-fraction coordinates,
so that varying the requested spacing visibly changes the panel rectangles.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the panel-rectangle
-- geometry (the per-direction equal-extent / proportional-gap tiling of the unit
-- interval) is spelled out concretely as closed-form arithmetic on the inputs, so
-- there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- A rectangle in figure-fraction coordinates: lower-left `(x0, y0)` and
upper-right `(x1, y1)`. -/
structure Rect where
  x0 : ℚ
  y0 : ℚ
  x1 : ℚ
  y1 : ℚ
deriving DecidableEq, Repr

/-- Build a rectangle from its four extents: left, bottom, right, top. -/
def Rect.ofExtents (left bottom right top : ℚ) : Rect := ⟨left, bottom, right, top⟩

/-- The common extent of a single panel along a direction holding `k` panels with
spacing `s`: `1 / (k + s·(k-1))`. -/
def panelExtent (k : Nat) (s : ℚ) : ℚ := 1 / ((k : ℚ) + s * ((k : ℚ) - 1))

/-- The gap left between two adjacent panels: `s` times the panel extent. -/
def panelGap (k : Nat) (s : ℚ) : ℚ := s * panelExtent k s

/-- Left edge of column `i` (`0`-based from the left): `i·(extent + gap)`. -/
def colLeft (ncols : Nat) (wspace : ℚ) (i : Nat) : ℚ :=
  (i : ℚ) * (panelExtent ncols wspace + panelGap ncols wspace)

/-- Right edge of column `i`: its left edge plus one panel extent. -/
def colRight (ncols : Nat) (wspace : ℚ) (i : Nat) : ℚ :=
  colLeft ncols wspace i + panelExtent ncols wspace

/-- Top edge of row `j` (`0`-based from the top): `1 - j·(extent + gap)`. -/
def rowTop (nrows : Nat) (hspace : ℚ) (j : Nat) : ℚ :=
  1 - (j : ℚ) * (panelExtent nrows hspace + panelGap nrows hspace)

/-- Bottom edge of row `j`: its top edge minus one panel extent. -/
def rowBottom (nrows : Nat) (hspace : ℚ) (j : Nat) : ℚ :=
  rowTop nrows hspace j - panelExtent nrows hspace

/-- The full grid of panel rectangles, row-major (row `0` topmost). -/
def gridRects (nrows ncols : Nat) (wspace hspace : ℚ) : List (List Rect) :=
  (List.range nrows).map (fun j =>
    (List.range ncols).map (fun i =>
      Rect.ofExtents (colLeft ncols wspace i) (rowBottom nrows hspace j)
                     (colRight ncols wspace i) (rowTop nrows hspace j)))
-- pure-end

-- post-conditions-start
/-- A grid of `nrows × ncols` panels with horizontal spacing `wspace` and vertical
spacing `hspace` lays out exactly the rectangles `gridRects`: each panel `(j, i)`
gets the rectangle whose left/right edges are column `i`'s edges and whose
bottom/top edges are row `j`'s edges, under the equal-extent / proportional-gap
tiling of the unit square. Pinning the whole grid leaves no panel rectangle
unconstrained — the spacing necessarily shifts and shrinks every panel. -/
def problem_spec_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ)
    (result : List (List Rect)) : Prop :=
  result = gridRects nrows ncols wspace hspace
-- post-conditions-end

-- impl-start
-- Faithful skeleton of the fix: first obtain the grid line positions
-- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
-- columns building, for each panel, the rectangle from those four extents
-- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
    List (List Rect) := Id.run do
  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
  let mut grid : List (List Rect) := []
  for j in [0:nrows] do
    let bottom := bottoms[j]!
    let top := tops[j]!
    let mut row : List Rect := []
    for i in [0:ncols] do
      let left := lefts[i]!
      let right := rights[i]!
      row := row ++ [Rect.ofExtents left bottom right top]
    grid := grid ++ [row]
  return grid
-- impl-end


-- proof-start
theorem correct_subfigureGrid :
    ∀ (nrows ncols : Nat) (wspace hspace : ℚ),
      1 ≤ nrows → 1 ≤ ncols → 0 ≤ wspace → 0 ≤ hspace →
      problem_spec_subfigureGrid nrows ncols wspace hspace
        (implementation_subfigureGrid nrows ncols wspace hspace) := by
  intro nrows ncols wspace hspace h1 h2 h3 h4
  have hf : ∀ {α β : Type} (f : α → β) (l : List α),
      (l.map (fun x => [f x])).flatten = l.map f := by
    intro α β f l
    induction l with
    | nil => rfl
    | cons a t ih => simp [ih]
  unfold problem_spec_subfigureGrid implementation_subfigureGrid gridRects
  simp only [Id.run]
  simp only [List.range_eq_range']
  simp [hf]
  apply List.map_congr_left
  intro j hj
  rw [List.mem_range'] at hj
  apply List.map_congr_left
  intro i hi
  rw [List.mem_range'] at hi
  rw [List.getElem?_range' (by omega : j < nrows), List.getElem?_range' (by omega : i < ncols)]
  simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of matplotlib__matplotlib-25960 / lean. Spec is an EXACT equality: problem_spec := result = gridRects nrows ncols wspace hspace, where gridRects is a total deterministic closed form. Because exactly one result satisfies the spec per input, any in-domain-wrong impl makes correct_ a FALSE proposition, unprovable with clean axioms — the structural reason no verify-not-correct gap can exist here.

SAME-SPEC: all 7 attacks pass swebench_unified.markers.same_spec (spec regions byte-frozen; only impl+proof edited). Positive control pos.lean = untouched Solution.lean verifies (exit 0).

### ATTACKS (cmd: bash scripts/lean_verify.sh atk_N.lean):
- atk_1 prepatch gapless (colLeft ncols 0 i etc; spacing dropped): exit 1, unsolved goals — does NOT close. Reproduces the prepatch bug.
- atk_2 partial-domain (honor wspace, drop hspace): exit 1, unsolved goals.
- atk_3 boundary off-by-one (column index i+1): exit 1, unsolved goals.
- atk_4 control-flow-effect (reverse each row via prepend): exit 1, apply List.map_congr_left unify fail.
- atk_5 ungrounded-oracle echo (impl := gridRects nrows ncols wspace hspace; proof by rfl): exit 0, VERIFIES. #print axioms correct_subfigureGrid = [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx.
- atk_6 swap wspace/hspace (cols use hspace, rows use wspace): exit 1, unsolved goals.
- atk_7 row-reflect (bottoms/tops[nrows-1-j]): exit 1, rewrite pattern-not-found.

RESOLVE (protocol step 2): the only clean-closing impl is atk_5, which is behaviorally IDENTICAL to the gold patch (returns gridRects, the exact layout gold produces). Its faithful materialization = the gold-behavior patch. run_resolve('matplotlib__matplotlib-25960', <patch>, run_id='sbu-atk5-echo') => RESOLVED=True, completed=True. So the one closing clean-axiom impl HAS a materialized faithful patch that RESOLVES. No verify-not-correct witness found.

A-REFERENCE AUDIT (refinement.md leg #3, the only non-R/I leg): gridRects/panelExtent/panelGap/colLeft/... ↔ real GridSpec.get_grid_positions with the fix's margins left=0,right=1,bottom=0,top=1 and equal ratios. Independently validated against the REAL patched matplotlib: built GridSpec + called get_grid_positions on[F2P],,[single row],[single col],[large spacing] — ALL match=True to 1e-9 vs the closed-form gridRects. F2P shadow matches mapping.md exactly: lefts [0,7/20,7/10], rights [3/10,13/20,1], tops [1,2/5], bottoms [3/5,0]. Deep model is faithful; A-reference holds.

REFINEMENT LEG AUDIT: axioms block EMPTY — no A-consumed legs, hence no kind-3 (consumed-axiom-without-proof) legs. Legs #1,#2 = R (float→ℚ; SubFigure→Rect), #3 = A-reference (validated above), #4,#5 = I (nested zip walk↔for-loop; Bbox.from_extents↔Rect.ofExtents / _redo_transform_rel_fig storing bbox). All legs are R / A-reference / I. Clean.

VERDICT: SOUND. 7 attacks run (≥5 distinct wrong impls: partial-domain, boundary, control-flow, swap, row-reflect, prepatch-gapless — all fail to close). The single closing clean-axiom impl (echo) resolves. A-reference independently validated faithful. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Arranging a regular grid of sub-panels inside a figure with requested spacing
between them.

A figure is divided into `nrows × ncols` sub-panels of equal share. The caller
may request a horizontal spacing `wspace` and a vertical spacing `hspace`, each a
non-negative fraction of the average panel width/height, to be left as gaps
between adjacent panels. The panels together with the gaps exactly fill the unit
square of figure-fraction coordinates `[0,1] × [0,1]`.

For a requested spacing the layout is determined as follows. Along a direction
with `k` panels and spacing `s`, every panel has the same extent
`c = 1 / (k + s·(k-1))` and consecutive panels are separated by a gap `s·c`, so
panel `i` (counting from the left/no-gap edge) starts at `i·(c + s·c)` and ends a
panel-extent later. Vertically the rows are placed from the top downwards (row
`0` is the topmost). The result lists, for each panel, its rectangle
`(x0, y0, x1, y1)` — left, bottom, right, top — in figure-fraction coordinates,
so that varying the requested spacing visibly changes the panel rectangles.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the panel-rectangle
-- geometry (the per-direction equal-extent / proportional-gap tiling of the unit
-- interval) is spelled out concretely as closed-form arithmetic on the inputs, so
-- there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- A rectangle in figure-fraction coordinates: lower-left `(x0, y0)` and
upper-right `(x1, y1)`. -/
structure Rect where
  x0 : ℚ
  y0 : ℚ
  x1 : ℚ
  y1 : ℚ
deriving DecidableEq, Repr

/-- Build a rectangle from its four extents: left, bottom, right, top. -/
def Rect.ofExtents (left bottom right top : ℚ) : Rect := ⟨left, bottom, right, top⟩

/-- The common extent of a single panel along a direction holding `k` panels with
spacing `s`: `1 / (k + s·(k-1))`. -/
def panelExtent (k : Nat) (s : ℚ) : ℚ := 1 / ((k : ℚ) + s * ((k : ℚ) - 1))

/-- The gap left between two adjacent panels: `s` times the panel extent. -/
def panelGap (k : Nat) (s : ℚ) : ℚ := s * panelExtent k s

/-- Left edge of column `i` (`0`-based from the left): `i·(extent + gap)`. -/
def colLeft (ncols : Nat) (wspace : ℚ) (i : Nat) : ℚ :=
  (i : ℚ) * (panelExtent ncols wspace + panelGap ncols wspace)

/-- Right edge of column `i`: its left edge plus one panel extent. -/
def colRight (ncols : Nat) (wspace : ℚ) (i : Nat) : ℚ :=
  colLeft ncols wspace i + panelExtent ncols wspace

/-- Top edge of row `j` (`0`-based from the top): `1 - j·(extent + gap)`. -/
def rowTop (nrows : Nat) (hspace : ℚ) (j : Nat) : ℚ :=
  1 - (j : ℚ) * (panelExtent nrows hspace + panelGap nrows hspace)

/-- Bottom edge of row `j`: its top edge minus one panel extent. -/
def rowBottom (nrows : Nat) (hspace : ℚ) (j : Nat) : ℚ :=
  rowTop nrows hspace j - panelExtent nrows hspace

/-- The full grid of panel rectangles, row-major (row `0` topmost). -/
def gridRects (nrows ncols : Nat) (wspace hspace : ℚ) : List (List Rect) :=
  (List.range nrows).map (fun j =>
    (List.range ncols).map (fun i =>
      Rect.ofExtents (colLeft ncols wspace i) (rowBottom nrows hspace j)
                     (colRight ncols wspace i) (rowTop nrows hspace j)))
-- pure-end

-- post-conditions-start
/-- A grid of `nrows × ncols` panels with horizontal spacing `wspace` and vertical
spacing `hspace` lays out exactly the rectangles `gridRects`: each panel `(j, i)`
gets the rectangle whose left/right edges are column `i`'s edges and whose
bottom/top edges are row `j`'s edges, under the equal-extent / proportional-gap
tiling of the unit square. Pinning the whole grid leaves no panel rectangle
unconstrained — the spacing necessarily shifts and shrinks every panel. -/
def problem_spec_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ)
    (result : List (List Rect)) : Prop :=
  result = gridRects nrows ncols wspace hspace
-- post-conditions-end

-- impl-start
-- Faithful skeleton of the fix: first obtain the grid line positions
-- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
-- columns building, for each panel, the rectangle from those four extents
-- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
    List (List Rect) := Id.run do
  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
  let mut grid : List (List Rect) := []
  for j in [0:nrows] do
    let bottom := bottoms[j]!
    let top := tops[j]!
    let mut row : List Rect := []
    for i in [0:ncols] do
      let left := lefts[i]!
      let right := rights[i]!
      row := row ++ [Rect.ofExtents left bottom right top]
    grid := grid ++ [row]
  return grid
-- impl-end


-- proof-start
theorem correct_subfigureGrid :
    ∀ (nrows ncols : Nat) (wspace hspace : ℚ),
      1 ≤ nrows → 1 ≤ ncols → 0 ≤ wspace → 0 ≤ hspace →
      problem_spec_subfigureGrid nrows ncols wspace hspace
        (implementation_subfigureGrid nrows ncols wspace hspace) := by
  intro nrows ncols wspace hspace h1 h2 h3 h4
  have hf : ∀ {α β : Type} (f : α → β) (l : List α),
      (l.map (fun x => [f x])).flatten = l.map f := by
    intro α β f l
    induction l with
    | nil => rfl
    | cons a t ih => simp [ih]
  unfold problem_spec_subfigureGrid implementation_subfigureGrid gridRects
  simp only [Id.run]
  simp only [List.range_eq_range']
  simp [hf]
  apply List.map_congr_left
  intro j hj
  rw [List.mem_range'] at hj
  apply List.map_congr_left
  intro i hi
  rw [List.mem_range'] at hi
  rw [List.getElem?_range' (by omega : j < nrows), List.getElem?_range' (by omega : i < ncols)]
  simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of matplotlib__matplotlib-25960 / lean. Spec is an EXACT equality: problem_spec := result = gridRects nrows ncols wspace hspace, where gridRects is a total deterministic closed form. Because exactly one result satisfies the spec per input, any in-domain-wrong impl makes correct_ a FALSE proposition, unprovable with clean axioms — the structural reason no verify-not-correct gap can exist here.

SAME-SPEC: all 7 attacks pass swebench_unified.markers.same_spec (spec regions byte-frozen; only impl+proof edited). Positive control pos.lean = untouched Solution.lean verifies (exit 0).

### ATTACKS (cmd: bash scripts/lean_verify.sh atk_N.lean):
- atk_1 prepatch gapless (colLeft ncols 0 i etc; spacing dropped): exit 1, unsolved goals — does NOT close. Reproduces the prepatch bug.
- atk_2 partial-domain (honor wspace, drop hspace): exit 1, unsolved goals.
- atk_3 boundary off-by-one (column index i+1): exit 1, unsolved goals.
- atk_4 control-flow-effect (reverse each row via prepend): exit 1, apply List.map_congr_left unify fail.
- atk_5 ungrounded-oracle echo (impl := gridRects nrows ncols wspace hspace; proof by rfl): exit 0, VERIFIES. #print axioms correct_subfigureGrid = [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx.
- atk_6 swap wspace/hspace (cols use hspace, rows use wspace): exit 1, unsolved goals.
- atk_7 row-reflect (bottoms/tops[nrows-1-j]): exit 1, rewrite pattern-not-found.

RESOLVE (protocol step 2): the only clean-closing impl is atk_5, which is behaviorally IDENTICAL to the gold patch (returns gridRects, the exact layout gold produces). Its faithful materialization = the gold-behavior patch. run_resolve('matplotlib__matplotlib-25960', <patch>, run_id='sbu-atk5-echo') => RESOLVED=True, completed=True. So the one closing clean-axiom impl HAS a materialized faithful patch that RESOLVES. No verify-not-correct witness found.

A-REFERENCE AUDIT (refinement.md leg #3, the only non-R/I leg): gridRects/panelExtent/panelGap/colLeft/... ↔ real GridSpec.get_grid_positions with the fix's margins left=0,right=1,bottom=0,top=1 and equal ratios. Independently validated against the REAL patched matplotlib: built GridSpec + called get_grid_positions on[F2P],,[single row],[single col],[large spacing] — ALL match=True to 1e-9 vs the closed-form gridRects. F2P shadow matches mapping.md exactly: lefts [0,7/20,7/10], rights [3/10,13/20,1], tops [1,2/5], bottoms [3/5,0]. Deep model is faithful; A-reference holds.

REFINEMENT LEG AUDIT: axioms block EMPTY — no A-consumed legs, hence no kind-3 (consumed-axiom-without-proof) legs. Legs #1,#2 = R (float→ℚ; SubFigure→Rect), #3 = A-reference (validated above), #4,#5 = I (nested zip walk↔for-loop; Bbox.from_extents↔Rect.ofExtents / _redo_transform_rel_fig storing bbox). All legs are R / A-reference / I. Clean.

VERDICT: SOUND. 7 attacks run (≥5 distinct wrong impls: partial-domain, boundary, control-flow, swap, row-reflect, prepatch-gapless — all fail to close). The single closing clean-axiom impl (echo) resolves. A-reference independently validated faithful. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift audit of the Lean spec vs. the real matplotlib callee (GridSpec.get_grid_positions) for the subfigures wspace/hspace fix.

MODEL: problem_spec_subfigureGrid pins result == gridRects nrows ncols wspace hspace, where gridRects uses panelExtent k s = 1/(k+s*(k-1)), panelGap = s*extent, colLeft i = i*(extent+gap), colRight = colLeft+extent, rowTop j = 1 - j*(extent+gap), rowBottom = rowTop-extent. This mirrors the fix (build GridSpec with left=0,right=1,bottom=0,top=1; call get_grid_positions; assemble Bbox.from_extents per panel).

STRUCTURAL CHECK: Confirmed the real get_grid_positions(raw=False) reads left/right/bottom/top from get_subplot_params, which for the fix's GridSpec are pinned to 0/1/0/1 => tot_width=tot_height=1. With equal (default) width/height ratios, norm*ratio_i == cell for every i, so cell_widths are all `cell` and cell_ws cumsum = 0,cell,cell+sep,2cell+sep,... => left_i=i*(cell+sep), right_i=left_i+cell; symmetric for rows from the top. Exactly gridRects.

EMPIRICAL CHECK: Ran the real matplotlib GridSpec.get_grid_positions against the Lean closed form. F2P (2,3,wspace=1/6,hspace=1/2) matches exactly (lefts [0,7/20,7/10], rights [3/10,13/20,1], tops [1,2/5], bottoms [3/5,0]). Four edge cases (1x1 zero-spacing, 3x2 large spacing, 1x4, 2x2) match. Fuzzed 3000 random (nrows,ncols in 1..6, wspace/hspace rational in [0,30]) inputs: 0 mismatches, agreement <1e-9. Spec is neither too strong nor drifting; no diverging input found.

SCOPE: model is the no-layout-engine + spacing-requested branch (the branch the fix adds and the F2P exercises); constrained-layout path (raw=True) is explicitly out of scope and documented in mapping.md. Correct scoping, not a drift.

LEAN INTEGRITY: scripts/lean_verify.sh exit 0 (compiles, no sorry). #print axioms correct_subfigureGrid => [propext, Classical.choice, Quot.sound] only; no sorryAx, proof genuine.

SPEC REGION: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) == True; only impl region differs (patched uses wspace/hspace; prepatch forces 0), spec/pure/post-conditions byte-identical. Prepatch impl (spacing dropped) evaluates result != gridRects on positive spacing, so G-DIFF correctly fires.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) Mechanical screen: leakage.screen(Solution.lean, lean, gold_patch, problem_statement) returns passed=True, hard_failures=[] — no diff markers, no reproduced gold-patch line (min-8-char normalized), no patched file path 'lib/matplotlib/figure.py' or dotted module, no spec-view identifier embedding a patched repo symbol, no narration keywords. (2) Byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — spec region (docstring/axioms/pure/post-conditions) identical across post/prepatch; only impl and proof regions differ, and the spec view elides both to placeholders. (3) Semantic review: the public problem_statement discloses only the BUG ('wspace and hspace in Figure.subfigures do nothing') plus the intended semantics ('a fraction of the average subfigure width/height'), not the fix. The gold edit is code-level mechanics — GridSpec built with left=0,right=1,bottom=0,top=1; guard get_layout_engine() is None and (wspace/hspace not None); gs.get_grid_positions(self); Bbox.from_extents(...) applied via sf._redo_transform_rel_fig(bbox=...). The spec view names NONE of these callees, symbols, or branch conditions. It contains only the closed-form target OUTPUT geometry (panelExtent=1/(k+s(k-1)), panelGap=s*c, colLeft/colRight/rowTop/rowBottom, gridRects postcondition) — the legitimate mathematical statement of desired behavior, consistent with the public docstring's 'fraction of average width/height'. The implementation skeleton (obtain lefts/rights/bottoms/tops then walk rows/cols) lives entirely in the elided impl region. A solver must still independently discover the GridSpec-full-extents + get_grid_positions + _redo_transform_rel_fig call path. No spec-view line reconstructs the gold edit beyond the public problem_statement. Bundle is not relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so the strict standard applies and is met.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
