#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-25960 (nagini).

Runs INSIDE the instance image with the gold patch already applied by the gate
(apply_gold=True, PYTHONPATH=/testbed), so `import matplotlib` resolves the
PATCHED in-tree source.

WHAT IS DIFFED
--------------
SHADOW — the `# impl-start` / `# impl-end` region of `model.py`, copied
VERBATIM (see `impl_grid_cell_placement` below; only the contract calls were
deleted, and there were none inside the region itself), together with the four
`@Pure` helpers of the `# pure-start` region it is checked against
(`col_left/col_right/row_top/row_bottom`, contracts stripped). No
transliteration, no restructuring, no renaming of the arithmetic: the model IS
Python here. `model.py` has NO `@ContractOnly` callee (mapping.md §3.2: the
axioms region is empty), so nothing had to be replaced by a real-function call;
the deep geometry it would otherwise axiomatize is exercised end-to-end because
the ORACLE below is the real function that computes it.

ORACLE — the REAL patched repo function, CALLED, not transliterated:

    matplotlib.figure.Figure.subfigures   (lib/matplotlib/figure.py:1543,
    the gap-honouring placement the gold patch adds at body lines 1583-1601)

This is the symbol mapping.md §1 names as the modeled changed function, and it
is drivable in-container: `Figure()` + `.subfigures(nrows, ncols, squeeze=False,
wspace=..., hspace=...)` needs no display, no live session, and no
pre-constructed container object. We therefore do NOT transliterate anything.
(The velvet sibling transliterates the reduced `GridSpec.get_grid_positions`
arithmetic because its shadow is Lean-side and it only refutes the R/I leg;
here we drive the whole patched path — GridSpec construction with the patch's
`left=0, right=1, bottom=0, top=1`, `get_grid_positions`, `Bbox.from_extents`,
`SubFigure._redo_transform_rel_fig` — so the axiom about `get_grid_positions`
is exercised rather than assumed. The gap branch is guarded by
`get_layout_engine() is None and (wspace is not None or hspace is not None)`;
we assert the figure has no layout engine and always pass both gap arguments
explicitly, so the patched branch is taken on every single call. If that branch
were absent (the pre-patch behaviour: column i at i/ncols, no gap), this check
FAILS — verified out-of-band on host matplotlib: 104 of the first 50
configurations' cells differ between the shadow and the gap-less placement, far
above the 1e-12 tolerance used here.)

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
* counts/indices: the model carries `nrows, ncols, j, i` as integer-valued
  reals (`--float-encoding=real` forbids `float(int)` coercion). We generate the
  repo's `int` nrows/ncols and feed the shadow the integer-valued reals they
  denote; cells are enumerated over the same ranges the patch's `zip` walks
  (row j from the TOP, column i left-to-right).
