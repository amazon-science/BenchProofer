#!/usr/bin/env python3
"""G-AX skip stub for django__django-13406.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (the `QuerySet.query` setter) calls nothing:
it reads one attribute off the installed query (`value.values_select`, modeled as
`StoredQuery.selectedFields`) and performs two state assignments (store the query;
conditionally switch the row-building strategy). The available row-building
strategies (`ModelIterable`, `ValuesIterable`, `ValuesListIterable`,
`FlatValuesListIterable`, `NamedValuesListIterable`) are sentinel class objects
that are *assigned*, never invoked, so they are modeled directly as the
constructors of `RowMode` in Solution.lean. There is no `opaque` callee and no
`axiom <callee>_prop`, so there is nothing for G-AX to validate. The whole impl is
R/I content, differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13406",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "query setter calls nothing and the impl is all R/I (validated "
                  "by G-CONF against the real patched setter)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
