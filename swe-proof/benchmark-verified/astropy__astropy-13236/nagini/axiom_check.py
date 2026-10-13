#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13236.

This bundle consumes NO `@ContractOnly` axiom and references NO stdlib
deep-model (the `axioms` region of model.py is empty): the modeled delta is a
control-flow decision over boolean classification bits, spelled out deeply as
the pure cascade `selected_kind` (model.py). G-AX therefore reduces to a
DECISION-EQUIVALENCE check: run the REAL `Table._convert_data_to_col` on the
F2P inputs and on a fuzz of structured / masked / record-array / plain-sequence
inputs, read the resulting column *kind*, and assert it equals the kind the
model's `selected_kind` decides from the same classification bits.

The load-bearing obligation: a structured (multi-field) ndarray that is neither
an existing `Column` nor a mixin is classified by mask-status ALONE — masked ->
`MaskedColumn` (KIND_MASKED), unmasked -> `Column` (KIND_COLUMN) — and is NOT
diverted into the mixin (`NdarrayMixin`) kind. This equivalence holds only
AFTER the gold patch; the script also asserts the pre-patch divergence is real
(a structured ndarray WOULD become an `NdarrayMixin` under the deleted clause),
documenting that the spec senses the change.

A second obligation validates the unchanged sequence-conversion branch: a
non-None input that lacks a dtype and whose sequence-to-array conversion
yields a masked array (a plain list with masked entries) becomes a
MaskedColumn (KIND_MASKED), not a plain Column — the `seq_masked` bit in the
model.

Imports only `numpy` and the repo's own `astropy.table` (the very package the
patch lives in) — no Nagini, nothing model-specific. Exit 0 iff every
obligation holds.
"""
import sys

import numpy as np

from astropy.table import Table, Column, MaskedColumn
from astropy.table.ndarray_mixin import NdarrayMixin

# Model kind codes (model.py pure region):
KIND_MIXIN = 0
KIND_SEQ_MIXIN = 1
KIND_MASKED = 2
KIND_COLUMN = 3


def selected_kind(is_column, is_mixin, data0_is_mixin, elem_cls_builds,
                  is_ndarray, is_structured, is_masked,
                  has_dtype, seq_masked, is_none):
    """Reference copy of model.py's pure `selected_kind` cascade — the FULL
    parameter list and arm set, so this is the function actually under audit."""
    if is_column and is_masked:
        return KIND_MASKED
    if is_column:
        return KIND_COLUMN
    if is_mixin:
        return KIND_MIXIN
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN
    if data0_is_mixin:
        return KIND_COLUMN
    if is_masked:
        return KIND_MASKED
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED
    return KIND_COLUMN


def real_kind(col):
    """Map a real stored column object to the model kind code. Order matters:
    NdarrayMixin and MaskedColumn are both ndarray subclasses, MaskedColumn is
    a Column subclass — classify most-specific first.

    Note the model's KIND_MASKED / KIND_COLUMN codes name the column NATURE the
    selection asks for, which is exactly what the stored class reports here;
    the already-a-column arm and the masked arm both report KIND_MASKED for a
    masked input because both really do produce a masked column, and the model
    agrees on that value from either arm."""
    if isinstance(col, NdarrayMixin):
        return KIND_MIXIN
    if isinstance(col, MaskedColumn):
        return KIND_MASKED
    if isinstance(col, Column):
        return KIND_COLUMN
    # any other mixin column (Quantity, Time, ...) registers as the mixin kind
    return KIND_MIXIN


def classification_bits(data):
    """Compute the model's input booleans for a real data object, mirroring the
    repo's own probes in `_convert_data_to_col`."""
    t = Table()
    is_column = isinstance(data, Column)
    is_mixin = t._is_mixin_for_table(data)
    try:
        data0_is_mixin = t._is_mixin_for_table(data[0])
    except Exception:
        data0_is_mixin = False
    is_ndarray = isinstance(data, np.ndarray)
    is_structured = is_ndarray and len(data.dtype) > 1
    from astropy.utils.masked import Masked
    is_masked = isinstance(data, (np.ma.MaskedArray, Masked))
    is_none = data is None
    has_dtype = hasattr(data, 'dtype')
    seq_masked = False
    if (not is_none) and (not has_dtype):
        from astropy.table.column import _convert_sequence_data_to_array
        try:
            converted = _convert_sequence_data_to_array(data, None)
            seq_masked = isinstance(converted, np.ma.MaskedArray)
        except Exception:
            seq_masked = False
    # the probe the sequence-of-mixins arm itself performs (table.py:1277-1279)
    elem_cls_builds = False
    if data0_is_mixin and not is_column:
        try:
            _c = data[0].__class__(data)
            _c.info.name = 'a'
            elem_cls_builds = True
        except Exception:
            elem_cls_builds = False
    return dict(is_column=is_column, is_mixin=is_mixin,
                data0_is_mixin=data0_is_mixin,
                elem_cls_builds=elem_cls_builds, is_ndarray=is_ndarray,
                is_structured=is_structured, is_masked=is_masked,
                has_dtype=has_dtype, seq_masked=seq_masked, is_none=is_none)


