# Requirements: Secure default Referrer-Policy header

## Introduction

The framework ships a security response filter (`SecurityMiddleware` in
`django/middleware/security.py`) that, when enabled, attaches a
`Referrer-Policy` response header whose value comes from the
`SECURE_REFERRER_POLICY` configuration setting declared in
`django/conf/global_settings.py`.

Historically the built-in default of `SECURE_REFERRER_POLICY` was the "no
policy" choice (unset), so a freshly-generated project advertised no referrer
policy. To reduce information leakage to third-party sites, the built-in default
must become the concrete, conservative policy value `same-origin`. As a result,
an out-of-the-box project that runs the security middleware over a response must
emit a `Referrer-Policy: same-origin` header, alongside the other security
headers already emitted under the default configuration, without any
project-level configuration.

The affected components are:

- the built-in default value of the `SECURE_REFERRER_POLICY` setting in the
  global settings module;
- `SecurityMiddleware.process_response`, which reads that setting and attaches
  the header.

## Requirement 1: Secure built-in default for the referrer-policy setting

**User story:** As a developer generating a new project with default settings,
I want the framework to advertise a conservative referrer policy out of the box,
so that my application leaks less referrer information to third-party sites
without any extra configuration.

**Acceptance criteria**

1. The system SHALL define the built-in default value of the
   `SECURE_REFERRER_POLICY` setting as the single policy value `same-origin`.
2. WHEN a project does not declare `SECURE_REFERRER_POLICY` in its own settings,
   THEN the effective value of the setting SHALL be exactly `same-origin`.
3. The built-in default value of `SECURE_REFERRER_POLICY` SHALL be a non-empty
   string value, not the "no policy" / unset choice.
4. IF a project declares its own value for `SECURE_REFERRER_POLICY`, THEN the
   effective value SHALL be exactly the project-declared value, and the built-in
   default SHALL NOT override it.

## Requirement 2: Referrer-Policy header emitted for default responses

**User story:** As an operator running a default project through the security
middleware, I want responses to carry a same-origin referrer policy header, so
that browsers restrict referrer information as intended.

**Acceptance criteria**

1. WHEN the security middleware processes an outgoing response under the
   built-in default configuration (no project override of
   `SECURE_REFERRER_POLICY`) and the response does not already carry a
   `Referrer-Policy` header, THEN the middleware SHALL attach a
   `Referrer-Policy` header whose value is exactly `same-origin`.
2. WHEN the middleware attaches the `Referrer-Policy` header from a single
   whitespace-free policy value, THEN the emitted header value SHALL be that
   value carried verbatim (no surrounding whitespace, no extra tokens).
3. IF the outgoing response already carries a `Referrer-Policy` header, THEN the
   middleware SHALL leave that existing header value unchanged.
4. IF the effective `SECURE_REFERRER_POLICY` value is the "no policy" / unset
   choice, THEN the middleware SHALL NOT attach a `Referrer-Policy` header.

## Requirement 3: Referrer-policy change does not disturb other responses

**User story:** As an operator relying on the default project's existing
behavior, I want the change to the referrer-policy default to be additive only,
so that introducing a same-origin referrer policy does not regress any other
response behavior.

**Acceptance criteria**

1. WHEN a response is processed under the built-in default configuration, THEN
   the only change to the response attributable to the new referrer-policy
   default SHALL be the addition of the `Referrer-Policy` header described in
   Requirements 1 and 2.
2. The change to the referrer-policy default SHALL NOT add, remove, reorder, or
   alter the value of any response header other than `Referrer-Policy`; every
   header the response would otherwise carry under the default configuration
   SHALL remain present with its original value.
3. The change to the referrer-policy default SHALL affect only the
   `SECURE_REFERRER_POLICY` setting's value and the resulting `Referrer-Policy`
   header, and SHALL NOT change any other configuration setting or the behavior
   of any other response filter.
