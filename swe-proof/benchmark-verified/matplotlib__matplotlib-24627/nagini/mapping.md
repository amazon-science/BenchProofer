# mapping.md — matplotlib__matplotlib-24627

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9d22ab09d52d279b125d8770967569de070913b2`, states the type
abstraction, and records callee provenance. There is **no axiom** in this
bundle: the changed behaviour is a pure object-graph mutation modelled deeply,
not a call into an unchanged library callee.

Repo file under change: `lib/matplotlib/axes/_base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reset_container(self)` | `_AxesBase.__clear(self)` — `lib/matplotlib/axes/_base.py:1239` (the private method invoked by `Axes.clear()`/`Axes.cla()`); the modeled hunk is the block at `lib/matplotlib/axes/_base.py:1315-1318` | the modeled changed function (the axes-reset routine) |
| `self` : `Container` | the `_AxesBase` instance being reset | the object whose member collection is emptied |
| `self.members` : `List[Element]` | `self._children` (`lib/matplotlib/axes/_base.py:1315`), the list of artists owned by the axes | the ordered collection of member elements |
| `Element` (`host`, `canvas`) | a child **artist** object and its two back-reference attributes `.axes` and `.figure` (declared on `Artist`, `lib/matplotlib/artist.py:152-173`) | a member element and the two owners it is parented under |
| `Element.host` : `Optional[int]` | the artist's `.axes` attribute (an `Axes` object, or `None`) | the host back-reference |
| `Element.canvas` : `Optional[int]` | the artist's `.figure` attribute (a `Figure` object, or `None`) | the canvas back-reference |

The gold patch replaces, at `lib/matplotlib/axes/_base.py:1315`,

```python
self._children = []
```

with

```python
old_children, self._children = self._children, []
for chld in old_children:
    chld.axes = chld.figure = None
```

— modelled by `old_members = self.members; self.members = []` followed by the
loop `old_members[i].host = None; old_members[i].canvas = None`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self._children` (a Python `list` of artist objects) | `self.members` : `List[Element]` | a `list` of objects ↔ a `List` of `Element`; `len`, index, and reassign-to-`[]` are identical operations |
| a child artist object | an `Element` instance carrying only the two touched fields | minimal class with only `.axes`/`.figure` analogues |
| `chld.axes` (an `Axes` instance or `None`) | `Element.host` : `Optional[int]` | a present owner (a non-`None` `Axes`) ↔ a non-`None` `int` token; `None` ↔ `None`. The F2P test observes this attribute only via `art.axes is ax` (present) vs `art.axes is None` (absent), so an opaque present/absent token is faithful. |
| `chld.figure` (a `Figure` instance or `None`) | `Element.canvas` : `Optional[int]` | a present owner (a non-`None` `Figure`) ↔ a non-`None` `int` token; `None` ↔ `None`. Observed only via `art.figure is fig` vs `art.figure is None`. |
| `chld.axes = chld.figure = None` (chained assignment of two attributes to `None`) | `old_members[i].host = None` and `old_members[i].canvas = None` | the chained assignment writes both attributes to the same `None`; modelled as two field writes to `None` |
| the `for chld in old_children:` iteration over the saved list | the `while i < len(old_members):` index loop | iteration over every former member, in any order (the de-parenting is order-independent — each element is set to the same `None` target) |

The dynamic attributes `.axes` / `.figure` are real fixed attribute names on
`Artist` (not name-computed), so they map directly to two `Element` fields; no
`str`-indexing/dynamic-`setattr` modelling is needed.

## 3. Callee provenance

None. The reset performs no call into an unchanged library callee whose
contract the proof consumes; it only re-binds `self._children` to a fresh empty
list and writes two attributes of each former child to `None`. Every operation
is a concrete object-graph mutation expressible directly in the model (see
refinement.md — all steps are R or I; there are no A steps and no kind-3 steps).
`axiom_check.py` therefore carries no axiom obligation; it instead executes the
real `Axes.clear()` end-to-end on the test's exact artist kinds (lines + image)
and asserts the de-parenting observable the refinement relies on (the structural
twin of the F2P test), confirming the deep model matches the real behaviour.
