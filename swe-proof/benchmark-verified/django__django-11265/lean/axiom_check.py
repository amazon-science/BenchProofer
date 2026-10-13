#!/usr/bin/env python
"""G-AX skip stub for django__django-11265.

No consumed callee axiom is declared in the bundle. Both modeled decisions —
constructing the nested inner query in `split_exclude`, and the leading-join
collapse decision in `trim_start` — are pure functions of observables the routine
already has in hand at the decision point. The repo callees they invoke
(`Query(...)`, `add_filter`, `clear_ordering`, `self.alias_map` lookups,
`join_field.related_fields`) are UNCHANGED by the patch; their relevant outputs
are taken as model inputs. The operations the patch CHANGES (carrying
`_filtered_relations` onto the inner query; the `not first_join.filtered_relation`
guard) are modeled DEEPLY in Lean (A-reference rows) and validated against the
real per-decision behavior by the differential `conformance_check.py` (G-CONF),
not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (both decisions modeled deeply; "
          "validated by G-CONF as A-reference)")
    sys.exit(0)
