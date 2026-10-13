# refinement.md — astropy__astropy-7336

Each operation of `implementation_applyReturnAnnotation` mapped to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op).

The modeled function is the return-finalizing epilogue of the unit-validating
function wrapper:

```python
            if wrapped_signature.return_annotation not in (inspect.Signature.empty, None):
                return return_.to(wrapped_signature.return_annotation)
            else:
                return return_
```

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `match annot with \| .unit u => … \| _ => …` (the branch selector) | the PATCHED guard `wrapped_signature.return_annotation not in (inspect.Signature.empty, None)` | R | The Python guard is true exactly when the annotation is *neither* the sentinel `empty` *nor* `None`, i.e. when it designates a concrete unit (`.unit u`). Modeled by the three-way `RetAnnotation` (`empty` / `noUnit` / `unit u`); only `.unit u` takes the conversion arm. The `empty`↔`empty` and `noUnit`↔`None` correspondences are the type refinement. This is THE fix: pre-patch the guard only excluded `empty`, so `None` (≈ `noUnit`) wrongly entered the conversion arm. |
| 2 | `return .ok (convertTo ret u)` | `return return_.to(wrapped_signature.return_annotation)` | A-reference | The unchanged value conversion `.to(unit)`. Not touched by the patch; modeled as the opaque callee `convertTo : RetVal → UnitObj → RetVal` (takes a *concrete* unit, never an absent/no-unit annotation — no impossible states) and validated against the real `Quantity.to` by G-AX. Reached only on the concrete-unit arm; succeeds (`.ok`). |
| 3 | `return .ok ret` | `return return_` (the `else` branch) | I | Identical concrete op: the produced value is returned unchanged, successfully. Reached for both `empty` and `noUnit`. |

Control flow: `Id.run do` with a `match` on the annotation — a `.unit u` arm
that converts and a catch-all `_` arm that passes the value through — a
line-for-line skeleton of the real two-armed `if/else` epilogue under the
patched guard.

## Outcome modeling (`Except FinalizeError RetVal`)

The real bug is an *exception*: a `-> None` annotation under the pre-fix guard
ran `return_.to(None)`, raising `AttributeError` (`None` has no `.to`). To make
"a conversion was wrongly attempted on a non-unit target" observable (rather than
silently collapsed into a value), finalizing returns `Except FinalizeError
RetVal`: success carries the finalized value, failure marks an attempted
conversion that had no convertible target. A correct finalizer succeeds on every
annotation shape; the bug surfaces as a failure on `noUnit`.

## Prepatch discriminator

`Solution_prepatch.lean` replaces the op-1 selector with "annotation is present"
(`match annot with | .empty => .ok ret | .noUnit => .error {} | .unit u => .ok
(convertTo ret u)`), mirroring the pre-fix guard `is not inspect.Signature.empty`
that fires for *any* non-absent annotation. On a `noUnit` annotation (≈ Python
`-> None`), the frozen spec demands `result = .ok ret`, but the buggy impl
returns `.error {}` (the failed conversion against a no-unit target — exactly the
real `AttributeError`). The carried gold proof cannot discharge the `noUnit`
clause — G-DIFF satisfied. This is exactly the F2P scenario
`test_return_annotation_none` (`-> None` must succeed and pass the value
through).

## Tag summary

One **R** row (op 1, the guard/selector) and one **I** row (op 3, passthrough)
⇒ the impl region has R/I content ⇒ `conf_skip = false`; G-CONF differential-tests
the R/I shadow (the three-way classification + passthrough) against the real
patched decorator, with the A-reference `convertTo` left as the real
`Quantity.to`. No **A-consumed** rows ⇒ no consumed callee axiom; the proof
closes by case analysis on `annot`.
