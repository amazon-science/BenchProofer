# P2 adversarial audit — matplotlib__matplotlib-25960

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,11 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
+    # PREPATCH BUG re-encoded: the requested gap fractions are not accounted
+    # for, so the cells abut and the requested spacing has no effect.
+    left = i * cw
     right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
+    top = 1.0 - j * ch
     bottom = top - ch
     return CellRect(left, bottom, right, top)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,11 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
+    # WRONG: rows counted from the BOTTOM instead of from the top, i.e. the
+    # vertical index order is flipped (the zip-order bug a real patch can have).
     left = i * cw * (1.0 + wspace)
     right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
+    bottom = j * ch * (1.0 + hspace)
+    top = bottom + ch
     return CellRect(left, bottom, right, top)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,18 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
-    right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
-    return CellRect(left, bottom, right, top)
+    # PARTIAL DOMAIN: honours the requested gaps only on the bottom row; every
+    # other row gets the gap-less placement.
+    if j >= nrows - 1.0:
+        left = i * cw * (1.0 + wspace)
+        right = left + cw
+        top = 1.0 - j * ch * (1.0 + hspace)
+        bottom = top - ch
+        return CellRect(left, bottom, right, top)
+    else:
+        left2 = i * cw
+        right2 = left2 + cw
+        top2 = 1.0 - j * ch
+        bottom2 = top2 - ch
+        return CellRect(left2, bottom2, right2, top2)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,11 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
+    # BOUNDARY WRONG: the gap is folded INTO each cell's own extent instead of
+    # being left between cells, so the cells overlap and the grid overruns [0,1].
     left = i * cw * (1.0 + wspace)
-    right = left + cw
+    right = left + cw * (1.0 + wspace)
     top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
+    bottom = top - ch * (1.0 + hspace)
     return CellRect(left, bottom, right, top)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,14 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
+    # CONTROL-FLOW EFFECT: computes the gold extents and then DIVERGES, so the
+    # placement never actually delivers its rectangle to a caller tiling a grid.
     left = i * cw * (1.0 + wspace)
     right = left + cw
     top = 1.0 - j * ch * (1.0 + hspace)
     bottom = top - ch
+    k = 1.0
+    while k > 0.0:
+        k = k + 1.0
     return CellRect(left, bottom, right, top)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,8 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
-    right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
-    return CellRect(left, bottom, right, top)
+    # ECHO: the four @Pure spec helpers handed straight back as the answer, so
+    # the impl region computes no geometry of its own at all.
+    return CellRect(col_left(i, wspace, cw), row_bottom(j, hspace, ch),
+                    col_right(i, wspace, cw), row_top(j, hspace, ch))
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,14 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
+    # A real ZERO mined from the PRECONDITION's own normalization equations, in
+    # the distributed spelling, added to both axes. Over the reals it is exactly
+    # 0 on every admissible input, so the extents are the gold ones.
+    zw = cw * ncols + cw * wspace * (ncols - 1.0) - 1.0
+    zh = ch * nrows + ch * hspace * (nrows - 1.0) - 1.0
+    left = i * cw * (1.0 + wspace) + zw
     right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
+    top = 1.0 - j * ch * (1.0 + hspace) + zh
     bottom = top - ch
     return CellRect(left, bottom, right, top)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,19 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
-    right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
-    return CellRect(left, bottom, right, top)
+    # A GUARD whose real truth value the precondition settles: by the column
+    # normalization equation the distributed sum is exactly 1, so the test is
+    # FALSE on every admissible input and the else branch always runs.
+    if cw * ncols + cw * wspace * (ncols - 1.0) < 1.0:
+        left = i * cw
+        right = left + cw
+        top = 1.0 - j * ch
+        bottom = top - ch
+        return CellRect(left, bottom, right, top)
+    else:
+        left2 = i * cw * (1.0 + wspace)
+        right2 = left2 + cw
+        top2 = 1.0 - j * ch * (1.0 + hspace)
+        bottom2 = top2 - ch
+        return CellRect(left2, bottom2, right2, top2)
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,15 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
-    right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
+    # RE-PARAMETERIZATION through the cell CENTRE: every named intermediate is
+    # an honest geometric quantity and there is no real zero or real one in it.
+    half_w = cw * 0.5
+    half_h = ch * 0.5
+    mid_x = i * cw * (1.0 + wspace) + half_w
+    mid_y = 1.0 - j * ch * (1.0 + hspace) - half_h
+    left = mid_x - half_w
+    right = mid_x + half_w
+    bottom = mid_y - half_h
+    top = mid_y + half_h
     return CellRect(left, bottom, right, top)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,11 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
-    right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
+    # CORRECT, spelled differently: anchor each cell on its RIGHT/BOTTOM edge
+    # and recover the left/top edge from it.
+    right = (i + 1.0) * cw + i * cw * wspace
+    left = right - cw
+    bottom = 1.0 - (j + 1.0) * ch - j * ch * hspace
+    top = bottom + ch
     return CellRect(left, bottom, right, top)
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit (A legs + model<->patch correspondence). Base_commit worktree at ./wt (clone of the upstream repository @ 1d0d255b79e8).

