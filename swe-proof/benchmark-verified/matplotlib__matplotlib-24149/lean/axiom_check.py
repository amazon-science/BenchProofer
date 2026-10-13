#!/usr/bin/env python3
"""G-AX — validate the A-reference deep models against the REAL matplotlib
callees that the patched `_convert_dx` selection delegates to.

The proof consumes NO callee axiom (axioms region empty). The A-reference models
are validated against the real callees over boundary + fuzz inputs
(refinement.md rows 2, 3, 4, 6):

  * `CoordVal.countsAsFinite`     == the real per-value test the search applies,
                                     across ALL THREE of its regimes: weighed by
                                     np.isfinite for a value it can weigh as a
                                     quantity, GRANTED unconditionally for a value
                                     it cannot weigh (a date, a duration, an exact
                                     decimal, text, a whole vector), and WITHHELD
                                     from a missing value
  * first-finite scan (find?)     == cbook._safe_first_finite(seq) (or its
                                     StopIteration, mapped to "no finite")
  * non-empty first-element       == cbook.safe_first_element(seq) == seq[0]
  * the `.single` identity arm    == the real callee's TypeError on a
                                     NON-ITERABLE argument, which the enclosing
                                     `except (TypeError, IndexError, KeyError):
                                     pass` turns into "the argument is its own
                                     representative"

The combined selection `chooseRepresentative` is then checked against the exact
post-patch selection over BOTH argument shapes. Fuzzing the lone-coordinate shape
is load-bearing, not decorative: it is the only configuration in which the
PLACEMENT of the `safe_first_element` call is observable, and an earlier revision
of this bundle fuzzed only non-empty numeric arrays and therefore validated a
model that admitted a mis-placed call (see refinement.md).

Runs the REAL callees in-container. exit 0 iff every observation matches.
"""
import datetime
import decimal
import math
import random
import sys

import numpy as np
from matplotlib import cbook

SEED = 24149


def real_counts_as_finite(val):
    """The real per-value test the search applies, reconstructed VERBATIM from the
    unchanged helper at base_commit (it is a closure inside `_safe_first_finite`,
    so it cannot be imported; this is a byte-faithful transcription and the
    transcription itself is asserted against the helper's observable behavior in
    section 1 below)."""
    if val is None:
        return False
    try:
        return np.isfinite(val) if np.isscalar(val) else True
    except TypeError:
        return True


def model_counts_as_finite(val):
    """Lean `CoordVal.countsAsFinite`, applied via the value's REGIME.

      .numeric v     -> v.isFinite   (an IEEE-754 double, weighed)
      .unweighable _ -> true         (not weighable as a quantity: counts anyway)
      .missing       -> false        (absent: never counts)
    """
    kind = regime_of(val)
    if kind == "numeric":
        return math.isfinite(float(val))
    if kind == "unweighable":
        return True
    return False


def regime_of(val):
    """Which CoordVal constructor a real coordinate value maps to, per the
    mapping.md type bijection: `missing` iff the value is absent; `numeric` iff
    the real test WEIGHS it as a quantity (np.isscalar and np.isfinite applies);
    `unweighable` otherwise."""
    if val is None:
        return "missing"
    if np.isscalar(val):
        try:
            np.isfinite(val)
            return "numeric"
        except TypeError:
            return "unweighable"
    return "unweighable"


def model_choose(arg):
    """Lean `chooseRepresentative` over a CoordArg -> Option CoordVal.

    arg is ("single", v) or ("sequence", vs).

      .single v    -> some v                      (no finiteness test applies)
      .sequence vs -> find? (.countsAsFinite); on some -> that value;
                      on none -> head? (first elem, or None when empty)

    The per-value test is the REGIME-aware `countsAsFinite`, not bare arithmetic
    finiteness — which is exactly the distinction this gate now validates.
    """
    kind, payload = arg
    if kind == "single":
        return ("some", payload)
    vs = payload
    for v in vs:
        if model_counts_as_finite(v):
            return ("some", v)
    if len(vs) > 0:
        return ("some", vs[0])
    return ("none", None)