* `cw` / `ch`: model INPUTS pinned by the linear equations
  `cw*(ncols+wspace*(ncols-1))==1` and `ch*(nrows+hspace*(nrows-1))==1`
  (Z3 cannot discharge reciprocal facts under real encoding). Inverting the
  bridge means producing, for each generated `(nrows, ncols, wspace, hspace)`,
  the unique reals satisfying them — i.e. the repo's
  `cell_w = tot_width/(ncols+wspace*(ncols-1))` with `tot_width = 1` (the
  patch's `left=0, right=1`), and likewise `cell_h`. Because
  `--float-encoding=real` means the model's arithmetic is EXACT real
  arithmetic, the shadow runs over exact rationals (class `Real` below, a
  `Fraction` carrier so that the literals `1.0` inside the verbatim impl stay
  exact), and every generated tuple is ASSERTED to satisfy each `Requires`
  clause exactly before it is used. No input is admitted that the model's
  precondition does not accept, and the domain is never narrowed to dodge a
  disagreement.
* `Bbox`: the repo returns SubFigure objects; the observable is each one's
  relative bbox, recovered from the pixel bbox exactly as the F2P test reads it
  (`sub_figs[j, i].bbox.min == [left*w, bottom*h]`, `.max == [right*w, top*h]`):
  `left = sf.bbox.min[0]/W`, `bottom = sf.bbox.min[1]/H`,
  `right = sf.bbox.max[0]/W`, `top = sf.bbox.max[1]/H` with `(W, H) =
  fig.bbox.max`. That is the inverse of the `CellRect(left, bottom, right, top)`
  carrier.

FLOAT BAND
----------
Exact-rational shadow vs float oracle: each edge is a rational function of
`(nrows, ncols, wspace, hspace)` with no cross-cell accumulation, so the two
legs agree to a few ulps. Comparison uses ABS_TOL = 1e-12 — six orders of
magnitude tighter than the `np.testing.assert_allclose` default (rtol 1e-7) the
F2P test asserts with, and four orders above the worst deviation observed
out-of-band (3.3e-16 over 4709 cells). The script prints the worst deviation it
actually saw, so a silently loosening oracle would be visible. The
discriminating properties (grid fills [0,1]; a positive requested gap STRICTLY
separates consecutive cells; a zero gap makes them abut) are checked EXACTLY on
the rational shadow, with no tolerance at all.

INPUTS
------
The modeled input space is infinite (`wspace, hspace` range over the
non-negative reals), so: boundary/sentinel catalogue first — the exact F2P
shape (2x3, wspace=1/6, hspace=1/2), the singleton grid 1x1, single row, single
column, zero gaps (cells abut), tiny gaps, unit gaps, very large gaps, and every
index boundary (i=0, i=ncols-1, j=0, j=nrows-1) — then seeded fuzz to reach
>= 1e5 cell-level checks. Each cell is one distinct Requires-satisfying model
input tuple. The impl region is straight-line (no branches), so branch coverage
is trivially total; index/gap boundary coverage is what the catalogue buys, and
it is asserted to be non-empty at the end.

Exit 0 iff zero disagreements. stdlib + matplotlib only (no hypothesis needed).
Pinned seed: SEED below, recorded in mapping.md § G-CONF.
"""
import random
import sys
from fractions import Fraction

SEED = 25960
TARGET_CELLS = 100_000       # >= 1e5 Requires-satisfying model inputs
ABS_TOL = 1e-12
MAX_REPORTED = 10


# --------------------------------------------------------------------------
# Exact-real carrier.  `--float-encoding=real` (mapping.md §2) means model
# arithmetic is exact real arithmetic and the literals `1.0` in the verbatim
# impl denote the real 1.  A Fraction subclass gives exactly that while
# letting the impl body below stay character-for-character the model's.
# (model.py's impl region uses no PSeq / ToSeq, so no sequence shim is needed.)
# --------------------------------------------------------------------------
class Real(Fraction):
    def __add__(self, o):
        return Real(Fraction(self) + Fraction(o))

    def __radd__(self, o):
        return Real(Fraction(o) + Fraction(self))

    def __sub__(self, o):
        return Real(Fraction(self) - Fraction(o))

    def __rsub__(self, o):
        return Real(Fraction(o) - Fraction(self))

    def __mul__(self, o):
        return Real(Fraction(self) * Fraction(o))

    def __rmul__(self, o):
        return Real(Fraction(o) * Fraction(self))

    def __truediv__(self, o):
        return Real(Fraction(self) / Fraction(o))

    def __rtruediv__(self, o):
        return Real(Fraction(o) / Fraction(self))

    def __neg__(self):
        return Real(-Fraction(self))


# --------------------------------------------------------------------------
# SHADOW — model.py `# pure-start`..`# pure-end` helpers, contracts stripped.
# --------------------------------------------------------------------------
def col_left(i, wspace, cw):
    return i * cw * (1.0 + wspace)


def col_right(i, wspace, cw):
    return col_left(i, wspace, cw) + cw


def row_top(j, hspace, ch):
    return 1.0 - j * ch * (1.0 + hspace)


def row_bottom(j, hspace, ch):
    return row_top(j, hspace, ch) - ch


class CellRect:
    """model.py's CellRect carrier (contracts stripped)."""

    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top


# --------------------------------------------------------------------------
# SHADOW — model.py `# impl-start`..`# impl-end`, VERBATIM.
# --------------------------------------------------------------------------
def impl_grid_cell_placement(nrows, ncols, j, i, wspace, hspace, cw, ch):
    # impl-start
    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
    # The grid-fill and positive-gap postconditions follow from the cell-size
    # normalization equations.
    left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)
    # impl-end


# --------------------------------------------------------------------------
# Requires of grid_cell_placement, checked EXACTLY on the bridged inputs.
# --------------------------------------------------------------------------
def requires_hold(nrows, ncols, j, i, wspace, hspace, cw, ch):
    """Every Requires clause of model.py::grid_cell_placement, in order."""
    return (nrows >= 1.0 and ncols >= 1.0
            and 0.0 <= j and j <= nrows - 1.0
            and 0.0 <= i and i <= ncols - 1.0
            and wspace >= 0.0
            and hspace >= 0.0
            and cw > 0.0
            and ch > 0.0
            and cw * (ncols + wspace * (ncols - 1.0)) == 1.0
            and ch * (nrows + hspace * (nrows - 1.0)) == 1.0)


def bridge(nrows_i, ncols_i, ws_f, hs_f):
    """mapping.md §2 inverted: repo (int, int, float, float) -> model reals,
    with cw/ch the unique reals pinned by the normalization equations."""
    nrows = Real(nrows_i)
    ncols = Real(ncols_i)
    wspace = Real(Fraction(ws_f))     # exact value of the float the repo gets
    hspace = Real(Fraction(hs_f))
    cw = Real(1) / (ncols + wspace * (ncols - 1.0))
    ch = Real(1) / (nrows + hspace * (nrows - 1.0))
    return nrows, ncols, wspace, hspace, cw, ch


