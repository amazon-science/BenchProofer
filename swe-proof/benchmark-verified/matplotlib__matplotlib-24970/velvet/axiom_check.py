#!/usr/bin/env python3
"""Executable soundness check (G-AX) for the axiomatized assumptions of
`Solution.lean`:

    `assignReserved_contract`  /  the `markersAdmitted` capability it grants,
    `slotsOf_rowOf`            /  readback of a BUILT container,

plus the faithfulness of the element classification those two are stated over
(mapping.md §2.1: the class is taken on the POST-cast value).

The Lean spec models the reserved-marker assignment over a classified row as a
callee `assignReserved(cells, paletteSize, admitsNegative, carrier)` whose
contract has ONE load-bearing claim: it is WELL-DEFINED — it yields the
per-element resolved slots AND grants the unforgeable `markersAdmitted`
capability — ONLY on a container in which every one of its three selection steps
is live. The container is described by TWO independent extents and there is one
obligation per end:

    paletteSize + 3 <= carrier      (the reserved-index writes are in range)
    admitsNegative = true           (the below-range selection selects at all)

`carrier` abstracts how far UP the integer container reaches — the count of
non-negative values its dtype represents, `iinfo(dtype).max + 1`, so it admits
`0 .. carrier-1`. `admitsNegative` abstracts whether it reaches BELOW zero at all,
`iinfo(dtype).min < 0`. The two are independent: an unsigned container of any
width admits every reserved index while making `xa[xa < 0] = self._i_under`
(colors.py:731) select nothing. The three reserved markers are
`paletteSize`, `paletteSize+1`, `paletteSize+2`; the largest is `paletteSize+2`,
so a container admits all of them iff its representable maximum is
`>= paletteSize + 2`, i.e. (for a container admitting `0 .. carrier-1`)
`carrier - 1 >= paletteSize + 2`, i.e. `carrier >= paletteSize + 3`.

This script asserts, against REAL numpy (the dependency the change operates on),
that this precondition coincides EXACTLY with the legality of the marker writes —
the boundary at which the reserved-marker scalar store does NOT trigger numpy's
out-of-bound-integer conversion warning. matplotlib's test configuration promotes
that warning to an error, so "writes legal (no warning)" coincides with "the
operation completes". The check exits 0 iff the precondition is neither too
strong (no admitting width warns) nor too weak (every non-admitting width warns).

`check_signedness_precondition` and `check_signedness_divergence_witness` cover
the second obligation, at widths that already satisfy the first, so the two are
measured separately: on an unsigned container the produced container reads back
`overSlot` where `slotSeq` says `underSlot`, which makes the contract's readback
claim FALSE there — the obligation is required for soundness, not convenience.
The width-only model is its own negative control, since every unsigned dtype in
the sweep satisfies the width obligation and still diverges.

`check_selection_order_dominance` and `check_row_rewrite_divergence_witness` cover
what the resolved slot of an ORDINARY index is. The assignment is a SEQUENCE of
selections over one container, and the first of them, `xa[xa > self.N - 1] =
self._i_over` (colors.py:730), takes every index that is not strictly inside the
palette — including an index whose value coincides with one of the reserved markers.
So an ordinary index keeps its value only while it is strictly inside the palette,
and otherwise resolves where an out-of-range-high element resolves. The identity
reading ("an ordinary index always keeps its value") is the negative control and
must disagree. The second leg measures the consequence through the whole block, in
both directions: re-mapping a row across the collision the identity reading created
DIVERGES for the below-range and invalid ends, while the out-of-range-high end is
inert (that selection already runs first), so the shipped reading's collision classes
are exactly the rows the real block cannot tell apart.

Three further legs, one per remaining assumption:

  * `check_container_readback` — reading a BUILT container back yields exactly
    the index values it was built from (`slotsOf (rowOf vs) = vs`).
  * `check_provenance_not_readable` — the load-bearing half of the abstract
    result type: two containers with IDENTICAL readback values, one narrow and
    one wide, differ on marker-write legality. So the readback values do NOT
    determine the capability, and `markersAdmitted` may not be stated over them.
  * `check_post_cast_classification` — the class of an element is the one the
    three reserved-marker stores see, i.e. taken AFTER the index cast, including
    the unsigned values that wrap negative in the signed carrier. The pre-cast
    reading is run as a negative control and must disagree there.

Imports only the standard library + numpy. Exit 0 iff sound.
"""
from __future__ import annotations

import sys
import warnings

import numpy as np


