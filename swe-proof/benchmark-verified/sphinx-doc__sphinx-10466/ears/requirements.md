# Requirements: De-duplicate and order message locations in the gettext catalog

## Introduction

When Sphinx builds gettext output (the `gettext` builder), it collects every
translatable message together with the source positions where that message
occurs. This collection is managed by the `Catalog` class in
`sphinx/builders/gettext.py`. Each time a message is encountered, an origin
`(source, line, identifier)` triple is recorded via `Catalog.add`. When the
catalog is iterated (`Catalog.__iter__`), it emits a `Message` object per
distinct message text, whose `locations` attribute is the list of
`(source, line)` positions for that message.

The defect: because the same message can be recorded at the identical source
and line multiple times (e.g. different index/uid entries at the same
position), the emitted `locations` list contained repeated `(source, line)`
pairs, which then surfaced as duplicated location comments in the generated
`.pot` output. The positions were also emitted in raw recording order.

The goal is that the positions reported for each message are exactly the
*distinct* recorded positions, presented in a deterministic ascending order,
while the message set, per-message identifier list, and the rest of the
gettext build behavior remain unchanged.

## Requirement 1: Report each occurrence position at most once

**User story:** As a documentation translator, I want each source location for
a message to appear only once, so that the generated message catalog is not
cluttered with duplicated location comments.

**Acceptance criteria**

1. WHEN a message is recorded multiple times with the same source path and the
   same line number, THEN the `Message` produced for that message by iterating
   the `Catalog` SHALL include that `(source, line)` position exactly once in
   its `locations`.
2. WHEN a message has been recorded at several positions where some positions
   are identical and others differ, THEN the resulting `locations` SHALL
   contain each distinct `(source, line)` pair exactly once and SHALL omit no
   distinct pair that was recorded.
3. The system SHALL treat two positions as identical only when both the source
   path and the line number are equal; positions that differ in either the
   source path or the line number SHALL each be reported.

## Requirement 2: Report positions in deterministic ascending order

**User story:** As a maintainer of translated documentation, I want message
locations emitted in a stable, predictable order, so that catalog output is
reproducible regardless of the order in which occurrences were recorded.

**Acceptance criteria**

1. WHEN a `Message` is produced by iterating the `Catalog`, THEN its
   `locations` SHALL be ordered ascending, comparing first by source path and,
   for equal source paths, by line number.
2. IF the same set of positions is recorded in different insertion orders,
   THEN the resulting `locations` list SHALL be identical in both cases.
3. The system SHALL produce `locations` that are strictly increasing under the
   above ordering (a direct consequence of ordering ascending and reporting
   each distinct position once).

## Requirement 3: Preserve message set and message iteration order

**User story:** As a Sphinx user, I want the set of collected messages and
their emitted order to be unaffected by the location handling, so that existing
gettext output ordering is preserved.

**Acceptance criteria**

1. WHEN the `Catalog` is iterated, THEN it SHALL yield exactly one `Message`
   per distinct message text that was added, and no others.
2. The system SHALL yield messages in the order in which each distinct message
   text was first recorded.
3. WHEN a message text has been recorded, THEN the `text` attribute of its
   emitted `Message` SHALL equal that recorded text.

## Requirement 4: Preserve per-occurrence identifier list

**User story:** As a developer relying on message uid tracking, I want the
per-message list of occurrence identifiers to remain complete, so that features
depending on it continue to work.

**Acceptance criteria**

1. WHEN a `Message` is produced, THEN its `uuids` attribute SHALL contain one
   identifier entry for every recorded occurrence of that message text,
   including entries for occurrences that share a source path and line number
   with another occurrence.
2. The system SHALL NOT de-duplicate or reorder the identifier list; the
   de-duplication and ordering behavior SHALL apply only to the reported
   `(source, line)` positions.

## Requirement 5: Preserve the recording API and overall gettext build

**User story:** As a Sphinx user building gettext output, I want a normal
documentation build to continue producing correct catalog files, so that the
fix does not regress existing behavior.

**Acceptance criteria**

1. The system SHALL keep `Catalog.add` recording a message occurrence from an
   origin object exposing `source`, `line`, and a uid, and SHALL keep ignoring
   origins that carry no uid.
2. The system SHALL keep producing a well-formed gettext catalog for a normal
   documentation build, including index entries, template-derived messages,
   and single-catalog output, with message ordering unchanged from prior
   behavior.
3. WHEN the gettext builder emits its `.pot` output, THEN each message's
   location comments SHALL reflect the de-duplicated, ascending positions
   described in Requirements 1 and 2.
