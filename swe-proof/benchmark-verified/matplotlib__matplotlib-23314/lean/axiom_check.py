#!/usr/bin/env python
"""G-AX — matplotlib__matplotlib-23314. SKIP STUB.

The bundle consumes NO callee axiom. The single modeled function
(`Axes3D.draw`) is a pure early-return guard on the visibility flag
(refinement.md op #1 = R). The unchanged remainder of `draw` is held as the
opaque A-reference `renderContents` (op #2), on which the spec and proof assert
NO property — it supplies only the "shown" output value. There is therefore no
`axiom <callee>_prop` for the proof to consume and nothing for G-AX to validate.

(The R guard IS validated against the post-patch control flow by G-CONF /
conformance_check.py.)

Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({"status": "skip",
                  "reason": "no consumed callee axiom; the guard is all-R and "
                            "the unchanged body is an unconstrained A-reference"}))
sys.exit(0)
