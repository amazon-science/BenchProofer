#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-14182 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's two impl regions,
              transliterated to Python over the *real* repo types
              (`list[str]`, `int`), via the mapping.md bijection
              (`List (List Char)` ↔ `list[str]`, `len(...)` ↔ `Nat`,
              `lines[k]!` ↔ `lines[k]`):
                surroundWithRuler : [lines[hrc]] + lines + [lines[hrc]]
                dataStartOffset   : 2 + hrc
              where hrc = len(header_rows). There are no A-tagged callees.
  * ORACLE  — patch.diff's behaviour: the REAL patched `astropy.io.ascii.RST`
              at base_commit WITH the gold patch applied (the harness applies
              patch.diff before this runs):
                framing  — the full output of a real
                           `QTable.write(format="ascii.rst", header_rows=...)`;
                read     — the `self.data.start_line` the patched `RST.read`
                           assigns, introspected from a real reader, plus a
                           full round-trip value/units check.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied by
the harness before this runs), stdlib + astropy only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import io
import random
import sys

SEED = 14182
N_FUZZ = 100_000

import numpy as np

import astropy.units as u
from astropy.io import ascii
from astropy.table import QTable

# Valid column-info attributes usable as header rows. "name" must be present
# (the RST reader does header_rows.index("name")); the rest are optional and
# always have a string rendering for the columns we build.
_HEADER_ATTRS = ["name", "unit", "dtype", "format", "description"]


# --- the R/I shadow: Solution.lean's two impl regions, transliterated --------

def shadow_surround(lines, hrc):
    """surroundWithRuler: [lines[hrc]] + lines + [lines[hrc]] (R/I ops)."""
    ruler = lines[hrc]
    return [ruler] + lines + [ruler]


def shadow_data_start(hrc):
    """dataStartOffset: 2 + hrc (the I op 2 + headerRowCount)."""
    return 2 + hrc


# --- the oracle: the REAL patched RST writer/reader --------------------------

def _make_table(rng, ncols, nrows):
    """A small QTable with units, formats and descriptions so that every
    header attribute renders to a non-empty value."""
    tbl = QTable()
    units = [u.nm, u.count, u.s, u.m]
    names = ["wave", "response", "time", "dist"]
    for c in range(ncols):
        data = np.array(
            [round(rng.uniform(1.0, 999.0), 1) for _ in range(nrows)],
            dtype=np.float64,
        )
        col = names[c]
        tbl[col] = data * units[c % len(units)]
        tbl[col].info.format = ".1f"
        tbl[col].info.description = "d%d" % c
    return tbl


def oracle_write_lines(tbl, header_rows):
    """Full output of the real patched RST writer (the framed rendering)."""
    out = io.StringIO()
    tbl.write(out, format="ascii.rst", header_rows=header_rows)
    return out.getvalue().splitlines()


def oracle_read_start_line(lines, header_rows):
    """The data.start_line the patched RST.read assigns, introspected from a
    real reader, plus the parsed table (for a round-trip value check)."""
    reader = ascii.get_reader(Reader=ascii.RST, header_rows=header_rows)
    parsed = reader.read(lines)
    return reader.data.start_line, parsed


def header_rows_choices(rng):
    """Prefixes of _HEADER_ATTRS (always starting with 'name'), giving header
    counts 1..len(_HEADER_ATTRS)."""
    k = rng.randint(1, len(_HEADER_ATTRS))
    return _HEADER_ATTRS[:k]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Deterministic boundary cases first (plan §4.1 step 4): every header-row
    # count 1..5, smallest and a few larger table shapes.
    boundary = []
    for k in range(1, len(_HEADER_ATTRS) + 1):
        boundary.append((_HEADER_ATTRS[:k], 1, 1))
        boundary.append((_HEADER_ATTRS[:k], 3, 2))
    # the exact F2P shape (3 header rows, 3 cols, 2 rows)
    boundary.append((["name", "unit", "dtype"], 3, 2))

    def run_case(header_rows, ncols, nrows):
        nonlocal count
        hrc = len(header_rows)
        tbl = _make_table(rng, ncols, nrows)

        # --- framing site (surroundWithRuler) ---------------------------
        oracle_full = oracle_write_lines(tbl, header_rows)
        # RST.write only prepends/appends one line each; the inner rendering
        # super().write produced is the middle. Reconstruct the framing from
        # that inner rendering via the shadow and compare to the real output.
        inner = oracle_full[1:-1]
        count += 1
        if hrc >= len(inner):
            # require headerRowCount < lines.length — must hold for real input
            disagreements.append(
                ("frame-precond", header_rows, oracle_full,
                 "hrc=%d >= len(inner)=%d" % (hrc, len(inner))))
            return
        shadow_full = shadow_surround(inner, hrc)
        if shadow_full != oracle_full:
            disagreements.append(
                ("frame", header_rows, shadow_full, oracle_full))

        # --- read site (dataStartOffset) --------------------------------
        count += 1
        real_start, parsed = oracle_read_start_line(oracle_full, header_rows)
        if shadow_data_start(hrc) != real_start:
            disagreements.append(
                ("data-start", header_rows, shadow_data_start(hrc), real_start))
        # round-trip sanity: parsed values match the original (real
        # correctness — the patched read must parse from the right line).
        count += 1
        try:
            ok = (list(parsed.colnames) == list(tbl.colnames) and
                  all(np.allclose(np.asarray(parsed[c]), np.asarray(tbl[c]))
                      for c in tbl.colnames))
        except Exception as e:  # pragma: no cover - defensive
            ok = False
            real_start = "round-trip error: %r" % (e,)
        if not ok:
            disagreements.append(
                ("round-trip", header_rows,
                 [list(tbl.colnames)], [list(parsed.colnames)]))

    for header_rows, ncols, nrows in boundary:
        run_case(header_rows, ncols, nrows)
        if len(disagreements) >= 5:
            break

    # --- randomized fuzz --------------------------------------------------
    if len(disagreements) < 5:
        for _ in range(N_FUZZ):
            header_rows = header_rows_choices(rng)
            ncols = rng.randint(1, 4)
            nrows = rng.randint(1, 6)
            run_case(header_rows, ncols, nrows)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d comparisons:"
              % (len(disagreements), count))
        for tag, hr, sh, orc in disagreements:
            print("  [%s] header_rows=%r shadow=%r oracle=%r" % (tag, hr, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of surroundWithRuler + dataStartOffset agrees "
          "with patch.diff behaviour on %d comparisons (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
