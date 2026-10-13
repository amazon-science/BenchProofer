# mapping.md — sympy__sympy-13480

Model ↔ repo symbol binding, type abstraction, and callee provenance.
All file:line references are at `base_commit`
`f57fe3f4b3f2cab225749e1b3b38ae1bf80b62f0`.

## Changed function under specification

| model symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `periodic_part_simplification(x, m)` | the periodic-part (`arg.is_Add`) branch inside `coth.eval` | `sympy/functions/elementary/hyperbolic.py:586-593` (class `coth`, `@classmethod eval`) |

The repo code at that branch:

```python
if arg.is_Add:
    x, m = _peeloff_ipi(arg)
    if m:
        cothm = coth(m)
        if cotm is S.ComplexInfinity:   # base_commit line 590
            return coth(x)
        else: # cothm == 0
            return tanh(x)
```

`periodic_part_simplification` models the body executed once `m` is truthy (the
guarded inner block): it receives the two pieces produced by the peel-off
(`x` = remainder part, `m` = periodic part) and returns the simplified
expression. The outer guards (`arg.is_Add`, `if m:`) and the peel-off
(`_peeloff_ipi`, `sympy/functions/elementary/hyperbolic.py:37`) are control
context that selects this branch; they are not part of the modeled
data-flow and are not modeled.

## Type abstraction

| repo reality | model |
|---|---|
| a sympy expression (`Expr`) | opaque integer handle (`int`) |
| `S.ComplexInfinity` (singleton `Expr`) | the distinguished handle `directed_infinity()` |
| `coth(...)` applied to an expression | the pure callee `primary(...)` over handles |
| `tanh(...)` applied to an expression | the pure callee `sibling(...)` over handles |
| `expr is S.ComplexInfinity` (identity test) | `handle == directed_infinity()` |

Expression *values* are opaque: the only property the proof relies on is that
each elementary function is a deterministic map (a fixed argument yields a
fixed result handle), so "the value computed from `m`" is the same value later
inspected. This is exactly what `@Pure` provides in Nagini and what sympy
guarantees (deterministic construction; `S.ComplexInfinity` is a singleton, so
the `is` test is deterministic). No richer property of `coth`/`tanh` is used.

## Callee provenance (axioms region)

All three are UNCHANGED by the patch — the patch touches only the branch test,
not `coth`, `tanh`, or `S.ComplexInfinity`.

| axiom | models | provenance (base_commit) | contract relied on |
|---|---|---|---|
| `primary` | `coth` (the hyperbolic cotangent ctor/eval) | `sympy/functions/elementary/hyperbolic.py:537` (class `coth(HyperbolicFunction)`) | determinism only (no `Ensures`); `@Pure` |
| `sibling` | `tanh` | `sympy/functions/elementary/hyperbolic.py:391` (class `tanh(HyperbolicFunction)`) | determinism only (no `Ensures`); `@Pure` |
| `directed_infinity` | `S.ComplexInfinity` | `sympy/core/singleton.py` registry; `ComplexInfinity` defined in `sympy/core/numbers.py:3239` (the `zoo` singleton) | a fixed singleton handle; `@Pure` |

Because the axioms carry **no `Ensures`**, there is no value/sentinel/raise
behavior to over-claim (SPEC_GUIDE directive 7). The only obligation G-AX
checks is determinism + the singleton identity, plus the end-to-end branch
correspondence against the real (gold-patched) `coth.eval` — see
`axiom_check.py`.

## Why the bug is a `NameError` and how the model expresses it

At `base_commit` line 589 binds `cothm = coth(m)`; line 590 tests `cotm`
(an unbound name) instead of `cothm`. On any input that reaches this branch
with `m` truthy (e.g. `coth(log(tan(2)))`, `coth(1 + I*pi/2)`), Python raises
`NameError: name 'cotm' is not defined` before any value is returned. The
intended behavior — confirmed by the sibling `tanh.eval`
(`hyperbolic.py:445-452`), which tests the same locally-computed `tanhm` —
is to branch on the just-computed `coth(m)`.

Nagini cannot host a literally-unbound name, so the pre-patch skeleton
(`model_prepatch.py`) expresses the defect faithfully as **inspecting a
different quantity than the one computed from `m`**: it tests
`primary(x) == directed_infinity()` rather than `primary(m) == ...`. This is
the same failure mode (the branch is decided by the wrong/unrelated value),
and it is exactly what the discriminating postcondition forbids.
