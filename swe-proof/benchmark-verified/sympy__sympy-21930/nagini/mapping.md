# mapping.md — sympy__sympy-21930

Binds every `model.py` symbol to its repository counterpart at
`base_commit = de446c6d85f633271dfec1452f6f28ea783e293f`, states the type
abstraction, and gives the provenance of the deep-model references (validated
against the real SymPy printer by `axiom_check.py` / G-AX).

Repo file under change: `sympy/physics/secondquant.py`.

## 1. Symbol ↔ repo binding

Model function names are deliberately **non-echoing** (`render_token_a/b/c`):
they do not token-overlap the patched repo class names (`AntiSymmetricTensor`,
`CreateBoson`, `CreateFermion`), which is required because those class
identities are not disclosed by the solver-visible `problem_statement`. The true
repo binding lives here in mapping/meta only, never in the consumer spec view.

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_token_a(body)` | `AntiSymmetricTensor._latex` — `sympy/physics/secondquant.py:219` | modeled changed renderer (index tensor `symbol^{upper}_{lower}`) |
| `render_token_b(body)` | `CreateBoson._latex` — `sympy/physics/secondquant.py:480` | modeled changed renderer (bosonic creation operator `b^\dagger_{state}`) |
| `render_token_c(body)` | `CreateFermion._latex` — `sympy/physics/secondquant.py:941` | modeled changed renderer (fermionic creation operator `a^\dagger_{state}`) |
| `grouped_token(body)` *(deep model — A-reference)* | the `"{%s...}"` wrapping the patched `_latex` methods install around their intrinsic body | pure spec: the rendered token is the body wrapped as one LaTeX group `{ body }` |
| `appended_super_is_outer(token, exp)` *(deep model — A-reference)* | the LaTeX grouping rule, as realized by the power printer `_helper_print_standard_power` (`sympy/printing/latex.py:663`, `tex = r"%s^{%s}"`): an appended superscript binds to a preceding self-delimited `{...}` group | pure spec: power-safety predicate (true iff `token` ends in `}`) |
| `LBRACE/RBRACE/CARET` | the ASCII tokens `{` `}` `^` | pure spec: LaTeX delimiters / superscript marker as code points |

The pre-patch repo bodies the change wraps (intrinsic renderings, referenced by
the refinement audit, not from the consumer spec view):
- `AntiSymmetricTensor._latex`: `"%s^{%s}_{%s}" % (symbol, upper, lower)`
  → e.g. `t^{ab}_{ij}` (`secondquant.py:219-224`).
- `CreateBoson._latex`: `"b^\\dagger_{%s}" % state.name` → e.g. `b^\dagger_{i}`
  (`secondquant.py:480-481`).
- `CreateFermion._latex`: `"a^\\dagger_{%s}" % state.name` → e.g. `a^\dagger_{i}`
  (`secondquant.py:941-942`).

Each intrinsic body contains an interior `^` (the tensor's upper-index slot;
the creators' `\dagger` superscript). The two annihilation renderers
`AnnihilateBoson._latex` (`b_{...}`, `secondquant.py:441`) and
`AnnihilateFermion._latex` (`a_{...}`, `secondquant.py:795`) have NO interior
`^` and are correctly left UNCHANGED by the gold patch — confirming the change
targets exactly the operators whose body carries a superscript.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the intrinsic `_latex` body, and the method's return) | `List[int]` of Unicode code points | `s[k]` ↔ `body[k] == ord(s[k])`; `len(s)` ↔ `len(body)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the `"{...}"` `%`-format wrapping (`"{%s^{%s}_{%s}}"`, `"{b^\\dagger_{%s}}"`, `"{a^\\dagger_{%s}}"`) | `grouped_token(body) = PSeq(123) + body + PSeq(125)` | the gold's outer `{` and `}` are prepended/appended around the unchanged intrinsic body |
| the per-operator constant prefix/suffix and index interpolation that build the intrinsic body | the opaque `body` parameter | identity: the body is the operator's intrinsic rendering; the change adds ONLY the outer braces, so the body is carried as an uninterpreted input and the wrap is the modeled delta (mapping.md §3) |
| the `printer` argument of `_latex` | omitted | the three methods ignore `printer`; their output depends only on `self.symbol`/`self.args`/`self.state.name`, all folded into `body` |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model references (A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The changed operation is the
brace-wrapping itself plus its interaction with the power printer; both are
modelled DEEPLY (spelled out as `grouped_token` and `appended_super_is_outer`)
and validated == the real SymPy printer out-of-band.

### 3.1 `grouped_token` ↔ the patched `_latex` wrapping (A-reference)
**Callee:** the three patched `_latex` methods. Each gold hunk inserts `{` …
`}` around an otherwise-unchanged `%`-format body, e.g.:
```
- return "b^\\dagger_{%s}" % self.state.name
+ return "{b^\\dagger_{%s}}" % self.state.name
```
The deep model `grouped_token(body) = "{" + body + "}"` is exactly that wrap.
`axiom_check.py` runs the REAL patched printer on each operator (and fuzzes the
index/state label) and asserts `sympy.latex(op) == grouped_token(body)` where
`body` is the operator's intrinsic (pre-fix) rendering, and that `body` carries
an interior `^` so the wrap is load-bearing.

### 3.2 `appended_super_is_outer` ↔ the power printer (A-reference)
**Callee:** the LaTeX power printer `LatexPrinter._helper_print_standard_power`
(`sympy/printing/latex.py:663`): for a base whose printed token is `t`, the
exponent printer emits `r"%s^{%s}" % (t, exp)` — i.e. the composite is
`t + "^{" + exp + "}"`. For these operators the base is **not** `is_Symbol`, so
the printer does NOT call `parenthesize_super` (`latex.py:667`); the base must
therefore self-protect by being a single delimited group. The model predicate
`appended_super_is_outer(token, exp)` is true iff `token` ends in `}` (a
self-delimited group), in which case the appended `^` binds to the whole group.
`axiom_check.py` asserts, on the real printer, that for each operator (a) the
token ends in `}`, (b) the composite `latex(op**2)` contains `token + "^{2}"`
(the exponent binds to the group), and (c) the composite does NOT contain the
malformed bare double superscript `body + "^{2}"`. It also checks the exact
issue-19661 witness
`latex(Commutator(Bd(0)**2, B(0))) == r'- \left[b_{0},{b^\dagger_{0}}^{2}\right]'`.

(The earlier illustrative pure helper `with_exponent(token, exp) = token + "^{"
+ exp + "}"` was removed from `model.py` in refinement — it was `@Pure` but
referenced by no `Ensures` and no impl, so it was non-load-bearing. The
composite shape it documented is asserted directly in `axiom_check.py` against
the real printer, above.)

**Soundness check (G-AX):** `axiom_check.py` imports only `sympy` (the library
under change — the analogue of the reference bundle importing stdlib `html`),
exercises the three operators plus 8 index-label variants and the power
composites, and exits 0 iff every observation matches the deep models. It
exits 0 on the patched printer and **non-zero on the unpatched (buggy) printer**
— a genuine discriminator, not a vacuous check.
