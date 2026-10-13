#!/usr/bin/env python3
r"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-20826.

Modeled step: the tick-keyword re-initialisation performed by `Axis.clear`
(lib/matplotlib/axis.py). Post-patch, `clear` updates ONLY the `'gridOn'` entry
of each of the two tick-keyword dicts (`_major_tick_kw`, `_minor_tick_kw`),
computing it from `rcParams['axes.grid']` and `rcParams['axes.grid.which']`, and
leaves every other entry intact.

ORACLE = the REAL patched callee: a live matplotlib `Axis`, into whose tick-kw
dicts we inject a fuzzed set of pre-existing entries, on which we then invoke the
real `Axis.clear()` under fuzzed rcParams, reading the dicts back out.

SHADOW = `implementation_clear` transliterated (R/I legs):
    major' = dict(major); major'['gridOn'] = grid and which in ('both','major')
    minor' = dict(minor); minor'['gridOn'] = grid and which in ('both','minor')
i.e. `Function.update` at key 'gridOn', every other entry carried through.

The shadow must reproduce the real dicts exactly (keys + values) for BOTH tables
on every input. Deterministic built-in fuzzer; pinned seed 2082620210811 (also
in mapping.md). matplotlib + stdlib only.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt

SEED = 2082620210811
N = 100_000

# `axes.grid.which` is a validated rcParam: only these three values are
# accepted by matplotlib (setting anything else raises), so these are exactly
# the realizable inputs for the modeled step.
WHICH = ["major", "minor", "both"]
# Candidate pre-existing entries: the boolean per-side visibility flags the bug
# drops, plus a non-boolean key to confirm preservation is value-agnostic.
BOOL_KEYS = ["tick1On", "tick2On", "label1On", "label2On", "gridOn"]
NONBOOL_ENTRIES = [("size", 4.0), ("color", "k"), ("labelrotation", 0.0)]


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def shadow_clear(major, minor, grid, which):
    """R/I transliteration of implementation_clear (Function.update at gridOn)."""
    maj = dict(major)
    mino = dict(minor)
    maj["gridOn"] = bool(grid) and which in ("both", "major")
    mino["gridOn"] = bool(grid) and which in ("both", "minor")
    return maj, mino


def oracle_clear(axis, major, minor, grid, which):
    """Run the REAL patched Axis.clear on a live axis with injected kw dicts.
    The axis is reused across iterations (creating a figure per call is far too
    heavy); each call fully overwrites both kw dicts before invoking clear()."""
    axis._major_tick_kw.clear()
    axis._major_tick_kw.update(major)
    axis._minor_tick_kw.clear()
    axis._minor_tick_kw.update(minor)
    with mpl.rc_context({"axes.grid": bool(grid),
                         "axes.grid.which": which}):
        axis.clear()
    return dict(axis._major_tick_kw), dict(axis._minor_tick_kw)


def _rand_entries(rnd):
    major, minor = {}, {}
    # random subset of boolean visibility flags, random truth values
    for k in BOOL_KEYS:
        if next(rnd) % 2:
            major[k] = bool(next(rnd) % 2)
        if next(rnd) % 2:
            minor[k] = bool(next(rnd) % 2)
    # occasionally a non-boolean entry (preservation must be value-agnostic)
    if next(rnd) % 3 == 0:
        key, val = NONBOOL_ENTRIES[next(rnd) % len(NONBOOL_ENTRIES)]
        major[key] = val
    if next(rnd) % 3 == 0:
        key, val = NONBOOL_ENTRIES[next(rnd) % len(NONBOOL_ENTRIES)]
        minor[key] = val
    return major, minor


def disagree(axis, major, minor, grid, which):
    o_maj, o_min = oracle_clear(axis, major, minor, grid, which)
    s_maj, s_min = shadow_clear(major, minor, grid, which)
    if o_maj != s_maj or o_min != s_min:
        return (major, minor, grid, which, (o_maj, o_min), (s_maj, s_min))
    return None


def _edges():
    return [
        ({}, {}, True, "both"),
        ({}, {}, False, "both"),
        ({"tick2On": False, "label1On": False}, {"tick2On": False}, True, "major"),
        ({"tick2On": False, "label1On": False}, {"tick2On": False}, False, "minor"),
        # the F2P scenario: shared-axis visibility flags must survive clear()
        ({"tick1On": True, "tick2On": False, "label1On": True, "label2On": False},
         {"tick1On": True, "tick2On": False, "label1On": False, "label2On": False},
         False, "major"),
        ({"gridOn": True, "size": 7.0}, {"gridOn": False, "color": "r"}, True, "minor"),
    ]


def main() -> int:
    checked = 0
    fig, ax = plt.subplots()
    axis = ax.xaxis
    try:
        for major, minor, grid, which in _edges():
            d = disagree(axis, major, minor, grid, which)
            if d:
                print(f"DISAGREE edge {d}")
                print("status=fail")
                return 1
            checked += 1

        rnd = _lcg(SEED)
        for _ in range(N):
            major, minor = _rand_entries(rnd)
            grid = bool(next(rnd) % 2)
            which = WHICH[next(rnd) % len(WHICH)]
            d = disagree(axis, major, minor, grid, which)
            if d:
                print(f"DISAGREE fuzz {d}")
                print("status=fail")
                return 1
            checked += 1
    finally:
        plt.close(fig)

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
