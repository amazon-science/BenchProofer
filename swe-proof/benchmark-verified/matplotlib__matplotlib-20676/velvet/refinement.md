# refinement.md — matplotlib__matplotlib-20676

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `initialMarkerPositions` `do` block) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee —
A-consumed or A-reference), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the observable the F2P test checks, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The boundary-marker setup site — `SpanSelector._setup_edge_handle` (`lib/matplotlib/widgets.py:2158`)

Gold hunk:
```
-        self._edge_handles = ToolLineHandles(self.ax, self.extents,
+        # Define initial position using the axis bounds to keep the same bounds
+        if self.direction == 'horizontal':
+            positions = self.ax.get_xbound()
+        else:
+            positions = self.ax.get_ybound()
+        self._edge_handles = ToolLineHandles(self.ax, positions,
                                              direction=self.direction,
                                              line_props=props,
                                              useblit=self.useblit)
```

| # | Solution.lean impl op (`initialMarkerPositions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `o : Orientation` | `self.direction` read | R | `{'horizontal','vertical'}` string ↔ `Orientation` (mapping.md §2). `direction.setter` guarantees the string is one of exactly the two values. |
| A2 | parameter `horizontalLimits : Rat × Rat` | `self.ax.get_xbound()` | R | order-preserving `(lower, upper)` float pair ↔ `Rat × Rat` (mapping.md §2). G-CONF feeds the real `get_xbound()` output into the shadow. |
| A3 | parameter `verticalLimits : Rat × Rat` | `self.ax.get_ybound()` | R | as A2, vertical axis. |
| A4 | parameter `currentSpan : Rat × Rat` (read-only, unused) | `self.extents` — present **only** in the pre-patch expression `ToolLineHandles(self.ax, self.extents, ...)` | R | the span pair ↔ `Rat × Rat`. The gold patch *removes* `self.extents` from this site; the spec models it as an explicit read-only input the result must not depend on (directive 5 frame: the postcondition pins `out` to the axis limits alone, so any impl that lets `currentSpan` leak in fails to verify). |
| A5 | `match o with .horizontal => horizontalLimits ; .vertical => verticalLimits` | `if self.direction == 'horizontal': positions = get_xbound() else: positions = get_ybound()` | I | the orientation dispatch is the concrete control flow of the fix, transliterated 1:1 (Lean `match` ↔ the Python `if/else`); G-CONF refutes any divergence. |
| A6 | `return positions` (`Rat × Rat`) consumed as the result | `positions` passed as `ToolLineHandles(self.ax, positions, ...)` first arg; observed via `_edge_handles.positions` | R + I | the handle container is created at exactly `positions` and `.positions` returns them verbatim (mapping.md §2, §3.2); identity on the pair. The construction call (`direction`, `line_props`, `useblit` args) is **unchanged** by the patch and outside the modeled slice. |

Discriminating content of the change — the initial marker positions are the
**orientation-matched axis bounds**, NOT the (degenerate) current selection span
`self.extents` — lives in the postcondition `out = initialMarkerSpec o
horizontalLimits verticalLimits`. The pre-patch passed `self.extents` (which is
`(0, 0)` at construction, dragging the axis view to include 0);
`Solution_prepatch.lean` reproduces that (`positions := currentSpan`) and
**fails** the postcondition (G-DIFF): `currentSpan = initialMarkerSpec o hl vl`
is unprovable.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real marker-placement choice is a straight-line pure
computation — an orientation dispatch over two already-computed limit pairs —
that always terminates and returns, and the F2P test observes its return value
(`tool._edge_handles.positions`), so total correctness is the faithful
semantics. Partial correctness would admit a same-spec implementation that
diverges (an infinite loop vacuously satisfies every `ensures`) — a wrong impl
the tests would fail — so it would leave the spec too weak.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the choice of
the first positional argument to `ToolLineHandles`, from `self.extents` to the
orientation-matched axis bounds — is the impl's `match` (step A5), a concrete
transliterated op, not hidden behind an axiom. There are **no consumed axioms
and no deep-model A-references**: the unchanged callees (`get_xbound`,
`get_ybound`, `ToolLineHandles`) are pure value sources / a consumer whose real
behaviour is exercised live by G-CONF (mapping.md §3).

## C. verify(Solution) ⇒ resolved

`initialMarkerPositions` verifies only if its output equals the orientation-
matched axis-bound pair (A5) and is independent of `currentSpan` (A4 frame). By R
(`direction ↔ Orientation`, `get_*bound() ↔ Rat × Rat`, identity of the
`ToolLineHandles` consumer) the verified op equals the gold patch's `positions`
choice; the F2P test `test_span_selector_bound` asserts exactly
`tool._edge_handles.positions == list(bound)` for `bound = get_xbound()` /
`get_ybound()` by direction, and that `ax.get_xbound()/get_ybound()` are
unchanged by introducing the selector — both implied by A5/A6. By G-CONF the R/I
transliteration agrees with the real patched `SpanSelector` behaviour on ≥10⁵
sampled inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust (G-AX = skip).
