# mapping.md — sympy__sympy-13852

## Function under spec

The behavior modeled is the **automatic closed-form evaluation** of a
parametrized special function on construction: given an order `s` and an argument
`z` (both symbolic expressions), decide whether the pair has a recognized closed
form and, if so, return it; otherwise leave the call unevaluated.

| Lean symbol | Python symbol | file:line @ base_commit `c935e1d106743efd5bf0705fbeedbd18fadff4dc` |
|---|---|---|
| `implementation_polylogEval` / `problem_spec_polylogEval` / `correct_polylogEval` | `polylog.eval(cls, s, z)` classmethod | `sympy/functions/special/zeta_functions.py:272-279` (the `@classmethod def eval` body, extended by the patch to lines 272-301) |

The patch's other hunk edits `polylog._eval_expand_func` (the `s == 1` branch,
removing a spurious `exp_polar(-I*pi)` factor) and the class docstring example.
That branch is NOT exercised by the graded test (`test_polylog_values`), which
calls only the automatic `eval` path; see "Independent hunk" below.

## Why `eval` is the modeled function

The graded FAIL_TO_PASS test is `test_polylog_values`. It asserts, e.g.,
`polylog(2, 2) == pi**2/4 - I*pi*log(2)`, `polylog(2, S.Half) == pi**2/12 -
log(2)**2/2`, and that `polylog(s, z).evalf()` matches the unevaluated numeric
value for `s ∈ {-1, 0, 1}` and the six order-2 arguments. Constructing
`polylog(s, z)` triggers `polylog.eval(s, z)`; its return value (or `None`,
meaning "stay unevaluated") is precisely what the test observes. So the
independently-fixed, graded behavior is `eval`'s dispatch table.

- **pre-patch** `eval`: handles only `z ∈ {1, -1, 0}` (and `z == 0` returned the
  Python `int` `0`); for every other pair it falls off the end ⇒ implicit `None`
  ⇒ the call stays unevaluated. Hence `polylog(2, S.Half)` did not evaluate.
- **post-patch** `eval`: adds, for `s == 2`, a six-entry argument table; for
  `s == 0` and `s == -1`, a rational closed form `z/(1-z)` resp. `z/(1-z)**2`;
  and returns `S.Zero` for `z == 0`.

## Type bijection (used by G-CONF)

| Python (SymPy) | Lean `SymExpr` |
|---|---|
| symbolic order/argument expression | `SymExpr` (structural carrier) |
| `Integer(n)` | `.lit n` |
| `pi` | `.pi` |
| `I` (imaginary unit) | `.imagUnit` |
| `sqrt(5)` | `.sqrt5` |
| `log(x)` | `.log x` |
| `zeta(s)` | `.zeta s` |
| `dirichlet_eta(s)` | `.eta s` |
| `-x` | `.neg x` |
| `a + b`, `a - b`, `a*b`, `a/b` | `.add`/`.sub`/`.mul`/`.div` |
| `x**n` (integer n) | `.powInt x n` |
| `S.Half` = `Rational(1,2)` | `SymExpr.half` = `.div (.lit 1) (.lit 2)` |
| `(sqrt(5)-1)/2`, `(sqrt(5)+1)/2`, `(3-sqrt(5))/2` | `SymExpr.gSub`, `SymExpr.gAdd`, `SymExpr.zC` |
| `polylog.eval` returns an expression | `Option.some <expr>` |
| `polylog.eval` returns `None` (stay unevaluated) | `Option.none` |

**Equality model.** Lean `SymExpr` uses *structural* `DecidableEq`. SymPy's `eval`
recognizes its argument by *structural / canonical-form* equality too (`z ==
S.Half`, `z == -(sqrt(5)-1)/2`, etc., are SymPy `Eq`-to-`True` structural
comparisons on the canonicalized inputs). The conformance check therefore feeds
each leg the *canonical SymPy form* of the table argument, so the structural Lean
match and SymPy's `==` dispatch agree. This is the dispatch the test exercises:
the test constructs the arguments by the same expressions (`S.Half`, `2`,
`(sqrt(5)-1)/2`, …).

## Callee provenance / flag dependencies

- No callee is axiomatized. The closed-form *outputs* (`zeta(s)`,
  `dirichlet_eta(s)`, the `pi`/`log`/`sqrt` expressions) are opaque `SymExpr`
  builders — the spec pins only *that* the correct builder-expression is returned
  for each recognized case, which is exactly what `eval` decides. There is no
  unchanged pure callee whose internal numeric behavior the proof must assume, so
  the axioms region declares only the `SymExpr` carrier and there is no `axiom
  <callee>_prop`.
- The dispatch has no runtime flag dependency: `eval` is a pure classmethod with
  no keyword configuration affecting these branches.

## Independent hunk (`_eval_expand_func`) — not separately modeled

The patch's second functional hunk changes the `s == 1` branch of
`_eval_expand_func` from `-log(1 + exp_polar(-I*pi)*z)` to `-log(1 - z)` (and the
docstring example). This is `expand_func(polylog(1, z))`, exercised by
`test_polylog_expansion` — which is **already PASSING at base_commit** and is NOT
in this instance's FAIL_TO_PASS set (`test_polylog_values` is). The graded
resolution is driven entirely by the `eval` table. The hunk is carried verbatim
in `patch.diff` for `resolved` parity (the harness applies the whole gold patch)
but is not an independently-graded behavior requiring its own triple; modeling it
would also require modeling `exp_polar` branch semantics with no effect on the
F2P verdict.

## G-CONF fuzz seed

`conf_seed = 13852` (pinned in `meta.json` and `conformance_check.py`).

## G-CONF `agree()` — non-finite result handling (root-cause of the prior 682)

The recognized case `s == 1, z == 1` makes both the real `polylog.eval` and the
shadow return `zeta(1)`, which auto-evaluates to `zoo` (complex infinity). The
original `agree()` certified equality via `simplify(real - shadow) == 0`, but
`simplify(zoo - zoo)` is `nan`, and `nan == 0` is `False` — so this genuinely
*agreeing* cell was reported as a disagreement. Being one of 9×19 boundary cells,
it was fuzz-sampled ~682 times, giving the prior 682-disagreement G-CONF fail.

Fix: `agree()` now tests canonical/structural equality (`real == shadow`) FIRST —
authoritative for non-finite results — and treats any non-finite `simplify`
difference (`nan`/`zoo`/`±oo`) as *not certified equal by subtraction* rather
than silently comparing to 0. Verified against the real base-commit
`polylog.eval` over the full boundary table + 1.2e5 fuzzed pairs: **0
disagreements**. This is a checker-soundness fix only; neither the Lean spec/impl
nor the shadow ladder changed.
