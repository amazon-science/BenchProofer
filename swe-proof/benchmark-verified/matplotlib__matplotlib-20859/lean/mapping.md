# mapping.md — matplotlib__matplotlib-20859

## Symbol binding (file:line @ base_commit 64619e53e9)
Modeled function: the **parent-kind dispatch** at the head of `Legend.__init__`,
`lib/matplotlib/legend.py` (the `isinstance(parent, …)` ladder, base lines
432–442). The constructor decides, from the kind of the `parent` artist it is
attached to, whether the legend is an *axes* legend or a *figure-like* legend,
and which figure object it records — or rejects the parent entirely.

Pre-patch ladder (base `legend.py:432–442`):
```python
from matplotlib.figure import Figure              # base :363
...
if isinstance(parent, Axes):
    self.isaxes = True
    self.axes = parent
    self.set_figure(parent.figure)
elif isinstance(parent, Figure):
    self.isaxes = False
    self.set_figure(parent)
else:
    raise TypeError("Legend needs either Axes or Figure as parent")
self.parent = parent
```
Post-patch the second arm tests `FigureBase` (the common base class of both the
top-level figure object and a nested sub-figure object) instead of the
top-level-figure class only.

Lean modeled function name: `resolveLegendParent` (names the *behavior* —
"resolve what kind of parent a legend is being attached to and what it records",
not the patched class/method `Legend.__init__`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `resolveLegendParent` (modeled decision) | `Legend.__init__` parent dispatch, `legend.py:432–442` |
| `Parent.kind` | the runtime class of `parent`: an axes, a top-level figure object, a nested sub-figure object, or anything else |
| `ParentKind.axes` | `isinstance(parent, Axes)` is true |
| `ParentKind.topCanvas` | `parent` is the top-level figure object (a `FigureBase` that is the whole canvas) |
| `ParentKind.subCanvas` | `parent` is a nested sub-canvas object (a `FigureBase` that is **not** the top-level figure) |
| `ParentKind.other` | none of the above (neither an axes nor any figure-like canvas) |
| `Parent.selfId` | object identity of `parent` itself (what `set_figure(parent)` records for a figure-like parent; the test asserts `leg.figure is subfig`) |
| `Parent.ownerFigureId` | for an axes parent, the identity of `parent.figure` — the figure the axes belongs to (`set_figure(parent.figure)`) |
| `result = .ok (true, fid)` | `self.isaxes = True; self.set_figure(parent.figure)` — figure recorded is `fid` |
| `result = .ok (false, fid)` | `self.isaxes = False; self.set_figure(parent)` — figure recorded is `fid` |
| `result = .error ()` | `raise TypeError("Legend needs either Axes or … as parent")` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| runtime class of `parent` ∈ {Axes, Figure(top), SubFigure(nested), other} | `Parent.kind : ParentKind` (4 constructors) |
| `id(parent)` (object identity used by `is`) | `Parent.selfId : Nat` |
| `id(parent.figure)` for an axes parent | `Parent.ownerFigureId : Nat` |
| `isinstance(parent, Axes)` | `isAxesKind p.kind = true` |
| `isinstance(parent, FigureBase)` (post-patch) | `isCanvasKind p.kind = true` (true for `topCanvas` **and** `subCanvas`) |
| `isinstance(parent, Figure)` (pre-patch, narrower) | `p.kind = .topCanvas` only |
| `(self.isaxes, id(self.figure))` after `__init__` returns | `result = .ok (isaxes, figureId)` |
| `raise TypeError(...)` | `result = .error ()` |

### Class-hierarchy modeling note
In matplotlib both the top-level figure object and a nested sub-figure object
derive from the common base class that the post-patch second arm tests; the
top-level figure object additionally derives from the narrower class the
pre-patch arm tested, but the nested sub-figure object does **not**. We model the
relevant runtime class as the 4-way enum `ParentKind`: the two figure-like kinds
(`topCanvas`, `subCanvas`) are both recognised by the post-patch `isCanvasKind`
predicate, while only `topCanvas` was recognised pre-patch. `Axes` and `other`
are the remaining kinds. The four kinds are mutually exclusive and exhaustive, so
the dispatch result is fully determined by `kind`.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `set_figure` is a plain setter
  whose only observable effect modeled here is which figure object is recorded;
  that object's identity enters as DATA (`selfId` / `ownerFigureId`). The
  `isinstance` tests are modeled deeply as the `kind`-discriminating predicates
  `isAxesKind` / `isCanvasKind` (an I/R op, not an axiom). Hence `axioms = []`,
  `deep_model_references = []`, and `axiom_check.py` is a skip stub.
- No flag dependency: the dispatch is unconditional on `kind`.

## G-LEAK
The solver-visible `problem_statement` is about *adding a legend to a SubFigure*
and quotes the classes `Axes`, `Figure`, `SubFigure`, and `FigureBase`. The spec
view nonetheless avoids narrating the edit: it describes the abstract behavior
("a legend is attached to a parent that is an axes, a top-level canvas, a nested
sub-canvas, or something else; both canvas kinds are valid figure-like parents")
using neutral identifiers (`topCanvas`, `subCanvas`, `isCanvasKind`) that echo no
patched repo symbol (`Figure`, `FigureBase`, `Legend`, `set_figure`). No gold
diff line is quoted.

## Pinned G-CONF fuzz seed
`20859`.
