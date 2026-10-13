# refinement.md — mwaskom__seaborn-3069

The operation-by-operation correspondence between `model.py`'s implementation
(the `finalize_axis_range` and `finalize_axis_grid` impl regions) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`Ensures`, **A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The categorical range site — `finalize_axis_range` ⇔ the new block in `_finalize_figure`

Gold hunk (`seaborn/_core/plot.py`, new "Nominal scale special-casing" block):
```
+ if isinstance(self._scales.get(axis_key), Nominal):
+     axis_obj.grid(False, which="both")
+     if axis_key not in p._limits:
+         nticks = len(axis_obj.get_major_ticks())
+         lo, hi = -.5, nticks - .5
+         if axis == "y":
+             lo, hi = hi, lo
+         set_lim = getattr(ax, f"set_{axis}lim")
+         set_lim(lo, hi, auto=None)
```
and the pre-existing explicit-limit block it sits beside (lines `:1635-1645`,
unchanged), which computes `lo, hi` from `p._limits[axis_key]`.

| # | model.py impl op (`finalize_axis_range`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `is_categorical: bool` | `isinstance(self._scales.get(axis_key), Nominal)` | R | the runtime Nominal-type test ↔ the boolean (mapping.md §2). |
| A2 | `has_explicit: bool` | `axis_key in p._limits` | R | dict membership ↔ the boolean (mapping.md §2). |
| A3 | `is_vertical: bool` | `axis == "y"` over the `"xy"` loop | R | string compare ↔ the boolean (True on the y iteration). |
| A4 | `if has_explicit: lo = user_lo; hi = user_hi` | the explicit-limit branch (`:1635-1645`): `lo, hi` from `p._limits[axis_key]`, applied; the new block's inner `if axis_key not in p._limits:` guards the categorical range OUT when a limit exists | I + R | when a limit exists the categorical range is not applied; the range is the caller's `(lo, hi)`. `user_lo/user_hi` ↔ the computed `lo, hi` (mapping.md §2). Domain boundary: the precondition `Implies(has_explicit, user_lo != user_hi)` excludes a singular caller pair — matplotlib's unchanged pre-existing range-sanitization expands a degenerate span before it lands as the visible range, behaviour identical before and after the patch and outside the modeled slice (mapping.md §2). |
| A4b | the fall-through (`lo, hi` initialised to `user_lo, user_hi` and returned unchanged when `not has_explicit and not is_categorical`) | the OUTER `isinstance(self._scales.get(axis_key), Nominal)` gate: a non-Nominal axis never enters the new block, so `_finalize_figure` never touches its range — it keeps the pre-existing automatic-margin range | I + R | the identity clauses `Implies(not is_categorical and not has_explicit, Result()[0]==user_lo)` / `Result()[1]==user_hi` pin this sub-domain. Without them the spec admitted a rival that dropped the `isinstance(..., Nominal)` gate and applied the categorical range to EVERY non-explicit axis; its faithful patch broke the hidden P2P log-scale tests (`test_faceted_log_scale`, `test_paired_single_log_scale`) — the recorded G-EQ attack. `user_lo/user_hi` ↔ the untouched pre-finalization range (mapping.md §2). |
| A5 | `elif is_categorical: n = slot_count()` | `nticks = len(axis_obj.get_major_ticks())` | A-consumed | `slot_count() >= 1` is the weakest contract on the unchanged matplotlib tick API the proof needs (mapping.md §3.1). The proof consumes its `Ensures` (it grounds the `n - 0.5` upper edge as `> -0.5`, giving a non-degenerate range). G-AX confirms `len(get_major_ticks()) >= 1` (and `== n`) on the real categorical axis. |
| A6 | `lo = -0.5; hi = n - 0.5` | `lo, hi = -.5, nticks - .5` | I | identical concrete arithmetic; `0.5` is exact under `--float-encoding=real`; `n` ↔ `nticks` via A5. |
| A7 | `if is_vertical: lo, hi = hi, lo` (via tmp) | `if axis == "y": lo, hi = hi, lo` | I | identical swap; the vertical axis range is the same pair reversed. |
| A8 | `return (lo, hi)` | `set_lim(lo, hi, auto=None)` records the pair as the axis range | R | matplotlib `set_xlim/set_ylim` store exactly the `(lo, hi)` given; `get_xlim/get_ylim` (what the F2P tests read) return it. The returned tuple ↔ the recorded range (mapping.md §2). |

