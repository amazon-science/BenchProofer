#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3095 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helper `derive_dtype` copies over
as a plain function; `IndexWrapper` is realized as a plain class holding the
two int fields. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`xarray.core.indexing.PandasIndexAdapter.copy` (the duplication method for the
labelled-index wrapper). The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable. Each
tested input constructs a real adapter (a buffer plus a supplied element type)
and calls `.copy(deep=...)` on it, observing the duplicate's reported dtype.

Type bridge (mapping.md section 2): numpy/pandas dtypes map to int element-type
codes — distinct dtypes get distinct codes, np.dtype('O') is pinned to
OBJECT_DTYPE = 0, and the "no dtype supplied" sentinel is NO_DTYPE = -1 (never
generated: the Requires demand both fields != NO_DTYPE). A wrapper state
(array_kind, stored_dtype) is realized concretely as a buffer whose
re-derivable dtype (read off empirically by constructing an adapter with no
dtype argument) is array_kind's dtype, wrapped with stored_dtype's dtype
supplied. The `deep` flag is carried through to the real call; per mapping.md
it selects buffer copy-vs-share only and is dtype-irrelevant, which the diff
confirms across both values.

Input domain: Requires demand array_kind != NO_DTYPE and stored_dtype !=
NO_DTYPE. Generation draws buffers from a pool spanning the re-derivable
kinds (fixed-width text — whose stored index re-derives to the generic object
dtype, so array_kind != stored_dtype there — plus int / float / datetime /
timedelta / bool) crossed with a pool of supplied dtypes (object, two text
widths, several numeric widths, bool, complex, datetime) and deep in
{True, False}. Every generated input satisfies the Requires.

