# mapping.md — sympy__sympy-23413

## Symbol binding (file:line @ base_commit `10de1a18a0`)

Modeled function: `_hermite_normal_form(A)` —
`sympy/polys/matrices/normalforms.py:177-248`. The change is the OUTER
row-processing loop, lines **207-217** (pre-patch) → **207-224** (post-patch).

| Lean symbol | Python | file:line |
|---|---|---|
| `implementation_hermiteNormalForm` / `problem_spec_hermiteNormalForm` / `correct_hermiteNormalForm` | `_hermite_normal_form` (outer loop) | normalforms.py:177-248 |
| `A0 : Mat` (`List (List Int)`) | `A = A.to_dense().rep.copy()` — the dense integer row carrier | normalforms.py:212 |
| `m n : Nat` | `m, n = A.shape` | normalforms.py:210 |
| `k : Nat` | `k` (leftmost pivot column pointer, init `n`) | normalforms.py:216 |
| `rowsDesc m` = `(List.range m).reverse` | `range(m - 1, -1, -1)` (post-patch row order) | normalforms.py:217 |
| `if k = 0 then break` | `if k == 0: break` (added) | normalforms.py:218-223 |
| `step A i k` | the per-row body: `k -= 1`; inner col clears `add_columns`; sign fix; `if b==0: k += 1` else reduce-right | normalforms.py:218-245 |
| `sliceCols A k` | `DomainMatrix.from_rep(A)[:, k:]` | normalforms.py:248 |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | note |
|---|---|---|
| `DomainMatrix` over `ZZ`, dense rep | `Mat := List (List Int)` | row-major integer rows |
| `A.shape == (m, n)` | `(m n : Nat)` | shape carried explicitly |
| `k` pointer | `Nat` | leftmost placed-pivot column index |
| per-row reduction (`add_columns`, `_gcdex`, `//`, sign fix) | `opaque step : Mat → Nat → Nat → Mat × Nat` | UNCHANGED; signature only |
| `[:, k:]` column slice | `opaque sliceCols : Mat → Nat → Mat` | UNCHANGED; signature only |

## Callee provenance + flag deps

- `step` — bundles the UNCHANGED per-row reduction (`add_columns` at
  normalforms.py:40-46, `_gcdex` at 156-174, floor-div `//`, the `b < 0` sign
  normalisation, and the `if b == 0: k += 1` pointer restore). Its net effect on
  the pointer is either `k -> k-1` (a pivot was placed) or `k -> k` (row placed
  no pivot: the `k += 1` cancels the `k -= 1`). This dichotomy is the only thing
  the row-selection change interacts with, so `step` is carried opaquely and NO
  property of it is consumed. No flag dependency.
- `sliceCols` — `DomainMatrix.from_rep(A)[:, k:]`, UNCHANGED column slice,
  carried opaquely.
- No callee raises on the modeled path (`A.domain.is_ZZ` guard at
  normalforms.py:205 is a precondition, not modeled).

## G-CONF fuzz seed

Pinned seed **23413** (`conformance_check.py` SEED). Shapes fuzzed over
`m, n ∈ [0, 8]`, plus the edge corpus (m>n, m<n, m=n, empty, single).
