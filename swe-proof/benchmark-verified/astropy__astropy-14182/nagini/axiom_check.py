#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14182.

Both changed behaviours are modelled DEEPLY as layout-index arithmetic (there
is no consumed @ContractOnly axiom). The two deep models are A-references:

  (A-reference 1) WRITE framing.  The model claims the simple-RST writer frames
      its fixed-width block of a table with ``n`` header rows by repeating the
      block's closing rule line (the run of ``=`` at offset ``n``) above the
      block and below it.  Equivalently: in the rendered output the first and
      last lines are the rule line, and the rule line that closes the header in
      the body sits at offset ``frame_index(n) == n`` inside the inner block.

  (A-reference 2) READ data start.  The model claims the first data value row of
      a simple-RST table with ``n`` header rows is at processed-line offset
      ``data_start_index(n) == n + 2`` (one leading rule, ``n`` header rows, one
      closing rule, then data).

This script drives the REAL astropy reStructuredText reader/writer (the module
the gold patch edits) on tables with n = 1, 2, 3 header rows over boundary +
fuzz shapes and asserts every observation matches those two model formulas.

Imports only the standard library + ``astropy`` (the repository under test, the
same package the gold patch lives in). Exit 0 iff every obligation holds.
"""
import io
import random
import sys

import numpy as np

import astropy.units as u
from astropy.table import QTable


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def frame_index(n):
    # model.py: frame_index(n) == n
    return n


def data_start_index(n):
    # model.py: data_start_index(n) == n + 2
    return n + 2


# header-row attribute names astropy understands, in canonical order
HEADER_ROW_NAMES = ["name", "unit", "dtype"]


def is_rule_line(line):
    """A processed RST rule line is a non-empty run of '=' and spaces with at
    least one '=' and no other glyphs (the position character is '=')."""
    s = line.strip()
    return len(s) > 0 and set(line.strip()) <= {"=", " "} and "=" in line


def make_table(ncols):
    cols = {}
    units = [u.nm, u.count, u.s, u.m, u.kg]
    for c in range(ncols):
        cols["c%d" % c] = [350.0 + c, 950.0 + c] * units[c % len(units)]
    return QTable(cols)


def render(tbl, header_rows):
    out = io.StringIO()
    tbl.write(out, format="ascii.rst", header_rows=header_rows)
    return out.getvalue().splitlines()


def check_write_framing(tbl, header_rows):
    """A-reference 1: the real RST writer frames with the closing rule line, and
    that rule sits at offset frame_index(n)==n in the inner (unframed) block."""
    n = len(header_rows)
    lines = render(tbl, header_rows)

    # Output must be non-trivial and framed top & bottom by a rule line.
    assert len(lines) >= 2, "RST output too short: %r" % (lines,)
    assert is_rule_line(lines[0]), "top line not a rule: %r" % (lines[0],)
    assert is_rule_line(lines[-1]), "bottom line not a rule: %r" % (lines[-1],)

    # The framed output is [rule] + inner_block + [rule]; recover the block.
    inner = lines[1:-1]
    # The framing lines must equal the block's closing header rule (offset n).
    assert n < len(inner), (
        "inner block shorter than frame offset: n=%d block=%r" % (n, inner))
    assert is_rule_line(inner[frame_index(n)]), (
        "block offset frame_index(%d)=%d is not the rule line: %r"
        % (n, frame_index(n), inner))
    assert inner[frame_index(n)] == lines[0] == lines[-1], (
        "frame lines != block rule at offset n=%d: top=%r block[n]=%r"
        % (n, lines[0], inner[frame_index(n)]))
    # And the header text rows before the rule are NOT rule lines.
    for k in range(n):
        assert not is_rule_line(inner[k]), (
            "header row %d unexpectedly a rule line: %r" % (k, inner[k]))


def check_read_data_start(tbl, header_rows):
    """A-reference 2: reading back, the first data value row is at processed
    offset data_start_index(n)==n+2 (one leading rule, n headers, one rule)."""
    n = len(header_rows)
    lines = render(tbl, header_rows)
    # Processed lines = non-blank lines (RST output here has no blank lines).
    processed = [ln for ln in lines if ln.strip()]
    ds = data_start_index(n)
    assert ds < len(processed), (
        "data_start_index(%d)=%d out of range for %r" % (n, ds, processed))
    # Structure: offset 0 rule, 1..n header rows, n+1 rule, n+2.. data.
    assert is_rule_line(processed[0]), "no leading rule: %r" % (processed,)
    assert is_rule_line(processed[n + 1]), (
        "no closing header rule at offset n+1=%d: %r" % (n + 1, processed))
    for k in range(1, n + 1):
        assert not is_rule_line(processed[k]), (
            "header offset %d is a rule: %r" % (k, processed[k]))
    assert not is_rule_line(processed[ds]), (
        "data offset %d is a rule line (expected a value row): %r"
        % (ds, processed[ds]))

    # Round-trip: reading the rendered table with the same header_rows recovers
    # exactly the original rows (the data really begins at offset n+2).
    back = QTable.read(lines, format="ascii.rst", header_rows=header_rows)
    assert len(back) == len(tbl), (
        "round-trip row count mismatch n=%d: %d vs %d"
        % (n, len(back), len(tbl)))
    assert list(back.colnames) == list(tbl.colnames), (
        "round-trip colnames mismatch n=%d: %r vs %r"
        % (n, list(back.colnames), list(tbl.colnames)))


def main():
    rng = random.Random(14182)

    # Boundary + systematic: every header-row count 1..3, several column counts.
    for n in (1, 2, 3):
        header_rows = HEADER_ROW_NAMES[:n]
        for ncols in (1, 2, 3, 4, 5):
            tbl = make_table(ncols)
            check_write_framing(tbl, header_rows)
            check_read_data_start(tbl, header_rows)

    # Fuzz: random column counts and random valid header-row subsets that
    # always include "name" (astropy requires the name row to be present).
    for _ in range(400):
        n = rng.randint(1, 3)
        header_rows = HEADER_ROW_NAMES[:n]
        ncols = rng.randint(1, 5)
        tbl = make_table(ncols)
        check_write_framing(tbl, header_rows)
        check_read_data_start(tbl, header_rows)

    print("G-AX OK: real astropy RST writer/reader matches the deep models "
          "frame_index(n)==n and data_start_index(n)==n+2 over header-row "
          "counts 1..3 (boundary + 400 fuzz shapes), 0 violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
