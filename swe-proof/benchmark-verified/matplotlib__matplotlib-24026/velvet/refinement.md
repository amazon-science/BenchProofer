# refinement.md — matplotlib__matplotlib-24026

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectLayerColors` `do` block and the deep `cyclicColors` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The colour-selection site — `stackplot()` (`lib/matplotlib/stackplot.py:72-73, 110-123`)

Gold hunks:
```
+import itertools
...
-    if colors is not None:
-        axes.set_prop_cycle(color=colors)
+    if colors is not None:
+        colors = itertools.cycle(colors)
+    else:
+        colors = (axes._get_lines.get_next_color() for _ in y)
...
-    color = axes._get_lines.get_next_color()
     coll = axes.fill_between(x, first_line, stack[0, :],
-                             facecolor=color, label=next(labels, None),
+                             facecolor=next(colors), label=next(labels, None),
...
     for i in range(len(y) - 1):
-        color = axes._get_lines.get_next_color()
         r.append(axes.fill_between(x, stack[i, :], stack[i + 1, :],
-                                   facecolor=color, label=next(labels, None),
+                                   facecolor=next(colors),
+                                   label=next(labels, None),
```

This bundle models the `colors is not None` branch — the one the issue exercises
(`colors=['C2','C3','C4']`) and the F2P test changes to
(`colors=["C0","C1","C2"]`). The `else` branch (no `colors`) is behaviour-identical
pre- and post-patch (it still draws each area's colour from the axes cycle via
`get_next_color`), so it is not a separately-fixed behaviour and needs no prepatch
(see §C).

| # | Solution.lean impl op (`selectLayerColors`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `colors : List String`, `require colors.length > 0` | the `colors=` argument under the `colors is not None` branch | R | Python colour-spec list → `List String` (mapping.md §2). Non-empty ↔ the branch only fires for a supplied non-empty list. G-CONF bridges tokens via `to_rgba`. |
| A2 | param `layerCount : Nat`, `List.range layerCount` | `len(y)` areas drawn at `:112` (area 0) and the `:119` `for i in range(len(y)-1)` loop (areas 1..M-1) | R | `y.shape[0]` ↔ `layerCount`; the ordered area indices ↔ `List.range layerCount` (mapping.md §2). |
| A3 | `out = cyclicColors colors layerCount`, i.e. `(List.range layerCount).map (fun i => colors[i % colors.length]!)` | `colors = itertools.cycle(colors)` then one `next(colors)` per area | A-reference + I | the changed colour-source operation is modeled **deeply**: `cyclicColors` (pure region) and the `List.range … map` loop ARE the cyclic repetition. No consumed `nextColor` axiom. The map/`%`/indexing ops are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `itertools.cycle` consumption is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | `ensures sharedCycle = sharedCycleOld` (the axes' shared colour cycle returned unchanged) | the **deletion** of `axes.set_prop_cycle(color=colors)` and the replacement of the per-area `axes._get_lines.get_next_color()` by `next(colors)` | I (frame) | the whole point of the fix. Pre-patch, `set_prop_cycle` overwrote the axes' shared cycle AND each area consumed it via `get_next_color` (advancing it); post-patch the supplied colours feed a private `itertools.cycle` and the axes cycle is neither replaced nor advanced. Directive-5 frame: pinned to the entry value `sharedCycleOld`. |

Discriminating content of the change — the **axes' shared colour cycle must
survive the operation unchanged** so colours stay synchronised across the other
artists — lives in `ensures sharedCycle = sharedCycleOld` (model) ⇔ the removal of
`set_prop_cycle` plus the switch to a private `itertools.cycle` (real). The
pre-patch code installs `colors` onto the shared cycle; `Solution_prepatch.lean`
reproduces that (`sharedCycle := colors`) and **fails** the frame clause — the
unsolved goal is `colors = sharedCycleOld`, i.e. the supplied colours leaking onto
the shared cycle (G-DIFF). (As a bonus, pre-patch `set_prop_cycle(color=['C2',…])`
also *raises* `ValueError: Cannot put cycle reference ('C2') in prop_cycler`, the
traceback in the issue — the same overwrite the frame clause forbids.)

## B. No consumed axioms

There are no `axiom` declarations and no `:|` stubs. The only kind-A construct is
the **A-reference** `cyclicColors` (a deep model validated == the real
`itertools.cycle` by G-AX, §A3). The directive-5 frame (`sharedCycle =
sharedCycleOld`) borrows no outside contract; its real soundness is checked
end-to-end by G-CONF against a control axes.

## C. No kind-3 (inexpressible-changed-op) steps; single observable behaviour

Every step is R, A, or I. The operations that genuinely *changed* — the colour
SOURCE (axes cycle → private cyclic walk of `colors`) and the colour-cycle FRAME
(overwritten/advanced → untouched) — are modeled **deeply** (the spelled-out
`cyclicColors`, A3, an A-reference + I) and **directly** (the `mut` frame, A4),
not hidden behind an axiom about the function under change. There is no consumed
axiom.

Only one independently-observable fixed behaviour exists (the `colors`-supplied
path: right colours, untouched shared cycle), so one `Solution_prepatch.lean`
suffices. The `else` (no-`colors`) path is unchanged by the patch (still
`get_next_color` per area) — modelling it would add no discriminating clause and
no failing prepatch.

## D. verify(Solution) ⇒ resolved

`selectLayerColors` verifies only if its output equals the cyclic repetition of
the supplied colours (A3) AND the shared colour cycle is returned exactly as it
came in (A4). By R (`colour-spec ↔ String`, `y.shape[0] ↔ layerCount`,
`range ↔ List.range`) the verified selection equals the post-patch
`facecolor=next(itertools.cycle(colors))` assignment on the tested inputs; by
G-AX the deep model `cyclicColors` equals the real `itertools.cycle` consumption
(A-reference); by G-CONF the R/I transliteration agrees with `patch.diff`'s
rendered-colour behaviour AND the control-axes frame holds over ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep model — and the gold patch
resolves the F2P `test_stackplot[png]`/`[pdf]` (G-RESOLVE). Trust points are
exactly the two of plan §1.1: deep-model soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).