9 attacks, each a copy of the bundle model.py with ONLY the impl region edited (axioms/@Pure/Requires/Ensures byte-identical). ALL 10 files (9 attacks + positive control) returned same-spec rc=0 via `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-25960 <path>`. Weakness cmd per file: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25960 <path>`, launched 3-at-a-time as background jobs.

REJECTED (rc=2, spec turned them down -- good), 5 distinct wrong-impl classes:
* atk_1.py PREPATCH BUG re-encoded: gap-separation factor dropped on BOTH axes (left=`i*cw`, top=1-`j*ch`), cells abut. rc=2. => prepatch_reproduced=true.
* atk_2.py CONTROL-FLOW/INDEXING: rows counted from the BOTTOM instead of the top (bottom=`j*ch`*(1+hspace), top=bottom+ch) -- the zip-order bug a real patch can have. rc=2.
* atk_3.py PARTIAL-DOMAIN: gold placement only on the bottom row (j>=nrows-1), gap-less everywhere else. rc=2.
* atk_4.py BOUNDARY: the gap folded INTO each cell extent (right=left+cw*(1+wspace), bottom=top-ch*(1+hspace)), cells overlap and the grid overruns [0,1]. rc=2.
* atk_5.py CONTROL-FLOW EFFECT: gold extents then `k=1.0; while k>0.0: k=k+1.0` -- rejected by A4d's METHOD-level MustTerminate(6). Confirms A4d is load-bearing, not decorative.

CANDIDATES (rc=0, share spec AND verify) -- 4, each materialized as a faithful refined patch and RUN through the official harness:
* atk_6.py (19.0s) ungrounded-oracle ECHO: the four @Pure helpers handed straight back.
* atk_7.py (17.0s) input-grounded ADDITIVE REAL ZERO on both axes, in the DISTRIBUTED spelling mined from the precondition: zw = `cw*ncols` + `cw*wspace`*(ncols-1) - 1.0, zh likewise. This is a fresh re-encoding of the family the PRIOR pass named as its counterexample (its atk_3/atk_9), rebuilt and re-verified from scratch rather than carried over. I measured that the distributed spelling is the sharp one: on the graded grid the FROZEN spelling cw*(ncols+wspace*(ncols-1))-1 is exactly 0.0 in float64 while the DISTRIBUTED `cw*ncols`+`cw*wspace`*(ncols-1)-1 is -1.1102230246251565e-16 (spellings.py; float64-nonzero on 283/3000 fuzz grids for the column equation, 1571/3000 for the row).
* atk_8.py (18.9s) a CONDITION the precondition settles over R: `if cw*ncols + cw*wspace*(ncols-1) < 1.0:` gap-less else gold. R-false on every admissible input; in float64 the distributed sum reads 0.9999999999999999 < 1.0 = TRUE on the graded grid (flips on 236/3000 fuzz grids).
* atk_9.py (17.5s) CELL-CENTRE re-parameterization: half_w/half_h, mid_x/mid_y, extents as mid +/- half -- no R-zero and no R-one anywhere in it.
* pos_control.py (15.5s) POSITIVE CONTROL, correct impl spelled right/bottom-anchored (right=(i+1)*cw+`i*cw*wspace`, left=right-cw, bottom=1-(j+1)*ch-`j*ch*hspace`, top=bottom+ch). Verifies => non-vacuity, spec not over-narrowed to the gold expression tree.

FAITHFUL PATCHES, built per refinement.md's OWN recipe (step 1: READ all four extents from gs.get_grid_positions(self) on the gridspec built with left=0,right=1,bottom=0,top=1; step 2: forward wspace/hspace unchanged (A2), cw/ch from the gridspec never as a reciprocal (A3); step 3: render every step by the R value it denotes). Generated programmatically from the real base-commit figure.py (mkpatch.py/mkpatch2.py) so they are guaranteed well-formed; ALL 8 pass `git apply --check` in the base_commit worktree, gold included.

RESOLVE RUNS -- 9, via swebench_unified.harness.run_resolve, strictly ONE AT A TIME through a serial driver (drive.sh), gold first. Every run completed=true, applied=true, P2P 137/137, no ImageNotFound and no load artifact:
  gold                 -> RESOLVED   F2P 1/1  [certifying control]
  atk_6.diff           -> RESOLVED   F2P 1/1
  atk_7.diff           -> RESOLVED   F2P 1/1
  atk_8.diff           -> RESOLVED   F2P 1/1
  atk_9.diff           -> RESOLVED   F2P 1/1
  pos_control.diff     -> RESOLVED   F2P 1/1
  ctl_transcribe_gold.diff -> NOT RESOLVED  F2P 0/1  [DECISIVE CONTROL, see below]
  atk_7_transcribed.diff   -> NOT RESOLVED  F2P 0/1
  atk_8_transcribed.diff   -> NOT RESOLVED  F2P 0/1
Every verifying attack's faithful patch RESOLVES => no verify-but-wrong witness. Verdict SOUND.

WHY THE PRIOR PASS'S BROKEN VERDICT DOES NOT STAND -- the control it never ran. The prior pass's whole case was: atk_3's real zero is mined from a FROZEN Requires clause over quantities mapping.md S1 binds to repo quantities (cw<->cell_w, ncols, wspace), so a refiner 'has no licence to render it as 0.0'; the faithful patch must TRANSCRIBE the same arithmetic; that patch does not resolve; therefore verify=/=>correct. I reproduced that transcribed patch and it does indeed fail (atk_7_transcribed.diff, F2P 0/1, bottom-left corner lands at -7.105427357601002e-14 px against an expected exact 0).

But the rendering rule that argument needs is refuted by the GOLD ITSELF, and I executed the refutation instead of arguing it: ctl_transcribe_gold.diff takes model.py's OWN impl region -- left=`i*cw`*(1+wspace), right=left+cw, top=1-`j*ch`*(1+hspace), bottom=top-ch, with cw/ch taken from the gridspec per A3 and NO rival subterm anywhere -- and transcribes it expression-for-expression instead of reading the four extents. It does NOT RESOLVE (F2P 0/1; the bottom row's bottom edge lands at -5.329070518200751e-14 px vs expected exact 0). So 'transcribe the expression tree over the bound repo quantities' is a rule under which the reference solution is unfaithful; it cannot be the criterion of faithfulness, and a patch built by it grades the rendering choice, not the spec.

That is exactly the reductio refinement.md C.1 states as answer 2 ('refuted by the reference solution') and mapping.md S2/S3.1 state as the reason A4 is an A-reference rather than an I leg -- previously asserted with a G-AX measurement, now confirmed end-to-end with the correctness oracle attached. Under the rule the bundle DOES declare, atk_7's faithful patch resolves.

Symmetry check, so the reading is not selective: the same transcribe-vs-render fork was run on atk_8 (atk_8_transcribed.diff, guard emitted as a float64 comparison -> gap-less branch selected -> F2P 0/1, 10 failing asserts, i.e. the reported bug reproduced) and it fails the same way, while atk_8.diff rendered by the guard's R truth value resolves. Three transcribed patches fail (one of them the gold's own arithmetic); six rendered patches resolve. The fork tracks the RENDERING, not the implementation -- which is the self-check refinement.md step 4 prescribes, and it is what makes atk_6/7/8/9 echoes of the reference solution rather than counterexamples.

### A-LEG AUDIT (the R/I legs being mechanically covered by G-CONF).
* A-consumed = 0, verified byte-wise: the axioms region of model.py holds no non-comment line and the file contains zero occurrences of `ContractOnly`. Nothing is assumed inside an Ensures.
* Declared leg tags parsed out of refinement.md S A: A1=R, A2=I, A3=R, A4=A-reference, A4d=I, A5=R. Every leg is R / A-reference / I -- NO kind-3 step, and the two textual 'kind-3' hits are both the section's own claim that there is none. Consistent with meta.json (axioms=[], deep_model_references=1).
* A4 (the single A-reference: col_left/col_right/row_top/row_bottom == GridSpec.get_grid_positions) INDEPENDENTLY REVALIDATED with my own harness (aref.py), not the bundle's: exact-rational closed form vs the REAL routine over 610 grids / 8482 extent comparisons (10 boundary incl. the graded 2x3 wspace=1/6 hspace=0.5, 1x1, 1x12, 12x1, 6x6, zero gaps, 1e-9 gaps, 100.0 gaps, plus 600 fuzz), worst |R closed form - routine| = 3.331e-16. Grid ORIGIN (lefts[0]==0.0, tops[0]==1.0) bit-exact on ALL 610 -- structural, from the leading zero separator of the interleaved cumsum. Closing edges bit-exact on 351/610 (57.5%), matching the bundle's reported 239/410 pattern. I also re-derived the graded grid by hand off the real routine: lefts=[0.0,0.35,0.7], rights=[0.3,0.6499999999999999,1.0], tops=[1.0,0.3999999999999999], bottoms=[0.6,0.0] -- the closed form's values. A4's correspondence HOLDS, and its A-reference (not I) tag is the correct one: the closed form re-evaluated in float64 puts the bottom row's bottom at -1.1102230246251565e-16 where the routine returns exactly 0.0 (facts.py), which is precisely why the extents must be READ.
* A4d (delivery) is a sound I leg and load-bearing: get_grid_positions is straight-line arithmetic plus two cumsums over `2*nrows`/`2*ncols` interleaved widths, and the gold adds two bounded nested zip loops -- no while, no recursion, no data-dependent exit, so 'always delivers' is TRUE of the real callee. Demonstrated live: atk_5 (gold extents + diverging loop) is REJECTED at the method level.
* A5 correspondence re-read in the repo and CONFIRMED: Bbox.from_extents(l,b,r,t) -> min=(l,b)/max=(r,t), and SubFigure.`_redo_transform_rel_fig`(bbox=...) assigns bbox_relative.p0=bbox.p0, .p1=bbox.p1 verbatim and returns early -- so CellRect's four fields are exactly the four coordinates the F2P test reads back as sub_figs[j,i].bbox.min/.max divided by the (untouched) figure pixel size. A3's tot_width=tot_height=1 premise is real: the gold patch's added left=0,right=1,bottom=0,top=1 is what makes it so, and I confirmed get_grid_positions derives tot_width/tot_height from exactly those subplot params.
* The one genuinely arguable item is A3's R tag, and it is the prior pass's 'root defect' claim. I re-measured it: the repo's float64 cell_w/cell_h do NOT satisfy the pinning equations identically (nonzero residual on 283/3000 grids for the frozen column spelling, 1571/3000 for the row). But refinement.md S2/C.1 and axiom_check.py DECLARE and MEASURE precisely that -- the residual is bounded (a few ulp; I observe worst 4.44e-16, consistent with G-CONF's end-to-end bound over 100006 inputs) and is asserted nonzero on the graded grid. A precondition is a hypothesis, not an operation: no repo step evaluates it, so a value correspondence transports its value (0), and the executed gold control above shows the transcription reading it would license is one the reference solution itself fails. So A3 is an honest R leg with a declared, measured, and now oracle-confirmed bridge -- not a disguised kind-3 step.

**HOST/EVIDENCE HYGIENE:** no attack and no resolve run was inconclusive. All 9 resolves reached completed=true on the first attempt with applied=true and P2P 137/137; the gold control resolved, so every attack's resolve result is interpretable. Resolves were serialized one-at-a-time on purpose (same instance -> the harness deletes the image at run end, so concurrency would have produced ImageNotFound and taken the gold control with it). No prior-pass label or verdict was reused: atk_7/atk_8 are my own re-encodings of the previously named families, re-verified and re-resolved from scratch. Artifacts in scratch: atk_{1..9}.py, pos_control.py, atk_{6,7,8,9}.diff, pos_control.diff, gold.diff, ctl_transcribe_gold.diff, atk_7_transcribed.diff, atk_8_transcribed.diff, resolve.log (full harness reports), facts.py/spellings.py/aref.py/predict.py/localgrade.py (measurements), build.py/mkpatch.py/mkpatch2.py (generators), wt/ (base_commit worktree, removable).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -158,13 +158,11 @@
                     row_top(j + 1.0, hspace, ch) < Result().bottom))
     # post-conditions-end
     # impl-start
-    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
-    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
-    # The grid-fill and positive-gap postconditions follow from the cell-size
-    # normalization equations.
-    left = i * cw * (1.0 + wspace)
-    right = left + cw
-    top = 1.0 - j * ch * (1.0 + hspace)
-    bottom = top - ch
+    # CORRECT, spelled differently: anchor each cell on its RIGHT/BOTTOM edge
+    # and recover the left/top edge from it.
+    right = (i + 1.0) * cw + i * cw * wspace
+    left = right - cw
+    bottom = 1.0 - (j + 1.0) * ch - j * ch * hspace
+    top = bottom + ch
     return CellRect(left, bottom, right, top)
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit (A legs + model<->patch correspondence). Base_commit worktree at ./wt (clone of the upstream repository @ 1d0d255b79e8).

9 attacks, each a copy of the bundle model.py with ONLY the impl region edited (axioms/@Pure/Requires/Ensures byte-identical). ALL 10 files (9 attacks + positive control) returned same-spec rc=0 via `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-25960 <path>`. Weakness cmd per file: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25960 <path>`, launched 3-at-a-time as background jobs.

