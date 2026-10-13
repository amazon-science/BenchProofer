#!/usr/bin/env python3
"""G-AX skip stub for django__django-11490.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (the per-part column-propagation loop of
`SQLCompiler.get_combinator_sql`) reads one thing off each part — whether it
already fixes a column list — and produces the query used for this evaluation
plus the part definition carried forward. A query part is observed solely by the
list of columns it projects (`QueryPart.columns <-> Query.values_select); the
callees `Query.set_values` / `Query.clone` are NOT modeled as opaque callees —
their only observable contribution is the resulting query's column list, captured
directly. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The R/I impl (and its
binding to the real patched propagation) is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11490",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "column-propagation loop's callees (set_values/clone) contribute "
                  "only the resulting column list, captured directly, so the impl "
                  "is all R/I (validated by G-CONF against the real patched "
                  "propagation)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
