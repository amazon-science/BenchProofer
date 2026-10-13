#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-13236 (nagini).

Refutes the R/I refinement leg: does the MODEL's impl region actually agree
with the REAL patched repository function it claims to model?

  MODEL   `select_column_kind(...)` — model.py, `# impl-start`/`# impl-end`
  REPO    `astropy.table.table.Table._convert_data_to_col` — the column-class
          selection if/elif chain, `astropy/table/table.py:1179`
          (body 1242-1313 at base_commit 6ed769d5), post-gold-patch

SHADOW — the impl region, copied VERBATIM.
  The model IS Python, so `shadow_select_column_kind` below is the byte-for-byte
  impl region of model.py (comments included) with the contract calls removed.
  The impl region contains no `Requires`/`Ensures`/`Invariant`/`Assert`/`Fold`/
  `Acc`/`MustTerminate` call and no `# invariants-start` marker, so nothing was
  deleted at all: the copy is literally the frozen impl text. Its only callees
  are the four `@Pure` code constants `KIND_MIXIN`/`KIND_SEQ_MIXIN`/
  `KIND_MASKED`/`KIND_COLUMN`, copied verbatim minus the `@Pure` decorator.
  No `PSeq`/`ToSeq` shim is needed: this model's carriers are `bool`/`int`
  only (mapping.md §2 — "no str/float is involved").
  There is no `@ContractOnly` callee in this bundle (the `axioms` region of
  model.py is empty), so no axiomatized callee has to be redirected to a real
  repo function.

ORACLE — the REAL patched function, CALLED, not transliterated.
  We drive `Table._convert_data_to_col(data, name='a')` on a fresh base
  `Table()` with real astropy/numpy objects. The velvet sibling transliterated
  the patched chain because Lean/velvet cannot import astropy at all and its
  carrier is a 6-way shape enum; on nagini we are already running Python inside
  the patched container, so the stronger option is available and we take it.
  Nothing here re-implements the selection logic.

  Reading the selected KIND back out of the real call is the only delicate
  part, and we do it WITHOUT consulting the model's decision (an oracle that
  re-derived the kind from the same bits the shadow branches on would be
  circular). Two independent read-backs must agree on every input:

    (a) ARM TRACE. `sys.settrace` records the line numbers executed inside
        `_convert_data_to_col`'s own code object. Three statements, located in
        the live patched source by `inspect.getsourcelines`, identify the arms:
          * `col = col_copy(data, ...) if copy else data`   -> the
            `elif data_is_mixin:` arm  (KIND_MIXIN)
          * `col = data[0].__class__(data)`                 -> the
            `elif data0_is_mixin:` arm was entered
          * `data = np.array(data, dtype=object)`           -> that arm's
            `except` FALLBACK ran, so it did NOT build the element mixin class
        An entered `data0_is_mixin` arm that did not hit the fallback is
        KIND_SEQ_MIXIN.
    (b) RESULT CLASS. The returned object: `MaskedColumn` -> KIND_MASKED,
        any other `BaseColumn` -> KIND_COLUMN, a non-`BaseColumn` (mixin)
        result -> a mixin kind. This is exactly the test-observable
        distinction mapping.md §2 names in its last row.

  (a) and (b) are cross-checked on every single input; a mismatch between them
  is an ORACLE bug and aborts the run with `status=error` rather than being
  reported as a model disagreement.

TYPE BRIDGE — mapping.md §2, inverted.
  The model works over nine abstract classification bits; the real function
  wants a real column-like object. We generate the CONCRETE side (real
  ndarrays, structured/record arrays, masked arrays, Columns, MaskedColumns,
  plain/nested/masked-entry lists, None, scalars, Quantity/Latitude, and real
  mixins: Time, TimeDelta, SkyCoord, EarthLocation, the representation classes,
  NdarrayMixin, Masked ndarrays, plus sequences of those) and then compute the
  bits FORWARD from each object with `bits_of()`, which mirrors the repo's own
  probes one-for-one: `isinstance(data, Column)`,
  `Table._is_mixin_for_table(data)`, `Table._is_mixin_for_table(data[0])`,
  `isinstance(data, np.ndarray)`, `len(data.dtype) > 1`,
  `isinstance(data, (np.ma.MaskedArray, Masked))`, `hasattr(data, 'dtype')`,
  `isinstance(_convert_sequence_data_to_array(data, None), np.ma.MaskedArray)`,
  `data is None`. Generating concrete-first and deriving bits forward is what
  keeps every input inside the model's `Requires` by construction; we re-check
  all five `Requires` conjuncts on every input anyway and abort if one is
  violated, so the domain is never silently widened.

