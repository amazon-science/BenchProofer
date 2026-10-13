# mapping.md — sympy__sympy-13877

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1659712001810f5fc563a443949f8e3bb38af4bd`, states the type
abstraction, and gives the provenance of each axiom / deep-model reference.

Repo file under change: `sympy/matrices/matrices.py` (the determinant routine).
(The gold patch also adds an unused-by-the-tested-behaviour optional `tolerance`
kwarg to `sympy/utilities/randtest.py:random_complex_number`; see §4 — it is a
pure additive default-preserving parameter, not exercised by FAIL_TO_PASS.)

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `lowest_live_index(col)` | the pivot-search step of `_eval_det_bareiss.bareiss` — the local helper `_find_pivot` (`sympy/matrices/matrices.py:178-183`) and the line that consumes it `pivot_pos, pivot_val, _, _ = _find_pivot(mat[:, 0])` (`:195`) → post-patch `_find_reasonable_pivot(mat[:, 0], iszerofunc=_is_zero_after_expand_mul)` (`:4067`) | the modeled changed function: given a matrix column, return the index of the pivot to use (or "no pivot"). Modeled on the **non-Float** columns only (the decisive-`iszerofunc` PASS-1 branch) — see the modeled-slice paragraph in §2. |
| `is_genuinely_zero(e)` *(deep-model reference — A-reference)* | `_is_zero_after_expand_mul(x)` ≡ `expand_mul(x) == 0` (added by the patch at `sympy/matrices/matrices.py:42`, calling `sympy.core.function.expand_mul`, `sympy/core/function.py:2347`) | pure spec: does the column entry vanish after `expand_mul`? The new zero-test the fixed pivot finder uses. Validated `== expand_mul(x)==0` by axiom_check.py (G-AX). |
| `struct_truthy(e)` | Python truthiness `if val:` used by the pre-patch `_find_pivot` (`sympy/matrices/matrices.py:179-180`) — `bool(val)` / `val.__bool__` on a SymPy expression | pure spec: the pre-patch "is this entry a usable pivot?" test (structural, not mathematical). Only referenced by the prepatch skeleton + the refinement audit; NOT used by the model.py contract. |
| `NO_PIVOT` (`-1`) | the `pivot_pos == None` / `return S.Zero` outcome (`sympy/matrices/matrices.py:196-197`) | sentinel: the column has no usable pivot, so this Bareiss minor contributes a zero determinant |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a **non-Float** matrix column `mat[:, 0]` — a finite sequence of SymPy expressions, not all of which are machine-precision numbers (see the modeled-slice paragraph below) | `List[int]` of per-entry *zero-status codes* | entry `k` of the column ↔ `col[k]`; `len(column)` ↔ `len(col)`; the lowest-index search ↔ the ascending loop index |
| one SymPy expression entry `x` of the column | one `int` code with the bijection below | each `x` is classified by the two observable predicates the pivot search uses |
| `_is_zero_after_expand_mul(x)` ≡ `expand_mul(x) == 0` (the fix's zero test) | `is_genuinely_zero(e)` ≡ `e <= 0` | see code bijection |
| Python `if x:` truthiness (the pre-patch test) | `struct_truthy(e)` ≡ `e != 0` | see code bijection |
| `(pivot_pos, pivot_val, _, _)` 4-tuple → only `pivot_pos` is consumed (`:195`) | a single returned index `int` (`-1` for "no pivot") | the patch immediately reduces the 4-tuple to `pivot_pos`; the rest is unused by the determinant control flow |

**Entry code bijection** (the carrier abstraction — chosen so the two predicates
the two pivot finders evaluate are both expressible, and they DISAGREE exactly on
the bug-triggering class):

| `int` code `e` | SymPy entry it abstracts | `struct_truthy(e)` = `e != 0` (pre-patch `if val:`) | `is_genuinely_zero(e)` = `e <= 0` (fix `expand_mul==0`) | usable pivot? (`not is_genuinely_zero`) |
|---|---|---|---|---|
| `0` | a literal/atomic zero (e.g. `S.Zero`) | `False` (falsy) | `True` | no |
| `> 0` | a genuinely non-zero expression (e.g. the symbol `a`, an integer ≠ 0) | `True` | `False` | **yes** |
| `< 0` | a **pseudo-zero**: a structurally non-trivial expression (a quotient `p/q` whose numerator expands to 0) that is `bool`-truthy yet `expand_mul(x) == 0` | `True` (truthy ⇒ pre-patch wrongly accepts it) | `True` | no |

The pre-patch `_find_pivot` accepts any `struct_truthy` entry, so it can select a
`< 0` pseudo-zero as pivot — the division by a pseudo-zero is what produces the
`nan` / `Invalid NaN comparison` in the issue. The fixed finder uses
`is_genuinely_zero`, so it accepts only `> 0` entries (and reports "no pivot" when
the whole column is `≤ 0`). The two predicates are identical on `0` and `> 0`
codes and differ precisely on the `< 0` pseudo-zero class — the bug class.

**Modeled slice: non-Float columns only.** The carrier abstracts each entry to
its zero-status code and nothing else — in particular it carries **no numeric
magnitude**. This is exact for every column the changed behaviour is observable
on: for a column that is not entirely machine-precision numeric,
`_find_reasonable_pivot` falls through its leading numeric branch into PASS 1,
and because the supplied `iszerofunc` (`_is_zero_after_expand_mul`) is
**decisive** (always returns a real bool, never `None`; §3.1) PASS 1 alone
returns the lowest index with `iszerofunc(x) == False` — exactly
`lowest_live_index` under the code bijection (PASS 2/3 are unreachable). The
one branch NOT modeled is `_find_reasonable_pivot`'s leading numeric branch
(`matrices.py:4092-4104` post-patch): when every entry is `Float`/`Integer`
with at least one `Float` it picks the entry of **largest absolute value**
(numerical partial pivoting), a choice the magnitude-free carrier cannot
express. This exclusion is principled, not a silent mismatch:

  * *unobservable in the graded behaviour* — the Bareiss determinant **value**
    does not depend on which non-zero pivot index is chosen (pivot choice
    affects only numerical conditioning), so no FAIL_TO_PASS / PASS_TO_PASS
    outcome distinguishes the max-norm choice from the lowest-index choice;
  * *off the bug's path* — the issue's matrices `M(n) = [[i + a*j]]` are
    symbolic (polynomials in `a`), and every elimination column they produce
    is non-Float, i.e. inside the modeled slice; the F2P test
    (`test_determinant`) exercises only integer/symbolic matrices;
  * *the discriminator is unaffected* — the pre-/post-patch disagreement (the
    `< 0` pseudo-zero class) arises only for symbolic entries; an all-Float
    column has no pseudo-zeros, so both pivot tests agree there.

`lowest_live_index` therefore models the pivot-index selection on the
non-Float (PASS-1) branch; the numeric partial-pivoting branch is outside the
abstraction boundary, exactly as in the sibling formalisations of this
instance.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `is_genuinely_zero` deep model ↔ `expand_mul(x) == 0` (A-reference)
**Callee:** the fix's new `_is_zero_after_expand_mul(x): return expand_mul(x) == 0`
(`sympy/matrices/matrices.py:42` post-patch), wrapping
`sympy.core.function.expand_mul` (`sympy/core/function.py:2347`), which is
`sympify(expr).expand(deep=True, mul=True, power_exp=False, power_base=False,
basic=False, multinomial=False, log=False)`. The changed zero-test is modeled
**deeply** by the `@Pure` `is_genuinely_zero` (a total decision over the entry
codes); there is no consumed `@ContractOnly` for it. It is validated equal to the
real callee out-of-band by axiom_check.py (G-AX): on representative SymPy entries
— a literal `0`, genuinely non-zero atoms/symbols, and the issue's actual
pseudo-zero quotients (numerator expands to 0) — `_is_zero_after_expand_mul(x)`
must equal `is_genuinely_zero(code(x))`. The key facts the model encodes:
`expand_mul` returns `0` for a quotient whose numerator expands to 0 (the
pseudo-zeros) and for a literal zero, and a non-zero result for a genuine
non-zero entry. Docs: https://docs.sympy.org/latest/modules/core.html#sympy.core.function.expand_mul.

### 3.2 `struct_truthy` ↔ pre-patch `if val:` (refinement-audit only)
`struct_truthy(e) ≡ e != 0` models Python truthiness `bool(x)` on a SymPy
expression as used by the removed `_find_pivot`. A literal SymPy zero is falsy
(`e == 0`); any structurally non-trivial expression — including a pseudo-zero
quotient — is truthy (`e != 0`). This predicate is the pre-patch pivot test; it
appears only in `model_prepatch.py` and this audit, never in the frozen contract.

## 4. The randtest.py site (not part of the tested behaviour)
`random_complex_number(..., tolerance=None)` adds an optional kwarg threaded into
`nsimplify(..., tolerance=tolerance)`. With the default `tolerance=None` the call
is byte-for-byte the old behaviour (`nsimplify(A, rational=True)`), so it changes
nothing observable. `random_complex_number` is called only from
`sympy/core/expr.py:450` (`Expr._random`) with no `tolerance` argument, and no
test in the test_patch nor the FAIL_TO_PASS test `test_determinant` passes a
`tolerance`. It is therefore an inert, default-preserving addition shipped
alongside the real fix and carries no modeled contract (no differential witness
is observable for it). `patch.diff` ships it verbatim so G-RESOLVE applies the
exact gold; the verification layer models only the determinant/pivot behaviour
the F2P test demands.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg: the `# impl-start` /
`# impl-end` region of `model.py` (`lowest_live_index`, plus the `@Pure`
`is_genuinely_zero` / `first_usable` it depends on) is copied **verbatim** with
only the contract calls stripped, and diffed against the **real patched repo
function, called** — `sympy.matrices.matrices._find_reasonable_pivot(col,
iszerofunc=_is_zero_after_expand_mul)`, the exact call the gold patch installs
at the Bareiss pivot step (`matrices.py:190` post-patch; the callee itself at
`matrices.py:4065` and `_is_zero_after_expand_mul` at `matrices.py:42`). Nothing
is transliterated and no `@ContractOnly` is assumed (this bundle consumes none).