def real_selection(obj, *, is_sequence):
    """The post-patch selection inside `_convert_dx`, isolated:

        try:                                     sel = _safe_first_finite(obj)
        except (TypeError, IndexError, KeyError): sel = obj   (unchanged)
        except StopIteration:                    sel = safe_first_element(obj)

    Returns ("some", v) or ("none", None) for the empty sequence. For the
    sequence shape we pass a numpy array, exactly as the F2P path does
    (np.asarray(convert_xunits(x))); for the lone-coordinate shape we pass the
    bare object, exactly as bar() passes `x0 = x`."""
    if is_sequence:
        # NOTE: deliberately NOT coerced through np.asarray(dtype=float). An
        # earlier revision did, which made every sequence of dates / durations /
        # exact decimals / absences literally unconstructible here — so the one
        # input class on which the regime-aware test differs from bare arithmetic
        # finiteness was outside this gate BY CONSTRUCTION. The callers pass such
        # sequences through verbatim, so they are fuzzed verbatim. Numeric
        # sequences are still materialised as ndarrays, matching the caller that
        # does convert.
        if len(obj) == 0:
            return ("none", None)
        if all(isinstance(v, (int, float, np.number)) and not isinstance(v, bool)
               for v in obj):
            target = np.asarray(obj, dtype=float)
        else:
            target = list(obj)
    else:
        target = obj
    try:
        return ("some", cbook._safe_first_finite(target))
    except (TypeError, IndexError, KeyError):
        # the argument is left bound to itself -> it IS the representative
        return ("some", target)
    except StopIteration:
        return ("some", cbook.safe_first_element(target))


def feq(a, b) -> bool:
    if a[0] != b[0]:
        return False
    if a[0] == "none":
        return True
    x, y = a[1], b[1]
    if isinstance(x, (float, np.floating)) and isinstance(y, (float, np.floating)):
        return (math.isnan(float(x)) and math.isnan(float(y))) or float(x) == float(y)
    return x == y or repr(x) == repr(y)