# Integer container kinds the input may carry, with their representable maxima.
# `carrier` (the Lean model's representable-range parameter) for an unsigned
# m-bit container is 2**m; the largest representable value is carrier-1.
_DTYPES = [
    ("uint8", np.uint8),
    ("uint16", np.uint16),
    ("uint32", np.uint32),
    ("uint64", np.uint64),
    ("int8", np.int8),
    ("int16", np.int16),
    ("int32", np.int32),
    ("int64", np.int64),
]


def _carrier_of(dtype) -> int:
    """The Lean-model `carrier` (count of admitted values) of an integer dtype:
    its representable range. The container admits `0 .. carrier-1`."""
    info = np.iinfo(dtype)
    # carrier = number of representable non-negative slots = max + 1.
    return int(info.max) + 1


def _marker_store_warns(dtype, paletteSize: int) -> bool:
    """Reproduce the reserved-marker scalar store the slot-assignment step
    performs: writing the largest reserved index `paletteSize + 2` into a
    container of the given integer dtype, via an all-False masked assignment on
    an F2P-shaped (single in-range value, no element selected) array. Returns
    True iff numpy emits the out-of-bound-integer conversion warning — i.e. the
    container does NOT admit the marker."""
    marker = paletteSize + 2  # invalidSlot: the largest reserved index written
    # F2P-shaped carrier: one ordinary in-range element, value 0; no mask hit.
    xa = np.array([0], dtype=dtype)
    mask = np.array([False])
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # promote (as matplotlib's conftest does)
        try:
            # The scalar RHS cast is evaluated regardless of the empty mask —
            # this is the operation the slot-assignment step performs.
            xa[mask] = marker
        except (DeprecationWarning, OverflowError, RuntimeWarning):
            return True
        except Exception:
            # Any conversion failure also means the marker is not admitted.
            return True
    return False


def check_legality_precondition() -> None:
    """The contract precondition `paletteSize + 3 <= carrier` must coincide
    EXACTLY with the marker writes completing without a warning, across dtypes
    and palette sizes sweeping the admit/not-admit boundary."""
    mismatches = []
    for name, dtype in _DTYPES:
        carrier = _carrier_of(dtype)
        # Sweep paletteSize across the boundary carrier = paletteSize + 3, i.e.
        # paletteSize around carrier - 3, plus general samples.
        boundary = carrier - 3
        samples = set()
        for d in range(-4, 5):
            p = boundary + d
            if p >= 1:
                samples.add(p)
        samples.update(p for p in (1, 2, 4, 8, 200, 250, 254, 255, 256, 257) if p >= 1)
        for paletteSize in sorted(samples):
            admits_model = (paletteSize + 3) <= carrier  # the Lean precondition
            warns = _marker_store_warns(dtype, paletteSize)
            completes_real = not warns  # legal store <=> no promoted warning
            if admits_model != completes_real:
                mismatches.append(
                    (name, carrier, paletteSize, admits_model, completes_real)
                )
    if mismatches:
        print("UNSOUND: precondition does not coincide with marker-write legality:")
        for m in mismatches[:20]:
            print("  dtype=%s carrier=%d paletteSize=%d model_admits=%s real_completes=%s"
                  % m)
        sys.exit(1)
    print("OK: precondition `paletteSize+3 <= carrier` coincides EXACTLY with "
          "reserved-marker-write legality across %s around the boundary."
          % "/".join(name for name, _ in _DTYPES))


def check_f2p_witness() -> None:
    """Pin the exact F2P case: a uint8 container with paletteSize = 256
    (carrier = 256 < paletteSize + 3 = 259) does NOT admit the markers — the
    marker store warns — while a widened container (carrier >= 259) admits them
    (no warning). Confirms the precondition discriminates the F2P input."""
    name, dtype = "uint8", np.uint8
    paletteSize = 256
    narrow_carrier = _carrier_of(dtype)  # 256
    assert narrow_carrier == 256, narrow_carrier
    assert (paletteSize + 3) > narrow_carrier, "uint8 should NOT admit markers"
    if not _marker_store_warns(dtype, paletteSize):
        print("UNSOUND: F2P-shaped uint8 marker store did not warn (expected it to)")
        sys.exit(1)
    # A widened container (signed int64) admits the markers: no warning.
    wide = np.array([0], dtype=np.int64)
    mask = np.array([False])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            wide[mask] = paletteSize + 2
        except Exception as e:  # pragma: no cover
            print("UNSOUND: widened container unexpectedly failed:", e)
            sys.exit(1)
    print("OK: F2P witness — uint8 (carrier 256 < 259) warns on marker store; "
          "widened carrier (>= 259) does not. Precondition pins the F2P.")


