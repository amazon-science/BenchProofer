# mapping.md — sympy__sympy-21930

Symbol binding, the Lean↔Python type bijection (used by G-CONF and G-AX), callee
provenance + flag dependencies, and the pinned G-CONF fuzz seed.

`spec_provenance: cold` — the specification was derived only from
`problem_statement`, the gold `patch`, and the real source at `base_commit`
(worktree `$SCRATCH`). No prior solution was consulted.

## 1. Modeled functions (symbol binding, file:line @ base_commit)

Base commit `de446c6d85f633271dfec1452f6f28ea783e293f`,
file `sympy/physics/secondquant.py`.

| model_symbol (Solution.lean) | repo_symbol | repo_location | carrier |
|---|---|---|---|
| `tensorLatex`  | `AntiSymmetricTensor._latex` | `sympy/physics/secondquant.py:220` (class `AntiSymmetricTensor`, def line 153) | renderer: (symbol, upper indices, lower indices) → LaTeX string |
| `creBosonLatex`| `CreateBoson._latex`         | `sympy/physics/secondquant.py:480` (class `CreateBoson`, def line 445)        | renderer: (state name) → LaTeX string |
| `creFermionLatex`| `CreateFermion._latex`     | `sympy/physics/secondquant.py:941` (class `CreateFermion`, def line 799)      | renderer: (state name) → LaTeX string |

These are the three functions the gold patch changes. Each is a pure
string-building method (`_latex(self, printer)`) returning a `str`; none mutate
`self` or `printer`. `printer` is unused by all three bodies (the format string
is built directly from `self`), so it is not modeled — directive 5: no `mut`
input, nothing overwritten.

## 2. Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Python (repo reality) | Lean (model) | bridge |
|---|---|---|
| `str` (LaTeX output, per code point) | `List Char` | `ch ↔ Char.ofNat (ord ch)`; G-CONF compares `"".join` of the shadow vs the real `str` |
| index/symbol `.name` (`str`) | `List Char` | same code-point bijection |
| `self.args[1]` (a `Tuple` of index objects) | `upper : List (List Char)` — the list of each index's `.name` as `List Char` | `[ i.name for i in self.args[1]]` ↔ `upper`; the per-element `.name` extraction is an **unchanged upstream** read (R), so the list of names is the carrier |
| `self.args[2]` (lower `Tuple`) | `lower : List (List Char)` | as above |
| `self.symbol` (a `Symbol`, printed via `"%s"`) | `symbol : List Char` | `str(self.symbol)` ↔ `symbol` |
| `self.state.name` (`str`) | `name : List Char` | code-point bijection |
| Python `%`-format / `"".join` | `List Char` concatenation `++` and the front-recursive fold `concatNames` | I / R |

Notes on `"%s^{%s}_{%s}" % (symbol, "".join(upper_names), "".join(lower_names))`:
`"".join` of a list of strings is the front-recursive concatenation
`concatNames` (pure region), and the `%`-template is literal-string interleaving
modeled by `++`. These join/format operations are **unchanged** by the patch
(I); only the surrounding brace-wrapping is new.

## 3. Callee provenance + flag dependencies

There are **no axiomatized callees** and **no deep-model references** in this
bundle. Every operation the three methods perform is a pure, total, fully
expressible string build:

- `"".join([ i.name for i in self.args[1]])` — `str.join` over the index names;
  modeled deeply as `concatNames` (front-recursive fold, A-NONE: it is
  transliterated I/R content checked by G-CONF, not an axiom). The `.name`
  attribute read on each index is an unchanged upstream attribute access (R).
- `"%s" % self.symbol`, `"%s" % self.state.name` — `str` coercion / formatting;
  identity on character content (R).
- The `"{...}"` wrap and the `b^\dagger_{...}`, `a^\dagger_{...}`,
  `^{...}_{...}` literal templates — literal string concatenation (I).

No callee is left as an `axiom` or `:|` stub, so `axiom_check.py` is a trivial
no-op pass (G-AX has nothing to validate); `meta.json` lists empty `axioms` and
`deep_model_references`. No flag-dependent callee.

## 4. G-CONF fuzz seed

Pinned seed: **`21930`**. `conformance_check.py` fuzzes ≥10⁵ inputs
(index-name strings, multi-index tuples, symbol names) and diffs the R/I shadow
of each modeled method against the patched real method behaviour at
`base_commit`. The shadow is pure R/I (no A-tagged callee in the impl regions),
so `conf_skip=false`.

## 5. The discriminating behavior (for G-DIFF)

The patch's entire content is: wrap each method's returned LaTeX in an extra
`{ ... }` group, so a following superscript (e.g. `**2` → `^{2}`) binds to the
whole operator instead of only its subscript. The frozen postconditions pin the
output to **begin with `{` and end with `}`** around the otherwise-identical
body. The pre-patch skeleton omits the wrap and therefore fails the postcondition
(`Solution_prepatch.lean`).