REJECTED (rc=2, spec turned them down -- good), 5 distinct wrong-impl classes:
* atk_1.py PREPATCH BUG re-encoded: gap-separation factor dropped on BOTH axes (left=`i*cw`, top=1-`j*ch`), cells abut. rc=2. => prepatch_reproduced=true.
* atk_2.py CONTROL-FLOW/INDEXING: rows counted from the BOTTOM instead of the top (bottom=`j*ch`*(1+hspace), top=bottom+ch) -- the zip-order bug a real patch can have. rc=2.
* atk_3.py PARTIAL-DOMAIN: gold placement only on the bottom row (j>=nrows-1), gap-less everywhere else. rc=2.
* atk_4.py BOUNDARY: the gap folded INTO each cell extent (right=left+cw*(1+wspace), bottom=top-ch*(1+hspace)), cells overlap and the grid overruns [0,1]. rc=2.
* atk_5.py CONTROL-FLOW EFFECT: gold extents then `k=1.0; while k>0.0: k=k+1.0` -- rejected by A4d's METHOD-level MustTerminate(6). Confirms A4d is load-bearing, not decorative.

CANDIDATES (rc=0, share spec AND verify) -- 4, each materialized as a faithful refined patch and RUN through the official harness:
* atk_6.py (19.0s) ungrounded-oracle ECHO: the four @Pure helpers handed straight back.
* atk_7.py (17.0s) input-grounded ADDITIVE REAL ZERO on both axes, in the DISTRIBUTED spelling mined from the precondition: zw = `cw*ncols` + `cw*wspace`*(ncols-1) - 1.0, zh likewise. This is a fresh re-encoding of the family the PRIOR pass named as its counterexample (its atk_3/atk_9), rebuilt and re-verified from scratch rather than carried over. I measured that the distributed spelling is the sharp one: on the graded grid the FROZEN spelling cw*(ncols+wspace*(ncols-1))-1 is exactly 0.0 in float64 while the DISTRIBUTED `cw*ncols`+`cw*wspace`*(ncols-1)-1 is -1.1102230246251565e-16 (spellings.py; float64-nonzero on 283/3000 fuzz grids for the column equation, 1571/3000 for the row).
* atk_8.py (18.9s) a CONDITION the precondition settles over R: `if cw*ncols + cw*wspace*(ncols-1) < 1.0:` gap-less else gold. R-false on every admissible input; in float64 the distributed sum reads 0.9999999999999999 < 1.0 = TRUE on the graded grid (flips on 236/3000 fuzz grids).
* atk_9.py (17.5s) CELL-CENTRE re-parameterization: half_w/half_h, mid_x/mid_y, extents as mid +/- half -- no R-zero and no R-one anywhere in it.
* pos_control.py (15.5s) POSITIVE CONTROL, correct impl spelled right/bottom-anchored (right=(i+1)*cw+`i*cw*wspace`, left=right-cw, bottom=1-(j+1)*ch-`j*ch*hspace`, top=bottom+ch). Verifies => non-vacuity, spec not over-narrowed to the gold expression tree.

