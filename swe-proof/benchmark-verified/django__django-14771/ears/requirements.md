# Requirements: Forward interpreter `-X` options across auto-reload restarts

## Introduction

Django's development server auto-reloader restarts the server in a child
process when source files change. To make the restart faithful, the reloader
reconstructs the command line originally used to launch the interpreter. This
reconstruction lives in `get_child_arguments()` in
`django/utils/autoreload.py`, which builds the argument vector later passed to
`subprocess.run(...)` by `restart_with_reloader()`.

Before this change the reconstructed command line preserved the interpreter
executable, the active warning (`-W`) options, and the original invocation
arguments — but it dropped any interpreter implementation options passed with
`-X` (for example `python -X utf8 manage.py runserver`). As a result, settings
established through `-X` (such as UTF-8 mode) silently reverted in the reloaded
child process, changing runtime behavior after the first reload.

The goal is for `get_child_arguments()` to additionally forward the active
interpreter `-X` options — as reported by `sys._xoptions` — when running on the
CPython implementation, while leaving every other part of the reconstructed
command line unchanged. `sys._xoptions` maps each active `-X` key to either the
boolean sentinel `True` (a flag-style option supplied as `-Xkey`) or a value
(an option supplied as `-Xkey=value`).

## Requirement 1: Forward active `-X` interpreter options on CPython

**User story:** As a developer running the dev server with `-X` interpreter
options (e.g. `-X utf8`), I want those options preserved when the auto-reloader
restarts the server, so that the child process behaves identically to the
process I launched.

**Acceptance criteria**

1. WHEN `get_child_arguments()` builds the child command line AND the running
   interpreter is the CPython implementation (as reported by
   `sys.implementation.name`), THEN `get_child_arguments()` SHALL include one
   command-line token for every active interpreter option reported by
   `sys._xoptions`.
2. IF an active `-X` option has the boolean sentinel value `True` (a flag-style
   option), THEN `get_child_arguments()` SHALL render it as a single token of
   the form `-X<key>` with no value component.
3. IF an active `-X` option has a non-sentinel value, THEN
   `get_child_arguments()` SHALL render it as a single token of the form
   `-X<key>=<value>`, joining the key and value with a single `=`.
4. The generated `-X` tokens SHALL appear in the same relative order as the
   corresponding entries reported by `sys._xoptions`.
5. WHEN the interpreter reports no active `-X` options, THEN
   `get_child_arguments()` SHALL add no `-X` tokens.
6. The `-X` tokens SHALL be placed after the warning (`-W`) tokens and before
   the reconstructed invocation arguments (the `-m <module>` block, a script
   entry point, or the original `sys.argv` entries), so that only the
   interpreter's own options precede the program arguments.

## Requirement 2: Restrict `-X` forwarding to CPython

**User story:** As a maintainer supporting non-CPython interpreters, I want the
`-X` forwarding to be gated on the interpreter implementation, so that
implementations without `sys._xoptions` semantics are unaffected.

**Acceptance criteria**

1. IF the running interpreter is not the CPython implementation (as reported by
   `sys.implementation.name`), THEN `get_child_arguments()` SHALL NOT add any
   `-X` tokens to the child command line, regardless of the contents of
   `sys._xoptions`.
2. WHEN the interpreter is not CPython, THEN the reconstructed command line
   SHALL be identical to what it would have been without the `-X` forwarding
   behavior.

## Requirement 3: Preserve the existing reconstructed command line

**User story:** As a developer relying on the auto-reloader, I want all
previously preserved parts of the command line to keep working exactly as
before, so that adding `-X` forwarding introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep the interpreter executable (`sys.executable`) as the
   first token of the reconstructed command line.
2. The system SHALL keep one `-W<option>` token for every active warning option
   (`sys.warnoptions`), in order, immediately following the executable and
   before any `-X` tokens.
3. WHEN the server was started with the `-m` module option (i.e. `__main__`
   exposes a `__spec__`), THEN `get_child_arguments()` SHALL keep reconstructing
   the command line as `-m <module-name>` followed by the original arguments
   (`sys.argv[1:]`), with the module name derived from the spec's parent package
   when the spec names the `__main__` module and otherwise from the spec name.
4. WHEN the server was started from a script that exists on disk, THEN
   `get_child_arguments()` SHALL keep appending the original `sys.argv` entries
   unchanged after the interpreter options.
5. IF the launching script path does not exist but a sibling `.exe` entry point
   exists, THEN `get_child_arguments()` SHALL keep returning that executable
   followed by the original arguments (`sys.argv[1:]`).
6. IF the launching script path does not exist but a sibling `-script.py` entry
   point exists, THEN `get_child_arguments()` SHALL keep returning the
   interpreter-option tokens followed by that script entry point and the
   original arguments.
7. IF the launching script path does not exist and no `.exe` or `-script.py`
   entry point can be found, THEN `get_child_arguments()` SHALL keep raising a
   runtime error reporting that the script does not exist.
