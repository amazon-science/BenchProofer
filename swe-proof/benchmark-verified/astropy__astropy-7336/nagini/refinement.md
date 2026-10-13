# refinement.md — astropy__astropy-7336

The operation-by-operation correspondence between `model.py`'s implementation
(the `finalize_return` impl region, the deep `convert_unit` model, and the
`is_genuine_target` decision) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == a real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The return-finalisation site — `wrapper` (`astropy/units/decorators.py:223-226`)

Gold hunk:
```
- if wrapped_signature.return_annotation is not inspect.Signature.empty:
+ if wrapped_signature.return_annotation not in (inspect.Signature.empty, None):
              return return_.to(wrapped_signature.return_annotation)
          else:
              return return_
```

| # | model.py impl op (`finalize_return`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target: int` | `wrapped_signature.return_annotation` | R | the declared return target abstracted to an int code: `inspect.Signature.empty` ↔ `TARGET_UNSPECIFIED()`, the `None` annotation ↔ `TARGET_NOVALUE()`, a genuine unit ↔ any int with `is_genuine_target` true (mapping.md §2). |
| A2 | parameter `ret: RetVal` (`is_none`, `unit`) | the local `return_` (the wrapped function's return value) | R | `return_ is None` ↔ `ret.is_none`; the unit of a `Quantity` return ↔ `ret.unit`; the `None` object carries no unit ↔ `ret.unit == NO_UNIT()` (mapping.md §2). |
| A3 | the guard `is_genuine_target(target)` = `target != TARGET_UNSPECIFIED() and target != TARGET_NOVALUE()` | `return_annotation not in (inspect.Signature.empty, None)` | I + R | identical boolean structure — membership-in-a-2-element-tuple is exactly the conjunction of two `!=` tests; under R (A1) the two excluded members are the two sentinels. This is THE changed operation, expressed identically once the annotation domain is refined (A1). |
| A4 | genuine-target branch: `return RetVal(False, convert_unit(ret.unit, target))` | `return return_.to(wrapped_signature.return_annotation)` | A-reference | `return_.to(annotation)` is modelled DEEPLY by `convert_unit` (pure region): the converted quantity is a genuine quantity (`is_none == False`) whose unit IS the target. There is no consumed `to` axiom — the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `Quantity.to(target)` and asserts `.unit == target` (mapping.md §3.1). |
| A5 | pass-through branch: `return RetVal(ret.is_none, ret.unit)` | `return return_` | R | observationally the identity on the value: the real wrapper returns the SAME object, the model returns a fresh `RetVal` equal on both observed fields (`is_none`, `unit`). The F2P/P2P tests observe only `result is None` (↔ `is_none`) and `result.unit` (↔ `unit`); both agree (mapping.md §2). |

The discriminating content of the change — the `None` return target is treated
like the unspecified sentinel (pass through), NOT like a genuine unit target —
lives in `is_genuine_target(TARGET_NOVALUE()) == False` (model) ⇔ `None in
(inspect.Signature.empty, None)` (real). The pre-patch guard excluded ONLY the
unspecified sentinel; `model_prepatch.py` reproduces that (`if target !=
TARGET_UNSPECIFIED(): convert`) and **fails** verification on the discriminating
`target == TARGET_NOVALUE()` input, because it then calls `convert_unit` whose
precondition `is_genuine_target(target)` does not hold — exactly the real
`None.to(None)` misuse the spec senses (G-DIFF).

## B. Why `convert_unit` is an A-reference, not a consumed axiom

`convert_unit` is a `@Pure` function with a body (`return target`), proven, not a
`@ContractOnly`. The proof of `finalize_return`'s genuine-target postcondition
uses `convert_unit`'s definition, not an opaque axiom; the function is validated
== the real `Quantity.to` by G-AX (mapping.md §3.1). The axioms region of
model.py is therefore empty, and there is no dead axiom. Likewise the
return-finalisation *decision* itself (A3+A4+A5) is validated == the real
`quantity_input` wrapper post-fix by G-AX (mapping.md §3.2): an **A-reference**,
since the changed operation is modelled deeply rather than hidden behind an
axiom about the function under change.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — the conversion guard — is expressed **identically** (A3) once the
annotation domain is type-refined (A1); the conversion it gates (`Quantity.to`)
is modelled **deeply** as `convert_unit` and validated against the real callee
(A4, A-reference). There is **no consumed axiom** and no kind-3 step.

## D. verify(model) ⇒ resolved

`finalize_return` verifies only if (A4) it converts to the declared unit exactly
when a genuine unit target is declared, and (A5) passes the value through
unchanged for BOTH the unspecified sentinel and the no-value (`-> None`) target —
and the no-value pass-through is forced by `convert_unit`'s precondition
`is_genuine_target(target)`, which would be violated if the impl tried to
convert on `TARGET_NOVALUE()`. By R (annotation ↔ int code, `return_` ↔ `RetVal`,
pass-through ↔ identity-on-observables) the verified decision equals the gold
guard `not in (inspect.Signature.empty, None)` with `return_.to(...)` /
`return return_`; by G-AX the deep model `convert_unit` equals the real
`Quantity.to` (A-reference) and the deep `finalize_return` decision equals the
real post-fix wrapper (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (here, deep-model == real callee, G-AX) and
refinement fidelity (this document, G-EQ).
