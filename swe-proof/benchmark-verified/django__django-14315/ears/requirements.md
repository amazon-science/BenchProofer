# Requirements: Database client shell must respect the ambient process environment

## Introduction

Django's database client shell support builds the argument list and an
environment mapping for the external client executable (for example, the
PostgreSQL `psql` shell), then launches it as a subprocess. The behavior lives
in two places:

- `django.db.backends.base.client.BaseDatabaseClient.runshell`, which takes the
  `(args, env)` produced by `settings_to_cmd_args_env` and invokes
  `subprocess.run`.
- `django.db.backends.postgresql.client.DatabaseClient.settings_to_cmd_args_env`,
  which assembles the connection-specific environment variables (e.g.
  `PGPASSWORD`, `PGSERVICE`, `PGSSLMODE`, `PGPASSFILE`) into an environment
  mapping.

A regression caused the client to spawn the subprocess with an **empty**
environment mapping when no connection-specific variables were required, instead
of letting the child inherit the ambient process environment (`os.environ`). As
a result, values a user placed in `os.environ` (such as a system `PGPASSWORD`,
`PATH`, or locale settings) were dropped, and the client ran with a stripped
environment.

The goal is to ensure that when there are no connection-specific environment
overrides, the subprocess inherits the ambient process environment; and when
there are overrides, they are layered on top of the ambient environment rather
than replacing it.

## Requirement 1: Inherit the ambient environment when there are no overrides

**User story:** As a developer opening a database shell, I want the client
subprocess to inherit my process environment when Django has no environment
overrides to add, so that variables I set in `os.environ` are honored.

**Acceptance criteria**

1. WHEN `runshell` obtains an environment value from
   `settings_to_cmd_args_env` that is absent (its Python truth value is false —
   i.e. `None` or an empty mapping), THEN `BaseDatabaseClient.runshell` SHALL
   invoke `subprocess.run` with its `env` argument set to `None`.
2. WHEN `runshell` invokes `subprocess.run` with `env` set to `None`, THEN the
   spawned client process SHALL inherit the ambient process environment
   (`os.environ`) rather than run with an empty or replaced environment.
3. The system SHALL treat an absent environment and a supplied-but-empty
   environment mapping identically for the purpose of deciding whether to pass
   `None` to the subprocess.
4. WHEN `runshell` is invoked, THEN it SHALL forward exactly the argument list
   returned by `settings_to_cmd_args_env` to `subprocess.run` and SHALL pass
   `check=True`.

## Requirement 2: Layer overrides on top of the ambient environment

**User story:** As a developer whose connection settings require environment
variables (such as a password or SSL options), I want those overrides applied
without discarding the rest of my environment, so that the client still sees
both my ambient variables and Django's overrides.

**Acceptance criteria**

1. WHEN `runshell` obtains a non-empty environment mapping from
   `settings_to_cmd_args_env`, THEN `BaseDatabaseClient.runshell` SHALL invoke
   `subprocess.run` with an environment consisting of the ambient process
   environment (`os.environ`) combined with that mapping.
2. WHILE combining the ambient environment with a non-empty override mapping,
   the system SHALL give the override mapping precedence for any variable name
   present in both.
3. IF the override mapping is non-empty, THEN the resolved environment passed to
   the subprocess SHALL NOT be `None`.

## Requirement 3: PostgreSQL client reports no environment when none is needed

**User story:** As a maintainer of the PostgreSQL client, I want
`settings_to_cmd_args_env` to signal "no overrides" distinctly from "an empty
set of overrides", so that downstream `runshell` correctly lets the child
inherit the ambient environment.

**Acceptance criteria**

1. WHEN `DatabaseClient.settings_to_cmd_args_env` assembles no
   connection-specific environment variables (none of password, service, SSL
   mode, SSL root cert, SSL cert, SSL key, or passfile are present), THEN it
   SHALL return `None` as the environment component of its `(args, env)` result.
2. WHEN at least one connection-specific environment variable is present, THEN
   `settings_to_cmd_args_env` SHALL return a non-empty mapping containing exactly
   those variables (and no others) as the environment component.
3. The system SHALL NOT return an empty mapping as the environment component;
   the absence of overrides SHALL be represented as `None`.

## Requirement 4: Preserve existing PostgreSQL argument and environment assembly

**User story:** As a user of the PostgreSQL database shell, I want all existing
argument- and environment-building behavior to remain unchanged, so that only
the empty-environment case is fixed.

**Acceptance criteria**

1. The system SHALL keep the executable name `psql` as the first element of the
   returned argument list.
2. WHEN a user, host, or port is configured, THEN `settings_to_cmd_args_env`
   SHALL include the corresponding `-U <user>`, `-h <host>`, and `-p <port>`
   options in the argument list, in that relative order.
3. WHEN a database name is configured, THEN it SHALL appear in the argument list;
   IF neither a database name nor a service is configured, THEN the system SHALL
   use the default database name `postgres`.
4. WHEN extra command parameters are supplied, THEN they SHALL be appended to the
   argument list after the connection arguments.
5. WHEN a password is configured, THEN the returned environment SHALL contain
   `PGPASSWORD` set to that password, and the password SHALL NOT appear in the
   argument list.
6. WHEN a service, SSL mode, SSL root cert, SSL cert, SSL key, or passfile is
   configured, THEN the returned environment SHALL contain the corresponding
   `PGSERVICE`, `PGSSLMODE`, `PGSSLROOTCERT`, `PGSSLCERT`, `PGSSLKEY`, or
   `PGPASSFILE` entry set to that value.
7. WHILE handling SIGINT during `runshell`, the PostgreSQL client SHALL ignore
   SIGINT for the duration of the child process and SHALL restore the original
   SIGINT handler afterward.

## Requirement 5: Preserve the base client abstract contract

**User story:** As a backend author, I want the base client to keep signalling
that `settings_to_cmd_args_env` is abstract, so that subclasses know they must
implement it.

**Acceptance criteria**

1. WHEN `BaseDatabaseClient.settings_to_cmd_args_env` is called directly without
   a subclass override, THEN it SHALL raise `NotImplementedError` with a message
   stating that subclasses must provide a `settings_to_cmd_args_env()` method or
   override `runshell()`.
