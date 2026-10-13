# refinement.md — sympy__sympy-13480

Operation correspondence between `implementation_cothReduce` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## What the fix is

The gold patch is a one-token correction inside the additive-argument branch of
the hyperbolic-cotangent evaluator (`coth.eval`, `arg.is_Add` case). After the
argument is split into a remaining part `x` and a multiple `m` of the imaginary
half-period and the multiple is found nonzero (`if m:`), the value computed for
the dispatch is `cothm = coth(m)`. The dispatch test must compare *that* value
against the point at infinity. The pre-patch line tests a name that was never
bound in this branch, so the branch does not complete — it raises `NameError`
and yields no value. The post-patch line tests the value that was actually
computed, so the branch completes and selects `coth(x)` (when `coth(m)` is the
point at infinity) or `tanh(x)` (otherwise).

The modeled observable is the outcome of this branch given `x` and the nonzero
`m`: an `Except Unit Expr` — `Except.ok v` for a completed reduction yielding
`v`, `Except.error ()` for a branch that does not complete.

## `implementation_cothReduce` ↔ the `if m:` branch of `coth.eval`

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let cothm := cothFn m` | `cothm = coth(m)` | A-reference | `cothFn` is the unchanged `coth` evaluator; left abstract, its result is validated == real `coth` by G-AX/G-CONF. The binding itself is identical control flow. |
| `if cothm = complexInfinity then …` | `if cothm is S.ComplexInfinity:` (post-patch) | I | the dispatch test — the corrected line. `is S.ComplexInfinity` (identity against the singleton sentinel) ↦ `= complexInfinity` (equality against the abstract sentinel value). `complexInfinity` is an A-reference (`S.ComplexInfinity`). |
| `return Except.ok (cothFn x)` | `return coth(x)` | A-reference | true branch; `cothFn` unchanged `coth`. Wrapping in `Except.ok` is the R encoding of "branch completes with a value". |
| `return Except.ok (tanhFn x)` | `return tanh(x)` (the `else` branch) | A-reference | false branch; `tanhFn` unchanged `tanh`. Same R encoding. |

Every op is **I** or **A-reference**. There is no consumed `_prop` axiom: the
proof discharges `problem_spec_cothReduce` by definitional case-analysis on the
dispatch test, never appealing to a property of `cothFn`/`tanhFn`/
`complexInfinity`. The A-reference callees are validated against the real repo
callees by G-CONF (the dispatch is differential-tested end-to-end against the
real patched `coth`); G-AX is a skip stub.

The `Except.error ()` outcome appears only in the prepatch (the non-completing
branch); the gold impl never produces it, matching the spec's guarantee that the
reduction always completes for this case.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the dispatch is never reached as a completed
  computation — the branch yields `Except.error ()` (no value), modeling the
  pre-patch `NameError` raised by testing an unbound name. The carried gold
  proof of `correct_cothReduce` fails to close: the spec requires
  `Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)`, but
  the prepatch produces `Except.error ()`. (FAIL_TO_PASS: `test_coth`; new
  assertions `coth(log(tan(2))) == coth(log(-tan(2)))` and
  `coth(1 + I*pi/2) == tanh(1)`, both of which raised pre-patch.)