FAITHFUL PATCHES, built per refinement.md's OWN recipe (step 1: READ all four extents from gs.get_grid_positions(self) on the gridspec built with left=0,right=1,bottom=0,top=1; step 2: forward wspace/hspace unchanged (A2), cw/ch from the gridspec never as a reciprocal (A3); step 3: render every step by the R value it denotes). Generated programmatically from the real base-commit figure.py (mkpatch.py/mkpatch2.py) so they are guaranteed well-formed; ALL 8 pass `git apply --check` in the base_commit worktree, gold included.

RESOLVE RUNS -- 9, via swebench_unified.harness.run_resolve, strictly ONE AT A TIME through a serial driver (drive.sh), gold first. Every run completed=true, applied=true, P2P 137/137, no ImageNotFound and no load artifact:
  gold                 -> RESOLVED   F2P 1/1  [certifying control]
  atk_6.diff           -> RESOLVED   F2P 1/1
  atk_7.diff           -> RESOLVED   F2P 1/1
  atk_8.diff           -> RESOLVED   F2P 1/1
  atk_9.diff           -> RESOLVED   F2P 1/1
  pos_control.diff     -> RESOLVED   F2P 1/1
  ctl_transcribe_gold.diff -> NOT RESOLVED  F2P 0/1  [DECISIVE CONTROL, see below]
  atk_7_transcribed.diff   -> NOT RESOLVED  F2P 0/1
  atk_8_transcribed.diff   -> NOT RESOLVED  F2P 0/1
