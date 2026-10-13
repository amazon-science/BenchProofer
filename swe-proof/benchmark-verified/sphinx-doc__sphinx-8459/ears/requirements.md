# Requirements: honour type aliases when documenting typehints in description mode

## Introduction

Sphinx's autodoc extension can render a documented callable's parameter and
return type hints either inline in the object signature or as a separate
"description" field list (controlled by the `autodoc_typehints` configuration
value). Independently, the `autodoc_type_aliases` configuration lets a project
substitute a chosen display name in place of a type's default rendering (for
example, showing an alias name instead of the concrete type it expands to).

When `autodoc_typehints` is set to `'signature'`, the alias substitution is
applied and the aliased names appear. But when `autodoc_typehints` is set to
`'description'`, the alias substitution is ignored: the type labels shown in the
generated Parameters / Return type description reflect the fully-resolved
underlying types rather than the configured aliases. This is inconsistent with
signature mode and with the documented purpose of `autodoc_type_aliases`.

The relevant behavior lives in the autodoc typehints support module
(`sphinx/ext/autodoc/typehints.py`), specifically in the step that records a
callable's parameter and return type annotations into the build environment
(the `record_typehints` handler for the `autodoc-process-signature` event). That
step introspects the callable's signature via `sphinx.util.inspect.signature`,
which already accepts a `type_aliases` mapping and applies it when resolving
annotations. The goal is to make the recorded (and therefore description-mode)
type labels honour `autodoc_type_aliases` exactly as signature mode does.

## Requirement 1: Apply configured type aliases when recording typehints for description output

**User story:** As a documentation author who configures `autodoc_type_aliases`,
I want the aliased type names to appear in the generated parameter and return
type descriptions when `autodoc_typehints` is `'description'`, so that my chosen
display names are shown consistently regardless of how typehints are rendered.

**Acceptance criteria**

1. WHEN autodoc records the type annotations of a documented callable and the
   project configures `autodoc_type_aliases`, THEN the system SHALL resolve each
   parameter annotation and the return annotation using that alias mapping
   before storing the type label used for description output.

2. IF a parameter's declared type name is a key in `autodoc_type_aliases`, THEN
   the recorded type label for that parameter SHALL be the configured
   replacement value rather than the type's default rendering.

3. IF the return value's declared type name is a key in
   `autodoc_type_aliases`, THEN the recorded return type label SHALL be the
   configured replacement value rather than the type's default rendering.

4. WHEN `autodoc_typehints` is `'description'` and `autodoc_type_aliases` is
   configured, THEN the rendered "Parameters" field for each annotated parameter
   SHALL display the alias-aware label, and the rendered "Return type" field
   SHALL display the alias-aware label.

5. The system SHALL produce, in description mode with aliases configured, the
   same aliased type labels that signature mode would produce for the same
   callable and the same alias mapping.

## Requirement 2: Preserve existing typehints and alias behavior

**User story:** As a Sphinx user relying on existing autodoc behavior, I want
the alias fix to leave all other typehints handling unchanged, so that current
documentation output is not regressed.

**Acceptance criteria**

1. WHEN a callable has a parameter whose declared type name is not present in
   `autodoc_type_aliases`, THEN the recorded type label for that parameter SHALL
   be the type's default rendering (no substitution).

2. WHEN a parameter carries no type annotation, THEN the system SHALL record no
   type label for it and SHALL NOT add a spurious type entry for that parameter.

3. WHEN the return value carries no type annotation, THEN the system SHALL
   record no return type label and SHALL NOT add a return type entry.

4. The system SHALL record annotations in declaration order: one entry per
   annotated parameter keyed by that parameter's name, followed by the return
   entry (under the reserved return key) when the return value is annotated.

5. WHILE `autodoc_typehints` is `'signature'`, the system SHALL continue to
   render type hints inline in the object signature, applying
   `autodoc_type_aliases` as before.

6. WHILE `autodoc_typehints` is `'none'`, the system SHALL continue to omit
   type hints from both the signature and the description output.

7. WHEN `autodoc_typehints` is `'description'` and `autodoc_type_aliases` is not
   configured, THEN the system SHALL continue to render the parameter and return
   type descriptions using the types' default renderings, unchanged from prior
   behavior.

8. IF introspecting a callable's signature raises an error (for example, an
   object whose signature cannot be determined), THEN the system SHALL record no
   annotations for that object and SHALL NOT propagate the error.