def main() -> int:
    rng = random.Random(SEED)
    NONFIN = [float("nan"), float("inf"), float("-inf")]
    FIN = [0.0, -0.0, 1.0, -1.0, 3.14, -2.5, 1e9, -1e-9, 42.0]

    # --- 1a. the transcribed per-value test == the REAL helper's own ruling.
    # Observable, not assumed: a ONE-ELEMENT sequence [v] selects v iff the test
    # counts v, and otherwise the search exhausts (StopIteration) and the
    # fall-back returns v anyway — so the ruling is read off the TWO-element
    # sequence [v, sentinel], where a counted v selects v and a passed-over v
    # selects the finite sentinel. That isolates the ruling exactly.
    SENTINEL = 12345.678
    regime_probe = (NONFIN + FIN + [rng.uniform(-1e6, 1e6) for _ in range(500)]
                    + [None, 3, -7, True, np.float64(2.0), np.float64(np.nan),
                       np.int64(5), np.asarray(1.0), np.asarray(float("nan")),
                       datetime.datetime(2018, 1, 1), datetime.date(2018, 1, 1),
                       datetime.timedelta(hours=3), decimal.Decimal("1.5"),
                       "abc", [1, 2], (1.0, 2.0)])
    mism = 0
    for v in regime_probe:
        try:
            sel = cbook._safe_first_finite([v, SENTINEL])
            observed = not (isinstance(sel, float) and sel == SENTINEL)
        except (TypeError, IndexError, KeyError, StopIteration):
            observed = None       # the helper did not get to rule; skip
        if observed is None:
            continue
        if bool(real_counts_as_finite(v)) != observed:
            print(f"G-AX FAIL: transcription({v!r}) = "
                  f"{real_counts_as_finite(v)} but the REAL helper ruled "
                  f"{observed}")
            mism += 1
        # 1b. and the LEAN model agrees with the real ruling, per regime.
        if bool(model_counts_as_finite(v)) != observed:
            print(f"G-AX FAIL: countsAsFinite regime model({v!r}, "
                  f"regime={regime_of(v)}) = {model_counts_as_finite(v)} but the "
                  f"REAL helper ruled {observed}")
            mism += 1
    if mism:
        return 1
    probe_scalars = regime_probe

    # --- 2. SEQUENCE shape: combined selection vs real callees ---
    alphabet = NONFIN * 4 + FIN
    fixed_seqs = [
        [],                       # empty -> none
        [float("nan")],           # the F2P bug case -> some nan
        [float("nan"), 1.0],      # leading nan, finite present -> some 1.0
        [float("inf"), float("-inf"), float("nan")],   # all nonfinite -> some inf
        [1.0, float("nan")],      # finite first
        [0.0],                    # finite singleton
        [float("nan"), float("nan"), 2.0, 3.0],
    ]
    # The regimes on which bare arithmetic finiteness DIVERGES from the real
    # ruling, driven as SEQUENCES — the class an earlier revision could not build.
    D = datetime.datetime(2018, 1, 1)
    DT = datetime.timedelta(hours=3)
    fixed_seqs += [
        [D, D],                  # the timedelta regression's own shape
        [D, 2.0], [2.0, D], [float("nan"), D], [D, float("nan")],
        [DT, D], [decimal.Decimal("1.5"), 2.0], ["a", 2.0],
        [None, 2.0], [None], [None, None], [None, D], [None, float("nan")],
        [np.asarray(float("nan")), 2.0], [(1.0, 2.0), 3.0],
        [D, None, 2.0], [None, D, 2.0],
    ]
    seq_cases = list(fixed_seqs)
    for _ in range(60_000):
        n = rng.randint(0, 8)
        seq_cases.append([rng.choice(alphabet) for _ in range(n)])
    # ...and fuzzed MIXED-REGIME sequences, so the ruling is exercised at every
    # position rather than only at a leading one.
    EXOTIC = [D, DT, datetime.date(2018, 1, 1), decimal.Decimal("1.5"), "a",
              np.asarray(float("nan")), (1.0, 2.0)]
    mixed_alphabet = alphabet + EXOTIC * 3 + [None] * 3
    for _ in range(40_000):
        n = rng.randint(1, 6)
        seq_cases.append([rng.choice(mixed_alphabet) for _ in range(n)])

    bad = 0
    examples = []
    for vs in seq_cases:
        got = model_choose(("sequence", vs))
        want = real_selection(vs, is_sequence=True)
        if not feq(got, want):
            bad += 1
            if len(examples) < 10:
                examples.append((("sequence", vs), got, want))

    # --- 3. LONE-COORDINATE shape: the identity arm vs the real TypeError route.
    # This is the configuration in which the mis-placed-fall-back rivals diverge
    # from the patched behavior, so it is fuzzed rather than assumed.
    fixed_singles = [
        1.0, -1.0, 0.0, -0.0, 42.0,
        float("nan"), float("inf"), float("-inf"),   # NO finiteness filter here
        1e308, 5e-324,
    ]
    single_cases = list(fixed_singles) + [
        rng.choice(NONFIN + FIN) for _ in range(30_000)
    ]
    for v in single_cases:
        got = model_choose(("single", v))
        want = real_selection(v, is_sequence=False)
        if not feq(got, want):
            bad += 1
            if len(examples) < 10:
                examples.append((("single", v), got, want))

    # --- 4. lone coordinates that are not plain floats. The model abstracts the
    # value to a Float because the selection never inspects it; what must hold is
    # that the real callee still routes them to the identity arm (a representative
    # IS produced, and it is the argument itself). These are the values the
    # timedelta regressions actually drive.
    exotic = [
        3, -7, np.float64(2.0), np.int64(5),
        np.asarray(1.0), np.asarray(float("nan")),
        datetime.datetime(2018, 1, 1),
        datetime.date(2018, 1, 1),
    ]
    for v in exotic:
        want = real_selection(v, is_sequence=False)
        if want[0] != "some":
            bad += 1
            if len(examples) < 10:
                examples.append((("single-exotic", v), ("some", v), want))
            continue
        # the representative must be the argument itself (identity route)
        if not (want[1] is v or repr(want[1]) == repr(v)):
            bad += 1
            if len(examples) < 10:
                examples.append((("single-exotic", v), ("some", v), want))

    if bad:
        print(f"G-AX FAIL: {bad} selection mismatches vs real cbook callees")
        for s, g, w in examples:
            print(f"  arg={s!r} model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: countsAsFinite (all three regimes) / _safe_first_finite / "
          f"safe_first_element deep models == real callees on {len(seq_cases)} "
          f"sequences (numeric AND mixed-regime) + "
          f"{len(single_cases)} lone coordinates + {len(exotic)} non-float lone "
          f"coordinates + {len(probe_scalars)} scalars (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
