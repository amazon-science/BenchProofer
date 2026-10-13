# mapping.md — sympy__sympy-14248

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9986b38181cdd556a3f3411e553864f11912244e`, states the type
abstraction, and records callee provenance.

Repo files under change: `sympy/printing/str.py`, `sympy/printing/latex.py`,
`sympy/printing/pretty/pretty.py`.  These change **three** distinct behaviours,
NOT two: (i) a spaced-binary-minus matrix-sum join (str/latex `_print_MatAdd`);
(ii) the leading sign of a matrix product (str/latex `_print_MatMul`); and
(iii) a single-space matrix-sum join that keeps the minus attached (pretty
`_print_MatAdd`) — a genuinely different algorithm from (i).  The model binds
(i) and (ii) to the **`str` printer** (`render_sum`, `render_product`) and
models (iii) as its own deep fold (`render_sum_space`).  `latex._print_MatAdd`
is a byte-identical R-refinement of (i); only it shares a modelled site
(refinement.md §C).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_sum(terms)` | `StrPrinter._print_MatAdd(self, expr)` — `sympy/printing/str.py:314` | the modeled changed function (spaced-binary-minus matrix-sum join) |
| `render_sum_space(terms, negs)` | `PrettyPrinter._print_MatAdd(self, expr)` — `sympy/printing/pretty/pretty.py:821` | the modeled changed function (single-space matrix-sum join, term kept in full; the per-item join decided by the STRUCTURAL fact `S(item.args[0]).is_negative`, carried as the input `negs`) |
| `render_product(factors, neg)` | `StrPrinter._print_MatMul(self, expr)` — `sympy/printing/str.py:306` | the modeled changed function (rendering a matrix product) |
| `matadd(terms)` | the post-patch body of str/latex `_print_MatAdd` (the sign-aware ` - `/` + ` join, minus stripped) | pure spec: the whole rendered sum sequence (§A discipline) |
| `matadd_space(terms, negs)` | the post-patch body of pretty `_print_MatAdd` (single space before a structurally-negative term, term kept in full; ` + ` otherwise) | pure spec: the whole rendered sum sequence (§A2 discipline) |
| `matmul(factors, neg)` | the post-patch body of `_print_MatMul` (leading-sign extraction) | pure spec: the whole rendered product sequence |
| `contrib / add_tail / lead` | the per-term branch in str/latex `_print_MatAdd`'s loop (`if t.startswith('-')` → `'-'` separator + `t[1:]`, else `'+'` separator + `t`; first term special) | pure spec: per-term infix contribution + folded tail + leading term |
| `contrib_space / add_tail_space` | the per-item branch in pretty `_print_MatAdd`'s loop (`if S(item.args[0]).is_negative` → single space + full item; else `' + '` + item; first item bare) | pure spec: per-item single-space contribution keyed on the structural fact `negs[k]` + folded tail |
| `joinstar / mul_tail` | the `'*'.join([...])` over `expr.args` in `_print_MatMul` | pure spec: the `*`-joined factor list |
| `is_neg / body` | `t.startswith('-')` and `t = t[1:]` in str/latex `_print_MatAdd` | pure spec: leading-minus test + minus strip |

