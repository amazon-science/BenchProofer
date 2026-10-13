# mapping.md — matplotlib__matplotlib-26291

## Symbol binding (file:line @ base_commit fa68f46289adf4a8a4bc7ba97ded8258ec9d079c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_resolveRenderContext` / `problem_spec_resolveRenderContext` | `mpl_toolkits.axes_grid1.inset_locator.AnchoredLocatorBase.__call__` (the added `if renderer is None: renderer = ax.figure._get_renderer()` guard at the head of the method, and the renderer each of the method's two downstream calls then receives) | `lib/mpl_toolkits/axes_grid1/inset_locator.py:71-77` (added lines after `:71`) |
| `RenderContext` (opaque) | the type of the `renderer` value flowing through `__call__` — a drawing/measurement context object (a `RendererBase`) | `lib/mpl_toolkits/axes_grid1/inset_locator.py:71` (`renderer` parameter) |

The single modeled function is the locator-call method whose behavior the gold
patch changes and that the FAIL_TO_PASS test (`test_inset_axes_tight`) exercises.
That test creates an inset axes and saves the figure with `bbox_inches="tight"`;
the tight-bbox machinery calls the axes locator with `renderer=None`
(`matplotlib/_tight_bbox.py:28`, `locator(ax, None)`), which pre-fix propagated
`None` into the downstream `get_window_extent` / `get_offset` calls and raised
`AttributeError: 'NoneType' object has no attribute '_get_renderer'`.

### What the method does (base_commit, pre-fix)

```python
def __call__(self, ax, renderer):
    self.axes = ax
    bbox = self.get_window_extent(renderer)              # uses renderer
    px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)  # uses renderer
    bbox_canvas = Bbox.from_bounds(px, py, bbox.width, bbox.height)
    tr = ax.figure.transSubfigure.inverted()
    return TransformedBbox(bbox_canvas, tr)
```

When the caller passes `renderer=None`, `None` flows unchanged into
`get_window_extent` / `get_offset`, and the downstream `OffsetBox.get_window_extent`
tries `self.figure._get_renderer()` on an object whose `figure` is `None` — the
reported crash. The method NEVER resolves a concrete renderer of its own.

Post-fix the method resolves a renderer first:

```python
def __call__(self, ax, renderer):
    if renderer is None:
        renderer = ax.figure._get_renderer()   # added: resolve from the axes' figure
    self.axes = ax
    bbox = self.get_window_extent(renderer)
    px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)
    ...
```

`ax.figure` is the axes' (host region's) figure (drawing surface), which always
supplies a renderer via `_get_renderer()` (`lib/matplotlib/figure.py:2731`).

#### TWO renderer consumers — both modeled (audit repair)

The guard rebinds the method's own `renderer` PARAMETER, so the resolved renderer
reaches BOTH downstream consumers — `get_window_extent(renderer)` and
`get_offset(..., renderer)` — and, in the post-patch source, those two call
arguments plus the `renderer is None` test are the ONLY reads of `renderer` in the
method (checked mechanically from the method's own AST by
`conformance_check.py::_capture_is_complete`, so a future third consumer cannot
slip outside the model unnoticed).

Both consumers are therefore part of the modeled observable, and the modeled
result is the PAIR of renderers they receive. This is load-bearing rather than
decorative: an earlier revision of this bundle modeled a single resolved renderer,
bound to "the value `renderer` holds when `get_window_extent` is called", and a
submitted rival that resolved a renderer for the extent call while passing the
caller's raw `None` on to `get_offset` VERIFIED against that model — yet its patch
does not repair the instance, because `AnchoredOffsetbox.get_offset` then
dereferences the `None` itself (`renderer.points_to_pixels(...)`) and
`test_inset_axes_tight` still fails. Modeling only the first consumer was the
defect; the pair is the faithful observable.

### `RenderContext` / `Option RenderContext` ↔ Python bijection

| Lean | Python | notes |
|---|---|---|
| `RenderContext` (opaque type) | a renderer object (`matplotlib.backend_bases.RendererBase`) — a drawing/measurement context | only WHICH context each step is handed matters here; its internal structure is irrelevant, so it is modeled as an opaque type. |
| `none : Option RenderContext` | the `renderer` argument is `None` | the caller supplied nothing (the tight-bbox path: `locator(ax, None)`). |
| `some r : Option RenderContext` | the `renderer` argument is a concrete renderer `r` | the caller supplied a renderer (the normal draw path). |
| `surfaceContext : RenderContext` | `ax.figure._get_renderer()` | the always-available context from the host's drawing surface. |

### Input/output bijection (used by G-CONF)

| Lean | Python meaning |
|---|---|
| `suppliedContext : Option RenderContext` | the `renderer` argument to `__call__` (`None` ↔ `none`, a concrete renderer ↔ `some _`). |
| `surfaceContext : RenderContext` | `ax.figure._get_renderer()`, the renderer the axes' figure furnishes. |
| `result : Option RenderContext × Option RenderContext` | the ordered pair of renderers the method's two downstream steps are handed, in the order the method reaches them (both always present post-fix). |
| `result.1` | the renderer passed to `self.get_window_extent(...)` — the EXTENT step (`inset_locator.py:74` post-fix). |
| `result.2` | the renderer passed to `self.get_offset(...)` — the PLACEMENT step (`inset_locator.py:75` post-fix). |

## Callee provenance + flag dependencies

- **No consumed callee axiom, no deep-model reference callee.** The behavior the
  patch changes — choosing which renderer flows into each downstream step — is
  modeled DEEPLY/structurally as an `Option`-fallback resolution
  (`suppliedContext`, else `surfaceContext`) shared by both steps. No opaque repo
  callee's contract is consumed by the proof; the surface's renderer is modeled as
  the plain input `surfaceContext` (a value, not a callee the proof reasons
  about), so `axiom_check.py` is a skip stub and G-AX skips. `RenderContext` is
  declared `opaque` only as the element type of the optional carrier / the surface
  value so the context can appear in the executable impl.
  - Note: `ax.figure._get_renderer()` is the source of `surfaceContext`. We do
    not axiomatize it; we treat its return as a given present value
    (`surfaceContext : RenderContext`, not `Option`), reflecting that the axes'
    figure always furnishes a renderer. The fix's contract — never hand a
    downstream step a `None` renderer — does not depend on any property of that
    renderer beyond its being present.
  - The two downstream consumers are likewise NOT axiomatized: nothing about what
    `get_window_extent` or `get_offset` compute is modeled or assumed. Only the
    identity of the renderer each is handed is observed, which is exactly the
    dataflow the patch changes.
- **No flag dependencies.** The guard fires solely on `renderer is None`; there
  is no configuration flag gating which context is chosen.

## G-CONF fuzz seed

Pinned LCG seed: **26291** (see `conformance_check.py` `SEED`). Corpus: the full
optional-context domain (`None`, and a family of distinct concrete renderers)
crossed against an in-process replica of the post-patch resolution, plus ≥1e5
fuzzed inputs, diffed by identity against the R/I shadow (each step receives
`suppliedContext` if present else `surfaceContext`).

The real method is driven to COMPLETION with both `get_window_extent` and
`get_offset` intercepted by capture-and-continue stubs, so the renderer reaching
EACH step is recorded and the observed pair is compared to the shadow's pair
componentwise, by identity. (The earlier revision raised out of the first
interception and so could only ever see the first component — the blind spot the
audit repair above closes. Measured in both directions: 0 disagreements against
the real gold-patched repo; disagreements on the second component against a repo
edit that resolves for the extent call only.)