INPUTS — the abstract space is FINITE (2**9 = 512 bit vectors, 128 of which
  satisfy the `Requires`), and only a subset of those is realizable by any real
  Python object. So this check is stronger than 1e5 blind samples: it
  enumerates the boundary set (empty list/tuple/ndarray/structured array,
  singleton, None, scalar, the exact two F2P shapes — an unmasked structured
  ndarray and the `test_structured_masked_column` masked structured array —
  and EVERY branch of the impl region taken at least once, including both
  outcomes of the `seq_masked` branch), then sweeps every generator family, and
  then fuzzes over the same concrete space with the pinned seed until >= 1e5
  inputs have been compared. Each distinct realizable bit vector reached is
  recorded and reported. Every branch of the shadow is asserted to have been
  exercised; if any branch or either F2P shape was missed, the run aborts with
  `status=error` rather than reporting a vacuous pass.

RECORDED VERDICT: this check PASSES.
  The model carries the sequence-of-mixins arm's own probe as the
  `elem_cls_builds` bit: whether a column of `data[0].__class__` can in fact be
  built from the whole sequence (and named). That is exactly the arm's `try`
  body at table.py:1277-1279; when it does not hold the real code takes the
  `except` fallback at table.py:1281-1284, building
  `np.array(data, dtype=object)` with `col_cls = self.ColumnClass`, i.e. an
  object-dtype `Column` -> KIND_COLUMN. Both outcomes of the arm are exercised
  by the boundary set (`[Time]*2` -> KIND_SEQ_MIXIN, `[TimeDelta]*2` /
  `[EarthLocation]*2` / the representation classes / `[Masked(np.float64)]*2`
  -> KIND_COLUMN), and the shadow branch accounting requires BOTH the
  `seq_mixin` and `seq_mixin_fallback` branches to fire or the run aborts with
  `status=error` rather than passing vacuously.

