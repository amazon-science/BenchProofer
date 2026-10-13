# Requirements: `:meta public:` / `:meta private:` on module-level variables

## Introduction

The API-documentation extension `sphinx.ext.autodoc` lets an author override the
default visibility of a member by writing a `:meta public:` or `:meta private:`
field in that member's documentation comment. For functions and class members
this override works, but for **module-level variables (data members)** it has no
effect: a module variable whose name begins with an underscore and is documented
`:meta public:` is still hidden, and a module variable documented
`:meta private:` is still shown.

The cause is in how the module documenter collects its members. When
`sphinx.ext.autodoc.ModuleDocumenter` gathers the entries of a target module (in
`ModuleDocumenter.get_object_members` in `sphinx/ext/autodoc/__init__.py`), the
collected entries do **not** carry the documentation comment recorded for each
name in the module source. The unchanged downstream filtering step
(`Documenter.filter_members`, which calls `sphinx.util.docstrings.extract_metadata`
to read each member's `:meta ...:` fields) therefore never sees the metadata for a
module variable and falls back to the leading-underscore naming convention alone.

The goal is that module-level variables honour `:meta public:` and
`:meta private:` exactly the way functions and other members already do, while
every other aspect of module-member collection is preserved.

## Requirement 1: Attach each module member's documentation comment when collecting members

**User story:** As a documentation author, I want the extension to know the
documentation comment I wrote for each module-level variable, so that the fields
in that comment (such as visibility metadata) can take effect.

**Acceptance criteria**

1. WHEN `ModuleDocumenter.get_object_members` collects the entries of a target
   module, THEN each collected member entry SHALL carry the documentation comment
   text recorded for that member's name in the module source.
2. IF no documentation comment is recorded for a name, THEN the entry for that
   name SHALL carry an empty documentation comment (never a missing/None comment
   that would suppress metadata extraction).
3. The system SHALL derive each name's recorded documentation comment from the
   module source analysis (the module-level attribute comments), joining a
   multi-line comment into a single text value.
4. WHEN there is no source analysis available for the module, THEN collection
   SHALL still succeed and SHALL treat every name as having an empty
   documentation comment.

## Requirement 2: `:meta public:` reveals an otherwise-private module variable

**User story:** As a documentation author, I want a module variable I marked
`:meta public:` to appear in the generated documentation even though its name
begins with an underscore, so that I can publish intentionally-public names that
follow the private naming convention.

**Acceptance criteria**

1. WHEN a module is documented with all members requested and a module-level
   variable whose name begins with an underscore is documented `:meta public:`,
   THEN that variable SHALL be included in the generated output as a data member.
2. WHEN such a `:meta public:` variable is emitted, THEN its rendered entry SHALL
   report its module and its value, and SHALL retain the `:meta public:` field in
   its description.
3. The system SHALL apply this override on the basis of the documentation
   comment's visibility metadata, taking precedence over the leading-underscore
   convention that would otherwise classify the variable as private.

## Requirement 3: `:meta private:` hides an otherwise-public module variable

**User story:** As a documentation author, I want a module variable I marked
`:meta private:` to be treated as private, so that I can hide implementation
details whose names do not follow the underscore convention.

**Acceptance criteria**

1. WHEN a module is documented with all members requested and default visibility,
   and a module-level variable is documented `:meta private:`, THEN that variable
   SHALL NOT appear in the generated output, even if its name does not begin with
   an underscore.
2. WHEN private members are explicitly requested for that module, THEN a
   `:meta private:` module variable SHALL be included in the generated output as
   a data member, reporting its module and value and retaining its `:meta private:`
   field.

## Requirement 4: Private module variables appear when explicitly requested

**User story:** As a documentation author, I want to include specific private
module variables by naming them, or by asking for private members, so that I can
document internal state on demand.

**Acceptance criteria**

1. WHEN private members are requested for a module (whether by a general
   private-members request or by naming specific members), THEN a private
   module-level variable — one whose name begins with an underscore or one
   documented `:meta public:`/`:meta private:` — that is covered by the request
   SHALL be included in the generated output as a data member.
2. WHEN a private module variable documented `:meta public:` is covered by a
   private-members request, THEN it SHALL be emitted with its module, its value,
   and its `:meta public:` field retained.
3. IF a name is requested for a module member that does not exist on the module,
   THEN the collection SHALL omit it (and the existing missing-attribute warning
   behavior for explicitly named members SHALL be preserved).

## Requirement 5: Preserve existing module-member collection behavior

**User story:** As a maintainer, I want the visibility fix to leave all other
module-member collection behavior unchanged, so that existing documents render
exactly as before.

**Acceptance criteria**

1. The system SHALL collect one entry for every name visible on the target
   module, in the module's name order, followed by one additional entry for every
   annotation-only member (a name with a declared type but no bound value) that
   was not already collected.
2. WHEN a member is annotation-only, THEN its entry SHALL be marked with the
   annotation-only value sentinel rather than a concrete value.
3. WHEN all members are requested and the module declares no explicit export
   list, THEN collection SHALL return every collected entry together with the flag
   indicating that all members were taken.
4. WHEN all members are requested and the module declares a non-empty explicit
   export list, THEN every collected entry SHALL be returned, with each entry
   whose name is not in the export list marked as suppressed, and the flag SHALL
   indicate that not all members were taken.
5. WHEN an explicit list of member names is requested, THEN collection SHALL
   return, in the requested order, the collected entry for each requested name
   that exists on the module, and SHALL leave the returned entries' name, value,
   and documentation comment unchanged.
6. The system SHALL keep the ordering, values, and names of returned entries
   unchanged relative to the mode of the request; only the suppression flag and
   which entries are returned SHALL depend on the request mode.
