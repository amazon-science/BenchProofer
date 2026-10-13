#!/usr/bin/env python3
"""G-AX for django__django-13212 — SKIP STUB.

The bundle consumes no callee axiom and declares no A-reference callee
(meta.json: axioms = [], deep_model_references = []). The single changed
operation — attaching the rejected input to a failed validation's substitution
params (`params={'value': value}`) — is a pure data construction over the inputs,
modeled DEEPLY in `implementation_validate` as `baseParams ++ [('value',
value)]`. The validity verdict is carried as the `accepted` input (the patch does
not alter how validity is decided). There is therefore no real callee whose
contract must be validated.

stdlib-only; exits 0 with status=skip.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13212",
        "reason": "no consumed axiom or A-reference callee; the changed op is a "
                  "pure data construction (baseParams ++ [('value', value)]) and "
                  "the validity verdict is an input, not an axiomatized callee.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
