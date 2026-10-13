# refinement.md — matplotlib__matplotlib-20676

Operation-by-operation correspondence between `implementation_initialMarkers`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`SpanSelector._setup_edge_handle` initial-position choice). Tags: **R** type
refinement, **A-consumed** proof uses an axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if inp.axis = .horizontal then pure inp.xViewBounds` | `if self.direction == 'horizontal': positions = self.ax.get_xbound()` | R |
| 2 | `else pure inp.yViewBounds` | `else: positions = self.ax.get_ybound()` | R |
| 3 | `return positions` (the bound pair becomes the result) | `self._edge_handles = ToolLineHandles(self.ax, positions, direction=..., line_props=props, useblit=...)` — `positions` is passed straight through and read back by `_edge_handles.positions` | I |

Notes:

- **Every step is R or I — no A.** The choice the patch changes (which coordinate
  pair becomes the initial marker positions) is modeled DEEPLY as a pure
  selection on `self.direction`; SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed decision. The `axioms` region is empty; **G-AX skips**.

- Ops 1–2 are the **fix itself**: choosing the axis' current view bounds along the
  selection direction. The R tag is the *carried-observation* refinement — the
  results of the UNCHANGED accessors `ax.get_xbound()` / `ax.get_ybound()` are
  carried as the grounded inputs `xViewBounds` / `yViewBounds` (exact-`ℚ` pairs)
  rather than re-derived. They are orthogonal to the fix and constrain no output
  component the spec leaves free: `result` is fully pinned to a view-bound pair on
  each direction branch.

- Op 3 is the **I** pass-through. `ToolLineHandles(ax, positions, ...)` draws one
  line per coordinate (`axvline`/`axhline`) and its `.positions` property reads
  each line's data back, so `ToolLineHandles(ax, p, ...).positions == list(p)`
  (identity). The modeled result IS that `positions` argument
  (`= _edge_handles.positions`), so the container is an identical concrete op, not
  an axiom. It is UNCHANGED by the patch.

- The **bug** is in op 1/2: pre-patch, `positions = self.extents` — the selector's
  own span — unconditionally. The pre-patch impl (`Solution_prepatch.lean`)
  re-introduces this as `pure inp.selectorSpan`, behaviourally identical to
  `positions = self.extents`. At setup the span is the degenerate `(0, 0)`, so the
  markers land at `0` and the axis view is forced to include `0` — the reported
  bug. The discriminating clause the spec pins: on each direction branch the
  result must equal the corresponding view bound, which `selectorSpan` does not
  satisfy in general (G-DIFF: prepatch unclosable; G-CONF: shadow disagrees).

- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the POST-PATCH selection
  over ≥1e5 fuzzed inputs.