def check_container_readback() -> None:
    """`slotsOf (rowOf vs) = vs`: a container BUILT over index values reads back
    exactly those values. `rowOf` is the ordinary array construction; `slotsOf` is
    the read the palette lookup performs."""
    bad = []
    rows = [
        [],
        [0],
        [0, 1, 2],
        [6, 7, 8],                  # the three reserved slots at paletteSize = 6
        [256, 257, 258],            # and at the default paletteSize = 256
        [5, 0, 5, 259, 1],
    ]
    for vs in rows:
        for name, dtype in _DTYPES + [("int", int)]:
            try:
                info = np.iinfo(dtype)
            except ValueError:      # pragma: no cover — `int` maps to a dtype
                info = np.iinfo(np.int64)
            if any(v > int(info.max) or v < int(info.min) for v in vs):
                continue            # not representable: not a container of these
            built = np.array(vs, dtype=dtype)          # rowOf vs
            read = [int(v) for v in built.tolist()]    # slotsOf (rowOf vs)
            if read != vs:
                bad.append((name, vs, read))
    if bad:
        print("UNSOUND: readback of a built container is not the identity:")
        for name, vs, read in bad[:20]:
            print("  dtype=%s built_from=%r read_back=%r" % (name, vs, read))
        sys.exit(1)
    print("OK: `slotsOf (rowOf vs) = vs` — a built container reads back exactly "
          "the index values it was built from, across %d dtypes."
          % (len(_DTYPES) + 1))


def check_provenance_not_readable() -> None:
    """The reason the modeled result is an abstract CONTAINER and not its index
    values: two containers whose readback values are IDENTICAL can differ on
    whether the reserved-marker stores are legal in them. So no predicate over
    the readback values can express the completing-assignment effect, and
    `markersAdmitted` is a predicate on the container instead.

    The two containers are exactly the ones this function chooses between: the
    input's own narrow array, and the wide array the index cast produces from it.
    """
    mismatches = []
    for paletteSize in (254, 256, 300, 1000):
        narrow = np.array([0], dtype=np.uint8)     # the input's own container
        wide = narrow.astype(int)                  # what the index cast produces
        if [int(v) for v in narrow.tolist()] != [int(v) for v in wide.tolist()]:
            print("UNSOUND: the cast changed the index values, so the two "
                  "containers are not readback-identical")
            sys.exit(1)
        narrow_legal = not _marker_store_warns(narrow.dtype, paletteSize)
        wide_legal = not _marker_store_warns(wide.dtype, paletteSize)
        # uint8 admits 0..255, so from paletteSize = 254 up the largest reserved
        # index (paletteSize + 2) does not fit it, while the signed `int` the cast
        # produces admits it at every paletteSize used here.
        if narrow_legal or not wide_legal:
            mismatches.append((paletteSize, narrow_legal, wide_legal))
    if mismatches:
        print("UNSOUND: readback-identical containers did not differ on "
              "marker-write legality, so the capability WOULD be a function of "
              "the index values:")
        for p, nl, wl in mismatches:
            print("  paletteSize=%d narrow_legal=%s wide_legal=%s" % (p, nl, wl))
        sys.exit(1)
    print("OK: readback-identical containers (the input's own uint8 array and "
          "the cast's `int` array) differ on reserved-marker-write legality at "
          "paletteSize 254/256/300/1000 — the capability is NOT a function of "
          "the index values, which is why the modeled result is a container.")


def _reference_stores(values, dtype, paletteSize):
    """The reference tree's index cast followed by the two range stores, in numpy
    alone: `xa = xa.astype(int)`, then `xa[xa > N-1] = _i_over`, then
    `xa[xa < 0] = _i_under` (the bad-mask store is not exercised here — no
    element is masked; G-CONF covers it against the real colormap)."""
    xa = np.array(values, dtype=dtype)
    with np.errstate(invalid="ignore"):
        xa = xa.astype(int)
    xa[xa > paletteSize - 1] = paletteSize + 1     # _i_over  = overSlot
    xa[xa < 0] = paletteSize                       # _i_under = underSlot
    return [int(v) for v in xa.tolist()]


