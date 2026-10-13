# refinement.md — pytest-dev__pytest-6197

The operation-by-operation correspondence between `model.py`'s implementation
(the `enumerate_children` and `access_object` impl regions, with the load
primitive modelled deeply) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee/behaviour by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The discovery site — `Package.collect()` (`src/_pytest/python.py:641`)

Gold hunk:
```
     def collect(self):
-        self._mount_obj_if_needed()
         this_path = self.fspath.dirpath()
         ...
```

`model.py` symbol: `enumerate_children(c)`.

| # | model.py impl op (`enumerate_children`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `c: Container` with fields `loaded`, `load_count` | `self` (the `Package` collector node), its `_obj`/import-side-effect state | R | collector node ↔ `Container`; `_obj is None` ↔ `not loaded`; "an import happened" ↔ `load_count += 1` (mapping.md §2). |
| A2 | (no load op in the body — `pass`; the discovery body that follows touches only children, never the container's own object) | the gold **deletes** the leading `self._mount_obj_if_needed()` line; the remaining body (`this_path = …`, the `visit` loop yielding child `Module`s) does not mount `self.obj` | I + R | the removal of the eager-mount call is rendered as the absence of any `load_count`-incrementing op in `enumerate_children`. The rest of `collect` (enumerating children) performs no load of the container's own object — R-refined away because it is irrelevant to the modelled observable (it neither reads nor mounts `self.obj`). |

Discriminating content: the gold deletes the eager load at the head of
discovery. `model.py`'s `enumerate_children` therefore performs **zero** loads
(`Ensures(c.load_count == Old(c.load_count))`). `model_prepatch.py` restores the
pre-patch behaviour — the eager-mount transition `if not c.loaded: loaded =
True; load_count += 1` at the head of discovery — and **fails** that exact
postcondition (G-DIFF). This is precisely the bug the F2P test
`test_does_not_eagerly_collect_packages` detects: a package whose `__init__.py`
runs `assert False` errors during collection iff discovery loads it.

## B. The access site — the `obj` getter (`src/_pytest/python.py:251`)

Gold hunk (the mount logic is inlined from the deleted `_mount_obj_if_needed`
into the property getter):
```
     @property
     def obj(self):
         """Underlying Python object."""
-        self._mount_obj_if_needed()
-        return self._obj
-    ...
-    def _mount_obj_if_needed(self):
         obj = getattr(self, "_obj", None)
         if obj is None:
             self._obj = obj = self._getobj()
             if self._ALLOW_MARKERS:
-                self.own_markers.extend(get_unpacked_marks(obj))
+                self.own_markers.extend(get_unpacked_marks(self.obj))
+        return obj
```

`model.py` symbol: `access_object(c)`.

| # | model.py impl op (`access_object`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if not c.loaded:` | `obj = getattr(self, "_obj", None); if obj is None:` | R | the "mount only once" guard; `_obj is None` ↔ `not loaded` (mapping.md §2). |
| B2 | `c.loaded = True; c.load_count = c.load_count + 1` | `self._obj = obj = self._getobj()` | R + A-reference | one execution of the import primitive ↔ one `load_count` increment and `loaded := True`; the load primitive is modelled DEEPLY (no opaque callee axiom — see §C), validated == real `_getobj` by G-AX. |
| B3 | (the modelled state ends loaded; the return of the object itself is abstracted away) | `return obj` (and the `own_markers.extend(...)` marker bookkeeping) | R | the returned object's identity and the marker side-bookkeeping are irrelevant to the tested load observable and are R-refined away; the only retained effect is "the container is now loaded" (`Ensures(c.loaded is True)`). |

The access phase preserves lazy single-load behaviour
(`Old(loaded) ⇒ load_count unchanged`; `not Old(loaded) ⇒ exactly one load`),
so the deferral introduced at site A is **not a silent drop**: the object is
still loaded the first time it is genuinely accessed. G-AX checks this against
real pytest (a package containing tests, with a raising `__init__.py`, still
surfaces the load on access).

## C. No consumed axiom; no kind-3 step

The one operation whose observable behaviour genuinely **changed** is the load
primitive's *timing* — whether `_getobj()`/`_importtestmodule()` runs during
discovery. Per SPEC_GUIDE §3 a changed operation is modelled **deeply**, never
hidden behind a `@ContractOnly` axiom about the function under change. It is
modelled here as the in-line state transition `loaded := True; load_count += 1`
(site B2), and validated == the real callee/behaviour out-of-band by
`axiom_check.py` (G-AX) — an **A-reference**, NOT an A-consumed axiom. There is
no consumed `@ContractOnly` in this bundle (the `axioms` region is empty), so
there is no dead-axiom or mislabelled-axiom risk. Every step above is R, A
(here A-reference), or I — no kind-3 (changed-inexpressible-op) step.

The two refactor-only hunks the gold also makes — deleting the standalone
`_mount_obj_if_needed` (its body is folded into the getter, site B) and deleting
`Module.__init__`'s `_ALLOW_MARKERS = False` for `__init__.py` — do not add an
independently-tested observable beyond the load-timing change: with loading now
lazy, `__init__.py` files are not loaded during discovery regardless of
`_ALLOW_MARKERS`, so the marker-allow flag no longer participates in the tested
path. Hence one `model_prepatch.py` (site A's eager-load restoration) is the
single independently-fixed behaviour the F2P tests observe (refinement.md §A;
mapping.md §1).

## C1b. Permission discipline (irreversibility of the load effect)

The value clauses alone (`load_count == Old(load_count)` etc.) pin only the NET
state change, but the real load effect is an import — irreversible. A body that
performs the load transition and then restores the counter would satisfy every
value clause while its faithful real translation still runs the import (there
is no real inverse of `-= 1`). The contracts therefore also restrict WHERE the
load state may be written, via fractional permissions:

- `enumerate_children`: `Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2)` —
  read-only. Discovery cannot write the load state AT ALL, transiently or
  otherwise. This renders the gold deletion of the eager mount at the head of
  `Package.collect` as a permission fact, not just a net-delta fact: same-spec
  rivals that load-then-undo (or flip-then-restore) during discovery fail with
  a permission error.
- `access_object`: `Acc(c.loaded)` (full — it must set loaded on first access)
  but write permission on `c.load_count` only when `not c.loaded` (the second
  `Acc(c.load_count, 1/2)` is granted under `Implies(not c.loaded, ...)`).
  On an already-loaded container the counter is read-only, so a redundant
  re-load (perform-then-undo on the already-loaded branch — whose faithful
  translation re-imports an already-imported object) fails with a permission
  error. This matches the patched getter: `_getobj()` runs only under the
  `obj is None` guard.

Both obligations are faithful to the gold behaviour, not a tightening beyond
it: the patched `collect` body never touches the package's own `_obj`/import
state, and the patched getter touches the import state only on the fresh path.
The positive controls (gold impl, reshaped access impl, read-only enumeration)
all still verify.

## C2. Termination (total correctness)

Both `enumerate_children` and `access_object` carry `Requires(MustTerminate(2))`
(and `Container.__init__` carries `MustTerminate(1)` so it remains callable from
either phase). Rationale: every value postcondition above is a
partial-correctness guarantee; without a termination obligation, a body that
diverges (`while True: pass`) satisfies all of them vacuously, and its faithful
real translation — an infinite loop at the head of `Package.collect` — hangs the
whole pytest run and resolves nothing (this exact same-spec rival was
constructed by the G-EQ audit, `atk_10_enum_loop.py`). In the real repo both
phases are bounded computations that return control to the collection loop:
`Package.collect` builds and returns its child list; the `obj` getter returns
the (possibly freshly mounted) object. So total correctness is a faithful part
of the specified behaviour, not a tightening beyond it. Under Nagini,
`MustTerminate` is discharged by loop-free bodies and rejects any loop that does
not consume the obligation with a strictly decreasing measure (obligation leak
check) — see `properties.py` case `enum-diverge-loop`.

## D. verify(model) ⇒ resolved

`enumerate_children` verifies only if it performs zero loads of the container's
own object (A2 — `Ensures(load_count == Old(load_count))`), and `access_object`
verifies only if it loads lazily exactly once on first access and leaves the
container loaded (B1–B3). By R (collector node ↔ `Container`, `_obj` ↔ `loaded`,
import side effect ↔ `load_count`) the verified discovery equals the gold
`Package.collect` with its leading mount deleted, and the verified access equals
the gold inlined `obj` getter, on the tested scenarios; by G-AX the deep load
model matches the real `_getobj` timing (A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited A-reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
