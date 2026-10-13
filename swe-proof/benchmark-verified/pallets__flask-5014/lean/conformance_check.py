#!/usr/bin/env python
"""G-CONF: differential conformance for pallets__flask-5014.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_construct` skeleton and diffs it against the REAL patched
`flask.Blueprint` over a boundary matrix of names plus >=1e5 randomized draws.

  observable of `Blueprint.__init__`:
    * constructing `Blueprint(name, __name__)` raises ValueError
      "'name' may not be empty."          -> Except.error BPError.emptyName
    * else it raises ValueError
      "'name' may not contain a dot '.' character."
                                           -> Except.error BPError.dottedName
    * else it constructs successfully, with bp.name == name
                                           -> Except.ok { name }

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import string
import sys

SEED = 20240612
N_RANDOM = 120_000  # >= 1e5


# ---- the modeled validation (post-patch desired behavior) ------------------
# This mirrors problem_spec_construct / implementation_construct in Solution.lean.
def shadow_construct(name):
    if name == "":
        return ("error", "empty")
    if "." in name:
        return ("error", "dotted")
    return ("ok", name)


def real(Blueprint, name):
    try:
        bp = Blueprint(name, __name__)
    except ValueError as e:
        msg = str(e)
        if "may not be empty" in msg:
            return ("error", "empty")
        if "may not contain a dot" in msg:
            return ("error", "dotted")
        raise
    return ("ok", bp.name)


def main():
    from flask import Blueprint

    # boundary matrix
    boundary = [
        "", ".", "..", "a", "ab", "a.b", ".a", "a.", "a.b.c",
        "foo", "foo_bar", "foo-bar", " ", "  ", "\t", " a ",
        "0", "9", "x" * 100, "x." + "y" * 50,
    ]

    rng = random.Random(SEED)
    alphabet = string.ascii_letters + string.digits + "._- "
    cases = list(boundary)
    for _ in range(N_RANDOM):
        # bias toward including '.' and the empty string at the boundaries
        n = rng.randint(0, 8)
        cases.append("".join(rng.choice(alphabet) for _ in range(n)))

    disagreements = 0
    checked = 0
    for name in cases:
        got = real(Blueprint, name)
        exp = shadow_construct(name)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH name={name!r}: real={got} shadow={exp}")

    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s) over {checked} checks")
    return 1


if __name__ == "__main__":
    sys.exit(main())
