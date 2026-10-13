# mapping.md — matplotlib__matplotlib-20676

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6786f437df54ca7780a047203cbcfaa1db8dc542`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `lib/matplotlib/widgets.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selector_initial_coords(direction, x_bound, y_bound, other_coords)` | `SpanSelector._setup_edge_handle(self, props)` — `lib/matplotlib/widgets.py:2158` | the modeled changed function: computes the initial handle positions and constructs the edge handles |
| `reported_positions(positions)` *(axiom — A-reference)* | `ToolLineHandles(ax, positions, …).positions` — `lib/matplotlib/widgets.py:2340` (`__init__`) and `:2375` (`positions` property) | unchanged community callee: the line-handle widget stores one line per supplied position and reports them back unchanged (`axvline(p)`/`axhline(p)` → `get_xdata()[0]`/`get_ydata()[0]` == p) |
| `HORIZONTAL`, `VERTICAL` | the string literals `'horizontal'`/`'vertical'` compared against `self.direction` (`widgets.py:2160`) | direction discriminant, modeled as `0`/`1` |
| parameter `x_bound` | `self.ax.get_xbound()` — `lib/matplotlib/axes/_base.py:3516` | the current x-axis bounds (lower, upper) |
| parameter `y_bound` | `self.ax.get_ybound()` — `lib/matplotlib/axes/_base.py:3860` | the current y-axis bounds (lower, upper) |
| parameter `other_coords` | `self.extents` — `SpanSelector.extents` property (`widgets.py:2322`); on a freshly-constructed selector the rectangle is at `(0,0)` with zero width/height, so it reads `(0, 0)` | the unrelated coordinate pair the pre-patch read from (the selector's own current shape extents); the spec-view parameter name is neutral (`other_coords`) so it does not telegraph the diagnosis |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): `self.extents` as the positional
argument to `ToolLineHandles` (`widgets.py:2159`, pre-patch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a single coordinate `float` (a bound endpoint, an extent endpoint) | `int` | the tested behaviour is a pure pass-through / selection of coordinate VALUES — no arithmetic, rounding, or comparison of fractional magnitudes is performed on them, so any injective `float ↔ int` encoding preserves the observed equalities. (Precision-independent per SPEC_GUIDE §2; see refinement.md.) |
| the pair `self.ax.get_xbound()` / `get_ybound()` (a 2-tuple of floats) | `Tuple[int, int]` | endpoint-wise `int` encoding above |
| `self.direction` `str` `'horizontal'`/`'vertical'` | `int` `0`/`1` | `_api.check_in_list(['horizontal','vertical'])` restricts the value to exactly these two; modeled as the two-valued discriminant `0`/`1` |
| `positions` `list`/tuple of 2 floats and `ToolLineHandles.positions` (a Python `list`) | `List[int]` of length 2 | element-wise as above; `list(bound)` ↔ the 2-element `List[int]` |

Floats are NOT modeled with `--float-encoding`: the bug is not a
precision/rounding bug, it is a *which-value-is-selected* bug (the current axis
bound vs. the rectangle's `(0,0)` extents). Equality of the observed positions
to the axis bound is preserved under the injective `int` encoding, so `int`
is faithful on the tested behaviour (refinement.md A-/R- rows).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reported_positions` ↔ `ToolLineHandles(ax, positions).positions` (A-reference)
**Callee:** `matplotlib.widgets.ToolLineHandles` (`lib/matplotlib/widgets.py:2326`).
`__init__(self, ax, positions, direction, …)` builds one line per supplied
position:

```python
line_fun = ax.axvline if self.direction == 'horizontal' else ax.axhline
self.artists = [line_fun(p, **line_props) for p in positions]
```

and the `positions` property reads them back:

```python
@property
def positions(self):
    method = 'get_xdata' if self.direction == 'horizontal' else 'get_ydata'
    return [getattr(line, method)()[0] for line in self.artists]
```

`ax.axvline(p)` creates `Line2D([p, p], [ymin, ymax])`, so `get_xdata()[0] == p`
(and symmetrically `axhline`/`get_ydata`). Therefore `ToolLineHandles(ax, P,
…).positions == list(P)` — the widget reports the supplied positions back
**unchanged**. The model encodes this as the identity `reported_positions(P) ==
P` (a deep model of the unchanged callee), NOT consumed as a load-bearing
axiom about the *changed* operation. The changed operation — which positions
are supplied — is modeled directly (the directional selection in
`selector_initial_coords`).

The *reason this is the whole point of the fix*: `axvline(p)` sets
`scalex = (p < xmin) or (p > xmax)` against the current `get_xbound()` and then
`_request_autoscale_view(scalex=scalex)` (`axes/_axes.py:743`). When the supplied
`p` is already inside the current bounds (post-patch: `p ∈ get_xbound()`),
`scalex == False` and the view is NOT expanded. When `p == 0` from the
pre-patch `extents == (0, 0)` and `0` lies outside `(10, 20)`, `scalex == True`
and the axes expand to include `0` — the reported bug. The model does not need
to encode autoscale: passing the current bound back is necessary and
sufficient for both observables the F2P test checks (positions == the bound,
and the bound is unchanged).

**Soundness check (G-AX):** `axiom_check.py` constructs a real Matplotlib axes
(Agg backend, no display), builds `ToolLineHandles(ax, positions, direction)`
for both directions over boundary + fuzz position pairs, and asserts
`ToolLineHandles(...).positions == list(positions)` (the A-reference identity).
It additionally reproduces the end-to-end observable: building the interactive
`SpanSelector` leaves `ax.get_xbound()`/`get_ybound()` unchanged and yields
`_edge_handles.positions == list(get_xbound()/get_ybound())`, while a pre-patch
construction (positions `= (0, 0)`) does expand the bound — confirming the
discriminator the spec pins. It imports only `matplotlib` (the very module the
patch changes). Exit 0 iff sound.
