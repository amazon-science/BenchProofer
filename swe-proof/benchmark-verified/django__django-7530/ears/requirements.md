# Requirements — makemigrations consistency-check router enumeration

## Introduction

When the `makemigrations` management command
(`django/core/management/commands/makemigrations.py`, inside
`Command.handle`) runs, it performs a migration-history consistency check.
Before checking a database connection, it decides whether that connection is
relevant by consulting the configured database routers: it calls
`router.allow_migrate(connection.alias, app_label, model_name=...)` for a
collection of `(app_label, model_name)` pairs and checks the history only when
at least one such call returns a truthy value.

The affected behavior is the *set of `(app_label, model_name)` pairs* that this
consistency check feeds to `allow_migrate()`. The command must pair each
application label only with the names of the models that actually belong to
that application. Previously it paired every application label with **all**
models in the entire project, so it passed application/model combinations that
do not correspond to a real model of that application. Such invalid
combinations break routers (for example sharding routers) that legitimately
assume they will only ever be asked about models an application actually owns.

The goal: ensure every `allow_migrate()` call made during the makemigrations
consistency check uses a valid `(app_label, model_name)` pair — an application
label together with a model that is registered to that same application — while
preserving all other existing behavior of the consistency check and of the
`makemigrations` command.

## Requirement 1: allow_migrate is queried only with an application's own models

**User story:** As a developer using a custom database router, I want
`makemigrations` to ask my router only about model/application combinations that
actually exist, so that a router which assumes valid combinations (such as a
sharded router whose shards do not all contain the same models) is not broken by
spurious queries.

**Acceptance criteria**

1. WHEN the makemigrations consistency check enumerates the pairs it passes to
   `router.allow_migrate()`, THEN for each application label included in the
   check the system SHALL enumerate only the models registered to that same
   application.
2. WHEN `router.allow_migrate(alias, app_label, model_name=name)` is called
   during the consistency check, THEN the system SHALL guarantee that `name` is
   the object name of a model that belongs to the application identified by
   `app_label`.
3. The system SHALL NOT call `router.allow_migrate()` during the consistency
   check with any `(app_label, model_name)` pair in which the model does not
   belong to the identified application.
4. IF an application defines a set of models different from other installed
   applications, THEN the system SHALL query each application with its own
   models independently, so that models owned only by other applications are
   never attributed to it.
5. The system SHALL resolve the models of an application from that
   application's own configuration (via its `AppConfig`) rather than from a
   project-wide model lookup that ignores the application label.

## Requirement 2: consistency check still covers every application and the correct connections

**User story:** As a Django user, I want the migration-history consistency check
to keep working across all my apps and databases, so that the fix to the
pairing does not weaken or skip the check.

**Acceptance criteria**

1. WHEN the consistency check runs, THEN the system SHALL consider every
   installed application (every application label subject to the consistency
   check), each paired with that application's own models.
2. WHEN database routers are configured, THEN the system SHALL evaluate the
   relevant database connections (not only the default connection) when
   determining whether to check history, calling `allow_migrate()` with each
   evaluated connection's alias.
3. WHEN no database routers are configured, THEN the system SHALL evaluate only
   the default database connection.
4. WHEN at least one `allow_migrate()` call for a given connection returns a
   truthy value, THEN the system SHALL perform the migration-history consistency
   check for that connection.
5. WHILE evaluating a connection whose engine is the dummy backend, the system
   SHALL NOT perform the history consistency check for that connection.
6. The system SHALL pass to each `allow_migrate()` call the alias of the
   connection currently being evaluated, unchanged.

## Requirement 3: preserve existing makemigrations behavior

**User story:** As a Django user, I want all other `makemigrations` behavior to
be unaffected, so that the enumeration fix is a targeted correction.

**Acceptance criteria**

1. The system SHALL keep the existing behavior of `makemigrations` for
   generating, merging, naming, and reporting migrations unchanged by this fix.
2. WHEN makemigrations is invoked for one or more named applications, THEN the
   system SHALL keep restricting its migration output and conflict handling to
   those applications as before.
3. The system SHALL keep raising the existing "app could not be found" error
   behavior when an invalid application label is requested.
