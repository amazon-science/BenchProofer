#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6721.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`chunkInventory`/`mergeVar`/`dedupeLast`/`mergePairs`/`mergePair`)
              transliterated to Python, over the `VarDesc` carrier: each variable
              is `(chunks, accessible, layout_readable)` where `chunks` is `None`
              (descriptor advertises no layout) or a list of `(dim, block)` pairs
              (the layout it advertises), and `layout_readable` says whether
              reading that layout back off the variable delivers it. The fold
              reads `chunks`, and on the advertising leg `layout_readable`, and
              NEVER `accessible`; it raises `inconsistent` iff two DIFFERENT
              chunked variables disagree on a shared dimension,
              `layoutUnavailable` iff an advertised layout is not delivered by
              its own read.

              A variable's own pairs are first assembled into a per-dimension
              mapping (`dedupeLast`): a variable's dimension names need NOT be
              distinct, and when one repeats, the read that yields these pairs
              overwrites rather than compares — first position, last block
              length. The must-agree rule therefore governs pairs from different
              variables only. The fuzzer below draws dimension ids WITH
              replacement so this leg is reached, not assumed away.

  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `xarray.core.common.get_chunksizes` (gold patch applied; the harness
              applies patch.diff before this runs), fed REAL
              `xarray.core.variable.Variable` objects — NOT mocks. This matters:
              the function reads a variable's layout back through
              `Variable.chunksizes`, a property that patch.diff does not touch,
              and a hand-written stand-in for it would encode the shadow's own
              assumption instead of the repo's behaviour. The six descriptor
              kinds below span the real states that property distinguishes.

There is NO A-tagged callee left symbolic in the impl region, so
`conf_skip=false`. The two sides must agree on every input: same verdict (ok vs
the inconsistency raise vs the layout-read failure) and, on the ok leg, the same
insertion-ordered inventory. Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample. The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import random
import sys

import numpy as np

from xarray.core import indexing, utils
from xarray.core.common import get_chunksizes
from xarray.core.variable import Variable
from xarray.tests import InaccessibleArray, UnexpectedDataAccess

try:  # a real dask array is used for the repeated-dimension boundary cases only
    import dask.array  # noqa: F401
    _HAVE_DASK = True
except Exception:  # pragma: no cover - the instance image ships dask
    _HAVE_DASK = False


# --- the six real descriptor kinds (mapping.md §2) ----------------------------
class _DuckChunked:
    """A duck array (the shape dask presents: `__array_function__` /
    `__array_ufunc__` / ndim / shape / dtype) that advertises `chunks`.
    `Variable.data` hands this back untouched, so reading the layout off it
    delivers the advertised pairs without materializing anything."""

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
    """A lazily-indexed storage descriptor (the shape a backend array presents:
    `ExplicitlyIndexed`, no `__array_function__`) that advertises `chunks`.
    NOT a duck array, so reading the layout back goes through the value view."""

    def __init__(self, array, chunks):
        self.array = array
        self.chunks = chunks


def _var_unchunked_accessible(dims, blocks):
    """Ordinary in-memory variable: descriptor advertises no layout."""
    return Variable(dims, np.zeros(blocks or (1,))[: np.prod(blocks or (1,))]
                    .reshape(blocks or (1,)))


def _var_unchunked_inaccessible(dims, blocks):
    """The failing scenario's shape: a lazily-indexed wrapper over a store that
    raises on any element access. Advertises no layout; values unavailable."""
    return Variable(dims, indexing.LazilyIndexedArray(
        InaccessibleArray(np.zeros(blocks or (1,)))))


def _var_chunked_readable(dims, blocks):
    """Advertises a layout AND delivers it: a duck array carrying `chunks`."""
    return Variable(dims, _DuckChunked(np.zeros(blocks),
                                       tuple((b,) for b in blocks)))


def _var_chunked_unreadable_values(dims, blocks):
    """Advertises a layout; the read does not deliver because the values cannot
    be obtained (the store raises on element access)."""
    return Variable(dims, _ChunkedNonDuck(InaccessibleArray(np.zeros(blocks)),
                                          tuple((b,) for b in blocks)))


