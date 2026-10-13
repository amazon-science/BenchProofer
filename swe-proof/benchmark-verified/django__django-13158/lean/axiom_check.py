#!/usr/bin/env python3
"""G-AX skip stub for django__django-13158.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`Query.set_empty`) forces a query — and,
post-fix, every sub-query combined into its result — to return an empty result
set. The behavior the patch changes (recursing the "force empty" into each
combined sub-query) is modeled DEEPLY: the per-node "force own where empty" is the
boolean `selfEmpty := true`, and the recursion is a self-call to
`implementation_makeEmpty`. SPEC_GUIDE §3 forbids axiomatizing the changed
operation.

The unchanged callees contribute no property the proof consumes:
* `where.add(NothingNode(), AND)` is abstracted to `selfEmpty := true` (the single
  touched per-node fact), not an axiomatized callee;
* the `clone()` deep-copy of `combined_queries` is an aliasing-safety prerequisite
  that is automatic under Lean's no-aliasing model (see refinement.md).

There is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean, so
there is nothing for G-AX to validate. The R/I impl is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13158",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "recursion that forces each combined sub-query empty (the changed "
                  "behavior) is modeled deeply (self-call) and the per-node force-"
                  "empty is the boolean selfEmpty, so the impl is all R/I (validated "
                  "by G-CONF against the post-patch set_empty semantics).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
