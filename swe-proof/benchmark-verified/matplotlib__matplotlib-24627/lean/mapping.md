# mapping.md — matplotlib__matplotlib-24627

## Symbol binding

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_clearAxes` / `problem_spec_clearAxes` / `correct_clearAxes` | the child-reset step inside `_AxesBase.__clear` (the `cla()`/`clear()` implementation) | `lib/matplotlib/axes/_base.py:1318` @ `9d22ab09d52d279b125d8770967569de070913b2` |

The modeled step is exactly the gold-edited region:

```python
# pre-patch (base_commit):
self._children = []
# post-patch (gold):
old_children, self._children = self._children, []
for chld in old_children:
    chld.axes = chld.figure = None
```

The surrounding `__clear` body (rcParam reads, locator/formatter resets, grid
setup, …) is unrelated to the modeled behavior and is not part of the spec.

## Lean ↔ Python type bijection (used by G-CONF)

| Lean | Python | notes |
|---|---|---|
| `Artist` | a child artist object (`Line2D`, `AxesImage`, …) | only the touched references are modeled |
| `Artist.axes : Option Nat` | `artist.axes` (an `Axes` or `None`) | identity abstracted to `Nat`; `none ⇔ None` (deparented) |
| `Artist.figure : Option Nat` | `artist.figure` (a `Figure` or `None`) | identity abstracted to `Nat`; `none ⇔ None` |
| `Artist.data : Nat` | every OTHER field of the artist | opaque placeholder for "state clear must not touch" |
| `artists : List Artist` (input) | `self._children` (the `old_children` snapshot) before clearing | order preserved |
| `result.1 : List Artist` | `self._children` after clearing | always `[]` |
| `result.2 : List Artist` | the former children, post-deparenting | positional with input |

The real code mutates each child in place and resets `self._children` to `[]`.
Lean is referentially transparent, so the impl returns the pair
`(newChildren, formerChildren)`: `newChildren` is the new `self._children` (`[]`)
and `formerChildren` are the (functionally) updated former children. The spec
pins both components (frame discipline §0.5): the new list is empty, and each
former child is deparented with all other fields preserved.

## Callee provenance / flag deps

No unchanged external callee is consumed. The modeled operation is a plain
list/record transformation (assignment + per-element field reset), modeled
deeply. No `opaque` decl, no `_prop` axiom, no A-reference. G-AX is a skip stub;
G-CONF validates the R legs.

## G-CONF fuzz seed

Pinned seed: **24627** (matches `conformance_check.py` `SEED` and
`meta.json verifier_pins.conf_seed`).
