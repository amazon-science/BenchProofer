# P2 adversarial audit — matplotlib__matplotlib-25960

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc1.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -82,8 +82,14 @@
   ensures out = axisExtents n s
   do
     -- impl-start
+    -- Pre-image: the requested gap fraction `s` is dropped on the floor. The
+    -- cells are laid out as a plain even split of the unit interval — pitch and
+    -- size both `1 / n`, regardless of `s` — so consecutive cells ABUT. This is
+    -- the bug: any positive `s` is ignored, so the extents MUST differ from
+    -- `axisExtents n s` (which spaces the cells) whenever `s > 0`.
+    let evenSize : Rat := 1 / (n : Rat)
     let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+      (fun (i : Nat) => ((i : Rat) * evenSize, (i : Rat) * evenSize + evenSize))
     return extents
     -- impl-end
 
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -82,7 +82,7 @@
   ensures out = axisExtents n s
   do
     -- impl-start
-    let extents := (List.range n).map
+    let extents := (List.range (n+1)).map
       (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
     return extents
     -- impl-end
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -83,7 +83,7 @@
   do
     -- impl-start
     let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+      (fun (i : Nat) => ((i : Rat) * cellSize n s, (i : Rat) * cellSize n s + cellSize n s))
     return extents
     -- impl-end
 
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -83,7 +83,7 @@
   do
     -- impl-start
     let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+      (fun (i : Nat) => ((i : Rat) * cellPitch n s + cellSize n s, (i : Rat) * cellPitch n s))
     return extents
     -- impl-end
 
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -83,7 +83,7 @@
   do
     -- impl-start
     let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+      (fun (_i : Nat) => ((0 : Rat), cellSize n s))
     return extents
     -- impl-end
 
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -82,8 +82,8 @@
   ensures out = axisExtents n s
   do
     -- impl-start
-    let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+    let extents := ((List.range n).map
+      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))).reverse
     return extents
     -- impl-end
 
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -82,8 +82,12 @@
   ensures out = axisExtents n s
   do
     -- impl-start
-    let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+    let extents := if n = 1 then
+        (List.range n).map
+          (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+      else
+        (List.range n).map
+          (fun (i : Nat) => ((i : Rat) * (1 / (n : Rat)), (i : Rat) * (1 / (n : Rat)) + (1 / (n : Rat))))
     return extents
     -- impl-end
 
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
 -- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
@@ -82,8 +82,7 @@
   ensures out = axisExtents n s
   do
     -- impl-start
-    let extents := (List.range n).map
-      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
+    let extents := axisExtents n (2 * s)
     return extents
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc1.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
--  the `pure` region — `cellSize`/`cellPitch`/`axisExtents` ARE the layout
--  computation, an A-reference validated == the real grid-position routine by
--  axiom_check.py (G-AX). No consumed axiom borrows soundness from it.)
-- axioms-end

-- pure-start
/- A row (or column) of `n` equally-sized cells is laid out along the unit
   interval `[0, 1]`, leaving a uniform gap between adjacent cells. The gap is
   expressed as a fraction `s` of a single cell's size: between every pair of
   neighbouring cells a separation of `s` times the cell size is inserted.

   With `n` cells and `n - 1` such gaps the interval must accommodate a total
   length of `n + s·(n-1)` cell-sizes, so each cell occupies a fraction

       cellSize n s = 1 / (n + s·(n-1)).

   For `n ≥ 1` the denominator is at least `1`, so the size is well defined and
   strictly positive. With no gap (`s = 0`) this is the even split `1 / n`. -/
def cellSize (n : Nat) (s : Rat) : Rat :=
  1 / ((n : Rat) + s * ((n : Rat) - 1))

/- The centre-to-centre stride from one cell's low edge to the next: a full
   cell plus the separation that follows it, i.e. `cellSize · (1 + s)`. When the
   gap fraction is zero this collapses to the cell size itself (cells abut). -/
def cellPitch (n : Nat) (s : Rat) : Rat :=
  cellSize n s * (1 + s)

