#!/usr/bin/env python3
"""G-CONF for sympy__sympy-18763.

Differential test: the R/I shadow of `implementation_renderRestriction` (the Lean
impl, transcribed in Python) vs an in-process replica of the POST-PATCH
`_print_Subs` assembly. Both consume the already-rendered body markup `inner` and
the parallel rendered LHS/RHS token lists `lhs`/`rhs` (the recursive `self._print`
results, which the fix does not touch — taken as inputs, mapping.md). We fuzz
those string/list inputs and assert byte-identical output over >=1e5 samples.

stdlib-only; exit 0 iff zero disagreements.
"""
import json
import random
import sys

SEED = 18763
N = 100_000


def lean_shadow(inner, lhs, rhs):
    """Transcription of implementation_renderRestriction (the R/I legs)."""
    sep = "\\\\ "  # subsSep : two backslashes + space
    entries = [l + "=" + r for (l, r) in zip(lhs, rhs)]  # subsEntries
    latex_subs = sep.join(entries)
    return ("\\left. \\left(" + inner + "\\right) \\right|_{\\substack{ "
            + latex_subs + " }}")


def patched_replica(inner, lhs, rhs):
    r"""In-process replica of the post-patch `_print_Subs` final assembly.

    Mirrors the repo source exactly:
        latex_subs = r'\\ '.join(e[0] + '=' + e[1]
                                 for e in zip(latex_old, latex_new))
        return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (
            latex_expr, latex_subs)
    """
    latex_subs = r'\\ '.join(a + '=' + b for (a, b) in zip(lhs, rhs))
    return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (inner, latex_subs)


def rand_token(rng):
    alphabet = "xyz01- +*\\(){}=_^"
    n = rng.randint(0, 8)
    return "".join(rng.choice(alphabet) for _ in range(n))


def rand_list(rng):
    n = rng.randint(0, 4)
    return [rand_token(rng) for _ in range(n)]


def main() -> int:
    rng = random.Random(SEED)
    # hand-picked edge cases first
    edge = [
        ("- x + y", ["x"], ["1"]),                 # the F2P case body
        ("x y", ["x", "y"], ["1", "2"]),           # the original docstring case
        ("", [], []),                              # empty body, no assignments
        ("a", ["x", "y"], ["1"]),                  # unequal lengths -> zip truncates
        ("a", ["x"], ["1", "2"]),                  # unequal lengths (other side)
        ("\\frac{1}{2}", ["\\alpha"], ["\\beta"]), # backslashes/braces in tokens
    ]
    disagreements = 0
    first_fail = None
    for (inner, lhs, rhs) in edge:
        if lean_shadow(inner, lhs, rhs) != patched_replica(inner, lhs, rhs):
            disagreements += 1
            if first_fail is None:
                first_fail = (inner, lhs, rhs)
    for _ in range(N):
        inner = rand_token(rng)
        lhs = rand_list(rng)
        rhs = rand_list(rng)
        if lean_shadow(inner, lhs, rhs) != patched_replica(inner, lhs, rhs):
            disagreements += 1
            if first_fail is None:
                first_fail = (inner, lhs, rhs)

    status = "pass" if disagreements == 0 else "fail"
    print(json.dumps({
        "status": status,
        "instance": "sympy__sympy-18763",
        "samples": N + len(edge),
        "seed": SEED,
        "disagreements": disagreements,
        "first_fail": first_fail,
    }))
    return 0 if disagreements == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
