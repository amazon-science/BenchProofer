#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12039.

This bundle has NO axiomatized callees and NO deep-model A-references
(mapping.md §3). The single modeled operation is the *changed* op itself
(`Columns.__str__.col_str`'s per-column rendering), spelled out deeply as
`columnText` in Solution.lean and validated against the real patched behaviour
by G-CONF (conformance_check.py) — not by an axiom. The unchanged callee
`quote_name` is absorbed into the input carrier `name` (an R-refinement,
identity in G-CONF), so it carries no contract to discharge.

There is therefore nothing for G-AX to check. We emit status=skip
(reason="no-axioms") and exit 0, mirroring the conf/mut skip convention
recorded in meta.json. The full soundness weight for the R/I refinement legs
falls on G-CONF; there are no A legs.
"""
import json
import sys


def main():
    print(json.dumps({
        "gate": "G-AX",
        "status": "skip",
        "reason": "no-axioms",
        "detail": ("django__django-12039 has no axiomatized callees and no "
                   "A-reference deep models; the changed op is modeled deeply "
                   "(columnText) and checked by G-CONF. Nothing to verify."),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
