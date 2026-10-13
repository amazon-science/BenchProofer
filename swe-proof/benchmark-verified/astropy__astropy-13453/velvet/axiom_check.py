#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13453.

Executes the REAL repo callee that the gold patch newly invokes —
`astropy.io.ascii.core.BaseData._set_col_formats` — over real astropy table
columns and asserts that its observable effect (each column's `info.format`
after the call) matches the deep model `effFormats`/`effFmt`/`lookupFormat`
encoded in Solution.lean's pure region.

The single kind-A check (there are no consumed axioms in this bundle):

  (A-reference) the deep model `eff_formats` (Solution.lean pure region) == the
      real `_set_col_formats`. The changed behaviour — selecting each column's
      effective display format from the supplied per-column `formats` — is
      modeled DEEPLY, not behind a consumed axiom; G-AX validates that deep model
      against the real callee:
        if col.info.name in formats:  -> col.info.format = formats[name]   (override)
        else:                         -> col.info.format unchanged          (keep)

Imports only `astropy` (the same package the gold patch calls). The callee
`_set_col_formats` is UNCHANGED by the patch — the bug was that the HTML writer
never *called* it (mapping.md §3.1). Exit 0 iff every observation holds.
"""
import random
import sys

from astropy.io.ascii import core
from astropy.table import Column, Table


# --- Solution.lean deep-model reference (kept in lock-step with the .lean) ---

def lookup_format(formats, name):
    """lookupFormat: supplied format for `name`, else None."""
    return formats.get(name, None)


def eff_fmt(formats, name, current):
    """effFmt: supplied-format-wins, else keep the column's current format."""
    f = lookup_format(formats, name)
    return f if f is not None else current


def eff_formats(formats, cols):
    """effFormats: element-wise override over (name, current_format) columns."""
    return [eff_fmt(formats, name, current) for (name, current) in cols]


# --- the check ---------------------------------------------------------------

def run_real_set_col_formats(col_specs, formats):
    """Build real astropy columns with the given (name, current_format) specs,
    attach them + the supplied `formats` to a real BaseData, run the REAL
    `_set_col_formats`, and return the per-column `info.format` after the call."""
    cols = []
    for name, current in col_specs:
        # numeric data so a real format string would format without error
        col = Column([1, 2, 3], name=name)
        col.info.format = current   # None or a format string
        cols.append(col)

    data = core.BaseData()
    data.cols = cols
    data.formats = dict(formats)

    data._set_col_formats()          # the REAL repo callee

    return [col.info.format for col in cols]


def check_selection(col_specs, formats):
    observed = run_real_set_col_formats(col_specs, formats)
    expected = eff_formats(dict(formats), col_specs)
    assert observed == expected, (
        "eff_formats deep model unsound on cols=%r formats=%r: "
        "_set_col_formats gave %r, deep model gives %r"
        % (col_specs, formats, observed, expected))


def main():
    # --- boundary cases -------------------------------------------------------
    boundary = [
        # (col_specs [(name, current_format)], formats {name: fmt})
        ([], {}),
        ([("C1", None)], {}),                                   # no formats supplied
        ([("C1", None)], {"C1": "04d"}),                        # override an unset format
        ([("C1", ".3f")], {"C1": "04d"}),                       # override an existing format
        ([("C1", ".3f")], {"C2": "04d"}),                       # supplied key matches no column
        ([("C1", None), ("C2", None)], {"C1": "04d", "C2": ".2e"}),  # the F2P scenario
        ([("C1", None), ("C2", ".9f")], {"C2": ".2e"}),         # partial: only C2 overridden
        ([("a", None), ("b", None)], {"a": ".2e"}),             # issue reproducer columns
        ([("x", "05d"), ("y", "06d"), ("z", None)],
         {"x": ".1e", "z": "+.4f"}),                            # mixed override/keep
    ]
    for col_specs, formats in boundary:
        check_selection(col_specs, formats)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13453)
    names_pool = ["C1", "C2", "a", "b", "x", "y", "z", "col_0", "col_1", "n"]
    fmt_pool = [None, "04d", ".2e", ".3f", "+.4f", "06d", "e", "g", "05.2f"]
    supplied_fmt_pool = ["04d", ".2e", ".3f", "+.4f", "06d", "e", "g", "05.2f"]
    for _ in range(20000):
        k = rng.randint(0, 6)
        # unique column names (a Table requires unique names; selection is by name)
        chosen = rng.sample(names_pool, min(k, len(names_pool)))
        col_specs = [(nm, rng.choice(fmt_pool)) for nm in chosen]
        # supplied formats: random subset of names (incl. possibly non-existent)
        formats = {}
        for nm in names_pool:
            if rng.random() < 0.4:
                formats[nm] = rng.choice(supplied_fmt_pool)
        check_selection(col_specs, formats)

    print("G-AX OK: eff_formats deep model (== _set_col_formats) sound on %d "
          "boundary + 20000 fuzz column/format configurations" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
