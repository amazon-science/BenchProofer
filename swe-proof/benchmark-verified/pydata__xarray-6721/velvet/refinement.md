# refinement.md — pydata__xarray-6721

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildChunkInventory` `do` block plus the deep `chunkInventory`/`mergeVar`/
`dedupeLast`/`mergePairs`/`mergePair` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the `VarDesc` R-refinement bridge and the `Variable.chunksizes` read it
depends on are checked by **G-AX**
(`axiom_check.py`). Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The chunk-inventory site — `get_chunksizes()` (`xarray/core/common.py:2026`)

Gold hunk:
```
-        if hasattr(v.data, "chunks"):
+        if hasattr(v._data, "chunks"):
```

| # | Solution.lean impl op (`buildChunkInventory`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `vars : List VarDesc` | `variables: Iterable[Variable]` arg | R | iterable of `Variable` ↔ `List VarDesc`, one-for-one in order (mapping.md §2). |
| A2 | `chunkInventory vars = vars.foldl mergeStep (Except.ok [])`: fold `mergeStep` over the variables front-to-back; the loop accumulates exactly `(vars.take i).foldl mergeStep (Except.ok [])` | the `for v in variables:` loop building `chunks` | I | the loop body is the concrete accumulation, transliterated 1:1 by G-CONF; the forward left-fold visits the variables in the repo's own iteration order, so a dimension is inserted the first time some variable advertises it and the insertion order of the resulting pairs equals the observable insertion order of the real `Frozen` mapping. |
| A3 | `mergeStep acc v` (= `mergeVar v acc`) branches on `v.chunks` (whether the descriptor advertises a layout) and NEVER on `v.accessible` | `if hasattr(v._data, "chunks")` — the **post-patch** predicate, testing for a chunk layout on the storage **descriptor** `_data` | R + I | the `Option` constructor of `VarDesc.chunks` ↔ `hasattr(v._data, "chunks")` (mapping.md §2, the R-refinement); the branch (advertising vs not) is the concrete `if` (I). The change is precisely `v.data → v._data`: the guard reads the descriptor, modeled by branching on `v.chunks` alone. |
| A3b | on the advertising leg, `mergeVar` consults `v.layoutReadable` and yields `Except.error ChunkErr.layoutUnavailable` when it is `false` | evaluating `v.chunksizes` in the loop header `for dim, c in v.chunksizes.items()` | R + I | `chunksizes` is **not** touched by `patch.diff` and is itself value-forcing: it tests `self._data` but then indexes `self.data.chunks` (mapping.md §1.1). Passing A3's descriptor guard therefore does not imply the advertised layout can be obtained, and for a non-duck descriptor it raises. `VarDesc.layoutReadable` ↔ "`v.chunksizes` completes" (mapping.md §2); propagating its failure is the concrete abort of the `for` loop's iterator (I). Measured on all four advertising descriptor kinds in mapping.md §2.1 and checked by G-AX. |
| A4 | `dedupeLast`: assemble the variable's own pairs into a per-dimension mapping — a repeated dimension keeps its FIRST position and LAST block length, never compared | the dict comprehension `{dim: c for dim, c in zip(self.dims, self.data.chunks)}` inside `Variable.chunksizes` (`variable.py:1017`) | I | dict construction over the zip, transliterated 1:1. A `Variable`'s `dims` need not be distinct, so this step is reachable and observable: `Variable(("x","x"), dask((4,),(2,2)))` reads as `{'x': (2,2)}` and raises nothing (mapping.md §1.2, §2.1). Insertion into a dict keyed by dimension ↔ overwrite-in-place on the first occurrence's position. |
| A4b | `mergePair` / `mergePairs`: a dimension shared with an EARLIER variable must agree, else `Except.error ChunkErr.inconsistent`; a new dimension is appended | `for dim, c in v.chunksizes.items(): if dim in chunks and c != chunks[dim]: raise ValueError(...); chunks[dim] = c` | I | per-(dim,block) merge with the inconsistency raise, transliterated 1:1; `chunks[dim] = c` ↔ append/overwrite, `dim in chunks and c != chunks[dim]` ↔ `lookup` mismatch. `chunks` here is the inventory built from the *preceding* variables, so the comparison is strictly between variables; the pairs iterated are `v.chunksizes.items()` — the mapping A4 assembled, not the raw zip. Measured to still raise for two variables disagreeing on a shared dimension (mapping.md §2.1, G-AX `check_layout_read_dedupes_repeated_dim` leg (d)). |
| A5 | result `Except ChunkErr (List (Int × Int))` returned | `return Frozen(chunks)` (success) / `raise ValueError` (inconsistency) / the raise out of `v.chunksizes` (`UnexpectedDataAccess` / `AttributeError` / `TypeError`) | R | `Frozen({d:c,…})` ↔ `Except.ok [(d,c),…]`; the inconsistency `ValueError` ↔ `Except.error inconsistent`; a raise out of the layout read ↔ `Except.error layoutUnavailable`, the three identified because the model records only THAT the read failed and the scan aborts identically on all three (mapping.md §2). |

Discriminating content of the change — test for a chunk layout on the storage
**descriptor** (`v._data`) instead of on the **materialized values** (`v.data`) —
lives in `mergeVar` branching on `v.chunks` and NEVER on `v.accessible`. The
pre-patch predicate `hasattr(v.data, "chunks")` forces `v.data`, which for an
inaccessible unchunked variable raises; `Solution_prepatch.lean` reproduces that
(its step emits `Except.error valuesUnavailable` when `accessible = false`) and
**fails** `out = chunkInventory vars` (G-DIFF), since the spec's `mergeVar` never
produces `valuesUnavailable`.

Note what the change does **not** do, and what A3b and A4 consequently must
carry: it does not make the whole operation value-free, and it does not make the
loop body's own read disappear. It moves the *guard* off the value view while
leaving that read (`v.chunksizes`) on it. So the modeled region divides into
three, not two: no layout advertised (passed over, values untouched — the delta,
§A above and mapping.md §3.1); a layout advertised and delivered (assembled by
A4, merged by A4b); and a layout advertised but not delivered by its own read
(`layoutUnavailable`). The third leg behaves identically before and after the
change, so it is not part of the delta — but it is inside the region
`buildChunkInventory` claims, and a model omitting it would describe a program in
which `chunksizes` reads the descriptor. That program is not the one in this
repository (mapping.md §1.1, §2.1).

For the same reason A4 and A4b must be kept apart. The read `v.chunksizes`
returns a *mapping*, so it collapses a dimension a single variable advertises
twice — first position, last block length, no comparison — while
`get_chunksizes` compares before inserting only against the dimensions earlier
variables contributed. Modelling one must-agree rule for both would describe a
program that raises on `Variable(("x","x"), dask((4,),(2,2)))`; this one returns
`{'x': (2,2)}`, identically before and after the change, and reachably from the
public API via `xr.Dataset({"a": v}).chunks` (mapping.md §1.2, §2.1).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the descriptor-vs-
values guard — is modeled **deeply** (`mergeVar` branches on `VarDesc.chunks`, the
R-refinement of `hasattr(v._data, "chunks")`), not hidden behind an axiom about
the function under change. There are **no consumed axioms** and **no deep-model
references**. The repo callees the body invokes are `hasattr` on a plain
attribute, dict insert/compare, and the `Variable.chunksizes` property; all three
are concrete and transliterated by G-CONF, the last one against the real property
rather than a stand-in for it — including its dict construction (A4) as well as
its value-forcing read (A3b), which is what makes both of those legs observable
there rather than assumed.

## C. verify(Solution) ⇒ resolved

`buildChunkInventory` verifies only if its output equals `chunkInventory vars`
(A2–A5), which decides whether each variable contributes by testing the
descriptor (`VarDesc.chunks`' constructor, the R-refinement of
`hasattr(v._data, "chunks")`) and never by testing whether the values can be
materialized (`VarDesc.accessible`) — while still failing where the advertised
layout's own read fails (`VarDesc.layoutReadable`, A3b) and still collapsing a
repeated dimension the way that read does (`dedupeLast`, A4), as the repo does. By R
(`Variable ↔ VarDesc`, `Frozen ↔ List`, `ValueError ↔ ChunkErr.inconsistent`,
raise-out-of-`chunksizes` ↔ `ChunkErr.layoutUnavailable`) the verified inventory
equals `get_chunksizes(variables)` after the gold patch on the tested inputs; by
G-AX the `VarDesc` carrier faithfully mirrors `hasattr(_data,"chunks")`,
`v.chunksizes` (including its collapse of a repeated dimension, on a duck array
and on a real `dask` array) and the value-forcing `.data` on the real `Variable`,
and the value-side observations are independent; by G-CONF the R/I transliteration
of the fold agrees with `patch.diff`'s behaviour on ≥10⁵ inputs built from **real**
`Variable` objects spanning all seven descriptor kinds (mapping.md §2.1), drawing
dimension ids with replacement so that the `layoutReadable` and `dedupeLast` legs
are reachable by the fuzzer rather than assumed away — the run reports how many
inputs advertised a repeated dimension and fails if none did.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The single
trust point (plan §1.1) is refinement fidelity (this doc + the `VarDesc` bridge,
G-CONF + G-AX); there are no axioms to trust.
