#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-7229.

This bundle has NO consumed `@ContractOnly` axioms: the changed behaviour --
when asked to preserve the second argument's attributes, the conditional
selection rebuilds the output's attribute mappings level-by-level -- is modelled
DEEPLY in model.py (the `rebuild_attrs` function). What is validated here is the
**A-reference** obligation: that the deep model matches the REAL post-patch
callee `xarray.where(cond, x, y, keep_attrs=True)`.

The deep model's postconditions, per regime, are:

  * coordinate level (EVERY regime): each output coordinate's attrs == x's OWN
    mapping AT that coordinate's name (NOT x's top-level attrs) -- the headline
    rule. "x's mapping at a name" is resolved ON x, as the callee resolves it
    (`getattr(getattr(x, name, None), "attrs", {})`), which is NOT the same
    function as "the attrs of the coordinate of that name, else {}": see
    `_level_attrs` and `_check_name_resolution` below, which pin the names where
    the two disagree;
  * ordinary regime (output no richer than x): the output's top-level (global)
    attrs == x's OWN top-level attrs, and each output sub-variable's attrs ==
    x's OWN same-named sub-variable attrs;
  * promotion regime (x promoted to a collection because y forced it): the
    output's top-level (global) attrs are EMPTY, and x's top-level attrs are
    routed to the single output sub-variable bearing x's name.

This script asserts EVERY modelled field (global, each coordinate, each
data-var) on EVERY F2P scenario -- including the promotion-case GLOBAL attrs,
which must be empty -- plus randomized fuzz. A modelled field is never silently
skipped on the scenario where the regimes diverge.

The model maps an attribute mapping to an opaque integer identity (distinct
mappings -> distinct identities, the empty mapping -> identity 0); this check
works directly on the real attribute dicts, which is exactly the identity
abstraction made concrete.

Imports only `xarray` / `numpy`. The container ships the BASE_COMMIT (buggy)
source, so this MUST be run with the gold patch applied first:

    run_in_container(..., apply_gold=True, gold_patch_path=<patch.diff>)

(equivalently `git apply patch.diff` in /testbed before running). Run against
the unpatched base it exits 1 -- correctly flagging the buggy callee. Exit 0 iff
every obligation holds against the post-patch callee.
"""
import random
import sys

import numpy as np
import xarray as xr


def _assert_eq(observed, expected, label):
    assert observed == expected, "%s: observed %r != expected %r" % (
        label, observed, expected)


def _level_attrs(obj, name):
    """The source's OWN mapping AT the output level `name`, as the real callee
    computes it: `getattr(getattr(x, name, None), "attrs", {})`.

    The name is resolved ON THE SOURCE OBJECT, not looked up among the levels
    the source carries, and that is not the same function: a name the source
    answers with a derived view of ITSELF (`T`, `variable`, `real`, `imag` on a
    DataArray) yields that view's mapping -- the source's own whole-object
    mapping -- even though the source carries no coordinate or data-var of that
    name, and a name it answers with something carrying no mapping (or with
    nothing at all) yields the empty mapping. Encoding this as
    `dict(x[name].attrs) if name in x.coords else {}` would mis-state the
    callee on exactly those names; `_check_name_resolution` below pins the
    difference against the real function.
    """
    return dict(getattr(getattr(obj, name, None), "attrs", {}) or {})


def _check_da(cond, x, y, label):
    """x is a real DataArray (ordinary regime: output is a DataArray)."""
    out = xr.where(cond, x, y, keep_attrs=True)
    # (1) top-level attrs preserved from x's OWN top-level attrs.
    _assert_eq(dict(out.attrs), dict(x.attrs), label + " [top-level attrs]")
    # (2) each coordinate's attrs preserved from x's OWN same-name coord attrs,
    #     NOT broadcast from x's top-level attrs.
    for c in out.coords:
        x_coord_attrs = _level_attrs(x, c)
        _assert_eq(dict(out[c].attrs), x_coord_attrs,
                   label + " [coord %r attrs]" % (c,))
        # the discriminating guard: where x's top-level attrs differ from this
        # coordinate's attrs, the output coord attrs must follow the COORD, not
        # the top-level mapping (this is exactly the pre-patch bug).
        if dict(x.attrs) != x_coord_attrs:
            assert dict(out[c].attrs) != dict(x.attrs), (
                label + " [coord %r] output coord attrs were broadcast from "
                "x's top-level attrs -- the pre-patch bug" % (c,))


def _check_scalar_x(cond, y, label):
    """x is a scalar: the source has no mapping at any name -> output takes
    none."""
    out = xr.where(cond, 0, y, keep_attrs=True)
    _assert_eq(dict(out.attrs), {}, label + " [scalar-x top-level attrs]")
    for c in out.coords:
        _assert_eq(dict(out[c].attrs), _level_attrs(0, c),
                   label + " [scalar-x coord %r]" % (c,))
        _assert_eq(_level_attrs(0, c), {},
                   label + " [scalar-x has no mapping at %r]" % (c,))


def _check_two_datasets(cond, ds_x, x, label):
    """ordinary regime, output is a Dataset (both x and y are Datasets):
    global attrs from ds_x's OWN global, each data-var from x's same-named var,
    each coord from x's OWN same-name coord."""
    out = xr.where(cond, ds_x, ds_x, keep_attrs=True)
    # (1) GLOBAL attrs == ds_x's OWN global attrs (ordinary regime).
    _assert_eq(dict(out.attrs), dict(ds_x.attrs), label + " [global attrs]")
    # (2) each data-var's attrs == ds_x's OWN mapping AT that data-var's name.
    for v in out.data_vars:
        src = _level_attrs(ds_x, v)
        _assert_eq(dict(out[v].attrs), src, label + " [data-var %r attrs]" % (v,))
    # (3) each coordinate's attrs == ds_x's OWN mapping AT that coord's name.
    for c in out.coords:
        src = _level_attrs(ds_x, c)
        _assert_eq(dict(out[c].attrs), src, label + " [coord %r attrs]" % (c,))


