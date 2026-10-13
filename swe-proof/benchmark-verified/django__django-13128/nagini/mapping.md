# mapping.md — django__django-13128

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2d67222472f80f251607ae1b720527afceba06ad`, states the type
abstraction, and documents the (single) deep-model reference and its provenance.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_kind(is_already_temporal, is_sub, t_lhs, t_rhs)` | `CombinedExpression.resolve_expression` — `django/db/models/expressions.py:476` | the modeled changed function: the resolve-time classification dispatch the patch adds |
| `resolved_kind(...)` *(deep model — A-reference)* | the dispatch branch the patch inserts into `CombinedExpression.resolve_expression` (`expressions.py:476-498` post-patch) | pure spec: which specialised expression the resolution yields, as a function of the operand output types, the connector, and whether self is already specialised |
| `is_datetime_type(t)` | the membership test `lhs_type in {'DateField','DateTimeField','TimeField'}` (post-patch `expressions.py`) | pure spec: a type code denotes a date/time field |
| `wants_duration(t_lhs, t_rhs)` | `'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type` (post-patch) | pure spec: the duration-dispatch branch condition |
| `wants_temporal(is_sub, t_lhs, t_rhs)` | `self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type` (post-patch) | pure spec: the temporal-subtraction-dispatch branch condition |

The repo classes the dispatch produces: `DurationExpression`
(`expressions.py:484`) and `TemporalSubtraction` (`expressions.py:512`,
`output_field = DurationField()`), each a `CombinedExpression` subclass.

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the temporal/duration dispatch lived
only in `CombinedExpression.as_sql` (`expressions.py:445-462`); the pre-patch
`resolve_expression` (`expressions.py:476-481`) resolved the two operands and
returned the plain combined expression with no classification — so a bare,
unwrapped temporal subtraction was never specialised at resolution time and its
output type could not be inferred (mixed `DateTimeField`/`DurationField` ⇒
`FieldError: Expression contains mixed types`, per the problem statement).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an operand's resolved output-field type, read via `operand.output_field.get_internal_type()` (or `None`/raise when no output type) | an `int` type code in `{T_UNKNOWN..T_OTHER}` | `'DateField'`↔`T_DATE(1)`, `'DateTimeField'`↔`T_DATETIME(2)`, `'TimeField'`↔`T_TIME(3)`, `'DurationField'`↔`T_DURATION(4)`, any other concrete internal type ↔ `T_OTHER(5)`, and a `None`/`FieldError`/`AttributeError` output type ↔ `T_UNKNOWN(0)`. The dispatch reads the type ONLY through equality with these named strings and the `datetime_fields` set membership, so the finite enumeration is observationally complete for the branch logic. |
| the connector `self.connector` vs `self.SUB` | `is_sub: bool` | `is_sub == (self.connector == self.SUB)`. The dispatch consults the connector only via the `== self.SUB` test. |
| `isinstance(self, (DurationExpression, TemporalSubtraction))` | `is_already_temporal: bool` | True iff self is already one of the two specialised forms. |
| the class of the resolution result (which wrapper, if any, is newly created) | an `int` kind code: `K_PLAIN(0)` / `K_DURATION(1)` / `K_TEMPORAL(2)` | `K_DURATION`↔a newly created `DurationExpression`, `K_TEMPORAL`↔a newly created `TemporalSubtraction`, `K_PLAIN`↔`self.copy()` with no new wrapper (incl. the already-specialised case, where the `isinstance` guard skips the dispatch). |

`None`/`FieldError`-typed operands collapse to `T_UNKNOWN`, which matches no
concrete type, so `wants_duration`/`wants_temporal` are both false for them —
exactly as the real `except (AttributeError, FieldError): … = None` branch makes
`'DurationField' in {None, …}` / `None in datetime_fields` false.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolved_kind` deep model ↔ `CombinedExpression.resolve_expression` dispatch
There is **no consumed `@ContractOnly` axiom**. The changed operation — the
resolve-time classification — is modeled **deeply** by the `@Pure` dispatch
`resolved_kind` (with `wants_duration`, `wants_temporal`, `is_datetime_type`),
which reproduces, branch-for-branch, the conditional the patch inserts:

```python
if not isinstance(self, (DurationExpression, TemporalSubtraction)):
    ... lhs_type, rhs_type from resolved operand output fields (None on error) ...
    if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
        return DurationExpression(...).resolve_expression(...)
    datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
    if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
        return TemporalSubtraction(...).resolve_expression(...)
# else: plain copy
```

The operand output types `resolved_kind` inspects are produced by the
already-modelled resolution of the sub-expressions (`lhs.output_field.get_internal_type()`
on the resolved operand), not by an opaque external callee — so this is a deep
model of the changed branch, not an axiom over an unchanged callee.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL Django
`CombinedExpression.resolve_expression` **post-patch (gold-applied)** — the
inserted classification branch is the A-reference, so the check self-applies the
gold patch to `/testbed` (idempotently) before importing Django (Value-based
operands of each modelled field type; the `T_UNKNOWN` case is a `Value` with no
`output_field`, whose `.output_field` raises `FieldError`) over the **full**
enumeration `{already_temporal} × {is_sub} × {6 type codes} × {6 type codes}`
(2 × 2 × 6 × 6 = 144 cases) and asserts the dispatch decision (which wrapper is
newly created) equals `resolved_kind`. It additionally pins the two F2P-relevant witnesses: a
bare `DateTimeField − DateTimeField` resolves to a `TemporalSubtraction` whose
`output_field` is a `DurationField` (no mixed-types `FieldError`), and a
`DateTimeField − DurationField` resolves to a `DurationExpression`. No database
access; imports only `django` (the system under test) + stdlib. Exit 0 iff
sound.

### 3.2 The second gold hunk — `DurationExpression.as_sql` native-duration short-circuit
The gold patch also adds, to `DurationExpression.as_sql` (`expressions.py:496`):
`if connection.features.has_native_duration_field: return super().as_sql(...)`.
This is a backend-SQL-emission detail (on a native-duration backend a
`DurationExpression` emits the same SQL as a plain combined expression). It is
**not** part of the resolve-time classification the F2P tests exercise on the
test backend (SQLite, `has_native_duration_field = False`), is not observable
through the modeled classification interface, and changes no behaviour on the
tested backend. It ships verbatim in `patch.diff` (so G-RESOLVE covers it) and
is documented in refinement.md §B as an I/R step outside the modeled function;
it is intentionally not separately modeled (modeling it would require a backend
`connection.features` object and SQL-string emission, neither of which the F2P
classification behaviour depends on).
