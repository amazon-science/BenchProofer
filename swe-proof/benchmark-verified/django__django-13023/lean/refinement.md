# refinement.md — django__django-13023

Maps every operation of `implementation_toPython` (Solution.lean, impl region)
to its `patch.diff` counterpart. Tags: **R** type refinement / **A-consumed**
proof axiom / **A-reference** deep-model validated == real callee / **I**
identical concrete op. The R/I legs are mechanically refuted by G-CONF; there are
no A legs (G-AX is a skip).

## Modeled function
`DecimalField.to_python(self, value)` (`django/db/models/fields/__init__.py`,
`to_python`). The patch widens the `except` clause that turns a failed decimal
conversion into a `ValidationError` from `decimal.InvalidOperation` alone to
`(decimal.InvalidOperation, TypeError, ValueError)`.

## Operation correspondence

| # | `implementation_toPython` op | `patch.diff` / source op | tag | note |
|---|---|---|---|---|
| 1 | `if v.isNone then return Outcome.returned` | `if value is None: return value` | **I** | unchanged guard; missing value passes through. `v.isNone ↔ value is None`. |
| 2 | `if v.isFloat then return Outcome.returned` | `if isinstance(value, float): return self.context.create_decimal_from_float(value)` | **R** | unchanged float branch. The concrete `Decimal` produced by `create_decimal_from_float` is abstracted to the *observable outcome* `returned` (the float branch always returns normally — incl. `inf`/`nan`, which `create_decimal_from_float` maps to `Decimal('Infinity')`/`Decimal('NaN')` without raising). `v.isFloat ↔ isinstance(value, float)` (consulted only when not `None`). |
| 3 | `match v.conv with \| none => return Outcome.returned` | `try: return decimal.Decimal(value)` (success path) | **R** | deep model of the conversion: `v.conv = none ↔ decimal.Decimal(value)` returns a `Decimal`. The concrete `Decimal` is abstracted to `returned`. |
| 4 | `\| some _ => return Outcome.validationError` | `except (decimal.InvalidOperation, TypeError, ValueError): raise exceptions.ValidationError(...)` | **R** | **the changed op.** Deep model of the failure handler: `v.conv = some e ↔ decimal.Decimal(value)` raises a low-level error of kind `e ∈ {notANumber, unsupportedType, malformedValue}` (= `{InvalidOperation, TypeError, ValueError}`, mapping.md bijection). The impl reports the *same* `validationError` for ALL three kinds — exactly the post-patch behaviour. The pre-patch leg (`Solution_prepatch.lean`) reports `validationError` only for `notANumber` and lets the other two escape as `propagated`, so it fails the spec's fourth conjunct — that is the bug G-DIFF must see. |

## Changed-inexpressible check
None. The only changed op (#4) is modeled deeply as a uniform mapping of every
low-level conversion failure to one validation error; the failure taxonomy
(`ConvError`) is validated against the real `decimal.Decimal` by G-CONF.

## Axioms
`axioms = []`, `deep_model_references = []` (of the A-consumed kind). No unchanged
callee contributes a property the proof consumes — `decimal.Decimal` is modeled
deeply (G-CONF), and `create_decimal_from_float` is abstracted to a normal return.
Hence `axiom_check.py` is a skip stub (G-AX skips).

## Conformance (G-CONF)
`conf_skip = false`: the impl region is all R/I (not all-A-tagged), so the R/I
shadow is differential-tested. `conformance_check.py` derives the Lean `Value`
classification from a real Python value by running `decimal.Decimal(value)` and
catching, applies the impl's branch logic to obtain the shadow `Outcome`, and
diffs it against the faithfully-reconstructed **post-patch** `to_python`
value→outcome over ≥10⁵ fuzzed inputs. Zero disagreements ⟹ exit 0. The check
also asserts the model's exhaustiveness claim: `decimal.Decimal` applied to a
non-`float`, non-`None` value raises ONLY `InvalidOperation` / `TypeError` /
`ValueError` (any other escaping exception would be a `propagated` the model does
not cover, and is reported as a disagreement).
