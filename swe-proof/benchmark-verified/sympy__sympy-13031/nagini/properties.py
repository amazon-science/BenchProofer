"""properties.py — PBT falsification manifest for sympy__sympy-13031.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The functions under spec are the rows<->cols transpose pair

    concat_right(a: Mat, b: Mat) -> Mat      # horizontal: append b's columns
    concat_below(a: Mat, b: Mat) -> Mat      # vertical:   append b's rows

each a deep model of `SparseMatrix.row_join` / `SparseMatrix.col_join`. A `Mat`
carries the touched shape facets `(rows, cols)` AND three facets of its HELD-CELL
population: the count `held`, the sum `rsum` of the held cells' row indices and
the sum `csum` of their column indices. A cell is HELD exactly when the repo's own
retention predicate keeps it — when its value TESTS TRUE (`if value:` / `if v:`,
sympy/matrices/sparse.py:58/66/76/87 and :1002/:1210) — and NOT when it merely
compares unequal to zero; the two split on `S.false`, `Eq(1, 2)`, `EmptySet()`,
`FiniteSet()`, and mapping.md §2 records the measurement.

Load-bearing contract of `concat_right` (concat_below is the exact transpose):

    Requires(Acc(a.rows,1/2) ... Acc(a.csum,1/2))         # READ-ONLY a
    Requires(Acc(b.rows,1/2) ... Acc(b.csum,1/2))         # READ-ONLY b
    Requires(a.rows>=0 and a.cols>=0 and b.rows>=0 and b.cols>=0)
    Requires(a.held>=0 and b.held>=0)
    Requires(a.rsum>=0 and a.csum>=0 and b.rsum>=0 and b.csum>=0)
    Requires(Implies(a.rows==0 or a.cols==0, a.held==0))  # CARRIER INVARIANT
    Requires(Implies(b.rows==0 or b.cols==0, b.held==0))
    Requires(Implies(a.held==0, a.rsum==0 and a.csum==0)) # CARRIER INVARIANT
    Requires(Implies(b.held==0, b.rsum==0 and b.csum==0))
    Requires(MustTerminate(3 if a.rows!=b.rows else 2))
    Ensures (Acc(a.rows,1/2) ... Acc(b.csum,1/2))         # operands read-only
    Ensures (Acc(Result().rows) ... Acc(Result().csum))
    # degenerate branch (a has no columns at all -> a contributes nothing):
    Ensures (Implies(a.cols==0,
                     Result().rows==b.rows and Result().cols==b.cols))
    # otherwise branch (rows must agree; column count is the SUM):
    Ensures (Implies(a.cols!=0,
                     a.rows==b.rows and Result().rows==a.rows
                     and Result().cols==a.cols+b.cols))      # ACCUMULATION PIN
    Ensures (Result().held == a.held + b.held)               # CONTENT PIN
    Ensures (Result().rsum == a.rsum + b.rsum)               # PLACEMENT PIN 1
    Ensures (Result().csum == a.csum + b.csum + a.cols*b.held)  # PLACEMENT PIN 2
    Exsures(ShapeMismatch, ... and a.cols!=0 and a.rows!=b.rows)  # raise path

What the spec defends, and the attacks it must survive:

  * THE FIRST PIN is `Result().cols == a.cols + b.cols` on the non-normalisation
    path. It is GROUNDED in the inputs (a plain integer sum of two read-only
    facets), NOT pinned to an opaque @Pure answer-key. There is therefore no
    "echo an answer key" rival for it — the only way to satisfy the pin is to
    produce a result whose column count really is the sum. The discriminating
    content of the F2P behaviour is exactly this accumulation: a degenerate
    zero-row result must ACCUMULATE the column counts of a whole chain, never
    reset to the last operand's. Every rival numbered 3a/3b/3c below exploits a
    position where the result column count is NOT the full sum (or mutates the
    read-only operand to fake it).

  * THE SECOND PIN is `Result().held == a.held + b.held` — CONTENT PRESERVATION,
    unconditional (it holds on the degenerate branch as well as the summing
    one). Concatenation moves both operands' held cells into the result and
    invents none, so the result's held-cell count is the SUM. This pin
    distinguishes a real join from a merely SHAPE-CORRECT fabrication: an impl
    that returns a right-shaped but cell-free result on the degenerate path
    satisfies every shape clause and still is not a concatenation. The F2P test
    asserts exactly this content equality — `a = MutableSparseMatrix([])`,
    `b = MutableDenseMatrix([1,2])`, `assert a.row_join(b) == b` and
    `assert a.col_join(b) == b` — which takes the normalisation path and compares
    CONTENT, not shape. Note the pin is an EQUALITY, not a lower bound: rival (8)
    over-approximates the held population (every cell of the result held) and
    must fail too.

  * THE THIRD AND FOURTH PINS are `Result().rsum == a.rsum + b.rsum` and
    `Result().csum == a.csum + b.csum + a.cols * b.held` — PLACEMENT. Shape and a
    held-cell COUNT cannot see a permutation of the cells: an impl may carry every
    cell over and put it in the wrong place. The two index sums pin the offset
    exactly: `a`'s cells keep their coordinates, `b`'s move along the
    concatenation axis ONLY, by exactly `a.cols` (`a.rows` for concat_below). They
    are what the F2P assertion `a.row_join(b) == b` really observes on the
    normalisation path (b's cells reappear AT THEIR OWN COORDINATES, offset
    a.cols == 0), and they are grounded in the inputs exactly as the first two
    pins are. Rivals (10), (11) and (11b) live in the space these two pins close;
    (10) is the case a shape-and-count-only spec would ADMIT.

  * The carrier invariants `Implies(rows==0 or cols==0, held==0)` and
    `Implies(held==0, rsum==0 and csum==0)` are TRUE properties of the modelled
    objects, not domain restrictions: an array with a zero dimension has no cells
    at all, and an empty set of coordinates sums to zero on both axes. They admit
    every operand the real callee accepts (see the axiom-containment probe) — in
    particular the whole F2P chain, whose operands are all zero-dimension and thus
    cell-free, and the F2P content case (a is 0x0 and cell-free, b is a 2x1
    holding two cells at rows 0 and 1). Rival (12) is the control that proves this
    Requires-domain is INHABITED rather than contradictory, i.e. that every
    "verify" case below is a real proof and not vacuous.

  * Both operands are held READ-ONLY (Acc(.,1/2)). The MANDATORY attack is FRAME
    MUTATION (`frame-mutate-a-cols`): an impl that WRITES to `a` to fabricate the
    accumulated count must fail for INSUFFICIENT PERMISSION (a field store needs
    full permission), not for a wrong value.

  * The raise path is pinned by the Exsures + the otherwise-branch's
    `a.rows==b.rows` conjunct: when `a.cols!=0 and a.rows!=b.rows` the function is
    FORCED to raise (no returned value can satisfy the otherwise branch, which
    demands `a.rows==b.rows`). Rivals (4) and (9) return there instead, on the
    whole domain and on a narrow sub-domain respectively.

  * TERMINATION is an obligation, not a comment: `MustTerminate(3 if a.rows!=b.rows
    else 2)` at the METHOD level. The degenerate branch is
    a self-call, so the only thing standing between this spec and an impl that
    "satisfies" every postcondition by delegating to itself for ever is that
    level. Rival (7) is that impl.

  * There are NO @ContractOnly axioms (empty axioms region). The single opaque
    sub-operation — the unchanged element merge's net effect on the SHAPE and on
    the HELD-CELL population — is an A-reference deep model (integer arithmetic on
    the five facets). The axiom lane therefore runs the REAL post-patch
    `SparseMatrix.row_join`/`col_join` callees in Docker and checks the deep model
    == real callee over the full operand-shape grid CROSSED WITH the payload
    catalogue (axiom-soundness) and that every operand the model can REACH lies in
    the real callee's supported domain (axiom-containment). This
    mirrors/strengthens axiom_check.py (whose oracle source is embedded so the
    probe is self-contained — the runner mounts ONLY the probe at /work).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside one `# impl-start`/`# impl-end` block; the frozen spec
(Requires/Ensures/Exsures) is never touched, so `markers.same_spec` is guaranteed
and a rejection is attributable to the POSTCONDITION catching wrong behaviour (or
to the permission / obligation system), never to a tampered spec.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13031"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (each strictly INSIDE one impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body of concat_right (between # impl-start and # impl-end).
_GOLD_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""

# The whole gold impl body of concat_below (the exact transpose).
_GOLD_BELOW = """    if a.rows == 0 and a.cols != b.cols:
        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
        return concat_below(base, b)
    if a.cols != b.cols:
        raise ShapeMismatch()
    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT concat_right. The branch order is
