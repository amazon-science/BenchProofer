#!/usr/bin/env python3
"""G-CONF for sympy__sympy-21379 — skip stub.

conf_skip = true (meta.json). The Lean `implementation_factorReduce` region
forwards two fully abstract unchanged callees (`extractFactor` ↔ `gcd(p, q)`,
`reduceByFactor` ↔ `gcd_terms(i/G, clear=False, fraction=False)`) and merely
routes between them on whether `extractFactor` signalled failure
(PolynomialError). There is NO R/I data transformation to transliterate into a
Python shadow — every impl op is A-reference or a trivial accumulator
init/return. SPEC_GUIDE §3/§4: an all-A-tagged impl region sets conf_skip=true
and ships this skip stub. The routing/toleration contract is pinned by
`problem_spec_factorReduce` and discharged by `correct_factorReduce`
(verify⟹correct); G-DIFF shows the prepatch (which propagates the failure)
violating the discriminating clause.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-21379",
    "reason": "impl region all-A-tagged (abstract callees + control-flow "
              "routing); no R/I content to differential-test (conf_skip=true)",
}))
sys.exit(0)
