# refinement.md — sympy__sympy-13852

Maps every operation of `implementation_polylogEval` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses an axiom's
property · **A-reference** deep model validated == real callee (G-AX/G-CONF) ·
**I** identical concrete op.

The modeled function is `polylog.eval(cls, s, z)`. Post-patch it is a pure
dispatch table; `implementation_polylogEval` is the line-for-line skeleton of that
table (early-`return` per branch, matching the Python `return` ladder).

| # | `implementation_polylogEval` op | `patch.diff` / post-patch counterpart | tag | note |
|---|---|---|---|---|
| 1 | `s z : SymExpr` inputs; result `Option SymExpr` | `eval(cls, s, z)` args; return value or `None` | R | symbolic exprs ↦ `SymExpr` carrier; `None` ↦ `Option.none`; bijection in mapping.md |
| 2 | `if z = .lit 1 then return some (.zeta s)` | `if z == 1: return zeta(s)` | I | unchanged branch (frame: pinned identically pre/post) |
| 3 | `if z = .lit (-1) then return some (.neg (.eta s))` | `elif z == -1: return -dirichlet_eta(s)` | I | unchanged branch |
| 4 | `if z = .lit 0 then return some (.lit 0)` | `elif z == 0: return S.Zero` | R | patch changes `return 0` → `return S.Zero`; both denote the zero expression ⇒ `some (.lit 0)`. (Value-identical; the literal-type change is invisible to the modeled behavior.) |
| 5 | `if s = .lit 2 then if z = SymExpr.half … return some SymExpr.outHalf` | `elif s == 2: if z == S.Half: return pi**2/12 - log(2)**2/2` | R | added branch; closed-form expr refined structurally |
| 6 | `if z = .lit 2 then return some SymExpr.outTwo` | `elif z == 2: return pi**2/4 - I*pi*log(2)` | R | added branch |
| 7 | `if z = SymExpr.zA … outA`; `zB … outB`; `zC … outC`; `gSub … outD` | the four remaining `elif z == …` rows of the `s == 2` block | R | added table rows; each closed-form refined structurally |
| 8 | (no order-2 match) `return none` | the `s == 2` block falls through with no `return` ⇒ implicit `None` | R | "no recognized order-2 argument ⇒ stay unevaluated" ↦ `Option.none` |
| 9 | `if s = .lit 0 then return some (.div z (.sub (.lit 1) z))` | `elif s == 0: return z/(1 - z)` | R | added branch |
| 10 | `if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))` | `elif s == -1: return z/(1 - z)**2` | R | added branch |
| 11 | final `return none` | function falls through ⇒ implicit `None` | R | "no recognized pair ⇒ stay unevaluated" ↦ `Option.none` |

**No changed-inexpressible op.** Every changed operation is a *structural*
dispatch decision (which `(s, z)` pattern is matched) returning a *structural*
closed-form expression. Both are modeled deeply in the `SymExpr` carrier — nothing
is axiomatized. The closed-form output expressions (`zeta`/`eta`/`pi`/`log`/`sqrt`
combinations) are opaque builders, not numeric oracles: the spec pins which
builder-expression is returned per case, exactly the decision `eval` makes. There
is no consumed axiom and no isolated A-reference contract, so `axiom_check.py` is a
skip stub.

**Pre-patch contrast (G-DIFF).** The pre-patch `eval` recognizes only `z ∈ {1,
-1, 0}` and falls through (⇒ `None`) for everything else. The prepatch Lean
skeleton (`Solution_prepatch.lean`) therefore returns `none` at, e.g., `s = 2,
z = 1/2`, where `problem_spec_polylogEval` requires `some SymExpr.outHalf`. The
`s = .lit 2 ∧ z = SymExpr.half` clause is then unsatisfiable, so
`correct_polylogEval` cannot close — this is exactly the issue ("`polylog(2,
Rational(1,2))` should evaluate to `-log(2)**2/2 + pi**2/12`"). Confirmed by
throwaway spec-validation: spec accepts `some outHalf`, rejects `none`, at that
input.

**Conformance (G-CONF).** `conformance_check.py` builds the R/I Python shadow of
`implementation_polylogEval` (the same dispatch ladder) and diffs it against the
REAL post-patch `polylog.eval` over the boundary table plus ≥1e5 fuzzed
`(s, z)` pairs drawn from the recognized and unrecognized expression forms,
comparing the returned expression (or `None`) by canonical SymPy equality. Exit 0
iff zero disagreements.