# reshaped: the rows-agree (normal sum) case is handled FIRST via an explicit
# guard, the genuinely-empty normalisation case SECOND, and the incompatible
# raise LAST. Every result facet is bound to a LOCAL before construction.
# Semantically identical to gold on every input:
#   - a.rows == b.rows                 -> Mat(a.rows, a.cols+b.cols, ...)  [sum]
#   - a.cols == 0 and a.rows != b.rows -> normalise -> b's shape and cells
#   - else (a.cols != 0, a.rows != b.rows) -> raise
# This needs no induction lemma (the recursion shape is preserved). If it fails
# to verify, the postcondition is over-fit to the exact gold spelling =>
# SPEC-TOO-STRONG.
_POS_RIGHT = """    if a.rows == b.rows:
        total = a.cols + b.cols  # type: int
        cells = a.held + b.held  # type: int
        rows_at = a.rsum + b.rsum  # type: int
        cols_at = a.csum + b.csum + a.cols * b.held  # type: int
        return Mat(a.rows, total, cells, rows_at, cols_at)
    if a.cols == 0:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    raise ShapeMismatch()"""
_POS_CONTROL = _swap(_BASE, _GOLD_RIGHT, _POS_RIGHT)

# (5b) A second, RECURSION-FREE correct impl. It collapses the whole degenerate
# case: whenever `a` has no columns the answer is b's shape carrying b's cells at
# b's own coordinates — which is true on BOTH sub-cases (a.rows != b.rows takes
# the normalisation path; a.rows == b.rows takes the sum path, where a.cols == 0
# forces a.held == 0, a.rsum == a.csum == 0 and the offset a.cols * b.held == 0,
# so the sum path returns exactly the same five facets). It therefore proves the
# spec does not over-fit the RECURSIVE spelling and, in particular, that the two
# placement pins genuinely admit the "the result equals b" reading of the
# degenerate path rather than merely tolerating the recursive rebuild. If this
# fails to verify => SPEC-TOO-STRONG.
_POS_RIGHT2 = """    if a.cols == 0:
        return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_POS_CONTROL2 = _swap(_BASE, _GOLD_RIGHT, _POS_RIGHT2)

# (6) ADMISSIBILITY. Self-calls on real-shaped inputs, checked BEFORE the gold
# body runs. Two probe pairs:
#   * the discriminating accumulation case — a (0 x 3) result joined
#     horizontally with a (0 x 3) operand, both cell-free (the case a reset would
#     collapse to (0,3) instead of (0,6));
#   * the F2P CONTENT case with PLACEMENT — a 0x0 cell-free operand joined with a
#     2x1 holding two cells at rows 0 and 1 (rsum == 1) and column 0 (csum == 0),
#     i.e. the literal `MutableSparseMatrix([]).row_join(MutableDenseMatrix([1,2]))`
#     abstraction, which must satisfy every Requires including both carrier
#     invariants.
# If a self-call cannot establish the Requires for such an ordinary input =>
# PRECOND-TOO-STRONG.
_ADMISS_RIGHT = """    p = Mat(0, 3, 0, 0, 0)  # type: Mat
    q = Mat(0, 3, 0, 0, 0)  # type: Mat
    Assert(Acc(p.rows, 1 / 2) and Acc(p.cols, 1 / 2) and Acc(p.held, 1 / 2))
    Assert(Acc(p.rsum, 1 / 2) and Acc(p.csum, 1 / 2))
    Assert(Acc(q.rows, 1 / 2) and Acc(q.cols, 1 / 2) and Acc(q.held, 1 / 2))
    Assert(Acc(q.rsum, 1 / 2) and Acc(q.csum, 1 / 2))
    Assert(p.rows >= 0 and p.cols >= 0 and q.rows >= 0 and q.cols >= 0)
    Assert(p.held >= 0 and q.held >= 0 and p.rsum >= 0 and q.csum >= 0)
    Assert(Implies(p.rows == 0 or p.cols == 0, p.held == 0))
    Assert(Implies(q.rows == 0 or q.cols == 0, q.held == 0))
    Assert(Implies(p.held == 0, p.rsum == 0 and p.csum == 0))
    Assert(Implies(q.held == 0, q.rsum == 0 and q.csum == 0))
    e = Mat(0, 0, 0, 0, 0)  # type: Mat
    f = Mat(2, 1, 2, 1, 0)  # type: Mat
    Assert(Acc(e.rows, 1 / 2) and Acc(e.cols, 1 / 2) and Acc(e.held, 1 / 2))
    Assert(Acc(e.rsum, 1 / 2) and Acc(e.csum, 1 / 2))
    Assert(Acc(f.rows, 1 / 2) and Acc(f.cols, 1 / 2) and Acc(f.held, 1 / 2))
    Assert(Acc(f.rsum, 1 / 2) and Acc(f.csum, 1 / 2))
    Assert(e.rows >= 0 and e.cols >= 0 and f.rows >= 0 and f.cols >= 0)
    Assert(e.held >= 0 and f.held >= 0 and e.rsum >= 0 and f.csum >= 0)
    Assert(Implies(e.rows == 0 or e.cols == 0, e.held == 0))
    Assert(Implies(f.rows == 0 or f.cols == 0, f.held == 0))
    Assert(Implies(e.held == 0, e.rsum == 0 and e.csum == 0))
    Assert(Implies(f.held == 0, f.rsum == 0 and f.csum == 0))
    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_ADMISS = _swap(_BASE, _GOLD_RIGHT, _ADMISS_RIGHT)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. Operand `a` is read-only
