# mapping.md — matplotlib__matplotlib-26291

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fa68f46289adf4a8a4bc7ba97ded8258ec9d079c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change:
`lib/mpl_toolkits/axes_grid1/inset_locator.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `computePlacement (ctx : Option Ctx) (host : Host)` | the placement callable `AnchoredLocatorBase.__call__(self, ax, renderer)` — `lib/mpl_toolkits/axes_grid1/inset_locator.py:71` | the modeled changed function (computes the placement region of an anchored child given an optional drawing context) |
| `ctx : Option Ctx` | the `renderer` argument of `__call__` (`inset_locator.py:71`); `None` when the caller has no live drawing context (e.g. `_tight_bbox.adjust_bbox` calls `locator(ax, None)`, `lib/matplotlib/_tight_bbox.py:28`) | the optional drawing context |
| `host : Host` | the `ax` argument of `__call__` (`inset_locator.py:71`) — the parent axes, which always carries a figure | the host axes the child is placed against |
| `hostContext : Host → Ctx` *(opaque axiom — A-consumed)* | `ax.figure._get_renderer()` (the patched line `inset_locator.py:73`; `_get_renderer` def in `lib/matplotlib/figure.py`) | the host figure's drawing context |
| `placeWith : Ctx → Host → Region` *(opaque axiom — A-consumed)* | the unchanged placement pipeline of `__call__` given a concrete context: `self.get_window_extent(renderer)` → `self.get_offset(...)` → `Bbox.from_bounds(...)` → `ax.figure.transSubfigure.inverted()` → `TransformedBbox(...)` (`inset_locator.py:73-77`) | the downstream region computation given a concrete context |
| the impl's context-substitution match (`some c ⇒ c | none ⇒ hostContext host`) + the `ctx = none` postcondition *(deep model — A-reference)* | the unchanged downstream as a function of the (optional) context: a concrete context yields a region; a *None* context fed to `self.get_window_extent(None)` on this figure-less artist raises `AttributeError` (`lib/matplotlib/offsetbox.py:398-399`, `self.figure` is `None` for the locator) | pure spec: the downstream's context-dependence, with the None branch a checked fact |
| `PlaceErr.noContext` | the `AttributeError: 'NoneType' object has no attribute '_get_renderer'` raised by the pre-patch when the context is absent (problem_statement traceback) | the one outcome a correct placement must never produce |

The locator artist (`AnchoredLocatorBase`, a subclass of `AnchoredOffsetbox`) is
attached to an axes via `set_axes_locator` and is **never added to a figure**, so
`self.figure is None`. That is why `get_window_extent(None)` — whose own guard is
`if renderer is None: renderer = self.figure._get_renderer()` — raises on this
artist: `None._get_renderer()`. The fix supplies a concrete context up front from
the *host axes'* figure (`ax.figure`), which is always present.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `renderer : RendererBase | None` | `ctx : Option Ctx` | a live renderer object `r ↔ some r`; `None ↔ none`. `Ctx` is opaque: the placement reacts only to present-vs-absent and to *which* concrete context reaches the downstream — never to a renderer's internal fields. |
| `ax : matplotlib.axes.Axes` | `host : Host` | opaque; the only observable used is its figure's drawing context (`ax.figure._get_renderer()`) and its participation in the downstream pipeline. |
| the returned `TransformedBbox` placement region | `Region` | opaque; equality of regions ↔ equality of `Bbox` extents (G-CONF compares the four bounds). |
| `ax.figure._get_renderer() : RendererBase` | `hostContext host : Ctx` | the real call ↔ the axiom value; total (a real axes always has a figure with a renderer). |
| the downstream region given a concrete renderer | `placeWith ctx host : Region` | the real pipeline output ↔ the axiom value; total and deterministic given `(renderer, ax)`. |
| the placement outcome | `Except PlaceErr Region` | a returned region `reg ↔ Except.ok reg`; the `AttributeError` raised by the unguarded pre-patch ↔ `Except.error PlaceErr.noContext`. The patched code never raises ⇒ always `Except.ok`. |

`ctx` distinguishes only present-vs-absent at the decision and threads the chosen
concrete context into `placeWith`; that is the entire observable surface, so
`Option Ctx` over an opaque `Ctx` is a faithful carrier.

## 3. Callee provenance, flag dependencies, A-tags

- `hostContext` ↔ `ax.figure._get_renderer()` — **A-consumed, opaque.** UNCHANGED
  callee (`matplotlib.figure.FigureBase._get_renderer`). Left fully opaque (no
  `ensures`); the only obligation is that it is a total `Host → Ctx` op. No flag
  dependency. (G-AX: witnessed total + deterministic on real axes.)
- `placeWith` ↔ the unchanged window-extent / offset / transform pipeline of
  `__call__` given a concrete renderer — **A-consumed, opaque.** UNCHANGED.
  Left fully opaque; obligation is total `Ctx → Host → Region`. (G-AX: witnessed
  total + deterministic given a concrete renderer.)
- the deep context-substitution model (the `none ⇒ hostContext host` fallback and
  the prepatch's `none ⇒ error` skeleton) — **A-reference.** Its
  `none`-branch encodes a CHECKED fact about the unchanged callee: feeding `None`
  to `get_window_extent` on the figure-less locator artist raises `AttributeError`.
  G-AX runs the real unpatched call with a `None` context and asserts it raises
  (the bug witness); and that the patched substitution makes it return a region.
- No callee under change is axiomatized. `__call__` (the function under spec) is
  modeled, not assumed; the renderer substitution is modeled deeply (the R/I
  leg), not hidden behind an axiom.

## 4. G-CONF fuzz seed

Pinned seed: **`26291`**. `N_FUZZ = 100_000` context configurations
(present-real-renderer vs absent / `None`) over a real `inset_axes`-created
locator, comparing the R/I substitution shadow against the patched `__call__`.