/- The closed extents `(low, high)` of every cell of the axis, in order from the
   low end. Cell `i` starts at `i` strides in and spans one cell size:

       low i  = i · cellPitch n s,
       high i = low i + cellSize n s.

   The result is the per-cell expansion of the index range `0 .. n-1`: exactly
   `n` extents, the `i`-th being the interval reserved for cell `i`. -/
def axisExtents (n : Nat) (s : Rat) : List (Rat × Rat) :=
  (List.range n).map
    (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Lay out `n` equally-sized cells along the unit axis with a uniform gap of
   fraction `s` between neighbours, and return each cell's `(low, high)` extent
   in order from the low end.

   The guarantees pin the behaviour the issue demands — that the requested gap
   actually reserves space between cells, instead of being silently dropped so
   the cells abut:

   - there are exactly `n` extents, one per cell (`out.length = n`);
   - the `i`-th extent is exactly `(i · cellPitch n s, i · cellPitch n s +
     cellSize n s)`. Because the pitch carries the `(1 + s)` factor, a non-zero
     gap genuinely separates consecutive cells — `high` of cell `i` is strictly
     below `low` of cell `i+1` whenever `s > 0`. An even split that ignores `s`
     cannot satisfy this for any positive gap.

   `n` and `s` are read-only inputs (not `mut`); the operation derives the
   extent list and mutates nothing (directive 5). The extents are modeled as
   exact rationals (`Rat`): the discriminating behaviour is the proportional
   placement of cell edges, an exact ratio computation that is
   precision-independent (the gap fraction multiplies, it never accumulates
   round-off across cells), so an exact ordered carrier is faithful. -/
method axisCellExtents (n : Nat) (s : Rat) return (out : List (Rat × Rat))
  require n ≥ 1
  require s ≥ 0
  ensures out.length = n
  ensures out = axisExtents n s
  do
    -- impl-start
    let extents := (List.range n).map
      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
    return extents
    -- impl-end

prove_correct axisCellExtents by
  loom_solve
  simp [axisExtents]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a maximally-tight exact functional equality: `ensures out = axisExtents n s` + `ensures out.length = n` over concrete computable `pure` defs (cellSize/cellPitch/axisExtents). No consumed axioms; the lone A-reference is the deep model axisExtents == real GridSpec.get_grid_positions.

### Protocol executed

same_spec=True for ALL 10 files (8 attacks + pc1 + pc2), verified via swebench_unified.markers.same_spec / get_backend('velvet').language.

Verify cmd (concurrent, <=4 at a time): `bash scripts/lean_verify.sh <file>`
- atk_1 (prepatch bug: even split 1/n, drops s): EXIT=1. Fails `ensures_1`, residual `forall a<n, a*(1/n) = a*cellPitch n s ...` false for s>0. PREPATCH REPRODUCED.
- atk_2 (off-by-one: range (n+1)): EXIT=1. Fails ensures_1 (map range(n+1)!=range n) AND ensures_2 (length=n).
- atk_3 (control-flow-effect: pitch=cellSize, drop (1+s), cells abut): EXIT=1. Fails ensures_1, `a*cellSize = a*cellPitch` false for s>0.
- atk_4 (boundary: low/high swapped): EXIT=1. Fails ensures_1.
- atk_5 (ungrounded-oracle echo: constant (0,cellSize) replicate): EXIT=1. Fails ensures_1.
- atk_6 (reversed list): EXIT=1. Fails ensures_1 (.reverse != identity).
- atk_7 (partial-domain: correct only at n=1, even-split otherwise): EXIT=1. Fails ensures_1 branch `not n=1 -> ...`.
- atk_8 (arg-tampered oracle echo: axisExtents n (2*s), correct only at s=0): EXIT=1. Fails ensures_1 AND ensures_2.
All 8 fail on the discriminating `ensures_1: out = axisExtents n s` clause (2 also on ensures_2) - correct-reason rejections, not automation/syntax glitches.

Positive controls verify (EXIT=0): pc1 = gold-corresponding impl (byte-identical to Solution.lean impl), pc2 = `return axisExtents n s` (structurally distinct). Spec is non-vacuous.

NO VERIFYING WRONG IMPL EXISTS -> patches map is empty; the 'materialize faithful patch + run_resolve' clause is vacuously satisfied (nothing to resolve). Because the postcondition is exact functional equality over concrete pure defs, ANY verifying impl produces exactly axisExtents n s; the only residual verify=>correct risk is an A-reference divergence.

A-REFERENCE FALSIFICATION (the real attack surface): axiom_check.py run against REAL matplotlib 3.6.3 -> `G-AX OK ... 3297 configs`, EXIT=0 (cols==lefts/rights, rows==reverse(bottoms/tops), incl. exact F2P params nrows=2,ncols=3,hspace=1/2,wspace=1/6). Independently reproduced the F2P test's expected bbox fractions from the model: cols (0,.3)(.35,.65)(.7,1), rows reversed (.6,1)(0,.4) - exact match to test_subfigures_wspace_hspace assertions. A-reference holds; verify=>correct.

REFINEMENT.MD LEG AUDIT: A1=R (int<->Nat, float<->Rat), A2=A-reference+I (deep model == get_grid_positions; fold ops I), A3=A-reference+R+I (extent list + Bbox/_redo identity + row reversal R), A4=R (per-axis count). Sec B: no consumed axioms. Sec C: no kind-3. Every leg is R / A-reference / I; A-reference correspondence to the real callee validated by G-AX. No kind-3, no dead/over-claimed axiom.

VERDICT: SOUND. >=5 distinct attacks (8 run) all refuted for the right reason; positive controls verify; A-reference validated against real callee + F2P; refinement legs clean. No verifying-wrong-impl to break the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc1.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc1.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
--  the `pure` region — `cellSize`/`cellPitch`/`axisExtents` ARE the layout
--  computation, an A-reference validated == the real grid-position routine by
--  axiom_check.py (G-AX). No consumed axiom borrows soundness from it.)
-- axioms-end

