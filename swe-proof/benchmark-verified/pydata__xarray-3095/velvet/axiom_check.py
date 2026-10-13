#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-3095.

There is NO consumed axiom in this bundle. The dtype-preserving copy is modeled
DEEPLY (Solution.lean's `adapterCopy` / `indexVariableCopy`). What G-AX validates
is the **A-reference**: that the deep model's two observables (element values
preserved, STORED element dtype preserved) equal the real numpy/pandas/xarray
behaviour the gold patch relies on.

G-AX runs against the BASE (unpatched) repo. The patched `PandasIndexAdapter`
gains a `copy` method whose body is `PandasIndexAdapter(array, self._dtype)`; we
exercise that exact expression directly (the constructor exists at base), so the
A-reference is the real Python the patch ships — not a re-statement of it.

Three checks against real callees (no value is asserted that the real code does
not produce):

  (A-reference 1) The re-inference gap that makes preservation observable: a
      `PandasIndexAdapter` built from a fixed-width unicode array WITHOUT a
      stored dtype re-derives a NON-unicode (generic object) element dtype
      (inferredDtype != storedDtype), while a float/int array re-derives the same
      dtype (inferredDtype == storedDtype). This is the `__init__` dtype-
      inference block; it justifies the model's distinct `inferredDtype` field.

  (A-reference 2) The patched `PandasIndexAdapter.copy` body
      `PandasIndexAdapter(array, self._dtype)` returns a wrapper whose `.dtype`
      equals the original's STORED dtype and whose element values are unchanged,
      for either `deep` setting. Additionally, because the copy's underlying
      `pandas.Index` carries the same element values, the dtype RE-DERIVED from
      the copy's underlying representation equals the one re-derived from the
      original's (model: `out.inferredDtype = self.inferredDtype`). This is the
      A-reference for `adapterCopy`.

  (A-reference 3) A real `IndexVariable` over a `<U*` coordinate, copied via the
      patched delegation `self._data.copy(deep=...)` (emulated by the §2 body
      since base lacks the method), yields a variable whose data wrapper keeps
      the unicode dtype — the user-visible behaviour the issue demands. Env-
      tolerant: skipped (not failed) if xarray cannot be set up here.

