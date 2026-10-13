# mapping.md — sympy__sympy-13877

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1659712001810f5fc563a443949f8e3bb38af4bd`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `sympy/matrices/matrices.py` (the symbolic-determinant
inner pivot-selection step) and `sympy/utilities/randtest.py` (a behaviour-
preserving signature extension — site B below).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectPivot (col : Array Entry)` | the inner pivot-selection step of `_eval_det_bareiss` — `sympy/matrices/matrices.py:165` (changed call site at body line 195, inside the nested `bareiss`) | the modeled changed function: pick the first column entry usable as a pivot |
| `Entry.litNonzero` | `bool(x)` truthiness of a scalar entry `x` (the cheap structural recogniser used by the pre-patch inner scan, `matrices.py:178-184` + `:195`) | one of an entry's two zero observations |
| `Entry.mathNonzero` *(deep-model reference — A-reference)* | `not _is_zero_after_expand_mul(x)`, i.e. `expand_mul(x) != 0` — `sympy/matrices/matrices.py:42-46` post-patch, supplied to `_find_reasonable_pivot` (`matrices.py:4067`) as `iszerofunc` | the decisive zero recogniser the post-patch scan uses |
| `consistent (col)` *(A-reference invariant)* | the sympy fact that `expand_mul(x) != 0 ⟹ bool(x)` for every scalar entry (equivalently: a literal/numeric zero is also zero after expansion) | the require relating the two recognisers |
| `PivotResult` | the `(pivot_offset, pivot_val, _, _)` 4-tuple of `_find_reasonable_pivot` (only `pivot_offset`/`found` are observable for the fix) — `matrices.py:4076` | result carrier: whether a pivot exists and at which index |

The pre-patch repo construct the change removes (refinement audit only, not in the
consumer spec view): the nested helper `_find_pivot(l)` (`matrices.py:178-184`),
which scans for the first `bool(val)`-truthy entry and is replaced by
`_find_reasonable_pivot(mat[:, 0], iszerofunc=_is_zero_after_expand_mul)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a matrix column `mat[:, 0]`: a finite sequence of scalar sympy `Expr` | `Array Entry` | the `k`-th sympy entry `x` ↔ `Entry` `⟨bool(x), expand_mul(x) != 0⟩`; `len(col)` ↔ `col.size`; the column order is preserved (index `k` ↔ `k`) |
| a scalar sympy `Expr` `x` | `Entry` | `x` ↔ `⟨litNonzero := bool(x), mathNonzero := (expand_mul(x) != 0)⟩`. The two booleans are the only observations the pivot scan makes of `x` (it never inspects the value otherwise — `pivot_val` is irrelevant to which index is chosen). |
| `pivot_offset is None` (no pivot) | `PivotResult.found = false` | `None` ↔ `found=false`; the index field is then unconstrained |
| `pivot_offset = k` (pivot at row `k`) | `PivotResult` `⟨true, k⟩` | `found=true ∧ idx=k` |

Only **non-Float** columns are modeled — i.e. columns the pre-patch crash arose
on (symbolic / integer entries). `_find_reasonable_pivot`'s leading Float branch
(`matrices.py:4090-4101`, partial pivoting by magnitude) fires only when every
entry is `Float`/`Integer` with at least one `Float`; for symbolic columns the
function reaches PASS 1, and because the supplied `iszerofunc` is **decisive**
(returns `True`/`False`, never `None`) PASS 1 alone selects the first non-zero
entry — there is no PASS 2/PASS 3 fallthrough. mapping.md §3 / G-CONF restrict the
fuzz domain to this modeled branch.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `mathNonzero` / `consistent` deep model ↔ `_is_zero_after_expand_mul` (A-reference)
**Callee:** the post-patch module function `_is_zero_after_expand_mul(x)` =
`expand_mul(x) == 0` (`matrices.py:42-46`), passed as `iszerofunc` to the
unchanged `_find_reasonable_pivot`. The decisive zero recogniser is modeled
**deeply** by the `Entry.mathNonzero` field; there is **no consumed axiom** about
the determinant or the pivot finder. The two modeled facts, validated against the
real callees by `axiom_check.py` (G-AX):

1. **definition faithfulness** — for every scalar `Expr` `x`:
   `_is_zero_after_expand_mul(x) == (expand_mul(x) == 0)`, and this is always a
   Python bool (decisive), so the modeled `mathNonzero = ¬ iszerofunc(x)` is well
   defined (no `None`);
2. **`consistent`** — `mathNonzero → litNonzero`, i.e.
   `expand_mul(x) != 0 ⟹ bool(x)`. A scalar that is still nonzero after expansion
   cannot be the literal/numeric zero, so `bool(x)` is truthy. (The converse
   FAILS — `bool(x)` truthy ↛ `expand_mul(x) != 0` — which is exactly the
   discriminating case the issue exhibits: a structurally-nonzero entry that is
   algebraically zero, e.g. `a*(a-1) - a*a + a`.)

**End-to-end corroboration (G-AX):** with the patched code the issue's matrices
`M(n) = [[i + a*j]]` give `M(5).det() == M(6).det() == M(7).det() == 0` and no
`Invalid NaN comparison` is raised — the FAIL_TO_PASS observation.

`_find_reasonable_pivot` itself is an **unchanged** callee; on the modeled
non-Float, decisive-`iszerofunc` branch its observable output equals
"first index `k` with `expand_mul(col[k]) != 0`, else `None`" — the behaviour
`selectPivot` transliterates (validated by G-CONF, §4).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13877`** so the
consumer-side verdict (§11.3) is reproducible. It builds the R/I shadow of the
`selectPivot` `do` block in Python — the first-index scan whose per-entry test is
the **real** callee `_is_zero_after_expand_mul` (the A-reference predicate, left
as the real repo callee, not re-modeled) — and diffs it against the ORACLE: the
real patched `_find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul)`
over fuzzed symbolic/integer columns (the modeled non-Float branch). Exit 0 iff
every column agrees on `(found, idx)`.

## 5. Site B — `random_complex_number` (behaviour-preserving, not modeled)

Gold also touches `sympy/utilities/randtest.py:16`: `random_complex_number` gains
an optional `tolerance=None` keyword forwarded to `nsimplify`. With the default
`tolerance=None` the new body `nsimplify(A, rational=True, tolerance=None)` is
**identical** to the old `nsimplify(A, rational=True)` (nsimplify treats a `None`
tolerance exactly as an omitted one — `simplify.py:1271`), so every existing
caller — including the determinant path and all PASS_TO_PASS / FAIL_TO_PASS tests
— observes byte-identical behaviour. It is a strictly-additive signature
extension, not an observable behaviour change, and is therefore carried in
`patch.diff` (gold verbatim, for G-RESOLVE) but not separately modeled. See
refinement.md §B.
