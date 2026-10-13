# Requirements: automodule must honor an empty export list

## Introduction

When the autodoc extension documents a whole module with the "document all
members" option enabled, it decides which of the module's discovered members to
include. That decision is governed by the module's export list (its `__all__`
attribute) in `sphinx/ext/autodoc/__init__.py`, specifically in the module
documenter's member-selection logic (`ModuleDocumenter.get_object_members`,
together with the export list captured during `import_object` and stored on the
documenter's `__all__` field).

The affected behavior distinguishes three situations:

* a module that declares **no** export list at all,
* a module that declares an export list that **names nothing** (an empty
  `__all__`), and
* a module that declares an export list that **names one or more** members.

The defect is that a present-but-empty export list is treated as if no export
list were declared, so every member is documented instead of none. Because an
empty export list and an absent export list are both falsy, they were
conflated. The goal is to treat an export list as authoritative whenever it is
present — including when it names nothing — so that an empty export list
suppresses all module members, while genuinely absent export lists and
populated export lists continue to behave as before.

## Requirement 1: Distinguish an absent export list from a present one

**User story:** As a documentation author, I want autodoc to treat the presence
of an export list as meaningful, so that declaring an export list — even one
that names nothing — actually controls which members are documented.

**Acceptance criteria**

1. The system SHALL treat a module's export list as *absent* only when the
   module declares no such attribute (the documenter's captured export list is
   the unset/None value), and as *present* whenever the module declares the
   attribute, regardless of how many names it contains.
2. WHEN the module member-selection logic decides whether to fall back to
   documenting every discovered member, THEN it SHALL base that decision on
   whether the export list is absent, and SHALL NOT base it on whether the
   export list is empty.
3. IF a module declares an export list that names nothing, THEN the
   member-selection logic SHALL classify it as present (not as absent).

## Requirement 2: An empty export list documents no members

**User story:** As a documentation author who sets an empty export list, I want
no members shown, so that an intentionally empty public surface is respected.

**Acceptance criteria**

1. WHEN a module whose export list is present but names nothing is documented
   with the document-all-members option enabled, THEN the module documenter
   SHALL produce output that contains no documented member entries.
2. WHEN such a module is documented, THEN the produced output SHALL still
   contain the module's own directive header and the module's own docstring.
3. WHEN member selection runs for such a module, THEN every discovered member
   SHALL be marked as skipped so that none of them is emitted, and the
   selection SHALL report that the implicit origin-based check is not to be
   applied.

## Requirement 3: Preserve behavior when no export list is declared

**User story:** As a documentation author of a module without an export list, I
want all members considered as before, so that existing modules keep
documenting their members.

**Acceptance criteria**

1. WHEN a module that declares no export list is documented with the
   document-all-members option enabled, THEN the member-selection logic SHALL
   keep every discovered member (none marked skipped on account of an export
   list) and SHALL report that the implicit origin-based check is still to be
   applied.
2. The system SHALL keep documenting the members of a module that declares no
   export list exactly as it did before, showing each such member's entry.

## Requirement 4: Preserve behavior when the export list names members

**User story:** As a documentation author who lists specific names in the
export list, I want exactly those members documented, so that a curated public
surface is respected.

**Acceptance criteria**

1. WHEN a module whose export list names one or more members is documented with
   the document-all-members option enabled, THEN the member-selection logic
   SHALL keep each discovered member in the result while marking as skipped
   every discovered member whose name is not among the export list's names.
2. WHEN such a module is documented, THEN the resulting documentation SHALL
   include entries only for those discovered members whose names appear in the
   export list.
3. WHEN such a module is documented, THEN the member-selection logic SHALL
   report that the implicit origin-based check is not to be applied.

## Requirement 5: Preserve behavior when members are requested by name

**User story:** As a documentation author who requests specific members by
name, I want just those members documented, so that explicit selections keep
working.

**Acceptance criteria**

1. WHEN members are requested by name (the document-all-members option is not
   in effect), THEN the member-selection logic SHALL return exactly the
   requested names that are present as discovered members, in the order
   requested, and SHALL report that the implicit origin-based check is not to
   be applied.
2. IF a requested name is not present as a discovered member, THEN that name
   SHALL be omitted from the returned members (and SHALL NOT cause a present
   member to be dropped).
