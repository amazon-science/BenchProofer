#!/usr/bin/env python3
"""G-AX soundness check for sphinx-doc__sphinx-8621 — NO AXIOMS (skip stub).

This bundle declares no `axiom` and no A-reference deep model of an outside
callee (mapping.md §3, refinement.md §C). The single changed operation — the
segmentation of a `:kbd:` keystroke string into its keys and the connector
characters joining them, where a connector (`-`, `+`, `^`) is treated as a
separator ONLY when it sits strictly between two keys (a character precedes it
and a character follows it), and otherwise as an ordinary key character — is
modeled DEEPLY in Solution.lean's `pure` region (`isSep`, `splitParts`),
entirely from concrete character operations over the input sequence. Per
directive 7 the operation the patch changes is never axiomatized, and the
segmentation calls no outside callee, so there is nothing for G-AX to validate
against a real callee.

The deep model's fidelity to the patched behaviour is instead exercised
mechanically by conformance_check.py (G-CONF), which drives the REAL patched
`KeyboardTransform.pattern.split` and diffs it against the R/I transliteration
over >=10^5 fuzzed inputs in the modeled (no-whitespace) keystroke domain.

Exit 0 with a skip status (meta.json gates.G-AX.status = "skip").
"""
import sys


def main():
    print("G-AX SKIP: no axioms / no A-reference in this bundle; the changed "
          "keystroke segmentation is modeled deeply (pure region) and checked "
          "by G-CONF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
