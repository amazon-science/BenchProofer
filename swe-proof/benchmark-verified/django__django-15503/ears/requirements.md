# Requirements — JSONField `has_key`/`has_keys`/`has_any_keys` with numeric keys

## Introduction

Django's `JSONField` supports the `has_key`, `has_keys`, and `has_any_keys`
lookups, which test whether a stored JSON object contains one or more given
member names. On PostgreSQL these lookups work for any key, but on SQLite,
MySQL, and Oracle a key that happens to be a run of decimal digits (for example
`"1111"`) is silently treated as an *array index* rather than as an *object
member name*, so the lookup fails to match objects that really do contain that
key.

The affected code lives in `django/db/models/fields/json.py`. The path-building
helper `compile_json_path` maps each key transform to a JSON-path segment,
rendering a decimal-digit key as a positional segment (`[n]`) and any other key
as a quoted named member (`."key"`). The class `HasKeyLookup` (and its
subclasses `HasKey`, `HasKeys`, `HasAnyKeys`) assembles, for each key being
tested, a JSON-path string that it feeds to the backend-specific existence
predicate (`JSON_TYPE(...) IS NOT NULL` on SQLite, `JSON_CONTAINS_PATH` on
MySQL, `JSON_EXISTS` on Oracle). Because the *final* segment of that path was
produced by the digit-sensitive helper, an all-digit key was addressed as an
array index and the object member of that name was never found.

The goal is to make the existence lookups address the key being tested as an
object member name on all backends, so numeric string keys are matched
consistently — while preserving every other existing behavior of these
lookups, including deep/nested paths, keys located inside arrays, and the
distinct array-index semantics still required by the `isnull` key lookup on
Oracle and SQLite.

## Requirement 1: Match object members whose name is all digits

**User story:** As a developer filtering a `JSONField` on SQLite, MySQL, or
Oracle, I want `has_key` with a numeric string key to match rows whose JSON
object contains that key, so that numeric keys behave the same as they do on
PostgreSQL.

**Acceptance criteria**

1. WHEN a `has_key` lookup is evaluated against a stored JSON object whose
   top-level members include a key that is a run of decimal digits, THEN the
   query SHALL match that row.
2. The system SHALL treat the key supplied to a `has_key`/`has_keys`/
   `has_any_keys` existence lookup as an object member name, regardless of
   whether the key text consists solely of decimal digits.
3. IF the tested key is a run of decimal digits with a leading zero, THEN the
   lookup SHALL still match the object member of that exact name and SHALL NOT
   reinterpret it as a positional index or otherwise normalize away the leading
   zero.
4. The system SHALL continue to match object members whose names are
   non-numeric (for example `"foo"`) exactly as before.

## Requirement 2: Numeric keys at nested and array-relative positions

**User story:** As a developer, I want numeric-key existence lookups to work at
any depth — including beneath other object members and beneath array elements —
so that nested numeric keys are found reliably.

**Acceptance criteria**

1. WHEN a `has_key` lookup targets a key transform reached through one or more
   intermediate object members (a nested path) and the final tested key is a
   run of decimal digits, THEN the query SHALL match a row whose value contains
   that member at that nested location.
2. WHEN a `has_key` lookup targets a key beneath an array element selected by a
   positional key transform, THEN the intermediate positional transform SHALL
   continue to address the array element by index, while the final tested key
   SHALL be addressed as an object member name.
3. The system SHALL preserve the existing behavior of intermediate key
   transforms: a decimal-digit key transform used to descend into the path
   (i.e. any key transform other than the final one being tested) SHALL still
   be rendered as a positional array index.
4. The assembled path for an existence lookup SHALL be the left-hand-side JSON
   path followed by the rendered intermediate segments followed by the final
   key rendered as a named member.

## Requirement 3: `has_keys` and `has_any_keys` honor numeric keys

**User story:** As a developer, I want the multi-key existence lookups to
handle numeric keys the same way `has_key` does, so that lists of keys behave
consistently.

**Acceptance criteria**

1. WHEN a `has_keys` lookup is given a list of keys that includes one or more
   all-digit keys, THEN the query SHALL match a row only if the JSON object
   contains an object member for every listed key (numeric keys addressed as
   member names).
2. WHEN a `has_any_keys` lookup is given a list of keys that includes one or
   more all-digit keys, THEN the query SHALL match a row if the JSON object
   contains an object member for at least one listed key.
3. The system SHALL apply the same member-name treatment of numeric keys to
   `has_keys` and `has_any_keys` at top level, at nested object positions, and
   beneath array elements.
4. The system SHALL continue to coerce each supplied key of a `has_keys`/
   `has_any_keys` lookup to its string form before testing membership.

## Requirement 4: Preserve existing existence-lookup behavior (regression)

**User story:** As a maintainer, I want the numeric-key fix to leave every
previously working `has_key`-family behavior unchanged, so that no existing
query regresses.

**Acceptance criteria**

1. The system SHALL keep matching a simple `has_key` lookup for a non-numeric
   top-level key.
2. The system SHALL keep supporting `has_any_keys` over a list of non-numeric
   keys, matching when any listed key is present.
3. The system SHALL keep the existing deep/nested `has_key` behavior for
   non-numeric keys reached through chained key transforms.
4. The system SHALL keep matching a key whose stored value is JSON null (the
   member exists but its value is null), i.e. presence — not value — determines
   a `has_key` match.
5. WHEN the left-hand side of an existence lookup is itself a key transform,
   THEN the system SHALL prepend that resolved path before the tested key when
   assembling the JSON path.
6. The system SHALL keep producing correct existence SQL for each supported
   backend (SQLite, MySQL, Oracle, PostgreSQL) without changing the
   PostgreSQL behavior, which already handled numeric keys.

## Requirement 5: Preserve array-index semantics for the `isnull` key lookup

**User story:** As a maintainer, I want the Oracle and SQLite `isnull`
implementation for key transforms to retain its established array-index-capable
path rendering, so that `key__isnull` queries and existing index-based
behaviors do not change.

**Acceptance criteria**

1. The system SHALL provide an existence variant whose final-key rendering
   preserves the pre-existing digit-run-as-array-index behavior, and SHALL use
   that variant for the `isnull` key lookup on Oracle and SQLite.
2. WHEN `key__isnull=False` is evaluated for a key transform, THEN it SHALL
   remain equivalent to testing that the key is present, using the
   array-index-capable rendering variant.
3. The system SHALL keep the Oracle handling of a key whose stored value is SQL
   null (matching a present key with a null value) using that same
   array-index-capable existence variant.
4. The system SHALL keep the results of existing `isnull` and none-value key
   lookups unchanged by this fix.
