#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_buildCallSql
against the patch.diff behaviour (post-patch aggregate-call rendering).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op (concatenate function, '(', the DISTINCT slot, the
argument text, ')'), with the DISTINCT slot computed exactly as the patched line
sets `extra_context['distinct']`. We diff that against an independent
reconstruction of the post-patch rendering: substitution of the three slots into
the literal template '%(function)s(%(distinct)s%(expressions)s)' with
`distinct = 'DISTINCT ' if distinct else ''`. Zero disagreements required over
>=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 10880          # pinned in mapping.md
N = 120_000           # >= 10^5

TEMPLATE = "%(function)s(%(distinct)s%(expressions)s)"

# Function-name alphabet (SQL identifiers) and an expression-text alphabet that
# oversamples a leading letter so the missing-separator bug is observable
# (DISTINCTCASE vs DISTINCT CASE).
FUNC_NAMES = ["COUNT", "SUM", "AVG", "MAX", "MIN", "STDDEV_POP", "VAR_SAMP", "F"]
EXPR_ALPHABET = list("CASE WHEN END *abcXYZ_, 0123()'\"")


def distinct_slot(distinct: bool) -> str:
    """Exactly the patched assignment: extra_context['distinct']."""
    return "DISTINCT " if distinct else ""


def shadow(function: str, distinct: bool, expressions: str) -> str:
    """R/I shadow of implementation_buildCallSql."""
    slot = ""
    if distinct:
        slot = "DISTINCT "
    return function + "(" + slot + expressions + ")"


def patched_render(function: str, distinct: bool, expressions: str) -> str:
    """Independent reconstruction of the post-patch rendering: substitute the
    three slots into the literal template via Python %-formatting."""
    return TEMPLATE % {
        "function": function,
        "distinct": distinct_slot(distinct),
        "expressions": expressions,
    }


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        ("COUNT", True, "CASE WHEN T.pages > 300 THEN T.rating ELSE NULL END"),
        ("COUNT", False, "CASE WHEN T.pages > 300 THEN T.rating ELSE NULL END"),
        ("COUNT", True, "*"),
        ("COUNT", False, "*"),
        ("SUM", True, ""),
        ("AVG", False, "T.col"),
        ("F", True, "x"),
    ]
    cases = fixed + [
        (
            rng.choice(FUNC_NAMES),
            rng.random() < 0.5,
            "".join(rng.choice(EXPR_ALPHABET) for _ in range(rng.randint(0, 30))),
        )
        for _ in range(N)
    ]

    for function, distinct, expressions in cases:
        got = shadow(function, distinct, expressions)
        want = patched_render(function, distinct, expressions)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((function, distinct, expressions), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
