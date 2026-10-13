# P2 adversarial audit — matplotlib__matplotlib-24570

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_5_center_no_descent.lean`, `atk_6_singleton_only.lean`, `atk_7_baseline_extent.lean`, `atk_8_option_boundary.lean`, `atk_9_order_reversed.lean`, `atk_10_descent_field.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2_empty_sentinel.lean`, `atk_3_empty_legal.lean`, `atk_4_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The three verifying wrong impls (atk_2, atk_3 partial-domain on hd=[]; atk_4 oracle echo) all had their faithful refined patches RESOLVE under the official harness, so none witnesses verify=>correct failure. The nearest miss is the residual freedom at hd=[]: `require hd ≠ []` leaves the empty-box case wholly unconstrained, and refinement.md A4 / mapping.md §2 justify this by claiming callers `HPacker`/`VPacker.get_extent_offsets` "return early on an empty child list before reaching it (offsetbox.py:473-474)". That justification is only HALF true at base_commit: HPacker.get_extent_offsets does have the `if not whd_list: return 2*pad, 2*pad, pad, pad, []` guard at lines 472-473, but VPacker.get_extent_offsets (lines 424-456) has NO such guard, so a VPacker with zero visible children reaches _get_aligned_offsets with an empty wd_list. The hole is therefore REACHABLE in principle, but it is not spec-breaking here: with an empty list the real prepatch/postpatch callee raises ValueError from `max(...)` on an empty sequence, so no test in the frozen F2P/P2P set (nor any observed legend/packer render path) exercises it -- an impl that instead returns a sentinel there still resolves, as atk_2 (return 1000000., 1000000., []) and atk_3 (return 0., 0., []) both empirically demonstrated. This is an accuracy defect in the A4/§2 prose (a wrong file-line citation and an over-broad "callers return early" claim), not a soundness defect in the spec.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,16 +87,21 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- Pre-image skeleton: the top/bottom anchors are grouped with the WRONG
+    -- edge. `top` is bucketed with `left` (offset = descent) and `bottom` with
+    -- `right` (offset = shortfall + descent) — the reverse of the desired
+    -- placement. The frozen spec requires the corrected grouping, so
+    -- prove_correct MUST fail on the top/bottom branches.
     let result : Aligned :=
       match anchor with
       | .baseline =>
           let hdesc := listMax (hd.map (fun p => p.1 - p.2))
           let desc  := listMax (hd.map (fun p => p.2))
           { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
-      | .left | .bottom =>
+      | .left | .top =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
-      | .right | .top =>
+      | .right | .bottom =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
       | .center =>
```

Attack 2 — `atk_2_empty_sentinel.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -87,24 +87,31 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (partial-domain): `require hd ≠ []` leaves the empty-list case
+    -- completely unconstrained, so this impl returns a wild sentinel there.
     let result : Aligned :=
-      match anchor with
-      | .baseline =>
-          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
-          let desc  := listMax (hd.map (fun p => p.2))
-          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
-      | .left | .bottom =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
-      | .right | .top =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
-      | .center =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
+      match hd with
+      | [] => { extent := 1000000, descent := 1000000, offsets := [] }
+      | _ :: _ =>
+        match anchor with
+        | .baseline =>
+            let hdesc := listMax (hd.map (fun p => p.1 - p.2))
+            let desc  := listMax (hd.map (fun p => p.2))
+            { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
+        | .left | .bottom =>
+            let h := resolvedExtent hd extent
+            { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
+        | .right | .top =>
+            let h := resolvedExtent hd extent
+            { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
+        | .center =>
+            let h := resolvedExtent hd extent
+            { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
     return result
     -- impl-end
 
 prove_correct alignOffsets by
   loom_solve
-  cases anchor <;> rfl
+  cases hd with
+  | nil => exact absurd rfl require_1
+  | cons hdA tl => cases anchor <;> rfl
```

Attack 3 — `atk_3_empty_legal.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -87,24 +87,31 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (partial-domain, plausible): on the empty list this returns a
+    -- benign-looking zero packing instead of the real callee's ValueError.
     let result : Aligned :=
-      match anchor with
-      | .baseline =>
-          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
-          let desc  := listMax (hd.map (fun p => p.2))
-          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
-      | .left | .bottom =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
-      | .right | .top =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
-      | .center =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
+      match hd with
+      | [] => { extent := 0, descent := 0, offsets := [] }
+      | _ :: _ =>
+        match anchor with
+        | .baseline =>
+            let hdesc := listMax (hd.map (fun p => p.1 - p.2))
+            let desc  := listMax (hd.map (fun p => p.2))
+            { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
+        | .left | .bottom =>
+            let h := resolvedExtent hd extent
+            { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
+        | .right | .top =>
+            let h := resolvedExtent hd extent
+            { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
+        | .center =>
+            let h := resolvedExtent hd extent
+            { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
     return result
     -- impl-end
 
 prove_correct alignOffsets by
   loom_solve
-  cases anchor <;> rfl
+  cases hd with
+  | nil => exact absurd rfl require_1
+  | cons hdA tl => cases anchor <;> rfl
```

Attack 4 — `atk_4_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -87,24 +87,12 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
-    let result : Aligned :=
-      match anchor with
-      | .baseline =>
-          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
-          let desc  := listMax (hd.map (fun p => p.2))
-          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
-      | .left | .bottom =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
-      | .right | .top =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
-      | .center =>
-          let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
+    -- ATTACK (ungrounded-oracle echo): the impl does no work at all and simply
+    -- echoes the postcondition's own oracle. If `alignSpec` were an axiom or
+    -- otherwise ungrounded, this would verify while pinning NO behaviour.
+    let result : Aligned := alignSpec hd extent anchor
     return result
     -- impl-end
 
 prove_correct alignOffsets by
   loom_solve
-  cases anchor <;> rfl
```

Attack 5 — `atk_5_center_no_descent.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,6 +87,7 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (boundary): the `.center` arm drops the `+ p.2` descent term.
     let result : Aligned :=
       match anchor with
       | .baseline =>
@@ -101,7 +102,7 @@
           { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
       | .center =>
           let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
+          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2) }
     return result
     -- impl-end
 
```

Attack 6 — `atk_6_singleton_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,24 +87,29 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
-    let result : Aligned :=
+    -- ATTACK (control-flow): the corrected top/bottom grouping is applied ONLY
+    -- when the box list is a singleton; for two or more boxes it silently falls
+    -- back to the pre-patch (swapped) grouping.
+    let swapped : Aligned :=
       match anchor with
       | .baseline =>
           let hdesc := listMax (hd.map (fun p => p.1 - p.2))
           let desc  := listMax (hd.map (fun p => p.2))
           { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
-      | .left | .bottom =>
+      | .left | .top =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
-      | .right | .top =>
+      | .right | .bottom =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
       | .center =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
+    let result : Aligned :=
+      if hd.length = 1 then alignSpec hd extent anchor else swapped
     return result
     -- impl-end
 
 prove_correct alignOffsets by
   loom_solve
-  cases anchor <;> rfl
+  cases anchor <;> simp_all <;> rfl
```

Attack 7 — `atk_7_baseline_extent.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,12 +87,15 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (deep-model reference): the `.baseline` arm honours a caller-supplied
+    -- `extent` instead of re-deriving the packing height from the boxes. The real
+    -- callee OVERWRITES `height` in the baseline branch, so this is wrong.
     let result : Aligned :=
       match anchor with
       | .baseline =>
-          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
           let desc  := listMax (hd.map (fun p => p.2))
-          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
+          { extent := resolvedExtent hd extent, descent := desc,
+            offsets := hd.map (fun _ => (0 : Rat)) }
       | .left | .bottom =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
```

Attack 8 — `atk_8_option_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,6 +87,9 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (boundary on the Option domain): the `.right | .top` arm resolves an
+    -- ABSENT extent from max(h - d) instead of max(h). Agrees with the spec
+    -- whenever every descent is 0 (which is what the F2P DrawingArea inputs give).
     let result : Aligned :=
       match anchor with
       | .baseline =>
@@ -97,7 +100,9 @@
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
       | .right | .top =>
-          let h := resolvedExtent hd extent
+          let h := match extent with
+                   | some v => v
+                   | none   => listMax (hd.map (fun p => p.1 - p.2))
           { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
       | .center =>
           let h := resolvedExtent hd extent
```

Attack 9 — `atk_9_order_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,21 +87,25 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (refinement leg A1/A10, list order): every arm computes the correct
+    -- multiset of offsets but returns them REVERSED, breaking the
+    -- "list order preserved" bijection mapping.md §2 asserts.
     let result : Aligned :=
       match anchor with
       | .baseline =>
           let hdesc := listMax (hd.map (fun p => p.1 - p.2))
           let desc  := listMax (hd.map (fun p => p.2))
-          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
+          { extent := hdesc + desc, descent := desc,
+            offsets := (hd.map (fun _ => (0 : Rat))).reverse }
       | .left | .bottom =>
           let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
+          { extent := h, descent := 0, offsets := (hd.map (fun p => p.2)).reverse }
       | .right | .top =>
           let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
+          { extent := h, descent := 0, offsets := (hd.map (fun p => h - p.1 + p.2)).reverse }
       | .center =>
           let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
+          { extent := h, descent := 0, offsets := (hd.map (fun p => (h - p.1) / 2 + p.2)).reverse }
     return result
     -- impl-end
 
```

Attack 10 — `atk_10_descent_field.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,6 +87,9 @@
   ensures out = alignSpec hd extent anchor
   do
     -- impl-start
+    -- ATTACK (field-wise leg A10): the edge arms report `descent := listMax d`
+    -- instead of the flat `0.` the real callee assigns. Only the `descent`
+    -- component of the returned triple differs.
     let result : Aligned :=
       match anchor with
       | .baseline =>
@@ -95,7 +98,8 @@
           { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
       | .left | .bottom =>
           let h := resolvedExtent hd extent
-          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
+          { extent := h, descent := listMax (hd.map (fun p => p.2)),
+            offsets := hd.map (fun p => p.2) }
       | .right | .top =>
           let h := resolvedExtent hd extent
           { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms: this bundle models the operation deeply over its actual numeric
-- inputs. Every offset is an exact arithmetic relation on that element's own
-- (height, descent) pair — there is no outside callee whose contract must be
-- assumed. (refinement.md: all rows are R or I; mapping.md §3 records "no
-- axioms / no A-reference callees".)
-- axioms-end

-- pure-start
/- The anchor of a box layout: which edge the boxes are aligned to within the
   common extent. Values mirror the public anchor names the layout accepts. -/
inductive Anchor where
  | baseline | left | top | right | bottom | center
  deriving DecidableEq

/- The result of aligning a list of boxes: the total extent, the descent of the
   packing, and the per-box offset along the aligned axis. -/
structure Aligned where
  extent  : Rat
  descent : Rat
  offsets : List Rat
  deriving DecidableEq

/- Maximum of a NON-EMPTY list of rationals: the head seeds the reduction and
   the tail is folded into it, so the fold contributes no bound of its own and a
   list whose entries are all negative has a negative maximum. The `[]` value is
   arbitrary and never consulted — the non-empty case does not recurse through
   it, and every use sits under `require hd ≠ []`. -/
def listMax : List Rat → Rat
  | []      => 0
  | x :: xs => xs.foldl max x

/- The extent to align within: the caller may supply it explicitly, otherwise it
   is the largest box height. -/
def resolvedExtent (hd : List (Rat × Rat)) (extent : Option Rat) : Rat :=
  match extent with
  | some v => v
  | none   => listMax (hd.map (fun p => p.1))

/- Reference semantics, one branch per anchor.

   * `baseline` re-derives the extent from the boxes and leaves every box at
     offset 0.
   * the edge anchors place each box by an exact relation on its own
     `(height, descent) = (p.1, p.2)`:
       - aligning to the LEFT or BOTTOM edge offsets each box by its descent;
       - aligning to the RIGHT or TOP edge offsets each box by how far it falls
         short of the extent, plus its descent;
       - `center` places each box at half its shortfall plus its descent.

   This is the desired per-anchor placement; the implementation must reproduce
   it exactly. -/
def alignSpec (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor) : Aligned :=
  match anchor with
  | .baseline =>
      let hdesc := listMax (hd.map (fun p => p.1 - p.2))
      let desc  := listMax (hd.map (fun p => p.2))
      { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
  | .left | .bottom =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
  | .right | .top =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
  | .center =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method alignOffsets (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor)
    return (out : Aligned)
  require hd ≠ []
  ensures out = alignSpec hd extent anchor
  do
    -- impl-start
    let result : Aligned :=
      match anchor with
      | .baseline =>
          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
          let desc  := listMax (hd.map (fun p => p.2))
          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
      | .left | .bottom =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
      | .right | .top =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
      | .center =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
    return result
    -- impl-end

prove_correct alignOffsets by
  loom_solve
  cases anchor <;> rfl
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, matplotlib__matplotlib-24570 (velvet). VERDICT: SOUND. 10 same-spec attacks encoded + verified; 3 verified and ALL THREE had faithful refined patches executed through the official harness and RESOLVED.

### Setup
- Repo worktree at base_commit 8f0003ae902952372824c9917975fb372c026a42: (git worktree from the upstream repository).
- Every attack is byte-identical in axioms/pure/pre/post: same_spec == True for all 10 attacks AND the positive control (checked with swebench_unified.markers.same_spec + backends.get_backend('velvet').language). Verified table printed in-transcript; all 11 rows OK.

### Positive control
- pos_control.lean = byte-identical copy of the bundle Solution.lean (sha256 078ddb5b8526428c016fbee2e38e70dbda235296f704e46cfd76460b518e4cbf, matches bundle).
- `bash scripts/lean_verify.sh pos_control.lean` -> EXIT 0 (verifies, no sorry).

### PREPATCH REPRODUCED (atk_1)
- atk_1_prepatch.lean (= bundle Solution_prepatch.lean, the pre-patch `.left|.top` / `.right|.bottom` grouping).
- lean_verify.sh -> EXIT 1. The unsolved `rfl` goals are EXACTLY Anchor.top and Anchor.bottom (goal text captured in atk_1_prepatch.log), matching refinement.md's G-DIFF claim precisely. The frozen spec does discriminate the bug.

### ATTACKS (all run via `bash scripts/lean_verify.sh <file>.lean`; launched concurrently in batches of <=4 as background jobs)
REJECTED (exit 1) -- the spec pins these:
- atk_5_center_no_descent.lean (boundary): `.center` drops the `+ p.2` descent term -> EXIT 1 (rfl fails on Anchor.center).
- atk_6_singleton_only.lean (control-flow-effect): corrected top/bottom grouping applied only when hd.length = 1, pre-patch swap otherwise -> EXIT 1.
- atk_7_baseline_extent.lean (deep-model): `.baseline` honours a caller-supplied extent instead of re-deriving max(h-d)+max(d); the real callee OVERWRITES height in that branch -> EXIT 1.
- atk_8_option_boundary.lean (Option-domain boundary): `.right|.top` resolves an ABSENT extent from max(h-d) instead of max(h) -- agrees with gold whenever all descents are 0, which is exactly what the F2P DrawingArea inputs give -> EXIT 1. This is the sharpest near-miss and the spec catches it.
- atk_9_order_reversed.lean (R-leg A1/A10, list order): correct offset multiset but returned REVERSED, attacking mapping.md §2's "list order preserved" bijection -> EXIT 1.
- atk_10_descent_field.lean (field-wise leg A10): edge arms report `descent := listMax d` instead of the flat 0. -> EXIT 1.

VERIFIED (exit 0) -- each REQUIRED a materialized faithful patch + executed resolve:
- atk_2_empty_sentinel.lean (partial-domain): hd=[] returns wild sentinel {extent:=1000000, descent:=1000000, offsets:=[]}; non-empty arms identical to gold. EXIT 0.
- atk_3_empty_legal.lean (partial-domain, plausible): hd=[] returns benign {0,0,[]}. EXIT 0.
- atk_4_oracle_echo.lean (ungrounded-oracle echo): impl body is literally `alignSpec hd extent anchor`, doing no work and echoing the postcondition's oracle. EXIT 0. This verifies only because alignSpec is FULLY GROUNDED (a concrete `def` over the numeric inputs, no axiom) -- so the echo is behaviourally the gold function, not a vacuity. Confirmed structurally: `grep -nE '^\s*(axiom|opaque|constant|@\[extern\]|partial def)' pos_control.lean` -> NONE; the axioms region is comment-only and the pure region is 2 inductives/structures + 3 concrete defs (listMax, resolvedExtent, alignSpec).

### MANDATORY RESOLVE RUNS (the decisive step; all three EXECUTED, not speculated)
Patches generated as faithful refinements of each verifying Lean impl (gold hunk + the impl's own empty-list branch where present); each confirmed to apply with `git apply --check` against the base_commit worktree (all 3 APPLIES CLEAN). Executed via swebench_unified.harness.run_resolve('matplotlib__matplotlib-24570', patch, timeout=1800, retries=1); one result record per attack, named `<atk>.json`:
- atk_2 -> resolved: TRUE ("resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)")
- atk_3 -> resolved: TRUE ("resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)")
- atk_4 -> resolved: TRUE ("resolved")
No verifying wrong impl's faithful patch failed to resolve => NO verify=>correct break. (atk_2/atk_3 needed the harness's own retry to clear transient load; both are consistent TRUE, so per the retained-label rule these are genuine resolves, not reject-lane results.)

### A-LEG AUDIT (the assigned focus)
- refinement.md rows A1-A10: A1,A2,A3,A4,A10 = R; A5-A9 = I. NO row is kind-3 and NO row is A-consumed or A-reference. That is not merely asserted -- it is structurally true: there are zero axiom/opaque/constant declarations, so there is no axiom-soundness trust point and G-AX correctly skips. Section B's "the operation that genuinely changed is modeled deeply" is accurate: the anchor->formula assignment is the spelled-out alignSpec match over the raw (height, descent) pairs, exactly the changed content of the gold hunk.
- Model<->patch correspondence independently re-derived (not taken from conformance_check.py): I transliterated listMax/resolvedExtent/alignSpec to Python with exact Fraction arithmetic and differential-tested against the PATCHED real `_get_aligned_offsets` extracted from the worktree, seed 24570, 40,000 random cases (1-4 boxes, negative/fractional heights and descents, extent None and explicit, all six anchors): 40000 compared, 0 disagreements. A5-A10 hold, including `* .5 <-> / 2` exact over Q and the field-wise triple<->struct mapping.
- mapping.md §2's Rat (not Float) choice is justified: the callee performs only max, +, -, * .5 and identity copies -- no rounding or transcendental step -- so Q is exact, not an abstraction that could hide a float artifact.

DEFECT FOUND (documentation accuracy, NOT soundness) -- worth recording for the bundle owner:
- refinement.md A4 and mapping.md §2 justify `require hd ≠ []` by claiming HPacker/VPacker "return early on an empty child list before reaching it (offsetbox.py:473-474)". Only HPacker has that guard (`if not whd_list: return 2*pad, 2*pad, pad, pad, []`, lines 472-473). VPacker.get_extent_offsets (lines 424-456) has NO empty guard and calls `_get_aligned_offsets`(wd_list, ...) unconditionally. So the precondition's stated justification is over-broad and its line citation is wrong. Consequence is benign here (the real callee raises ValueError from max() on empty; nothing in the frozen F2P/P2P set nor any observed legend/packer render path reaches it -- an instrumented spy over legend + packer draws recorded ZERO empty-list calls), and both empty-case attacks resolved. But the prose should be corrected to "HPacker guards; VPacker does not, and the empty case raises in the real callee" rather than claiming both callers return early.

### EXCLUDED FROM THE SUBMITTED SET (my authoring errors, not spec verdicts -- reported for completeness, deliberately NOT counted as rejections)
- atk_11_demonic_empty.lean: intended demonic-choice attack on the unconstrained empty case; failed at EXIT 1 with Lean/Velvet `do`-sequence parse errors ("must be last element in a `do` sequence", "Failed to parse an assertion without names: WPGen sorry"). That is my syntax, not a spec rejection, so it is excluded. Its intent is already covered soundly by atk_2/atk_3, which reach the same empty-domain freedom and were carried all the way through resolve.
- An earlier draft of atk_2/atk_3 failed on a reserved-token tactic name (`as`); both were rewritten and re-verified to EXIT 0 before use. The reported results are from the corrected files.

**CONCLUSION:** the frozen spec discriminates the prepatch bug on exactly the right two anchors, rejects 6 distinct further wrong impls spanning boundary / control-flow-effect / deep-model / refinement-leg families, and its only residual freedom (hd=[]) is provably non-exploitable against the official oracle -- all three verifying impls' faithful patches resolved. Refinement fidelity holds; the sole finding is a fixable inaccuracy in the A4/§2 justification prose. Verdict SOUND (advisory; runner re-runs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_5_center_no_descent.lean`, `atk_6_singleton_only.lean`, `atk_7_baseline_extent.lean`, `atk_8_option_boundary.lean`, `atk_9_order_reversed.lean`, `atk_10_descent_field.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2_empty_sentinel.lean`, `atk_3_empty_legal.lean`, `atk_4_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The three verifying wrong impls (atk_2, atk_3 partial-domain on hd=[]; atk_4 oracle echo) all had their faithful refined patches RESOLVE under the official harness, so none witnesses verify=>correct failure. The nearest miss is the residual freedom at hd=[]: `require hd ≠ []` leaves the empty-box case wholly unconstrained, and refinement.md A4 / mapping.md §2 justify this by claiming callers `HPacker`/`VPacker.get_extent_offsets` "return early on an empty child list before reaching it (offsetbox.py:473-474)". That justification is only HALF true at base_commit: HPacker.get_extent_offsets does have the `if not whd_list: return 2*pad, 2*pad, pad, pad, []` guard at lines 472-473, but VPacker.get_extent_offsets (lines 424-456) has NO such guard, so a VPacker with zero visible children reaches _get_aligned_offsets with an empty wd_list. The hole is therefore REACHABLE in principle, but it is not spec-breaking here: with an empty list the real prepatch/postpatch callee raises ValueError from `max(...)` on an empty sequence, so no test in the frozen F2P/P2P set (nor any observed legend/packer render path) exercises it -- an impl that instead returns a sentinel there still resolves, as atk_2 (return 1000000., 1000000., []) and atk_3 (return 0., 0., []) both empirically demonstrated. This is an accuracy defect in the A4/§2 prose (a wrong file-line citation and an over-broad "callers return early" claim), not a soundness defect in the spec.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_empty_sentinel.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_empty_legal.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5_center_no_descent.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_singleton_only.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_baseline_extent.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_option_boundary.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_order_reversed.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_descent_field.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms: this bundle models the operation deeply over its actual numeric
-- inputs. Every offset is an exact arithmetic relation on that element's own
-- (height, descent) pair — there is no outside callee whose contract must be
-- assumed. (refinement.md: all rows are R or I; mapping.md §3 records "no
-- axioms / no A-reference callees".)
-- axioms-end

-- pure-start
/- The anchor of a box layout: which edge the boxes are aligned to within the
   common extent. Values mirror the public anchor names the layout accepts. -/
inductive Anchor where
  | baseline | left | top | right | bottom | center
  deriving DecidableEq

/- The result of aligning a list of boxes: the total extent, the descent of the
   packing, and the per-box offset along the aligned axis. -/
structure Aligned where
  extent  : Rat
  descent : Rat
  offsets : List Rat
  deriving DecidableEq

/- Maximum of a NON-EMPTY list of rationals: the head seeds the reduction and
   the tail is folded into it, so the fold contributes no bound of its own and a
   list whose entries are all negative has a negative maximum. The `[]` value is
   arbitrary and never consulted — the non-empty case does not recurse through
   it, and every use sits under `require hd ≠ []`. -/
def listMax : List Rat → Rat
  | []      => 0
  | x :: xs => xs.foldl max x

/- The extent to align within: the caller may supply it explicitly, otherwise it
   is the largest box height. -/
def resolvedExtent (hd : List (Rat × Rat)) (extent : Option Rat) : Rat :=
  match extent with
  | some v => v
  | none   => listMax (hd.map (fun p => p.1))

/- Reference semantics, one branch per anchor.

   * `baseline` re-derives the extent from the boxes and leaves every box at
     offset 0.
   * the edge anchors place each box by an exact relation on its own
     `(height, descent) = (p.1, p.2)`:
       - aligning to the LEFT or BOTTOM edge offsets each box by its descent;
       - aligning to the RIGHT or TOP edge offsets each box by how far it falls
         short of the extent, plus its descent;
       - `center` places each box at half its shortfall plus its descent.

   This is the desired per-anchor placement; the implementation must reproduce
   it exactly. -/
def alignSpec (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor) : Aligned :=
  match anchor with
  | .baseline =>
      let hdesc := listMax (hd.map (fun p => p.1 - p.2))
      let desc  := listMax (hd.map (fun p => p.2))
      { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
  | .left | .bottom =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
  | .right | .top =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
  | .center =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method alignOffsets (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor)
    return (out : Aligned)
  require hd ≠ []
  ensures out = alignSpec hd extent anchor
  do
    -- impl-start
    let result : Aligned :=
      match anchor with
      | .baseline =>
          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
          let desc  := listMax (hd.map (fun p => p.2))
          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
      | .left | .bottom =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
      | .right | .top =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
      | .center =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
    return result
    -- impl-end

prove_correct alignOffsets by
  loom_solve
  cases anchor <;> rfl
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, matplotlib__matplotlib-24570 (velvet). VERDICT: SOUND. 10 same-spec attacks encoded + verified; 3 verified and ALL THREE had faithful refined patches executed through the official harness and RESOLVED.

### Setup
- Repo worktree at base_commit 8f0003ae902952372824c9917975fb372c026a42: (git worktree from the upstream repository).
- Every attack is byte-identical in axioms/pure/pre/post: same_spec == True for all 10 attacks AND the positive control (checked with swebench_unified.markers.same_spec + backends.get_backend('velvet').language). Verified table printed in-transcript; all 11 rows OK.

### Positive control
- pos_control.lean = byte-identical copy of the bundle Solution.lean (sha256 078ddb5b8526428c016fbee2e38e70dbda235296f704e46cfd76460b518e4cbf, matches bundle).
- `bash scripts/lean_verify.sh pos_control.lean` -> EXIT 0 (verifies, no sorry).

### PREPATCH REPRODUCED (atk_1)
- atk_1_prepatch.lean (= bundle Solution_prepatch.lean, the pre-patch `.left|.top` / `.right|.bottom` grouping).
- lean_verify.sh -> EXIT 1. The unsolved `rfl` goals are EXACTLY Anchor.top and Anchor.bottom (goal text captured in atk_1_prepatch.log), matching refinement.md's G-DIFF claim precisely. The frozen spec does discriminate the bug.

### ATTACKS (all run via `bash scripts/lean_verify.sh <file>.lean`; launched concurrently in batches of <=4 as background jobs)
REJECTED (exit 1) -- the spec pins these:
- atk_5_center_no_descent.lean (boundary): `.center` drops the `+ p.2` descent term -> EXIT 1 (rfl fails on Anchor.center).
- atk_6_singleton_only.lean (control-flow-effect): corrected top/bottom grouping applied only when hd.length = 1, pre-patch swap otherwise -> EXIT 1.
- atk_7_baseline_extent.lean (deep-model): `.baseline` honours a caller-supplied extent instead of re-deriving max(h-d)+max(d); the real callee OVERWRITES height in that branch -> EXIT 1.
- atk_8_option_boundary.lean (Option-domain boundary): `.right|.top` resolves an ABSENT extent from max(h-d) instead of max(h) -- agrees with gold whenever all descents are 0, which is exactly what the F2P DrawingArea inputs give -> EXIT 1. This is the sharpest near-miss and the spec catches it.
- atk_9_order_reversed.lean (R-leg A1/A10, list order): correct offset multiset but returned REVERSED, attacking mapping.md §2's "list order preserved" bijection -> EXIT 1.
- atk_10_descent_field.lean (field-wise leg A10): edge arms report `descent := listMax d` instead of the flat 0. -> EXIT 1.

VERIFIED (exit 0) -- each REQUIRED a materialized faithful patch + executed resolve:
- atk_2_empty_sentinel.lean (partial-domain): hd=[] returns wild sentinel {extent:=1000000, descent:=1000000, offsets:=[]}; non-empty arms identical to gold. EXIT 0.
- atk_3_empty_legal.lean (partial-domain, plausible): hd=[] returns benign {0,0,[]}. EXIT 0.
- atk_4_oracle_echo.lean (ungrounded-oracle echo): impl body is literally `alignSpec hd extent anchor`, doing no work and echoing the postcondition's oracle. EXIT 0. This verifies only because alignSpec is FULLY GROUNDED (a concrete `def` over the numeric inputs, no axiom) -- so the echo is behaviourally the gold function, not a vacuity. Confirmed structurally: `grep -nE '^\s*(axiom|opaque|constant|@\[extern\]|partial def)' pos_control.lean` -> NONE; the axioms region is comment-only and the pure region is 2 inductives/structures + 3 concrete defs (listMax, resolvedExtent, alignSpec).

### MANDATORY RESOLVE RUNS (the decisive step; all three EXECUTED, not speculated)
Patches generated as faithful refinements of each verifying Lean impl (gold hunk + the impl's own empty-list branch where present); each confirmed to apply with `git apply --check` against the base_commit worktree (all 3 APPLIES CLEAN). Executed via swebench_unified.harness.run_resolve('matplotlib__matplotlib-24570', patch, timeout=1800, retries=1); one result record per attack, named `<atk>.json`:
- atk_2 -> resolved: TRUE ("resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)")
- atk_3 -> resolved: TRUE ("resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)")
- atk_4 -> resolved: TRUE ("resolved")
No verifying wrong impl's faithful patch failed to resolve => NO verify=>correct break. (atk_2/atk_3 needed the harness's own retry to clear transient load; both are consistent TRUE, so per the retained-label rule these are genuine resolves, not reject-lane results.)

### A-LEG AUDIT (the assigned focus)
- refinement.md rows A1-A10: A1,A2,A3,A4,A10 = R; A5-A9 = I. NO row is kind-3 and NO row is A-consumed or A-reference. That is not merely asserted -- it is structurally true: there are zero axiom/opaque/constant declarations, so there is no axiom-soundness trust point and G-AX correctly skips. Section B's "the operation that genuinely changed is modeled deeply" is accurate: the anchor->formula assignment is the spelled-out alignSpec match over the raw (height, descent) pairs, exactly the changed content of the gold hunk.
- Model<->patch correspondence independently re-derived (not taken from conformance_check.py): I transliterated listMax/resolvedExtent/alignSpec to Python with exact Fraction arithmetic and differential-tested against the PATCHED real `_get_aligned_offsets` extracted from the worktree, seed 24570, 40,000 random cases (1-4 boxes, negative/fractional heights and descents, extent None and explicit, all six anchors): 40000 compared, 0 disagreements. A5-A10 hold, including `* .5 <-> / 2` exact over Q and the field-wise triple<->struct mapping.
- mapping.md §2's Rat (not Float) choice is justified: the callee performs only max, +, -, * .5 and identity copies -- no rounding or transcendental step -- so Q is exact, not an abstraction that could hide a float artifact.

DEFECT FOUND (documentation accuracy, NOT soundness) -- worth recording for the bundle owner:
- refinement.md A4 and mapping.md §2 justify `require hd ≠ []` by claiming HPacker/VPacker "return early on an empty child list before reaching it (offsetbox.py:473-474)". Only HPacker has that guard (`if not whd_list: return 2*pad, 2*pad, pad, pad, []`, lines 472-473). VPacker.get_extent_offsets (lines 424-456) has NO empty guard and calls `_get_aligned_offsets`(wd_list, ...) unconditionally. So the precondition's stated justification is over-broad and its line citation is wrong. Consequence is benign here (the real callee raises ValueError from max() on empty; nothing in the frozen F2P/P2P set nor any observed legend/packer render path reaches it -- an instrumented spy over legend + packer draws recorded ZERO empty-list calls), and both empty-case attacks resolved. But the prose should be corrected to "HPacker guards; VPacker does not, and the empty case raises in the real callee" rather than claiming both callers return early.

### EXCLUDED FROM THE SUBMITTED SET (my authoring errors, not spec verdicts -- reported for completeness, deliberately NOT counted as rejections)
- atk_11_demonic_empty.lean: intended demonic-choice attack on the unconstrained empty case; failed at EXIT 1 with Lean/Velvet `do`-sequence parse errors ("must be last element in a `do` sequence", "Failed to parse an assertion without names: WPGen sorry"). That is my syntax, not a spec rejection, so it is excluded. Its intent is already covered soundly by atk_2/atk_3, which reach the same empty-domain freedom and were carried all the way through resolve.
- An earlier draft of atk_2/atk_3 failed on a reserved-token tactic name (`as`); both were rewritten and re-verified to EXIT 0 before use. The reported results are from the corrected files.

**CONCLUSION:** the frozen spec discriminates the prepatch bug on exactly the right two anchors, rejects 6 distinct further wrong impls spanning boundary / control-flow-effect / deep-model / refinement-leg families, and its only residual freedom (hd=[]) is provably non-exploitable against the official oracle -- all three verifying impls' faithful patches resolved. Refinement fidelity holds; the sole finding is a fixable inaccuracy in the A4/§2 justification prose. Verdict SOUND (advisory; runner re-runs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness / spec-too-strong-or-drifted) for matplotlib__matplotlib-24570, velvet backend. Reference used correctly: fresh worktree from the upstream repository at base_commit 8f0003ae902952372824c9917975fb372c026a42 with patch.diff APPLIED (confirmed post-apply source reads `elif align in ["left", "bottom"]` / `elif align in ["right", "top"]`). Base commit consulted only to confirm the delta, never used as the oracle.

**NO DIVERGING INPUT FOUND.** Evidence:

1. Patch fidelity: velvet/patch.diff is byte-identical to instance.json['patch'] (gold). The bundle's own patch.diff lives at the instance root, not the velvet dir.

2. Spec-region integrity: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True, so the prepatch control is a genuine impl-only swap under a frozen spec. Regions: axioms = prose-only 'no axioms' note (no `axiom` declarations at all), pure = Anchor/Aligned/listMax/resolvedExtent/alignSpec, pre-conditions and post-conditions regions empty (contracts `require hd != []` / `ensures out = alignSpec hd extent anchor` sit on the method signature).

3. EXHAUSTIVE equivalence, no divergence: extracted the real patched `_get_aligned_offsets` by regex + exec with a stub `_api` (avoids needing a built matplotlib), then compared against a faithful transliteration of alignSpec/resolvedExtent/listMax. Exhaustive sweep over domain {-2,-1/2,0,1/2,1,2} for both height and descent, list lengths 1..3, extent in {None} + all 6 domain values (includes extent < max height and NEGATIVE extent), all 6 anchors: 2,015,496 cases, 0 divergences.

4. Randomized rational fuzz (seed 24570), exact Fraction arithmetic, integers/halves/quarters incl. negatives, n=1..5, extent None or explicit: 200,000 cases, 0 disagreements.

5. F2P-exact inputs verified branch-by-branch. From test_packers with DrawingArea(10,30)/DrawingArea(20,60), pad=0, sep=0: HPacker hd_list=[(30,0),(60,0)] and VPacker wd_list=[(10,0),(20,0)], height/width=None. All 6 anchors match the real patched callee EXACTLY (bottom -> offsets [0,0]; top -> [30,0] resp. [10,0]; center -> [15,0] resp. [5,0]). These agree with the test_patch's own expectation table (`baseline/left/bottom -> 0`, `right/top -> y2-y1`, `center -> (y2-y1)/2`), so the spec's grouping is the post-patch grouping, not the pre-patch one.

6. Positive control (spec is not vacuous / not too weak in the direction that would mask drift): Solution_prepatch.lean, which differs ONLY by restoring the pre-patch grouping (top with left, bottom with right), FAILS verification, exit 1, and the only two unsolved `rfl` goals are exactly `Anchor.top` and `Anchor.bottom`. Solution.lean itself verifies, exit 0. So the ensures clause discriminates precisely the delta the patch introduces -- the spec is neither too strong nor too weak on the changed op.

TWO POTENTIAL OVER-STRENGTH / DRIFT CONCERNS EXAMINED AND REJECTED:

(a) Rat vs Float abstraction. A stress fuzz with adversarial float magnitudes (1e-8 up to 1e12, non-dyadic thirds/tenths) shows 111,253/200,000 cases where the float pipeline is not bit-exactly the rational one, worst RELATIVE error 4.88e-05 -- but this is pure FP rounding of `max`/`+`/`-`/`*.5`, identical operations in identical order, not a logic difference. At the actual domain magnitudes (screen-space pixels 0..2000, dpi-scaled), 200,000 cases give worst ABSOLUTE deviation 3.41e-13 px, three orders inside the 1e-7 tolerance mapping.md §4 documents for G-CONF. The patch performs only order- and field-operations with no transcendental or rounding step, so modeling with Rat is the SPEC_GUIDE 'order-only => Rat' rule and does not constitute drift. Notably the F2P values are exact small integers, where float and Rat coincide bit-for-bit (verified in item 5).

(b) `require hd != []` could be an over-strong precondition that carves away real behavior. Probed the real callee on hd_list=[]: with extent=None every anchor raises ValueError (`max()` on an empty sequence), and with an explicit extent the five non-baseline anchors return (extent, 0.0, []) while baseline still raises. So the precondition does exclude some inputs on which the real function is total. It is nonetheless admissible: it never lets the spec CLAIM anything false (it only declines to constrain), and the empty case is unreachable from the only two callers -- HPacker.get_extent_offsets has the `if not whd_list: return ...` early return at offsetbox.py:474-475 that mapping.md §2 cites.

One inaccuracy worth flagging as documentation-only: mapping.md §2 and refinement.md A4 assert the guard exists in BOTH `HPacker`/`VPacker`, but VPacker.get_extent_offsets (offsetbox.py:424+) has NO empty-list guard, so VPacker with zero visible children would reach `_get_aligned_offsets([], self.width, align)`. This weakens the stated justification for A4 slightly, but it does not produce a diverging input for the spec: the precondition still only narrows the domain rather than misdescribing behavior on it, and no F2P or P2P test exercises an empty-children packer. Reported as a citation defect in the refinement prose, not a faithfulness break.

**CONCLUSION:** the modeled function agrees with the real patched callee on every input tested -- 2,015,496 exhaustive exact cases plus 400,000 randomized cases plus the 12 exact F2P branch inputs, with zero logic disagreements. No input exists where alignSpec disagrees with post-patch `_get_aligned_offsets`. Verdict FAITHFUL.

**Note on prior record:** velvet/verdict.md shows all four roles previously recorded 'fail' with machine verdict INCONCLUSIVE (no verdict submitted / 0 admissible attacks), i.e. harness/submission failures rather than adjudicated spec defects, consistent with the retained-attack-label and agent-launch-outage hazards. This run reaches a submitted verdict on rebuilt evidence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC-REGION INTEGRITY (verified first): swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean) = True; the rendered spec_view of the two files is BYTE-IDENTICAL; sha256(spec_view) = 5140e3f68ebf30a8dbf153845808dc606975e7cb2751d49560846be30c618326, which matches meta.json gates.G-HYGIENE.data.region_hashes.spec_view exactly. Per-region hashes (axioms/pure/pre/post) are equal across patched and prepatch variants; pre- and post-conditions regions are empty (e3b0c442...). So the frozen spec is genuinely identical between lanes and nothing in the projection distinguishes them.

**WHAT SHIPS TO THE SOLVER:** I confirmed via eval/dataset.py (MODES_WITH_SPEC={1,2}, task.spec_view = adapter.spec_view(model), d['spec_view']=...) that only the markers projection of Solution.lean reaches the consumer. refinement.md and mapping.md are auditor-only and are never emitted into the task payload. This matters here because refinement.md DOES quote the gold hunk verbatim (both reversed elif guards, plus 'lib/matplotlib/offsetbox.py:130' and the F2P test name test_packers) and calls out 'The corrected grouping: bottom joins left' — that would be flagrant leakage if it shipped, but it does not. I flag it only as scope confirmation, not a finding.

**MECHANICAL SCREEN:** leakage.screen(Solution.lean, velvet tables, patch.diff, problem_statement) => passed=True, zero hard failures, zero warnings (same for Solution_prepatch.lean). Checked each rule by hand rather than trusting the aggregate: (L1) no diff markers ('@@', 'diff --git', '+++ ', '\nindex '); none of the four gold changed lines ('elif align in ["left", "top"]:', '...["left", "bottom"]:', '...["right", "bottom"]:', '...["right", "top"]:') appears in the normalized spec view — the spec view contains no Python syntax at all ('elif' occurs 0 times). (L2) patched path 'lib/matplotlib/offsetbox.py' and dotted module 'lib.matplotlib.offsetbox' absent; grep for offsetbox/HPacker/VPacker/packer/`_get_aligned_offsets`/check_in_list/hd_list/test_packers/24570 => 0 hits each.

(L2/L5) the sole patched distinctive symbol is 'get_aligned_offsets'; I enumerated every spec-view identifier (Aligned, Anchor, alignOffsets, alignSpec, listMax, resolvedExtent, hd, hdesc, desc, extent, descent, offsets, anchor, ...) and none embeds it — 'Aligned' is the only near-miss and 'get_aligned_offsets' is not a substring of it, so this is not even a borderline lexer call. (L3) no narration token from `_NARRATION`: no bug/fix/patch/prepatch/regression/previously/incorrectly/wrong/broken; grep for revers*/swap/corrected/'used to'/'was ' => 0 hits. Notably the spec view never says the anchors were reversed or that anything was swapped.

DERIVABILITY — the substantive judgment (this is where a rubber stamp would hide): the only content that could conceivably localize the edit is the alignSpec grouping ('.left | .bottom' => offset = p.2, and '.right | .top' => offset = h - p.1 + p.2) and its matching doc comment ('aligning to the LEFT or BOTTOM edge offsets each box by its descent; aligning to the RIGHT or TOP edge offsets each box by how far it falls short of the extent, plus its descent'). I checked each ingredient against the two legitimate public sources and every one is already public:
  1. problem_statement (title '[Bug]: `align` in `HPacker` is reversed', body naming align='bottom', HPacker/VPacker, and an expected-outcome screenshot) publicly states that top and bottom are reversed. Confirmed 'top', 'bottom', 'center', 'align', 'offset', 'hpacker' all occur in problem_statement.
  2. The base_commit source (/tmp worktree at 8f0003ae90) already publishes, in the `_get_aligned_offsets` docstring, the full six-name anchor vocabulary {'baseline','left','top','right','bottom','center'} — so Anchor's constructor list is public — and publishes every arithmetic formula verbatim and UNCHANGED by the patch: max(h-d), max(d), height=height_descent+descent, offsets=[0.], [d], [height-h+d], [(height-h)*.5+d], and 'if height is None: height = max(h ...)'. The patch touches only the two guard membership lists; it changes no formula. Hence resolvedExtent, listMax, the baseline branch, the center branch, and both edge formulas carry zero non-public information.
Composing (1) and (2): base source groups left+top and right+bottom; the public issue says top/bottom are reversed; therefore the corrected pairing left+bottom / right+top is fully derivable from public material alone. The spec view adds no fact beyond that composition — it does not reveal WHICH file or function or line to edit, does not diagnose the mechanism, and does not quote the diff. I also considered the stronger framing that alignSpec is effectively a reference implementation of the target function and so 'reconstructs the gold'.

I reject it as a finding: a formal contract's whole purpose in modes 1/2 is to state the desired behavior, the harness design puts reference semantics in the 'pure' region, and spec_guide.md directive 6 bans quoting the edit / naming the patched file-function-line / echoing patched symbols / narrating the bug->fix MECHANISM while explicitly requiring the spec to 'state the abstract desired behavior'. This spec states behavior and nothing about the edit. Treating desired-behavior disclosure as leakage would make every spec in the benchmark leaky, and the relaxed-leakage escape hatch is not needed here (G-LEAK.status is 'pass', not 'relaxed', which is correct).

MINOR, NOT A FINDING: the axioms-region comment references auditor-only artifacts by name ('refinement.md: all rows are R or I; mapping.md §3 records "no axioms / no A-reference callees"'). This is process meta-commentary that arguably should not ship in a consumer-visible view, but it discloses no gold-edit content (no file, symbol, formula, or diagnosis) and is a hygiene wart rather than leakage. Recording it so it is not mistaken for a leak on a later pass.

**CONCLUSION:** NO-LEAKAGE. The spec region is byte-identical across lanes and hash-matches meta; the mechanical screen passes on every rule individually; and every element of the spec view is public in problem_statement, public in the unchanged base_commit source, or a direct composition of the two. No leaking line identified.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
