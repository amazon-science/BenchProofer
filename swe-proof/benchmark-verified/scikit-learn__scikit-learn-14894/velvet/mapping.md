# mapping.md — scikit-learn__scikit-learn-14894

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fdbaa58acbead5a254f2e6d597dc1ab3b947f4c6`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled/axiomatized callee.

Repo file under change: `sklearn/svm/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildSparseCoef (nSV nClass dataLen : Nat)` | the per-class sparse-coefficient assembly tail of `BaseLibSVM._sparse_fit` — `sklearn/svm/base.py:287–294` (the `n_SV`-derived layout that ends by setting `self.dual_coef_`) | the modeled changed code region |
| `SparseCoef` (structure) | a `scipy.sparse.csr_matrix` — only its observed fields | the result carrier (compressed-row matrix) |
| `arangeIndptr (nSV nClass)` *(deep model — A-reference)* | `np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)` — `base.py:290–291` | pure spec: the strided row index-pointer layout; the range whose **stride is `0` when `nSV = 0`** (the division `dual_coef_indices.size / n_class`); validated == real `np.arange` by axiom_check.py (G-AX), NOT a consumed axiom |
| `tileRange (nSV nClass)` *(deep model — A-reference)* | `np.tile(np.arange(n_SV), n_class)` — `base.py:289` | pure spec: the per-element column-index sequence; validated == real `np.tile(np.arange(...))` by G-AX |
| `emptyResult` *(deep model — A-reference)* | `sp.csr_matrix([])` — `base.py` post-patch empty branch | pure spec: the empty compressed-row container; validated == real `sp.csr_matrix([])` observed fields by G-AX |
| `builtResult` / `SparseCoef` literal | `sp.csr_matrix((dual_coef_data, dual_coef_indices, dual_coef_indptr), (n_class, n_SV))` — `base.py:292–294` | pure spec: the strided compressed-row matrix |

The pre-patch repo behavior the change fixes (refinement audit only): the
unconditional `np.arange(..., dual_coef_indices.size / n_class)` at `base.py:290`,
whose stride `dual_coef_indices.size / n_class = (n_SV·n_class) / n_class = n_SV`
is `0` when `n_SV = 0`, making `np.arange` raise `ZeroDivisionError`
(`float division by zero`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `n_SV = self.support_vectors_.shape[0]` (a non-negative row count) | `nSV : Nat` | identity on ℕ; `n_SV == 0` ↔ `nSV = 0` |
| `n_class` (≥ 1: `len(classes_) - 1` for classification, `1` for regression) | `nClass : Nat`, `require 1 ≤ nClass` | identity on ℕ; the `require` mirrors that `n_class` is always ≥ 1 at this call site |
| `dual_coef_data.size` (count of stored coefficient values) | `dataLen : Nat` | identity on ℕ; carried opaquely (the assembly never inspects the values) |
| a `scipy.sparse.csr_matrix` | `SparseCoef` | `m.data.size` ↔ `dataLen`; `list(m.indices)` ↔ `indices`; `list(m.indptr)` ↔ `indptr`; `m.shape` ↔ `(rows, cols)` |
| `np.tile(np.arange(n_SV), n_class)` (a 1-D int array) | `tileRange nSV nClass : List Nat` | `arr.tolist()` ↔ the `List Nat`; `np.arange(n_SV)` ↔ `List.range nSV`; `np.tile(a, k)` ↔ `k` concatenated copies (`List.replicate k a |>.flatten`) |
| `np.arange(0, N+1, stride)` with `stride = N / n_class` | `arangeIndptr nSV nClass : Except FitErr (List Nat)` | for `nSV ≥ 1`, `N = n_SV·n_class`, `stride = n_SV`, so the float range `0, n_SV, …, n_class·n_SV` is exact-integer and ↔ `(List.range (nClass+1)).map (·*nSV)`; for `nSV = 0` the stride is `0` ⇒ `ZeroDivisionError` ↔ `Except.error zeroDivision` |
| raised `ZeroDivisionError` | `Except.error FitErr.zeroDivision` | the only failure shape the region can take |

`n_class ≥ 1` always holds at this call site: in the classification branch
`n_class = len(self.classes_) - 1 ≥ 1` (a fitted SVC has ≥ 2 classes); in the
regression branch (SVR/OneClassSVM, the issue's reproducer) `n_class = 1`. The
`require 1 ≤ nClass` records this; it is needed so `dual_coef_indices.size / n_class`
is well-defined whenever the stride is nonzero, i.e. the only division-by-zero
is the `n_SV = 0` one the fix addresses.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `arangeIndptr` / `tileRange` / `emptyResult` deep models ↔ NumPy/SciPy (A-reference)

**Callees:** `numpy.arange`, `numpy.tile`, `scipy.sparse.csr_matrix` — all
**unchanged** library functions the region calls; the gold patch changes only
the *control flow* around them (it adds the `if not n_SV` guard), not the
functions themselves.

The deep models encode the observable behavior of the real callees:

* `tileRange nSV nClass` == `np.tile(np.arange(n_SV), n_class).tolist()` — the
  column indices `0 … nSV-1` tiled `nClass` times.
* `arangeIndptr nSV nClass`:
  - `nSV = 0`: `np.arange(0, 1, 0.0)` raises `ZeroDivisionError` (the
    `dual_coef_indices.size / n_class` stride is `0`) ⇒ `Except.error zeroDivision`;
  - `nSV ≥ 1`: `np.arange(0, n_SV·n_class + 1, n_SV)` == `[0, n_SV, 2·n_SV, …,
    n_class·n_SV]` ⇒ `Except.ok ((List.range (nClass+1)).map (·*nSV))`. The float
    division yields the exact integer `n_SV` because
    `dual_coef_indices.size = n_SV·n_class` is divisible by `n_class`.
* `emptyResult` == the observed fields of `sp.csr_matrix([])`: `data.size == 0`,
  `indices == []`, `indptr == [0, 0]`, `shape == (1, 0)`.

**Soundness check (G-AX):** `axiom_check.py` runs the real `numpy`/`scipy` over
boundary `(nSV, nClass)` pairs (including `nSV = 0`) plus randomized fuzz,
asserting (a) `tileRange == np.tile(np.arange(..))`, (b) `arangeIndptr` matches
the real `np.arange` (raising for `nSV = 0`, equal list otherwise), and (c) the
empty/built `csr_matrix` field tuples match. Imports only `numpy`/`scipy` (the
same libraries the gold patch calls). Exit 0 iff sound.

### 3.2 No consumed axioms

There is **no** `axiom` whose `ensures` the proof consumes: every modeled callee
is spelled out as a deep model (`arangeIndptr`, `tileRange`, `emptyResult`,
`builtResult`) in the `axioms`/`pure` regions and validated == its real callee
by G-AX (A-reference). The `FitErr` / `SparseCoef` declarations carry no
behavioral assumption. Hence `meta.json axioms = []`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14894`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl region's branch + `tileRange`/`emptyResult`/`builtResult` (R/I-tagged
ops) to Python and compares the resulting `csr_matrix` observable fields against
the gold-patched `_sparse_fit` assembly behavior over ≥10⁵ fuzzed `(nSV, nClass,
dataLen)` inputs (including `nSV = 0`).
