#!/usr/bin/env python3
r"""G-CONF differential conformance check for matplotlib__matplotlib-22871 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the OBSERVABLE the F2P test
checks — the offset string `ConciseDateFormatter.get_offset()` returns after
`format_ticks` runs.

  * ORACLE  — `patch.diff`'s behaviour: a real `ConciseDateFormatter` (built on a
              real `AutoDateLocator`) whose patched `format_ticks(values)` runs,
              then `get_offset()`. The single changed operation is the offset
              -display decision; everything else in `format_ticks` (and all of
              `num2date`/`timetuple`/`np.unique`/`strftime`) is the unchanged
              upstream/downstream, executed by the real patched repo.

  * SHADOW  — `Solution.lean`'s modeled operation (`offsetSelection` + the pure
              `offsetDecision` scan) transliterated to Python over the real repo
              types, via the mapping.md §2 bijection:
                  initShow (Bool)          <->  formatter.show_offset (bool)
                  stats : List (Nat×List Int)  <->  [(level, column)] for
                       level in 5,4,3,2,1,0, column = tickdate[:, level] as ints
                  offsetDecision           <->  scan_decide below
              The integer columns are derived from the SAME real
              `num2date(value).timetuple()[:6]` the patched code uses (the
              unchanged upstream, I-reference — run via the real repo, not
              re-modeled). The shadow's (level, show_offset) is then rendered to
              the offset string through the SAME unchanged downstream the patched
              `format_ticks` uses: `tickdatetime[-1].strftime(offset_formats[level])`
              when shown, else "" (refinement.md §A4). There are NO A-tagged ops
              (no consumed axioms, no deep-model references), so the shadow is
              pure R/I (conf_skip=false).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

stdlib + numpy + matplotlib (Agg, no display). Fuzz seed pinned (mapping.md §4).
"""
import random
import sys
from datetime import datetime, timedelta

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates

SEED = 22871
N_FUZZ = 100_000


# --- SHADOW: the R/I transliteration of offsetDecision / offsetSelection -----

def _col_varies(col):
    # colVaries col = col.any (· != col.headD 0): more than one distinct value.
    if not col:
        return False
    first = col[0]
    return any(v != first for v in col)


def _col_has_one(col):
    # colHasOne col = col.contains 1: the integer one occurs in the column.
    return 1 in col


def _suppress_offset(level, col):
    # suppressOffset level col = decide (level < 2) && colHasOne col.
    return (level < 2) and _col_has_one(col)


def offset_decision(init_show, stats):
    """offsetDecision initShow stats — the front-recursive scan, transliterated.
    `stats` is the list of (level, column) pairs in scan order (finest first)."""
    for (lvl, col) in stats:                     # cons :: peels the leading pair
        if _col_varies(col):
            return (lvl, (False if _suppress_offset(lvl, col) else init_show))
        # else: recurse on the tail
    return (5, init_show)                        # [] => (5, initShow)


def shadow_offset_string(formatter, values):
    """The do-block's decision, rendered to the offset string via the SAME
    unchanged downstream the patched format_ticks uses."""
    tickdatetime = [mdates.num2date(v, tz=formatter._tz) for v in values]
    tickdate = np.array([tdt.timetuple()[:6] for tdt in tickdatetime])
    # stats: (level, integer column across the ticks), scan order finest->coarsest
    stats = [(level, [int(x) for x in tickdate[:, level]])
             for level in (5, 4, 3, 2, 1, 0)]
    level, show = offset_decision(bool(formatter.show_offset), stats)
    if show:
        s = tickdatetime[-1].strftime(formatter.offset_formats[level])
        if formatter._usetex:
            s = mdates._wrap_in_tex(s)
        return s
    return ""


# --- ORACLE: the real patched ConciseDateFormatter ---------------------------

def _make_formatter():
    loc = mdates.AutoDateLocator()
    return mdates.ConciseDateFormatter(loc)


def oracle_offset_string(formatter, values):
    """patch.diff's behaviour: run the patched format_ticks, read get_offset()."""
    formatter.format_ticks(values)
    return formatter.get_offset()


# --- fuzz: tick datetime sets spanning sub-second to multi-year --------------

def _fuzz_dts(rng):
    n = rng.randint(2, 8)
    year = rng.randint(1990, 2025)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    start = datetime(year, month, day,
                     rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))
    span_days = rng.choice([1e-4, 1e-3, 1e-2, 0.05, 0.25, 1, 3, 7, 20,
                            45, 90, 180, 300, 400, 800, 2000, 4000])
    return [start + timedelta(days=span_days * i / (n - 1)) for i in range(n)]


def fuzz_inputs(n, rng):
    base = datetime(1997, 1, 1)
    # F2P spans (test_offset_changes): the three asserted offsets.
    yield [base + timedelta(weeks=3 * i / 7) for i in range(8)]                  # '1997-Jan'
    yield [base + timedelta(weeks=7) + timedelta(weeks=23 * i / 7)
           for i in range(8)]                                                    # '1997'
    yield [base + timedelta(weeks=520 * i / 7) for i in range(8)]                # ''
    # issue example: ~200 days starting mid-Feb, no January in range
    issue0 = datetime(2021, 2, 14)
    yield [issue0 + timedelta(days=199 * i / 7) for i in range(8)]
    # boundary spans
    yield [base, base]                                                           # single distinct instant
    yield [datetime(2000, 1, 1), datetime(2000, 1, 1, 12)]                       # within one day, Jan-1
    yield [datetime(2000, 6, 5), datetime(2000, 6, 5, 0, 0, 1)]                  # seconds vary
    yield [datetime(2010, 3, 1) + timedelta(days=d) for d in range(0, 60, 7)]    # ~2 months, includes day 1
    for _ in range(n):
        yield _fuzz_dts(rng)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for dts in fuzz_inputs(N_FUZZ, rng):
        values = mdates.date2num(dts)
        formatter = _make_formatter()
        try:
            oracle = oracle_offset_string(formatter, values)
        except Exception:
            continue
        shadow = shadow_offset_string(formatter, values)
        count += 1
        if shadow != oracle:
            disagreements.append(([d.isoformat() for d in dts], shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for dts, sh, orc in disagreements:
            print("  dts=%r shadow=%r oracle=%r" % (dts[:4], sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of offsetSelection agrees with patch.diff "
          "behaviour (real ConciseDateFormatter.get_offset) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
