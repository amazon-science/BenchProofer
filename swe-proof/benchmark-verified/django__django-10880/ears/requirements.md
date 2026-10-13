# Requirements: Correct SQL rendering of the DISTINCT modifier in aggregate expressions

## Introduction

Django's ORM aggregate expressions (in `django.db.models.aggregates`, centered on
the `Aggregate` base class and its subclasses such as `Count`) can be constructed
with `distinct=True`. When such an aggregate is compiled to SQL, the base
`Aggregate.as_sql` method assembles the call text from a template of the shape
`FUNCTION(<distinct-modifier><argument-expression>)`, where the distinct-modifier
slot is filled with the `DISTINCT` keyword when the aggregate is distinct and left
empty otherwise.

The defect: the distinct-modifier slot was filled with the bare keyword
`DISTINCT` with no trailing separator. Because the modifier text is concatenated
directly in front of the argument expression, the emitted SQL glued the keyword to
the start of the argument text whenever that text did not itself begin with
whitespace. In particular, a `Count` annotation that combines `distinct=True` with
a conditional `Case`/`When` argument produced malformed SQL such as
`COUNT(DISTINCTCASE WHEN ...)` — the keyword and the following token were run
together — causing a database query syntax error on any backend.

The goal: ensure the distinct modifier is always kept lexically separate from the
argument expression it precedes, so that combining a distinct aggregate with any
argument (including a conditional expression) yields valid SQL, while leaving all
other aggregate rendering behavior unchanged.

## Requirement 1: DISTINCT modifier is separated from the argument expression

**User story:** As a developer building a distinct aggregate over an arbitrary
expression, I want the generated SQL to keep the `DISTINCT` keyword separate from
the argument, so that the query is syntactically valid regardless of how the
argument text begins.

**Acceptance criteria**

1. WHEN an aggregate expression is compiled to SQL and the aggregate was
   constructed as distinct, THEN the compiler SHALL emit the `DISTINCT` keyword
   followed by a single separating space immediately before the argument
   expression text within the aggregate call.
2. WHEN a distinct aggregate is compiled and its argument expression text begins
   with an alphabetic token (for example a conditional expression that renders as
   `CASE WHEN ...`), THEN the emitted call SHALL contain a whitespace boundary
   between the `DISTINCT` keyword and that token so that they are never
   concatenated into a single token (never `DISTINCTCASE`).
3. WHEN a distinct aggregate over a conditional argument is executed against a
   database backend, THEN the query SHALL execute without raising a SQL syntax
   error, and its computed result SHALL reflect the distinct count of the
   values selected by the conditional argument.
4. The system SHALL apply this separation uniformly for every aggregate function
   that supports the distinct modifier, independent of the database backend in use.

## Requirement 2: Non-distinct aggregates emit no distinct modifier text

**User story:** As a developer using an ordinary (non-distinct) aggregate, I want
the generated SQL to contain no distinct-related text or stray separator, so that
existing aggregate queries are byte-for-byte unaffected by the fix.

**Acceptance criteria**

1. WHEN an aggregate expression is compiled to SQL and the aggregate was not
   constructed as distinct, THEN the distinct-modifier slot SHALL be empty and the
   argument expression text SHALL immediately follow the opening parenthesis with
   no leading keyword and no leading separating space.
2. The system SHALL leave the rendered SQL of every non-distinct aggregate
   identical to its previous output, introducing neither the `DISTINCT` keyword nor
   any extra whitespace.

## Requirement 3: Preserve existing aggregate construction and rendering behavior

**User story:** As a maintainer, I want the fix to change only the spacing of the
distinct modifier, so that all other aggregate features and validation continue to
behave exactly as before.

**Acceptance criteria**

1. The system SHALL keep the overall structure of a rendered aggregate call as the
   function name, an opening parenthesis, the (possibly empty) distinct-modifier
   slot, the argument expression text, and a closing parenthesis, in that order,
   changing only whether the distinct modifier carries a trailing separator.
2. IF an aggregate that does not permit the distinct modifier is constructed with
   `distinct=True`, THEN the system SHALL raise a `TypeError` indicating the
   aggregate does not allow distinct, as before.
3. WHEN an aggregate that permits distinct is combined with a filter condition,
   THEN the system SHALL render its filter clause exactly as before, applying the
   corrected distinct spacing on backends that support aggregate filter clauses and
   preserving the conditional-expression fallback on backends that do not.
4. The system SHALL keep the results and SQL of all existing aggregate operations
   unchanged, including plain counts, star counts, distinct sums, filtered and
   conditional aggregations, value/annotation aggregations, ordering by
   aggregates, and the existing error raised when a non-distinct-capable aggregate
   receives the distinct flag.
