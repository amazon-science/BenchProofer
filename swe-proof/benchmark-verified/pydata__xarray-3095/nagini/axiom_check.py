#!/usr/bin/env python3
"""G-AX executable soundness / faithfulness check for pydata__xarray-3095.

This bundle has NO consumed @ContractOnly axiom. The changed behaviour — that
duplicating an index wrapper preserves the element type (dtype) the original was
created with, rather than re-deriving it from the duplicated buffer — is
modelled DEEPLY in model.py:

  * derive_dtype(array_kind, given_dtype): the element type a freshly built
    wrapper reports — the supplied type verbatim when one is given, else the
    type re-derived from the buffer (the lossy step).
  * adapter_copy(self, deep): the duplicate's reported type equals the
    original's stored type (Result() == Old(self.stored_dtype)).

What must be checked against REAL xarray (the libraries/code the gold patch
touches) is that this deep model is FAITHFUL:

  (F1) Construction faithfulness (derive_dtype):
       - PandasIndexAdapter(array, dtype=D) reports dtype == D  (supplied wins);
       - PandasIndexAdapter(array, dtype=None) RE-DERIVES from the buffer, and
         for a fixed-width-text ('<U*') array that re-derivation collapses to
         the generic object dtype  (array_kind == OBJECT for the text case) —
         i.e. the re-derivation really is lossy, justifying why the original
         type must be carried over.

  (F2) Copy faithfulness (adapter_copy):
       - PandasIndexAdapter.copy(deep=D) reports the SAME dtype as the original,
         for deep in {True, False}, for text / int / float element types —
         exactly model.py's Result() == Old(self.stored_dtype).

  (F3) End-to-end (the F2P regression): IndexVariable.copy(deep=True) on a
       unicode-typed index preserves the '<U*' dtype (does NOT cast to object).
       This is xarray/tests/test_variable.py::TestIndexVariable::test_copy[str-True].

Imports numpy / pandas / xarray (the exact libraries the patched code uses),
available in the evaluation container. Exit 0 iff every obligation holds.
"""
import sys

import numpy as np
import pandas as pd

from xarray.core.indexing import PandasIndexAdapter
from xarray.core.variable import IndexVariable


# --- deep-model references (kept in lock-step with model.py) -----------------

NO_DTYPE = None          # model.py NO_DTYPE sentinel (here: "no dtype supplied")


def derive_dtype(array_kind, given_dtype):
    """model.py's derive_dtype as a pure Python function over real np.dtype
    objects: a supplied element type is used verbatim, else re-derive from the
    buffer (the value passed in as array_kind)."""
    if given_dtype is not NO_DTYPE:
        return given_dtype
    return array_kind


def fail(msg):
    print("G-AX FAIL: " + msg)
    sys.exit(1)


# --- F1: construction faithfulness of derive_dtype ---------------------------

