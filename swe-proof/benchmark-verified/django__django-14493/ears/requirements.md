# Requirements: Post-processing static files must not crash when the maximum number of passes is zero

## Introduction

Django's `ManifestStaticFilesStorage` (and its base `HashedFilesMixin`) rewrites
collected static files to include a content hash in their names and rewrites
references between files so they point at the hashed names. This work is done by
`HashedFilesMixin.post_process` in
`django/contrib/staticfiles/storage.py`, which is called from the
`collectstatic` management command.

`post_process` first performs a single pass over all collected files (yielding
non-adjustable files and any exceptions, and collecting the adjustable files).
It then runs a bounded refinement loop that re-processes the adjustable files up
to `max_post_process_passes` times, stopping early as soon as a pass produces no
further reference substitutions. After the loop it inspects a local flag,
`substitutions`, to decide whether the loop stopped because it ran out of passes
while references were still changing — in which case it yields a
`RuntimeError('Max post-process passes exceeded.')`.

The defect: the `substitutions` flag was assigned only *inside* the refinement
loop. A subclass may legitimately set `max_post_process_passes = 0` (for example
to avoid emitting invalid CSS from reference rewriting). With a maximum of `0`
the loop body never executes, so the flag is never assigned, and the subsequent
inspection raises `UnboundLocalError: local variable 'substitutions' referenced
before assignment`. This aborts `collectstatic` entirely.

The goal is to make `post_process` complete normally for every non-negative
value of `max_post_process_passes`, including `0`, while preserving the existing
convergence, early-stop, and "max passes exceeded" behavior for positive values.

## Requirement 1: Post-processing succeeds when the maximum number of passes is zero

**User story:** As a Django developer who has subclassed the hashing static
files storage and set `max_post_process_passes = 0`, I want `collectstatic` to
run to completion, so that my static files are collected and hashed without the
command crashing.

**Acceptance criteria**

1. WHEN `post_process` is invoked on a storage whose `max_post_process_passes`
   is `0`, THEN `post_process` SHALL complete without raising `UnboundLocalError`
   (or any other error caused by an unset internal substitution flag).
2. WHEN the configured maximum number of refinement passes is `0`, THEN
   `post_process` SHALL treat the refinement loop as having produced no
   outstanding substitutions and SHALL NOT yield a
   `RuntimeError('Max post-process passes exceeded.')`.
3. WHEN `collectstatic` runs against a storage whose `max_post_process_passes`
   is `0` and there are static files to collect, THEN the command SHALL finish
   successfully and its output SHALL report that files were post-processed.
4. WHEN `max_post_process_passes` is `0`, THEN `post_process` SHALL still perform
   the initial single pass over the collected files and SHALL still yield every
   adjustable file under its final hashed name (i.e. the files are still hashed
   and reported), even though no reference-rewriting refinement passes are run.

## Requirement 2: The substitution flag is always defined before it is inspected

**User story:** As a maintainer, I want the flag that records whether references
were still changing to have a well-defined value regardless of how many
refinement passes ran, so that the post-loop check never reads an uninitialized
variable.

**Acceptance criteria**

1. The system SHALL initialize the refinement loop's substitution flag to a
   "no substitutions" (false) value before the refinement loop begins, so that
   the flag has a defined value even when the loop body executes zero times.
2. WHEN the refinement loop executes at least one pass, THEN the post-loop
   substitution flag SHALL reflect the outcome of the most recently executed
   pass (true if that pass produced any substitution, otherwise false), exactly
   as before.
3. WHEN the refinement loop executes zero passes, THEN the post-loop
   substitution flag SHALL have its initial false value.

## Requirement 3: Preserve existing refinement behavior for positive pass limits (regression protection)

**User story:** As a maintainer, I want the convergence and error-reporting
behavior for the normal (positive) maximum-pass case to be exactly as before, so
that removing the crash does not change how ordinary post-processing behaves.

**Acceptance criteria**

1. WHILE running the refinement loop with a positive `max_post_process_passes`,
   the storage SHALL re-process the adjustable files once per pass, updating each
   adjustable file's recorded final hashed name to the most recent result.
2. WHEN a refinement pass produces no substitutions, THEN `post_process` SHALL
   stop the refinement loop immediately (before exhausting the remaining passes).
3. IF the refinement loop runs the full `max_post_process_passes` passes and the
   final executed pass still produced substitutions, THEN `post_process` SHALL
   yield `'All', None, RuntimeError('Max post-process passes exceeded.')`.
4. WHEN the refinement loop stops because a pass produced no substitutions, THEN
   `post_process` SHALL NOT yield the max-passes-exceeded error.
5. The system SHALL, in all cases, yield the non-adjustable files and any
   per-file exceptions from the initial pass, and finally yield each adjustable
   file under its final hashed name, and SHALL update the stored mapping of
   hashed files — preserving the existing outputs of `post_process` unchanged
   apart from no longer crashing when the maximum number of passes is `0`.