Every verifying attack's faithful patch RESOLVES => no verify-but-wrong witness. Verdict SOUND.

WHY THE PRIOR PASS'S BROKEN VERDICT DOES NOT STAND -- the control it never ran. The prior pass's whole case was: atk_3's real zero is mined from a FROZEN Requires clause over quantities mapping.md S1 binds to repo quantities (cw<->cell_w, ncols, wspace), so a refiner 'has no licence to render it as 0.0'; the faithful patch must TRANSCRIBE the same arithmetic; that patch does not resolve; therefore verify=/=>correct. I reproduced that transcribed patch and it does indeed fail (atk_7_transcribed.diff, F2P 0/1, bottom-left corner lands at -7.105427357601002e-14 px against an expected exact 0).

But the rendering rule that argument needs is refuted by the GOLD ITSELF, and I executed the refutation instead of arguing it: ctl_transcribe_gold.diff takes model.py's OWN impl region -- left=`i*cw`*(1+wspace), right=left+cw, top=1-`j*ch`*(1+hspace), bottom=top-ch, with cw/ch taken from the gridspec per A3 and NO rival subterm anywhere -- and transcribes it expression-for-expression instead of reading the four extents. It does NOT RESOLVE (F2P 0/1; the bottom row's bottom edge lands at -5.329070518200751e-14 px vs expected exact 0). So 'transcribe the expression tree over the bound repo quantities' is a rule under which the reference solution is unfaithful; it cannot be the criterion of faithfulness, and a patch built by it grades the rendering choice, not the spec.

That is exactly the reductio refinement.md C.1 states as answer 2 ('refuted by the reference solution') and mapping.md S2/S3.1 state as the reason A4 is an A-reference rather than an I leg -- previously asserted with a G-AX measurement, now confirmed end-to-end with the correctness oracle attached. Under the rule the bundle DOES declare, atk_7's faithful patch resolves.

Symmetry check, so the reading is not selective: the same transcribe-vs-render fork was run on atk_8 (atk_8_transcribed.diff, guard emitted as a float64 comparison -> gap-less branch selected -> F2P 0/1, 10 failing asserts, i.e. the reported bug reproduced) and it fails the same way, while atk_8.diff rendered by the guard's R truth value resolves. Three transcribed patches fail (one of them the gold's own arithmetic); six rendered patches resolve. The fork tracks the RENDERING, not the implementation -- which is the self-check refinement.md step 4 prescribes, and it is what makes atk_6/7/8/9 echoes of the reference solution rather than counterexamples.

### A-LEG AUDIT (the R/I legs being mechanically covered by G-CONF).
* A-consumed = 0, verified byte-wise: the axioms region of model.py holds no non-comment line and the file contains zero occurrences of `ContractOnly`. Nothing is assumed inside an Ensures.
* Declared leg tags parsed out of refinement.md S A: A1=R, A2=I, A3=R, A4=A-reference, A4d=I, A5=R. Every leg is R / A-reference / I -- NO kind-3 step, and the two textual 'kind-3' hits are both the section's own claim that there is none. Consistent with meta.json (axioms=[], deep_model_references=1).
* A4 (the single A-reference: col_left/col_right/row_top/row_bottom == GridSpec.get_grid_positions) INDEPENDENTLY REVALIDATED with my own harness (aref.py), not the bundle's: exact-rational closed form vs the REAL routine over 610 grids / 8482 extent comparisons (10 boundary incl. the graded 2x3 wspace=1/6 hspace=0.5, 1x1, 1x12, 12x1, 6x6, zero gaps, 1e-9 gaps, 100.0 gaps, plus 600 fuzz), worst |R closed form - routine| = 3.331e-16. Grid ORIGIN (lefts[0]==0.0, tops[0]==1.0) bit-exact on ALL 610 -- structural, from the leading zero separator of the interleaved cumsum. Closing edges bit-exact on 351/610 (57.5%), matching the bundle's reported 239/410 pattern. I also re-derived the graded grid by hand off the real routine: lefts=[0.0,0.35,0.7], rights=[0.3,0.6499999999999999,1.0], tops=[1.0,0.3999999999999999], bottoms=[0.6,0.0] -- the closed form's values. A4's correspondence HOLDS, and its A-reference (not I) tag is the correct one: the closed form re-evaluated in float64 puts the bottom row's bottom at -1.1102230246251565e-16 where the routine returns exactly 0.0 (facts.py), which is precisely why the extents must be READ.
* A4d (delivery) is a sound I leg and load-bearing: get_grid_positions is straight-line arithmetic plus two cumsums over `2*nrows`/`2*ncols` interleaved widths, and the gold adds two bounded nested zip loops -- no while, no recursion, no data-dependent exit, so 'always delivers' is TRUE of the real callee. Demonstrated live: atk_5 (gold extents + diverging loop) is REJECTED at the method level.
* A5 correspondence re-read in the repo and CONFIRMED: Bbox.from_extents(l,b,r,t) -> min=(l,b)/max=(r,t), and SubFigure.`_redo_transform_rel_fig`(bbox=...) assigns bbox_relative.p0=bbox.p0, .p1=bbox.p1 verbatim and returns early -- so CellRect's four fields are exactly the four coordinates the F2P test reads back as sub_figs[j,i].bbox.min/.max divided by the (untouched) figure pixel size. A3's tot_width=tot_height=1 premise is real: the gold patch's added left=0,right=1,bottom=0,top=1 is what makes it so, and I confirmed get_grid_positions derives tot_width/tot_height from exactly those subplot params.
* The one genuinely arguable item is A3's R tag, and it is the prior pass's 'root defect' claim. I re-measured it: the repo's float64 cell_w/cell_h do NOT satisfy the pinning equations identically (nonzero residual on 283/3000 grids for the frozen column spelling, 1571/3000 for the row). But refinement.md S2/C.1 and axiom_check.py DECLARE and MEASURE precisely that -- the residual is bounded (a few ulp; I observe worst 4.44e-16, consistent with G-CONF's end-to-end bound over 100006 inputs) and is asserted nonzero on the graded grid. A precondition is a hypothesis, not an operation: no repo step evaluates it, so a value correspondence transports its value (0), and the executed gold control above shows the transcription reading it would license is one the reference solution itself fails. So A3 is an honest R leg with a declared, measured, and now oracle-confirmed bridge -- not a disguised kind-3 step.

