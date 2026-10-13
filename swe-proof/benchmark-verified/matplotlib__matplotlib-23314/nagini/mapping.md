# mapping.md — matplotlib__matplotlib-23314

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 97fc1154992f64cfb2f86321155a7404efeb2d8a`, states the type
abstraction, and documents callee provenance.

Repo file under change: `lib/mpl_toolkits/mplot3d/axes3d.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render(self, sink)` | `Axes3D.draw(self, renderer)` — `lib/mpl_toolkits/mplot3d/axes3d.py:389` | the modeled changed function (the 3D axes render entry point) |
| `self: Container` | the `Axes3D` instance (the renderable container) | object whose visibility flag gates the pass |
| `self.visible` | `self.get_visible()` — accessor `Artist.get_visible` at `lib/matplotlib/artist.py:809`, returning the `self._visible` flag set by `set_visible` (`artist.py:1016`) | the boolean visibility flag the new guard reads |
| `self.content` | the entire body of `Axes3D.draw` after the new guard (`self._unstale_viewLim()`; `self.patch.draw(renderer)`; aspect/projection setup; the collections/patches `do_3d_projection` loop; the axis pane/axis draws; `super().draw(renderer)`) — `axes3d.py:390-444` | the total drawable work the pass delivers to the renderer when it runs |
| `sink: Sink` | the `renderer` argument and the artists/state it is driven to draw | the output sink that accumulates rendering work |
| `sink.work` | the cumulative rendering effect on the `renderer` (artists drawn / draw-commands emitted) | the observable amount of work performed |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Axes3D` instance | `Container` with only the two read fields | `self.get_visible()` ↔ `self.visible` (bool); the post-guard render body ↔ the opaque non-negative quantity `self.content` (the count of drawable artists / amount of work the body would deliver). The full body is unchanged by the patch, so it is abstracted as a single quantity. |
| `renderer` (the rendering backend the draw drives) | `Sink` with only `work` | the cumulative effect on the renderer (artists drawn, commands emitted) ↔ the running tally `sink.work`. A "rendered nothing" pass leaves `sink.work` unchanged; a full pass adds `self.content`. |
| early `return` of the render entry point | `if not self.visible: return` | identical control flow (kind I) |
| boolean test `not self.get_visible()` | `not self.visible` | identical boolean operation under the accessor bijection (kind I) |

`content >= 0` is an invariant of the abstraction: a render body never delivers
negative work. It is the minimal arithmetic fact the discriminating clauses
need (so the visible/invisible cases are distinguishable exactly when there is
something to draw, `content > 0`).

## 3. Callee provenance

There is **no consumed `@ContractOnly` axiom** in this bundle and **no opaque
library callee** to fuzz. The only function the new code calls is the unchanged
accessor `get_visible()`, which is modeled directly as the boolean field read
`self.visible` (kind I, §2) — it is fully expressible, not axiomatized. The
render body is abstracted as the opaque quantity `self.content` (kind R) rather
than spelled out, because the patch does not change it.

`axiom_check.py` (G-AX) therefore validates the two behavioral facts the
refinement leans on, by executing the REAL matplotlib code in-container:

  (a) **Accessor faithfulness** — `Artist.get_visible()` returns exactly the
      stored visibility flag (so `set_visible(False)` ⇒ `get_visible()` is
      `False`); i.e. the modeled boolean read `self.visible` == the real
      `self.get_visible()`. Source: `lib/matplotlib/artist.py:809-811`
      (`def get_visible(self): return self._visible`) and `:1016`
      (`set_visible` sets `self._visible = b`).

  (b) **Guard semantics reference** — an `Axes3D` flagged not-visible draws
      nothing, while a visible one drives the renderer; and this matches the
      sibling 2D path `matplotlib.axes._base._AxesBase.draw`, which has carried
      exactly this `if not self.get_visible(): return` guard
      (`lib/matplotlib/axes/_base.py:3022-3023`). The check renders an invisible
      vs. a visible 3D axes onto a recording backend and asserts the invisible
      one emits no draw calls (sink unchanged) while the visible one does — the
      `content==0 vs content>0` discrimination of clauses (1)/(2). This is the
      behavioral reference the deep model is validated against (an
      **A-reference** in the sense of SPEC_GUIDE §3), not a consumed axiom.

Imports nothing exotic: `matplotlib` (the package under test, driven through
its public `Agg`/recording API) is exactly what the gold patch lives in. Exit 0
iff every obligation holds.
