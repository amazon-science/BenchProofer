# refinement.md — mwaskom__seaborn-3069

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`finalizeAxis` `do` block plus the `decidedLimits`/`decidedGrid` pure models) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, performs the same per-axis
finalization decision as the gold patch on the observable state the F2P tests
read, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change — `Plotter._finalize_figure` per-axis loop body (`seaborn/_core/plot.py:1628`)

Gold hunk (the added categorical block, lines 1646–1656 post-patch):
```python
+                axis_obj = getattr(ax, f"{axis}axis")
 ...
+                # Nominal scale special-casing
+                if isinstance(self._scales.get(axis_key), Nominal):
+                    axis_obj.grid(False, which="both")
+                    if axis_key not in p._limits:
+                        nticks = len(axis_obj.get_major_ticks())
+                        lo, hi = -.5, nticks - .5
+                        if axis == "y":
+                            lo, hi = hi, lo
+                        set_lim = getattr(ax, f"set_{axis}lim")
+                        set_lim(lo, hi, auto=None)
```
(The other two hunks — `from ... import Scale, Nominal` at the top and removing a
redundant local `from ... import Nominal` inside `_setup_scales` — are an import
relocation with no behavioural effect; they make the `Nominal` name available at
the `_finalize_figure` call site. No model node; pure I on a non-observable.)

| # | Solution.lean impl op (`finalizeAxis`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | inputs `isCategorical, hasUserLimit, isY, nticks, userLo, userHi, autoLo, autoHi, gridWasOn` | the loop's read-only observations: `isinstance(self._scales.get(axis_key), Nominal)`, `axis_key in p._limits`, `axis == "y"`, `len(axis_obj.get_major_ticks())`, the resolved `p._limits[axis_key]`, the default-margin limits, the active-style grid | R | each bridged 1:1 by mapping.md §2. None is mutated by the decision (directive 5): the model reads them and never writes back to an input. |
| 2 | `lo := autoLo; hi := autoHi` then `if hasUserLimit then lo := userLo; hi := userHi` | the pre-existing limit logic: default margins, overridden by `ax.set(**{f"{axis}lim": (lo,hi)})` when `axis_key in p._limits` (lines 1635–1645) | I | identical control flow: pinned limits win over default margins. Concrete, transliterated by G-CONF. |
| 3 | `if isCategorical then grid := false` | `if isinstance(...Nominal): axis_obj.grid(False, which="both")` | I | grid suppressed exactly on the categorical axis; `decidedGrid` encodes this. `which="both"` ⇒ all gridlines hidden, matching the F2P `not any(x.get_visible() ...)`. |
| 4 | `if isCategorical then (if hasUserLimit then pure () else set ±1/2 limits)` | `if isinstance(...Nominal): ... if axis_key not in p._limits: ... set_lim(...)` | I | the categorical limit-set is guarded by "no pinned limit" — `decidedLimits` gives the user pair priority, matching `if axis_key not in p._limits`. The F2P `p.limit(x=lim)` case asserts the pinned limit survives. |
| 5 | `edge := (nticks : Rat) - 1/2`; `if isY then lo := edge; hi := -1/2 else lo := -1/2; hi := edge` | `lo, hi = -.5, nticks - .5`; `if axis == "y": lo, hi = hi, lo`; `set_lim(lo, hi, auto=None)` | R + I | the half-integer arithmetic is exact: `-.5` and `nticks-.5` are dyadic, so `Rat` (`-1/2`, `(nticks:Rat)-1/2`) equals the IEEE-754 floats bit-for-bit (mapping.md §2, R). The y-axis swap `lo,hi = hi,lo` is the `isY` branch reversal (I) — this is the "axis is inverted" requirement. |
| 6 | result `{ lo, hi, gridVisible }` | the installed `get_{x,y}lim()` and gridline visibility | R | `AxisFinal` records exactly the observable state the F2P tests read; `set_lim`/`grid` are effects that install it (mapping.md §3). |

## Discriminating content & the prepatch

The behavioural change is steps 3–5: on a categorical, non-pinned axis,
(a) suppress the grid and (b) set limits to `[-1/2, n-1/2]`, reversed on y.
`Solution_prepatch.lean` reproduces the pre-patch body (no categorical block:
grid left to the style, limits left to default margins) and **fails**
`prove_correct` precisely on `decidedGrid`/`decidedLimits` in the categorical
branch (G-DIFF) — the same divergence the F2P `test_nominal_x_axis_tweaks`
(`xlim == (-.5, 2.5)`, no visible gridlines) and `test_nominal_y_axis_tweaks`
(`ylim == (2.5, -.5)`) observe.

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — the per-axis
finalization decision — is modeled **deeply** (`decidedLimits`/`decidedGrid` and
the `do` block spell out the exact decision), not hidden behind an axiom. There
are **no** consumed axioms and no A-reference deep model: every value the
decision turns on is a read-only input bridged by mapping.md §2.

## verify(Solution) ⇒ resolved

`finalizeAxis` verifies only if its result equals `decidedGrid`/`decidedLimits`
on every input combination — i.e. it suppresses the grid and sets `[-1/2, n-1/2]`
(reversed on y) for a categorical non-pinned axis, defers to the pinned limits
otherwise, and leaves the grid to the style on a non-categorical axis. By R
(the input/limit bijection, exact for the dyadic half-integers) the verified
decision equals the gold patch's per-axis decision on the observable state; by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed input tuples. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom trust point for this bundle.
