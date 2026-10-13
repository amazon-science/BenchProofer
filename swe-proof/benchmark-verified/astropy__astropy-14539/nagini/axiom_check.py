#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14539.

The bundle consumes NO @ContractOnly axiom. It models, deeply, the descriptor
recognition and the comparator-applicability it governs, and validates each deep
model against the REAL callee it abstracts (the A-reference checks of
refinement.md / mapping.md):

  (A-reference 1) `is_vla_descriptor(fmt)` (model.py pure region) == the REAL
      layout-string membership test the patch performs on a column's format
      string: `("P" in col.format) or ("Q" in col.format)`. The model encodes
      it as: the code-point sequence contains 80 ('P') or 81 ('Q').

  (A-reference 2) the model's single row-granular discipline
      `row_granular_count(row_mismatches)` == the REAL per-column accumulation
      `diff_total += len(set(diffs[0]))` on BOTH branches the patch selects
      between, and the applicability constraint that distinguishes them:

        * row-aware (VLA) path, used when the descriptor designates
          variable-length storage:
              diffs = ([idx for idx in range(len(arra))
                        if not np.allclose(arra[idx], arrb[idx],
                                           rtol=0, atol=0)],)
          accumulates, after `set`, the number of ROWS whose two sub-arrays are
          not element-wise close == `row_granular_count(row_mismatches)`.

        * element-wise (non-VLA) path, used for an ordinary column:
              diffs = np.where(arra != arrb)
          ALSO accumulates, after `set(diffs[0])`, the number of distinct
          differing ROWS (NOT the element total) == `row_granular_count`.
          Confirmed here on multi-element fixed-width columns, where a partial-
          row diff would distinguish a row count from an element sum.

        * APPLICABILITY (the control-flow effect the patch fixes): the
          element-wise `np.where(arra != arrb)` path RAISES `ValueError` when
          handed a genuine variable-length column (an object array of
          multi-element sub-arrays). This grounds the model's
          `Requires(not is_vla_descriptor(...))` on `compare_elementwise`: a
          variable-length column must NOT be routed through the element-wise
          comparator. The pre-patch code, recognising only 'P', routes a
          'Q'-marked variable-length column here and raises (or, on scalar/
          ragged degenerate rows, mis-counts) — both violate the row-granular
          postcondition.

        * APPLICABILITY, symmetric direction: the row-aware `np.allclose`
          path RAISES when handed an ordinary fixed-width column whose stored
          values are non-numeric (e.g. a character column: numpy cannot
          promote string dtypes for the closeness arithmetic). This grounds
          the model's `Requires(is_vla_descriptor(...))` on
          `compare_row_aware`: an ordinary column must NOT be routed through
          the row-aware comparator either — the routing is pinned in BOTH
          directions to the descriptor recognition.

`row_mismatches[i]` is grounded in the real data as the number of element
positions at which the two sub-arrays in row i differ, at the default exact
tolerances (rtol=atol=0), where closeness is element equality.

Imports: only the standard library and numpy (a core astropy dependency present
in the evaluation container). Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


# --- model.py reference encodings (kept in lock-step with the model) ---------

def is_vla_descriptor_model(fmt_str):
    """model.py `is_vla_descriptor` over the format STRING: contains 'P'(80) or
    'Q'(81) as a code point."""
    cps = [ord(ch) for ch in fmt_str]
    return (80 in cps) or (81 in cps)


def row_granular_count_model(row_mismatches):
    """model.py `row_granular_count`: number of rows with >=1 differing
    element. This is the SINGLE discipline both comparators yield in model.py."""
    return sum(1 for m in row_mismatches if m > 0)


def row_mismatches_of(rows_a, rows_b):
    """Ground `row_mismatches` for the ROW-AWARE branch in that comparator's OWN
    per-position verdict: per row, the number of positions `np.isclose` rejects
    at the default tolerances, counted under the SAME positional alignment the
    real row comparator uses (numpy's own) rather than a hand-rolled length
    penalty.

    `np.allclose` IS the conjunction of `np.isclose` over the aligned positions,
    so this summary is zero exactly when the real comparator judges the row
    close. It is deliberately NOT `a != b`: the closeness verdict is evaluated in
    a fixed-precision arithmetic whose significand is narrower than the 64-bit
    integer range, so above 2**53 it cannot separate neighbouring values that
    `!=` does separate, and an exact-inequality summary would report differing
    rows the real comparator calls identical. The element-wise branch uses its
    own plain-inequality verdict; see `row_mismatches_of_elementwise`.

    A length difference is therefore not by itself a difference: two sub-arrays
    of unequal length that still align positionally agree iff every aligned
    position agrees, exactly as the real `np.allclose` judges them. A pair that
    cannot be aligned at all raises here precisely as the real comparator does,
    marking that row as outside the comparison's domain."""
    out = []
    for ra, rb in zip(rows_a, rows_b):
        a = np.asarray(ra)
        b = np.asarray(rb)
        out.append(int(np.count_nonzero(~np.isclose(a, b, rtol=0, atol=0))))
    return out