-- pure-start
/- A row (or column) of `n` equally-sized cells is laid out along the unit
   interval `[0, 1]`, leaving a uniform gap between adjacent cells. The gap is
   expressed as a fraction `s` of a single cell's size: between every pair of
   neighbouring cells a separation of `s` times the cell size is inserted.

   With `n` cells and `n - 1` such gaps the interval must accommodate a total
   length of `n + s·(n-1)` cell-sizes, so each cell occupies a fraction

       cellSize n s = 1 / (n + s·(n-1)).

   For `n ≥ 1` the denominator is at least `1`, so the size is well defined and
   strictly positive. With no gap (`s = 0`) this is the even split `1 / n`. -/
def cellSize (n : Nat) (s : Rat) : Rat :=
  1 / ((n : Rat) + s * ((n : Rat) - 1))

/- The centre-to-centre stride from one cell's low edge to the next: a full
   cell plus the separation that follows it, i.e. `cellSize · (1 + s)`. When the
   gap fraction is zero this collapses to the cell size itself (cells abut). -/
def cellPitch (n : Nat) (s : Rat) : Rat :=
  cellSize n s * (1 + s)

/- The closed extents `(low, high)` of every cell of the axis, in order from the
   low end. Cell `i` starts at `i` strides in and spans one cell size:

       low i  = i · cellPitch n s,
       high i = low i + cellSize n s.

   The result is the per-cell expansion of the index range `0 .. n-1`: exactly
   `n` extents, the `i`-th being the interval reserved for cell `i`. -/
