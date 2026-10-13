# Requirements: Recognize URL language prefixes that carry both a script and a region

## Introduction

Django resolves the language of a request in part from the leading component of
the URL path. When `i18n_patterns` is used, an incoming path such as
`/en-us/…` is inspected: its first path segment is treated as a candidate
language tag, and if that tag corresponds to a supported language the request is
served in that language. This resolution is implemented by
`get_language_from_path` in `django/utils/translation/trans_real.py`, which
extracts the leading tag with a module-level regular expression
(`language_code_prefix_re`) and then maps the extracted tag to a supported
language via `get_supported_language_variant` (which consults
`settings.LANGUAGES` and its generic-variant fallback logic).

The extraction pattern only admitted a primary subtag optionally followed by a
**single** additional subtag (for example a language plus a region, `de-at`).
Per RFC 5646 a language tag may be written as `language[-script][-region]` —
i.e. the language followed by **both** a script and a region subtag (for example
`en-latn-us` or, with mixed case, `en-Latn-US`). Because the extractor stopped
after one trailing subtag, such three-part tags in a URL prefix were not
recognized as language tags, so requests for those locales failed to resolve and
returned 404 even when the locale was listed in `settings.LANGUAGES`.

The goal is to make the leading-path language-tag extractor recognize a primary
subtag followed by **up to two** trailing subtags (script and region), so that
`language-script-region` prefixes resolve to their supported language, while
every existing resolution and non-resolution behavior (single-subtag tags,
generic-variant fallback, unsupported tags, over-long multi-segment path names,
and the i18n-disabled variants) is preserved.

## Requirement 1: Recognize language tags with both a script and a region subtag

**User story:** As a site operator whose supported languages include tags of the
form `language-script-region`, I want a URL whose leading path component is such
a tag to be recognized and served in that language, so that locales combining a
script and a region work with `i18n_patterns` just like simpler tags.

**Acceptance criteria**

1. WHEN `get_language_from_path` is given a path whose leading component is a
   well-formed tag consisting of a primary subtag followed by two further subtags
   (a script and a region, each introduced by a `-` separator) and that exact tag
   is a supported language, THEN it SHALL return that tag unchanged.
2. WHEN the leading three-part tag differs from a supported language only by
   letter case, THEN `get_language_from_path` SHALL still resolve it, returning
   the supported language whose value it matches (the match SHALL be
   case-insensitive, and the returned value SHALL be the supported code as it is
   listed, not a case-normalized form of the requested path).
3. WHEN a path's leading three-part tag is not itself a supported language but a
   more generic prefix of it (the primary-and-script portion, or the primary
   subtag alone) is supported, THEN `get_language_from_path` SHALL return that
   more generic supported language, applying the same generic-variant fallback
   used for shorter tags.
4. The extractor SHALL treat the candidate tag as terminated either by a `/`
   separator or by the end of the path, so that a path consisting only of a
   valid tag with no trailing slash resolves identically to the same tag followed
   by a trailing slash.

## Requirement 2: Do not over-match path components with more than two trailing subtags

**User story:** As a developer serving ordinary hyphenated URLs, I want a leading
path segment that contains more separator-delimited parts than a real language
tag to NOT be treated as a language tag, so that regular multi-word URLs are not
misinterpreted as locales.

**Acceptance criteria**

1. WHEN the leading path component consists of a primary subtag followed by
   **three or more** separator-introduced subtags (more parts than
   `language-script-region` allows), THEN `get_language_from_path` SHALL treat
   the path as carrying no valid language tag for the purpose of the leading
   extraction and SHALL return `None` unless a valid, shorter language prefix is
   nonetheless resolvable by the ordinary rules.
2. WHEN a request path's leading component is such an over-long hyphenated name
   that does not correspond to a supported language, THEN the request SHALL NOT
   be resolved to any language via the path prefix (the routing SHALL behave as
   though no language prefix were present).
3. WHEN `get_language_from_path` is given a leading component that is not a
   supported language and has no supported generic variant, THEN it SHALL return
   `None`.

## Requirement 3: Preserve existing language-from-path resolution (regression protection)

**User story:** As a maintainer, I want all previously working path-to-language
resolutions to keep working exactly as before, so that widening the accepted tag
shape does not change any established behavior.

**Acceptance criteria**

1. WHEN the leading path component is a supported bare primary subtag (no
   trailing subtags), THEN `get_language_from_path` SHALL return that language,
   both when the tag is followed by a trailing slash and when it is the entire
   path with no trailing slash.
2. WHEN the leading path component is a supported tag with exactly one trailing
   subtag (for example a language-and-region tag), THEN `get_language_from_path`
   SHALL return that tag unchanged.
3. WHEN the leading path component is a tag whose exact value is not supported but
   whose primary subtag is a supported language, THEN `get_language_from_path`
   SHALL fall back to and return that supported generic language.
4. WHEN the leading path component does not correspond to any supported language
   (neither exactly nor via a generic variant), THEN `get_language_from_path`
   SHALL return `None`.
5. The candidate-tag extraction SHALL accept a primary subtag followed by up to
   two trailing subtags, where each trailing subtag is composed of word
   characters and may be introduced by **either** a `-` separator **or** the
   `@`-modifier separator already accepted (the two trailing subtags need not use
   the same separator). The only change in the set of recognized leading
   components SHALL be the admission of a *second* such trailing subtag: a single
   trailing subtag introduced by either separator SHALL continue to be accepted
   exactly as before, and a second trailing subtag SHALL now likewise be accepted
   regardless of which of those two separators introduces it.

## Requirement 4: Preserve behavior when internationalization is disabled

**User story:** As a maintainer, I want the no-op internationalization code path
(used when translation is disabled) to keep its established behavior, so that the
change to path parsing does not affect the disabled configuration.

**Acceptance criteria**

1. WHEN internationalization is disabled and the disabled variant of
   `get_language_from_path` is called for any path, THEN it SHALL return `None`.
2. WHEN internationalization is disabled and the disabled variant of
   `get_supported_language_variant` is called with the configured
   `LANGUAGE_CODE`, THEN it SHALL return that same code.
3. IF internationalization is disabled and the disabled variant of
   `get_supported_language_variant` is called with any code other than the
   configured `LANGUAGE_CODE`, THEN it SHALL raise a `LookupError`.
