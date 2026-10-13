#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-8872 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM with the contract
          calls (Requires/Ensures) stripped; the model IS Python, so no
          transliteration. The @Pure helpers (kind-tag constants,
          is_int_like, realizable) copy over as plain functions. The shadow
          works over the model's carrier types: three plain observables of
          an element type (kind code point, whether a reference 32-bit real
          fits its storage losslessly, whether it is composite).

BRIDGE  — mapping.md §2's type abstraction, applied to a real numpy dtype:
          kind == ord(dtype.kind); fits_ref_real32 ==
          bool(np.can_cast(np.float32, dtype)); is_composite ==
          bool(dtype.fields). The boolean the modeled functions return IS
          the coercion decision: True means the stored element type becomes
          the default real type (float64), False means the value's own
          element type is preserved. So the comparison observable is the
          resulting dtype of the constructed quantity.

ORACLE  — the REAL patched constructor astropy.units.Quantity.__new__
          (PYTHONPATH=/testbed, gold patch applied by the gate before this
          script runs), driven through both modeled decision sites:
            * homogeneous path: wrap a value that already carries a unit
              (build a Quantity with its dtype pinned explicitly so no
              decision fires during setup, then re-wrap it with no dtype
              argument — the re-wrap reaches the modeled decision);
            * generic path: wrap a plain ndarray with no unit and no dtype
              argument.
          In both cases the resulting .dtype is the observable.

DOMAIN  — inputs range over the element-type domain the mapping documents
          (mapping.md §2): the boolean, signed/unsigned integer, real,
          complex, per-element-object and composite kinds, i.e. exactly the
          dtypes the modeled decision is reached with (string kinds are
          rejected earlier by an unchanged type-validity guard and are
          outside the model; ditto datetime kinds). Every generated dtype's
          observables are asserted to satisfy the model's realizable()
          precondition, mirroring the Requires.

Exit 0 iff zero disagreements over the boundary dtypes + fuzzed inputs
(>= 1e5 comparisons in total). Pinned seed: 8872. stdlib + numpy only.
"""
import random
import sys

import numpy as np

SEED = 8872
N_FUZZ = 60_000   # each fuzz case exercises BOTH decision sites -> 120k+ cmp

# ---------------------------------------------------------------------------
# model.py pure region, copied over as plain functions (@Pure stripped).
# ---------------------------------------------------------------------------


def KIND_BOOL() -> int:
    # numpy kind tag 'b'
    return 98


def KIND_INT() -> int:
    # numpy kind tag 'i' (signed integer)
    return 105


def KIND_UINT() -> int:
    # numpy kind tag 'u' (unsigned integer)
    return 117


def KIND_REAL() -> int:
    # numpy kind tag 'f' (real / inexact floating)
    return 102


def KIND_COMPLEX() -> int:
    # numpy kind tag 'c' (complex)
    return 99


def KIND_OBJECT() -> int:
    # numpy kind tag 'O' (per-element Python object)
    return 79


def KIND_COMPOSITE() -> int:
    # numpy kind tag 'V' (void / structured multi-field record)
    return 86


def is_int_like(kind):
    """The integer / unsigned-integer element kinds."""
    return kind == KIND_INT() or kind == KIND_UINT()


def realizable(kind, fits_ref_real32, is_composite):
    """Executable form of model.py's realizable() precondition (the Implies
    ghost connective expanded to plain boolean logic)."""
    if fits_ref_real32 and not (
            kind == KIND_REAL() or kind == KIND_COMPLEX()
            or kind == KIND_OBJECT()):
        return False
    if is_composite != (kind == KIND_COMPOSITE()):
        return False
    if kind == KIND_COMPLEX() and is_composite:
        return False
    if is_int_like(kind) or kind == KIND_BOOL():
        if fits_ref_real32 or is_composite:
            return False
    return True


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM (contract statement lines stripped).
# ---------------------------------------------------------------------------


def coerce_homogeneous_input(kind, fits_ref_real32, is_composite):
    return is_int_like(kind)


def coerce_generic_input(kind, fits_ref_real32, is_composite):
    return is_int_like(kind) or kind == KIND_OBJECT()


# ---------------------------------------------------------------------------
# Bridge: real numpy dtype -> the model's three observables (mapping.md §2).
# ---------------------------------------------------------------------------


def observables(dtype):
    kind = ord(dtype.kind)
    fits_ref_real32 = bool(np.can_cast(np.float32, dtype))
    is_composite = bool(dtype.fields)
    return kind, fits_ref_real32, is_composite


FLOAT64 = np.dtype(float)


def predicted_dtype(dtype, coerce):
    """The boolean decision IS the coercion: True -> default real type,
    False -> the value's own element type, unchanged."""
    return FLOAT64 if coerce else dtype


