#!/usr/bin/env python3
"""G-CONF — cross-language differential test for django__django-16901.

Builds the R/I shadow of `implementation_xorFallback` (the Lean impl) in Python
and diffs it against the behaviour of the gold `patch.diff` (the patched
`WhereNode.as_sql` XOR fallback) over >=10^5 fuzzed inputs.

Per mapping.md, each child predicate is reduced to the truth value of its
condition on one row, so the modeled input is a list of booleans `cs` and the
modeled output is the boolean "does this row match the combined predicate".

stdlib-only; exit 0 iff zero disagreements.
"""
import json
import random
import sys

SEED = 16901  # pinned in meta.json verifier_pins.conf_seed


def lean_shadow(cs):
    """R/I shadow of implementation_xorFallback (Lean), translated op-for-op."""
    lhs = False
    for c in cs:
        lhs = lhs or c
    rhs_sum = 0
    for c in cs:
        if c:
            rhs_sum = rhs_sum + 1
    if len(cs) > 2:
        rhs = (rhs_sum % 2 == 1)
    else:
        rhs = (rhs_sum == 1)
    return lhs and rhs


def patched_behaviour(cs):
    """Boolean semantics of the patched WhereNode.as_sql XOR fallback.

    Mirrors patch.diff exactly:
      lhs      = OR over children
      rhs_sum  = sum of (1 if child true else 0)
      if len > 2: rhs_sum = rhs_sum % 2          # the Mod(rhs_sum, 2) fix
      rhs      = (rhs_sum == 1)                  # Exact(1, rhs_sum)
      match    = lhs AND rhs
    """
    lhs = any(cs)
    rhs_sum = sum(1 if c else 0 for c in cs)
    if len(cs) > 2:
        rhs_sum = rhs_sum % 2
    rhs = (rhs_sum == 1)
    return lhs and rhs


def main():
    rng = random.Random(SEED)
    N = 120000
    disagreements = []
    checked = 0

    # Exhaustive small cases (lengths 0..12) to nail the boundary at len == 2/3.
    for n in range(0, 13):
        for mask in range(1 << n):
            cs = [bool((mask >> i) & 1) for i in range(n)]
            checked += 1
            if lean_shadow(cs) != patched_behaviour(cs):
                disagreements.append(cs)
            if len(disagreements) > 20:
                break
        if n >= 12 or checked >= 9000:
            break

    # Random fuzz over wider/longer lists.
    while checked < N:
        n = rng.randint(0, 40)
        cs = [rng.random() < 0.5 for _ in range(n)]
        checked += 1
        if lean_shadow(cs) != patched_behaviour(cs):
            disagreements.append(cs)
            if len(disagreements) > 20:
                break

    if disagreements:
        print(json.dumps({
            "status": "fail",
            "inputs": checked,
            "disagreements": len(disagreements),
            "examples": disagreements[:10],
            "seed": SEED,
        }))
        sys.exit(1)

    print(json.dumps({
        "status": "pass",
        "inputs": checked,
        "disagreements": 0,
        "seed": SEED,
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
