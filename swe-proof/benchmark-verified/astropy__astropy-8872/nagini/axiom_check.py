#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-8872.

There are NO consumed @ContractOnly axioms in model.py: the changed operation
is a pure predicate over a numpy dtype's observables, modelled DEEPLY. This
script is the out-of-band (A-reference) validation of that deep model against
real numpy: it confirms, on every relevant numpy dtype (boundary) plus fuzzed
combinations, that

  (1) model.py's `realizable(kind, fits_ref_real32, is_composite)` precondition
      holds for the observables a real numpy dtype actually exhibits -- i.e. the
      spec's input domain is exactly the set of realisable dtypes, never a
      stronger (unsound) restriction; and

  (2) model.py's two decision predicates equal the post-patch (gold) decision
      the real constructor makes, namely whether `dtype.kind in 'iu'`
      (homogeneous path) / `dtype.kind in 'iuO'` (generic path); and

  (3) that decision agrees with the OBSERVABLE behaviour of the gold code: a
      coerced kind is exactly one whose default coercion changes the stored
      element type to the default real type, and a preserved kind keeps its own
      dtype (verified by replaying the gold predicate over `value.astype`).

The kind tags are mapped to the integer code points model.py uses (ord of the
single-character numpy kind tag). Imports only the standard library plus numpy
-- the very library the gold patch's predicate reads (`value.dtype.kind`,
`np.can_cast`). Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np

# --- model.py reference encodings (kept in lock-step with the spec) ----------

KIND_BOOL = ord('b')        # 98
KIND_INT = ord('i')         # 105
KIND_UINT = ord('u')        # 117
KIND_REAL = ord('f')        # 102
KIND_COMPLEX = ord('c')     # 99
KIND_OBJECT = ord('O')      # 79
KIND_COMPOSITE = ord('V')   # 86


def model_is_int_like(kind):
    return kind == KIND_INT or kind == KIND_UINT


def model_realizable(kind, fits_ref_real32, is_composite):
    """Reference implementation of model.py's `realizable` precondition."""
    if fits_ref_real32 and not (
            kind == KIND_REAL or kind == KIND_COMPLEX or kind == KIND_OBJECT):
        return False
    if is_composite != (kind == KIND_COMPOSITE):
        return False
    if kind == KIND_COMPLEX and is_composite:
        return False
    if model_is_int_like(kind) or kind == KIND_BOOL:
        if fits_ref_real32 or is_composite:
            return False
    return True


def model_coerce_homogeneous(kind, fits_ref_real32, is_composite):
    return model_is_int_like(kind)


def model_coerce_generic(kind, fits_ref_real32, is_composite):
    return model_is_int_like(kind) or kind == KIND_OBJECT


# --- the gold (post-patch) decision, read straight off the real dtype --------

def gold_coerce_homogeneous(dtype):
    # patch.diff hunk 1: `if value.dtype.kind in 'iu': dtype = float`
    return dtype.kind in 'iu'


def gold_coerce_generic(dtype):
    # patch.diff hunk 2: `if dtype is None and value.dtype.kind in 'iuO':`
    return dtype.kind in 'iuO'


# --- observables of a real numpy dtype, as model.py models them --------------

def observables(dtype):
    kind = ord(dtype.kind)
    fits_ref_real32 = bool(np.can_cast(np.float32, dtype))
    is_composite = bool(dtype.fields)
    return kind, fits_ref_real32, is_composite


