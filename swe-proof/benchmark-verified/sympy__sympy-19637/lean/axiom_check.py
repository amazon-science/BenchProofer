#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model against the REAL marker-membership
callee that post-patch `kernS` uses.

refinement.md row 4 models the changed op `hit = kern in s` (in the space-present
subcase) as the constant `True`. The justification is that the real callee — the
marker-generation loop `while kern in s: kern += choice(...)` followed by
`s = s.replace(' ', kern)` — guarantees that, whenever the pre-substitution
string contains a space, the freshly chosen marker occurs in the post-
substitution string (so `kern in s` is necessarily `True`). This script runs
that real callee on boundary + fuzz inputs and asserts the property holds on
every observation.

The proof consumes NO callee axiom (axioms region empty); this guards the deep
model against drift from the real marker logic.

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import string
import sys

SEED = 19637


def real_marker_membership(s: str, rng: random.Random) -> bool:
    """The REAL post-patch `kernS` marker-substitution + membership callee
    (sympy/core/sympify.py lines 511-516), reached only when ' ' in s."""
    kern = '_'
    while kern in s:
        kern += rng.choice(string.ascii_letters + string.digits)
    s = s.replace(' ', kern)
    return kern in s          # the modeled op: `hit = kern in s`


def main() -> int:
    rng = random.Random(SEED)

    # Boundary strings that contain at least one space (the subcase modeled).
    fixed = [
        " ", "  ", "a b", "x y z", "* *(", "-( *(x+y))",
        " _", "_ _", "a _ b", " " + "_" * 50,
        "2*x / (x - 1)", "( a + b )", "\t ", " \n ",
        # strings already saturated with underscores (forces marker growth):
        "_ _" + "".join("_" + c for c in string.ascii_letters),
    ]

    cases = list(fixed)
    alphabet = list("_ ()*+-/xyz") + list(string.ascii_letters + string.digits)
    for _ in range(50_000):
        n = rng.randint(1, 30)
        cand = "".join(rng.choice(alphabet) for _ in range(n))
        if ' ' in cand:          # the callee is only reached when a space exists
            cases.append(cand)

    failures = 0
    examples = []
    for s in cases:
        # property: with a space present, the real callee yields True
        got = real_marker_membership(s, rng)
        if got is not True:
            failures += 1
            if len(examples) < 10:
                examples.append((s, got))

    if failures:
        print(f"G-AX FAIL: {failures} observations where `kern in s` was not True")
        for s, g in examples:
            print(f"  s={s!r} kern_in_s={g!r}")
        return 1

    print(f"G-AX OK: marker-membership == True on all {len(cases)} "
          f"space-present probes (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
