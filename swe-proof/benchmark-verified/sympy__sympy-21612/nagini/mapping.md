# mapping.md — sympy__sympy-21612

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b4777fdcef467b7132c055f8ac2c9a5059e6a145`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/printing/str.py` — `StrPrinter._print_Mul`
(`sympy/printing/str.py:249`), specifically the denominator-gathering loop and
the later bracketing pass inside it.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `bracket_flags(factors)` | the per-denominator-factor bracketing decision in `_print_Mul`: the `pow_paren` collection inside the gather loop (`sympy/printing/str.py:328-346`, the `else` branch at 334-339) together with the wrapping pass that consumes it (`sympy/printing/str.py:353-356`) | the modeled changed behaviour: which denominator factors are wrapped in brackets |
| `Factor` (class: `parts`, `form`) | one denominator `item` — a commutative `Pow` with `item.exp is S.NegativeOne` — abstracted to the two facets the decision reads | minimal carrier for a denominator factor |
| `Factor.parts` | `len(item.args[0].args)` (`str.py:335`) — the number of arguments of the reciprocated base | part count of the reciprocated quantity |
| `Factor.form` | the structural class of `item.base` tested by `isinstance(item.base, (Mul, Pow))` (`str.py:336`, post-patch) | structural-form tag: 0 atomic, 1 `Mul`, 2 `Pow` |
| `is_composite_form(form)` | `isinstance(item.base, (Mul, Pow))` (`str.py:336`, post-patch) | the form test: product or power is composite, atom is not |
| `needs_brackets(parts, form)` | the full guard `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))` (`str.py:335-336`, post-patch) | per-factor bracketing predicate |

The pre-patch repo symbol the change widens (for the refinement audit, not
referenced from the consumer spec view): the guard
`isinstance(item.base, Mul)` at `str.py:336` — which omitted the `Pow` form and
left a reciprocal-of-a-reciprocal (`1/y == Pow(y, -1)`) denominator factor
un-bracketed, printing `x/1/y` instead of `x/(1/y)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a denominator `item` (`Pow`, `exp is S.NegativeOne`) | a `Factor` object | the loop iterates a list of such items; the model takes `List[Factor]` in the same order |
| `len(item.args[0].args)` (int) | `Factor.parts` (int ≥ 0) | identity on the integer count; the only comparison performed on it is `!= 1`, which the model reproduces exactly |
| `isinstance(item.base, (Mul, Pow))` (bool) | `is_composite_form(Factor.form)` with `form ∈ {0,1,2}` | the `isinstance` test against the 2-tuple `(Mul, Pow)` ↔ membership of the form tag in `{1, 2}`; `form == 0` (any other class, e.g. a `Symbol`) ↔ `isinstance` False. The disjunction `form == 1 or form == 2` is exactly `isinstance(_, (Mul, Pow))`. |
| `item in pow_paren` ⇒ `b_str` wrapped `"(%s)"` (`str.py:354-356`) | the boolean flag `Result()[k]` | a True flag ↔ the factor's rendered base is bracketed; a False flag ↔ bare. The string-rendering and `'/'.join` are downstream of the decision and unchanged by the patch, so they are not modeled; the decision is the entire delta. |

`item.args[0]` is the reciprocated quantity: for a denominator `item` with
`exp == -1`, `item.args[0]` is `item.base` (the thing being reciprocated), and
`item.args[0].args` are its parts. Confirmed at base_commit on the issue's own
expression: `Mul(x, Pow(1/y, -1, evaluate=False), evaluate=False)` has the
denominator item `1/(1/y)` whose `base` is `1/y == Pow(y, -1)` (a `Pow`, form
tag 2) with `args == (y, -1)` (two parts, so `parts == 2 != 1`). Old guard:
`isinstance(base, Mul)` False ⇒ no brackets ⇒ `x/1/y` (the bug). New guard:
`isinstance(base, (Mul, Pow))` True ⇒ brackets ⇒ `x/(1/y)`. The `#14160`
witness `Mul(-2, x, Pow(Mul(y,y,evaluate=False), -1, evaluate=False))` has base
`y*y` (a `Mul`, form tag 1, two parts), so both guards bracket it — output
`-2*x/(y*y)` is preserved.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

None. There is **no `@ContractOnly` axiom**. The changed operation is the
two-part guard (`len(...) != 1` and `isinstance(item.base, (Mul, Pow))`), which
is modeled **deeply** as integer/boolean reasoning over the abstracted facets
`parts` and `form` (the `pure` region functions `is_composite_form` and
`needs_brackets`, and the verified loop). Both `len(...)` and `isinstance(...)`
are concrete Python operations the patched code performs, refined to int/bool
operations on `Factor` fields (kind R, §2); neither is an opaque library callee
whose contract the proof would consume.

`axiom_check.py` is therefore a **structural-faithfulness validator** (G-AX
A-reference role): it constructs the issue's and `#14160`'s real sympy
expressions in-container, extracts the real `(len(item.args[0].args),
form-of(item.base))` facets for every denominator item, and asserts that the
model predicate `needs_brackets` over those facets equals the real post-patch
guard `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))`, and
disagrees with the pre-patch guard exactly on the issue's `1/y` factor. It
imports only `sympy` (the repo under test) — nothing test-specific — and exits
0 iff the abstraction is faithful.
