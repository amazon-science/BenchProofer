# Requirements: Honour variable comments when documenting module-level type aliases

## Introduction

When Sphinx's `sphinx.ext.autodoc` extension documents a module-level name that
is bound to an object it treats as a class alias (for example, a type alias such
as `MyAlias = Dict[str, Any]`), it renders the object in "alias" mode. In this
mode the ordinary class docstring is intentionally suppressed and the output is
reduced to a single placeholder line of the form `alias of <target>`.

The affected code is the `ClassDocumenter` in `sphinx/ext/autodoc/__init__.py`,
specifically its `get_doc` and `add_content` methods and their handling of the
"documented as an alias" state (the flag conventionally named `doc_as_attr`).

The problem is that many such aliases have an author-written documentation
comment attached at the module level — the block string that immediately follows
the assignment statement, which Sphinx already collects as a variable/attribute
comment through its source-code analyzer (`ModuleAnalyzer`, via the collected
attribute-documentation mapping keyed by namespace and dotted object path). When
this comment exists, autodoc currently discards it and still shows only the
`alias of ...` placeholder, so the author's documentation never appears.

The goal is: when an object is documented as an alias **and** a documentation
comment for that object is available from the module source, autodoc must show
that comment instead of the `alias of ...` placeholder. When no such comment
exists, the previous behaviour (show the `alias of ...` placeholder, and no
class docstring) must be preserved exactly.

## Requirement 1: Look up the alias object's variable/attribute comment

**User story:** As a documentation author, I want autodoc to find the comment I
wrote next to a module-level type-alias assignment, so that my explanation can be
associated with the alias.

**Acceptance criteria**

1. The system SHALL provide, on the class documenter, a means of retrieving the
   documentation comment collected for the object currently being documented,
   looked up by the object's dotted path within its module namespace.
2. WHEN the documentation comment is looked up, THEN the class documenter SHALL
   locate it using the attribute-documentation mapping produced by analyzing the
   object's real (defining) module source, using an empty class-namespace
   component together with the object's dotted path as the lookup key.
3. IF the module source cannot be analyzed because of a source-parsing error,
   THEN the lookup SHALL report that no comment is available rather than
   propagating an error.
4. WHEN a comment entry exists for the object, THEN the lookup SHALL return the
   comment as its sequence of text lines.
5. WHEN no comment entry exists for the object, THEN the lookup SHALL report an
   absent comment (an empty result).

## Requirement 2: Select the documentation block for an alias based on comment presence

**User story:** As a documentation author, I want a documented alias to yield an
empty (rather than suppressed) documentation block when I have written a comment
for it, so that the comment content is allowed to flow into the rendered output.

**Acceptance criteria**

1. WHILE the object is being documented as an alias, WHEN a documentation comment
   for the object is present (a lookup that succeeds and yields at least one
   line), THEN `get_doc` SHALL return an empty documentation block (a present
   result containing no docstring groups) rather than "no documentation".
2. WHILE the object is being documented as an alias, WHEN no documentation
   comment for the object is present (the lookup fails or yields no lines), THEN
   `get_doc` SHALL return "no documentation" (a `None` result), preserving the
   prior behaviour.
3. A lookup result that is present but empty SHALL be treated as an absent
   comment for the purpose of the two criteria above.
4. IF the object is not being documented as an alias, THEN `get_doc` SHALL
   compute and return the ordinary documentation block exactly as it did before,
   without consulting the variable comment.

## Requirement 3: Emit the comment content and suppress the placeholder when a comment exists

**User story:** As a reader of the generated documentation, I want to see the
author's alias comment rather than only the `alias of ...` line, so that the
documentation is complete.

**Acceptance criteria**

1. WHEN the object is being documented as an alias AND no documentation comment
   for the object is present, THEN `add_content` SHALL replace the forwarded
   supplementary content with a single line describing the alias target in the
   form `alias of <target>`.
2. WHEN the object is being documented as an alias AND a documentation comment
   for the object is present, THEN `add_content` SHALL NOT substitute the
   `alias of <target>` placeholder and SHALL forward the caller-supplied
   supplementary content unchanged, so that the collected comment content is the
   documentation shown for the alias.
3. IF the object is not being documented as an alias, THEN `add_content` SHALL
   forward the caller-supplied supplementary content unchanged, exactly as
   before.
4. WHEN building the `alias of <target>` line, IF the alias target cannot be
   rendered as a reference, THEN `add_content` SHALL leave the caller-supplied
   supplementary content unchanged rather than raising an error.

## Requirement 4: Confine the change to the alias-with-comment path

**User story:** As a maintainer, I want this change to affect only the case it
targets — an alias that has an author-written documentation comment — so that
every other autodoc behaviour is left exactly as it was and no regressions are
introduced.

**Acceptance criteria**

1. IF the object is not being documented as an alias, THEN the system SHALL
   produce byte-for-byte the same documentation output as before this change,
   consulting no variable comment and altering nothing about how ordinary
   classes, their docstrings, their members, or any other kind of documented
   object is rendered.
2. WHEN the object is being documented as an alias AND no documentation comment
   for the object is present, THEN the system SHALL render exactly the previous
   output: only the `alias of <target>` placeholder line, with the class's own
   docstring suppressed.
3. WHEN documenting an object as an alias (whether or not a comment is present),
   THEN the system SHALL continue to skip documenting that object's members, as
   before.
4. The change SHALL be limited to the alias-with-comment path; for every input
   that does not exercise that path, observable autodoc output SHALL be
   identical to the pre-change behaviour.
