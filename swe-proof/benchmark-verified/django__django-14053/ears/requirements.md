# Requirements: `post_process()` must report each post-processed file only once

## Introduction

`HashedFilesMixin.post_process()` in
`django/contrib/staticfiles/storage.py` is the generator that
`ManifestStaticFilesStorage` and `CachedStaticFilesStorage` use to rename static
files to include a content hash and to rewrite intra-file references to those
hashed names. It is invoked by the `collectstatic` management command's
`collect()` method (in
`django/contrib/staticfiles/management/commands/collectstatic.py`), which
consumes the generator's yielded `(name, hashed_name, processed)` records and
uses them to build the post-processing statistics reported to the user.

To resolve nested references between files, `post_process()` runs several passes:
an initial pass over all matched files, followed by up to
`max_post_process_passes` additional passes over the "adjustable" files (those
whose contents may contain references needing rewriting, as selected by matching
the mixin's configured patterns). Because a file that is rewritten in more than
one pass was previously yielded once per pass, `post_process()` emitted the same
original file name multiple times, sometimes with different (intermediate) hashed
names.

This causes: (1) `collectstatic`'s summary counts to overstate the number of
post-processed files, since it counts one yield per post-processed file;
(2) subclasses and third-party storage backends that act on each yielded file to
perform duplicate work (e.g. recompressing or re-uploading the same file); and
(3) an inconsistent view, since only some intermediate hashed names are yielded.

The goal is to make `post_process()` report each original file name **exactly
once**, carrying its **final** hashed name, while preserving the multi-pass
reference-rewriting logic and all existing behavior for non-adjustable files,
error reporting, and pass-exhaustion signaling.

## Requirement 1: Each post-processed original file is reported exactly once

**User story:** As a developer running `collectstatic`, I want each static file
to be reported as post-processed only once, so that the summary counts are
accurate and downstream consumers do not do duplicate work.

**Acceptance criteria**

1. WHEN `post_process()` completes for a given set of input paths, THEN the
   generator SHALL yield at most one record whose original name equals any given
   original file name, excluding error records described in Requirement 4.
2. The collection of original names contained in the records yielded by
   `post_process()` SHALL contain no duplicates (each distinct original name
   appears no more than once).
3. WHEN a file is adjusted (its references rewritten) across more than one pass,
   THEN `post_process()` SHALL still yield exactly one record for that file's
   original name, not one record per pass.
4. WHEN a file is adjustable but requires no rewriting after its first pass,
   THEN `post_process()` SHALL yield exactly one record for that file's original
   name.

## Requirement 2: Reported hashed name is the final hashed name

**User story:** As a consumer of `post_process()` output, I want the hashed name
reported for a file to be its final content-hashed name, so that I never act on
a superseded intermediate name.

**Acceptance criteria**

1. WHEN an adjustable file is processed across multiple passes and its hashed
   name changes between passes, THEN the single record yielded for that file
   SHALL carry the hashed name produced by the last pass in which it was
   processed.
2. The system SHALL NOT yield any record carrying an intermediate hashed name
   that was later superseded within the same `post_process()` invocation for the
   same original file.
3. WHEN a file's hashed name is unchanged across passes, THEN the record yielded
   for it SHALL carry that hashed name.

## Requirement 3: First-encounter ordering and correct processed flag preserved

**User story:** As a maintainer relying on stable, predictable output, I want the
reporting order and processed status to remain meaningful, so that existing
behavior and tests continue to hold.

**Acceptance criteria**

1. The single record yielded for each original file SHALL carry the `processed`
   status observed for that file in the last pass in which it was processed.
2. The system SHALL preserve the association between each original name and its
   corresponding `(hashed_name, processed)` values, so that no record mixes one
   file's name with another file's hashed name or processed flag.

## Requirement 4: Non-adjustable files and errors are still reported immediately and once

**User story:** As a developer, I want files that never needed reference
rewriting, and any errors, to continue to be reported as before, so that
behavior for the common case and error visibility are unchanged.

**Acceptance criteria**

1. WHEN a file matched for post-processing is not an adjustable file, THEN
   `post_process()` SHALL yield exactly one record for that file (as it did
   before), and SHALL NOT defer or duplicate it.
2. IF processing a file produces an error condition (the processed value is an
   exception), THEN `post_process()` SHALL yield that error record for the
   file's original name without suppressing or deduplicating it away.
3. The system SHALL continue to yield a record signaling that the maximum number
   of post-processing passes was exceeded WHEN substitutions were still occurring
   after the final allowed pass.

## Requirement 5: Multi-pass reference rewriting behavior is preserved

**User story:** As a Django user, I want nested references between static files
to still be correctly rewritten to hashed names, so that fixing the duplicate
reporting does not regress correctness.

**Acceptance criteria**

1. The system SHALL continue to perform an initial post-processing pass over all
   matched files followed by additional passes over adjustable files until no
   further substitutions occur or the maximum number of passes is reached.
2. WHEN all passes complete, THEN the final hashed name recorded for each
   processed file SHALL be stored so that later lookups resolve references to the
   final hashed names.
3. The system SHALL preserve, for `dry_run` mode, its existing behavior of
   performing no post-processing and yielding nothing.
