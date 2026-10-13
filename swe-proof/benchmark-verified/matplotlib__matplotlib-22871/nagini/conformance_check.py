#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-22871
(nagini).

SHADOW: the impl region of model.py `determine_level`, copied verbatim below
with the contract calls stripped. `TickLevel` copies over as a plain class
(contract lines removed). The two @Pure helpers `col_varies` / `col_has_one`
copy over as plain functions: their bodies are existential formulas whose
guards (`0 <= i < j < len(col)`, `0 <= i < len(col)`) bound the quantified
variables to a finite range, so the executable form enumerates exactly that
guarded range. No @ContractOnly callees exist in this model.

ORACLE: the REAL patched repo method the model models per mapping.md --
`matplotlib.dates.ConciseDateFormatter.format_ticks` (the labelling-level
scan inside it computes the modeled pair). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. The modeled pair (level, show_offset) is observed through
the method's real outputs by constructing the formatter with sentinel format
strings:

  * per-level tick formats "F<k>" / zero-formats "Z<k>" -- every returned
    tick label then spells the chosen labelling level k;
  * per-level offset formats "OFF<k>" -- the offset string is "OFF<k>" when
    the offset is shown at level k, and "" when it is suppressed.

(The sentinel strings contain no strftime directives and no '.', so they pass
through the method's label post-processing unchanged.)

Type bridge (mapping.md section 2): the repo builds an N x 6 integer table,
one row per tick, from the tick instants' calendar breakdown; the model
carries the SAME table as six parallel List[int] columns (c0..c5 = year,
month, day, hour, minute, second) with tickdate[k, level] <-> c{level}[k].
This script realises the bridge by generating tick instants as real
datetimes, converting them to matplotlib date numbers (the method's real
input), and deriving the shadow's six columns from the very same calendar
breakdown the method computes internally (num2date + timetuple, the unchanged
prologue upstream of the modeled scan). The model's show_offset in {0,1}
maps to the repo boolean (1 <-> shown); the formatter is built with its
default offset-visibility flag, matching the shadow's fixed default of 1.

Input domain: Requires demands six equal-length columns with N >= 1; the
bridged domain is the image of real tick instants, so the fuzzer draws
calendar components in their natural ranges (years incl. year 1, months
1..12 biased to include/exclude 1, days 1..28, h/m/s full range, occasional
sub-second parts) and biases columns toward constant/varying to exercise
every branch of the scan.

>= 1e5 Requires-satisfying inputs: boundary tick tables + 100000 fuzz draws.
Pinned fuzz seed: 22871.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + matplotlib (the repo under test) + numpy (its
dependency) only.
"""
import datetime
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.dates import (AutoDateLocator, ConciseDateFormatter,
                              date2num, num2date)

SEED = 22871
N_FUZZ = 100_000


# --- pure region of model.py, contracts stripped -------------------------------
# The existential bodies are enumerated over their guard-bounded finite ranges.

def col_varies(col):
    """True iff the column is not constant across the ticks, i.e. two ticks
    disagree on this calendar component."""
    return any(0 <= i and i < j and j < len(col) and col[i] != col[j]
               for i in range(len(col)) for j in range(len(col)))


def col_has_one(col):
    """True iff the value 1 occurs somewhere in the column."""
    return any(0 <= i and i < len(col) and col[i] == 1
               for i in range(len(col)))


class TickLevel:
    """The two observed outputs of the labelling-level computation: the chosen
    labelling level and a 0/1 flag for whether the summary offset is shown."""

    def __init__(self, level, show_offset):
        self.level = level          # type: int
        self.show_offset = show_offset  # type: int


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def determine_level(c0, c1, c2, c3, c4, c5):
    # Default: the offset is shown. The descending scan over the six levels is
    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
    if col_varies(c5):
        return TickLevel(5, 1)
    if col_varies(c4):
        return TickLevel(4, 1)
    if col_varies(c3):
        return TickLevel(3, 1)
    if col_varies(c2):
        return TickLevel(2, 1)
    if col_varies(c1):
        if col_has_one(c1):
            return TickLevel(1, 0)
        return TickLevel(1, 1)
    if col_varies(c0):
        if col_has_one(c0):
            return TickLevel(0, 0)
        return TickLevel(0, 1)
    # No column varies: every tick is identical down to the second. The scan
    # reaches the coarsest level with all entries equal and resets to the finest
    # level; the offset keeps its default (shown).
    return TickLevel(5, 1)


# --- oracle plumbing ------------------------------------------------------------

FMTS = ["F0", "F1", "F2", "F3", "F4", "F5"]
ZEROFMTS = ["Z0", "Z1", "Z2", "Z3", "Z4", "Z5"]
OFFSETFMTS = ["OFF0", "OFF1", "OFF2", "OFF3", "OFF4", "OFF5"]


def oracle(values):
    """Feed matplotlib date numbers to the REAL patched format_ticks and read
    the modeled (level, show_offset) pair back out of its sentinel-formatted
    outputs. Returns (level, show_offset) or raises on an unreadable output."""
    fmt = ConciseDateFormatter(AutoDateLocator(), formats=FMTS,
                               zero_formats=ZEROFMTS,
                               offset_formats=OFFSETFMTS)
    labels = fmt.format_ticks(values)   # REAL patched method
    off = fmt.get_offset()
    levels = set()
    for lab in labels:
        if len(lab) != 2 or lab[0] not in "FZ" or not lab[1].isdigit():
            raise AssertionError("unreadable tick label %r" % (lab,))
        levels.add(int(lab[1]))
    if len(levels) != 1:
        raise AssertionError("inconsistent per-label levels %r" % (labels,))
    level = levels.pop()
    if off == "":
        return level, 0
    if off != OFFSETFMTS[level]:
        raise AssertionError("offset %r inconsistent with level %d"
                             % (off, level))
    return level, 1


def columns_of(values):
    """The six parallel integer columns for the given date numbers, derived by
    the same (unchanged, upstream) calendar breakdown the real method uses:
    per tick, the first six timetuple fields of the instant."""
    rows = [num2date(v).timetuple()[:6] for v in values]
    return [[row[j] for row in rows] for j in range(6)]


def check(values, tag):
    """Run oracle + shadow on one list of date numbers; return an error string
    on disagreement, else None."""
    obs_level, obs_show = oracle(values)
    cols = columns_of(values)
    res = determine_level(cols[0], cols[1], cols[2], cols[3], cols[4], cols[5])
    if (res.level, res.show_offset) != (obs_level, obs_show):
        return ("DISAGREEMENT [%s]\n  values=%r\n  columns=%r\n"
                "  shadow=(level=%d, show_offset=%d)\n"
                "  real=(level=%d, show_offset=%d)"
                % (tag, list(values), cols, res.level, res.show_offset,
                   obs_level, obs_show))
    return None


# --- input generation -----------------------------------------------------------

def dt_nums(dts):
    """Real datetimes -> the matplotlib date numbers the method consumes."""
    return [date2num(d) for d in dts]


BOUNDARY = [
    # single tick: everything constant -> finest level, offset shown
    ("single", [datetime.datetime(1997, 6, 14, 3, 30, 15)]),
    # all ticks identical down to the second
    ("identical", [datetime.datetime(2021, 2, 3, 4, 5, 6)] * 3),
    # months vary, month 1 present
    ("months-with-1", [datetime.datetime(1997, m, 1) for m in (1, 2, 3)]),
    # months vary, month 1 absent
    ("months-no-1", [datetime.datetime(1997, m, 1) for m in (2, 4, 7, 10)]),
    # years vary, no year 1
    ("years-no-1", [datetime.datetime(y, 6, 1) for y in (1997, 2002, 2007)]),
    # years vary, year 1 present (degenerate but valid calendar input)
    ("years-with-1", [datetime.datetime(1, 6, 1), datetime.datetime(5, 6, 1)]),
    # days vary (fine level), day 1 present
    ("days", [datetime.datetime(1997, 6, d) for d in (1, 14, 28)]),
    # hours vary
    ("hours", [datetime.datetime(1997, 6, 1, h) for h in (0, 5, 23)]),
    # minutes vary
    ("minutes", [datetime.datetime(1997, 6, 1, 3, m) for m in (0, 1, 59)]),
    # seconds vary
    ("seconds", [datetime.datetime(1997, 6, 1, 3, 30, s) for s in (10, 20)]),
    # seconds vary with sub-second parts present
    ("subsecond", [datetime.datetime(1997, 6, 1, 3, 30, s, 250000)
                   for s in (10, 20)]),
    # month and day both vary, month 1 absent
    ("month-day", [datetime.datetime(1997, 2, 19), datetime.datetime(1997, 4, 1),
                   datetime.datetime(1997, 7, 30)]),
]


def rand_component(rng, j):
    # j: 0=year 1=month 2=day 3=hour 4=minute 5=second
    if j == 0:
        return rng.choice([1, 1, 1996, 1997, 1998, 2021, 2022, 2100])
    if j == 1:
        return rng.choice([1, 1, 2, 3, 5, 8, 11, 12])
    if j == 2:
        return rng.randint(1, 28)
    if j == 3:
        return rng.randint(0, 23)
    if j == 4:
        return rng.randint(0, 59)
    return rng.randint(0, 59)


def rand_values(rng):
    """One fuzzed tick list: N in 1..6 valid instants whose per-component
    columns are biased toward constant (to exercise the descending scan) and
    toward containing/excluding the value 1."""
    n = rng.randint(1, 6)
    base = [rand_component(rng, j) for j in range(6)]
    # components coarser than this stay constant across the ticks (with some
    # noise), so every labelling level gets exercised
    vary_from = rng.randint(0, 6)   # 6 -> everything constant
    dts = []
    for _ in range(n):
        comps = []
        for j in range(6):
            if j < vary_from or rng.random() < 0.35:
                comps.append(base[j])
            else:
                comps.append(rand_component(rng, j))
        micro = rng.choice([0, 0, 0, 500000])
        dts.append(datetime.datetime(comps[0], comps[1], comps[2],
                                     comps[3], comps[4], comps[5], micro))
    return dt_nums(dts)


def main():
    checked = 0

    for tag, dts in BOUNDARY:
        err = check(dt_nums(dts), tag)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for k in range(N_FUZZ):
        err = check(rand_values(rng), "fuzz-%d" % k)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched format_ticks scan on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(BOUNDARY), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
