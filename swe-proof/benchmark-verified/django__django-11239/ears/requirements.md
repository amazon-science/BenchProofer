# Requirements: PostgreSQL dbshell TLS client-certificate support

## Introduction

The `dbshell` management command opens an interactive session with the
configured database by invoking its native command-line client. For the
PostgreSQL backend, the invocation is assembled in
`django/db/backends/postgresql/client.py` by the
`DatabaseClient.runshell_db` classmethod, which is reached from
`DatabaseClient.runshell` via the connection's parameters.

Applications routinely secure their PostgreSQL connections with mutual TLS,
supplying an SSL mode plus a trusted-authority certificate, a client
certificate, and a client private key through the database `OPTIONS` mapping
(`sslmode`, `sslrootcert`, `sslcert`, `sslkey`). The application's own
connections already honor these parameters, but the interactive client launched
by `dbshell` did not: it forwarded only the user, host, port, database name,
and password. As a result, the shell could not connect to a server that
requires certificate-based mutual TLS.

The goal is to make `runshell_db` forward the transport-security connection
parameters to the PostgreSQL client so the interactive session authenticates
exactly as the application's connections do, while preserving all previously
supported behavior (argument vector construction and password forwarding).

A connection parameter is considered **supplied** when it is present with a
non-empty string value; otherwise it is treated as absent and contributes
nothing to the invocation.

## Requirement 1: Forward transport-security parameters to the client

**User story:** As a Django developer whose PostgreSQL server requires
certificate-based mutual TLS, I want `dbshell` to pass my configured SSL mode
and certificate/key parameters to the PostgreSQL client, so that the
interactive shell connects using the same mutual-TLS configuration as my
application.

**Acceptance criteria**

1. WHEN `runshell_db` assembles the child-process environment and the SSL mode
   parameter is supplied, THEN the command SHALL place its value in the child
   environment under the `PGSSLMODE` variable that the PostgreSQL client reads.
2. WHEN the trusted-authority (root) certificate parameter is supplied, THEN the
   command SHALL place its value in the child environment under the
   `PGSSLROOTCERT` variable.
3. WHEN the client certificate parameter is supplied, THEN the command SHALL
   place its value in the child environment under the `PGSSLCERT` variable.
4. WHEN the client private-key parameter is supplied, THEN the command SHALL
   place its value in the child environment under the `PGSSLKEY` variable.
5. The command SHALL read the transport-security parameters from the same
   connection-parameters mapping used for user, host, port, database, and
   password.
6. WHEN a supplied parameter's value is not already a string, THEN the command
   SHALL inject its string form into the environment.

## Requirement 2: Omit unsupplied parameters

**User story:** As a developer who does not use TLS client certificates, I want
`dbshell` to behave exactly as before, so that enabling this feature never
changes an environment I did not configure.

**Acceptance criteria**

1. IF the SSL mode parameter is absent (missing or empty), THEN the command
   SHALL NOT set the `PGSSLMODE` variable in the child environment.
2. IF the trusted-authority certificate parameter is absent, THEN the command
   SHALL NOT set the `PGSSLROOTCERT` variable.
3. IF the client certificate parameter is absent, THEN the command SHALL NOT set
   the `PGSSLCERT` variable.
4. IF the client private-key parameter is absent, THEN the command SHALL NOT set
   the `PGSSLKEY` variable.
5. The command SHALL introduce no transport-security environment variable other
   than the four named above, and each supplied parameter SHALL map only to its
   corresponding variable.

## Requirement 3: Preserve the existing invocation behavior

**User story:** As a maintainer, I want the previously supported `dbshell`
behavior to remain intact, so that adding TLS support does not regress
connection handling.

**Acceptance criteria**

1. The command SHALL start the client argument vector with the PostgreSQL client
   executable name.
2. WHEN the user parameter is supplied, THEN the command SHALL append the user
   flag followed by the user value to the argument vector.
3. WHEN the host parameter is supplied, THEN the command SHALL append the host
   flag followed by the host value to the argument vector.
4. WHEN the port parameter is supplied, THEN the command SHALL append the port
   flag followed by the port value (as a string) to the argument vector.
5. The command SHALL append the database name as the final element of the
   argument vector, regardless of whether it is empty.
6. WHEN the password parameter is supplied, THEN the command SHALL place its
   value (as a string) in the child environment under the `PGPASSWORD` variable;
   IF the password is absent, THEN the command SHALL NOT set `PGPASSWORD`.
7. The command SHALL leave the argument vector unaffected by the
   transport-security parameters — only the child environment carries them.
8. The command SHALL invoke the client with the assembled argument vector and
   the assembled environment, keep it inheriting the current process
   environment, and continue to ignore keyboard-interrupt signals for the
   duration of the invocation, restoring the prior signal handling afterward.