# --------------------------------------------------------------------------
# ORACLE — the REAL patched Figure.subfigures, called.
# --------------------------------------------------------------------------
def real_relative_bboxes(nrows, ncols, ws, hs):
    """Drive the patched `Figure.subfigures` and return, per (j, i), the cell's
    relative bbox (left, bottom, right, top) the way the F2P test reads it."""
    from matplotlib.figure import Figure

    fig = Figure()
    if fig.get_layout_engine() is not None:
        raise RuntimeError("figure unexpectedly has a layout engine; the "
                           "patched gap branch would be skipped")
    W, H = fig.bbox.max
    sfs = fig.subfigures(nrows, ncols, squeeze=False, wspace=ws, hspace=hs)
    out = {}
    for j in range(nrows):
        for i in range(ncols):
            sf = sfs[j, i]
            x0, y0 = sf.bbox.min
            x1, y1 = sf.bbox.max
            out[(j, i)] = (x0 / W, y0 / H, x1 / W, y1 / H)
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")

    rng = random.Random(SEED)
    cells = 0
    configs = 0
    worst = 0.0
    worst_at = None
    disagreements = []
    boundary_hits = {"i=0": 0, "i=ncols-1": 0, "j=0": 0, "j=nrows-1": 0,
                     "wspace=0": 0, "hspace=0": 0, "wspace>0": 0,
                     "hspace>0": 0, "1x1": 0}

    def check_config(nrows, ncols, ws, hs, tag):
        nonlocal cells, configs, worst, worst_at
        n, nc, wspace, hspace, cw, ch = bridge(nrows, ncols, ws, hs)
        # Never admit an input outside the model's precondition, and never
        # weaken the precondition: a tuple that fails it is a bridge bug.
        for j in range(nrows):
            for i in range(ncols):
                if not requires_hold(n, nc, Real(j), Real(i),
                                     wspace, hspace, cw, ch):
                    disagreements.append(
                        f"BRIDGE BUG: Requires violated for nrows={nrows} "
                        f"ncols={ncols} wspace={ws!r} hspace={hs!r} "
                        f"j={j} i={i}")
                    return
        real = real_relative_bboxes(nrows, ncols, ws, hs)
        configs += 1
        if nrows == 1 and ncols == 1:
            boundary_hits["1x1"] += 1
        boundary_hits["wspace=0" if wspace == 0 else "wspace>0"] += 1
        boundary_hits["hspace=0" if hspace == 0 else "hspace>0"] += 1

        for j in range(nrows):
            for i in range(ncols):
                got = impl_grid_cell_placement(n, nc, Real(j), Real(i),
                                               wspace, hspace, cw, ch)
                shadow = (got.left, got.bottom, got.right, got.top)
                oracle = real[(j, i)]
                cells += 1
                if i == 0:
                    boundary_hits["i=0"] += 1
                if i == ncols - 1:
                    boundary_hits["i=ncols-1"] += 1
                if j == 0:
                    boundary_hits["j=0"] += 1
                if j == nrows - 1:
                    boundary_hits["j=nrows-1"] += 1

                dev = max(abs(float(a) - float(b))
                          for a, b in zip(shadow, oracle))
                if dev > worst:
                    worst, worst_at = dev, (nrows, ncols, ws, hs, j, i)
                if dev > ABS_TOL:
                    disagreements.append(
                        f"[{tag}] nrows={nrows} ncols={ncols} wspace={ws!r} "
                        f"hspace={hs!r} cell(j={j}, i={i}): "
                        f"shadow={tuple(float(v) for v in shadow)} "
                        f"oracle={tuple(float(v) for v in oracle)} "
                        f"maxdev={dev:g}")

                # The pure helpers must agree with the impl (exactly), and the
                # discriminating properties hold exactly on the rationals.
                if (got.left != col_left(Real(i), wspace, cw)
                        or got.right != col_right(Real(i), wspace, cw)
                        or got.top != row_top(Real(j), hspace, ch)
                        or got.bottom != row_bottom(Real(j), hspace, ch)):
                    disagreements.append(
                        f"[{tag}] impl != pure helpers at nrows={nrows} "
                        f"ncols={ncols} j={j} i={i}")
                if i == 0 and got.left != 0:
                    disagreements.append(f"[{tag}] left col not at 0: {got.left}")
                if i == ncols - 1 and got.right != 1:
                    disagreements.append(f"[{tag}] right col not at 1: {got.right}")
                if j == 0 and got.top != 1:
                    disagreements.append(f"[{tag}] top row not at 1: {got.top}")
                if j == nrows - 1 and got.bottom != 0:
                    disagreements.append(f"[{tag}] bottom row not at 0: {got.bottom}")
                if i <= ncols - 2:
                    nxt = col_left(Real(i) + 1.0, wspace, cw)
                    if wspace > 0 and not got.right < nxt:
                        disagreements.append(
                            f"[{tag}] positive wspace={ws!r} left no column "
                            f"gap at i={i}: right={got.right} next={nxt}")
                    if wspace == 0 and got.right != nxt:
                        disagreements.append(
                            f"[{tag}] wspace=0 columns do not abut at i={i}")
                if j <= nrows - 2:
                    nxt = row_top(Real(j) + 1.0, hspace, ch)
                    if hspace > 0 and not nxt < got.bottom:
                        disagreements.append(
                            f"[{tag}] positive hspace={hs!r} left no row gap "
                            f"at j={j}: bottom={got.bottom} next_top={nxt}")
                    if hspace == 0 and nxt != got.bottom:
                        disagreements.append(
                            f"[{tag}] hspace=0 rows do not abut at j={j}")

    # ---------------- boundary / sentinel catalogue -----------------------
    boundary = [
        (2, 3, 1 / 6., 0.5, "F2P"),           # the exact F2P configuration
        (1, 1, 0.0, 0.0, "singleton"),
        (1, 1, 0.5, 0.5, "singleton-gaps-irrelevant"),
        (1, 2, 0.0, 0.0, "single-row-zero-gap"),
        (2, 1, 0.0, 0.0, "single-col-zero-gap"),
        (1, 6, 1.0, 0.0, "single-row-unit-gap"),
        (6, 1, 0.0, 1.0, "single-col-unit-gap"),
        (2, 2, 0.0, 0.0, "abutting"),
        (3, 3, 0.0, 0.5, "zero-wspace-positive-hspace"),
        (3, 3, 0.5, 0.0, "positive-wspace-zero-hspace"),
        (4, 5, 1e-9, 1e-9, "tiny-gaps"),
        (5, 4, 1.0, 1.0, "unit-gaps"),
        (2, 2, 100.0, 100.0, "huge-gaps"),
        (6, 6, 2.0, 0.25, "6x6"),
        (1, 12, 1 / 3., 0.0, "wide-row"),
        (12, 1, 0.0, 1 / 7., "tall-col"),
    ]
    for (nr, nc, ws, hs, tag) in boundary:
        check_config(nr, nc, ws, hs, tag)

    # ---------------- seeded fuzz to reach >= 1e5 cells -------------------
    gap_pool = [0.0, 1e-9, 0.01, 0.1, 1 / 6., 0.2, 0.25, 1 / 3., 0.5, 0.75,
                1.0, 1.5, 2.0, 5.0, 20.0]
    while cells < TARGET_CELLS and len(disagreements) <= MAX_REPORTED:
        nr = rng.randint(1, 6)
        nc = rng.randint(1, 6)
        ws = rng.choice(gap_pool) if rng.random() < 0.5 else rng.random() * 3.0
        hs = rng.choice(gap_pool) if rng.random() < 0.5 else rng.random() * 3.0
        check_config(nr, nc, ws, hs, "fuzz")

    missing = [k for k, v in boundary_hits.items() if v == 0]
    if missing:
        disagreements.append(
            f"COVERAGE GAP: boundary classes never exercised: {missing}")

    if disagreements:
        print(f"G-CONF FAIL: {len(disagreements)} disagreement(s) over {cells} "
              f"cell checks in {configs} grid configurations (seed={SEED}).")
        for d in disagreements[:MAX_REPORTED]:
            print("  -", d)
        print('{"status": "fail", "checks": %d, "configs": %d, '
              '"disagreements": %d, "seed": %d}'
              % (cells, configs, len(disagreements), SEED))
        return 1

    print(f"G-CONF OK: verbatim impl region of model.py agrees with the REAL "
          f"patched Figure.subfigures on {cells} Requires-satisfying cell "
          f"inputs across {configs} grid configurations "
          f"(boundary + F2P + seeded fuzz, seed={SEED}); worst deviation "
          f"{worst:g} at (nrows,ncols,wspace,hspace,j,i)={worst_at} "
          f"(tol {ABS_TOL:g}); grid-fill and strict positive-gap separation "
          f"checked exactly; 0 disagreements.")
    print('{"status": "pass", "checks": %d, "configs": %d, '
          '"disagreements": 0, "worst_deviation": %r, "abs_tol": %r, '
          '"seed": %d, "oracle": "matplotlib.figure.Figure.subfigures (called)"}'
          % (cells, configs, worst, ABS_TOL, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
