# refinement.md — matplotlib__matplotlib-20859

The operation-by-operation correspondence between `model.py`'s implementation
(the `attach` impl region, plus the deep `in_canvas_family` / `is_coords_artist`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `Ensures`, **A-reference** where a deep model is validated == a real
callee/relation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The parent-classification dispatch — `Legend.__init__` (`lib/matplotlib/legend.py:433-442`)

Gold hunks:
```
- from matplotlib.figure import Figure
+ from matplotlib.figure import FigureBase
  ...
- elif isinstance(parent, Figure):
+ elif isinstance(parent, FigureBase):
      self.isaxes = False
      self.set_figure(parent)
  else:
-     raise TypeError("Legend needs either Axes or Figure as parent")
+     raise TypeError(
+         "Legend needs either Axes or FigureBase as parent"
+     )
```

| # | model.py impl op (`attach`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `parent: Parent` with `parent.tag : int` | the `parent` argument of `Legend.__init__`, classified by `isinstance` | R | the runtime class ↔ a class-family tag; `isinstance(parent, C)` ↔ a pure predicate over the tag encoding the real `issubclass` relation (mapping.md §2,§3). |
| A2 | `if is_coords_artist(parent.tag): return Attached(True, parent.host_canvas)` | `if isinstance(parent, Axes): self.isaxes = True; self.set_figure(parent.figure)` | R + A-reference | `is_coords_artist(tag)` is the deep model of `isinstance(parent, Axes)` (validated == `issubclass(cls, Axes)` by G-AX); `is_coords=True` ↔ `self.isaxes=True`; `canvas == host_canvas` ↔ `set_figure(parent.figure)` (R: identity tokens, `set_figure` = assignment, mapping.md §2). |
| A3 | `elif in_canvas_family(parent.tag): return Attached(False, parent.tag)` | `elif isinstance(parent, FigureBase): self.isaxes = False; self.set_figure(parent)` | A-reference + R | **the changed test**, modelled DEEPLY: `in_canvas_family(tag)` (`tag ∈ {TAG_TOPLEVEL, TAG_NESTED}`) is the per-class subtype membership in the canvas-surface family. There is no consumed `is_figurebase` axiom — the proof never depends on one. The deep model is validated **== the real `isinstance(parent, FigureBase)`** out-of-band: G-AX (axiom_check.py) runs `issubclass` against the real `Figure`, `SubFigure`, `Axes`, foreign classes and asserts agreement. `is_coords=False` ↔ `self.isaxes=False`; `canvas == parent.tag` (identity) ↔ `set_figure(parent)` (R). |
| A4 | `else: raise ParentRejected()` | `else: raise TypeError("Legend needs either Axes or FigureBase as parent")` | R | a foreign parent (neither family) is rejected; `ParentRejected` stands in for `TypeError` (builtin-exception `Exsures` crashes Nagini, mapping.md §2). Only the reject-vs-attach distinction is observed. |

The discriminating content of the change — a nested canvas region (`SubFigure`)
is a member of the canvas-surface family (`FigureBase`) and so must be ACCEPTED
rather than rejected — lives in `in_canvas_family(TAG_NESTED) == True` (model)
⇔ `isinstance(subfigure, FigureBase) == True` (real). The pre-patch narrow test
`isinstance(parent, Figure)` rejected a `SubFigure` (since `SubFigure` is not a
subclass of `Figure`); `model_prepatch.py` reproduces that by testing the narrow
`parent.tag == TAG_TOPLEVEL` in its impl and **fails** the postcondition
`Implies(in_canvas_family(parent.tag), (not Result().is_coords) and Result().canvas == parent.tag)`
together with the `Exsures` clause `not in_canvas_family(parent.tag)` for the
`TAG_NESTED` parent — which is exactly the spec sensing the change (G-DIFF;
verifier error: "Assertion (not in_canvas_family(parent.tag)) might not hold").

## B. No kind-3 (unexpressible-changed-op) steps
Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the parent type test widening from `Figure` to `FigureBase` — is
modelled **deeply** (`in_canvas_family`, the per-class family-membership
predicate in the `pure` region, step A3, an **A-reference**), not hidden behind
an axiom about the function under change. There is **no consumed axiom** in this
bundle: the subtype relation is the only opaque fact and it is validated == the
real `issubclass` by G-AX (axiom_check.py), not asserted as a `@ContractOnly`.

## C. verify(model) ⇒ resolved
`attach` verifies only if, for a canvas-family parent (`TAG_TOPLEVEL` or
`TAG_NESTED` alike), it returns normally with `is_coords=False` and
`canvas == parent` (A3) — in particular it must NOT raise for the nested-region
parent. By R (class ↔ tag, `set_figure` = assignment, identity tokens) and by
G-AX (`in_canvas_family` == real `isinstance(·, FigureBase)`, the A-reference),
the verified dispatch equals the gold dispatch
`isinstance(parent, FigureBase) ⇒ isaxes=False, set_figure(parent)` on every
parent the tests pass — in particular it accepts a `SubFigure`, makes
`leg.figure is subfig`, and does not raise. The F2P test `test_subfigure_legend`
observes exactly this (`leg.figure is subfig`); the P2P tests pass an `Axes`
parent (A2 branch) or a top-level `Figure` parent (A3 branch) and are unaffected.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited subtype relation — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
the A-reference subtype soundness (G-AX) and refinement fidelity (this
document, G-EQ).
