# mapping.md — pydata__xarray-4094

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a64cf2d5476e7bbda099b34c40b7be1880dbd39a`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `xarray/core/dataarray.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `to_unstacked(n, data, resid)` | `DataArray.to_unstacked_dataset(self, dim, level=0)` — `xarray/core/dataarray.py:1901` (body lines 1961-1967) | the modeled changed function (the stacked-collection reconstruction / inverse of `to_stacked_array`) |
| `carried(discard, position)` *(axiom — A-consumed)* | `DataArray.sel(..., drop=...).squeeze(drop=True)` — `xarray/core/dataarray.py:1068` (sel) / `xarray/core/common.py:343` (squeeze) | unchanged callees: the per-member label selection and size-one-axis collapse. Gives the annotation value a slice carries as a function of `drop` |
| `shared_value()` *(axiom — A-consumed)* | the absence of a distinguishing residual coordinate on a `drop=True` slice (a single common state across all members) | unchanged callee behaviour: with `drop=True` the residual coordinate is dropped, so every slice carries the same (no-distinguishing-annotation) state |
| `assemble(slices, resid, discard)` *(axiom — A-consumed)* | `Dataset(data_dict)` constructor / merge — `xarray/core/dataset.py` (`Dataset.__init__` → `merge_*`) | unchanged callee: combines the per-member slices into one collection; rejected with `MergeError` on a conflicting shared coordinate; grants the `combined_collection` token on its output |
| `combined_collection(collection, positions)` *(axiom — A-consumed; abstract predicate token, keyed by the output OBJECT reference)* | the **identity** of `Dataset(data_dict)`'s output — `xarray/core/dataarray.py:1967` `return Dataset(data_dict)` | unchanged callee output: the reconstruction's only producer of the unstacked collection is the `Dataset` merge; the abstract token is held by the merge's output object itself (reference-keyed, not value-keyed), so "the result came through the merge" — the merge can neither be bypassed nor laundered by returning a value-equal object built elsewhere |
| `carried_seq(discard, positions)` | the element-wise annotation list the slices carry over the members' positions | pure spec fold |
| `all_equal(xs)` | the merge-compatibility check inside the `Dataset` constructor (a shared-name coordinate must carry one common value, else `MergeError`) | pure spec predicate |
| `distinct_residuals(resid)` | the single-sample-dim regression case: variables sit at distinct stacked positions (the residual `y` coordinate value differs per variable) | pure spec predicate |
| `lemma_carried_len`, `lemma_carried_all_equal` | proof-only induction lemmas over the front-recursive `carried_seq` (no repo counterpart) | ghost lemmas |

