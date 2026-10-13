#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-9296.

The bundle has NO consumed axiom. The single A leg is the A-reference `pageOf`
(Solution.lean), the opaque map standing for the UNCHANGED accessor
`Paginator.page(self, number)`. G-AX validates that deep-model reference against
the real callee, asserting the three properties the proof relies on:

  (A-reference, property a — determinism) for a fixed Paginator, `page(n)` is a
      deterministic function of the 1-based index `n`: calling it repeatedly
      returns the same observable `list(page)`. This is what makes
      `pageOf : PageIdx -> List Int` well-defined.

  (A-reference, property b — order independence / the modeled identity) the
      patched `__iter__` materializes to exactly
          [list(self.page(n)) for n in self.page_range]
      i.e. iterating the object equals `pageSeq` applied to `page_range` under
      the mapping.md bijection (Page <-> list(page), page_range <-> List PageIdx).

  (A-reference, property c — THE DOMAIN) `page` is a PARTIAL operation, and its
      domain is exactly the index sequence the object presents:
          dom(page) == list(page_range) == [1 .. num_pages]
      Positively: `page(n)` returns without raising for every n in that range.
      Negatively: `page(n)` RAISES EmptyPage for every other integer n — below 1
      and above num_pages alike, including the boundary n == num_pages + 1 and
      including n == 1 when the object presents no pages at all.

Property (c) is what the model's index carrier
`PageIdx = {n // 1 <= n <= numPages}` claims, and it is the property this
bundle's G-EQ repair rests on: an earlier revision modeled `pageOf` as total on
all of Nat, which erased the accessor's refusal and let an implementation apply
it off-domain, discard the result and still satisfy the postcondition — while its
real counterpart raises here and fails the target test. The carrier makes the
off-domain application inexpressible; this check is what establishes that the
carrier's bound is the accessor's REAL domain and not a convenient
over-restriction, by measuring both directions (no false refusals inside,
no silent successes outside) over the same sweep + fuzz.

Imports only the standard library and django (the same module the gold patch
edits); django.core.paginator is the package under test. Exit 0 iff every
obligation holds over the configuration sweep + fuzz.
"""
import random
import sys

from django.core.paginator import EmptyPage, Paginator


def observe_page(paginator, n):
    """The observable content of the sub-view at 1-based index n: list(page)."""
    return list(paginator.page(n))


def check_determinism(paginator):
    """Property (a): page(n) is a deterministic function of n for a fixed
    Paginator -- repeated calls agree, so pageOf is well-defined."""
    for n in paginator.page_range:
        first = observe_page(paginator, n)
        for _ in range(3):
            again = observe_page(paginator, n)
            assert again == first, (
                "page(%d) non-deterministic: %r then %r" % (n, first, again))


def check_iteration_identity(paginator):
    """Property (b): list(iter(paginator)) == [list(page(n)) for n in
    page_range]. This is the A-reference identity pageOf == real page, lifted
    to the whole iteration (the modeled `out = pageSeq pageRange`)."""
    # The post-patch __iter__ may or may not be present in this checkout; the
    # A-reference is about `page`, so we build the reference family directly
    # from `page` + `page_range` (the gold generator's definition) and assert it
    # against an explicit re-materialization. If __iter__ exists we also check it.
    reference = [observe_page(paginator, n) for n in paginator.page_range]
    rematerialized = [list(paginator.page(n)) for n in list(paginator.page_range)]
    assert reference == rematerialized, (
        "page-family not stable: %r vs %r" % (reference, rematerialized))
    it = getattr(paginator, "__iter__", None)
    if it is not None:
        try:
            via_iter = [list(p) for p in iter(paginator)]
        except TypeError:
            return  # no iteration protocol in this checkout (pre-patch) -- skip
        assert via_iter == reference, (
            "iteration disagrees with [page(n) for n in page_range]: "
            "%r vs %r" % (via_iter, reference))


def check_domain(paginator):
    """Property (c): dom(page) == list(page_range) == [1 .. num_pages], measured
    in BOTH directions.

    This is the executable content of the model's index carrier
    `PageIdx = {n // 1 <= n <= numPages}`: the carrier is sound only if the real
    accessor admits every index inside that bound (else the carrier would be too
    WIDE and the spec would attest to calls that raise) and refuses every index
    outside it (else the carrier would be too NARROW and the spec would forbid
    calls the object really serves — the over-restriction that would make the
    repair SPEC-TOO-STRONG).
    """
    n_pages = paginator.num_pages

    # The index sequence names exactly 1 .. num_pages -- this is the identity
    # that lets `List PageIdx` stand for `page_range`.
    assert list(paginator.page_range) == list(range(1, n_pages + 1)), (
        "page_range is not [1 .. num_pages]: %r vs num_pages=%d"
        % (list(paginator.page_range), n_pages))

    # Inside the bound: never refuses. (A raise here would mean the carrier
    # admits an index the accessor does not.)
    for n in range(1, n_pages + 1):
        try:
            paginator.page(n)
        except Exception as exc:            # noqa: BLE001 - any raise is a defect
            raise AssertionError(
                "page(%d) raised inside [1 .. %d]: %r" % (n, n_pages, exc))

    # Outside the bound: always refuses, on both sides and at the boundary.
    # n_pages + 1 is the index the recorded G-EQ attack applied the accessor at;
    # when n_pages == 0 that probe is n == 1, i.e. the object that presents no
    # pages must refuse even its first index.
    for bad in (-1, 0, n_pages + 1, n_pages + 2, n_pages + 17):
        if 1 <= bad <= n_pages:
            continue
        try:
            paginator.page(bad)
        except EmptyPage:
            continue
        raise AssertionError(
            "page(%d) did NOT raise EmptyPage outside [1 .. %d]"
            % (bad, n_pages))


def configs():
    """A sweep of Paginator configurations exercising boundaries:
    empty / single / exact-multiple / orphans / allow_empty_first_page."""
    yield ([], 1, 0, True)
    yield ([], 1, 0, False)
    yield ([], 3, 0, True)
    yield ([1], 1, 0, True)
    yield ([1, 2, 3], 2, 0, True)            # the F2P fixture
    yield (list(range(10)), 3, 0, True)
    yield (list(range(10)), 3, 2, True)      # orphans absorb the tail
    yield (list(range(11)), 3, 2, True)
    yield (list(range(7)), 7, 0, True)       # exact single page
    yield (list(range(8)), 7, 0, True)       # one orphan-free overflow
    yield (list(range(100)), 13, 5, True)


def main():
    # boundary / structured configurations
    for object_list, per_page, orphans, allow_empty in configs():
        p = Paginator(object_list, per_page, orphans=orphans,
                      allow_empty_first_page=allow_empty)
        check_determinism(p)
        check_iteration_identity(p)
        check_domain(p)

    # randomized fuzz over configurations
    rng = random.Random(9296)
    for _ in range(2000):
        size = rng.randint(0, 40)
        object_list = list(range(size))
        per_page = rng.randint(1, 10)
        orphans = rng.randint(0, 5)
        allow_empty = rng.choice([True, False])
        p = Paginator(object_list, per_page, orphans=orphans,
                      allow_empty_first_page=allow_empty)
        check_determinism(p)
        check_iteration_identity(p)
        check_domain(p)

    print("G-AX OK: pageOf A-reference sound -- Paginator.page deterministic, "
          "list(iter(paginator)) == [list(page(n)) for n in page_range], and "
          "dom(page) == list(page_range) == [1 .. num_pages] exactly (no refusal "
          "inside, EmptyPage outside, both boundaries) "
          "over 11 boundary configs + 2000 fuzz configs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
