# refinement.md — pydata__xarray-3095

The operation-by-operation correspondence between `model.py`'s implementation
(the `adapter_copy` impl region and the deep `derive_dtype` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The new duplication method — `PandasIndexAdapter.copy` (`xarray/core/indexing.py`, added by the patch)

Gold hunk (new method):
```python
+    def copy(self, deep: bool = True) -> 'PandasIndexAdapter':
+        array = self.array.copy(deep=True) if deep else self.array
+        return PandasIndexAdapter(array, self._dtype)
```
together with the `__init__` change that makes a supplied dtype authoritative:
```python
+        else:
+            dtype = np.dtype(dtype)
```

| # | model.py impl op (`adapter_copy`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `self: IndexWrapper` with fields `array_kind`, `stored_dtype` | `self`, a `PandasIndexAdapter` with `.array` and `._dtype` | R | the wrapper ↔ a record of the only facts the duplication's dtype reads: the re-derivable buffer type (`array_kind`) and the stored element type (`stored_dtype` ↔ `_dtype`). mapping.md §1–2. |
| A2 | `array_kind = self.array_kind` | `array = self.array.copy(deep=True) if deep else self.array` | R | producing the duplicate's buffer ↔ carrying the buffer's re-derivable type code. `deep` only chooses copy-vs-share of the *buffer*; the buffer's element type (hence `array_kind`) is identical either way, so the dtype-relevant projection is `deep`-independent (mapping.md §2). |
| A3 | `dtype = self.stored_dtype` | `self._dtype` (2nd arg of the `PandasIndexAdapter(...)` call) | R/I | the original's stored element type is read and passed on. `_dtype` ↔ `stored_dtype` code (identity on the dtype carrier). |
| A4 | `duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))` | `PandasIndexAdapter(array, self._dtype)` | A-reference | reconstructing the wrapper ↔ the deep model `derive_dtype` of `__init__`'s dtype-determination. Because a dtype IS supplied (`dtype == stored_dtype != NO_DTYPE`), `derive_dtype` returns it verbatim — exactly the patch's added `else: dtype = np.dtype(dtype)`. The deep model is validated == the real `PandasIndexAdapter.__init__` by G-AX (axiom_check.py F1/F2), NOT consumed as an axiom. |
| A5 | `return duplicate.stored_dtype` | the returned `PandasIndexAdapter`'s `.dtype` | R | the duplicate's reported element type ↔ its `.dtype` property (returns `_dtype`). The F2P/`assert_identical` observes exactly this dtype. |

The discriminating content of the change — duplicating must PRESERVE the
original element type rather than re-derive it from the duplicated buffer —
lives in step A4: the original `stored_dtype` is passed to the reconstruction,
so `derive_dtype(array_kind, stored_dtype) == stored_dtype`, and the
postcondition `Result() == Old(self.stored_dtype)` holds.

## B. The rewired caller — `IndexVariable.copy` (`xarray/core/variable.py:1920`)

Gold hunk:
```python
         if data is None:
-            if deep:
-                data = PandasIndexAdapter(self._data.array.copy(deep=True))
-            else:
-                data = self._data
+            data = self._data.copy(deep=deep)
```

This is the CALLER of the new method. Its observable effect — the duplicated
index's dtype equals the original's — is exactly what `adapter_copy` pins, so it
introduces no separate modeled function. The PRE-patch inlined form
`PandasIndexAdapter(self._data.array.copy(deep=True))` omits the dtype argument,
so `__init__` RE-DERIVES it from the (object-dtype, for text) copied pandas
Index — the bug. `model_prepatch.py` reproduces exactly this: it rebuilds the
wrapper as `IndexWrapper(array_kind, derive_dtype(array_kind, NO_DTYPE))` =
`array_kind`, and **fails** the postcondition `Result() == Old(self.stored_dtype)`
on the witness `array_kind != stored_dtype` (the `<U*` case, `array_kind ==
OBJECT_DTYPE != stored_dtype`). That is precisely the spec sensing the change
(G-DIFF) and the F2P regression `test_copy[str-True]`.

## C. Read-only input, fractional permission

`adapter_copy` does not mutate `self` (the gold builds a NEW
`PandasIndexAdapter` and returns it; the original is untouched). Accordingly
`self.array_kind` and `self.stored_dtype` are Required AND Ensured at
`Acc(..., 1/2)`, and the two `Ensures(field == Old(field))` clauses pin the
original as unchanged. A full-permission, free-to-overwrite `self` would let a
wrong impl satisfy `Result() == Old(self.stored_dtype)` vacuously by rewriting
`stored_dtype`; the fractional read-only permission plus the `Old`-equality
clauses block that (directive 5).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— how the duplicate's dtype is determined (carry over vs re-derive) — is modelled
**deeply** (`derive_dtype` + the verified `adapter_copy` body), not hidden behind
an axiom about the function under change. There is **no consumed `@ContractOnly`
axiom**: the only kind-A item is the **A-reference** of step A4, where G-AX
validates the deep `derive_dtype`/`adapter_copy` against the real
`PandasIndexAdapter` construction/copy.

## E. verify(model) ⇒ resolved

`adapter_copy` verifies only if its returned dtype equals the original's stored
dtype (A4/A5) for every input, INCLUDING the fixed-width-text case where
`array_kind != stored_dtype`. By R (dtype ↔ code, `_dtype` ↔ `stored_dtype`,
`.dtype` ↔ reported code; `deep` is dtype-irrelevant) the verified method equals
`PandasIndexAdapter(array, self._dtype).dtype` on every input. By G-AX the deep
model `derive_dtype`/`adapter_copy` equals the real `PandasIndexAdapter`
construction/copy (A-reference): a supplied dtype is preserved, re-derivation of
text is lossy (object), and the real `copy(deep=True/False)` preserves the dtype.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited A-reference — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ) plus the A-reference faithfulness check (G-AX); there is no
consumed axiom.