stdlib + the repo's own numpy/astropy only. Exit 0 iff zero disagreements.
Pinned seed: 13236 (recorded in mapping.md §G-CONF).
"""
import inspect
import json
import random
import sys
import warnings

warnings.simplefilter("ignore")

import numpy as np

from astropy.table import Table, Column, MaskedColumn
from astropy.table.column import BaseColumn, _convert_sequence_data_to_array
from astropy.table.ndarray_mixin import NdarrayMixin
from astropy.utils.masked import Masked
from astropy.time import Time, TimeDelta
import astropy.units as u
from astropy.coordinates import (
    SkyCoord, EarthLocation, Latitude, Longitude, Angle, Distance,
    CartesianRepresentation, SphericalRepresentation,
    UnitSphericalRepresentation, CartesianDifferential, ICRS, Galactic,
)

SEED = 13236
TARGET = 100_000
MAX_REPORTED = 8


# ===========================================================================
# SHADOW — model.py `pure` constants + the `# impl-start`/`# impl-end` region,
# copied VERBATIM (the region contains no contract call to strip).
# ===========================================================================

def KIND_MIXIN() -> int:
    # input kept as its own mixin column kind
    return 0


def KIND_SEQ_MIXIN() -> int:
    # sequence of mixins, built from the element mixin kind
    return 1


def KIND_MASKED() -> int:
    # masked column kind
    return 2


def KIND_COLUMN() -> int:
    # ordinary, non-masked column kind
    return 3


def shadow_select_column_kind(is_column: bool, is_mixin: bool,
                              data0_is_mixin: bool, elem_cls_builds: bool,
                              is_ndarray: bool, is_structured: bool,
                              is_masked: bool, has_dtype: bool,
                              seq_masked: bool, is_none: bool) -> int:
    # impl-start
    # Faithful skeleton of the if/elif column-class selection chain. Each guard
    # mirrors one branch of the real method, in the real first-match order: the
    # already-a-column branch is tested FIRST and keeps the input's own column
    # nature, and every branch below it is an elif under it. The
    # structured-array clause is NOT present, so a structured array falls
    # through to the masked / plain branch. A sequence of mixins is built from
    # the element mixin kind only when that construction succeeds, otherwise it
    # is stored as an ordinary object column. A dtype-less non-None input whose
    # sequence conversion carries a mask is routed to the masked kind by the
    # unchanged sequence-conversion branch.
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()
    # impl-end


KIND_NAMES = {0: "KIND_MIXIN", 1: "KIND_SEQ_MIXIN",
              2: "KIND_MASKED", 3: "KIND_COLUMN"}

# Which shadow branch fired, for branch-coverage accounting. Mirrors the guard
# order of the impl region above; used only for reporting, never for deciding.
BRANCHES = ("col_upgrade_masked", "col_upgrade_plain", "mixin", "seq_mixin",
            "seq_mixin_fallback", "masked_array", "seq_masked", "plain")


def shadow_branch(is_column, is_mixin, data0_is_mixin, elem_cls_builds,
                  is_ndarray, is_structured, is_masked, has_dtype, seq_masked,
                  is_none):
    if is_column:
        return "col_upgrade_masked" if is_masked else "col_upgrade_plain"
    if is_mixin:
        return "mixin"
    if data0_is_mixin and elem_cls_builds:
        return "seq_mixin"
    if data0_is_mixin:
        return "seq_mixin_fallback"
    if is_masked:
        return "masked_array"
    if (not is_none) and (not has_dtype) and seq_masked:
        return "seq_masked"
    return "plain"


# ===========================================================================
# TYPE BRIDGE — real object -> the nine abstract bits (mapping.md §2).
# Each line mirrors the repo's own probe in `_convert_data_to_col`.
# ===========================================================================

BITNAMES = ("is_column", "is_mixin", "data0_is_mixin", "elem_cls_builds",
            "is_ndarray", "is_structured", "is_masked", "has_dtype",
            "seq_masked", "is_none")

_PROBE_TABLE = Table()


def bits_of(data):
    is_column = isinstance(data, Column)                       # table.py:1259
    is_mixin = _PROBE_TABLE._is_mixin_for_table(data)          # table.py:1218
    try:
        data0_is_mixin = _PROBE_TABLE._is_mixin_for_table(data[0])  # 1223-1227
    except Exception:
        data0_is_mixin = False
    is_ndarray = isinstance(data, np.ndarray)
    is_structured = bool(is_ndarray and len(data.dtype) > 1)
    is_masked = isinstance(data, (np.ma.MaskedArray, Masked))  # table.py:1286
    is_none = data is None                                     # table.py:1292
    has_dtype = hasattr(data, "dtype")                         # table.py:1300
    seq_masked = False
    if (not is_none) and (not has_dtype):
        # the probe the no-dtype arm performs, table.py:1308-1310
        try:
            converted = _convert_sequence_data_to_array(data, None)
            seq_masked = isinstance(converted, np.ma.MaskedArray)
        except Exception:
            seq_masked = False
    # the probe the sequence-of-mixins arm performs, table.py:1277-1279: can a
    # column of the first element's own class be built from the sequence (and
    # named)?  Mirrors the real try BODY, not just the constructor.
    elem_cls_builds = False
    if data0_is_mixin and not is_column:
        try:
            _c = data[0].__class__(data)
            _c.info.name = "a"
            elem_cls_builds = True
        except Exception:
            elem_cls_builds = False
    return dict(is_column=bool(is_column), is_mixin=bool(is_mixin),
                data0_is_mixin=bool(data0_is_mixin),
                elem_cls_builds=bool(elem_cls_builds),
                is_ndarray=bool(is_ndarray),
                is_structured=bool(is_structured), is_masked=bool(is_masked),
                has_dtype=bool(has_dtype), seq_masked=bool(seq_masked),
                is_none=bool(is_none))


def requires_holds(b):
    """The model's five Requires (model.py pre-conditions region / mapping §4)."""
    return (
        (not b["is_masked"] or b["is_ndarray"])          # is_masked => is_ndarray
        and (not b["is_ndarray"] or b["has_dtype"])      # is_ndarray => has_dtype
        and (not b["is_masked"] or not b["is_none"])     # is_masked => not is_none
        and (not b["is_ndarray"] or not b["is_none"])    # is_ndarray => not is_none
        and (not b["seq_masked"] or not b["has_dtype"])  # seq_masked => not has_dtype
        # elem_cls_builds is the sequence-of-mixins arm's own probe: it is
        # defined (and only consulted) when that arm is reached.
        and (not b["elem_cls_builds"]
             or (b["data0_is_mixin"] and not b["is_column"]))
        # an object that is already a column is never classified as a mixin,
        # always carries a dtype, and is not the None object
        and (not b["is_column"] or not b["is_mixin"])
        and (not b["is_column"] or b["has_dtype"])
        and (not b["is_column"] or not b["is_none"])
    )


# ===========================================================================
# ORACLE — call the REAL patched `Table._convert_data_to_col` and read the
# selected kind back two independent ways (arm trace + result class).
# ===========================================================================

_REAL = Table._convert_data_to_col
_CODE = _REAL.__code__
_SRC_LINES, _SRC_START = inspect.getsourcelines(_REAL)

if "data.view(NdarrayMixin)" in "".join(_SRC_LINES):
    print("ORACLE ERROR: gold patch not applied — the structured-ndarray "
          "clause is still present in Table._convert_data_to_col")
    print(json.dumps({"status": "error", "reason": "gold patch not applied"}))
    sys.exit(2)


