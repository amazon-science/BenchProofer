# refinement.md — pydata__xarray-4695

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`labelSelect` `do` block) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — A-consumed / A-reference),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1, run in-container with the gold patch applied); the narrative is audited by
**G-EQ**. There are **no A-tagged ops** (no consumed axioms, no deep-model
references): see §C.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed dispatch — `_LocIndexer.__getitem__` (`xarray/core/dataarray.py:199`)

Gold hunk (the behavioural core):
```
             # expand the indexer so we can handle Ellipsis
             labels = indexing.expanded_indexer(key, self.data_array.ndim)
             key = dict(zip(self.data_array.dims, labels))
-        return self.data_array.sel(**key)
+        return self.data_array.sel(key)
```

| # | Solution.lean impl op (`labelSelect`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `key : List (String × Label)` | the normalized indexer dict `{dim: labels}` reaching the `sel` call (after `is_dict_like`/`expanded_indexer` at `:195-198`) | R | indexer mapping ↔ ordered `List (String × Label)`; dim name ↔ `String`; label list ↔ `List String` (mapping.md §2). G-CONF bridges to a real dict passed to `da.loc[...]`. |
| A2 | `return Except.ok key` | `return self.data_array.sel(key)` — the dict is passed **positionally** as `indexers`; `either_dict_or_kwargs` returns it unchanged (`dataset.py:2230`), so every entry is applied as a `(dimension, labels)` request | R + I | **I** at the level of the modeled behaviour: the applied mapping IS the whole input mapping, unchanged — the model's identity carry-through is the patched code's "pass the dict as the indexer mapping". **R** in carrier: the returned *selected array* is refined to the *applied mapping* it is a deterministic function of (mapping.md §2). `Except.ok` (vs `error`) ⇔ no entry diverted to an option ⇔ no spurious reject. G-CONF validates against the real patched `.loc` over values + dims + coordinate labels. |

The post-condition pins this exactly: `out = Except.ok key`. No implementation
may drop an entry (e.g. silently omit a dimension named `method`/`tolerance`/
`drop`/`indexers` from the applied mapping), reorder it, re-purpose it as a
selection option, or reject the selection — all of which the pre-patch
`sel(**key)` splat does for a reserved-named dimension, and all of which the
F2P test `test_loc_dim_name_collision_with_sel_params` forbids.

## B. The pre-patch (G-DIFF discriminator) — `Solution_prepatch.lean`

The pre-patch skeleton models `sel(**key)`: each entry is dispatched by name.
An entry named `method` binds to the `method=` option, whose value is not a
valid fill method, so selection is rejected (`Except.error "Invalid fill
method"`); any other reserved-named entry (`tolerance`/`drop`/`indexers`) binds
to its option and is thereby dropped from the applied dimension mapping
(`key.filter (·.1 ∉ reserved)`). Against the frozen spec `out = Except.ok key`
this diverges precisely when a reserved-named dimension is present — exactly the
issue's bug and exactly what the F2P test exercises (a dimension named
`method`). `prove_correct` fails on both branches (the `method` reject branch
and the reserved-drop branch), confirming the spec sees the defect.

The pre-patch keeps the spec byte-identical (G-DIFF `same_spec` verified): the
extra logic lives entirely inside the elided `impl` region; no `pure`/contract
text differs.

## C. No A-tagged ops; no kind-3

Every step is R or I. There is **no axiomatized callee** and **no deep-model
reference**: the operation that genuinely changed is *how the indexer mapping is
handed to the selection engine* (kwargs-splat → positional), which is modeled
**directly** as the identity carry-through of the applied mapping (A2). The
selection engine itself (`sel`/`either_dict_or_kwargs`/the index gather) is
neither axiomatized nor re-modeled in Lean — under the R refinement (mapping.md
§2) its effect is the deterministic function of the applied mapping that G-CONF
*executes* via the real patched `.loc`. Hence `meta.json axioms = []`,
`deep_model_references = []`, G-AX skipped. There is **no kind-3**
(inexpressible-changed-op) step: the change is expressible as "apply the whole
mapping", which the spec pins.

## D. verify(Solution) ⇒ resolved

`labelSelect` verifies only if its output is `Except.ok key` (A2): the entire
indexer mapping applied, in order, with no entry diverted and no spurious
reject. By R (indexer mapping ↔ `List (String × Label)`; selected array ↔
applied mapping) the verified method equals the patched
`_LocIndexer.__getitem__`'s applied-selection on every mapping, including
reserved-named dimensions. By G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on 10⁵ inputs against the REAL patched `da.loc[key]`
(and the pre-patch — which diverts/drops reserved-named dims — disagrees,
confirming discrimination). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc +
G-CONF); there is no axiom-soundness trust point (no axioms).
