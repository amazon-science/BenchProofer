#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16901 -- status=skip.

This bundle has NO axioms and NO deep-model A-references (meta.json
`axioms = []`, `deep_model_references = []`). The patch's behavioral content is a
pure boolean/arithmetic reduction over already-evaluated operand truth values:
the n-ary exclusive-or rewrite computes, per database row, whether an odd number
of the operands hold. The model (`trueCount`, `parityOdd`, and the `oddParityReduce`
method) takes those per-row truth values as free inputs (`children : List Bool`)
and assumes no callee contract, so there is nothing for G-AX to validate.

The SQL constructors the rewrite composes (`Case`/`When`/`Mod`/`Exact`/`reduce`/
`operator.add`/`self.__class__`) run to ASSEMBLE the predicate; they are
unchanged and the model depends on none of their contracts beyond the value-level
bijection of mapping.md section 2. The fidelity of that assembled SQL (that it
evaluates to exactly this boolean per row) is exercised end-to-end by G-CONF
(`conformance_check.py`), which runs the real patched XOR rewrite against an
in-memory SQLite database (no native XOR -> the rewrite branch), and by
G-RESOLVE. See mapping.md section 3 and refinement.md section C.
"""
import sys


def main():
    print("G-AX status=skip: django__django-16901 -- no axioms and no "
          "deep-model A-references; the modeled reduction assumes no callee "
          "contract (mapping.md section 3). Soundness of the assembled SQL is "
          "covered by G-CONF (real patched XOR rewrite over SQLite) + G-RESOLVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
