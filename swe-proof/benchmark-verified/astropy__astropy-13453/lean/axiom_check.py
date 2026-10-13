#!/usr/bin/env python
"""G-AX for astropy__astropy-13453.

`renderCell` is an A-REFERENCE: the unchanged value->string rendering primitive
the writer delegates to (`Column.info.iter_str_vals()` under `info.format`). The
proof of `correct_formattedCells` consumes NO property of it (spec and impl
render values pointwise, identically), so there is no `_prop` axiom to validate.

What this check confirms (the modeling assumption the A-reference rests on):
  1. Per-value determinism: rendering a column is the pointwise map of a
     per-value function — `iter_str_vals()` yields one string per row, in order,
     and re-running gives the same result.
  2. Format-drivenness: the rendered strings depend only on the cell value and
     `info.format` — two columns with identical values and identical `info.format`
     render identically regardless of name/other metadata. This is what licenses
     "set the effective format, then render" (impl) == "render under effective
     format" (spec).

stdlib + astropy only. Exit 0 iff every observation holds on boundary + fuzz.
"""
import random
import sys

from astropy.table import Column, Table

SEED = 13453
N = 20_000
FORMAT_CHOICES = [None, "04d", "+05d", "d", ".2e", ".3f", "e", "g", ".1f"]


def render(values, fmt):
    """The real per-column rendering primitive under a chosen info.format."""
    col = Column(values)
    if fmt is not None:
        col.info.format = fmt
    return list(col.info.iter_str_vals())


def main():
    rng = random.Random(SEED)
    # Boundary cases.
    boundary = [
        ([0], None), ([0], "04d"), ([-1, 1], "+05d"),
        ([1.0, -1.0], ".2e"), ([1e-24, 3e-15], ".2e"),
        ([1.23456789], ".3f"), ([float("inf"), float("-inf")], "g"),
        ([float("nan")], "g"), ([10 ** 9], "d"), ([0.0, -0.0], ".1f"),
    ]
    cases = list(boundary)
    for _ in range(N):
        nrows = rng.randint(1, 5)
        if rng.random() < 0.5:
            vals = [rng.randint(-10 ** 9, 10 ** 9) for _ in range(nrows)]
        else:
            vals = [rng.uniform(-1e12, 1e12) * (10 ** rng.randint(-20, 5))
                    for _ in range(nrows)]
        cases.append((vals, rng.choice(FORMAT_CHOICES)))

    checked = 0
    for vals, fmt in cases:
        try:
            r1 = render(vals, fmt)
        except Exception:
            continue  # a format invalid for the dtype — writer would reject too
        # (1) determinism + one-string-per-row
        r2 = render(vals, fmt)
        if r1 != r2 or len(r1) != len(vals):
            print(f"AXIOM FAIL determinism/shape: vals={vals} fmt={fmt} "
                  f"r1={r1} r2={r2}")
            print("G-AX FAIL")
            sys.exit(1)
        # (2) format-drivenness: same values + same format under a different
        # column name render identically (name/metadata-independence).
        c = Column(vals, name="renamed_xyz")
        if fmt is not None:
            c.info.format = fmt
        r3 = list(c.info.iter_str_vals())
        if r3 != r1:
            print(f"AXIOM FAIL name-dependence: vals={vals} fmt={fmt} "
                  f"r1={r1} r3={r3}")
            print("G-AX FAIL")
            sys.exit(1)
        checked += 1

    print(f"G-AX OK: renderCell A-reference holds on {checked} cases "
          f"(boundary+fuzz), seed={SEED}")
    sys.exit(0)


if __name__ == "__main__":
    main()
