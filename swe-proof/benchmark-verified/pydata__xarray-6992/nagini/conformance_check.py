#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6992 (nagini).

SHADOW  — the impl regions of `model.py` copied VERBATIM below with the
          contract statement lines (Requires/Ensures) stripped; the model IS
          Python, so no transliteration.  The model's carrier `PSet[int]`
          becomes a thin frozenset shim (`PSetShim`) whose `+` is union and
          `-` is difference — exactly the two PSet operators the impl region
          uses — so the impl bodies of `promote_to_index` / `teardown_index`
          and the `State` record copy over character-for-character.  There
          are no @ContractOnly callees (mapping.md §3: the behaviour is
          modelled deeply; no axiom).

ORACLE  — the REAL patched repo methods the model models (mapping.md §1):
            `xarray.core.dataset.Dataset.set_index`   <-> `promote_to_index`
            `xarray.core.dataset.Dataset.reset_index` <-> `teardown_index`
          The gate applies the gold diff to /testbed before this script runs
          (PYTHONPATH=/testbed); this script never applies any diff itself.

BRIDGE  — mapping.md §2's type abstraction: each name collection of a real
          Dataset maps to a set of integer name ids via a per-run name<->id
          registry (a bijection on the names actually seen):
            variables   <-> keyset of ds._variables
            coord_names <-> ds._coord_names
            indexes     <-> keyset of ds._indexes
            index_repr  <-> {k : isinstance(ds._variables[k], IndexVariable)}
          The model's input channels are derived from the real call exactly
          as mapping.md documents the repo data flow:
            promote:  promoted_names        = the names passed for promotion
                      displaced_index_coords = union over [dim]+names of
                        xindexes.get_all_coords(key, errors="ignore"),
                        restricted to the input index names
                      new_index_vars        = the result's index names
            teardown: dropped_coords   = variables_in  - variables_out
                      new_index_vars   = indexes_out   - indexes_in
                      converted_coords = (indexes_in - indexes_out)
                                         - dropped_coords - new_index_vars
          (structural reads of input/output, not back-derived per collection:
          the four-way equality check below is what would catch a wrong
          recomputation).  Every generated scenario is checked against the
          model's Requires (well-formed input; promoted names have stored
          arrays and are part of the new index; torn-down names are existing
          index coords; the three fates are pairwise disjoint) — a derived
          channel tuple violating a Requires counts as a disagreement, since
          the generator only emits scenarios inside the modeled domain.
          Scenario shapes the real method rejects up front with ValueError
          (e.g. a dimension-length mismatch) never reach the modeled
          recomputation and are skipped without counting; single-name
          promotions that rename the coordinate to the dimension are not
          generated (the renamed-name case is outside the Requires domain:
          the promoted name is not part of the resulting index's names).

Inputs: a boundary battery (the issue's chained promote-then-teardown
scenario, the de-indexed-coordinate promotion, the 2-level and 3-level
teardown grids over every drop/convert combination, the plain single-index
teardown) plus seeded fuzz over randomly shaped small datasets (0-3 index
levels, extra coordinates and data variables, random promote/teardown
choices) until >= 1e5 Requires-satisfying scenarios are checked.
Pinned fuzz seed: 6992.  Exit 0 iff zero disagreements; on disagreement
print the scenario and both outcomes and exit 1.
stdlib + numpy + pandas + xarray (the repo under test and its own hard
dependencies) only.
"""
import random
import sys
import warnings

warnings.simplefilter("ignore")

SEED = 6992
TARGET_CHECKS = 100_000
MAX_DISAGREEMENTS = 10


# ---------------------------------------------------------------------------
# PSet shim: frozenset with `+` = union, `-` = difference (the only PSet
# operators the impl region uses), so the impl bodies copy over verbatim.
# ---------------------------------------------------------------------------

class PSetShim(object):
    __slots__ = ("_s",)

    def __init__(self, items=()):
        self._s = frozenset(items)

    def __add__(self, other):
        return PSetShim(self._s | other._s)

    def __sub__(self, other):
        return PSetShim(self._s - other._s)

    def __eq__(self, other):
        return isinstance(other, PSetShim) and self._s == other._s

    def __hash__(self):
        return hash(self._s)

    def __repr__(self):
        return "PSetShim(%r)" % (sorted(self._s),)


# --- the State record from model.py, contracts stripped -----------------------

class State(object):
    """The four name collections of a container (immutable record)."""

    def __init__(self, variables, coord_names, indexes, index_repr):
        self.variables = variables
        self.coord_names = coord_names
        self.indexes = indexes
        self.index_repr = index_repr


# --- the impl regions of model.py, VERBATIM, contract calls stripped ----------

def promote_to_index(variables0, coord_names0, indexes0, index_repr0,
                     new_index_vars, promoted_names, displaced_index_coords):
    # impl-start
    drop_variables = promoted_names + displaced_index_coords
    readd = (drop_variables - new_index_vars) - promoted_names
    new_variables_all = new_index_vars + readd
    indexes_out = (indexes0 - displaced_index_coords) + new_index_vars
    index_repr_out = (index_repr0 - readd) + new_index_vars
    variables_out = (variables0 - drop_variables) + new_variables_all
    coord_names_out = (coord_names0 - drop_variables) + new_variables_all
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end


def teardown_index(variables0, coord_names0, indexes0, index_repr0,
                   new_index_vars, dropped_coords, converted_coords):
    # impl-start
    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars
    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
    variables_out = (variables0 - dropped_coords) + new_index_vars
    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end


# ---------------------------------------------------------------------------
# Bridge: real Dataset name collections <-> integer-id sets.
# ---------------------------------------------------------------------------

_NAME_IDS = {}


def _nid(name):
    return _NAME_IDS.setdefault(name, len(_NAME_IDS))


def _ids(names):
    return frozenset(_nid(n) for n in names)


def name_sets(ds, IndexVariable):
    """The four name collections of a real Dataset, as str sets."""
    variables = set(map(str, ds._variables))
    coord_names = set(map(str, ds._coord_names))
    indexes = set(map(str, ds._indexes))
    index_repr = set(
        str(k) for k, v in ds._variables.items() if isinstance(v, IndexVariable))
    return variables, coord_names, indexes, index_repr


def well_formed_sets(v, c, i, r):
    return i <= c and c <= v and r <= i


def shadow_tuple(state):
    """The shadow State's four collections as frozensets of ids."""
    return (state.variables._s, state.coord_names._s,
            state.indexes._s, state.index_repr._s)


# ---------------------------------------------------------------------------
# Differential driver.
# ---------------------------------------------------------------------------

class Driver(object):
    def __init__(self, xr, IndexVariable):
        self.xr = xr
        self.IndexVariable = IndexVariable
        self.checked = 0
        self.skipped_rejects = 0
        self.disagreements = []

    def _report(self, tag, inputs, shadow, real):
        self.disagreements.append((tag, inputs, shadow, real))
        print("DISAGREEMENT %s" % tag)
        print("  scenario inputs: %r" % (inputs,))
        print("  shadow: %r" % (shadow,))
        print("  real:   %r" % (real,))
        return len(self.disagreements) < MAX_DISAGREEMENTS

    def check_promote(self, tag, ds, dim, var_names):
        """One promotion scenario: real Dataset.set_index vs shadow."""
        v0, c0, i0, r0 = name_sets(ds, self.IndexVariable)
        try:
            res = ds.set_index({dim: var_names if len(var_names) > 1
                                else var_names[0]})
        except (ValueError, KeyError):
            # rejected up front (e.g. dimension mismatch) before the modeled
            # recomputation; outside the checked domain.
            self.skipped_rejects += 1
            return True
        v1, c1, i1, r1 = name_sets(res, self.IndexVariable)
        promoted = set(map(str, var_names))
        displaced = set()
        for key in [dim] + list(var_names):
            displaced |= set(map(
                str, ds.xindexes.get_all_coords(key, errors="ignore")))
        displaced &= i0
        new_index = set(i1)
        inputs = (tag, dim, list(var_names),
                  dict(variables=sorted(v0), coord_names=sorted(c0),
                       indexes=sorted(i0), index_repr=sorted(r0)),
                  dict(promoted=sorted(promoted), displaced=sorted(displaced),
                       new_index=sorted(new_index)))
        # the model's Requires must hold on the derived channels
        if not (well_formed_sets(v0, c0, i0, r0)
                and promoted <= v0 and promoted <= new_index
                and displaced <= i0):
            return self._report("promote/Requires " + tag, inputs,
                                "derived channels violate the model Requires",
                                (sorted(v1), sorted(c1), sorted(i1), sorted(r1)))
        st = promote_to_index(
            PSetShim(_ids(v0)), PSetShim(_ids(c0)), PSetShim(_ids(i0)),
            PSetShim(_ids(r0)), PSetShim(_ids(new_index)),
            PSetShim(_ids(promoted)), PSetShim(_ids(displaced)))
        self.checked += 1
        if shadow_tuple(st) != (_ids(v1), _ids(c1), _ids(i1), _ids(r1)):
            return self._report(
                "promote " + tag, inputs, shadow_tuple(st),
                (sorted(v1), sorted(c1), sorted(i1), sorted(r1)))
        return True

    def check_teardown(self, tag, ds, arg, drop):
        """One teardown scenario: real Dataset.reset_index vs shadow."""
        v0, c0, i0, r0 = name_sets(ds, self.IndexVariable)
        try:
            res = ds.reset_index(arg, drop=drop)
        except (ValueError, KeyError):
            self.skipped_rejects += 1
            return True
        v1, c1, i1, r1 = name_sets(res, self.IndexVariable)
        dropped = v0 - v1
        new_index = i1 - i0
        converted = (i0 - i1) - dropped - new_index
        inputs = (tag, arg, drop,
                  dict(variables=sorted(v0), coord_names=sorted(c0),
                       indexes=sorted(i0), index_repr=sorted(r0)),
                  dict(dropped=sorted(dropped), converted=sorted(converted),
                       new_index=sorted(new_index)))
        if not (well_formed_sets(v0, c0, i0, r0)
                and dropped <= i0 and converted <= i0
                and not (dropped & converted)
                and not (new_index & dropped) and not (new_index & converted)):
            return self._report("teardown/Requires " + tag, inputs,
                                "derived channels violate the model Requires",
                                (sorted(v1), sorted(c1), sorted(i1), sorted(r1)))
        st = teardown_index(
            PSetShim(_ids(v0)), PSetShim(_ids(c0)), PSetShim(_ids(i0)),
            PSetShim(_ids(r0)), PSetShim(_ids(new_index)),
            PSetShim(_ids(dropped)), PSetShim(_ids(converted)))
        self.checked += 1
        if shadow_tuple(st) != (_ids(v1), _ids(c1), _ids(i1), _ids(r1)):
            return self._report(
                "teardown " + tag, inputs, shadow_tuple(st),
                (sorted(v1), sorted(c1), sorted(i1), sorted(r1)))
        return True


# ---------------------------------------------------------------------------
# Scenario generation.
# ---------------------------------------------------------------------------

def boundary(drv, xr, pd):
    """The known hard shapes: chained promote+teardown, de-indexed coordinate
    promotion, every drop/convert combination on 2- and 3-level stacked
    indexes, the plain single-index teardown."""
    # chained promote then teardown (both flavours of drop)
    ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["p", "q", "r"])})
    drv.check_promote("chained.promote", ds, "z", ["a", "b"])
    s = ds.set_index(z=["a", "b"])
    for drop in (False, True):
        drv.check_teardown("chained.teardown", s, "z", drop)

    # promotion that displaces an existing stacked index (conversion channel)
    one = ["a", "a", "b", "b"]
    two = [1, 2, 1, 2]
    mi = pd.MultiIndex.from_arrays([one, two], names=["one", "two"])
    ds2 = xr.Dataset(coords={"x": mi, "three": ("x", ["c", "c", "d", "d"]),
                             "four": ("x", [3, 4, 3, 4])})
    drv.check_promote("displacing", ds2, "x", ["three", "four"])

    # promotion over an existing plain dimension index
    ds3 = xr.Dataset(coords={"x": [10, 20, 30], "a": ("x", [1, 2, 3]),
                             "b": ("x", [4, 5, 6])})
    drv.check_promote("plain-dim", ds3, "x", ["a", "b"])

    # 2-level teardown grid: every arg shape x both drops
    for arg in ("foo", "bar", "x", ["foo", "bar"], ["x", "foo"], ["foo", "x"]):
        for drop in (False, True):
            ds4 = xr.Dataset(coords={"x": pd.MultiIndex.from_product(
                [["a", "b"], [1, 2]], names=("foo", "bar"))})
            drv.check_teardown("grid2", ds4, arg, drop)

    # 3-level teardown grid with a bystander coordinate and a data variable
    for arg in ("f", ["f", "g"], ["f", "g", "h"], "x", ["x", "f"], ["g", "h"]):
        for drop in (False, True):
            mi3 = pd.MultiIndex.from_product(
                [["a", "b"], [1, 2], [True, False]], names=("f", "g", "h"))
            ds5 = xr.Dataset(coords={"x": mi3, "extra": ("x", list(range(8)))})
            ds5["v"] = ("x", list(range(8)))
            drv.check_teardown("grid3", ds5, arg, drop)

    # plain single-index teardown (whole-coordinate drop / convert)
    for drop in (False, True):
        ds6 = xr.Dataset(coords={"x": [1, 2]})
        drv.check_teardown("plain", ds6, "x", drop)