The changed line (`xarray/core/dataarray.py:1964`):
```
- data_dict[k] = self.sel({variable_dim: k}).squeeze(drop=True)
+ data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the stacked `DataArray` `self` (a MultiIndex `dim` over (variable, position) pairs, single sample axis) | `n` members `0..n-1`, with `data[k]` the value carried by member `k` and `resid[k]` the residual position-coordinate value paired with member `k` | member identifier `k` ↔ the variable label `variables[k]`; the residual position coordinate value ↔ `resid[k]`; the per-member data slice value ↔ `data[k]` (one `int` per member — the per-member data width is incidental to the coordinate-merge bug) |
| `self.sel({variable_dim: k}, drop=D).squeeze(drop=True)` | a slice whose carried annotation is `carried(D, resid[k])` and whose value is `data[k]` | the `drop` argument `D` ↔ the `discard` parameter; the annotation the slice carries ↔ `carried(D, resid[k])` (its own position `resid[k]` when `D=False`; the single `shared_value()` when `D=True`) |
| `data_dict` (dict variable→slice) + `Dataset(data_dict)` (the assembled collection) | the result `List[int]` of recovered per-member values, returned by `assemble` | a successful merge ↔ a normally-returning `assemble`; a `MergeError` ↔ the violated `assemble` precondition `all_equal(carried_seq(discard, resid))` (the slices' carried annotations disagree) |

The per-member data is one `int`: the F2P regression
(`test_to_stacked_array_to_unstacked_dataset`, single-dim case) fails because the
reconstruction RAISES `MergeError`, an error wholly determined by the coordinate
set the selection leaves behind — independent of the numeric data width. The
roundtrip identity `recovered == data` is modeled as `ToSeq(Result()) == ToSeq(data)`.

**Soundness of the `assemble` contract (the re-spec's key strengthening).** The
guard `assemble` checks is `all_equal(carried_seq(discard, resid))` over the
SAME `discard` that shapes the slices AND the members' real positions `resid`,
which are required to be `distinct_residuals`. This pins the merge-compatibility
to the actual selection: no implementation can select under one `drop` and have
the merge judged under another, and no implementation can fabricate an all-equal
position list (that violates the `distinct_residuals` precondition). The single
verifying choice is `discard=True` (= `drop=True`, the gold). See refinement.md.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `carried(discard, position)` + `shared_value()` ↔ `DataArray.sel(..., drop=...).squeeze(drop=True)` (A-consumed)
**Callee:** `DataArray.sel(indexers, drop=drop)` (`xarray/core/dataarray.py:1068`,
docstring: *"If `drop=True`, drop coordinates variables in `indexers` instead of
making them scalar."*) followed by `.squeeze(drop=True)` (`xarray/core/common.py:343`,
which drops only **size-one dimensions**). Selecting one variable label along the
stacked MultiIndex level turns the stacked position coordinate `y` into a
**scalar coordinate** on the slice; `.squeeze(drop=True)` removes the size-one
*dimension* but NOT that scalar *coordinate*. Hence with `drop=False` the slice
carries its own position label (`carried(False, position) == position`); with
`drop=True` the position coordinate is dropped, so every slice carries no
distinguishing position annotation — modeled as the single `shared_value()`
(`carried(True, position) == shared_value()`).

The axioms are the weakest the proof needs (two equivalences). They are sound
only for the `.squeeze(drop=True)` configuration the method uses;
`axiom_check.py` exercises exactly that. Docs:
https://docs.xarray.dev/en/stable/generated/xarray.DataArray.sel.html

### 3.2 `assemble(slices, resid, discard)` ↔ `Dataset(data_dict)` (A-consumed)
**Callee:** the `Dataset` constructor (`xarray/core/dataset.py`,
`Dataset.__init__` → the variable/coordinate merge). Constructing a `Dataset`
from several DataArrays merges their coordinates; a coordinate that appears under
the **same name** on two members with **different values** is a conflict and is
rejected with `MergeError: conflicting values for variable 'y' ...` (the exact
error in the issue). When no kept coordinate conflicts, the construction succeeds
and each member's data is preserved verbatim. Thus `assemble` succeeds (and
returns the data verbatim) iff `all_equal(carried_seq(discard, resid))`: the
annotations the slices carry under the selection `discard`, over the members'
positions, must agree.

**Soundness check (G-AX, validated IN THE PINNED CONTAINER, rc=0):**
`axiom_check.py` builds the single-position-axis stacked array from the issue's
MCVE and checks, against the real **unchanged** callees only (it does NOT call
the function under change `to_unstacked_dataset`):
- with `drop=False` the residual position coordinate `y` survives onto each
  squeezed slice carrying a **distinct** per-member value (`carried(False, .)`);
- with `drop=True` `y` does **not** survive (`carried(True, .)` — no
  distinguishing annotation);
- `Dataset(data_dict)` is **rejected** (`MergeError`) for the `drop=False` slices
  (conflicting `y`) and **succeeds + recovers the original Dataset verbatim** for
  the `drop=True` slices.
It models ONLY the residual `y` (NOT the selection level `variable`, whose
survival onto the squeezed slice is xarray-version-dependent — the previous
version of this check over-scoped to `variable` and failed in-container). Imports
only `xarray`/`numpy`/`pandas`; exit 0 iff sound. Confirmed rc=0 in the
pinned eval image `swebench/sweb.eval.x86_64.pydata_1776_xarray-4094` (re-audit).

### 3.3 `combined_collection(members, positions)` ↔ `return Dataset(data_dict)` (A-consumed; abstract token)
**Callee/output:** the reconstruction's return value is `Dataset(data_dict)`
(`xarray/core/dataarray.py:1967`) — the **only** producer of the unstacked
collection in the function body. `combined_collection` is an abstract
`@ContractOnly @Predicate` *capability token* (no body) whose first argument is
the output **object itself** (`List[int]` reference), NOT a value sequence:
`assemble` (= the `Dataset` merge) grants it on its own output object via its
postcondition, and Nagini forbids any implementation from fabricating it (it
rejects `Fold` of an abstract predicate, and an object not produced by
`assemble` lacks the token's permission — including a value-equal object built
elsewhere, since the token is keyed by reference). `to_unstacked`'s
postcondition requires the token on `Result()`, so a verifying reconstruction
MUST return the merge's own output — the merge (where the `MergeError` bug
lives) can neither be bypassed nor laundered through a value-identical
substitute. This is a capability, not an answer-key oracle: it carries no value
the implementation can echo back.

**Reference-keying rationale (post-audit strengthening).** An earlier revision
keyed the token by value (`ToSeq(Result())`). A Viper predicate is keyed by its
argument VALUES, so a value-equal list that never went through the merge could
discharge the postcondition: call the merge on one list to mint the token, then
return a second, value-identical list built independently. The refined real
counterpart returns the un-merged per-member mapping (a plain dict, not the
reconstructed collection), which fails the roundtrip test. Keying the token by
the output object (`Result()` as a `List[int]` reference) removes that channel:
the token's permission attaches to the one object `assemble` returned, and no
other object — however value-equal — holds it.

**Why this is needed (the re-audit's residual G-EQ hole).** The per-member
recovered *values* are the same whether or not the merge happened (the bug is
"raises vs returns", not "wrong value"), so NO value-level postcondition
(`ToSeq(Result()) == ToSeq(data)`) can separate the gold patch from an impl that
builds the verbatim values and skips `Dataset(...)` (the named counterexample
`atk_7`, whose faithful refinement `return data_dict` returns a dict and fails
the F2P `assert_identical`). The token forces the merge onto the result path.

**Soundness check (G-AX, `axiom_check.py`):** the recovered collection equals
`xr.Dataset(good)`'s output (a Dataset, identical to the original); the
un-merged per-member mapping `good` is a plain `dict`, is NOT a `Dataset`, and is
NOT `.identical` to the original — so the token (held only by the merge's output)
genuinely cannot be obtained by bypassing the merge. These are pure-Python
assertions independent of xarray version.
