# refinement.md — sympy__sympy-13877

The operation-by-operation correspondence between `model.py`'s implementation
(the `lowest_live_index` impl region, plus the deep `is_genuinely_zero` / `first_usable`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The pivot-selection site — `_eval_det_bareiss.bareiss` (`sympy/matrices/matrices.py`)

Gold hunk (the two coupled edits):
```
- # XXX included as a workaround for issue #12362.  Should use `_find_reasonable_pivot` instead
- def _find_pivot(l):
-     for pos,val in enumerate(l):
-         if val:
-             return (pos, val, None, None)
-     return (None, None, None, None)
...
- pivot_pos, pivot_val, _, _ = _find_pivot(mat[:, 0])
+ pivot_pos, pivot_val, _, _ = _find_reasonable_pivot(mat[:, 0],
+                              iszerofunc=_is_zero_after_expand_mul)
  if pivot_pos == None:
      return S.Zero
```
plus the new module helper
```
+ def _is_zero_after_expand_mul(x):
+     return expand_mul(x) == 0
```

`model.py` models the function under change as `lowest_live_index(col)`: given a matrix
column, return the index of the pivot to use, or `-1` ("no pivot" — the
`pivot_pos == None → return S.Zero` outcome). The 4-tuple is reduced to its only
consumed component, `pivot_pos` (mapping.md §2).

| # | model.py impl op (`lowest_live_index`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `col: List[int]` (status codes) | `mat[:, 0]` — the first column of the current minor | R | a **non-Float** matrix column ↔ `List[int]`; each entry abstracted by its zero-status code (mapping.md §2). `len(col)` ↔ column length; ascending loop index ↔ "lowest index" search. The all-`Float`/`Integer`-with-a-`Float` configuration takes `_find_reasonable_pivot`'s leading numeric branch (max-magnitude partial pivoting) and is OUTSIDE the modeled slice — mapping.md §2 records why that branch is unobservable in the graded behaviour (the determinant value is pivot-choice independent) and off the issue's symbolic path. |
| A2 | the ascending scan returning the first `i` with `not is_genuinely_zero(col[i])` | `_find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul)`'s PASS 1, which returns the first `i` with `iszerofunc(x) == False` | I + A-reference | on the modeled non-Float columns (A1) `_find_reasonable_pivot` skips its leading numeric branch and, with this `iszerofunc`, returns the lowest index where `iszerofunc(x) == False`, i.e. `expand_mul(x) != 0` (PASS 1 always makes a determination because the iszerofunc is total: it returns a real bool, never `None`, so PASS 2/3 are unreachable). The scan structure is the same lowest-index loop (I); the *predicate* `is_genuinely_zero` is the deep model of the real `iszerofunc` (A-reference, §A3). |
| A3 | `is_genuinely_zero(col[i])` decides "skip / not a pivot" | `_is_zero_after_expand_mul(x)` ≡ `expand_mul(x) == 0` | **A-reference** | the changed zero-test is modeled **deeply** by `is_genuinely_zero` (the spelled-out total decision over status codes in the `pure` region); there is **no consumed `@ContractOnly`** for it. The deep model is validated **== the real callee** out-of-band by G-AX: `axiom_check.py` runs `expand_mul(x) == 0` on a literal zero, genuine non-zeros, and the issue's pseudo-zeros (numerator expands to 0 over a non-zero denominator) and asserts agreement with `is_genuinely_zero(code(x))`. mapping.md §3.1. |
| A4 | `return -1` when the whole column vanishes | `if pivot_pos == None: return S.Zero` | R | `-1` ("no pivot") ↔ `pivot_pos is None`; the determinant contribution of a no-pivot minor is `S.Zero`. The postcondition `(Result()==-1) == (first_usable(...)==len(col))` pins exactly this case — the singular-matrix case the F2P test (`M(5/6/7).det() == 0`) exercises. |
| A5 | `return i` (the chosen index) | `pivot_pos` (consumed at `:195`) | R | only `pivot_pos` flows into the control decision (`== None?`); `pivot_val` and the assumed/newly-determined fields are unused by the determinant control flow, so the model carries the index alone (mapping.md §2). |

The discriminating content of the change — *which entries count as zero when
choosing a pivot* — lives in the predicate `is_genuinely_zero` (model) ⇔
`_is_zero_after_expand_mul = (expand_mul(x) == 0)` (real). The pre-patch
`_find_pivot` instead used Python truthiness `if val:` (`struct_truthy`,
mapping.md §3.2), which accepts a structurally non-trivial **pseudo-zero** —
exactly the `(pivot*x − y*z)/cumm` entries that arise in the singular matrices of
the issue and that `bool(...)` reports truthy. `model_prepatch.py` reproduces
that buggy test (`if col[i] != 0:` ≡ `struct_truthy`) and **fails** the
postcondition `(Result()==-1) == (first_usable(ToSeq(col),0)==len(col))`: on an
all-vanishing column containing a pseudo-zero it returns that index instead of
`-1`, i.e. it picks a bad pivot where the spec demands "no pivot" — precisely the
bug the F2P test senses (`det == 0` vs `nan`). (G-DIFF.)

## B. No kind-3 (unexpressible-changed-op) steps
Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — the pivot zero-test — is modeled **deeply** (`is_genuinely_zero`, a
total decision over the entry status codes, consumed by `lowest_live_index`), not hidden
behind an axiom about the function under change. There is **no consumed axiom**
in this bundle: the only kind-A item is the **A-reference** `is_genuinely_zero`,
which G-AX validates against the real `expand_mul(x) == 0`. (mapping.md §3.)

## C. The randtest.py site (no refinement step)
The gold patch also threads an optional `tolerance=None` kwarg through
`random_complex_number → nsimplify` (`sympy/utilities/randtest.py`). With the
default `tolerance=None` this is byte-for-byte the prior behaviour, no caller in
the repo passes `tolerance`, and no test in the test_patch nor the F2P test
`test_determinant` exercises it (mapping.md §4). It is an inert,
default-preserving addition with no observable differential, so it carries no
modeled contract and contributes no refinement row. `patch.diff` ships it
verbatim only so the applied diff equals the gold (G-RESOLVE).

## D. verify(model) ⇒ resolved
`lowest_live_index` verifies only if it returns the lowest index whose entry does **not**
vanish after expansion (A2/A3) and returns `-1` exactly when the whole column
vanishes (A4) — the singular-column case. By R (matrix-column ↔ `List[int]`,
`pivot_pos is None` ↔ `-1`, the 4-tuple reduction) the verified scan equals
`_find_reasonable_pivot(mat[:,0], iszerofunc=_is_zero_after_expand_mul)`'s pivot
selection on the entries the F2P matrices produce; by G-AX the deep model
`is_genuinely_zero` equals the real `expand_mul(x) == 0` (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited zero-test — and the gold patch resolves: `M(n).det()`
for the singular `M(5/6/7)` returns `0` instead of raising the `Invalid NaN
comparison` (G-RESOLVE). The single trust point is exactly PLAN §1.1 refinement
fidelity + the one A-reference's G-AX soundness; there is no consumed axiom.
