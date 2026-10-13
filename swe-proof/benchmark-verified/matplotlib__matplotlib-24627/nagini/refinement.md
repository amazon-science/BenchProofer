# refinement.md — matplotlib__matplotlib-24627

The operation-by-operation correspondence between `model.py`'s implementation
(the `reset_container` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement — same operation, refined carrier type),
**A** (axiomatized callee — split **A-consumed** / **A-reference**), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `__clear` (`lib/matplotlib/axes/_base.py:1315`)

Gold hunk:
```
-        self._children = []
+        old_children, self._children = self._children, []
+        for chld in old_children:
+            chld.axes = chld.figure = None
```

| # | model.py impl op (`reset_container`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `self : Container`, `self.members : List[Element]` | `self` (`_AxesBase`), `self._children` (`list` of artists) | R | object/list carrier refinement (mapping.md §1–2): the `_AxesBase` instance ↔ `Container`, its `_children` list ↔ `members`. |
| 2 | `old_members = self.members` | `old_children, self._children = self._children, []` — the `old_children = self._children` half (the tuple-assignment captures the existing list before the rebind) | I | bind a name to the existing collection. The model writes it as a separate statement preceding the rebind; the gold uses a simultaneous tuple assignment. Both capture the pre-reset list into a local; the value bound is identical (the old RHS is evaluated before either target is written in a tuple assignment). |
| 3 | `self.members = []` | `... self._children = []` — the second half of the tuple assignment | I | rebind the collection to a fresh empty list. Identical operation; identical post-value (`len == 0`). |
| 4 | `while i < len(old_members): ... i = i + 1` | `for chld in old_children:` | I | iterate over every former member. The gold's `for` visits each element once; the model's index loop visits indices `0..len-1` once. The body is order-independent (step 5 writes the same constant `None` to each, with no cross-element dependence), so the two iteration orders produce identical final state. |
| 5 | `old_members[i].host = None` and `old_members[i].canvas = None` | `chld.axes = chld.figure = None` | R | de-parent the element: clear both back-references. `chld.axes`↔`host`, `chld.figure`↔`canvas` (mapping.md §2; `Optional[int]` token ↔ `Axes`/`Figure`-or-`None`). The chained assignment `a = b = None` writes both attributes to the same `None`; modelled as two writes to `None`. The discriminating content of the change — the former members end de-parented (`host is None and canvas is None`) rather than still attached — lives here. |

There is **no A step**: the reset calls no unchanged library callee whose
contract the proof consumes (it performs only a list rebind and per-element
attribute writes). There is **no kind-3 step**: every changed operation is a
concrete object-graph mutation expressed directly.

## B. The bug the spec senses (G-DIFF)

Pre-patch, `__clear` executed only `self._children = []` and left every former
child's `.axes`/`.figure` pointing at the now-cleared axes/figure.
`model_prepatch.py` reproduces exactly this (it performs `self.members = []` and
omits the de-parenting loop) and **fails** postcondition (2),
`Forall k. Old(self.members)[k].host is None and .canvas is None`. That is
precisely the spec sensing the change: the only behavioural difference between
the two skeletons is whether the former members are de-parented, and the spec's
discriminating clause is exactly that property. Postcondition (1)
(`len(self.members) == 0`) holds in both pre- and post-patch — it is the
unchanged half of the routine — so the differential witness is uniquely the
de-parenting clause.

## C. verify(model) ⇒ resolved

`reset_container` verifies only if, after the reset, the container's collection
is empty (postcondition 1) **and** every former member has both back-references
cleared to absent (postcondition 2). By R (object/list carrier; `Optional[int]`
token ↔ `Axes`/`Figure`-or-`None`) and I (the list rebind and the per-element
two-attribute clear) the verified routine is the gold `__clear` hunk up to type
refinement. The F2P test `test_cla_clears_children_axes_and_fig` observes
exactly postcondition (2): after `ax.clear()`, every artist that had been a
child has `art.axes is None` and `art.figure is None`. The P2P tests (which keep
`_children` emptied on clear, the unchanged half) observe postcondition (1).
Therefore a model satisfying this spec, refined by the map above, IS the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The lone
trust point is refinement fidelity (this document, G-EQ); there is no axiom, so
G-AX has no axiom obligation (it instead validates the deep object-graph model
against the real `Axes.clear()` end-to-end).
