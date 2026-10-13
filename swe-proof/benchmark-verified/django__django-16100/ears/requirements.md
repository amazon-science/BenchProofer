# Requirements: Atomic processing of bulk list-editable saves in the admin changelist

## Introduction

The Django admin's changelist view (`ModelAdmin.changelist_view` in
`django/contrib/admin/options.py`) supports inline bulk editing of multiple
rows at once (the `list_editable` feature). When such a bulk-edit form is
submitted with the save action, the view iterates over every changed row and
persists it by running a sequence of save operations per row — saving the
object, its related objects, and writing an admin audit-log entry.

Before this change, each row was saved independently as the loop progressed.
If one row's save sequence failed partway through the loop (for example, a
database error while writing one of the rows or its audit-log entry), the rows
already processed in that same request had **already been committed**, leaving
the database in an inconsistent, partially-applied state that the user never
confirmed.

The goal is to make the bulk-edit save loop **all-or-nothing**: the entire set
of per-row writes for a single submission must be processed as one atomic
database unit, so that either every changed row is persisted together, or — if
any part of the processing fails — none of the changes take effect and the
database is left exactly as it was before the submission. This affects only the
POST branch of `changelist_view` that handles `list_editable` bulk saves; all
other behavior (searching, filtering, ordering, pagination, display, single
edits, admin-log rendering) must be unchanged.

## Requirement 1: Atomic all-or-nothing bulk save

**User story:** As an admin user editing several rows inline on the changelist
and saving them at once, I want the whole submission to succeed or fail as a
unit, so that a mid-way error never leaves some rows changed and others not.

**Acceptance criteria**

1. WHEN a `list_editable` bulk-edit form is submitted for saving and the
   submitted formset is valid, THEN `changelist_view` SHALL process the
   per-row save operations for all changed rows within a single database
   transaction scoped to the write database of the edited model.
2. WHEN every changed row's save sequence completes without error, THEN
   `changelist_view` SHALL commit all of those changes together so that all
   edited rows reflect their new values after the request.
3. IF any save operation performed while processing the changed rows raises an
   error before all changed rows have been processed, THEN `changelist_view`
   SHALL cause none of the row changes made during that submission to persist,
   so that every affected row retains exactly the value it had immediately
   before the submission.
4. IF an error is raised while processing the very first changed row, THEN
   `changelist_view` SHALL leave all affected rows unchanged from their
   pre-submission values.
5. IF one or more changed rows are processed successfully and then an error is
   raised while processing a later changed row, THEN `changelist_view` SHALL
   also roll back the earlier, already-processed rows so that they too retain
   their pre-submission values.

## Requirement 2: The failure is surfaced, not silently swallowed

**User story:** As a developer relying on the admin, I want a save failure to
propagate rather than be hidden, so that the caller observes the error instead
of a silently incomplete save.

**Acceptance criteria**

1. IF an error is raised while processing the changed rows of a bulk-edit
   submission, THEN `changelist_view` SHALL allow that error to propagate out of
   the request handling rather than suppressing it or reporting a success.
2. WHEN such an error propagates, THEN `changelist_view` SHALL NOT report a
   "changed successfully" outcome for that submission.

## Requirement 3: Preserve normal successful bulk-edit behavior (regression)

**User story:** As an admin user making a normal, error-free bulk edit, I want
the existing successful save behavior to keep working unchanged.

**Acceptance criteria**

1. WHEN a valid `list_editable` bulk-edit form is submitted for saving and no
   error occurs, THEN `changelist_view` SHALL, for each row whose data changed,
   perform its full save sequence — saving the object, saving its related
   objects, and recording an admin audit-log entry for the change.
2. WHEN one or more rows are changed and saved successfully, THEN
   `changelist_view` SHALL report the number of successfully changed objects to
   the user and SHALL redirect back to the changelist page.
3. The system SHALL apply the atomic transaction only to the bulk `list_editable`
   save path; the ordering of the per-row save operations and the set of
   operations performed for each changed row SHALL remain as before.
4. WHEN a submitted row's data is unchanged, THEN `changelist_view` SHALL NOT
   perform save operations for that row and SHALL NOT count it as changed.

## Requirement 4: Unrelated changelist behavior is unaffected (regression)

**User story:** As a user of the admin changelist, I want every non-bulk-save
feature to behave exactly as before, so that adding transaction handling does
not change unrelated functionality.

**Acceptance criteria**

1. The system SHALL preserve all existing changelist behavior unrelated to the
   bulk save path, including search, list filtering, result ordering,
   pagination, result-list rendering, empty-value display, and single-object
   editing.
2. The system SHALL preserve the behavior of admin-log rendering and related
   changelist query construction unchanged.
