# refinement.md — django__django-13121

Maps every operation in `implementation_expressionSqlStrategy` to its
`patch.diff` counterpart in `CombinedExpression.as_sql`
(`django/db/models/expressions.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch behavior — the strategy-selection head)
```python
# CombinedExpression.as_sql, after computing lhs_type / rhs_type
# (each = self.<side>.output_field.get_internal_type(), or None on FieldError):
if (
    not connection.features.has_native_duration_field and
    'DurationField' in {lhs_type, rhs_type} and
    lhs_type != rhs_type
):
    return DurationExpression(self.lhs, self.connector, self.rhs).as_sql(compiler, connection)
datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
    return TemporalSubtraction(self.lhs, self.rhs).as_sql(compiler, connection)
# else: generic combine_expression path
```
The modeled value is WHICH of the three strategies is selected. The bug the issue
reports (duration + duration on SQLite/MySQL crashing in
`convert_durationfield_value`) is caused by the pre-patch head routing a
duration+duration expression into the duration-arithmetic strategy; the fix's new
`lhs_type != rhs_type` guard makes a same-type (duration+duration) expression
fall through to the generic strategy instead.

## Operation correspondence
| # | Lean op (`implementation_expressionSqlStrategy`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if nativeDurationSupport = false ∧ (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then return ExprStrategy.durationArithmetic` | `if not connection.features.has_native_duration_field and 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type: return DurationExpression(...).as_sql(...)` | R | op-for-op: `not has_native_duration_field ↔ nativeDurationSupport = false`; `'DurationField' in {lhs_type, rhs_type} ↔ isDurationField lhs ∨ isDurationField rhs`; `lhs_type != rhs_type ↔ lhs ≠ rhs` (the FIX); selecting `DurationExpression.as_sql` ↔ `durationArithmetic`. Type bijection in mapping.md. |
| 2 | `if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then return ExprStrategy.dateSubtraction` | `if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type: return TemporalSubtraction(...).as_sql(...)` | R | `connector == SUB ↔ isSubtraction`; `lhs_type in {Date,DateTime,Time} ↔ isDateTimeField lhs`; `lhs_type == rhs_type ↔ lhs = rhs`. With `lhs = rhs`, `rhs_type in datetime_fields` is implied, matching the post-patch dropping of the separate `rhs_output` check. Selecting `TemporalSubtraction.as_sql` ↔ `dateSubtraction`. |
| 3 | `return ExprStrategy.genericArithmetic` | falling through both guards to the generic `combine_expression` body | R | every remaining case ↔ the ordinary arithmetic path ↔ `genericArithmetic`. This is where duration+duration now correctly lands. |

Every op is **R**; **no A row** — no unchanged callee contract is consumed and no
op is deeply modeled over an opaque callee. The three downstream strategy bodies
(`DurationExpression.as_sql`, `TemporalSubtraction.as_sql`, generic
`combine_expression`) are observed only as the IDENTITY of the strategy selected,
per mapping.md — not as contracts. Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## Notes on the rest of the gold diff (consequential dead-code cleanup)
The gold patch also: drops the `DurationValue` class; drops the now-unreachable
`date_interval_sql` methods on base/mysql/sqlite3 ops (and their import + the
deleted base-class test); simplifies `_combine` to always build a `Value` with an
optional `output_field`; and simplifies `DurationExpression.compile` (no longer
special-casing `DurationValue`). All of these are *consequences* of removing the
`DurationValue` indirection and do NOT change the observable strategy-selection
decision modeled here — they are the mechanism by which a duration literal now
carries a `DurationField` `output_field` so the SAME head logic classifies it.
The single behavior the FAIL_TO_PASS test (`test_duration_expressions`) observes
is the routing decision in op #1's new `lhs_type != rhs_type` guard.

## R legs ⇒ G-CONF
The whole impl is R, so `conformance_check.py` mechanically differential-tests the
impl shadow against the post-patch decision over the full finite operand domain
plus ≥10^5 fuzzed inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the head lacked the `lhs_type != rhs_type` guard: ANY expression with a
duration operand (and no native duration support) was routed to the duration
strategy — including duration + duration, the F2P case
(`F('estimated_time') + timedelta`). On SQLite/MySQL this produced SQL that fed a
non-numeric interval string into `convert_durationfield_value`, raising
`decimal.InvalidOperation`. The prepatch impl
(`implementation_expressionSqlStrategy` with op #1's guard reduced to
`nativeDurationSupport = false ∧ (isDurationField lhs ∨ isDurationField rhs)`,
missing `lhs ≠ rhs`) is exactly this. It cannot satisfy
`problem_spec_expressionSqlStrategy` on the discriminating third clause: with
`nativeDurationSupport = false`, `lhs = rhs = some durationField`,
`isSubtraction = false`, the spec's `durationCond` is FALSE (requires `lhs ≠ rhs`)
and `dateSubCond` is FALSE, so the result must be `genericArithmetic`; the buggy
impl returns `durationArithmetic`, so the carried gold proof's `rw [if_neg hnd,
if_neg hns]` cannot rewrite the impl's differently-shaped `if`, and the case fails.
This is precisely what `test_duration_expressions (FTimeDeltaTests)` exercises.
G-DIFF: `Solution_prepatch.lean` fails to verify (confirmed, exit 1).