**HOST/EVIDENCE HYGIENE:** no attack and no resolve run was inconclusive. All 9 resolves reached completed=true on the first attempt with applied=true and P2P 137/137; the gold control resolved, so every attack's resolve result is interpretable. Resolves were serialized one-at-a-time on purpose (same instance -> the harness deletes the image at run end, so concurrency would have produced ImageNotFound and taken the gold control with it). No prior-pass label or verdict was reused: atk_7/atk_8 are my own re-encodings of the previously named families, re-verified and re-resolved from scratch. Artifacts in scratch: atk_{1..9}.py, pos_control.py, atk_{6,7,8,9}.diff, pos_control.diff, gold.diff, ctl_transcribe_gold.diff, atk_7_transcribed.diff, atk_8_transcribed.diff, resolve.log (full harness reports), facts.py/spellings.py/aref.py/predict.py/localgrade.py (measurements), build.py/mkpatch.py/mkpatch2.py (generators), wt/ (base_commit worktree, removable).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL attacker 2 (faithfulness-break / spec-too-strong). Scratch: (git worktree at base_commit 1d0d255b7, gold patch applied).

**REFERENCE SETUP:** grid_cell_placement was compared against the PATCHED repo (Figure.subfigures with left=0,right=1,bottom=0,top=1 on the GridSpec, plus the get_grid_positions -> Bbox.from_extents -> `_redo_transform_rel_fig` block), NOT against the base gap-less version, so the patch delta is not miscounted as drift. For the UNCHANGED callee GridSpec.get_grid_positions I verified programmatically that the base_commit arithmetic (gridspec.py:183-204) is line-for-line identical to host matplotlib 3.10.9 after tot_width, so driving the host build is a sound proxy for the base-commit callee.

### Evidence the spec does not overstate the real behaviour
1) Value fidelity, independently re-fuzzed with my own harness (not the bundle's): ~130k cell observations over ~1650 grid configurations, real Figure.subfigures CALLED and read exactly as the F2P test reads it (sf.bbox.min/max divided by fig.bbox.max), versus the model's exact-rational closed form. nrows,ncols in [1,50]; wspace/hspace covering 0.0, 1e-25..1e20, 1e100, 1e300, plus the F2P shape (2x3, wspace=1/6, hspace=0.5). ZERO deviations above 1e-9; worst deviation 4.44e-16, one float64 ulp of the interleaved cumsum. No input found where the modelled function disagrees with the real callee.
2) F2P agreement: the closed form reproduces all 12 assert_allclose targets of test_subfigures_wspace_hspace exactly (column 1 at 0.35, not 1/3), as does the real code.
3) Row-from-top convention checked including NESTED subfigures (parent.subfigures called on a SubFigure): cell (j,i) bbox_relative == the model's (col_left, row_bottom, col_right, row_top) to <1e-12 for all 6 cells of a 2x3 nested grid. The (j,i)=row-from-top indexing is correct at base_commit (the row-major reordering is a later 3.10 change, absent here).
4) The one apparent over-strength I found is NOT a divergence. The model's Ensures on grid-fill (i=0 -> left==0, i=ncols-1 -> right==1, j=0 -> top==1, j=nrows-1 -> bottom==0) and on strict gaps (right < col_left(i+1) when wspace>0) hold EXACTLY over the reals but fail in float64 in the real code: e.g. nrows=1,ncols=4,wspace=0.3 gives real right edge 0.9999999999999998 not 1.0; nrows=4,ncols=1,hspace=0.7 gives bottom = -2.22e-16 not 0.0; and at nrows=4,ncols=5,wspace=1.72e-18 the real horizontal gap between columns 0 and 1 is exactly 0.0 (0.2 vs 0.2), while the spec demands a STRICTLY positive gap. These are exactly the R-leg cases mapping.md's "Magnitude side-condition on the R<->float64 bridge" and refinement.md C.1 declare in advance: --float-encoding=real reads coordinates as rationals, all such residuals are at or below 4.44e-16 (5+ orders inside the F2P test's assert_allclose rtol 1e-7 and 3 orders inside G-CONF's 1e-12), and a subnormal-scale wspace is not a value any caller of subfigures reaches. So this is the documented, bounded abstraction of the encoding, not an unfaithful claim about behaviour.
5) Crucially, the strict-gap clauses add NO strength at all: over R, col_left(i+1) - col_right(i) = `cw*wspace` > 0 is entailed by the four extent equalities plus cw>0, wspace>0. I confirmed this mechanically by deleting both gap Ensures from the frozen spec and re-verifying -- still "Verification successful", so the admitted implementation set is unchanged. They cannot narrow the spec below the real behaviour.
6) Precondition is not over-restrictive relative to the real callee's reachable domain: the two normalization equations cw*(ncols+wspace*(ncols-1))==1 and ch*(nrows+hspace*(nrows-1))==1 are precisely cell_w/cell_h with tot_width=tot_height=1, which the patch's own added left=0,right=1,bottom=0,top=1 forces; wspace,hspace >= 0 matches SubplotParams (a negative gap is not a supported input); the equal-ratios restriction (no width_ratios/height_ratios parameter) is a declared narrowing of scope, not a false claim -- I confirmed width_ratios=[1,2,3] gives real edges (0,0.125),(0.25,0.5),(0.625,1.0) vs the equal-ratio model's (0,0.25),(0.375,0.625),(0.75,1.0), but the model simply does not quantify over that case, and the F2P test does not exercise it.
7) Constrained-layout path: with layout='constrained' the patched branch is skipped and the real cells are the gap-less 1/3-wide ones, disagreeing with the model. This is NOT drift either -- the model's domain is the no-layout-engine branch (mapping.md section 2 states the gap arguments are given and no layout engine is active; conformance_check.py asserts fig.get_layout_engine() is None on every call). Same for wspace=None (rcParams 0.2 is substituted upstream of the modelled placement, and I confirmed the real code then matches the model instantiated at wspace=0.2 exactly).
8) MustTerminate(6) is TRUE of the real callee: get_grid_positions is straight-line arithmetic plus two cumsums over grid-dimension arrays and the patch's added code is two nested zip loops over sfarr -- no while, no recursion, no data-dependent exit. It is also not over-strong against correct alternatives: a bounded-loop variant (m=3; while m>0 with Invariant(MustTerminate(m))) VERIFIES, as do two algebraically-rearranged spellings of the same geometry (left = `i*cw` + `i*sep_w` form, and the right/bottom-inward form right=(i+1)*cw+`i*cw*wspace`). Only a loop whose measure I stated on a real-valued counter was rejected, which is a proof-annotation issue in my attack, not a spec defect.

