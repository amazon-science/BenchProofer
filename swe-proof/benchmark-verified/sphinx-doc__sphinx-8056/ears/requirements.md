# Requirements: Napoleon should render grouped Numpy-style parameters individually

## Introduction

Sphinx's `sphinx.ext.napoleon` extension converts Numpy- and Google-style
docstrings into reStructuredText. The Numpy docstring format permits declaring
several closely-related parameters on a single line by listing their names,
comma-separated, before the type, for example:

```
x1, x2 : array_like
    Input arrays, description of `x1`, `x2`.
```

Currently, when `napoleon_use_param` is enabled, the Napoleon parser treats the
whole comma-separated list (`x1, x2`) as one parameter name. The resulting
`:param:`/`:type:` rendering therefore shows a single malformed parameter
entry, and any trailing qualifier such as `, optional` is lost in the display,
so the reader cannot see the individual parameters or their optionality.

The goal is to make the Parameters-section handling in
`sphinx/ext/napoleon/docstring.py` (the `GoogleDocstring`/`NumpyDocstring`
field-consumption logic, used by `_parse_parameters_section` and
`_format_docutils_params`) expand such a grouped declaration into one
parameter entry per listed name — each carrying the shared type and shared
description — while leaving every other docstring section and configuration
mode unchanged.

## Requirement 1: Expand comma-grouped parameter names into individual entries

**User story:** As a library author documenting several similar arguments on
one line, I want each named parameter to be rendered as its own entry, so that
every parameter (and its type/optionality) is visible in the generated docs.

**Acceptance criteria**

1. WHEN a Numpy-style Parameters section is parsed with `napoleon_use_param`
   enabled and a field's name portion contains comma-separated names (e.g.
   `x1, x2`), THEN the parser SHALL emit one separate parameter entry for each
   listed name rather than a single entry containing the whole list.
2. WHEN a grouped name field is expanded, THEN each produced entry SHALL carry
   the same type string and the same description lines as the original field.
3. WHEN each individual name is extracted from the comma-separated list, THEN
   the parser SHALL strip surrounding whitespace from that name so the emitted
   parameter name has no leading or trailing spaces.
4. WHEN a Parameters field declares a single name (no comma), THEN the parser
   SHALL emit exactly one entry for that name, identical to its prior behavior.
5. The order of the emitted parameter entries SHALL follow the order in which
   the names appear in the source line (and across successive fields).
6. WHEN `napoleon_use_param` is enabled, THEN the expanded entries SHALL be
   rendered through the existing `:param:`/`:type:` (docutils params) output so
   that each listed parameter produces its own `:param:` and `:type:` lines.

## Requirement 2: Preserve field consumption for empty and non-grouped fields

**User story:** As a maintainer, I want the parameter-splitting change to leave
already-correct docstrings untouched, so that no existing rendering regresses.

**Acceptance criteria**

1. WHEN a Parameters field has an empty name but a non-empty type and/or
   description, THEN the parser SHALL still emit that field as a single entry
   (the splitting behavior SHALL apply only when a name is present).
2. The parser SHALL continue to preserve any type qualifier text (such as an
   `optional` marker) associated with the shared type for every expanded entry.
3. The system SHALL preserve the existing escaping of special argument names —
   names beginning with `*` or `**` (variadic `*args`/`**kwargs` style) SHALL
   remain correctly escaped in the emitted output.

## Requirement 3: Restrict splitting to the parameter list under use_param

**User story:** As a user relying on other docstring sections, I want the new
behavior confined to the Parameters section in `napoleon_use_param` mode, so
that unrelated sections keep their current output.

**Acceptance criteria**

1. WHEN `napoleon_use_param` is disabled, THEN the Parameters section SHALL be
   consumed and formatted exactly as before, WITHOUT splitting comma-separated
   names into multiple entries.
2. The system SHALL NOT apply comma-name splitting to other field-based
   sections (for example Other Parameters, Keyword Arguments, Raises, Returns,
   or Attributes); those sections SHALL retain their existing entry behavior.
3. IF a docstring section is not the parameters list handled under
   `napoleon_use_param`, THEN its field names containing commas SHALL be left
   intact as a single name.

## Requirement 4: Preserve all existing Napoleon docstring rendering

**User story:** As a downstream project, I want the full range of Napoleon
docstring features to keep working, so that upgrading does not break my docs.

**Acceptance criteria**

1. WHEN any docstring construct other than a comma-grouped Numpy Parameters
   name under `napoleon_use_param` is rendered, THEN the system SHALL produce
   output byte-identical to its behavior before this change.
2. The change SHALL be confined to the comma-grouped-name expansion in the
   Parameters field-consumption path; the system SHALL NOT alter the behavior
   of any other docstring section, type-specification handling, attribute
   handling, or section-header processing.
