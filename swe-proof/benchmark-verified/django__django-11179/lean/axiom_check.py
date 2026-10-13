#!/usr/bin/env python3
"""G-AX skip stub for django__django-11179.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`Collector.delete`) removes a batch of
collected records and, as a side effect, clears each removed record's primary-key
attribute. The behavior the patch changes — clearing the removed record's key on
the single-object fast path before its early return — is modeled DEEPLY
(`{ inst with pk := none }` on the fast path, `clearAllPks` on the general path);
SPEC_GUIDE §3 forbids axiomatizing the changed operation.

The unchanged callees contribute no property the proof consumes:
* `can_fast_delete` is the universally-quantified predicate `directlyDeletable`
  (the spec holds for every such predicate, pinning only that the fast path
  clears the key);
* `delete_batch` / `_raw_delete` produce the row counts, abstracted as the
  parameters `directCount` / `generalTotal`.

There is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean, so
there is nothing for G-AX to validate. The R/I impl (and its binding to the real
patched routing of the pk-clear) is differential-tested by conformance_check.py
(G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11179",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "primary-key clearing (the changed side effect) is modeled "
                  "deeply (pk := none / clearAllPks), and the fast-delete decision "
                  "and row counts are universally-quantified parameters, so the "
                  "impl is all R/I (validated by G-CONF against the real patched "
                  "delete()).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