INTEGRITY / HYGIENE CHECKS RUN:
- model.py sha256 252927b23619883de003462b6fc8b24c453d7fc82b447a41b69c25351f87a231 matches the sha recorded in the G-AX, G-CONF, G-DIFF, G-VERIFY, G-GOLD, G-MUT, G-PBT gate sources; model_prepatch.py sha also matches its G-DIFF record.
- markers.same_spec(model.py, model_prepatch.py) is True and all spec regions (axioms/pure/pre-conditions/post-conditions/spec_view) hash-match, with only the impl region differing -- the G-DIFF discrimination is a genuine spec-sensing result.
- model.py verifies under the pinned verifier with --float-encoding=real ("Verification successful", 9.2s).
- NON-VACUITY control: Assert(False) spliced at the head of the impl region is REJECTED ("Assertion False might not hold"), so the precondition group including both normalization equations is satisfiable and the rejections above are real refutations.

NOTE (not a spec finding, for the rollup): the stale G-EQ / G-PANEL / G-PANEL-1 fail records on this cell were stamped against an older model.py (sha 861a0e6d...), not the current 252927b2... spec; per the freshness rule those verdicts judge bytes that no longer exist and should not be read as findings against the spec I audited.

**CONCLUSION:** no input exists at which the modelled function disagrees with the real (patched) callee within the declared domain and the declared R<->float64 magnitude side-condition. Every residual I found is either an entailed clause that adds no strength, a sub-ulp rational-vs-float64 artifact explicitly bounded in mapping.md/refinement.md C.1, or a case outside the model's declared domain (unequal ratios, active layout engine). Verdict FAITHFUL; no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction of the nagini spec view for matplotlib__matplotlib-25960. NO relaxation claim in this bundle -- meta.json has no `relaxed_leakage` key (checked: False/None), gates.G-LEAK.status == "pass", and no RELAXED_LEAKAGE.md exists anywhere under the instance dir (`find . -name 'RELAXED_LEAKAGE*'` -> empty). So this is judged as an ordinary strict no-leakage review, not an inherited disposition.

### WHAT I RAN (all from repo root; bundle never modified; worktree at base_commit 1d0d255b79e8):
1. Mechanical screen: `leakage.screen(model.py, nagini, row['patch'], row['problem_statement'], test_patch=...)` -> passed=True, hard_failures=[], warnings=[]. Reproduced independently of the stamped G-LEAK record.
2. Projection is real: `spec_view(model.py, nagini)` elides the impl region to `...  # implementation elided` (impl-start/end retained as structural markers). Confirmed `same_spec` machinery is live: `adversary same-spec nagini ... model_prepatch.py` -> exit 0 ("SAME"), so the spec bytes I screened are the bytes a consumer sees.

