# mapping.md — matplotlib__matplotlib-20859

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 64619e53e9d0ed417daba287ac0d3a06943a54d5`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deep-model reference.

Repo file under change: `lib/matplotlib/legend.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `anchorToParent (parent : Container)` | the parent-dispatch block of `Legend.__init__` — `lib/matplotlib/legend.py:433-442` (the `if isinstance(parent, Axes): … elif isinstance(parent, <canvas>): … else: raise TypeError` ladder, plus the binding side effects it performs) | the modeled changed function (the dispatch guard + its three branches) |
| `Container` | `parent` — the object the constructor anchors the new artist to | the parent shape: `region ↔` an `Axes`; `canvas id topLevel ↔` a figure-like canvas (`topLevel=true ↔` a top-level `Figure`, `topLevel=false ↔` a nested `SubFigure`); `other ↔` anything else |
| `isRegion` *(deep model — A-reference)* | `isinstance(parent, Axes)` — `legend.py:433` (`from matplotlib.axes import Axes`, `legend.py:362`) | pure spec: the parent is a plotting region |
| `isCanvas` *(deep model — A-reference)* | `isinstance(parent, FigureBase)` — `legend.py:437` **post-patch** (`from matplotlib.figure import FigureBase`) | pure spec: the parent is a figure-like canvas of EITHER kind (the BROAD membership test the fix installs) |
| `isTopCanvas` *(deep model — A-reference)* | `isinstance(parent, Figure)` — `legend.py:437` **pre-patch** (`from matplotlib.figure import Figure`) | pure spec: the parent is specifically a top-level canvas (the NARROW pre-patch test); used only in the prepatch and in the `isTopCanvas → isCanvas` lemma |
| `regionCanvas` | `parent.figure` — the owning canvas of an `Axes` (`legend.py:436`, `self.set_figure(parent.figure)`) | pure spec: the canvas a region is bound to |
| `canvasId` | `parent` itself — the canvas an `Axes`-less parent is bound to (`legend.py:439`, `self.set_figure(parent)`) | pure spec: the canvas a figure-like parent is bound to |
| `Anchor { fromRegion, canvas }` | the observable post-state of the dispatch: `self.isaxes` (`fromRegion`) and the figure passed to `self.set_figure(...)` (`canvas`) | pure spec: the binding the dispatch establishes |
| `AnchorErr.unsupportedParent` | `raise TypeError("Legend needs either Axes or … as parent")` — `legend.py:441` | pure spec: rejection of an unsupported parent |
| `anchorSpec` | the intended behavior of the dispatch block | pure spec the method's `ensures` pins |

The pre-patch repo test the change replaces (refinement audit only, not named in
the consumer spec view): `isinstance(parent, Figure)` (`legend.py:437`), which
only accepts a top-level canvas and so rejects a nested sub-canvas, raising the
`TypeError`. The fix broadens it to `isinstance(parent, FigureBase)` (and updates
the message text).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `parent` argument | `Container` | an `Axes` instance `↔ .region (id parent.figure)`; a `FigureBase` instance `↔ .canvas (id parent) topLevel`, where `topLevel = isinstance(parent, Figure)` (a top-level canvas ↔ `true`, a nested sub-canvas ↔ `false`); any other object `↔ .other` |
| `isinstance(parent, Axes)` | `isRegion parent` | a real builtin membership test; total and exact (the runtime class hierarchy is fixed) |
| `isinstance(parent, FigureBase)` | `isCanvas parent` | broad membership test; true for both a top-level canvas and a nested sub-canvas |
| `isinstance(parent, Figure)` | `isTopCanvas parent` | narrow membership test; true only for a top-level canvas |
| `parent.figure` (Axes) / `parent` (canvas) — the figure passed to `set_figure` | `regionCanvas` / `canvasId` (a `Nat` identity) | only the IDENTITY of the bound canvas is observed (F2P `leg.figure is subfig`); `id(obj)` is an injective tag, a faithful total carrier for "which canvas" |
| `self.isaxes` flag | `Anchor.fromRegion : Bool` | `True ↔ true`; set on the region branch, cleared on the canvas branch |
| `raise TypeError(...)` from the dispatch | `Except.error .unsupportedParent` | the only error this slice raises; tests observe the raised type |

Unit/object identity is modeled as `Nat` tags: the dispatch only ever selects a
branch on the parent's runtime type and records which canvas the child is bound
to — it never inspects canvas internals. A `Nat` tag is a faithful, total carrier
for "which canvas". The magnitudes/contents the parent carries are observationally
irrelevant to this change and are not modeled (avoids over-claiming).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `isRegion`/`isCanvas`/`isTopCanvas` deep model ↔ `isinstance` (A-reference)
**Callee:** the Python builtin `isinstance(parent, C)` against the unchanged
classes `Axes`, `FigureBase`, `Figure`. The patch does NOT change any of these
classes or `isinstance`; it changes only *which* class the second dispatch arm
tests against (`Figure` → `FigureBase`). The three predicates are modeled
**deeply** in the `pure` region and validated == the real `isinstance` by G-AX.

The load-bearing structural fact the fix turns on is the class hierarchy
`SubFigure(FigureBase)`, `Figure(FigureBase)`:

* a top-level canvas satisfies both the broad and the narrow test
  (`isinstance(fig, FigureBase)` and `isinstance(fig, Figure)`);
* a **nested sub-canvas** satisfies the broad test but **NOT** the narrow one
  (`isinstance(subfig, FigureBase)` is `True`, `isinstance(subfig, Figure)` is
  `False`) — this is exactly the reported bug: the pre-patch narrow test rejects
  it;
* a plotting region (`Axes`) satisfies none of the three (branch disjointness).

These are encoded as `isTopCanvas p → isCanvas p` (the lemma `loom_solve`/`grind`
uses) plus the carrier construction `topLevel = isinstance(parent, Figure)`.

This is an **A-reference**, not a consumed axiom: the membership tests are
modeled deeply (the inductive `Container` + the three predicates) and validated
against the real builtin by G-AX, which constructs real `Figure` / `SubFigure` /
`Axes` / non-figure objects and asserts each predicate matches `isinstance`, the
`isTopCanvas → isCanvas` implication holds, branch disjointness holds, and the
discriminator (sub-canvas is `FigureBase` & not `Figure`) holds. There is **no**
consumed `axiom` in this bundle.

The patched function under spec (`anchorToParent` ↔ the dispatch block) is
**never** axiomatized — only the unchanged `isinstance` callee against unchanged
classes is modeled (SPEC_GUIDE §0.7).

### 3.2 Flag/branch dependency
`isCanvas` (the broad test) is reached by `anchorToParent` exactly when the
parent is not a region. G-AX therefore exercises `isinstance(parent, FigureBase)`
on the configurations the impl actually reaches (top-level canvas, nested
sub-canvas, and non-canvas), and separately confirms the narrow/broad split that
motivates broadening the test.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`20859`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the dispatch branch selection and its consequence (bound canvas / region flag /
rejection) to Python and bridges I/O via the §2 bijection, leaving the A-tagged
membership tests as the real builtin `isinstance` against the real class
hierarchy. It diffs the shadow against `patch.diff`'s patched-`Legend.__init__`
behavior over ≥10⁵ fuzzed parent objects spanning every `Container` shape
(top-level canvas, nested sub-canvas incl. deep nesting, plotting region, and
unsupported parents). The observable depends only on the parent's runtime type,
so the (expensive) real-object oracle is memoized per parent identity.
