#!/usr/bin/env python3
"""G-AX skip stub for django__django-9296.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (walking a paginated collection page by
page) is the iteration protocol the patch adds. The behavior it drives — the
page count, the 1-based page numbering, and the per-page slice of items — is
modeled DEEPLY by the pure helpers `pageCount` / `pageNumbers` / `pageSlice`
(arithmetic + list slicing) over the four input data (SPEC_GUIDE §3: a
deeply-modeled callee is never axiomatized).

The unchanged callees the new iteration drives (`num_pages`, `page_range`,
`page(n)`) contribute no property the proof consumes: they are pure functions of
`(object_list, per_page, orphans, allow_empty_first_page)` and are reproduced
exactly by the pure helpers. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The R/I impl (and its binding to the real patched paginator) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-9296",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "page count, 1-based page numbering, and per-page slice driven "
                  "by the added iteration protocol are modeled deeply (pageCount "
                  "/ pageNumbers / pageSlice), so the impl is all R/I (validated "
                  "by G-CONF against the real patched paginator iteration)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
