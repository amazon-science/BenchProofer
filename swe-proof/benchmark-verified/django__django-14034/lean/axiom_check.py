#!/usr/bin/env python3
"""G-AX for django__django-14034 — SKIP STUB.

The modeled decision (where the HTML required marker is placed) consumes no
unchanged callee's *behavior* as an axiom. The only unchanged callee involved,
`Widget.use_required_attribute(initial)`, has its boolean result supplied as an
INPUT to the model (`widgetUseReq` / `subUseReq`; see mapping.md) — it is fed in,
not recomputed — and the differential `conformance_check.py` (G-CONF) bridges it
by driving the REAL method with that boolean. There are therefore no
`axiom <callee>_prop` declarations in Solution.lean and nothing for G-AX to
validate. Exit 0 with status=skip. stdlib-only.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (the required-marker predicate "
          "result is taken as an input and bridged by G-CONF)")
    sys.exit(0)
