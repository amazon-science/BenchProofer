# mapping.md — pydata__xarray-3677

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ef6e6a7b86f8479b9a1fecf15ad5b88a2326b31e`, states the type
abstraction, and gives the provenance of the conversion callee the deep model is
validated against.

Repo file under change: `xarray/core/dataset.py` (the `Dataset.merge` method).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `merge_method(receiver, other)` | `Dataset.merge(self, other, ...)` body, `xarray/core/dataset.py:3548` (changed line is the operand-list construction handed to `dataset_merge_method`, `dataset.py:3606-3615`) | the modeled changed function |
| `Operand` (`is_mapping`, `name`, `value`) | a merge operand: a `Dataset` (mapping-shaped) or a `DataArray` (array-shaped, single named value) — `xarray/core/dataset.py` / `xarray/core/dataarray.py:214` | minimal carrier of the touched fields |
| `as_mapping(o)` *(deep model — A-reference)* | `DataArray.to_dataset()` → `_to_dataset_whole()` — `xarray/core/dataarray.py:490, 462` | the conversion the fix calls on an array-shaped second operand: builds the one-variable Dataset keyed by the array's name |
| `is_array_shaped(o)` | `isinstance(other, xr.DataArray)` test in the fix (`dataset.py` new line) | pure spec: an operand without the named-entry interface |

The downstream consumer of the operand list (why every operand must be
mapping-shaped): `dataset_merge_method` (`xarray/core/merge.py:798`) builds
`objs = [dataset, other]` and calls `merge_core` (`merge.py:501`), which calls
`coerce_pandas_values` (`merge.py:369`); that routine, for any operand that is
NOT a `Dataset`, executes `for k, v in obj.items()` (`merge.py:394`). A
`DataArray` has no `.items()`, so an unconverted array-shaped second operand
raises `AttributeError: 'DataArray' object has no attribute 'items'`. The
top-level `xr.merge([...])` does not hit this because it coerces each list
element to a Dataset-like first.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `Dataset` operand | `Operand` with `is_mapping == True` | a Dataset exposes `.items()` (the named-entry interface), so it is "mapping-shaped"; its first/only variable's name and value are abstracted to `name`/`value` ints |
| a `DataArray` operand | `Operand` with `is_mapping == False` | a DataArray has a single value and a `.name` but no `.items()`, so it is "array-shaped"; `name` = the array's `.name` (abstracted to an int code; -1 = unnamed), `value` = its data |
| `isinstance(other, xr.DataArray)` | `is_array_shaped(other)` == `not other.is_mapping` | a DataArray is array-shaped; a Dataset is mapping-shaped — the two shapes the merge argument can take |
| `other.to_dataset()` | `as_mapping(other)` | `to_dataset()` (no `dim`) → `_to_dataset_whole(name=self.name)`: a one-variable Dataset whose single variable is keyed by the array's name and holds the array's value. Modeled as producing an `Operand` with `is_mapping == True` and the same `name`/`value`. |
| variable NAME (a `Hashable`) | `int` code | order/identity-only; the F2P test's `name="b"` is one such code |
| variable VALUE | `int` | the F2P test's scalar data (`0`, `1`); only equality/preservation is observed |

`receiver is not other`: the receiver Dataset and the merge argument are always
distinct Python objects (the argument is a separately-constructed operand); this
is a faithful, non-weakening precondition that also keeps the field-permission
accounting free of self-aliasing.

## 3. Conversion provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `as_mapping` deep model ↔ `DataArray.to_dataset()`

`as_mapping` is NOT a consumed `@ContractOnly` axiom — it is a deep model (an
ordinary verified function) of the unchanged conversion callee the fix invokes.
Its relied-on properties:

* the result is mapping-shaped (a `Dataset`, which exposes `.items()`);
* the result carries the same single named variable (name and value preserved).

Provenance: `DataArray.to_dataset(self, dim=None, name=None)`
(`xarray/core/dataarray.py:490`) with no `dim` delegates to
`_to_dataset_whole(name=self.name)` (`dataarray.py:462`), which sets
`variables[name] = self.variable` and constructs a `Dataset`
(`Dataset._construct_direct`, `dataarray.py:487`). So a named DataArray converts
to a one-variable Dataset keyed by its name and holding its value — exactly the
two properties above. `axiom_check.py` (G-AX) runs the REAL
`DataArray.to_dataset()` on boundary + fuzz inputs and asserts the produced
object is a `Dataset` (mapping-shaped, has `.items()`) carrying the same single
`{name: value}` variable.

Flag/precondition dependency: the conversion is well-defined only for a NAMED
DataArray (`_to_dataset_whole` raises `ValueError` on an unnamed array,
`dataarray.py:467-471`); the model encodes this as `as_mapping`'s precondition
`o.name >= 0` (and `merge_method` requires `Implies(is_array_shaped(other),
other.name >= 0)`). The F2P test uses a named array (`name="b"`); the unnamed
case is the separate `test_merge_dataarray_unnamed` path (top-level `merge`,
unchanged here).

## 4. No consumed axioms

No `@ContractOnly` axiom is consumed by the proof. The only callee the change
introduces is the array→mapping conversion, modeled deeply as `as_mapping`
(§3.1, an A-reference). The `axioms` marker region is therefore empty.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg by diffing a VERBATIM copy
of `model.py`'s impl regions (contract calls stripped; `Operand`,
`is_array_shaped`, `as_mapping`, `merge_method`) against the REAL patched repo
function, which is **called, not transliterated**.

* **Oracle**: the patched `Dataset.merge` (`xarray/core/dataset.py:3548`, §1).
  The modeled output — the two-operand sequence handed to the core combination
  routine — is recovered by wrapping `xarray.core.dataset.dataset_merge_method`
  (the real callee that builds `objs = [dataset, other]`, `merge.py:817-819`)
  with a spy that records the operand pair and then delegates to the real
  function, so the branch decision and the conversion are both executed by the
  real patched module. `_assert_oracle_is_patched()` aborts (exit 2) if the
  imported `Dataset.merge` is not the patched one.
* **Type bridge** (§2 inverted): concrete→abstract reads `is_mapping` off the
  real named-entry interface (`hasattr(obj, "items")` — the property
  `coerce_pandas_values` needs, not a re-test of the patch's `isinstance`),
  `name` through the fixed `_NAME_BY_CODE` bijection (`-1` = unnamed), `value` =
  the single/first data variable's scalar int. abstract→concrete builds
  `xr.DataArray(data=value, name=...)` (array-shaped) or `xr.Dataset({...})`
  (mapping-shaped). Inputs are generated concretely, so every one satisfies
  `merge_method`'s `Requires` by construction (receiver always a Dataset,
  operands always distinct objects, array-shaped argument always named).
* **Diffed clauses**: all six postconditions of `merge_method` — length 2,
  receiver object pass-through, `is_mapping` of BOTH operands, name/value
  preservation of the second, and the mapping-shaped identity clause
  `Implies(not is_array_shaped(other), Result()[1] is other)`. On every
  array-shaped input the deep model is additionally cross-checked against the
  real A-reference callee: `as_mapping(abstract(da)) == abstract(da.to_dataset())`.
* **Inputs**: 100050 = 50 systematic + 100000 fuzz. The systematic grid
  exhaustively crosses receiver size 0..3 × argument shape (named DataArray /
  Dataset of 0..3 variables) × name regime (disjoint / colliding-equal /
  colliding-differing, i.e. including the MergeError regime, which the model's
  `Requires` does not exclude), starting with the exact F2P shape
  `xr.Dataset({"a": 0}).merge(xr.DataArray(data=1, name="b"))`, plus empty
  receiver, empty-Dataset argument, extreme values, and a multi-variable
  argument (the lossy-rebuild witness). Both impl branches are taken ~50k times
  each and the driver FAILS if either count is zero.
* **Pinned seed**: `SEED = 3677` (module constant `SEED`; `N_FUZZ = 100_000`).
* **Falsifiability evidence**: three mutants were run against the real patched
  oracle and all exited 1 — (a) the pre-patch shadow (`as_mapping` call removed)
  fails on the F2P input with `operand 1 differs: shadow (False,1,1) vs real
  (True,1,1)`; (b) a paraphrase that rebuilds a mapping-shaped operand instead
  of passing it through fails the identity clause; (c) a bridge that drops the
  variable's value fails the preservation clause. Running the unmutated script
  against UNPATCHED source exits 2 via the patched-oracle guard.
