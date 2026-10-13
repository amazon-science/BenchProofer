# Requirements: Iterating a Paginator over its pages

## Introduction

The pagination utility in `django/core/paginator.py` exposes a `Paginator`
class that splits an `object_list` into fixed-size pages. Today, walking every
page requires manually looping over the `page_range` property and calling
`page(number)` for each number. This is awkward and non-idiomatic: consumers
expect that a collection-like object can be walked directly with a Python
`for` loop (or `iter()` / `next()`).

The goal is to make a `Paginator` instance directly iterable so that iterating
it produces each of its pages, in page-number order, without changing any of
the existing paging arithmetic, validation, or warning behavior. The affected
module is `django/core/paginator.py`; the affected type is `Paginator`. The
per-page contents, page numbering, page counting, and validation all continue
to be governed by the existing `page`, `page_range`, `num_pages`, `count`, and
`validate_number` members.

## Requirement 1: Paginator is directly iterable over its pages

**User story:** As a developer using Django pagination, I want to iterate a
`Paginator` instance directly with a normal Python loop, so that I can walk
every page without manually referencing `page_range` and calling `page()`.

**Acceptance criteria**

1. The `Paginator` type SHALL support Python iteration protocol, such that
   passing a `Paginator` instance to `iter()` returns an iterator.
2. WHEN a `Paginator` instance is iterated (e.g. `for page in paginator`,
   `iter(paginator)`, `list(paginator)`), THEN it SHALL yield one `Page`
   object per page number in the paginator's `page_range`.
3. WHEN a `Paginator` instance is iterated, THEN the pages SHALL be produced in
   ascending page-number order, beginning at page number 1 and following the
   same ordering as `page_range`.
4. WHEN the iterator yields the page for a given page number, THEN that yielded
   object SHALL be identical in contents to the object returned by calling
   `page(number)` for that same page number — i.e. the same page slice of
   `object_list`, in the same order.
5. WHEN the object list is divided into a final partial page, THEN iterating
   SHALL yield that final page containing exactly the trailing remainder of
   items (honoring the existing `orphans` allowance), consistent with
   `page(num_pages)`.
6. WHEN a `Paginator` has exactly one page, THEN iterating it SHALL yield
   exactly that single page and then stop.
7. IF the paginator's `page_range` is empty (no pages), THEN iterating the
   `Paginator` SHALL yield no pages and terminate immediately.
8. WHEN iteration is performed lazily via `next()` on the paginator's iterator,
   THEN each successive call SHALL return the next page in order, and the
   iterator SHALL raise `StopIteration` after the last page has been produced.

## Requirement 2: Existing paging behavior is preserved

**User story:** As a maintainer, I want the new iteration support to add
behavior without altering any existing pagination semantics, so that current
code relying on the `Paginator` and `Page` API continues to work unchanged.

**Acceptance criteria**

1. The `page_range` property SHALL continue to return a 1-based range of page
   numbers from 1 through `num_pages` inclusive.
2. The `num_pages` property SHALL continue to compute the total number of pages
   from `count`, `per_page`, `orphans`, and `allow_empty_first_page`, including
   returning 0 pages when the collection is empty and empty first pages are not
   allowed.
3. The `count` property SHALL continue to report the total number of objects
   across all pages.
4. WHEN `page(number)` is called, THEN it SHALL continue to validate the number
   and return the `Page` for that 1-based page number with the same slice of
   `object_list` as before.
5. WHEN `validate_number` receives a value that is not an integer, THEN it
   SHALL raise `PageNotAnInteger`; WHEN it receives a number less than 1 or a
   number greater than the available pages (outside the allowed-empty-first-page
   case), THEN it SHALL raise `EmptyPage`.
6. WHEN `get_page(number)` is called with an out-of-range or non-integer value,
   THEN it SHALL continue to return a valid page (page 1 for non-integers, the
   last page for out-of-range numbers) rather than raising.
7. IF an unordered `object_list` (such as an unordered QuerySet) is paginated,
   THEN the paginator SHALL continue to emit an `UnorderedObjectListWarning`.
8. The `Page` object SHALL continue to expose its existing behavior — length,
   indexing, `has_next`/`has_previous`/`has_other_pages`,
   `next_page_number`/`previous_page_number`, and `start_index`/`end_index` —
   unchanged.
