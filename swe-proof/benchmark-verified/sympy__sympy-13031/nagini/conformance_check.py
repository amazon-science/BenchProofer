#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13031 (nagini).

SHADOW — the impl regions of `model.py`, copied VERBATIM with only the contract
calls removed. On nagini the model IS Python, so nothing is transliterated: the
bodies of `concat_right` / `concat_below` below are byte-for-byte the lines
between `# impl-start` and `# impl-end` in model.py (including the recursive
self-call through the normalisation rebuild), and `Mat.__init__` /
`ShapeMismatch` are the model's own carrier declarations minus their
`Requires`/`Ensures`. The model has an EMPTY axioms region and an EMPTY pure
region, so there is no `@ContractOnly` callee to bridge and no `@Pure` helper to
copy: the whole impl is directly executable, hence `conf_skip` stays false and
this gate carries full weight.

ORACLE — the REAL patched repo functions, CALLED, not reimplemented:
  * `SparseMatrix.row_join` — sympy/matrices/sparse.py:1161 (mapping.md §1)
  * `SparseMatrix.col_join` — sympy/matrices/sparse.py:949
The gate applies the gold patch to /testbed and sets PYTHONPATH before this
runs; `_assert_patched()` below refuses to report a verdict unless the loaded
source really contains the patched guard, so a green run cannot come from
unpatched code.

TYPE BRIDGE (mapping.md §2, inverted). The carrier `Mat(rows, cols, held, rsum,
csum)` abstracts a matrix to its shape plus three facets of its HELD-CELL
population. A cell counts as held exactly when the repo's own retention
predicate keeps it, namely when its value TESTS TRUE — the predicate the
`SparseMatrix` constructor applies to every cell it is given
(`if value:` / `if v:` at sparse.py:58, 66, 76, 87) and the predicate the
merge loop applies to a non-sparse `other` (`if v:` at sparse.py:1002 for
col_join and sparse.py:1210 for row_join). It is NOT `v != 0`: for a sympy
object those two predicates split (`S.false`, `Eq(1, 2)`, `EmptySet()`,
`FiniteSet()` all test false while comparing unequal to 0), and it is the
truth-test reading that the repo maintains and that `SparseMatrix.__eq__`
compares through (`self._smat == MutableSparseMatrix(other)._smat`,
sparse.py:92-100) — so it is the reading under which the abstraction is a
FUNCTION and the F2P equality assertion is an observation of it.
`held_cells()` below applies that predicate through the PUBLIC element accessor
`m[i, j]`, so a dense `other` and a sparse one are measured identically, and
`_check_reading()` MEASURES that this agrees cell-for-cell with the repo's own
sparse image on the whole payload catalogue (including the falsy-but-unequal-to-
zero class) rather than assuming it.

