# mapping.md — mwaskom__seaborn-3069

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 54cab15bdacfaa05a88fbc5502a5b322d99f148e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

`spec_provenance: cold` — derived from `problem_statement` + gold `patch` +
repo source only.

Repo file under change: `seaborn/_core/plot.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finalizeAxis (...)` | the per-axis body of `Plotter._finalize_figure(self, p)` — `seaborn/_core/plot.py:1628` (the `for axis in "xy":` loop body, lines 1631–1645 pre-patch; the patch adds the categorical block at 1646–1656) | the modeled changed function: the finalization decision for one axis |
| `decidedLimits (...)` | the post-patch view-limit decision the loop body computes per axis (`ax.set(**{f"{axis}lim": ...})` at 1645 and the new `set_lim(lo, hi, auto=None)` at 1655) | pure spec: the (lo, hi) view limits set on the axis |
| `decidedGrid (...)` | the post-patch grid decision (`axis_obj.grid(False, which="both")` at 1648, vs. leaving the active-style grid otherwise) | pure spec: whether gridlines remain visible |
| `AxisFinal` | the observable axis state finalization sets: `ax.get_{x,y}lim()` and `ax.{x,y}axis` gridline visibility (what the F2P tests assert) | model carrier (structure, only the touched fields) |

The repo symbol the patch keys on — `isinstance(self._scales.get(axis_key), Nominal)` (line 1647, post-patch) — is modeled by the read-only input `isCategorical`. `Nominal` is the discrete/categorical scale class (`seaborn/_core/scales.py`); a `Nominal`-scaled axis is exactly the "categorical axis" the public issue describes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `isinstance(self._scales.get(axis_key), Nominal)` (a categorical scale on this axis) | `isCategorical : Bool` | `True ↔ true` |
| `axis_key in p._limits` (consumer pinned limits for this axis) | `hasUserLimit : Bool` | `True ↔ true` |
| `axis == "y"` | `isY : Bool` | `"y" ↔ true`, `"x" ↔ false` |
| `len(axis_obj.get_major_ticks())` (tick count) | `nticks : Nat` | `n ↔ (n : Nat)`; always ≥ 0 |
| `(lo, hi)` view-limit floats (`ax.get_{x,y}lim()`) | `Rat × Rat` | a float value `v` ↔ the rational `v`. The only non-integer limits the categorical branch produces are the exact half-integers `-1/2` and `n - 1/2`; `Rat` represents them exactly (no IEEE rounding). User/auto limits are transported verbatim. |
| `-.5`, `nticks - .5` literals (line 1652) | `-1/2`, `(nticks : Rat) - 1/2` | exact: `-.5` and `n-.5` are dyadic, hence exact in both IEEE-754 `float` and `Rat` |
| the consumer's resolved limit pair `p._limits[axis_key]` after `convert_units` (lines 1636–1644) | `(userLo, userHi) : Rat × Rat` | transported verbatim; finalization does not recompute them in the categorical case (`if axis_key not in p._limits:` guards the categorical limit-set, line 1650) |
| the limits the default margin logic would set when neither user nor categorical applies | `(autoLo, autoHi) : Rat × Rat` | the would-be `get_{x,y}lim()` for a non-categorical, non-pinned axis; transported verbatim (finalization leaves them unchanged) |

The model is per-axis: `_finalize_figure` runs this same decision independently
for `axis ∈ {"x","y"}` of every subplot. `finalizeAxis` models one axis; the x
and y F2P assertions are the `isY=false` and `isY=true` instantiations.

## 3. Callee provenance

No axiomatized callees and no A-reference deep model.

- `axis_obj.grid(False, which="both")`, `set_lim(lo, hi, auto=None)`,
  `ax.set(**{f"{axis}lim": ...})` are **effects** that install the decided grid
  state / view limits; they are not values the spec reads back through a
  contract. They are modeled as the assignment of `decidedGrid` / `decidedLimits`
  to the result `AxisFinal` (the observable state the F2P tests read via
  `get_{x,y}lim()` and `xaxis.get_gridlines()[i].get_visible()`).
- `len(axis_obj.get_major_ticks())` and the default-margin limits are read-only
  environment observations, passed in as the inputs `nticks` / `autoLo,autoHi`.
  The patch does not change how ticks are produced or how default margins are
  computed; it only consumes them. So they are inputs, not axioms.

Hence there is **no axiom_check.py** for this bundle (G-AX = skip, meta.json).
The changed operation is a pure decision over these inputs, modeled deeply by
`decidedLimits`/`decidedGrid` and the `do` block — all R/I content, so G-CONF
produces a real (non-skip) verdict.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`3069`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `decidedLimits`/`decidedGrid` to Python and compares against the
patched `_finalize_figure` per-axis decision transliterated verbatim from the
gold patch (the oracle), over fuzzed `(isCategorical, hasUserLimit, isY, nticks,
userLo, userHi, autoLo, autoHi, gridWasOn)` tuples. There are no A-tagged ops to
leave as a real callee.