The discriminating content — a categorical axis with no caller range gets the
range `(-0.5, n-0.5)` (inverted on y) rather than the ordinary automatic-margin
range — lives in A6/A7. The pre-patch code has **no** such block, so a nominal
axis keeps its automatic-margin range; `model_prepatch.py` reproduces that (the
categorical branch is absent, the range stays at the pre-existing/default value)
and **fails** the postcondition `Result()[0] + 0.5 == 0.0` (the categorical
lower edge `-0.5`), which is exactly the spec sensing the change (G-DIFF). The
deep range model is validated == the real finalized range by G-AX (A-reference,
mapping.md §3.2).

## B. The grid site — `finalize_axis_grid` ⇔ `axis_obj.grid(False, which="both")`

| # | model.py impl op (`finalize_axis_grid`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `grid_visible = pre_visible` (default) | a non-categorical axis never enters the `isinstance(... Nominal)` block, so `_finalize_figure` makes NO grid call — the axis keeps whatever gridline visibility the active rc style had already produced | I + R | absence of the grid-off call ↔ visibility unchanged. `pre_visible` ↔ the pre-finalization gridline visibility (mapping.md §2); the identity clause `Implies(not is_categorical, Result() == pre_visible)` pins this sub-domain, so a rival whose faithful patch forces a grid state on ordinary axes is rejected. |
| B2 | `if is_categorical: grid_visible = False` | `axis_obj.grid(False, which="both")` (inside the `isinstance(... Nominal)` block) | A-reference | the grid-off effect is modeled deeply (`Implies(is_categorical, not Result())` — off whatever `pre_visible` was); validated == the real gridline visibility by G-AX (`any(g.get_visible() ...)` is False on a categorical axis under both grid rc themes), mapping.md §3.3. |

The pre-patch code never turns the grid off; `model_prepatch_grid.py` reproduces
that (`grid_visible = pre_visible` always — every axis keeps its incoming
visibility) and **fails** the postcondition
`Implies(is_categorical, not Result())` for a categorical axis whose incoming
visibility was on (G-DIFF). This is an independently-observable fixed
behaviour — the F2P tests assert both the range AND the gridline
invisibility — so it gets its own failing prepatch.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The two operations that
genuinely *changed* — the categorical range computation and the grid-off — are
modeled **deeply** (the spelled-out branch in `finalize_axis_range` and the
boolean in `finalize_axis_grid`), not hidden behind an axiom about the function
under change. There is no consumed range/grid axiom. The only consumed axiom,
`slot_count` (**A-consumed**, step A5), covers an **unchanged** matplotlib
callee (`Axis.get_major_ticks`) the new code merely *reads*; its count appears
in the model only via that axiom, and the deep range/grid models are the
**A-references** that G-AX validates against the real finalized axis (§A8, §B2).

## D. verify(model) ⇒ resolved

`finalize_axis_range` verifies only if, on a categorical axis with no caller
range, it produces `(-0.5, n-0.5)` (A6) reversed on the vertical axis (A7), the
verbatim caller range when one is present (A4), and the UNCHANGED incoming
range on an ordinary (non-categorical) axis with no caller range (A4b — so a
gate-dropping rival that imposes the categorical range on every axis is
rejected, closing the recorded G-EQ break); `finalize_axis_grid` verifies
only if a categorical axis's grid is off (B2) AND an ordinary axis's grid
visibility passes through unchanged (B1 — so a rival that forces a grid state
on ordinary axes is rejected). By R (the boolean/type refinements and
`set_xlim/set_ylim` recording the pair) the verified range is exactly what
the gold block sets via `set_lim(lo, hi, auto=None)`, and the verified grid
boolean is exactly the `grid(False)` effect (present iff categorical). By
A-consumed the real `get_major_ticks` count meets `slot_count() >= 1`; by
A-reference (G-AX) the deep range/grid models equal the real finalized axis
range and gridline visibility on the F2P witnesses and the `n = 1..12` sweep
(grid under both rc themes, ordinary-axis pass-through grounded against the
captured pre-finalization visibility). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited unchanged callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