NAMES = ["n%d" % i for i in range(20)]


def make_dataset(rng, xr, pd):
    """A random small dataset over dimension x (length 4): optionally a plain
    or 2-3-level stacked dimension index, plus extra coordinates and data
    variables along x."""
    names = rng.sample(NAMES, rng.randint(2, 8))
    it = iter(names)
    coords = {}
    used = []
    kind = rng.random()
    if kind < 0.30:
        pass                                    # no dimension index
    elif kind < 0.55:
        coords["x"] = [10, 20, 30, 40]          # plain dimension index
    else:                                       # 2-3-level stacked index
        nlev = rng.randint(2, min(3, len(names)))
        levs = [next(it) for _ in range(nlev)]
        used += levs
        arrays = [["a", "a", "b", "b"], [1, 2, 1, 2],
                  [rng.randint(0, 1) for _ in range(4)]]
        coords["x"] = pd.MultiIndex.from_arrays(arrays[:nlev], names=levs)
    extra = [n for n in names if n not in used]
    ncoord = rng.randint(0, len(extra))
    for n in extra[:ncoord]:
        coords[n] = ("x", [rng.randint(0, 3) for _ in range(4)])
    ds = xr.Dataset(coords=coords)
    for n in extra[ncoord:]:
        ds[n] = ("x", list(range(4)))
    return ds


