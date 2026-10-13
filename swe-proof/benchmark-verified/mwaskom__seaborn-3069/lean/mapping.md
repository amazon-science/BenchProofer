# mapping.md — mwaskom__seaborn-3069

## Symbol binding (file:line @ base_commit 54cab15bdacfaa05a88fbc5502a5b322d99f148e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_nominalAxis` / `problem_spec_nominalAxis` / `correct_nominalAxis` | the per-axis finalization decision (grid visibility + extent) computed inside the `for axis in "xy"` loop of `Plotter._finalize_figure` | `seaborn/_core/plot.py:1628-1649` (`_finalize_figure`), patched block at `:1632-1660` |

The modeled function is the per-axis sub-computation that the patch adds to
`Plotter._finalize_figure`: for each subplot axis it decides (1) whether the
grid is forced off and (2) whether the axis extent is pinned to the categorical
range. It is the only behavior the patch changes and the only behavior the two
FAIL_TO_PASS tests observe.

### What the function does (base_commit)

At base_commit `_finalize_figure` only applies user-supplied limits:

```python
for sub in self._subplots:
    ax = sub["ax"]
    for axis in "xy":
        axis_key = sub[axis]
        # Axis limits
        if axis_key in p._limits:
            ...
            ax.set(**{f"{axis}lim": (lo, hi)})
```

A nominal/categorical axis is given no special treatment: its grid follows the
active style, and its extent follows matplotlib's ordinary data-margin logic.

### What the function does (post-fix)

The patch adds a per-axis block:

```python
axis_obj = getattr(ax, f"{axis}axis")
...
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

So a nominal axis: (a) always has its grid turned off; (b) when no explicit
limit was set for it, has its extent pinned to `(-0.5, nticks - 0.5)`, reversed
to `(nticks - 0.5, -0.5)` on the `y` axis. A non-nominal axis is left untouched.

### Input ↔ Python expression bijection

| Lean argument | Python source (`_finalize_figure`) | notes |
|---|---|---|
| `isY : Bool` | `axis == "y"` | which of the two axes the loop iteration is handling; `"x"` ↦ `false`, `"y"` ↦ `true` |
| `isNominal : Bool` | `isinstance(self._scales.get(axis_key), Nominal)` | whether the axis carries a Nominal scale (including inferred ones) |
| `hasLimit : Bool` | `axis_key in p._limits` | whether the user pinned an explicit limit on this axis |
| `nticks : Nat` | `len(axis_obj.get_major_ticks())` | number of major tick marks (= number of categories) on the axis |
| `result.gridHidden : Bool` | whether `axis_obj.grid(False, which="both")` was called | grid forced off |
| `result.fixedLimit : Option (ℚ × ℚ)` | the `(lo, hi)` passed to `set_{axis}lim(..., auto=None)`, or absence of that call | `some (lo, hi)` iff the categorical extent was pinned |

### Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `axis == "y"` (`bool`) | `isY : Bool` | `True`/`False` ↔ `true`/`false` |
| `isinstance(..., Nominal)` (`bool`) | `isNominal : Bool` | identity |
| `axis_key in p._limits` (`bool`) | `hasLimit : Bool` | identity |
| `len(axis_obj.get_major_ticks())` (`int ≥ 0`) | `nticks : Nat` | identity on non-negative integers |
| `-.5`, `nticks - .5` (`float`, exact half-integers) | `-1/2`, `(nticks : ℚ) - 1/2` (`ℚ`) | these limits are EXACT half-integers; modeled as `ℚ` so order/equality are transparent to the kernel (DECISIONS.md: never model order-relevant floats as kernel `Float`). The values `-0.5` and `n-0.5` are representable exactly in both. |
| `(lo, hi)` tuple passed to `set_{axis}lim` | `(ℚ × ℚ)` pair | identity; `y`-axis swap `lo, hi = hi, lo` ↔ `(hi, lo)` |
| "the call was/ wasn't made" | `Option` | call made ↔ `some (lo,hi)`; not made ↔ `none` |

The coordinates are exact half-integers (matplotlib computes `-.5` and
`nticks - .5` with no rounding), so `ℚ` is the faithful model (SPEC_GUIDE §2:
float with order-only / exact values → exact `Rat`).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The two decisions are a closed expression over
  the four inputs `(isY, isNominal, hasLimit, nticks)` using only Boolean tests,
  rational subtraction, and a pair swap; the modeled function calls no unchanged
  repo callee whose internal contract the proof must assume (SPEC_GUIDE §0.7).
  The tick count `nticks` and the nominal flag are taken as input observations
  resolved upstream (matplotlib tick generation / scale setup), not modeled
  callees. `axiom_check.py` is therefore a skip stub and G-AX skips.
- **Flag dependencies.** Two booleans gate the behavior and are honored by both
  the spec and the conformance oracle:
  - `isNominal` gates the entire special-casing (grid + extent). It is the
    `isinstance(self._scales.get(axis_key), Nominal)` test; the `Nominal` import
    moved to module top by the patch is a refactor with no behavioral effect.
  - `hasLimit` (`axis_key in p._limits`) gates ONLY the extent pin; the grid is
    hidden for every nominal axis regardless. When `hasLimit` is true the
    explicit-limit branch (unchanged code, above the new block) sets the extent,
    so the new block leaves `fixedLimit` unset.
- **Upstream provenance of inputs.** `self._scales`, `p._limits`, and the tick
  count are populated earlier in the plotting pipeline (`_setup_scales`,
  `.limit(...)`, matplotlib autoscaling); that resolution is unchanged by the
  patch and upstream of the modeled decision, so it is the (arbitrary) input to
  the modeled function.

## G-CONF fuzz seed

Pinned LCG seed: **3069** (see `conformance_check.py` `SEED`). Corpus: `isY`,
`isNominal`, `hasLimit` each drawn from `{False, True}`; `nticks` drawn from a
boundary set (`0, 1, 2, 3, 10, 100`) plus random non-negative integers. The full
cross-product of the three booleans with the boundary `nticks` set is enumerated
as the edge set (it contains the discriminating nominal cases for both `x` and
`y` axes); the fuzz loop then samples ≥1e5 random `(isY, isNominal, hasLimit,
nticks)` tuples, diffed against an in-process replica of the post-patch per-axis
finalization decision (0 disagreements required).
