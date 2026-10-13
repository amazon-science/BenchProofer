#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24970 (plan §4.1).

Band: pure-data (per-element lookup-table slot resolution).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `resolveSlots` impl region
              transliterated to Python: classify each input element into a
              `Cell` (mapping.md §2.1), then `slotOf`/`slotSeq` map each class to
              its lookup-table slot — ordinary index `k` to `k` while `k` is
              strictly inside the palette (mapping.md §2.4), and the three
              out-of-range / invalid classes to the EXACT reserved trailing slots
              `N`, `N+1`, `N+2`.
  * ORACLE  — `patch.diff`'s behaviour: a REAL `matplotlib.colors.Colormap`
              built at base_commit with the gold patch applied. We call the real
              `cmap(X)` (the patched `Colormap.__call__`) and RECOVER the slot
              each element resolved to by matching its output RGBA row against
              the colormap's lookup table `cmap._lut` (the array `lut.take(xa,
              …)` indexes, `colors.py:738`). The recovered slot index per element
              IS the value the modeled result reads back — `slotsOf out`
              (mapping.md §2). This is the real correctness oracle (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

THE DISCRIMINATING PATH. Pre-patch, the index cast `xa.astype(int)` ran only
inside the `xa.dtype.kind == "f"` branch, so float inputs were already widened;
INTEGER-dtype inputs (e.g. `uint8`, the F2P `test_index_dtype[uint8]` case)
skipped it, leaving the resolved slots in a carrier too narrow to hold the
reserved indices `N`, `N+1`, `N+2` (for the default `N = 256`, `uint8`'s max is
255 < 256), which numpy then wrapped/raised on. The patch makes the cast
unconditional. We therefore fuzz integer dtypes (uint8 especially) AND float
dtypes so the shadow/oracle agreement is exercised on exactly the path the bug
lived on.

THE CAST IS ALSO PART OF CLASSIFICATION, and the shadow applies it
unconditionally for that reason (mapping.md §2.1). It targets the SIGNED platform
`int`, so an unsigned element that does not fit wraps NEGATIVE and the under-range
store claims it: at `N = 6` a `uint64` element `2**63 - 1` resolves to `overSlot`
(it fits) while `2**63`, `2**63 + 1` and `2**64 - 1` resolve to `underSlot`. The
boundary cases below therefore include every integer dtype's own extremes and the
`uint64` signed threshold, and the fuzz draws integer values from each dtype's
full range rather than a clamped window, so this region is reachable at all.

TWO CONTAINER PROPERTIES, TWO DISCRIMINATING LEGS. The cast the fix hoists gives
the container both of the properties the reserved-marker assignment needs, and the
spec has one obligation per property, so this check has one leg per obligation:

  * carrier legality (`paletteSize + 3 <= carrier`) — the reserved markers fit,
    observed as the ABSENCE of the out-of-bound cast report on an empty uint8
    input (input-independent, which is what the F2P discriminates);
  * container signedness (`admitsNegative = true`) — the below-range selection
    `xa[xa < 0] = self._i_under` still selects something, observed as a
    below-range element resolving to `underSlot` and NOT to `overSlot`. Its
    negative control is the same resolution in an unsigned container that already
    satisfies the width obligation, where the element resolves to `overSlot`
    instead — so the two legs are independent and neither implies the other.

A THIRD LEG COVERS WHAT THE FORWARD FUZZ STRUCTURALLY CANNOT SEE. The fuzz above
runs `classify` on real input values, so it only ever reaches the IMAGE of the
classification. `Cell` is a wider syntax than that image — `inPalette k` is
well-formed for every `k` while `classify` produces only `k <= N-1` — and the
classified row is an INPUT of the modeled function, so the model's claim about an
ordinary cell carrying an out-of-palette index is a claim about the repository that
has to hold. That region is compared directly against the three stores run on the
index array (`colors.py:730-732` verbatim), with the identity reading of an
ordinary index as the negative control (mapping.md §2.4).

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + numpy + matplotlib only. The fuzz seed is pinned (mapping.md
§4) for a deterministic verdict.
"""
import random
import sys
import warnings

import numpy as np

import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import ListedColormap

SEED = 24970
N_FUZZ = 100_000

# A small palette so reserved indices N, N+1, N+2 are easy to materialise and
# so a uint8 input can address both ordinary slots (< N) and, after we force
# the under/over/bad classes, the reserved slots. We give every lut row a
# DISTINCT colour so the recovered slot is unambiguous.
PALETTE_N = 6


def make_cmap(n):
    """A ListedColormap with `n` ordinary slots, each a distinct colour, and
    distinct under/over/bad colours so all `n + 3` lut rows differ. Returns the
    initialised cmap (so `cmap._lut` is populated)."""
    # n distinct ordinary colours in [0,1]; keep them away from the reserved
    # colours we set below.
    colors = [(i / (2.0 * n), 0.10 + i / (4.0 * n), 0.20, 1.0) for i in range(n)]
    cmap = ListedColormap(colors, name="gconf24970")
    cmap.set_under((1.0, 0.0, 0.0, 1.0))   # reserved slot N
    cmap.set_over((0.0, 1.0, 0.0, 1.0))    # reserved slot N+1
    cmap.set_bad((0.0, 0.0, 1.0, 1.0))     # reserved slot N+2
    cmap._init()                            # build cmap._lut (n+3 rows)
    return cmap


# --- the R/I shadow: classify + slotOf/slotSeq, transliterated ---------------

def classify(value, n, is_nan):
    """mapping.md §2.1: the class of one element AS THE THREE RESERVED-MARKER
    STORES SEE IT. `value` is the element's POST-CAST integer value (the cast is
    unconditional in the reference tree — see shadow_slots); `n` is paletteSize.
    `invalid` first, because `xa[mask_bad] = _i_bad` is the last store and
    overwrites whatever the range stores wrote at that position."""
    if is_nan:
        return ("invalid", None)
    if value < 0:
        return ("belowRange", None)
    if value > n - 1:
        return ("aboveRange", None)
    return ("inPalette", int(value))


def slot_of(cell_kind, k, n):
    """slotOf transliterated (mapping.md §2.4).

    An ordinary index keeps the value it carries ONLY while that value is strictly
    inside the palette. The three stores are three SELECTIONS in a fixed order and
    the FIRST of them, `xa[xa > self.N - 1]`, also selects an element carrying one
    of the reserved marker values, so such an element resolves to `overSlot`
    instead of keeping its index. `classify` never produces such a cell (it is
    outside the classification's image), so this guard is unreachable through the
    fuzz above; it is exercised directly by `out_of_image_leg`."""
    if cell_kind == "inPalette":
        return k if k < n else n + 1
    if cell_kind == "belowRange":
        return n          # underSlot
    if cell_kind == "aboveRange":
        return n + 1      # overSlot
    return n + 2          # invalidSlot


def shadow_slots(X, n):
    """slotSeq of the classified row. X is the raw input array; we reproduce the
    examination and the index cast exactly as the reference tree does, then map
    each class to its slot. Returns a list[int] of resolved slots."""
    xa = np.array(X, copy=True)
    mask_bad = np.isnan(xa) if xa.dtype.kind == "f" else np.zeros(xa.shape, bool)
    # Reproduce the upstream value examination VERBATIM (colors.py:717-726) and
    # then the index cast, which in the reference tree is UNCONDITIONAL and sits
    # immediately before the three stores. Critical fidelity points the abstract
    # `Cell` classification depends on:
    #   * the float scaling `xa *= self.N` runs IN THE INPUT DTYPE (colors.py:719) —
    #     for a float16 input it rounds in float16, so e.g. 0.6665*6 == 4.0 (not the
    #     float64 value 3.999). Upcasting to float64 first would misclassify it.
    #   * the cast TRUNCATES toward zero BEFORE the over/under comparison
    #     (colors.py:730), so 5.49 (=0.914*6) resolves to the in-range integer 5,
    #     not `aboveRange`.
    #   * the cast applies to INTEGER inputs too, and it targets the signed
    #     platform `int`. An unsigned element that does not fit therefore WRAPS
    #     NEGATIVE and the `xa < 0` store claims it: a uint64 element >= 2**63
    #     resolves to underSlot, not overSlot, even though its magnitude is far
    #     above the palette (mapping.md §2.1). Classifying off the pre-cast value
    #     would get exactly that region wrong.
    # We therefore mutate `xa` in place exactly as the repo does, then classify off
    # the resulting integer array.
    with np.errstate(invalid="ignore"):
        if xa.dtype.kind == "f":
            xa *= n                          # in-dtype scale (colors.py:719)
            xa[xa < 0] = -1                  # colors.py:722
            xa[xa == n] = n - 1              # colors.py:724
            np.clip(xa, -1, n, out=xa)       # colors.py:726
        xa = xa.astype(int)                  # unconditional in the reference tree
    out = []
    flat_vals = np.ravel(xa)
    flat_bad = np.ravel(mask_bad)
    for v, b in zip(flat_vals, flat_bad):
        # `v` is the post-cast integer index; classify() routes it to
        # inPalette/below/above/invalid.
        kind, k = classify(v, n, bool(b))
        out.append(slot_of(kind, k, n))
    return out


# --- the oracle: real patched cmap, slot recovered from the output RGBA ------

def _row_to_slot(rgba_row, lut):
    """Recover which lut row produced this output RGBA row (exact match)."""
    matches = np.where(np.all(lut == rgba_row, axis=1))[0]
    # Distinct colours per row ⇒ a unique match. (mode='clip' on take never
    # invents a colour outside lut.)
    return int(matches[0])


def oracle_slots(X, cmap):
    """patch.diff's behaviour: call the REAL patched cmap and recover the slot
    each element resolved to by matching its output RGBA against cmap._lut."""
    lut = cmap._lut
    with warnings.catch_warnings():
        # The whole point of the patch is that the patched code raises NO
        # warning; if the (pre-patch) code under test warns we want to SEE it,
        # but the oracle here is the PATCHED tree, so be explicit and let any
        # unexpected warning surface as an error during development.
        warnings.simplefilter("error", DeprecationWarning)
        rgba = cmap(X)
    rgba = np.asarray(rgba, dtype=float).reshape(-1, 4)
    return [_row_to_slot(rgba[i], lut) for i in range(rgba.shape[0])]


def oracle_carrier_represents_reserved(cmap, n):
    """patch.diff's carrier-legality behaviour (the discriminating change). The
    gold hunk relocates `xa = xa.astype(int)` so it runs UNCONDITIONALLY (out of
    the `kind == "f"` branch). The carrier the reserved markers are written into
    is therefore always a wide integer array that ADMITS every reserved marker
    (N, N+1, N+2), INDEPENDENT of the input dtype and of whether any element
    selects a reserved slot — exactly the precondition the gated callee's
    `markersAdmitted` capability abstracts (`paletteSize + 3 <= carrier`).

    We confirm this directly: feeding a NARROW integer dtype (uint8) whose
    representable range (0..255) is < the reserved markers (N+1 = 257 for N=256),
    the patched code must NOT raise the out-of-bound-cast warning (it widens
    first), i.e. the carrier admits the markers.

    Returns the carrier's effective representable range (the count of admitted
    values), matching the modeled `carrier` parameter: a value `>= n + 3` when
    the markers are admitted, or `n` when they are not. For an empty/in-range
    input the marker writes are still materialised by numpy, so the warning is a
    function of dtype+N alone, not of element values."""
    # Use the default N = 256 colormap path width: a uint8 input forces the
    # narrow-carrier path the bug lived on. We probe with an EMPTY uint8 array
    # (no element selects any reserved slot) — pre-patch this still warns,
    # post-patch it must not, proving the carrier-legality fix is input-independent.
    probe = np.empty((0,), dtype=np.uint8)
    raised = False
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        try:
            cmap(probe)
        except DeprecationWarning:
            raised = True
    if raised:
        # The carrier could NOT admit the reserved markers — its representable
        # range is only as wide as the narrow input dtype.
        return n  # i.e. paletteSize + 3 NOT <= carrier -> precondition fails
    # The carrier widened to int: it admits every reserved marker.
    return n + 3


def oracle_container_admits_negative(cmap, n):
    """patch.diff's OTHER container property, and the second obligation of the
    modeled callee: the container the reserved markers are written into must
    represent values BELOW zero.

    The gold hunk casts to the platform SIGNED `int`, so it does. The observable
    consequence is that `xa[xa < 0] = self._i_under` (colors.py:731) still selects
    something: a below-range element resolves to `underSlot = n`. In a container
    that reaches high enough for the markers but not below zero, that store selects
    NOTHING and the element keeps the `overSlot = n + 1` the preceding store wrote,
    because a below-range element IS a large positive value there.

    Probes the real patched tree with a below-range float element and returns True
    iff it resolves to `underSlot`, i.e. iff the container admits negative values —
    the modeled `admitsNegative`.

    Uses the DISTINCT-row palette (`make_cmap`), not a stock colormap: a stock
    colormap's under/over/bad rows default to copies of its own extreme colours, so
    slot recovery from the output RGBA is ambiguous there (`underSlot`'s row is
    byte-identical to slot 0's) and the probe would report the wrong slot."""
    probe = np.array([-1.0], dtype=float)
    slots = oracle_slots(probe, cmap)
    return slots == [n]


def unsigned_container_control(n):
    """NEGATIVE CONTROL for the leg above, so it is load-bearing rather than
    decorative: the same resolution carried out in an UNSIGNED container that
    admits every reserved index (uint16, carrier 65536 >= n + 3). Returns the
    resolved slot of the same below-range element. It must NOT be `underSlot`."""
    xa = np.array([-1.0], dtype=float)
    mask_bad = np.isnan(xa)
    xa = xa * n
    with np.errstate(invalid="ignore"):
        xa[xa < 0] = -1
        xa[xa == n] = n - 1
        np.clip(xa, -1, n, out=xa)
        xa = xa.astype(np.uint16)          # admits every marker; not below zero
    xa[xa > n - 1] = n + 1                 # _i_over
    xa[xa < 0] = n                         # _i_under (dead in an unsigned array)
    xa[mask_bad] = n + 2                   # _i_bad
    return [int(v) for v in xa.tolist()]


# --- input generation --------------------------------------------------------

INT_DTYPES = [np.uint8, np.uint16, np.uint32, np.uint64,
              np.int8, np.int16, np.int32, np.int64]


def _store_block(index_values, mask_bad, n):
    """The three reserved-marker stores VERBATIM (colors.py:730-732), applied to an
    index array already in hand. This is the oracle for a classified row that the
    forward fuzz cannot reach: `Cell` is a wider syntax than `classify`'s image, so
    an ordinary cell may carry an index the classification never produces, and the
    model still has to say truthfully what such an element resolves to."""
    xa = np.array(index_values, dtype=int, copy=True)
    bad = np.array(mask_bad, dtype=bool)
    xa[xa > n - 1] = n + 1          # colors.py:730  _i_over   — runs FIRST
    xa[xa < 0] = n                  # colors.py:731  _i_under
    xa[bad] = n + 2                 # colors.py:732  _i_bad
    return xa.tolist()


def _cells_to_index_row(cells, n):
    """The index values and bad-mask the store block sees for a classified row.
    `belowRange` is any negative value, `aboveRange` any value above `n-1`, and an
    `inPalette k` cell carries exactly `k` — including a `k` outside the palette."""
    vals, bad = [], []
    for kind, k in cells:
        if kind == "inPalette":
            vals.append(int(k)); bad.append(False)
        elif kind == "belowRange":
            vals.append(-1); bad.append(False)
        elif kind == "aboveRange":
            vals.append(n); bad.append(False)
        else:
            vals.append(0); bad.append(True)
    return vals, bad


def out_of_image_rows(n):
    """Classified rows whose ordinary cells carry indices OUTSIDE the palette —
    exactly the region `classify` never produces and the fuzz therefore cannot
    reach. Includes each reserved marker value as an ordinary index, which is the
    collision the resolution must not make."""
    rows = [
        [("inPalette", n)],
        [("inPalette", n + 1)],
        [("inPalette", n + 2)],
        [("inPalette", n + 7)],
        [("inPalette", 2 * n)],
        [("inPalette", n), ("belowRange", None)],
        [("inPalette", n + 2), ("invalid", None)],
        [("belowRange", None), ("inPalette", n), ("aboveRange", None),
         ("invalid", None), ("inPalette", 0)],
    ]
    if n >= 2:
        rows.append([("inPalette", n - 1), ("inPalette", n)])
    return rows


def fuzz_inputs(n, rng):
    """Yield (label, numpy array) inputs. Integer dtypes (the bug's path) and
    float dtypes, plus boundary cases (empty, exact reserved-triggering, and each
    integer dtype's own extremes — where the index cast into the signed carrier
    wraps, mapping.md §2.1)."""
    # boundary: the F2P matrix — scalar 0 of each dtype the test parametrizes
    for dt in (np.uint8, np.int64, np.float16, np.float64):
        yield ("scalar0-%s" % np.dtype(dt).name, np.array([dt(0)]))
    # boundary: each integer dtype's own extremes, UNCLAMPED. For an unsigned
    # dtype at least as wide as the signed carrier, the top of the range is where
    # the unconditional cast wraps negative and the under-range store claims the
    # element — the region a clamped fuzz window cannot reach.
    for dt in INT_DTYPES:
        info = np.iinfo(dt)
        vals = sorted({int(info.min), int(info.min) + 1, 0, 1, n - 1, n, n + 1,
                       int(info.max) - 1, int(info.max)})
        vals = [v for v in vals if int(info.min) <= v <= int(info.max)]
        yield ("dtype-extremes-%s" % np.dtype(dt).name, np.array(vals, dtype=dt))
    # boundary: the uint64 signed threshold itself. 2**63 - 1 still fits the
    # signed carrier (so it stays above the palette), 2**63 and beyond wrap.
    yield ("uint64-signed-threshold",
           np.array([2**63 - 2, 2**63 - 1, 2**63, 2**63 + 1, 2**64 - 1],
                    dtype=np.uint64))
    # boundary: order-preserving probe — an ordinary index, a wrapping element,
    # an above-range element and 0 in one row, so a per-element (not per-row)
    # disagreement is localised.
    yield ("uint64-order-probe",
           np.array([min(5, max(n - 1, 0)), 2**63, 300, 0], dtype=np.uint64))
    # the bug repro: empty uint8 array
    yield ("empty-uint8", np.empty((0,), dtype=np.uint8))
    yield ("empty-f64", np.empty((0,), dtype=np.float64))
    # uint8 covering ordinary indices AND values that exceed N-1 (over) — for
    # N <= 255 a uint8 can hold an over-range index.
    yield ("uint8-range", np.arange(0, 256, dtype=np.uint8))
    # integer inputs that hit under (negative) and over (> N-1)
    yield ("int-mixed", np.array([-5, -1, 0, 1, n - 1, n, n + 10, 1000], dtype=np.int64))
    # float inputs: 0..1 maps across the palette; <0 under; >1 over; nan bad
    yield ("float-spread",
           np.array([-0.5, 0.0, 0.25, 0.5, 0.999, 1.0, 1.5, np.nan], dtype=np.float64))
    yield ("float16-spread",
           np.array([-0.5, 0.0, 0.5, 1.0, 1.5], dtype=np.float16))

    int_dtypes = INT_DTYPES
    flt_dtypes = [np.float16, np.float32, np.float64]
    for _ in range(N_FUZZ):
        k = rng.randint(0, 12)
        if rng.random() < 0.6:
            dt = rng.choice(int_dtypes)
            info = np.iinfo(dt)
            # Drawn from the dtype's OWN full range, not a clamped window: the
            # top of an unsigned 64-bit range is where the index cast wraps into
            # the signed carrier, and a window of -50..300 never reaches it.
            vals = []
            for _ in range(k):
                r = rng.random()
                if r < 0.20:
                    vals.append(int(info.max) - rng.randint(0, 2))
                elif r < 0.30:
                    vals.append(int(info.min) + rng.randint(0, 2))
                else:
                    vals.append(rng.randint(max(int(info.min), -50),
                                            min(int(info.max), 300)))
            arr = np.array(vals, dtype=dt)
            yield ("int-fuzz", arr)
        else:
            dt = rng.choice(flt_dtypes)
            vals = []
            for _ in range(k):
                r = rng.random()
                if r < 0.15:
                    vals.append(float("nan"))
                elif r < 0.30:
                    vals.append(rng.uniform(-2.0, 0.0))
                elif r < 0.45:
                    vals.append(rng.uniform(1.0, 3.0))
                else:
                    vals.append(rng.uniform(0.0, 1.0))
            yield ("float-fuzz", np.array(vals, dtype=dt))


def main():
    rng = random.Random(SEED)
    cmap = make_cmap(PALETTE_N)
    n = cmap.N
    assert cmap._lut.shape[0] == n + 3, "lut must have N+3 rows"
    # sanity: all lut rows distinct so slot recovery is unambiguous
    uniq = {tuple(row) for row in cmap._lut}
    assert len(uniq) == n + 3, "palette rows must be distinct for recovery"

    disagreements = []
    count = 0
    for label, X in fuzz_inputs(n, rng):
        count += 1
        shadow = shadow_slots(X, n)
        oracle = oracle_slots(X, cmap)
        if shadow != oracle:
            disagreements.append((label, np.ravel(X).tolist(), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for label, x, sh, orc in disagreements:
            print("  [%s] input=%r shadow=%r oracle=%r" % (label, x, sh, orc))
        return 1

    # --- the DISCRIMINATING leg: the carrier-legality of the marker writes ---
    # The Lean spec's discriminating obligation is the unforgeable capability
    # `markersAdmitted out paletteSize`, granted only by the gated callee
    # `assignReserved` under the precondition `paletteSize + 3 <= carrier` — the
    # carrier into which the reserved markers are written must admit the largest
    # one (`invalidSlot = n+2`) on EVERY call, independent of element values. We
    # confirm the REAL patched tree exhibits exactly this legality: build a
    # DEFAULT-N colormap (N=256, the F2P `viridis` path) where a uint8 carrier
    # cannot hold the reserved markers (257 > 255), and verify the patched code
    # widens the carrier so the marker writes are legal — observed via the
    # ABSENCE of the out-of-bound cast warning on an EMPTY uint8 input (no element
    # selects a reserved slot, so this isolates the input-independent carrier
    # legality the capability abstracts). On the PRE-patch tree this same probe
    # warns (carrier too narrow), so the leg genuinely discriminates the fix.
    import matplotlib as _mpl
    big = _mpl.colormaps["viridis"]      # N = 256 (the F2P colormap)
    big_n = big.N
    # The model: assignReserved is called with a carrier of range n+3 (gold), so
    # the precondition n+3 <= carrier holds and markersAdmitted is granted.
    shadow_carrier = big_n + 3
    shadow_admits = (big_n + 3) <= shadow_carrier            # the precondition
    # The patched tree: does the carrier admit the markers (no warning)?
    oracle_carrier = oracle_carrier_represents_reserved(big, big_n)
    oracle_admits = (big_n + 3) <= oracle_carrier
    if shadow_admits != oracle_admits:
        print("G-CONF FAIL: marker-write carrier-legality disagreement at N=%d: "
              "shadow carrier=%d (admits %s) vs patched-tree carrier=%d "
              "(admits %s)"
              % (big_n, shadow_carrier, shadow_admits, oracle_carrier, oracle_admits))
        return 1

    # --- the SECOND discriminating leg: the container's SIGNEDNESS -----------
    # The modeled callee's other obligation is `admitsNegative = true`. Its
    # observable is the below-range selection being live: on the real patched tree
    # a below-range element must resolve to `underSlot = n`. The negative control
    # is the same resolution in an unsigned container that ALREADY satisfies the
    # width obligation (uint16, carrier 65536 >= n + 3), where the element resolves
    # to `overSlot = n + 1` instead — so this leg measures signedness alone and is
    # not implied by the carrier-legality leg above.
    shadow_admits_negative = True                     # the modeled call's argument
    oracle_admits_negative = oracle_container_admits_negative(cmap, n)
    if shadow_admits_negative != oracle_admits_negative:
        print("G-CONF FAIL: container-signedness disagreement at N=%d: model says "
              "admitsNegative=%s but the patched tree resolved the below-range "
              "probe to %r (underSlot would be [%d])"
              % (n, shadow_admits_negative,
                 oracle_slots(np.array([-1.0]), cmap), n))
        return 1
    control = unsigned_container_control(n)
    if control == [n]:
        print("G-CONF FAIL: the unsigned-container control also resolved the "
              "below-range element to underSlot %d, so the signedness leg does not "
              "discriminate" % n)
        return 1

    # --- the THIRD leg: the OUT-OF-IMAGE region of the classified row ---------
    # `cells` is an INPUT of the modeled function and `Cell` is a wider syntax than
    # `classify`'s image: an ordinary cell may carry an index the classification
    # never produces. The forward fuzz above cannot reach that region by
    # construction, so it is compared here against the three stores run directly on
    # the index array (colors.py:730-732 verbatim). The IDENTITY reading of an
    # ordinary index (`inPalette k -> k` for every `k`) is the negative control and
    # must DISAGREE, otherwise this leg measures nothing (mapping.md §2.4).
    oi_rows = 0
    identity_disagreed = False
    for n_probe in (n, 1, 256):
        for cells in out_of_image_rows(n_probe):
            vals, bad = _cells_to_index_row(cells, n_probe)
            oracle = _store_block(vals, bad, n_probe)
            shadow = [slot_of(kind, k, n_probe) for kind, k in cells]
            if shadow != oracle:
                print("G-CONF FAIL: out-of-image disagreement at N=%d: cells=%r "
                      "shadow=%r store-block=%r" % (n_probe, cells, shadow, oracle))
                return 1
            identity = [(k if kind == "inPalette" else slot_of(kind, k, n_probe))
                        for kind, k in cells]
            if identity != oracle:
                identity_disagreed = True
            oi_rows += 1
    if not identity_disagreed:
        print("G-CONF FAIL: the identity reading of an ordinary index agreed with "
              "the store block on every out-of-image row, so the third leg does "
              "not discriminate")
        return 1

    print("G-CONF OK: R/I shadow of resolveSlots agrees with patch.diff "
          "behaviour (real patched Colormap.__call__, slot recovered from "
          "output RGBA) on %d inputs (boundary + F2P dtype matrix + int/float "
          "fuzz, seed=%d), 0 disagreements; AND the marker-write carrier-legality "
          "the capability abstracts (precondition `paletteSize+3 <= carrier`) "
          "holds on the real patched tree (N=%d uint8 input: no out-of-bound cast "
          "warning, carrier admits the reserved markers), matching the modeled "
          "`markersAdmitted` capability; AND the container SIGNEDNESS the second "
          "obligation abstracts (`admitsNegative = true`) holds on the real patched "
          "tree (a below-range element resolves to underSlot %d on the "
          "distinct-row palette), with an unsigned container that already admits "
          "every marker as the negative control (same element resolves to %r "
          "instead); AND the OUT-OF-IMAGE region of the classified row (%d rows "
          "whose ordinary cells carry indices outside the palette, compared "
          "against the three stores run directly on the index array) agrees, with "
          "the identity reading of an ordinary index as the negative control."
          % (count, SEED, big_n, n, control, oi_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
