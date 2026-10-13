#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-8593 — skip stub.

The bundle consumes NO unchanged-callee axiom: the `proof` region of
`correct_collectModuleEntries` needs no property of any opaque callee (the
`axioms` region declares no `opaque`/`axiom … _prop`). The soundness-critical
behaviour the patch changes — attaching each member's recorded documentation
comment to the entry built for it — is modeled DEEPLY and structurally
(`baseTable` carries `doc name` on every entry; the impl builds each entry with
its `doc name`), and SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
operation. The two per-name observations (the member's value lookup and the
recorded documentation comment) are INPUT functions (`val`, `doc`), not callee
contracts the proof consumes. The R leg is validated by G-CONF. There is
therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-8593",
    "reason": "no consumed callee axiom; the per-name value and documentation-comment "
              "observations are plain inputs and the changed entry-construction "
              "(attaching each name's recorded comment) is modeled deeply "
              "(validated by G-CONF)",
}))
sys.exit(0)
