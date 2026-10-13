#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-10466.

Differential test: the R/I shadow of `implementation_dedupSort` (built in Python
from the Lean ops) vs the gold patch.diff behaviour, over >=1e5 fuzzed inputs.

  * gold behaviour (patch.diff, gettext.py:60):
        positions = sorted(set((source, line) for source, line, uuid in triples))
  * Lean-shadow (Solution.lean `implementation_dedupSort`):
        project each triple to (source, line) in order, then List.dedup, then
        List.mergeSort with lexLe = lexicographic ((source <), tie-break line <=).

`sorted` on (str,int) tuples is exactly lexicographic tuple comparison, which is
what lexLe encodes; after dedup the elements are distinct so comparator ties
never arise. The two must agree on every input. stdlib-only; exit 0 iff zero
disagreements.
"""
import functools
import json
import random
import sys

SEED = 1046620250630  # pinned (mapping.md)
N = 120_000


def lex_le(a, b):
    """Lean lexLe as a cmp-style bool: True iff a <= b lexicographically."""
    if a[0] == b[0]:
        return a[1] <= b[1]
    return a[0] < b[0]


def lex_cmp(a, b):
    if a == b:
        return 0
    return -1 if lex_le(a, b) else 1


def lean_shadow(triples):
    # op2: project each triple to (source, line), order-preserving
    pairs = []
    for (source, line, _uuid) in triples:
        pairs.append((source, line))
    # op3: List.dedup (keep first occurrence, drop later repeats)
    seen = set()
    deduped = []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    # op4: List.mergeSort lexLe
    return sorted(deduped, key=functools.cmp_to_key(lex_cmp))


def gold(triples):
    # patch.diff: sorted(set((source, line) for source, line, uuid in triples))
    return sorted(set((source, line) for (source, line, _uuid) in triples))


def main():
    rng = random.Random(SEED)
    # bias toward collisions: small alphabets so duplicate (source,line) are common
    sources = ["", "a", "b", "ab", "/p/x.rst", "/p/y.rst", "../../m/hair.rst"]
    lines = [-3, -1, 0, 0, 1, 1, 2, 2, 5, 92, 121, 1000]
    mismatches = 0
    examples = []

    # structured boundary cases first
    boundary = [
        [],
        [("a", 0, "u0")],
        [("a", 1, "u0"), ("a", 1, "u1")],                      # exact dup pos, diff uuid
        [("a", 2, "u0"), ("a", 1, "u1")],                      # out-of-order line
        [("b", 0, "u0"), ("a", 0, "u1")],                      # out-of-order source
        [("a", 1, "u0"), ("a", 1, "u1"), ("a", 2, "u2"),
         ("b", 1, "u3")],                                      # the F2P "hello" case
        [("a", 0, "u")] * 6,                                   # heavy repetition
    ]
    for t in boundary:
        if lean_shadow(t) != gold(t):
            mismatches += 1
            if len(examples) < 10:
                examples.append({"input": t, "shadow": lean_shadow(t), "gold": gold(t)})

    for _ in range(N):
        n = rng.randint(0, 12)
        triples = []
        for _ in range(n):
            triples.append((rng.choice(sources), rng.choice(lines),
                            "u%d" % rng.randint(0, 10_000)))
        if lean_shadow(triples) != gold(triples):
            mismatches += 1
            if len(examples) < 10:
                examples.append({"input": triples,
                                 "shadow": lean_shadow(triples),
                                 "gold": gold(triples)})

    status = "pass" if mismatches == 0 else "fail"
    print(json.dumps({
        "status": status,
        "instance": "sphinx-doc__sphinx-10466",
        "cases": N + len(boundary),
        "mismatches": mismatches,
        "examples": examples,
        "seed": SEED,
    }))
    sys.exit(0 if mismatches == 0 else 1)


if __name__ == "__main__":
    main()
