# mapping.md — matplotlib__matplotlib-26342

## Instance
- repo: matplotlib/matplotlib
- base_commit: 2aee6ccd7c7e1f8d282c1e7579f4ee546b838542
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch edits `lib/matplotlib/collections.py`. Two sites, one behavioral
change:

1. `Collection.set_paths` (the base class, `lib/matplotlib/collections.py:209`)
   changes from `raise NotImplementedError` to
   ```python
   self._paths = paths
   self.stale = True
   ```
   i.e. it now actually installs the replacement path list and raises the
   staleness flag, instead of rejecting the call.

2. `PathCollection.set_paths` (a subclass, `lib/matplotlib/collections.py:1004`
   @ base_commit) — which already had exactly that body — is **deleted**. This is
   a pure refactor: the subclass now inherits the identical implementation from
   the base class. No observable behavior changes at the `PathCollection` site
   (before and after, `set_paths` does `self._paths = paths; self.stale = True`).

The only behavior the patch changes is at the base-class `Collection.set_paths`:
pre-patch it raised; post-patch it succeeds and updates the two fields. This is
the behavior the FAIL_TO_PASS test `test_contour_set_paths` exercises: a
`ContourSet` (a `Collection` subclass that does NOT override `set_paths`) has
`cs_test.set_paths(cs_ref.get_paths())` called on it; pre-patch this raised
`NotImplementedError`, post-patch it replaces the paths so the test figure
matches the reference figure.

## Modeled function
I model the **base-class `set_paths` operation**: given a container holding a
path list, a staleness flag, and other state, install a replacement path list.
This is the smallest unit whose observable behavior the patch changes and the
F2P test pins. It is a pure field update with no I/O; its whole observable
behavior is the resulting container (or the rejection).

The PathCollection-deletion site is NOT separately modeled: it is a behavior-
preserving refactor (the subclass body is identical to the base body it now
inherits), so it contributes no independently-observable fixed behavior and no
prepatch variant (SPEC_GUIDE §3: "one failing prepatch per independently-
observable fixed behavior").

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_setPaths` | `Collection.set_paths` (`lib/matplotlib/collections.py:209`), post-patch body |
| `problem_spec_setPaths` | the post-condition the resulting container must satisfy |
| `PathContainer` | the touched fields of a `Collection`: `_paths`, `stale`, plus an opaque carrier for all other state |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `Path : Type` (parameter) | a `matplotlib.path.Path` (or any object stored in the list) | the operation is agnostic to the element type; modeled as a free type |
| `coll : PathContainer Path` | a `Collection` instance | `.paths ↔ self._paths` (the list of paths), `.stale ↔ self.stale` (bool), `.rest ↔` the frame of all other attributes |
| `newPaths : List Path` | the `paths` argument to `set_paths` | a Python list of paths ↔ `List Path` (identity, order-preserving) |
| result `: Except Unit (PathContainer Path)` | the post-call state, or a raised `NotImplementedError` | `Except.ok c ↔ "the call returned and self now holds c"`; `Except.error () ↔ "the call raised NotImplementedError"` (the pre-patch behavior) |

`List Path ↔ Python list` is the identity bijection (same length, same order,
same elements). The `Except` layer models the raise/success distinction: the
post-patch base method always succeeds (`ok`), the pre-patch one always raised
(`error`).

## Callee provenance / flag deps
- No unchanged repo callee is consumed. The post-patch body is two direct
  attribute assignments (`self._paths = paths`, `self.stale = True`); there is no
  helper whose behavior must be captured. There is no `opaque` callee and no
  `axiom <callee>_prop`; the `axioms` region is empty and `axiom_check.py` is a
  skip stub.
- No flag dependency: `set_paths` branches on nothing; it unconditionally
  installs the list and sets the flag.

## G-CONF fuzz seed
- pinned seed: `26342`
- ≥10^5 fuzzed replacement lists (varying length 0..N and element identity); the
  shadow performs the field update, the oracle calls the REAL patched
  `Collection.set_paths` on a fresh `Collection` and reads back `_paths`/`stale`.
