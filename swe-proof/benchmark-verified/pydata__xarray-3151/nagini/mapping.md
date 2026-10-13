# mapping.md — pydata__xarray-3151

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 118f4d996e7711c9aced916e6049af9f28d5ec66`, states the type
abstraction, and documents the refinement/soundness boundary (this bundle
consumes no `@ContractOnly` axiom).

Repo file under change: `xarray/core/combine.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `guard_rejects(is_joined, is_monotonic)` | the post-concatenation monotonicity-check loop inside `combine_by_coords` — `xarray/core/combine.py:503-511` (the `for dim in concatenated.dims: if dim in concatenated: ... raise ValueError(...)` block) | the modeled changed code: whether the final consistency guard rejects the combined result |
| `any_joined_nonmonotonic(is_joined, is_mono)` *(deep model — A-reference)* | the post-patch selection rule `for dim in concat_dims: if not (indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing): raise` (`xarray/core/combine.py:503-510` post-patch) | pure spec: the result is rejected iff some joined dimension is non-monotonic; the deep model of the changed selection logic, validated == the real post-patch guard by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the loop iterates `concatenated.dims`
(ALL dimensions of the combined result) guarded by `if dim in concatenated` (the
dimension is a coordinate present in the result), instead of iterating
`concat_dims` (only the dimensions actually concatenated along).

## 2. Type abstraction (R-refinements)

The combined result `concatenated` and its per-dimension metadata are modelled
by two parallel `List[int]` flag lists, one entry per modeled dimension, aligned
by position. The modeled domain is the **coordinate dimensions present in the
combined result** — i.e. exactly the dimensions the pre-patch loop's
`if dim in concatenated` guard admits and the F2P test exercises (`x`, `y`).
Within that domain:

| repo reality | model carrier | bijection |
|---|---|---|
| `dim in concat_dims` (the dimension was concatenated along, because its coordinate varied between the input datasets) | `is_joined[d] == 1` | `concat_dims` is exactly `{ d : is_joined[d] == 1 }`; a bystander coordinate dimension (identical across inputs, not concatenated) is `is_joined[d] == 0` |
| `indexes = concatenated.indexes.get(dim); indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing` (the dimension's combined index runs monotonically, either direction) | `is_monotonic[d] == 1` | the single-coordinate monotonicity test is an unchanged predicate on the combined index; its boolean outcome is the carrier flag. A non-monotonic combined coordinate is `is_monotonic[d] == 0` |
| `raise ValueError("Resulting object does not have monotonic global indexes ...")` vs. completing the loop without raising | the boolean `Result()` of `guard_rejects` (`True` = the guard rejects/raises) | raising ↔ `Result() == True`; falling through ↔ `Result() == False`. The downstream `merge(...)` and the rich `Dataset` payload are unchanged by the guard and are outside the modeled behaviour. |
| the guard is a bounded `for` loop over the finite `concat_dims` and always completes (raising or falling through) | `Requires(MustTerminate(2))` (total-correctness obligation), discharged by the loop measure `Invariant(MustTerminate(i))` | the real guard always ANSWERS. Nagini verifies partial correctness by default, so without this obligation an implementation with no normal exit (an infinite loop) satisfies every value `Ensures` vacuously; the obligation pins the control-flow effect that a verdict is actually delivered. |

Rich `Dataset` objects, `pandas.Index`, and `str` dimension names are banned
or unusable in Nagini, so the carrier is parallel `List[int]` of 0/1 flags; the
specification is phrased over `PSeq[int]` via `ToSeq`.

**Domain-restriction note (audited by G-EQ / G-PANEL faithfulness).** The
pre-patch loop additionally skips dimensions that are *not* coordinates present
in the result (`dim in concatenated.dims` but `dim not in concatenated`). All
modeled dimensions are coordinate dimensions present in the result, so the
pre-patch guard inspects every modeled dimension; the post-patch guard inspects
only the joined subset (`is_joined == 1`). This is the exact contrast the F2P
test exercises and is what the prepatch's failing invariant senses. Every
dimension that is joined along is necessarily a coordinate present in the result
(it has a combined coordinate index), so `concat_dims ⊆ {coordinate dims present}`
— the post-patch set is a subset of the pre-patch set, never larger.

## 3. Soundness boundary (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `any_joined_nonmonotonic` deep model ↔ the real post-patch guard (A-reference)
**Callee/behaviour:** the post-patch monotonicity guard of
`xarray.core.combine.combine_by_coords`. The changed selection — *which*
dimensions are subjected to the monotonicity check — is modelled **deeply** by
the `@Pure` front-recursive existential `any_joined_nonmonotonic` (in the `pure`
region) and the matching loop in `guard_rejects`; there is **no `@ContractOnly`
axiom** the proof consumes. The deep model is validated equal to the real
post-patch behaviour out-of-band by `axiom_check.py` (G-AX).

Post-patch source (the gold patch's hunk, `xarray/core/combine.py`):

```python
# Check the overall coordinates are monotonically increasing
for dim in concat_dims:
    indexes = concatenated.indexes.get(dim)
    if not (indexes.is_monotonic_increasing
            or indexes.is_monotonic_decreasing):
        raise ValueError("Resulting object does not have monotonic"
                         " global indexes along dimension {}"
                         .format(dim))
```

`concat_dims` is produced by `_infer_concat_order_from_coords`
(`xarray/core/combine.py:51-112`): a dimension is appended to `concat_dims`
**only** inside the `if not all(index.equals(indexes[0]) ...)` branch — i.e.
only when its coordinate **varies** between the input datasets (a "bystander"
dimension whose coordinate is identical on every dataset is deliberately left
out, per the docstring promise that "coordinate dimensions which do not vary
between each dataset" are ignored). Hence `dim in concat_dims` ⟺ the dimension
was concatenated along ⟺ `is_joined[d] == 1`.

The real guard therefore rejects iff some dimension in `concat_dims` has a
non-monotonic combined index — exactly `any_joined_nonmonotonic`. A bystander
coordinate (e.g. `y = ['a','c','b']`, identical across inputs, non-monotonic) is
not in `concat_dims`, so the post-patch guard never inspects it; the pre-patch
guard did (it iterated `concatenated.dims` filtered by `dim in concatenated`),
which is the spurious `ValueError` the issue reports.

**Soundness check (G-AX):** `axiom_check.py`
1. reproduces the real post-patch guard predicate from the dimension metadata
   (`concat_dims` membership = `is_joined`; per-dimension monotonicity =
   `is_monotonic`) and asserts it equals the deep model
   `any_joined_nonmonotonic` over all 341 exhaustive boundary metadata vectors
   (dimension counts 0..4) plus 50 000 randomized fuzz vectors (counts up to 8);
2. when run in-container (where the patched xarray is installed), builds real
   `xarray.Dataset`s — including the issue's non-monotonic `['a','c','b']`
   bystander, a non-monotonic *joined* dimension, and an all-monotonic control —
   runs the real `combine_by_coords`, and asserts that whether it raises matches
   the deep model.

Exit 0 iff every observation matches. It imports only `itertools`/`random`
(standard library) and the package under change, `xarray`; nothing else
repo-specific.
