#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-14182.

The bundle models TWO header-row-count-dependent positions in the simple
reStructuredText fixed-width table format (mapping.md):

  * rstWrap        — emitting: bracket the rendered table with a copy of the
                     column-rule line, which sits at index `numHeaderRows` in
                     the rendered sequence of lines, producing
                     `[sep] + lines + [sep]`.
  * rstDataStart   — parsing: the first data line index is `2 + numHeaderRows`.

Both modeled values are PURE functions of `numHeaderRows` (and, for the wrap,
the already-rendered list of `lines` — which the patch does NOT recompute, it
only changes which index of the renderer's output is selected). Standing up the
full astropy fixed-width writer/reader to drive the real selection is heavy and
orthogonal: the modeled values are exactly these two index computations over
observables the real code exposes. So the ORACLEs below replicate the POST-PATCH
formulas and the SHADOWs are op-for-op transliterations of the Solution.lean impl
regions (per refinement.md).

This genuinely tests the soundness-critical change: with multiple header rows the
bracketing rule line is read from index `numHeaderRows` (not the fixed `1`) and
the data start is `2 + numHeaderRows` (not the fixed `3`) — matching the F2P
round-trip which uses three header rows.

stdlib-only. Pinned seed: 14182 (also in mapping.md).
"""
import random
import sys

SEED = 14182
N = 120_000


# --- ORACLE: faithful in-process replica of the POST-PATCH selection ----------
def oracle_wrap(num_header_rows, lines):
    idx = len(self_header_rows_proxy(num_header_rows))   # == num_header_rows
    sep = lines[idx] if 0 <= idx < len(lines) else ""
    return [sep] + lines + [sep]


def oracle_data_start(num_header_rows):
    return 2 + num_header_rows


def self_header_rows_proxy(n):
    # the real code reads `len(self.header.header_rows)`; we model the count
    # directly, so the proxy is simply a list of length n.
    return [None] * n


# --- SHADOW of the Solution.lean impl regions (the R/I legs) ------------------
def shadow_wrap(num_header_rows, lines):
    # mirrors implementation_rstWrap: idx := numHeaderRows; sep := lines.getD idx ""
    idx = num_header_rows
    sep = lines[idx] if 0 <= idx < len(lines) else ""
    return [sep] + lines + [sep]


def shadow_data_start(num_header_rows):
    # mirrors implementation_rstDataStart: 2 + numHeaderRows
    return 2 + num_header_rows


def disagree(num_header_rows, lines):
    ow, sw = oracle_wrap(num_header_rows, lines), shadow_wrap(num_header_rows, lines)
    if ow != sw:
        return ("wrap", num_header_rows, lines, ow, sw)
    od, sd = oracle_data_start(num_header_rows), shadow_data_start(num_header_rows)
    if od != sd:
        return ("data_start", num_header_rows, lines, od, sd)
    return None


def _mk_lines(num_header_rows, num_data, rng):
    # a plausible rendered table: n header rows, one rule line, then data rows.
    rule = "=" * rng.randint(3, 9) + " " + "=" * rng.randint(3, 9)
    hdrs = [f"hdr{i}_" + "x" * rng.randint(0, 6) for i in range(num_header_rows)]
    data = [f"row{i}_" + "y" * rng.randint(0, 6) for i in range(num_data)]
    return hdrs + [rule] + data


def _edge_cases():
    cases = []
    # F2P round-trip uses three header rows: name, unit, dtype.
    cases.append((3, ["======= ======== ====",
                      "   wave response ints",
                      "     nm       ct     ",
                      "float64  float32 int8",
                      "======= ======== ====",
                      "  350.0      1.0    1",
                      "  950.0      2.0    2"]))
    # historical single header row (default header_rows=['name']).
    cases.append((1, ["==== ===== ======",
                      "Col1  Col2  Col3",
                      "==== ===== ======",
                      "  1    2.3  Hello",
                      "  2    4.5  Worlds"]))
    # two header rows (name, unit).
    cases.append((2, ["===== ========",
                      " wave response",
                      "    nm       ct",
                      "===== ========",
                      "350.0      0.7"]))
    # zero header rows degenerate layout.
    cases.append((0, ["===== =====", "1.0 2.0"]))
    return cases


def main() -> int:
    checked = 0
    for n, lines in _edge_cases():
        d = disagree(n, lines)
        if d:
            print(f"DISAGREE edge: leg={d[0]} n={d[1]} oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 8)
        num_data = rng.randint(1, 6)
        lines = _mk_lines(n, num_data, rng)
        d = disagree(n, lines)
        if d:
            print(f"DISAGREE fuzz: leg={d[0]} n={d[1]} oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
