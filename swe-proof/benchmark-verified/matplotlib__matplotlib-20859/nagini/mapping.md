# mapping.md — matplotlib__matplotlib-20859

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 64619e53e9d0ed417daba287ac0d3a06943a54d5`, states the type
abstraction, and gives the provenance of the subtype relation the deep model
is validated against.

Repo file under change: `lib/matplotlib/legend.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `attach(parent)` | the parent-classification dispatch inside `Legend.__init__` — `lib/matplotlib/legend.py:433-442` | the modeled changed code: classify the legend's parent, set the coordinates flag and the owning canvas, or reject |
| `Parent.tag` | the runtime class of the `parent` argument of `Legend.__init__` (`legend.py:295`) | which class family the parent belongs to |
| `Parent.host_canvas` | `parent.figure` (read when the parent is an `Axes`, `legend.py:436`: `self.set_figure(parent.figure)`) | the canvas an `Axes` parent already sits on |
| `Attached.is_coords` | `self.isaxes` (`legend.py:434,438`) | the coordinates flag the dispatch sets |
| `Attached.canvas` | `self.figure` after `set_figure(...)` (`legend.py:436,439`; `Artist.set_figure` at `lib/matplotlib/artist.py:719` sets `self.figure = fig`) | the canvas the legend comes to belong to |
| `is_coords_artist(tag)` | `isinstance(parent, Axes)` (`legend.py:433`) | pure spec: parent is a coordinate-system artist |
| `in_canvas_family(tag)` *(deep model — A-reference)* | `isinstance(parent, FigureBase)` (post-patch, `legend.py:437`) restricted to the else-branch (i.e. excluding the `Axes` case already taken) | pure spec: parent is a member of the canvas-surface family; deep model of the real subtype test, validated by axiom_check.py (G-AX), NOT a consumed axiom |
| `ParentRejected` | `raise TypeError("Legend needs either Axes or FigureBase as parent")` (post-patch, `legend.py:440-441`) | the rejection of a parent in neither family |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the narrow check
`isinstance(parent, Figure)` (`legend.py:437` at base_commit) and its local
import `from matplotlib.figure import Figure` (`legend.py:363`). The fix widens
both to `FigureBase`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the runtime class of `parent` | `Parent.tag : int` (one of `TAG_COORDS=0`, `TAG_TOPLEVEL=1`, `TAG_NESTED=2`, `TAG_FOREIGN=3`) | each tag stands for a representative real class: `Axes`, `Figure`, `SubFigure`, and a foreign artist (`Line2D`) respectively (mapping.md §3). `isinstance(parent, C)` ↔ a pure predicate over the tag encoding the real `issubclass` relation. |
| `parent.figure` (an Axes' owning canvas) | `Parent.host_canvas : int` | object identity modelled as an `int` token; only its equality with `Attached.canvas` is observed (the F2P test uses `leg.figure is subfig`, an identity comparison). |
| `self.isaxes : bool` | `Attached.is_coords : bool` | identical boolean. |
| `self.figure` (set by `set_figure`) | `Attached.canvas : int` | object identity as an `int` token; `set_figure(parent)` ⇒ `canvas == parent`'s identity, `set_figure(parent.figure)` ⇒ `canvas == host_canvas`. |
| `raise TypeError(...)` | `raise ParentRejected()` | a builtin exception in an `Exsures` crashes the Nagini translator, so a user-defined exception stands in (SPEC_GUIDE §2). The only observed property is that a foreign parent is rejected rather than attached. |

`set_figure` itself (`artist.py:719`) is the identity on the figure attribute
for the inputs the dispatch produces (the legend starts with `self.figure is
None`, so the `set_figure` no-op / single-figure guards never fire); it is
modelled as a direct assignment `Attached.canvas = <arg>`.

## 3. Subtype-relation provenance (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `in_canvas_family` / `is_coords_artist` deep model ↔ the real class hierarchy
**Callee:** Python's built-in `isinstance` / `issubclass` against matplotlib's
class hierarchy in `lib/matplotlib/figure.py` and `lib/matplotlib/axes/`:

```
class FigureBase(Artist):     # figure.py:181
class SubFigure(FigureBase):  # figure.py:1924
class Figure(FigureBase):     # figure.py:2112
class Axes(_AxesBase):        # axes/_axes.py:47   (_AxesBase(Artist): axes/_base.py:542)
```

So, with the dispatch reaching the second branch only after the `Axes` branch
did not fire:

  `isinstance(parent, FigureBase)` is true for **both** `Figure` and
  `SubFigure` (they share the `FigureBase` base type) and false for `Axes` and
  for any foreign artist.

The changed test is modelled **deeply** by the pure predicate
`in_canvas_family(tag)` (`tag ∈ {TAG_TOPLEVEL, TAG_NESTED}`); there is **no
`@ContractOnly` axiom** the proof consumes. The deep model is validated equal
to the real subtype relation out-of-band by axiom_check.py (G-AX), which asserts
for every modelled tag:

  `is_coords_artist(tag) == issubclass(real_class, Axes)`
  `in_canvas_family(tag) == (issubclass(real_class, FigureBase) and not issubclass(real_class, Axes))`

and the discriminating facts `issubclass(SubFigure, FigureBase)` and
`not issubclass(SubFigure, Figure)` — exactly why the pre-patch narrow
`isinstance(parent, Figure)` rejected a `SubFigure` while the post-patch
`isinstance(parent, FigureBase)` accepts it.

**Flag dependency:** none — `isinstance`/`issubclass` take no behaviour-altering
flag. The relation is fixed by the class definitions at `base_commit` (and is
stable across the matplotlib 3.4 series in this instance's image).

**Soundness check (G-AX):** `axiom_check.py` imports the real
`matplotlib.axes.Axes`, `matplotlib.figure.{Figure, FigureBase, SubFigure}`,
and a foreign `matplotlib.lines.Line2D`, and asserts the two model predicates
agree with the real `issubclass` relation for all four representative classes,
that the families are mutually exclusive, and that the discriminating
`SubFigure`-is-a-`FigureBase`-but-not-a-`Figure` facts hold. It imports only
matplotlib (the package the patch lives in) and the standard library. Exit 0
iff sound.

## 4. No consumed axioms
This bundle ships **no** `@ContractOnly` axiom. The single non-trivial semantic
fact — the subtype relation — is modelled deeply (`in_canvas_family`,
`is_coords_artist`) and validated as an **A-reference** by G-AX, not consumed
as an axiom.
