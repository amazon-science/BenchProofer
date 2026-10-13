# mapping.md — matplotlib__matplotlib-26291

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fa68f46289adf4a8a4bc7ba97ded8258ec9d079c`, states the type
abstraction, and gives the provenance of the lone axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `lib/mpl_toolkits/axes_grid1/inset_locator.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `call(self, ax, renderer)` | `AnchoredLocatorBase.__call__(self, ax, renderer)` — `lib/mpl_toolkits/axes_grid1/inset_locator.py:71` | the modeled changed function (the inset-position callable) |
| `Locator` | `AnchoredLocatorBase` (and its subclasses `AnchoredSizeLocator`, `AnchoredZoomLocator`) — `inset_locator.py:60,80,106` | the object the callable lives on |
| `measure(self, context)` | the window-extent + offset measurement performed inside `__call__`: `bbox = self.get_window_extent(renderer)` then `self.get_offset(bbox.width, bbox.height, 0, 0, renderer)` — `inset_locator.py:73-74` | the measurement that consumes the drawing context; modeled deeply (the `measurements`/`measured_with` observables), NOT axiomatized |
| `axes_context(ax)` *(axiom — A-consumed)* | `ax.figure._get_renderer()` — the renderer obtained from the host axes' figure; `Figure._get_renderer` at `lib/matplotlib/figure.py:2731` (delegates to `backend_bases._get_renderer`) | unchanged callee the patch uses to obtain a renderer when none was supplied |
| `renderer: Optional[int]` | the `renderer` argument of `__call__` (`None` = no renderer supplied) | the optional drawing context |
| `ax: int` | the host axes argument of `__call__` | the host axes (only its figure-renderer capability is observed) |

The pre-patch behaviour the change repairs (for the refinement audit, not
referenced from the consumer spec view): with no `renderer`, the old `__call__`
passed `renderer=None` straight into `self.get_window_extent(None)`
(`offsetbox.py:395-398`), whose fallback `renderer = self.figure._get_renderer()`
dereferences the locator's OWN figure — which is `None` for these locators (they
are never added as artists to a figure), raising
`AttributeError: 'NoneType' object has no attribute '_get_renderer'`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a renderer object / `None` (the `renderer` arg) | `Optional[int]` — `None` ↔ absent; a present renderer ↔ a positive opaque handle | only present-vs-absent and the *identity* of the threaded renderer are observed; the handle's numeric value stands for the renderer object's identity |
| a renderer object handed to the measurement | `int > 0` (the `context` param of `measure`); the `0`/absent sentinel models "no usable context" | a present renderer ↔ a positive handle; "measurement attempted without a usable context" ↔ handle `0`, which the measurement's `Requires(context > 0)` rejects (mirrors the real measurement being unreachable without a renderer) |
| the host axes object (`ax`) | `int` (an opaque axes code) | only `ax.figure._get_renderer()` is observed, modeled by `axes_context(ax)` |
| `bbox = get_window_extent(r)` then `get_offset(..., r)` — one measurement against the renderer `r` | one `measure(self, r)` call (one `+1` to `measurements`, recording `r` in `measured_with`) | the measurement's *occurrence against a present context* is the load-bearing observable; the returned `TransformedBbox` is not observed numerically by the F2P test (it only requires the save to succeed) |
| `self.axes = ax` assignment (`inset_locator.py:72`) | omitted | a book-keeping field set the F2P test never observes; orthogonal to the renderer-resolution fix |

`measured_with`/`measurements` are auxiliary observables (not repo fields): they
make "the measurement runs exactly once, against a present context equal to the
resolved renderer" statable and checkable. They are the analog of the
lookup/verification counters in the django__django-11451 exemplar.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `axes_context` ↔ `ax.figure._get_renderer()` (A-consumed)
**Callee:** the renderer obtained from the host axes' figure. In the gold patch:
`renderer = ax.figure._get_renderer()`. `Axes.figure` is always a real
`Figure` (an axes belongs to a figure), and `Figure._get_renderer`
(`lib/matplotlib/figure.py:2731`) returns a real renderer object via
`matplotlib.backend_bases._get_renderer(self)` — never `None`.

**Axiom (weakest sufficient contract):** `axes_context(ax)` Ensures
`Result() > 0`, i.e. the host axes always produces a PRESENT (non-absent)
drawing context. This is the only property the proof needs: the resolved
renderer is present, so the measurement's `Requires(context > 0)` is satisfied
on the no-renderer path. The axiom says nothing about the renderer's internal
state beyond presence — it is not the full renderer contract, only "a usable
context exists."

**Soundness check (G-AX):** `axiom_check.py` constructs real axes in several
shapes (a plain axes, multi-subplot axes, the regression's own
`inset_axes` scenario, and figures of varying size/dpi), calls the real
`ax.figure._get_renderer()` for each, and asserts the returned object is present
(not `None`) and usable (`hasattr(renderer, "points_to_pixels")` — the
point-to-pixel scale the downstream offset measurement requires). The check
asserts ONLY the axiom's property over the UNCHANGED callee; it deliberately does
NOT run the end-to-end tight-bbox `savefig`, because that path exercises the
unpatched bug and raises at `base_commit` — so the checker runs RC=0
pre-patch (the soundness of the axiom is independent of whether the fix is
applied). It imports only `matplotlib` (the package the patch lives in) and
forces the Agg backend for headless execution. Exit 0 iff sound (verified over
10 witnesses).

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow) against
the real patched `AnchoredLocatorBase.__call__` (oracle) in-container over
>= 1e5 Requires-satisfying inputs (boundary scenario grid + fuzz). Pinned fuzz
seed: **26291**. The bridge follows §2: renderer/axes objects <-> positive
opaque handles by identity; the observables compared are the measurement count
and the identity handle of the renderer the measurement consumed.
