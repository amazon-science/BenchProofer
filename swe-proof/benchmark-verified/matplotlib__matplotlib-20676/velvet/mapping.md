# mapping.md — matplotlib__matplotlib-20676

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6786f437df54ca7780a047203cbcfaa1db8dc542`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the unchanged callees.

Repo file under change: `lib/matplotlib/widgets.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initialMarkerPositions (o, horizontalLimits, verticalLimits, currentSpan)` | `SpanSelector._setup_edge_handle(self, props)` — `lib/matplotlib/widgets.py:2158` | the modeled changed function: it computes the INITIAL positions the boundary-marker artists are created at |
| `Orientation` (`.horizontal` / `.vertical`) | `self.direction` (`self._direction`), a `{'horizontal','vertical'}` string — `lib/matplotlib/widgets.py:2196-2217` (property) | the picker's orientation, fixed at construction |
| `horizontalLimits : Rat × Rat` | `self.ax.get_xbound()` — `lib/matplotlib/axes/_base.py:3516` | order-preserving `(lower, upper)` view-limit pair of the horizontal axis (unchanged callee; a pure value source) |
| `verticalLimits : Rat × Rat` | `self.ax.get_ybound()` — `lib/matplotlib/axes/_base.py:3860` | order-preserving `(lower, upper)` view-limit pair of the vertical axis (unchanged callee; a pure value source) |
| `currentSpan : Rat × Rat` | `self.extents` (the `(vmin, vmax)` property) — `lib/matplotlib/widgets.py:2320-2329` | the picker's present selection span; read-only input that must NOT influence the result |
| (result `out`) consumed by | `ToolLineHandles(self.ax, <positions>, direction=..., ...)` — `lib/matplotlib/widgets.py:2342-2372`; `.positions` property at `:2374-2378` | the unchanged consumer: the boundary-handle container created at `<positions>`; `.positions` reports them back verbatim |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): the first positional argument to `ToolLineHandles` was
`self.extents` (`widgets.py:2159` pre-patch). The fix replaces it with the
orientation-matched axis bounds.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.direction` ∈ `{'horizontal','vertical'}` | `Orientation` | `'horizontal'` ↔ `.horizontal`; `'vertical'` ↔ `.vertical`. `direction.setter` (`widgets.py:2201`) checks the string is one of exactly these two via `_api.check_in_list`, so the carrier is total. |
| `self.ax.get_xbound()` → `(left, right)` with `left ≤ right` | `horizontalLimits : Rat × Rat` | the float pair ↔ a `Rat × Rat`; modeled order-only (the discriminating behaviour is *which axis's limits are chosen*, not float precision), so `Rat` is exact and sufficient. `get_xbound` returns the limits in increasing order (`_base.py:3526-3530`). |
| `self.ax.get_ybound()` → `(bottom, top)` with `bottom ≤ top` | `verticalLimits : Rat × Rat` | as above, for the vertical axis (`_base.py:3860`). |
| `self.extents` → `(vmin, vmax)` | `currentSpan : Rat × Rat` | the present span pair ↔ `Rat × Rat`. At construction it is the degenerate rectangle `(0, 0)` (the `_rect` starts at origin with zero width, `widgets.py:2147`); read-only, never enters the result. |
| `ToolLineHandles(ax, positions, ...).positions` | identity on the result pair | the handle container places its line artists at exactly the `positions` argument and `.positions` returns `[getattr(line, get_*data)()[0] for line in artists]` (`widgets.py:2372-2378`), i.e. the very values passed in. So observing `tool._edge_handles.positions` observes the result `out`. Identity on `Rat × Rat` ↔ `[lo, hi]`. |

A 2-element pair (`Rat × Rat`) is the carrier because both `get_*bound()` and the
constructed `ToolLineHandles` deal in exactly the two boundary positions (the
`_edge_order = ['min', 'max']`, `widgets.py:2109`).

## 3. Callee provenance

There are **no consumed axioms and no deep-model A-references** in this bundle.
The unchanged callees the modeled function invokes are pure value sources whose
results are taken directly as the operation's inputs / consumer:

### 3.1 `get_xbound` / `get_ybound` (unchanged value-source callees → inputs)
`self.ax.get_xbound()` and `self.ax.get_ybound()` are unchanged by the patch.
They return the `(lower, upper)` view limits of the respective axis in increasing
order (`_base.py:3516-3530`, `:3860-3874`). Their results are the modeled
operation's inputs `horizontalLimits` / `verticalLimits`; they are not modeled
deeply, so they carry no Lean `axiom`. G-CONF feeds the **real** `get_xbound()` /
`get_ybound()` outputs into the shadow, so their behaviour is exercised live.

### 3.2 `ToolLineHandles` (unchanged consumer callee)
Unchanged by the patch. The result `out` is passed to `ToolLineHandles` as its
`positions`, and the handles are created at exactly those positions
(`widgets.py:2372`); `.positions` reports them back (`widgets.py:2374-2378`).
G-CONF observes `tool._edge_handles.positions` on the **real** patched
`SpanSelector`, so this consumer is exercised live, not modeled.

Because every leg is an R/I refinement validated end-to-end by G-CONF against the
real callees, there is no `axiom_check.py` and **G-AX = skip** (the precedent is
`tasks/astropy__astropy-13236`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`20676`** so the
consumer-side verdict (§11.3) is reproducible. It builds a bounded pool of
distinct real `SpanSelector` configurations (both orientations; data away from
0, crossing 0, negative-only, tiny, large, asymmetric x/y), reads back the axis
bounds the real axes report and the real `_edge_handles.positions`, then performs
≥10⁵ shadow/oracle comparisons by sampling the pool (the observable is a pure
function of the configuration). The shadow transliterates the orientation-matched
selection of `initialMarkerPositions`; `currentSpan` is passed in and confirmed
unused.