def _var_chunked_unreadable_plain(dims, blocks):
    """Advertises a layout; the values ARE obtainable but what they carry is not
    a layout (a plain in-memory array has no chunk attribute)."""
    return Variable(dims, _ChunkedNonDuck(np.zeros(blocks),
                                          tuple((b,) for b in blocks)))


def _var_chunked_unreadable_none(dims, blocks):
    """Advertises a chunk attribute whose value is not a layout at all
    (`None` — the convention for "not chunked"), so the read cannot deliver."""
    return Variable(dims, _DuckChunked(np.zeros(blocks), None))


def _var_chunked_dask(dims, blocks):
    """Advertises a layout AND delivers it, backed by a REAL `dask.array` rather
    than a hand-written duck array -- so the boundary cases that exercise a
    repeated dimension name run against the array type the repo is actually
    written for, not against a stand-in that could encode the shadow's own
    assumption."""
    import dask.array as da

    return Variable(dims, da.from_array(np.zeros(blocks),
                                        chunks=tuple((b,) for b in blocks)))


# kind -> (builder, advertises_layout, accessible, layout_readable)
KINDS = {
    "unchunked":            (_var_unchunked_accessible,        False, True,  True),
    "unchunked_inaccessible": (_var_unchunked_inaccessible,    False, False, True),
    "chunked":              (_var_chunked_readable,            True,  True,  True),
    "chunked_no_values":    (_var_chunked_unreadable_values,   True,  False, False),
    "chunked_plain_values": (_var_chunked_unreadable_plain,    True,  True,  False),
    "chunked_none_layout":  (_var_chunked_unreadable_none,     True,  True,  False),
    "chunked_dask":         (_var_chunked_dask,                True,  True,  True),
}


def _dim_name(dim_id):
    """The bijection dimension-name <-> interned Int (mapping.md §2)."""
    return "d%d" % dim_id


# --- the R/I shadow: Solution.lean `chunkInventory`, transliterated ----------
_INCONSISTENT = ("error", "inconsistent")
_LAYOUT_UNAVAILABLE = ("error", "layoutUnavailable")


def _merge_pair(acc, dim, block):
    for (d, sz) in acc:
        if d == dim:
            if sz == block:
                return acc
            return None  # inconsistent
    return acc + [(dim, block)]


def _dedupe_last(pairs):
    """`dedupeLast`: assemble ONE variable's advertised pairs into the mapping its
    own read yields. Keyed by dimension, so a dimension the variable advertises
    more than once keeps the position of its FIRST occurrence and the block
    length of its LAST -- overwritten, never compared."""
    acc = []
    for dim, block in pairs:
        if any(d == dim for (d, _b) in acc):
            acc = [(dim, block) if d == dim else (d, b) for (d, b) in acc]
        else:
            acc = acc + [(dim, block)]
    return acc


def shadow_verdict(variables):
    """`chunkInventory variables`: fold each variable's advertised layout. A
    variable advertising none contributes nothing and is not read; one that
    advertises a layout it cannot deliver fails the whole inventory;
    `accessible` is never consulted. Each variable's own pairs are deduped into a
    mapping first, so `inconsistent` can only arise BETWEEN variables."""
    acc = []
    for chunks, _accessible, layout_readable in variables:
        if chunks is None:
            continue
        if not layout_readable:
            return _LAYOUT_UNAVAILABLE
        for dim, block in _dedupe_last(chunks):
            nxt = _merge_pair(acc, dim, block)
            if nxt is None:
                return _INCONSISTENT
            acc = nxt
    return ("ok", acc)


# --- the oracle: patch.diff's real patched get_chunksizes --------------------
_VAR_CACHE = {}