**Bridge (§2 inverted).** Generation runs concrete → abstract so every input
satisfies the `Requires` by construction: each column entry is built as an
expression tree over the grammar {integer monomial `c*a^i*b^j`, `+`, `-`, `*`,
optional top-level division by a non-vanishing denominator}, its mathematical
vanish status is decided by an **independent flat-polynomial evaluator** in the
script (dict `(i,j) → coefficient`), and the §2 status code is read off:
vanishing + structurally falsy → `0`; vanishing + structurally truthy → `-1`
(pseudo-zero, the bug class); non-vanishing → `+1`. The code is therefore
derived from the entry's construction, never from the repo predicate, so the
check is not circular in `is_genuinely_zero`. The grammar excludes Pow-of-Add
because `expand_mul` does not expand it (`power_base=False`,
`multinomial=False`), so such entries lie outside the abstraction's domain; the
evaluator was cross-checked in-container against the real
`_is_zero_after_expand_mul` on 20000 generated entries with 20000/20000
agreement. Only `Integer`/`Symbol` polynomials are emitted and every column is
asserted Float-free, keeping generation inside §2's modeled non-Float (PASS-1)
slice.

**Inputs.** 100037 columns: the 12 columns the real patched Bareiss recursion
actually feeds the pivot finder for the FAIL_TO_PASS matrices
`M(n) = [[i + a*j]]`, n = 1..7 (recorded by wrapping the module global and
running `.det()`), + 25 boundary columns (empty, singleton of each code class,
all-zero, all-pseudo-zero, pseudo-zero-then-live, quotient pseudo-zeros,
length-8), + 100000 seeded fuzz columns. The modeled space is infinite
(unbounded length and entry size), so fuzz is used rather than exhaustion.

**Pinned seed: `SEED = 13877`** (module constant `SEED`; `N_FUZZ = 100_000`).

Branch/class coverage is asserted non-zero over both all inputs and the fuzz
phase alone (a shortfall exits 1), so the check cannot pass vacuously. Verdict:
`G-CONF=pass`, 0 disagreements.
