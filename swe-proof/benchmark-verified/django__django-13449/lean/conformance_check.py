#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_renderWindowSql
against the patch.diff behaviour (post-patch SQLite window-expression rendering).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: render the bare windowed expression
`operand + ' OVER (' + window + ')'`, then — only for a decimal output type —
wrap that whole string in `CAST(... AS NUMERIC)`. We diff that against an
independent reconstruction of the post-patch rendering built from the two literal
templates the real code uses:

  * the window template            : '%(expression)s OVER (%(window)s)'
  * the numeric-cast wrapper        : 'CAST(%s AS NUMERIC)' % sql   (decimal only)

so that the cast spans the ENTIRE windowed expression. Zero disagreements
required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13449          # pinned in mapping.md
N = 120_000           # >= 10^5

WINDOW_TEMPLATE = "%(expression)s OVER (%(window)s)"
CAST_TEMPLATE = "CAST(%s AS NUMERIC)"

# Operand-text alphabet (compiled source-expression SQL such as
# `LAG("t"."amount", 7)`) and window-clause alphabet (PARTITION BY / ORDER BY).
OPERAND_ALPHABET = list('LAGFIRST_VALUE("t"."amount", 7)0123 *')
WINDOW_ALPHABET = list('PARTITION BY ORDER ASC DESC "t"."modified", 0123')


def shadow(operand: str, window: str, is_decimal: bool) -> str:
    """R/I shadow of implementation_renderWindowSql."""
    sql = operand + " OVER (" + window + ")"
    if is_decimal:
        sql = "CAST(" + sql + " AS NUMERIC)"
    return sql


def patched_render(operand: str, window: str, is_decimal: bool) -> str:
    """Independent reconstruction of the post-patch rendering: substitute into the
    window template, then (decimal only) wrap the whole string in the cast."""
    sql = WINDOW_TEMPLATE % {"expression": operand, "window": window}
    if is_decimal:
        sql = CAST_TEMPLATE % sql
    return sql


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        ('LAG("t"."amount", 7)', 'PARTITION BY "t"."modified" ORDER BY "t"."modified" ASC', True),
        ('LAG("t"."amount", 7)', 'PARTITION BY "t"."modified" ORDER BY "t"."modified" ASC', False),
        ("", "", True),
        ("", "", False),
        ("x", "", True),
        ("", "y", True),
        ("LAG(a, 1)", "ORDER BY b", True),
    ]
    cases = fixed + [
        (
            "".join(rng.choice(OPERAND_ALPHABET) for _ in range(rng.randint(0, 30))),
            "".join(rng.choice(WINDOW_ALPHABET) for _ in range(rng.randint(0, 40))),
            rng.random() < 0.5,
        )
        for _ in range(N)
    ]

    for operand, window, is_decimal in cases:
        got = shadow(operand, window, is_decimal)
        want = patched_render(operand, window, is_decimal)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((operand, window, is_decimal), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
