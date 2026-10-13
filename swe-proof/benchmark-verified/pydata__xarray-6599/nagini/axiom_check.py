#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6599.

Executes the REAL callees that model.py abstracts and asserts every observation
meets the contract encoded in model.py. Two kind-A checks plus the precondition
honesty of the axiom:

  (A-consumed) `elapsed_since` (model.py axioms region) models the unchanged
      callee `xarray.core.duck_array_ops.datetime_to_numeric`, called by the
      timestamp branch with `offset = np.datetime64("1970-01-01")` and
      `datetime_unit = "ns"`. The axiom states, for a TIME_POINT input:
          result[k] == values[k] - reference            (per element)
      where `values[k]` is the timestamp's ns-since-epoch magnitude and
      `reference` is the offset's ns-since-epoch magnitude. With the 1970-01-01
      offset the reference is 0, so result == the raw ns magnitudes. We run the
      REAL callee on datetime64[ns] arrays and assert this holds exactly.

  (precondition honesty) The axiom's `Requires(kind == TIME_POINT)` claims the
      instant-relative measurement is DEFINED ONLY for timestamps. We assert the
      REAL callee, called exactly as the timestamp branch calls it
      (offset = a datetime64 instant), RAISES on a timedelta64 (TIME_SPAN)
      input -- i.e. it genuinely cannot accept a duration. This is what makes
      routing a duration through it (the pre-patch bug) a real error, and what
      makes the precondition sound rather than artificially strong.

  (A-reference) `magnitude_read` (model.py pure region) is the deep model of the
      NEW duration branch `x.astype(float)`. We run the REAL `astype(float)` on
      timedelta64[ns] arrays and assert it equals the raw ns magnitudes (the
      identity that `magnitude_read` encodes).

Imports the real callee from xarray (the very function the patched code calls)
plus numpy. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np

from xarray.core.duck_array_ops import datetime_to_numeric

OFFSET = np.datetime64("1970-01-01")          # the timestamp branch's offset
REFERENCE_NS = OFFSET.astype("datetime64[ns]").astype("int64")  # == 0

# The not-a-value (NaT) sentinel magnitude: the int64 extremum. A datetime64[ns]
# whose underlying int64 magnitude is this value IS `NaT`, the unique nan-
# producing magnitude. The axiom's Requires(well_defined_magnitudes) EXCLUDES it
# (no element equals it); check_elapsed_since_axiom honours that exclusion, and
# check_sentinel_excluded asserts the exclusion is *necessary* (the real callee
# really does deviate from the per-element subtraction there).
NAT_NS = -9223372036854775808                 # == -2**63


def check_elapsed_since_axiom(ns_values):
    """A-consumed: real datetime_to_numeric on a TIME_POINT array whose
    magnitudes are well-defined (no NaT sentinel) meets
    Ensures(result[k] == values[k] - reference). Inputs containing the excluded
    NaT sentinel are NOT in the axiom's domain and are checked separately."""
    assert NAT_NS not in ns_values, (
        "check_elapsed_since_axiom must only see well-defined (NaT-free) "
        "magnitudes; %r contains the excluded sentinel" % (ns_values,))
    arr = np.array(ns_values, dtype="datetime64[ns]")
    observed = datetime_to_numeric(arr, offset=OFFSET, datetime_unit="ns")
    expected = [v - int(REFERENCE_NS) for v in ns_values]
    obs = [float(x) for x in np.asarray(observed).tolist()]
    exp = [float(x) for x in expected]
    assert obs == exp, (
        "elapsed_since axiom unsound on %r: datetime_to_numeric gave %r, "
        "axiom requires %r (reference_ns=%r)"
        % (ns_values, obs, exp, int(REFERENCE_NS)))


def check_sentinel_excluded():
    """Domain honesty for the NaT sentinel: the axiom's per-element-subtraction
    Ensures would OVER-CLAIM on the NaT sentinel magnitude -2**63 (it asserts
    result[k] == values[k] - reference == -2**63, but the real callee terminates
    in `np.where(isnull(array), np.nan, ...)` and returns `nan` there). We assert
    the real callee really does deviate (returns NaN, not the subtraction) on a
    NaT-containing datetime64[ns] array -- proving the axiom's
    Requires(well_defined_magnitudes) exclusion of -2**63 is NECESSARY, not
    gratuitous. This is the input the original (un-refined) axiom over-claimed on
    and that the old fuzz band [-10**15, 10**15] could never reach."""
    for tail in ([], [1000], [0, 999999999]):
        ns_values = [NAT_NS] + tail
        arr = np.array(ns_values, dtype="datetime64[ns]")
        observed = datetime_to_numeric(arr, offset=OFFSET, datetime_unit="ns")
        obs = np.asarray(observed).tolist()
        # element 0 is the NaT sentinel: real callee yields NaN, NOT -2**63
        assert isinstance(obs[0], float) and np.isnan(obs[0]), (
            "expected datetime_to_numeric to return NaN on the NaT sentinel "
            "magnitude %r, got %r -- if this ever equals the per-element "
            "subtraction the axiom's exclusion would be unnecessary" % (NAT_NS, obs[0]))
        assert obs[0] != float(NAT_NS - int(REFERENCE_NS)), (
            "axiom would over-claim: callee NaN at NaT sentinel must not equal "
            "the per-element subtraction %r" % (float(NAT_NS - int(REFERENCE_NS)),))
        # the well-defined tail elements still meet the per-element subtraction
        for j, v in enumerate(tail, start=1):
            assert obs[j] == float(v - int(REFERENCE_NS)), (
                "well-defined element %r mis-measured: got %r, want %r"
                % (v, obs[j], float(v - int(REFERENCE_NS))))


