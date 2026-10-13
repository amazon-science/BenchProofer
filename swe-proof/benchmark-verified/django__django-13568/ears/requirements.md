# Requirements: Skip the USERNAME_FIELD uniqueness error when a total unique constraint covers it

## Introduction

Django's authentication framework runs a set of system checks against the
configured user model (`AUTH_USER_MODEL`) in
`django.contrib.auth.checks.check_user_model`. One of these checks
(`auth.E003`, downgraded to the warning `auth.W004` when a non-default
authentication backend is in use) requires that the field named by the model's
`USERNAME_FIELD` be unique, because the login field must identify at most one
user.

Historically this check inspected only the field's own `unique` attribute. A
developer can, however, guarantee uniqueness of a single field by declaring a
`UniqueConstraint` in the model's `Meta.constraints` instead of setting
`unique=True` — this is sometimes preferable because `unique=True` on a
`CharField`/`TextField` creates an extra implicit `*_like` index on PostgreSQL.
When uniqueness was expressed that way, the check wrongly reported `auth.E003`.

The goal is to extend the uniqueness check so that it also treats the
`USERNAME_FIELD` as unique when a *total* (unconditional) unique constraint
ranges over exactly that one field. Only unconditional unique constraints
count: a partial constraint (one carrying a `condition`) does not guarantee
global uniqueness and must not suppress the diagnostic. All other user-model
checks must remain unchanged.

The affected module/function is `check_user_model` in
`django/contrib/auth/checks.py`. It relies on
`Model._meta.total_unique_constraints` (defined in
`django/db/models/options.py`), which returns the model's `UniqueConstraint`
instances whose `condition` is `None`.

## Requirement 1: Suppress the uniqueness diagnostic when a total unique constraint covers the login field

**User story:** As a developer defining a custom user model, I want to
guarantee the login field's uniqueness with an unconditional single-field
unique constraint instead of `unique=True`, so that my model passes the auth
system checks without creating an extra implicit index.

**Acceptance criteria**
1. WHEN `check_user_model` runs against a user model whose `USERNAME_FIELD`
   field does not have `unique=True`, AND the model declares an unconditional
   unique constraint (a `UniqueConstraint` whose `condition` is `None`, i.e. one
   present in `Model._meta.total_unique_constraints`) whose constrained fields
   are exactly the single `USERNAME_FIELD` name, THEN `check_user_model` SHALL
   NOT emit the "must be unique because it is named as the 'USERNAME_FIELD'"
   error, and SHALL NOT emit the corresponding non-uniqueness warning.
2. IF such a covering total unique constraint is present, THEN the suppression
   SHALL apply regardless of which authentication backends are configured
   (both the default-backend error path and the non-default-backend warning
   path are suppressed).
3. The system SHALL determine whether a constraint covers the login field by
   comparing the constraint's constrained field collection against a collection
   containing exactly the one `USERNAME_FIELD` name; a constraint over a
   different field, or over more than one field, SHALL NOT be treated as
   covering the login field.

## Requirement 2: Continue reporting the uniqueness diagnostic when the field is genuinely not guaranteed unique

**User story:** As a Django maintainer, I want the login-field uniqueness check
to keep firing whenever uniqueness is not actually guaranteed, so that
misconfigured user models are still caught.

**Acceptance criteria**
1. WHEN `check_user_model` runs against a user model whose `USERNAME_FIELD`
   field does not have `unique=True`, AND no unconditional unique constraint
   covers exactly that single field, AND the only configured authentication
   backend is the default model backend, THEN `check_user_model` SHALL emit an
   error diagnostic with id `auth.E003` stating that the field must be unique
   because it is named as the `USERNAME_FIELD`.
2. WHEN the same non-unique situation holds AND the configured authentication
   backends are not exactly the single default model backend, THEN
   `check_user_model` SHALL instead emit a warning diagnostic with id
   `auth.W004` stating that the field is named as the `USERNAME_FIELD` but is
   not unique.
3. IF the model declares a unique constraint over the `USERNAME_FIELD` that is
   *partial* — that is, it carries a non-`None` `condition` and therefore is not
   part of `total_unique_constraints` — THEN `check_user_model` SHALL still emit
   the uniqueness diagnostic (`auth.E003` / `auth.W004`) as if the constraint
   were absent, because a conditional constraint does not guarantee global
   uniqueness.
4. WHEN the `USERNAME_FIELD` field itself has `unique=True`, THEN
   `check_user_model` SHALL NOT emit any login-field uniqueness diagnostic,
   preserving the pre-existing behavior.

## Requirement 3: Preserve all other user-model system checks unchanged

**User story:** As a Django maintainer, I want the remaining user-model checks
to behave exactly as before, so that this change is limited to the uniqueness
guard.

**Acceptance criteria**
1. WHEN `REQUIRED_FIELDS` is not a list or tuple, THEN `check_user_model` SHALL
   emit the `auth.E001` error, unchanged by this requirement.
2. WHEN the `USERNAME_FIELD` name appears in `REQUIRED_FIELDS`, THEN
   `check_user_model` SHALL emit the `auth.E002` error, unchanged.
3. WHEN the user model's `is_anonymous` is a plain method rather than an
   attribute/property, THEN `check_user_model` SHALL emit the `auth.C009`
   critical diagnostic; and WHEN `is_authenticated` is a plain method, THEN it
   SHALL emit the `auth.C010` critical diagnostic — both unchanged.
4. The system SHALL leave the separate model-permissions checks
   (`check_models_permissions`, covering permission name/codename length limits,
   clashing and duplicate custom/default permissions, verbose-name and
   model-name length limits) entirely unaffected by this change.
5. The system SHALL preserve the framing of each emitted diagnostic — its id
   code, severity (error / warning / critical), target object, and message/hint
   text — so that only *whether* the uniqueness diagnostic fires changes, not
   how any diagnostic is reported.
