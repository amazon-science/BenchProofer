# refinement.md — scikit-learn__scikit-learn-10844

Operation correspondence between `implementation_fmIndex` (Solution.lean, impl
region) and `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep-model == real callee, G-AX), **I**
(identical concrete op). Every op is R, A, or I.

The gold patch changes two lines of `fowlkes_mallows_score`:
```
- c = contingency_matrix(labels_true, labels_pred, sparse=True)
+ c = contingency_matrix(labels_true, labels_pred, sparse=True).astype(np.int64)
  tk = np.dot(c.data, c.data) - n_samples
  pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples
  qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples
- return tk / np.sqrt(pk * qk) if tk != 0. else 0.
+ return np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.
```
Both edits remove a fixed-width integer overflow: `.astype(np.int64)` widens the
entry/marginal squares away from int32; the reassociation
`tk/√(pk·qk) → √(tk/pk)·√(tk/qk)` removes the product `pk·qk` that overflows
int64. Over exact reals the two formulas are equal (`tk,pk,qk ≥ 0`, `pk,qk>0`),
so a model that held the three counts in unbounded `ℤ` could not tell the two
lines apart at all: the second edit would be a no-op and any reassociation of the
quotient would refine it. The model therefore keeps the counts in the width the
library keeps them in — one signed machine word each, `BitVec 64` — and reads them
back with `.toInt`. Only ops the patched code performs on ONE count at a time
(`tk / pk`, `tk / qk`) stay inside the word; the product `pk·qk` is a `BitVec 64`
multiply, a term the model owns and the postcondition rules out, which is what
makes the second edit a real refinement obligation instead of a rewriting.

| # | `implementation_fmIndex` op | `patch.diff` / source counterpart | tag | note |
|---|---|---|---|---|
| 1 | input `M : List (List ℕ)` | dense int64 contingency matrix `c` (after `.astype(np.int64)`) | **R** | row-major bijection (mapping.md); int64 dense ⇄ exact ℕ entries |
| 2 | `cmTk M = sumSqZ M.flatten - totalZ M` | `tk = np.dot(c.data, c.data) - n_samples` | **R** | `np.dot(data,data)` = Σ over nonzero entries² = Σ over all entries² (zeros add 0); `n_samples` = Σ all entries = `totalZ M` |
| 3 | `cmPk M = sumSqZ (M.transpose.map (·.sum)) - totalZ M` | `pk = np.sum(c.sum(axis=0)**2) - n_samples` | **R** | `c.sum(axis=0)` = column totals = row sums of transpose |
| 4 | `cmQk M = sumSqZ (M.map (·.sum)) - totalZ M` | `qk = np.sum(c.sum(axis=1)**2) - n_samples` | **R** | `c.sum(axis=1)` = row totals |
| 4b | `cmTkW/cmPkW/cmQkW M = BitVec.ofInt 64 (…)` | `tk`, `pk`, `qk` as the int64 scalars numpy leaves them in | **R** | the assignment itself: each count is stored into one signed machine word of the width `.astype(np.int64)` selected |
| 4c | `let tk := (cmTkW M).toInt` (and `pk`, `qk`) | the VALUE of that int64 scalar, as true division widens it | **R** | `.toInt` ⇄ reading the word back / `int(x)`; on an in-window count it is the count |
| 5 | `if tk = 0 then some 0` | `… if tk != 0. else 0.` | **I** | identical branch on the agreement count. `some 0` because the guarded call returns the float `0.0`, which names the real `0` |
| 6a | `fdiv (tk : ℝ) (pk : ℝ)`, `fdiv (tk : ℝ) (qk : ℝ)` | `tk / pk`, `tk / qk` (float true division) | **R** | float division is PARTIAL: it names a real only when the divisor is nonzero. `fdiv _ 0 = none`. Each division has ONE count on each side, so no product of two counts is ever formed in a word — that is precisely the content of the second edit |
| 6b | `fsqrt a`, `fsqrt b` | `np.sqrt(...)` | **R** | `np.sqrt` is PARTIAL: negative argument gives `nan`, not a real. `fsqrt x = none` on `x < 0` |
| 6c | `pure (ra * rb)` | the float `*` joining the two roots | **R** | exact `ℝ` multiply; the `Option` bind carries the propagation that IEEE does via `nan` |

No **A-consumed** and no **A-reference** rows: the only callees on the modeled
path (`check_clusterings`, `contingency_matrix`) are UNCHANGED and produce the
function's input carrier `M`; they are not part of the index computation that the
fix touches, so they are neither axiomatized nor deep-modeled — `M` is primitive.
The axioms region is empty; `axiom_check.py` is a skip stub.

No changed-inexpressible op. The entry/marginal square-sums, the branch and the
reassociated quotient-of-roots are all modeled deeply, and BOTH of the ways the
real arithmetic fails to be the tidy total arithmetic of a textbook are modeled
as terms the model owns:

1. **Fixed width.** The three counts live in `BitVec 64`, so the pre-patch's
   single-word marginal product is a term of the model (`cmPkW M * cmQkW M`)
   rather than something the model cannot say.
2. **Partiality.** Float division and `np.sqrt` are partial — they can return a
   value that names no real number — so the result carrier is `Option ℝ` and the
   two operations are `fdiv`/`fsqrt`. Without this, the guard on line 5 is
   INEXPRESSIBLE: Mathlib's `/` and `Real.sqrt` are total (`x / 0 = 0`, and
   `Real.sqrt` of a non-positive argument is `0`), so on an `ℝ` carrier the
   guarded function and the guard-erased function are literally equal
   (machine-checked by `funext`; see mapping.md "Why the carrier is partial").
   With `Option ℝ`, op 5 is a genuine obligation: at a zero-agreement input the
   result must be the real number `0`, which guard erasure cannot deliver
   because it divides `0` by `0` there.

What stays in exact `ℝ` is only the one float multiply the patched line performs,
and what stays in exact `ℤ` is only the counts' own definitions, which the
patched code computes without overflow by construction of the `inWord`
preconditions.

## Preconditions (faithful + total)
`correct_fmIndex` takes rectangularity of `M` (`∀ r ∈ M, r.length = w`), the shape
of every real contingency matrix, plus `inWord (cmTk M)`, `inWord (cmPk M)`,
`inWord (cmQk M)`: each count, SEPARATELY, fits one signed machine word. That is
the exact domain on which the patched line is claimed correct — it only ever
divides one count by another — and it is not an escape hatch, because the
PRODUCT of the two marginal counts is deliberately left unconstrained. The F2P
workload's matrix satisfies all three (`3003497866`, `5152663196`, `3294371982`,
all `< 2⁶³`) while `pk·qk ≈ 1.70·10¹⁹` does not, so the obligation is live exactly
where the dataset's overflow is; adding a hypothesis about `cmPk M * cmQk M` would
make it vacuous there and re-admit the pre-patch arithmetic.

No `0 < cmPk`/`0 < cmQk` assumption is imposed: under rectangularity `tk ≤ pk` and
`tk ≤ qk`, so a zero marginal count forces `tk = 0` and the `tk = 0` branch
returns `0` — exactly the real code's `if tk != 0. else 0.`. The spec is thus
faithful over the entire domain of in-word contingency matrices (no excluded
inputs beyond the library's own integer width).

## Conformance (G-CONF)
All impl ops are R/I, so `conf_skip=false`. `conformance_check.py` rebuilds the
R/I shadow (`shadow_fmi`) from the real `contingency_matrix` output and diffs the
returned float against the real patched `fowlkes_mallows_score` over the discrete
catalogue (incl. the F2P overflow workload) + 1.2·10⁵ fuzzed label arrays.

## Prepatch discriminator (G-DIFF)
`Solution_prepatch.lean` keeps spec byte-identical and replaces op 6 with the
pre-patch arithmetic — one root over the marginal product taken in a single word,
`fdiv tk (fsqrt ((pk * qk).toInt))`, where `pk * qk` is the `BitVec 64` multiply,
i.e. the honest numpy int64 product of the two marginal scalars with no
hand-rolled reduction anywhere. On the F2P workload `pk·qk ≈ 1.7·10¹⁹` exceeds
`2⁶³−1`, so the word holds a negative value, `fsqrt` of it is `none`, and the
result names no real where the spec demands the positive index. The prepatch
therefore cannot satisfy `problem_spec_fmIndex` and its `correct_fmIndex` is
unclosable (the carried gold proof fails to typecheck against the wrapping impl).
The same term is what refutes the reassociation-erasing rival in general: at
`M0 = [[54000, 54000]]` all three counts are in window (`T = P = 5831892000`,
`Q = 11663892000`) while `(cmPkW M0 * cmQkW M0).toInt = -5764417851174206464`, so
any impl that forms the marginal product in a word returns `0` where the spec
demands a positive value.