def check_precondition_honest(ns_magnitudes):
    """Precondition honesty: real datetime_to_numeric, called as the timestamp
    branch calls it (datetime offset), must RAISE on a timedelta (TIME_SPAN)
    input -- the measurement is undefined for durations."""
    arr = np.array(ns_magnitudes, dtype="timedelta64[ns]")
    raised = False
    try:
        datetime_to_numeric(arr, offset=OFFSET, datetime_unit="ns")
    except Exception:
        raised = True
    assert raised, (
        "precondition unsound: datetime_to_numeric(offset=datetime64) did NOT "
        "raise on a timedelta input %r -- the instant-relative measurement was "
        "expected to be undefined for durations" % (ns_magnitudes,))


def check_magnitude_read_reference(ns_magnitudes):
    """A-reference: real timedelta64[ns].astype(float) equals the raw ns
    magnitudes (the identity that magnitude_read models). Unlike the timestamp
    measurement, the duration branch's astype(float) does NOT special-case the
    NaT sentinel: a NaT timedelta64 simply reinterprets its int64 magnitude
    (-2**63) as that value's float image, so magnitude_read (identity) stays
    sound even on the sentinel -- the comparison is therefore against the float
    image of the raw int64 magnitude (no NaN expected)."""
    arr = np.array(ns_magnitudes, dtype="timedelta64[ns]")
    observed = arr.astype(float)                       # the new branch's op
    obs = [float(x) for x in np.asarray(observed).tolist()]
    exp = [float(np.float64(np.int64(v))) for v in ns_magnitudes]  # identity
    assert obs == exp, (
        "magnitude_read deep model unsound on %r: astype(float) gave %r, "
        "deep model (identity) gives %r" % (ns_magnitudes, obs, exp))


def main():
    assert int(REFERENCE_NS) == 0, (
        "the 1970-01-01 offset is the ns epoch; reference must be 0, got %r"
        % int(REFERENCE_NS))

    # --- the NaT-sentinel domain check (the over-claim the axiom now excludes)
    # The original axiom over-claimed on -2**63; the refined axiom's
    # Requires(well_defined_magnitudes) excludes it. Prove the exclusion is
    # NECESSARY: the real callee deviates (returns NaN) on the sentinel.
    check_sentinel_excluded()

    # --- boundary inputs (well-defined / NaT-free for the timestamp axiom) ---
    # The NaT sentinel -2**63 is OUT OF DOMAIN for check_elapsed_since_axiom
    # (the refined Requires excludes it) and is exercised by check_sentinel_
    # excluded above; it is IN domain for the duration branch (astype(float)
    # does not special-case it), so it appears in the magnitude_read boundary.
    boundary = [
        [],
        [0],
        [1000, 2000, 3000],            # the F2P timedelta magnitudes
        [0, 1000000000, 2000000000],   # the datetime test's ns-since-epoch
        [-1, -1000, 999999],
        [123456789, 987654321],
        # near-extreme well-defined int64 magnitudes (NOT the NaT sentinel):
        [9223372036854775807, -9223372036854775807],   # +max int64, -2**63+1
    ]
    for ns in boundary:
        check_elapsed_since_axiom(ns)
        check_magnitude_read_reference(ns)
        if ns:                          # raising check needs a non-empty array
            check_precondition_honest(ns)

    # the duration branch's identity is sound even on the NaT sentinel -2**63
    # (astype(float) reinterprets, no NaN) -- exercise it for magnitude_read:
    magnitude_boundary = [
        [NAT_NS],
        [NAT_NS, 1000, 2000],
        [9223372036854775807, NAT_NS, -9223372036854775807],
    ]
    for ns in magnitude_boundary:
        check_magnitude_read_reference(ns)
        check_precondition_honest(ns)

    # at least one non-trivial duration array for the precondition check
    check_precondition_honest([1000, 2000, 3000])

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(6599)
    # explicit near-int64-extreme draws (incl. the NaT sentinel) so the fuzz
    # band is no longer blind to the boundary the original axiom over-claimed on.
    extremes = [NAT_NS, NAT_NS + 1, 9223372036854775807,
                -10**15, 10**15, 0, -1, 1]
    for _ in range(20000):
        n = rng.randint(0, 16)
        # mix the generic band with deliberate int64 extremes / the NaT sentinel
        ns = []
        for _j in range(n):
            if rng.random() < 0.25:
                ns.append(rng.choice(extremes))
            else:
                ns.append(rng.randint(-10**15, 10**15))
        # the timestamp axiom is checked only on its (NaT-free) domain; any draw
        # of the NaT sentinel is routed to the dedicated sentinel check instead.
        if NAT_NS in ns:
            check_sentinel_excluded()
        else:
            check_elapsed_since_axiom(ns)
        check_magnitude_read_reference(ns)   # sound on the full int64 range
        if ns:
            check_precondition_honest(ns)

    print("G-AX OK: elapsed_since axiom (== datetime_to_numeric, ref=0) sound on "
          "its NaT-free domain, the NaT sentinel -2**63 correctly EXCLUDED "
          "(real callee returns NaN there, so the exclusion is necessary), "
          "precondition honest (datetime_to_numeric raises on timedelta), and "
          "magnitude_read deep model (== timedelta astype(float)) sound on the "
          "full int64 range incl. the NaT sentinel; %d+%d boundary + 20000 fuzz "
          "inputs (now fuzzing int64 extremes / NaT sentinel)"
          % (len(boundary), len(magnitude_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
