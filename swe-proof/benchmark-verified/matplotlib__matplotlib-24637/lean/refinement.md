# refinement.md — matplotlib__matplotlib-24637

Operation-by-operation correspondence between `implementation_drawAnnotationBbox`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `AnnotationBbox.draw`
method body). Tags: **R** type refinement, **A-consumed** proof uses an axiom,
**A-reference** deep model validated == real callee, **I** identical concrete op.

The modeled artifact is the ORDERED TRACE of renderer operations that
`AnnotationBbox.draw` emits. The renderer is a side-effect sink; the observable
"result" of `draw` is the sequence of calls it makes on the renderer, in order.
The patch inserts an `open_group(class_name, gid=...)` before the part-draws and a
matching `close_group(class_name)` after them. Every part-draw (arrow, patch,
offsetbox) already pushes its own marker into the same output stream, so the gid
group encloses them.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if !visible \|\| !posResolvable then return []` | `if not self.get_visible() or not self._check_xy(renderer): return` (no ops emitted) | R |
| 2 | `trace := trace ++ [RenderOp.groupStart clsName gid]` | `renderer.open_group(self.__class__.__name__, gid=self.get_gid())` (the ADDED line) | R |
| 3 | (`update_positions`) `-- position resolution … emits no marker` | `self.update_positions(renderer)` — repositions, draws nothing | I (no-op in the trace) |
| 4 | `if hasArrow then trace := trace ++ [RenderOp.drawArrow]` | `if self.arrow_patch is not None: … self.arrow_patch.draw(renderer)` | R |
| 5 | `trace := trace ++ [RenderOp.drawPatch]` | `self.patch.draw(renderer)` | R |
| 6 | `trace := trace ++ [RenderOp.drawOffsetbox]` | `self.offsetbox.draw(renderer)` | R |
| 7 | `trace := trace ++ [RenderOp.groupEnd clsName]` | `renderer.close_group(self.__class__.__name__)` (the ADDED line) | R |
| — | `return trace` | `self.stale = False` (book-keeping; not an emitted op) | I |

Notes:

- **Every step is R or I — no A.** The drawing behavior is modeled DEEPLY as the
  ordered emitted trace over the artist's observable flags (`visible`,
  `posResolvable`, `hasArrow`), its class name and its optional gid. SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed behavior; the `axioms` region is
  empty and **G-AX skips**.
- The R tag on the part-draws (ops 4–6) is the *abstraction* refinement: each real
  `<child>.draw(renderer)` pushes its own marker(s) into the renderer's output
  stream; we abstract each child's whole sub-trace to a single opaque marker
  (`drawArrow` / `drawPatch` / `drawOffsetbox`) because the FIX only concerns the
  ENCLOSING group, not the children's internal drawing (which is unchanged). The
  children's relative ORDER and PRESENCE are pinned, which is all the fix touches.
- `self.arrow_patch.figure = self.figure` assignment inside the arrow branch is a
  field fixup that emits no renderer op; folded into the `hasArrow` guard (op 4).
- The **fix itself** is ops 2 and 7: emitting the group-start (carrying the gid)
  and the matching group-end around the part-draws. Their effect is captured by
  the presence of `groupStart clsName gid` … `groupEnd clsName` bracketing the
  trace, exactly mirroring the two added lines. The pre-patch impl
  (`Solution_prepatch.lean`) omits both markers, so the gid never enters the
  trace — the bug the issue reports.
- **Frame discipline (directive 5):** the spec pins the FULL ordered trace — every
  component (presence/absence of each marker AND their order) is constrained to
  `drawTrace …`. No output component is left free, so a wrong impl cannot drop the
  group markers (or reorder them) and still satisfy the spec.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the post-patch `draw` trace
  over ≥1e5 fuzzed inputs.