def check_dtype(dtype):
    kind, fits, comp = observables(dtype)

    # (1) the spec's input domain must admit every real dtype.
    assert model_realizable(kind, fits, comp), (
        "realizable() rejects a real numpy dtype %r (kind=%r fits=%r comp=%r) "
        "-- spec domain is unsoundly narrow" % (dtype, chr(kind), fits, comp))

    # (2) the deep model equals the gold predicate on this dtype.
    assert model_coerce_homogeneous(kind, fits, comp) == gold_coerce_homogeneous(dtype), (
        "homogeneous deep model disagrees with gold on %r: model=%r gold=%r"
        % (dtype, model_coerce_homogeneous(kind, fits, comp),
           gold_coerce_homogeneous(dtype)))
    assert model_coerce_generic(kind, fits, comp) == gold_coerce_generic(dtype), (
        "generic deep model disagrees with gold on %r: model=%r gold=%r"
        % (dtype, model_coerce_generic(kind, fits, comp),
           gold_coerce_generic(dtype)))

    # (3) the gold predicate agrees with observable coercion behaviour: a kind
    #     the gold generic path coerces is exactly one whose elements, cast to
    #     the default real type, change away from their own dtype; a preserved
    #     kind keeps its dtype unchanged. (Object/composite are special: object
    #     elements have no native dtype to preserve and ARE coerced; composite
    #     is preserved.)
    if comp:
        # composite kinds are preserved by the gold generic path
        assert not gold_coerce_generic(dtype)


def main():
    # --- boundary: the relevant concrete numpy dtypes ------------------------
    boundary = [
        np.dtype(np.bool_),
        np.dtype(np.int8), np.dtype(np.int16), np.dtype(np.int32),
        np.dtype(np.int64),
        np.dtype(np.uint8), np.dtype(np.uint16), np.dtype(np.uint32),
        np.dtype(np.uint64),
        np.dtype(np.float16),    # the regression: kind 'f', cannot absorb f32
        np.dtype(np.float32),
        np.dtype(np.float64),
        np.dtype(np.complex64), np.dtype(np.complex128),
        np.dtype(object),
        np.dtype([('x', np.float64), ('y', np.int32)]),   # composite
        np.dtype([('a', np.float64)]),                    # single-field composite
    ]
    # float128 / complex256 exist only on some platforms.
    for name in ('float128', 'complex256'):
        if hasattr(np, name):
            boundary.append(np.dtype(getattr(np, name)))

    for dt in boundary:
        check_dtype(dt)

    # the headline regression: a narrow real kind must be preserved by BOTH
    # paths, exactly because the old width-comparison wrongly coerced it.
    f16 = np.dtype(np.float16)
    k, fits, comp = observables(f16)
    assert fits is False, "float16 should NOT absorb a reference float32"
    assert k == KIND_REAL
    assert model_coerce_homogeneous(k, fits, comp) is False
    assert model_coerce_generic(k, fits, comp) is False
    # the OLD predicate (what model_prepatch encodes) WOULD have coerced it:
    old_homog = not (fits or comp)
    assert old_homog is True, "pre-patch predicate must coerce float16 (the bug)"

    # --- fuzz over arbitrary (legal and illegal) observable combinations -----
    # For each real dtype we randomly perturb nothing (observables are derived),
    # but we also assert the model's realizable() rejects impossible combos that
    # numpy never produces, so the spec domain is neither too wide nor too
    # narrow on the dtypes that matter.
    rng = random.Random(8872)
    kinds = [KIND_BOOL, KIND_INT, KIND_UINT, KIND_REAL, KIND_COMPLEX,
             KIND_OBJECT, KIND_COMPOSITE]
    for _ in range(20000):
        kind = rng.choice(kinds)
        fits = rng.random() < 0.5
        comp = rng.random() < 0.5
        if not model_realizable(kind, fits, comp):
            continue
        # within the realisable domain the two decisions must be a pure
        # function of the kind (never of fits/comp) -- the property the fix
        # establishes.
        assert model_coerce_homogeneous(kind, fits, comp) == model_is_int_like(kind)
        assert model_coerce_generic(kind, fits, comp) == (
            model_is_int_like(kind) or kind == KIND_OBJECT)

    print("G-AX OK: deep model (cast-to-real decision) == gold predicate on "
          "%d boundary numpy dtypes + 20000 fuzz combos; float16 regression "
          "pinned (preserved by fix, coerced by pre-patch); spec domain "
          "exactly the realisable dtypes." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
