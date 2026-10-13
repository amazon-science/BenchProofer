# Requirements: suppress the spurious class "return type" under `autodoc_typehints = "description"`

## Introduction

When Sphinx's autodoc extension is configured with `autodoc_typehints = "description"`
(or `"both"`), type-hint information is moved out of the signature and rendered as
fields in the description of each documented object. For a class, autodoc documents
the class by way of its constructor (`__init__`), whose annotated return is always the
unit annotation `None`. As a result, the rendered class description gained a spurious
"Return type: None" entry, which is meaningless for a class and confused readers.

The affected code is the type-hint field-list machinery in
`sphinx/ext/autodoc/typehints.py`: the transform `merge_typehints`, which decides how
to inject type information for each documented object, and the helper
`modify_field_list`, which appends `type`/`param`/`rtype` fields to an object's
description field list. The goal is to stop emitting the return-type field for a class
whose (constructor) return annotation is `None`, while leaving every other object's
type-hint rendering unchanged.

Concrete behavioral vocabulary used below:
- The description field list of a documented object holds fields whose name text is one
  of `param <name>`, `type <name>`, `param <kind> <name>`, `rtype`, or `return`.
- The recorded annotations are an ordered mapping from a parameter name (or the special
  return position) to its rendered type string, with unique keys.
- "the return-type field" is the field whose name text is `rtype` and whose body is the
  rendered return annotation.

## Requirement 1: Do not emit a return-type field for a class with a `None` return annotation

**User story:** As a documentation author using `autodoc_typehints = "description"`, I
want `autoclass` output to omit a return-type entry, so that a class is not shown as
"returning" `None`.

**Acceptance criteria**

1. WHEN autodoc renders the description of an object whose object type is a class,
   `autodoc_typehints` is `"description"` (or `"both"`), and the effective
   description target selects the mode that appends type/param fields for every recorded
   annotation, THEN the field-list machinery in `sphinx/ext/autodoc/typehints.py` SHALL
   determine the recorded return annotation for that object.
2. IF the object type is a class AND the recorded return annotation is exactly the unit
   annotation `None`, THEN the machinery SHALL NOT append any return-type (`rtype`) field
   to that object's description field list.
3. WHILE rendering a class whose recorded return annotation is `None`, the machinery
   SHALL leave every parameter's `type`/`param` field generation unchanged (each recorded
   non-return annotation still yields its type field unless a type is already declared,
   and its param field unless the parameter is already declared).
4. IF the object type is a class AND a recorded return annotation exists that is NOT the
   unit annotation `None`, THEN the machinery SHALL append the return-type field exactly
   as it would for any other object.

## Requirement 2: Preserve the return-type field for non-class objects (functions and methods)

**User story:** As a user documenting functions and methods, I want their return type to
keep appearing in the description, so that suppressing the class case does not regress
ordinary callables.

**Acceptance criteria**

1. WHEN autodoc renders the description of an object whose object type is NOT a class
   (for example a function or a method) with the same append-all type-hint mode active,
   THEN the machinery SHALL append the return-type field whenever a return annotation is
   recorded and no return type is already declared among the existing fields — including
   when that recorded return annotation is `None`.
2. The system SHALL treat the suppression of the `None` return type as applying only to
   the class object type; no non-class object's rendered output SHALL change as a result
   of this behavior.

## Requirement 3: Preserve all existing type-hint field-list behavior

**User story:** As a maintainer, I want the fix to be surgical, so that the many existing
type-hint description behaviors continue to hold.

**Acceptance criteria**

1. WHEN the append-all type-hint mode processes an object's recorded annotations, THEN for
   each recorded non-return annotation the machinery SHALL append a `type <name>` field
   carrying the rendered type unless the existing fields already declare a type for that
   name, and SHALL append an empty `param <name>` field unless the existing fields already
   declare that parameter — in the recorded annotation order, after the pre-existing
   fields.
2. IF the existing fields already declare a return type (an `rtype` field, or a field
   naming the return position), THEN the machinery SHALL NOT append an additional
   return-type field, regardless of object type or annotation value.
3. WHEN the description target is the mode that augments only documented parameters, THEN
   the machinery SHALL keep its existing behavior of adding a return-type field when a
   return is documented or when return-type addition is forced and the return annotation
   is not `None`, and SHALL NOT be affected by the class suppression rule.
4. WHEN the description target is the default mode that augments descriptions with types,
   THEN the machinery SHALL keep adding a `type` field for each parameter that has a
   description but no declared type, and SHALL add the return-type field only when a
   return description is present and no return type is declared.
5. The body text of an appended return-type field SHALL be the recorded return annotation
   for that object (not a stale value left over from processing an earlier parameter).
6. The system SHALL leave unchanged the behaviors selected by `autodoc_typehints` values
   `"signature"`, `"none"`, and their handling of overloads, type aliases, fully-qualified
   formatting, and the `autoclass_content` options (class/init/both), so that those
   renderings are unaffected by this change.