def _check_promotion(cond, x_named, ds_y, x, label):
    """promotion regime: x (a DataArray bearing a name) is promoted to a Dataset
    because y is a Dataset. GLOBAL attrs MUST be empty; x's top-level attrs are
    routed to the output data-var bearing x's name; each coord keeps x's own."""
    out = xr.where(cond, x_named, ds_y, keep_attrs=True)
    # (1) GLOBAL attrs are EMPTY -- the regime-divergent field the deep model
    #     pins to identity 0 (Result().attrs == 0). THIS is the assertion whose
    #     omission previously masked the over-claim.
    _assert_eq(dict(out.attrs), {}, label + " [promotion GLOBAL attrs empty]")
    # (2) the output data-var bearing x's name takes x's TOP-LEVEL attrs.
    name = x_named.name
    assert name in out.data_vars, (
        label + " [promotion] expected x's name %r among output data-vars %r"
        % (name, list(out.data_vars)))
    _assert_eq(dict(out[name].attrs), dict(x.attrs),
               label + " [promotion matching data-var %r attrs]" % (name,))
    # (3) each coordinate's attrs == x's OWN mapping AT that coord's name.
    for c in out.coords:
        src = _level_attrs(x, c)
        _assert_eq(dict(out[c].attrs), src,
                   label + " [promotion coord %r attrs]" % (c,))


# Names a DataArray answers with a DERIVED VIEW OF ITSELF, so that
# `getattr(getattr(x, nm, None), "attrs", {})` is x's OWN whole-object mapping
# even when x carries no coordinate of that name (measured against the patched
# callee: all four carry `x.attrs`).
_DERIVED_VIEW_NAMES = ("T", "variable", "real", "imag")
# Names a DataArray answers with something carrying no mapping of its own (an
# ndarray, a tuple, a dict) or with nothing at all -> the empty mapping.
_NO_MAPPING_NAMES = ("values", "shape", "zzz")