def _real_variable(kind, dim_ids, blocks):
    """A real `xarray` Variable of the given descriptor kind. Cached: variables
    are immutable values here and `get_chunksizes` only reads them, so reuse
    across inputs is observationally identical and keeps the fuzz affordable."""
    key = (kind, dim_ids, blocks)
    v = _VAR_CACHE.get(key)
    if v is None:
        dims = tuple(_dim_name(d) for d in dim_ids)
        v = KINDS[kind][0](dims, blocks)
        _VAR_CACHE[key] = v
    return v


def oracle_verdict(spec):
    """Run the real patched function on real Variables built from `spec`
    (a list of `(kind, dim_ids, blocks)`)."""
    variables = [_real_variable(*s) for s in spec]
    try:
        frozen = get_chunksizes(variables)
    except ValueError as exc:
        if "inconsistent chunks" in str(exc):
            return _INCONSISTENT
        return ("other", "ValueError: %s" % exc)
    except UnexpectedDataAccess:
        # the layout read reached the values and the store refused
        return _LAYOUT_UNAVAILABLE
    except AttributeError as exc:
        # the layout read reached the values and found no layout on them
        if "chunks" in str(exc):
            return _LAYOUT_UNAVAILABLE
        return ("other", "AttributeError: %s" % exc)
    except TypeError as exc:
        # the advertised chunk attribute was not a layout
        if "iterable" in str(exc):
            return _LAYOUT_UNAVAILABLE
        return ("other", "TypeError: %s" % exc)
    # Frozen is a Mapping; compare as insertion-ordered (dim, block) pairs,
    # translating names and block tuples back through the bijection.
    out = []
    for dim, c in frozen.items():
        if not (isinstance(dim, str) and dim.startswith("d")):
            return ("other", "unmapped dimension %r" % (dim,))
        if not (isinstance(c, tuple) and len(c) == 1):
            return ("other", "unmapped block layout %r" % (c,))
        out.append((int(dim[1:]), c[0]))
    return ("ok", out)


def carrier(spec):
    """The `List VarDesc` the shadow consumes, from the same input spec."""
    out = []
    for kind, dim_ids, blocks in spec:
        _, advertises, accessible, readable = KINDS[kind]
        pairs = list(zip(dim_ids, blocks)) if advertises else None
        out.append((pairs, accessible, readable))
    return out


BLOCKS = (1, 2, 4, 8)
UNCHUNKED = ("unchunked", "unchunked_inaccessible")
# `chunked_dask` is deliberately NOT in the random pool: it is used only in the
# boundary block, so the random stream (and therefore the pinned-seed verdict)
# does not depend on whether dask is importable.
CHUNKED = ("chunked", "chunked_no_values", "chunked_plain_values",
           "chunked_none_layout")
