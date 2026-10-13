# Requirements: Render Python Enum default values readably in generated docs

## Introduction

When Sphinx's autodoc renders a function signature, it displays each
parameter's default value as text. The value-to-text conversion is performed by
`object_description` in `sphinx/util/inspect.py`, a `repr()`-style helper that
returns a string safe to embed in reST output. It already gives dedicated
renderings to mappings (`dict`), sets (`set`), and frozen sets (`frozenset`),
and falls back to a general-purpose `repr()`-based rendering (with
non-deterministic memory addresses stripped and newlines flattened) for
everything else.

For a member of a Python enumeration (`enum.Enum`), the general-purpose
fallback produces the raw `repr()`, e.g. `<MyEnum.ValueA: 10>`, which is ugly
and leaks the member's underlying value into the documented signature. The
desired display is the member's qualified name, e.g. `MyEnum.ValueA`.

The goal is to make `object_description` render a plain enumeration member as
its class name and member name joined by a dot, while leaving the existing
dedicated container renderings and the general-purpose fallback untouched, so
that documented default values that are enum members read cleanly and every
other value renders exactly as before.

## Requirement 1: Render an enumeration member as its qualified name

**User story:** As a developer documenting a function whose default argument is
an enumeration member, I want the generated signature to show the member as
`ClassName.MemberName`, so that the rendered default value is readable and does
not expose the member's raw representation or underlying value.

**Acceptance criteria**

1. WHEN `object_description` is called with an `enum.Enum` member that is not
   also an instance of one of the specially-rendered container kinds
   (`dict`, `set`, `frozenset`), THEN it SHALL return the text formed by the
   member's enumeration class name, followed by a single `.`, followed by the
   member's name.
2. WHEN rendering such an enumeration member, THEN the class-name portion SHALL
   be the unqualified name of the member's own class (its class `__name__`),
   and the member-name portion SHALL be the member's `name` attribute (the
   identifier under which the member is defined), and the returned string SHALL
   contain neither the member's underlying value nor any angle brackets or
   `repr()` decoration.
3. WHEN two distinct members of the same enumeration are rendered, THEN
   `object_description` SHALL return strings that differ only in the member-name
   portion, each being that member's own name.

## Requirement 2: Preserve existing renderings for all other values (regression protection)

**User story:** As a maintainer, I want every value that already had a defined
rendering to keep rendering exactly as before, so that adding enum support does
not change the output for containers or any other type.

**Acceptance criteria**

1. WHEN `object_description` is called with a `dict` whose keys can be sorted,
   THEN it SHALL return the existing brace-delimited rendering listing each
   key/value pair (each key and value itself rendered by `object_description`)
   with keys in sorted order, unchanged by this feature.
2. WHEN `object_description` is called with a `set` whose members can be sorted,
   THEN it SHALL return the existing brace-delimited rendering of its members in
   sorted order; and IF the members cannot be sorted, THEN it SHALL fall back to
   the general-purpose rendering, exactly as before.
3. WHEN `object_description` is called with a `frozenset` whose members can be
   sorted, THEN it SHALL return the existing `frozenset({...})` rendering of its
   members in sorted order; and IF the members cannot be sorted, THEN it SHALL
   fall back to the general-purpose rendering, exactly as before.
4. IF a value is an enumeration member that is ALSO an instance of one of the
   specially-rendered container kinds (`dict`, `set`, or `frozenset`), THEN
   `object_description` SHALL apply that container's existing rendering rather
   than the qualified-name rendering of Requirement 1, so that the container
   renderings take precedence over the enum rendering.
5. WHEN `object_description` is called with any value that is neither an
   enumeration member nor one of the specially-rendered container kinds, THEN it
   SHALL return the result of the existing general-purpose rendering: the
   value's `repr()` with non-deterministic memory addresses stripped and
   embedded newlines replaced by spaces, unchanged by this feature.
6. IF computing a value's representation raises an exception in the
   general-purpose path, THEN `object_description` SHALL continue to raise the
   same error it raised before, unchanged.