>= 1e5 Requires-satisfying inputs: the exhaustive boundary matrix (every
buffer x supplied-dtype x deep combination) + 100000 fuzz draws.
Pinned fuzz seed: 3095.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy (+ pandas, which the repo itself requires
and which realizes the buffers the oracle operates on).
"""
import random
import sys

import numpy as np
import pandas as pd

from xarray.core.indexing import PandasIndexAdapter

SEED = 3095
N_FUZZ = 100_000


# --- model.py constants, verbatim --------------------------------------------

# A distinguished code for "no explicit element type supplied" (re-derive it).
NO_DTYPE = -1            # type: int
# The generic object element-type code (the lossy fallback).
OBJECT_DTYPE = 0         # type: int


# --- IndexWrapper as a plain class (contracts stripped) -----------------------

class IndexWrapper:
    """A wrapper around a labelled index. ``stored_dtype`` is the element-type
    code the wrapper reports; ``array_kind`` is the type code that would be
    re-derived from the underlying buffer with no element type supplied."""

    def __init__(self, array_kind, stored_dtype):
        self.array_kind = array_kind
        self.stored_dtype = stored_dtype


# --- pure helper from model.py, contracts stripped ----------------------------

def derive_dtype(array_kind, given_dtype):
    """The element-type code a freshly constructed wrapper reports, given the
    re-derivable type code of its buffer (``array_kind``) and an optionally
    supplied element-type code (``given_dtype``)."""
    if given_dtype != NO_DTYPE:
        return given_dtype
    return array_kind


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def adapter_copy(self, deep):
    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
    # so its reported type is carried over rather than re-derived.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype
    # (model.py returns the duplicate's reported element-type code; the oracle
    # observation is the duplicate adapter's .dtype, bridged to a code.)


# --- bridge: np.dtype <-> int element-type code --------------------------------

_CODES = {np.dtype('O'): OBJECT_DTYPE}


def code_of(dt):
    """Distinct dtypes <-> distinct non-negative codes; object is pinned to
    OBJECT_DTYPE. Codes are assigned deterministically in first-seen order
    over the fixed pools below, so the run is reproducible."""
    dt = np.dtype(dt)
    if dt not in _CODES:
        _CODES[dt] = max(_CODES.values()) + 1
    return _CODES[dt]


def build_pools():
    """Concrete buffers (as pandas Indexes, the wrapper's stored buffer form)
    with their empirically read-off re-derivable dtype (array_kind), plus the
    pool of supplied element types (stored_dtype candidates)."""
    raw_buffers = [
        ("text",  np.array(['foo', 'bar', 'baz']).astype(str)),   # '<U*'
        ("text2", (0.5 * np.arange(10)).astype(str)),             # '<U32'
        ("int",   np.arange(5)),
        ("float", 0.5 * np.arange(5)),
        ("dt",    pd.date_range('2000-01-01', periods=3).values),
        ("td",    pd.timedelta_range('1 day', periods=3).values),
        ("bool",  np.array([True, False, True])),
    ]
    buffers = []
    for name, buf in raw_buffers:
        # Read the re-derivable dtype off the real constructor with no
        # element type supplied — this IS the array_kind realization.
        probe = PandasIndexAdapter(buf, dtype=None)
        array_kind = probe.dtype
        buffers.append((name, probe.array, array_kind))
    supplied = [
        np.dtype('O'),
        np.dtype('<U3'),
        np.dtype('<U32'),
        np.dtype('int64'),
        np.dtype('int32'),
        np.dtype('float64'),
        np.dtype('float32'),
        np.dtype('bool'),
        np.dtype('complex128'),
        np.dtype('M8[ns]'),
    ]
    # Register codes deterministically (buffers first, then the supplied pool).
    for _, _, ak in buffers:
        code_of(ak)
    for d in supplied:
        code_of(d)
    return buffers, supplied


def check_one(name, index_buf, array_kind, supplied_dtype, deep):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    ak_code = code_of(array_kind)
    st_code = code_of(supplied_dtype)
    # Requires of adapter_copy: both codes != NO_DTYPE.
    assert ak_code != NO_DTYPE and st_code != NO_DTYPE
    # Shadow over the abstract wrapper state.
    shadow_out = adapter_copy(IndexWrapper(ak_code, st_code), deep)
    # Oracle: real adapter built with the supplied element type, duplicated.
    original = PandasIndexAdapter(index_buf, dtype=supplied_dtype)
    dup = original.copy(deep=deep)
    oracle_out = code_of(dup.dtype)
    # Read-only frame: the original must be unchanged by the duplication.
    if original.dtype != np.dtype(supplied_dtype):
        return ("original mutated: buffer=%s supplied=%r deep=%r -> "
                "original.dtype=%r" % (name, supplied_dtype, deep,
                                       original.dtype))
    if shadow_out != oracle_out:
        return ("disagreement: buffer=%s (array_kind=%r code=%d) "
                "supplied=%r (code=%d) deep=%r :: shadow=%d oracle=%d "
                "(oracle dtype %r)"
                % (name, array_kind, ak_code, supplied_dtype, st_code,
                   deep, shadow_out, oracle_out, dup.dtype))
    return None


def main():
    buffers, supplied = build_pools()
    rng = random.Random(SEED)
    n = 0

    # Boundary matrix: every buffer x supplied dtype x deep, exhaustively.
    # Includes the discriminating case (text buffer whose re-derivable dtype
    # is object while the supplied dtype is a text width: array_kind !=
    # stored_dtype) and the agreeing numeric cases.
    for name, buf, ak in buffers:
        for d in supplied:
            for deep in (True, False):
                err = check_one(name, buf, ak, d, deep)
                if err:
                    print(err)
                    return 1
                n += 1
        # identity case: supply exactly the re-derivable dtype.
        for deep in (True, False):
            err = check_one(name, buf, ak, ak, deep)
            if err:
                print(err)
                return 1
            n += 1

    # Fuzz: 100000 pinned-seed draws over the same Requires-satisfying domain.
    for _ in range(N_FUZZ):
        name, buf, ak = buffers[rng.randrange(len(buffers))]
        d = supplied[rng.randrange(len(supplied))]
        deep = bool(rng.getrandbits(1))
        err = check_one(name, buf, ak, d, deep)
        if err:
            print(err)
            return 1
        n += 1

    print("G-CONF OK: shadow (impl region of adapter_copy + derive_dtype) "
          "agrees with the real patched duplication method on %d "
          "Requires-satisfying inputs (boundary matrix + %d fuzz draws, "
          "seed %d); duplicate's reported element type always equals the "
          "original's stored type, independent of deep." % (n, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