def _model_slots(values, dtype, paletteSize, post_cast):
    """`slotSeq paletteSize (classify each element)`, with the class taken on the
    POST-cast value (`post_cast=True`, mapping.md §2.1) or on the raw input value
    (`post_cast=False`, the negative control)."""
    xa = np.array(values, dtype=dtype)
    if post_cast:
        with np.errstate(invalid="ignore"):
            xa = xa.astype(int)
    out = []
    for v in xa.tolist():
        v = int(v)
        if v < 0:
            out.append(paletteSize)                # underSlot
        elif v > paletteSize - 1:
            out.append(paletteSize + 1)            # overSlot
        else:
            out.append(v)                          # inPalette v
    return out


def check_post_cast_classification() -> None:
    """mapping.md §2.1: the class is the one the three stores see, i.e. taken
    AFTER the index cast. Asserts the modeled slots equal the real stores' result
    across integer dtypes, and requires the PRE-cast reading to DISAGREE
    somewhere (else this check would be decorative)."""
    mismatches = []
    control_disagreed = []
    for paletteSize in (6, 256):
        for name, dtype in _DTYPES:
            info = np.iinfo(dtype)
            vals = sorted({int(info.min), int(info.min) + 1, 0, 1,
                           paletteSize - 1, paletteSize, paletteSize + 1,
                           int(info.max) - 1, int(info.max)})
            vals = [v for v in vals if int(info.min) <= v <= int(info.max)]
            if int(info.max) >= 2 ** 63:
                vals += [2 ** 63 - 2, 2 ** 63 - 1, 2 ** 63, 2 ** 63 + 1]
                vals = sorted(set(v for v in vals if v <= int(info.max)))
            real = _reference_stores(vals, dtype, paletteSize)
            modeled = _model_slots(vals, dtype, paletteSize, post_cast=True)
            if modeled != real:
                mismatches.append((name, paletteSize, vals, modeled, real))
            if _model_slots(vals, dtype, paletteSize, post_cast=False) != real:
                control_disagreed.append(name)
    if mismatches:
        print("UNSOUND: post-cast classification does not match the real stores:")
        for name, p, vals, modeled, real in mismatches[:10]:
            print("  dtype=%s paletteSize=%d values=%r modeled=%r real=%r"
                  % (name, p, vals, modeled, real))
        sys.exit(1)
    if not control_disagreed:
        print("UNSOUND: the PRE-cast reading agreed everywhere, so this check "
              "does not exercise the region it exists for (an unsigned value "
              "that wraps negative in the signed carrier)")
        sys.exit(1)
    # The wrapping region itself, spelled out so the record shows it was reached.
    probe = [2 ** 63 - 1, 2 ** 63, 2 ** 64 - 1]
    real = _reference_stores(probe, np.uint64, 6)
    if real != [7, 6, 6]:
        print("UNSOUND: uint64 signed-threshold probe gave %r, expected "
              "[overSlot, underSlot, underSlot] = [7, 6, 6] at paletteSize 6"
              % (real,))
        sys.exit(1)
    print("OK: the class taken on the POST-cast value reproduces the real "
          "reserved-marker stores across %d integer dtypes at paletteSize 6 and "
          "256, including uint64 at the signed threshold (2**63-1 -> overSlot 7, "
          "2**63 and 2**64-1 -> underSlot 6); the PRE-cast reading disagrees on "
          "%s, so the check is load-bearing."
          % (len(_DTYPES), "/".join(sorted(set(control_disagreed)))))


def _admits_negative_of(dtype) -> bool:
    """The Lean-model `admitsNegative` of an integer dtype: whether the container
    represents values below zero at all. True for every signed dtype, False for
    every unsigned one (mapping.md §2, §2.3)."""
    return int(np.iinfo(dtype).min) < 0


def _stores_in_container(values, dtype, paletteSize):
    """The reserved-marker assignment carried out IN a container of `dtype` — i.e.
    `assignReserved` on a container whose two extents are `_carrier_of(dtype)` and
    `_admits_negative_of(dtype)`. The pre-store values arrive as the post-clamp
    floats (`-1` for anything below the range), are placed in the container, and
    the two range stores then run in it."""
    xa = np.array(values, dtype=float)
    with np.errstate(invalid="ignore"):
        xa = xa.astype(dtype)
    xa[xa > paletteSize - 1] = paletteSize + 1      # _i_over  = overSlot
    xa[xa < 0] = paletteSize                        # _i_under = underSlot
    return [int(v) for v in xa.tolist()]


