# Requirements: Require a non-empty name for Blueprints

## Introduction

Flask's `Blueprint` class (`flask.blueprints.Blueprint`, defined in
`src/flask/blueprints.py`) accepts a `name` as the first positional argument to
its constructor (`Blueprint.__init__`). This name identifies the blueprint and
is used to build endpoint names and to register the blueprint on an application.

Historically an empty blueprint name was accepted, but a blueprint with an empty
name does not work correctly (endpoints and registration misbehave). The goal of
this change is to validate the `name` argument at construction time so that an
empty name is rejected immediately with a clear error, rather than causing
confusing downstream failures. This must be done without disturbing the
existing validation of dotted names or any other blueprint construction
behavior.

## Requirement 1: Reject an empty blueprint name

**User story:** As a Flask developer, I want the `Blueprint` constructor to
reject an empty name, so that misconfigured blueprints fail fast with a clear
error instead of behaving incorrectly later.

**Acceptance criteria**

1. WHEN a `Blueprint` is constructed with a `name` argument that is an empty
   string, THEN the constructor SHALL raise a `ValueError`.
2. WHEN the constructor rejects an empty `name`, THEN it SHALL raise the error
   during construction (i.e. no `Blueprint` instance is returned to the caller
   for an empty name).
3. The system SHALL treat the emptiness check as a check for a falsy/empty
   `name` value, independent of the values passed for any other constructor
   argument (such as `import_name`).

## Requirement 2: Preserve rejection of dotted blueprint names

**User story:** As a Flask developer, I want blueprint names containing a dot to
continue to be rejected, so that existing naming guarantees are not weakened by
the new validation.

**Acceptance criteria**

1. WHEN a `Blueprint` is constructed with a non-empty `name` that contains a
   dot (`.`) character, THEN the constructor SHALL raise a `ValueError`.
2. The system SHALL keep the dotted-name check independent of and in addition to
   the empty-name check, so that a name may be rejected for being empty or for
   containing a dot.

## Requirement 3: Preserve construction and behavior for valid names

**User story:** As a Flask developer, I want blueprints with valid names to keep
working exactly as before, so that adding the empty-name validation does not
break any existing usage.

**Acceptance criteria**

1. WHEN a `Blueprint` is constructed with a non-empty `name` that contains no
   dot character, THEN the constructor SHALL succeed and produce a usable
   `Blueprint` instance.
2. The system SHALL keep the constructed blueprint's `name` attribute equal to
   the `name` argument that was supplied.
3. The system SHALL keep all other blueprint construction behavior unchanged for
   valid names, including handling of `import_name`, static and template folder
   options, `url_prefix`, `subdomain`, `url_defaults`, `root_path`, and CLI
   group configuration.
4. The system SHALL keep supporting the full set of established blueprint
   capabilities for validly-named blueprints, including: registering blueprints
   on an application; blueprint-specific and application-level error handling;
   URL prefix handling and joining of parent/child prefixes; URL defaults and
   URL value processors; serving templates and static files; request and
   context processing callbacks (including application-wide variants);
   registering template filters, tests, and globals (with or without explicit
   names and templates); route and endpoint decorators (including custom
   endpoints and endpoints containing dots); nesting blueprints (including
   nested registration callback ordering and subdomain handling); enforcing
   unique blueprint registration names; self-registration behavior; and
   renaming a blueprint at registration time.
