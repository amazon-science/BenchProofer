#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-8872.

The bundle models the two dtype-coercion decisions in `Quantity.__new__`
(mapping.md): on the general construction path and on the fast reuse path, decide
the *effective element dtype* the array is stored under when no explicit dtype is
requested.

Post-patch rule (the gold edit, refinement.md):
    general path:  promote-to-float iff  value.dtype.kind in 'iuO'
    reuse path:    promote-to-float iff  value.dtype.kind in 'iu'
where "promote-to-float" means the stored dtype becomes numpy.dtype(float)
(float64), otherwise it stays the input dtype.

ORACLE = the post-patch Python expressions themselves (`kind in 'iuO'` /
`kind in 'iu'`), applied to real numpy dtype observations where possible.
SHADOW = the op-for-op transliteration of `implementation_resolveDtype` /
`implementation_reuseDtype` (Solution.lean impl region), driven by the modeled
`DType` triple from mapping.md (kind, canHoldSingle, structured).

This is a pure R/I check (no axioms), so conf_skip = false.

Two input populations:
  (1) every real numpy scalar dtype + a structured dtype — grounds the model in
      actual `numpy.dtype.kind` / `numpy.can_cast(float32, dt)` observations;
  (2) ≥10^5 fuzzed synthetic `(kind, canHoldSingle, structured)` triples drawn
      from the real category codes, so the decision is exercised on every branch.

stdlib + numpy only. Pinned seed: 8872 (also in mapping.md).
"""
import random
import sys

SEED = 8872
N_FUZZ = 120_000

FLOAT_DTYPE = ("f", True, False)  # numpy.dtype(float) = float64


# --- ORACLE: faithful replica of the POST-PATCH decision ----------------------
def oracle_general(kind, can_hold_single, structured):
    return FLOAT_DTYPE if kind in "iuO" else (kind, can_hold_single, structured)


def oracle_reuse(kind, can_hold_single, structured):
    return FLOAT_DTYPE if kind in "iu" else (kind, can_hold_single, structured)


# --- SHADOW of the Lean impl regions (the R leg) ------------------------------
# implementation_resolveDtype: promoteGeneral dt = kind in {i,u,O}; if so float.
def shadow_general(kind, can_hold_single, structured):
    result = (kind, can_hold_single, structured)
    if kind == "i" or kind == "u" or kind == "O":
        result = FLOAT_DTYPE
    return result


# implementation_reuseDtype: promoteReuse dt = kind in {i,u}; if so float.
def shadow_reuse(kind, can_hold_single, structured):
    result = (kind, can_hold_single, structured)
    if kind == "i" or kind == "u":
        result = FLOAT_DTYPE
    return result


def real_numpy_dtypes():
    """Real numpy dtypes -> modeled (kind, canHoldSingle, structured) triples."""
    import numpy as np
    triples = []
    names = [
        np.float16, np.float32, np.float64,
        np.int8, np.int16, np.int32, np.int64,
        np.uint8, np.uint16, np.uint32, np.uint64,
        np.bool_, np.complex64, np.complex128,
        np.dtype("O"), np.dtype("S4"), np.dtype("U4"),
    ]
    if hasattr(np, "float128"):
        names.append(np.float128)
    for t in names:
        dt = np.dtype(t)
        triples.append((dt.kind, bool(np.can_cast(np.float32, dt)), bool(dt.fields)))
    # a structured/record dtype
    sdt = np.dtype([("a", np.float64), ("b", np.int32)])
    triples.append((sdt.kind, bool(np.can_cast(np.float32, sdt)), bool(sdt.fields)))
    return triples


def main():
    rng = random.Random(SEED)
    mismatches = 0
    checked = 0

    # population (1): real numpy dtype observations
    try:
        grounded = real_numpy_dtypes()
    except Exception as e:  # pragma: no cover
        print(f"status=error numpy unavailable: {e}")
        return 2
    for (kind, chs, st) in grounded:
        for orc, shd, name in (
            (oracle_general, shadow_general, "general"),
            (oracle_reuse, shadow_reuse, "reuse"),
        ):
            checked += 1
            if orc(kind, chs, st) != shd(kind, chs, st):
                mismatches += 1
                if mismatches <= 10:
                    print(f"MISMATCH[{name}] real dtype kind={kind!r} "
                          f"canHoldSingle={chs} structured={st}: "
                          f"oracle={orc(kind, chs, st)} shadow={shd(kind, chs, st)}")

    # population (2): fuzz synthetic triples over real category codes
    KINDS = list("iufbcOVSU")
    for _ in range(N_FUZZ):
        kind = rng.choice(KINDS)
        chs = rng.random() < 0.5
        st = rng.random() < 0.5
        for orc, shd, name in (
            (oracle_general, shadow_general, "general"),
            (oracle_reuse, shadow_reuse, "reuse"),
        ):
            checked += 1
            if orc(kind, chs, st) != shd(kind, chs, st):
                mismatches += 1
                if mismatches <= 10:
                    print(f"MISMATCH[{name}] kind={kind!r} "
                          f"canHoldSingle={chs} structured={st}: "
                          f"oracle={orc(kind, chs, st)} shadow={shd(kind, chs, st)}")

    if mismatches:
        print(f"status=fail checked={checked} mismatches={mismatches}")
        return 1
    print(f"status=pass checked={checked} mismatches=0 seed={SEED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
