#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-9296.

Validates, against the REAL callee in-container, the two kind-A obligations the
twin-artifact bundle relies on for the page-traversal model (`model.py`):

  (A-consumed) `page_lookup(number)` is the collection's UNCHANGED page-by-number
      accessor, abstracted to an OPAQUE PURE function of the page number alone.
      The only property the axiom claims (its contract is `Ensures(True)`) is
      that the value produced for a given page number is well defined and does
      not depend on when in the traversal it is observed — i.e. `page(n)` is a
      deterministic function of `n` for a fixed collection. This check asserts
      that determinism on the real `Paginator.page`.

  (A-reference) the deep model `mapped(page_numbers)` (model.py pure region) ==
      the real page traversal: iterating a collection yields, in order, exactly
      one page per page number, namely the page-by-number accessor applied to
      each page number of the collection's ordered page-number run. This check
      asserts that the real `Paginator.__iter__` produces precisely
      `[paginator.page(n) for n in paginator.page_range]`, in order, page-for-
      page (compared by page number and by page content), over a broad sweep of
      collection shapes (object_list length, per_page, orphans,
      allow_empty_first_page) including the empty / single-page / orphan
      boundaries.

The real callee is `django.core.paginator.Paginator` (the module the gold patch
edits); it is importable in the official evaluation container. Exit 0 iff every
obligation holds.
"""
import itertools
import sys

from django.core.paginator import Paginator


def page_signature(page):
    """An observable signature of a single page: its 1-based number plus the
    concrete contents of its object_list (what the F2P test observes via
    `list(next(page_iterator))`)."""
    return (page.number, list(page.object_list))


def check_config(object_list, per_page, orphans, allow_empty_first_page):
    paginator = Paginator(
        object_list, per_page, orphans=orphans,
        allow_empty_first_page=allow_empty_first_page,
    )

    page_numbers = list(paginator.page_range)

    # (A-consumed) determinism of the page-by-number accessor: page(n) observed
    # twice yields the same page (pure function of n for a fixed collection).
    for n in page_numbers:
        a = page_signature(paginator.page(n))
        b = page_signature(paginator.page(n))
        assert a == b, (
            "page_lookup not deterministic for n=%r on config "
            "(len=%d, per_page=%d, orphans=%d, allow_empty=%r): %r vs %r"
            % (n, len(object_list), per_page, orphans,
               allow_empty_first_page, a, b))

    # (A-reference) the deep model `mapped(page_range)` == real __iter__:
    # iterating the collection yields exactly page(n) for each n in page_range,
    # in order.
    expected = [page_signature(paginator.page(n)) for n in page_numbers]
    observed = [page_signature(pg) for pg in paginator]
    assert observed == expected, (
        "real __iter__ disagrees with mapped(page_range) on config "
        "(len=%d, per_page=%d, orphans=%d, allow_empty=%r): "
        "iter gave %r, page-over-page_range gave %r"
        % (len(object_list), per_page, orphans, allow_empty_first_page,
           observed, expected))

    # The traversal length equals the number of page numbers (no page skipped or
    # repeated), and the visited numbers are exactly page_range in order.
    assert [num for (num, _) in observed] == page_numbers, (
        "traversal page numbers != page_range for config "
        "(len=%d, per_page=%d, orphans=%d, allow_empty=%r): %r vs %r"
        % (len(object_list), per_page, orphans, allow_empty_first_page,
           [num for (num, _) in observed], page_numbers))

    return len(page_numbers)


def main():
    # The F2P witness exactly.
    f2p = Paginator([1, 2, 3], 2)
    assert [list(pg) for pg in f2p] == [[1, 2], [3]], (
        "F2P witness failed: iterating Paginator([1,2,3], 2) did not yield "
        "[[1, 2], [3]]")

    checked = 0
    lengths = [0, 1, 2, 3, 4, 5, 7, 10, 11, 20, 23, 50]
    per_pages = [1, 2, 3, 5, 7, 10]
    orphans_opts = [0, 1, 2, 3, 5]
    allow_opts = [True, False]

    for length, per_page, orphans, allow in itertools.product(
            lengths, per_pages, orphans_opts, allow_opts):
        if orphans >= per_page:
            # Django requires orphans < per_page in practice; skip degenerate.
            continue
        object_list = list(range(length))
        check_config(object_list, per_page, orphans, allow)
        checked += 1

    print("G-AX OK: page_lookup determinism + mapped(page_range) == real "
          "Paginator.__iter__ over %d collection configs (incl. F2P witness, "
          "empty / single-page / orphan boundaries)" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