# (Acc(a.cols,1/2)). This rival, on the normal path, STORES the accumulated count
# back into the read-only input (`a.cols = a.cols + b.cols`) and then returns
# `Mat(a.rows, a.cols, ...)` — an attempt to fabricate the pin by mutating the
# operand in place. Under Acc(a.cols,1/2) a field store needs FULL permission, so
# it must fail for INSUFFICIENT PERMISSION (not a wrong value). The normalisation
# branch and the raise are kept verbatim, so the failure is attributable solely to
# the write. Rejection source: the PERMISSION SYSTEM.
_FRAME_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    a.cols = a.cols + b.cols
    return Mat(a.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum)"""
_RIVAL_FRAME = _swap(_BASE, _GOLD_RIGHT, _FRAME_RIGHT)

# (3a) PARTIAL-DOMAIN — the accumulation RESET, as a uniqueness rival. On the
# normal path it returns b's shape (drops `a.cols`) instead of the column SUM.
# This is correct ONLY on the sub-domain `a.cols == 0` (where b.cols ==
# a.cols+b.cols); it diverges whenever `a.cols > 0`. Rejection source: the
# otherwise-branch PIN `Result().cols == a.cols + b.cols`.
_PARTIAL_RESET_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(b.rows, b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_PARTIAL_RESET = _swap(_BASE, _GOLD_RIGHT, _PARTIAL_RESET_RIGHT)

# (3b) PARTIAL-DOMAIN (sub-domain on a value class). Correct EXCEPT when b is
# itself zero-column (`b.cols == 0`): it emits the accumulator's column count
# unchanged instead of `a.cols + b.cols`. When b.cols == 0 the two coincide, so
# this is the cheapest "looks-right" rival — it diverges exactly when b.cols > 0.
# Rejection source: the PIN — `a.cols != a.cols + b.cols` whenever b.cols > 0.
_PARTIAL_BCOLS_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    if b.cols == 0:
        return Mat(a.rows, a.cols + b.cols, a.held + b.held,
                   a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
    return Mat(a.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_PARTIAL_BCOLS = _swap(_BASE, _GOLD_RIGHT, _PARTIAL_BCOLS_RIGHT)

# (4) CONTROL-FLOW-EFFECT — drop the raise on the incompatible path. This rival
# REMOVES the `raise ShapeMismatch()` and returns a value on the incompatible
# path (a.cols != 0, a.rows != b.rows). The otherwise branch then demands
# `a.rows == b.rows`, which is false there, so no returned value can satisfy the
# postcondition; the function MUST raise. Rejection source: the otherwise-branch
# conjunct `a.rows == b.rows`.
_NORAISE_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_NORAISE = _swap(_BASE, _GOLD_RIGHT, _NORAISE_RIGHT)

# (3c) TRANSPOSE-SITE PARTIAL-DOMAIN — the accumulation reset on concat_below
# (the OTHER modeled function), to confirm the symmetric spec is equally tight.
# On the normal path it returns b's shape (drops a.rows) instead of the row SUM.
# Correct only when a.rows == 0. Rejection source: concat_below's otherwise-branch
# PIN `Result().rows == a.rows + b.rows`.
_PARTIAL_RESET_BELOW = """    if a.rows == 0 and a.cols != b.cols:
        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
        return concat_below(base, b)
    if a.cols != b.cols:
        raise ShapeMismatch()
    return Mat(b.rows, b.cols, a.held + b.held,
               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)"""
_RIVAL_PARTIAL_BELOW = _swap(_BASE, _GOLD_BELOW, _PARTIAL_RESET_BELOW)

# (7-old, renumbered 2a) CONTENT-DISCARD ON THE NORMALISATION PATH. Keeps every
# SHAPE clause satisfiable: on the degenerate-normalisation path it returns a
# result of exactly the right shape `(b.rows, b.cols)` but CELL-FREE — it drops
# b's held cells instead of carrying them over. A shape-correct fabrication rather
# than a concatenation. Rejection source: the CONTENT PIN
# `Result().held == a.held + b.held` — on that path a.held == 0 (a has a zero
# dimension, by the carrier invariant), so the pin demands b.held and the rival
# delivers 0, which differs whenever b holds a cell.
_CONTENT_DISCARD_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        return Mat(b.rows, b.cols, 0, 0, 0)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_CONTENT_DISCARD = _swap(_BASE, _GOLD_RIGHT, _CONTENT_DISCARD_RIGHT)

# (2b) CONTENT-DISCARD, transpose site (col_join), same class.
_CONTENT_DISCARD_BELOW = """    if a.rows == 0 and a.cols != b.cols:
        return Mat(b.rows, b.cols, 0, 0, 0)
    if a.cols != b.cols:
        raise ShapeMismatch()
    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)"""
_RIVAL_CONTENT_DISCARD_BELOW = _swap(_BASE, _GOLD_BELOW, _CONTENT_DISCARD_BELOW)


# --- fresh attacks, distinct families --------------------------------------

# (8) OVER-APPROXIMATION. Every clause about the held population is an EQUALITY,
# and this rival tests that: it carries every operand cell over (never dropping
# one) and then some — it reports the result as holding EVERY cell of its own
# shape (`a.rows * (a.cols + b.cols)`), a strict SUPERSET of the true held
# population whenever either operand has an unheld cell. A spec that only bounded
# the content from below (`>= a.held + b.held`, "nothing is lost"), or that
# omitted the held clause and kept only the shape ones, would ADMIT it. Placement
# is left at the gold formula so the failure is attributable to the count alone.
# Rejection source: the CONTENT PIN as an EQUALITY —
# `a.rows * (a.cols + b.cols) != a.held + b.held` in general (e.g. a 1x1 operand
# holding nothing joined with a 1x1 holding nothing gives 2 != 0).
_OVERAPPROX_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.rows * (a.cols + b.cols),
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_OVERAPPROX = _swap(_BASE, _GOLD_RIGHT, _OVERAPPROX_RIGHT)

# (9) PARTIAL-DOMAIN GUARD ON THE RAISE PATH. The incompatible path is left
# intact EXCEPT on the narrow sub-domain where the other operand holds no cells:
# there the rival quietly returns a value instead of rejecting. The sub-domain is
# ordinary and reachable (an all-zero operand of mismatched shape), and on it
# every content and placement clause is satisfied by the returned facets —
# b.held == 0 forces b.rsum == b.csum == 0, so `a.held + b.held == a.held` and
# both index sums are a's. So the ONLY clause that can catch it is the
# otherwise-branch's control-flow conjunct. Rejection source: the otherwise
# branch demands `a.rows == b.rows`, which is false on that sub-domain, so
# returning there is unprovable however right the facets look.
_PARTIAL_RAISE_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows and b.held == 0:
        return Mat(a.rows, a.cols + b.cols, a.held, a.rsum, a.csum)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_PARTIAL_RAISE = _swap(_BASE, _GOLD_RIGHT, _PARTIAL_RAISE_RIGHT)

# (10) THE FREEDOM THE PLACEMENT PINS CLOSE — the sharpest fresh attack, and the
# one a shape-and-count-only spec ADMITS. The rival is gold except on the
# sub-domain `a.held == 0`: an operand with real columns that happens to hold no
# cells. There it carries b's cells over (so the CONTENT pin is satisfied:
# a.held + b.held == b.held) and keeps the right shape, but places them at their
# OWN coordinates instead of shifting them right by `a.cols` — the frame's empty
# columns are silently collapsed. Under a spec carrying only (rows, cols, held)
# this rival is INDISTINGUISHABLE from gold and would verify; it is exactly the
# hole `csum` closes. Rejection source: PLACEMENT PIN 2 —
# `b.csum != a.csum + b.csum + a.cols * b.held` whenever a.cols > 0 and
# b.held > 0 (and a.csum == 0 there by the carrier invariant).
_PLACEMENT_FREE_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    if a.held == 0:
        return Mat(a.rows, a.cols + b.cols, b.held, b.rsum, b.csum)
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_PLACEMENT_FREE = _swap(_BASE, _GOLD_RIGHT, _PLACEMENT_FREE_RIGHT)

# (11) WRONG AXIS. The offset is applied — but to the OTHER coordinate: b's cells
# are pushed DOWN by a.cols instead of RIGHT. Shape, held count and the total
# "amount of displacement" are all as gold; only which axis moved differs. This is
# the transposition a single-index-sum spec could not see, and it is the mutation
# the differential conformance control measured as 1994 disagreements against the
# real callee. Rejection source: BOTH placement pins — rsum gains a term the pin
# forbids and csum loses the one it demands.
_WRONG_AXIS_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum + a.cols * b.held, a.csum + b.csum)"""
_RIVAL_WRONG_AXIS = _swap(_BASE, _GOLD_RIGHT, _WRONG_AXIS_RIGHT)

