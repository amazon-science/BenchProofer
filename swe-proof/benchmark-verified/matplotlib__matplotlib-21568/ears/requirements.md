# Requirements: TeX-mode spacing of date/time tick labels

## Introduction

When matplotlib renders date and time axis tick labels with TeX math mode
enabled (`text.usetex = True`, or a formatter constructed with `usetex=True`),
each formatted label string is transformed into a math-mode fragment before it
is drawn. This transformation lives in the date-formatting helper of
`matplotlib.dates` (the routine that wraps a formatted date string in TeX math
mode) and is used by both `matplotlib.dates.DateFormatter` and
`matplotlib.dates.ConciseDateFormatter` (including its offset string).

Following a regression in the 3.4 series, the spacing of these labels became
unclear: numeric groups separated by spaces were run together, and the colon in
time-of-day labels (e.g. `08:00`) was typeset with the wide spacing TeX applies
to binary operators, unlike in 3.3. The goal is to restore clear, 3.3-style
spacing by rewriting the problematic symbols inside the math group while keeping
the existing correct behavior for alphabetic runs, dashes, digits, and empty
labels. This document specifies the exact string a formatted label must be
transformed into, so the visual spacing is well defined.

Throughout, "the math-wrapping transform" means the helper in
`matplotlib.dates` that converts a plain formatted date/time string into its
TeX math-mode representation, and "math group" means a `$\mathdefault{...}$`
region.

## Requirement 1: Colons must not be spaced as binary operators

**User story:** As a user plotting a datetime axis with TeX enabled, I want the
colon in time labels to render with tight, natural spacing, so that times such
as `08:00` read as a single clock time rather than an arithmetic expression.

**Acceptance criteria**
1. WHEN the math-wrapping transform processes a formatted string that contains
   one or more colon (`:`) characters, THEN the transform SHALL replace every
   colon with the three-character sequence consisting of an opening brace, the
   colon, and a closing brace, so that each colon is enclosed in its own brace
   group within the math fragment.
2. The system SHALL apply this colon rewrite to every colon in the string, not
   only the first.
3. IF a formatted string contains no colon, THEN the transform SHALL leave the
   string unchanged with respect to colons.

## Requirement 2: Spaces between fields must be preserved as thin spaces

**User story:** As a user plotting a datetime axis with TeX enabled, I want
space-separated fields of a label (for example a day and a time, or a month and
a day) to keep visible separation, so that adjacent numbers are not concatenated
into an unreadable run.

**Acceptance criteria**
1. WHEN the math-wrapping transform processes a formatted string that contains
   one or more space (` `) characters that fall inside a math group, THEN the
   transform SHALL replace each such space with the TeX thin-space command
   (a backslash followed by a semicolon) so that the numbers on either side
   remain visually separated rather than concatenated.
2. The system SHALL apply this space rewrite to every applicable space in the
   string, not only the first.

## Requirement 3: Dashes must remain braced (kept behavior)

**User story:** As a maintainer, I want the existing correct handling of dashes
to be preserved, so that fixing colon and space spacing does not regress
date labels such as `1990-01-05`.

**Acceptance criteria**
1. WHEN the math-wrapping transform processes a formatted string containing one
   or more hyphen/dash (`-`) characters, THEN the transform SHALL replace every
   dash with the three-character sequence consisting of an opening brace, the
   dash, and a closing brace, so that dashes are not spaced like binary
   operators.
2. The system SHALL keep this behavior for every dash in the string.

## Requirement 4: Alphabetic runs remain upright text outside the math group

**User story:** As a user, I want month abbreviations and other letter runs to
render as upright text, so that labels like `Jan` are not italicized as math
variables.

**Acceptance criteria**
1. WHEN the math-wrapping transform processes a formatted string containing a
   maximal run of ASCII letters, THEN the transform SHALL lift that letter run
   out of the surrounding math group: it SHALL close the current math group,
   emit the letter run verbatim as ordinary (non-math) text, and open a fresh
   math group immediately after the run.
2. The system SHALL treat digits and any characters other than letters, dashes,
   colons, and spaces as ordinary content that passes through unchanged (aside
   from the group boundaries introduced by adjacent letter runs and the
   symbol rewrites above).
3. WHEN a label begins with a letter run (for example a leading month
   abbreviation), THEN the transform SHALL emit that run as leading upright text
   preceding the math group, and SHALL NOT leave an empty math group before it.

## Requirement 5: Outer math wrapping and empty-group removal

**User story:** As a user, I want the overall label to be valid, minimal TeX
math markup, so that rendering succeeds and no stray empty groups appear.

**Acceptance criteria**
1. The system SHALL enclose the transformed content in a single outer math
   group, i.e. the numeric/symbol content SHALL be surrounded by an opening
   `$\mathdefault{` and a closing `}$`.
2. WHEN the resulting string contains an empty math group (an opening
   `$\mathdefault{` immediately followed by its closing `}$` with nothing
   between them), THEN the transform SHALL remove every such empty math group
   from the result.
3. WHEN the input string is empty, THEN the transform SHALL produce an empty
   string (no leftover empty math group).
4. The composition of the symbol rewrites (Requirements 1–3), the letter-run
   lifting (Requirement 4), the outer wrapping, and the empty-group removal
   SHALL be deterministic: for a given input string the transform SHALL always
   produce the same output string, with every input character's contribution to
   the output fixed.

## Requirement 6: TeX transform is applied exactly when TeX mode is active

**User story:** As a user, I want the TeX rewriting to happen only when TeX math
mode is enabled, so that non-TeX rendering is unaffected.

**Acceptance criteria**
1. WHEN a date formatter (`DateFormatter`) formats a value while its TeX mode is
   active, THEN it SHALL return the math-wrapping transform of the
   `strftime`-formatted string; WHILE TeX mode is inactive it SHALL return the
   plain formatted string unchanged.
2. WHEN a concise date formatter (`ConciseDateFormatter`) produces its list of
   tick labels while its TeX mode is active, THEN it SHALL apply the
   math-wrapping transform to each label, and, when an offset string is shown,
   SHALL apply the same transform to the offset string.
3. The system SHALL keep all existing non-TeX date-formatting, locating, and
   conversion behavior unchanged (regression protection): date-to-number and
   number-to-date conversions, tick locators, concise formatting, offset
   display, and format-string handling SHALL continue to behave as before when
   TeX mode is not involved.
