#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14007 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (`list[tuple]` rows;
              per-column converter chains), via the mapping.md bijection
              (`List (List Int)` ↔ rows, `List (Int -> Int)` ↔ column→callable).
              The impl's computed `out` is the backward `while` fold building
              `convertRows convs rows`; transliterated, it is the loop below.
  * ORACLE  — `patch.diff`'s behaviour: the conversion the patched
              `execute_sql` performs on the assembled rows, i.e.
              `if converters: rows = list(apply_converters(rows, converters))`.
              `apply_converters` is the A-reference callee (deep-modeled), so the
              oracle runs the REAL `apply_converters` body (reproduced verbatim,
              as in axiom_check.py) — G-CONF holds the R/I legs to the real
              callee's behaviour.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib only; seed pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 14007
N_FUZZ = 100_000


# --- ORACLE: patch.diff conversion behaviour (real apply_converters) ---------
# apply_converters body verbatim from django/db/models/sql/compiler.py:1110,
# wrapped by the patch's `if converters:` guard (`get_converters` returns {}
# when no field defines a converter -> rows returned unchanged).
def real_apply_converters(rows, converters):
    converters = list(converters.items())
    out = []
    for row in map(list, rows):
        for pos, (convs, expression) in converters:
            value = row[pos]
            for converter in convs:
                value = converter(value, expression, None)
            row[pos] = value
        out.append(row)
    return out


def oracle(convs, rows):
    converters = _to_real_converters(convs, _ncols(rows))
    if converters:                       # patch's `if converters:` guard
        return real_apply_converters(rows, converters)
    return [list(r) for r in rows]


def _ncols(rows):
    return max((len(r) for r in rows), default=0)


def _to_real_converters(convs, ncols):
    converters = {}
    for j in range(min(len(convs), ncols)):
        f = convs[j]
        converters[j] = ([(lambda val, expr, conn, _f=f: _f(val))], object())
    return converters


# --- SHADOW: Solution.lean impl region, transliterated -----------------------
# convertRow : per-position transform, short converter list passes through.
def _convert_row(convs, row):
    out = []
    for j, v in enumerate(row):
        out.append(convs[j](v) if j < len(convs) else v)
    return out


# the `do` block: backward while loop prepending each converted row.
def shadow(convs, rows):
    result = []
    i = len(rows)
    while i > 0:
        row = rows[i - 1]
        result = [_convert_row(convs, row)] + result
        i = i - 1
    return result


def main():
    rng = random.Random(SEED)

    ident = lambda v: v
    inc = lambda v: v + 1
    dbl = lambda v: v * 2
    neg = lambda v: -v
    sq = lambda v: v * v
    POOL = [ident, inc, dbl, neg, sq]

    disagreements = 0
    first = None
    for _ in range(N_FUZZ):
        ncols = rng.randint(0, 4)
        nconvs = rng.randint(0, ncols + 1)
        convs = [rng.choice(POOL) for _ in range(nconvs)]
        nrows = rng.randint(0, 4)
        rows = [[rng.randint(-1000, 1000) for _ in range(ncols)] for _ in range(nrows)]

        s = shadow(convs, rows)
        o = oracle(convs, rows)
        if s != o:
            disagreements += 1
            if first is None:
                first = (convs, rows, s, o)

    if disagreements == 0:
        print(f"G-CONF OK: R/I shadow of transformedResultRows agrees with "
              f"patch.diff behaviour on {N_FUZZ} inputs (seed={SEED}), "
              f"0 disagreements.")
        return 0
    convs, rows, s, o = first
    print(f"G-CONF FAIL: {disagreements}/{N_FUZZ} disagreements (seed={SEED}). "
          f"First: rows={rows}\n  shadow={s}\n  oracle={o}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
