#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14539 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `diffVLAColumn` impl region,
              transliterated to Python over the *real* repo types: classify the
              column by `isVLA(col.format)` (= "'P' in fmt or 'Q' in fmt"), then
              produce the per-row difference verdict either row-wise (VLA) or via
              the generic route (whose ambiguous-verdict failure is pinned to a
              multi-element row). The route sub-observations are the REAL repo
              operations (`np.allclose` per row, `np.where` for the generic
              route) — real code, not a model.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched real
              `astropy.io.fits.TableDataDiff` applied to a one-column table at
              base_commit (the real correctness oracle, G-RESOLVE — the harness
              applies patch.diff before this runs).

Both are classified into the `Except DiffErr (List Bool)` outcome domain: a
`ValueError` escaping ↔ ("error",); a completed comparison ↔ ("ok", frozenset of
the differing row indices). They must agree for every column. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Note (scope): on the gold-patched oracle every column is sent down a route its
element kind supports — variable-length (object-dtype) columns are classified VLA
(P or Q) and compared row-wise; every other column (incl. text columns, which the
row-wise numeric route cannot handle) takes the generic route — so both routes
complete and the ("error",) outcomes are UNREACHABLE through the patched oracle.
The two failure outcomes (the generic route raising on an intrinsically-VLA
multi-element row, and the row-wise numeric route raising on a non-numComparable
text column) are validated separately by G-AX (axiom_check.py facts 2 & 3).
G-CONF here refutes the route-choice + per-row-verdict legs (A3/A4) against the
real patched diff, including text columns that the shadow must route generic.

Runs in-container (the prebuilt SWE-Bench instance image), numpy + the astropy
under test only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

import numpy as np
from astropy.io import fits
from astropy.io.fits.diff import TableDataDiff


SEED = 14539
N_FUZZ = 100_000


# --- isVLA: the Lean deep model, transliterated -------------------------------
def is_vla(fmt):
    return ("P" in fmt) or ("Q" in fmt)


def shadow(fmt_str, arra, arrb, rtol=0.0, atol=0.0):
    """R/I transliteration of diffVLAColumn: route by isVLA, then produce the
    differing-row set (row-wise for a VLA column, else the generic element-wise
    route). The generic route runs only on non-VLA columns, whose element-wise
    comparison always completes (the `error` outcome is reachable only when an
    intrinsically-VLA multi-element column is misrouted, which the patched
    classifier never does — see the scope note in the module docstring)."""
    if is_vla(fmt_str):
        diffs = (
            [idx for idx in range(len(arra))
             if not np.allclose(arra[idx], arrb[idx], rtol=rtol, atol=atol)],
        )
        return ("ok", frozenset(diffs[0]))
    # generic route
    try:
        d = np.where(arra != arrb)
        return ("ok", frozenset(d[0].tolist()))
    except ValueError:
        return ("error",)


def build(fmt, a, b):
    """Construct the two one-column tables ONCE; both shadow and oracle read
    them, so they see identical data and construction cost is paid once."""
    ta = fits.BinTableHDU.from_columns([fits.Column("K", format=fmt, array=a)])
    tb = fits.BinTableHDU.from_columns([fits.Column("K", format=fmt, array=b)])
    return ta, tb


def oracle(ta, tb):
    """patch.diff's behaviour: the gold-patched real TableDataDiff over the
    one-column tables. Returns ('error',) if it raises ValueError, else
    ('ok', frozenset of differing row indices for the column)."""
    try:
        d = TableDataDiff(ta.data, tb.data, numdiffs=10**6)
    except ValueError:
        return ("error",)
    idxs = frozenset(idx for ((_name, idx), _vals) in d.diff_values)
    return ("ok", idxs)