def axisExtents (n : Nat) (s : Rat) : List (Rat × Rat) :=
  (List.range n).map
    (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Lay out `n` equally-sized cells along the unit axis with a uniform gap of
   fraction `s` between neighbours, and return each cell's `(low, high)` extent
   in order from the low end.

   The guarantees pin the behaviour the issue demands — that the requested gap
   actually reserves space between cells, instead of being silently dropped so
   the cells abut:

   - there are exactly `n` extents, one per cell (`out.length = n`);
   - the `i`-th extent is exactly `(i · cellPitch n s, i · cellPitch n s +
     cellSize n s)`. Because the pitch carries the `(1 + s)` factor, a non-zero
     gap genuinely separates consecutive cells — `high` of cell `i` is strictly
     below `low` of cell `i+1` whenever `s > 0`. An even split that ignores `s`
     cannot satisfy this for any positive gap.

   `n` and `s` are read-only inputs (not `mut`); the operation derives the
   extent list and mutates nothing (directive 5). The extents are modeled as
   exact rationals (`Rat`): the discriminating behaviour is the proportional
   placement of cell edges, an exact ratio computation that is
   precision-independent (the gap fraction multiplies, it never accumulates
   round-off across cells), so an exact ordered carrier is faithful. -/
method axisCellExtents (n : Nat) (s : Rat) return (out : List (Rat × Rat))
  require n ≥ 1
  require s ≥ 0
  ensures out.length = n
  ensures out = axisExtents n s
  do
    -- impl-start
    let extents := (List.range n).map
      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
    return extents
    -- impl-end

prove_correct axisCellExtents by
  loom_solve
  simp [axisExtents]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a maximally-tight exact functional equality: `ensures out = axisExtents n s` + `ensures out.length = n` over concrete computable `pure` defs (cellSize/cellPitch/axisExtents). No consumed axioms; the lone A-reference is the deep model axisExtents == real GridSpec.get_grid_positions.

### Protocol executed

same_spec=True for ALL 10 files (8 attacks + pc1 + pc2), verified via swebench_unified.markers.same_spec / get_backend('velvet').language.

Verify cmd (concurrent, <=4 at a time): `bash scripts/lean_verify.sh <file>`
- atk_1 (prepatch bug: even split 1/n, drops s): EXIT=1. Fails `ensures_1`, residual `forall a<n, a*(1/n) = a*cellPitch n s ...` false for s>0. PREPATCH REPRODUCED.
- atk_2 (off-by-one: range (n+1)): EXIT=1. Fails ensures_1 (map range(n+1)!=range n) AND ensures_2 (length=n).
- atk_3 (control-flow-effect: pitch=cellSize, drop (1+s), cells abut): EXIT=1. Fails ensures_1, `a*cellSize = a*cellPitch` false for s>0.
- atk_4 (boundary: low/high swapped): EXIT=1. Fails ensures_1.
- atk_5 (ungrounded-oracle echo: constant (0,cellSize) replicate): EXIT=1. Fails ensures_1.
- atk_6 (reversed list): EXIT=1. Fails ensures_1 (.reverse != identity).
- atk_7 (partial-domain: correct only at n=1, even-split otherwise): EXIT=1. Fails ensures_1 branch `not n=1 -> ...`.
- atk_8 (arg-tampered oracle echo: axisExtents n (2*s), correct only at s=0): EXIT=1. Fails ensures_1 AND ensures_2.
All 8 fail on the discriminating `ensures_1: out = axisExtents n s` clause (2 also on ensures_2) - correct-reason rejections, not automation/syntax glitches.

Positive controls verify (EXIT=0): pc1 = gold-corresponding impl (byte-identical to Solution.lean impl), pc2 = `return axisExtents n s` (structurally distinct). Spec is non-vacuous.

NO VERIFYING WRONG IMPL EXISTS -> patches map is empty; the 'materialize faithful patch + run_resolve' clause is vacuously satisfied (nothing to resolve). Because the postcondition is exact functional equality over concrete pure defs, ANY verifying impl produces exactly axisExtents n s; the only residual verify=>correct risk is an A-reference divergence.

A-REFERENCE FALSIFICATION (the real attack surface): axiom_check.py run against REAL matplotlib 3.6.3 -> `G-AX OK ... 3297 configs`, EXIT=0 (cols==lefts/rights, rows==reverse(bottoms/tops), incl. exact F2P params nrows=2,ncols=3,hspace=1/2,wspace=1/6). Independently reproduced the F2P test's expected bbox fractions from the model: cols (0,.3)(.35,.65)(.7,1), rows reversed (.6,1)(0,.4) - exact match to test_subfigures_wspace_hspace assertions. A-reference holds; verify=>correct.

REFINEMENT.MD LEG AUDIT: A1=R (int<->Nat, float<->Rat), A2=A-reference+I (deep model == get_grid_positions; fold ops I), A3=A-reference+R+I (extent list + Bbox/_redo identity + row reversal R), A4=R (per-axis count). Sec B: no consumed axioms. Sec C: no kind-3. Every leg is R / A-reference / I; A-reference correspondence to the real callee validated by G-AX. No kind-3, no dead/over-claimed axiom.

VERDICT: SOUND. >=5 distinct attacks (8 run) all refuted for the right reason; positive controls verify; A-reference validated against real callee + F2P; refinement legs clean. No verifying-wrong-impl to break the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / model-vs-real-callee drift) attack: NO defect found. (1) same_spec(Solution, Solution_prepatch, velvet)==True — the frozen spec region is byte-identical; only the impl region differs (postpatch spacing-aware extents vs prepatch even-split 1/n). (2) Solution.lean elaborates clean via lean_verify.sh (exit 0), so the impl truly satisfies `ensures out = axisExtents n s` and `out.length = n`. Faithfulness of the deep model `axisExtents n s` (from cellSize=1/(n+s(n-1)), cellPitch=cellSize*(1+s)) to the REAL matplotlib.gridspec.GridSpec.get_grid_positions under the patch-supplied margins left=0,right=1,bottom=0,top=1 and equal ratios: verified against installed matplotlib 3.6.3 (worktree). Bundle axiom_check.py -> OK on 3297 configs. Independent broad fuzz (8000+ configs, n up to 500, s up to 1000 and down to 1e-6, seed varied) -> ZERO mismatches. Worst-case large-n float cumsum stress -> max abs deviation 2e-14 (ULP noise). The reduced closed form lefts[i]=i*cell_w*(1+wspace), rights[i]=lefts[i]+cell_w matches axisExtents exactly (norm=1 with equal ratios); row axis correctly modeled as reverse(axisExtents(nrows,hspace)) for top-origin indexing. No input in the spec domain (n>=1, s>=0) makes the modeled function disagree with the real callee beyond float rounding. The spec is not too strong and does not drift: it faithfully pins the gold spacing-aware placement and correctly refutes the prepatch even split (residual goal false for s!=0). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view = axioms+pure+pre/post regions + method signature (impl and prove_correct bodies elided). same_spec(Solution, Solution_prepatch)=True; spec regions byte-identical. Mechanical leakage.screen() PASSES (0 hard_failures). Checked against public problem_statement ONLY (not hints_text).

