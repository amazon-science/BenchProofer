#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-7229 (nagini).

SHADOW — the `# impl-start` / `# impl-end` region of model.py, copied VERBATIM
below (both regions: `WhereResult.__init__` and `rebuild_attrs`) with only the
contract calls removed (`Requires` / `Ensures` / `Invariant` / `Assert` and the
`# invariants-start` / `-end` markers). No statement is renamed, reordered or
"simplified": the two `while` loops, the two regime branches, the `coord_src` /
`var_src` materializations and the final `top` selection stand exactly as
model.py has them. `PSeq` is realized by the immutable-tuple shim below and
`ToSeq` materializes one, so `coord_src` / `var_src` evaluate as they do under
Nagini. (Those two bindings are read only by the stripped `Invariant`s, so they
are dead here — they are kept anyway rather than tidied away, because verbatim
copying is the property this shadow is supposed to have.)
model.py declares no `@Pure` helpers and no `@ContractOnly` callees
(mapping.md §3: "There are no consumed @ContractOnly axioms"), so nothing is
axiomatized away — the whole shadow is executable R/I content and
`conf_skip` does NOT apply.

ORACLE — the REAL patched repo function, CALLED, not transliterated:
`xarray.core.computation.where(cond, x, y, keep_attrs=True)`
(`xarray/core/computation.py:1775` @ base_commit; the rebuild block the gold
patch adds at lines 1875-1892 is the behaviour under specification). The gate
applies patch.diff to /testbed before this script runs and PYTHONPATH=/testbed
makes the patched module importable, so the post-patch source is what executes.
Nothing about the rebuild is reimplemented here.

Two further REAL calls supply the abstraction's inputs, never its answer:
  * `where(cond, x, y, keep_attrs=False)` — the same call with metadata
    dropped — supplies only the output SKELETON (the `result.coords` and
    `result.data_vars` names and their order), which mapping.md §2 makes the
    frame the positional carriers align against. Taking it from the
    keep_attrs=False path keeps the frame independent of the rebuild under test.
  * `apply_ufunc(duck_array_ops.where, cond, x, y, join="exact",
    dataset_join="exact", dask="allowed", keep_attrs=True)` — the real upstream
    callee of `where`, invoked with `where`'s own kwargs — supplies the
    "as apply_ufunc produced it" baseline used for the unmodelled promotion
    slots (see below). Only reached in the promotion regime.

TYPE BRIDGE (mapping.md §2, inverted). Concrete inputs are built first (real
`DataArray` / `Dataset` / scalars) and the model carriers are then derived from
them with the abstraction function mapping.md §2 states, so every generated
input lands inside `rebuild_attrs`'s `Requires` by construction:
  * an attrs `dict` ↔ an opaque `int` identity, via a per-case interning table:
    `{}` ↔ 0 and distinct dict contents ↔ distinct non-zero ids (mapping.md §2:
    only mapping identity is observable, `assert_identical` compares dicts for
    equality). The SAME table interns x's mappings and the result's mappings,
    so model-level identity equality is exactly dict equality.
  * `x_attrs` ← `ident(getattr(x, "attrs", {}))`
  * `x_coord_attrs[i]` ← `ident(getattr(getattr(x, c_i, None), "attrs", {}))`
    for `c_i` the i-th name of the skeleton's `coords`
  * `x_var_attrs[i]` ← `ident(getattr(getattr(x, v_i, None), "attrs", {}))`
    for `v_i` the i-th name of the skeleton's `data_vars`
    Both resolve the level's NAME ON x, exactly as the patched callee does
    (`xarray/core/computation.py:1889` and `:1892` post-patch) — which is NOT
    the same function as "the attrs of the level x carries of that name, else
    `{}`". A name x answers with a derived view of ITSELF (`T`, `variable`,
    `real`, `imag` on a DataArray) abstracts to x's OWN whole-object mapping
    identity even though x carries no coordinate or data-var of that name;
    a name x answers with nothing, or with something carrying no mapping,
    abstracts to 0. Boundary cases below generate both groups.
  * `top_unmatched`      ← `isinstance(y, Dataset) and not isinstance(x, Dataset)`
  * `named_slot` ← index of `getattr(x, "name", None)` in the skeleton's
    `data_vars`, else -1 — so `Implies(top_unmatched, -1 <= named_slot <
    len(x_var_attrs))` holds for every case, satisfying the only `Requires`
    with content (the others are permission facts, vacuous outside Viper).
  The oracle's real `result` is abstracted the other way with the same table:
  `result.attrs` → `attrs`, `[result[c].attrs for c in result.coords]` →
  `coord_attrs`, `[result[v].attrs for v in result.data_vars]` → `var_attrs`.
  Shadow and oracle are then compared field by field, all three levels.

