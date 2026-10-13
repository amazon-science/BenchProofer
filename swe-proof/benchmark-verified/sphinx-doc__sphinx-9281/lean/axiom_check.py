#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-9281 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
patch's behaviour — render an enum member as its qualified name `Class.Member`,
and otherwise defer to the existing general-purpose value→text routine — is
modeled DEEPLY: the enum branch is spelled out as the concatenation
`className ++ "." ++ memberName` (== `"%s.%s" % (cls_name, member_name)`), and
the non-enum branch is the opaque `legacyDescription`. SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed op, so there is no callee contract to
validate.

The one `opaque` declared, `legacyDescription` (the unchanged repr-based
rendering tail), carries NO `_prop` axiom: for the `other` kind it appears
verbatim on both sides of the spec equation, and for the `enumMember` kind it is
absent. Since the proof consumes no property of it, it is neither A-consumed nor
A-reference. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-9281",
    "reason": "no consumed callee axiom and no A-reference; the sole opaque "
              "(legacyDescription) carries no asserted property; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
