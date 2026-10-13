#!/usr/bin/env python
"""G-AX for django__django-15572 — SKIP STUB.

The bundle declares NO consumed callee axioms. The one modeled function collects
template directory paths by filtering and normalizing directory entries. The two
unchanged callees it uses — the path normalizer (`cwd / to_path(d)`) and the
framework-path predicate (`is_django_path`) — are modeled as
universally-quantified PARAMETERS of the spec/impl (`resolveDir`,
`isFrameworkPath`). Because the contract is stated for ANY such functions, the
proof consumes no property of either, so there is no `axiom <callee>_prop` to
validate.

(The R/I behavior is validated against the post-patch decision by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (callees are abstract parameters)")
sys.exit(0)
