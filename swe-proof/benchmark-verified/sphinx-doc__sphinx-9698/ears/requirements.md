# Requirements: Property methods must not show parentheses in the index

## Introduction

The Python domain of the documentation tool (`sphinx/domains/python.py`)
registers a single general-index entry for each documented class member. For
the `py:method` directive, the label text for that entry is produced by the
`PyMethod.get_index_text` method, based on the member's fully-qualified dotted
name, the enclosing module name, the `add_module_names` configuration flag, and
which option modifier (if any) was supplied on the directive.

When the `py:method` directive is given the `:property:` option, the member is a
value that is *accessed*, not a callable that is *invoked*. The index label,
however, was rendered with a trailing empty argument list — of the abstract form
`<member>() (<class> property)` — as if it were called. This is inconsistent
with the label produced for a member documented via the dedicated `py:property`
directive (`PyProperty.get_index_text`), which correctly shows no parentheses.

The goal is to make the `py:method` `:property:` index label render the member
name **without** the trailing `()`, while leaving every other method-kind label
and every unrelated Python-domain behavior exactly as before.

## Requirement 1: Index label for a property-flagged method omits parentheses

**User story:** As a documentation author using `py:method` with the
`:property:` option, I want the generated general-index entry to show the member
name without parentheses, so that it reads as an attribute access and matches
entries produced by `py:property`.

**Acceptance criteria**

1. WHEN `PyMethod.get_index_text` builds the index label for a member whose
   dotted name splits into a class part and a member part AND the directive
   carries the `property` option (and not the `classmethod` option), THEN the
   method SHALL return a label of the form `<member> (<class> property)` in
   which the member name is followed directly by a space and the parenthesized
   qualifier, with **no** `()` appended to the member name.
2. IF a member is documented with `py:method` and the `:property:` option, THEN
   the resulting general-index entry's display text SHALL contain the member
   name immediately followed by ` (` and SHALL NOT contain the substring
   `()` after the member name.
3. The system SHALL keep the parenthesized class qualifier `(<class> property)`
   in the property label unchanged; only the empty argument list following the
   member name is removed.

## Requirement 2: Non-property method-kind labels are unchanged

**User story:** As a maintainer, I want the index labels for ordinary methods,
class methods, and static methods to keep their existing call-style `()`
rendering, so that this fix does not regress other member kinds.

**Acceptance criteria**

1. WHEN `PyMethod.get_index_text` builds a label for a member carrying the
   `classmethod` option, THEN the method SHALL return `<member>() (<class> class
   method)` with the trailing `()` preserved.
2. WHEN the member carries the `staticmethod` option (and neither `classmethod`
   nor `property`), THEN the method SHALL return `<member>() (<class> static
   method)` with the trailing `()` preserved.
3. WHEN the member carries none of the `classmethod`, `property`, or
   `staticmethod` options, THEN the method SHALL return `<member>() (<class>
   method)` with the trailing `()` preserved.
4. WHILE both the `classmethod` and `property` options are present, the method
   SHALL render the class-method label form, because the class-method kind is
   selected in preference to the property kind.
5. WHEN the dotted name has no separating dot so that no class part can be
   formed, THEN the method SHALL fall back to `<name>() (in module <module>)`
   when a module name is present and `<name>()` otherwise, preserving the
   trailing `()` in this fallback regardless of the property option.

## Requirement 3: The property-flagged method still renders correctly on the page

**User story:** As a documentation author, I want a `py:method` with
`:property:` to keep rendering as a property in the signature, so that only the
general-index label — not the visible signature — changes.

**Acceptance criteria**

1. WHEN a `py:method` directive carries the `:property:` option, THEN the
   rendered signature SHALL display the `property` prefix annotation followed by
   the member name, unchanged by this fix.
2. The system SHALL continue to register exactly one general-index entry for
   such a member, targeting the member's fully-qualified name, with only the
   entry's display text affected as described in Requirement 1.

## Requirement 4: Dedicated attribute and property directives are unaffected

**User story:** As a maintainer, I want the separate `py:attribute` and
`py:property` directives to keep their current parenthesis-free index labels, so
that the fix is confined to the property-flagged `py:method` path.

**Acceptance criteria**

1. The system SHALL continue to produce `<member> (<class> attribute)` for a
   member documented with `py:attribute`, without a trailing `()`.
2. The system SHALL continue to produce `<member> (<class> property)` for a
   member documented with `py:property`, without a trailing `()`.
3. WHEN cross-references are resolved for members documented as properties, THEN
   the resolution behavior SHALL remain unchanged by this fix.
