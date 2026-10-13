#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-9698 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled function (`getIndexText`) is all R/I (validated by G-CONF). The dotted
name is split deeply (`rsplitLastDot` == `str.rsplit('.', 1)`), the optional
module prefix is modeled deeply (`'.'.join`), and each label is a direct string
concatenation of the gettext format strings. There is therefore no callee
contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-9698",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
