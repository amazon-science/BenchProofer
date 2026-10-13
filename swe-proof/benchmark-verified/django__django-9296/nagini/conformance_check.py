#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-9296 (nagini).

SHADOW: the impl region of `model.py::paginate_iter`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. After
stripping, the impl body uses only plain-list operations, so no PSeq shim is
needed (`PSeq`/`mapped` appear only inside contracts). The single
@ContractOnly callee, `page_lookup`, calls the REAL repo accessor
`Paginator.page` of the collection under test (dispatched through a module
global bound per generated collection), per its binding in mapping.md.

ORACLE: the real patched traversal of the collection — consuming
`iter(paginator)` left-to-right — for `django.core.paginator.Paginator`, the
function the model models per mapping.md/refinement.md. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. This script does NOT apply the patch itself.

Type bridge (mapping.md section 2):
  * `page_numbers: List[int]` <- the materialized elements of the collection's
    `page_range` (`list(paginator.page_range)`).
  * each traversal item (a rich Page object) <- an opaque per-page-number
    value; realized here as the page's observable signature
    `(page.number, list(page.object_list))`, a pure function of the page
    number for a fixed collection (the property G-AX validated).
  * the traversal generator <- the ordered list of yielded values.

Input domain: the model's Requires asks only for a well-formed read-only
input list; bridged through mapping.md the inputs are collection
configurations (object_list length, per_page, orphans,
allow_empty_first_page) whose `page_range` supplies the page-number run.
Generation covers the empty / single-page / orphan boundaries plus the F2P
witness shape, and restricts orphans < per_page (the swept operating domain,
matching axiom_check.py).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz configs.
Pinned fuzz seed: 9296.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

from django.core.paginator import Paginator  # REAL patched repo module

SEED = 9296
N_FUZZ = 100_000


# --- @ContractOnly callee bridge: page_lookup -> real Paginator.page ---------

_CURRENT_PAGINATOR = None


def page_signature(page):
    """Observable signature of one traversal item: its 1-based number plus the
    concrete contents of its object_list (what the F2P test observes)."""
    return (page.number, list(page.object_list))


def page_lookup(number):
    """The model's @ContractOnly page-by-number accessor: calls the REAL repo
    function on the collection currently under test and abstracts the rich
    result to an opaque value (the page signature)."""
    return page_signature(_CURRENT_PAGINATOR.page(number))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def paginate_iter(page_numbers):
    result = []  # type: list
    i = len(page_numbers)
    while i > 0:
        x = page_numbers[i - 1]
        result = [page_lookup(x)] + result
        i = i - 1
    return result


# --- differential check --------------------------------------------------------

def check_config(object_list, per_page, orphans, allow_empty_first_page):
    """Run shadow and oracle on one collection configuration; return an error
    string on disagreement, else None."""
    global _CURRENT_PAGINATOR
    paginator = Paginator(
        object_list, per_page, orphans=orphans,
        allow_empty_first_page=allow_empty_first_page,
    )
    _CURRENT_PAGINATOR = paginator

    # Bridge: the ordered run of page numbers, materialized.
    page_numbers = list(paginator.page_range)

    shadow = paginate_iter(page_numbers)

    # Oracle: the real patched traversal, consumed left-to-right and each
    # yielded item abstracted to the same opaque signature.
    real = [page_signature(pg) for pg in paginator]

    if shadow != real:
        return ("DISAGREEMENT\n"
                "  config: object_list=%r per_page=%r orphans=%r "
                "allow_empty_first_page=%r\n"
                "  page_numbers=%r\n"
                "  shadow=%r\n"
                "  real=%r"
                % (object_list, per_page, orphans, allow_empty_first_page,
                   page_numbers, shadow, real))
    return None


def boundary_configs():
    """Hand-picked boundary collection shapes (object_list, per_page, orphans,
    allow_empty_first_page)."""
    return [
        ([], 1, 0, True),            # empty collection, one empty page
        ([], 1, 0, False),           # empty collection, empty traversal
        ([], 5, 2, True),
        ([], 5, 2, False),
        ([1], 1, 0, True),           # single item, single page
        ([1], 1, 0, False),
        ([1], 10, 0, True),
        ([1, 2, 3], 2, 0, True),     # the F2P witness shape: pages [1,2],[3]
        ([1, 2, 3], 2, 0, False),
        ([1, 2, 3, 4], 2, 0, True),  # exact multiple: no partial last page
        ([1, 2, 3, 4, 5], 2, 1, True),   # orphan absorbed into last page
        ([1, 2, 3, 4, 5], 2, 1, False),
        (list(range(10)), 3, 2, True),
        (list(range(11)), 5, 4, True),   # orphans just under per_page
        (list(range(50)), 7, 3, True),
        (list(range(100)), 1, 0, True),  # many single-item pages
        (["a", "b", "c"], 2, 0, True),   # non-int contents
        ([(1, 2), (3, 4), (5, 6)], 1, 0, True),
    ]


def rand_config(rng):
    length = rng.randint(0, 30)
    per_page = rng.randint(1, 8)
    orphans = rng.randint(0, per_page - 1)
    allow = rng.random() < 0.5
    if rng.random() < 0.1:
        object_list = [rng.randint(-5, 5) for _ in range(length)]
    else:
        object_list = list(range(length))
    return object_list, per_page, orphans, allow


def main():
    checked = 0
    boundaries = boundary_configs()
    for cfg in boundaries:
        err = check_config(*cfg)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_config(*rand_config(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real traversal on %d collection configs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundaries), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly page_lookup -> real "
                                "Paginator.page)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
