#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-11510 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
patch's behaviour — joining the included lines minus the two trailing markers,
offering that body to the source-read hook, re-splitting the rewritten text and
re-attaching the markers, all gated on a listener being registered — is modeled
DEEPLY over the inputs (`joinLines`, `splitLines`, the `take`/`drop` marker
boundary, the `hasListeners` gate). SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed op, so there is no callee contract to validate.

The one `opaque` declared, `pathToDocname` (the unchanged path->docname
derivation), carries NO `_prop` axiom: it enters only as an opaque tag in the
emitted payload, which the spec pins to `pathToDocname path`. Since the proof
consumes no property of it, it is neither A-consumed nor A-reference. The R legs
are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-11510",
    "reason": "no consumed callee axiom and no A-reference; the sole opaque "
              "(pathToDocname) carries no asserted property; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
