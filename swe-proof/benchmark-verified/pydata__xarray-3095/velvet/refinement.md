# refinement.md — pydata__xarray-3095

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `adapterCopy` and `indexVariableCopy` `do` blocks) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The wrapper-copy site — new `PandasIndexAdapter.copy` (`xarray/core/indexing.py`)

Gold hunk (added method):
```
+    def copy(self, deep: bool = True) -> 'PandasIndexAdapter':
+        array = self.array.copy(deep=True) if deep else self.array
+        return PandasIndexAdapter(array, self._dtype)
```

| # | Solution.lean impl op (`adapterCopy`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self : IndexAdapter` | `self` (a `PandasIndexAdapter`) | R | `PandasIndexAdapter` ↔ `IndexAdapter` exposing only the touched notions: `values`, `storedDtype`, `inferredDtype` (mapping.md §1, §2). |
| A2 | parameter `deep : Bool` | `deep: bool = True` | R | `bool` ↔ `Bool` (identity). |
| A3 | `let arr := if deep then self.values else self.values` | `array = self.array.copy(deep=True) if deep else self.array` | R + I | the branch selects whether the underlying values are physically duplicated; under the value-identity bijection (mapping.md §2) a deep copy yields the SAME element values as the original, so both legs map to `self.values`. The `if deep … else …` control structure is identical (I); the "copied ndarray has equal values" step is the R refinement (physical duplication is unobservable in the value carrier). |
| A4 | `return { values := arr, storedDtype := self.storedDtype, inferredDtype := self.inferredDtype }` | `return PandasIndexAdapter(array, self._dtype)` | R + I | construct a fresh wrapper passing the STORED dtype `self._dtype` (↔ `self.storedDtype`) — NOT re-inferring it. `inferredDtype` is carried unchanged (it is a property of the same values, not chosen by the impl; the copy's underlying `pandas.Index` holds the same element values, so re-derivation yields the same dtype). The post-state observables are `out.values = self.values`, `out.storedDtype = self.storedDtype`, and `out.inferredDtype = self.inferredDtype`. |

Discriminating content of the change — passing `self._dtype` to the constructor
(model: `storedDtype := self.storedDtype`) rather than letting the constructor
re-derive it from `array` (model: `:= self.inferredDtype`) — lives in clause A4.
See §B for the failing prepatch.

## B. The index-variable-copy site — `IndexVariable.copy` (`xarray/core/variable.py:1920`)

Gold hunk (`data is None` branch):
```
-            if deep:
-                data = PandasIndexAdapter(self._data.array.copy(deep=True))
-            else:
-                data = self._data
+            data = self._data.copy(deep=deep)
```

| # | Solution.lean impl op (`indexVariableCopy`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `self : IndexAdapter` | `self` (an `IndexVariable`, via `self._data`, a `PandasIndexAdapter`) | R | the variable's data wrapper `self._data` ↔ `IndexAdapter` (mapping.md §1). Only the data-wrapper notions the copy touches are modeled. |
| B2 | `let data ← adapterCopy self deep` | `data = self._data.copy(deep=deep)` | R + I (callee-under-spec) | delegate the data clone to the wrapper's own copy. `adapterCopy` is the SAME modeled function as site A; `prove_correct` supplies `adapterCopy_correct`, so the caller's proof consumes the wrapper-copy postconditions directly (callee-under-spec, SPEC_GUIDE §3 — better than an axiom). The `deep` flag is forwarded unchanged (I). |
| B3 | `return data` | `return type(self)(self.dims, data, …, fastpath=True)` | R | the surrounding `Variable` reconstruction (dims/attrs/encoding) is unchanged by the patch and observationally identity on the modeled observables (element values + stored element dtype); the only behaviour the fix changes is which `data` wrapper is handed in (B2). The F2P test `assert_identical(v, w)` observes the element values and dtype carried by `data`. |

The pre-patch `IndexVariable.copy` (`variable.py:1944-1948`) reconstructed
`PandasIndexAdapter(self._data.array.copy(deep=True))` — passing NO dtype, so the
constructor re-derived the element dtype from the underlying representation
(`inferredDtype`). For a fixed-width unicode coordinate that re-derived dtype is
a generic object dtype, not the stored unicode dtype — the exact regression in
the issue (`<U3` silently cast to `object` on `copy(deep=True)`).
`Solution_prepatch.lean` reproduces that by returning
`{ … storedDtype := self.inferredDtype … }` in `indexVariableCopy` and **fails**
the postcondition `out.storedDtype = self.storedDtype` — confirmed: the unsolved
goal is `self.inferredDtype = self.storedDtype` (G-DIFF). This is precisely the
spec sensing the bug: only an impl that carries the stored dtype through (never
re-derives it) verifies.

## C. Consumed axioms

None. Both modeled functions are changed functions; the copy is modeled
**deeply** (the record constructions of `adapterCopy`/`indexVariableCopy`). There
is no axiom the proof consumes — no dead axiom.

## D. Deep-model reference (A-reference)

The real callee facts the deep model stands on — that the `PandasIndexAdapter`
constructor re-derives a DIFFERENT (object) element dtype for a unicode array
when given no dtype (so preservation is observable), that the patched
`PandasIndexAdapter.copy` returns a wrapper whose `.dtype` equals the original's
stored dtype with unchanged values for either `deep` setting, and that the
patched `IndexVariable.copy` yields a variable whose data wrapper has the same
stored dtype — are the **A-reference**: validated equal to the real
numpy/pandas/xarray behaviour by `axiom_check.py` (G-AX), NOT consumed as an
axiom. See mapping.md §3.

## E. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — passing
the stored dtype to the reconstructed wrapper instead of re-deriving it — is
modeled **deeply** (the `storedDtype := self.storedDtype` field of the
constructed record, clause A4 / B2), not hidden behind an axiom about the
function under change. There is no consumed axiom.

## F. verify(Solution) ⇒ resolved

`adapterCopy`/`indexVariableCopy` verify only if the result preserves the
element values (`out.values = self.values`), the STORED element dtype
(`out.storedDtype = self.storedDtype`), and the re-derivable dtype
(`out.inferredDtype = self.inferredDtype` — a property of the unchanged
values, so any faithful copy preserves it), for either `deep` setting.
The spec runs under TOTAL-correctness semantics
(`set_option loom.semantics.termination "total"`): the real copy is a
straight-line construction that always completes, so a diverging
implementation must NOT satisfy the spec (under partial correctness a
non-terminating body would discharge every postcondition vacuously). By R
(`PandasIndexAdapter ↔ IndexAdapter`, dtype ↔ name string, deep-copy value
identity) the verified copy equals `self._data.copy(deep=deep)` returning a
wrapper built with `self._dtype` — the gold patch — on the tested inputs; by
G-AX the deep model's two observables equal the real patched
`PandasIndexAdapter.copy` / `IndexVariable.copy` (A-reference) and the re-
inference gap holds (unicode loses its dtype on re-derivation, float/int do not);
by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