def check_construction():
    # A few representative buffers spanning the element types the F2P matrix
    # exercises (str / int / float) plus datetime.
    buffers = [
        ("text",  np.array(['foo', 'bar', 'baz']).astype(str)),   # '<U*'
        ("int",   np.arange(5)),
        ("float", 0.5 * np.arange(5)),
        ("text2", (0.5 * np.arange(10)).astype(str)),             # the F2P data
        ("dt",    pd.date_range('2000-01-01', periods=3).values),
    ]
    for name, buf in buffers:
        # (a) supplied dtype is used verbatim by the real adapter.
        for D in (np.dtype('O'), np.dtype('<U7'), np.dtype('int64'),
                  np.dtype('float64')):
            a = PandasIndexAdapter(buf, dtype=D)
            if a.dtype != D:
                fail("supplied dtype not preserved on %r: gave %r, expected %r"
                     % (name, a.dtype, D))
            # mirror: derive_dtype(<anything>, D) == D
            if derive_dtype(a.dtype, D) != D:
                fail("derive_dtype disagrees with real adapter (supplied) on %r"
                     % name)

        # (b) dtype=None re-derives from the buffer (the lossy step). Record the
        # re-derived "array_kind".
        a_none = PandasIndexAdapter(buf, dtype=None)
        array_kind = a_none.dtype
        if derive_dtype(array_kind, NO_DTYPE) != array_kind:
            fail("derive_dtype disagrees with real adapter (re-derived) on %r"
                 % name)

    # (c) the crux, reproducing the REAL pre-patch reconstruction path. The
    # original adapter holds a pandas.Index in ``.array``; for fixed-width text
    # that stored index is object-dtype, so RE-DERIVING (dtype=None) from a copy
    # of that index collapses to the generic object dtype, losing the original
    # '<U*' element type. This is precisely the lossy step the fix avoids by
    # carrying over the original dtype.
    text_buf = (0.5 * np.arange(10)).astype(str)        # '<U32'
    original = PandasIndexAdapter(text_buf)             # original stored dtype
    original_dtype = original.dtype
    if original_dtype == np.dtype('O'):
        fail("setup error: original text adapter already object-typed")
    # the pre-patch reconstruction: PandasIndexAdapter(self.array.copy(deep=True))
    rederived = PandasIndexAdapter(original.array.copy(deep=True), dtype=None)
    if rederived.dtype != np.dtype('O'):
        fail("expected re-derived text dtype to collapse to object, got %r"
             % rederived.dtype)
    # array_kind (re-derived) and stored_dtype (original) genuinely DISAGREE for
    # text — exactly the model.py case where they differ; the deep model says
    # derive_dtype(array_kind, NO_DTYPE) == array_kind == object != original.
    if derive_dtype(rederived.dtype, NO_DTYPE) == original_dtype:
        fail("model assumes array_kind != stored_dtype for text but they match")
    # the post-patch reconstruction carries over the original dtype.
    kept = PandasIndexAdapter(original.array.copy(deep=True), original._dtype)
    if kept.dtype != original_dtype:
        fail("carrying over original dtype did not preserve it, got %r"
             % kept.dtype)


# --- F2: copy faithfulness of adapter_copy -----------------------------------

def check_adapter_copy():
    buffers = [
        np.array(['foo', 'bar']).astype(str),       # text '<U*'
        (0.5 * np.arange(10)).astype(str),           # the F2P text data
        np.arange(7),                                # int
        0.5 * np.arange(7),                          # float
        pd.date_range('2000-01-01', periods=4).values,  # datetime
    ]
    for buf in buffers:
        original = PandasIndexAdapter(buf)            # dtype re-derived once
        original_dtype = original.dtype
        for deep in (True, False):
            dup = original.copy(deep=deep)
            # model.py: Result() == Old(self.stored_dtype)
            if dup.dtype != original_dtype:
                fail("copy(deep=%r) changed dtype on %r: %r -> %r"
                     % (deep, buf.dtype, original_dtype, dup.dtype))


# --- F3: the F2P regression itself (end-to-end IndexVariable.copy) -----------

def check_f2p_regression():
    for deep in (True, False):
        v = IndexVariable('x', (0.5 * np.arange(10)).astype(str), {'foo': 'bar'})
        w = v.copy(deep=deep)
        if w.dtype != v.dtype:
            fail("IndexVariable.copy(deep=%r) cast unicode index to %r "
                 "(expected %r)" % (deep, w.dtype, v.dtype))
        if w.dtype == np.dtype('O') and v.dtype != np.dtype('O'):
            fail("IndexVariable.copy(deep=%r) cast unicode -> object" % deep)


def main():
    check_construction()
    check_adapter_copy()
    check_f2p_regression()
    print("G-AX OK: derive_dtype + adapter_copy deep models faithful to real "
          "PandasIndexAdapter construction/copy; re-derivation of fixed-width "
          "text collapses to object (lossy) while copy preserves the original "
          "dtype for text/int/float/datetime across deep in {True,False}; F2P "
          "IndexVariable.copy(deep=True/False) preserves '<U*'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
