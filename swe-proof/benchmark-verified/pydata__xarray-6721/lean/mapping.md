# mapping.md — pydata__xarray-6721

## Instance
- repo: pydata/xarray @ `cc183652bf6e1273e985e1c4b3cba79c896c1193`
- modeled function: `get_chunksizes(variables)` in `xarray/core/common.py`
  (lines 2020–2034 @ base_commit; the changed line is the `hasattr(...)` guard
  at line 2026 of the hunk).

## Symbol binding (file:line @ base_commit)
| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_getChunksizes` / `problem_spec_getChunksizes` / `correct_getChunksizes` | `get_chunksizes(variables)` | `xarray/core/common.py:2020` |
| `XVar` (structure) | one `Variable` element of `variables` | `xarray/core/variable.py` |
| `XVar.hasChunks` | `hasattr(v._data, "chunks")` (truthy iff `_data` is a chunked / dask array) | `xarray/core/common.py:2026` (POST-patch guard); `Variable._data` |
| `XVar.chunksizes` | `v.chunksizes` (`Mapping[dim, tuple[int,...]]`; non-empty only for chunked data) | `xarray/core/variable.py:1002` |
| `XVar.isDuckArray` | `is_duck_array(v._data)` — whether `.data` returns `_data` directly without materializing | `xarray/core/variable.py:337` (`Variable.data`) |
| `XVar.materializeRaises` | whether forcing `v.values` (`_as_array_or_item(self._data)`) raises (e.g. an inaccessible backend store) | `xarray/core/variable.py:513` (`Variable.values`) |
| `Except.error ()` | a raised exception out of `get_chunksizes` (either the inconsistent-chunks `ValueError`, or a materialization failure on the pre-patch path) | `common.py:2029` |
| `Except.ok m`  | `Frozen(chunks)` — the accumulated dim→block-lengths mapping | `common.py:2034` |

## The real code (base_commit)
```python
def get_chunksizes(variables):
    chunks: dict[Any, tuple[int, ...]] = {}
    for v in variables:
        if hasattr(v.data, "chunks"):        # base/buggy. POST-patch: v._data
            for dim, c in v.chunksizes.items():
                if dim in chunks and c != chunks[dim]:
                    raise ValueError(
                        f"Object has inconsistent chunks along dimension {dim}. "
                        "This can be fixed by calling unify_chunks()."
                    )
                chunks[dim] = c
    return Frozen(chunks)
```
`Variable.data` (variable.py:337):
```python
@property
def data(self):
    if is_duck_array(self._data):
        return self._data
    else:
        return self.values        # forces materialization → may raise / load all data
```

## Bug semantics (cold-derived from problem_statement + source)
The guard inspects whether each variable's underlying array advertises a
`chunks` attribute. The **value** of `hasattr(..., "chunks")` is the same whether
read off `v.data` or `v._data` for every variable (a chunks-bearing array is
always a duck array, so `v.data` returns `_data` unchanged; a non-chunked
in-memory duck array yields `False` either way). The ONLY difference is a *side
effect*: for a variable whose `_data` is **not** a duck array (a lazy
backend handle), `v.data` forces `self.values`, materializing the whole array.
When the backing store is inaccessible this materialization **raises**, so the
whole `get_chunksizes` call raises instead of returning the (correct) chunk map.
The fix reads `v._data`, inspecting the handle without materializing.

Distilled discriminating condition (pre-patch raises, post-patch does not):
a variable with `¬hasChunks ∧ ¬isDuckArray ∧ materializeRaises`.

## Lean ↔ Python type bijection (G-CONF / G-AX)
| Python | Lean |
|---|---|
| `Variable` (only touched observables) | `XVar { hasChunks, chunksizes, isDuckArray, materializeRaises }` |
| `v.chunksizes : Mapping[str, tuple[int,...]]` | `chunksizes : List (String × List Nat)` (insertion order) |
| `dict[str, tuple[int,...]]` result | `List (String × List Nat)` (Python-dict insertion semantics; compared order-insensitively by G-CONF) |
| `raise` | `Except.error ()` |
| `Frozen(chunks)` | `Except.ok chunks` |

`hasChunks`, `isDuckArray`, `materializeRaises` are **R** (type refinements of
observable properties of a `Variable`), supplied as inputs — not callees invoked
inside the modeled function, so there is no consumed axiom and no A-reference.
`chunksizes` is **R**. The merge / inconsistency-raise is modeled **deeply** (I).

## Callee provenance / flag deps
- No unchanged callee is invoked *inside* the merge that needs an axiom: the
  per-dimension accumulation, the `dim in chunks and c != chunks[dim]` check, and
  the `chunks[dim] = c` write are all spelled out (I).
- `hasChunks` is flag-free (it is just `hasattr(_data, "chunks")`).

## G-CONF fuzz seed (pinned)
`SEED = 6721` (also recorded in conformance_check.py and meta.json).
