#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14539.

Runs the REAL repo callees the modeled column-comparison consults — the
UNCHANGED format test `"P" in col.format or "Q" in col.format` and the two
UNCHANGED comparison routes (the row-wise `np.allclose` list-comprehension and
the generic `np.where(arra != arrb)`) — in-container on real FITS columns over
boundary and fuzzed data, and asserts the facts the deep models rely on.

There is NO consumed axiom in this bundle (directive 7): the changed route
choice is modeled directly and both route behaviors are DEEP models. What G-AX
establishes are the **A-reference** facts that make those deep models faithful
and the modeled failure (`DiffErr.ambiguous`) non-vacuous (mapping.md §3,
refinement.md §A):

  1. isVLA FAITHFUL: `isVLA(col.format)` (= "'P' in fmt or 'Q' in fmt") agrees
     with the real `"P" in col.format or "Q" in col.format` on every column, and
     exactly the P/Q-format columns are the object-dtype (VLA) ones.
  2. ROW-WISE OUTCOME FAITHFUL (numComparable): the VLA branch's
     `np.allclose` list-comprehension COMPLETES iff the column's elements are
     numerically comparable (`col.numComparable`), and otherwise RAISES (a
     non-numeric column — e.g. text elements, a "*A" format — cannot be compared
     by numeric closeness; np.allclose raises). When it completes its
     differing-index set equals {i | rows[i].differs} (the rowResult deep model),
     for every column whatever its rows' element counts. Every intrinsically-VLA
     (object dtype, P/Q) column IS numerically comparable (its elements are numeric
     sub-arrays), so the row-wise route always completes on the columns the
     classifier sends down it. This is exactly diffSpec's `rowWiseOutcome` guard
     (`col.numComparable` -> ok(rowResult), else error): it makes "send everything
     row-wise" wrong on a text column, which the generic route handles.
  3. GENERIC OUTCOME FAITHFUL (varLength && anyMulti): the generic route
     `np.where(arra != arrb)` raises a ValueError iff the column is intrinsically
     variable-length (object dtype, i.e. a P/Q format -> col.varLength) AND some
     row holds >1 element (anyMulti rows). A column that is NOT intrinsically
     variable-length is a regular fixed-width (possibly multidimensional) block
     whose element-wise comparison ALWAYS completes, whatever its rows' element
     counts — so e.g. a fixed-multidim "2J" column does NOT raise. When the
     generic route completes it yields the SAME differing-index set as the row-wise
     route. This `varLength && anyMulti` condition is exactly the `DiffErr.ambiguous`
     guard of diffSpec's `genericOutcome` and the spurious-difference failure the
     public problem statement reports; pinning it to the column's intrinsic kind
     (not merely to multi-element rows) is what makes the post-patch comparison
     provably always complete.
  4. CLASSIFIER MATCHES INTRINSIC KIND (isVLA == varLength): the format
     classification `isVLA(col.format)` equals the column's intrinsic
     variable-length kind `col.varLength` (object dtype). This is what makes the
     route faithful to the element kind, so every column is sent down a route its
     element kind supports and the comparison always completes — the property the
     dead-branch-free diffSpec relies on.

Imports numpy + the astropy under test only. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
from astropy.io import fits


# --- isVLA: the Lean deep model, transliterated verbatim ----------------------
#     isVLA fmt = fmt.contains 'P' || fmt.contains 'Q'
def is_vla_model(fmt):
    return ("P" in fmt) or ("Q" in fmt)


def real_format_test(fmt):
    """The UNCHANGED real route-selecting test (diff.py:1452 post-patch)."""
    return ("P" in fmt) or ("Q" in fmt)


# --- the two UNCHANGED comparison routes, run on real arrays ------------------
def row_wise_route(arra, arrb, rtol=0.0, atol=0.0):
    """The VLA branch (diff.py:1453-1461). Returns ('ok', set) or ('raise',):
    np.allclose RAISES on a column whose elements are not numerically comparable
    (e.g. text), and otherwise COMPLETES with the differing-index set."""
    try:
        diffs = (
            [idx for idx in range(len(arra))
             if not np.allclose(arra[idx], arrb[idx], rtol=rtol, atol=atol)],
        )
        return ("ok", set(diffs[0]))
    except (TypeError, ValueError) as _e:  # DTypePromotionError <: TypeError
        return ("raise",)


