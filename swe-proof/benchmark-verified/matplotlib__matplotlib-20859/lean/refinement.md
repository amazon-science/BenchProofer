# refinement.md — matplotlib__matplotlib-20859

Maps every operation in `implementation_resolveLegendParent` to its
`patch.diff` counterpart in the parent-kind dispatch at the head of
`Legend.__init__` (`lib/matplotlib/legend.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch dispatch ladder)
```python
from matplotlib.figure import FigureBase          # was: import Figure
...
if isinstance(parent, Axes):
    self.isaxes = True
    self.axes = parent
    self.set_figure(parent.figure)
elif isinstance(parent, FigureBase):              # was: isinstance(parent, Figure)
    self.isaxes = False
    self.set_figure(parent)
else:
    raise TypeError("Legend needs either Axes or FigureBase as parent")
self.parent = parent
```
The modeled value is the triple of decisions the ladder makes from `parent`'s
kind: `(self.isaxes, the recorded figure object, or rejection)`.

## Operation correspondence
| # | Lean op (`implementation_resolveLegendParent`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if isAxesKind p.kind then` | `if isinstance(parent, Axes):` | R | `isinstance(parent, Axes)` ↔ `isAxesKind p.kind = true`. The runtime class of `parent` is modeled as the enum `ParentKind` (mapping.md). |
| 2 | `return .ok (true, p.ownerFigureId)` | `self.isaxes = True; self.axes = parent; self.set_figure(parent.figure)` | R | axes legend; the recorded figure is the canvas the axes belongs to — `id(parent.figure)` ↔ `ownerFigureId`. `self.axes = parent` is not separately modeled (it records the same `parent`; the observable the test pins is `self.figure`). |
| 3 | `else if isCanvasKind p.kind then` | `elif isinstance(parent, FigureBase):` | R | **the fix.** `isinstance(parent, FigureBase)` ↔ `isCanvasKind p.kind = true`, which holds for BOTH `topCanvas` and `subCanvas`. Pre-patch this tested the narrower `Figure` (= `topCanvas` only). |
| 4 | `return .ok (false, p.selfId)` | `self.isaxes = False; self.set_figure(parent)` | R | non-axes legend; the recorded figure is `parent` itself — `id(parent)` ↔ `selfId`. The F2P test asserts exactly `leg.figure is subfig`, i.e. the recorded figure equals the (sub-)canvas parent. |
| 5 | `else return .error ()` | `else: raise TypeError("Legend needs either Axes or FigureBase as parent")` | R | rejection of a non-axes, non-canvas parent ↔ `Except.error`. The exception message is not modeled (it is not an observable the spec pins). |

Every op is R; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — `isinstance` is modeled deeply as the kind predicates, and the
figure object identity enters as data per mapping.md). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R legs ⇒ G-CONF
The whole impl is R, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs (the four
parent kinds × random object ids). `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the second arm tests the narrower top-level-figure class
(`isinstance(parent, Figure)`), so a nested sub-canvas — which is canvas-like but
NOT the top-level figure class — falls through to the `else` and is rejected with
`TypeError`. The prepatch impl reproduces this exactly:
`else if p.kind = .topCanvas then …` recognises only `topCanvas`, so for
`p.kind = .subCanvas` it returns `.error ()`. It therefore cannot satisfy
`problem_spec_resolveLegendParent` on the discriminating clause
(`isAxesKind = false → isCanvasKind = true → result = .ok (false, selfId)`)
when `p.kind = .subCanvas` (`isCanvasKind = true` but the impl returns `.error`).
This is precisely the case the FAIL_TO_PASS test `test_subfigure_legend`
exercises: a legend added to a sub-figure must succeed with `leg.figure is
subfig`. The carried gold proof fails to typecheck against the buggy impl on the
`refine_2.subCanvas` goal (G-DIFF — confirmed: prepatch verify exits 1).
