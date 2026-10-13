# mapping.md — pydata__xarray-6721

Model↔repo symbol binding, type abstraction, and callee provenance. All
file:line references are at `base_commit`
`cc183652bf6e1273e985e1c4b3cba79c896c1193`.

## Modeled function

| model.py symbol | repo symbol | repo location | role |
|---|---|---|---|
| `get_chunksizes(entries: List[Entry]) -> List[int]` | `xarray.core.common.get_chunksizes(variables)` | `xarray/core/common.py:2020-2034` | the single changed function: inspects a collection of variables and reports, per dimension, the chunk (block) lengths of the chunked variables. |

The gold change is one line inside this function (`xarray/core/common.py:2026`):
`if hasattr(v.data, "chunks"):` → `if hasattr(v._data, "chunks"):`.

## Type abstraction

| repo reality | model as | bijection |
|---|---|---|
| `variables: Iterable[Variable]` | `entries: List[Entry]` | one `Variable` ↔ one `Entry`; iteration order preserved. |
| a `Variable` `v` | `Entry` with fields `block_backed`, `forces_load`, `axis`, `length` | see below. |
| `getattr(v._data, "chunks", None) is not None`, i.e. the UNDERLYING store `v._data` advertises a `chunks` attribute | `e.block_backed: bool` | `v._data` is the raw, possibly lazily-backed array stored on the variable (`Variable.__slots__` includes `_data`, `xarray/core/variable.py:285`; set in `__init__`, line 307). A backend array (e.g. a `LazilyIndexedArray`) exposes `chunks` only when it is a dask array. |
| accessing `v.data` forces a load when `v._data` is not a duck array | `e.forces_load: bool` | `Variable.data` (`xarray/core/variable.py:337-342`) returns `self._data` if it is a duck array, **else `self.values`** — and `Variable.values` (`:513-515`) calls `_as_array_or_item(self._data)` → `np.asarray(...)`, materialising the whole payload. A lazily-backed, non-duck store (the regression case) has `forces_load == True`; an already-in-memory / duck array has `forces_load == False`. |
| dimension key carried by the variable | `e.axis: int` | one representative dimension per variable (abstracted to an int label). The real function aggregates `v.chunksizes.items()` over all dims; the model carries one labelled axis per entry — sufficient to pin the aggregation behaviour and the per-entry skip/contribute decision. |
| chunk (block) length along that dim | `e.length: int` | the value `c` in `v.chunksizes` (`xarray/core/variable.py:1002-1020`), itself read from `self.data.chunks` only when `hasattr(self._data, "chunks")`. |
| `Frozen(chunks)` returned mapping | flat `List[int]` of `(axis, length)` pairs + a trailing loads tally | `(Result()[2*i], Result()[2*i+1])` is entry i's contribution: `(-1,-1)` = skipped (no block structure), else `(axis, length)`; `Result()[2*len(entries)]` is the total materialisations forced (must be 0). The `Frozen`/`dict` wrapper is identity on content (mapping bijection); membership/inconsistency handling is orthogonal to the tested regression. |

## Side-effect modeling (the heart of the spec)

The bug is a data-flow defect, not a value defect: both `v.data` and `v._data`
let `hasattr(..., "chunks")` answer correctly for an in-memory or dask-backed
variable, but `v.data` additionally **materialises** a lazily-backed,
non-dask variable (pulling its whole payload into memory). The model makes that
side effect observable:

- `inspect_underlying(e)` (model of `hasattr(v._data, "chunks")`) returns the
  block status from `e.block_backed` and forces `0` loads — `v._data` is read
  in place.
- `inspect_materialised(e)` (model of `hasattr(v.data, "chunks")`) forces
  `block_load_cost(e)` loads (`1` iff `e.forces_load`); its block status is
  `e.block_backed and not e.forces_load`, because once a lazy store is
  materialised it is a plain in-memory array advertising no `chunks`.

`get_chunksizes`'s postcondition pins (a) that every entry is still
`payload_intact` — no variable was materialised — via an UNFORGEABLE, CONSUMABLE
capability token (below), and (b) the per-entry contribution from the UNDERLYING
block status `e.block_backed`. The pre-patch skeleton, inspecting via
`inspect_materialised`, consumes the token (and forces a load) and so cannot
re-establish clause (a) (and, for a chunked-but-lazy variable, violates the
block-status clause too).

## The `payload_intact` capability token (the unforgeable regression sensor)

The bug is a SIDE EFFECT with no value footprint on the F2P regime
(`block_backed=False, forces_load=True`): both `v.data` and `v._data` answer the
same block status (`False`), so a bare value postcondition cannot tell the buggy
and fixed code apart, and a trailing `loads == 0` slot in the postcondition is an
echoable constant (an impl can do the buggy load and then write `0`). The
discriminator is therefore carried by an abstract `@ContractOnly @Predicate
payload_intact(e)` — a capability token with no body (Nagini rejects any `Fold`,
so it can never be fabricated, and once consumed it is gone for good):

- `inspect_underlying` (`v._data`) **requires and returns** `payload_intact(e)`
  — it reads in place, so the entry stays intact.
- `inspect_materialised` (`v.data`) **requires but does NOT return**
  `payload_intact(e)` — obtaining the materialised payload pulls it into memory,
  consuming intactness.
- `block_lengths_by_axis` requires `payload_intact` for every entry on entry and
  **re-establishes it for every entry in its postcondition**.

So a verifying implementation must keep every entry intact end-to-end, which is
possible only if it never materialises any entry — i.e. it must use the
underlying view. An impl that calls `inspect_materialised` on any entry, even one
that also reads the underlying store for the correct value and writes a literal
`0` into the trailing load slot, permanently loses that entry's token and cannot
discharge the postcondition (machine-confirmed in both call orderings). The token
is a proof-only construct with no runtime footprint (it is not, and cannot be,
checked by `axiom_check.py`; only the value/forced-load contracts are).

## FAIL_TO_PASS regression evidence

`xarray/tests/test_dataset.py::TestDataset::test_chunks_does_not_load_data`
(added by `test_patch`): builds a dataset over an `InaccessibleVariableDataStore`
whose variables wrap `LazilyIndexedArray(InaccessibleArray(...))`
(`xarray/tests/test_dataset.py:202-217`; `InaccessibleArray.__getitem__` raises
`UnexpectedDataAccess`, `xarray/tests/__init__.py:137-142`). Such a variable has
`block_backed == False` (no `chunks`) and `forces_load == True` (not a duck
array; `v.data` would call `np.asarray` → `__getitem__` → raise). The test
asserts `ds.chunks == {}` succeeds (i.e. no load). Pre-patch: `hasattr(v.data,
"chunks")` triggers the load → `UnexpectedDataAccess`. Post-patch: `hasattr(
v._data, "chunks")` reads the raw store → `False`, no load, `{}` returned.

## Callee provenance / axioms

The two payload-view reads are unchanged library operations Nagini cannot
express, so they are modelled as `@ContractOnly` callees whose contracts the
proof consumes (**A-consumed**): `inspect_underlying` (`hasattr(v._data,
"chunks")`, provenance `xarray/core/variable.py:285,307,999`) and
`inspect_materialised` (`hasattr(v.data, "chunks")`, provenance
`xarray/core/variable.py:337-342,513-515`). Their runtime-observable contracts
(block status + forced-load count) are validated against the real semantics of
`Variable._data` / `Variable.data` / `Variable.values` by `axiom_check.py`
(G-AX). The abstract `payload_intact` capability token (above) is a proof-only
construct with no runtime footprint. No external flag dependency.
