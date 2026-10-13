# Requirements: uniform column rendering for nested boolean filter trees

## Introduction

Django's ORM lowers a boolean filter expression (a `Q` object) into a
`WhereNode` tree of lookups whose left-hand (and sometimes right-hand) operands
are column references. A column reference can be produced in one of two forms:

- a **table-qualified column** (the ordinary form used when building queries,
  e.g. `Col`, rendered as `"table"."field"`), or
- a **bare/simple column** (`SimpleCol`, rendered as just `"field"`), which is
  the form required when the resulting SQL must not embed a table name — most
  notably the `CHECK` constraint expression emitted for a
  `models.CheckConstraint`.

The choice between these forms is a single boolean decision made once, at the
top of the lowering, in `django.db.models.sql.query.Query`. `build_where`
starts the lowering with the bare/simple form selected; the recursive worker
`_add_q` carries this decision downward, and `build_filter` /
`resolve_lookup_value` / the module-level `_get_col` helper consume it to pick
`SimpleCol` versus the table-qualified column for each leaf lookup.

The defect: `_add_q` applied the selected form only to leaf children it handled
directly, but when it recursed into a **nested** `Q` sub-node it failed to pass
the form flag along, so the recursive call reverted to the default
(table-qualified) form. A `Q` expression that mixes connectors — e.g. an `OR`
of an inner `AND` group with another term — therefore rendered its
deeply-nested leaves as table-qualified columns while its top-level leaves were
bare. For a `CheckConstraint` this produced SQL containing a fully qualified
name (`"table"."field"`) inside part of the check, which breaks SQLite/Oracle
table-rebuild migrations because the qualified table name does not exist in the
constraint's scope.

The goal: the column-form decision must be **global** — it must apply
uniformly to every leaf of the filter tree at every nesting depth, so that a
leaf buried inside several levels of grouping is rendered in exactly the same
form as a leaf at the top level.

## Requirement 1: Propagate the column-form choice into nested sub-expressions

**User story:** As a developer defining a `CheckConstraint` whose condition
combines `AND` and `OR` groups, I want every field reference in the generated
constraint SQL to use the same column form, so that the constraint is valid on
all backends and the migration does not fail.

**Acceptance criteria**

1. WHEN `_add_q` (in `django.db.models.sql.query.Query`) processes a child that
   is itself a nested `Q`/`Node` sub-expression, THEN it SHALL forward the
   currently-selected column-form choice (the `simple_col` flag) to the
   recursive lowering of that child.
2. WHEN a filter tree is lowered with the bare/simple column form selected,
   THEN the system SHALL render every leaf lookup's column reference as a
   `SimpleCol` (bare column) regardless of that leaf's nesting depth.
3. WHEN a filter tree is lowered with the bare/simple column form selected,
   THEN a leaf that sits inside one or more nested sub-expressions SHALL be
   rendered in exactly the same column form as a leaf that sits at the top
   level of the same lowering.
4. The system SHALL apply the column-form choice as a single global decision
   fixed at the start of the lowering, not one that silently changes between
   shallow and deeply-nested leaves.

## Requirement 2: Correct rendering of a mixed AND/OR condition

**User story:** As a developer, I want a condition that combines an inner
conjunctive (`AND`) group with a disjunctive (`OR`) term — the mixed shape that
triggered the defect — to lower correctly, so that its structure and every
column reference, on either side of every comparison, use the selected column
form.

**Acceptance criteria**

1. WHEN a condition combining an inner conjunctive group with a disjunctive
   term is lowered with the simple/bare column form, THEN each leaf comparison
   inside the inner conjunctive group SHALL be produced with its left-hand
   column operand rendered as a `SimpleCol`, whatever the particular lookup.
2. WHEN such a condition is lowered, THEN each top-level disjunctive term
   SHALL be produced with its left-hand column operand rendered as a
   `SimpleCol`.
3. WHEN any operand of a leaf comparison is itself a field reference (rather
   than a literal value) — whether it appears on the left-hand or the
   right-hand side — and the simple/bare column form is selected, THEN that
   operand SHALL also be rendered as a `SimpleCol`; the uniform column form
   applies to every column reference in the tree, on either side of a
   comparison, at any nesting depth.
4. The system SHALL preserve the grouping structure of the original filter
   tree: the connectors and the nesting of sub-expressions in the produced
   `WhereNode` SHALL mirror those of the input `Q` object.

## Requirement 3: Constraint enforcement is unaffected by the rendering fix

**User story:** As a developer, I want the check constraint's runtime meaning to
be exactly the boolean condition I wrote, so that only conforming rows are
accepted after the fix.

**Acceptance criteria**

1. WHEN a `CheckConstraint` whose condition is an `OR` of an inner `AND` group
   and another term is added to a table on a backend that supports table check
   constraints, THEN the resulting constraint SHALL reject (raise an integrity
   error for) any row that satisfies neither disjunct.
2. WHEN such a constraint is in force, THEN the system SHALL accept any row that
   satisfies at least one disjunct of the condition.
3. The system SHALL emit the check-constraint SQL using bare column names only,
   containing no table-qualified field reference inside the constraint
   expression.

## Requirement 4: Preserve existing lowering behavior (regression protection)

**User story:** As a maintainer, I want all previously-correct filter lowering
to keep working, so that the fix introduces no regression.

**Acceptance criteria**

1. The system SHALL keep producing the same lowering for a simple single-clause
   condition: a single comparison SHALL yield its lookup with the correct
   right-hand value and its left-hand column resolving to the intended model
   field.
2. The system SHALL keep producing the correct lowering for a top-level `OR` of
   two simple comparisons (no nested groups), unchanged by this fix.
3. The system SHALL keep the default (table-qualified) column form for ordinary
   query building when the bare/simple form is not selected.
4. The system SHALL keep lowering conditions that reference related-model
   fields (foreign keys), multiple fields, and negated nullable comparisons
   with their existing structure and column resolution.
5. WHEN a `CheckConstraint` is added, removed, or created together with a model,
   THEN the corresponding migration operations SHALL continue to behave as
   before for conditions that do not mix `AND`/`OR` groups (including partial
   unique constraints and percent-escaped checks).
