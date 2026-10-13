# Requirements: `__in` lookup on JSON key/index transforms

## Introduction

Django's `JSONField` lets a query "reach into" stored JSON with *key transforms*
(`field__key`) and *array-index transforms* (`field__0`). A transform produces a
value that further lookups compare against, e.g. `field__key=value` matches rows
whose JSON value at that key equals `value`.

The membership lookup `__in` (`field__key__in=[v1, v2, ...]`) is expected to
behave as the disjunction of the corresponding equality lookups: it should match
exactly the rows that `field__key=v1` OR `field__key=v2` OR ... would match. On
PostgreSQL (which stores JSON natively) this already works, but on backends that
do NOT have a native JSON column type — SQLite, MySQL, MariaDB, and Oracle —
`__in` applied to a key/index transform returned no rows even when the equivalent
single-key equality lookup matched many rows. The values on the right-hand side
of `__in` were compared against the raw stored representation instead of against
the value extracted from the JSON document, so they never matched.

This work lives in the JSON key-transform lookup machinery in
`django/db/models/fields/json.py` (the same module that defines the exact,
regex, and other key-transform lookups, all registered on the key transform).
The goal is that `__in` on a key or index transform yields the same result set
as the equivalent equality lookup(s), on every supported database backend,
without disturbing the other key-transform lookups.

## Requirement 1: `__in` on a key/index transform matches by membership

**User story:** As a developer querying a `JSONField`, I want
`field__key__in=[...]` to return the same rows I would get by OR-ing the
individual `field__key=value` lookups, so that membership queries over JSON key
values behave consistently across all database backends.

**Acceptance criteria**

1. WHEN a queryset filters a key transform (or array-index transform) of a
   `JSONField` with an `__in` lookup whose right-hand side is a non-empty list of
   candidate values, THEN the query SHALL return exactly those objects whose
   extracted JSON value at that key/index is equal to at least one of the listed
   candidate values.
2. WHEN the `__in` list contains exactly one candidate value, THEN the resulting
   queryset SHALL be identical to the queryset produced by the equality lookup
   `field__key=<that value>` on the same key/index transform.
3. WHEN the `__in` list contains several candidate values, THEN an object SHALL
   be returned IF AND ONLY IF its extracted value at that key/index equals one of
   the listed values; adding further candidate values SHALL only ever add matching
   objects, never remove a match that a smaller list already produced.
4. The set of objects returned by an `__in` lookup on a key/index transform
   SHALL be independent of the underlying database backend — it SHALL be the same
   on backends with a native JSON column type and on backends without one (so that
   the membership query is not silently empty on the latter).
5. WHEN the extracted JSON value is compared against a candidate value, THEN the
   comparison SHALL be made against the value *extracted from the stored JSON
   document* at that key/index, not against the raw stored text, so that a match
   occurs whenever the decoded value equals the candidate.

## Requirement 2: Candidate values may be scalars, arrays, or objects

**User story:** As a developer, I want `__in` on a JSON key transform to accept
the same kinds of values that equality accepts — numbers, strings, lists, and
dicts — so that I can filter on structured JSON values, not just primitives.

**Acceptance criteria**

1. WHEN a candidate value in the `__in` list is a JSON scalar (for example an
   integer or a string), THEN an object SHALL match IF its extracted value at the
   key/index equals that scalar.
2. WHEN a candidate value in the `__in` list is a JSON array (a list), THEN an
   object SHALL match IF its extracted value at the key/index is an array equal to
   that candidate array (element-for-element).
3. WHEN a candidate value in the `__in` list is a JSON object (a dict), THEN an
   object SHALL match IF its extracted value at the key/index is an object equal
   to that candidate object.
4. WHEN the `__in` list mixes candidate values of different JSON types, THEN each
   candidate SHALL be matched according to its own type per criteria 1–3, and an
   object SHALL be returned IF it matches any candidate.
5. WHEN the transform addresses an array element by numeric index (an
   array-index transform such as `field__0`), THEN `__in` SHALL match against the
   value at that array position exactly as it does for a named key.

## Requirement 3: Preserve the other key-transform lookups (regression protection)

**User story:** As a maintainer, I want adding membership (`__in`) support to
leave every other key-transform lookup behaving exactly as before, so that
existing JSON queries keep working.

**Acceptance criteria**

1. WHEN a case-insensitive regular-expression lookup is applied to a key
   transform of a `JSONField` (`field__key__iregex=<pattern>`), THEN it SHALL
   match an object IF the string form of the extracted key value matches the
   pattern case-insensitively; a pattern differing from the stored value only in
   letter case SHALL still match.
2. WHEN a case-sensitive regular-expression lookup is applied to a key transform
   (`field__key__regex=<pattern>`), THEN it SHALL match only when the string form
   of the extracted key value matches the pattern with case significant.
3. The equality lookup on a key/index transform (`field__key=value`) SHALL
   continue to return exactly the objects whose extracted value equals `value`,
   unchanged by the addition of the membership lookup.
4. The other key-transform lookups already supported — such as `iexact`,
   `contains`/`icontains` where available, `startswith`/`istartswith`,
   `endswith`/`iendswith`, `isnull`, and the numeric comparison lookups (`lt`,
   `lte`, `gt`, `gte`) — SHALL continue to behave exactly as they did before,
   with the same result sets on every backend.
5. The system SHALL keep resolving `__in` on a `JSONField` key/index transform as
   a registered lookup on the key transform, so that the lookup is available on
   all databases rather than raising an unsupported-lookup error.
