#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20428.

This bundle has NO axiomatized callees and NO A-reference deep model of an
external callee (mapping.md §3, refinement.md §C). The only operation the gold
patch changes — the truth value of a symbolic field element in
`ExpressionDomain.Expression.__bool__`, switched from `f.ex != 0` (a structural
comparison against the literal zero) to `not f.ex.is_zero` (the mathematical /
identical zero test) — is modeled DEEPLY and CONCRETELY in Solution.lean
(`nonzeroSpec` over the `SymExpr` carrier, whose two fields `identicallyZero` /
`literalZero` are the two zero-observations the surrounding, UNCHANGED machinery
exposes).

The two zero-tests themselves (`expr.is_zero` and `expr == 0`) are primitive
observations of the element, not callees the changed function delegates a
contract to; they are abstracted to the two `SymExpr` booleans and exercised
structurally by G-CONF (conformance_check.py), which both differential-tests the
shadow against the real patched `__bool__` AND asserts the load-bearing modeling
invariant `literalZero -> identicallyZero` over boundary + 10^5 fuzzed real
`EX(expr)` elements. There is therefore nothing to validate against a real callee
here: G-AX is vacuous.

This script emits status=skip, as recorded in meta.json (axioms: [],
deep_model_references: [], G-AX.status="skip").
"""
import json
import sys


def main():
    result = {
        "instance": "sympy__sympy-20428",
        "status": "skip",
        "reason": ("no axioms and no A-reference deep models of an external "
                   "callee; the changed element truth value (is_zero vs "
                   "!=literal-0) is modeled deeply (nonzeroSpec over SymExpr) "
                   "and validated structurally by G-CONF, including the "
                   "modeling invariant literalZero -> identicallyZero, not "
                   "against a real callee"),
        "axioms_checked": 0,
        "deep_model_references_checked": 0,
    }
    print(json.dumps(result))
    print("G-AX SKIP: no callee axioms to validate (see mapping.md §3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