Bridge down: `Mat(r, c, ...) -> SparseMatrix(r, c, payload)`, optionally a dense
`Matrix` as `other` (which drives the real method's
`not isinstance(B, SparseMatrix)` copy branch). Bridge up: the concrete result is
observed as `(rows, cols, held, rsum, csum)` where `rsum` / `csum` are the sums
of the row / column indices of the held cells — the facets that pin WHERE the
merge puts each operand's cells, not merely how many survive. `ShapeMismatch`
corresponds to `sympy.matrices.common.ShapeError`. The abstraction is applied to
the concrete OPERANDS too, so the shadow is handed exactly the facets the oracle
received; every generated input therefore satisfies the model's Requires
(non-negative facets, "a zero dimension holds nothing", "an empty population
sums to zero") by construction.

VALUE DOMAIN. The payload catalogue deliberately spans the axis on which the two
candidate retention predicates differ, because that is the axis a shape-and-count
bridge cannot see: plain ints, rationals, radicals, symbols, `oo` / `nan` / `zoo`,
AND the falsy-but-unequal-to-zero class `S.false` / `Eq(1, 2)` / `EmptySet()` /
`FiniteSet()`. A cell whose truth value is INDETERMINATE (e.g. `x > 0`) is
outside the modelled type altogether: it has no sparse image at all, so the
abstraction is undefined on it and the real callee raises `TypeError` rather than
returning. `_check_indeterminate()` measures exactly that agreement (both the
abstraction and the callee refuse), so the domain boundary is recorded rather
than quietly assumed.

NOT A STATEMENT ABOUT ONE CLASS. Because the facets are read through the public
element accessor, they are defined for every matrix class in the repo, and the
behaviour the model states is a property of CONCATENATION rather than of a
particular container. `_check_class_agnostic()` measures that: the same shadow is
run against the general-purpose DENSE class's `row_join` / `col_join` over the
whole shape grid crossed with the payload catalogue, and the run FAILS if it
disagrees there. So the modelled behaviour is exactly the behaviour the task
statement's own `hstack` / `vstack` example describes, and the spec view singles
out no implementation site.

INPUTS (>= 1e5 satisfying the Requires). The Requires-domain is infinite, so it
is covered as: (1) an EXHAUSTIVE enumeration of the shape grid {0..7}^4 for both
functions (4096 operand pairs each) — every degenerate zero-row/zero-column
combination and every branch of both impls; (2) an explicit boundary catalogue
(empty, singleton, the exact F2P chain shapes, the normalisation branch, the
raise branch, the branch-overlap case `a.cols == 0 and a.rows == b.rows`), each
also re-run with NON-EMPTY payloads from every payload class on both operands
and with a dense `other`; (3) seeded fuzz over mixed magnitudes, payload classes
and sparse/dense `other`, biased onto each branch; (4) end-to-end
`hstack`/`vstack` chains against the SHADOW folded over the same operand list,
including the literal F2P chains, and including chains whose parts hold cells so
the placement facets are non-trivial; (5) the literal F2P content case.
All six impl branches are recorded by tracing the shadow, and the run FAILS if
any was never taken.

Pinned seed: 13031 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + sympy only.
"""
import json
import random
import sys

SEED = 13031
GRID = 8            # exhaustive shape grid {0..GRID-1}^4, both functions
N_TARGET = 100000   # minimum Requires-satisfying observations
MAX_REPORT = 6


# ---------------------------------------------------------------------------
# SHADOW: model.py's carrier + impl regions, verbatim, contracts stripped.
# ---------------------------------------------------------------------------

class ShapeMismatch(Exception):
    """Raised when the two operands cannot be concatenated because they
    disagree on the shared dimension and no degenerate normalisation applies."""
    pass


class Mat:
    def __init__(self, rows, cols, held, rsum, csum):
        self.rows = rows
        self.cols = cols
        self.held = held
        self.rsum = rsum
        self.csum = csum


# Branch coverage is recorded by TRACING the shadow's own line executions (see
# `_tracer` / `branch_coverage` below) rather than by editing the copied bodies,
# so the two impl regions below are byte-identical to model.py's. Each branch is
# identified by a LANDMARK substring; the landmark's physical line (plus the
# continuation lines of a statement that spans several) is resolved from this
# file at run time, so no line number is hard-coded.
BRANCH_LANDMARK = {
    "right_norm":  ("concat_right", "base = Mat(b.rows, 0, 0, 0, 0)", 1),
    "right_raise": ("concat_right", "raise ShapeMismatch()", 1),
    "right_sum":   ("concat_right", "return Mat(a.rows, a.cols + b.cols,", 2),
    "below_norm":  ("concat_below", "base = Mat(0, b.cols, 0, 0, 0)", 1),
    "below_raise": ("concat_below", "raise ShapeMismatch()", 1),
    "below_sum":   ("concat_below", "return Mat(a.rows + b.rows, a.cols,", 2),
}
_COVERED = set()


def concat_right(a, b):
    # impl-start (model.py, verbatim; contracts above it stripped)
    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
    # impl-end


def concat_below(a, b):
    # impl-start (model.py, verbatim; contracts above it stripped)
    if a.rows == 0 and a.cols != b.cols:
        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
        return concat_below(base, b)
    if a.cols != b.cols:
        raise ShapeMismatch()
    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
    # impl-end


# Nothing above this line was added to, removed from, or reordered within the
# two copied impl regions; branch coverage is observed from outside instead:

def _tracer(frame, event, arg):
    if event == "line":
        _COVERED.add((frame.f_code.co_name, frame.f_lineno))
    return _tracer


def _landmark_lines():
    """branch -> (function name, set of physical linenos) resolved by scanning
    THIS file for each branch's landmark substring INSIDE that branch's own
    function body. A statement that spans several physical lines contributes all
    of them, so the answer does not depend on which line the interpreter reports
    for a multi-line statement."""
    with open(__file__) as fh:
        lines = fh.readlines()
    bodies = {}
    for i, ln in enumerate(lines):
        if ln.startswith("def concat_right(") or ln.startswith("def concat_below("):
            fname = ln[4:ln.index("(")]
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("# impl-end"):
                j += 1
            bodies[fname] = (i + 1, j + 1)
    out = {}
    for branch in BRANCH_LANDMARK:
        fname, landmark, span = BRANCH_LANDMARK[branch]
        lo, hi = bodies[fname]
        hits = [i + 1 for i in range(lo, hi)
                if landmark in lines[i] and not lines[i].lstrip().startswith("#")]
        if len(hits) != 1:
            raise SystemExit("G-CONF ERROR: landmark %r for %s resolved to %d "
                             "lines in %s (expected 1) — the copied impl region "
                             "drifted" % (landmark, branch, len(hits), fname))
        out[branch] = (fname, set(range(hits[0], hits[0] + span)))
    return out


_LANDMARKS = _landmark_lines()


def branch_coverage():
    """Which impl branches the inputs actually executed (by traced line)."""
    out = {}
    for branch in _LANDMARKS:
        fname, linenos = _LANDMARKS[branch]
        out[branch] = any((fname, n) in _COVERED for n in linenos)
    return out


def shadow(fn, a_abs, b_abs):
    """Run the shadow on the abstract carrier.
    -> (rows, cols, held, rsum, csum) or None (raise).

    Traced, so the branch actually taken inside the verbatim region is recorded
    without touching the region itself.
    """
    sys.settrace(_tracer)
    try:
        r = fn(Mat(*a_abs), Mat(*b_abs))
    except ShapeMismatch:
        return None
    finally:
        sys.settrace(None)
    return (r.rows, r.cols, r.held, r.rsum, r.csum)


# ---------------------------------------------------------------------------
# TYPE BRIDGE (mapping.md §2, inverted) + ORACLE (the real patched functions)
# ---------------------------------------------------------------------------

def _assert_patched(SparseMatrix):
    """Refuse to certify anything unless the loaded repo really is patched."""
    import inspect
    for meth in (SparseMatrix.row_join, SparseMatrix.col_join):
        src = inspect.getsource(meth)
        if "A null matrix can always be stacked" not in src:
            raise SystemExit("G-CONF ERROR: %s is not the patched source; the "
                             "oracle would be wrong" % meth.__name__)


def held_cells(m):
    """The coordinates of the cells `m` HOLDS, under the repo's own retention
    predicate: a cell is held iff its value TESTS TRUE (sparse.py:58/66/76/87
    in the constructor, sparse.py:1002/1210 in the merge). Read through the
    PUBLIC element accessor, so a dense and a sparse operand are measured the
    same way. NOT `m[i, j] != 0`: see the module docstring."""
    out = []
    for i in range(m.rows):
        for j in range(m.cols):
            if m[i, j]:
                out.append((i, j))
    return out


def abstract(m):
    """Bridge up: matrix -> Mat facets (rows, cols, held, rsum, csum)."""
    cells = held_cells(m)
    return (m.rows, m.cols, len(cells),
            sum(i for (i, j) in cells), sum(j for (i, j) in cells))


def alt_abstract_nonzero(m):
    """The REJECTED alternative bridge up, kept as an executable negative
    control: `held` read as "unequal to zero" instead of "tests true". It is
    what `_check_reading` / negative control (e) demonstrate is NOT a function
    of the real callee — see the module docstring and mapping.md §2."""
    cells = [(i, j) for i in range(m.rows) for j in range(m.cols)
             if m[i, j] != 0]
    return (m.rows, m.cols, len(cells),
            sum(i for (i, j) in cells), sum(j for (i, j) in cells))


def oracle(ShapeError, method_name, a_real, b_real):
    """CALL the real patched repo method.
    -> (rows, cols, held, rsum, csum) or None (ShapeError)."""
    try:
        res = getattr(a_real, method_name)(b_real)
    except ShapeError:
        return None
    return abstract(res)


# --- payload catalogue: the VALUE axis the two readings split on -------------

def payload_classes(S, Eq, sqrt, EmptySet, FiniteSet, oo, nan, zoo):
    """value class -> list of cell values. `falsy` is the class on which
    "tests true" and "unequal to zero" DISAGREE; the others are the class on
    which they agree."""
    return {
        "int":     [-7, -2, -1, 1, 3, 5, 11],
        "exotic":  [S.Half, sqrt(2), S.Pi, oo, nan, zoo, S.true],
        "falsy":   [S.false, Eq(1, 2), EmptySet(), FiniteSet()],
        "mixed":   [1, -7, S.false, Eq(1, 2), S.Half, EmptySet(), S.true,
                    FiniteSet(), oo],
    }


def payload(rng, rows, cols, vals):
    """A concrete cell payload for a (rows, cols) operand (bridge down)."""
    smat = {}
    if rows == 0 or cols == 0 or not vals:
        return smat
    for _ in range(rng.randint(1, max(1, min(6, rows * cols)))):
        smat[(rng.randrange(rows), rng.randrange(cols))] = rng.choice(vals)
    return smat


def to_real(SparseMatrix, Matrix, rows, cols, smat=None, dense=False):
    """Bridge down: the abstract shape + payload -> the concrete repo value.
    A sparse operand is built through the SparseMatrix constructor (which
    applies the repo's own retention predicate); a dense one is built as a flat
    list, so a falsy-but-unequal-to-zero cell really is present in `_mat` and
    really does reach the merge's `if v:` filter."""
    if not smat:
        return (Matrix if dense else SparseMatrix).zeros(rows, cols)
    if dense:
        flat = [0] * (rows * cols)
        for (i, j) in smat:
            flat[i * cols + j] = smat[(i, j)]
        return Matrix(rows, cols, flat)
    return SparseMatrix(rows, cols, dict(smat))


# ---------------------------------------------------------------------------
# differential driver
# ---------------------------------------------------------------------------

class Diff(object):
    def __init__(self):
        self.count = 0
        self.bad = []

    def check(self, SparseMatrix, Matrix, ShapeError, which, ar, ac, br, bc,
              a_smat=None, b_smat=None, dense_other=False):
        fn, method = ((concat_right, "row_join") if which == "right"
                      else (concat_below, "col_join"))
        a_real = to_real(SparseMatrix, Matrix, ar, ac, a_smat)
        b_real = to_real(SparseMatrix, Matrix, br, bc, b_smat, dense_other)
        # the abstraction of the CONCRETE operands (bridge up on the inputs), so
        # the shadow sees exactly the facets the oracle was handed
        exp = shadow(fn, abstract(a_real), abstract(b_real))
        got = oracle(ShapeError, method, a_real, b_real)
        self.count += 1
        if got != exp:
            self.bad.append(
                ("%s a=(%d,%d)%s b=(%d,%d)%s%s  shadow=%s  real=%s"
                 % (method, ar, ac, "" if not a_smat else repr(a_smat),
                    br, bc, "" if not b_smat else repr(b_smat),
                    " dense_other" if dense_other else "",
                    "ShapeMismatch" if exp is None else exp,
                    "ShapeError" if got is None else got)))
        return got == exp


def fold_shadow(fn, operands):
    """The shadow folded over an operand list == the unchanged hstack/vstack
    reduce (mapping.md: hstack == reduce(row_join, ...))."""
    acc = Mat(*operands[0])
    for facets in operands[1:]:
        acc = fn(acc, Mat(*facets))
    return (acc.rows, acc.cols, acc.held, acc.rsum, acc.csum)


def _check_reading(d, SparseMatrix, Matrix, classes, rng):
    """MEASURE that the bridge's retention predicate is the repo's own: for
    every payload class, the cells `held_cells` reports are exactly the keys of
    the matrix's sparse image, for a sparse AND for a dense operand. This is the
    step that makes the abstraction's well-definedness a measurement rather than
    a claim — and it is where the "unequal to zero" reading is shown to differ."""
    from sympy.matrices import MutableSparseMatrix
    splits = 0
    for cname in sorted(classes):
        vals = classes[cname]
        for _ in range(24):
            r, c = rng.randint(1, 4), rng.randint(1, 4)
            smat = payload(rng, r, c, vals)
            for dense in (False, True):
                m = to_real(SparseMatrix, Matrix, r, c, smat, dense)
                image = sorted(MutableSparseMatrix(m)._smat.keys())
                if sorted(held_cells(m)) != image:
                    d.bad.append(
                        "bridge retention predicate != repo sparse image: "
                        "%s %s payload=%r held=%r image=%r"
                        % ("dense" if dense else "sparse", cname, smat,
                           sorted(held_cells(m)), image))
                if abstract(m) != alt_abstract_nonzero(m):
                    splits += 1
            d.count += 1
    return splits


def _check_indeterminate(d, SparseMatrix, Matrix):
    """MEASURE the domain boundary: a cell whose truth value is INDETERMINATE
    has no sparse image, so the abstraction is undefined on it — and the real
    callee likewise refuses (TypeError) instead of returning. Model and repo
    agree that such a value is not representable, so it is outside the modelled
    type rather than a case the spec gets wrong."""
    from sympy import Symbol
    from sympy.matrices import MutableSparseMatrix
    x = Symbol('x')
    m = Matrix(1, 1, [x > 0])
    probes = [
        ("abstraction", lambda: abstract(m)),
        ("sparse image", lambda: MutableSparseMatrix(m)),
        ("row_join", lambda: SparseMatrix.zeros(1, 0).row_join(m)),
        ("col_join", lambda: SparseMatrix.zeros(0, 1).col_join(m)),
    ]
    for (label, fn) in probes:
        d.count += 1
        try:
            fn()
        except TypeError:
            continue
        d.bad.append("indeterminate-truth cell: %s did NOT refuse, so the "
                     "domain boundary recorded in mapping.md is wrong" % label)


def _check_class_agnostic(d, Matrix, ShapeError, classes, rng):
    """MEASURE that the spec is a statement about CONCATENATION, not about one
    container class. The five facets are read through the public element
    accessor, so they are defined for every matrix class in the repo; this check
    runs the SAME shadow against the general-purpose dense class's
    `row_join`/`col_join` over the whole shape grid and payload catalogue. If the
    shadow agrees there too, the spec view carries no information about which
    class implements it — it is satisfied by the class the task statement itself
    names. A disagreement would mean the model is secretly about one class only,
    and this run FAILS."""
    n = 0
    for ar in range(5):
        for ac in range(5):
            for br in range(5):
                for bc in range(5):
                    for cname in sorted(classes):
                        vals = classes[cname]
                        A = to_real(Matrix, Matrix, ar, ac,
                                    payload(rng, ar, ac, vals), True)
                        B = to_real(Matrix, Matrix, br, bc,
                                    payload(rng, br, bc, vals), True)
                        for (fn, meth) in ((concat_right, "row_join"),
                                           (concat_below, "col_join")):
                            exp = shadow(fn, abstract(A), abstract(B))
                            try:
                                got = abstract(getattr(A, meth)(B))
                            except ShapeError:
                                got = None
                            n += 1
                            d.count += 1
                            if got != exp:
                                d.bad.append(
                                    "class-agnostic %s a=(%d,%d) b=(%d,%d) [%s] "
                                    "shadow=%s dense=%s"
                                    % (meth, ar, ac, br, bc, cname, exp, got))
    return n


def main():
    from sympy import (SparseMatrix, Matrix, S, Eq, sqrt, EmptySet,
                       FiniteSet, oo, nan, zoo)
    from sympy.matrices.common import ShapeError

    _assert_patched(SparseMatrix)
    rng = random.Random(SEED)
    d = Diff()
    classes = payload_classes(S, Eq, sqrt, EmptySet, FiniteSet, oo, nan, zoo)
    class_names = sorted(classes)

    def chk(which, ar, ac, br, bc, **kw):
        d.check(SparseMatrix, Matrix, ShapeError, which, ar, ac, br, bc, **kw)

    # -- (0) the bridge itself, and the domain boundary ---------------------
    splits = _check_reading(d, SparseMatrix, Matrix, classes, rng)
    _check_indeterminate(d, SparseMatrix, Matrix)
    n_agnostic = _check_class_agnostic(d, Matrix, ShapeError, classes, rng)
    n_bridge = d.count          # bridge probes: predicate split + indeterminate
                                # boundary + the dense-class agreement run
    if splits == 0:
        d.bad.append("the payload catalogue never produced a matrix on which "
                     "the two candidate retention predicates differ, so the "
                     "value axis is untested and a green verdict would certify "
                     "nothing about it")

    # -- (1) boundary catalogue ---------------------------------------------
    boundary = [
        # empty / singleton
        (0, 0, 0, 0), (0, 0, 0, 1), (0, 1, 0, 0), (1, 1, 1, 1),
        # the exact F2P chain steps: hstack(zeros(0,n) for n in 0..3)
        (0, 0, 0, 1), (0, 1, 0, 2), (0, 3, 0, 3),
        # the transpose F2P chain steps: vstack(zeros(n,0) for n in 0..3)
        (0, 0, 1, 0), (1, 0, 2, 0), (3, 0, 3, 0),
        # normalisation branch (a's shared dim degenerate, orthogonal differs)
        (0, 0, 2, 3), (1, 0, 2, 3), (5, 0, 2, 3), (2, 3, 0, 0),
        # branch overlap: a.cols == 0 but rows already agree -> sum path
        (2, 0, 2, 3), (0, 0, 0, 4),
        # raise branch: shared dim disagrees, no normalisation
        (1, 1, 2, 1), (3, 2, 1, 2), (2, 2, 0, 2), (2, 1, 3, 4),
        # larger, still Requires-satisfying
        (17, 0, 4, 6), (4, 6, 4, 9), (0, 6, 4, 6),
        # placement-sensitive: both operands hold cells and the offsets differ
        (3, 2, 3, 5), (2, 4, 2, 1), (4, 3, 4, 3),
    ]
    for (ar, ac, br, bc) in boundary:
        chk("right", ar, ac, br, bc)
        chk("below", ar, ac, br, bc)
        # same shapes with the operands swapped, so each branch is hit from
        # both sides of the asymmetric guard
        chk("right", br, bc, ar, ac)
        chk("below", br, bc, ar, ac)
        # ...and again with NON-EMPTY payloads from EVERY value class on both
        # operands (an all-zero operand holds nothing, which would make the
        # content and placement observations vacuous), sparse and dense `other`.
        for cname in class_names:
            vals = classes[cname]
            fa = payload(rng, ar, ac, vals)
            fb = payload(rng, br, bc, vals)
            for dense in (False, True):
                chk("right", ar, ac, br, bc, a_smat=fa, b_smat=fb,
                    dense_other=dense)
                chk("below", ar, ac, br, bc, a_smat=fa, b_smat=fb,
                    dense_other=dense)
    n_boundary = d.count - n_bridge

    # -- (2) EXHAUSTIVE shape grid {0..GRID-1}^4, both functions ------------
    for ar in range(GRID):
        for ac in range(GRID):
            for br in range(GRID):
                for bc in range(GRID):
                    chk("right", ar, ac, br, bc)
                    chk("below", ar, ac, br, bc)
    n_grid = d.count - n_boundary - n_bridge

    # -- (3) seeded fuzz: mixed magnitudes, payload classes, sparse/dense ---
    def dim(k):
        if k < 6:
            return rng.randint(0, 4)
        if k < 9:
            return rng.randint(0, 12)
        return rng.choice([0, 1, 23, 40, 97])

    while d.count < N_TARGET:
        which = "right" if rng.random() < 0.5 else "below"
        mode = rng.randrange(3)          # bias onto each impl branch in turn
        k = rng.randrange(10)
        br, bc = dim(k), dim(k)
        if which == "right":
            if mode == 0:                # normalisation branch: a.cols == 0
                ar, ac = dim(k), 0
            elif mode == 1:              # sum branch: rows agree
                ar, ac = br, dim(k)
            else:                        # raise branch: rows disagree, ac != 0
                ar, ac = br + rng.randint(1, 3), rng.randint(1, 4)
        else:
            if mode == 0:                # normalisation branch: a.rows == 0
                ar, ac = 0, dim(k)
            elif mode == 1:
                ar, ac = dim(k), bc
            else:
                ar, ac = rng.randint(1, 4), bc + rng.randint(1, 3)
        heavy = (d.count % 5 == 0) and max(ar, ac, br, bc) <= 12
        vals = classes[class_names[d.count % len(class_names)]]
        chk(which, ar, ac, br, bc,
            a_smat=payload(rng, ar, ac, vals) if heavy else None,
            b_smat=payload(rng, br, bc, vals) if heavy else None,
            dense_other=(d.count % 7 == 0) and max(br, bc) <= 12)
    n_fuzz = d.count - n_grid - n_boundary - n_bridge

    # -- (4) end-to-end hstack/vstack (unchanged reduce) vs folded shadow ---
    e2e = [0]

    def chk_chain(kind, shapes, vals=None):
        fn = concat_right if kind == "h" else concat_below
        parts = [to_real(SparseMatrix, Matrix, r, c,
                         payload(rng, r, c, vals) if vals else None)
                 for (r, c) in shapes]
        exp = fold_shadow(fn, [abstract(p) for p in parts])
        real = (SparseMatrix.hstack(*parts) if kind == "h"
                else SparseMatrix.vstack(*parts))
        e2e[0] += 1
        d.count += 1
        if abstract(real) != exp:
            d.bad.append("%sstack%s folded-shadow=%s real=%s"
                         % (kind, shapes, exp, abstract(real)))
            return
        # the F2P assertion's own observation: equality against a dense empty
        if not vals and (exp[0] == 0 or exp[1] == 0):
            if not (real == Matrix(exp[0], exp[1], [])):
                d.bad.append("%sstack%s != Matrix%s"
                             % (kind, shapes, (exp[0], exp[1])))

    chk_chain("h", [(0, n) for n in range(4)])   # the literal F2P chain
    chk_chain("v", [(n, 0) for n in range(4)])   # the literal F2P chain
    chk_chain("h", [(1, n) for n in range(4)])
    chk_chain("v", [(n, 1) for n in range(4)])
    for _ in range(2000):
        r = rng.randint(0, 3)
        chk_chain("h", [(r, rng.randint(0, 3)) for _ in range(rng.randint(2, 5))])
        c = rng.randint(0, 3)
        chk_chain("v", [(rng.randint(0, 3), c) for _ in range(rng.randint(2, 5))])
        # chains whose parts HOLD cells, so the placement facets accumulate
        vals = classes[class_names[_ % len(class_names)]]
        r = rng.randint(1, 3)
        chk_chain("h", [(r, rng.randint(0, 3)) for _ in range(rng.randint(2, 4))],
                  vals)
        c = rng.randint(1, 3)
        chk_chain("v", [(rng.randint(0, 3), c) for _ in range(rng.randint(2, 4))],
                  vals)

    # -- (5) the F2P CONTENT case ------------------------------------------
    # `a = MutableSparseMatrix([]); b = MutableDenseMatrix([1, 2])` with
    # `a.row_join(b) == b` / `a.col_join(b) == b`: the degenerate-normalisation
    # path, observed for CONTENT AND PLACEMENT.
    from sympy.matrices import MutableSparseMatrix, MutableDenseMatrix
    _e = MutableSparseMatrix([])
    _f = MutableDenseMatrix([1, 2])
    for (_fn, _m) in ((concat_right, "row_join"), (concat_below, "col_join")):
        _exp = shadow(_fn, abstract(_e), abstract(_f))
        _res = getattr(_e, _m)(_f)
        d.count += 1
        if abstract(_res) != _exp:
            d.bad.append("F2P content %s: shadow=%s real=%s"
                         % (_m, _exp, abstract(_res)))
        elif not (_res == _f):
            d.bad.append("F2P content %s: result != b (content discarded)" % _m)

    # -- verdict ------------------------------------------------------------
    covered = branch_coverage()
    missed = [b for b in sorted(covered) if not covered[b]]
    if missed:
        d.bad.append("input generator never took impl branch(es): %s "
                     "(a green verdict would certify nothing)" % ", ".join(missed))

    if d.bad:
        print("G-CONF FAIL: %d disagreement(s) over %d Requires-satisfying "
              "inputs" % (len(d.bad), d.count))
        for line in d.bad[:MAX_REPORT]:
            print("  " + line)
        print(json.dumps({"checked": d.count, "disagreements": len(d.bad),
                          "seed": SEED, "branches": covered,
                          "shadow": "direct (contract-stripped impl region)"}))
        return 1

    print("G-CONF OK: contract-stripped impl regions of model.py "
          "(concat_right/concat_below) agree with the REAL patched "
          "SparseMatrix.row_join/col_join on %d Requires-satisfying inputs "
          "(%d boundary + %d exhaustive {0..%d}^4 grid + %d fuzz, seed=%d, "
          "+ %d bridge probes) plus %d end-to-end hstack/vstack chains incl. "
          "the F2P chains; "
          "all %d impl branches exercised; the bridge's retention predicate was "
          "measured == the repo's own sparse image on every payload class and "
          "differed from the unequal-to-zero reading on %d operand(s); the "
          "indeterminate-truth domain boundary holds; the same shadow also "
          "agrees with the general-purpose dense class's row_join/col_join on "
          "%d observations (the spec is about concatenation, not about one "
          "container class); 0 disagreements."
          % (d.count, n_boundary, n_grid, GRID - 1, n_fuzz, SEED, n_bridge,
             e2e[0], len(BRANCH_LANDMARK), splits, n_agnostic))
    print(json.dumps({"checked": d.count, "disagreements": 0, "seed": SEED,
                      "branches": covered, "endtoend_chains": e2e[0],
                      "predicate_splits": splits,
                      "class_agnostic_observations": n_agnostic,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "called: SparseMatrix.row_join / col_join "
                                "(sympy/matrices/sparse.py:1161 / :949, "
                                "patched)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