def _reference_slot_seq(values, paletteSize):
    """`slotSeq paletteSize cells` — the reference resolution, i.e. the same two
    stores in the container the reference tree's `astype(int)` produces."""
    return _stores_in_container(values, int, paletteSize)


def check_signedness_precondition() -> None:
    """The contract's OTHER obligation, `admitsNegative = true`, must coincide
    EXACTLY with the produced container reading back `slotSeq` on a row that
    contains a below-range element.

    The reserved-marker assignment is three SELECTIONS, and they do not all look at
    the same end of the container: `xa[xa < 0] = self._i_under` (colors.py:731) is a
    predicate on NEGATIVE values. In a container that represents nothing below zero
    it selects nothing, so a below-range element keeps the `overSlot` the preceding
    store wrote (in such a container a below-range element IS a large positive one).
    The readback then differs from `slotSeq`, which means the contract's readback
    claim would be UNSOUND on such a container — the obligation is required for
    soundness, not for convenience.

    Restricted to containers that satisfy the OTHER obligation
    (`paletteSize + 3 <= carrier`), so the two are separated: what is measured here
    is signedness alone, at widths that already admit every reserved index. The
    width-only model is thereby its own negative control — every unsigned dtype
    below passes the width obligation and still diverges."""
    rows = {6: [-1, 0, 2, 5, 6, 11], 256: [-1, 0, 2, 179, 255, 256, 300]}
    mismatches = []
    signed_seen = unsigned_seen = 0
    for paletteSize, values in rows.items():
        reference = _reference_slot_seq(values, paletteSize)
        for name, dtype in _DTYPES:
            carrier = _carrier_of(dtype)
            if (paletteSize + 3) > carrier:
                continue                    # excluded by the width obligation
            model_ok = _admits_negative_of(dtype)      # the Lean obligation
            real = _stores_in_container(values, dtype, paletteSize)
            real_ok = (real == reference)               # readback == slotSeq
            if model_ok:
                signed_seen += 1
            else:
                unsigned_seen += 1
            if model_ok != real_ok:
                mismatches.append((name, carrier, paletteSize, model_ok, real,
                                   reference))
    if mismatches:
        print("UNSOUND: `admitsNegative = true` does not coincide with the produced "
              "container reading back slotSeq:")
        for name, carrier, p, m, real, ref in mismatches[:20]:
            print("  dtype=%s carrier=%d paletteSize=%d model_admits_negative=%s "
                  "readback=%r slotSeq=%r" % (name, carrier, p, m, real, ref))
        sys.exit(1)
    if not signed_seen or not unsigned_seen:
        print("UNSOUND: the sweep did not exercise both signedness kinds at an "
              "admitting width (signed=%d unsigned=%d), so this check would be "
              "decorative" % (signed_seen, unsigned_seen))
        sys.exit(1)
    print("OK: `admitsNegative = true` coincides EXACTLY with the produced "
          "container reading back slotSeq on rows containing a below-range element "
          "— %d signed container/paletteSize pairs agree and %d unsigned ones "
          "DIVERGE, all of them at widths that already satisfy "
          "`paletteSize + 3 <= carrier`. So the width obligation alone is NOT "
          "sufficient and the signedness obligation is neither too strong nor too "
          "weak." % (signed_seen, unsigned_seen))


def _model_slot_of_index(k: int, paletteSize: int, dominates: bool) -> int:
    """`slotOf paletteSize (.inPalette k)` under the two candidate readings of what
    an ordinary index resolves to. `dominates=True` is the shipped reading — the
    FIRST selection takes every index that is not strictly inside the palette, so
    such an index resolves to `overSlot`. `dominates=False` is the identity reading
    ("an ordinary index always keeps its value"), kept as the negative control."""
    if dominates:
        return k if k < paletteSize else paletteSize + 1
    return k


