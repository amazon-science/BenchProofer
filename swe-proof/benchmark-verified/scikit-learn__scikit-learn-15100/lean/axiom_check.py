#!/usr/bin/env python3
"""G-AX — scikit-learn__scikit-learn-15100.

This bundle consumes NO callee axiom. The two unchanged callees the function
reads — `unicodedata.normalize('NFKD', ·)` and `unicodedata.combining(·)` — enter
the executable impl as opaque references (`canonDecompose`, `isCombiningMark`),
but `correct_stripAccents` consumes NO property of either (spec and impl are
structurally identical and the proof closes by `split <;> rfl`). They are
A-references, validated against the real `unicodedata` routines by G-CONF, not
axiomatized. The `axioms` region of Solution.lean declares only their `opaque`
signatures; no `axiom <callee>_prop` is shipped.

So G-AX has nothing to validate: it is a skip stub.
"""
import json
import sys

if __name__ == "__main__":
    print(json.dumps({
        "status": "skip",
        "instance": "scikit-learn__scikit-learn-15100",
        "reason": "no consumed callee axiom; the unchanged unicodedata callees are "
                  "A-references (validated by G-CONF against the real routines)",
    }))
    sys.exit(0)
