# mapping.md — sympy__sympy-13480

Model ↔ repo symbol binding, type abstraction, and callee provenance.
All file:line references are at `base_commit`
`f57fe3f4b3f2cab225749e1b3b38ae1bf80b62f0`.

## Changed function under specification

| model symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `cothEvalPeriodic (x m : Int)` | the periodic-part (`arg.is_Add`) branch inside `coth.eval` | `sympy/functions/elementary/hyperbolic.py:586-593` (class `coth`, `@classmethod eval`) |

The repo code at that branch:

```python
if arg.is_Add:
    x, m = _peeloff_ipi(arg)
    if m:
        cothm = coth(m)
        if cotm is S.ComplexInfinity:   # base_commit line 590 (typo: cotm)
            return coth(x)
        else: # cothm == 0
            return tanh(x)
```

`cothEvalPeriodic` models the body executed once `m` is truthy (the guarded
inner block): it receives the two pieces produced by the peel-off (`x` =
remainder part, `m` = periodic part) and returns the simplified expression
handle. The outer guards (`arg.is_Add`, `if m:`) and the peel-off
(`_peeloff_ipi`, `sympy/functions/elementary/hyperbolic.py:37`) are control
context that selects this branch; they are not part of the modeled data-flow
and are not modeled.

## Type abstraction (opaque-handle model)

Symbolic expressions are modeled as opaque `Int` handles — the Lean port of the
nagini "opaque integer handle" model. The only property the proof relies on is
that each elementary function is a deterministic map (a fixed argument handle
yields a fixed result handle), so "the value computed from `m`" is the same
value later inspected. This is exactly what an `opaque : Int → Int` provides in
Lean and what sympy guarantees (deterministic construction; `S.ComplexInfinity`
is a singleton, so the `is` test is deterministic). No richer property of
`coth`/`tanh`/`cot` is used.

| repo reality | model |
|---|---|
| a sympy expression (`Expr`) | opaque integer handle (`Int`) |
| `S.ComplexInfinity` (singleton `Expr`) | the opaque distinguished handle `directedInfinity : Int` |
| `coth(...)` applied to an expression | the opaque callee `primaryEval : Int → Int` |
| `tanh(...)` applied to an expression | the opaque callee `siblingEval : Int → Int` |
| `cot(...)` applied to an expression | the opaque callee `cofamilyEval : Int → Int` (pre-image only) |
| `expr is S.ComplexInfinity` (identity test) | `handle = directedInfinity` (decidable `Int` equality) |

`opaque` (not `axiom`) is required: these symbols are referenced inside the
executable Velvet `do` block, and a bare `axiom` referenced in a `do` block
triggers Lean's code-generator error (`dependsOnNoncomputable`). `opaque` keeps
the value abstract for the proof (same weakest-contract semantics) while being
computable so the block elaborates. (LESSONS.md, django-12276.)

## Callee provenance (axioms region)

All four are UNCHANGED by the patch — the patch touches only the branch test,
not `coth`, `tanh`, `cot`, or `S.ComplexInfinity`.

| model symbol | models | provenance (base_commit) | contract relied on |
|---|---|---|---|
| `primaryEval` | `coth` (the hyperbolic cotangent ctor/eval) | `sympy/functions/elementary/hyperbolic.py:537` (class `coth(HyperbolicFunction)`) | determinism only (opaque free function; no asserted `ensures`) |
| `siblingEval` | `tanh` | `sympy/functions/elementary/hyperbolic.py:391` (class `tanh(HyperbolicFunction)`) | determinism only (opaque free function) |
| `cofamilyEval` | `cot` (the circular cotangent — a DIFFERENT function in the family) | `sympy/functions/elementary/trigonometric.py` (class `cot`) | determinism only; appears only in the pre-image to model "the wrong variable" |
| `directedInfinity` | `S.ComplexInfinity` | `sympy/core/singleton.py` registry; `ComplexInfinity` defined in `sympy/core/numbers.py:3239` (the `zoo` singleton) | a fixed singleton handle (opaque constant) |

Because the opaque symbols carry **no asserted value/`ensures`**, there is no
value/sentinel/raise behavior to over-claim (SPEC_GUIDE directive 7). They are
free functions/constants: the spec pins only the STRUCTURE of the branch
(governed by `primaryEval m`). There is nothing to validate against the real
callee, so **no axiom_check.py / G-AX skip** (meta.json `gates.G-AX.status =
"skip"`).

## Why the bug is a `NameError` and how the model expresses it

At `base_commit` line 589 binds `cothm = coth(m)`; line 590 tests `cotm`
(an unbound name) instead of `cothm`. On any input that reaches this branch with
`m` truthy (e.g. `coth(log(tan(2)))`, `coth(1 + I*pi/2)`), Python raises
`NameError: name 'cotm' is not defined` before any value is returned. The
intended behavior — confirmed by the sibling `tanh.eval`
(`hyperbolic.py:445-452`), which tests the same locally-computed `tanhm` — is to
branch on the just-computed `coth(m)`.

Lean cannot host a literally-unbound name, so the pre-patch skeleton
(`Solution_prepatch.lean`) expresses the defect faithfully as **inspecting a
different quantity than the one computed from `m`**: it tests
`cofamilyEval m = directedInfinity` (an unrelated family function, the model of
`cot m`) rather than `primaryEval m = directedInfinity` (the computed
`coth(m)`). This is the same failure mode (the branch is decided by the
wrong/unrelated value), and it is exactly what the discriminating postcondition
forbids. Because `primaryEval` and `cofamilyEval` are DISTINCT opaque functions,
loom cannot prove they agree, so the prepatch's output cannot be shown equal to
the spec → `prove_correct` fails.

## G-CONF fuzz seed

`conf_skip = true`. Symbolic sympy expressions have no DB-free numeric R/I
shadow: the oracle is sympy's symbolic engine itself (`S.ComplexInfinity`
identity over arbitrary `Expr` trees), which cannot be reconstructed from a
fuzzed integer carrier. The impl region is all-opaque/A-tagged. No fuzz seed;
`conformance_check.py` is a `status=skip` stub. Soundness rests on
G-VERIFY + G-DIFF + G-RESOLVE + G-EQ.
