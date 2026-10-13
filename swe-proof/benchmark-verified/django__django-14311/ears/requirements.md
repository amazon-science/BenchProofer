# Requirements: Correctly reconstruct the `-m` module name when autoreloading a server started with `python -m`

## Introduction

Django's development-server autoreloader restarts the running process when it
detects source changes. To do so it rebuilds the child command line in
`get_child_arguments()` in `django/utils/autoreload.py`. When the server was
launched with the interpreter's `-m` switch (`python -m <module>`), Python sets
`__main__.__spec__`, whose `name` and `parent` attributes describe how the
program was located. The autoreloader uses that spec to regenerate an equivalent
`-m <module>` invocation for the child process.

The original logic always rebuilt the command line from `__main__.__spec__.parent`
(the containing package). That is correct only when the program was started by
executing a *package* (`python -m pkg`, which runs `pkg/__main__.py` and whose
spec name is `pkg.__main__` with parent `pkg`). It is wrong when the program was
started by executing a *dotted module that is not a package* (`python -m
foo.bar.baz` where `baz` is a plain module `baz.py`): there the spec name is
`foo.bar.baz` and its parent is `foo.bar`, so rebuilding from the parent
produces `-m foo.bar` and silently drops the final component. It is also wrong
for a top-level single module (`python -m foo` where `foo.py` is a module), whose
spec has an empty parent, causing the `-m` reconstruction to be skipped entirely.

The goal is to reconstruct the child arguments so that the regenerated `-m`
target names the *same* module the process was originally launched with, for
packages, for arbitrarily deep dotted non-package modules, and for top-level
single modules — while preserving every existing behavior for the package case,
for processes not started with `-m`, and for the Windows/entry-point fallbacks.

## Requirement 1: Reconstruct the `-m` target from how the process was launched

**User story:** As a developer who runs a Django (or non-Django) management
process via `python -m <module>` and relies on the autoreloader, I want the
autoreloader to relaunch the child with the exact same `-m <module>` I used, so
that reloading works regardless of whether `<module>` is a package or a plain
dotted module.

**Acceptance criteria**

1. WHEN `get_child_arguments()` runs and `__main__` exposes a non-`None`
   `__spec__`, THEN the function SHALL reconstruct the child command as an `-m`
   invocation followed by the original command-line arguments after the program
   name (`sys.argv[1:]`).
2. WHEN the program was started by executing a package's `__main__` submodule —
   detected because `__main__.__spec__.name` is exactly `"__main__"` or ends with
   `".__main__"` — and that spec has a non-empty `parent`, THEN the reconstructed
   `-m` target SHALL be that `parent` package name.
3. WHEN the program was started by executing a dotted module that is not a
   package — detected because `__main__.__spec__.name` is neither exactly
   `"__main__"` nor ends with `".__main__"` — THEN the reconstructed `-m` target
   SHALL be the full `__main__.__spec__.name`, preserving every dotted component
   (for example, `foo.bar.baz` SHALL remain `foo.bar.baz` and SHALL NOT be
   reduced to `foo.bar`).
4. WHEN the process was started with `python -m` such that a spec is present but
   its `parent` is empty (a single top-level module), THEN the function SHALL
   still emit an `-m` invocation whose target is the spec's own name, and SHALL
   NOT fall through to the no-`-m` / script-path handling.
5. The reconstructed executable prefix SHALL remain the running interpreter
   (`sys.executable`) together with any active warning options, and the `-m`
   target and forwarded arguments SHALL be appended after that prefix.

## Requirement 2: Preserve the existing package launch and warning-option behavior

**User story:** As a maintainer, I want the existing, already-correct behaviors
for package launches, warning options, and interpreter selection to be
unchanged, so that fixing the dotted-module case introduces no regression.

**Acceptance criteria**

1. WHEN the server was started as `python -m <pkg>` where `<pkg>` is a package
   run through its `__main__` submodule, THEN the reconstructed child SHALL be
   `-m <pkg>` (the parent package), exactly as before this change.
2. WHILE the interpreter was launched with one or more warning options
   (`-W ...`), the reconstructed child arguments SHALL include an equivalent
   `-W` option for each active warning option, positioned before the `-m` target.
3. The forwarded arguments SHALL be exactly the original arguments following the
   program name, preserving their order and contents.

## Requirement 3: Preserve behavior when the process was not started with `-m`

**User story:** As a maintainer, I want processes that were not launched via
`-m`, and the Windows/entry-point fallbacks, to keep behaving as before, so that
the change is scoped strictly to the `-m` reconstruction.

**Acceptance criteria**

1. IF `__main__` has no `__spec__` (its `__spec__` attribute is absent or
   `None`), THEN `get_child_arguments()` SHALL NOT emit an `-m` invocation and
   SHALL instead use the non-`-m` argument-reconstruction path.
2. WHEN there is no usable spec and the original program file
   (`sys.argv[0]`) exists on disk, THEN the reconstructed child SHALL run the
   interpreter (with any warning options) against the original `sys.argv`.
3. WHEN there is no usable spec and the program file does not exist, THEN the
   function SHALL apply the existing Windows fallbacks: it SHALL run a sibling
   `.exe` entry point directly if one exists, otherwise run a sibling
   `<name>-script.py` under the interpreter if one exists, and otherwise SHALL
   raise a `RuntimeError` reporting that the script does not exist.