UNMODELLED PROMOTION SLOTS — declared, not skipped. mapping.md §3 records that
in the promotion regime the non-matching data-var slots are unconstrained
because "the gold patch leaves them as apply_ufunc produced"; the model's input
tuple carries nothing about `cond`, so those slots are outside the abstraction's
domain and the impl writes the empty mapping (0) as its placeholder. Rather than
drop the field, this check turns the documented claim into a testable one: for
`top_unmatched and j != named_slot`, the oracle's slot abstracts to 0 iff its attrs
are UNCHANGED from the real `apply_ufunc` baseline, and to -1 (never equal to
the shadow's 0) otherwise. So if the patched rebuild ever wrote anything into a
non-matching slot the comparison FAILS; only "the rebuild left it alone" passes.
Every other slot, and all three levels in the ordinary regime, are compared
directly against the real attrs. The count of slots governed by this rule is
reported.

NEGATIVE CONTROL — the check is known to be capable of failing, not merely
believed to be. Run in the same container against the UNPATCHED base (pre-patch
`where`, where `keep_attrs is True` becomes a single `lambda attrs, context:
getattr(x, "attrs", {})` handed to apply_ufunc and broadcast to every level) it
exits 1 with 23 of the 26 boundary cases disagreeing, including 6 of the 7 F2P
scenarios (then the first fuzz case disagrees too and the ">= 3 disagreements"
abort stops the sweep, so the reported totals are 24 disagreements over 27
inputs). Every family of the comparison is exercised by that control:
  * coord level — pre-patch every coord mapping comes out as x's TOP-LEVEL
    mapping instead of x's own same-coord mapping ("ord:two distinct coord
    levels", "ord:coord present in output, absent from x");
  * global level — pre-patch the promotion regime leaves x's top-level mapping
    at the output global instead of emptying it ("pro:*", shadow attrs=0 vs
    oracle attrs=x's id);
  * the unmodelled-slot rule — pre-patch the broadcast WRITES x's top-level
    mapping into non-matching promotion slots, so those slots differ from the
    apply_ufunc baseline, abstract to the -1 sentinel and disagree with the
    shadow's 0 ("pro:name absent from output", var_attrs [-1, -1]). The rule is
    therefore a real check, not a wildcard that always matches.
The 3 boundary cases that do NOT move are ones where the two behaviours
genuinely coincide, each for a stated reason: "F2P:x scalar" and
"ord:Datasets with empty mappings" — x carries only empty mappings, so the
pre-patch broadcast broadcasts `{}`, which is also what the patched per-level
rebuild computes (measured: every level of both abstracts to identity 0); and
"ord:no coords (empty coord carrier)" — the input has NO coordinate and NO
data-var level at all, so the only level is the ordinary-regime top level, which
both readings take from x's whole-object mapping. Scalar x is not a blind spot of
the control: its sibling "F2P:x and y scalar" DOES move, because with y scalar
too nothing conflicts with cond's coordinate mapping in the pre-patch merge, so
that coordinate comes out `{'attr': 'cond_coord'}` pre-patch where the patched
rebuild empties it.

DOMAIN EDGE, stated rather than hidden: when cond, x AND y are all plain
scalars the real `where` returns a bare `numpy.ndarray` — an object with no
top-level, coordinate or data-var attribute levels whatsoever — so there is no
`WhereResult` for it to abstract to and the case lies outside the bijection of
mapping.md §2, not inside it with a different answer. It is therefore excluded
from generation. This does NOT narrow the modelled behaviour: the F2P
"x and y as a scalar" scenario (`where(cond, 1, 0, keep_attrs=True)`, cond a
DataArray) still produces a real DataArray with attribute levels and IS checked
as a boundary case, and it is the case that pins the all-empty carrier.

INPUTS — the modelled space is infinite (arbitrary attribute mappings), so:
26 boundary cases first (the 7 F2P scenarios verbatim from the test patch, plus
empty-coord / no-data-var / multi-coord / coord-absent-from-x / multi-var
promotion / name-absent promotion / scalar-x promotion, plus 5 name-resolution
cases: an output level named `T` / `variable` (x answers with a derived view of
ITSELF, so the level takes x's own whole-object mapping) and `values` / `zzz`
(x answers with something carrying no mapping / with nothing, so the level takes
`{}`), and one where x ALSO carries a coordinate of the shadowed name `T` and the
derived view still wins the lookup), covering both regimes,
both `named_slot` dispositions, and empty as well as non-empty carrier lists;
then 100_000 seeded fuzz cases over the same construction. Pinned seed 7229
(recorded in mapping.md §G-CONF). A real call that raises would mean an input
outside the modelled domain: such cases are counted and make the run FAIL
rather than being silently dropped.

Exit 0 iff zero disagreements. stdlib + numpy + the repo package only.
"""
import json
import random
import sys
from typing import List  # noqa: F401  (keeps the copied `# type:` comments valid)

import numpy as np
from xarray import DataArray, Dataset
from xarray.core import duck_array_ops
from xarray.core.computation import apply_ufunc, where as repo_where

SEED = 7229
N_FUZZ = 100_000


# --------------------------------------------------------------------------
# Nagini carrier shim: PSeq is an immutable sequence; ToSeq materializes one.
# --------------------------------------------------------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(tuple(lst))


# ==========================================================================
# SHADOW: model.py's impl regions, verbatim, contracts stripped.
# ==========================================================================

class WhereResult:
    def __init__(self, attrs, coord_attrs, var_attrs):
        # impl-start
        self.attrs = attrs  # type: int
        self.coord_attrs = coord_attrs  # type: List[int]
        self.var_attrs = var_attrs  # type: List[int]
        # impl-end


def rebuild_attrs(x_attrs, x_coord_attrs, x_var_attrs, top_unmatched, named_slot):
    # impl-start
    coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]
    var_src = ToSeq(x_var_attrs)  # type: PSeq[int]
    # always fill coord attrs from the SAME source coordinate (every case)
    out_coords = []  # type: List[int]
    i = 0
    while i < len(x_coord_attrs):
        out_coords.append(x_coord_attrs[i])
        i = i + 1
    # fill sub-variable attrs per case (two cases, two loops -- each loop
    # carries a single per-element rule so the Forall trigger stays simple)
    out_vars = []  # type: List[int]
    if not top_unmatched:
        # each output sub-variable slot is the SAME-INDEX source sub-variable
        # slot.
        j = 0
        while j < len(x_var_attrs):
            out_vars.append(x_var_attrs[j])
            j = j + 1
    else:
        # the sub-variable bearing the source's name takes the source's
        # WHOLE-OBJECT mapping; the other slots are left as the upstream
        # computation produced them (modelled here as the empty mapping -- the
        # contract makes no claim about them).
        j = 0
        while j < len(x_var_attrs):
            if j == named_slot:
                out_vars.append(x_attrs)
            else:
                out_vars.append(0)
            j = j + 1
    if top_unmatched:
        top = 0
    else:
        top = x_attrs
    return WhereResult(top, out_coords, out_vars)
    # impl-end


# ==========================================================================
# TYPE BRIDGE (mapping.md §2, inverted)
# ==========================================================================

UNMODELLED = -1  # sentinel: never equal to the impl's placeholder 0
# Sentinel for a source-side carrier entry the contract does not read (the
# sub-variable carriers in the regime where the source reaches its slot through
# its NAME alone). Distinct from every interned identity and from UNMODELLED, so
# a contract that DID read one could not agree with the oracle by accident.
UNREAD = -2


class Interner:
    """attrs dict <-> opaque int identity. {} is identity 0; distinct dict
    contents get distinct non-zero identities (mapping.md §2)."""

    def __init__(self):
        self._ids = {}

    def ident(self, attrs):
        d = dict(attrs or {})
        if not d:
            return 0
        key = tuple(sorted((str(k), repr(v)) for k, v in d.items()))
        if key not in self._ids:
            self._ids[key] = len(self._ids) + 1
        return self._ids[key]


def _own_attrs(obj):
    """x's OWN top-level mapping: getattr(x, "attrs", {}) (repo expression)."""
    return getattr(obj, "attrs", {})


def _level_attrs(obj, name):
    """x's OWN mapping AT the output level's `name`, the repo expression:
    getattr(getattr(x, name, None), "attrs", {}).

    The name is resolved ON x, not looked up among the levels x carries. So the
    empty mapping comes back when x answers with nothing (the ordinary "x has no
    such level" case) or with something carrying no mapping -- but a name x
    answers with a derived view of ITSELF comes back with that view's mapping,
    i.e. x's own whole-object mapping, which is not empty. Same function as the
    patched callee's, character for character."""
    return getattr(getattr(obj, name, None), "attrs", {})


def _name_answers(obj, name):
    """Does resolving `name` on `obj` as a whole object DELIVER an answer?

    mapping.md "Domain edge 2", source side. `getattr(x, name, None)` suppresses
    only AttributeError, so a descriptor that raises anything else abandons the
    call rather than falling back to the default. Measured on the patched
    callee, `dt` on a non-datetime-like source is the only such name.
    """
    try:
        getattr(obj, name, None)
        return True
    except Exception:
        return False


def _roster_is_a_roster(result, coll):
    """Is the output's level ROSTER obtained AS a roster?

    mapping.md "Domain edge 2", output side. The ordinary branch reads the
    sub-variable roster as `getattr(result, coll, [])` after the output has
    already received the source's whole-object mapping, so on an output with no
    genuine `coll` property the value recorded under that key is walked instead.
    In domain iff the answer can be walked AND each entry names a level the
    output actually carries (then the coord loop rewrites those levels with the
    same expression and the observable result is unchanged).
    """
    try:
        got = getattr(result, coll, [])
    except Exception:
        return False
    try:
        names = list(got)
    except Exception:
        return False
    for nm in names:
        if not isinstance(nm, str):
            return False
        try:
            result[nm]
        except Exception:
            return False
    return True


def _output_frame(cond, x, y):
    """The metadata-free combination of the three arguments, and the level names
    the positional carriers align against -- or (None, why) when the arguments do
    not combine into an object carrying attribute levels at all.

    This is mapping.md "Domain edge 1", made a computed predicate instead of a
    hand-enumerated case. Whether the arguments combine, and into what shape, is
    settled by the metadata-dropping call, so asking it here keeps the frame
    independent of the rebuild under test (same call `abstract_inputs` uses).
    """
    try:
        skeleton = repo_where(cond, x, y, keep_attrs=False)
    except Exception as exc:                                  # noqa: BLE001
        return None, "arguments do not combine: %s" % (type(exc).__name__,)
    if not hasattr(skeleton, "attrs") or not hasattr(skeleton, "coords"):
        return None, ("the combination carries no attribute levels (%s)"
                      % (type(skeleton).__name__,))
    coord_names = [str(c) for c in skeleton.coords]
    var_names = [str(v) for v in getattr(skeleton, "data_vars", [])]
    return (skeleton, coord_names, var_names), None


def _interrogated_names(coord_names, var_names, top_unmatched):
    """The level names the rebuild actually asks the SOURCE about.

    Every regime asks about the output's coordinate names. Only the ordinary
    regime asks about the output's sub-variable names; the promotion regime
    routes the source's whole-object mapping to the slot bearing the source's
    NAME without interrogating the source under any sub-variable name at all.
    Getting this split right matters in BOTH directions: treating the promotion
    regime as if it interrogated its sub-variable names would exclude calls the
    real callee completes, which would be narrowing the claim rather than
    stating it (measured: a promoted source NAMED for a declining accessor
    delivers, global {} and its own slot carrying its whole-object mapping).
    """
    if top_unmatched:
        return list(coord_names)
    return list(coord_names) + list(var_names)


def in_modelled_domain(cond, x, y, coord_names, var_names, top_unmatched):
    """The exact admissibility predicate of mapping.md "Domain edge 2".

    Validated differentially against the patched callee over 6174 constructed
    calls spanning both regimes, every operand as the carrier of a roster-named
    mapping key, `Variable` operands, `Dataset` sub-variables named for object
    properties, and 23 output coordinate names drawn from the accessor /
    property vocabulary: 5638 in-domain with 0 clause failures, 536 excluded of
    which 536 genuinely failed to deliver, 0 predicted-admissible-but-raised,
    0 excluded-but-delivered. Returns (ok, reason).
    """
    for nm in _interrogated_names(coord_names, var_names, top_unmatched):
        if not _name_answers(x, nm):
            return False, "source name %r declines to answer" % (nm,)
    if not top_unmatched:
        probe = _roster_probe(cond, x, y)
        if probe is not None and not _roster_is_a_roster(probe, "data_vars"):
            return False, "sub-variable roster diverted to a bogus roster"
    return True, None


def _roster_probe(cond, x, y):
    """The output as it stands when the roster is read: the metadata-dropping
    skeleton carrying the source's whole-object mapping. Built from
    keep_attrs=False so it is independent of the rebuild under test."""
    try:
        skel = repo_where(cond, x, y, keep_attrs=False)
    except Exception:
        return None
    try:
        skel = skel.copy()
        skel.attrs = dict(_own_attrs(x))
    except Exception:
        return None
    return skel


def _carried_level_attrs(obj, name):
    """The OTHER, WRONG reading of the same phrase, kept only to measure where
    it differs: the attrs of the level `obj` carries under that name, else the
    empty mapping. Never used in the comparison -- `_level_attrs` is."""
    try:
        if (name in getattr(obj, "coords", {})
                or name in getattr(obj, "data_vars", {})):
            return dict(obj[name].attrs or {})
    except Exception:
        pass
    return {}


def abstract_inputs(cond, x, y, itn, frame=None):
    """Concrete (cond, x, y) -> the model's argument tuple, plus the skeleton
    level names the positional carriers align against.

    `frame` is the already-computed `_output_frame` triple. It is passed in
    rather than recomputed so that admissibility is decided BEFORE any
    name-resolving abstraction step runs: the carriers themselves are only
    defined on admissible calls (`x_coord_attrs[i]` resolves the level's name on
    the source, which is one of the interrogations that can decline), so
    computing them first would let an inadmissible call surface as a harness
    error instead of as the exclusion it is.
    """
    if frame is None:
        got, why = _output_frame(cond, x, y)
        if got is None:
            raise ValueError("no output frame: %s" % (why,))
        frame = got
    skeleton, coord_names, var_names = frame

    x_attrs = itn.ident(_own_attrs(x))
    x_coord_attrs = [itn.ident(_level_attrs(x, c)) for c in coord_names]
    top_unmatched = isinstance(y, Dataset) and not isinstance(x, Dataset)
    if top_unmatched:
        # No name-to-mapping question is put to the source at the sub-variable
        # level in this regime (the source reaches its slot through its NAME
        # alone), so only the LENGTH of this carrier carries information and the
        # contract reads none of its entries. Resolving the names anyway would
        # not merely be wasted work: it would resolve names the routine never
        # resolves, and a name that declines only when asked would then be
        # mistaken for an inadmissible input -- narrowing the claim to exclude a
        # shape the specified behaviour covers. `UNREAD` is a value the contract
        # cannot be reading; if a future edit ever did read one, the comparison
        # would fail loudly rather than agree by luck.
        x_var_attrs = [UNREAD] * len(var_names)
    else:
        x_var_attrs = [itn.ident(_level_attrs(x, v)) for v in var_names]
    x_name = getattr(x, "name", None)
    named_slot = var_names.index(x_name) if x_name in var_names else -1
    return (x_attrs, x_coord_attrs, x_var_attrs, top_unmatched, named_slot,
            coord_names, var_names)


def abstract_result(result, coord_names, var_names, top_unmatched, named_slot,
                    cond, x, y, itn, stats):
    """The oracle's real result -> the model's output carriers."""
    attrs = itn.ident(result.attrs)
    coord_attrs = [itn.ident(result[c].attrs) for c in coord_names]

    baseline = None
    var_attrs = []
    for j, v in enumerate(var_names):
        observed = dict(result[v].attrs or {})
        if top_unmatched and j != named_slot:
            # Outside the abstraction's domain (mapping.md §3: left as
            # apply_ufunc produced it). Abstracts to the impl's placeholder 0
            # iff the rebuild really did not touch it; otherwise to a sentinel
            # that forces a disagreement.
            if baseline is None:
                baseline = apply_ufunc(
                    duck_array_ops.where, cond, x, y,
                    join="exact", dataset_join="exact", dask="allowed",
                    keep_attrs=True,
                )
            stats["unmodelled_slots"] += 1
            untouched = observed == dict(baseline[v].attrs or {})
            var_attrs.append(0 if untouched else UNMODELLED)
        else:
            var_attrs.append(itn.ident(observed))
    return attrs, coord_attrs, var_attrs


# ==========================================================================
# INPUT CONSTRUCTION
# ==========================================================================

# `data_vars` and `coords` are the level-ROSTER names: an attrs key of that name
# on an operand is what diverts a whole-object roster lookup (mapping.md
# "Domain edge 2"). They are in the vocabulary so the generator REACHES the
# excluded class -- both its failing members and its benign ones -- instead of
# the gate passing because it never draws the key.
_ROSTER_KEYS = ["data_vars", "coords"]
_KEYS = ["attr", "long_name", "units", "standard_name"] + _ROSTER_KEYS
# Ordinary mapping values: opaque payloads, only ever compared for identity.
_VALS = ["cond_da", "x_da", "y_da", "x_coord", "y_coord", "deg", 1, 2, 7]
# Roster-key values, drawn ONLY for the roster keys, chosen so those keys land on
# both sides of the domain line: rosters of names the output does carry ("a" --
# benign, still in domain, and the observable result must be unchanged) and
# answers it cannot walk or that name levels it does not carry (a bare str
# iterates per character; "zz" is absent; 5 is not iterable; [] and {"a": 1} are
# walkable but reshape the metadata-free combination, so the arguments no longer
# form an output at all). Kept separate from `_VALS` because these same payloads
# are ALSO reached, through a different route, as the data of a constructed
# operand -- mixing the pools made the generator fail to build its own inputs and
# report harness errors instead of exercising the class.
_ROSTER_VALS = ["a", ["a"], ("a",), "zz", ["zz"], ["x"], 5, 1, [], {"a": 1},
                None, True]


def rattrs(rng, allow_empty=True):
    n = rng.randint(0 if allow_empty else 1, 2)
    keys = rng.sample(_KEYS, n)
    return {k: rng.choice(_ROSTER_VALS if k in _ROSTER_KEYS else _VALS)
            for k in keys}


def da1(vals, name=None, top=None, ca=None, extra=None, extra_attrs=None):
    """A 1-D DataArray over the dimension coordinate "a" (the F2P shape)."""
    d = DataArray(vals, coords={"a": [0, 1]}, attrs=dict(top or {}), name=name)
    d["a"].attrs = dict(ca or {})
    if extra is not None:
        d = d.assign_coords({extra: ("a", [7, 8])})
        d[extra].attrs = dict(extra_attrs or {})
        d.attrs = dict(top or {})
    return d


def da2(vals, top=None, ca=None, cb=None, name=None):
    """A 2-D DataArray: two coordinate levels, so a coord-by-coord rule and a
    broadcast-the-top-level rule cannot coincide."""
    d = DataArray(np.array(vals).reshape(2, 2), coords={"a": [0, 1], "b": [0, 1]},
                  dims=("a", "b"), attrs=dict(top or {}), name=name)
    d["a"].attrs = dict(ca or {})
    d["b"].attrs = dict(cb or {})
    return d


def nodim(vals, top=None, name=None):
    """No coordinates at all -> the empty coord-carrier boundary."""
    return DataArray(vals, dims="x", attrs=dict(top or {}), name=name)


def boundary_inputs():
    # --- the 7 F2P scenarios, verbatim from the test patch -----------------
    cond = da1([True, False], top={"attr": "cond_da"}, ca={"attr": "cond_coord"})
    x = da1([1, 1], top={"attr": "x_da"}, ca={"attr": "x_coord"})
    y = da1([0, 0], top={"attr": "y_da"}, ca={"attr": "y_coord"})
    yield cond, x, y, "F2P:3 DataArrays"
    yield cond, 0, y, "F2P:x scalar"
    yield cond, x, 0, "F2P:y scalar"
    yield cond, 1, 0, "F2P:x and y scalar"
    yield True, x, y, "F2P:cond scalar"
    ds_x = Dataset(data_vars={"x": x}, attrs={"attr": "x_ds"})
    ds_y = Dataset(data_vars={"x": y}, attrs={"attr": "y_ds"})
    yield cond, ds_x, ds_y, "F2P:DataArray + 2 Datasets"
    yield cond, x.rename("x"), ds_y, "F2P:promotion (2 DataArrays + 1 Dataset)"

    # --- ordinary regime, structural boundaries ---------------------------
    yield (nodim([True, False], top={"attr": 1}), nodim([1, 1], top={"attr": 2}),
           nodim([0, 0], top={"attr": 7}), "ord:no coords (empty coord carrier)")
    yield (da2([True, False, True, False], top={"attr": 1}, ca={"attr": 2},
               cb={"units": "deg"}),
           da2([1, 1, 1, 1], top={"attr": "x_da"}, ca={"attr": "x_coord"},
               cb={"units": 1}),
           da2([0, 0, 0, 0], top={"attr": "y_da"}, ca={"attr": "y_coord"},
               cb={"units": 2}),
           "ord:two distinct coord levels")
    yield (cond, da1([1, 1], top={"attr": "x_da"}, ca={}), y,
           "ord:x coord mapping empty, x top-level non-empty")
    yield (cond, da1([1, 1], top={}, ca={"attr": "x_coord"}), y,
           "ord:x top-level empty, x coord mapping non-empty")
    yield (cond, y, da1([0, 0], top={}, ca={}, extra="extra",
                        extra_attrs={"attr": "y_extra"}),
           "ord:coord present in output, absent from x")

    # --- name resolution: the level's NAME is resolved ON x ------------------
    # `T` / `variable` are answered with a derived view of x ITSELF, so those
    # coordinate levels take x's OWN whole-object mapping and are NOT empty even
    # though x carries no coordinate of that name; `values` is answered with an
    # ndarray (no mapping of its own) and `zzz` with nothing, so those take the
    # empty mapping. The "attrs of the level x carries of that name, else {}"
    # reading disagrees with the callee on the first group and agrees on the
    # second, so these cases discriminate between the two.
    for nm in ("T", "variable", "values", "zzz"):
        yield (cond, x, da1([0, 0], top={"attr": "y_da"}, ca={"attr": "y_coord"},
                            extra=nm, extra_attrs={"attr": "y_" + nm}),
               "ord:level name resolved on x (%r)" % (nm,))
    # ...and with x ALSO carrying a coordinate of the shadowing name: the derived
    # view still wins the lookup, so that level does NOT take the coordinate's
    # own mapping.
    yield (cond,
           da1([1, 1], top={"attr": "x_da"}, ca={"attr": "x_coord"},
               extra="T", extra_attrs={"attr": "x_T_coord"}),
           da1([0, 0], top={"attr": "y_da"}, ca={"attr": "y_coord"},
               extra="T", extra_attrs={"attr": "y_T"}),
           "ord:x carries the coord the derived-view lookup shadows")
    yield (da1([True, False], top={"attr": 1}, ca={"attr": 2}), 1, 0,
           "ord:x scalar (all-empty carriers)")
    # NOTE: where(True, 1, 0) is deliberately absent -- it returns a bare
    # ndarray with no attribute levels at all, so it has no WhereResult image
    # under the mapping.md §2 bijection (see the DOMAIN EDGE note above).
    ds_x2 = Dataset(data_vars={"x": da1([1, 1], top={"attr": "x_da"},
                                        ca={"attr": "x_coord"}),
                              "z": da1([2, 2], top={"units": "deg"})},
                    attrs={"attr": "x_ds"})
    ds_y2 = Dataset(data_vars={"x": da1([0, 0], top={"attr": "y_da"}),
                               "z": da1([9, 9], top={"units": 7})},
                    attrs={"attr": "y_ds"})
    yield cond, ds_x2, ds_y2, "ord:two Datasets, two data vars each"
    yield (cond, ds_x2, da1([0, 0], top={"attr": "y_da"}),
           "ord:x Dataset, y DataArray (no promotion)")
    yield (cond, Dataset(data_vars={"x": da1([1, 1], top={})}, attrs={}),
           Dataset(data_vars={"x": y}, attrs={}),
           "ord:Datasets with empty mappings")

    # --- promotion regime, structural boundaries --------------------------
    ds_multi = Dataset(data_vars={"x": da1([0, 0], top={"attr": "y_da"}),
                                  "z": da1([9, 9], top={"units": 7})},
                       attrs={"attr": "y_ds"})
    yield (cond, x.rename("x"), ds_multi,
           "pro:multi var, named_slot=0 (non-matching slot unmodelled)")
    yield (cond, x.rename("z"), ds_multi,
           "pro:multi var, named_slot=1")
    yield (cond, x.rename("q"), ds_multi,
           "pro:name absent from output (named_slot=-1)")
    yield (cond, 5, ds_multi, "pro:x scalar (named_slot=-1)")
    yield (cond, x.rename("x"), Dataset(data_vars={"x": y}, attrs={}),
           "pro:single var, y Dataset with empty global mapping")


_PRO_NAMES = ["x", "z", "q", None]


def fuzz_inputs(rng, n):
    for _ in range(n):
        shape = rng.randint(0, 7)
        if shape == 0:                                    # 3 DataArrays
            yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)),
                   da1([1, 1], top=rattrs(rng), ca=rattrs(rng)),
                   da1([0, 0], top=rattrs(rng), ca=rattrs(rng)), "fuzz:3da")
        elif shape == 1:                                  # x scalar
            yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)),
                   rng.choice([0, 1, 5]),
                   da1([0, 0], top=rattrs(rng), ca=rattrs(rng)), "fuzz:xscalar")
        elif shape == 2:                                  # y and/or cond scalar
            xx = da1([1, 1], top=rattrs(rng), ca=rattrs(rng))
            if rng.random() < 0.5:
                yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)), xx,
                       rng.choice([0, 1, 5]), "fuzz:yscalar")
            else:
                yield (True, xx, da1([0, 0], top=rattrs(rng), ca=rattrs(rng)),
                       "fuzz:condscalar")
        elif shape == 3:                                  # two coord levels
            yield (da2([True, False, True, False], top=rattrs(rng),
                       ca=rattrs(rng), cb=rattrs(rng)),
                   da2([1, 1, 1, 1], top=rattrs(rng), ca=rattrs(rng),
                       cb=rattrs(rng)),
                   da2([0, 0, 0, 0], top=rattrs(rng), ca=rattrs(rng),
                       cb=rattrs(rng)), "fuzz:2coords")
        elif shape == 4:                                  # coord only on one side
            # the extra level's name is drawn from names x answers with a derived
            # view of itself ("T", "variable", "real", "imag"), names it answers
            # with something carrying no mapping ("values"), and names it answers
            # with nothing ("extra", "zzz") -- so the name-resolution rule is
            # fuzzed, not just pinned by the boundary cases.
            enm = rng.choice(["extra", "zzz", "T", "variable", "real", "imag",
                              "values"])
            xx = da1([1, 1], top=rattrs(rng), ca=rattrs(rng))
            yy = da1([0, 0], top=rattrs(rng), ca=rattrs(rng),
                     extra=enm, extra_attrs=rattrs(rng))
            if rng.random() < 0.5:
                xx = xx.assign_coords({enm: ("a", [7, 8])})
                xx[enm].attrs = rattrs(rng)
            yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)), xx, yy,
                   "fuzz:extracoord")
        elif shape == 5:                                  # ordinary, Datasets
            names = ["x"] + (["z"] if rng.random() < 0.5 else [])
            dsx = Dataset(
                data_vars={nm: da1([1, 1], top=rattrs(rng),
                                   ca=rattrs(rng) if nm == "x" else None)
                           for nm in names},
                attrs=rattrs(rng))
            dsy = Dataset(data_vars={nm: da1([0, 0], top=rattrs(rng))
                                     for nm in names}, attrs=rattrs(rng))
            if rng.random() < 0.25:                       # x Dataset, y DataArray
                yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)), dsx,
                       da1([0, 0], top=rattrs(rng), ca=rattrs(rng)),
                       "fuzz:xds+yda")
            else:
                yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)),
                       dsx, dsy, "fuzz:2ds")
        else:                                             # promotion
            names = ["x"] + (["z"] if rng.random() < 0.5 else [])
            dsy = Dataset(data_vars={nm: da1([0, 0], top=rattrs(rng))
                                     for nm in names}, attrs=rattrs(rng))
            nm = rng.choice(_PRO_NAMES)
            xx = da1([1, 1], top=rattrs(rng), ca=rattrs(rng), name=nm)
            if nm is None and rng.random() < 0.3:
                xx = rng.choice([0, 1, 5])                # scalar x, promotion
            yield (da1([True, False], top=rattrs(rng), ca=rattrs(rng)), xx, dsy,
                   "fuzz:promotion")


