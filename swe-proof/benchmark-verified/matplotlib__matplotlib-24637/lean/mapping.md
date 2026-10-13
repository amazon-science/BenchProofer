# mapping.md — matplotlib__matplotlib-24637

## Symbol binding (file:line @ base_commit a9ba9d5d3fe9d5ac15fbdb06127f97d381148dd0)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_drawAnnotationBbox` / `problem_spec_drawAnnotationBbox` / `correct_drawAnnotationBbox` | `AnnotationBbox.draw` (the renderer-operation trace it emits) | `lib/matplotlib/offsetbox.py:1448-1462` |
| `RenderOp` (pure helper) | one emitted renderer operation | the `renderer.open_group/close_group` calls + each child `.draw(renderer)` |
| `drawTrace` (pure helper) | the ordered sequence of operations `draw` pushes onto the renderer | `offsetbox.py:1448-1462` |

The modeled behavior is the SEQUENCE of renderer operations `AnnotationBbox.draw`
emits. It is the only behavior the patch changes and the only behavior the
FAIL_TO_PASS test observes:

- `test_backend_svg.py::test_annotationbbox_gid` builds an `AnnotationBbox` with
  an image, calls `ab.set_gid("a test for issue 20044")`, saves the figure to
  SVG, and asserts the string `'<g id="a test for issue 20044">'` appears in the
  output. That `<g id=...>` element is emitted by the SVG renderer's
  `open_group(..., gid=...)` — which `draw` only calls after the patch.

### What the function does (base_commit, pre-patch)

```python
def draw(self, renderer):
    # docstring inherited
    if renderer is not None:
        self._renderer = renderer
    if not self.get_visible() or not self._check_xy(renderer):
        return
    self.update_positions(renderer)
    if self.arrow_patch is not None:
        if self.arrow_patch.figure is None and self.figure is not None:
            self.arrow_patch.figure = self.figure
        self.arrow_patch.draw(renderer)
    self.patch.draw(renderer)
    self.offsetbox.draw(renderer)
    self.stale = False
```

The children's `.draw(renderer)` calls each push their own markers into the
renderer's output stream, but nothing wraps them in a group, so the artist's gid
(`self.get_gid()`) never reaches the output. The patch inserts
`renderer.open_group(self.__class__.__name__, gid=self.get_gid())` right after the
visibility/position guard and `renderer.close_group(self.__class__.__name__)`
right before `self.stale = False`, bracketing the part-draws with a gid-carrying
group.

### Lean modeling

- The observable result of `draw` is the ORDERED TRACE of renderer operations.
  `RenderOp` enumerates the operation kinds the trace can contain:
  `groupStart gname gid`, `groupEnd gname`, `drawArrow`, `drawPatch`,
  `drawOffsetbox`. Each child's full internal sub-trace is abstracted to one
  opaque marker because the fix concerns only the enclosing group, not the
  children's (unchanged) internal drawing.
- The decision inputs are the observable flags the method reads:
  `visible` (`self.get_visible()`), `posResolvable` (`self._check_xy(renderer)`),
  `hasArrow` (`self.arrow_patch is not None`), plus `clsName`
  (`self.__class__.__name__`) and `gid` (`self.get_gid()`, an `Option String`).
- `drawTrace` is the post-patch trace; the impl is the `Id.run do` skeleton
  mirroring the method body (guard → group-start → optional arrow → patch →
  offsetbox → group-end). The pre-patch impl omits the two group markers.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.get_visible()` | `visible : Bool` | identity |
| `self._check_xy(renderer)` (truthy) | `posResolvable : Bool` | identity |
| `self.arrow_patch is not None` | `hasArrow : Bool` | identity |
| `self.__class__.__name__` | `clsName : String` | identity |
| `self.get_gid()` (str or None) | `gid : Option String` | `None ↔ none`, `s ↔ some s` |
| `renderer.open_group(name, gid=g)` | `RenderOp.groupStart name g` | identity |
| `renderer.close_group(name)` | `RenderOp.groupEnd name` | identity |
| `self.arrow_patch.draw(renderer)` (its sub-trace) | `RenderOp.drawArrow` | abstraction (whole child sub-trace ↔ one marker) |
| `self.patch.draw(renderer)` (its sub-trace) | `RenderOp.drawPatch` | abstraction |
| `self.offsetbox.draw(renderer)` (its sub-trace) | `RenderOp.drawOffsetbox` | abstraction |
| the ordered list of emitted ops | `result : List RenderOp` | order-preserving |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — emitting a
  gid-carrying group around the part-draws — is modeled DEEPLY and structurally as
  the ordered trace; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
  behavior. So the `axioms` region is empty and **G-AX skips**.
- `update_positions(renderer)` repositions the box and emits no renderer drawing
  op; it is unchanged by the patch and contributes no trace marker.
- The children's `.draw(renderer)` (`arrow_patch`, `patch`, `offsetbox`) are
  UNCHANGED by the patch; their internal sub-traces are orthogonal to the fix and
  abstracted to single markers whose presence and relative order are pinned.
- `open_group` / `close_group` are renderer methods that, for the SVG backend,
  emit `<g id="...">` / `</g>`; their gid-carrying behavior is the abstract
  `groupStart gname gid` / `groupEnd gname` markers. No flag dependency beyond
  the visibility/position guard.

## G-CONF fuzz seed

Pinned LCG seed: **24637** (see `conformance_check.py` `SEED`). Corpus: randomized
`(visible, posResolvable, hasArrow, clsName, gid)` tuples crossing every branch —
not-drawn (either guard false), drawn-with/without-arrow, gid present vs `None` —
over ≥1e5 fuzzed inputs. The R/I shadow of `implementation_drawAnnotationBbox` is
diffed against an in-process replica of the POST-PATCH trace. Hand-picked edge
cases pin the discriminating ops: a visible, position-resolvable artist with a gid
emits `groupStart clsName (some gid)` first and `groupEnd clsName` last.
