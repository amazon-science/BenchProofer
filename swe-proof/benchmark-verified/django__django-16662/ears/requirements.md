# Requirements: Import statement ordering in generated migration files

## Introduction

When Django generates a migration file, the module begins with a block of
import statements assembled by `MigrationWriter.as_string` in
`django/db/migrations/writer.py`. Each statement is either a plain module
import (`import <module>`) or a selective import (`from <module> import
<objects>`). Today the writer orders this block purely by the module name,
interleaving the two statement kinds. This violates the Django coding style —
which requires all plain `import module` statements to appear before all
`from module import objects` statements within a section — and it conflicts
with the default behavior of the isort tool, so freshly generated migrations
can fail an isort check.

The goal is to make the writer emit the import block grouped by statement kind
(plain imports first, then `from ... import ...` statements) while preserving
the existing alphabetical ordering by module name within each group, without
changing any other part of the generated migration or adding/dropping any
import. The behavioral change is confined to how the collected import lines are
ordered before they are joined into the `imports` section of the migration
template.

## Requirement 1: Group plain imports before `from ... import ...` imports

**User story:** As a developer running isort or following the Django coding
style on generated migrations, I want the migration writer to place every
plain `import module` statement before every `from module import objects`
statement, so that generated migrations pass isort and match the documented
import conventions.

**Acceptance criteria**

1. WHEN the migration writer renders the import block for a generated migration
   and the collected imports contain at least one plain module-import statement
   and at least one selective (`from ... import ...`) statement, THEN the writer
   SHALL emit every plain module-import statement before any selective import
   statement in the rendered block.
2. The system SHALL treat a statement whose leading whitespace-delimited token
   is `from` as a selective import, and any other statement as a plain module
   import.
3. WHEN the collected imports contain only plain module-import statements, THEN
   the writer SHALL emit them with no reordering relative to the kind grouping
   (grouping introduces no change for a single-kind block).
4. WHEN the collected imports contain only selective import statements, THEN the
   writer SHALL emit them with no reordering relative to the kind grouping.

## Requirement 2: Alphabetical ordering by module within each group

**User story:** As a developer reviewing a generated migration, I want the
imports within each group ordered by the module being imported, so that the
import block is stable and readable exactly as before, aside from the new
grouping.

**Acceptance criteria**

1. WHEN the writer emits the plain module-import statements, THEN it SHALL order
   them by the module token — the whitespace-delimited token immediately
   following the leading keyword — in non-decreasing (ascending) order.
2. WHEN the writer emits the selective import statements, THEN it SHALL order
   them by the module token — the whitespace-delimited token immediately
   following the leading keyword — in non-decreasing (ascending) order.
3. The system SHALL determine each statement's ordering module name from the
   token after `import` in `import <module>` and from the token after `from` in
   `from <module> import ...`.
4. WHEN two statements share the same statement kind and the same module token,
   THEN the writer SHALL emit them adjacently within their group.

## Requirement 3: Preserve the exact set of import statements

**User story:** As a maintainer, I want the reordering to be a pure
rearrangement, so that no import is added, removed, duplicated, or textually
altered by the new ordering logic.

**Acceptance criteria**

1. The system SHALL emit exactly the same collection of import statement lines
   that it collected, differing only in their order.
2. The system SHALL NOT add, drop, duplicate, or textually modify any import
   statement as a result of the ordering step.

## Requirement 4: Preserve existing import-assembly behavior

**User story:** As a maintainer, I want all pre-existing behavior of the import
block assembly to remain intact, so that this change fixes only the ordering
and regresses nothing else.

**Acceptance criteria**

1. The system SHALL continue to include the `from django.db import migrations`
   dependency in every generated migration's import block.
2. WHEN a `from django.db import models` import is present, THEN the writer
   SHALL merge it with the migrations import and emit the single combined
   statement `from django.db import migrations, models`.
3. WHEN no model import is needed, THEN the writer SHALL NOT emit any
   `models` import in the generated migration.
4. WHEN an import refers to an object defined in another migration file, THEN
   the writer SHALL remove that import from the emitted block and instead
   append the existing manual-porting comment listing those modules, keeping
   that behavior unchanged.
5. The system SHALL keep the rest of the generated migration file — header,
   dependencies, operations, and all serialization of values — unchanged by
   this ordering change.
6. WHEN the migration has no imports beyond the always-present ones, THEN the
   writer SHALL still produce a valid, importable migration file.
