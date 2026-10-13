# Requirements — admindocs URL-pattern simplification of trailing capture groups

## Introduction

Django's admindocs helper turns a URL-pattern regular expression into a
human-readable path. The relevant helpers live in
`django/contrib/admindocs/utils.py`: `replace_named_groups(pattern)` replaces
each named capture group (e.g. `(?P<a>\w+)`) with `<a>`, `replace_unnamed_groups(pattern)`
replaces each unnamed capture group (e.g. `(\w+)`) with `<var>`, and
`simplify_regex(pattern)` (in `django/contrib/admindocs/views.py`) composes both
and then strips leftover regex metacharacters.

Each helper locates a capture group's opening parenthesis and then scans the
characters that follow it, tracking the parenthesis-nesting depth, to find the
group's matching closing parenthesis. The defect is that a group whose closing
parenthesis is the **last character of the pattern** (a pattern with no trailing
`/`, `$`, or other text after the group) is not detected, so that trailing group
is left unreplaced. For example,
`entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)` leaves
`(?P<related_field>\w+)` untouched instead of producing `related_field`'s
placeholder. The goal is to make the helpers detect and replace such trailing
groups while preserving all previously correct behavior.

## Requirement 1: Replace a trailing named group with no following characters

**User story:** As a developer viewing admindocs, I want a named capture group
that ends a URL pattern to be shown as its group-name placeholder, so that the
rendered path is fully readable even without a trailing slash.

**Acceptance criteria**
1. WHEN `replace_named_groups` is given a pattern in which a named capture group
   is closed by the final character of the pattern (nothing follows its closing
   parenthesis), THEN `replace_named_groups` SHALL replace that group's entire
   substring (from its opening parenthesis through its matching closing
   parenthesis) with `<groupname>`, where `groupname` is that group's name.
2. WHEN a pattern contains multiple named capture groups and the last one has no
   characters following its closing parenthesis, THEN `replace_named_groups`
   SHALL replace that final group in addition to all earlier named groups.
3. IF a named capture group's closing parenthesis is the final character of the
   pattern, THEN the substring chosen for replacement SHALL include that closing
   parenthesis and SHALL NOT include any characters preceding the group's opening
   parenthesis.

## Requirement 2: Replace a trailing unnamed group with no following characters

**User story:** As a developer viewing admindocs, I want an unnamed capture group
that ends a URL pattern to be shown as the generic placeholder, so that the
rendered path does not expose raw regex for the final segment.

**Acceptance criteria**
1. WHEN `replace_unnamed_groups` is given a pattern in which an unnamed capture
   group is closed by the final character of the pattern (nothing follows its
   closing parenthesis), THEN `replace_unnamed_groups` SHALL replace that group's
   entire substring (opening through matching closing parenthesis) with `<var>`.
2. WHEN a pattern contains a nested unnamed group whose outermost closing
   parenthesis is the final character of the pattern, THEN `replace_unnamed_groups`
   SHALL replace the whole outermost group (up to and including that final
   parenthesis) with a single `<var>` and SHALL NOT emit an additional `<var>`
   for the inner nested group.
3. The system SHALL compute the closing position of an unnamed group such that
   the replaced span ends exactly at the group's matching closing parenthesis,
   whether or not any characters follow it.

## Requirement 3: Preserve replacement of groups that are followed by other characters

**User story:** As a maintainer, I want patterns that already worked to keep
working, so that the fix for trailing groups introduces no regression.

**Acceptance criteria**
1. WHEN a named capture group is followed by additional characters (such as `/`,
   `$`, or literal text), THEN `replace_named_groups` SHALL continue to replace
   that group with `<groupname>` and SHALL leave the following characters intact.
2. WHEN an unnamed capture group is followed by additional characters, THEN
   `replace_unnamed_groups` SHALL continue to replace that group with `<var>` and
   SHALL leave the following characters intact.
3. WHEN a group is immediately followed by trailing literal text (for example a
   group followed by `ab`), THEN the helper SHALL replace only the group and
   SHALL retain that trailing literal text in the result.
4. The system SHALL correctly determine a group's closing parenthesis when the
   group contains nested parentheses (e.g. `((x|y)\w+)` or `(?P<a>(x|y))`),
   matching the depth-balanced closing parenthesis rather than the first
   parenthesis encountered.
5. The system SHALL treat an escaped parenthesis (a `(` or `)` immediately
   preceded by a backslash) as a literal character that does not open or close a
   group, so that escaped parentheses inside a group do not shift the detected
   closing position.

## Requirement 4: Preserve end-to-end simplification behavior

**User story:** As a developer, I want `simplify_regex` to render whole URL
patterns readably, so that admindocs output is correct for both trailing-group
and conventional patterns.

**Acceptance criteria**
1. WHEN `simplify_regex` is given a pattern whose final segment is a named or
   unnamed capture group with no trailing `/` or `$`, THEN `simplify_regex` SHALL
   return a path in which that final group is rendered as its placeholder
   (`<groupname>` for named, `<var>` for unnamed).
2. The system SHALL continue to strip leading `^`, trailing `$`, and `?`
   metacharacters and SHALL continue to guarantee the returned path begins with
   `/`.
3. WHEN a pattern already ends with a trailing `/` after its final group, THEN
   `simplify_regex` SHALL produce the same readable path it produced before this
   change (the trailing-group fix SHALL NOT alter results for patterns that
   already ended in a slash or metacharacter).
