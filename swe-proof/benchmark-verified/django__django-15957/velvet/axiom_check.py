#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15957 — SKIPPED.

This bundle has NO consumed axiom and NO deep-model A-reference of an outside
callee. The operation the patch changes — converting a single GLOBAL slice of
all prefetched related rows into an independent slice PER GROUP (per
`partition_by=field_name` partition) — is modeled DIRECTLY in Solution.lean by
`groupSlice`/`slicedGroups` (pure `take`/`drop`/`++` over the already-ordered
groups), the I-tagged concrete ops of refinement.md. The ordering machinery the
patch composes with (`queryset.query.get_compiler(...).get_order_by()`) is
UNCHANGED and shared by both the buggy and fixed branches, so the resolved
per-group order enters the model as an abstracted input (the already-ordered
`groups`), tagged R, not as a consumed contract (LESSONS:
abstracted-input-not-axiom). There is therefore no axiom or A-reference to
execute against a real callee.

Soundness of the modeled net effect rests on G-VERIFY (the spec provably forces
`out = slicedGroups low high groups`), G-DIFF (the global-slice prepatch fails
exactly that clause), G-RESOLVE (the real patch resolves the F2P integration
tests), and G-EQ / G-PANEL (the SQL-window ↔ per-group-slice correspondence
narrative). See mapping.md §3 and refinement.md §C.
"""
import sys


def main():
    print("G-AX status=skip: django__django-15957 — no consumed axiom and no "
          "deep-model A-reference. The changed op (per-partition window slice "
          "replacing a global slice) is modeled directly by groupSlice/"
          "slicedGroups; the unchanged ordering machinery is an abstracted "
          "input (tagged R). Nothing to execute against a real callee. "
          "Soundness covered by G-VERIFY + G-DIFF + G-RESOLVE + G-EQ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
