# Requirements: allow exiting `sphinx-quickstart` when an existing `conf.py` is found

## Introduction

`sphinx-quickstart` (module `sphinx/cmd/quickstart.py`) walks the user through
setting up a new Sphinx documentation project by asking a series of questions in
`ask_user`. Before collecting project details, it checks the selected root path
for an already-existing Sphinx project by testing for `conf.py` (directly in the
root path, or under a `source/` subdirectory). When one is found, the utility
refuses to overwrite it and re-prompts the user for a different root path, using
the message *"Please enter a new root path (or just Enter to exit)"*.

The bug: that prompt promises that pressing Enter (supplying an empty value)
will exit, but the prompt is wired to the ordinary existing-directory path
validator. That validator rejects the empty string as an invalid path name, so
the loop prints *"Please enter a valid path name."* and re-asks instead of
exiting. The user cannot leave the utility as the prompt advertises.

The goal is to make the empty entry at this re-prompt an accepted value so that
the surrounding flow can honour it and terminate the program, while every other
path prompt continues to demand a valid, existing directory. The affected code
is `ask_user`, the interactive prompt helper `do_prompt`, and the path
validation helpers (notably `is_path`) in `sphinx/cmd/quickstart.py`.

## Requirement 1: Allow leaving the re-prompt with an empty entry

**User story:** As a user who accidentally runs `sphinx-quickstart` in a folder
that already contains a Sphinx project, I want pressing Enter at the
"enter a new root path (or just Enter to exit)" prompt to leave the utility, so
that I can abort without being forced to type a bogus path.

**Acceptance criteria**

1. WHEN `ask_user` detects an existing `conf.py` in the selected root path (or
   in a `source/` subdirectory of it) and re-prompts for a new root path, THEN
   the value-validation applied to that re-prompt SHALL accept an empty entry
   and return it unchanged instead of raising a validation error.
2. IF the user supplies an empty entry at that re-prompt, THEN `ask_user` SHALL
   terminate the program by raising `SystemExit` with a non-zero (status `1`)
   exit code.
3. WHILE an existing `conf.py` remains detectable at the selected root path and
   the user has not supplied an empty entry, `ask_user` SHALL keep re-prompting
   for a new root path rather than continuing to the remaining questions.
4. WHEN a non-empty entry is supplied at that re-prompt, THEN the same
   existing-directory validation used for an ordinary root-path answer SHALL be
   applied to it: an entry naming an existing directory SHALL be accepted, and
   an entry not naming an existing directory SHALL be rejected with a validation
   error so the user is re-prompted.

## Requirement 2: Preserve strict validation for the initial root-path prompt

**User story:** As a user setting up a new project, I want the initial root-path
question to keep rejecting invalid paths, so that the project is created in a
real directory.

**Acceptance criteria**

1. WHEN `ask_user` asks for the root path for documentation and no value is
   pre-supplied, THEN it SHALL require the answer to name an existing directory,
   rejecting any entry that does not with the "valid path name" validation error.
2. The system SHALL continue to treat a bare Enter at the initial root-path
   prompt as selecting the offered default (the current directory), NOT as an
   empty/exit entry.

## Requirement 3: Preserve the interactive prompt helper behavior

**User story:** As a maintainer, I want the generic prompt helper `do_prompt`
to keep its existing input handling, so that fixing the exit behavior does not
regress other prompts.

**Acceptance criteria**

1. The system SHALL keep `do_prompt` stripping surrounding whitespace from the
   raw user input before validating it.
2. WHEN a default value is offered and the user enters an empty (or
   whitespace-only) response, THEN `do_prompt` SHALL substitute the default
   value.
3. WHEN a validator raises a validation error, THEN `do_prompt` SHALL report the
   error message and re-prompt rather than returning.
4. The system SHALL keep `do_prompt` returning the validated value, and SHALL
   preserve correct handling of non-ASCII input.

## Requirement 4: Preserve unrelated quickstart behavior

**User story:** As a maintainer, I want the rest of the quickstart flow to be
unchanged, so that generated projects and their configuration stay correct.

**Acceptance criteria**

1. The system SHALL continue to run the full quickstart flow to completion with
   default answers and with all answers supplied, producing the expected
   configuration and project files.
2. The system SHALL preserve the existing handling of the extensions setting,
   the source file suffix, the master/root document name, and the line-ending
   convention of generated files.
