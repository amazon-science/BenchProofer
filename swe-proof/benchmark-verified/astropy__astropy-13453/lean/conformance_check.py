#!/usr/bin/env python
"""G-CONF for astropy__astropy-13453.

Differential test of the R/I legs of `implementation_formattedCells` against the
PATCHED astropy HTML writer (the gate git-applies the gold patch before running
this, so `astropy.io.ascii` here is the fixed code).

Modeled (R) behavior: when writing a table to HTML, each column's displayed
cell strings honor the user-supplied per-column `formats` mapping — the
effective format for a column is the requested format if the column's name is a
key of `formats`, else the column's pre-existing `info.format`.

Shadow (this file): replicate that selection logic in Python, rendering each
column's values with the REAL repo rendering primitive (`col.info.iter_str_vals`
under the chosen `info.format` — the A-reference callee). Compare the resulting
row-major cell strings against the `<td>` contents the patched writer emits.

stdlib + astropy only. Exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import io
import random
import re
import sys

from astropy.table import Table

SEED = 13453
N = 100_000

FORMAT_CHOICES = ["04d", "+05d", "d", ".2e", ".3f", "e", "g", ".1f", "6.2f"]
NAME_POOL = ["C1", "C2", "col_a", "b", "X", "value", "n"]

_TD = re.compile(r"<td>(.*?)</td>", re.DOTALL)


def shadow_cells(table, formats):
    """Row-major list of cell strings produced by the modeled logic, using the
    real per-column rendering primitive."""
    cols = list(table.columns.values())
    # R legs 1-3: apply requested format by name (override only when requested).
    for col in cols:
        if col.info.name in formats:
            col.info.format = formats[col.info.name]
    # A-reference leg 4: render each column with its (now effective) format.
    per_col = [list(col.info.iter_str_vals()) for col in cols]
    # I leg 5: arrange column-major lists into row-major, stripping (the writer
    # emits `el.strip()` into each <td>).
    nrows = len(per_col[0]) if per_col else 0
    out = []
    for r in range(nrows):
        for c in range(len(cols)):
            out.append(per_col[c][r].strip())
    return out


def oracle_cells(table, formats):
    """Cell strings the patched HTML writer emits, in document (row-major) order."""
    with io.StringIO() as sp:
        table.write(sp, format="html", formats=formats)
        html = sp.getvalue()
    # The body cells are the <td> entries (header uses <th>), in row-major order.
    return [m.group(1).strip() for m in _TD.finditer(html)]


def gen_case(rng):
    ncols = rng.randint(1, 4)
    names = rng.sample(NAME_POOL, ncols)
    nrows = rng.randint(1, 4)
    data, formats = [], {}
    for name in names:
        if rng.random() < 0.5:
            col = [rng.randint(-9999, 9999) for _ in range(nrows)]
        else:
            col = [rng.uniform(-1e12, 1e12) * (10 ** rng.randint(-20, 5))
                   for _ in range(nrows)]
        data.append(col)
        # Randomly request a format for this column (by name).
        if rng.random() < 0.6:
            formats[name] = rng.choice(FORMAT_CHOICES)
    table = Table(data, names=names)
    return table, formats


def main():
    rng = random.Random(SEED)
    checked = 0
    for i in range(N):
        table, formats = gen_case(rng)
        try:
            want = oracle_cells(table, formats)
        except Exception as e:  # an unsupported format string for a dtype, etc.
            continue            # skip cases the writer itself rejects
        # shadow uses a fresh copy so info.format mutation doesn't leak across.
        got = shadow_cells(table.copy(), dict(formats))
        if got != want:
            print(f"DISAGREEMENT at case {i}: names={list(table.colnames)} "
                  f"formats={formats}\n  oracle={want}\n  shadow={got}")
            print("G-CONF FAIL")
            sys.exit(1)
        checked += 1
    print(f"G-CONF OK: {checked} cases agree (of {N} generated), seed={SEED}")
    sys.exit(0)


if __name__ == "__main__":
    main()
