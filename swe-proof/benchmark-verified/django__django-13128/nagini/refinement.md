# refinement.md — django__django-13128

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_kind` impl region and the deep `resolved_kind` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses a `@ContractOnly` axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The classification site — `CombinedExpression.resolve_expression` (`django/db/models/expressions.py:476`)

Gold hunk (the inserted dispatch, after resolving the two operands):
```
+ if not isinstance(self, (DurationExpression, TemporalSubtraction)):
+     try:    lhs_type = lhs.output_field.get_internal_type()
+     except (AttributeError, FieldError): lhs_type = None
+     try:    rhs_type = rhs.output_field.get_internal_type()
+     except (AttributeError, FieldError): rhs_type = None
+     if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
+         return DurationExpression(self.lhs, self.connector, self.rhs).resolve_expression(...)
+     datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
+     if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
+         return TemporalSubtraction(self.lhs, self.rhs).resolve_expression(...)
  c = self.copy(); c.is_summary = summarize; c.lhs = lhs; c.rhs = rhs; return c
```

| # | model.py impl op (`resolve_kind`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `is_already_temporal: bool` parameter | `isinstance(self, (DurationExpression, TemporalSubtraction))` | R | bool ↔ the isinstance test (mapping.md §2). |
| A2 | `t_lhs`, `t_rhs: int` type codes | `lhs_type`/`rhs_type` from `…output_field.get_internal_type()` (or `None` on `AttributeError`/`FieldError`) | R | internal-type string (or absent) ↔ `int` code; `None`/error ↔ `T_UNKNOWN` (mapping.md §2). The operand types are produced by already-modelled operand resolution, not an opaque callee. |
| A3 | `is_sub: bool` parameter | `self.connector == self.SUB` | R | bool ↔ the connector equality test. |
| A4 | guard `if not is_already_temporal:` | `if not isinstance(self, (DurationExpression, TemporalSubtraction)):` | I | identical control-flow guard under A1. |
| A5 | `if (t_lhs == T_DURATION or t_rhs == T_DURATION) and t_lhs != t_rhs: return K_DURATION` | `if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type: return DurationExpression(...).resolve_expression(...)` | A-reference (R-mapped) | the duration-dispatch branch, modeled deeply: `'DurationField' in {a,b}` ↔ `a==T_DURATION or b==T_DURATION` and the `!=` is identical. Producing a `DurationExpression` ↔ result kind `K_DURATION` (mapping.md §2). The deep model is validated == the real dispatch by G-AX (axiom_check.py). |
| A6 | `if is_sub and is_datetime_type(t_lhs) and t_lhs == t_rhs: return K_TEMPORAL` | `if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type: return TemporalSubtraction(...).resolve_expression(...)` | A-reference (R-mapped) | the temporal-subtraction branch: `lhs_type in {'DateField','DateTimeField','TimeField'}` ↔ `is_datetime_type(t_lhs)`; the SUB test and `==` are identical. Producing a `TemporalSubtraction` ↔ `K_TEMPORAL`. Validated == real dispatch by G-AX. |
| A7 | `return K_PLAIN` (fall-through and already-temporal) | `c = self.copy(); c.lhs = lhs; c.rhs = rhs; return c` (the plain branch; also the branch reached when the recursive `DurationExpression/TemporalSubtraction.resolve_expression` re-enters with the isinstance guard now true) | R | "no NEW wrapper created" ↔ `K_PLAIN` (mapping.md §2). The fields/copy bookkeeping (`is_summary`, `c.lhs`, `c.rhs`) is operand-resolution plumbing the classification does not observe. |

The discriminating content of the change — that a bare temporal subtraction is
classified at RESOLUTION time (so its output type is well-defined) rather than
being left plain until SQL emission — lives in branches A5/A6. The pre-patch
`resolve_expression` performed neither; `model_prepatch.py` reproduces that
(always `return K_PLAIN`) and **fails** the postconditions

  `(Result()==K_DURATION) == (not already ∧ wants_duration(...))` and
  `(Result()==K_TEMPORAL) == (not already ∧ ¬wants_duration ∧ wants_temporal(...))`,

which is exactly the spec sensing the change (G-DIFF). The F2P tests drop the
`ExpressionWrapper(..., output_field=DurationField())` precisely because the
patched resolution now supplies the temporal classification (and hence the
output type) that the wrapper used to supply by hand.

## B. The second hunk — `DurationExpression.as_sql` native-duration short-circuit

Gold hunk (`expressions.py:496`):
```
  def as_sql(self, compiler, connection):
+     if connection.features.has_native_duration_field:
+         return super().as_sql(compiler, connection)
      connection.ops.check_expression_support(self)
      ...
```

| # | model.py | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (not modeled) | `if connection.features.has_native_duration_field: return super().as_sql(...)` | I (SQL-emission, outside modeled function) | On a native-duration backend, a `DurationExpression` must emit the same SQL as a plain combined expression rather than the duration-arithmetic SQL. This is a backend SQL-string detail keyed on `connection.features`; it does not alter the resolve-time classification the modeled function captures, and on the test backend (SQLite, `has_native_duration_field = False`) the guard is false, so the path is unchanged. It ships verbatim in `patch.diff` (covered by G-RESOLVE). Not separately modeled because the F2P classification behaviour does not depend on it (mapping.md §3.2). |

Why no separate failing `model_prepatch` for hunk B: hunk B changes no
behaviour on the tested backend (the guard is false on SQLite/MySQL where the
temporal F2P tests run, `has_native_duration_field = False`), and emits SQL
strings — outside the modeled classification interface. The single
`model_prepatch.py` exercises the load-bearing, F2P-observable behaviour (the
resolve-time classification of hunk A).

## C. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R, I, or A-reference. The one operation that genuinely
*changed* — the resolve-time classification dispatch — is modeled **deeply**
(`resolved_kind`, the spelled-out branch logic over the operand type codes),
not hidden behind an axiom about the function under change: there is **no
consumed `@ContractOnly` axiom** in this bundle. The deep model is the
A-reference that G-AX validates against the real
`CombinedExpression.resolve_expression` dispatch (axiom_check.py). Hunk B (§B)
is an I step in SQL emission outside the modeled function.

## D. verify(model) ⇒ resolved

`resolve_kind` verifies only if its dispatch decision equals the exact branch
logic of `resolved_kind` (A5/A6/A7) — duration form iff a duration operand is
present with differing types, temporal-subtraction form iff a SUB of two equal
date/time operands, plain otherwise, and never re-classifying an
already-specialised expression. By R (type codes ↔ internal-type strings,
bool ↔ isinstance/connector tests, kind code ↔ result class) this is exactly the
classification the gold patch performs in `CombinedExpression.resolve_expression`;
by G-AX the deep model equals the real dispatch over the full enumeration
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement on the F2P-observable behaviour — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom/reference soundness (G-AX) and refinement fidelity (this
document, G-EQ).