def _check_name_resolution(cond, x, label):
    """The per-level source is x's mapping AT the level's NAME, resolved on x
    itself -- NOT looked up among the coordinates x happens to carry. The two
    readings disagree on the names below, so this pins which one the real
    callee implements:

      * a coordinate name x answers with a derived view of itself takes x's OWN
        whole-object mapping (NOT the empty mapping), even though x carries no
        coordinate of that name;
      * a coordinate name x answers with nothing, or with something carrying no
        mapping, takes the empty mapping.

    Every coordinate of every output here is asserted by the single rule
    `_level_attrs`, so a checker that agreed with the "levels x carries"
    reading would fail on the first group.
    """
    for nm in _DERIVED_VIEW_NAMES + _NO_MAPPING_NAMES:
        y = xr.DataArray([0, 0], coords={"a": [0, 1]}, attrs={"attr": "y_da"})
        y = y.assign_coords({nm: ("a", [7, 8])})
        y.attrs = {"attr": "y_da"}
        y["a"].attrs = {"attr": "y_coord"}
        y[nm].attrs = {"attr": "y_" + nm}
        out = xr.where(cond, x, y, keep_attrs=True)
        assert nm in out.coords, (
            label + " [%r] expected the output to carry that coordinate, "
            "got %r" % (nm, list(out.coords)))
        assert nm not in x.coords, (
            label + " [%r] x must NOT carry a coordinate of that name for this "
            "case to discriminate" % (nm,))
        # the uniform rule, on every level of the output
        for c in out.coords:
            _assert_eq(dict(out[c].attrs), _level_attrs(x, c),
                       label + " [%r shadowing, coord %r]" % (nm, c))
        # and the two readings really do disagree / agree as claimed
        if nm in _DERIVED_VIEW_NAMES:
            _assert_eq(_level_attrs(x, nm), dict(x.attrs),
                       label + " [%r does not resolve to a view of x]" % (nm,))
            assert dict(out[nm].attrs) != {}, (
                label + " [%r] the level x carries no coordinate for came out "
                "EMPTY -- the 'levels x carries' reading" % (nm,))
        else:
            _assert_eq(dict(out[nm].attrs), {},
                       label + " [%r yields no mapping]" % (nm,))


def _forms_an_output(cond, x, y):
    """Do the three arguments COMBINE into an object carrying attribute levels?

    mapping.md "Domain edge 1". Settled by the metadata-DROPPING call, which is
    the same question the routine answers when asked to keep no attributes, so
    the answer is independent of the rebuild under test.
    """
    try:
        skel = xr.where(cond, x, y, keep_attrs=False)
    except Exception:                                       # noqa: BLE001
        return False
    return hasattr(skel, "attrs") and hasattr(skel, "coords")


