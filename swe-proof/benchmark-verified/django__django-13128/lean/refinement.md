# refinement.md — django__django-13128

Maps every operation in `implementation_resolveKind` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `resolveKind` (`CombinedExpression.resolve_expression`)

Post-patch repo code (`patch.diff` applied), classification core:
```python
def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
    lhs = self.lhs.resolve_expression(query, allow_joins, reuse, summarize, for_save)
    rhs = self.rhs.resolve_expression(query, allow_joins, reuse, summarize, for_save)
    if not isinstance(self, (DurationExpression, TemporalSubtraction)):
        try:
            lhs_type = lhs.output_field.get_internal_type()
        except (AttributeError, FieldError):
            lhs_type = None
        try:
            rhs_type = rhs.output_field.get_internal_type()
        except (AttributeError, FieldError):
            rhs_type = None
        if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
            return DurationExpression(self.lhs, self.connector, self.rhs).resolve_expression(...)
        datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
        if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
            return TemporalSubtraction(self.lhs, self.rhs).resolve_expression(...)
    c = self.copy()
    c.is_summary = summarize
    c.lhs = lhs
    c.rhs = rhs
    return c
```

Lean impl (`implementation_resolveKind`):
```lean
def implementation_resolveKind (selfKind : ExprKind) (connector : Connector)
    (lhsType rhsType : Option FieldType) : ExprKind := Id.run do
  if selfKind ≠ ExprKind.combined then
    return selfKind
  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)
        ∧ lhsType ≠ rhsType then
    return ExprKind.duration
  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then
    return ExprKind.temporal
  return ExprKind.combined
```

The modeled OUTPUT is the resolved combination's KIND — i.e. which class the
resolved expression becomes (`CombinedExpression` / `DurationExpression` /
`TemporalSubtraction`). That kind is the entire observable effect of the fix: it
fixes the combination's output field and therefore whether a temporal arithmetic
expression is usable without an explicit `ExpressionWrapper(output_field=...)`.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `lhsType rhsType : Option FieldType` (inputs) | `lhs = self.lhs.resolve_expression(...)` then `lhs_type = lhs.output_field.get_internal_type()` (in `try/except (AttributeError, FieldError)`) | **R** | the resolved operands' value-types are the classification inputs. `get_internal_type()` is an UNCHANGED callee whose result is observed (not axiomatized); `(AttributeError, FieldError)` → `None` ↔ `none`. The five recognised type strings ↔ the five `FieldType` constructors (mapping.md). |
| 2 | `if selfKind ≠ ExprKind.combined then return selfKind` | `if not isinstance(self, (DurationExpression, TemporalSubtraction)): <classify> ... else: <fall through to plain copy>` | **R** | the reclassification guard. An expression already in a specialized kind is NOT reclassified — modeled by gating on `selfKind = combined` and returning `selfKind` unchanged otherwise. This is also the recursion guard: the recursive `.resolve_expression()` on the freshly-built `DurationExpression`/`TemporalSubtraction` re-enters with `self` of that class, so it returns a plain copy of that class — i.e. the same `duration`/`temporal` kind, exactly what `return selfKind` yields. |
| 3 | `if (lhsType = some duration ∨ rhsType = some duration) ∧ lhsType ≠ rhsType then return ExprKind.duration` | `if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type: return DurationExpression(...).resolve_expression(...)` | **I** (deep model of the changed op) | **the fixed operation (case A).** Set membership over a ≤2-element set ↔ the disjunction `lhsType = some duration ∨ rhsType = some duration`; `lhs_type != rhs_type` ↔ `lhsType ≠ rhsType`. The resolved expression becomes a duration combination ↔ result `ExprKind.duration`. |
| 4 | `if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then return ExprKind.temporal` | `if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type: return TemporalSubtraction(...).resolve_expression(...)` | **I** (deep model of the changed op) | **the fixed operation (case B).** `self.connector == self.SUB` ↔ `connector = Connector.sub`; `lhs_type in {'DateField','DateTimeField','TimeField'}` ↔ `isDateTimeField lhsType`; `lhs_type == rhs_type` ↔ `lhsType = rhsType`. The resolved expression becomes a temporal-subtraction combination (whose `output_field = DurationField()`) ↔ result `ExprKind.temporal`. |
| 5 | `return ExprKind.combined` | `c = self.copy(); c.is_summary = summarize; c.lhs = lhs; c.rhs = rhs; return c` | **R** | the default branch: an ordinary combination that matches neither temporal case stays an ordinary combination (same class). The copy, `is_summary`, and reassigned operands are unchanged-behavior bookkeeping orthogonal to the modeled kind (mapping.md); the observable kind is `combined`. |
| — | (abstracted) | hunk 1: removal of the same type-dispatch from `CombinedExpression.as_sql`; hunk 3: `DurationExpression.as_sql` native-duration short-circuit (`if connection.features.has_native_duration_field: return super().as_sql(...)`) | **A-reference (abstracted)** | downstream SQL-compilation consequences of relocating the dispatch from compile-time to resolve-time. They do NOT change the resolved-expression kind the FAIL_TO_PASS tests observe; abstracted out of the modeled observable (mapping.md). Not consumed by the proof ⇒ no dead axiom shipped. |

All impl-region ops are **R/I** — there is NO A-consumed (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched classification dispatch.

## Soundness check (verify ⟹ correct)

- `problem_spec_resolveKind selfKind connector lhsType rhsType result := result =
  classifyKind selfKind connector lhsType rhsType` pins the verdict EXACTLY (full
  `ExprKind` equality to an input-grounded total function) — directive 5 (frame):
  the resolved kind is fully determined by `selfKind`, `connector`, `lhsType`,
  `rhsType`. No output component is left unconstrained; no ungrounded oracle
  (directive 8) — `classifyKind` is a transparent total function of the inputs, so
  the postcondition is dischargeable only by performing the actual classification.
- The prepatch impl (`return selfKind` — resolution always copies the same class,
  never reclassifying) is the real bug: it never inspects the operand types or
  operator, so an ordinary combination of two temporal operands stays an ordinary
  combination with no determinate output type. It violates the spec on the
  discriminating clause `selfKind = combined, connector = sub, lhsType = rhsType =
  some datetime`, where it returns `combined` but the spec requires `temporal`. Its
  carried gold proof cannot close (G-DIFF/G-PANEL confirmed: the prepatch fails to
  verify).
- This discriminating case is precisely what the FAIL_TO_PASS tests exercise:
  `test_date_subtraction`, `test_time_subtraction`, `test_datetime_subtraction_microseconds`
  and the `*_subquery_subtraction` / `test_date_case_subtraction` tests all
  annotate with a bare `F('a') - F('b')` (NO `ExpressionWrapper(output_field=
  DurationField())` wrapper, which the test_patch removes). For the query to
  produce the right values, the resolved combination must acquire the temporal /
  duration kind on its own — exactly what the post-fix classification yields and
  the pre-fix code does not.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  classification dispatch over ALL 216 inputs of the finite modeled space plus
  ≥1e5 fuzzed inputs.