WHAT vs HOW: The public problem_statement already states the intended behavior — wspace/hspace should reserve space between subfigures 'expressed as a fraction of the average subfigure width/height' (via the linked docstring) and currently 'do nothing'. The spec view models exactly that required behavior arithmetically: cellSize=1/(n+s(n-1)), cellPitch=cellSize*(1+s), axisExtents = per-cell (low,high) with a (1+s) pitch that separates cells when s>0. This is the WHAT (the gap-aware layout the issue demands), derivable from the public statement.

The gold edit is a MECHANISM that is NOT reconstructable from the spec view: GridSpec(..., left=0,right=1,bottom=0,top=1); gs.get_grid_positions(self); Bbox.from_extents; sf._redo_transform_rel_fig(bbox=...); the nested zip loops; the `get_layout_engine() is None` guard. None of these callee names, margin literals, loop structure, class names (GridSpec/Bbox), or the patched file path (lib/matplotlib/figure.py) / symbol appear anywhere in the spec view. The only changed repo symbol, `subfigures`, is public. Crucially the closed-form 1/(n+s(n-1)) lives in the UNCHANGED callee get_grid_positions, not in the patch hunk — so it reflects pre-existing repo behavior, not the edit.

Comments reference 'grid-position arithmetic/routine' only descriptively (concept), never the verbatim get_grid_positions symbol. mapping.md/refinement.md do name get_grid_positions, Bbox, figure.py etc., but those are auditor docs explicitly scoped 'not in the consumer spec view' and are not part of the G-LEAK spec view. No L1/L2/L3/L5 hits; no gold-edit reconstruction beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
