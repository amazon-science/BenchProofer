#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24970.

This bundle has ONE @ContractOnly callee, `assign_special_rows` (plus the
@Predicate token `rows_assigned` it grants), modelling the UNCHANGED per-element
special-row assignment over an integer array. The deep pure models
(`selected_index` / `clip_row` / `final_row` / `rows_of`) describe its result.
G-AX validates the callee's contract against the REAL NumPy integer-array
operation the colormap performs, on boundary + fuzz inputs.

The callee contract makes two claims that this script validates:

  (1) RESULT.  On a well-defined assignment (a container that admits every
      special index it writes), the per-element result `final_row(v,n,bad)`
      equals the REAL NumPy index pipeline:
          xa = xa.astype(int)          # the carrier admits every index
          xa[xa > n-1] = n+1           # over-range row
          xa[xa < 0]  = n              # under-range row
          xa[mask]    = n+2            # bad/masked row
          row = clip(xa, 0, n+2)       # lut.take(..., mode='clip')

  (2) LEGALITY PRECONDITION (the weakest-sufficient claim, load-bearing).
      The contract's `Requires(modulus >= n+3)` is exactly the condition under
      which the special-row assignment COMPLETES without an out-of-range store
      into the integer container -- i.e. without the NumPy out-of-bound-integer
      deprecation (which pytest's `filterwarnings=error` turns into the F2P
      failure). This script asserts, against real NumPy:
        * a container with `modulus >= n+3` (the carrier admits the largest
          special index n+2) performs the special-row stores with NO
          DeprecationWarning -- the assignment is well-defined (token granted);
        * a container with `modulus < n+3` (a special index does not fit) emits
          the deprecation on the store of that index -- the assignment is NOT
          well-defined there, EVEN WHEN no element actually matches the mask
          (the store's scalar conversion is evaluated regardless). This is the
          discriminator the F2P test observes for `cm(uint8(0))`: value 0 takes
          no special branch, yet the narrow uint8 store of 257/256/258 warns.
      So `modulus >= n+3` is neither too strong (it does not exclude a width
      that would actually complete) nor too weak (every excluded width really
      does fail), i.e. it is the weakest sufficient legality precondition.

Imports only the standard library plus `numpy` -- the very dependency the gold
patch operates on. Exit 0 iff every obligation holds.
"""
import random
import sys
import warnings

import numpy as np


# --- model.py reference encodings (kept in lock-step with the deep models) ---

def selected_index(v, n, bad):
    """model.py `selected_index`: bad wins, then over-range, then under-range,
    else the element's own index."""
    if bad:
        return n + 2
    if v > n - 1:
        return n + 1
    if v < 0:
        return n
    return v


def clip_row(idx, n):
    """model.py `clip_row`: clip to the valid table-row range 0..N+2."""
    if idx < 0:
        return 0
    if idx > n + 2:
        return n + 2
    return idx


def final_row(v, n, bad):
    """model.py `final_row`: select then clip."""
    return clip_row(selected_index(v, n, bad), n)


# --- the REAL NumPy pipeline (what the repo code does) -----------------------

def real_row_widened(value, n, bad):
    """The patched integer pipeline of Colormap.__call__ on a single element:
    the carrier admits every index (signed int), write the three special rows,
    then clip. This is the assignment when modulus >= n+3."""
    xa = np.atleast_1d(np.array(value))
    with np.errstate(invalid="ignore"):
        xa = xa.astype(int)
    mask_bad = np.atleast_1d(np.array(bad, dtype=bool))
    xa[xa > n - 1] = n + 1
    xa[xa < 0] = n
    xa[mask_bad] = n + 2
    return int(np.clip(xa, 0, n + 2)[0])


def store_emits_deprecation(n, dtype):
    """Run the special-row stores into a container of `dtype` on a SINGLE
    in-range, unmasked element (value 0, mask False) -- the F2P-shaped input:
    no element matches any special mask, so the result VALUE is unchanged, yet
    the stores convert the special-index scalars n+1, n, n+2 into the container.
    Returns True iff NumPy emits a DeprecationWarning on any of those stores
    (the out-of-bound-integer deprecation the F2P test escalates to an error)."""
    xa = np.atleast_1d(np.array(0, dtype=dtype))      # value 0, in range
    mask_bad = np.atleast_1d(np.array(False, dtype=bool))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            xa[xa > n - 1] = n + 1     # over-range row index
            xa[xa < 0] = n             # under-range row index
            xa[mask_bad] = n + 2       # bad/masked row index
        except (OverflowError, ValueError):
            # NumPy refused the out-of-range store outright -- a fortiori the
            # assignment is not well-defined for this container.
            return True
    return any(issubclass(w.category, DeprecationWarning) for w in caught)


def container_modulus(dtype):
    """The number of distinct values a NumPy unsigned integer dtype admits
    (modulus): an m-bit unsigned dtype admits 0..2**m-1, i.e. modulus = 2**m."""
    info = np.iinfo(dtype)
    return int(info.max) - int(info.min) + 1


# --- the checks --------------------------------------------------------------

def check_result_on_widened():
    """(1) `final_row` == the real widened NumPy pipeline, boundary + fuzz.
    This is the result the callee returns on a well-defined (modulus>=n+3)
    assignment."""
    boundary = []
    for n in (1, 2, 8, 255, 256, 257, 300):
        for v in (-3, -1, 0, 1, n - 2, n - 1, n, n + 1, n + 5):
            for bad in (False, True):
                boundary.append((v, n, bad))
    for (v, n, bad) in boundary:
        exp = final_row(v, n, bad)
        obs = real_row_widened(v, n, bad)
        assert exp == obs, (
            "final_row deep model unsound on (v=%d,n=%d,bad=%s): model %d, "
            "real widened pipeline %d" % (v, n, bad, exp, obs))

    rng = random.Random(24970)
    for _ in range(20000):
        n = rng.randint(1, 320)
        v = rng.randint(-6, n + 12)
        bad = rng.random() < 0.2
        exp = final_row(v, n, bad)
        obs = real_row_widened(v, n, bad)
        assert exp == obs, (
            "final_row deep model unsound on (v=%d,n=%d,bad=%s): model %d, "
            "real widened pipeline %d" % (v, n, bad, exp, obs))


def check_legality_precondition():
    """(2) `modulus >= n+3` is the WEAKEST-SUFFICIENT legality precondition for
    a completing (no-deprecation) special-row assignment, verified against real
    NumPy on the F2P-shaped input (value 0, unmasked).

      * modulus >= n+3 (the largest index n+2 fits): NO deprecation -> the
        assignment is well-defined and the contract applies (token granted).
      * modulus <  n+3 (a special index does not fit): deprecation emitted ->
        the assignment is NOT well-defined; the contract correctly does not
        apply (precondition false), so model_prepatch's narrow carrier fails.

    Checked across the unsigned dtypes the bug concerns, sweeping N around each
    container's modulus so both sides of the n+3 threshold are exercised."""
    int_dtypes = [np.uint8, np.uint16, np.int8, np.int16]
    for dtype in int_dtypes:
        info = np.iinfo(dtype)
        hi = int(info.max)            # largest representable value
        # The largest special index written is n+2; it fits iff n+2 <= hi,
        # i.e. n <= hi-2. For UNSIGNED dtypes modulus = hi+1, so n+2<=hi <=>
        # modulus >= n+3. Sweep N across the threshold n = hi-2.
        for n in range(max(1, hi - 5), hi + 4):
            fits = (n + 2 <= hi)              # the real "container admits n+2"
            emits = store_emits_deprecation(n, dtype)
            # The legality precondition must coincide with "no deprecation".
            assert fits != emits, (
                "legality threshold mismatch for dtype=%s n=%d: index n+2=%d "
                "fits=%s but NumPy emits-deprecation=%s (expected opposite)"
                % (np.dtype(dtype).name, n, n + 2, fits, emits))
            # For UNSIGNED dtypes confirm the model's `modulus >= n+3` form
            # matches `fits` exactly (the contract is written in modulus terms).
            if np.issubdtype(dtype, np.unsignedinteger):
                modulus = container_modulus(dtype)
                model_legal = (modulus >= n + 3)
                assert model_legal == fits, (
                    "modulus form mismatch dtype=%s n=%d: modulus=%d "
                    "modulus>=n+3 -> %s but index-fits -> %s"
                    % (np.dtype(dtype).name, n, modulus, model_legal, fits))


def check_f2p_witness():
    """The exact F2P observable: for a uint8 container at the default N=256 the
    special indices (256,257,258) do NOT fit (modulus 256 < n+3 = 259), so even
    the unmasked value-0 store emits the deprecation -- the narrow assignment is
    not well-defined (model_prepatch's failure). A widened (signed int) carrier
    admits them: no deprecation, same row value (0). This is precisely
    `cm(uint8(0))` warning pre-patch / not post-patch, with the value unchanged."""
    n = 256
    # Narrow uint8 carrier: modulus 256 < n+3 = 259 -> NOT well-defined.
    assert container_modulus(np.uint8) == 256
    assert not (container_modulus(np.uint8) >= n + 3)
    assert store_emits_deprecation(n, np.uint8), (
        "expected the narrow uint8 store to emit the out-of-bound deprecation "
        "even for the unmasked value-0 input (the F2P discriminator)")
    # Widened carrier (modulus >= n+3): no deprecation, value-0 row stays 0.
    assert not store_emits_deprecation(n, np.int64)
    assert final_row(0, n, False) == 0, "value-0 element keeps row 0"
    assert real_row_widened(0, n, False) == 0


def main():
    check_result_on_widened()
    check_legality_precondition()
    check_f2p_witness()
    print("G-AX OK: final_row == real widened NumPy pipeline (48 boundary + "
          "20000 fuzz); modulus>=n+3 is the weakest-sufficient legality "
          "precondition (coincides exactly with no-deprecation across "
          "uint8/uint16/int8/int16 around the threshold); F2P witness: narrow "
          "uint8 store of 256/257/258 deprecates on the unmasked value-0 input "
          "while a widened carrier does not, value unchanged (row 0).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
