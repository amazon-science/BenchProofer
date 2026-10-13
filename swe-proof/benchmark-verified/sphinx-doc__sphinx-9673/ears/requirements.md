# Requirements: Return type appears when a documented return is written with the plural return field

## Introduction

When `autodoc_typehints = "description"` is set, `sphinx.ext.autodoc` moves type
information from the signature into the description as reStructuredText fields.
The transform lives in `sphinx/ext/autodoc/typehints.py`: `merge_typehints`
selects, per object, how the recorded type annotations are woven into the
object's field list. When `autodoc_typehints_description_target` is `"documented"`
(anything other than `"all"`), it calls `augment_descriptions_with_types(field_list,
annotations)`, which only adds type information for names the author has already
described.

`augment_descriptions_with_types` scans the existing fields, splitting each field
name into whitespace-separated tokens, to learn which names already have a
*description* and which already have a *declared type*. For the function result it
recognizes a description from a field headed `return` and a declared type from a
field headed `rtype`; when a return description exists but no declared return type
does, and a return-type annotation is available, it appends an `rtype` field so the
return type shows up.

The bug: the Napoleon extension (Google and NumPy styles) renders a documented
return using the **plural** field keyword (`returns`), not the singular `return`
that this transform looked for. As a result, with `autodoc_typehints =
"description"` and `autodoc_typehints_description_target = "documented"`, a function
whose docstring documents its return had its return *description* go unrecognized,
so no `rtype` field was added and the return type was silently dropped from the
generated documentation.

The goal is to make the return-description detection accept the plural return
keyword as equivalent to the singular one, so the return type is emitted whenever
the result is documented — regardless of which return keyword the docstring style
produced — while leaving every other behavior of this transform unchanged.

## Requirement 1: Recognize a plural return field as a documented return

**User story:** As an author using a docstring style (such as Napoleon's Google or
NumPy styles) that renders the documented return with the plural return keyword, I
want the return type to appear in the generated description, so that enabling
`autodoc_typehints = "description"` with `autodoc_typehints_description_target =
"documented"` still documents my return type.

**Acceptance criteria**
1. WHEN `augment_descriptions_with_types` processes a field list in which the
   result is described by a field whose leading token is the plural return keyword
   (`returns`), THEN it SHALL treat the result as having a description, exactly as
   it does for the singular return keyword (`return`).
2. WHEN a function has a recorded return-type annotation and its field list
   documents the return via a plural-return-keyword field but declares no return
   type (no `rtype` field), THEN `augment_descriptions_with_types` SHALL append a
   single `rtype` field whose body is the stringified return-type annotation.
3. WHEN documentation is built with `autodoc_typehints = "description"` and
   `autodoc_typehints_description_target = "documented"` for a function that
   documents its return with the plural return keyword and has a return
   annotation, THEN the rendered output SHALL include both the return description
   and a return-type entry carrying that annotation.

## Requirement 2: Do not treat the return name as an ordinary documented parameter

**User story:** As a maintainer, I want the result name to remain excluded from the
per-parameter type augmentation, so that the return is never emitted as if it were
a positional parameter under either return keyword spelling.

**Acceptance criteria**
1. WHILE iterating the recorded annotations to add `type <name>` fields for
   described-but-untyped parameters, `augment_descriptions_with_types` SHALL skip
   any annotation whose name is the singular or the plural return keyword
   (`return` or `returns`).
2. The system SHALL emit the return type only as a single `rtype` field, never as
   a `type return` or `type returns` parameter-type field.

## Requirement 3: Preserve the existing singular-return behavior

**User story:** As a maintainer, I want docstring styles that already used the
singular return keyword to keep working exactly as before, so that this change adds
support for the plural form without regressing the original one.

**Acceptance criteria**
1. WHEN a field list documents the return with the singular return keyword and has
   no declared return type, and a return annotation exists, THEN
   `augment_descriptions_with_types` SHALL append an `rtype` field carrying that
   annotation, as it did previously.
2. IF the field list already contains a declared return type (an `rtype` field),
   THEN `augment_descriptions_with_types` SHALL NOT append an additional `rtype`
   field, regardless of which return keyword described the result.
3. IF the result is not documented by any return-description field, THEN
   `augment_descriptions_with_types` SHALL NOT append an `rtype` field, even when a
   return annotation is available.

## Requirement 4: Preserve parameter type augmentation

**User story:** As a user, I want documented-but-untyped parameters to keep gaining
their annotated types under the `"documented"` target, so that the fix is confined
to return handling.

**Acceptance criteria**
1. WHEN a parameter is described (a `param` field is present) but carries no
   declared type (no matching `type` field) and has a recorded annotation, THEN
   `augment_descriptions_with_types` SHALL append a `type <name>` field carrying
   that parameter's annotation.
2. IF a parameter already has a declared type, THEN
   `augment_descriptions_with_types` SHALL NOT add a duplicate `type` field for it.
3. IF a parameter is not described in the field list, THEN
   `augment_descriptions_with_types` SHALL NOT add a `type` field for it (the
   `"documented"` target adds types only for documented names).

## Requirement 5: Preserve the "all" target and other typehint modes

**User story:** As a maintainer, I want the other `autodoc_typehints` and
`autodoc_typehints_description_target` behaviors to be unaffected, so that only the
documented-return case changes.

**Acceptance criteria**
1. WHEN `autodoc_typehints_description_target` is `"all"`, THEN `merge_typehints`
   SHALL continue to augment the field list with types for all parameters and the
   return (adding missing `param`, `type`, and `rtype` fields), unchanged by this
   fix.
2. WHILE `autodoc_typehints` is set to `"none"`, `"signature"`, or `"both"`, the
   system SHALL preserve its prior placement of type information for those modes.
3. The system SHALL leave the recording of type annotations (parameter annotations
   and the return annotation stored under the return name) unchanged.