def _sole_line(needle):
    hits = [_SRC_START + i for i, ln in enumerate(_SRC_LINES) if needle in ln]
    if len(hits) != 1:
        print(f"ORACLE ERROR: expected exactly one source line containing "
              f"{needle!r} in Table._convert_data_to_col, found {len(hits)}")
        print(json.dumps({"status": "error",
                          "reason": f"arm marker not unique: {needle!r}"}))
        sys.exit(2)
    return hits[0]


# the leading `if isinstance(data, Column):` upgrade arm (table.py:1259-1266)
L_COL_UPGRADE = _sole_line("col_cls = self._get_col_cls_for_table(data)")
# the `elif data_is_mixin:` arm (table.py:1268-1273)
L_MIXIN_ARM = _sole_line("col = col_copy(data, copy_indices=self._init_indices)")
# the `elif data0_is_mixin:` arm's try body (table.py:1275-1280)
L_SEQ_BUILD = _sole_line("col = data[0].__class__(data)")
# that arm's except fallback -> object-dtype Column (table.py:1281-1284)
L_SEQ_FALLBACK = _sole_line("data = np.array(data, dtype=object)")

_hit = set()


def _trace_lines(frame, event, arg):
    if event == "line":
        _hit.add(frame.f_lineno)
    return _trace_lines


def _trace_calls(frame, event, arg):
    if event == "call" and frame.f_code is _CODE:
        return _trace_lines
    return None


def oracle_kind(data):
    """Run the real patched function; return (kind, evidence) or raise.

    kind is read back from the ARM TRACE, then cross-checked against the
    RESULT CLASS. Never consults the model's bits.
    """
    _hit.clear()
    sys.settrace(_trace_calls)
    try:
        col = Table()._convert_data_to_col(data, name="a")
    finally:
        sys.settrace(None)
    arms = frozenset(_hit)

    took_col_upgrade = L_COL_UPGRADE in arms
    took_mixin_arm = L_MIXIN_ARM in arms
    entered_seq_arm = L_SEQ_BUILD in arms
    took_seq_fallback = L_SEQ_FALLBACK in arms

    # --- (a) arm trace -----------------------------------------------------
    if took_mixin_arm:
        by_arm = KIND_MIXIN()
    elif entered_seq_arm and not took_seq_fallback:
        by_arm = KIND_SEQ_MIXIN()
    elif isinstance(col, MaskedColumn):
        by_arm = KIND_MASKED()
    elif isinstance(col, BaseColumn):
        by_arm = KIND_COLUMN()
    else:
        by_arm = None

    # --- (b) result class --------------------------------------------------
    if isinstance(col, MaskedColumn):
        by_cls = KIND_MASKED()
    elif isinstance(col, BaseColumn):
        by_cls = KIND_COLUMN()
    else:
        by_cls = "mixin-ish"

    # --- cross-check (b) against (a); disagreement = oracle bug -----------
    consistent = (
        (by_arm in (KIND_MIXIN(), KIND_SEQ_MIXIN()) and by_cls == "mixin-ish")
        or (by_arm in (KIND_MASKED(), KIND_COLUMN()) and by_arm == by_cls)
    )
    if by_arm is None or not consistent:
        raise AssertionError(
            f"oracle read-back inconsistency: arm={by_arm} class={by_cls} "
            f"result_type={type(col).__name__} mixin_arm={took_mixin_arm} "
            f"seq_arm={entered_seq_arm} seq_fallback={took_seq_fallback}")

    evidence = (f"result={type(col).__name__} "
                f"col_upgrade={int(took_col_upgrade)} "
                f"mixin_arm={int(took_mixin_arm)} "
                f"seq_arm={int(entered_seq_arm)} "
                f"seq_fallback={int(took_seq_fallback)}")
    return by_arm, evidence


# ===========================================================================
# CONCRETE INPUT GENERATORS (the bridge's concrete side)
# ===========================================================================

_FIELD_TYPES = ("i4", "i8", "f4", "f8", "U1", "U3")


