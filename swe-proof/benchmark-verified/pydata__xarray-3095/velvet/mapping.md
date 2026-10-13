# mapping.md — pydata__xarray-3095

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1757dffac2fa493d7b9a074b84cf8c830a706688`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo files under change:
- `xarray/core/indexing.py` (the index wrapper `PandasIndexAdapter`)
- `xarray/core/variable.py` (`IndexVariable.copy`)

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `IndexAdapter` (structure) | `PandasIndexAdapter` — `xarray/core/indexing.py:1229` | the wrapper carrying an index's element values + the precise element dtype it presents |
| `IndexAdapter.values` | the element identities of `PandasIndexAdapter.array` (`indexing.py:1233`, a `pandas.Index` via `utils.safe_cast_to_index`) | ordered element values |
| `IndexAdapter.storedDtype` | `PandasIndexAdapter._dtype` (`indexing.py:1244`), surfaced by the `dtype` property (`indexing.py:1247-1249`) | the precise element dtype the wrapper presents |
| `IndexAdapter.inferredDtype` | the element dtype the `__init__` dtype-inference block (`indexing.py:1234-1244`) re-derives from `array` alone when `dtype=None` | the dtype obtained by ignoring the stored dtype and re-deriving from the underlying representation |
| `adapterCopy (self) (deep)` | `PandasIndexAdapter.copy(self, deep=True)` — the new method the gold adds (`indexing.py`, post-patch) | the modeled changed function: a dtype-preserving clone of the wrapper |
| `indexVariableCopy (self) (deep)` | `IndexVariable.copy(self, deep=True, data=None)` — `xarray/core/variable.py:1920` (the `data is None` branch) | the modeled changed function: an index-variable copy that delegates its data clone to the wrapper |

The pre-patch repo construct the change removes (refinement audit only, not in
the consumer spec view): the inline reconstruction in `IndexVariable.copy`'s
`deep` branch, `PandasIndexAdapter(self._data.array.copy(deep=True))`
(`variable.py:1944-1948` @ base_commit), which passes no `dtype` and so re-runs
the `__init__` inference (`indexing.py:1234-1244`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| element values of the wrapped `pandas.Index` (an ndarray of values) | `IndexAdapter.values : List Int` | the ordered element identities; `len` ↔ `.length`; identity-by-position. The element *payloads* are irrelevant to the modeled property (dtype preservation), so they are carried as opaque `Int` identities. |
| `numpy.dtype` (an element dtype such as `dtype('<U3')` or `dtype('O')`) | `String` (the dtype's `.name`/`str`) | a dtype ↔ its canonical name string; dtype equality ↔ string equality. The bijection is used for the equalities `out.storedDtype = self.storedDtype` and `out.inferredDtype = self.inferredDtype`. |
| `PandasIndexAdapter._dtype` (stored dtype) | `IndexAdapter.storedDtype : String` | `str(adapter._dtype)` ↔ `storedDtype` |
| the dtype re-derived by `__init__` from `array` alone (when `dtype=None`) | `IndexAdapter.inferredDtype : String` | `str(PandasIndexAdapter(values).dtype)` ↔ `inferredDtype` |
| `deep : bool` flag | `deep : Bool` | identity; governs only physical duplication of the values, never the observable element values or stored dtype |
| `PandasIndexAdapter(array, dtype)` construction | `IndexAdapter` record literal | a fresh wrapper with the given values + dtype |

The modeled property turns on the relationship `storedDtype` vs `inferredDtype`:
for a fixed-width unicode element kind the two DIFFER (`<U3` stored, but the
underlying `pandas.Index` representation re-derives a generic object dtype); for
float/int element kinds they AGREE. The fix must carry `storedDtype` through
unchanged rather than re-derive it. (Confirmed locally: a `<U3` numpy array's
`pandas.Index` re-derives an object/str element dtype via `idx.values`, whereas
float64/int64 are preserved — see §3.)

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `adapterCopy`/`indexVariableCopy` deep model ↔ real copy (A-reference)
The changed copy operation is modeled **deeply** by `adapterCopy` (returns a
fresh wrapper with the same values and the same `storedDtype`) and
`indexVariableCopy` (delegates to it). There is **no consumed axiom**. What G-AX
validates is the A-reference: that the real repo behaviour matches the model on
the two observables the spec pins.

**Callee facts the deep model stands on (validated by `axiom_check.py`, G-AX):**

1. **The re-inference gap (the property that makes preservation observable).**
   For the `PandasIndexAdapter` constructor's dtype-inference block
   (`indexing.py:1234-1244`), constructing a wrapper from a fixed-width unicode
   array WITHOUT a stored dtype re-derives a NON-unicode (generic object) element
   dtype, i.e. `inferredDtype ≠ storedDtype` for unicode; while for float/int
   arrays `inferredDtype = storedDtype`. G-AX builds real
   `PandasIndexAdapter(arr)` over `str`/`float`/`int` arrays and reads `.dtype`.

2. **The patched `PandasIndexAdapter.copy` preserves the stored dtype.** For a
   wrapper built WITH an explicit precise dtype (the unicode case), the patched
   `copy(deep=True/False)` returns a wrapper whose `.dtype` equals the original's
   stored `.dtype` and whose element values are unchanged — for either `deep`
   setting. G-AX runs the real patched `copy` and asserts
   `out.dtype == self.dtype` and equal values. Because the copy's underlying
   `pandas.Index` carries the same element values as the original's, the dtype
   RE-DERIVED from the copy's underlying representation also equals the one
   re-derived from the original's (`out.inferredDtype = self.inferredDtype` in
   the model) — G-AX asserts this too. This is the A-reference for
   `adapterCopy`.

3. **`IndexVariable.copy` delegates to the wrapper copy (A-reference for
   `indexVariableCopy`).** The patched `IndexVariable.copy(deep=...)` produces a
   variable whose data wrapper has the same stored dtype as the original's. G-AX
   constructs a real `IndexVariable` over a `<U*` coordinate and asserts the
   copied variable's `.dtype` is the unicode dtype (not object), matching the
   issue's expected behaviour, for both `deep=True` and `deep=False`.

No value is asserted that the real code does not produce; the model pins only
the two structural observables (values preserved, stored dtype preserved).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`3095`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `adapterCopy`/`indexVariableCopy` (R/I-tagged ops) to Python over
the real carrier — a `(values, stored_dtype)` wrapper whose copy returns
`(values, stored_dtype)` — and diffs the two observables (element values; stored
dtype name) against `patch.diff`'s behaviour: the real patched
`PandasIndexAdapter.copy` / `IndexVariable.copy` invoked on real numpy arrays of
`str`/`float`/`int` element kind. A-tagged callees (none consumed) are left as
the real repo callee.