def _check_domain_edges(cond, x, y, label):
    """The modelled behaviour is claimed only for calls the callee DELIVERS a
    result for. Three things can leave a call outside it: the arguments may not
    combine into anything carrying attribute levels at all (mapping.md "Domain
    edge 1"), and either of two name resolutions inside the rebuild may abandon
    the call (mapping.md "Domain edge 2"). This pins BOTH directions, so the
    restriction cannot quietly grow into a narrowing of the claim:

      (a) EXCLUDED calls really do fail to deliver -- an output coordinate named
          for the source-side accessor that declines on a non-datetime-like
          source, and a source whose whole-object mapping records a roster name
          whose value is not a walkable roster of levels the output carries;
      (b) the BENIGN members of the same shapes are still IN domain and satisfy
          the uniform rule -- a diverted roster value that IS walkable and names
          only levels the output carries changes nothing observable; the SAME
          declining accessor name borne by a PROMOTED source is in domain,
          because the promotion regime never interrogates the source under a
          sub-variable name; and the same coordinate name is in domain when the
          source is of a sort the accessor answers for;
      (c) the calls excluded by the FIRST edge are excluded for a reason that
          does not depend on the rebuild: they already fail to form an output
          when no attributes are kept at all.
    """
    # (a1) source-side: the level-name lookup declines to answer.
    yd = y.assign_coords({"dt": ("a", [7, 8])})
    raised = None
    try:
        xr.where(cond, x, yd, keep_attrs=True)
    except Exception as exc:                                # noqa: BLE001
        raised = exc
    assert raised is not None, (
        label + " [dt] expected the call to be abandoned (the source-side "
        "lookup declines on a non-datetime-like source), but it delivered")
    # ...and that same call DOES form an output when no attributes are kept, so
    # the exclusion is the interrogation's, not the combination's.
    assert _forms_an_output(cond, x, yd), (
        label + " [dt] the arguments must still COMBINE -- otherwise this case "
        "is testing the wrong domain edge")

    # (a2) output-side: the roster lookup is diverted to a bogus roster.
    for payload in ("temperature", ["q"], ["zz"], 5):
        xb = x.copy()
        xb.attrs = {"data_vars": payload}
        raised = None
        try:
            xr.where(cond, xb, y, keep_attrs=True)
        except Exception as exc:                            # noqa: BLE001
            raised = exc
        assert raised is not None, (
            label + " [roster %r] expected the call to be abandoned (the "
            "sub-variable roster diverts to a value that is not a roster of "
            "levels the output carries), but it delivered" % (payload,))
        assert _forms_an_output(cond, xb, y), (
            label + " [roster %r] the arguments must still COMBINE -- otherwise "
            "this case is testing the wrong domain edge" % (payload,))

    # (b1) the BENIGN roster members stay IN domain and obey the uniform rule.
    for payload in ([], ["a"], "", ("a",), {"a": 1}):
        xb = x.copy()
        xb.attrs = {"data_vars": payload}
        out = xr.where(cond, xb, y, keep_attrs=True)
        _assert_eq(dict(out.attrs), dict(xb.attrs),
                   label + " [benign roster %r top-level]" % (payload,))
        for c in out.coords:
            _assert_eq(dict(out[c].attrs), _level_attrs(xb, c),
                       label + " [benign roster %r coord %r]" % (payload, c))

    # (b2) THE ANTI-NARROWING CASE. The declining accessor name borne by a
    # PROMOTED source: the promotion regime routes the source's whole-object
    # mapping to the slot bearing the source's NAME without ever interrogating
    # the source under a sub-variable name, so this call is squarely IN domain
    # even though the very same name declines when asked of the same source. A
    # domain statement that excluded it would be shrinking the claim rather than
    # stating it -- and it would exclude a shape the specified behaviour covers.
    for nm in ("dt",):
        xp = x.rename(nm)
        declines = False
        try:
            getattr(xp, nm, None)
        except Exception:                                   # noqa: BLE001
            declines = True
        assert declines, (
            label + " [promoted %r] this case only discriminates if the name "
            "really does decline when asked of the source" % (nm,))
        ds_y = xr.Dataset(data_vars={nm: y}, attrs={"attr": "y_ds"})
        out = xr.where(cond, xp, ds_y, keep_attrs=True)
        _assert_eq(dict(out.attrs), {},
                   label + " [promoted %r GLOBAL attrs empty]" % (nm,))
        assert nm in out.data_vars, (
            label + " [promoted %r] expected the source's name among the "
            "output's sub-variables" % (nm,))
        _assert_eq(dict(out[nm].attrs), dict(xp.attrs),
                   label + " [promoted %r matching sub-variable]" % (nm,))
        for c in out.coords:
            _assert_eq(dict(out[c].attrs), _level_attrs(xp, c),
                       label + " [promoted %r coord %r]" % (nm, c))

    # (b3) ...and the same coordinate name is IN domain when the source is of a
    # sort the accessor DOES answer for: the exclusion is a property of the pair,
    # never of the name alone.
    stamps = np.array(["2000-01-01", "2000-01-02"], dtype="datetime64[ns]")
    xt = xr.DataArray(stamps, coords={"a": [0, 1]}, attrs={"attr": "x_dt"})
    xt["a"].attrs = {"attr": "x_coord"}
    yt = xr.DataArray(stamps, coords={"a": [0, 1]}).assign_coords(
        {"dt": ("a", [7, 8])})
    answers = True
    try:
        getattr(xt, "dt", None)
    except Exception:                                       # noqa: BLE001
        answers = False
    assert answers, (label + " [datetime dt] the accessor must answer for a "
                     "datetime-like source or this case proves nothing")
    out = xr.where(cond, xt, yt, keep_attrs=True)
    _assert_eq(dict(out.attrs), dict(xt.attrs),
               label + " [datetime dt top-level]")
    for c in out.coords:
        _assert_eq(dict(out[c].attrs), _level_attrs(xt, c),
                   label + " [datetime dt coord %r]" % (c,))

    # (c) the FIRST edge: arguments that do not combine into anything carrying
    # attribute levels. Excluded, and excluded already with no attributes kept.
    for cx, xx, yy, tag in (
            (True, 1, 0, "all plain scalars"),
            (np.array([True, False]), 1, 0, "plain condition array"),
    ):
        assert not _forms_an_output(cx, xx, yy), (
            label + " [%s] expected no output carrying attribute levels" % tag)
        raised = None
        try:
            xr.where(cx, xx, yy, keep_attrs=True)
        except Exception as exc:                            # noqa: BLE001
            raised = exc
        assert raised is not None, (
            label + " [%s] expected the call to be abandoned" % tag)


