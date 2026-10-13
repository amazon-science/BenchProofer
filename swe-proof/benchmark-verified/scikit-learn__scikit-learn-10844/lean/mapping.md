# mapping.md — scikit-learn__scikit-learn-10844

Instance: `scikit-learn/scikit-learn`, base_commit `97523985b39ecde369d83352d7c3baf403b60a22`.
spec_provenance: **cold** (derived from `problem_statement` + gold `patch` + repo
source at base_commit only).

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `problem_spec_fmIndex` / `implementation_fmIndex` | body of `fowlkes_mallows_score` from the contingency matrix onward | `sklearn/metrics/cluster/supervised.py:792`–`860` (changed lines 855, 859) |
| `cmTk M`  | `tk = np.dot(c.data, c.data) - n_samples` | line 856 |
| `cmPk M`  | `pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples` | line 857 |
| `cmQk M`  | `qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples` | line 858 |
| `totalZ M` | `n_samples` ( = total number of label pairs = sum of all contingency entries ) | line 853 / 855 |
| (input) `M : List (List ℕ)` | the integer contingency matrix `c` produced by `contingency_matrix(labels_true, labels_pred, sparse=True)` | line 855 |

## The model boundary (why no opaque callee)

The fix is entirely DOWNSTREAM of two UNCHANGED callees:
- `check_clusterings` (`supervised.py:34`) — validates that the two label arrays
  are 1-D and equal length; returns them unchanged. No behaviour relevant to the
  result value; not modeled.
