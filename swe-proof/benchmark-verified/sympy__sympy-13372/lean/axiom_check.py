#!/usr/bin/env python3
"""G-AX for sympy__sympy-13372 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
gold fix is a pure control-flow guard: it adds `else: raise NotImplementedError`
to the real and imaginary classification cascades of the `evalf` fallback branch,
introducing no new callee. The only callee on the changed lines
(`._to_mpmath(...)._mpf_`) produces a value the fix never inspects or re-derives;
it is threaded through unchanged as a carried payload, so it is a passthrough,
not an axiomatized contract (SPEC_GUIDE §3). The R/I legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-13372",
    "reason": "no consumed callee axiom and no A-reference; the fix is a pure "
              "control-flow guard, impl is all R/I (validated by G-CONF)",
}))
sys.exit(0)