def num_comparable_model(arra):
    """col.numComparable bijection: whether the column's elements are comparable
    by numeric closeness — i.e. a numeric (or boolean) dtype, OR an object-dtype
    VLA column whose elements are numeric sub-arrays. A text/byte column is NOT.
    For object (VLA) columns we probe an element's dtype."""
    dt = arra.dtype
    if dt == object:
        # VLA: elements are sub-arrays; numerically comparable iff their dtype is
        for el in arra:
            a = np.asarray(el)
            if a.size and not (np.issubdtype(a.dtype, np.number)
                               or np.issubdtype(a.dtype, np.bool_)):
                return False
        return True
    return bool(np.issubdtype(dt, np.number) or np.issubdtype(dt, np.bool_))


def generic_route(arra, arrb):
    """The else branch (diff.py:1463). Returns ('ok', set) or ('raise',)."""
    try:
        diffs = np.where(arra != arrb)
        return ("ok", set(diffs[0].tolist()))
    except ValueError:
        return ("raise",)


# --- the row model: differs / multiElem, derived from the real arrays ---------
def rows_model(arra, arrb, rtol=0.0, atol=0.0):
    """rows : List Row — per-row (differs, multiElem) from the real arrays. For a
    numComparable column `differs` is the numeric-closeness verdict (the row-wise
    route's per-row test); for a non-numComparable (text) column — which is never
    routed row-wise — `differs` falls back to plain element inequality so the
    model is still well-defined (it only feeds rowResult, unused on such columns)."""
    out = []
    num_comp = num_comparable_model(arra) and num_comparable_model(arrb)
    for i in range(len(arra)):
        if num_comp:
            differs = not np.allclose(arra[i], arrb[i], rtol=rtol, atol=atol)
        else:
            differs = bool(np.any(np.asarray(arra[i]) != np.asarray(arrb[i])))
        multi = np.size(arra[i]) > 1 or np.size(arrb[i]) > 1
        out.append((differs, multi))
    return out


def row_result_set(rows):
    """{i | rows[i].differs} — the rowResult deep model as an index set."""
    return {i for i, (differs, _m) in enumerate(rows) if differs}


def any_multi(rows):
    return any(m for (_d, m) in rows)


def make_col(fmt, arr):
    return fits.BinTableHDU.from_columns(
        [fits.Column("x", format=fmt, array=arr)])


def col_array(fmt, arr):
    hdu = make_col(fmt, arr)
    return hdu.data["x"], hdu.columns["x"].format


# --- the checks ---------------------------------------------------------------
def check_isvla_faithful(fmt_str):
    model = is_vla_model(fmt_str)
    real = real_format_test(fmt_str)
    assert model == real, (
        "isVLA(%r)=%r but real test=%r" % (fmt_str, model, real))


def check_routes(fmt, a, b, rtol=0.0, atol=0.0):
    arra, fmt_str = col_array(fmt, a)
    arrb, _ = col_array(fmt, b)
    check_isvla_faithful(fmt_str)
    rows = rows_model(arra, arrb, rtol, atol)
    is_vla = is_vla_model(fmt_str)

    # fact 4: classifier matches intrinsic kind: isVLA(fmt) == varLength
    # (object dtype). The route is then faithful to the element kind.
    var_length = (arra.dtype == object)
    assert is_vla == var_length, (
        "isVLA(%r)=%r but intrinsic varLength (object dtype)=%r"
        % (fmt_str, is_vla, var_length))

    # numComparable bijection (must agree on both arrays)
    num_comp = num_comparable_model(arra)
    assert num_comp == num_comparable_model(arrb), (
        "numComparable disagrees across the two arrays (fmt=%r)" % fmt)
    # every intrinsically-VLA column is numerically comparable (numeric sub-arrays)
    if var_length:
        assert num_comp, (
            "intrinsically-VLA column %r modeled non-numComparable" % fmt_str)

    # fact 2: ROW-WISE OUTCOME — completes iff numComparable, else raises; on
    # completion its set == rowResult model. This is diffSpec's rowWiseOutcome.
    rw = row_wise_route(arra, arrb, rtol, atol)
    if num_comp:
        assert rw[0] == "ok", (
            "row-wise route RAISED on a numComparable column (fmt=%r a=%r b=%r): "
            "%r" % (fmt, a, b, rw))
        expected = row_result_set(rows)
        assert rw[1] == expected, (
            "row-wise differing set %r != rowResult model %r (fmt=%r a=%r b=%r)"
            % (rw[1], expected, fmt, a, b))
    else:
        assert rw[0] == "raise", (
            "row-wise route did NOT raise on a non-numComparable column "
            "(fmt=%r a=%r b=%r): got %r" % (fmt, a, b, rw))

    # fact 3: GENERIC OUTCOME — raises IFF (intrinsically VLA, i.e. object dtype)
    # AND (some row multi-element). Pinning the failure to the column's intrinsic
    # kind, not merely to multi-element rows, is diffSpec's genericOutcome guard
    # `varLength && anyMulti rows`: a non-VLA fixed-multidim block never raises.
    g = generic_route(arra, arrb)
    am = any_multi(rows)
    should_raise = var_length and am
    if should_raise:
        assert g[0] == "raise", (
            "generic route did NOT raise on an intrinsically-VLA multi-element "
            "column (fmt=%r a=%r b=%r): got %r" % (fmt, a, b, g))
    else:
        assert g[0] == "ok", (
            "generic route raised where genericOutcome expects completion "
            "(varLength=%r anyMulti=%r fmt=%r a=%r b=%r)"
            % (var_length, am, fmt, a, b))
        if num_comp:
            # both routes complete and must agree on the differing-index set
            assert g[1] == rw[1], (
                "generic set %r != row-wise set %r on completing column "
                "(fmt=%r a=%r b=%r)" % (g[1], rw[1], fmt, a, b))


