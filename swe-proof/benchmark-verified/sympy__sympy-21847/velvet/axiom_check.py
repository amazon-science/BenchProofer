#!/usr/bin/env python3
"""G-AX soundness check for sympy__sympy-21847 — NO AXIOMS (skip stub).

This bundle declares no `axiom` and no A-reference deep model of an outside
callee (mapping.md §3, refinement.md §C). The single changed operation — the
per-candidate keep decision that compares a candidate's total degree against the
lower bound — is modeled DEEPLY in Solution.lean's `pure` region
(`totalDegree`, `selectByDegree`), entirely from concrete arithmetic over the
inputs. Per directive 7 the operation the patch changes is never axiomatized, so
there is nothing for G-AX to validate against a real callee.

The surrounding machinery the change does NOT touch — the candidate enumerator
(`itertools.combinations_with_replacement` / `product`), the per-candidate
counting loop, the term constructor `Mul`, and the final `set(...)` dedup — is
abstracted into the free `candidates` input; the spec makes no behavioural claim
about it and holds for every candidate list, so there is nothing to check.

The deep model's fidelity to the patched behaviour is instead exercised
mechanically by conformance_check.py (G-CONF), which drives the REAL patched
`itermonomials` and diffs it against the R/I transliteration over >=10^5 fuzzed
inputs across both the commutative and non-commutative enumerations.

Exit 0 with a skip status (meta.json gates.G-AX.status = "skip").
"""
import sys


def main():
    print("G-AX SKIP: no axioms / no A-reference in this bundle; the changed "
          "degree threshold is modeled deeply (pure region) and checked by "
          "G-CONF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
