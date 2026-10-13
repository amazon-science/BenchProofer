#!/usr/bin/env python3
"""G-AX skip stub for django__django-16255.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`Sitemap.get_latest_lastmod`) makes a pure
decision over `(hasattr(self,"lastmod"), callable(self.lastmod), the per-item
timestamp list, the fixed-timestamp value)` — what optional timestamp to report —
and the only non-trivial sub-expression is the empty-safe greatest-of-a-list,
which is modeled DEEPLY as `List.max?` (no axiom). The act of producing the
per-item timestamp list (`self.items()` / `self.lastmod(item)`) is abstracted to
its result and supplied as the input carrier; it is not modeled or axiomatized.
There is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean, so
there is nothing for G-AX to validate. The decision (and its empty-collection
boundary) is differential-tested against the real patched `get_latest_lastmod`
by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-16255",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "latest-timestamp report is a pure decision with the empty-safe "
                  "greatest-of-a-list modeled deeply as List.max?, so the impl is "
                  "all R/I (validated by G-CONF against the real "
                  "Sitemap.get_latest_lastmod).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
