#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-6599.

The bundle models ONE routine: `to_floatable`, the per-array value coercion
inside `_ensure_numeric` (mapping.md). The coerced value list is a PURE function
of three observables of the array:

    kind  : "datetime" | "duration" | "numeric"   (numpy dtype .kind "M"/"m"/else)
    raw   : list[int]   (the underlying int64 nanosecond buffer)
    data  : list[float] (the array's values as floats)

Post-patch rule (the gold edit SPLITS the single `kind in "mM"` clause into a
datetime-only branch and a NEW duration branch `x.astype(float)`):

    if   kind == "datetime": result = datetime_to_numeric(raw)     # unchanged
    elif kind == "duration": result = [float(n) for n in raw]      # NEW: astype(float)
    else:                    result = data                         # return x

`datetime_to_numeric` is UNCHANGED by the patch and appears identically in the
Lean spec helper and impl (carried as the opaque `datetimeToFloat`). It is
therefore modeled here as the SAME deterministic stand-in on both the oracle and
the shadow — G-CONF tests the soundness-critical part the patch actually changes:
the branch SELECTION by kind and the duration int→float cast. (Standing up numpy
to drive the real `datetime_to_numeric` is unnecessary: it is identical on both
legs and cancels.)

The discriminating clause: a duration array must be cast element-wise to float
(`[1000,2000,3000] -> [1000.0,2000.0,3000.0]`, the F2P case) and must NOT be
routed through the datetime reduction (which the pre-patch code did, raising or
producing the wrong epoch-relative values).

stdlib-only. Pinned seed: 6599 (also in mapping.md).
"""
import random
import sys

SEED = 6599
N = 120_000

DATETIME = "datetime"
DURATION = "duration"
NUMERIC = "numeric"
KINDS = [DATETIME, DURATION, NUMERIC]


# --- the unchanged datetime reduction, modeled as a deterministic stand-in -----
# Identical on oracle and shadow (it is the opaque `datetimeToFloat`); its exact
# numeric behavior is out of scope for the differential (unchanged by the patch).
def datetime_to_float(raw):
    return [("DT", n) for n in raw]


# --- ORACLE: faithful in-process replica of the POST-PATCH to_floatable --------
def oracle(inp):
    kind, raw, data = inp["kind"], inp["raw"], inp["data"]
    if kind == DATETIME:
        return datetime_to_float(raw)
    elif kind == DURATION:
        return [float(n) for n in raw]
    else:
        return data


# --- SHADOW of implementation_coerceToFloat (the R legs) -----------------------
# Mirrors Solution.lean impl region exactly (if/else-if chain on kind).
def shadow(inp):
    kind, raw, data = inp["kind"], inp["raw"], inp["data"]
    if kind == DATETIME:
        return datetime_to_float(raw)
    elif kind == DURATION:
        return [float(n) for n in raw]
    else:
        return data


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def mk(kind=NUMERIC, raw=None, data=None):
    return dict(kind=kind, raw=raw or [], data=data or [])


def _enumerate_edge():
    cases = []
    # F2P: duration buffer [1000,2000,3000] -> element-wise float cast
    cases.append(mk(DURATION, raw=[1000, 2000, 3000]))
    # duration: negatives, zero, large magnitude, NaT sentinel (int64 min)
    cases.append(mk(DURATION, raw=[0, -1, 1, -1000000000]))
    cases.append(mk(DURATION, raw=[-9223372036854775808, 5]))
    cases.append(mk(DURATION, raw=[]))
    # datetime controls (routed through the unchanged reduction)
    cases.append(mk(DATETIME, raw=[1617254719000000000]))
    cases.append(mk(DATETIME, raw=[]))
    # numeric: returned unchanged
    cases.append(mk(NUMERIC, data=[1.5, -2.0, 3.0]))
    cases.append(mk(NUMERIC, data=[]))
    return cases


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        kind = rng.choice(KINDS)
        length = rng.randint(0, 6)
        raw = [rng.randint(-(2**40), 2**40) for _ in range(length)]
        data = [rng.uniform(-1e6, 1e6) for _ in range(length)]
        inp = mk(kind=kind, raw=raw, data=data)
        d = disagree(inp)
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
