# refinement.md — matplotlib__matplotlib-20676

The operation-by-operation correspondence between `model.py`'s implementation
(the `selector_initial_coords` impl region, the deep `selected_bound` model, and
the `reported_positions` identity reference) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `SpanSelector._setup_edge_handle` (`widgets.py:2158`)

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

| # | model.py impl op (`selector_initial_coords`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `direction: int` (`0`/`1`) | `self.direction` (`'horizontal'`/`'vertical'`) | R | `_api.check_in_list(['horizontal','vertical'])` restricts the value to exactly two; modeled as the two-valued discriminant `0`/`1` (mapping.md §2). |
| A2 | parameters `x_bound`, `y_bound` (`Tuple[int,int]`) | `self.ax.get_xbound()`, `self.ax.get_ybound()` (2-tuples of `float`) | R | coordinate `float` ↔ `int` endpoint-wise; the tested behaviour is value selection/pass-through, precision-independent (mapping.md §2; §C below). |
| A3 | `if direction == HORIZONTAL: result = [x_bound[0], x_bound[1]] else: result = [y_bound[0], y_bound[1]]` (the directional selection of the orientation's bound, the deep model `selected_bound`) | `if self.direction == 'horizontal': positions = self.ax.get_xbound() else: positions = self.ax.get_ybound()` | I (control flow) + R (carrier) | the *changed* operation — choosing the orientation's current axis bound as the initial marker coordinates — is spelled out concretely. Same branch on the same discriminant; the chosen value is the 2-endpoint bound. This is what replaces the pre-patch `self.extents`. |
| A4 | `reported_positions(ToSeq(result))` (the reported marker positions, modeled as the identity on the supplied coordinates) | `ToolLineHandles(self.ax, positions, …)` and the observed `._edge_handles.positions` | A-reference | `ToolLineHandles` reports the supplied positions back unchanged (`axvline(p)`/`axhline(p)` → `get_xdata()[0]`/`get_ydata()[0]` == p; mapping.md §3.1). The deep model `reported_positions` is the identity; G-AX (axiom_check.py) validates `ToolLineHandles(ax, P, dir).positions == list(P)` against the real widget on boundary + fuzz. NOT a consumed axiom about the changed op — the changed op (which `P`) is modeled directly (A3). |

The discriminating content of the change — the marker coordinates come from the
orientation's **current axis bound** rather than the selector's degenerate
`(0, 0)` rectangle `extents` — lives in A3 (`Result()[0] == x_bound[0] ∧
Result()[1] == x_bound[1]` for horizontal; symmetric for vertical). The
pre-patch passed `self.extents`; `model_prepatch.py` reproduces that
(`result = [other_coords[0], other_coords[1]]`, the `other_coords`
parameter being the abstraction of `self.extents`) and **fails** the postcondition
`Implies(direction == HORIZONTAL, Result()[0] == x_bound[0] ∧ Result()[1] ==
x_bound[1])` — exactly the spec sensing the change (G-DIFF). The end-to-end
consequence (axes bounds unchanged) follows from `axvline(p)` setting
`scalex = (p < xmin) or (p > xmax)` against the current bound: when `p` is a
current bound endpoint, `scalex == False`, no expansion; when `p == 0` ∉
`(10, 20)`, `scalex == True`, the bug (mapping.md §3.1). The spec pins the
necessary and sufficient cause (positions == the current bound), so no
autoscale modeling is needed.

## B. Why the two observables are both covered by A3 + A4

The F2P `test_span_selector_bound` checks two things after constructing the
interactive selector:
1. `tool._edge_handles.positions == list(bound)` — pinned directly by A3/A4:
   the result equals the orientation's bound endpoints (A3), reported back
   unchanged (A4).
2. `ax.get_xbound()`/`get_ybound()` unchanged by construction — a *consequence*
   of (1): supplying the current bound endpoints to `axvline`/`axhline` yields
   `scalex/scaley == False`, so the view is not expanded. axiom_check.py
   reproduces this end-to-end against real Matplotlib (and shows the pre-patch
   `(0,0)` does expand it), confirming the spec's pinned cause is the tested
   effect.

## C. Precision-independence (the float → int refinement is faithful)

The widget never performs arithmetic, rounding, or magnitude comparison on the
selected coordinates inside the modeled behaviour — it *selects* a bound by
orientation and *passes the values through* the marker widget, then the test
compares the reported positions for equality with the original bound. Equality
is preserved by the injective `float ↔ int` encoding, so `int` is faithful on
the tested inputs (`[10, 20]` plot ⇒ integer-valued bounds in the F2P test
anyway). `--float-encoding` is therefore unnecessary; the bug is a
which-value-is-selected bug, not a precision bug.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — selecting the orientation's current axis bound as the initial
marker coordinates — is modeled **directly** (A3, the spelled-out branch +
`selected_bound`), not hidden behind an axiom about the function under change.
The only `@ContractOnly`, `reported_positions`, is an **A-reference** to the
**unchanged** `ToolLineHandles` report-back behaviour, validated by G-AX; the
proof does not lean on it for the discriminating clause (A3 is a direct
structural postcondition on the bound inputs).

## E. verify(model) ⇒ resolved

`selector_initial_coords` verifies only if its result equals the orientation's
current axis bound endpoints (A3) and equals the marker widget's report of them
(A4). By R (`float ↔ int`, `'horizontal'/'vertical' ↔ 0/1`, tuple/list
carriers) the verified selection equals the gold patch's
`positions = self.ax.get_xbound()/get_ybound()` fed to
`ToolLineHandles(self.ax, positions, …)`; by G-AX the real `ToolLineHandles`
reports those positions back unchanged (A-reference) and the resulting axes
bounds are unchanged. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited callee — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN
§1.1: callee soundness (G-AX) and refinement fidelity (this document, G-EQ).
