# mapping.md — matplotlib__matplotlib-24637

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a9ba9d5d3fe9d5ac15fbdb06127f97d381148dd0`, states the type
abstraction (the Lean↔Python bijection used by G-CONF), and records callee
provenance.

Repo file under change: `lib/matplotlib/offsetbox.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `groupedRender (gid : Option String) (children : List RenderCmd) : List RenderCmd` | `AnnotationBbox.draw(self, renderer)` — `lib/matplotlib/offsetbox.py:1449` (body after the visibility/placement guard, lines 1455–1462) | the modeled changed function: it produces the ordered stream of drawing commands the composite hands to the rendering back end |
| `gid` parameter | `self.get_gid()` (the artist's own identifier; `lib/matplotlib/artist.py:618`) — passed as `gid=...` to `renderer.open_group` | the composite artist's identifier (`None` when unset) |
| `children` parameter | the in-order stream of drawing commands produced by the composite's sub-renderings: `self.update_positions(renderer)`, then `self.arrow_patch.draw(renderer)` (if present), `self.patch.draw(renderer)`, `self.offsetbox.draw(renderer)` (lines 1455–1461) | the contained drawing, as the command stream it emits |
| `out` (the result `List RenderCmd`) | the ordered sequence of back-end commands the renderer receives during `AnnotationBbox.draw`: `renderer.open_group(self.__class__.__name__, gid=self.get_gid())`, then the children's commands, then `renderer.close_group(self.__class__.__name__)` | the command stream actually handed to the back end |
| `RenderCmd.beginGroup gid` | one `renderer.open_group(s, gid=...)` call (`lib/matplotlib/backend_bases.py:179`; SVG impl `backends/backend_svg.py:663` emits `<g id="gid">`) | open an enclosing grouping element tagged with `gid` |
| `RenderCmd.endGroup` | one `renderer.close_group(s)` call (`backend_bases.py:186`; SVG `backend_svg.py:671` emits `</g>`) | close the grouping element opened most recently |
| `RenderCmd.child tag` | one drawing primitive a contained sub-artist hands to the renderer (`draw_path` / `draw_image` / `draw_text` / …) | a single child drawing command |

The change is the pair of commands that newly bracket the composite's body:

```
+ renderer.open_group(self.__class__.__name__, gid=self.get_gid())   # before children
  ... self.arrow_patch.draw / self.patch.draw / self.offsetbox.draw ...
+ renderer.close_group(self.__class__.__name__)                      # after children
```

Pre-patch the body emits only the children's commands; the identifier never
reaches the back end (the SVG `<g>` element is never opened with it).

## 2. Type abstraction (R-refinements) — the Lean ↔ Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ordered stream of back-end commands during `draw` | `out : List RenderCmd` | list order ↔ call order; the first command ↔ `out.head?`, the last ↔ `out.getLast?` |
| `renderer.open_group(s, gid=g)` | `RenderCmd.beginGroup g` | the only observable that matters for the issue is the `gid` argument carried to `open_group` — the SVG back end writes `<g id="{gid}">` iff `gid` is truthy. The grouping *label* `s` (`self.__class__.__name__`) is a constant that does not affect the tested behaviour and is abstracted away. `gid` is `Option String`: `None`/`""` (falsy) ↔ no identifier on the group, a non-empty string ↔ that identifier on the group. |
| `renderer.close_group(s)` | `RenderCmd.endGroup` | the matching close of the most-recently opened group; `s` abstracted as above |
| a child sub-artist's drawing command | `RenderCmd.child tag` | the concrete primitive and its arguments are opaque to the tested behaviour (the issue is solely about the enclosing group carrying the gid); only the child's *presence and position* in the stream are modeled. The `tag : Nat` is an abstract identity placeholder, never inspected by the spec. |

G-CONF (`conformance_check.py`) drives the real gold-patched `AnnotationBbox.draw`
against a recording renderer, captures the actual `(open/close/child)` event
stream, and checks it against the model bracket: first command is
`open_group(gid=self.get_gid())`, last is the matching `close_group`, the outer
group encloses the whole body (depth returns to 0 only at the final close), and
real child draw commands occur inside. Fuzz seed: **24637**.

## 3. Callee provenance

None consumed as an axiom. The change is the insertion of two grouping commands
around the composite's existing body; the model spells those commands out
directly (`beginGroup`/`endGroup`) and reproduces the children's stream verbatim.

`renderer.open_group` / `renderer.close_group` (`backend_bases.py:179,186`,
SVG override `backend_svg.py:663,671`) are **unchanged** by the patch — the patch
only *calls* them. They are back-end command sinks, not part of the modeled
construction: in the model their effect IS the emitted `beginGroup`/`endGroup`
command, exactly the observable the issue is about (the SVG `<g id=...>` wrapper).
The contained sub-renderings (`update_positions`, `arrow_patch.draw`,
`patch.draw`, `offsetbox.draw`) are likewise unchanged; the patch neither adds,
removes, nor reorders them, so they are modeled as an opaque `children` stream
carried through verbatim.

Consequently there is **no axiom** and **no A-reference deep model** — and
therefore **no `axiom_check.py`** for this bundle (nothing for G-AX to execute
against a real callee). The single trust point is refinement fidelity
(refinement.md, G-EQ), mechanically re-checked by G-CONF against the real
patched `draw` (G-RESOLVE is the end-to-end correctness oracle).