# ---------------------------------------------------------------------------
# Oracle: the REAL patched constructor, both decision sites.
# ---------------------------------------------------------------------------


def oracle_generic_dtype(arr):
    """Resulting dtype when a plain (unit-less) value is wrapped with no
    explicit element type: reaches the generic-path decision."""
    from astropy.units import Quantity
    return Quantity(arr, unit='m').dtype


def oracle_homogeneous_dtype(arr):
    """Resulting dtype when a value already carrying a unit is re-wrapped
    with no explicit element type: reaches the homogeneous-path decision.
    Setup pins the dtype explicitly, so no decision fires before the
    re-wrap; copy stays at its default (True) so the re-wrap does not
    short-circuit."""
    from astropy.units import Quantity
    q0 = Quantity(arr, unit='m', dtype=arr.dtype)
    if q0.dtype != arr.dtype:
        raise AssertionError(
            "setup failed to pin dtype %r (got %r)" % (arr.dtype, q0.dtype))
    return Quantity(q0).dtype


# ---------------------------------------------------------------------------
# Input generation (element types + concrete values in the documented domain)
# ---------------------------------------------------------------------------

PRIMITIVE_DTYPES = [
    np.dtype(np.bool_),
    np.dtype(np.int8), np.dtype(np.int16), np.dtype(np.int32),
    np.dtype(np.int64),
    np.dtype(np.uint8), np.dtype(np.uint16), np.dtype(np.uint32),
    np.dtype(np.uint64),
    np.dtype(np.float16), np.dtype(np.float32), np.dtype(np.float64),
    np.dtype(np.complex64), np.dtype(np.complex128),
]
for _name in ('float128', 'complex256'):
    if hasattr(np, _name):
        PRIMITIVE_DTYPES.append(np.dtype(getattr(np, _name)))

# non-native byte order variants of the multi-byte primitives
SWAPPED_DTYPES = [dt.newbyteorder() for dt in PRIMITIVE_DTYPES
                  if dt.itemsize > 1]

OBJECT_DTYPE = np.dtype(object)

FIELD_MEMBER_DTYPES = [np.dtype(np.int32), np.dtype(np.int64),
                       np.dtype(np.uint8), np.dtype(np.float16),
                       np.dtype(np.float32), np.dtype(np.float64),
                       np.dtype(np.complex64), np.dtype(np.bool_)]

try:
    from decimal import Decimal
except ImportError:  # pragma: no cover
    Decimal = float


def rand_struct_dtype(rng):
    nfields = rng.randint(1, 3)
    fields = [('f%d' % i, rng.choice(FIELD_MEMBER_DTYPES))
              for i in range(nfields)]
    return np.dtype(fields)


def rand_object_element(rng):
    r = rng.random()
    if r < 0.4:
        return rng.randint(-10**6, 10**6)
    if r < 0.8:
        return rng.uniform(-1e6, 1e6)
    return Decimal(rng.randint(-1000, 1000)) / Decimal(4)


