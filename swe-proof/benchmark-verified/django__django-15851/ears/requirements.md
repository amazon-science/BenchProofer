# Requirements: PostgreSQL dbshell argument ordering

## Introduction

When a user opens an interactive PostgreSQL shell through Django's management
tooling (`./manage.py dbshell`), Django builds the command-line argument vector
that is handed to the `psql` client program. This behavior lives in
`django/db/backends/postgresql/client.py`, in the
`DatabaseClient.settings_to_cmd_args_env` classmethod, which translates a
connection settings dictionary plus any caller-supplied extra parameters into
the `(args, env)` pair used to launch `psql`.

The `psql` client requires that all options appear **before** the database name
on the command line. Once `psql` encounters the database name (a positional
argument), it treats any subsequent tokens as extra positional arguments and
ignores them (emitting `extra command-line argument ... ignored` warnings).
Previously Django appended the caller-supplied extra parameters (for example the
arguments following `--` on the `dbshell` command line, such as
`-c "select ..."`) *after* the database name, so those parameters were silently
dropped by `psql`.

The goal is to construct the argument vector so that the caller-supplied extra
parameters precede the database name, while preserving all existing ordering and
environment-variable behavior for connection options, credentials, and SSL
settings.

## Requirement 1: Extra parameters precede the database name

**User story:** As a developer running `./manage.py dbshell -- <extra args>`, I
want the extra arguments I pass to reach `psql` intact, so that options like
`-c "select ..."` are honored instead of being ignored.

**Acceptance criteria**

1. WHEN `settings_to_cmd_args_env` is called with a non-empty sequence of extra
   parameters and a connection settings dictionary that carries a database name,
   THEN the returned argument list SHALL place all of the extra parameters
   before the database name.
2. WHEN extra parameters and a database name are both present, THEN the returned
   argument list SHALL contain the extra parameters in their original given
   order, immediately followed by the database name as the final element.
3. WHEN extra parameters are supplied, THEN `settings_to_cmd_args_env` SHALL
   preserve every supplied parameter in the returned argument list (none are
   dropped, duplicated, or reordered relative to each other).
4. The system SHALL emit the database name (when present) as the last element of
   the returned argument list.

## Requirement 2: Program name and connection options ordering

**User story:** As a Django maintainer, I want the connection flags to keep
their established position, so that existing dbshell invocations continue to
work.

**Acceptance criteria**

1. The system SHALL emit the client program name (`psql`) as the first element
   of the returned argument list.
2. WHEN the connection settings carry a user value, THEN the returned argument
   list SHALL include the `-U` flag immediately followed by the user value,
   positioned before the extra parameters and the database name.
3. WHEN the connection settings carry a host value, THEN the returned argument
   list SHALL include the `-h` flag immediately followed by the host value,
   positioned before the extra parameters and the database name.
4. WHEN the connection settings carry a port value, THEN the returned argument
   list SHALL include the `-p` flag immediately followed by the port value
   rendered as a string, positioned before the extra parameters and the database
   name.
5. The system SHALL order the emitted connection options as program name, then
   user option, then host option, then port option, then the extra parameters,
   then the database name.
6. IF a given connection setting (user, host, or port) carries no value, THEN
   the returned argument list SHALL omit that setting's flag and value entirely.

## Requirement 3: Default database name behavior

**User story:** As a developer, I want a sensible default database connection
when no name or service is configured, so that dbshell still connects.

**Acceptance criteria**

1. IF neither a database name nor a service is configured, THEN
   `settings_to_cmd_args_env` SHALL use `"postgres"` as the database name in the
   returned argument list.
2. WHEN a database name is configured, THEN the returned argument list SHALL use
   that configured name, still positioned after any extra parameters.

## Requirement 4: Environment variables for credentials and SSL (kept behavior)

**User story:** As a Django user, I want credentials and SSL configuration to be
passed to `psql` via environment variables exactly as before, so that
authentication and secure connections keep working.

**Acceptance criteria**

1. WHEN a password is configured, THEN `settings_to_cmd_args_env` SHALL return an
   environment mapping containing `PGPASSWORD` set to the password value, and
   SHALL NOT place the password anywhere in the argument list.
2. WHEN a service option is configured, THEN the returned environment mapping
   SHALL contain `PGSERVICE` set to that service value.
3. WHEN a passfile option is configured, THEN the returned environment mapping
   SHALL contain `PGPASSFILE` set to that passfile value.
4. WHEN any of the sslmode, sslrootcert, sslcert, or sslkey options are
   configured, THEN the returned environment mapping SHALL contain the
   corresponding `PGSSLMODE`, `PGSSLROOTCERT`, `PGSSLCERT`, or `PGSSLKEY` entry
   set to that value.
5. IF none of the credential or SSL environment values are configured, THEN
   `settings_to_cmd_args_env` SHALL return `None` in place of an environment
   mapping.
6. The system SHALL keep credential and SSL values out of the returned argument
   list under all configurations.
