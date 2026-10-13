# Requirements — MySQL backend should use non-deprecated connection kwargs

## Introduction

The MySQL database backend historically passed the database name and password to
the underlying `mysqlclient` driver, and derived the `mysql` command-line
database argument, using the driver's deprecated keyword names `db` and `passwd`.
The driver now marks those names as deprecated in favor of `database` and
`password`, which it has supported since the minimum version Django requires.

This change updates two collaborating pieces of the MySQL backend to prefer the
non-deprecated names while remaining backward compatible with configurations that
still supply the deprecated names:

- `django/db/backends/mysql/base.py` — `DatabaseWrapper.get_connection_params`,
  which builds the keyword-argument mapping handed to the `mysqlclient` connect
  call.
- `django/db/backends/mysql/client.py` — `DatabaseClient.settings_to_cmd_args_env`,
  which builds the argument vector and environment for launching the `mysql`
  command-line shell.

The goal is: emit the modern kwarg names for the driver connection, and let the
shell honor the modern `database` option key while still accepting the deprecated
`db` key, all without disturbing the existing handling of user, host/socket, port,
SSL, charset, password secrecy, and trailing parameters.

## Requirement 1: Connection kwargs use non-deprecated driver names

**User story:** As a Django developer connecting to MySQL, I want the backend to
pass the database name and password to the driver under its current keyword names,
so that I do not trigger deprecation warnings and remain compatible with future
driver releases.

**Acceptance criteria**
1. WHEN `get_connection_params` builds the connection keyword mapping and the
   configured `NAME` is a non-empty value, THEN the backend SHALL record that
   database name under the key `database` (and SHALL NOT record it under the
   deprecated key `db`).
2. WHEN `get_connection_params` builds the connection keyword mapping and the
   configured `PASSWORD` is a non-empty value, THEN the backend SHALL record that
   password under the key `password` (and SHALL NOT record it under the deprecated
   key `passwd`).
3. IF the configured `NAME` is empty or unset, THEN the backend SHALL NOT add any
   database-name entry to the connection keyword mapping.
4. IF the configured `PASSWORD` is empty or unset, THEN the backend SHALL NOT add
   any password entry to the connection keyword mapping.
5. The system SHALL continue to populate the remaining connection keyword entries
   (user, host or unix socket, port, and the other pre-existing entries) exactly as
   before, unchanged by this requirement.

## Requirement 2: Shell honors modern database option key with deprecated fallback

**User story:** As an operator running the database shell, I want the command to
target the correct database whether my `OPTIONS` use the modern `database` key or
the legacy `db` key, so that existing configurations keep working while new ones
use current names.

**Acceptance criteria**
1. WHEN `settings_to_cmd_args_env` determines the trailing database-name argument
   and the connection `OPTIONS` mapping contains the key `database`, THEN it SHALL
   use that option's value as the chosen database name, in preference to any `db`
   option or the configured `NAME`.
2. WHEN the `OPTIONS` mapping does not contain the key `database` but does contain
   the deprecated key `db`, THEN `settings_to_cmd_args_env` SHALL use the `db`
   option's value as the chosen database name, in preference to the configured
   `NAME`.
3. WHEN the `OPTIONS` mapping contains neither `database` nor `db`, THEN
   `settings_to_cmd_args_env` SHALL use the configured `NAME` as the chosen
   database name.
4. IF the `OPTIONS` mapping contains the key `database` with an empty value, THEN
   `settings_to_cmd_args_env` SHALL treat that empty value as the chosen database
   name and SHALL NOT fall back to `db` or `NAME` (selection is by key presence,
   not by truthiness of the option value).
5. WHEN the chosen database name is non-empty, THEN `settings_to_cmd_args_env`
   SHALL append it as the final database-name token of the argument vector,
   positioned after all option flags and before any explicitly supplied extra
   parameters.
6. IF the chosen database name is empty, THEN `settings_to_cmd_args_env` SHALL NOT
   append any database-name token to the argument vector.

## Requirement 3: Shell honors modern password option key with deprecated fallback

**User story:** As an operator running the database shell, I want the command to
authenticate with the right password whether my `OPTIONS` use the modern `password`
key or the legacy `passwd` key, so that both old and new configurations work.

**Acceptance criteria**
1. WHEN `settings_to_cmd_args_env` determines the password and the `OPTIONS`
   mapping contains the key `password`, THEN it SHALL use that option's value as
   the password, in preference to any `passwd` option or the configured `PASSWORD`.
2. WHEN the `OPTIONS` mapping does not contain `password` but does contain the
   deprecated key `passwd`, THEN `settings_to_cmd_args_env` SHALL use the `passwd`
   option's value, in preference to the configured `PASSWORD`.
3. WHEN the `OPTIONS` mapping contains neither `password` nor `passwd`, THEN
   `settings_to_cmd_args_env` SHALL use the configured `PASSWORD` as the password.

## Requirement 4: Preserve existing shell argument, environment, and error behavior

**User story:** As a Django maintainer, I want the surrounding behavior of the
shell-argument builder to remain intact, so that this change fixes only the kwarg
naming and nothing else regresses.

**Acceptance criteria**
1. WHEN a non-empty password is determined, THEN `settings_to_cmd_args_env` SHALL
   convey it through the process environment (as the MySQL password environment
   variable) and SHALL NOT place the password anywhere in the returned argument
   vector.
2. IF no non-empty password is determined, THEN `settings_to_cmd_args_env` SHALL
   return no password environment mapping.
3. The system SHALL continue to derive the user, host-versus-unix-socket, port,
   SSL certificate/key/CA, and default-character-set arguments from settings and
   `OPTIONS` with the same precedence and flag formatting as before this change.
4. WHEN extra parameters are supplied to `settings_to_cmd_args_env`, THEN it SHALL
   append them to the end of the argument vector, after the database-name token.
5. IF the settings mapping is missing a required top-level key needed to build the
   command, THEN `settings_to_cmd_args_env` SHALL fail rather than silently
   producing a command with missing information.
</content>
</invoke>
