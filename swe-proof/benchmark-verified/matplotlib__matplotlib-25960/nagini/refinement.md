# refinement.md — matplotlib__matplotlib-25960

The operation-by-operation correspondence between `model.py`'s implementation
(the `grid_cell_placement` impl region, the deep geometry model in the `pure`
region, and the `CellRect` carrier) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**, a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

"Refined per the map" is the load-bearing qualifier, and §C.1 states the one
condition each step of a refinement has to meet: its `float64` evaluation denotes
the ℝ value the model's step denotes. A program that computes the gold's real
numbers and only misbehaves once a step violates that condition is an echo of the
gold rather than a counterexample — the faithful refinement of it is the gold
placement, which resolves — and §C.1 explains why no clause of `model.py` could
be the place that says so.

**How to build the repo patch for an arbitrary implementation of this model** (the
rule §C.1 derives, stated here because it is what "faithful patch" means for this
bundle — read `--float-encoding=real` off `meta.json`, so every value in `model.py`
is a RATIONAL, not a `float64`):

1. READ each cell's extents from `gs.get_grid_positions(self)` on the gridspec the
   patch builds with `wspace, hspace, left=0, right=1, bottom=0, top=1` — and read
   **all four of them**: `left = lefts[i]`, `right = rights[i]`, `top = tops[j]`,
   `bottom = bottoms[j]`. Each extent is bound to one of those four arrays by
   mapping.md §3.1, so each comes from its own array. In particular `right` is NOT
   re-derived as `left + cw` and `bottom` is NOT re-derived as `top - ch`, even
   though the model spells them that way in its impl region and states them that way
   in its `Ensures` — those clauses say which rational the extent is, and A4's
   A-reference tag says which repo array delivers it. The two spellings denote the
   same rational; only the read one denotes it in `float64` at the closing edges.
   Measured on the configuration the instance grades: `bottoms[-1]` is exactly `0.0`
   while `tops[-1] - ch` is `-1.11e-16`, and the graded comparison is relative with
   no absolute part, so against an expected `0.0` that difference is unbounded. G-AX
   asserts that pair. This is what makes A4 an **A-reference**: the closed form is
   the model OF that routine, not a licence to re-derive it in `float64`. Note also
   that the model states the closing edges as clauses of their own —
   `j == nrows-1 ⇒ bottom == 0.0` and `i == ncols-1 ⇒ right == 1.0`, the two
   grid-fill guarantees among its postconditions — so a
   re-derived patch violates a clause of the very contract it is meant to refine,
   at the one place §C.1 shows the bridge has no tolerance. Whatever implementation
   it started from, such a patch is not a faithful refinement of it.
2. Forward `wspace`/`hspace` unchanged (A2); take `cw`/`ch` from the gridspec, never
   as a reciprocal you compute (A3).
3. Render every step the implementation takes so that its `float64` value denotes the
   ℝ value the model's step denotes — the condition mapping.md §2 states on every R
   row of §A. What decides a rendering is the ℝ VALUE of a step, never its expression
   tree, and that applies to a whole expression exactly as it does to a part of one.
   A step the model does not name is bound to no repo operation, so its ℝ value is
   the only thing that licenses it. The rule is one line, but it has three faces
   worth spelling out, because a narrow reading of any of them re-admits what the
   condition excludes:
   * **An arithmetic subterm.** One whose ℝ value is `0` (added or subtracted) or `1`
     (multiplied or divided by) is rendered by the `float64` literal that denotes it
     — `0.0`, `1.0` — equivalently, dropped. This holds however it is spelled and
     wherever it came from: literal algebra, the precondition's normalization
     equation, the difference or the ratio of the two normalization equations, or any
     of those scaled by a further factor (`k * 0` is still `0`, so amplifying an ℝ
     zero by `1.0e16` yields an ℝ zero and renders as `0.0` — its `float64` value on
     the graded grid is `-1.11`, a full unit of figure width). G-AX asserts the
     rendered literals are bit-exact no-ops on every coordinate it observes.
   * **A whole expression.** One that denotes the same ℝ value as a quantity the model
     names is rendered by the repo quantity that names it. `(x + 1.0e10) - 1.0e10`
     denotes `x`, so it renders as the array read that delivers `x` — not as two
     `float64` operations, which shift an interior column edge by a relative `1.1e-6`
     (measured at `0.35 -> 0.35000038`, eleven times the graded comparison's `rtol`)
     while leaving the two edges pinned at `0.0` and `1.0` exact.
     This face of the rule is also the one that decides a RE-PARAMETERIZATION, where
     no subterm is an ℝ zero or an ℝ one at all. An implementation may compute each
     cell from its centre — `half_w = cw*0.5`,
     `mid_x = i*cw*(1.0+wspace) + half_w`, `left = mid_x - half_w`,
     `right = mid_x + half_w` and the row analogue (measured verifying, §C.2) — and
     `half_w`, `mid_x` are honest geometric quantities, so the subterm face above has
     nothing to say about them. This face does: `mid_x - half_w` denotes the column's
     left extent, which mapping.md §3.1 binds to `lefts[i]`, and `mid_y - half_h`
     denotes the row's bottom extent, bound to `bottoms[j]`, while the routine
     delivers no array of centres for the intermediate itself to be identical to.
     So the four extents are rendered by their own reads. Transcribed instead, the
     centre arithmetic puts the bottom row's bottom edge at `-1.11e-16` when the
     centre is taken off the read top edge, and at `-5.55e-17` when it is taken as
     the midpoint of the two read edges: both spellings of the transcription miss
     the coordinate the comparison grades against an exact `0.0`, and step 4's
     self-check catches either.
   * **A CONDITION.** One whose ℝ truth value is settled by the precondition on every
     admissible input is rendered by that truth value — that is, by the branch it
     selects — and not by a `float64` comparison. A guard the contract proves false
     selects the `else` branch, and rendering it as a comparison is precisely the
     excluded step: `ch*nrows + ch*hspace*nrows > 1.0 + ch*hspace` is false over ℚ by
     A3's row equation, while in `float64` it reads `1.2000000000000002 > 1.2` on the
     graded grid — true there and on 58 of G-AX's 410 grids (the column analogue on
     29). Rendering it as a comparison therefore selects a branch the implementation
     provably never takes, which is how an ℝ-invisible difference turns into the
     reported bug rather than into a rounding difference.
   The test is uniform: if a step's `float64` evaluation can differ from the ℝ value
   or truth value the model's step denotes, that step names no repo operation and the
   rendering is wrong.
