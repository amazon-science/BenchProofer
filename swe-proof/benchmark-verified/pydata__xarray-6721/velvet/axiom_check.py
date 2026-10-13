#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6721.

This bundle consumes NO axioms and references NO deep-model callee (mapping.md
§3): the chunk-inventory body is modeled DEEPLY (`chunkInventory`/`mergeVar`/
`mergePairs`/`mergePair` in Solution.lean's `pure` region). There is therefore no
axiom `ensures` to validate.

What remains to confirm is the **R-refinement** of the variable carrier
(mapping.md §2): that the `VarDesc` input bits the spec consumes faithfully
mirror the real repo facts about a `Variable`:

  (R bridge, `VarDesc.chunks`)  the chunk layout the spec reads is the one the
      variable's cheap storage descriptor advertises — `getattr(v._data,
      "chunks", None)` — and reading it NEVER materializes the values. For an
      ordinary (un-chunked) variable, and for an un-chunked variable wrapping an
      inaccessible store, this is `None` (=> `VarDesc.chunks = none`), obtained
      without touching the data.

  (R bridge, `VarDesc.layoutReadable`)  for a variable that DOES advertise a
      layout, whether reading that layout back off the variable delivers it. The
      read the repo performs is `v.chunksizes`, which zips the dims against
      `v.data.chunks` — the VALUE view, not the descriptor — so it can fail three
      distinct ways, and does: over a store that refuses element access it raises
      `UnexpectedDataAccess`; over an ordinary in-memory array the values carry no
      chunk attribute at all (`AttributeError`); and a descriptor advertising
      `chunks = None` yields a non-iterable (`TypeError`). Only a genuine duck
      array carrying a real layout delivers the advertised pairs. Checked for all
      four kinds, including that the delivered pairs EQUAL the advertised ones.

  (R bridge, the payload is a MAPPING keyed by dimension)  that read assembles its
      pairs into a mapping keyed by dimension. A variable's dimension names need
      not be distinct, and when one repeats the two block lengths need not agree:
      the mapping OVERWRITES rather than compares -- first position, last block
      length -- and raises nothing. So the must-agree rule the model applies has a
      counterpart only BETWEEN variables, which is checked to still raise. Verified
      on a duck array and on a REAL dask array with a multi-block layout.

  (R bridge, `VarDesc.chunks = none` short-circuits the read)  a variable that
      advertises no layout is never read at all, so on that leg `layoutReadable`
      is unconstrained and cannot reach the outcome. Confirmed on the real
      function: the inaccessible un-chunked variable yields the empty inventory
      without raising, which is only possible if the layout read is skipped.

  (R bridge, `VarDesc.accessible`)  the orthogonal "can the values be forced into
      memory?" fact maps to whether `v.data` raises. An ordinary variable ->
      accessible (True); a variable whose store raises on element access ->
      inaccessible (False). Checked to be independent of `layoutReadable` in both
      directions, so neither field is derivable from the other and both are
      genuinely needed.

  (non-vacuity / the modeled change is real)  for the inaccessible un-chunked
      variable, the PRE-patch predicate `hasattr(v.data, "chunks")` forces
      `v.data` and RAISES (the very crash the fix removes), whereas the POST-patch
      predicate `hasattr(v._data, "chunks")` reads the descriptor and is False
      without raising. This confirms the descriptor read is load-bearing, not
      vacuous, and that the two predicates genuinely diverge on this input.

Imports only numpy + the real xarray Variable / test fixtures the gold patch's
neighbourhood uses. Exit 0 iff every obligation holds.
"""
import inspect
import sys

import numpy as np

from xarray.core.common import get_chunksizes
from xarray.core.variable import Variable
from xarray.core import indexing, utils
from xarray.tests import InaccessibleArray, UnexpectedDataAccess


class _DuckChunked:
    """A duck array (what dask presents) advertising a chunk layout: `Variable.
    data` hands it back untouched, so the layout read delivers."""

    def __init__(self, array, chunks):
        self._array = np.asarray(array)
        self.chunks = chunks

    @property
    def ndim(self):
        return self._array.ndim

    @property
    def shape(self):
        return self._array.shape

    @property
    def dtype(self):
        return self._array.dtype

    def __array__(self, dtype=None):
        return np.asarray(self._array, dtype=dtype)

    def __array_function__(self, func, types, args, kwargs):
        raise NotImplementedError

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        raise NotImplementedError

    def __getitem__(self, key):
        return self._array[key]


class _ChunkedNonDuck(utils.NDArrayMixin, indexing.ExplicitlyIndexed):
    """A storage descriptor (what a backend presents: `ExplicitlyIndexed`, no
    `__array_function__`) advertising a chunk layout. NOT a duck array, so the
    layout read goes through the value view."""

    def __init__(self, array, chunks):
        self.array = array
        self.chunks = chunks


def _descriptor_chunks(v):
    """The post-patch read: the chunk layout the storage descriptor advertises.
    Must NOT touch the materialized values."""
    return getattr(v._data, "chunks", None)


def _layout_read(v):
    """The read the repo performs to obtain a variable's advertised layout:
    `v.chunksizes`. Returns `("ok", pairs)` when it delivers, else
    `("unreadable", <exception type name>)`."""
    try:
        sizes = v.chunksizes
    except (UnexpectedDataAccess, AttributeError, TypeError) as exc:
        return ("unreadable", type(exc).__name__)
    return ("ok", tuple(sizes.items()))


def _values_force_raises(v):
    """Whether forcing the values into memory (the pre-patch `v.data`) raises."""
    try:
        v.data  # pre-patch path: duck-array fast path else self.values
        return False
    except UnexpectedDataAccess:
        return True


def check_accessible_unchunked():
    """An ordinary numpy-backed variable: descriptor advertises no chunks
    (VarDesc.chunks = none) and the values are materializable (accessible)."""
    v = Variable(("x",), np.arange(5))
    assert _descriptor_chunks(v) is None, (
        "an un-chunked ndarray variable must advertise no descriptor chunks "
        "(VarDesc.chunks = none)")
    assert _values_force_raises(v) is False, (
        "an ordinary ndarray variable's values must be materializable "
        "(VarDesc.accessible = true)")


def check_inaccessible_unchunked():
    """The F2P fixture's variable kind: a LazilyIndexedArray over an
    InaccessibleArray. Descriptor advertises no chunks (none) and forcing the
    values raises (VarDesc.accessible = false)."""
    data = indexing.LazilyIndexedArray(InaccessibleArray(np.zeros((3, 4))))
    v = Variable(("y", "z"), data)
    # the descriptor read is total and chunk-less -- no materialization
    assert _descriptor_chunks(v) is None, (
        "the inaccessible un-chunked variable must advertise no descriptor "
        "chunks (VarDesc.chunks = none)")
    # forcing the values raises -> VarDesc.accessible = false
    assert _values_force_raises(v) is True, (
        "forcing the inaccessible variable's values must raise "
        "(VarDesc.accessible = false)")


def check_non_vacuity():
    """The descriptor read is load-bearing: on the inaccessible un-chunked
    variable the pre-patch `hasattr(v.data, "chunks")` RAISES while the post-patch
    `hasattr(v._data, "chunks")` is False without raising -- exactly the
    divergence the fix introduces."""
    data = indexing.LazilyIndexedArray(InaccessibleArray(np.zeros((2, 2))))
    v = Variable(("a", "b"), data)

    # post-patch predicate: reads the descriptor, no materialization, -> False
    post = hasattr(v._data, "chunks")
    assert post is False, "post-patch descriptor predicate must be False here"

    # pre-patch predicate: forces v.data -> raises UnexpectedDataAccess
    pre_raised = False
    try:
        hasattr(v.data, "chunks")
    except UnexpectedDataAccess:
        pre_raised = True
    assert pre_raised, (
        "pre-patch `hasattr(v.data, 'chunks')` must raise on the inaccessible "
        "variable (the crash the fix removes) -- confirms the modeled "
        "descriptor-vs-values distinction is non-vacuous")


def check_chunked_layout_delivered():
    """A duck array carrying a real layout: the descriptor advertises it AND the
    read delivers exactly those pairs (VarDesc.layoutReadable = true, and the
    `chunks` payload the spec merges is the payload the read yields)."""
    v = Variable(("x", "y"), _DuckChunked(np.zeros((4, 3)), ((4,), (3,))))
    advertised = _descriptor_chunks(v)
    assert advertised == ((4,), (3,)), "duck descriptor must advertise its layout"
    status, delivered = _layout_read(v)
    assert status == "ok", (
        "a duck array's advertised layout must be readable "
        f"(VarDesc.layoutReadable = true), got {delivered!r}")
    assert delivered == (("x", (4,)), ("y", (3,))), (
        "the delivered layout must be the advertised one, dimension by "
        f"dimension (the R bridge for VarDesc.chunks), got {delivered!r}")


def check_chunked_layout_unreadable_kinds():
    """Three real ways an advertised layout is NOT delivered by its own read --
    each mapping to VarDesc.layoutReadable = false. The advertisement itself is
    readable off the descriptor in every case, so this is a property of the READ,
    not of the advertisement."""
    cases = [
        # (variable, expected raise, why)
        (Variable(("x",), _ChunkedNonDuck(InaccessibleArray(np.zeros((4,))),
                                          ((4,),))),
         "UnexpectedDataAccess",
         "a non-duck descriptor's layout read reaches the values, which the "
         "store refuses"),
        (Variable(("x",), _ChunkedNonDuck(np.zeros((4,)), ((4,),))),
         "AttributeError",
         "a non-duck descriptor's layout read reaches obtainable values that "
         "carry no layout"),
        (Variable(("x",), _DuckChunked(np.zeros((4,)), None)),
         "TypeError",
         "a descriptor advertising `chunks = None` yields a non-iterable"),
    ]
    for v, expected, why in cases:
        assert hasattr(v._data, "chunks"), (
            f"the advertisement must be present off the descriptor ({why})")
        status, detail = _layout_read(v)
        assert status == "unreadable", (
            f"this advertised layout must NOT be delivered by its read "
            f"(VarDesc.layoutReadable = false): {why}; got {detail!r}")
        assert detail == expected, (
            f"expected the read to fail with {expected} ({why}), got {detail!r}")


def check_unadvertised_layout_never_read():
    """On the `VarDesc.chunks = none` leg the layout read is never performed, so
    `VarDesc.layoutReadable` is unconstrained there and cannot reach the outcome
    (`mergeVar_unadvertised`). Shown end-to-end on the real function, and stated
    for whichever tree this runs in: G-AX runs at base_commit by default, where
    the guard is the value-forcing one, so the expected observation depends on
    which guard the loaded source carries -- and BOTH observations establish the
    claim, because the read that is skipped is exactly the one that fails."""
    data = indexing.LazilyIndexedArray(InaccessibleArray(np.zeros((3, 4))))
    v = Variable(("y", "z"), data)
    assert _descriptor_chunks(v) is None, "this variable must advertise no layout"
    # The read itself is total and yields nothing on this leg, even though the
    # values are unavailable: `chunksizes` tests the DESCRIPTOR before reaching
    # the value view, so it returns empty rather than raising. This is what
    # `mergeVar_unadvertised` denotes -- `layoutReadable` cannot reach the outcome
    # here because the payload it would gate is empty either way.
    status, delivered = _layout_read(v)
    assert status == "ok" and delivered == (), (
        "a variable advertising no layout must read as the empty layout without "
        f"forcing its values, got {status!r} {delivered!r}")
    src = inspect.getsource(get_chunksizes)
    descriptor_guard = 'hasattr(v._data, "chunks")' in src
    if descriptor_guard:
        # the guard reads the descriptor: no layout is advertised, so the read is
        # skipped and the variable is passed over silently
        assert dict(get_chunksizes([v])) == {}, (
            "a variable advertising no layout must contribute nothing and be "
            "passed over without any read of its values")
    else:
        # the guard reads the value view instead: the read is NOT skipped, and it
        # is the very read shown to fail above -- which is what makes the
        # descriptor guard load-bearing rather than cosmetic
        raised = False
        try:
            get_chunksizes([v])
        except UnexpectedDataAccess:
            raised = True
        assert raised, (
            "with the value-forcing guard the skipped-read claim must be "
            "observably false on this variable; if it is not, the guard is not "
            "the discriminator this model says it is")


def check_layout_binding_is_the_zip():
    """`VarDesc.chunks` binds to the (dimension, block-length) pairs the READ
    yields -- `zip(v.dims, v.data.chunks)` -- not to the raw tuple the descriptor
    carries. The two differ when the descriptor advertises fewer block tuples than
    the variable has dimensions: the zip truncates, and it is the truncated pair
    list the repo merges. Binding to the zip absorbs that, so the carrier needs no
    separate arity side-condition (mapping.md §2)."""
    v = Variable(("x", "y"), _DuckChunked(np.zeros((4, 3)), ((4,), (3,))))
    status, delivered = _layout_read(v)
    assert status == "ok"
    assert delivered == tuple(zip(v.dims, v._data.chunks)), (
        "the delivered layout must be exactly the zip of dims against the "
        "descriptor's block tuples")
    # under-length advertisement: the read truncates to the shorter side
    short = Variable(("x", "y"), _DuckChunked(np.zeros((4, 3)), ((4,),)))
    status, delivered = _layout_read(short)
    assert status == "ok", "an under-length advertisement still reads cleanly"
    assert delivered == (("x", (4,)),), (
        "the read must truncate to the advertised block tuples, and it is that "
        f"truncated pair list `VarDesc.chunks` denotes, got {delivered!r}")


def check_layout_read_dedupes_repeated_dim():
    """`VarDesc.chunks`' payload is the pair list the READ yields, and that read
    builds a mapping KEYED BY DIMENSION. A variable's dimension names need not be
    distinct, and when one repeats, the two block lengths need not agree: the
    mapping OVERWRITES rather than compares -- the repeated dimension keeps the
    position of its FIRST occurrence and the block length of its LAST, and NOTHING
    is raised. So the must-agree rule belongs BETWEEN variables only; modelling it
    within one variable would describe a program that raises here, which this one
    does not (`dedupeLast`, mapping.md §1.1). Checked against a real dask array as
    well as a duck array, and end-to-end through `get_chunksizes`."""
    # (a) duck array, disagreeing repeat: overwritten, not compared
    v = Variable(("x", "x"), _DuckChunked(np.zeros((4, 2)), ((4,), (2,))))
    assert tuple(zip(v.dims, v._data.chunks)) == (("x", (4,)), ("x", (2,))), (
        "the advertised pairs must repeat the dimension -- otherwise this check "
        "is not exercising the leg it claims")
    status, delivered = _layout_read(v)
    assert status == "ok", (
        f"a repeated dimension must NOT make the read fail, got {delivered!r}")
    assert delivered == (("x", (2,)),), (
        "the read must keep the LAST block length for a repeated dimension, "
        f"overwriting the first, got {delivered!r}")
    assert dict(get_chunksizes([v])) == {"x": (2,)}, (
        "and the inventory must carry that overwritten value through, without "
        "raising an inconsistency for a within-variable repeat")

    # (b) first position, last value, with an unrelated dimension interleaved
    v3 = Variable(("x", "y", "x"),
                  _DuckChunked(np.zeros((4, 8, 2)), ((4,), (8,), (2,))))
    status, delivered = _layout_read(v3)
    assert status == "ok"
    assert delivered == (("x", (2,)), ("y", (8,))), (
        "the repeated dimension must keep the position of its FIRST occurrence "
        f"and the block length of its LAST, got {delivered!r}")

    # (c) the same, on a REAL dask array with a genuinely multi-block layout --
    # the exact shape of the reported counterexample, so the claim does not rest
    # on the hand-written duck array agreeing with dask.
    try:
        import dask.array as da
    except Exception:  # pragma: no cover - the instance image ships dask
        pass
    else:
        vd = Variable(("x", "x"),
                      da.from_array(np.zeros((4, 4)), chunks=((4,), (2, 2))))
        assert vd._data.chunks == ((4,), (2, 2))
        status, delivered = _layout_read(vd)
        assert status == "ok", f"real dask: read must not fail, got {delivered!r}"
        assert delivered == (("x", (2, 2)),), (
            "real dask: the repeated dimension must be overwritten last-wins, "
            f"got {delivered!r}")
        assert dict(get_chunksizes([vd])) == {"x": (2, 2)}, (
            "real dask: the inventory must carry the overwritten value and raise "
            "nothing")

    # (d) BETWEEN variables the must-agree rule is unchanged and DOES raise --
    # so (a)-(c) are a genuine distinction, not the absence of a check.
    a = Variable(("x",), _DuckChunked(np.zeros((4,)), ((4,),)))
    b = Variable(("x",), _DuckChunked(np.zeros((2,)), ((2,),)))
    raised = False
    try:
        get_chunksizes([a, b])
    except ValueError as exc:
        raised = "inconsistent chunks" in str(exc)
    assert raised, (
        "two DIFFERENT variables disagreeing on a shared dimension must still "
        "raise the inconsistency -- if they do not, the model's `inconsistent` "
        "leg has no counterpart at all")


def check_layout_read_independent_of_accessibility():
    """`layoutReadable` and `accessible` are independent observations: neither is
    a function of the other, so both fields are needed and neither may be dropped
    or conflated."""
    # accessible values, unreadable layout
    plain = Variable(("x",), _ChunkedNonDuck(np.zeros((4,)), ((4,),)))
    assert _values_force_raises(plain) is False, (
        "this variable's values ARE materializable (accessible = true)")
    assert _layout_read(plain)[0] == "unreadable", (
        "yet its advertised layout is not delivered (layoutReadable = false) -- "
        "so readability is not implied by accessibility")
    # inaccessible values, unreadable layout
    refuse = Variable(("x",), _ChunkedNonDuck(InaccessibleArray(np.zeros((4,))),
                                              ((4,),)))
    assert _values_force_raises(refuse) is True
    assert _layout_read(refuse)[0] == "unreadable"
    # accessible values, readable layout
    duck = Variable(("x",), _DuckChunked(np.zeros((4,)), ((4,),)))
    assert _values_force_raises(duck) is False
    assert _layout_read(duck)[0] == "ok", (
        "a duck array is both materializable and layout-readable -- so "
        "unreadability is not implied by inaccessibility either")


def main():
    check_accessible_unchunked()
    check_inaccessible_unchunked()
    check_non_vacuity()
    check_chunked_layout_delivered()
    check_chunked_layout_unreadable_kinds()
    check_unadvertised_layout_never_read()
    check_layout_binding_is_the_zip()
    check_layout_read_dedupes_repeated_dim()
    check_layout_read_independent_of_accessibility()
    print("G-AX OK: no consumed axioms; VarDesc.chunks/layoutReadable/accessible "
          "R-refinement validated against the real xarray Variable -- descriptor "
          "read (`v._data.chunks`) is chunk-less and total for ordinary AND "
          "inaccessible un-chunked variables; the layout read (`v.chunksizes`) "
          "delivers the advertised pairs for a duck array and fails in all three "
          "real ways otherwise (UnexpectedDataAccess / AttributeError / "
          "TypeError); the read yields the empty layout without forcing values "
          "when none is advertised, and binds to the zip against the dims; "
          "a dimension a variable advertises twice is overwritten last-wins by "
          "the read (duck AND real dask, no raise) while two DIFFERENT variables "
          "disagreeing on a shared dimension still raise; "
          "layout-readability and value-materializability are independent in both "
          "directions; value-forcing (`v.data`) raises only for the inaccessible "
          "variable; descriptor-vs-values divergence confirmed load-bearing "
          "(non-vacuous).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
