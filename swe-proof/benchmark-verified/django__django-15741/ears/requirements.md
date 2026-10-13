# Requirements: Accept lazy format names when resolving localized formats

## Introduction

`django.utils.formats.get_format(format_type, lang=None, use_l10n=None)` resolves
a localized format (for example a date or time format) given the *name* of the
format. The function is reached, among other paths, by `date_format` /
`time_format` in the same module and ultimately by the `date` template filter in
`django.template.defaultfilters`, which passes the filter argument through as the
format name.

A previous change made `get_format` build a cache key from `format_type` and call
`getattr(...)` with `format_type` as the attribute name. Consequently, when the
format name arrives as a lazy string (a deferred/proxy string produced by
translation helpers such as `gettext_lazy`, e.g. from a template like
`some_date|date:_("Y-m-d")`), resolution fails with a `TypeError` because a
lazy proxy is not a concrete `str` and cannot be used as an attribute name.

The goal is to make `get_format` accept a lazy string as `format_type` and behave
exactly as it would for the equivalent concrete string, while preserving all
existing behavior for concrete-string inputs and for the callers that route
through it (the `date`/`time` formatting helpers and the `date` template filter).

## Requirement 1: Accept a lazy format name

**User story:** As a developer localizing templates, I want to pass a lazy
(translation-deferred) string as the format name so that expressions like
`some_date|date:_("H:i")` render correctly instead of raising an error.

**Acceptance criteria**
1. WHEN `django.utils.formats.get_format` is called with a `format_type` that is a
   lazy string proxy (such as one produced by `gettext_lazy`), THEN `get_format`
   SHALL resolve and return a value without raising `TypeError` (or any other
   exception caused by the argument not being a concrete `str`).
2. WHEN `get_format` receives a lazy `format_type`, THEN `get_format` SHALL return
   the same result it would return for the concrete string obtained by forcing
   that lazy value to its text (`str`) form, for the same language and
   localization settings.
3. WHEN `get_format` receives a lazy `format_type` naming a recognized format
   (for example the active locale's date format under default settings), THEN
   `get_format` SHALL return that format's value exactly as it would for the
   equivalent concrete name.
4. The system SHALL treat the format name purely by its concrete text content:
   two `format_type` arguments whose forced-`str` text is equal SHALL yield equal
   results under identical language and localization settings, regardless of
   whether each argument arrived as a concrete or lazy string.

## Requirement 2: Preserve existing behavior for concrete format names

**User story:** As a maintainer, I want the existing lookups and caching behavior
to be unchanged for ordinary string inputs, so that adding lazy support
introduces no regression.

**Acceptance criteria**
1. WHEN `get_format` is called with a concrete `str` `format_type`, THEN
   `get_format` SHALL return the same result it returned before this change for
   that input, language, and localization settings.
2. WHEN `format_type` names a localized format available in the active language's
   format modules and localization is enabled, THEN `get_format` SHALL return the
   value from those format modules.
3. IF the requested format is not found in any format module (or localization is
   disabled) AND the name corresponds to a known format setting, THEN
   `get_format` SHALL return the value taken from the project settings for that
   name.
4. IF the requested name does not correspond to any known format setting, THEN
   `get_format` SHALL return the requested name unchanged as its result.
5. The system SHALL continue to honor the `lang` and `use_l10n` parameters,
   including forcing localized or non-localized resolution when `use_l10n` is
   given, and defaulting the language to the active language when appropriate.
6. WHEN `get_format` returns a result derived from a lazy `format_type`, THEN the
   returned format value SHALL be a directly usable value of the same kind that
   would be returned for the equivalent concrete name (not a deferred proxy in
   place of the resolved format).

## Requirement 3: Lazy format names through the date/time formatting helpers and the date template filter

**User story:** As a template author, I want `some_date|date:_("...")` and the
underlying date/time formatting helpers to work with lazy format arguments, so
that translation-marked format strings render the same as plain ones.

**Acceptance criteria**
1. WHEN a date or time value is formatted via the module's date/time formatting
   helpers with a format argument that is a lazy string, THEN the helpers SHALL
   produce the same output they would produce for the equivalent concrete format
   string.
2. WHEN the `date` template filter in `django.template.defaultfilters` is applied
   with a lazy format argument (for example `_("H:i")`), THEN the rendered output
   SHALL equal the output produced by the equivalent concrete format argument.
3. WHEN a date or time value is rendered through the `date` filter with a lazy
   format argument, THEN the rendered output SHALL be a fully evaluated concrete
   string, character-for-character identical to the output produced by the
   equivalent concrete format argument, and SHALL NOT be an error, an empty
   result, or a lazy proxy standing in place of the rendered text.
4. The system SHALL keep the existing behavior of the `date` template filter for
   concrete-string and default (no-argument) format inputs unchanged, including
   its handling of empty/invalid values and escaped format characters.