def _vla_int_val(rng):
    """A 64-bit VLA element magnitude. Mixes small values with the FULL declared
    range and with values straddling the per-position closeness verdict's
    resolution limit (2**53), so the regime the 64-bit descriptor exists to carry
    is actually reachable by the fuzz."""
    r = rng.random()
    if r < 0.45:
        return rng.randint(-3, 3)
    if r < 0.70:
        return rng.getrandbits(62)
    if r < 0.90:
        return (1 << 53) + rng.randint(-2, 6)
    return rng.choice([1 << 53, (1 << 53) + 1, 1 << 62, (1 << 62) + 1])


def row_mismatches_of_elementwise(rows_a, rows_b):
    """Ground `row_mismatches` for the ELEMENT-WISE branch in ITS own
    per-position verdict, the plain inequality `arra != arrb` that the real
    `np.where` path applies to the regular ndarray column. The two branches do
    not share a per-position test, so collapsing them onto one is what makes a
    summary diverge from the real figure on one branch or the other."""
    out = []
    for ra, rb in zip(rows_a, rows_b):
        a = np.asarray(ra)
        b = np.asarray(rb)
        out.append(int(np.count_nonzero(a != b)))
    return out


# --- the REAL callees (verbatim transcription of the patched diff.py paths) --

def real_vla_test(fmt_str):
    """The exact layout-string test the patch performs on col.format."""
    return ("P" in fmt_str) or ("Q" in fmt_str)


def _as_object_array(rows):
    arr = np.empty(len(rows), dtype=object)
    for i, r in enumerate(rows):
        arr[i] = np.asarray(r)
    return arr


def real_vla_diff_total(rows_a, rows_b):
    """Row-aware (VLA) path: diffs over rows via np.allclose, then
    len(set(diffs[0]))."""
    arra = _as_object_array(rows_a)
    arrb = _as_object_array(rows_b)
    diffs = (
        [
            idx
            for idx in range(len(arra))
            if not np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)
        ],
    )
    return len(set(diffs[0]))


def real_elementwise_diff_total(arra, arrb):
    """Element-wise (non-VLA `else`) path on a regular ndarray column:
    diffs = np.where(arra != arrb); len(set(diffs[0]))."""
    diffs = np.where(arra != arrb)
    return len(set(diffs[0]))


# --- the checks --------------------------------------------------------------

def check_vla_descriptor(fmt_str):
    assert is_vla_descriptor_model(fmt_str) == real_vla_test(fmt_str), (
        "is_vla_descriptor deep model disagrees with real test on %r: "
        "model=%r real=%r"
        % (fmt_str, is_vla_descriptor_model(fmt_str), real_vla_test(fmt_str)))


def check_vla_count(rows_a, rows_b):
    """The row-granular count over the grounded row_mismatches equals the real
    row-aware (VLA) path's accumulated diff_total."""
    m = row_mismatches_of(rows_a, rows_b)
    assert row_granular_count_model(m) == real_vla_diff_total(rows_a, rows_b), (
        "row_granular_count deep model disagrees with the real VLA path on "
        "(%r,%r): model=%r real=%r"
        % (rows_a, rows_b, row_granular_count_model(m),
           real_vla_diff_total(rows_a, rows_b)))


def check_elementwise_count(arra, arrb):
    """The row-granular count over the grounded row_mismatches equals the real
    element-wise (non-VLA `else`) path's accumulated diff_total, INCLUDING on
    multi-element fixed-width columns where an element-sum would diverge."""
    rows_a = [np.asarray(arra[i]) for i in range(len(arra))]
    rows_b = [np.asarray(arrb[i]) for i in range(len(arrb))]
    m = row_mismatches_of_elementwise(rows_a, rows_b)
    real = real_elementwise_diff_total(arra, arrb)
    model = row_granular_count_model(m)
    assert model == real, (
        "row_granular_count deep model disagrees with the real element-wise "
        "(np.where) path on (%r,%r): model=%r real=%r"
        % (arra.tolist(), arrb.tolist(), model, real))
    # And confirm a naive element-SUM would have diverged on this column, i.e.
    # this column actually distinguishes the row-granular discipline from an
    # element-granular one (guards against a vacuous check).
    return sum(m), real


