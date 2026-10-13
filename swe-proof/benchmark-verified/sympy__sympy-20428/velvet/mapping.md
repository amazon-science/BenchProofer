# mapping.md — sympy__sympy-20428

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c0e85160406f9bf2bcaa2992138587668a1cd0bc`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each callee.

Repo file under change: `sympy/polys/domains/expressiondomain.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `symbolicNonzero (e : SymExpr)` | `ExpressionDomain.Expression.__bool__(f)` — `sympy/polys/domains/expressiondomain.py:122` (body line 123) | the modeled changed function (truth value / nonzero-test of a symbolic field element) |
| `nonzeroSpec (e : SymExpr)` | the post-patch body `not f.ex.is_zero` — `expressiondomain.py:123` | pure spec: the intended truth value of an element |
| `SymExpr.identicallyZero` | `f.ex.is_zero is True` — sympy `Expr.is_zero` (three-valued mathematical zero predicate) | the math/identical zero observation of the underlying expression `f.ex` |
| `SymExpr.literalZero` | `f.ex == 0` (i.e. `f.ex == Integer(0)`) — the pre-patch test `f.ex != 0` | the coarse structural observation: whether the representation is the bare literal zero |

The pre-patch repo symbol the change removes (refinement audit only, not in the
consumer spec view): the body expression `f.ex != 0` at `expressiondomain.py:123`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a single symbolic field element `f` of `ExpressionDomain.Expression`, carrying one SymPy expression `f.ex` | `SymExpr` (a 2-field structure) | `f` ↔ `{ identicallyZero := (f.ex.is_zero is True), literalZero := (f.ex == Integer(0)) }`. The element is read by `__bool__` through exactly these two observations and nothing else, so the abstraction is faithful for this operation. |
| `f.ex.is_zero is True` (Python `bool`; `is_zero` is three-valued — `True`/`False`/`None`, and the patched `not f.ex.is_zero` treats `None` as nonzero) | `SymExpr.identicallyZero : Bool` | `True ↔ true`; `False`/`None ↔ false`. Matches `not f.ex.is_zero` because `not (None) == True` and `not (False) == True` both yield "nonzero", i.e. `identicallyZero = false`. |
| `f.ex == 0` (structural equality of the representation to `Integer(0)`) | `SymExpr.literalZero : Bool` | `True ↔ true`, `False ↔ false`. |
| `bool(f)` / `__bool__`'s return (Python `bool`, "is this element nonzero") | the method result `out : Bool` | `True ↔ true` (nonzero), `False ↔ false` (zero). |

**Modeling invariant (the method `require`):** a representation equal to the
literal zero always *denotes* zero, so `literalZero → identicallyZero`. This is
validated over boundary + 10^5 fuzzed real `EX(expr)` elements by G-CONF
(conformance_check.py); 0 violations observed. The converse fails — an element
can denote zero (`identicallyZero = true`) while not being the literal zero
(`literalZero = false`); that is exactly the issue's bad poly and the
discriminating case (`Solution_prepatch.lean`).

## 3. Callee provenance (kind — checked by G-AX / axiom_check.py)

**No axioms; no A-reference to an external callee.** The changed operation is
modeled DEEPLY and CONCRETELY: `nonzeroSpec e = !e.identicallyZero` IS the
post-patch decision `not f.ex.is_zero`, transliterated over the two-observation
abstraction. The two zero-tests it reads (`Expr.is_zero`, `== 0`) are primitive
observations of the element — UNCHANGED machinery — not callees the changed
function delegates a contract to; they are abstracted to the two `SymExpr`
booleans (§2) and exercised structurally by G-CONF, not asserted as an axiom.

`axiom_check.py` (G-AX) is therefore vacuous and emits `status=skip`
(refinement.md §C). The one externally-checkable claim — the modeling invariant
`literalZero → identicallyZero` (§2) — is asserted inside G-CONF against real
SymPy elements, where the real patched `__bool__` is also the G-CONF oracle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`20428`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`nonzeroSpec` to Python over the two-observation abstraction; the oracle is the
REAL gold-patched `Expression.__bool__` observed through `bool(EX(expr))`.
Inputs are small expression trees over rationals, symbols, and surds (incl. the
issue's `1/(sqrt(2)-1) - (sqrt(2)+1)`, a math-zero element that is not the
literal zero), built with `+ - * /`.
