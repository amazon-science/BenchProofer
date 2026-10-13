#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7910.

This bundle has NO axiomatized callees and NO A-reference deep models of an
external callee (mapping.md §3, refinement.md §C). The only operation the gold
patch changes — which namespace the owner-class lookup consults: the target's
own namespace vs the namespace of the object it stands for once any wrapper is
seen through (`obj.__globals__` -> `inspect.unwrap(obj).__globals__`) — is
modeled DEEPLY and CONCRETELY in Solution.lean (`inclusionDecision` and its
helpers `containerPath` / `isMultiSegment` / `scopeOwns` / `ownerIn` /
`categoryEnabled` over the `Context` / `DocTarget` / `Decision` carriers). The
surrounding per-object machinery (attribute lookups, importlib/functools walk,
the unwrap step, `__dict__` membership) is UNCHANGED by the patch and is
abstracted to the recorded structural fields the branch inspects; it is exercised
by G-CONF (conformance_check.py), not asserted as an axiom.

There is therefore nothing to validate against a real callee: G-AX is vacuous.
This script emits status=skip, as recorded in meta.json (axioms: [],
deep_model_references: [], G-AX.status="skip").
"""
import json
import sys


def main():
    result = {
        "instance": "sphinx-doc__sphinx-7910",
        "status": "skip",
        "reason": ("no axioms and no A-reference deep models of an external "
                   "callee; the changed owner-lookup namespace (the target's own "
                   "scope vs the unwrapped object's scope) is modeled deeply "
                   "(inclusionDecision/ownerIn over directScope vs resolvedScope) "
                   "and validated structurally by G-CONF, not against a real "
                   "callee"),
        "axioms_checked": 0,
        "deep_model_references_checked": 0,
    }
    print(json.dumps(result))
    print("G-AX SKIP: no callee axioms to validate (see mapping.md §3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
