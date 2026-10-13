# mapping.md — pytest-dev__pytest-6197

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e856638ba086fcf5bebf1bebea32d5cf78de87b4`, states the type
abstraction, and gives the provenance of the modelled load primitive.

Repo file under change: `src/_pytest/python.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Container` (class with `loaded: bool`, `load_count: int`) | a `PyobjMixin`/`Module`/`Package` collector node — the parts touched are its lazily-mounted `_obj` (`getattr(self, "_obj", None)`) and the import side effect of `_getobj()` (`src/_pytest/python.py:248-272`) | minimal carrier with only the two touched pieces of state |
| `Container.loaded` | "`_obj` is not `None`", i.e. the underlying object has been mounted/imported (`src/_pytest/python.py:262-264`) | abstract boolean: object loaded yet? |
| `Container.load_count` | the number of times the load side effect `self._getobj()` has been performed (for `Module`/`Package`, `_getobj` is `_importtestmodule`, the actual import of the `__init__.py` / module — the observable, possibly-raising effect) (`src/_pytest/python.py:264`, `443-444`, `508`) | abstract observable: how many loads happened |
| `access_object(c)` | the `obj` property getter — POST-patch the mount logic is inlined into it (`src/_pytest/python.py:251-255` pre-patch via `_mount_obj_if_needed`; post-patch the getter itself does the lazy mount) | the on-demand access phase: lazy mount, return |
| `enumerate_children(c)` | `Package.collect(self)` (`src/_pytest/python.py:641-670`) | the discovery phase: enumerate children WITHOUT loading the container's own object |

Pre-patch repo symbols the change removes/relocates (for the refinement audit,
not referenced from the consumer spec view):

- `PyobjMixin._mount_obj_if_needed(self)` (`python.py:261-268`) — the standalone
  lazy-mount helper. Post-patch it is **deleted** and its body folded into the
  `obj` getter (`python.py:251-259` post-patch).
- The `self._mount_obj_if_needed()` call at the head of `Package.collect`
  (`python.py:642`) — **removed** post-patch. This removal is the discriminating
  behavioural change: discovery no longer eagerly loads the package object.
- `Module.__init__` (`python.py:435-441`) — **removed** post-patch (the
  `_ALLOW_MARKERS = False` for `__init__.py` files). A refactor consequence of
  the now-lazy marker unpacking; observationally subsumed by the lazy-load
  change for the tested behaviour (see refinement.md §C).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| collector node with attribute `_obj` (`None` ⟺ not yet mounted) | `Container.loaded: bool` | `_obj is None` ⟺ `not loaded`; `_obj is not None` ⟺ `loaded`. The model abstracts the object's *identity* away (irrelevant to the tested behaviour) and keeps only the boolean "is it mounted". |
| the import side effect of `_getobj()` / `_importtestmodule()` (runs module/`__init__.py` top-level code; may raise) | `Container.load_count: int` incremented by the deep-modelled load transition | one execution of `_getobj()` ⟺ `load_count += 1`. The model abstracts *what* the load returns and *whether* it raises into the single observable "a load happened", which is exactly what the FAIL_TO_PASS tests detect (a `__init__.py` with `assert False` errors iff it is loaded). |
| `self._obj = obj = self._getobj()` (the cached mount: sets `_obj` and runs the import) | `c.loaded = True; c.load_count = c.load_count + 1` | the two assignments are the cache-and-load transition; modelled deeply (no opaque callee). |
| `if obj is None:` guard before mounting | `if not c.loaded:` | the "mount only once" guard. |

## 3. Callee provenance (kind-A)

**There is no consumed `@ContractOnly` axiom.** The only opaque thing the
changed code touches is the load primitive `_getobj()`/`_importtestmodule()`,
whose *changed observable* (whether it runs during discovery) is precisely the
behaviour under test — per SPEC_GUIDE §3 it is therefore modelled **deeply**
(the in-line `loaded := True; load_count += 1` transition), NOT hidden behind an
axiom about the function under change. Consequently it is an **A-reference**,
validated against reality by `axiom_check.py` (G-AX), not an A-consumed axiom.

### 3.1 load primitive deep model ↔ real `_getobj`/`Package.collect` (A-reference)
**Reference behaviour:** in patched pytest,
`Package.collect` (`src/_pytest/python.py`, post-patch) no longer begins with
`self._mount_obj_if_needed()`, so enumerating a package's children performs
**zero** loads of the package's own underlying object; the object is mounted
lazily only when `self.obj` is read (the inlined getter,
`python.py:251-259` post-patch). The deep model encodes exactly this:
`enumerate_children` leaves `load_count` unchanged; `access_object` performs the
load lazily (≤ 1, and leaves `loaded` true).

**Soundness check (G-AX):** `axiom_check.py` drives the REAL installed pytest as
a subprocess over the two FAIL_TO_PASS scenarios (a package whose `__init__.py`
raises must not break an unrelated run; a `src`-layout package must not be put
on the path / loaded by discovery) plus boundary package names and randomized
package layouts, and asserts: discovery succeeds (rc == 0 ⟹ zero loads during
enumeration) while genuinely accessing a package's own object still surfaces the
load on demand (deferral ≠ silent drop). Imports only the standard library;
pytest is invoked via `sys.executable -m pytest`, the way the harness runs it.
Exit 0 iff sound.

Flag/configuration dependency: the F2P observable assumes pytest's default
collection (no `--keepduplicates`, no custom `python_files` that would match the
`__init__.py`); `axiom_check.py` runs with defaults, matching the tests.

## 3.2 Conformance check (G-CONF)

`conformance_check.py` diffs the contract-stripped impl region (shadow)
against real patched collector nodes (the `obj` getter / `Package.collect`)
over >= 1e5 realized (state, op-sequence) inputs across on-disk package
layouts. Pinned fuzz seed: **6197** (layout-generation rng: 6198).

## 4. Permission discipline (irreversibility of the load effect)

The real load primitive is an import: once its side effect has happened it
cannot be un-happened. A spec that only pins the NET change of `load_count`
(`== Old(load_count)`) would admit bodies that perform the load transition and
then restore the counter — meaningless in the model, impossible in reality.
The contracts therefore grant write permission on the load state only where a
load may legitimately occur:

- `enumerate_children` takes `Acc(c.loaded, 1/2)` and `Acc(c.load_count, 1/2)`
  (read-only): ANY write to the load state during discovery — even one that
  restores the old value — is a permission failure. Repo counterpart: patched
  `Package.collect` never mounts the package's own object.
- `access_object` takes `Acc(c.loaded)` (it must be able to set loaded) but
  only `Acc(c.load_count, 1/2)` unconditionally, plus the second half
  conditionally under `Implies(not c.loaded, ...)`: the counter is writable
  exactly when the container is not yet loaded. On an already-loaded container
  the counter is read-only, so a redundant re-load (perform-then-undo on the
  already-loaded branch) is a permission failure. Repo counterpart: the
  patched `obj` getter runs `_getobj()` only under the `obj is None` guard.

The value postconditions (`== Old(...)`, `+1`) are retained on top of the
permission discipline; together they pin both WHERE a load may happen and WHAT
the resulting state must be.

## 5. Termination obligation

Both modelled phases carry `Requires(MustTerminate(2))` (total correctness;
`Container.__init__` carries `MustTerminate(1)`). Repo counterpart: real
`Package.collect` and the real `obj` getter are bounded computations that
return control to the collection run (collect iterates the finite directory
visit; the getter performs at most one import then returns). A diverging body
would satisfy the value postconditions only vacuously while hanging the test
session — not the repo behaviour in either the fixed or the buggy state. See
refinement.md §C2.