# ==========================================================================
# DRIVER
# ==========================================================================

def _excluded(cond, x, y, label, why, stats, disagreements):
    """Record an out-of-domain call -- and CROSS-CHECK the exclusion.

    An out-of-domain call is never allowed to masquerade as a passing in-domain
    one, and equally the exclusion is never allowed to grow into a narrowing of
    the claim: if the real callee DELIVERS a result on a call the predicate
    excluded, that is recorded as a disagreement and the gate FAILS. So both
    error directions of the domain statement are enforced by this gate rather
    than assumed.
    """
    stats["out_of_domain"] += 1
    try:
        repo_where(cond, x, y, keep_attrs=True)
    except Exception:                                         # noqa: BLE001
        return                          # correctly excluded: really does fail
    disagreements.append({
        "case": label,
        "kind": "excluded-but-delivered",
        "reason": why,
        "note": "the domain predicate excluded a call the real callee "
                "completes; the domain restriction is narrowing the claim",
    })


def compare(cond, x, y, label, stats, disagreements):
    itn = Interner()

    # Domain FIRST, abstraction second. The carriers are only defined on
    # admissible calls, so admissibility is settled before anything that
    # resolves a level name on the source runs. Both domain edges are computed
    # predicates here, not hand-listed cases.
    frame, why = _output_frame(cond, x, y)
    if frame is None:
        _excluded(cond, x, y, label, why, stats, disagreements)
        return
    _skeleton, coord_names, var_names = frame
    top_unmatched = isinstance(y, Dataset) and not isinstance(x, Dataset)
    ok_domain, why = in_modelled_domain(cond, x, y, coord_names, var_names,
                                        top_unmatched)
    if not ok_domain:
        _excluded(cond, x, y, label, why, stats, disagreements)
        return

    (x_attrs, x_coord_attrs, x_var_attrs, top_unmatched, named_slot,
     coord_names, var_names) = abstract_inputs(cond, x, y, itn, frame=frame)

    # Requires of rebuild_attrs (the only clause with content outside Viper).
    assert (not top_unmatched) or (-1 <= named_slot < len(x_var_attrs)), \
        "generated input violates Requires: %r" % (label,)

    shadow = rebuild_attrs(x_attrs, list(x_coord_attrs), list(x_var_attrs),
                           top_unmatched, named_slot)
    result = repo_where(cond, x, y, keep_attrs=True)
    o_attrs, o_coord_attrs, o_var_attrs = abstract_result(
        result, coord_names, var_names, top_unmatched, named_slot,
        cond, x, y, itn, stats)

    stats["regime_promote" if top_unmatched else "regime_ordinary"] += 1
    # cases on which the two readings of "x's mapping at this level" DIFFER, so
    # the abstraction's choice of `_level_attrs` (name resolved ON x, the
    # callee's own expression) is load-bearing rather than incidental.
    # Only over the names the routine actually asks about -- the same split the
    # domain predicate uses, so this statistic cannot resolve a name the routine
    # never resolves.
    if any(dict(_level_attrs(x, n) or {}) != _carried_level_attrs(x, n)
           for n in _interrogated_names(coord_names, var_names, top_unmatched)):
        stats["name_resolved_on_x"] += 1
    if not coord_names:
        stats["empty_coord_carrier"] += 1
    if var_names:
        stats["with_data_vars"] += 1
    if top_unmatched and named_slot >= 0:
        stats["promoted_named"] += 1
    if top_unmatched and named_slot < 0:
        stats["promoted_nameless"] += 1

    if (shadow.attrs != o_attrs or shadow.coord_attrs != o_coord_attrs
            or shadow.var_attrs != o_var_attrs):
        disagreements.append({
            "case": label,
            "model_input": {"x_attrs": x_attrs, "x_coord_attrs": x_coord_attrs,
                            "x_var_attrs": x_var_attrs, "top_unmatched": top_unmatched,
                            "named_slot": named_slot,
                            "coords": coord_names, "data_vars": var_names},
            "concrete_input": {"cond": repr(cond), "x": repr(x), "y": repr(y)},
            "shadow": {"attrs": shadow.attrs,
                       "coord_attrs": list(shadow.coord_attrs),
                       "var_attrs": list(shadow.var_attrs)},
            "oracle": {"attrs": o_attrs, "coord_attrs": o_coord_attrs,
                       "var_attrs": o_var_attrs},
            "oracle_raw": {
                "attrs": dict(result.attrs),
                "coord_attrs": {c: dict(result[c].attrs) for c in coord_names},
                "var_attrs": {v: dict(result[v].attrs) for v in var_names}},
        })