def check_selection_order_dominance() -> None:
    """`slotOf` on an ordinary index: the FIRST selection dominates.

    The reserved-marker assignment is three successive stores over ONE container,
    not a case analysis over disjoint classes evaluated independently. The first of
    them is `xa[xa > self.N - 1] = self._i_over` (colors.py:730), whose predicate
    `> N-1` also holds of the three reserved index VALUES themselves (`N`, `N+1`,
    `N+2`). So an element that arrives at the assignment carrying such an index does
    NOT keep it: the first store takes it and writes `overSlot` over it, and no later
    store takes it back — `overSlot` is not negative, so the below-range store passes
    over it, and the element is not masked, so the invalid store passes over it too.

    Asserts the shipped reading reproduces the real stores on exactly those values,
    and requires the identity reading to DISAGREE there, so the leg is load-bearing
    rather than decorative."""
    mismatches = []
    control_disagreed = []
    for paletteSize in (1, 6, 256):
        vals = sorted({0, 1, paletteSize - 1, paletteSize, paletteSize + 1,
                       paletteSize + 2, paletteSize + 7, 2 * paletteSize})
        vals = [v for v in vals if v >= 0]
        real = _reference_stores(vals, int, paletteSize)
        shipped = [_model_slot_of_index(v, paletteSize, True) for v in vals]
        control = [_model_slot_of_index(v, paletteSize, False) for v in vals]
        if shipped != real:
            mismatches.append((paletteSize, vals, shipped, real))
        if control != real:
            control_disagreed.append(paletteSize)
    if mismatches:
        print("UNSOUND: the modeled slot of an ordinary index does not match the "
              "real selections:")
        for p, vals, shipped, real in mismatches:
            print("  paletteSize=%d indices=%r modeled=%r real=%r"
                  % (p, vals, shipped, real))
        sys.exit(1)
    if not control_disagreed:
        print("UNSOUND: the identity reading agreed everywhere, so this check does "
              "not exercise the region it exists for (an ordinary index whose value "
              "is not strictly inside the palette)")
        sys.exit(1)
    # The collision region itself, spelled out so the record shows it was reached.
    probe = _reference_stores([256, 257, 258], int, 256)
    if probe != [257, 257, 257]:
        print("UNSOUND: the reserved-valued index probe gave %r, expected all three "
              "to reach overSlot 257 at paletteSize 256" % (probe,))
        sys.exit(1)
    print("OK: the first selection dominates — an ordinary index at or above "
          "`paletteSize` resolves to overSlot, matching the real selections at "
          "paletteSize 1, 6 and 256; at paletteSize 256 the three reserved-valued "
          "indices 256/257/258 all resolve to overSlot 257, and the identity "
          "reading disagrees at paletteSize %s, so the check is load-bearing."
          % ("/".join(str(p) for p in control_disagreed)))


def _full_reference_pipeline(X, paletteSize, cast_dtype):
    """The whole index-resolution block of the reference tree in numpy alone
    (colors.py:709-732), with the cast target as a parameter: the bad mask, the
    float scale and clamps, the (hoisted, unconditional) cast into a container of
    `cast_dtype`, then the three reserved-marker stores. `cast_dtype = int` is the
    reference tree; any unsigned dtype is the container whose below-range selection
    is dead."""
    xa = np.array(X, dtype=float)
    mask_bad = np.isnan(xa)
    xa = xa * paletteSize
    with np.errstate(invalid="ignore"):
        xa[xa < 0] = -1
        xa[xa == paletteSize] = paletteSize - 1
        np.clip(xa, -1, paletteSize, out=xa)
        xa = xa.astype(cast_dtype)
    xa[xa > paletteSize - 1] = paletteSize + 1      # _i_over
    xa[xa < 0] = paletteSize                        # _i_under
    xa[mask_bad] = paletteSize + 2                  # _i_bad
    return [int(v) for v in xa.tolist()]


def check_signedness_divergence_witness() -> None:
    """Pin the concrete divergence mapping.md §2.3 tabulates, through the WHOLE
    resolution block rather than the stores alone: at the default palette size the
    signed container the reference tree casts to and an unsigned container that
    admits every reserved index resolve the SAME row differently, and only on its
    below-range elements."""
    paletteSize = 256
    X = [-np.inf, -1.0, 0.0, np.nan, 0.7, 2.0, np.inf]
    signed = _full_reference_pipeline(X, paletteSize, int)
    unsigned = _full_reference_pipeline(X, paletteSize, np.uint16)
    expect_signed = [256, 256, 0, 258, 179, 257, 257]
    expect_unsigned = [257, 257, 0, 258, 179, 257, 257]
    if signed != expect_signed:
        print("UNSOUND: the reference (signed `int`) container resolved %r, "
              "expected %r" % (signed, expect_signed))
        sys.exit(1)
    if unsigned != expect_unsigned:
        print("UNSOUND: the unsigned (uint16) container resolved %r, expected %r"
              % (unsigned, expect_unsigned))
        sys.exit(1)
    if (paletteSize + 3) > _carrier_of(np.uint16):
        print("UNSOUND: uint16 was expected to satisfy the width obligation")
        sys.exit(1)
    differing = [i for i, (a, b) in enumerate(zip(signed, unsigned)) if a != b]
    if differing != [0, 1]:
        print("UNSOUND: expected the divergence to be exactly the below-range "
              "elements (positions 0 and 1), got %r" % (differing,))
        sys.exit(1)
    print("OK: signedness witness — at paletteSize 256 the signed container "
          "resolves %r and the uint16 container (carrier 65536, which SATISFIES "
          "`paletteSize + 3 <= carrier`) resolves %r; they differ at exactly the "
          "two below-range elements, which reach overSlot 257 instead of "
          "underSlot 256 because the below-range store is dead there."
          % (signed, unsigned))