def main():
    # --- boundary: the exact F2P scenarios (issue #7229) ------------------
    cond = xr.DataArray([True, False], coords={"a": [0, 1]},
                        attrs={"attr": "cond_da"})
    cond["a"].attrs = {"attr": "cond_coord"}
    x = xr.DataArray([1, 1], coords={"a": [0, 1]}, attrs={"attr": "x_da"})
    x["a"].attrs = {"attr": "x_coord"}
    y = xr.DataArray([0, 0], coords={"a": [0, 1]}, attrs={"attr": "y_da"})
    y["a"].attrs = {"attr": "y_coord"}

    # 3 DataArrays, takes attrs (top-level AND coord) from x
    _check_da(cond, x, y, "F2P 3-DataArrays")
    # y as a scalar, takes attrs from x
    _check_da(cond, x, 0, "F2P y-scalar")
    # cond and y as a scalar, takes attrs from x
    _check_da(True, x, y, "F2P cond+y-scalar")

    # x as a scalar, takes no attrs
    _check_scalar_x(cond, y, "F2P x-scalar")
    # x and y as a scalar, takes no attrs
    out = xr.where(cond, 1, 0, keep_attrs=True)
    _assert_eq(dict(out.attrs), {}, "F2P x+y-scalar top-level attrs")
    for c in out.coords:
        _assert_eq(dict(out[c].attrs), _level_attrs(1, c),
                   "F2P x+y-scalar coord %r" % (c,))
        _assert_eq(_level_attrs(1, c), {},
                   "F2P x+y-scalar has no mapping at %r" % (c,))

    # name resolution: coordinate names the source answers with a derived view
    # of ITSELF vs names it answers with nothing -- the two readings of "the
    # source's mapping at this level" differ here, and this is which one holds.
    _check_name_resolution(cond, x, "F2P+name-resolution")

    # domain edges: which calls the modelled behaviour is claimed for at all,
    # pinned in both directions (excluded really fails; benign really holds).
    _check_domain_edges(cond, x, y, "F2P+domain-edges")

    # DataArray and 2 Datasets (ordinary Dataset regime): GLOBAL + data-var +
    # coord all asserted from x's OWN same-level mapping.
    ds_x = xr.Dataset(data_vars={"x": x}, attrs={"attr": "x_ds"})
    _check_two_datasets(cond, ds_x, x, "F2P 2-Datasets")

    # 2 DataArrays and 1 Dataset (x promoted to Dataset): GLOBAL attrs EMPTY,
    # matching data-var takes x's top-level attrs, coords keep x's own.
    ds_y = xr.Dataset(data_vars={"x": y}, attrs={"attr": "y_ds"})
    _check_promotion(cond, x.rename("x"), ds_y, x, "F2P promote")

    # --- randomized fuzz: distinct top-level vs coord attrs ----------------
    rng = random.Random(7229)
    for _ in range(2000):
        n = rng.randint(1, 5)
        coords = {"a": list(range(n))}
        cv = bool(rng.getrandbits(1))
        cond_f = xr.DataArray([cv] * n, coords=coords)
        # distinct identities for top-level vs coordinate mappings
        xv_attr = "xtop_%d" % rng.randint(0, 10**6)
        xc_attr = "xcoord_%d" % rng.randint(0, 10**6)
        xf = xr.DataArray(np.ones(n), coords=coords, attrs={"k": xv_attr})
        xf["a"].attrs = {"k": xc_attr}
        yf = xr.DataArray(np.zeros(n), coords=coords, attrs={"k": "ytop"})
        yf["a"].attrs = {"k": "ycoord"}
        _check_da(cond_f, xf, yf, "fuzz DataArray")

        # fuzz the promotion regime too: GLOBAL must stay empty, matching
        # data-var takes x's top-level, coord keeps x's own.
        if rng.getrandbits(1):
            ds_yf = xr.Dataset(data_vars={"x": yf}, attrs={"k": "ydstop"})
            _check_promotion(cond_f, xf.rename("x"), ds_yf, xf,
                             "fuzz promote")

    print("G-AX OK: deep model matches real xarray.where(..., keep_attrs=True) "
          "on every modelled field (global, each coordinate, each data-var) of "
          "all 7 F2P scenarios -- including the promotion-case EMPTY global "
          "attrs and the matching data-var -- plus %d name-resolution "
          "scenarios (%d output coordinate names x answers with a derived view "
          "of itself, %d it answers with no mapping), the domain edges pinned "
          "in both directions (7 calls outside the specified behaviour -- 1 "
          "source-side declining lookup, 4 diverted rosters, 2 argument "
          "combinations carrying no attribute levels -- against 7 in-domain "
          "members of the very same shapes: 5 benign diverted rosters, the "
          "declining accessor name borne by a PROMOTED source, and the same "
          "coordinate name on a source the accessor answers for, all obeying "
          "the uniform rule), and 2000 fuzz cases. No consumed axioms."
          % (len(_DERIVED_VIEW_NAMES) + len(_NO_MAPPING_NAMES),
             len(_DERIVED_VIEW_NAMES), len(_NO_MAPPING_NAMES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
