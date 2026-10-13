# refinement.md — pydata__xarray-3095

Operation correspondence between `implementation_copy` and the gold `patch.diff`.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX/G-CONF), **I**
(identical concrete op).

No axioms are declared or consumed. The only behavior the patch changes —
preserving the *stored* element type (`dtype`) of an index wrapper across a deep
copy instead of re-deriving it from the underlying sequence — is modeled DEEPLY
in Lean (`implementation_copy` / `problem_spec_copy`). Every row below is **R**,
**A-reference**, or **I**. The R/I/A-reference legs are differential-tested by
G-CONF; G-AX is a skip stub (no consumed callee axiom).

## What the gold patch does

The gold patch spans two files but is a single behavioral change:

1. `xarray/core/indexing.py` — adds a `copy(deep=True)` method to the index
   wrapper (`PandasIndexAdapter`) that rebuilds the wrapper from a (deep or
   shallow) copy of the underlying index **and re-attaches the wrapper's stored
   `self._dtype`**:
   ```python
   def copy(self, deep: bool = True) -> 'PandasIndexAdapter':
       array = self.array.copy(deep=True) if deep else self.array
       return PandasIndexAdapter(array, self._dtype)   # <-- stored dtype kept
   ```
   (The other indexing.py hunks are pure type annotations / docstring reflow —
   no behavior; see mapping.md.)

2. `xarray/core/variable.py` — `IndexVariable.copy(deep, data)` now delegates to
   that method:
   ```python
   if data is None:
       data = self._data.copy(deep=deep)             # POST-PATCH
   ```
   replacing the pre-patch branch
   ```python
   if data is None:
       if deep:
           data = PandasIndexAdapter(self._data.array.copy(deep=True))  # no dtype!
       else:
           data = self._data
   ```
   The pre-patch deep branch rebuilds the wrapper from the array **without**
   passing `self._data._dtype`, so the wrapper re-infers its dtype from the
   pandas index. For a `<U*` (fixed-width unicode) index, pandas stores it as an
   `object`-dtype `Index`, so the re-inferred dtype is `object` — the reported
   regression. The shallow branch reused `self._data` directly, so its dtype
   survived (matching the issue note that `deep=False` is unaffected).

## `implementation_copy` ↔ the gold patch

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `deep : Bool`, `v : IVar` binder | `IndexVariable.copy(deep, data=None)` with `self._data : PandasIndexAdapter` | R | the `data=None` path (the only path the patch touches); `IVar.data` ↦ `self._data` |
| `let mut arr := v.data.values; if deep then arr := v.data.values` | `array = self.array.copy(deep=True) if deep else self.array` | R | duplicate-vs-share the underlying sequence; CONTENT-preserving either way (a deep copy and a shallow copy carry the same element values). Modeled as identity on the value list since value content is what the observable depends on |
| `{ values := arr, native := v.data.native, dtype := v.data.dtype }` | `PandasIndexAdapter(array, self._dtype)` | A-reference | THE EDITED op: the rebuilt wrapper re-attaches the original stored element type. Modeled deeply (carry `v.data.dtype` verbatim); validated == real `PandasIndexAdapter(array, dtype).dtype` by G-CONF |
| `{ dims := v.dims, attrs := v.attrs, data := newData }` | `type(self)(self.dims, data, self._attrs, self._encoding, fastpath=True)` | R | reassemble the variable with unchanged dims/attrs and the new data wrapper; frame discipline (§0.5) pins dims + attrs to their input values |
| `return …` | `return type(self)(...)` | I | return the copied variable |

`native` (the underlying-sequence element type, e.g. pandas reporting a `<U*`
index as `object`) is pinned to its input value and is exactly what the buggy
deep path leaks into `dtype`; pinning both `native` and `dtype` to the input is
what discriminates the fix (the result must keep the *recorded* `dtype`, which
may differ from `native`).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: on a deep copy the rebuilt wrapper takes its stored
  element type from the underlying sequence (`dt := v.data.native`) rather than
  the recorded one. The carried gold proof of `correct_copy` fails to close on
  the `result.data.dtype = v.data.dtype` clause for any `deep=true` input whose
  `dtype ≠ native` (e.g. a fixed-width-unicode value whose native element type
  is the generic catch-all). This is the single fixed behavior.
  (FAIL_TO_PASS: `TestIndexVariable::test_copy[str-True]`.)
