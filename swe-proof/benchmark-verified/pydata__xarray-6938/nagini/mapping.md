# mapping.md — pydata__xarray-6938

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c4e40d991c28be51de9ac560ce895ac7f9b14924`, states the type
abstraction, and gives the provenance of the deep-model reference (there are NO
consumed axioms).

Repo files under change: `xarray/core/variable.py` and `xarray/core/dataset.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `CoordVar` | `xarray.core.variable.IndexVariable` (and its base `Variable`) — `variable.py:2710` / `variable.py:276` | minimal model of a 1-D coordinate variable: only the touched field `dims` is carried |
| `CoordVar.dims` (`List[int]`) | `Variable._dims` / the `Variable.dims` property+setter — `variable.py:572-579` | the tuple of dimension names; the setter `dims.setter` reassigns `self._dims` |
| `to_index_variable(self)` | `IndexVariable.to_index_variable` — `variable.py:2882-2884` | **the modeled changed function**: pre-patch `return self`; post-patch `return self.copy()` |
| `copy_coord(self)` | `IndexVariable.copy(deep=True, data=None)` → `Variable._replace` — `variable.py:2831-2865`, `_replace` `variable.py:977-992` | the copy invoked by the fix: builds a fresh object with `copy.copy(self._dims)` |
| `to_base_variable(self)` | `Variable.to_base_variable` — `variable.py:539-543` | sibling re-presentation: already returns a fresh `Variable(...)`; the patch only changes `self.dims`→`self._dims` (identical value) |

Sites in the gold patch that are NOT separately modeled (no observable behaviour
change — recorded for the refinement audit):
- `Variable.to_base_variable` / `Variable.to_index_variable`: `self.dims` →
  `self._dims` (`variable.py:539-551`). The `dims` property simply returns
  `self._dims` (`variable.py:572-575`); the read value is identical. Pure
  micro-read change.
- `Dataset.swap_dims`: an added local annotation `var: Variable`
  (`dataset.py:3774`). A type annotation; no runtime effect. This is the call
  site that USES the fix: `var = v.to_index_variable(); var.dims = dims`
  (`dataset.py:3775-3776`) — mutating `var` must not mutate the original `v`.
- Return-type annotations and the `name`/`level_names` property annotations
  (`-> Variable`, `-> IndexVariable`, `-> pd.Index`, `-> Hashable`,
  `-> NoReturn`, `-> list[str] | None`) and the `NoReturn` import: annotation-
  only, no runtime effect.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Variable` / `IndexVariable` object | `CoordVar` instance | only the touched field is modeled; `self` ↔ the receiver |
| `dims`: a `tuple[Hashable, ...]` of dimension names | `dims`: `List[int]` of name codes | `dims[k]` ↔ `ord`/id of the k-th name; `len` ↔ tuple length; tuple equality ↔ `ToSeq` equality. The F2P observes only the tuple of names (`a.dims == ("x",)`), so any injective name↔int coding is faithful. |
| `var.dims = (...)` (the `dims` setter, `variable.py:577-579`) | reassigning the `CoordVar.dims` field | both replace the receiver's stored dimension-name sequence in place |
| object identity (`a is not b`) | Nagini reference (`Result() is not self`) + permission separation | distinct allocation ⇔ disjoint write permission to `Result().dims` vs `self.dims` |

`str` indexing/iteration is banned in Nagini, so dimension names are carried as
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

| the callee always returns (straight-line `return self.copy()`; `copy`/`_replace` are bounded allocations with no loops over unbounded state) | `Requires(MustTerminate(n))` on every modeled operation (constructor 1, clone 2, coordinate 3, plain 4; copy loops discharge with the strictly decreasing measure `len(dims) - i + 1`) | total correctness: the real re-presentations never diverge, and `Dataset.swap_dims` relies on `to_index_variable` RETURNING before it reassigns `var.dims`. A diverging implementation satisfies value/identity postconditions only vacuously and hangs the F2P (`test_to_index_variable_copy` would time out, not pass) — so partial correctness alone under-pins the patched behaviour. |

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `to_index_variable` / `copy_coord` ↔ `IndexVariable.to_index_variable`
**Callee:** post-patch `IndexVariable.to_index_variable(self)` returns
`self.copy()`; `IndexVariable.copy` (`variable.py:2831-2865`) calls
`self._replace(data=...)`, and `_replace` (`variable.py:977-992`) does
`type(self)(copy.copy(self._dims), ...)` — i.e. it **allocates a fresh object
with a copied dimension-name tuple**.

The changed operation (alias → independent copy) is modeled **deeply**, NOT
behind a consumed `@ContractOnly` axiom: the model's permission discipline
*is* the independence guarantee. `to_index_variable` requires only fractional
read permission on the receiver (`Acc(self.dims, 1/2)`, returned unchanged) and
ensures FULL write permission to a distinct result (`Acc(Result().dims)`,
`Result() is not self`, `Result().dims is not self.dims`). The pre-patch
`return self` cannot satisfy this (the receiver's retained 1/2 plus the result's
full 1 would be 3/2 > 1, and `Result() is not self` is false).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL post-patch callees
in-container (`IndexVariable.to_index_variable`, `Variable.to_base_variable`,
`Variable.to_index_variable`) on the exact F2P scenario (issue #6931), 5
boundary 1-D index variables, and 2000 randomized fuzz cases, and asserts every
observation meets the deep model: (1) the result is a DISTINCT object, (2) it
initially carries the receiver's dimension names, (3) reassigning the result's
`dims` leaves the receiver's `dims` unchanged. It imports only `xarray` (the
module the gold patch edits). Exit 0 iff sound. There is no consumed axiom to
check; this validates the deep model against the real callee (A-reference).

Provenance / issue: https://github.com/pydata/xarray/issues/6931 ("`.swap_dims()`
can modify original object"). Doc behaviour: `to_index_variable` "Return this
variable as an xarray.IndexVariable" — the contract is that it is a
re-presentation, and a re-presentation must not alias mutable state of the
receiver, as the swap_dims call site (`dataset.py:3775-3776`) immediately
reassigns `var.dims`.

## 4. G-CONF (conformance_check.py)

Differential gate: the contract-stripped impl region (shadow) vs the real
patched callees in-container (`IndexVariable.to_index_variable` ↔
`as_coordinate`, `IndexVariable.copy` ↔ `independent_clone`,
`Variable.to_base_variable` ↔ `as_plain`), bridged per §2 (name code `c` ↔
dimension name `"d<c>"`; the dims setter ↔ rebinding the stored name
sequence). Observables per input: result distinctness, initial result dims,
receiver dims after the call, and both objects' dims after reassigning the
RESULT's dims (mutation independence). ≥1e5 Requires-satisfying inputs:
104 boundary checks + 34000 fuzz iterations × 3 operation checks.
**Pinned fuzz seed: 6938** (the instance number).