def _rewritten_pipeline(X, paletteSize, rewrite):
    """The same whole block as `_full_reference_pipeline` at `cast_dtype = int`, but
    with the per-element indices REWRITTEN in the container just before the three
    selections run. This is the Python reading of a modeled implementation that
    re-maps the classified row across a resolved-slot collision before the gated
    call: the row it hands the assignment is not the row the value examination
    produced. `rewrite` receives and returns `(xa, mask_bad)`."""
    xa = np.array(X, dtype=float)
    mask_bad = np.isnan(xa)
    xa = xa * paletteSize
    with np.errstate(invalid="ignore"):
        xa[xa < 0] = -1
        xa[xa == paletteSize] = paletteSize - 1
        np.clip(xa, -1, paletteSize, out=xa)
        xa = xa.astype(int)
    xa, mask_bad = rewrite(xa, mask_bad, paletteSize)
    xa[xa > paletteSize - 1] = paletteSize + 1      # _i_over
    xa[xa < 0] = paletteSize                        # _i_under
    xa[mask_bad] = paletteSize + 2                  # _i_bad
    return [int(v) for v in xa.tolist()]


def _rewrite_below_to_under_index(xa, mask_bad, paletteSize):
    """below-range element |-> ordinary index `underSlot paletteSize`."""
    xa[xa < 0] = paletteSize
    return xa, mask_bad


def _rewrite_invalid_to_invalid_index(xa, mask_bad, paletteSize):
    """invalid element |-> ordinary index `invalidSlot paletteSize`, no longer
    masked (the row it hands on carries the marker as a value instead)."""
    xa[mask_bad] = paletteSize + 2
    return xa, np.zeros_like(mask_bad)


def _rewrite_above_to_over_index(xa, mask_bad, paletteSize):
    """out-of-range-high element |-> ordinary index `overSlot paletteSize`."""
    xa[xa > paletteSize - 1] = paletteSize + 1
    return xa, mask_bad


def check_row_rewrite_divergence_witness() -> None:
    """Why the resolved-slot sequence has to distinguish these rows at all.

    A modeled implementation may hand the assignment a row it re-mapped itself. The
    three rewrites below all leave the modeled resolved-slot sequence UNCHANGED under
    the identity reading of an ordinary index, so under that reading the model cannot
    see them. Measured here, through the whole block, they split into two kinds:

      * below-range |-> ordinary index `N`, and invalid |-> ordinary index `N+2`,
        DIVERGE from the reference resolution — the first selection takes the
        rewritten element and stores `overSlot` over it before the selection that was
        supposed to take it ever runs. These are exactly the rows the shipped reading
        of `slotOf` keeps apart.
      * out-of-range-high |-> ordinary index `N+1` AGREES everywhere — that selection
        already runs first, so the rewrite is inert. The shipped reading identifies
        this row with the reference row, which is why it is not over-strong.

    So the shipped reading's collision classes are exactly the rows the real block
    cannot tell apart, measured, in both directions."""
    paletteSize = 256
    X = [-np.inf, -1.0, 0.0, np.nan, 0.7, 2.0, np.inf]
    reference = _full_reference_pipeline(X, paletteSize, int)
    cases = [
        ("below-range |-> ordinary index %d" % paletteSize,
         _rewrite_below_to_under_index, False),
        ("invalid |-> ordinary index %d" % (paletteSize + 2),
         _rewrite_invalid_to_invalid_index, False),
        ("out-of-range-high |-> ordinary index %d" % (paletteSize + 1),
         _rewrite_above_to_over_index, True),
    ]
    results = []
    for label, rewrite, expect_agree in cases:
        got = _rewritten_pipeline(X, paletteSize, rewrite)
        agree = got == reference
        results.append((label, got, agree))
        if agree != expect_agree:
            print("UNSOUND: the rewrite `%s` was expected to %s the reference "
                  "resolution %r, but resolved %r"
                  % (label, "agree with" if expect_agree else "diverge from",
                     reference, got))
            sys.exit(1)
    print("OK: row-rewrite witness at paletteSize %d — the reference row resolves "
          "%r; %s; %s; %s. The two divergent rewrites are the ones the shipped "
          "reading of `slotOf` separates, and the inert one is the one it "
          "identifies."
          % (paletteSize, reference,
             "`%s` -> %r (diverges)" % (results[0][0], results[0][1]),
             "`%s` -> %r (diverges)" % (results[1][0], results[1][1]),
             "`%s` -> %r (agrees)" % (results[2][0], results[2][1])))


