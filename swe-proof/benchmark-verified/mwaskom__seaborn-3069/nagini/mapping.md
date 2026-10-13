# mapping.md — mwaskom__seaborn-3069

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 54cab15bdacfaa05a88fbc5502a5b322d99f148e`, states the type
abstraction, and gives the provenance of the consumed axiom and the two deep
models (callee source + the exact behaviour each encodes).

Repo file under change: `seaborn/_core/plot.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finalize_axis_range(is_categorical, has_explicit, is_vertical, user_lo, user_hi)` | the per-axis limit logic inside `Plotter._finalize_figure` — `seaborn/_core/plot.py:1628` (loop body at `:1631-1645`, new categorical block added at `:1647-1657`) | the modeled changed behaviour: the final `(lo, hi)` axis range a categorical axis receives |
| `finalize_axis_grid(is_categorical, pre_visible)` | the gridline-visibility effect of `axis_obj.grid(False, which="both")` added in the same block (`seaborn/_core/plot.py:1648`) | the modeled changed behaviour: whether a finalized axis shows gridlines. `pre_visible` carries the axis's gridline visibility immediately before `_finalize_figure` runs (whatever the active rc style produced); a non-Nominal axis never enters the block, so its visibility survives unchanged |
| `slot_count()` *(axiom — A-consumed)* | `len(axis_obj.get_major_ticks())` (matplotlib `Axis.get_major_ticks`), used at `seaborn/_core/plot.py:1650` post-patch | unchanged matplotlib tick-querying routine the new code calls to learn the number of category slots `n` |
| `is_categorical` | `isinstance(self._scales.get(axis_key), Nominal)` (`seaborn/_core/plot.py:1647`); `Nominal` is `seaborn/_core/scales.py:138` | whether the axis's scale is the categorical (Nominal) scale |
| `has_explicit` | `axis_key in p._limits` (`seaborn/_core/plot.py:1635, 1649`); `_limits` set by `Plot.limit` (`seaborn/_core/plot.py:650-668`) | whether the caller pinned an explicit range for the axis |
| `is_vertical` | `axis == "y"` (`seaborn/_core/plot.py:1653`) | whether the axis is the vertical (y) one |
| `user_lo / user_hi` | `lo, hi` computed from `p._limits[axis_key]` (`seaborn/_core/plot.py:1638-1644`) | the explicit caller range, when present |

The post-patch block being modeled (`seaborn/_core/plot.py`):

```python
# Nominal scale special-casing
if isinstance(self._scales.get(axis_key), Nominal):
    axis_obj.grid(False, which="both")
    if axis_key not in p._limits:
        nticks = len(axis_obj.get_major_ticks())
        lo, hi = -.5, nticks - .5
        if axis == "y":
            lo, hi = hi, lo
        set_lim = getattr(ax, f"set_{axis}lim")
        set_lim(lo, hi, auto=None)
