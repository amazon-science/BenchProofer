#!/usr/bin/env python3
"""G-AX soundness check for django__django-16136 — SKIP (no axioms).

This bundle declares no `axiom` and no A-reference deep model of an outside
callee (see mapping.md §3 / refinement.md §B). The two callees the modeled
handler touches — `self._allowed_methods()` and `self.view_is_async` — are
UNCHANGED and are taken as read-only free inputs (`allowed`, `asynchronous`)
owed no contract; the only behaviour under spec (how the 405 response is handed
back) is modeled deeply by `deliverNotAllowed`. There is therefore nothing to
check against a real callee. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("G-AX SKIP: no axioms / no A-reference in this bundle "
          "(unchanged callees modeled as free inputs; changed delivery modeled "
          "deeply). status=skip")
    sys.exit(0)
