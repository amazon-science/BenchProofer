#!/usr/bin/env python3
"""G-AX skip stub for sphinx-doc__sphinx-8621.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior is the token list produced by the post-patch
`KeyboardTransform.pattern.split(text)`. The operation the gold patch changes is
the split pattern itself (`re.compile(r'(-|\\+|\\^|\\s+)')` ->
`re.compile(r'(?<=.)(-|\\+|\\^|\\s+)(?=.)')`), so it is modeled DEEPLY in
Solution.lean (the `step`/`finalize` deferred-fold tokenizer that reproduces the
lookbehind/lookahead/greedy-`\\s+` semantics) rather than axiomatized
(SPEC_GUIDE 0.7 — never axiomatize the operation the patch changes). The input
text enters as an arbitrary `List Char`, and `implementation_tokenizeKeystrokes`
is definitionally `specSplit text`, so `correct_tokenizeKeystrokes` consumes no
property of any opaque callee. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.

The deep model's fidelity to the real changed callee is differential-tested by
conformance_check.py (G-CONF), whose ORACLE is the REAL post-patch `re.split`.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-8621",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "changed split pattern is modeled deeply (the step/finalize "
                  "tokenizer reproducing the (?<=.)...(?=.) lookaround + greedy "
                  "\\s+ semantics) and validated by G-CONF against the real "
                  "post-patch re.split, so the impl is all R/I",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