def fuzz_inputs(n, rng):
    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    # the F2P scenarios: QJ(2) identical and differing (test_diff.py c11/cb11)
    yield ("QJ(2)", [[0, 1], [2, 3]], [[0, 1], [2, 3]])
    yield ("QJ(2)", [[0, 1], [2, 3]], [[1, 2], [3, 4]])
    yield ("PI(2)", [[0, 1], [2, 3]], [[0, 1], [2, 3]])      # P still works
    yield ("PI(2)", [[0, 1], [2, 3]], [[1, 2], [3, 4]])
    # the issue repro shape: ragged QD identical -> no difference
    yield ("QD", [[0.0], [0.0, 0.0]], [[0.0], [0.0, 0.0]])
    yield ("PD", [[0.0], [0.0, 0.0]], [[0.0], [0.0, 0.0]])
    # scalar (non-VLA) columns: generic route, must agree
    yield ("J", [0, 1, 2], [0, 9, 2])
    yield ("J", [0, 1, 2], [0, 1, 2])
    yield ("E", [0.0, 1.0], [0.0, 2.0])
    yield ("L", [True, False], [True, False])
    # TEXT (non-VLA, non-numComparable) columns: the row-wise numeric route cannot
    # run on these (np.allclose raises), so they MUST take the generic route. They
    # make "route everything row-wise" wrong; the shadow routes them generic
    # (isVLA=False) and must agree with the patched oracle (np.where completes).
    yield ("10A", ["foo", "bar"], ["foo", "baz"])
    yield ("5A", ["abcd", "ef"], ["abcd", "ef"])
    yield ("A", ["x", "y"], ["z", "y"])
    yield ("20A", ["hello", "world"], ["hello", "WORLD"])
    # non-VLA fixed-MULTIDIM columns: multi-element rows but NOT object dtype, so
    # the generic route COMPLETES (never raises). These distinguish the corrected
    # `isVLA && anyMulti` guard from a naive `anyMulti`-only model and must agree
    # with the patched oracle (both yield the differing-index set, no error).
    yield ("2J", [[0, 1], [2, 3]], [[0, 1], [2, 3]])
    yield ("2J", [[0, 1], [2, 3]], [[1, 2], [3, 4]])
    yield ("3I", [[0, 1, 2], [3, 4, 5]], [[0, 1, 9], [3, 4, 5]])
    yield ("2E", [[0.0, 1.0], [2.0, 3.0]], [[0.0, 9.0], [2.0, 3.0]])
    # VLA float, partial differences
    yield ("QE(2)", [[0.0, 1.0], [2.0, 3.0]], [[0.0, 1.0], [3.0, 4.0]])
    yield ("PJ(2)", [[5, 6], [7, 8]], [[5, 6], [9, 8]])

    # --- randomized fuzz -----------------------------------------------------
    vla_int = ["PI(2)", "PJ(2)", "QI(2)", "QJ(2)"]
    vla_flt = ["PE(2)", "PD(2)", "QE(2)", "QD(2)"]
    scalar = ["J", "I", "K", "E", "D"]
    for _ in range(n):
        roll = rng.random()
        if roll < 0.7:
            # VLA column (P or Q), int or float, varied row lengths
            if rng.random() < 0.5:
                fmt = rng.choice(vla_int)
                lo, hi, flo = 0, 4, False
            else:
                fmt = rng.choice(vla_flt)
                lo, hi, flo = 0, 4, True
            nrows = rng.randint(1, 5)
            rowlens = [rng.choice([1, 1, 2, 2, 3]) for _ in range(nrows)]
            a = [[rng.randint(lo, hi) for _ in range(L)] for L in rowlens]
            if flo:
                a = [[float(v) for v in row] for row in a]
            b = [[(v if rng.random() < 0.6
                   else (rng.randint(lo, hi) if not flo
                         else float(rng.randint(lo, hi)))) for v in row]
                 for row in a]
            yield (fmt, a, b)
        else:
            # scalar column (non-VLA): generic route
            fmt = rng.choice(scalar)
            nrows = rng.randint(1, 6)
            flo = fmt in ("E", "D")
            a = [(rng.randint(0, 5) if not flo else float(rng.randint(0, 5)))
                 for _ in range(nrows)]
            b = [(v if rng.random() < 0.6
                  else (rng.randint(0, 5) if not flo
                        else float(rng.randint(0, 5)))) for v in a]
            yield (fmt, a, b)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for fmt, a, b in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            ta, tb = build(fmt, a, b)
            arra, arrb = ta.data["K"], tb.data["K"]
            fmt_str = str(ta.columns["K"].format)
            sh = shadow(fmt_str, arra, arrb)
            orc = oracle(ta, tb)
        except Exception as e:  # construction error -> skip this input
            disagreements.append((fmt, a, b, "exc:%r" % e, None))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append((fmt, a, b, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fmt, a, b, sh, orc in disagreements:
            print("  fmt=%r a=%r b=%r shadow=%r oracle=%r" % (fmt, a, b, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of diffVLAColumn agrees with patch.diff "
          "(gold-patched TableDataDiff) behaviour on %d columns (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
