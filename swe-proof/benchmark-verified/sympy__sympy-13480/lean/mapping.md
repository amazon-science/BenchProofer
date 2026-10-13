# mapping.md — sympy__sympy-13480

## Symbol binding (file:line @ base_commit f57fe3f4b3f2cab225749e1b3b38ae1bf80b62f0)

- Changed function: `coth.eval` (classmethod) —
  `sympy/functions/elementary/hyperbolic.py:555` (`def eval`), additive-argument
  branch at `:587-593`.
- The split: `x, m = _peeloff_ipi(arg)` — `hyperbolic.py:587`, calling
  `_peeloff_ipi` (`hyperbolic.py:37`). `_peeloff_ipi` splits an `Add` into a
  "rest" `x` and a multiple `m` of `I*pi/2` (a Rational multiple of the
  imaginary half-period; `m == 0` when no such summand exists).
- The nonzero-multiple guard: `if m:` — `hyperbolic.py:588`.
- The dispatch value: `cothm = coth(m)` — `hyperbolic.py:589`.
- The patched dispatch test:
  - pre-patch: `if cotm is S.ComplexInfinity:` — `hyperbolic.py:590`
    (`cotm` is unbound in this branch → `NameError`).
  - post-patch: `if cothm is S.ComplexInfinity:` (tests the value bound on the
    preceding line).
- True branch: `return coth(x)` — `hyperbolic.py:591`.
- False branch (`else: # cothm == 0`): `return tanh(x)` — `hyperbolic.py:593`.
- Sentinel: `S.ComplexInfinity` (the `zoo` singleton).

Modeling scope: the additive-argument branch reached with a **nonzero** multiple
part `m` (`if m:` taken) — exactly the case the two new F2P assertions exercise
and the only case the patched line participates in. The argument split
(`_peeloff_ipi`) and the `is_Number` / imaginary-coefficient / negative-coeff
pre-branches are unchanged surrounding context; they are documented here and not
re-modeled — they select *which* `(x, m)` reach the dispatch, not how the
dispatch behaves.

## F2P behavior witnessed (post-patch, base_commit semantics)

- `coth(log(tan(2)))`: `log(tan(2)) = log(-tan(2)) + I*pi`, so the split gives
  `m = I*pi` (an even multiple of `I*pi/2`); `coth(I*pi) = zoo =
  S.ComplexInfinity`, so the dispatch is true and the result is `coth(x) =
  coth(log(-tan(2)))`. Matches `coth(log(tan(2))) == coth(log(-tan(2)))`.
- `coth(1 + I*pi/2)`: split gives `x = 1`, `m = I*pi/2`; `coth(I*pi/2) = 0`
  (not `zoo`), so the dispatch is false and the result is `tanh(x) = tanh(1)`.
  Matches `coth(1 + I*pi/2) == tanh(1)`.
Both raised `NameError` pre-patch.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean |
|---|---|
| symbolic expression `Expr` (the subterms `x`, `m`) | `Expr` (a `repr : String` carrier; observed via equality + as evaluator args) |
| `S.ComplexInfinity` (`zoo`) | `complexInfinity : Expr` (opaque) |
| `coth(·)` evaluator applied to a subterm | `cothFn : Expr → Expr` (opaque) |
| `tanh(·)` evaluator applied to a subterm | `tanhFn : Expr → Expr` (opaque) |
| `x is S.ComplexInfinity` (identity vs singleton) | `cothFn m = complexInfinity` (decidable equality) |
| branch completes returning value `v` | `Except.ok v` |
| branch raises (does not complete; `NameError` pre-patch) | `Except.error ()` |
| `coth(arg)` with `arg.is_Add`, `m ≠ 0` | `implementation_cothReduce x m` |

## Callee provenance — none consumed as axioms

The three opaque declarations (`cothFn`, `tanhFn`, `complexInfinity`) are
UNCHANGED outside operations the branch uses:

- `cothFn` ↔ `coth` evaluator (`hyperbolic.py:555`), applied to `m` and to `x`.
- `tanhFn` ↔ `tanh` evaluator (`tanh.eval`, `hyperbolic.py:258`), applied to `x`.
- `complexInfinity` ↔ `S.ComplexInfinity` singleton (`sympy/core/numbers.py`,
  `ComplexInfinity`).

They are tagged **A-reference**, NOT consumed axioms: the proof of
`correct_cothReduce` discharges the spec by definitional case analysis on the
single decidable test `cothFn m = complexInfinity`, consuming no property of
these callees. No `axiom _prop` is declared. G-AX is therefore a skip stub; the
faithfulness of the dispatch (and of the abstract callees against the real
`coth`/`tanh`/`zoo`) is validated end-to-end by G-CONF against the real patched
function.

No flag dependency: the dispatch is unconditional once the `if m:` branch is
entered.

## G-CONF fuzz seed

Pinned seed: **13480**. Fuzz inputs are sympy expressions of the form
`x + m` where `m` is a nonzero Rational multiple `k/2` of `I*pi` (i.e.
`m = Rational(p, q) * I * pi` reduced to the half-period lattice) and `x` is a
small real/symbolic term, sampled so that both dispatch legs are exercised:
`m` an even multiple of `I*pi/2` (→ `coth(m) = zoo`, true leg) and `m` an odd
multiple (→ `coth(m) = 0`, false leg). The shadow runs the Lean dispatch
(`coth(m) is zoo ? coth(x) : tanh(x)`) and diffs against the real patched
`coth(x + m)`.
