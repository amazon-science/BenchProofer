#!/usr/bin/env python
"""G-AX for django__django-14493 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function
(`ManifestFilesMixin.post_process`) is modeled DEEPLY. The modeled behavior is
the bounded refinement loop's own control flow — a flag initialized before the
loop, overwritten once per pass with that pass's substitution outcome, with an
early `break` when a pass produces none, and the loop bounded by
`max_post_process_passes`. The per-pass content work (`self._post_process` over
the collected files) is abstracted as the input `passSubst`, not axiomatized.

There is no `axiom <callee>_prop` for the proof to consume, so there is nothing
to validate. (The deep model IS validated against the post-patch loop behavior
by G-CONF / conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
