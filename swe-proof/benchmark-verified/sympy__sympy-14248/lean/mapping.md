# mapping.md — sympy__sympy-14248

## Symbol binding

| Lean symbol | Python symbol | file:line @ base_commit `9986b38181` |
|---|---|---|
| `implementation_renderSum` / `problem_spec_renderSum` | `StrPrinter._print_MatAdd` | `sympy/printing/str.py:314-316` (post-patch `:314-330`) |
| (same algorithm, second site) | `LatexPrinter._print_MatAdd` | `sympy/printing/latex.py:1479-1481` (post-patch) |

The modeled routine is the additive-term recombination performed by
`_print_MatAdd`. At base_commit it is just `' + '.join(terms)`; the patch rewrites
it to inspect each already-rendered term and, when that term carries a leading
`'-'`, emit it as a subtraction instead of a `+ (-...)`. The `str.py` and
`latex.py` `_print_MatAdd` bodies are **byte-identical** in algorithm (only the
per-term renderer that produces the input differs), so one Lean model covers both.

## Input carrier — the Lean↔Python type bijection (used by G-CONF)

| Python | Lean |
|---|---|
| `terms : list[str]` — the list comprehension `[self.parenthesize(arg, precedence(expr)) for arg in expr.args]` (str.py) / `[self._print(t) for t in expr.args]` (latex.py) | `terms : List String` |
| `str` term | Lean `String` |
| `t.startswith('-')` | `t.startsWith "-"` |
| `t[1:]` | `t.drop 1` |
| `' '.join(l)` | `String.intercalate " " l` |
| `l.extend([sign, t])` | `l := l ++ [sign, body]` |
| `l.pop(0)` | `l.headD "+"` (value) + `l.tail` (remainder) |
| return value `str` | `String` |

The list of already-rendered term strings IS the input. The per-term renderer
(`parenthesize` / `_print`, plus the unchanged `_print_MatMul` negative-coeff
handling) is what *produces* that input; it is NOT part of the modeled routine,
so the model has **no callee** — no `opaque` decl and no consumed axiom.

## Callee provenance / flag deps
None. The modeled routine is a self-contained pure transform over `List String`.
`_print_MatMul`'s negative-coefficient handling (also touched by the gold patch)
is what makes a term render with a leading `'-'`; it is upstream of this routine
and supplies the input terms — out of scope for this model.

## G-CONF fuzz seed
`SEED = 14248` (pinned; mirrored in `conformance_check.py`).

## F2P anchor cases (post-patch behavior)
- `["-B", "-A*B", "A"]` → `"-B - A*B + A"`   (`str(A - A*B - B)`)
- `["-(A + B)", "A*B"]` → `"-(A + B) + A*B"`  (`str(A*B - (A+B))`)
- `["-B", "A"]` → `"-B + A"`                  (MatrixElement `(-B + A)[0, 0]`)