def stored_kind(data):
    """Add `data` to a fresh table and read back the resulting column kind."""
    t = Table()
    t['col'] = data
    return real_kind(t['col'])


def check(data, label):
    bits = classification_bits(data)
    want = selected_kind(**bits)
    got = stored_kind(data)
    assert got == want, (
        f"{label}: real stored kind {got} != model selected_kind {want} "
        f"(bits={bits})")
    return bits, want, got


def main():
    n_checks = 0

    # --- F2P case 1: plain structured ndarray (unmasked) -> Column -----------
    a = np.array([(1, 'a'), (2, 'b'), (3, 'c'), (4, 'd')],
                 dtype='<i4,' + ('|U1'))
    b = np.array([(1, 'a'), (2, 'b'), (3, 'c'), (4, 'd')],
                 dtype=[('x', 'i4'), ('y', ('U2'))])
    c = np.rec.fromrecords([(100., 'raa'), (200., 'rbb'),
                            (300., 'rcc'), (400., 'rdd')],
                           names=['rx', 'ry'])
    d = np.arange(8, dtype='i8').reshape(4, 2)  # 2-D, NOT structured
    for data, lab in [(a, 'struct a'), (b, 'struct b'),
                      (c, 'recarray c'), (d, 'plain 2d d')]:
        bits, want, got = check(data, lab)
        if lab in ('struct a', 'struct b', 'recarray c'):
            assert bits['is_structured'] and not bits['is_column'] \
                and not bits['is_mixin'], f"{lab}: expected non-col non-mixin structured"
            assert want == KIND_COLUMN and got == KIND_COLUMN, \
                f"{lab}: unmasked structured ndarray must be a plain Column"
        n_checks += 1

    # --- F2P case 2: masked structured ndarray -> MaskedColumn ---------------
    dtype = np.dtype([('z', 'f8'), ('x', 'f8'), ('y', 'i4')])
    m = np.ma.array([(1, 2, 3), (4, 5, 6)],
                    mask=[(False, False, True), (False, True, False)],
                    dtype=dtype)
    bits, want, got = check(m, 'masked struct')
    assert bits['is_structured'] and bits['is_masked'] \
        and not bits['is_column'] and not bits['is_mixin'], \
        "masked struct: expected structured masked non-col non-mixin"
    assert want == KIND_MASKED and got == KIND_MASKED, \
        "masked structured ndarray must be a MaskedColumn"
    # and the per-field mask survives (the F2P assertion)
    t = Table(); t['a'] = m
    assert np.all(t['a']['z'].mask == [False, False])
    assert np.all(t['a']['x'].mask == [False, True])
    assert np.all(t['a']['y'].mask == [True, False])
    n_checks += 1

    # --- control: plain (non-structured) arrays still classify correctly -----
    for arr, lab in [(np.arange(5), 'int 1d'),
                     (np.ma.array([1, 2, 3], mask=[0, 1, 0]), 'masked 1d'),
                     (np.array([1.0, 2.0, 3.0]), 'float 1d')]:
        check(arr, lab)
        n_checks += 1

    # --- control: an existing column keeps its OWN column nature -------------
    # Both halves of the leading already-a-column arm, including the masked
    # half (a MaskedColumn is both a Column and a np.ma.MaskedArray, so it is
    # the case that distinguishes the arm from the masked-array arm), and a
    # user SUBCLASS, whose class the arm preserves.
    class _MyColumn(Column):
        pass

    class _MyMaskedColumn(MaskedColumn):
        pass

    for data, lab, expect in [
            (Column([1, 2, 3], name='x'), 'existing Column', KIND_COLUMN),
            (Column([], name='x'), 'empty Column', KIND_COLUMN),
            (Column(a, name='x'), 'structured Column', KIND_COLUMN),
            (_MyColumn([1, 2, 3], name='x'), 'Column subclass', KIND_COLUMN),
            (MaskedColumn([1, 2, 3], mask=[0, 1, 0], name='x'),
             'existing MaskedColumn', KIND_MASKED),
            (MaskedColumn([1, 2, 3], name='x'),
             'MaskedColumn without a mask set', KIND_MASKED),
            (MaskedColumn([], name='x'), 'empty MaskedColumn', KIND_MASKED),
            (MaskedColumn(a, name='x'), 'structured MaskedColumn', KIND_MASKED),
            (_MyMaskedColumn([1, 2, 3], mask=[0, 1, 0], name='x'),
             'MaskedColumn subclass', KIND_MASKED)]:
        bits, want, got = check(data, lab)
        assert bits['is_column'] and not bits['is_mixin'] \
            and bits['has_dtype'] and not bits['is_none'], \
            f"{lab}: the already-a-column domain facts must hold"
        assert want == expect and got == expect, \
            f"{lab}: expected kind {expect}, spec {want}, real {got}"
        n_checks += 1

    # --- control: dtype-less sequences (the unchanged conversion branch) -----
    # A plain list containing masked entries converts to a masked array and
    # must be stored as a MaskedColumn (KIND_MASKED); a plain list without
    # masked entries stays an ordinary Column. This exercises the seq_masked
    # bit of the model on real inputs.
    for seq, lab, expect in [
            ([1, np.ma.masked, 2], 'int list w/ masked entry', KIND_MASKED),
            ([1.0, np.ma.masked, 2.0], 'float list w/ masked entry', KIND_MASKED),
            (['a', np.ma.masked], 'str list w/ masked entry', KIND_MASKED),
            ([1, 2, 3], 'plain int list', KIND_COLUMN),
            (['x', 'y'], 'plain str list', KIND_COLUMN)]:
        bits, want, got = check(seq, lab)
        assert not bits['has_dtype'] and not bits['is_none'], \
            f"{lab}: expected a dtype-less non-None sequence"
        assert want == expect and got == expect, \
            f"{lab}: expected kind {expect}, spec {want}, real {got}"
        n_checks += 1

    # --- fuzz: random structured dtypes, masked and unmasked -----------------
    rng = np.random.default_rng(13236)
    field_types = ['i4', 'i8', 'f4', 'f8', 'U1', 'U3']
    for _ in range(400):
        nf = int(rng.integers(2, 5))            # >= 2 fields => structured
        names = [f'f{i}' for i in range(nf)]
        types = [field_types[int(rng.integers(len(field_types)))]
                 for _ in range(nf)]
        dt = np.dtype(list(zip(names, types)))
        nrow = int(rng.integers(1, 5))
        rows = []
        for _r in range(nrow):
            row = []
            for ty in types:
                if ty.startswith('U'):
                    row.append('ab'[: int(ty[1:])])
                elif ty.startswith('f'):
                    row.append(float(rng.integers(0, 100)))
                else:
                    row.append(int(rng.integers(0, 100)))
            rows.append(tuple(row))
        arr = np.array(rows, dtype=dt)
        bits, want, got = check(arr, 'fuzz unmasked struct')
        assert want == KIND_COLUMN and got == KIND_COLUMN
        n_checks += 1

        marr = np.ma.array(arr)
        bits, want, got = check(marr, 'fuzz masked struct')
        assert want == KIND_MASKED and got == KIND_MASKED
        n_checks += 1

    # --- fuzz: plain sequences with / without masked entries -----------------
    for i in range(50):
        n = int(rng.integers(2, 6))
        vals = [int(rng.integers(0, 100)) for _ in range(n)]
        check(list(vals), 'fuzz plain list')
        n_checks += 1
        pos = int(rng.integers(0, n))
        masked_vals = list(vals)
        masked_vals[pos] = np.ma.masked
        bits, want, got = check(masked_vals, 'fuzz masked-entry list')
        assert want == KIND_MASKED and got == KIND_MASKED
        n_checks += 1

    # --- the pre-patch divergence is real (documents what G-DIFF senses) -----
    # Under the DELETED clause a structured ndarray would have been viewed as an
    # NdarrayMixin (KIND_MIXIN); confirm that the explicit `.view(NdarrayMixin)`
    # path (which the pre-patch code performed) does produce the mixin kind, so
    # removing it genuinely changes the classification.
    a_as_mixin = a.view(NdarrayMixin)
    t2 = Table(); t2['a'] = a_as_mixin
    assert isinstance(t2['a'], NdarrayMixin), \
        "sanity: an explicit NdarrayMixin view stays a mixin (the pre-patch kind)"
    assert real_kind(t2['a']) == KIND_MIXIN
    # and the post-patch plain structured array is NOT that kind
    assert stored_kind(a) == KIND_COLUMN != KIND_MIXIN, \
        "post-patch structured ndarray must NOT be the NdarrayMixin kind"

    print(f"G-AX OK: decision-equivalence holds on {n_checks} real inputs "
          f"(F2P + controls + structured fuzz + sequence fuzz); real "
          f"_convert_data_to_col classification matches model selected_kind; "
          f"structured ndarrays are Column/MaskedColumn by mask-status, not "
          f"NdarrayMixin; masked-entry sequences are MaskedColumn. "
          f"No consumed axiom.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