- `contingency_matrix` (`supervised.py:53`) — builds the integer co-occurrence
  matrix `c` (`C[i,j]` = #samples in true-class `i` and predicted-cluster `j`).
  Unchanged. Its OUTPUT is taken as the modeled function's input carrier
  `M : List (List ℕ)`. We model the computation of the index FROM the matrix.

Because the matrix is the primitive input (the domain of the modeled function),
neither callee is declared `opaque` and **no `axiom _prop` is consumed** — the
axioms region is empty. This avoids a dead axiom (SPEC_GUIDE §0.7, §3).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| integer contingency matrix `c` (dense, shape `(R, K)`) | `M : List (List ℕ)` | row-major: `M[i][j] = C[i,j]`; `M.length = R`, each row length `K` |
| `c.data` (nonzero entries of sparse `c`) | nonzero entries of `M.flatten` | sum of squares over nonzero ≡ sum of squares over all (zeros contribute 0) |
| `c.sum(axis=1)` (row sums) | `M.map (·.sum)` | per-row totals |
| `c.sum(axis=0)` (column sums) | `M.transpose.map (·.sum)` | per-column totals |
| `n_samples` | `totalZ M = (M.flatten.map (Int.ofNat)).sum` | total sample count = Σ all entries |
| `tk`,`pk`,`qk` — the numpy int64 SCALARS the library holds the three counts in | `cmTkW`,`cmPkW`,`cmQkW : BitVec 64` | one signed machine word each, the same fixed width the library uses. `BitVec.ofInt 64` is the store into that word. A numpy int64 multiply of two such scalars is the `BitVec 64` multiply `cmPkW M * cmQkW M` — reduced mod 2⁶⁴ — and nothing else. |
| `int(x)` applied to such a scalar (widening to Python's unbounded `int`) | `(·).toInt : BitVec 64 → ℤ` | reads a word back as the integer it stands for; on a value inside the window this is the identity on the count |
| Python `int` (unbounded), i.e. the mathematical count itself | `cmTk`,`cmPk`,`cmQk : ℤ` | exact and unbounded. **`*` on `ℤ` may NOT be refined to a fixed-width multiply.** The faithful counterpart of a `ℤ`/`ℝ` product of two counts is a Python-`int` product — `np.sqrt(int(pk) * int(qk))`, or `math.sqrt` over `int`s — never `np.sqrt(pk * qk)` on the int64 scalars. That last one is the `BitVec 64` product, a different term, and `problem_spec_fmIndex` refutes it. |
| float `/` on two such scalars | `fdiv : ℝ → ℝ → Option ℝ` | **partial.** IEEE division names a real number only when the divisor is nonzero; `x/0.` yields `nan`/`inf`, which is not the name of any real. `fdiv x y = none` on `y = 0` records exactly that non-naming. Mathlib's own `/` is TOTAL (`x / 0 = 0`) and is therefore NOT the faithful counterpart of a float divide — see "Why the carrier is partial" below. |
| `np.sqrt` of such a quantity | `fsqrt : ℝ → Option ℝ` | **partial.** `np.sqrt` of a negative argument is `nan` (plus a RuntimeWarning), not a real. `fsqrt x = none` on `x < 0`. Mathlib's `Real.sqrt` is TOTAL (`Real.sqrt` of a non-positive argument is `0`) and so is likewise not the faithful counterpart on its own. |
| float `*` | `*` on `ℝ` | exact real multiplication; total on both sides, so no wrapper is needed. `nan * x = nan` is carried by the `Option` bind, not by the multiply. |
| `score` as returned by the function | `result : Option ℝ` | `some v` ⟺ the call returned the finite float naming the real `v`; `none` ⟺ the call returned a value that names no real number (`nan`, `±inf`). The three-way IEEE outcome collapses to the two-way "did this name a real" because every assertion the workload makes about the score is an assertion that it *is* a particular real. |

`tk = Σ_e e² − n`, `pk = Σ_k (colsum_k)² − n`, `qk = Σ_i (rowsum_i)² − n`, with
`n = Σ_e e`. For any `ℕ`-matrix `e²≥e`, `colsum²≥colsum`, `rowsum²≥rowsum`, so
`cmTk, cmPk, cmQk ≥ 0` (provable, no precondition needed for non-negativity).

## Preconditions: rectangularity, and each count fits one word
`correct_fmIndex` carries two hypotheses. The first is that `M` is
rectangular: `∃ w, ∀ r ∈ M, r.length = w`. This is the genuine shape of every
`contingency_matrix` output (a dense `R×K` grid), and it is what makes the
`transpose`-based column sums equal the real `c.sum(axis=0)` (on a ragged list
`List.transpose` is not column sums, and `Σ colsums = Σ entries` can fail, so
`pk` could even go negative). No `0 < cmPk`/`0 < cmQk` precondition is imposed:
under rectangularity, `pk = Σ colsum² − Σ colsum ≥ 0` and likewise `qk,tk ≥ 0`,
and crucially `tk ≤ pk` and `tk ≤ qk` (each entry lies in some column/row, and
`Σ_in-group e² ≤ (Σ_in-group e)²`), so `tk ≠ 0 ⟹ pk > 0 ∧ qk > 0`. Hence the
`tk = 0` branch already covers every zero-denominator input the real code
handles via `if tk != 0. else 0.` — the spec is faithful on the FULL domain of
real contingency matrices, with no excluded inputs an impl could exploit.

The second hypothesis is `inWord (cmTk M) ∧ inWord (cmPk M) ∧ inWord (cmQk M)`:
each of the three counts, INDIVIDUALLY, sits in the signed window `[-2⁶³, 2⁶³)`
of one machine word. That is exactly what the patched code needs and no more — it
forms only `tk/pk` and `tk/qk`, each of whose operands is a single count — and it
is what makes the three words value-transparent (`tkW_val`/`pkW_val`/`qkW_val`),
so the obligation is the exact index. **Nothing is assumed about the PRODUCT
`cmPk M * cmQk M`**, and that asymmetry is deliberate and load-bearing: the F2P
workload's own matrix satisfies all three `inWord` hypotheses
(`cmTk = 3003497866`, `cmPk = 5152663196`, `cmQk = 3294371982`) while its marginal
product `≈ 1.70·10¹⁹` does NOT fit, so the obligation is live precisely where the
overflow is. A hypothesis mentioning the product would go vacuous there and
re-admit the pre-patch arithmetic.

## Why the carrier is partial (`Option ℝ`, not `ℝ`)

The function's guarded shape — a zero test on `tk` whose false branch does the
dividing — is behaviour, and a spec on an `ℝ` carrier cannot see it. Mathlib's
`/` and `Real.sqrt` are total: `x / 0 = 0` and `Real.sqrt` of a non-positive
argument is `0`. So on an `ℝ` carrier the guarded assembly and the guard-erased
one are not merely hard to tell apart, they are **the same function**. Machine
checked, with `gold` the guarded assembly and `guardless` the same expression
with the zero test deleted:

```
theorem obstruction : gold = guardless := by
  funext M; unfold gold guardless
  by_cases h : (cmTkW M).toInt = 0
  · rw [if_pos h, h]; simp          -- √(0/p) · √(0/q) = 0 · 0 = 0, totally
  · rw [if_neg h]
```

Consequence: **no** predicate on `(M, result : ℝ)` can hold of one and fail of
the other. The weakness is not a missing conjunct; it is an observable the model
erased. Adding clauses to an `ℝ`-carrier spec is provably futile.

The repair restores the observable. `fdiv`/`fsqrt` are the library's division
and root as the *partial* operations they actually are, and the carrier gains a
`none` to receive "this named no real number". Then the postcondition's demand
that a zero-agreement input yield the real number `0` — i.e. `some 0`, not
`none` — has content: it is satisfied by the guarded assembly and violated by
the guard-erased one, at the fully admissible matrix `[[1,1,1,1,1,1]]`
(`tk = 0`, `pk = 0`, `qk = 30`), where erasing the guard divides `0` by `0`.

This is faithful in both directions and not over-fitted:
- **TRUE of the real patched function.** With the patch applied, a
  zero-agreement input returns the float `0.0`, never `nan`.
- **FALSE of guard erasure**, which is what the audit exhibited.
- **Does not pin the guard's syntax or position.** `pos-branch-reorder`
  (zero test written last) verifies; `pos-inline-cheapest` verifies.
- **Does not pin the reassociated formula as the only route.** The
  exact-arithmetic echo `pos-specform-product` — one root over the exact product
  of unbounded counts — verifies, because it too names a real everywhere the
  spec demands one. What it may not do is form the product *in one machine word*;
  that is the other half of the behaviour, carried by the `BitVec 64` row above.

### The one shape that still verifies, and why that is correct

An assembly that erases the zero test but uses Mathlib's TOTAL `/` and
`Real.sqrt`, wrapping the outcome in `some`, still verifies. That is not a
residual hole: on the entire admissible domain it is **extensionally equal** to
the frozen assembly, machine-checked (`E_eq_gold_on_admissible`). On
`(cmTkW M).toInt = 0` both yield `some 0` — the frozen one by its branch, the
total one because `√(0/P) · √(0/Q) = 0` whether or not a marginal count vanishes.
On `≠ 0`, `P_pos`/`Q_pos` give both marginal counts strictly positive, so every
`fdiv`/`fsqrt` step in the frozen assembly takes its `some` branch and the two
agree term for term. Two equal functions cannot be separated by any
postcondition, so rejecting it would be SPEC-TOO-STRONG. Its faithful Python
counterpart keeps the library's guard (an unguarded float `0./0.` is `nan`, not
`0`), so its patch resolves. It is retained as the positive
`pos-total-arithmetic-echo` precisely so a later audit does not relitigate it.

The contrast with the `guard-erasure` reject is the whole content of the repair:
that rival erases the guard *while routing through the partial arithmetic* — the
faithful model of the float ops — and is refuted at `[[1,1,1,1,1,1]]`.

## Callee provenance + flag deps
- `sparse=True` is passed to `contingency_matrix`; irrelevant to the modeled
  index value (only affects dense vs sparse representation of the same counts).
- No flag-dependent callee on the modeled path.

## Numeric crux (drives the prepatch discriminator)
Over exact reals `tk/√(pk·qk) = √(tk/pk)·√(tk/qk)` when `tk,pk,qk ≥ 0`,`pk,qk>0`.
The two formulas differ ONLY under fixed-width integer wrapping of the product
`pk·qk`. For the F2P workload the marginal square-sums give
`pk·qk ≈ 1.7·10¹⁹ > 2⁶³−1 (≈9.22·10¹⁸)`, so the int64 product wraps negative and
`np.sqrt` of it is `nan` → the old expression returns `nan`. The fixed expression
never forms the product.

This is why the three counts are carried as `BitVec 64` and not merely as `ℤ`:
the wrapping multiply has to be a term the model OWNS, or the distinction between
the two halves of the patch is inexpressible and the pre-patch line refines an
`ℤ` product unnoticed. With the word type present, the prepatch needs no
hand-rolled fold — it is the honest machine product
`(cmPkW M * cmQkW M).toInt`, whose value at a witness such as `[[54000, 54000]]`
is `-5764417851174206464` (confirmed in numpy), so its root is not a real number
and the postcondition's positive value is unreachable.

## G-CONF fuzz seed (pinned)
seed = `10844`.
