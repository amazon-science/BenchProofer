#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-22871 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
behavior the patch changes is how two reads of a tick-component column are
COMBINED to decide whether the separate summary (year) label is shown: pre-patch
hides it whenever the varying component is year/month; post-patch additionally
requires that the value `1` occurs in that component. Both reads — the
distinct-value count and the `== 1` membership — are modeled DEEPLY in
`Solution.lean` (`List.dedup.length` and `List.contains 1` over the column taken
as input), not axiomatized. There is thus no callee property to validate against
the real repo. The R legs (the whole level/offset decision loop) are validated by
G-CONF, which transliterates the real patched decision loop and diffs the chosen
`(level, show_offset)`.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-22871",
    "reason": "no consumed callee axiom and no A-reference; np.unique/np.any "
              "reads are modeled deeply (dedup.length / contains 1) over the "
              "input column, and the decision loop is all R/I (validated by "
              "G-CONF)",
}))
sys.exit(0)
