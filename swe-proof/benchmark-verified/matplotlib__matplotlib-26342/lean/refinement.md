# refinement.md — matplotlib__matplotlib-26342

Maps every operation in `implementation_setPaths` to its `patch.diff`
counterpart. Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch, the modeled site)
```python
# lib/matplotlib/collections.py — Collection.set_paths
def set_paths(self, paths):
    self._paths = paths      # was: raise NotImplementedError
    self.stale = True
```
The patch also deletes the now-redundant `PathCollection.set_paths` override
(identical body, behavior-preserving inheritance refactor) — not modeled (see
mapping.md; contributes no independently-observable fixed behavior).

## Operation correspondence
| # | Lean op (`implementation_setPaths`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut c := coll` | enter the method with `self` bound | I | the container being mutated |
| 2 | `c := { c with paths := newPaths }` | `self._paths = paths` | R | `self._paths : list ↔ c.paths : List Path` (identity, order-preserving); record-update models the attribute assignment |
| 3 | `c := { c with stale := true }` | `self.stale = True` | I | `Bool` `true ↔ Python `True` |
| 4 | `return Except.ok c` | the method returns normally (no raise) | R | `Except.ok ↔ "returned"`; post-patch the method never raises, modeling the removal of `raise NotImplementedError` |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

The frame (`c.rest = coll.rest`, every other field untouched) is guaranteed by
the record-`with` update only naming `paths` and `stale`; it corresponds to the
fact that `set_paths` touches only `self._paths` and `self.stale`.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the REAL patched `Collection.set_paths` behavior (the
resulting `_paths`/`stale`) over ≥10^5 fuzzed replacement lists.
`conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` returns `Except.error ()` — the literal pre-patch
behavior, `raise NotImplementedError`. The spec demands `result = Except.ok c`
with `c.paths = newPaths ∧ c.stale = true`; an `error` result can never satisfy
the existential `∃ c, result = Except.ok c ∧ …`, so the carried gold proof fails
to typecheck on exactly the discriminating clause. This is precisely the behavior
the FAIL_TO_PASS test `test_contour_set_paths` asserts: calling `set_paths` on a
`ContourSet` must succeed and replace the paths (pre-patch it raised). The spec
is byte-identical between the two files (only the impl body differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the `collections.py` change); it applies
at `base_commit` and the harness resolves.