def check_carrier_refinement_scope() -> None:
    """How far the two container obligations pin the container down — measured in
    BOTH directions, because an earlier revision of mapping.md over-claimed here and
    an independent audit measured the over-claim.

    The claim that was too strong: "an admitting `carrier` refines to the platform
    signed `int` and to nothing else." What is actually true, and all that is:

      * a NARROWER signed container that satisfies both obligations — int16 at
        paletteSize 256 — agrees with the platform `int` on every element the FLOAT
        path can deliver, because that path clamps and clips into `[-1, N]` before
        the cast. So on the graded inputs it is INDISTINGUISHABLE, and the modeled
        call does not, and need not, exclude it. Measured below.
      * it diverges only on an INTEGER-dtype input, which skips the scale/clamp/clip
        and reaches the cast with its own magnitude. Measured below as well.

    So the two obligations pin exactly what they say — the two extents the three
    selections read — and the choice of the platform `int` is the R-leg's binding of
    the container the change actually introduces (mapping.md §2), not an extra
    discriminating obligation. This leg exists to keep that distinction measured
    rather than asserted."""
    paletteSize = 256
    narrow_name, narrow = "int16", np.int16
    if not _admits_negative_of(narrow):
        print("UNSOUND: %s was expected to admit negative values" % narrow_name)
        sys.exit(1)
    if (paletteSize + 3) > _carrier_of(narrow):
        print("UNSOUND: %s was expected to satisfy the width obligation at "
              "paletteSize %d" % (narrow_name, paletteSize))
        sys.exit(1)
    # (i) On the float path the two containers are indistinguishable.
    X = [-np.inf, -1.0, -0.3, 0.0, np.nan, 0.7, 1.0, 2.0, np.inf]
    ref_float = _full_reference_pipeline(X, paletteSize, int)
    narrow_float = _full_reference_pipeline(X, paletteSize, narrow)
    if ref_float != narrow_float:
        print("UNSOUND: %s was expected to agree with the platform `int` on the "
              "float path (which clamps into [-1, N] before the cast), but "
              "resolved %r where the platform `int` resolved %r"
              % (narrow_name, narrow_float, ref_float))
        sys.exit(1)
    # (ii) An INTEGER-dtype input is not clipped upstream, so it reaches the cast
    # with its own magnitude and the two containers do separate there.
    values = [100000, 40000, 32768]
    reference = _reference_slot_seq(values, paletteSize)
    narrowed = _stores_in_container(values, narrow, paletteSize)
    if reference == narrowed:
        print("UNSOUND: %s reproduced the platform-`int` resolution even on %r, so "
              "the two containers would be indistinguishable everywhere and §2's "
              "binding of the container could not be measured at all"
              % (narrow_name, values))
        sys.exit(1)
    print("OK: refinement scope — %s satisfies BOTH modeled obligations at "
          "paletteSize %d (carrier %d >= %d, admits negatives) and resolves the "
          "float-path row %r exactly as the platform `int` does, so the obligations "
          "correctly do NOT exclude it and the graded inputs cannot separate the two; "
          "the two containers separate only on an integer-dtype input that skips the "
          "upstream clamp (%r -> %r vs %r). The obligations pin the two extents the "
          "selections read, and nothing more."
          % (narrow_name, paletteSize, _carrier_of(narrow), paletteSize + 3,
             ref_float, values, narrowed, reference))


def main() -> None:
    check_legality_precondition()
    check_signedness_precondition()
    check_signedness_divergence_witness()
    check_selection_order_dominance()
    check_row_rewrite_divergence_witness()
    check_carrier_refinement_scope()
    check_f2p_witness()
    check_container_readback()
    check_provenance_not_readable()
    check_post_cast_classification()
    print("axiom_check: ALL SOUND (exit 0)")
    sys.exit(0)


if __name__ == "__main__":
    main()
