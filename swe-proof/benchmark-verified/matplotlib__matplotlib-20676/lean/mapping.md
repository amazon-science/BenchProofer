# mapping.md — matplotlib__matplotlib-20676

## Symbol binding (file:line @ base_commit 6786f437df54ca7780a047203cbcfaa1db8dc542)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_initialMarkers` / `problem_spec_initialMarkers` | the choice of the initial handle positions inside `SpanSelector._setup_edge_handle` | `lib/matplotlib/widgets.py:2158-2162` |
| `MarkerSetup` (pure helper) | the inputs that choice reads: `self.direction`, `self.extents`, and the axis' view bounds along x / y | `widgets.py:2158`, `widgets.py:2320-2330` (`extents`), `ax.get_xbound()`/`ax.get_ybound()` |
| `SelectDirection` (pure helper) | the string flag `self.direction ∈ {"horizontal","vertical"}` | `widgets.py:2316-2319` |
| `initialMarkers` (pure helper) | the value bound to the local `positions` and passed as the `positions=` argument of `ToolLineHandles(...)` | `widgets.py:2159` |

## What the function does (base_commit)

`SpanSelector._setup_edge_handle(self, props)` constructs the pair of interactive
boundary-marker lines for the selector and stores them. At `base_commit`:

```python
def _setup_edge_handle(self, props):
    self._edge_handles = ToolLineHandles(self.ax, self.extents,
                                         direction=self.direction,
                                         line_props=props,
                                         useblit=self.useblit)
    self.artists.extend([line for line in self._edge_handles.artists])
```

The first positional argument after `self.ax` is `positions` — the data
coordinates at which the marker lines are drawn. `ToolLineHandles.__init__` draws
one line per position with `ax.axvline(p)` (horizontal direction) or
`ax.axhline(p)` (vertical direction); its `.positions` property reads each line's
data back, so `ToolLineHandles(ax, positions, ...).positions == list(positions)`
(identity pass-through, unchanged by the patch).

At construction time `_setup_edge_handle` is reached from `SpanSelector.__init__`
when `interactive=True`. At that point `self._rect` is the zero-size rectangle
created by `new_axes` (`Rectangle((0, 0), w, h)` with the moving dimension width
`0`), so `self.extents` — computed from the rectangle's position/size — is
`(0, 0)`. Drawing the markers at `0` via `axvline(0)` / `axhline(0)` expands the
axis view to include `0`, which is the reported bug (xlim forced down to 0).

`self.extents` (`widgets.py:2320`):

```python
@property
def extents(self):
    if self.direction == 'horizontal':
        vmin = self._rect.get_x(); vmax = vmin + self._rect.get_width()
    else:
        vmin = self._rect.get_y(); vmax = vmin + self._rect.get_height()
    return vmin, vmax
```

### Post-patch behavior

The patch chooses the initial marker positions from the axis' current view bounds
along the selection direction, instead of from the (degenerate) selector extents:

```python
def _setup_edge_handle(self, props):
    if self.direction == 'horizontal':
        positions = self.ax.get_xbound()
    else:
        positions = self.ax.get_ybound()
    self._edge_handles = ToolLineHandles(self.ax, positions, ...)
```

`ax.get_xbound()` / `ax.get_ybound()` return the current view interval
`(lower, upper)` along x / y. Placing the markers at the existing view bounds
leaves the view undisturbed, so `ax.get_xbound()`/`ax.get_ybound()` are unchanged
by setting up the selector (exactly what the F2P test asserts).

### F2P observation

`test_span_selector_bound[horizontal|vertical]` builds a `SpanSelector(ax, print,
direction, interactive=True)` and asserts:

- `ax.get_xbound() == x_bound` and `ax.get_ybound() == y_bound` (the view is NOT
  disturbed by creating the selector), and
- `tool._edge_handles.positions == list(bound)` where `bound = x_bound` if
  horizontal else `y_bound` — i.e. the initial marker positions equal the axis'
  view bounds along the selection direction (was the degenerate `[0, 0]`).

