#!/usr/bin/env python3
"""G-AX for pydata__xarray-6599 — skip stub.

The bundle consumes NO unchanged-callee axiom property. The only opaque callee,
`datetimeToFloat` (the unchanged `datetime_to_numeric` reduction used for the
datetime branch), appears IDENTICALLY in the spec helper `coerceResult` and in
`implementation_coerceToFloat`, so the datetime branch closes by reflexivity and
the proof consumes no `_prop` of it (it is an A-reference carried by signature,
not an A-consumed axiom). The only CHANGED branch — the duration cast — is
modeled DEEPLY as `raw.map Float.ofInt` (SPEC_GUIDE §3 forbids axiomatizing the
changed op). There is thus no callee contract to validate against the real repo;
the R legs (branch selection + duration cast) are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pydata__xarray-6599",
    "reason": "no consumed callee axiom and no A-reference _prop; the unchanged "
              "datetime callee is carried identically in spec and impl (closes "
              "by reflexivity) and the changed duration branch is modeled deeply "
              "(validated by G-CONF)",
}))
sys.exit(0)
