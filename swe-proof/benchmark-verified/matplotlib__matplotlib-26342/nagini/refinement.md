# refinement.md — matplotlib__matplotlib-26342

The operation-by-operation correspondence between `model.py`'s implementation
(the `install_geometry` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The setter site — `Collection.set_paths` (`lib/matplotlib/collections.py:209`)

Gold hunk:
```
     def set_paths(self, paths):
-        raise NotImplementedError
+        self._paths = paths
+        self.stale = True
```

| # | model.py impl op (`install_geometry`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self: GeometryCollection` | `self` (a `Collection`/`ContourSet`) | R | the modeled object carries exactly the two touched fields; `GeometryCollection` ↔ `Collection` (mapping.md §1–2). |
| A2 | parameter `new_items: List[int]` | `paths: list[Path]` | R | `list[Path]` ↔ `List[int]` of opaque per-item identity tokens; each `Path` is opaque to the setter (mapping.md §2). |
| A3 | `self.items = new_items` | `self._paths = paths` | R + I | identical concrete operation (attribute assignment of a reference), under the field rename `items` ↔ `_paths` (R). The post-state `self.items is new_items` ⇔ `self._paths is paths`, i.e. `get_paths() is paths` — the same object is stored. |
| A4 | `self.out_of_date = True` | `self.stale = True` | R + I | identical concrete operation (assign the boolean literal `True`), under the field rename `out_of_date` ↔ `stale` (R). `self.out_of_date is True` ⇔ `self.stale is True`. The `Artist.stale` setter writes the backing bool and fires a callback that does not change the stored value (mapping.md §2). |

The discriminating content of the change — that the call now *installs* the
supplied sequence and marks the collection out of date, rather than failing —
lives in the postcondition `self.items is new_items and self.out_of_date is True`.
The pre-patch body raised before any assignment; `model_prepatch.py` reproduces
that as a body that installs nothing and **fails** the postcondition on the
clause `self.items is new_items` (line 71), which is exactly the spec sensing
the change (G-DIFF).

## B. The removed subclass override — `PathCollection.set_paths` (`collections.py:1005-1007`)

Gold hunk (deletion):
```
-    def set_paths(self, paths):
-        self._paths = paths
-        self.stale = True
-
```

This override performed the *same* `self._paths = paths; self.stale = True` the
base class now performs; the patch deletes it so the behaviour is inherited.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no node — single modeled `install_geometry`) | delete `PathCollection.set_paths` | I | pure de-duplication: the deleted override is byte-for-byte the behaviour `install_geometry` already specifies (A3+A4). For a `PathCollection` instance, dispatching `set_paths` to the fixed base class is observationally identical to the deleted override (same two assignments). No independent behaviour is fixed here, so no separate `model_prepatch` variant is warranted — site B introduces no new observable behaviour beyond site A. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The changed operation — installing the supplied
sequence and setting the out-of-date flag — is two concrete attribute
assignments, modeled **identically** (A3, A4) under field renames (R). There is
no opaque callee, hence **no consumed axiom** (`axioms` region is empty). The
only kind-A item is an **A-reference**: the real `Collection.set_paths`
semantics (stored-reference identity + flag + read-only input) against which
G-AX validates the modeled behaviour (mapping.md §3.1). Nothing the proof
consumes is an axiom.

## D. verify(model) ⇒ resolved

`install_geometry` verifies only if it stores EXACTLY the supplied sequence
(`self.items is new_items`, A3) and sets the out-of-date flag
(`self.out_of_date is True`, A4), while leaving the supplied sequence's contents
untouched (read-only postcondition). By R (the two field renames and the
opaque-`Path`-token carrier) this is exactly `self._paths = paths; self.stale =
True`, i.e. the gold hunk. The F2P test `test_contour_set_paths` calls
`cs_test.set_paths(cs_ref.get_paths())` and renders: it passes iff the test
figure now draws the reference paths, which holds iff `get_paths()` returns the
installed `paths` object (A3) and the artist redraws because it is stale (A4).
Pre-patch this raised `NotImplementedError` (the prepatch's installs-nothing
skeleton). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to field renames and the opaque-token carrier — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ); the A-reference real-setter semantics are confirmed by G-AX
(run with the gold patch applied — the modeled function IS the changed function,
so the A-reference target is the post-patch `Collection.set_paths`; mapping.md
§3.1).

### D.1 The identity clause is deliberately stronger than the test-observable
The F2P test `test_contour_set_paths[png]` is a `@check_figures_equal` oracle:
it observes *render equality + redraw*, not CPython object identity. A copy
variant (`self._paths = list(paths)`) would also pass F2P + all P2P (it renders
the same geometry and marks the artist stale), yet it FAILS the load-bearing
`self.items is new_items` (A3) identity clause. So this spec is strictly
*stronger* than the minimal test-observable behaviour.

This is intentional and does NOT break the bundle's `verify ⟹ resolved`
contract (which is one-directional: everything that verifies still resolves).
The identity clause is the faithful-to-gold contract required by SPEC_GUIDE
directive 3: `model.py` is a faithful skeleton mirroring `patch.diff`
line-for-line, and gold is `self._paths = paths` — a by-identity store, NOT a
copy. The copy variant is a *different algorithm* the guide explicitly forbids
modeling toward; identity (Nagini `is`) is the correct refinement of gold's
exact data flow (A3) and also supports the documented stored-reference use case
(a caller that prepares a sequence and expects that very object used). It is
modeled deliberately and should not be re-flagged as over-specification.
