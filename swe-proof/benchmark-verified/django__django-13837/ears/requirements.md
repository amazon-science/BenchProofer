# Requirements: Autoreload relaunch of any `python -m <pkg>` entry point

## Introduction

Django's development-server autoreloader relaunches the current interpreter
process when it needs to restart. The command line for that relaunch is built by
`get_child_arguments()` in `django/utils/autoreload.py`. When the program was
originally started with the interpreter's `-m` module-execution option
(`python -m <package> runserver`), the relaunch must re-invoke the *same*
module, otherwise the reloaded child runs a different program than the parent.

The existing logic only recognizes one specific case: the program launched as
`python -m django`. It does this by comparing the running script path
(`sys.argv[0]`) against `django.__main__.__file__`. That approach has two
problems: it hard-codes the package name `django`, so a Django-based
command-line tool launched as `python -m some_other_package runserver` is *not*
relaunched as a module; and it relies on `__file__` being set on the module,
which is not guaranteed in every Python environment.

The goal is to make `get_child_arguments()` detect module execution generally,
using the interpreter's own documented mechanism — the top-level `__main__`
module's import spec (`__main__.__spec__`) — so that autoreloading works for
*any* package launched with `-m`, while leaving every other launch mode
(direct script, Windows entry-point fallbacks, missing-script error) unchanged.

Affected module/function: `django.utils.autoreload.get_child_arguments` (and,
transitively, `restart_with_reloader`, which relaunches using its result).

## Requirement 1: Relaunch any module launched with `-m` by its package name

**User story:** As a developer building a Django-based command-line tool with
its own `__main__` submodule, I want the autoreloader to relaunch my program
with `python -m <my_package>`, so that the reloaded child process runs the same
entry point I started and my overrides of built-in management commands (such as
`runserver`) keep working after a reload.

**Acceptance criteria**

1. WHEN the program was started with the interpreter's `-m` option to run a
   package or module (so the top-level `__main__` module has a non-empty
   package/parent label available via its import spec, i.e.
   `__main__.__spec__` is not `None` and `__main__.__spec__.parent` is a
   non-empty string), THEN `get_child_arguments()` SHALL return an argument list
   whose tokens are the interpreter executable, followed by the warning-option
   tokens, followed by `-m` and that package/parent label, followed by the
   original trailing program arguments.
2. WHEN the launching package/parent label is a package other than `django`
   (for example a differently named package that provides its own `__main__`),
   THEN `get_child_arguments()` SHALL use that actual label as the `-m` argument
   and SHALL NOT substitute or hard-code the name `django`.
3. WHEN the launching package/parent label is exactly `django` (the program was
   started with `python -m django`), THEN `get_child_arguments()` SHALL return
   an argument list containing `-m` followed by `django`, followed by the
   original trailing program arguments — the historical behavior for this case
   is preserved.
4. WHEN a module launch is detected, THEN the trailing program arguments
   appended after `-m <label>` SHALL be exactly the original argument vector
   with its first element (the script/entry element) removed, in their original
   order, with no additions, omissions, or reordering.
5. The system SHALL determine whether the program was started with `-m` from
   the `__main__` module's import spec (`__main__.__spec__` / its `parent`),
   and SHALL NOT decide module-launch by comparing `sys.argv[0]` to any
   module's `__file__`.

## Requirement 2: Preserve the interpreter and warning-option prefix

**User story:** As a developer relying on the autoreloader, I want the relaunch
command to start with the same interpreter and the same warning options I ran
with, so that the child process behaves identically to the parent.

**Acceptance criteria**

1. The system SHALL begin every constructed relaunch argument list (in all
   branches that build one) with the current interpreter executable
   (`sys.executable`).
2. WHEN one or more Python warning options are active, THEN
   `get_child_arguments()` SHALL insert, immediately after the interpreter
   executable, one `-W<option>` token for each active warning option, in their
   original order, and SHALL preserve these tokens across all launch modes that
   build an argument list.
3. WHEN no warning options are active, THEN `get_child_arguments()` SHALL add no
   `-W` tokens.

## Requirement 3: Preserve non-module launch behavior (regression protection)

**User story:** As a maintainer, I want the change to affect only module-launch
detection, so that direct-script launches, Windows entry-point fallbacks, and
the missing-script error path continue to behave exactly as before.

**Acceptance criteria**

1. IF the program was not started as a module (no non-empty package/parent label
   is available from `__main__`'s import spec) and the running script path
   exists on disk, THEN `get_child_arguments()` SHALL return the interpreter
   executable and warning-option prefix followed by the original argument vector
   unchanged (a verbatim replay of the current arguments).
2. IF the program was not started as a module and the running script path does
   not exist on disk but an executable-suffixed entry point (the script path
   with an `.exe` suffix) does exist, THEN `get_child_arguments()` SHALL return
   that executable entry point followed by the original trailing program
   arguments, and SHALL NOT prepend the interpreter executable.
3. IF the program was not started as a module and the running script path does
   not exist on disk but a `<name>-script.py` sibling entry point exists, THEN
   `get_child_arguments()` SHALL return the interpreter and warning-option
   prefix, then that script entry point, then the original trailing program
   arguments.
4. IF the program was not started as a module and neither the running script
   path nor either fallback entry point exists, THEN `get_child_arguments()`
   SHALL raise a `RuntimeError` reporting that the script does not exist.
5. WHEN `restart_with_reloader()` relaunches the process, THEN it SHALL invoke
   the child using exactly the argument list produced by
   `get_child_arguments()` (for example, a program started with `python -m
   django` under an all-warnings option is relaunched with the interpreter,
   `-Wall`, `-m`, `django`, and the original trailing arguments).
