# mapping.md — sympy__sympy-18189

## Instance
- repo: sympy/sympy
- base_commit: `1923822ddf8265199dbd9ef9ce09641d3fd042b9`
- changed file: `sympy/solvers/diophantine.py`
- changed function: `diophantine(eq, param, syms=None, permute=False)`
  (def @ line 101; touched region @ lines 180–186).

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python source | location |
|---|---|---|
| `implementation_diophantine` / `problem_spec_diophantine` | the requested-symbol-order branch of `diophantine` (the `if syms != var:` block at lines 180–186, plus the fall-through canonical solve) | `sympy/solvers/diophantine.py:180-186` |
| `var : List Nat` | `var = list(eq.expand(force=True).free_symbols)` then `var.sort(key=default_sort_key)` — the equation's variables in canonical order | `diophantine.py:170-171` |
| `syms : List Nat` | `syms = [i for i in syms if i in var]` — the requested output order, filtered to actual variables | `diophantine.py:178` |
| `permute : Bool` | the `permute` keyword parameter | `diophantine.py:101-102` |
| `solveCanonical eq permute` | the recursive call `diophantine(eq, param, permute=permute)` (post-patch) returning the canonical-order solution set under the given mode | `diophantine.py:184` |
| `reindexTuple var syms t` | `tuple([t[dict_sym_index[i]] for i in var])` with `dict_sym_index = dict(zip(syms, range(len(syms))))` | `diophantine.py:182-184` |
| `reindexAll` (over the for-loop / set comprehension) | `{ … for t in diophantine(eq, param, permute=permute)}` | `diophantine.py:183-184` |

## Variables modeled as `Nat`
Sympy `Symbol`s appear here only as identity tokens used for ordering and as
dict keys. They are modeled as `Nat` (distinct symbols ↔ distinct naturals);
the canonical order is the list `var`, the requested order is the list `syms`.
`dict_sym_index[i]` (the position of variable `i` within `syms`) ↔ `syms.idxOf i`.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)

| Lean | Python | notes |
|---|---|---|
| `List Nat` (`var`, `syms`) | ordered list of `Symbol`s | distinct symbols ↔ distinct `Nat`s; ordering preserved |
| `List Int` (one tuple) | `tuple` of integers, one entry per variable | positional |
| `List (List Int)` | a solution set of tuples | sympy uses a Python `set`; the Lean list is ordered/with-multiplicity. The bijection is up to set-equality: G-CONF compares `set(shadow)` vs the real `set` |
| `Bool` (`permute`) | `bool` (`permute=`) | identical |
| `solveCanonical eq permute` | `set(diophantine(eq, param, permute=permute))` | UNCHANGED callee; left as the real repo callee in G-CONF |
| `reindexTuple var syms t` | `tuple([t[dict_sym_index[i]] for i in var])` | `t.getD (syms.idxOf i) 0` ↔ `t[dict_sym_index[i]]`; the `getD` default `0` is never hit (every `i ∈ var` is in `syms` post-filter) |

## Callee provenance + flag deps
- `solveCanonical` ↔ the recursive `diophantine(eq, param, permute=permute)` call.
  UNCHANGED subroutine (the fix only threads its `permute` argument). The proof
  consumes NO property of it; it carries an `opaque` signature only (no `_prop`
  axiom). Flag dependency: its **second argument is the very flag the fix routes**
  — base-only solutions when `false`, the additional admissible solutions when
  `true`. G-CONF must fuzz both modes and the issue equation where the two modes
  diverge.
- No deep-model reference (A-reference) requiring G-AX: `solveCanonical` is left
  abstract, so `axiom_check.py` is a skip stub.

## Pinned G-CONF fuzz seed
`SEED = 18189` (see `conformance_check.py`, `meta.json verifier_pins.conf_seed`).