3. EDIT-LOCALIZATION SYMBOLS -- none present. `_patch_changed_symbols(gold)` == {'subfigures'}, which (a) IS public (problem_statement says "`wspace` and `hspace` in `Figure.subfigures`") and (b) does not occur in the spec view at all; the view uses neutral "sub-region"/"grid cell" vocabulary. Token-scanned the view for every identifier the gold ADDS: get_layout_engine, ConstrainedLayoutEngine, rcParams, constrained, `_redo_transform_rel_fig`, Bbox, from_extents, get_grid_positions, sfarr, sfrow, lefts/rights/bottoms/tops, height_ratios, `left=0`/`right=1` -- ALL absent (each checked False). The gold's docstring rewrite ("inferred from rcParams if using constrained layout ... or zero if not using a layout engine") is the hints-only discriminator and is entirely absent: no 'rcParams', no 'constrained', no 'layout engine', no 'layout_engine' in the view.
4. Patched path/module: 'lib/matplotlib/figure.py' and 'matplotlib.figure' absent from the view; no diff markers (@@, diff --git, +++ , --- , \nindex). Only occurrence of the word 'matplotlib' is the instance-id line of the module docstring, which is the harness's own header convention.
5. **HINTS-ONLY VOCABULARY:** differenced hints_text tokens (len>=5) against problem_statement tokens and intersected with the view -- the only hits are ordinary English (between, average, width, height, spacing, issue, never, result, sizes, position, correct, total...). No distinctive hints term, no gridspec.py pointer, no 'constrained layout' observation from the hints thread.
6. **TEST LEAKAGE:** none of the F2P constants (1/6, 0.35, 0.65, 0.3, 0.6, 0.4, 0.7, 640, 480) nor 'sub_figs', 'allclose', 'bbox.min/.max', 'test_' appear in the view.
7. **NARRATION:** harness `_NARRATION_RE` clean. My own wider sweep flagged one word -- 'ignored', on the wrapped comment "the requested spacing is honoured, not / # ignored." That is a restatement of the PUBLIC symptom ("do nothing" / "Same figure independently of the values of hspace and wspace"), not a mechanism diagnosis, and it does not reproduce the gold's added comment line ("Gridspec wspace and hspace is ignored on subfigure instantiation") -- the L1 normalized >=8-char reproduction check passes.

8. THE TWO CLAUSES THAT COULD PLAUSIBLY LEAK, AND WHY THEY DO NOT:
   (a) The normalization `cw*(ncols + wspace*(ncols-1)) == 1` and the closed form `i*cw*(1+wspace)`. This is DERIVABLE FROM THE PROBLEM STATEMENT ALONE. The PS's "Expected outcome" is a permalink to figure.py L1550-1554; I read those exact lines at that blob (`git show b3bd929c:lib/matplotlib/figure.py | sed -n 1550,1554p`) -- the public docstring says wspace/hspace are "expressed as a fraction of the average subfigure width/height". With equal cells the average cell width IS cw, so n cells plus (n-1) gaps of `wspace*cw` filling the span gives `cw*n` + `wspace*cw`*(n-1) == 1 -- the spec's equation verbatim, and the per-column offset `i*cw`*(1+wspace) follows. The spec's geometry is a public-consequence derivation, not gold internals.

   (b) The grid-fill clauses (leftmost left==0, rightmost right==1, top row top==1, bottom row bottom==0), which sit near the gold's added `left=0, right=1, bottom=0, top=1`. I MEASURED that this is pre-existing observable behaviour, not a gold discriminator: I reconstructed the PRE-patch subfigures() path (bare `GridSpec(nrows,ncols,figure=f,wspace=1/6,hspace=0.5)` + add_subfigure, no left/right/bottom/top kwarg, no post-hoc `_redo_transform_rel_fig`) and printed bbox_relative -- cells came out p0=(0,0.5)/p1=(0.333,1) ... p0=(0.667,0)/p1=(1,0.5), i.e. the grid ALREADY tiles the unit square exactly pre-patch. So "the grid fills the figure" discriminates nothing about the edit; it is stated as a geometric property of the desired placement, never as a constructor kwarg.

9. CLOSEST CALL, resolved as non-leaking: the docstring's A-reference disclosure "validated == the real grid-position routine out-of-band by axiom_check.py (G-AX)". It is a generic paraphrase, not the symbol `get_grid_positions` (which the gold CALLS rather than defines, so it is correctly outside the changed-symbol set), and it names no file, function, or line. It is also corpus-wide harness convention, not instance-specific narration: 140 of the nagini model.py files carry "axiom_check.py (G-AX)" and 47 carry "validated == the real". Given the view already spells out the full closed-form geometry legitimately (and that form is PS-derivable per 8a), the existence-of-a-grid-position-routine remark adds no localization the behavioural content does not already license.

**NO FILE IN THE BUNDLE ADDRESSES ME.** Grepped model.py, model_prepatch.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py for G-PANEL / attacker / reviewer / auditor / verdict / NO-LEAKAGE / "honest recording" / "recording convention" / "you should submit" -- zero hits. No steering to report.

### OUT-OF-FACET OBSERVATIONS (not part of this verdict, flagged for the record):
- **RECORD STALENESS:** meta.json region_hashes disagree with live model.py on TWO regions -- pre-conditions (stored 7a735a89 vs live b4952f5a) and spec_view (stored 4da6a308 vs live 0c1f3537); axioms/pure/post-conditions/impl match. The spec view text has been edited since stamping, so any retained attack keyed on spec_signature is void and stamped per-gate records should be re-derived rather than trusted. My leakage verdict is on the LIVE bytes I read and screened, not on the stamp.
- The stamped G-EQ and G-PANEL-1 are `fail` (atk_2.py verifies but its patch does not resolve -- spec-too-weak). That is a different facet and does not bear on leakage, but it means this cell is not green for reasons independent of my verdict. G-VERIFY of the shipped model.py re-confirmed live here (`nagini_verify.sh` on a /tmp copy, 7.45s / 9.01s, exit 0), so the spec I screened is the verifying one.

**CONCLUSION:** the spec view reveals nothing about the gold edit beyond the public problem_statement (and the docstring lines it explicitly links). Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
