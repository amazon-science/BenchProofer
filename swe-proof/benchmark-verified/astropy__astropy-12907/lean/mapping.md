# mapping.md — astropy__astropy-12907

## Symbol binding (base_commit d16bfe05a744909de4b27f5875fe0d4ed41ce607)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_direct_sum` / `problem_spec_direct_sum` | `_cstack(left, right)`, the **array/array branch** (the `else` clauses) | `astropy/modeling/separable.py:219-247` |
| (impl op) `cleftRow` block placement | `cleft = np.zeros((noutp, left.shape[1])); cleft[:left.shape[0], :left.shape[1]] = left` | `separable.py:239-240` |
| (impl op) `crightRow` block placement (the fixed line) | `cright = np.zeros((noutp, right.shape[1])); cright[-right.shape[0]:, -right.shape[1]:] = right` | `separable.py:244-245` |
| (impl op) row concatenation | `np.hstack([cleft, cright])` | `separable.py:247` |
| `noutp = lout + rout` | `_compute_n_outputs(left, right)` (array case: `left.shape[0] + right.shape[0]`) | `separable.py:105-127, 234` |

`_cstack` is the handler for the `&` operator in `_operators` (`separable.py:316`).
Inside `_separable` (`separable.py:290-311`) the operator handlers are *always*
invoked on already-computed correlation arrays (`sepleft`/`sepright`), never on
`Model` objects — so the array/array branch is the only path exercised on
nested compound models, and is exactly the path the bug lives on.

## Type bijection (G-CONF / G-AX use this)

| Python | Lean | notes |
|---|---|---|
| 2-D `np.ndarray` of shape `(rows, cols)`, entries in {0,1} | `List (List Nat)` — outer = rows, each inner = one row of `cols` entries | a row's `0` ↔ independent, nonzero ↔ dependent |
| `left.shape[0]` | `left.length` | output count of left block |
| `left.shape[1]` | `lin` (precondition: every row of `left` has length `lin`) | input width of left block |
| `right.shape[0]` | `right.length` | output count of right block |
| `right.shape[1]` | `rin` (precondition: every row of `right` has length `rin`) | input width of right block |
| `np.zeros((·, k))` row | `zeroRow k = List.replicate k 0` | |
| `np.hstack([rowL, rowR])` (per row) | `rowL ++ rowR` | |

The matrices fed to `_cstack` are rectangular by construction (`_coord_matrix`
/ recursive results), so the `(∀ r ∈ left, r.length = lin)` and
`(∀ r ∈ right, r.length = rin)` preconditions in `correct_direct_sum` hold.

## Callee provenance / flag deps

None consumed. The combinator is modeled deeply (block-diagonal placement is
spelled out element-wise); no unchanged callee's behavior is axiomatized.
`_compute_n_outputs` is inlined as `left.length + right.length` (the array
case), not axiomatized. → no `opaque`/`axiom` decls; `axiom_check.py` is a skip
stub.

## G-CONF fuzz seed (pinned)

`seed = 12907` (used in `conformance_check.py`). Dimensions fuzzed:
`lout, rout ∈ [0,6]`, `lin, rin ∈ [0,6]`, entries ∈ {0,1}; ≥10⁵ cases.