The modeled value is precisely the pair of initial marker positions
(`= _edge_handles.positions`, by the identity pass-through above).

## Lean modeling

- `SelectDirection` — `self.direction`: `.horizontal ↔ "horizontal"`,
  `.vertical ↔ "vertical"` (`_api.check_in_list` restricts it to these two).
- `MarkerSetup` carries the four inputs the choice reads:
  `axis : SelectDirection` (= `self.direction`),
  `selectorSpan : ℚ × ℚ` (= `self.extents`, the degenerate `(0,0)` at init —
  used only by the pre-patch buggy skeleton),
  `xViewBounds : ℚ × ℚ` (= `ax.get_xbound()`),
  `yViewBounds : ℚ × ℚ` (= `ax.get_ybound()`).
- Coordinates are floats but the fix is a pure *selection* between two existing
  coordinate pairs (no arithmetic on the values), so they are modeled with the
  exact ordered field `ℚ` (SPEC_GUIDE §2: value-level float, model exactly so
  equality is decidable; no `Float` order is consulted).
- `initialMarkers inp` is the post-patch selection: `xViewBounds` if horizontal
  else `yViewBounds`. The result `ℚ × ℚ` is the pair of initial marker positions
  (`= _edge_handles.positions`). The pre-patch impl returns `selectorSpan`
  unconditionally (the bug: `positions = self.extents`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.direction` (`"horizontal"`/`"vertical"`) | `SelectDirection` | `"horizontal" ↔ .horizontal`, `"vertical" ↔ .vertical` |
| `self.extents` (`(vmin, vmax)`) | `selectorSpan : ℚ × ℚ` | float pair ↔ exact `ℚ` pair (identity on values) |
| `ax.get_xbound()` (`(lo, hi)`) | `xViewBounds : ℚ × ℚ` | float pair ↔ exact `ℚ` pair |
| `ax.get_ybound()` (`(lo, hi)`) | `yViewBounds : ℚ × ℚ` | float pair ↔ exact `ℚ` pair |
| `positions` passed to `ToolLineHandles` == `_edge_handles.positions` | `result : ℚ × ℚ` | the ordered pair of initial marker positions |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behavior the patch changes —
  *which* coordinate pair becomes the initial marker positions — is modeled
  DEEPLY as a pure selection on `self.direction`. SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed decision, so the `axioms` region is empty
  and **G-AX skips**.
- `ToolLineHandles(ax, positions, ...)` and its `.positions` read-back are an
  UNCHANGED identity pass-through (`ToolLineHandles(ax, p, ...).positions ==
  list(p)`); the modeled result IS that `positions` argument, so the pass-through
  is an **I** (identical) refinement, not an axiom. It constrains no output
  component the spec leaves free.
- `ax.get_xbound()` / `ax.get_ybound()` are UNCHANGED accessors that simply
  return the current view interval; their values enter the model as the grounded
  inputs `xViewBounds` / `yViewBounds` (carried observations), not re-derived.
- **Flag dependency:** the selection is governed entirely by `self.direction`;
  G-CONF fuzzes both `"horizontal"` and `"vertical"`. `_setup_edge_handle` is
  only reached when `interactive=True` (the configuration the F2P tests use).

## G-CONF fuzz seed

Pinned LCG seed: **20676** (see `conformance_check.py` `SEED`). Corpus: random
`MarkerSetup`s with `axis` uniform over `{horizontal, vertical}` and independent
random `selectorSpan` / `xViewBounds` / `yViewBounds` integer-valued `ℚ` pairs,
over ≥1e5 fuzzed inputs, plus hand-picked edge cases reproducing the F2P scenario
(`selectorSpan = (0,0)`, view bounds away from `0`, each direction). The R/I
shadow of `implementation_initialMarkers` is diffed against an in-process replica
of the POST-PATCH selection.