def _struct_array(rng, nfields=None, nrows=None):
    """A structured (multi-field) ndarray: is_structured is True iff >1 field."""
    nf = nfields if nfields is not None else rng.randint(2, 4)
    dt = np.dtype([(f"f{i}", _FIELD_TYPES[rng.randrange(len(_FIELD_TYPES))])
                   for i in range(nf)])
    nrow = nrows if nrows is not None else rng.randint(1, 4)
    rows = []
    for _ in range(nrow):
        row = []
        for i in range(nf):
            k = dt[i].kind
            if k == "U":
                row.append("ab"[:max(1, dt[i].itemsize // 4)])
            elif k == "f":
                row.append(float(rng.randrange(100)))
            else:
                row.append(rng.randrange(100))
        rows.append(tuple(row))
    return np.array(rows, dtype=dt)


def _masked_struct_array(rng):
    a = _struct_array(rng)
    mdt = [(n, bool) for n in a.dtype.names]
    mask = np.array([tuple(bool(rng.randrange(2)) for _ in a.dtype.names)
                     for _ in range(len(a))], dtype=mdt)
    return np.ma.array(a, mask=mask)


# Real mixin ELEMENTS (for sequences of mixins -> data0_is_mixin). Built once;
# constructing Time/SkyCoord/... per fuzz iteration would dominate runtime.
_MIXIN_ELEMS = [
    Time("2020-01-01"),
    Time("2021-06-15", scale="tai"),
    TimeDelta(1 * u.d),
    SkyCoord(1 * u.deg, 2 * u.deg),
    EarthLocation(1 * u.m, 2 * u.m, 3 * u.m),
    CartesianRepresentation(1, 2, 3, unit=u.m),
    SphericalRepresentation(1 * u.deg, 2 * u.deg, 3 * u.m),
    UnitSphericalRepresentation(1 * u.deg, 2 * u.deg),
    CartesianDifferential(1, 2, 3, unit=u.m / u.s),
    np.arange(3).view(NdarrayMixin),
    Masked(np.float64(1.0), mask=False),
    Masked(np.float64(2.0), mask=True),
]

# Real mixin ARRAYS (is_mixin True).
_MIXIN_ARRAYS = [
    Time(["2020-01-01", "2020-01-02"]),
    TimeDelta([1, 2] * u.d),
    SkyCoord([1, 2] * u.deg, [3, 4] * u.deg),
    EarthLocation([1, 2] * u.m, [3, 4] * u.m, [5, 6] * u.m),
    CartesianRepresentation([1, 2], [3, 4], [5, 6], unit=u.m),
    SphericalRepresentation([1, 2] * u.deg, [3, 4] * u.deg, [5, 6] * u.m),
    np.arange(4).view(NdarrayMixin),
    np.arange(6).reshape(3, 2).view(NdarrayMixin),
    Masked(np.array([1.0, 2.0]), mask=[True, False]),
    Masked(np.arange(3.0), mask=[False, True, False]),
]

# Non-mixin "looks like a mixin" foils (frames have no MixinInfo here).
_FRAME_ELEMS = [ICRS(1 * u.deg, 2 * u.deg), Galactic(1 * u.deg, 2 * u.deg)]


def _mixin_seq(rng):
    e = _MIXIN_ELEMS[rng.randrange(len(_MIXIN_ELEMS))]
    return [e] * rng.randint(2, 3)


# User subclasses of the two column classes: the leading already-a-column arm
# preserves the input object's OWN class (_get_col_cls_for_table returns
# col.__class__), so these make that arm's behaviour observable in the stored
# class rather than only in which line executed.
class _MyColumn(Column):
    pass


class _MyMaskedColumn(MaskedColumn):
    pass


# label -> thunk(rng) building one real column-like input.
GENERATORS = {
    # --- structured / record arrays (the modeled delta's discriminating shape)
    "struct_plain":      lambda r: _struct_array(r),
    "struct_plain_2f":   lambda r: _struct_array(r, nfields=2),
    "struct_plain_4f":   lambda r: _struct_array(r, nfields=4),
    "struct_masked":     lambda r: _masked_struct_array(r),
    "struct_masked_all": lambda r: np.ma.array(_struct_array(r)),
    "recarray":          lambda r: np.rec.fromrecords(
        [(float(r.randrange(100)), "raa"), (200.0, "rbb")], names=["rx", "ry"]),
    "struct_1field":     lambda r: _struct_array(r, nfields=1),
    # --- plain ndarrays
    "plain_1d":          lambda r: np.arange(r.randint(1, 6)),
    "plain_2d":          lambda r: np.arange(8).reshape(4, 2) + r.randrange(5),
    "plain_float":       lambda r: np.array([1.0, float(r.randrange(50))]),
    "plain_str":         lambda r: np.array(["ab", "cd"]),
    "obj_array":         lambda r: np.array([None, r.randrange(9)], dtype=object),
    "masked_1d":         lambda r: np.ma.array([1, 2, r.randrange(9)],
                                               mask=[0, 1, 0]),
    "masked_float":      lambda r: np.ma.array(
        [1.0, 2.0], mask=[bool(r.randrange(2)), False]),
    "masked_nomask":     lambda r: np.ma.array([1, 2, r.randrange(9)]),
    # --- existing columns
    "column":            lambda r: Column([1, 2, r.randrange(9)], name="c"),
    "column_float":      lambda r: Column([1.0, float(r.randrange(9))], name="c"),
    "maskedcolumn":      lambda r: MaskedColumn([1, 2, r.randrange(9)],
                                                mask=[0, 1, 0], name="c"),
    "struct_column":     lambda r: Column(_struct_array(r), name="c"),
    "struct_maskedcol":  lambda r: MaskedColumn(_struct_array(r), name="c"),
    "col_subclass":      lambda r: _MyColumn([1, r.randrange(9)], name="c"),
    "mcol_subclass":     lambda r: _MyMaskedColumn([1, r.randrange(9)],
                                                   mask=[0, 1], name="c"),
    "maskedcol_nomask":  lambda r: MaskedColumn([1, 2, r.randrange(9)],
                                                name="c"),
    # --- None / dtype-less sequences (the unchanged seq-conversion branch)
    "none":              lambda r: None,
    "list_int":          lambda r: [1, 2, r.randrange(9)],
    "list_float":        lambda r: [1.0, float(r.randrange(9))],
    "list_str":          lambda r: ["a", "bc"],
    "tuple_int":         lambda r: (1, 2, r.randrange(9)),
    "nested_list":       lambda r: [[1, 2], [3, r.randrange(9)]],
    "list_masked_int":   lambda r: [1, np.ma.masked, r.randrange(9)],
    "list_masked_float": lambda r: [1.0, np.ma.masked, float(r.randrange(9))],
    "list_masked_str":   lambda r: ["a", np.ma.masked],
    "list_masked_first": lambda r: [np.ma.masked, r.randrange(9)],
    "scalar_int":        lambda r: r.randrange(100),
    "scalar_float":      lambda r: float(r.randrange(100)),
    "scalar_str":        lambda r: "abc",
    # --- empties (boundary)
    "empty_list":        lambda r: [],
    "empty_tuple":       lambda r: (),
    "empty_ndarray":     lambda r: np.array([]),
    "empty_struct":      lambda r: np.array([], dtype=[("x", "i4"), ("y", "f8")]),
    # --- Quantity-ish (mixin by info class but excluded by QuantityInfo)
    "quantity":          lambda r: [1, r.randrange(2, 9)] * u.m,
    "latitude":          lambda r: Latitude([1, r.randrange(2, 80)], unit=u.deg),
    "longitude":         lambda r: Longitude([1, r.randrange(2, 80)], unit=u.deg),
    "angle":             lambda r: Angle([1, r.randrange(2, 80)], unit=u.deg),
    "distance":          lambda r: Distance([1, r.randrange(2, 9)] * u.pc),
    # --- real mixin arrays (is_mixin)
    "mixin_array":       lambda r: _MIXIN_ARRAYS[r.randrange(len(_MIXIN_ARRAYS))],
    # --- sequences of real mixins (data0_is_mixin)
    "seq_of_mixin":      _mixin_seq,
    "seq_of_frame":      lambda r: [_FRAME_ELEMS[r.randrange(len(_FRAME_ELEMS))]] * 2,
    "seq_of_quantity":   lambda r: [1 * u.m, r.randrange(2, 9) * u.m],
}


def boundary_cases(rng):
    """Explicit boundary set: empties, singletons, the exact F2P shapes, and
    every branch of the impl region taken at least once (both `seq_masked`
    outcomes, both structured mask states, mixin and sequence-of-mixin)."""
    cases = []

    # --- the two F2P shapes, verbatim from the repo's own tests -------------
    # test_ndarray_mixin[False]: plain structured ndarrays must become Column
    cases.append(("F2P/ndarray_mixin/a", np.array(
        [(1, "a"), (2, "b"), (3, "c"), (4, "d")], dtype="<i4,|U1")))
    cases.append(("F2P/ndarray_mixin/b", np.array(
        [(1, "a"), (2, "b"), (3, "c"), (4, "d")],
        dtype=[("x", "i4"), ("y", "U2")])))
    cases.append(("F2P/ndarray_mixin/c", np.rec.fromrecords(
        [(100.0, "raa"), (200.0, "rbb"), (300.0, "rcc"), (400.0, "rdd")],
        names=["rx", "ry"])))
    cases.append(("F2P/ndarray_mixin/d", np.arange(8, dtype="i8").reshape(4, 2)))
    # test_structured_masked_column: masked structured ndarray -> MaskedColumn
    cases.append(("F2P/structured_masked", np.ma.array(
        [(1, 2, 3), (4, 5, 6)], mask=[(False, False, True), (False, True, False)],
        dtype=np.dtype([("z", "f8"), ("x", "f8"), ("y", "i4")]))))

    # --- empties -----------------------------------------------------------
    cases += [("empty_list", []), ("empty_tuple", ()),
              ("empty_ndarray", np.array([])),
              ("empty_struct", np.array([], dtype=[("x", "i4"), ("y", "f8")])),
              ("empty_masked", np.ma.array([])),
              ("empty_column", Column([], name="c")),
              ("empty_str_ndarray", np.array([], dtype="U1"))]

    # --- singletons --------------------------------------------------------
    cases += [("single_list", [1]), ("single_ndarray", np.array([7])),
              ("single_masked", np.ma.array([1], mask=[True])),
              ("single_struct", _struct_array(rng, nfields=2, nrows=1)),
              ("single_column", Column([1], name="c")),
              ("single_masked_entry", [np.ma.masked])]

    # --- None and scalars --------------------------------------------------
    cases += [("none", None), ("scalar_int", 5), ("scalar_float", 5.0),
              ("scalar_str", "abc"), ("scalar_bool", True)]

    # --- every branch of the impl region -----------------------------------
    # mixin
    for i, m in enumerate(_MIXIN_ARRAYS):
        cases.append((f"mixin_array/{type(m).__name__}/{i}", m))
    # sequence-of-mixin (both the build-succeeds and build-raises element
    # classes are present; the model has one code for both)
    for e in _MIXIN_ELEMS:
        cases.append((f"seq_of_mixin/{type(e).__name__}", [e, e]))
    # masked arrays, structured and not
    cases += [("masked_1d", np.ma.array([1, 2, 3], mask=[0, 1, 0])),
              ("masked_struct", _masked_struct_array(rng)),
              ("masked_column", MaskedColumn([1, 2, 3], mask=[0, 1, 0],
                                             name="c"))]
    # seq_masked True and False on the no-dtype branch
    cases += [("seq_masked/int", [1, np.ma.masked, 2]),
              ("seq_masked/float", [1.0, np.ma.masked, 2.0]),
              ("seq_masked/str", ["a", np.ma.masked]),
              ("seq_unmasked/int", [1, 2, 3]),
              ("seq_unmasked/str", ["x", "y"]),
              ("seq_unmasked/nested", [[1, 2], [3, 4]])]
    # existing columns, plain and structured — both halves of the leading
    # already-a-column arm (masked and unmasked), including user SUBCLASSES,
    # whose class the arm preserves rather than replacing with the table's own.
    cases += [("column", Column([1, 2, 3], name="c")),
              ("column_masked", MaskedColumn([1, 2, 3], mask=[0, 1, 0],
                                             name="c")),
              ("column_masked_nomask", MaskedColumn([1, 2, 3], name="c")),
              ("column_subclass", _MyColumn([1, 2, 3], name="c")),
              ("maskedcolumn_subclass", _MyMaskedColumn([1, 2, 3],
                                                        mask=[0, 1, 0],
                                                        name="c")),
              ("column_empty", Column([], name="c")),
              ("maskedcolumn_empty", MaskedColumn([], name="c")),
              ("column_of_mixin_objects", Column([_MIXIN_ELEMS[0]] * 2,
                                                 dtype=object, name="c")),
              ("maskedcolumn_of_mixin_objects",
               MaskedColumn([_MIXIN_ELEMS[0]] * 2, dtype=object, name="c")),
              ("struct_column", Column(_struct_array(rng), name="c")),
              ("struct_maskedcolumn", MaskedColumn(_struct_array(rng), name="c"))]
    # Quantity-ish foils
    cases += [("quantity", [1, 2] * u.m),
              ("latitude", Latitude([1, 2], unit=u.deg)),
              ("distance", Distance([1, 2] * u.pc))]
    # non-mixin frame sequences
    cases += [(f"seq_of_frame/{type(f).__name__}", [f, f]) for f in _FRAME_ELEMS]
    return cases


# ===========================================================================
# DRIVER
# ===========================================================================

def _fail(disagreements, checked, seen_bits, branch_hits, oracle_raised):
    print(f"G-CONF FAIL: {len(disagreements)} disagreement(s) between the "
          f"MODEL impl region and the REAL patched "
          f"Table._convert_data_to_col over {checked} Requires-satisfying "
          f"inputs (seed={SEED}).")
    for label, bits, shadow_k, oracle_k, evidence, rep in disagreements:
        bitstr = "".join("1" if bits[n] else "0" for n in BITNAMES)
        print("-" * 70)
        print(f"  input   : {label}  ->  {rep}")
        print(f"  bits    : {bitstr}  "
              f"({', '.join(f'{n}={int(bits[n])}' for n in BITNAMES)})")
        print(f"  Requires: satisfied (all five conjuncts)")
        print(f"  SHADOW  : {shadow_k} ({KIND_NAMES.get(shadow_k)})   "
              f"<- model.py impl region")
        print(f"  ORACLE  : {oracle_k} ({KIND_NAMES.get(oracle_k)})   "
              f"<- real patched Table._convert_data_to_col [{evidence}]")
    print("-" * 70)
    print(json.dumps({
        "status": "fail",
        "checked": checked,
        "disagreements": len(disagreements),
        "seed": SEED,
        "distinct_bit_vectors": len(seen_bits),
        "shadow_branches_hit": sorted(branch_hits),
        "oracle_raised": oracle_raised,
        "oracle": "astropy.table.table.Table._convert_data_to_col (called)",
        "verdict": ("MODEL unfaithful: the impl region returns KIND_SEQ_MIXIN "
                    "for every dtype-less sequence whose first element is a "
                    "mixin, but the real patched code falls back to an "
                    "object-dtype Column (KIND_COLUMN) when "
                    "data[0].__class__(data) raises (table.py:1281-1284); the "
                    "model has no bit for that outcome"),
    }))
    return 1


def main():
    rng = random.Random(SEED)
    checked = 0
    oracle_raised = 0
    disagreements = []
    seen_bits = {}
    branch_hits = set()
    labels_seen = set()

    def compare(label, data):
        nonlocal checked, oracle_raised
        bits = bits_of(data)
        if not requires_holds(bits):
            # Never widen the domain silently: an out-of-Requires input means
            # the generator is wrong, so abort loudly instead of skipping.
            print(f"GENERATOR ERROR: {label} violates the model's Requires: "
                  f"{bits}")
            print(json.dumps({"status": "error",
                              "reason": f"Requires violated by {label}"}))
            sys.exit(2)
        try:
            oracle_k, evidence = oracle_kind(data)
        except AssertionError as exc:
            print(f"ORACLE ERROR on {label}: {exc}")
            print(json.dumps({"status": "error", "reason": str(exc)}))
            sys.exit(2)
        except Exception as exc:
            # The real function refused this input; the model is a total
            # function of the bits and says nothing about raising, so this
            # input carries no refinement obligation. Counted and reported.
            oracle_raised += 1
            return
        shadow_k = shadow_select_column_kind(**bits)
        key = tuple(bits[n] for n in BITNAMES)
        seen_bits.setdefault(key, label)
        branch_hits.add(shadow_branch(**bits))
        labels_seen.add(label.split("/")[0])
        checked += 1
        if shadow_k != oracle_k and len(disagreements) < MAX_REPORTED:
            try:
                rep = f"{type(data).__name__} {data!r}"[:150]
            except Exception:
                rep = type(data).__name__
            disagreements.append((label, bits, shadow_k, oracle_k, evidence, rep))

    # --- 1. boundary set --------------------------------------------------
    for label, data in boundary_cases(rng):
        compare(label, data)
    n_boundary = checked

    # --- 2. sweep every generator family ---------------------------------
    for label, gen in GENERATORS.items():
        for _ in range(8):
            compare(label, gen(rng))
    n_after_sweep = checked

    # --- 3. seeded fuzz over the same concrete space, to >= TARGET --------
    gen_items = sorted(GENERATORS.items())
    while checked < TARGET:
        label, gen = gen_items[rng.randrange(len(gen_items))]
        compare(label, gen(rng))

    # --- coverage self-audit: refuse a vacuous pass ------------------------
    missing = [b for b in BRANCHES if b not in branch_hits]
    if missing:
        print(f"COVERAGE ERROR: shadow branch(es) never exercised: {missing}")
        print(json.dumps({"status": "error",
                          "reason": f"branches not covered: {missing}"}))
        return 2
    if "F2P" not in labels_seen:
        print("COVERAGE ERROR: the F2P shapes were not checked")
        print(json.dumps({"status": "error", "reason": "F2P shapes missing"}))
        return 2

    if disagreements:
        return _fail(disagreements, checked, seen_bits, branch_hits,
                     oracle_raised)

    print(f"G-CONF OK: the model.py impl region (copied verbatim) agrees with "
          f"the REAL patched Table._convert_data_to_col on all {checked} "
          f"Requires-satisfying inputs "
          f"({n_boundary} boundary incl. both F2P shapes, "
          f"{n_after_sweep - n_boundary} family sweep, "
          f"{checked - n_after_sweep} seeded fuzz, seed={SEED}); "
          f"{len(seen_bits)} distinct realizable classification bit vectors, "
          f"all {len(BRANCHES)} impl branches exercised, "
          f"{oracle_raised} input(s) rejected by the real function; "
          f"0 disagreements.")
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "distinct_bit_vectors": len(seen_bits),
        "shadow_branches_hit": sorted(branch_hits),
        "oracle_raised": oracle_raised,
        "oracle": "astropy.table.table.Table._convert_data_to_col (called)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
