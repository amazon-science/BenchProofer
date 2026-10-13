# mapping.md — matplotlib__matplotlib-26342

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2aee6ccd7c7e1f8d282c1e7579f4ee546b838542`, states the type
abstraction, and records callee provenance.

Repo file under change: `lib/matplotlib/collections.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `install_geometry(self, new_items)` | `Collection.set_paths(self, paths)` — `lib/matplotlib/collections.py:209` | the modeled changed function (the base-class path setter) |
| `GeometryCollection` (modeled object) | `Collection` (and any subclass, e.g. `ContourSet(ContourLabeler, Collection)` at `lib/matplotlib/contour.py:706`) | the drawable collection whose two touched fields are modeled |
| `self.items` (field) | `self._paths` — read back by `Collection.get_paths` (`collections.py:206-207`) | the held geometry sequence (an object reference) |
| `self.out_of_date` (field) | `self.stale` — the cached-rendering-out-of-date flag (`matplotlib/artist.py:310-328`, `Artist.stale` property/setter) | whether the artist must be re-drawn |
| `new_items` (param) | `paths` — the supplied list of `matplotlib.path.Path` objects | the sequence being installed |

The pre-patch repo state the change replaces (for the refinement audit, not
referenced from the consumer spec view): `Collection.set_paths` raised
`NotImplementedError` (`collections.py:209-210`); the subclass override
`PathCollection.set_paths` (`collections.py:1005-1007`) already performed the
`self._paths = paths; self.stale = True` assignment and is removed by the patch
(its behaviour now inherited from the fixed base class — pure de-duplication,
observationally identical for `PathCollection`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `paths` : `list[matplotlib.path.Path]` (and `self._paths`) | `List[int]` of opaque per-item identity tokens | the operation never inspects an item's internals; each `Path` is an opaque token `new_items[k]`; `len(paths)` ↔ `len(new_items)`; list element order ↔ list index order |
| object reference identity `get_paths() is paths` | Nagini `self.items is new_items` | storing a reference: Python attribute assignment binds the same object; `is` models CPython identity |
| `self.stale` : `bool` (via the `Artist.stale` property, backed by `self._stale`) | `self.out_of_date` : `bool` | `stale = True` ↔ `out_of_date is True`; the property setter writes the backing bool and fires a callback that does not alter the value observed here |
| `raise NotImplementedError` (pre-patch body) | a body that performs no installation (model_prepatch) | the pre-patch never reached an assignment; modeled as a no-op skeleton so the identity/flag postconditions are violated (G-DIFF) |

`matplotlib.path.Path` carries no behaviour the setter touches, so it is an
opaque token; the carrier `List[int]` lets the spec state read-only-ness
(fractional `list_pred` permission + per-index content preservation) and stored
reference identity (`is`).

## 3. Callee provenance

No `@ContractOnly` axiom is consumed: installing a geometry sequence is pure
object/state logic — store a reference (`self._paths = paths`) and set a flag
(`self.stale = True`). There is no external callee whose contract the proof
depends on.

### 3.1 A-reference: the real setter semantics (checked by G-AX / axiom_check.py)
The modeled behaviour is validated against the real Python semantics of the
patched `Collection.set_paths` out-of-band:

* attribute assignment `self._paths = paths` stores the **same object**, so
  `Collection.get_paths()` returns it by identity (`get_paths() is paths`) —
  the modeled `self.items is new_items`;
* `self.stale = True` leaves the artist marked out of date
  (`Artist.stale` reads back `True`) — the modeled `self.out_of_date is True`;
* the supplied `paths` list is not rewritten by the setter (the contents the
  caller passed are the contents observed afterwards) — the modeled read-only
  postcondition (fractional `list_pred` + per-index preservation).

`axiom_check.py` exercises the REAL **post-patch** `Collection.set_paths` (it
runs with the gold patch applied — see the scope note below), asserting all
three observations on the call sites that genuinely dispatch to the modeled
*base* setter:

* a `ContourSet` (the F2P subject), which inherits the base setter;
* `PathCollection` — the patch DELETES its identical override, so post-patch it
  inherits the base setter (the script verifies `PathCollection.set_paths is
  Collection.set_paths`); and
* a bare `Collection` instance (the base method directly, incl. the
  empty-sequence boundary).

It also confirms the environment-independent primitive (Python attribute
assignment stores by reference; bool assignment yields the assigned value).

**Scope discipline.** `LineCollection` and `PolyCollection` are NOT in scope: at
`base_commit` their `set_paths` is an *override* (`LineCollection.set_paths` is
`set_segments`; `PolyCollection.set_paths` is `set_verts`) that rebuilds
`self._paths` from the supplied data and does NOT store the supplied object by
identity (verified in-container). Asserting the base setter's identity contract
on them would be factually wrong. `axiom_check.py` instead uses them as a
**negative control**, asserting `LineCollection.set_paths is not
Collection.set_paths` and `PolyCollection.set_paths is not Collection.set_paths`,
confirming they fall correctly OUTSIDE the modeled function's scope.

**Apply-gold requirement.** The modeled function IS the changed function (deep
model, empty axioms region), so the A-reference target is the *post-patch*
symbol. Pre-patch the base setter `raise NotImplementedError` and reaches no
assignment; therefore `axiom_check.py` must run with the gold patch applied
(orchestrator `apply_gold=True`, `gold_patch_path=patch.diff`). Invoked without
it, the script prints `G-AX SKIP` and returns 0 (it does not assert against the
un-patched state, and does not attempt an in-process matplotlib reload).

Source of the change: `lib/matplotlib/collections.py:209-210` (patched to
`self._paths = paths; self.stale = True`). Exit 0 iff sound.