4. A patch built this way differs from the gold patch exactly where the
   implementation's ℝ behaviour differs from the gold's, and nowhere else. If it
   differs elsewhere, that difference came from a rendering choice in step 1 or 3
   rather than from the implementation, and what the oracle then grades is the
   choice and not the spec. The one self-check that catches this: on the graded
   configuration the patch must place the bottom row's bottom edge at exactly `0.0`
   and the first column's left edge at exactly `0.0`. Both hold for a patch that
   reads all four extents, and the second alone will hold for one that reads two of
   them and re-derives the other two — a mixed patch is the likeliest way to grade a
   rendering choice by mistake, because the half that is read looks like compliance.

Equivalently, in the form that is easiest to check: **the patch written for an
implementation must be the same patch one would write for any other implementation
with the same ℝ denotation.** The postcondition determines all four extents uniquely
as a function of the inputs (§C.2), so every verifying implementation has the gold's
ℝ denotation, and the faithful patch of every verifying implementation of this model
is therefore the read template of step 1. That is not a loophole in the audit; it is
what a specification COMPLETE over ℝ means — there is no verifying implementation
left that computes a different function, and the audit's remaining content is the
ℝ↔`float64` bridge, which G-AX and G-CONF measure rather than assert. It is also why
the two shapes named next, and not a re-spelling of the gold rationals, are what
would break §D.

Two shapes would break the claim in §D, and they are the ones worth aiming at: a
verifying implementation whose ℝ extents differ from the gold's on some admissible
input (§C.2 argues from determinacy that there is none, and its seven rejections are
the evidence), or an implementation every step of which renders value-faithfully by
the rule above and whose patch still does not resolve. What is NOT such a shape is a
program that computes the gold's rationals and is then transcribed rather than
rendered: §C.1 measures why, and §C.2 records that whole class as VERIFYING, row by
row, so that this boundary is stated up front rather than rediscovered.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`, the
real correctness oracle G-RESOLVE).

## A. The change

Gold hunks (`lib/matplotlib/figure.py`, `Figure.subfigures`):

```
  gs = GridSpec(nrows=nrows, ncols=ncols, figure=self,
                wspace=wspace, hspace=hspace,
                width_ratios=width_ratios,
-               height_ratios=height_ratios)
+               height_ratios=height_ratios,
+               left=0, right=1, bottom=0, top=1)

  ... add_subfigure(gs[j, i]) for each cell ...

