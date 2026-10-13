#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-13989.

The bundle models ONE routine: the assembly of the `hist_kwargs` mapping inside
`Axes.hist` (mapping.md), immediately around the gold edit:

    hist_kwargs = dict()
    ...
        hist_kwargs['range'] = bin_range        # set iff single/empty-dataset path
    ...
    density = bool(density) or bool(normed)
    if density and not stacked:
        hist_kwargs['density'] = density        # FIX: set in place (was: rebind dict)

The modeled value is a PURE function of four already-resolved observables the
real function exposes at that point:

    setRange      : bool   -- whether the 'range' entry is added
    binRange      : (lo,hi)-- the bounds tuple stored under 'range'
    densityFlag   : bool   -- the resolved density request
    stacked       : bool   -- whether datasets are being stacked

Standing up numpy / the full Axes.hist machinery is heavy and unnecessary: the
modeled value is exactly this dict assembly. So the ORACLE below is a faithful
in-process replica of the POST-PATCH assembly (item-assignment, range preserved),
and the SHADOW is the op-for-op transliteration of
`implementation_assembleHistKeywordArgs` (Solution.lean impl region), per
refinement.md.

This genuinely tests the soundness-critical clause: setting the 'density' entry
must NOT drop a previously-set 'range' entry (the reported bug). The pre-patch
`hist_kwargs = dict(density=density)` would diverge here.

The mapping is represented as a dict with optional 'range'/'density' keys
(missing key <-> Option.none, per mapping.md).

stdlib-only. Pinned seed: 13989 (also in mapping.md).
"""
import random
import sys

SEED = 13989
N = 120_000


# --- ORACLE: faithful in-process replica of the POST-PATCH assembly -----------
def oracle(setRange, binRange, densityFlag, stacked):
    hk = {}
    if setRange:
        hk['range'] = binRange
    if densityFlag and not stacked:
        hk['density'] = densityFlag          # item-assignment: range preserved
    return hk


# --- SHADOW of implementation_assembleHistKeywordArgs (the R leg) -------------
# Mirrors Solution.lean impl region exactly: a HistKeywordArgs record with
# range/density fields, init both none, set each independently.
def shadow(setRange, binRange, densityFlag, stacked):
    rng = None
    den = None
    if setRange:
        rng = binRange
    if densityFlag and not stacked:
        den = densityFlag
    # normalize record to the dict representation (some v <-> present key)
    hk = {}
    if rng is not None:
        hk['range'] = rng
    if den is not None:
        hk['density'] = den
    return hk


def disagree(setRange, binRange, densityFlag, stacked):
    got = oracle(setRange, binRange, densityFlag, stacked)
    want = shadow(setRange, binRange, densityFlag, stacked)
    if got != want:
        return ((setRange, binRange, densityFlag, stacked), got, want)
    return None


def _enumerate_edge():
    cases = []
    R = (0, 1)
    # the F2P scenario: range requested AND density requested, not stacked
    # -> both entries must survive
    cases.append((True, R, True, False))
    # all 16 combinations of the three booleans x setRange (binRange fixed)
    for sr in (True, False):
        for d in (True, False):
            for st in (True, False):
                cases.append((sr, R, d, st))
    return cases


def main() -> int:
    checked = 0
    for c in _enumerate_edge():
        d = disagree(*c)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        setRange = rng.random() < 0.5
        binRange = (rng.randint(-1000, 1000), rng.randint(-1000, 1000))
        densityFlag = rng.random() < 0.5
        stacked = rng.random() < 0.5
        d = disagree(setRange, binRange, densityFlag, stacked)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
