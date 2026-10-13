# Requirements: Absent optional named groups must not corrupt URL resolution and reversal

## Introduction

Django resolves an incoming URL path by searching it against a compiled URL
pattern. For regex-based patterns this happens in `RegexPattern.match` in
`django/urls/resolvers.py`. On a successful search the method returns a triple of
the leftover path, the positional captures, and the named captures (the keyword
arguments) that downstream machinery — `resolve()`, `reverse()`, and
`translate_url()` in `django/urls/base.py` — consumes.

A URL pattern may contain an **optional** named group (for example a segment that
may or may not be present, written with `(?:(?P<name>...)...)?`). When such a
group does not participate in a match, Python's regular-expression machinery
reports that group in `re.Match.groupdict()` with the value `None`. Historically
`RegexPattern.match` copied the whole `groupdict()` verbatim into the keyword
arguments, so an absent optional named group was carried through as a keyword
argument whose value is `None`.

That produced two defects. First, when the resolved match is fed back into
`reverse()` (as `translate_url()` does when switching a page's language), the
`None` value is coerced to the literal string `"None"`, so the rebuilt URL is
wrong and the translated page 404s. Second, because the keyword-argument mapping
was non-empty even when every named value was absent, the positional-capture
fallback was suppressed even though no usable named capture existed.

The goal is to make `RegexPattern.match` omit any named group that did not
participate in the match (whose captured value is `None`) from the keyword
arguments it returns, so that resolution and reversal stay symmetric for patterns
with missing optional named groups, while every existing behavior for present
captures, positional captures, and non-matching paths is preserved.

## Requirement 1: Omit absent optional named captures from resolved keyword arguments

**User story:** As a developer whose URL pattern declares an optional named group,
I want resolving a URL in which that group is absent to yield keyword arguments
that do not mention the missing group, so that the resolved arguments describe
only the captures that actually occurred.

**Acceptance criteria**

1. WHEN a regex URL pattern is searched against a path and the search succeeds,
   THEN `RegexPattern.match` SHALL return the keyword-argument mapping containing
   exactly those named groups whose captured value is not `None` (the groups that
   participated in the match), and SHALL exclude every named group whose captured
   value is `None`.
2. WHEN a pattern contains an optional named group and the matched path does not
   supply that group, THEN the returned keyword-argument mapping SHALL NOT contain
   any entry for that group (neither the group's name mapped to `None` nor to any
   placeholder).
3. WHEN a pattern contains an optional named group and the matched path does
   supply that group, THEN the returned keyword-argument mapping SHALL contain
   that group's name mapped to its captured text.
4. WHEN resolving a path against a pattern that has one required named group and
   one optional named group, and the optional group is absent, THEN the resolved
   match's keyword arguments SHALL contain only the required group; and WHEN both
   groups are present, THEN the resolved match's keyword arguments SHALL contain
   both.

## Requirement 2: Fall back to positional captures only when no named capture remains

**User story:** As a developer, I want a pattern whose only named groups are
optional and all absent to still expose its positional captures, so that a match
that yields no usable keyword arguments is not left with empty arguments.

**Acceptance criteria**

1. WHEN a search succeeds and, after absent named groups are omitted, at least one
   named capture remains, THEN `RegexPattern.match` SHALL return that
   keyword-argument mapping and SHALL return an empty positional-argument tuple.
2. WHEN a search succeeds and, after absent named groups are omitted, no named
   capture remains, THEN `RegexPattern.match` SHALL return an empty
   keyword-argument mapping and SHALL return the pattern's positional captures as
   the positional-argument tuple.
3. The choice between reporting positional captures and reporting keyword
   arguments SHALL depend only on whether any named capture with a non-`None`
   value survived, never on whether the raw named-group dictionary was non-empty
   before absent groups were removed.

## Requirement 3: Preserve leftover path and non-matching behavior (regression protection)

**User story:** As a maintainer, I want the remaining outputs of pattern matching
and the no-match case to behave exactly as before, so that removing absent named
captures changes nothing else.

**Acceptance criteria**

1. WHEN a search against a path succeeds, THEN `RegexPattern.match` SHALL return
   the leftover path — the portion of the path beyond the end of the matched
   prefix — unchanged from prior behavior, alongside the arguments and keyword
   arguments.
2. IF the search against a path does not succeed, THEN `RegexPattern.match` SHALL
   return no match result (a `None`), exactly as before.
3. WHEN a path is resolved against a pattern whose named groups all participate in
   the match, THEN the resolved keyword arguments and the resolved route SHALL be
   identical to prior behavior (every present named capture is reported with its
   value).

## Requirement 4: Keep resolve and reverse symmetric for missing optional groups

**User story:** As a user switching a page's language, I want translating a URL
that contains an absent optional named group to produce the correctly translated
URL rather than a broken one, so that language switching does not 404 on such
pages.

**Acceptance criteria**

1. WHEN `translate_url()` is given a URL that resolves against a pattern with an
   absent optional named group, THEN it SHALL reverse the resolved view using only
   the captures that actually occurred and SHALL produce a translated URL that
   contains no literal `"None"` text introduced by the missing group.
2. WHEN `translate_url()` is given such a URL and a target language, THEN the
   returned URL SHALL be the target-language equivalent of the input URL,
   preserving the present captured segment(s) and the URL's structure (path,
   query, and fragment).
3. WHEN `translate_url()` is given a URL whose optional named group is present,
   THEN the returned URL SHALL still be correctly translated with that captured
   segment retained.
4. The system SHALL keep `translate_url()` returning correctly translated URLs for
   patterns that have no optional named groups (fixed routes and routes with
   required captures), so that existing translation behavior is unaffected.
