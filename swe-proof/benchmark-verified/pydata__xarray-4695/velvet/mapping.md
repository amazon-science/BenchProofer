# mapping.md — pydata__xarray-4695

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed. All line numbers are at `base_commit`
`51ef2a66c4e0896eab7d2b03e3dfb3963e338e3c`.

## 1. Symbol binding

| Lean (`Solution.lean`) | repo symbol | location @ base_commit |
|---|---|---|
| `labelSelect` | `xarray.core.dataarray._LocIndexer.__getitem__` (label-based selection: `DataArray.loc[key]`) | `xarray/core/dataarray.py:194` (the method); changed line `:199` |
| `key : List (String × Label)` | the dict-like `key` argument once it is the per-dimension indexer mapping (after the `is_dict_like` / `expanded_indexer` normalization at `:195-198`) | `xarray/core/dataarray.py:194-199` |

The single changed function is `_LocIndexer.__getitem__`. The gold patch's one
hunk (`dataarray.py:199`) changes how the normalized indexer mapping `key` is
handed to the selection engine:

```
-        return self.data_array.sel(**key)
+        return self.data_array.sel(key)
```

Pre-patch, `key` is splat as keyword arguments, so each entry is dispatched by
name against `sel`'s own parameter list
(`def sel(self, indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs)`,
`dataarray.py:1118`): an entry whose dimension name is `indexers`/`method`/
`tolerance`/`drop` binds to that option rather than to `**indexers_kwargs`. A
dimension named `method` therefore passes its label list as the *fill method*,
which the index machinery rejects ("Invalid fill method ...") — the issue's
symptom. Post-patch the whole mapping is passed positionally as `indexers`, and
`Dataset.sel`'s first act is
`indexers = either_dict_or_kwargs(indexers, indexers_kwargs, "sel")`
(`dataset.py:2230`, `utils.either_dict_or_kwargs` at `utils.py:254`), which —
given the positional dict and empty kwargs — returns the dict unchanged. Every
entry is thus honoured as a `(dimension, labels)` request regardless of name.

## 2. Type bijection (Lean ↔ Python)  — used by G-CONF

| Lean | Python (real repo) |
|---|---|
| `key : List (String × Label)` | the normalized indexer dict `{dim_name: label_values}` passed to selection (ordered; one pair per requested dimension) |
| `String` (first projection) | a dimension name (`Hashable`, here always `str`) |
| `Label = List String` (second projection) | the tick labels requested along that dimension — a list of labels (a scalar label is the singleton list; list-valued indexers keep the dimension in the result) |
| `out : Except String (List (String × Label))` | the *applied* indexer mapping — i.e. which `(dimension, labels)` requests `sel` actually carries out. `Except.ok m` ⇔ selection succeeds applying mapping `m`; `Except.error _` ⇔ selection is rejected (an entry was diverted to an option, e.g. the "Invalid fill method" reject). |
| `out = Except.ok key` | "all of `key` is applied, in order, none diverted, no spurious error". |

**R refinement (the heart):** for a given source array, the selected
sub-array `da.loc[key]` is a *deterministic function of the applied
`(dimension, labels)` mapping* — it gathers, along each named dimension, the
positions of the requested labels (orthogonal/outer indexing for list
indexers), leaving unnamed dimensions full. Hence pinning the **applied
mapping** (`out = Except.ok key`) pins the **selected array**. G-CONF realizes
this refinement concretely: its shadow computes the selected array directly from
the coordinate label tables by positional `np.ix_` gather (never calling
`.sel`/`.loc`), and compares against the real patched `da.loc[key]`
(values + result dims + per-axis coordinate labels).

## 3. Callee provenance & flag dependencies

- **`DataArray.sel` / `Dataset.sel` / `either_dict_or_kwargs`** — these are the
  selection engine the changed line dispatches to. They are **NOT axiomatized**
  and **NOT deeply modeled** as separate Lean objects: the behaviour under
  specification is purely *which mapping reaches the engine*. Under the R
  refinement above, the engine's effect (gather by labels) is the deterministic
  function of the applied mapping that G-CONF executes via the real patched
  `.loc`. There is therefore **no consumed axiom and no A-reference** (see
  refinement.md §C). G-AX is skipped (`meta.json axioms = []`,
  `deep_model_references = []`), exactly as in the no-axiom exemplar
  django__django-11087.
- **`is_dict_like` (`utils.py:230`) / `expanded_indexer` (`indexing.py:23`)** —
  run *before* the changed line to normalize `key` into the indexer mapping.
  They are unchanged and lie upstream of the modeled step; the model takes the
  normalized mapping as its input `key` (no contract consumed).
- **Reserved-name set.** The names that collide with `sel`'s options are exactly
  its non-`**kwargs` parameters: `indexers`, `method`, `tolerance`, `drop`
  (`dataarray.py:1118-1124`). `method` is the one the issue reports (its values
  must be a valid fill method); the other three are equally diverted under the
  pre-patch splat. G-CONF fuzzes all four (see §4).

## 4. G-CONF fuzz seed & coverage

- **Seed:** `SEED = 4695` (pinned in `conformance_check.py`).
- **N:** `N_FUZZ = 100_000` fuzzed cases.
- **Coverage:** 1–3 dimensions; dimension names drawn from a pool that includes
  all four reserved names (`method`, `tolerance`, `drop`, `indexers`) plus
  ordinary names, with a 60% bias to force ≥1 reserved name into the dims;
  per-dimension label subsets of varying size and order; indexer mappings over
  random subsets of the dims (≥1). Each case asserts the real patched
  `da.loc[key]` agrees with the shadow on result dims, per-axis coordinate
  labels, and selected values. Exit 0 iff zero disagreements.
