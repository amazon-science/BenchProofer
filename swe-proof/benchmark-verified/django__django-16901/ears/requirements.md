# Requirements: Correct n-ary XOR fallback semantics for databases without native XOR

## Introduction

Django's ORM lets query predicates be combined with the exclusive-or operator
(`Q(...) ^ Q(...) ^ ...`). On database backends that natively support a logical
XOR (e.g. MySQL), the combination is delegated to the backend. On backends that
do **not** support logical XOR (e.g. PostgreSQL, SQLite, Oracle), Django emits
fallback SQL that must reproduce the same truth value.

The affected code is `WhereNode.as_sql` in
`django/db/models/sql/where.py`, specifically the branch taken when the node's
connector is exclusive-or and the connection reports no native logical-XOR
support. That branch rewrites the XOR of its operands into an equivalent
combination of an OR of the operands and an arithmetic test on how many operands
are true.

The correct meaning of an n-ary exclusive-or — and the meaning implemented by
backends that support it natively — is a **parity** test: the combination is
true exactly when an **odd number** of its operands are true. The existing
fallback instead tested for **exactly one** true operand, which is only correct
for two operands. For three or more operands the fallback produced wrong
results (e.g. three identical true operands returned no rows instead of
matching). The goal is to make the fallback compute the odd-parity semantics for
any number of operands while leaving all other behavior unchanged.

## Requirement 1: Odd-parity semantics for exclusive-or fallback with more than two operands

**User story:** As a developer running queries on a database without native XOR
support, I want `Q(...) ^ Q(...) ^ ...` over three or more predicates to match
rows for which an odd number of the predicates hold, so that my results agree
with the mathematical meaning of exclusive-or and with backends that support XOR
natively.

**Acceptance criteria**

1. WHEN a WHERE clause combines more than two operands with the exclusive-or
   connector AND the database connection does not support native logical XOR,
   THEN the query SHALL match a row if and only if an odd number of those
   operands evaluate to true for that row.
2. WHEN the exclusive-or fallback is applied to more than two operands, THEN the
   system SHALL compute the number of operands that are true, reduce that count
   modulo two, and treat the combination as true exactly when the reduced value
   equals one.
3. WHEN an odd number (one, three, five, ...) of the combined operands are true
   for a row, THEN the query SHALL include that row in the result set.
4. WHEN an even number (zero, two, four, ...) of the combined operands are true
   for a row, THEN the query SHALL exclude that row from the result set.
5. WHEN the same true predicate is exclusive-or-combined an odd number of times
   (three, five, ...) against a matching row, THEN the query SHALL match that
   row; WHEN it is combined an even number of times, THEN the query SHALL not
   match it.
6. WHEN operands whose truth regions overlap are exclusive-or-combined — so that
   a single row may satisfy several of the operands at once — THEN that row SHALL
   be selected exactly when the number of operands it satisfies is odd, matching
   the parity outcome rather than an exactly-one outcome.

## Requirement 2: Preserve exactly-one semantics for the two-operand case

**User story:** As a developer, I want `Q(a) ^ Q(b)` to keep behaving as before,
so that upgrading does not change results for the common two-operand case.

**Acceptance criteria**

1. WHEN a WHERE clause combines exactly two operands with the exclusive-or
   connector AND the database connection does not support native logical XOR,
   THEN the query SHALL match a row if and only if exactly one of the two
   operands evaluates to true for that row.
2. The system SHALL, for the two-operand fallback, compare the count of true
   operands directly against one without applying any modulo reduction.
3. WHEN exactly two operands are combined, THEN the odd-parity outcome and the
   exactly-one outcome coincide, and the query SHALL return the same rows it
   returned before this change.

## Requirement 3: Localize the fallback to backends lacking native XOR

**User story:** As a maintainer, I want the parity rewrite to apply only to the
non-native fallback path, so that backends with native XOR are unaffected.

**Acceptance criteria**

1. IF the database connection supports native logical XOR, THEN the system SHALL
   delegate the exclusive-or to the backend and SHALL NOT apply the OR-plus-count
   fallback rewrite.
2. The system SHALL apply the count-based fallback rewrite only WHEN the
   connector is exclusive-or AND the connection reports no native logical-XOR
   support.
3. The system SHALL preserve the existing structure of the fallback: the row
   must satisfy the OR of all operands AND satisfy the count/parity test on the
   number of true operands.

## Requirement 4: Preserve existing exclusive-or and query behaviors (regression protection)

**User story:** As a developer, I want all previously correct query behaviors to
keep working, so that this fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to select, for a two-operand exclusive-or filter,
   the rows matching one operand or the other but not both.
2. WHEN the operands of an exclusive-or combination are ordinary field lookups,
   negated predicates, primary-key predicates, or any mixture thereof, THEN the
   system SHALL determine each operand's truth value for a row and apply the same
   parity (for more than two operands) or exactly-one (for two operands) rule to
   those truth values, independent of the particular predicate form used.
3. WHEN an exclusive-or combination is used to exclude rows rather than to select
   them, THEN the resulting rows SHALL be exactly the complement of the rows the
   same combination would select.
4. The system SHALL produce query results that are unaffected by whether an
   exclusive-or condition is expressed all at once or built up incrementally, so
   long as the effective combined condition is the same.
5. The system SHALL leave the SQL generation for non-exclusive-or connectors
   (AND, OR) and for negated nodes unchanged.
