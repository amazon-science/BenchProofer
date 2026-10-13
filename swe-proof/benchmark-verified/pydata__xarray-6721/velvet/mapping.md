# mapping.md — pydata__xarray-6721

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = cc183652bf6e1273e985e1c4b3cba79c896c1193`, states the type
abstraction (the bijection G-CONF and the G-AX R-bridge use to translate
Lean↔Python values), and records the (no-)axiom provenance.

Repo file under change: `xarray/core/common.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildChunkInventory (vars : List VarDesc)` | `get_chunksizes(variables)` — `xarray/core/common.py:2020` (body line 2026) | the modeled changed function (assembles a dataset's chunk inventory) |
| `chunkInventory` *(deep model, pure)* | the `for v in variables: …` accumulation in `get_chunksizes`' body | pure spec: the merged per-dimension block layout over all variables, folded left-to-right (`vars.foldl mergeStep`) in the repo's own iteration order, so insertion order of the (dim, block) pairs matches the real assembled mapping |
| `mergeStep` / `mergeVar` / `mergePairs` / `mergePair` *(deep model, pure)* | the per-variable `if hasattr(…, "chunks"): for dim, c in v.chunksizes.items(): … chunks[dim] = c` body | pure spec: fold one variable's advertised layout into the running inventory, failing on a shared-dimension disagreement **between variables** (`chunks` is the inventory built from the earlier ones, so this is the `dim in chunks and c != chunks[dim]` test) and on a layout read that does not deliver. Note the loop iterates `v.chunksizes.items()` — the read's *mapping*, already collapsed by `dedupeLast` — not the raw pair sequence |
| `VarDesc.chunks` *(R-refinement)* | the guard `hasattr(v._data, "chunks")` (`common.py:2026`) for WHICH constructor, and `list(zip(v.dims, v.data.chunks))` — the pairs the read `v.chunksizes` (`xarray/core/variable.py:1017`) is handed — for the payload | whether the variable's cheap storage **descriptor** (`_data`) advertises a chunk layout, and which (dimension, block-length) pairs the read of it is handed. Those pairs need NOT name distinct dimensions (§1.2) |
| `dedupeLast` *(deep model, pure)* | the dict comprehension `{dim: c for dim, c in zip(self.dims, self.data.chunks)}` inside `Variable.chunksizes` (`variable.py:1017`) | pure spec: assemble one variable's pairs into the per-dimension mapping its own read yields — a repeated dimension keeps its FIRST position and its LAST block length (§1.2) |
| `VarDesc.layoutReadable` *(R-refinement)* | whether evaluating `v.chunksizes` (`variable.py:1002-1020`) completes rather than raising | whether the layout the descriptor advertises is actually delivered by its own read. The read tests `self._data` but then indexes `self.data.chunks` — the **value view** — so it can fail |
| `VarDesc.accessible` *(R-refinement)* | whether `v.data` (`xarray/core/variable.py:338`) can materialize the values without raising | an orthogonal observation of the variable: what the pre-image path consulted. Never consulted by the current behaviour |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `hasattr(v.data, "chunks")` (`common.py:2026`), where
`v.data` (`variable.py:337-342`) returns `self._data` for a duck array else
`self.values`, the latter forcing materialization of the values.

### 1.1 The two reads are different reads — and only one is guarded
The change swaps the **guard** from the value view to the descriptor. It does not
touch `Variable.chunksizes`, which the loop body still calls, and which is
itself value-forcing:

```python
# xarray/core/variable.py  (unchanged by patch.diff)
@property
def chunksizes(self):
    if hasattr(self._data, "chunks"):                                  # descriptor
        return Frozen({dim: c for dim, c in zip(self.dims, self.data.chunks)})
    else:                                                              #  ^^^^ VALUE view
        return {}
```

So passing the descriptor guard does **not** imply the layout can be obtained:
for a variable that advertises `chunks` but is not a duck array, `self.data`
falls through to `self.values` and materializes. `VarDesc.layoutReadable` is the
field that denotes this second, unguarded read; without it the model would
describe a program in which `chunksizes` reads the descriptor, which is not the
program in this repository. Verified empirically in the instance image — see
§2.1.

### 1.2 The read yields a MAPPING, so a repeated dimension is overwritten
The comprehension above builds a **dict keyed by dimension**. A `Variable`'s
`dims` are not required to be distinct — `Variable(("x", "x"), arr)` is an
ordinary variable, reachable straight from the public API — and when a dimension
repeats, the comprehension does not compare the two block lengths: it overwrites,
keeping the **first occurrence's position** and the **last occurrence's value**.
Nothing is raised. Measured in the instance image, identically before and after
`patch.diff`:

```
v = Variable(("x","x"), da.from_array(np.zeros((4,4)), chunks=((4,),(2,2))))
v.dims                            ('x', 'x')
v._data.chunks                    ((4,), (2, 2))
list(zip(v.dims, v.data.chunks))  [('x', (4,)), ('x', (2, 2))]   <- the pairs the read is handed
v.chunksizes                      {'x': (2, 2)}                  <- overwritten, no raise
get_chunksizes([v])               {'x': (2, 2)}
xr.Dataset({"a": v}).chunks       {'x': (2, 2)}                  <- reachable publicly

