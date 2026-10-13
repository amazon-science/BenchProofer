# mapping.md — django__django-13121

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ec5aa2161d8015a3fe57dcbbfe14200cd18f0a16`, states the type
abstraction, and gives the provenance of each modelled decision.

Repo file under change: `django/db/models/expressions.py` (plus the trivial
removal of the now-unused `date_interval_sql` overrides in
`django/db/backends/{base,mysql,sqlite3}/operations.py`, which carry no
verifiable behaviour — see refinement.md §C).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_arithmetic_path(lhs_kind, rhs_kind, is_subtract, native_duration)` | the rendering-class dispatch inside `CombinedExpression.as_sql` — `django/db/models/expressions.py:443-459` | modeled changed function #1: chooses which expression class renders an arithmetic combination |
| `operand_format_flag(operand_kind, is_literal)` | the per-operand decision inside `DurationExpression.compile` — `django/db/models/expressions.py:482-492` | modeled changed function #2: whether the duration-format wrapper is applied to one operand |
| `KIND_NONE / KIND_DURATION / KIND_DATE / KIND_DATETIME / KIND_TIME / KIND_OTHER` | the string results of `output_field.get_internal_type()` (and `None` on `FieldError`) | int refinement of the finite result-kind name set |
| `PATH_DURATION / PATH_TEMPORAL / PATH_PLAIN` | the three rendering classes: `DurationExpression`, `TemporalSubtraction`, and the plain `CombinedExpression` body | int refinement of the dispatch target |
| `is_temporal_kind(k)` | the literal set `{'DateField', 'DateTimeField', 'TimeField'}` (`expressions.py:457` pre, `:461` post) | the temporal-subtraction family |

Pre-patch repo symbols the change removes (for the refinement audit, not
referenced from the consumer spec view): the `DurationValue` subclass
(`expressions.py:712-717`) and the special-casing of a `timedelta` literal into
it inside `Combinable._combine` (`expressions.py:59-62`); plus the now-dead
`date_interval_sql` overrides.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `output_field.get_internal_type()` → one of `'DurationField' / 'DateField' / 'DateTimeField' / 'TimeField' / <other>`, or `None` when `output_field` raises `FieldError` | `int` code (`KIND_*`) | name ↔ code per the table above; `None` ↔ `KIND_NONE`. Only operations used are `==`, `!=`, and membership in the temporal set — all of which are equality/finite-set tests preserved exactly by the int coding. |
| the chosen rendering class (`DurationExpression` / `TemporalSubtraction` / plain `CombinedExpression`) | `int` code (`PATH_*`) | one code per dispatch target; the only observable is which branch is taken. |
| `self.connector == self.SUB` | `is_subtract: bool` | identical boolean. |
| `connection.features.has_native_duration_field` | `native_duration: bool` | identical boolean. |
| "the operand is a literal value vs a stored column reference" — pre-patch the literal `timedelta` operand was a `DurationValue` instance, the special case the format decision keyed on | `is_literal: bool` | the boolean the pre-patch code branched on (`isinstance(side, DurationValue)`); post-patch the format decision is independent of it, which the spec pins (the flag does not appear in `operand_format_flag`'s postcondition value). |

`output_field.get_internal_type()` returns from a closed finite set of class
names; modelling it as a small int enum is a faithful refinement because the
dispatch reads it only through equality and finite-set membership.

## 3. Callee provenance / decision provenance (checked by G-AX / axiom_check.py)

This bundle consumes **no `@ContractOnly` axioms** — both changed decisions are
modelled deeply over the integer abstraction. The two **A-reference** decisions
validated by `axiom_check.py` (G-AX) against the real post-patch Django source:

### 3.1 `select_arithmetic_path` ↔ `CombinedExpression.as_sql` dispatch (A-reference)
Post-patch source (`expressions.py:443-459`):
```python
def as_sql(self, compiler, connection):
    try:
        lhs_type = self.lhs.output_field.get_internal_type()
    except FieldError:
        lhs_type = None
    try:
        rhs_type = self.rhs.output_field.get_internal_type()
    except FieldError:
        rhs_type = None
    if (
        not connection.features.has_native_duration_field and
        'DurationField' in {lhs_type, rhs_type} and
        lhs_type != rhs_type
    ):
        return DurationExpression(self.lhs, self.connector, self.rhs).as_sql(...)
    datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
    if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
        return TemporalSubtraction(self.lhs, self.rhs).as_sql(...)
    ...  # plain combination
```
The model encodes exactly these three guards. The discriminating change vs.
pre-patch: the duration guard gained `and lhs_type != rhs_type`, so a
duration+duration pairing now falls through to the plain branch instead of the
duration-arithmetic subclass (`model_prepatch.py` reverts this and fails).
G-AX asserts `select_arithmetic_path == oracle` over every `(lhs_kind,
rhs_kind, is_subtract, native_duration)` combination, where the oracle is this
source transcribed verbatim, plus an end-to-end SQLite evaluation of the
durations-only F2P scenario.

### 3.2 `operand_format_flag` ↔ `DurationExpression.compile` (A-reference)
Post-patch source (`expressions.py:482-492`):
```python
def compile(self, side, compiler, connection):
    try:
        output = side.output_field
    except FieldError:
        pass
    else:
        if output.get_internal_type() == 'DurationField':
            sql, params = compiler.compile(side)
            return connection.ops.format_for_duration_arithmetic(sql), params
    return compiler.compile(side)
```
Post-patch, the format wrapper is applied iff the operand's result kind is a
duration — with **no** `isinstance(side, DurationValue)` exemption (that guard
and the `DurationValue` class are removed). The model returns `1` iff
`operand_kind == KIND_DURATION`, regardless of `is_literal`
(`model_prepatch_2.py` reverts to the literal-exempting behaviour and fails).
G-AX asserts `operand_format_flag == oracle` over every `(operand_kind,
is_literal)` and confirms a literal duration operand is formatted.

**Soundness check (G-AX):** `axiom_check.py` (a) exhaustively compares both
model functions to a verbatim transcription of the patched source over all
finite input combinations plus 20 000 randomized fuzz draws, and (b)
in-container drives the REAL post-patch `CombinedExpression`/`DurationExpression`
on the durations-only F2P scenario on the SQLite backend, asserting it
round-trips `estimated_time + timedelta` and that the duration+duration pairing
is not routed through the duration-arithmetic subclass. It imports only
`django` (the repo under test) and the standard library. Exit 0 iff sound.