+ if self.get_layout_engine() is None and (wspace is not None or
+                                          hspace is not None):
+     bottoms, tops, lefts, rights = gs.get_grid_positions(self)
+     for sfrow, bottom, top in zip(sfarr, bottoms, tops):
+         for sf, left, right in zip(sfrow, lefts, rights):
+             bbox = Bbox.from_extents(left, bottom, right, top)
+             sf._redo_transform_rel_fig(bbox=bbox)
```

The pre-patch code never recomputes the cells from the requested spacing, so
each subfigure keeps the gap-less, ratios-only relative bbox `add_subfigure`
gave it — the reported bug (the figure is identical regardless of `wspace`/
`hspace`).

| # | model.py impl op (`grid_cell_placement`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `nrows, ncols, j, i` (integer-valued reals) | `nrows, ncols` and the `j, i` loop indices over `sfarr` / the grid-position arrays | R | int grid count/index ↔ integer-valued `float` (mapping.md §2); `--float-encoding=real` bans int→float coercion, so counts/indices are carried as the reals they denote, with bounds expressed over reals. |
| A2 | parameters `wspace, hspace` (`>= 0`) | the `wspace`/`hspace` arguments forwarded to `GridSpec(...)` | I | the requested gap fractions, same scalar semantics. (Pre-patch they reached the gridspec too; the bug is that nothing READ them back for placement.) |
| A3 | inputs `cw, ch` PINNED by `cw*(ncols+wspace*(ncols-1))==1`, `ch*(nrows+hspace*(nrows-1))==1`, both `>0` | the normalized cell width/height inside `get_grid_positions`: `cell_w = tot_width/(ncols+wspace*(ncols-1))` with `tot_width = right-left = 1` (because the gold patch sets `left=0, right=1, bottom=0, top=1` on the gridspec); symmetrically `cell_h` | R | a real division `1/(...)` ↔ the positive real `cw` characterized by its **linear** defining equation. The division operator is uninterpreted under `--float-encoding=real` (Z3 cannot decide `(1/d)*d==1`), so `cw`/`ch` enter as positive inputs pinned by the multiplicative-but-linear normalization the real code's division satisfies. This is grounded in the inputs (the equation forces the value the division produces), not an oracle. The gold patch's added `left=0,right=1,bottom=0,top=1` is exactly what makes `tot_width=tot_height=1`, so the model's "fills [0,1]" form matches. |
| A4 | `left = i*cw*(1+wspace)`, `right = left+cw`, `top = 1 - j*ch*(1+hspace)`, `bottom = top-ch`; equality to `col_left/col_right/row_top/row_bottom` (deep `pure` geometry) | `lefts, rights = (left + cell_ws).reshape((-1,2)).T` and `tops, bottoms = (top - cell_hs).reshape((-1,2)).T` inside `get_grid_positions`, where `cell_ws`/`cell_hs` are the cumulative sums of the interleaved `[gap, cell]` widths | A-reference | the changed placement is modeled **deeply** (the spelled-out per-cell linear arithmetic `col_left/.../row_bottom`, equal ratios), NOT behind a consumed axiom. For equal ratios the `cumsum` of `[0,cw,sep,cw,sep,...]` gives left edge of column i `= i*(cw+sep) = i*cw*(1+wspace)` and right `= +cw`; rows are `top - cumsum` giving `1 - j*ch*(1+hspace)` (j from the top). axiom_check.py (G-AX) runs the REAL `GridSpec.get_grid_positions(fig)` (left=0,right=1,bottom=0,top=1, equal ratios) and asserts every cell's `(left,bottom,right,top)` equals this closed form over 10 boundary + 400 fuzz grids — the deep model == the real callee. |
| A4d | the precondition's DELIVERY obligation: for every admissible grid and in-range cell the placement reaches a normal return in finitely many steps (so the extent clauses are claims about an answer that exists, not claims discharged by never producing one) | the whole patched placement path is finite by construction: `get_grid_positions` (`lib/matplotlib/gridspec.py:145`) is straight-line arithmetic plus two `np.cumsum`s over the `2*ncols`/`2*nrows` interleaved `[gap, cell]` widths, and the gold patch's added code is two nested `zip` loops over `sfarr`/`bottoms`/`tops` and `sfrow`/`lefts`/`rights` — every loop bound is a grid dimension settled before entry, with no `while`, no recursion, and no data-dependent exit | I | the real callee has no unbounded control flow on any input the precondition admits, so "always delivers" is TRUE of it — this is a property of the real function, not a shape of the model's impl. It is load-bearing rather than decorative: Nagini without a method-level obligation proves only PARTIAL correctness, so a placement that never returns satisfies all ten `Ensures` VACUOUSLY (the post-return state is infeasible) while honouring none of them. The refined patch of such a model is a `subfigures()` that hangs instead of laying out the grid, which resolves nothing. The obligation is on the method, not merely on its loops, because loop invariants alone do not constrain a diverging callee. Correct alternatives are unaffected: a placement that reaches the same extents through a BOUNDED loop discharges the obligation (`pos-bounded-loop`, measured verifying), so the clause pins delivery and not loop-freedom. |
| A5 | `return CellRect(left, bottom, right, top)` | `bbox = Bbox.from_extents(left, bottom, right, top)` then `sf._redo_transform_rel_fig(bbox=bbox)` (which sets `bbox_relative.p0=(left,bottom)`, `.p1=(right,top)`) | R | the model `CellRect` carries exactly the four extents (mapping.md §2); `Bbox.from_extents(l,b,r,t)` builds a bbox with `min=(l,b)`, `max=(r,t)` and `_redo_transform_rel_fig` writes those into the subfigure's relative bbox. The F2P test reads `sub_figs[j,i].bbox.min == [left*w, bottom*h]`, `.max == [right*w, top*h]` — exactly the four extents the model pins, scaled by the (untouched) figure pixel size. |

## B. The discriminating clause (G-DIFF)

The behavioural delta the issue + F2P test demand is that the requested spacing
is **honoured**: column i (i>0) is shifted right by the accumulated gap, so its
left edge is `i*cw*(1+wspace)`, strictly greater than the gap-less `i*cw`.

`model_prepatch.py` reproduces the pre-patch placement by DROPPING the
gap-separation factor (`left = i*cw`, `top = 1 - j*ch`) — i.e. cells abut and
the requested spacing has no effect (the reported symptom). It shares the spec
byte-identically and **fails** the postcondition
`Result().left == col_left(i, wspace, cw)` (which carries the `(1+wspace)`
factor), for any `i>0, wspace>0`. That is exactly the spec sensing the change
(G-DIFF). The F2P configuration `(nrows=2, ncols=3, wspace=1/6, hspace=0.5)`
witnesses it: e.g. column 1 must start at `0.35`, not `1/3`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-cell placement now derived from the requested spacing — is
modeled **deeply** (the spelled-out linear geometry `col_left/.../row_bottom`
consumed in `grid_cell_placement`, an **A-reference** validated == the real
`get_grid_positions` by G-AX), not hidden behind an axiom about the routine
under change. There is **no consumed `@ContractOnly` axiom**: the axioms region
is empty (`A-consumed` count = 0). The only real division the deep model elides
(`1/(...)`) is refined (R, step A3) to a positive input pinned by its linear
defining equation, because Z3's real-division fragment cannot discharge the
reciprocal facts directly.

### C.1 The side-condition the real encoding carries (declared, not assumed away)

`--float-encoding=real` interprets the extents, gap fractions and cell sizes as
**rationals**. That is the right abstraction for this geometry — A3's linear
normalization is not decidable in Z3's float fragment, and the discriminating
value is a real inequality — but a rational reading of code that executes in
`float64` carries a side-condition, and the axis that condition runs along is the
**sequence of operations**, not the magnitude of the values:

* **The condition, stated per step — and what "value preserved" is measured
  against.** An **R** step names a repo operation (§A) and claims the model's step
  denotes what that operation computes. Value preservation is judged against that
  named operation, not against exact ℚ arithmetic — and it has to be, because the
  repo's own `cell_w = 1/(ncols+wspace*(ncols-1))` is a rounded division whose
  `float64` result does not denote the exact rational the model's `cw` carries
  either. That gap is the abstraction's rounding, and it is bounded and measured
  rather than waved through: G-AX evaluates the model's normalization equations on
  the routine's OWN cell width and height and finds them satisfied to within
  4.5 ulp on every grid it runs but **not** identically (residual nonzero on 229 of
  410 grids), and G-CONF bounds the end-to-end gap at `4.44e-16` over 100 006
  inputs. What the condition excludes is not rounding inside a named operation but
  a subterm the model does NOT name: that term is bound to no repo operation, so
  nothing except its own ℝ value licenses it in the patch, and rendering it as
  anything else is not R (the value is not preserved), not I (it is not the same
  concrete operation) and not A (no callee is being referenced) — it is a changed
  operation the model does not express, exactly the kind-3 step §C rules out.
* **The condition is already load-bearing in the map, before any rival.** It is
  why A4 is an **A-reference** and not I: a refinement reads each cell's extents
  from `get_grid_positions`, and it may not re-derive them by transcribing the
  closed form. Measured — the closed form evaluated in `float64` puts the bottom
  row's bottom edge at `-1.11e-16` on the graded configuration, where the
  routine's own interleaved cumulative sum returns exactly `0.0`. So even the
  GOLD arithmetic, transcribed rather than referenced, names no repo operation and
  delivers a different number there than the operation A4 does name. G-AX's `1e-9`
  band is the right tolerance for the question G-AX asks (is the ℝ closed form the
  right description of the routine?) and the wrong one for the question a patch asks
  (which arrays do the extents come from?); the A-reference tag answers the second.
* **The one class of programs the condition excludes.** A program carrying a
  subexpression whose ℝ value and `float64` value differ. Over ℝ such a term can
  be **exactly zero** by algebra alone, so the program computes the gold extents
  and every `Ensures` holds; in `float64` it is not zero, and its size is set by
  the scale of its own literals rather than by the scale of the geometry:

  The class is closed under the arithmetic the model has, so it is named on the
  operation the subterm is applied with — additively a real **zero**,
  multiplicatively or divisively a real **one** — and not on the sign or the size
  of the term:

  | subterm, as applied to an extent | ℝ value | `float64` value |
  |---|---|---|
  | `+ ((a + b) - a - b)` with `a = 0.1`, `b = 0.2` | 0 | `+2.78e-17` |
  | `+ (1.0e16 + 1.0 - 1.0e16 - 1.0)` | 0 | `-1.0` |
  | `+ (1.0e17 + cw - 1.0e17 - cw)` | 0 | `-cw` |
  | `+ (1.0e308 + 1.0e308 - 1.0e308 - 1.0e308)` | 0 | non-finite |
  | `+ (1.0e308 + 1.0e308 - (1.0e308 + 1.0e308))` | 0 | NaN |
  | `* (1.0e17 + 1.0 - 1.0e17)` | 1 | `* 0.0` |
  | `/ (1.0e17 + 1.0 - 1.0e17)` | 1 | division by `0.0` |
  | `* (((0.1 + 0.2) - 0.1) / 0.2)` | 1 | `* 1.0000000000000002` |
  | `+ (cw*ncols + cw*wspace*(ncols-1) - 1)` — zero **by the precondition** | 0 | `-1.11e-16` on the graded grid |
  | `/ (cw*ncols + cw*wspace*(ncols-1))` — one by the same equation | 1 | division by `0.9999999999999999` |

  The first row is why a MAGNITUDE domain is the wrong statement of this
  condition: `float64` addition is non-associative at unit scale too, so the
  class has a member every quantity of which lies in `[0, 1]`. A bound on the
  values would exclude the loud rows and admit the quiet one. (The `left == left`
  reflexivity the `CellRect` carrier requires screens the NaN row under an
  interpreted encoding, and is vacuous under `real` — another reason the
  condition has to be stated rather than delegated to a clause.)

  The last two rows are the sharpest members, because the ℝ zero does not have to
  be manufactured from literals at all: **the precondition supplies one.** A3's
  normalization equations are hypotheses of the method, so a term built from them is
  a real zero (or a real one) on every input the contract admits — invisible to
  every clause by construction rather than by coincidence, and not reachable by
  strengthening a clause, since those equations are what pin `cw`/`ch` in the first
  place. In `float64` the repo's own cell width does not satisfy them identically,
  so the term is not zero there either: G-AX asserts it is nonzero on the graded
  grid (`-1.11e-16`) and reports it nonzero on 229 of its 410 grids. That is why
  this half of the class is measured rather than argued, and why the condition is
  stated on the rendering of subterms rather than on where a subterm came from.

  **Why the precondition does not license transcribing such a term** — the natural
  objection, stated so it can be answered rather than left implicit. It runs: the
  spec ASSERTS the value of `cw*(ncols+wspace*(ncols-1))`, and every quantity in it
  is bound to a repo quantity by mapping.md §1 (`cw`↔`cell_w`, `ncols`↔`ncols`,
  `wspace`↔`subplot_params.wspace`), so the faithful rendering must be the same
  arithmetic over those same repo quantities. Four things are wrong with it.
  1. A precondition is a **hypothesis, not an operation**. Nothing in the repo
     evaluates `cw*ncols + cw*wspace*(ncols-1) - 1`; §A tags no step with it, so
     there is no named operation for a transcription to be identical TO. What binds
     `cw` to `cell_w` is a value correspondence, and a value correspondence
     transports the term's value, which is `0`.
  2. Read as a rendering rule, "transcribe the tree over the bound quantities" is
     **refuted by the reference solution**: applied to the model's own impl region it
     re-derives the closed form in `float64` and misses the graded figure edge, which
     G-AX asserts. A rule under which the gold implementation comes out unfaithful is
     not the rule this map declares.
  3. The equation is **not true of the repo's `float64` cell width** — G-AX measures
     the residual nonzero on 229 of 410 grids — so "the spec asserts its value"
     cannot be a claim about a `float64` quantity at all without making the model
     unsound. It is a claim about the rational the division denotes. That is
     precisely what makes the mined term a real zero, and its rendering `0.0`.
  4. On the loud rows of the table the transcription reading contradicts the model's
     own **delivery obligation** (A4d), which is the clearest case because it needs
     no appeal to tolerances. `1.0e17 + 1.0 - 1.0e17` denotes `1`, so the program
     that divides its extents by it — measured verifying in §C.2 — is proved by this
     contract, on every admissible input, to terminate and hand back a rectangle.
     That subterm's `float64` value is `0.0`, and `/` on a zero divisor hands back
     nothing at all. A rendering that turns a total function into one that raises is
     not a refinement of that function under any reading of A4d, so here the value
     rendering is not the map's preference: it is the only rendering that refines the
     program. The same row read the other way is a reductio on the transcription
     rule, since the rule can be made to "break" any real-valued spec at will by
     choosing wilder literals.
  The same four answers apply verbatim to a real ONE mined the same way, and to any
  future member: what decides the rendering is the subterm's ℝ value, never its
  provenance.

  **The modeling boundary this implies, and why it is not moved.** The alternative is
  to give the implementation no arithmetic to mine: make the four extents (or the
  per-column and per-row cumulative offsets) inputs READ from the routine, so the
  only freedom left is indexing. That does remove the precondition-derived members —
  but not the class, since literal algebra supplies a real zero with no `cw` in sight
  — and it pays for that by moving the entire content of the change into an
  assumption: the gap-aware geometry, which is the very thing the issue reports
  broken, would become a hypothesis about the inputs instead of an obligation the
  implementation has to discharge. G-DIFF's discriminating clause would then be
  satisfied by assumption rather than proved, and the pre-patch model would no longer
  be refutable on the geometry. A spec that cannot state the bug it fixes is a worse
  artifact than one that states it and declares its ℝ↔`float64` bridge, which is why
  the boundary stays where §A puts it.

  **The additive and the multiplicative halves are not equally consequential, and
  that too is arithmetic rather than opinion.** A rendered factor or divisor cannot
  displace an exact zero — `0.0 * 1.0000000000000002 == 0.0`,
  `0.0 / 0.9999999999999999 == 0.0` — so a quiet member of the multiplicative or
  divisive half moves neither of the two coordinates the graded comparison pins with
  no tolerance at all, and its one-ulp effect on the interior extents lies inside
  that comparison's relative band. Only two kinds of member actually displace a
  graded coordinate: an ADDITIVE one, whose rendered value is added to a zero and
  survives it, and a LOUD one, whose rendering is `0.0`, non-finite or NaN. The
  divisive rows additionally land in the real-division fragment mapping.md §2 keeps
  out of the proof, which is why A3 pins `cw`/`ch` by linear equations rather than
  by a reciprocal.
* **Two renderings are possible, and G-AX measures what each does — this is not
  settled by prose.** A model step can be carried into `float64` by transcribing
  its expression TREE, or by rendering it so that its `float64` VALUE denotes the
  ℝ value the step denotes. The map takes the second (that is what the R tag
  claims), and `axiom_check.py` now asserts both halves of what the choice does
  here:
  1. *The two renderings differ exactly where the graded comparison has no
     tolerance.* On the graded configuration the extents READ from
     `get_grid_positions` close the bottom row at exactly `0.0`, while the closed
     form re-derived in `float64` lands at `-1.11e-16`; G-AX asserts that pair,
     and reports that the two renderings agree bit-for-bit on only 112 of its 410
     grids (worst disagreement `3.33e-16`). So the tree-preserving rendering is
     refuted BY THE GOLD: applied to the model's own impl region it produces a
     placement the instance's comparison rejects, with no rival term involved at
     all. A rendering discipline under which the reference model itself fails is
     not the discipline this map declares.
  2. *Under the rendering the map does declare, every member of the class above is
     a no-op.* `+ 0.0`, `- 0.0`, `* 1.0` and `/ 1.0` — the `float64` literals that
     denote those subterms' ℝ values — leave every one of the 5590 coordinates
     G-AX observes bit-identical, which it asserts rather than states.
  Together: a program in that class returns the gold's four extents over the
  audited semantics (`x + 0` IS `x`), so by determinacy (§C.2) it *is* the gold
  function; its faithful patch differs from the gold patch only by subterms row 2
  measures to be bit-exact no-ops on every coordinate the instance grades; and the
  gold patch resolves (G-RESOLVE). Such a program is therefore an **echo** of the
  reference solution in the sense the pipeline defines — a correct alternative
  implementation — and not a spec weakness. Corroboration with the oracle
  attached, on one hunk template: a program that hands back the `@Pure` helpers
  verbatim — a genuinely different program with the same ℝ meaning — verifies
  (11.2s) and its patch RESOLVES, while the same template carrying a transcribed
  term does not; so that template grades the term and not the editing.
* **The graded coordinates admit no slack at all, which is the other half of the
  same point.** The instance's coordinate comparison is relative with no absolute
  part, so where an expected extent is an exact figure edge it admits NO
  deviation: against an expected `0`, `1e-300` is as far off as `1e300`. Two of
  the extents the model pins are such edges — the first column's left and the
  bottom row's bottom, pinned by the grid-fill clauses `i == 0 ⇒ left == 0` and
  `j == nrows-1 ⇒ bottom == 0`. "Rational and `float64` evaluation agree closely
  enough" is therefore not a claim available on those coordinates at any
  tolerance. What is available is that the real routine reaches them EXACTLY, and
  G-AX measures that instead of asserting it: `lefts[0] == 0.0` and
  `tops[0] == 1.0` bit-exactly on every grid it runs, which the leading zero
  separator of the interleaved cumulative sum makes structural. The closing
  edges are weaker and the check reports it — `rights[-1]`/`bottoms[-1]` are
  bit-exact on 239 of the 410 grids G-AX runs and off by at most `3.33e-16` on
  the rest — which is the measured reason the bottom edge cannot be re-derived
  (previous bullet) and must be read from the routine.
* **Why no clause in `model.py` could take this over.** Not an omission. Over the
  audited semantics a program of that class returns the SAME REAL NUMBERS as the
  gold, so no formula whose terms denote those numbers can separate the two: a
  range clause is satisfied (the values are in range, being the gold values), an
  exactness clause is satisfied (they are exactly the gold values), and no
  postcondition of any shape distinguishes `x` from `x + 0`. Nor can the encoding
  be swapped for one that sees the difference — and this is a property of the
  backend, not of how hard this model was tried. Nagini offers exactly two float
  encodings (`--float-encoding` accepts `real` or `ieee32`, and nothing else): ℚ,
  under which the class is denotationally invisible, or IEEE **single** precision.
  The repo computes these coordinates in **double**, so `ieee32` is not a stricter
  reading of the same program, it is a different arithmetic — a subterm that is a
  no-op in one width need not be one in the other, so a proof there would not be
  evidence about the code either. There is therefore NO configuration of this
  backend in which the ℝ↔`float64` bridge becomes a clause; it is a declared and
  measured refinement leg by necessity. (The two measurements that pin the corners,
  taken on the byte-identical `model.py`: with float operations left uninterpreted
  it fails outright at `CellRect`'s `left == left` precondition, 8.6s; under
  `--float-encoding=ieee32` it reaches no verdict at all — no convergence in 900s,
  against 10.6s under `real` — because A3's normalization equations are not
  decidable in the interpreted float fragment.) Nor does moving the geometry onto a
  carrier the class cannot inhabit help, and that is worth stating because it is the
  obvious next idea: an INTEGER model would be immune — Python's integers are exact,
  so `(a+b)-a-b` is `0` in the code as well as in the logic — but the quantities here
  are `wspace = 1/6` and a column edge at `0.35`, i.e. inherently non-integral, and a
  rational-pair carrier would only move the same bridge one step later, onto the
  `float64` division that turns the pair back into a coordinate. The condition
  therefore has one honest home — the statement of what the R tag claims — and §C.2
  records the class as VERIFYING rather than implying that the spec rejects it.
* **Where this leg is discharged, and what would refute it.** Not by a frozen
  clause — the bullet above measures why no clause over ℚ could reach it — but in
  the two places this pipeline discharges a refinement leg: G-AX, which validates
  the A-reference against the real callee and asserts the three measurable facts
  this section rests on — the two renderings disagree at the graded edge, the
  literal rendering of an ℝ-0/ℝ-1 subterm is a bit-exact no-op on every coordinate
  it observes, and A3's normalization equations hold on the routine's own cell size
  to a few ulp but not identically — and G-CONF, which runs the impl region's
  exact-rational shadow against the REAL patched `Figure.subfigures` over 100 006
  inputs with a worst edge deviation of `4.44e-16` and the discriminating properties
  checked exactly on the rationals. What would refute the leg is (i) a verifying program whose ℝ extents
  differ from the gold's on some admissible input — determinacy (§C.2) says there
  is none, and the seven rejections there are the evidence — or (ii) a program
  every step of which renders value-faithfully into `float64` and whose patch
  still does not resolve. The class above is neither; (ii) is the shape to aim at,
  and it is the shape §D claims is empty.
* **Why it is not an escape hatch.** It removes no implementation from the
  admitted set: the four extent equalities pin one rectangle per admissible input
  (§C.2), so every verifying implementation already has the gold's ℝ behaviour,
  and the condition is what makes "therefore its refinement resolves" total
  rather than a case carved out of it. It is also checkable by inspection —
  evaluate the suspect subterm in both semantics and compare — and it appeals to
  nothing about which inputs the caller happens to reach.

So the R tag on A1/A3/A5 is to be read as "realized by the operations §A names,
with the value preserved", which is the only reading under which an ℝ abstraction
of `float64` code claims anything at all. Operationally, building the real patch
for any implementation of this model means: READ each cell's extents from
`gs.get_grid_positions(self)` (A4's A-reference), forward `wspace`/`hspace`
unchanged (A2), obtain `cw`/`ch` from the gridspec rather than by a reciprocal
(A3), and render any subterm the implementation carries by a `float64` expression
whose value denotes that subterm's ℝ value — for the class above, the literal
`0.0` or `1.0`, whether the subterm was built from literals or from the
precondition's own normalization equation. Transcribing the model's expression tree
instead is not a refinement under this map, and G-AX measures the reason: done to the
model's own impl region it misses the figure edge the instance grades against `0.0`.

### C.2 What a verifying implementation must be (determinacy), and the measured battery

The four extent equalities pin `Result().left/right/bottom/top` to closed forms of
the inputs alone, so over the audited logic the postcondition group has exactly
ONE satisfying rectangle per admissible input: any implementation that verifies
returns the gold placement pointwise, on every admissible grid and cell, not only
on the tested ones. Together with A4d's delivery obligation that is the entire
content of D below — there is no residual freedom in the observed projection for
a rival to occupy. What determinacy leaves open is not a rival placement but a
rival *spelling* of the gold one, and C.1's per-step condition is what decides
which spellings a refinement may carry into `float64`.

Measured against the frozen spec (impl region swapped, spec bytes untouched,
`--float-encoding=real`, verifier cap 1200s):

| impl region | verifier | reading |
|---|---|---|
| `k = 1.0; while k > 0.0: k = k*0.5` over ℝ, then `return CellRect(0,0,0,0)` | **rejected**, 10.5s: `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` | A4d's obligation is what rejects it, and it is at the METHOD level — a loop invariant alone would not |
| `k = 1.0; while k > 0.0: k = k+1.0`, same degenerate return | **rejected** | same obligation |
| that halving loop with `Assert(False)` spliced after it | **rejected** | the vacuous-proof route through an infeasible post-loop state is gone with the loop |
| `return grid_cell_placement(nrows, ncols, j, i, wspace, hspace, cw, ch)` (self-call on the same arguments) | **rejected** | a self-call cannot discharge the obligation at an undiminished measure, so the guarded-self-call vacuity route is closed too |
| `while True: pass` | **rejected** | same obligation |
| `raise ValueError(...)` instead of a placement | **rejected** | there is no `Exsures`, so an abrupt exit is not a permitted outcome |
| gold arithmetic with `Assert(False)` at the HEAD of the impl | **rejected** | NON-VACUITY control: the precondition group (including the two normalization equations) is satisfiable, so the rejections above are refutations and not an infeasible hypothesis proving everything |
| gold extents, then a BOUNDED loop (`m = 3; while m > 0: Invariant(MustTerminate(m)); m = m - 1`) | **verifies**, 12.1s | the obligation pins delivery, not loop-freedom: a correct alternative that loops is admitted |
| the same extents spelled differently: `right = (i+1)*cw + i*cw*wspace`, `left = right - cw`, `bottom = 1 - (j+1)*ch - j*ch*hspace`, `top = bottom + ch` | **verifies**, 10.5s | the spec observes the geometry, not one spelling of it — it is not narrowed to the gold expression tree |
| the reciprocal inlined instead of carried: `left = i*(1.0+wspace)/(ncols + wspace*(ncols-1.0))`, `right = left + 1.0/(...)`, and the row analogues — `cw`/`ch` never mentioned | **verifies**, 13.8s | the boundary marker for §C.1: a re-association whose `float64` value differs from the gold's by rounding, yet on the graded grid it still reaches both graded edges exactly (`i=0` gives `0.0`; the bottom row gives `0.4 - 0.4`). So the condition is not "any `float64` difference breaks it" — what breaks is displacement at a coordinate the comparison grades against an exact edge |
| gold arithmetic plus `eps = (0.1 + 0.2) - 0.1 - 0.2` added to the column extents | **verifies**, 15.3s | ECHO, and the reason §C.1 is stated on the operations and not on the magnitudes: `eps` is 0 over ℝ, so this IS the gold function and its faithful refinement is the gold placement, which resolves. Every quantity in it lies in `[0, 1]`, so no magnitude bound reaches it; in `float64` `eps` is `2.78e-17`, and the first column's left edge has zero margin (§C.1), so a patch that TRANSCRIBES the term instead of refining the program misplaces the grid |
| the same shape with `1.0e308+1.0e308-1.0e308-1.0e308` (non-finite in `float64`), `1.0e16+1.0-1.0e16-1.0` (`-1.0`), `1.0e17+cw-1.0e17-cw` (`-cw`), `1.0e308+1.0e308-(1.0e308+1.0e308)` (NaN) | **verifies**, 15.6 / 15.7 / 10.4 / 10.2s | the loud members of the same class; identical reading. The NaN one also shows that the carrier's `left == left` reflexivity — a NaN screen under an interpreted encoding — is vacuous under `real` |
| `zero = cw*ncols + cw*wspace*(ncols-1) - 1.0` added to the column AND row extents: a real zero taken from the PRECONDITION rather than from literals | **verifies**, 13.6s | the sharpest additive member — no literal algebra to spot, and no clause could reject it without discarding the equations that pin `cw`/`ch`. Its `float64` value on the graded grid is `-1.11e-16` (G-AX asserts nonzero there), so transcribing it rather than rendering its ℝ value misplaces the graded edges |
| `one = cw*ncols + cw*wspace*(ncols-1)` used as a DIVISOR of all four extents: a real one from the same equation | **verifies**, 14.1s | the divisive precondition member; `0.9999999999999999` in `float64`, and measurably in the harmless half — a divisor cannot displace an exact zero (`0.0/0.9999999999999999 == 0.0`) |
| the same class applied MULTIPLICATIVELY: `one = 1.0e17 + 1.0 - 1.0e17` (a real one; `0.0` in `float64`) used as a factor on all four extents | **verifies**, 16.7s | the multiplicative member, which is why §C.1 names the class by the operation the subterm is applied with rather than by the term's sign |
| the same `one` used as a DIVISOR of all four extents | **verifies**, 15.9s | the divisive member; its `float64` rendering divides by `0.0`, and it is also the one shape that reaches the real-division fragment mapping.md §2 keeps out of the proof |
| a QUIET real one, `one = ((0.1 + 0.2) - 0.1) / 0.2` (`1.0000000000000002` in `float64`), as a factor on all four extents | **verifies**, 17.1s | the quiet end of the multiplicative family, and the measured reason it is not a second quiet channel: a factor cannot displace an exact zero (`0.0 * 1.0000000000000002 == 0.0`), so it moves neither coordinate the graded comparison pins with no tolerance, and one ulp on the interior extents is inside that comparison's relative band |
| `return CellRect(col_left(i,wspace,cw), row_bottom(j,hspace,ch), col_right(i,wspace,cw), row_top(j,hspace,ch))`: the `@Pure` helpers handed back verbatim | **verifies**, 11.2s, and its patch **resolves** | the ECHO control with the oracle attached — a different program with the gold's ℝ meaning, whose patch resolves through the same hunk template the two rows above fail on. So that template grades the added term and not the editing, which is what makes those two rows readable as echoes rather than as breaks |
| the same additive precondition zero AMPLIFIED: `zero = (cw*ncols + cw*wspace*(ncols-1) - 1.0) * 1.0e16` | **verifies**, 24.1s | `k*0` is still `0`, so scaling an ℝ zero does not leave the class. Its `float64` value on the graded grid is `-1.1102230246251565` — a full unit of figure width, not a rounding — which is why the rendering rule is stated on a subterm's ℝ value and never on how small the term looks |
| an ℝ IDENTITY applied to each extent rather than a term added to it: `big = 1.0e10`, `left = (i*cw*(1.0+wspace) + big) - big`, and the same for the other three | **verifies**, 23.5s | the expression denotes the extent itself, so it renders as the array read that delivers that extent. Transcribed, it shifts an interior column edge by a relative `1.1e-6` (`0.35` → `0.35000038`, eleven times the graded comparison's `rtol`) while leaving the two exact edges at `0.0` and `1.0` — the mirror image of the additive members, and the reason the rule is stated on whole expressions and not only on subterms |
| a GUARD the precondition makes ℝ-false: `if ch*nrows + ch*hspace*nrows > 1.0 + ch*hspace:` gap-less placement `else:` gold placement | **verifies**, 26.3s | the sharpest member of the class. Over ℚ A3's row equation makes the condition false, so this program IS the gold one; in `float64` the comparison reads `1.2000000000000002 > 1.2` on the graded grid — true there, and on 58 of G-AX's 410 grids (the column analogue on 29). Rendered by its ℝ truth value it is the `else` branch; rendered as a `float64` comparison it reproduces the reported bug. This is why the condition of §C.1 has to be stated on conditions as well as on arithmetic, and why no `Ensures` could reach the class: the clause it would have to reject is one the contract itself proves unreachable |
| the CELL-CENTRE re-parameterization: `half_w = cw*0.5`, `mid_x = i*cw*(1.0+wspace) + half_w`, `left = mid_x - half_w`, `right = mid_x + half_w`, and the row analogue | **verifies**, 22.0s | the member with no ℝ zero and no ℝ one anywhere in it: `mid ± half` is the gold rectangle over ℚ by algebra alone, and every named intermediate is a real geometric quantity. It is rendered by §C.1 step 3's whole-expression face — `mid_x - half_w` denotes the left extent and renders as `lefts[i]` — because the routine delivers no array of centres for the intermediate to be identical to. Transcribed, the bottom row's bottom edge lands at `-1.11e-16` with the centre taken off the read top edge and `-5.55e-17` with it taken as the midpoint of the two read edges, so neither spelling of it reaches the graded `0.0`. This is the row that shows the rendering rule cannot be narrowed to "drop the ℝ-0/ℝ-1 subterms": what it rules on is every step's denoted value |

The three loop/spelling admissions are the reason the obligation and the equalities
are not spec-too-strong; the seven rejections, read with the non-vacuity control,
are the reason they are not spec-too-weak. The last twelve rows are the §C.1 class in
full — additive, multiplicative and divisive subterms drawn from literal algebra and
from the precondition, an ℝ zero amplified by `1.0e16`, an ℝ identity applied to a
whole extent, an ℝ-false guard, and a re-parameterization with no ℝ-0/ℝ-1 subterm at
all — and its control: they verify because they must,
since in the audited
semantics they are the gold function, and they are recorded here so that the
artifact states the boundary of its own claim instead of leaving a reader to
rediscover it. Under the rendering the map declares, each of them refines to the
gold placement (G-AX asserts the no-op; G-RESOLVE runs the gold), which is what
makes them echoes rather than counterexamples. The inlined-reciprocal row is the
counterweight that keeps that reading from being circular: its `float64` rendering
differs from the gold's too (column 1 lands one ulp away, at
`0.35000000000000003`), yet it reaches both graded edges exactly, so what §C.1's
condition rules on is displacement at a graded edge — not the mere existence of a
rounding difference.

## D. verify(model) ⇒ resolved

`grid_cell_placement` verifies only if each cell's extents equal the
gap-accounting closed form (A4) with the grid filling [0,1] (the four edge
clauses) and a strictly positive gap whenever the requested spacing is positive
(the two gap clauses) **and** only if it always DELIVERS those extents (A4d: the
obligation rules out the placement that satisfies the extent clauses vacuously by
never returning). By R (int↔real counts/indices A1, the division↔linear
normalization A3, `CellRect`/`Bbox.from_extents`/`_redo_transform_rel_fig` extent
identity A5) and I (the forwarded `wspace`/`hspace` A2), the verified placement
equals the gold patch's `Bbox.from_extents(left,bottom,right,top)` per cell on
every admissible grid and cell (§C.2), the tested configuration included; by
G-AX (A4) the deep geometry equals the real
`get_grid_positions`. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited A-reference — and
the gold patch resolves (G-RESOLVE). Every step of that refinement meets §C.1's
per-step condition, which is what makes "up to type refinement" a claim about
values rather than about syntax: the extents are READ from the routine (A4's
A-reference), so a `float64` transcription of the model's arithmetic — the gold's
included — never stands between the verified geometry and the placement. The
trust points are exactly the two of PLAN §1.1: the A-reference soundness (G-AX)
and refinement fidelity (this document, G-EQ).
