# mapping.md — django__django-13121

## Symbol binding (file:line @ base_commit ec5aa2161d)
- Modeled function: `CombinedExpression.as_sql` strategy-selection head
  (`django/db/models/expressions.py:443-459` @ base_commit). The post-patch
  decision (gold) at the same site selects, from the two operand field types,
  the operator, and the backend's native-duration support, which of three
  SQL-generation strategies builds the expression:
  - `DurationExpression(...).as_sql(...)`  → `ExprStrategy.durationArithmetic`
  - `TemporalSubtraction(...).as_sql(...)` → `ExprStrategy.dateSubtraction`
  - the fall-through generic `combine_expression` path → `ExprStrategy.genericArithmetic`
- Lean triple: `implementation_expressionSqlStrategy` /
  `problem_spec_expressionSqlStrategy` / `correct_expressionSqlStrategy` in
  `Solution.lean`.

## Lean ↔ Python type bijection (G-CONF uses this)
| Python | Lean | note |
|---|---|---|
| `connection.features.has_native_duration_field : bool` | `nativeDurationSupport : Bool` | base default `False` (features.py:69) |
| `self.connector == self.SUB` | `isSubtraction : Bool` | the operator is subtraction |
| `self.lhs.output_field.get_internal_type()` or `None` on `FieldError` | `lhs : Option FieldType` | operand field type, or `none` if unresolvable |
| `self.rhs.output_field.get_internal_type()` or `None` on `FieldError` | `rhs : Option FieldType` | operand field type, or `none` if unresolvable |
| internal-type string `'DurationField'` | `FieldType.durationField` | |
| `'DateField' / 'DateTimeField' / 'TimeField'` | `FieldType.dateField / dateTimeField / timeField` | the date/time kinds |
| any other internal-type string | `FieldType.other` | irrelevant to the decision |
| `'DurationField' in {lhs_type, rhs_type}` | `isDurationField lhs = true ∨ isDurationField rhs = true` | post-patch membership test |
| `lhs_type in {'DateField','DateTimeField','TimeField'}` | `isDateTimeField lhs = true` | |
| `lhs_type != rhs_type` | `lhs ≠ rhs` | post-patch's NEW guard (the fix) |
| `lhs_type == rhs_type` | `lhs = rhs` | date-subtraction same-type guard |
| selected strategy | `ExprStrategy` (3 ctors) | observed only as WHICH strategy, not its SQL text |

`get_internal_type()` returns a fixed string keyed solely on the field class; the
five-way `FieldType` enum is a faithful quotient (only the duration + three
date/time kinds steer the decision; all else collapses to `other`). No native
ordering or content of the string is consumed.

## Callee provenance + flag deps
- No unchanged callee is consumed as an axiom. `DurationExpression.as_sql`,
  `TemporalSubtraction.as_sql`, and the generic `combine_expression` path are
  observed only as the IDENTITY of the strategy chosen at this site — they are
  not invoked in the model and contribute no contract. (`axioms = []`,
  `deep_model_references = []`.)
- Flag dependency: the duration strategy is reachable only when
  `has_native_duration_field` is `False` (SQLite/MySQL); on backends with native
  support the first branch is never taken. Captured as `nativeDurationSupport`.

## G-CONF fuzz seed
Pinned seed: **13121** (also in conformance_check.py).