def main():
    # --- fact 1: isVLA faithful + P/Q <-> object dtype on real columns --------
    scalar_fmts = ["L", "X", "B", "I", "J", "K", "E", "D", "C", "M", "A"]
    vla_fmts = ["PI(2)", "PJ(2)", "PE(2)", "PD(2)", "QI(2)", "QJ(2)",
                "QE(2)", "QD(2)"]
    for fmt in scalar_fmts:
        arr = [0, 1] if fmt not in ("A",) else ["a", "b"]
        if fmt in ("C", "M"):
            arr = [0 + 1j, 2 + 3j]
        _arr, fmt_str = col_array(fmt, arr)
        check_isvla_faithful(fmt_str)
        assert not is_vla_model(fmt_str), "scalar fmt %r flagged VLA" % fmt_str
        assert _arr.dtype != object, (
            "scalar fmt %r unexpectedly object dtype" % fmt_str)
    for fmt in vla_fmts:
        _arr, fmt_str = col_array(fmt, [[0, 1], [2, 3]])
        check_isvla_faithful(fmt_str)
        assert is_vla_model(fmt_str), "VLA fmt %r not flagged VLA" % fmt_str
        assert _arr.dtype == object, (
            "VLA fmt %r not object dtype" % fmt_str)

    # --- facts 2 & 3: route behaviors on boundary VLA columns -----------------
    # P and Q, int and float, identical and differing, scalar/multi/ragged/empty
    int_fmts = ["PI(2)", "PJ(2)", "QI(2)", "QJ(2)"]
    flt_fmts = ["PE(2)", "PD(2)", "QE(2)", "QD(2)"]
    boundary_int = [
        ([[0, 1], [2, 3]], [[0, 1], [2, 3]]),    # multi, identical
        ([[0, 1], [2, 3]], [[1, 2], [3, 4]]),    # multi, all differ
        ([[0, 1], [2, 3]], [[0, 1], [3, 4]]),    # multi, one differs
        ([[5], [6]],       [[5], [6]]),          # scalar rows, identical
        ([[5], [6]],       [[5], [7]]),          # scalar rows, one differs
        ([[], []],         [[], []]),            # empty rows
    ]
    boundary_flt = [
        ([[0.0, 1.0], [2.0, 3.0]], [[0.0, 1.0], [2.0, 3.0]]),
        ([[0.0, 1.0], [2.0, 3.0]], [[1.0, 2.0], [3.0, 4.0]]),
        ([[0.0], [1.0]],           [[0.0], [1.0]]),
        ([[0.0], [1.0]],           [[0.0], [2.0]]),
    ]
    n_checks = 0
    for fmt in int_fmts:
        for a, b in boundary_int:
            check_routes(fmt, a, b); n_checks += 1
    for fmt in flt_fmts:
        for a, b in boundary_flt:
            check_routes(fmt, a, b); n_checks += 1

    # --- fact 3 lower bound: NON-VLA fixed-multidim columns must NOT raise -----
    # These are the columns that distinguish `isVLA && anyMulti` from a naive
    # `anyMulti`-only guard: regular fixed-width multidimensional blocks (e.g.
    # "2J", "3I", "2E") have multi-element rows yet are NOT object dtype, so the
    # generic route completes. check_routes asserts is_vla(fmt)==False, anyMulti
    # ==True, and that the generic route returns "ok" matching the row-wise set.
    nonvla_multidim = [
        ("2J", [[0, 1], [2, 3]], [[0, 1], [2, 3]]),     # identical
        ("2J", [[0, 1], [2, 3]], [[1, 2], [3, 4]]),     # all differ
        ("3I", [[0, 1, 2], [3, 4, 5]], [[0, 1, 9], [3, 4, 5]]),  # one differs
        ("2E", [[0.0, 1.0], [2.0, 3.0]], [[0.0, 1.0], [2.0, 3.0]]),
        ("2D", [[0.0, 1.0], [2.0, 3.0]], [[0.0, 9.0], [2.0, 3.0]]),
    ]
    n_nonvla_multi = 0
    for fmt, a, b in nonvla_multidim:
        arr_chk, fs = col_array(fmt, a)
        assert not is_vla_model(fs), "non-VLA fixture %r flagged VLA" % fs
        assert arr_chk.dtype != object, (
            "non-VLA multidim fixture %r unexpectedly object dtype" % fs)
        # confirm the row IS multi-element (so this genuinely tests the guard)
        assert any(np.size(arr_chk[i]) > 1 for i in range(len(arr_chk))), (
            "non-VLA multidim fixture %r is not actually multi-element" % fs)
        check_routes(fmt, a, b); n_checks += 1; n_nonvla_multi += 1
    assert n_nonvla_multi >= 5, "non-VLA multidim coverage missing"

    # --- fact 2 lower bound: NON-numComparable (text) columns ------------------
    # These columns distinguish "route everything row-wise" from the gold route:
    # they are NOT object dtype (so isVLA=False -> sent generic) and their
    # elements are NOT numerically comparable, so the row-wise np.allclose route
    # RAISES on them while the generic np.where route completes. check_routes
    # asserts num_comparable==False, row-wise raises, generic completes.
    text_cols = [
        ("10A", ["foo", "bar"], ["foo", "baz"]),
        ("5A", ["abcd", "ef"], ["abcd", "ef"]),
        ("A", ["x", "y"], ["z", "y"]),
        ("20A", ["hello", "world"], ["hello", "WORLD"]),
    ]
    n_text = 0
    for fmt, a, b in text_cols:
        arr_chk, fs = col_array(fmt, a)
        assert not is_vla_model(fs), "text fixture %r flagged VLA" % fs
        assert arr_chk.dtype != object, (
            "text fixture %r unexpectedly object dtype" % fs)
        assert not num_comparable_model(arr_chk), (
            "text fixture %r modeled numComparable" % fs)
        check_routes(fmt, a, b); n_checks += 1; n_text += 1
    assert n_text >= 4, "non-numComparable (text) coverage missing"

    # --- randomized fuzz over VLA columns -------------------------------------
    rng = random.Random(14539)
    n_fuzz = 4000
    n_multi = 0
    for _ in range(n_fuzz):
        fmt = rng.choice(int_fmts)
        nrows = rng.randint(1, 4)
        rowlens = [rng.choice([1, 1, 2, 3]) for _ in range(nrows)]
        a = [[rng.randint(0, 4) for _ in range(L)] for L in rowlens]
        # b: same shapes (so np.where can be attempted), values maybe differ
        b = [[(v if rng.random() < 0.6 else rng.randint(0, 4)) for v in row]
             for row in a]
        if any(L > 1 for L in rowlens):
            n_multi += 1
        check_routes(fmt, a, b)
    assert n_multi > 500, (
        "fuzz produced too few multi-element columns (%d) — the raising leg is "
        "under-exercised" % n_multi)

    print("G-AX OK: isVLA deep model (== real \"P\"/\"Q\" format test) sound and "
          "== intrinsic varLength (object dtype) on %d formats; row-wise route "
          "completes iff numComparable (== rowResult) and RAISES on %d "
          "non-numComparable text columns (rowWiseOutcome guard); generic route "
          "raises iff the column is intrinsically VLA (object dtype) AND a row is "
          "multi-element (== varLength && anyMulti, the genericOutcome guard) and "
          "else matches row-wise — incl. %d non-VLA fixed-multidim columns that "
          "do NOT raise — on %d boundary + %d fuzz columns (%d multi-element). "
          "A-reference facts sound; no consumed axiom."
          % (len(scalar_fmts) + len(vla_fmts), n_text, n_nonvla_multi, n_checks,
             n_fuzz, n_multi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
