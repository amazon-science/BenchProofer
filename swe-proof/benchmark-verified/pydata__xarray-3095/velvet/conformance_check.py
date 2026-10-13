#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3095 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `adapterCopy` /
              `indexVariableCopy` impl regions transliterated to Python over the
              *real* repo carrier. The impl constructs a fresh wrapper whose
              ELEMENT VALUES equal the input's, whose STORED element dtype
              equals the input's stored dtype, and whose RE-DERIVABLE
              (inferred) dtype equals the input's — for either `deep` setting.
              So the shadow's three observables are simply
              `(values, stored_dtype, inferred_dtype)` carried through.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `PandasIndexAdapter.copy(deep=...)` (and, when importable, the real
              patched `IndexVariable.copy(deep=...)`), invoked in-process on real
              numpy arrays. G-CONF runs with the gold patch applied
              (PYTHONPATH=/testbed), so this is the actual Python the patch ships.

They must agree on every input: the SHADOW's preserved (values, stored-dtype,
inferred-dtype) must equal the ORACLE copy's (values, dtype, dtype re-derived
from the copy's underlying representation). The discriminating element kind is
fixed-width unicode (`<U*`), whose stored dtype the bug dropped to object; float
and int kinds (unaffected) are exercised too. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

stdlib + numpy + the repo under test. The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import random
import sys

SEED = 3095
N_FUZZ = 100_000


def _values_key(arr):
    """Order-preserving element-identity key (the bijection of mapping.md §2):
    compare element values position-by-position, kind-agnostically."""
    import numpy as np
    a = np.asarray(arr)
    return [repr(x) for x in a.tolist()]


def make_arrays(n, rng):
    """Boundary cases first, then fuzz. Each is a numpy array whose element
    dtype is fixed-width unicode / float / int (the three astype kinds the F2P
    test parametrizes: str, float, int)."""
    import numpy as np
    # boundary cases (plan §4.1 step 4)
    yield np.array(['foo'])                          # the issue's exact case
    yield np.array(['foo', 'bar', 'baz'])
    yield np.array(['a', 'bb', 'ccc'])               # mixed widths
    yield np.array([''], dtype='<U1')                # empty string
    yield (0.5 * np.arange(10)).astype(float)        # the test's float leg
    yield (0.5 * np.arange(10)).astype(int)          # the test's int leg
    yield np.array([0.0])
    yield np.array([0])
    yield np.array(['x' * 50])                        # wide unicode
    for _ in range(n):
        kind = rng.choice(['str', 'float', 'int'])
        k = rng.randint(1, 12)
        if kind == 'str':
            w = rng.randint(1, 8)
            elems = [''.join(rng.choice('abcdefghij ')
                             for _ in range(rng.randint(0, w))) for _ in range(k)]
            yield np.array(elems)
        elif kind == 'float':
            yield np.array([rng.uniform(-1e3, 1e3) for _ in range(k)])
        else:
            yield np.array([rng.randint(-1000, 1000) for _ in range(k)])


def shadow_copy(stored_values_key, stored_dtype_name, inferred_dtype_name):
    """Solution.lean `adapterCopy`/`indexVariableCopy`, transliterated:
    out.values = self.values ; out.storedDtype = self.storedDtype ;
    out.inferredDtype = self.inferredDtype, for either `deep`. Returns the
    three observables carried straight through."""
    return stored_values_key, stored_dtype_name, inferred_dtype_name


def main():
    try:
        import numpy as np  # noqa: F401
        from xarray.core.indexing import PandasIndexAdapter
    except Exception as e:  # pragma: no cover
        print("G-CONF ERROR: cannot import repo PandasIndexAdapter (%s: %s)"
              % (type(e).__name__, e), file=sys.stderr)
        return 2

    # Optional IndexVariable leg (xarray import; env-tolerant).
    try:
        from xarray.core.variable import IndexVariable
        have_iv = True
    except Exception:  # pragma: no cover
        IndexVariable = None
        have_iv = False

    rng = random.Random(SEED)
    fails = 0
    checked = 0
    iv_checked = 0

    for arr in make_arrays(N_FUZZ, rng):
        # Build the stored wrapper the way IndexVariable does at construction:
        # PandasIndexAdapter(<numpy array>) infers the stored dtype from the
        # ORIGINAL array's dtype (so unicode is stored as <U*>).
        stored = PandasIndexAdapter(arr)
        stored_values_key = _values_key(arr)
        stored_dtype_name = stored.dtype.name
        # inferredDtype: the dtype re-derived from the wrapper's underlying
        # representation alone (no stored dtype passed).
        inferred_dtype_name = PandasIndexAdapter(stored.array).dtype.name

        for deep in (True, False):
            # ORACLE: the real patched PandasIndexAdapter.copy.
            out = stored.copy(deep=deep)
            oracle_values_key = _values_key(np.asarray(out))
            oracle_dtype_name = out.dtype.name
            oracle_inferred_name = PandasIndexAdapter(out.array).dtype.name

            # SHADOW: values + stored dtype + inferred dtype carried through.
            shadow_values_key, shadow_dtype_name, shadow_inferred_name = \
                shadow_copy(stored_values_key, stored_dtype_name,
                            inferred_dtype_name)

            if shadow_dtype_name != oracle_dtype_name:
                fails += 1
                if fails <= 10:
                    print("DTYPE DISAGREE: arr.dtype=%s deep=%s shadow=%s "
                          "oracle=%s" % (arr.dtype, deep, shadow_dtype_name,
                                         oracle_dtype_name), file=sys.stderr)
            if shadow_inferred_name != oracle_inferred_name:
                fails += 1
                if fails <= 10:
                    print("INFERRED DTYPE DISAGREE: arr.dtype=%s deep=%s "
                          "shadow=%s oracle=%s"
                          % (arr.dtype, deep, shadow_inferred_name,
                             oracle_inferred_name), file=sys.stderr)
            if shadow_values_key != oracle_values_key:
                fails += 1
                if fails <= 10:
                    print("VALUES DISAGREE: arr.dtype=%s deep=%s"
                          % (arr.dtype, deep), file=sys.stderr)
            checked += 1

        # IndexVariable leg: the copied variable's data dtype preserves the
        # stored element dtype (the user-visible regression in the issue).
        if have_iv:
            try:
                v = IndexVariable('x', arr)
                for deep in (True, False):
                    w = v.copy(deep=deep)
                    if w.dtype.name != v.dtype.name:
                        fails += 1
                        if fails <= 10:
                            print("IV DTYPE DISAGREE: arr.dtype=%s deep=%s "
                                  "v=%s w=%s" % (arr.dtype, deep, v.dtype.name,
                                                 w.dtype.name), file=sys.stderr)
                    iv_checked += 1
            except Exception as e:  # pragma: no cover
                # not all element arrays are valid 1-D index coords; skip those
                if "must be 1-dimensional" not in str(e):
                    pass

    if fails:
        print("G-CONF FAIL: %d disagreement(s) over %d adapter-copy cases "
              "(+%d IndexVariable cases), seed %d." % (fails, checked,
                                                       iv_checked, SEED),
              file=sys.stderr)
        return 1
    print("G-CONF PASS: %d PandasIndexAdapter.copy cases + %d IndexVariable.copy "
          "cases, 0 disagreements (seed %d). Stored element dtype + re-derived "
          "(inferred) dtype + element values preserved for str/float/int kinds, "
          "deep=True/False." % (checked, iv_checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
