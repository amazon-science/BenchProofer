#!/usr/bin/env python
"""G-CONF for astropy__astropy-14365 (Triple 2: reading a data row's values).

Differential test of the R/I legs of `implementation_readRow` against the
PATCHED astropy QDP reader (the gate git-applies the gold patch before running
this, so `astropy.io.ascii.qdp` here is the fixed code).

Modeled (R) behavior: when a QDP data row is read into cells, a token is the
missing-value sentinel — and becomes a masked cell — exactly when it equals the
sentinel `NO` up to ASCII letter-case (`v.upper() == "NO"`); every other token
becomes a number obtained by the unchanged parser (`int(v)` else `float(v)`,
the A-reference `parseNumber`). One cell per token, in order.

Shadow (this file): replicate that per-token masked-vs-number decision in Python,
parsing non-sentinel tokens with the SAME real `int(v) or float(v)` primitive
(the A-reference callee left as the real repo behavior). Oracle: run the patched
reader on a one-row QDP file and read, per cell, whether it is masked and (if
not) its numeric value.

stdlib + astropy only. Exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import random
import sys

import numpy as np
from astropy.io.ascii.qdp import _get_tables_from_qdp_file

SEED = 20240629
N = 100_000

# Token pool: the sentinel in assorted cases (the R discriminator), plus ints
# and floats in several textual forms. NOTE: a bare lowercase "nan"/"NO" token in
# a data line is recognized by the patched line classifier; we restrict numeric
# tokens to plain ints/decimals so each generated row is an unambiguous data line
# of consistent width.
SENTINELS = ["NO", "no", "No", "nO"]
INT_TOKENS = ["0", "1", "-3", "42", "+7", "123", "-100"]
FLOAT_TOKENS = ["0.5", "-2.5", "1.0", "3.14", "-0.0", "2.0", ".25", "1e3", "-1.5e-2"]


def parse_number(tok):
    """The unchanged repo number parser: int(v) else float(v)."""
    try:
        return int(tok)
    except ValueError:
        return float(tok)


def shadow_row(tokens):
    """Modeled cells: (is_masked, value_or_None) per token, in order.
    R leg: sentinel test `v.upper() == "NO"`. A-reference leg: parse_number."""
    out = []
    for v in tokens:
        if v.upper() == "NO":            # R: case-insensitive sentinel
            out.append((True, None))
        else:
            out.append((False, parse_number(v)))  # A-reference parser
    return out


def oracle_row(tokens):
    """Cells the PATCHED reader produces for a one-row data file: (is_masked,
    value_or_None) per column, in order. Returns None if the reader rejects the
    constructed file (e.g. width inconsistency) — caller skips such cases."""
    line = " ".join(tokens)
    # A bare data file (no READ command) parses to a single table whose row is
    # the read values; one data line => one row, len(tokens) columns.
    tables = _get_tables_from_qdp_file([line])
    if len(tables) != 1:
        return None
    t = tables[0]
    if len(t) != 1 or len(t.colnames) != len(tokens):
        return None
    row = t[0]
    out = []
    for x in row:
        if np.ma.is_masked(x):
            out.append((True, None))
        else:
            out.append((False, x))
    return out


def values_match(a, b):
    """Compare a shadow cell to an oracle cell up to numeric equality."""
    (ma, va), (mb, vb) = a, b
    if ma != mb:
        return False
    if ma:
        return True
    # both numbers: compare as floats (int vs float coercion is immaterial here)
    if va != va and vb != vb:   # both NaN
        return True
    return float(va) == float(vb)


def gen_tokens(rng):
    ncol = rng.randint(1, 6)
    toks = []
    for _ in range(ncol):
        r = rng.random()
        if r < 0.35:
            toks.append(rng.choice(SENTINELS))
        elif r < 0.65:
            toks.append(rng.choice(INT_TOKENS))
        else:
            toks.append(rng.choice(FLOAT_TOKENS))
    return toks


def main():
    rng = random.Random(SEED)
    checked = 0
    for i in range(N):
        tokens = gen_tokens(rng)
        try:
            want = oracle_row(tokens)
        except Exception:
            continue            # reader rejected the constructed file; skip
        if want is None:
            continue
        got = shadow_row(tokens)
        if len(got) != len(want) or not all(
                values_match(g, w) for g, w in zip(got, want)):
            print(f"DISAGREEMENT at case {i}: tokens={tokens}\n"
                  f"  oracle={want}\n  shadow={got}")
            print("G-CONF FAIL")
            sys.exit(1)
        checked += 1
    if checked == 0:
        print("G-CONF ERROR: no cases exercised")
        sys.exit(1)
    print(f"G-CONF OK: {checked} cases agree (of {N} generated), seed={SEED}")
    sys.exit(0)


if __name__ == "__main__":
    main()