# (11b) WRONG AXIS, transpose site (concat_below): the row offset is applied to
# the column sum instead. Confirms both placement pins are equally tight at both
# modeled functions.
_WRONG_AXIS_BELOW = """    if a.rows == 0 and a.cols != b.cols:
        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
        return concat_below(base, b)
    if a.cols != b.cols:
        raise ShapeMismatch()
    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.rows * b.held)"""
_RIVAL_WRONG_AXIS_BELOW = _swap(_BASE, _GOLD_BELOW, _WRONG_AXIS_BELOW)

# (12) BOUNDARY TOKEN SWAP. One token of the normalisation rebuild is moved off
# the boundary: the frame `a` is rebuilt with ONE column instead of ZERO
# (`Mat(b.rows, 1, 0, 0, 0)`). Everything else is gold, and the rebuilt frame
# still satisfies every carrier invariant, so the variant is well-formed — but the
# self-call now returns a result with `1 + b.cols` columns and b's cells shifted
# one place right. Rejection source: the normalisation-branch Ensures
# (`Result().cols == b.cols`) and PLACEMENT PIN 2 (the offset must be a.cols == 0
# on that path, so b's cells must reappear at their own coordinates).
_TOKEN_SWAP_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 1, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_TOKEN_SWAP = _swap(_BASE, _GOLD_RIGHT, _TOKEN_SWAP_RIGHT)