# dimension ids are drawn WITH replacement from this pool, so a single variable
# can advertise the same dimension twice -- the leg `dedupeLast` describes.
DIM_POOL = (0, 1, 2)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []                                                # empty -> ok []
    yield [("unchunked", (0,), (4,))]                        # one un-chunked
    yield [("unchunked_inaccessible", (0,), (4,))]           # THE discriminator: values
    yield [("unchunked_inaccessible", (0,), (4,)),           # unavailable, no layout
           ("unchunked_inaccessible", (1,), (2,))]           #   -> ok []
    yield [("chunked", (0,), (4,))]                          # one chunked -> ok [(0,4)]
    yield [("chunked", (0,), (4,)),
           ("unchunked_inaccessible", (1,), (2,))]           # chunked + skipped
    yield [("chunked", (0,), (4,)), ("chunked", (0,), (4,))]  # agreeing shared dim
    yield [("chunked", (0,), (4,)), ("chunked", (0,), (8,))]  # clashing -> inconsistent
    yield [("chunked", (0, 1), (4, 2)), ("chunked", (1, 2), (2, 8))]  # merge + agree
    yield [("chunked_no_values", (0,), (4,))]                # advertised, not delivered
    yield [("chunked_plain_values", (0,), (4,))]             # advertised, not delivered
    yield [("chunked_none_layout", (0,), (4,))]              # advertised, not a layout
    yield [("unchunked_inaccessible", (0,), (4,)),           # skip, then a failing read
           ("chunked_no_values", (1,), (2,))]
    yield [("chunked", (0,), (4,)), ("chunked", (0,), (8,)),  # first failure in scan
           ("chunked_no_values", (1,), (2,))]                #   order wins
    yield [("chunked_no_values", (1,), (2,)),
           ("chunked", (0,), (4,)), ("chunked", (0,), (8,))]

    # A variable may advertise the SAME dimension twice, and the two block
    # lengths need not agree: the read builds a mapping keyed by dimension, so it
    # overwrites (first position, last length) instead of comparing. These are
    # the boundary cases for `dedupeLast`; the last three run against a REAL
    # dask array, the shape the reported counterexample used.
    yield [("chunked", (0, 0), (4, 2))]                # repeat, disagreeing
    yield [("chunked", (0, 0), (4, 4))]                # repeat, agreeing
    yield [("chunked", (0, 1, 0), (4, 8, 2))]          # first position, last value
    yield [("chunked", (0, 0), (4, 2)),                # dedupe, then agree across
           ("chunked", (0,), (2,))]
    yield [("chunked", (0, 0), (4, 2)),                # dedupe, then clash across
           ("chunked", (0,), (4,))]
    yield [("chunked", (0,), (4,)),                    # pinned first, then dedupe
           ("chunked", (0, 0), (4, 2))]
    yield [("chunked", (0, 0), (4, 2)),                # repeat + a skipped variable
           ("unchunked_inaccessible", (1,), (2,))]
    yield [("chunked_no_values", (0, 0), (4, 2))]      # repeat under a failing read
    if _HAVE_DASK:
        yield [("chunked_dask", (0, 0), (4, 2))]       # THE reported input, real dask
        yield [("chunked_dask", (0, 1, 0), (4, 8, 2))]
        yield [("chunked_dask", (0, 0), (4, 2)),
               ("chunked_dask", (0,), (4,))]

    for _ in range(n):
        width = rng.randint(0, 5)
        spec = []
        for _ in range(width):
            if rng.random() < 0.40:
                kind = rng.choice(UNCHUNKED)
            else:
                kind = rng.choice(CHUNKED)
            k = rng.randint(1, 3)
            # WITH replacement: a variable's dimension names need not be distinct
            dim_ids = tuple(rng.choice(DIM_POOL) for _ in range(k))
            blocks = tuple(rng.choice(BLOCKS) for _ in range(k))
            spec.append((kind, dim_ids, blocks))
        yield spec


def _has_repeated_dim(spec):
    """Whether some variable in `spec` advertises one dimension more than once --
    the leg `dedupeLast` describes. Reported so the verdict shows the leg was
    reached rather than merely provided for."""
    for kind, dim_ids, _blocks in spec:
        if KINDS[kind][1] and len(set(dim_ids)) != len(dim_ids):
            return True
    return False


def main():
    rng = random.Random(6721)
    disagreements = []
    count = 0
    repeats = 0
    for spec in fuzz_inputs(100_000, rng):
        count += 1
        if _has_repeated_dim(spec):
            repeats += 1
        shadow = shadow_verdict(carrier(spec))
        oracle = oracle_verdict(spec)
        if shadow != oracle:
            disagreements.append((spec, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  vars=%r shadow=%r oracle=%r" % (v, sh, orc))
        return 1
    if not repeats:
        print("G-CONF FAIL: no input exercised a repeated dimension name, so the "
              "`dedupeLast` leg was not reached -- the fuzzer cannot refute it")
        return 1
    print("G-CONF OK: R/I shadow of buildChunkInventory agrees with patch.diff "
          "behaviour on %d inputs (seed=6721) over real xarray Variables of all "
          "%d descriptor kinds, 0 disagreements; %d of those inputs advertise a "
          "repeated dimension name (the `dedupeLast` leg)%s."
          % (count, len(KINDS), repeats,
             ", 3 of them backed by a real dask array" if _HAVE_DASK
             else " (dask unavailable, duck-array kinds only)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
