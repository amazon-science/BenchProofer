# Requirements: Resolve output field for the modulo operator on mixed numeric types

## Introduction

Django's ORM lets users build arithmetic query expressions by combining two
sub-expressions with an operator (for example an `F()` expression plus a
`Value`). When such a `CombinedExpression` is used in a query, Django must infer
the Django model field type of the result — its `output_field` — so it knows how
to convert the database value back into a Python object.

The type inference lives in `django/db/models/expressions.py`: the class
`CombinedExpression` exposes an `output_field` (resolved via the module-level
helper `_resolve_combined_type`, which consults a registry of
`(left field type, right field type) -> result field type` combinations keyed by
operator). The operators are the constants on the `Combinable` class:
`ADD` (`+`), `SUB` (`-`), `MUL` (`*`), `DIV` (`/`), `MOD` (`%`), `POW` (`**`),
plus the bitwise operators.

For the standard arithmetic operators, the registry already covers **mixed**
numeric operand types: combining an integer-typed operand with a decimal-typed
operand promotes the result to the decimal type, integer with float promotes to
float, and so on. The modulo (remainder, `%`) operator was omitted from the
mixed-type registry, so an expression such as a `DecimalField` value modulo an
`IntegerField` value failed to resolve its result to a `DecimalField` the way
addition, subtraction, multiplication, and division do.

The goal is to make the modulo operator resolve the combined `output_field` for
mixed numeric operand types consistently with the other arithmetic operators,
without changing the behavior of any other operator or of the null / same-type
cases.

## Requirement 1: Modulo of mixed numeric types resolves to the wider numeric type

**User story:** As a developer building ORM query expressions, I want a modulo
expression whose operands have different numeric field types to resolve its
result field type the same way the other arithmetic operators do, so that the
computed value is converted back to the correct Python type.

**Acceptance criteria**

1. WHEN a `CombinedExpression` combines a left operand whose resolved field type
   is `IntegerField` with a right operand whose resolved field type is
   `DecimalField` using the modulo (`%`) operator, THEN accessing its
   `output_field` SHALL yield a `DecimalField` instance.
2. WHEN a `CombinedExpression` combines a `DecimalField`-typed left operand with
   an `IntegerField`-typed right operand using the modulo (`%`) operator, THEN
   accessing its `output_field` SHALL yield a `DecimalField` instance.
3. WHEN a `CombinedExpression` combines an `IntegerField`-typed left operand with
   a `FloatField`-typed right operand using the modulo (`%`) operator, THEN
   accessing its `output_field` SHALL yield a `FloatField` instance.
4. WHEN a `CombinedExpression` combines a `FloatField`-typed left operand with an
   `IntegerField`-typed right operand using the modulo (`%`) operator, THEN
   accessing its `output_field` SHALL yield a `FloatField` instance.
5. WHEN a `CombinedExpression` combines an `IntegerField`-typed operand with an
   auto-increment integer (`AutoField`) operand in either order using the modulo
   (`%`) operator, THEN accessing its `output_field` SHALL yield an
   `IntegerField` instance.
6. The system SHALL resolve the modulo operator's mixed-numeric-type result field
   using the same left/right-to-result promotions already applied to the
   addition, subtraction, multiplication, and division operators.

## Requirement 2: Existing arithmetic operators keep resolving mixed numeric types

**User story:** As a developer relying on existing arithmetic expressions, I want
the type resolution for the other operators to remain unchanged, so that adding
support for modulo does not regress current behavior.

**Acceptance criteria**

1. WHEN a `CombinedExpression` combines two operands of differing numeric field
   types (integer with decimal, decimal with integer, integer with float, float
   with integer, or integer with auto-increment integer in either order) using
   the addition (`+`), subtraction (`-`), multiplication (`*`), or division
   (`/`) operator, THEN accessing its `output_field` SHALL yield the wider
   numeric field type (decimal when a decimal operand is present, otherwise float
   when a float operand is present, otherwise integer).
2. WHEN a `CombinedExpression` combines two operands of the **same** numeric
   field type using any arithmetic operator that already supported that same-type
   combination, THEN accessing its `output_field` SHALL yield that same numeric
   field type.

## Requirement 3: Unresolvable numeric-with-null combinations still raise an error

**User story:** As a developer, I want combinations whose result type cannot be
inferred to fail loudly rather than silently guess, so that ambiguous
expressions are surfaced instead of producing wrong conversions.

**Acceptance criteria**

1. IF a `CombinedExpression` combines a numeric-typed operand with a null-typed
   operand (a `Value(None)`) in a way that has no registered result type — for
   example an auto-increment integer operand added to a null operand, or a
   null operand combined with a numeric operand where no combination is
   registered — THEN accessing its `output_field` SHALL raise a `FieldError`
   whose message states that the type of the expression involving those types
   cannot be inferred.
2. The system SHALL NOT introduce a resolved result type for any numeric-with-null
   combination that previously raised `FieldError`; such combinations SHALL
   continue to raise `FieldError`.
3. The system SHALL continue to raise `FieldError` (rather than returning a
   result field type) for any operator/operand-type combination that is not
   present in the type-inference registry.