# (13) ORACLE ECHO / SELF-DELEGATION. The spec's pins are grounded in the inputs,
# so there is no opaque answer key to echo — the only "oracle" available to an
# impl that wants to satisfy the postcondition without doing the work is the
# specified function ITSELF. This rival takes it: on the normalisation path it
# delegates to `concat_right(a, b)` with the operands UNCHANGED. Every
# postcondition is then trivially inherited from the callee's own contract, so a
# partial-correctness reading of this spec would ADMIT it while it computes
# nothing at all (it diverges). Rejection source: the TERMINATION OBLIGATION at
# the method level — the caller holds `MustTerminate(3)` on that branch and the
# self-call, with the same operands, still satisfies the guard, so the callee
# demands level 3 again; nothing decreases and the obligation cannot be
# discharged.
_ECHO_RIGHT = """    if a.cols == 0 and a.rows != b.rows:
        return concat_right(a, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_ECHO = _swap(_BASE, _GOLD_RIGHT, _ECHO_RIGHT)

# (14) VACUITY CONTROL. Every "verify" case above is worthless if the Requires
# are contradictory — an infeasible precondition proves every postcondition. This
# rival asserts FALSE at the top of the body, before any branch. It can only
# verify if the Requires-domain is EMPTY. Its rejection is the machine-checked
# statement that the domain is inhabited, i.e. that the two carrier invariants and
# the termination level narrow nothing away and every positive control is a real
# proof. Rejection source: `Assert(False)` is unprovable under a satisfiable
# precondition.
_VACUITY_RIGHT = """    Assert(False)
    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)"""
_RIVAL_VACUITY = _swap(_BASE, _GOLD_RIGHT, _VACUITY_RIGHT)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL,
     "rationale": "structurally-different but CORRECT concat_right (rows-agree sum "
                  "case handled FIRST, normalisation SECOND, raise LAST; every result "
                  "facet bound to a local). Same semantics, no extra induction lemma. "
                  "If it fails to verify, the postcondition is over-fit to the gold "
                  "spelling => SPEC-TOO-STRONG."},
    {"id": "pos-control-degenerate-collapse", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL2,
     "rationale": "a RECURSION-FREE correct impl: whenever a has no columns it "
                  "returns b's shape carrying b's cells at b's own coordinates, which "
                  "agrees with gold on both sub-cases (a.cols == 0 forces a.held == 0 "
                  "and a.rsum == a.csum == 0, and the column offset a.cols * b.held is "
                  "0). Proves the spec is not over-fit to the recursive spelling and "
                  "that the placement pins admit the 'result equals b' reading of the "
                  "degenerate path. Failure => SPEC-TOO-STRONG."},
    {"id": "admiss-f2p-accumulate", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "self-calls on the F2P-shaped accumulation input (Mat(0,3) joined "
                  "with Mat(0,3)) AND on the F2P content input (a 0x0 cell-free operand "
                  "with a 2x1 holding two cells, rsum==1, csum==0 — the abstraction of "
                  "MutableSparseMatrix([]).row_join(MutableDenseMatrix([1,2]))) must "
                  "establish Acc(.,1/2), the non-negative facets and BOTH carrier "
                  "invariants. If the precondition rejects such an ordinary input => "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "frame-mutate-a-cols", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: the gold row_join "
                   "mutates A.cols where A IS self (full ownership of its own shape) and "
                   "returns A; the modeled operand `a` is held READ-ONLY (Acc(a.cols,1/2)) "
                   "because the consumer-visible contract observes a as an unmodified "
                   "input. Storing into a 1/2-permission field is a pure verification "
                   "artifact with no resolving real-patch analogue — it must be rejected "
                   "on permission, not silently admitted.",
     "rationale": "rejection from the PERMISSION SYSTEM: under Acc(a.cols,1/2) a field "
                  "store `a.cols = ...` needs FULL permission, so the impl fails for "
                  "INSUFFICIENT PERMISSION (not a wrong value)."},
    {"id": "partial-domain-reset-bcols", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_RESET,
     "refinement": "this is the accumulation reset: a row_join that returns a matrix "
                   "shaped like `other` discards the accumulated a.cols. Its faithful "
                   "real patch is the unmodified callee, which fails the F2P hstack "
                   "chain ((0,6) vs (0,3)). Definitively non-resolving.",
     "rationale": "rejection from the otherwise-branch PIN Result().cols == a.cols+b.cols: "
                  "returning b.cols satisfies it only when a.cols==0; for a.cols>0 the "
                  "postcondition fails (b.cols != a.cols+b.cols)."},
    {"id": "partial-domain-forget-bcols", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_BCOLS,
     "refinement": "a row_join that returns a.cols (drops other.cols) on the non-empty "
                   "merge agrees with gold only when other.cols==0; on every operand with "
                   "other.cols>0 it under-counts. The F2P hstack chain mixes other.cols "
                   "0,1,2,3, so it FAILS (yields (0,1) not (0,6)). Faithful but "
                   "non-resolving.",
     "rationale": "rejection from the PIN: for b.cols>0 the result column count a.cols "
                  "!= a.cols+b.cols, so the otherwise-branch postcondition fails."},
    {"id": "control-flow-no-raise", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NORAISE,
     "refinement": "a row_join that silently returns a (malformed) merge instead of "
                   "raising ShapeError on incompatible rows fails the P2P test_errors "
                   "(which asserts row_join on mismatched shapes raises ShapeError) and "
                   "would also corrupt downstream shapes. Faithful but non-resolving.",
     "rationale": "rejection from the otherwise-branch conjunct a.rows==b.rows: on the "
                  "incompatible path (a.cols!=0, a.rows!=b.rows) the function returns a "
                  "value, so the Implies(not normalisation, a.rows==b.rows and ...) "
                  "antecedent holds but its consequent demands a.rows==b.rows, which is "
                  "false — the postcondition cannot be discharged without the raise."},
    {"id": "partial-domain-reset-below", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_BELOW,
     "refinement": "the transpose accumulation reset on col_join: returns a matrix shaped "
                   "like other (b.rows), discarding accumulated a.rows. Faithful real "
                   "patch is the unmodified col_join, which fails the F2P vstack chain "
                   "((6,0) vs (3,0)). Non-resolving; confirms the symmetric spec is "
                   "equally tight.",
     "rationale": "rejection from concat_below's otherwise-branch PIN "
                  "Result().rows == a.rows+b.rows: returning b.rows satisfies it only "
                  "when a.rows==0; for a.rows>0 the postcondition fails."},
    {"id": "content-discard-on-normalisation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONTENT_DISCARD,
     "refinement": "a row_join that returns a right-shaped but CELL-FREE matrix on the "
                   "degenerate-normalisation path (the operands' held cells dropped "
                   "rather than carried over) satisfies every shape clause and still is "
                   "not a concatenation. Its faithful real patch FAILS the F2P "
                   "test_sparse_matrix, which takes exactly this path and asserts CONTENT "
                   "equality (a = MutableSparseMatrix([]); b = MutableDenseMatrix([1,2]); "
                   "assert a.row_join(b) == b): the real function returns b's two cells, "
                   "the fabrication returns an all-zero 2x1. Shape-correct but "
                   "non-resolving.",
     "rationale": "rejection from the CONTENT PIN Result().held == a.held + b.held: on the "
                  "normalisation path a.held == 0 (a has a zero dimension, by the carrier "
                  "invariant), so the pin demands b.held; returning 0 fails whenever b "
                  "holds a cell."},
    {"id": "content-discard-on-normalisation-below", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONTENT_DISCARD_BELOW,
     "refinement": "the transpose of the above on col_join: a right-shaped but cell-free "
                   "result on the degenerate path. Faithful real patch fails the same F2P "
                   "assertion's col_join half (assert a.col_join(b) == b). Confirms the "
                   "content pin is equally tight at both sites.",
     "rationale": "rejection from concat_below's CONTENT PIN Result().held == a.held+b.held: "
                  "a.held == 0 on that path, so the pin demands b.held and the rival "
                  "delivers 0."},

    # ---- fresh attacks, distinct families (must reject) ----
    {"id": "over-approx-hold-every-cell", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVERAPPROX,
     "refinement": "its faithful real patch stores a value into EVERY cell of the merged "
                   "result instead of only the cells the operands held — a strict "
                   "over-approximation that loses no content but invents it. The repo's "
                   "matrix equality compares the retained-cell images, so a result "
                   "carrying explicit entries in cells the operands left unheld no longer "
                   "compares equal to the expected matrix: it fails the P2P sparse "
                   "row_join/col_join equality assertions (and blows up the stored size of "
                   "every join). Faithful but non-resolving.",
     "rationale": "rejection from the CONTENT PIN read as an EQUALITY: the rival reports "
                  "a.rows*(a.cols+b.cols) held cells, which differs from a.held+b.held on "
                  "any operand pair with an unheld cell (1x1 cell-free joined with 1x1 "
                  "cell-free: 2 != 0). A spec that only demanded 'nothing is lost' "
                  "(>= a.held+b.held) would admit it."},
    {"id": "partial-domain-accept-mismatch-when-b-empty", "kind": "uniqueness",
     "expect": "reject", "module": _RIVAL_PARTIAL_RAISE,
     "refinement": "a row_join that accepts a row-count mismatch whenever `other` holds "
                   "no cells returns a matrix with self's row count and the summed column "
                   "count, silently disagreeing with other's shape. Measured against the "
                   "real callee: SparseMatrix.zeros(2,3).row_join(SparseMatrix.zeros(5,1)) "
                   "RAISES ShapeError, so this rival contradicts the patched reference on "
                   "an ordinary input, and it fails the P2P test_errors ShapeError "
                   "assertions for any cell-free operand. Faithful but non-resolving.",
     "rationale": "rejection from the otherwise-branch CONTROL-FLOW conjunct: on that "
                  "sub-domain b.held==0 forces b.rsum==b.csum==0, so every content and "
                  "placement clause is satisfied by the returned facets — only "
                  "`a.rows == b.rows` is not, and returning there makes it unprovable. The "
                  "guard is on a REACHABLE sub-domain (an all-zero operand of mismatched "
                  "shape), so the rejection is not vacuous."},
    {"id": "placement-collapse-frame-when-a-empty", "kind": "uniqueness",
     "expect": "reject", "module": _RIVAL_PLACEMENT_FREE,
     "refinement": "its faithful real patch skips the column shift when self holds no "
                   "cells: other's cells are copied to (i, j) instead of (i, j + A.cols). "
                   "Measured against the real callee: "
                   "SparseMatrix.zeros(2,3).row_join(Matrix(2,1,[1,2])) puts its two cells "
                   "at [(0,3), (1,3)] — csum 6 — while this rival puts them at "
                   "[(0,0), (1,0)], csum 0. The resulting matrices are not equal, so it "
                   "fails the P2P sparse row_join equality assertions. Faithful but "
                   "non-resolving.",
     "rationale": "rejection from PLACEMENT PIN 2 (Result().csum == a.csum+b.csum+"
                  "a.cols*b.held): on the guarded sub-domain a.held==0 forces a.csum==0, "
                  "so the pin demands b.csum + a.cols*b.held and the rival delivers "
                  "b.csum. THIS IS THE RIVAL A SHAPE-AND-COUNT-ONLY SPEC ADMITS — it "
                  "satisfies every clause about rows, cols and held, and only the "
                  "column-index sum refutes it."},
    {"id": "placement-offset-wrong-axis", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_AXIS,
     "refinement": "its faithful real patch offsets other's cells on the wrong axis "
                   "(A._smat[(i + A.cols, j)] instead of (i, j + A.cols)) — the cells are "
                   "all present but transposed out of the result's own shape, which the "
                   "differential conformance control measured as 1994 disagreements "
                   "against the real callee over the same input set. Non-resolving.",
     "rationale": "rejection from BOTH placement pins: rsum acquires the a.cols*b.held "
                  "term the pin forbids and csum loses the term it demands, so both fail "
                  "whenever a.cols>0 and b.held>0. Shape and held count are untouched, so "
                  "this rival is invisible to every other clause."},
    {"id": "placement-offset-wrong-axis-below", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_AXIS_BELOW,
     "refinement": "the transpose site: col_join offsetting other's cells along the "
                   "COLUMN axis by a.rows instead of down the row axis. Same measured "
                   "disagreement class against the real callee. Non-resolving; confirms "
                   "both placement pins are equally tight at both modeled functions.",
     "rationale": "rejection from concat_below's placement pins (csum must be the plain "
                  "sum; rsum must pick up a.rows once per held cell of b)."},
    {"id": "boundary-token-swap-rebuild-frame", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TOKEN_SWAP,
     "refinement": "its faithful real patch rebuilds the normalisation frame with one "
                   "column instead of zero (self._new(other.rows, 1, []) rather than "
                   "(other.rows, 0, [])). That is a single-token slip on the boundary the "
                   "patched guard is about, and it FAILS the F2P content assertion "
                   "directly: MutableSparseMatrix([]).row_join(MutableDenseMatrix([1,2])) "
                   "would be 2x2 with its cells in column 1, so `== b` is false. "
                   "Definitively non-resolving.",
     "rationale": "rejection from the normalisation-branch Ensures (Result().cols == "
                  "b.cols, violated by the extra column) and from PLACEMENT PIN 2 (the "
                  "rebuilt frame's cols is 1, so b's cells are shifted one place right "
                  "where the pin demands they keep their own coordinates)."},
    {"id": "oracle-echo-self-delegate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ECHO,
     "refinement": "its faithful real patch is `return self.row_join(other)` on the "
                   "degenerate path — unbounded recursion. Running the F2P content case "
                   "raises RecursionError instead of returning b, so it resolves nothing; "
                   "there is no input on which it computes an answer at all.",
     "rationale": "rejection from the TERMINATION OBLIGATION at the method level. Every "
                  "value clause is inherited verbatim from the callee's own contract, so a "
                  "partial-correctness reading of this spec would ADMIT an impl that "
                  "diverges. MustTerminate(3 if a.rows!=b.rows else 2) is "
                  "what refutes it: on that branch the caller holds level 3 and the "
                  "self-call with UNCHANGED operands re-enters the same guard, demanding "
                  "level 3 again, so nothing decreases. The verifier reports it as "
                  "'Obligation leak check failed. Callee concat_right might not take all "
                  "unsatisfied obligations from the caller.' — i.e. the rejection comes "
                  "from the obligation, not from a value clause, which is exactly the "
                  "point: no value clause CAN catch it."},
    {"id": "vacuity-assert-false", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_VACUITY,
     "refinement": "not a candidate implementation at all — the control that decides "
                   "whether this battery's 'verify' verdicts mean anything. An impl "
                   "asserting FALSE before any branch can verify only if the "
                   "Requires-domain is EMPTY, in which case every postcondition holds "
                   "vacuously and every positive control above is worthless. Its "
                   "rejection is the machine-checked statement that the precondition "
                   "(both carrier invariants and the termination level included) is "
                   "SATISFIABLE.",
     "rationale": "rejection because Assert(False) is unprovable under a satisfiable "
                  "precondition; a verification here would mean the spec excludes the "
                  "whole interesting domain."},
]


# ===========================================================================
# AXIOM LANE (Docker, real sympy callee under the gold patch)
# ===========================================================================
# There are NO @ContractOnly axioms (empty axioms region). The single opaque
# sub-operation is an A-reference: the unchanged element merge's net effect on the
# result SHAPE and on the HELD-CELL population (count and both index sums),
# modeled deeply as integer arithmetic, plus the degenerate-normalisation guard
# and the incompatible-path raise. These two probes run the REAL post-patch
# SparseMatrix.row_join/col_join callees in Docker:
#   - axiom-soundness: deep 5-facet model == real callee on the FULL operand grid
#     CROSSED WITH the payload catalogue (including the falsy-but-unequal-to-zero
#     value class, which is the axis on which the retention predicate is decided)
#     + degenerate cases + F2P chains + the raise path. Strengthens axiom_check.py
#     with a wider grid, explicit no-raise checks, and an executable refutation of
#     the rejected reading of the retention predicate.
#   - axiom-containment: every operand the model can reach (non-negative facets
#     under both carrier invariants, incl. the (b.rows,0,0,0,0)/(0,b.cols,0,0,0)
#     normalisation rebuilds) is a legal operand the real callee accepts, so the
#     A-reference is exercised exactly where the model reaches it; a reachable
#     operand the real callee could not form would be AXIOM-TOO-WEAK-FOR-CALLER
#     (none exists).
# Both probes are SELF-CONTAINED (import only sympy + stdlib) because the runner
# mounts ONLY the probe at /work — axiom_check.py is NOT in-container.

_AX_SHAPE_SOUND = r'''
import sys

# ---- deep model, transcribed from model.py's impl regions. The carrier is the
# ---- five facets (rows, cols, held, rsum, csum): shape, the size of the
# ---- HELD-CELL population, and the sums of that population's row and column
# ---- indices (which pin WHERE the merge puts each operand's cells).
class _Mismatch(Exception):
    pass

def model_concat_right(a, b):
    (ar, ac, ah, ars, acs) = a
    (br, bc, bh, brs, bcs) = b
    if ac == 0 and ar != br:
        return model_concat_right((br, 0, 0, 0, 0), b)
    if ar != br:
        raise _Mismatch()
    return (ar, ac + bc, ah + bh, ars + brs, acs + bcs + ac * bh)

def model_concat_below(a, b):
    (ar, ac, ah, ars, acs) = a
    (br, bc, bh, brs, bcs) = b
    if ar == 0 and ac != bc:
        return model_concat_below((0, bc, 0, 0, 0), b)
    if ac != bc:
        raise _Mismatch()
    return (ar + br, ac, ah + bh, ars + brs + ar * bh, acs + bcs)

# A cell is HELD iff its value TESTS TRUE — the repo's own retention predicate
# (`if value:` / `if v:` in the sparse constructor and in both merge loops), read
# through the PUBLIC element accessor so dense and sparse operands are measured
# identically. NOT `!= 0`: the two split on falsy sympy objects.
def facets(m):
    cells = [(i, j) for i in range(m.rows) for j in range(m.cols) if m[i, j]]
    return (m.rows, m.cols, len(cells),
            sum(i for (i, j) in cells), sum(j for (i, j) in cells))

def facets_nonzero(m):
    cells = [(i, j) for i in range(m.rows) for j in range(m.cols)
             if m[i, j] != 0]
    return (m.rows, m.cols, len(cells),
            sum(i for (i, j) in cells), sum(j for (i, j) in cells))

def main():
    from sympy import (SparseMatrix, Matrix, S, Eq, sqrt, EmptySet, FiniteSet,
                       oo, nan, zoo)
    from sympy.matrices.common import ShapeError

    classes = {
        "empty":  [],
        "int":    [1, -7, 3, 5, 2, -2, 11],
        "exotic": [S.Half, sqrt(2), S.Pi, oo, nan, zoo, S.true],
        "falsy":  [S.false, Eq(1, 2), EmptySet(), FiniteSet()],
        "mixed":  [1, S.false, S.Half, Eq(1, 2), -7, EmptySet(), S.true,
                   FiniteSet(), oo],
    }

    def operand(r, c, vals, dense=False):
        present = {}
        if vals:
            for i in range(r):
                for j in range(c):
                    if (i + 3 * j) % 4 != 1:
                        present[(i, j)] = vals[(i + 2 * j) % len(vals)]
        if not present:
            return (Matrix if dense else SparseMatrix).zeros(r, c)
        if dense:
            flat = [0] * (r * c)
            for (i, j) in present:
                flat[i * c + j] = present[(i, j)]
            return Matrix(r, c, flat)
        return SparseMatrix(r, c, dict(present))

    bad = []
    n = 0
    # ---- wide operand grid {0..4}^4 x payload class x sparse/dense `other` ---
    for ar in range(5):
        for ac in range(5):
            for br in range(5):
                for bc in range(5):
                    for cname in sorted(classes):
                        vals = classes[cname]
                        for dense in (False, True):
                            a = operand(ar, ac, vals)
                            b = operand(br, bc, vals, dense)
                            fa, fb = facets(a), facets(b)
                            for (model, meth) in (
                                    (model_concat_right, "row_join"),
                                    (model_concat_below, "col_join")):
                                try:
                                    exp = model(fa, fb)
                                except _Mismatch:
                                    exp = None
                                if exp is None:
                                    raised = False
                                    try:
                                        getattr(a, meth)(b)
                                    except ShapeError:
                                        raised = True
                                    if not raised:
                                        bad.append((meth + " no-raise", fa, fb,
                                                    cname))
                                else:
                                    got = facets(getattr(a, meth)(b))
                                    if got != exp:
                                        bad.append((meth, fa, fb, cname, got,
                                                    exp))
                                n += 1

    # ---- the retention predicate is DECIDED, not assumed: the catalogue must
    # ---- reach the class where the two candidate readings differ, and the model
    # ---- must be REFUTABLE under the rejected one.
    splits = 0
    refuted = 0
    for r in (1, 2, 3):
        for c in (1, 2, 3):
            for dense in (False, True):
                m = operand(r, c, classes["falsy"], dense)
                if facets(m) != facets_nonzero(m):
                    splits += 1
                z = SparseMatrix.zeros(r, 0)
                if model_concat_right(facets_nonzero(z),
                                      facets_nonzero(m)) != facets(z.row_join(m)):
                    refuted += 1
    if splits == 0:
        bad.append(("retention predicate untested: no operand split the two "
                    "candidate readings",))
    if refuted == 0:
        bad.append(("retention predicate unpinned: the model could not be "
                    "refuted under the rejected unequal-to-zero reading",))

    # ---- the domain boundary: an INDETERMINATE truth value is outside the
    # ---- modelled type, and the real callee refuses it too.
    from sympy import Symbol
    from sympy.matrices import MutableSparseMatrix
    x = Symbol('x')
    ind = Matrix(1, 1, [x > 0])
    for (label, fn) in (("abstraction", lambda: facets(ind)),
                        ("sparse image", lambda: MutableSparseMatrix(ind)),
                        ("row_join",
                         lambda: SparseMatrix.zeros(1, 0).row_join(ind)),
                        ("col_join",
                         lambda: SparseMatrix.zeros(0, 1).col_join(ind))):
        try:
            fn()
            bad.append(("indeterminate truth not refused", label))
        except TypeError:
            pass

    # ---- the exact FAIL_TO_PASS stacking chains ----
    hs = [SparseMatrix.zeros(0, k) for k in range(4)]
    got = SparseMatrix.hstack(*hs)
    if got.shape != (0, 6) or got != Matrix(0, 6, []):
        bad.append(("hstack chain", got.shape))
    vs = [SparseMatrix.zeros(k, 0) for k in range(4)]
    got = SparseMatrix.vstack(*vs)
    if got.shape != (6, 0) or got != Matrix(6, 0, []):
        bad.append(("vstack chain", got.shape))
    if SparseMatrix.hstack(*[SparseMatrix.zeros(1, k)
                             for k in range(4)]).shape != (1, 6):
        bad.append(("hstack 1xn chain",))

    # ---- chains whose parts HOLD cells, folded through the deep model, so the
    # ---- placement facets accumulate over more than one step ----
    for cname in sorted(classes):
        vals = classes[cname]
        parts = [operand(2, k, vals) for k in range(4)]
        acc = facets(parts[0])
        for p in parts[1:]:
            acc = model_concat_right(acc, facets(p))
        if facets(SparseMatrix.hstack(*parts)) != acc:
            bad.append(("hstack fold", cname, acc,
                        facets(SparseMatrix.hstack(*parts))))
        parts = [operand(k, 2, vals) for k in range(4)]
        acc = facets(parts[0])
        for p in parts[1:]:
            acc = model_concat_below(acc, facets(p))
        if facets(SparseMatrix.vstack(*parts)) != acc:
            bad.append(("vstack fold", cname, acc,
                        facets(SparseMatrix.vstack(*parts))))
        n += 2

    # ---- type preservation (P2P guard) ----
    a = SparseMatrix(((1, 0), (0, 1)))
    b = SparseMatrix(((2, 0), (0, 2)))
    if type(a.row_join(b)) != type(a) or type(a.col_join(b)) != type(a):
        bad.append(("type preservation",))

    # ---- the F2P CONTENT case: joining onto an operand that holds nothing must
    # ---- reproduce the other operand IN FULL AND IN PLACE (== b).
    from sympy.matrices import MutableDenseMatrix
    e = MutableSparseMatrix([])
    f = MutableDenseMatrix([1, 2])
    for (model, meth) in ((model_concat_right, "row_join"),
                          (model_concat_below, "col_join")):
        r = getattr(e, meth)(f)
        if facets(r) != model(facets(e), facets(f)) or r != f:
            bad.append(("F2P content " + meth, facets(r),
                        model(facets(e), facets(f)), r == f))
        n += 1

    if bad:
        print("AXIOM-UNSOUND (deep model != real callee):", bad[:8])
        return 1
    print("5-facet A-reference SOUND: deep model == real SparseMatrix.row_join/"
          "col_join over", n, "observations spanning", len(classes), "payload "
          "classes and sparse/dense operands + F2P chains + folded "
          "cell-carrying chains + F2P content case + type preservation; "
          "ShapeError fires exactly on the model's raise path; the retention "
          "predicate split from the unequal-to-zero reading on", splits,
          "operand(s) and refuted the model under that reading", refuted,
          "time(s); the indeterminate-truth domain boundary holds.")
    return 0

sys.exit(main())
'''

_AX_SHAPE_CONTAIN = r'''
import sys

def main():
    from sympy import SparseMatrix, S, Eq

    # The model's Requires is: all five facets of both operands non-negative,
    # plus the two CARRIER INVARIANTS
    #   (rows==0 or cols==0) => held==0        [a zero dimension has no cells]
    #   held==0              => rsum==0 and csum==0   [an empty population sums 0]
    # The A-reference callee is SparseMatrix.row_join/col_join, whose supported
    # operand domain is ANY matrix: any non-negative int shape with any held-cell
    # population. So every operand the model can reach is constructible and
    # accepted, and the deep model is exercised exactly where the model reaches
    # it. A reachable operand the callee could NOT form would be
    # AXIOM-TOO-WEAK-FOR-CALLER; we confirm none exists by constructing every
    # grid shape (incl. the 0-dimension boundary and the rebuild operands
    # Mat(b.rows,0,0,0,0)/Mat(0,b.cols,0,0,0)) at every admissible held count AND
    # at the extreme placements of that population, and by confirming BOTH
    # invariants are real properties of the objects rather than restrictions.
    bad = []
    n = 0

    def facets(m):
        cells = [(i, j) for i in range(m.rows) for j in range(m.cols)
                 if m[i, j]]
        return (m.rows, m.cols, len(cells),
                sum(i for (i, j) in cells), sum(j for (i, j) in cells))

    # (i) invariant 1 is TRUE of the real objects: every zero-dimension matrix
    #     the callee accepts really does hold zero cells.
    for d in range(0, 6):
        for m in (SparseMatrix.zeros(0, d), SparseMatrix.zeros(d, 0)):
            f = facets(m)
            if f[2] != 0:
                bad.append(("invariant 1 violated by real object", f))
            n += 1

    # (ii) invariant 2 is TRUE of the real objects: a matrix holding no cell has
    #      both index sums zero — including one whose cells are all FALSY (the
    #      value class on which the retention predicate is decided), which is a
    #      non-degenerate shape holding nothing.
    for (r, c) in ((1, 1), (2, 3), (3, 2), (4, 4)):
        for filler in (0, S.false, Eq(1, 2)):
            m = SparseMatrix(r, c, lambda i, j: filler)
            f = facets(m)
            if f[2] != 0 or f[3] != 0 or f[4] != 0:
                bad.append(("invariant 2 violated by real object", (r, c),
                            str(filler), f))
            n += 1

    # (iii) every admissible (shape, held count) pair is constructible, and the
    #       index sums it can carry span the full range the carrier allows.
    for r in range(0, 4):
        for c in range(0, 4):
            cells = r * c
            for k in range(0, cells + 1):
                m = SparseMatrix(r, c,
                                 lambda i, j: 1 if i * c + j < k else 0)
                f = facets(m)
                if f[0] != r or f[1] != c or f[2] != k:
                    bad.append(("admissible (shape,held) not constructible",
                                r, c, k, f))
                if k == 0 and (f[3] != 0 or f[4] != 0):
                    bad.append(("cell-free operand with non-zero index sums",
                                r, c, f))
                n += 1
            # the extreme placements: all cells in the first row/column vs the
            # last, so the reachable (rsum, csum) range is exercised, not just
            # one representative.
            if cells:
                lo = SparseMatrix(r, c, lambda i, j: 1 if i == 0 else 0)
                hi = SparseMatrix(r, c, lambda i, j: 1 if i == r - 1 else 0)
                if facets(lo)[3] != 0:
                    bad.append(("first-row placement", r, c, facets(lo)))
                if facets(hi)[3] != c * (r - 1):
                    bad.append(("last-row placement", r, c, facets(hi)))
                n += 2

    # (iv) the normalisation rebuild operands the impl forms.
    for k in range(0, 5):
        if SparseMatrix.zeros(k, 0).shape != (k, 0):
            bad.append(("rebuild (k,0)", k))
        if SparseMatrix.zeros(0, k).shape != (0, k):
            bad.append(("rebuild (0,k)", k))
        n += 2

    if bad:
        print("AXIOM-TOO-WEAK-FOR-CALLER:", bad[:8])
        return 1
    print("containment OK: every operand the model can reach (non-negative "
          "five facets under BOTH carrier invariants, incl. the 0-dimension "
          "boundary, the all-falsy cell-free operand and the "
          "(b.rows,0,0,0,0)/(0,b.cols,0,0,0) rebuild operands, at every "
          "admissible held count and at the extreme index-sum placements) is "
          "constructible and accepted by the real row_join/col_join callee, and "
          "both carrier invariants are TRUE properties of the real objects "
          "rather than domain restrictions.", n, "operands confirmed.")
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-shape-sound", "axiom": "shape-A-reference", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_SHAPE_SOUND,
     "rationale": "if the real post-patch SparseMatrix.row_join/col_join differs from "
                  "the deep 5-facet model (the column/row sum, the held-cell count, the "
                  "two index sums, the degenerate normalisation, and ShapeError on the "
                  "incompatible path) on any operand => the A-reference is unsound "
                  "(AXIOM-UNSOUND). Strengthens axiom_check.py with a wider grid crossed "
                  "with the payload catalogue, explicit no-raise checks, an executable "
                  "refutation of the rejected retention predicate, and the "
                  "indeterminate-truth domain boundary."},
    {"id": "ax-shape-containment", "axiom": "shape-A-reference", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_SHAPE_CONTAIN,
     "rationale": "every operand the model can reach (its Requires: non-negative five "
                  "facets under both carrier invariants, plus the (b.rows,0,...)/(0,b.cols,"
                  "...) normalisation rebuilds) is constructible and accepted by the real "
                  "callee, at every admissible held count and at the extreme index-sum "
                  "placements, so the A-reference is exercised exactly where the caller "
                  "reaches it. A reachable operand the callee cannot form would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER (none exists)."},
]