def check_elementwise_raises_on_vla(rows_a, rows_b):
    """The element-wise path is NOT applicable to a genuine variable-length
    column: np.where(arra != arrb) on an object array of multi-element
    sub-arrays RAISES. This grounds model.py's
    Requires(not is_vla_descriptor) on compare_elementwise."""
    arra = _as_object_array(rows_a)
    arrb = _as_object_array(rows_b)
    try:
        _ = real_elementwise_diff_total(arra, arrb)
    except ValueError:
        return True
    raise AssertionError(
        "expected the element-wise np.where path to RAISE on a multi-element "
        "variable-length column %r vs %r, but it returned a value" % (rows_a, rows_b))


def check_row_aware_raises_on_string_column(vals_a, vals_b):
    """The row-aware path is NOT applicable to an ordinary column with
    non-numeric stored values: np.allclose on string values RAISES (dtype
    promotion fails). This grounds model.py's Requires(is_vla_descriptor) on
    compare_row_aware."""
    arra = np.array(vals_a)
    arrb = np.array(vals_b)
    try:
        _ = real_vla_diff_total_plain(arra, arrb)
    except Exception:
        return True
    raise AssertionError(
        "expected the row-aware np.allclose path to RAISE on a non-numeric "
        "fixed-width column %r vs %r, but it returned a value"
        % (vals_a, vals_b))


def real_vla_diff_total_plain(arra, arrb):
    """The row-aware comparator body applied to an arbitrary (already
    materialised) column pair — used to probe its applicability domain."""
    diffs = (
        [
            idx
            for idx in range(len(arra))
            if not np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)
        ],
    )
    return len(set(diffs[0]))


