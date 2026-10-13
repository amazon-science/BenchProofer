# Requirements: XDG-compliant persistent-data home for pylint

## Introduction

pylint stores per-run persistent data (pickled statistics) in a "home"
directory whose absolute path is exposed as the module-level constant
`PYLINT_HOME` in `pylint/config/__init__.py`. Historically this constant
defaulted to `~/.pylint.d`, placing an application data directory directly in
the user's home folder.

The goal is to make the default location compliant with the XDG Base Directory
Specification: instead of `~/.pylint.d`, the default persistent-data home
SHALL be the standard per-user, per-application cache directory for the
application named `pylint` (on Linux, this is `$XDG_CACHE_HOME/pylint`,
defaulting to `~/.cache/pylint`; other platforms resolve to their own
conventional per-application cache location). The existing explicit-override
behavior (the `PYLINTHOME` environment variable) and the degenerate
unresolvable-home behavior must be preserved unchanged, and downstream data
read/write helpers must continue to work relative to the resolved directory.

The affected code is the module-level initialization of `USER_HOME` and
`PYLINT_HOME` in `pylint/config/__init__.py`, and the helpers
`_get_pdata_path`, `load_results`, and `save_results` in the same module, which
consume `PYLINT_HOME`.

## Requirement 1: XDG-compliant default persistent-data home

**User story:** As a pylint user, I want pylint to store its persistent data in
the standard per-application cache directory rather than in a dotted directory
directly under my home folder, so that my home directory stays clean and
pylint follows the XDG Base Directory Specification.

**Acceptance criteria**

1. WHEN the `PYLINTHOME` environment variable is not set AND the user's home
   directory resolves to a concrete path, THEN the system SHALL set
   `config.PYLINT_HOME` to the standard per-user, per-application cache
   directory for the application named `pylint`.
2. The system SHALL resolve that per-application cache directory using the same
   platform conventions the XDG Base Directory Specification prescribes on
   platforms that use it (honoring `XDG_CACHE_HOME` when present and defaulting
   to `~/.cache/pylint` on Linux), so that the value is identical to what a
   standard per-application cache-directory resolver returns for the
   application name `pylint`.
3. The system SHALL NOT use `~/.pylint.d` (a `.pylint.d` directory located
   directly under the resolved user home) as the default persistent-data home
   in this case.

## Requirement 2: Preserve explicit-override behavior

**User story:** As a user who sets `PYLINTHOME`, I want my explicit choice to
keep taking precedence, so that I can control where pylint stores its data.

**Acceptance criteria**

1. WHEN the `PYLINTHOME` environment variable is set, THEN the system SHALL set
   `config.PYLINT_HOME` to that environment variable's value verbatim,
   regardless of the resolved user home or the XDG cache location.
2. IF the `PYLINTHOME` environment variable is set AND the user's home
   directory cannot be resolved (i.e. it expands to the literal `"~"`), THEN
   the system SHALL set `USER_HOME` to the directory portion (parent
   directory) of the `PYLINTHOME` value.
3. WHEN the module is reloaded after `PYLINTHOME` has been set to a given path,
   THEN `config.PYLINT_HOME` SHALL equal that path.

## Requirement 3: Preserve unresolvable-home fallback

**User story:** As a user whose home directory cannot be resolved, I want
pylint to keep working with its historical relative fallback, so that behavior
does not regress on such systems.

**Acceptance criteria**

1. WHEN the `PYLINTHOME` environment variable is not set AND the user's home
   directory cannot be resolved (i.e. it expands to the literal `"~"`), THEN
   the system SHALL set `config.PYLINT_HOME` to the bare relative directory
   name `.pylint.d`.

## Requirement 4: Migration notice for the obsolete location

**User story:** As a user upgrading pylint, I want to be told that my old data
directory is no longer used, so that I can clean it up.

**Acceptance criteria**

1. WHEN the default XDG-compliant persistent-data home is selected (per
   Requirement 1) AND a directory named `.pylint.d` still exists directly under
   the resolved user home, THEN the system SHALL emit an informational message
   to standard error indicating that the persistent-data home has moved to the
   new location and that the old `.pylint.d` directory can be safely removed.
2. WHILE no such obsolete `.pylint.d` directory exists under the resolved user
   home, the system SHALL NOT emit that message.

## Requirement 5: Keep persistent-data read/write working relative to the home

**User story:** As a pylint maintainer, I want the statistics read/write
helpers to keep operating relative to whatever `PYLINT_HOME` resolves to, so
that changing the default location does not break persistence.

**Acceptance criteria**

1. The system SHALL compute the path of a persistent-data file by joining the
   resolved `PYLINT_HOME` directory with a file name derived from the given
   base name (with path separators in the base name replaced) and the given
   recursion marker, keeping the `.stats` suffix.
2. WHEN results are saved AND the resolved `PYLINT_HOME` directory does not yet
   exist, THEN the system SHALL attempt to create it before writing.
3. The system SHALL continue to load previously saved results from, and save
   results to, files located under the resolved `PYLINT_HOME` directory.
