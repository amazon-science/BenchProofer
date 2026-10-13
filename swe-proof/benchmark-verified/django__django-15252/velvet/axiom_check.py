#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15252.

This bundle has NO axioms and NO deep-model references (see mapping.md §3 and
refinement.md §C). The operation under specification is a pure control-flow
decision: the gate at the top of `MigrationExecutor.migrate` is modeled DEEPLY
in `Solution.lean` (the nested-`if` impl region), and the functions it touches
(`has_table`, `ensure_schema`, `_create_project_state`, `check_replacements`)
enter the model only as boolean inputs / tracked effect-observations, never as
contracts the proof consumes.

Therefore G-AX has nothing to execute: there is no axiomatized callee to run the
real repo callee against. The cross-language fidelity of the change is carried
entirely by G-CONF (`conformance_check.py`), which drives the real patched
`migrate`. This script records that fact and exits 0 (vacuously sound).

stdlib only; exit 0.
"""
import sys


def main():
    print("G-AX OK (vacuous): django__django-15252 declares no axioms and no "
          "A-reference deep models. The changed operation is a pure "
          "control-flow gate, modeled deeply in Solution.lean (all I/R legs); "
          "no callee contract is consumed, so there is nothing to validate "
          "against a real repo callee. Cross-language fidelity is checked by "
          "conformance_check.py (G-CONF), not here. See mapping.md §3 / "
          "refinement.md §C.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