def rand_array(rng, dtype):
    """A small concrete array of the given element type. Object arrays hold
    numeric Python values only (non-numeric elements are rejected by an
    unchanged validity guard before the modeled decision is reached), and
    are kept non-empty (the guard inspects the first element)."""
    if dtype.kind == 'O':
        n = rng.randint(1, 4)
        arr = np.empty(n, dtype=object)
        for i in range(n):
            arr[i] = rand_object_element(rng)
        return arr
    if dtype.fields:
        return np.zeros(rng.randint(0, 4), dtype=dtype)
    n = rng.randint(0, 4)
    if dtype.kind == 'b':
        base = np.array([rng.random() < 0.5 for _ in range(n)], dtype=bool)
    elif dtype.kind in 'iu':
        base = np.array([rng.randint(0, 100) for _ in range(n)])
    elif dtype.kind == 'c':
        base = np.array([complex(rng.uniform(-10, 10), rng.uniform(-10, 10))
                         for _ in range(n)])
    else:
        vals = [rng.uniform(-1e4, 1e4) for _ in range(n)]
        if n and rng.random() < 0.1:
            vals[0] = float('nan') if rng.random() < 0.5 else float('inf')
        base = np.array(vals)
    return base.astype(dtype)


def rand_dtype(rng):
    r = rng.random()
    if r < 0.55:
        return rng.choice(PRIMITIVE_DTYPES)
    if r < 0.75:
        return rng.choice(SWAPPED_DTYPES)
    if r < 0.88:
        return OBJECT_DTYPE
    return rand_struct_dtype(rng)


def boundary_arrays():
    for dt in PRIMITIVE_DTYPES + SWAPPED_DTYPES:
        yield np.zeros(1, dtype=dt)
        yield np.zeros(3, dtype=dt)
        yield np.zeros((), dtype=dt)          # 0-d scalar array
        yield np.zeros(0, dtype=dt)           # empty
    obj = np.empty(2, dtype=object)
    obj[0] = 1
    obj[1] = 2.5
    yield obj
    objd = np.empty(1, dtype=object)
    objd[0] = Decimal('1.5')
    yield objd
    yield np.zeros(2, dtype=[('x', np.float64), ('y', np.int32)])
    yield np.zeros(1, dtype=[('a', np.float64)])   # single-field composite
    yield np.zeros(1, dtype=[('a', np.float16), ('b', np.uint8),
                             ('c', np.complex64)])


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def check_one(arr, disagreements):
    dt = arr.dtype
    kind, fits, comp = observables(dt)
    # the Requires: the spec domain must admit this real element type
    if not realizable(kind, fits, comp):
        raise AssertionError(
            "realizable() rejects a real dtype %r "
            "(kind=%r fits=%r comp=%r)" % (dt, chr(kind), fits, comp))
    n = 0
    for path, shadow_fn, oracle_fn in (
            ("generic", coerce_generic_input, oracle_generic_dtype),
            ("homogeneous", coerce_homogeneous_input,
             oracle_homogeneous_dtype)):
        want = predicted_dtype(dt, shadow_fn(kind, fits, comp))
        got = oracle_fn(arr)
        n += 1
        if got != want:
            disagreements.append((path, dt, arr, want, got))
    return n


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for arr in boundary_arrays():
        count += check_one(arr, disagreements)

    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        arr = rand_array(rng, rand_dtype(rng))
        count += check_one(arr, disagreements)

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d comparisons (seed=%d):"
              % (len(disagreements), count, SEED))
        for path, dt, arr, want, got in disagreements[:5]:
            print("  path=%s dtype=%r value=%r\n    shadow-predicted "
                  "dtype=%r\n    real dtype=%r" % (path, dt, arr, want, got))
        return 1
    print("G-CONF OK: model.py impl shadow (element-type observables per the "
          "mapping.md bridge) agrees with the real patched constructor on "
          "both decision sites over %d comparisons (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
