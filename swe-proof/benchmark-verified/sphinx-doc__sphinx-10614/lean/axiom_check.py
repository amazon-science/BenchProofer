#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-10614 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled behavior (`buildUrls`) is all R/I (validated by G-CONF). Splitting a URI
at its final fragment separator is modeled deeply (`uriTail` == `str.rsplit('#',
1)[-1]`), and every link string is a direct concatenation of the inputs. There
is therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-10614",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
