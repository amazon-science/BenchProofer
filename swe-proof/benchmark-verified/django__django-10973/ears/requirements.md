# Requirements: PostgreSQL dbshell client password handling

## Introduction

The PostgreSQL database backend launches the interactive `psql` client from
`django.db.backends.postgresql.client` (the `DatabaseClient.runshell_db`
classmethod). Historically the client made the connection password available to
`psql` by writing a temporary PostgreSQL password file and pointing the
`PGPASSFILE` environment variable at it, which required escaping colons and
backslashes for the password-file format and cleaning up the temporary file and
the global environment variable afterwards.

The goal is to make the password available to the `psql` child process directly
through the `PGPASSWORD` environment variable of the child process's
environment, without creating any temporary file and without applying any
password-file escaping. The command-line argument vector passed to `psql` and
the SIGINT-handling behavior around the child process must be preserved. This
document specifies the observable behavior of `runshell_db` in behavioral terms
so an implementing agent can locate and correct the code in
`django/db/backends/postgresql/client.py`.

Throughout, "connection parameters" refers to the mapping passed to
`runshell_db` (as produced by the connection's `get_connection_params`), whose
relevant keys are `host`, `port`, `database`, `user`, and `password`. A value is
"supplied" when it is present and non-empty; otherwise it is "absent".

## Requirement 1: Construct the psql command-line argument vector

**User story:** As a developer running `dbshell` against a PostgreSQL database,
I want the client to be invoked with exactly the right positional and option
arguments, so that the correct database and role are selected.

**Acceptance criteria**

1. The system SHALL invoke the client program whose executable name is `psql`,
   passing that executable name as the first element of the argument vector.
2. WHEN the `user` connection parameter is supplied, THEN `runshell_db` SHALL
   append the option flag `-U` immediately followed by the user value to the
   argument vector.
3. IF the `user` connection parameter is absent, THEN `runshell_db` SHALL append
   neither `-U` nor a user value.
4. WHEN the `host` connection parameter is supplied, THEN `runshell_db` SHALL
   append the option flag `-h` immediately followed by the host value.
5. IF the `host` connection parameter is absent, THEN `runshell_db` SHALL append
   neither `-h` nor a host value.
6. WHEN the `port` connection parameter is supplied, THEN `runshell_db` SHALL
   append the option flag `-p` immediately followed by the port value rendered
   as a string.
7. IF the `port` connection parameter is absent, THEN `runshell_db` SHALL append
   neither `-p` nor a port value.
8. The system SHALL append the database name (the `database` connection
   parameter, or an empty string when absent) as the final element of the
   argument vector, unconditionally.
9. The system SHALL order the argument vector exactly as: the executable name,
   then the user flag-and-value (if any), then the host flag-and-value (if any),
   then the port flag-and-value (if any), then the database name.
10. The system SHALL pass user, host, and database values into the argument
    vector verbatim, applying no escaping, quoting, or transformation to them
    (for example, a value containing a colon, or one containing a backslash,
    appears unchanged, including cases where the value consists solely of such
    characters).
11. The system SHALL keep the argument vector independent of the password: the
    presence, absence, or content of the password SHALL NOT change any element
    of the argument vector.

## Requirement 2: Provide the password to the child process via its environment

**User story:** As a developer, I want the password delivered to `psql` through
the `PGPASSWORD` environment variable of the spawned process, so that
authentication succeeds without a temporary password file.

**Acceptance criteria**

1. WHEN a password is supplied, THEN `runshell_db` SHALL run the client with a
   child-process environment in which the `PGPASSWORD` variable is set to the
   supplied password value.
2. The system SHALL set `PGPASSWORD` to the password value verbatim, applying no
   escaping, quoting, or colon/backslash transformation (for example, a password
   containing a colon is delivered with the colon intact, and a password
   containing non-ASCII/accented characters is delivered unchanged).
3. IF no password is supplied, THEN `runshell_db` SHALL NOT define `PGPASSWORD`
   in the child-process environment (its value, as seen by the child, is absent).
4. The child-process environment SHALL otherwise be a copy of the current
   process environment, so that variables other than `PGPASSWORD` remain
   available to the client.
5. The system SHALL make the password available only through the child-process
   environment; it SHALL NOT create a temporary password file nor rely on a
   password-file mechanism to convey the password.
6. The system SHALL NOT mutate the current process's own environment as a means
   of passing the password (the calling process's environment is left as it was
   with respect to password-related variables).

## Requirement 3: Preserve SIGINT handling around the client process

**User story:** As a developer, I want Ctrl-C to abort a running query in `psql`
rather than kill the parent, and I want normal signal handling restored
afterward, so that interactive use is safe and repeatable.

**Acceptance criteria**

1. WHILE the client process is being launched, `runshell_db` SHALL cause SIGINT
   to be ignored in the parent Python process (so the interrupt is passed
   through to `psql` to abort queries).
2. WHEN control leaves `runshell_db`, whether the client invocation succeeds or
   raises, THEN `runshell_db` SHALL restore the SIGINT handler that was in effect
   before it was called.

## Requirement 4: Run the client and propagate failures

**User story:** As a developer, I want a failed client invocation to surface as
an error, so that problems are not silently ignored.

**Acceptance criteria**

1. The system SHALL launch the client as a subprocess using the constructed
   argument vector and the child-process environment described above.
2. IF the client process exits with a non-zero status, THEN `runshell_db` SHALL
   raise an error rather than return normally.
3. The system SHALL keep the public entry point `runshell` behaving as before:
   calling it SHALL invoke `runshell_db` with the connection parameters obtained
   from the connection.