v3 = Variable(("x","y","x"), duck(chunks=((4,),(3,),(2,))))
v3.chunksizes                     {'x': (2,), 'y': (3,)}         <- first position, last value
```

The must-agree rule the inventory applies therefore has a counterpart **only
between different variables**, where `get_chunksizes` genuinely does compare
before inserting (`if dim in chunks and c != chunks[dim]: raise`) — measured to
still raise for two variables disagreeing on a shared dimension. `dedupeLast`
is the field of the model that denotes the within-variable half; without it the
model would describe a program that raises on a repeated dimension, which is not
the program in this repository. Checked by G-AX
(`check_layout_read_dedupes_repeated_dim`, on a duck array **and** on a real
`dask` array) and reached by G-CONF on 41 538 of its 100 026 inputs.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table the G-AX R-bridge and G-CONF (§4.1) use to translate values
between the Lean value domain and the Python repo types. A wrong entry surfaces
as a spurious G-CONF disagreement (the falsifiability plan §4 relies on).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `variables` (an iterable of `Variable`) | `List VarDesc` | ordered one-for-one; `len(variables)` ↔ `vars.length`; iteration order ↔ list order |
| does the descriptor advertise a layout — `hasattr(v._data, "chunks")` — and, if so, the pairs the read `v.chunksizes` is handed | `VarDesc.chunks : Option (List (Int × Int))` | attribute **absent** ↔ `none`; attribute **present** ↔ `some pairs`, where `pairs = list(zip(v.dims, v.data.chunks))` — each Hashable dimension name interned to a distinct `Int`, each block-length tuple interned to a distinct `Int` (see below). The list is the **pre-mapping** pair sequence, so it may name one dimension twice (§1.2); `dedupeLast` assembles it into the mapping the read returns. Which constructor it is is ALWAYS observable: the `hasattr` test reads the descriptor and never materializes values. Note `chunks` **present but `None`** is `some`, not `none`: it passes the guard and then fails the read (`layoutReadable = false`), which is what the repo does. |
| the dict comprehension in `Variable.chunksizes` collapsing repeated dimensions | `dedupeLast : List (Int × Int) → List (Int × Int)` | a dimension appearing more than once in the pair sequence keeps the position of its FIRST occurrence and the block length of its LAST; the two lengths are never compared and nothing is raised (§1.2). On a pair sequence whose dimensions are already distinct this is the identity, so it is invisible on those inputs and load-bearing only on the repeated ones. |
| does `v.chunksizes` complete? | `VarDesc.layoutReadable : Bool` | completes ↔ `true`; raises ↔ `false`. Decomposes as `is_duck_array(v._data) ∧ v._data.chunks is iterable`: a duck array's `v.data` **is** `v._data`, so the read delivers; otherwise `v.data` materializes and the read fails — `UnexpectedDataAccess` over a store that refuses element access, `AttributeError` when the materialized values carry no chunk attribute, `TypeError` when the advertised attribute is not iterable (`chunks = None`). Meaningful only on the `some` leg; on the `none` leg the read returns `{}` without forcing values, so the field is unconstrained there and provably cannot reach the outcome (`mergeVar_unadvertised`). |
| can `v.data` be forced into memory without raising? | `VarDesc.accessible : Bool` | a normal/duck array ↔ `true`; a lazily-indexed wrapper over an inaccessible store (`InaccessibleArray`, raises `UnexpectedDataAccess` on `__getitem__`) ↔ `false`. Independent of `layoutReadable` in both directions (G-AX `check_layout_read_independent_of_accessibility`), so neither field is derivable from the other. The current behaviour never reads it. |
| the assembled `Frozen(chunks)` mapping | `List (Int × Int)` (insertion-ordered (dim, block) pairs) | `Frozen({d: c, …})` ↔ `[(d, c), …]`; membership/value lookup ↔ `List.lookup`; an empty mapping ↔ `[]` |
| `raise ValueError("inconsistent chunks …")` | `Except.error ChunkErr.inconsistent` | raised iff two **different** variables that both advertise a layout disagree on a shared dimension. A single variable advertising one dimension twice with different block lengths does NOT raise — that is resolved by `dedupeLast` (§1.2) — so this row's `iff` is between variables, not within one. |
| a raise out of `v.chunksizes` — `UnexpectedDataAccess` / `AttributeError` / `TypeError` as above | `Except.error ChunkErr.layoutUnavailable` | the layout a descriptor advertised was not delivered by its own read. These three are identified because the model records only THAT the read failed, and the scan aborts identically on all three. |
| `UnexpectedDataAccess` from forcing values in the **guard** | `Except.error ChunkErr.valuesUnavailable` | the failure the change removes; appears only on the pre-image skeleton's `accessible = false` leg |

Lean `List` indexing is total and sound; the carrier is `List VarDesc` because
the operation is a left-to-right accumulation over the variables.

**Interning of block lengths.** A repo block length is a `tuple[int, ...]`
(e.g. `(2, 2)`), not an `int`. The only operation the modeled body performs on
one is an equality comparison (`if dim in chunks and c != chunks[dim]`), so the
faithful encoding is any injection from block-length tuples to `Int`; equality of
the `Int`s then holds exactly when the tuples are equal. G-CONF instantiates that
injection concretely with single-block layouts, `(b,) ↔ b`, which is injective on
the fuzzed domain.

**Binding the payload to the zip.** `VarDesc.chunks`' payload is the pair
sequence the read is handed, `zip(v.dims, v.data.chunks)`, not the raw tuple the
descriptor carries. This matters when a descriptor advertises fewer block tuples
than the variable has dimensions: the real `zip` truncates, and it is the
truncated pair sequence the repo assembles. Binding to the zip absorbs that, so
the carrier needs no separate arity side-condition (G-AX
`check_layout_binding_is_the_zip`).

**Why the payload is the zip and not the mapping.** The read's *result*,
`v.chunksizes`, is a mapping, so binding the payload to `list(v.chunksizes
.items())` would also be sound — and would make repeated-dimension payloads
unreachable rather than merely deduped. The zip is bound instead because it is
the earlier, more primitive observation: it needs no case analysis to compute
from the descriptor, and it keeps `dedupeLast` — the collapsing step the repo
actually performs — *inside* the model where it is visible, checkable and
mutable, rather than hidden in the abstraction function. The consequence is that
the model must agree with the repo on a payload naming one dimension twice, and
it does (§1.2); under the alternative binding it would merely never be asked.
Both bindings now yield the same answer on every reachable variable, so the
choice is no longer load-bearing — which is the point.

**No claim of distinct dimensions.** An earlier version of this document asserted
that a variable's pairs come from zipping `v.dims`, "distinct by construction",
and concluded that a payload repeating a dimension was unreachable. That is
**false**: `Variable(("x", "x"), arr)` is an ordinary variable and
`xr.Dataset({"a": v}).chunks` reaches it from the public API (§1.2). No such
claim is made here, and none is needed: `dedupeLast` gives the repeated-dimension
payloads the repo's own answer, so they are described rather than excused.

### 2.1 Measured, in the instance image (xarray 2022.6.0rc1.dev17+gcc183652b, numpy 1.23.0)
Each row is a single `Variable`; the last two columns are `get_chunksizes([v])`
before and after `patch.diff`. Rows 1-3 are the ones the earlier model described
wrongly: it put them all on the `ok` leg.

| `v._data` | `hasattr(_data,"chunks")` | `is_duck_array(_data)` | base | patched |
|---|---|---|---|---|
| `ExplicitlyIndexed` + `chunks`, over an inaccessible store | True | False | `UnexpectedDataAccess` | `UnexpectedDataAccess` |
| `ExplicitlyIndexed` + `chunks`, over `np.zeros` | True | False | `{}` | `AttributeError: 'numpy.ndarray' object has no attribute 'chunks'` |
| duck array with `chunks = None` | True | True | `TypeError: 'NoneType' object is not iterable` | `TypeError: …` |
| duck array with `chunks = ((4,),)` | True | True | `{'x': (4,)}` | `{'x': (4,)}` |
| `np.zeros` | False | True | `{}` | `{}` |
| `LazilyIndexedArray(InaccessibleArray(...))` | False | False | `UnexpectedDataAccess` | `{}` |

The first three diverge from the earlier model **identically before and after**
the change, so they are not part of the delta this bundle is about; they are
simply region the model claimed and did not describe. `VarDesc.layoutReadable`
adds them to the described region. The last row is the delta (§3.1).

Repeated dimension names, measured the same way — each row one `Variable`, the
last two columns `get_chunksizes([v])` before and after `patch.diff`:

| `v.dims` | `v._data.chunks` | pairs the read is handed | base | patched |
|---|---|---|---|---|
| `('x','x')` | `((4,), (2,2))` real dask | `[('x',(4,)), ('x',(2,2))]` | `{'x': (2, 2)}` | `{'x': (2, 2)}` |
| `('x','x')` | `((4,), (2,2))` duck | `[('x',(4,)), ('x',(2,2))]` | `{'x': (2, 2)}` | `{'x': (2, 2)}` |
| `('x','x')` | `((4,), (2,))` duck | `[('x',(4,)), ('x',(2,))]` | `{'x': (2,)}` | `{'x': (2,)}` |
| `('x','y','x')` | `((4,),(3,),(2,))` duck | `[('x',(4,)),('y',(3,)),('x',(2,))]` | `{'x': (2,), 'y': (3,)}` | `{'x': (2,), 'y': (3,)}` |
| two variables, `('x',)` each | `((4,),)` and `((2,),)` | — | `ValueError` | `ValueError` |

Identical on both sides again, so this too is unmodelled region rather than
delta: the earlier model answered `inconsistent` on rows 1-4 where the repo
answers with the overwritten mapping and raises nothing. `dedupeLast` adds them
to the described region; row 5 confirms the between-variable rule the model keeps
is not thereby weakened.

## 3. Callee provenance (kind-A) — NONE

This bundle consumes **no axioms** and references **no deep-model callee**. The
three facts the inventory consults about each variable are abstracted as the
input fields of `VarDesc`:

- **`VarDesc.chunks`** ⟵ `hasattr(v._data, "chunks")` for the constructor,
  `zip(v.dims, v.data.chunks)` for the payload — the pair sequence the read is
  handed, which may name one dimension twice (§1.2). Testing whether a layout is
  advertised is a pure attribute read on the storage **descriptor**; it never
  materializes the values. Modeled as concrete input data, not an axiom.
- **`VarDesc.layoutReadable`** ⟵ whether `v.chunksizes` completes. Consulted only
  where a layout is advertised. Modeled as concrete input data, not an axiom;
  §1.1 gives the repo source that makes it a genuinely separate observation and
  §2.1 the measurements.
- **`VarDesc.accessible`** ⟵ whether `v.data` raises. The current behaviour does
  not consult this; it is carried as an orthogonal observation so the pre-image
  skeleton (which forced `v.data` in the guard) can be written in the twin.

`mergeVar`/`dedupeLast`/`mergePairs`/`mergePair`/`chunkInventory` are the body of
`get_chunksizes` — together with the `Variable.chunksizes` read it calls (§1.1,
§1.2) — modeled **deeply** in the `pure` region; there is no opaque contract left
symbolic. Soundness of the `VarDesc` R-refinement is checked by `axiom_check.py`
against the real `Variable` (`_data.chunks` vs `v.chunksizes` vs the value-forcing
`.data`, and the read's collapsing of a repeated dimension); behavioural fidelity
of the deep fold to `patch.diff` is checked by `conformance_check.py` (G-CONF),
which builds **real** `xarray.core.variable.Variable` objects of all seven
descriptor kinds in §2.1 — not stand-ins, and including a real `dask` array — so
that the `layoutReadable` and `dedupeLast` legs are actually reachable by the
fuzzer rather than provided for and never visited.

### 3.1 The discriminating behaviour (why the F2P test changes)
The F2P test `test_chunks_does_not_load_data` builds a store whose non-index
variables wrap an `InaccessibleArray` (raises on any element access) inside a
`LazilyIndexedArray`, then asserts `ds.chunks == {}`. None of those variables
advertise a `chunks` layout (`VarDesc.chunks = none`), and none can be
materialized (`VarDesc.accessible = false`); `layoutReadable` is unconstrained
because on that leg no read is performed. The current behaviour tests the
descriptor only (`mergeVar` consults `v.chunks`), passes every variable over, and
returns the empty inventory. The pre-image behaviour forced `v.data` to test
`hasattr(v.data, "chunks")`, materializing the values and raising
`UnexpectedDataAccess` — exactly the `valuesUnavailable` leg the prepatch
diverges on (G-DIFF).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`6721`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `chunkInventory`/`mergeVar`/`dedupeLast`/`mergePairs`/`mergePair`
(all R/I ops, no A-tagged callee) to Python and diffs against the real patched
`get_chunksizes` over the bijection above. Dimension ids are drawn **with
replacement** from a three-element pool, so a single variable can advertise the
same dimension twice; the run reports how many inputs did, and fails if none did.
The real-`dask` kind is used only in the boundary block, so the random stream —
and therefore the pinned-seed verdict — does not depend on whether `dask` imports.