def fuzz(drv, rng, xr, pd, IndexVariable):
    """Seeded fuzz until TARGET_CHECKS scenarios are counted; several
    operations are exercised per constructed dataset."""
    while drv.checked < TARGET_CHECKS and not drv.disagreements:
        ds = make_dataset(rng, xr, pd)
        v0, c0, i0, r0 = name_sets(ds, IndexVariable)
        plain_coords = sorted(c0 - i0)
        for _ in range(3):
            op = rng.random()
            if op < 0.5 and len(plain_coords) >= 2:
                k = rng.randint(2, min(3, len(plain_coords)))
                var_names = rng.sample(plain_coords, k)
                dim = "x" if rng.random() < 0.7 else "znew"
                if not drv.check_promote("fuzz", ds, dim, var_names):
                    return
            elif i0:
                resettable = sorted(i0)
                k = rng.randint(1, min(3, len(resettable)))
                arg = rng.sample(resettable, k)
                if not drv.check_teardown("fuzz", ds, arg if k > 1 else arg[0],
                                          rng.random() < 0.5):
                    return
            else:
                break


def main():
    import pandas as pd
    import xarray as xr
    from xarray.core.variable import IndexVariable

    drv = Driver(xr, IndexVariable)
    boundary(drv, xr, pd)
    if not drv.disagreements:
        fuzz(drv, random.Random(SEED), xr, pd, IndexVariable)

    if drv.disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d scenarios (seed=%d)"
              % (len(drv.disagreements), drv.checked, SEED))
        return 1
    print("G-CONF OK: model.py impl shadow (promote_to_index / teardown_index"
          " over the PSet shim) agrees with the real patched Dataset.set_index"
          " / Dataset.reset_index name-collection recomputation on %d"
          " scenarios (seed=%d; %d up-front rejects skipped), 0 disagreements."
          % (drv.checked, SEED, drv.skipped_rejects))
    import json
    print(json.dumps({"checked": drv.checked, "disagreements": 0,
                      "seed": SEED, "skipped_rejects": drv.skipped_rejects,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