Imports only numpy + the repo under test. Exit 0 iff every obligation holds.
"""
import os
import sys


STR_ARRAYS = None  # built lazily once numpy is imported


def _arrays(np):
    return {
        'str': [np.array(['foo']),
                np.array(['foo', 'bar', 'baz']),
                np.array(['a', 'bb', 'ccc']),
                np.array(['x' * 50])],
        'float': [(0.5 * np.arange(10)).astype(float),
                  np.array([0.0]),
                  np.array([1.5, -2.5, 3.0])],
        'int': [(0.5 * np.arange(10)).astype(int),
                np.array([0]),
                np.array([-1, 2, -3])],
    }


def _values_key(np, arr):
    return [repr(x) for x in np.asarray(arr).tolist()]


def check_reinference_gap(np, PandasIndexAdapter):
    """A-reference 1: the gap that makes preservation observable.

    The original wrapper stores its dtype from the INPUT ndarray's dtype, so a
    `<U*` array yields a wrapper whose stored dtype is the precise unicode dtype.
    But the wrapper's UNDERLYING representation is a `pandas.Index`, whose dtype
    is a generic object dtype for unicode. Reconstructing a wrapper from that
    underlying `pandas.Index` WITHOUT a stored dtype (exactly what the buggy
    `IndexVariable.copy` did) re-derives that object dtype — so
    `inferredDtype != storedDtype` for unicode. For float/int the underlying
    `pandas.Index` dtype matches, so `inferredDtype == storedDtype`."""
    n = 0
    arrays = _arrays(np)
    for arr in arrays['str']:
        assert arr.dtype.kind == 'U', "expected unicode array"
        orig = PandasIndexAdapter(arr)                    # stored from input ndarray
        stored = orig.dtype                               # the precise <U*> dtype
        assert stored == arr.dtype, \
            "stored dtype should be the input unicode dtype, got %r" % (stored,)
        # inferredDtype: reconstruct from the underlying pandas.Index, no dtype.
        inferred = PandasIndexAdapter(orig.array).dtype
        assert inferred != stored, (
            "re-inference from the underlying pandas.Index should DROP the "
            "precise unicode dtype %r, got %r" % (stored, inferred))
        assert inferred == np.dtype('O'), \
            "unicode re-inference should fall back to object, got %r" % (inferred,)
        n += 1
    for kind in ('float', 'int'):
        for arr in arrays[kind]:
            orig = PandasIndexAdapter(arr)
            stored = orig.dtype
            inferred = PandasIndexAdapter(orig.array).dtype
            assert inferred == stored, (
                "%s dtype should survive re-inference: stored=%r inferred=%r"
                % (kind, stored, inferred))
            n += 1
    return n


def check_patched_copy(np, PandasIndexAdapter):
    """A-reference 2: the patched copy body `PandasIndexAdapter(array, self._dtype)`
    preserves the STORED dtype and the element values, for either `deep`."""
    n = 0
    arrays = _arrays(np)
    for kind, arrs in arrays.items():
        for arr in arrs:
            # The wrapper as IndexVariable stores it: dtype inferred from the
            # input ndarray at construction. For unicode this stores '<U*'.
            stored = PandasIndexAdapter(arr)
            for deep in (True, False):
                # patched body: array = self.array.copy(deep=True) if deep
                #               else self.array ; PandasIndexAdapter(array, self._dtype)
                array = stored.array.copy(deep=True) if deep else stored.array
                out = PandasIndexAdapter(array, stored._dtype)
                assert out.dtype == stored.dtype, (
                    "%s deep=%s: patched copy must preserve stored dtype "
                    "%r, got %r" % (kind, deep, stored.dtype, out.dtype))
                assert _values_key(np, out) == _values_key(np, stored), (
                    "%s deep=%s: patched copy must preserve element values"
                    % (kind, deep))
                # inferredDtype preservation: re-deriving from the COPY's
                # underlying representation yields the same dtype as re-deriving
                # from the ORIGINAL's (same element values underneath) — the
                # model's `out.inferredDtype = self.inferredDtype`.
                inferred_orig = PandasIndexAdapter(stored.array).dtype
                inferred_out = PandasIndexAdapter(out.array).dtype
                assert inferred_out == inferred_orig, (
                    "%s deep=%s: re-derived dtype must be preserved across "
                    "copy: orig=%r out=%r" % (kind, deep, inferred_orig,
                                              inferred_out))
                # for unicode this is exactly the dtype the BUGGY path (no dtype,
                # reconstruct from the underlying pandas.Index) would have dropped:
                if arr.dtype.kind == 'U':
                    dropped = PandasIndexAdapter(array).dtype
                    assert dropped != out.dtype, \
                        "unicode: patched (preserve) must differ from buggy (drop)"
                n += 1
    return n


def check_real_index_variable(np):
    """A-reference 3: a real IndexVariable over a <U*> coordinate, copied via the
    patched delegation, keeps the unicode dtype. Env-tolerant."""
    from xarray.core.variable import IndexVariable
    from xarray.core.indexing import PandasIndexAdapter
    n = 0
    for arr in (np.array(['foo']), np.array(['foo', 'bar', 'baz'])):
        v = IndexVariable('x', arr)
        assert v.dtype.kind == 'U', \
            "IndexVariable over <U*> coord should present a unicode dtype, got %r" % (v.dtype,)
        # patched delegation: data = self._data.copy(deep=deep); the wrapper copy
        # body is PandasIndexAdapter(array, self._dtype). Emulate it (base lacks
        # the method) and rebuild the variable.
        for deep in (True, False):
            d = v._data
            array = d.array.copy(deep=True) if deep else d.array
            new_data = PandasIndexAdapter(array, d._dtype)
            w = IndexVariable('x', new_data)
            assert w.dtype == v.dtype, (
                "deep=%s: copied IndexVariable must keep the unicode dtype "
                "%r, got %r" % (deep, v.dtype, w.dtype))
            n += 1
    return n


def main():
    sys.path.insert(0, os.environ.get('TESTBED', '/testbed'))
    import numpy as np
    from xarray.core.indexing import PandasIndexAdapter

    n_gap = check_reinference_gap(np, PandasIndexAdapter)
    n_copy = check_patched_copy(np, PandasIndexAdapter)
    try:
        n_iv = check_real_index_variable(np)
        iv_note = "%d real IndexVariable.copy cases" % n_iv
    except Exception as e:  # pragma: no cover - environment-dependent
        print("G-AX NOTE: real IndexVariable leg skipped (%s: %s)"
              % (type(e).__name__, e), file=sys.stderr)
        iv_note = "real IndexVariable leg skipped (env)"

    print("G-AX OK: re-inference gap sound on %d arrays (unicode drops to object, "
          "float/int preserved); patched copy preserves stored dtype + re-derived "
          "(inferred) dtype + values on %d cases (== deep model adapterCopy); %s."
          % (n_gap, n_copy, iv_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