```

The pre-existing explicit-limit block it sits beside (`:1635-1645`) computes
`lo, hi` from `p._limits[axis_key]` and applies them; that branch is the
`has_explicit` path of `finalize_axis_range`, preserved unchanged.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `isinstance(self._scales.get(axis_key), Nominal)` (a runtime type test) | `is_categorical: bool` | the boolean the test yields |
| `axis_key in p._limits` (dict membership) | `has_explicit: bool` | the boolean the membership yields |
| `axis == "y"` (string compare over the `"xy"` loop) | `is_vertical: bool` | True on the y iteration, False on the x iteration |
| `nticks = len(axis_obj.get_major_ticks())` (int) | `slot_count() -> int` (axiom) | the number of category slots `n`; `nticks` ↔ `slot_count()` |
| the axis range `(lo, hi)` / `set_xlim`/`set_ylim` argument (a pair of `float`) | `Tuple[float, float]` interpreted reals (`--float-encoding=real`) | `(lo, hi)` ↔ `Result()`; `set_xlim(lo, hi)` / `set_ylim(lo, hi)` record exactly this pair (matplotlib stores the (lo, hi) given) — **for a non-singular pair (`lo != hi`)**. A singular explicit pair (`lo == hi`) is expanded by matplotlib's pre-existing range-sanitization (`nonsingular`) before it lands as the visible range; that machinery is unchanged by the patch and identical before/after it, so the model excludes the singular case from the explicit-range domain via the precondition `Implies(has_explicit, user_lo != user_hi)` rather than modeling deep unrelated matplotlib internals |
| `axis_obj.grid(False, ...)` side effect (gridlines turned off) | `finalize_axis_grid -> bool` (grid visible?) | `False` (grid off) ↔ result `False`; the categorical axis draws no visible gridlines. For a non-Nominal axis the call never happens, so the result is the incoming visibility (`pre_visible` ↔ the pre-finalization gridline visibility the active rc style produced) |
| the literal `-.5` / `nticks - .5` half-slot offsets | the literals `-0.5` / `n - 0.5` | exact, `0.5` is representable; the test compares exact float tuples |

Floats are interpreted reals (`--float-encoding=real`) because the behaviour at
stake is a real-valued range relation (edges half a slot beyond the extreme
category positions, reversed on y) probed to floating tolerance; `0.5` is exact
so no precision loss arises.

The `axis_obj = getattr(ax, f"{axis}axis")` line the patch also adds is a pure
local-binding refactor (it names the matplotlib `Axis` object the new block
queries via `get_major_ticks` / `grid`); it introduces no observable behaviour
of its own and is not separately modeled.

## 3. Provenance — the consumed axiom and the two deep models (G-AX)

### 3.1 `slot_count` ↔ `len(Axis.get_major_ticks())` (A-consumed)
**Callee:** matplotlib `matplotlib.axis.Axis.get_major_ticks(numticks=None)` —
returns the list of major `Tick` objects for the axis. For a categorical
(Nominal) axis seaborn places one tick per category, so the count equals the
number of categories `n >= 1`. The proof consumes only the **weakest** fact it
needs: `slot_count() >= 1` (so the upper edge `n - 0.5 > -0.5`, giving a
non-degenerate increasing horizontal range / decreasing vertical range). This
is matplotlib's unchanged tick API — the patch does not change it; it only
*reads* the count. Docs:
https://matplotlib.org/stable/api/_as_gen/matplotlib.axis.Axis.get_major_ticks.html

**Soundness check (G-AX):** `axiom_check.py` builds real categorical axes
(`Plot(x=cats, y=...)` / `Plot(x=..., y=cats)`) for `n = 1..12` and asserts the
real `len(axis.get_major_ticks())` is `>= 1` AND equals `n` (so the `n - 0.5`
upper edge is grounded in the real count, not assumed).

### 3.2 `finalize_axis_range` ↔ the real finalized axis range (A-reference)
The changed range behaviour is modeled **deeply** (the spelled-out branch over
`is_categorical` / `has_explicit` / `is_vertical` producing `(-0.5, n-0.5)`,
inverted on y, the verbatim caller range, or the UNCHANGED incoming range on a
non-categorical axis with no caller range); there is **no consumed range
axiom**. The deep model is validated **== the real callee** out-of-band by
`axiom_check.py` (G-AX): it runs the real seaborn `Plot.plot()` and asserts
`get_xlim()` / `get_ylim()` equal the model's prediction — exactly the F2P
assertions:
* `Plot(x=["a","b","c"], y=[1,2,3])` → `get_xlim() == (-0.5, 2.5)`;
* `Plot(x=[1,2,3], y=["a","b","c"])` → `get_ylim() == (2.5, -0.5)` (inverted);
* `.limit(x=(-1, 2.1))` → `get_xlim() == (-1, 2.1)` (explicit range verbatim);

plus the identity sub-domain (`not is_categorical and not has_explicit` →
`Result() == (user_lo, user_hi)`, the range left untouched), which mirrors the
real outer `isinstance(..., Nominal)` gate: a non-Nominal axis never enters the
new block, so its automatic-margin range survives finalization. This clause is
what the hidden P2P log-scale tests (`test_faceted_log_scale`,
`test_paired_single_log_scale`) observe — a rival that drops the gate imposes
`(-0.5, n-0.5)` on a log axis and crashes/fails them (the recorded G-EQ
attack). `axiom_check.py` grounds it against the real repo: a continuous axis'
finalized `get_xlim()/get_ylim()` equals the range captured immediately before
`Plotter._finalize_figure` ran (the finalizer touched nothing), and a
log-scaled axis keeps strictly positive limits with an intact log transform.

### 3.3 `finalize_axis_grid` ↔ the real gridline visibility (A-reference)
The changed grid behaviour (`axis_obj.grid(False, which="both")`) is modeled
deeply: `finalize_axis_grid(is_categorical, pre_visible)` returns `False` on a
categorical axis (grid turned off whatever it was before) and `pre_visible`
unchanged on an ordinary axis (a non-Nominal axis never enters the new block,
so `_finalize_figure` never touches its grid — the rc-style-produced
visibility survives). Validated == the real callee by `axiom_check.py`: a
categorical axis has no visible gridlines
(`any(g.get_visible() for g in axis.get_gridlines())` is False) under both a
grid-drawing and a grid-suppressing rc theme, mirroring the F2P assertion
`not any(x.get_visible() for x in ax.xaxis.get_gridlines())`; and an ordinary
axis's finalized gridline visibility equals the visibility captured
immediately before `Plotter._finalize_figure` ran, across both truth values
of that pre-visibility (theme sweep). The earlier model hardcoded the
ordinary-axis result to "grid on", which misstates the real finalizer under a
grid-suppressing style — the G-PANEL-2 counterexample this revision corrects.

`axiom_check.py` imports only `seaborn` and `matplotlib` (the package the gold
patch lives in); nothing test- or harness-specific. Exit 0 iff every obligation
holds.

## 4. G-CONF (conformance_check.py)

Differential gate: the contract-stripped impl regions (shadow) vs the real
patched `Plotter._finalize_figure` (oracle) driven per trial on a live
matplotlib Axes, per the section-2 bridge; `slot_count()` is bound to the real
live major-tick count. >= 1e5 Requires-satisfying inputs (exhaustive boolean
boundary grid + slot/range sweeps + 55000 fuzz trials, each trial checking
both axes' range and grid). **Pinned fuzz seed: 3069** (the instance number).