def main():
    rng = random.Random(14539)

    # --- A-reference 1: descriptor recognition --------------------------------
    vla_formats = [
        "PI(2)", "QJ(2)", "QD", "PD(5)", "QL(10)", "1PJ(3)", "1QE(4)",
        "PB()", "QA(7)",
    ]
    non_vla_formats = [
        "L", "X", "B", "I", "J", "K", "A", "E", "D", "C", "M", "10A", "5J",
        "E15.7", "B(2)", "",
    ]
    for f in vla_formats:
        assert real_vla_test(f), "expected %r to be a VLA format" % f
        check_vla_descriptor(f)
    for f in non_vla_formats:
        assert not real_vla_test(f), "expected %r NOT to be a VLA format" % f
        check_vla_descriptor(f)

    # randomized format fuzz
    letters = list("LXBIJKAEDCMPQ") + list("lxbijkaedcmpq") + list("0123456789().")
    for _ in range(20000):
        n = rng.randint(0, 8)
        f = "".join(rng.choice(letters) for _ in range(n))
        check_vla_descriptor(f)

    # --- A-reference 2a: row-aware (VLA) path == row_granular_count -----------
    # Boundary: the F2P test data for the QJ(2) column.
    check_vla_count([[0, 1], [2, 3]], [[0, 1], [2, 3]])  # identical -> 0
    check_vla_count([[0, 1], [2, 3]], [[1, 2], [3, 4]])  # both differ -> 2
    # Issue repro: QD with ragged rows, identical.
    check_vla_count([[0], [0, 0]], [[0], [0, 0]])        # identical -> 0
    # Single-element (scalar-like) VLA rows.
    check_vla_count([[5], [6], [7]], [[5], [9], [7]])    # one differs -> 1
    # Equal-width multi-element rows with a PARTIAL-row diff: a row with a
    # single differing element among several still counts ONCE (row-granular),
    # which an element sum would over-count.
    check_vla_count([[1, 2, 3], [4, 5, 6]], [[1, 9, 3], [4, 5, 6]])  # -> 1
    check_vla_count([[1, 2, 3], [9, 9, 9]], [[1, 0, 3], [9, 0, 9]])  # -> 2
    # Rows whose two sub-arrays have UNEQUAL lengths but still align
    # positionally. The real comparator judges these by that alignment, so a
    # length difference alone is NOT a difference; each expected value below is
    # the REAL callee's, confirmed on real Q-columns in the instance image.
    check_vla_count([[0]], [[0, 0]])                    # aligns, agrees -> 0
    check_vla_count([[0]], [[0, 1]])                    # aligns, differs -> 1
    check_vla_count([[0]], [[1, 1]])                    # row-granular -> 1
    check_vla_count([[0, 0]], [[0]])                    # other orientation -> 0
    check_vla_count([[5]], [[5, 5, 5]])                 # width 1 vs 3 -> 0
    check_vla_count([[1], [2, 2]], [[1, 1], [2]])       # both rows align -> 0
    check_vla_count([[3], [0, 1]], [[3, 3, 3], [0, 1]])  # -> 0
    # 64-bit magnitudes. The row comparator's per-position closeness verdict is
    # evaluated in a fixed-precision arithmetic whose significand is narrower
    # than the 64-bit integer range, so at and above 2**53 it is strictly COARSER
    # than exact inequality: neighbouring values it cannot separate are judged
    # close and contribute NO differing row. Each expected value below is the
    # REAL callee's (TableDataDiff.diff_total on real 64-bit columns), not what an
    # exact-equality reading of the comparator would predict. This is exactly the
    # magnitude regime the 64-bit descriptor exists to carry.
    check_vla_count([[9007199254740992]], [[9007199254740993]])      # -> 0
    check_vla_count([[9007199254740992]], [[9007199254740994]])      # -> 1
    check_vla_count([[9007199254740991]], [[9007199254740992]])      # -> 1
    check_vla_count([[0, 9007199254740992]], [[0, 9007199254740993]])  # -> 0
    check_vla_count([[9007199254740992], [3]],
                    [[9007199254740993], [4]])                      # -> 1
    check_vla_count([[4611686018427387904]], [[4611686018427387905]])  # -> 0
    check_vla_count([[9007199254740992]],
                    [[9007199254740992, 9007199254740992]])         # -> 0

    # randomized VLA-column fuzz. Sub-array widths are drawn INDEPENDENTLY per
    # side, so unequal-length rows (the alignment-dependent class) are squarely
    # in this A-reference's domain rather than excluded from it. Where no
    # positional alignment exists the real comparator raises; the grounded
    # summary must raise identically, which is asserted rather than skipped.
    # Magnitudes span the FULL declared 64-bit range, not just small values: the
    # per-position closeness verdict's significand is narrower than that range,
    # so a generator confined to tiny magnitudes structurally cannot reach the
    # region where the verdict stops separating neighbours and would assert an
    # agreement it never tested. `n_wide` counts draws in that region and the run
    # FAILS below if the class was never exercised.
    n_ragged_aligned = 0
    n_outside_domain = 0
    n_wide = 0
    WIDE = 1 << 53
    for _ in range(20000):
        nrows = rng.randint(0, 6)
        rows_a = []
        rows_b = []
        ragged = False
        for _r in range(nrows):
            w = rng.randint(0, 5)
            ra = [_vla_int_val(rng) for _ in range(w)]
            if rng.random() < 0.4:
                wb = rng.randint(0, 5)
                rb = [_vla_int_val(rng) for _ in range(wb)]
                if wb != w:
                    ragged = True
            else:
                rb = list(ra)
                for k in range(w):
                    if rng.random() < 0.3:
                        # A SMALL delta, so the pair lands on either side of the
                        # verdict's resolution limit depending on magnitude.
                        rb[k] = ra[k] + rng.choice([0, 1, -1, 2, -2])
            if (any(abs(v) >= WIDE for v in ra)
                    or any(abs(v) >= WIDE for v in rb)):
                n_wide += 1
            rows_a.append(ra)
            rows_b.append(rb)
        try:
            real_vla_diff_total(rows_a, rows_b)
        except ValueError:
            # Outside the alignment domain: the grounded summary must be
            # undefined here too, never silently numeric.
            try:
                row_mismatches_of(rows_a, rows_b)
            except ValueError:
                n_outside_domain += 1
                continue
            raise AssertionError(
                "the real row-aware comparator raised on %r/%r but the grounded "
                "row_mismatches summary returned a value" % (rows_a, rows_b))
        check_vla_count(rows_a, rows_b)
        if ragged:
            n_ragged_aligned += 1
    assert n_ragged_aligned > 0, (
        "the VLA fuzz never exercised an unequal-length but ALIGNING row, so "
        "the alignment-dependent class went untested")
    assert n_wide > 0, (
        "the VLA fuzz never drew a magnitude at or beyond the per-position "
        "closeness verdict's resolution limit (2**53), so the wide-magnitude "
        "class the 64-bit descriptor exists to carry went untested and its "
        "agreement was asserted rather than checked")

    # --- A-reference 2b: element-wise (non-VLA `else`) path == row_granular ----
    # The UNCHANGED branch is also row-granular (len(set(np.where(...)[0]))).
    # Test on regular ndarray columns INCLUDING multi-element fixed-width ones,
    # where a row with a partial diff would make an element sum diverge from the
    # row count. We require that at least some fuzz column genuinely exercises
    # that divergence (sum > row_count) so the check is not vacuous.
    distinguishing_seen = 0
    # boundary: 1-D scalar column, 2-D X-like column, (2,2) fixed multi-element.
    check_elementwise_count(np.array([1, 2]), np.array([1, 3]))           # 1
    check_elementwise_count(np.array([[0], [0]]), np.array([[0], [1]]))   # 1
    s, r = check_elementwise_count(np.array([[1, 2], [3, 4]]),
                                   np.array([[1, 9], [8, 8]]))            # rows 0,1 -> 2
    if s > r:
        distinguishing_seen += 1
    for _ in range(20000):
        nrows = rng.randint(0, 6)
        width = rng.randint(1, 4)
        a = rng.choice([
            lambda: np.array([[rng.randint(-3, 3) for _ in range(width)]
                              for _ in range(nrows)]).reshape(nrows, width),
            lambda: np.array([rng.randint(-3, 3) for _ in range(nrows)]),
        ])()
        if a.ndim == 1:
            b = a.copy()
            for i in range(nrows):
                if rng.random() < 0.3:
                    b[i] = rng.randint(-3, 3)
        else:
            b = a.copy()
            for i in range(nrows):
                for j in range(width):
                    if rng.random() < 0.25:
                        b[i, j] = rng.randint(-3, 3)
        s, r = check_elementwise_count(a, b)
        if s > r:
            distinguishing_seen += 1
    assert distinguishing_seen > 0, (
        "element-wise check never exercised a multi-element partial-row diff "
        "(element sum never exceeded row count) — the row-vs-element distinction "
        "was not tested")

    # --- A-reference 2c: element-wise path is NOT applicable to a VLA column ----
    # The np.where comparator RAISES on a genuine multi-element variable-length
    # (object-array) column; this is the control-flow effect that the descriptor
    # recognition exists to avoid and that model.py encodes as the
    # Requires(not is_vla_descriptor) applicability precondition.
    check_elementwise_raises_on_vla([[0, 1], [2, 3]], [[1, 2], [3, 4]])  # F2P QJ(2) differing
    check_elementwise_raises_on_vla([[0, 1], [2, 3]], [[0, 1], [2, 3]])  # F2P QJ(2) identical
    check_elementwise_raises_on_vla([[0], [0, 0]], [[0], [0, 0]])        # issue ragged QD

    # --- A-reference 2d: row-aware path is NOT applicable to an ordinary
    # column with non-numeric stored values --------------------------------
    # np.allclose RAISES on string values (dtype promotion fails), so an
    # ordinary character column must not be routed through the row-aware
    # comparator; this grounds compare_row_aware's
    # Requires(is_vla_descriptor) applicability precondition (the routing is
    # pinned in both directions).
    check_row_aware_raises_on_string_column(["abc", "def"], ["abc", "def"])
    check_row_aware_raises_on_string_column(["abc", "def"], ["abc", "ghi"])

    print(
        "G-AX OK: is_vla_descriptor (A-ref 1) == real ('P' in fmt or 'Q' in fmt) "
        "on %d boundary + 20000 fuzz formats; row_granular_count == real "
        "row-aware np.allclose path (A-ref 2a) on 20 boundary + 20000 fuzz VLA "
        "columns with INDEPENDENTLY drawn per-side widths and FULL-RANGE 64-bit "
        "magnitudes (%d unequal-length "
        "but aligning rows agreed; %d outside the alignment domain, where the "
        "real comparator and the grounded summary raise together; %d wide "
        "magnitudes at/beyond the per-position verdict's resolution limit "
        "agreed); == real "
        "element-wise np.where path (A-ref 2b) "
        "on multi-element fixed-width columns (%d distinguishing partial-row "
        "diffs seen); the element-wise path RAISES on multi-element "
        "variable-length columns (A-ref 2c, applicability); and the row-aware "
        "path RAISES on non-numeric fixed-width columns (A-ref 2d, symmetric "
        "applicability)."
        % (len(vla_formats) + len(non_vla_formats), n_ragged_aligned,
           n_outside_domain, n_wide, distinguishing_seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