There are **no axiomatized callees** (`@ContractOnly`): both behaviours are
modelled deeply.  The per-argument rendering inside each gold loop —
`self._print(t)` / `self.parenthesize(arg, precedence(expr))` for a sum term,
and `self.parenthesize(arg, precedence(expr))` for a product factor — is taken
as the **input** to each model function (the list of already-rendered term /
factor strings), an input refinement (§2), not an opaque callee under contract.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a rendered term/factor `str` (the result of `self._print(t)` / `self.parenthesize(arg, precedence(expr))`) | `PSeq[int]` of Unicode code points | `s[k]` ↔ `t[k] == ord(s[k])`; `t.startswith('-')` ↔ `len(t) > 0 and t[0] == 45`; `t[1:]` ↔ `t.drop(1)`; `str` concatenation ↔ `PSeq +` |
| the list `[self._print(t) for t in expr.args]` (str/latex `_print_MatAdd`) | `terms: List[PSeq[int]]` | each list element is one rendered term; `len(expr.args)` ↔ `len(terms)` |
| the per-item `pform = self._print(item)` over `expr.args` (pretty `_print_MatAdd`) | `terms: List[PSeq[int]]` | each element is one rendered item picture; on the single-line F2P cases the picture is one row, so it refines to a flat `PSeq[int]` of code points |
| `S(item.args[0]).is_negative` (pretty `_print_MatAdd` per-item test) | `negs: List[bool]`, `negs[k]` alongside `terms[k]` | the truthiness of the STRUCTURAL negativity test on item k's leading argument, carried as its own boolean input — NOT derived from the rendered text.  The test can disagree with a rendered leading `'-'` (e.g. `y*B` with `Symbol('y', negative=True)` renders `y⋅B` with no `'-'` yet `S(y).is_negative` is True), so the fact is an input exactly like `neg` in `_print_MatMul` (see §2.2) |
| the list `[self.parenthesize(arg, precedence(expr)) for arg in expr.args]` of the (coefficient-normalised) product (str `_print_MatMul`) | `factors: List[PSeq[int]]` | each element is one rendered factor of the product `_keep_coeff(-c, m)` produces when `c < 0`, else of `expr` itself |
| `expr.args[0].is_Number and expr.args[0] < 0` / `c, m = expr.as_coeff_mmul(); c.is_number and c < 0` (str `_print_MatMul`) | `neg: bool` | the boolean fact "the product carries a negative numeric leading coefficient"; an input refinement of the structural test the gold performs on the expression tree |
| the separators `' + '`, `' - '`, `'*'`, the leading `'-'` | `PSeq(32,43,32)`, `PSeq(32,45,32)`, `PSeq(42)`, `PSeq(45)` | code-point literals |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]` /
`PSeq[int]` of code points throughout, and the list of rendered children is
`List[PSeq[int]]` (specification over `PSeq[PSeq[int]]` via `ToSeq`).

### 2.1 Why `neg` (and the coefficient normalisation) is an input, not an axiom

The gold `_print_MatMul` calls `expr.as_coeff_mmul()`, `_keep_coeff(-c, m)`,
`arg.is_Number`, and `arg < 0`.  None of these is *changed* by the patch; the
patch only *uses* them to decide (a) whether to emit a leading `-` and (b)
which factor list to render.  The model abstracts their joint result to its two
observable consequences — the boolean `neg` and the (already-rendered) `factors`
list — exactly as the model abstracts `self._print(term)` to the term string.
This is an R input-refinement of the surrounding render, not an axiom about a
callee, so there is no G-AX obligation: the function under spec is the
*assembly of the output string* from `(factors, neg)`, which is the part the
patch rewrites.  (The pre-patch emitted no sign at all; `model_prepatch_2.py`
drops the `neg` leading minus and fails — §refinement.md §B.)

### 2.2 Why the pretty negativity test is the boolean input `negs`, not `is_neg` on the rendered item and not an axiom

The gold pretty `_print_MatAdd` decides the separator with
`S(item.args[0]).is_negative` (a structural test on the term's leading
argument), then appends the **full** rendered item.  This test is not
*changed* by the patch — it is *used* to choose the join.  Crucially the test
is NOT equivalent to "the rendered item begins with `'-'`": for an item `y*B`
with `Symbol('y', negative=True)` (an assumption-negative symbolic
coefficient) `S(item.args[0]).is_negative` is True while the rendered picture
`y⋅B` carries no leading `'-'`; conversely `S(...)` of a non-number leading
argument can be non-negative while other renderings differ.  An earlier
revision of this model abstracted the test to `is_neg(t)` on the rendered
item and was correctly rejected as unfaithful (G-PANEL-2) — the two disagree
on admissible inputs, e.g. the real output `'-A y⋅B'` vs the modeled
`'-A + y⋅B'` for `-A + y*B`.

The faithful abstraction is the same one §B/§2.1 uses for `_print_MatMul`'s
coefficient test: the *truthiness of the structural test* is carried as a
boolean input — `negs[k]` alongside the rendered item `terms[k]` — because the
patch only *consumes* that fact to assemble the output.  The function under
spec is the *assembly of the output string* from `(terms, negs)` (the part the
patch rewrites: separator choice + the item kept in full), so this is an R
input-refinement, not an axiom — no G-AX obligation.  What `render_sum_space`
pins distinctly from `render_sum` is BOTH the decision source (the structural
fact `negs[k]`, not the rendered text) and the OUTPUT shape: a single space
(not ` - `) before a structurally-negative item and the item emitted IN FULL
(nothing stripped).  (The pre-patch joined every item with ` + `;
`model_prepatch_3.py` reproduces that and fails — §refinement.md §A2.  A rival
that decides on the rendered text, `contrib_space(t, is_neg(t))`, is rejected
by G-PBT `weak-space-text-negativity`.)

## 3. Callee provenance

None.  No `@ContractOnly` axiom is shipped and no `axiom_check.py` is required:
the three modeled behaviours are pure string-assembly logic, modelled deeply as
front-recursive folds (`matadd`, `matadd_space`, `matmul`) over the abstract
child-render sequences, with the per-child rendering supplied as input.  The soundness of
the twin therefore rests entirely on refinement fidelity (refinement.md, G-EQ)
and the real-harness oracle on the gold `patch.diff` (G-RESOLVE).
