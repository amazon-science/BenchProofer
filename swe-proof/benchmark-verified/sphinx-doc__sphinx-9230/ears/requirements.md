# Requirements: Correct type/name splitting for inline-typed info fields

## Introduction

Sphinx lets a documenter declare a parameter's type inline with its name in a
single info field, using the form `:param <type> <name>:`. This is handled by
`DocFieldTransformer.transform` in `sphinx/util/docfields.py`, which decomposes
the field-argument string (the text between `:param ` and the trailing `:`) into
a type part and a name part before the type is cross-referenced and the
parameter is rendered.

The decomposition currently assumes the type is a single whitespace-free token:
it splits the field-argument string at its **first** run of whitespace, treating
the first token as the type and everything after it as the name. This is wrong
whenever the declared type itself contains whitespace — for example
`:param dict(str, str) opc_meta:`. Such a
field is mis-decomposed: part of the type is captured as the name and part of
the name/type is lost or reordered, so the generated documentation shows a
garbled entry (e.g. `str) opc_meta (dict(str,) –`) instead of
`opc_meta (dict(str, str)) –`.

The goal is to make the decomposition treat the **last** whitespace-delimited
token as the parameter name and the entire preceding remainder as the type, so
that types containing internal whitespace render correctly, while all
previously-correct single-token cases continue to behave exactly as before.

The affected behavior is localized to the inline-typed field-argument
decomposition inside `DocFieldTransformer.transform`
(`sphinx/util/docfields.py`); the surrounding type-collection and
node-construction logic consumes the resulting `(type, name)` pair verbatim.

## Requirement 1: Split inline-typed fields at the last whitespace

**User story:** As a documentation author, I want to write a parameter's type
and name together as `:param <type> <name>:` where the type may contain spaces,
so that the type renders intact and the name is identified correctly.

**Acceptance criteria**

1. WHEN a typed info field's argument string contains two or more
   whitespace-delimited tokens, THEN `DocFieldTransformer.transform` SHALL treat
   the final whitespace-delimited token as the parameter name and the entire
   remaining prefix (up to, but not including, the whitespace run that precedes
   that final token) as the parameter's type.
2. WHEN the declared type itself contains internal whitespace (for example a
   generic or container type written with a comma-and-space such as the type in
   `:param dict(str, str) opc_meta:`), THEN `DocFieldTransformer.transform` SHALL
   preserve that whitespace inside the type and SHALL NOT absorb any part of the
   type into the parameter name.
3. WHEN a type is extracted from an inline `<type> <name>` field, THEN that type
   SHALL be handed to the same type-rendering path used for a type supplied via a
   separate type field, so that the extracted type is cross-referenced and
   rendered identically to how the very same type string would be rendered had it
   been written as a separate type field for the same parameter.
4. WHEN the type/name split succeeds, THEN the parameter entry SHALL be rendered
   with the parameter name first, followed by the fully-reconstructed type, so
   that the type shown equals the originally written type string.

## Requirement 2: Preserve behavior for single-token and untyped fields

**User story:** As a maintainer, I want the existing well-formed field forms to
keep rendering exactly as they did, so that fixing the multi-word-type case
introduces no regressions.

**Acceptance criteria**

1. WHEN a typed info field's argument string consists of exactly one type token
   followed by one name token (for example `int age`), THEN
   `DocFieldTransformer.transform` SHALL identify the first token as the type
   and the second token as the name — identical to the prior behavior for this
   form.
2. IF a typed info field's argument string contains only a single
   whitespace-delimited token (no separate type token), THEN
   `DocFieldTransformer.transform` SHALL leave the field-argument string
   unchanged and SHALL NOT record a type for it, matching the existing handling
   when the type/name split cannot be performed.
3. WHEN a parameter's type is instead supplied through a separate type field
   rather than inline with the name, THEN the parameter and its type SHALL be
   associated and rendered exactly as before this change.
4. The system SHALL continue to render parameter, type, return, and other info
   fields whose arguments do not use the inline `<type> <name>` form without any
   change to their existing output.
5. WHEN leading, trailing, or repeated interior whitespace surrounds the tokens
   of an inline-typed field argument, THEN the split SHALL collapse and strip
   whitespace at the token boundaries in the same manner as the prior
   single-token handling, so that the name and type carry no spurious leading or
   trailing whitespace.
