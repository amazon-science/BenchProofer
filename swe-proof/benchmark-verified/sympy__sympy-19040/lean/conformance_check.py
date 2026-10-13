#!/usr/bin/env python3
"""G-CONF for sympy__sympy-19040 — skip stub.

conf_skip = true (meta.json). The Lean `implementation_extFactor` region routes
values among UNCHANGED, fully abstract polynomial-algebra callees
(`groundLC`, `groundMonic`, `degreeList`, `sqfPart`, `sqfNorm`,
`factorListInclude`, `raiseShift`, `recoverOne`, `trialDivision`) declared as
`opaque`. The modeled behaviour is exactly the data routing among them — which
polynomial flows into the square-free-norm step (the full monic original, not its
principal-variable square-free part). Every impl op is A-reference or a trivial
accumulator init/append; there is NO R/I data transformation that computes a
concrete observable value in Lean independently of the real callees, hence
nothing to transliterate into a Python shadow and differential-test.

SPEC_GUIDE §3/§4: an all-A-tagged impl region sets conf_skip=true and ships this
skip stub. The routing contract is pinned by `problem_spec_extFactor` and
discharged by `correct_extFactor` (verify⟹correct); G-DIFF shows the prepatch
(square-free-norm of the square-free part) violating the discriminating clause,
and patch.diff (gold) carries the behavioural equivalence (G-RESOLVE/G-GOLD).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-19040",
    "reason": "impl region all-A-tagged (abstract polynomial-algebra callees + "
              "data routing); no R/I content to differential-test "
              "(conf_skip=true)",
}))
sys.exit(0)
