#!/usr/bin/env python
"""G-AX for django__django-15863 — skip stub.

The bundle declares the opaque callee `floatFallback` (the binary64
approximation fallback, `Decimal(str(float(text)))`) but consumes NO value
property of it: the post-patch primary coercion always succeeds for the modeled
input (a finite exact Decimal), so the fallback branch is dead on the live path
and `correct_coerceDecimal` relies only on the structural fact that it is not
reached — never on what it returns. There is therefore no callee contract
(`_prop` axiom) to validate against the real repo. The single R/I leg (the
primary coercion preserves the exact value) is validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15863",
    "reason": "opaque floatFallback carries no consumed value property "
              "(post-patch primary coercion is always taken for the modeled "
              "finite-Decimal input; fallback branch is dead); the R/I leg is "
              "validated by G-CONF",
}))
sys.exit(0)