def main():
    rng = random.Random(SEED)
    stats = {"regime_ordinary": 0, "regime_promote": 0, "unmodelled_slots": 0,
             "empty_coord_carrier": 0, "with_data_vars": 0,
             "promoted_named": 0, "promoted_nameless": 0,
             "name_resolved_on_x": 0, "out_of_domain": 0}
    disagreements = []
    errors = []
    count = 0

    def run_case(cond, x, y, label):
        nonlocal count
        count += 1
        try:
            compare(cond, x, y, label, stats, disagreements)
        except Exception as exc:                          # outside the domain
            errors.append({"case": label, "error": "%s: %s"
                           % (type(exc).__name__, exc)})

    for cond, x, y, label in boundary_inputs():
        run_case(cond, x, y, label)
    n_boundary = count
    for cond, x, y, label in fuzz_inputs(rng, N_FUZZ):
        run_case(cond, x, y, label)
        if len(disagreements) >= 3 or len(errors) >= 3:
            break

    for d in disagreements:
        print("DISAGREEMENT %s" % json.dumps(d, default=repr, sort_keys=True))
    for e in errors:
        print("ERROR %s" % json.dumps(e, sort_keys=True))

    ok = not disagreements and not errors
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "pydata__xarray-7229",
        "backend": "nagini",
        "status": "pass" if ok else "fail",
        "shadow": "model.py impl region (verbatim, contracts stripped)",
        "oracle": "xarray.core.computation.where(cond, x, y, keep_attrs=True) "
                  "(real patched repo function, called)",
        "inputs": count,
        "boundary": n_boundary,
        "fuzz": count - n_boundary,
        "seed": SEED,
        "disagreements": len(disagreements),
        "errors": len(errors),
        "coverage": stats,
    }, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
