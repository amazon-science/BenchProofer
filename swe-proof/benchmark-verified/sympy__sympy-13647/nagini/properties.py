# properties.py — PBT falsification battery for sympy__sympy-13647.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside the `# impl-start` / `# impl-end` block (so the frozen spec — axioms,
# pure helpers, pre/post-conditions, signature — is byte-identical and
# same_spec holds). The runner stamps each with verify(host, Nagini) + same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (the spec this battery attacks)
# ---------------------------------------------------------------------------
#   insert_row(self_row: List[int], other_row: List[int],
#              cols: int, other_cols: int, pos: int) -> List[int]
#   builds ONE output row of a column-block insertion (the row-independent whole
#   content of MatrixShaping._eval_col_insert). self_row and other_row are
#   READ-ONLY inputs: Acc(list_pred(self_row), 1/2) / Acc(list_pred(other_row),
#   1/2), held verbatim in the Ensures.
#
#   The load-bearing postcondition is the per-position pin
#       Ensures(len(Result()) == cols + other_cols)
#       Ensures(Forall j: 0<=j<cols+other_cols ->
#                 Result()[j] == output_value(self_row,other_row,cols,
#                                              other_cols,pos,j))
#   where `output_value` (the `# pure` region) is the banding
#       j < pos                  -> self_row[j]           (left band)
#       pos <= j < pos+other_cols-> other_row[j - pos]    (middle / block band)
#       otherwise                -> self_row[j - other_cols]  (right band)
#   The DISCRIMINATING clause is the right band index `j - other_cols`
#   (corrected) vs the pre-patch `j - pos - other_cols` (which over-subtracts
#   `pos`), as in model_prepatch.py and the issue's eye(6).col_insert(3, V).
#
# Oracle-grounding note (ungrounded-oracle-echo class — DOES NOT APPLY):
#   `output_value` is a @Pure helper, but it is NOT an opaque answer-key oracle.
#   Its body is fully spelled out and reads ONLY the inputs (self_row[j],
#   other_row[j-pos], self_row[j-other_cols]); the postcondition unfolds it. An
#   impl that "echoes" output_value (return [output_value(...) for each j]) is
#   therefore the CORRECT gold answer, not a cheat — there is no wrong value to
#   echo. The discriminating content lives entirely INSIDE output_value's
#   banding. So we instead supply (a) an honest structurally-different positive
#   control that echoes output_value directly (cheapest correct impl, must
#   verify) and (b) the partial-domain band-corruption rivals below, each of
#   which perturbs the band so Result()[j] != output_value(...) on a subdomain.
#
# Control-flow-effect note (DOES NOT APPLY):
#   insert_row has no raise / early-return / side-effect branch — it is a single
#   total value-producing loop with no exceptional path. The whole content is
#   the produced row, which the value abstraction already pins per position. So
#   there is no capability-token discriminator to add; omitted (see assessment).

from pathlib import Path

INSTANCE = "sympy__sympy-13647"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything between # impl-start and
# # impl-end, markers exclusive). Every variant is produced by _swap on _BASE
# touching ONLY text inside this block.
_GOLD_IMPL = """    width = cols + other_cols
    result = []  # type: List[int]
    j = 0
    while j < width:
        # invariants-start
        Invariant(Acc(list_pred(self_row), 1 / 2))
        Invariant(Acc(list_pred(other_row), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(cols >= 0 and other_cols >= 0)
        Invariant(0 <= pos and pos <= cols)
        Invariant(width == cols + other_cols)
        Invariant(len(self_row) == cols and len(other_row) == other_cols)
        Invariant(0 <= j and j <= width)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda b: (
            Implies(0 <= b and b < j,
                    result[b] == output_value(
                        self_row, other_row, cols, other_cols, pos, b)),
            [[result[b]]])))
        Invariant(MustTerminate(width - j + 1))
        # invariants-end
        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - other_cols]
        # v is exactly the banded source value for output index j.
        Assert(v == output_value(self_row, other_row, cols, other_cols,
                                   pos, j))
        old_result = result
        result = result + [new_matrix_cell(v)]
        # the append preserves every prior element and places v at index j.
        Assert(len(result) == j + 1)
        Assert(Forall(int, lambda b: (
            Implies(0 <= b and b < j, result[b] == old_result[b]),
            [[result[b]]])))
        Assert(result[j] == new_matrix_cell(v))
        Assert(result[j] == output_value(self_row, other_row, cols,
                                            other_cols, pos, j))
        j = j + 1
    return result
"""

# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# The exact band-computation block (the only thing the partial-domain rivals
# perturb). The framing/lemma asserts AROUND it are kept verbatim in every rival
# so a rejection is attributable to the BAND being wrong (Result()[j] !=
# output_value(...)), never to a deleted proof obligation.
_GOLD_BAND = """        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - other_cols]"""


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
#    Reshape: instead of the if/elif/else chain that binds a local `v`, call the
#    pure `output_value` band oracle directly (v = output_value(...)). This is a
#    legitimate, faithful impl (output_value IS the corrected banding, validated
#    == the real patched callee by G-AX) and is the cheapest correct shape. It
#    keeps the FORWARD append, the prefix-preservation invariant, and EVERY gold
#    framing assert verbatim, so the gold proof obligations still discharge.
#    MUST verify — else SPEC-TOO-STRONG.
_POS_IMPL = _swap(
    _GOLD_IMPL,
    _GOLD_BAND,
    "        v = output_value(self_row, other_row, cols, other_cols, pos, j)",
)


# ===========================================================================
# 2. POSITIVE CONTROL #2 (soundness) — a DIFFERENT structural reshape that
#    keeps the explicit 3-way band but REORDERS it: test the right band first
#    (j >= pos + other_cols), then the left band, then fall through to the
#    middle/block band. The three guards still partition 0..width-1 identically,
#    so v is the same value for every j; all gold asserts are kept verbatim.
#    MUST verify — else SPEC-TOO-STRONG (the spec would be rejecting a faithful
#    branch-reorder).
_POS2_IMPL = _swap(
    _GOLD_IMPL,
    _GOLD_BAND,
    """        if j >= pos + other_cols:
            v = self_row[j - other_cols]
        elif j < pos:
            v = self_row[j]
        else:
            v = other_row[j - pos]""",
)


# ===========================================================================
# 3. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input.
#    The Requires is permission (Acc(list_pred,1/2)) + the already-clamped
#    matrix-shape facts (cols,other_cols>=0; 0<=pos<=cols; len matches). The
#    issue's witness is eye(6).col_insert(3, 6x2 block): per row that is
#    self_row of width cols=6, other_row of width other_cols=2, pos=3 — squarely
#    in-domain. We keep the full gold impl and add, at the TOP of impl,
#    derivable assertions that confirm the shape facts the model relies on are
#    establishable (a 1/4 read share is obtainable from the 1/2 held; the
#    band-window arithmetic pos+other_cols <= width is consistent). If this
#    fails to verify => PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    Assert(Acc(list_pred(self_row), 1 / 4))
    Assert(Acc(list_pred(other_row), 1 / 4))
    Assert(len(self_row) == cols and len(other_row) == other_cols)
    Assert(0 <= pos and pos <= cols and other_cols >= 0)
""" + _GOLD_IMPL


# ===========================================================================
# 4. FRAME-MUTATION (MANDATORY — read-only inputs). A rival that WRITES to the
#    read-only input `self_row` before the loop. With only
#    Acc(list_pred(self_row), 1/2) the assignment self_row[0] = 0 needs FULL
#    permission and MUST be rejected for insufficient permission. Every gold
#    invariant / band / assert is kept verbatim so the rejection is attributable
#    to the WRITE, not to a proof gap. expect=reject.
#    Refinement: the repo callee `_eval_col_insert.entry` reads `self[i, j]` /
#    `other[i, j-pos]` from the SOURCE matrices and never writes into them; the
#    new matrix is built fresh by `self._new(...)`. A faithful patch cannot
#    mutate the source row. One that zeroed self_row[0] before reading would
#    corrupt the left band: on the issue's eye(6).col_insert(3, V) the first
#    diagonal 1 at output (0,0) would read 0 instead of 1, so the result no
#    longer equals the expected Matrix([[1,0,0,2,2,0,0,0],...]) — F2P
#    test_col_insert FAILS. So a verifying mutator is a true verify-not-resolve
#    break.
_FRAME_IMPL = _swap(
    _GOLD_IMPL,
    "    width = cols + other_cols\n    result = []",
    "    if cols > 0:\n        self_row[0] = 0\n    width = cols + other_cols\n    result = []",
)


# ===========================================================================
# 5. PARTIAL-DOMAIN (the LITERAL pre-patch bug) — right band reads
#    self_row[j - pos - other_cols] (over-subtracts pos). Identical to
#    model_prepatch.py. Only the right-band index is changed; the framing asserts
#    are kept verbatim, so it fails ONLY on Assert(v == output_value(...)) /
#    the loop invariant (the right band disagrees whenever pos>0 and a right band
#    exists). expect=reject.
#    Refinement: this is the exact regression. On the issue's
#    eye(6).col_insert(3, 6x2 of twos), the right band (output cols 5..7) reads
#    self_row[j - 3 - 2] = self_row[j-5] instead of self_row[j-2], shifting the
#    trailing identity block from the bottom rows up to the top — producing the
#    buggy Out[33] in the issue, NOT the expected Matrix; F2P test_col_insert
#    FAILS. The canonical verify-not-resolve rival.
_PREPATCH_BAND = """        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - pos - other_cols]"""
_PREPATCH_IMPL = _swap(_GOLD_IMPL, _GOLD_BAND, _PREPATCH_BAND)


# ===========================================================================
# 6. PARTIAL-DOMAIN (off-by-one right band) — right band reads
#    self_row[j - other_cols + 1] (under-subtracts by 1). Correct on the left and
#    middle bands and at the first right-band position when other_cols makes it
#    coincide, but shifts every trailing original entry by one column. Framing
#    asserts kept verbatim; fails on Assert(v == output_value(...)). expect=reject.
#    Refinement: a faithful patch with `self[i, j - other.cols + 1]` would, on
#    eye(6).col_insert(0, V) (pos=0, other_cols=2), read the right band at
#    self_row[j-1] instead of self_row[j-2]: output col 2 would read self_row[1]
#    (=0) instead of self_row[0] (=1), losing the leading diagonal 1 — the
#    result no longer equals the expected col_insert Matrix; F2P test_col_insert
#    FAILS. (And every P2P col_insert assertion that exercises a right band fails
#    too.) A real off-by-one in the corrected index would not resolve.
_OFFBYONE_BAND = """        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - other_cols + 1]"""
_OFFBYONE_IMPL = _swap(_GOLD_IMPL, _GOLD_BAND, _OFFBYONE_BAND)


# ===========================================================================
# 7. PARTIAL-DOMAIN (wrong middle-band offset) — the block band reads
#    other_row[j] instead of other_row[j - pos] (drops the insertion offset).
#    Correct when pos==0; wrong for every pos>0 inserted-block position. Framing
#    asserts kept verbatim; fails on Assert(v == output_value(...)). expect=reject.
#    Refinement: a patch returning `other[i, j]` for the block band would, on
#    eye(6).col_insert(3, V) (pos=3), read the inserted twos at other_row[3],
#    other_row[4] — out of the width-2 block (index error / wrong value) rather
#    than other_row[0], other_row[1]; the inserted columns would not be the
#    expected pair of 2-columns at output cols 3,4; F2P test_col_insert FAILS.
#    A real patch dropping the `- pos` block offset would not resolve.
_MIDBAND_BAND = """        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j]
        else:
            v = self_row[j - other_cols]"""
_MIDBAND_IMPL = _swap(_GOLD_IMPL, _GOLD_BAND, _MIDBAND_BAND)


# ===========================================================================
# 8. PARTIAL-DOMAIN (single-position miss) — correct EVERYWHERE except output
#    index j == width-1 (the last column), where it returns a fixed 0 instead of
#    the banded value. A near-miss that pins the entire domain but one position;
#    framing asserts kept verbatim; fails on Assert(v == output_value(...)) at
#    that one j. expect=reject.
#    Refinement: a patch that special-cased the final column to 0 would, on
#    eye(6).col_insert(3, V), set output (i, 7) to 0; for i in {3,4,5} the
#    expected last column is the trailing diagonal 1, so (3,7),(4,7),(5,7) would
#    be 0 not the expected ...,0,0,1] tail — the result is not the expected
#    Matrix; F2P test_col_insert FAILS. A real one-position bug would not resolve.
_LASTPOS_BAND = """        if j == width - 1:
            v = 0
        elif j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - other_cols]"""
_LASTPOS_IMPL = _swap(_GOLD_IMPL, _GOLD_BAND, _LASTPOS_BAND)


SPEC_TESTS = [
    {
        "id": "pos-control-echo-output-value",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: drops the explicit 3-way "
            "if/elif/else and binds v = output_value(...) directly (the cheapest "
            "faithful shape; output_value IS the corrected banding, G-AX-"
            "validated == the real patched _eval_col_insert). Keeps the forward "
            "append, the prefix-preservation invariant, and every gold framing "
            "assert verbatim, so the gold proof obligations still discharge. "
            "Must verify; if it cannot, the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-band-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS2_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: same explicit 3-way band, "
            "but the guards are REORDERED (right band tested first, then left, "
            "then the block band falls through). The three guards still partition "
            "0..width-1 identically so v is unchanged for every j; all gold "
            "asserts kept verbatim. Must verify; if it cannot, SPEC-TOO-STRONG "
            "(rejecting a faithful branch reorder)."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is permission (Acc(list_pred,1/2)) + the clamped "
            "matrix-shape facts; the issue's witness eye(6).col_insert(3, 6x2) "
            "is per-row self_row width 6, other_row width 2, pos=3 — in-domain. "
            "Added top-of-impl assertions confirm a 1/4 read share is derivable "
            "from the 1/2 held and the shape facts hold. Must verify; if it "
            "cannot, PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutate-readonly-self-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_IMPL),
        "refinement": (
            "the repo callee _eval_col_insert.entry only READS self[i,j] / "
            "other[i,j-pos] and builds a fresh matrix via self._new(...); a "
            "faithful patch cannot write into the source row. One that zeroed "
            "self_row[0] would corrupt the left band: on eye(6).col_insert(3, V) "
            "output (0,0) would read 0 instead of the diagonal 1, so the result "
            "is not the expected Matrix([[1,0,0,2,2,0,0,0],...]) — F2P "
            "test_col_insert FAILS. A verifying mutator is a true "
            "verify-not-resolve break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: self_row holds only "
            "Acc(list_pred(self_row),1/2); the write self_row[0]=0 needs full "
            "permission and is rejected for insufficient permission. Every gold "
            "invariant/band/assert is kept verbatim so the failure is "
            "attributable to the write, not a proof gap. If it verifies, the "
            "frame is unguarded (FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-prepatch-right-band",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PREPATCH_IMPL),
        "refinement": (
            "the LITERAL pre-patch bug (== model_prepatch.py): right band reads "
            "self_row[j - pos - other_cols] (over-subtracts pos). On the issue's "
            "eye(6).col_insert(3, 6x2 of twos) the trailing identity block is "
            "shifted from the bottom rows to the top (the buggy Out[33] in the "
            "issue), so the result is NOT the expected Matrix; F2P "
            "test_col_insert FAILS. The canonical verify-not-resolve rival."
        ),
        "rationale": (
            "REJECT comes from the postcondition pin Result()[j] == "
            "output_value(...): the right band value self_row[j-pos-other_cols] "
            "!= output_value's self_row[j-other_cols] whenever pos>0 and a right "
            "band exists, so Assert(v == output_value(...)) / the loop invariant "
            "fails. If it verifies, the spec does not pin the corrected right-"
            "band index (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-offbyone-right-band",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _OFFBYONE_IMPL),
        "refinement": (
            "off-by-one corrected index: right band reads self_row[j - "
            "other_cols + 1]. On eye(6).col_insert(0, V) (pos=0, other_cols=2) "
            "output col 2 reads self_row[1]=0 instead of self_row[0]=1, losing "
            "the leading diagonal 1; the result is not the expected col_insert "
            "Matrix; F2P test_col_insert FAILS. A real off-by-one in the "
            "corrected index would not resolve."
        ),
        "rationale": (
            "REJECT comes from Result()[j] == output_value(...): self_row[j-"
            "other_cols+1] != output_value's self_row[j-other_cols] in the right "
            "band (where the indices differ by 1), so Assert(v == "
            "output_value(...)) fails. If it verifies, the right-band index is "
            "unpinned to within +/-1 (partial-domain SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-middle-band-offset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _MIDBAND_IMPL),
        "refinement": (
            "the block band drops the insertion offset: reads other_row[j] "
            "instead of other_row[j-pos]. Correct only when pos==0. On "
            "eye(6).col_insert(3, V) (pos=3) the inserted twos at output cols "
            "3,4 would be read from other_row[3]/other_row[4] (outside the "
            "width-2 block) rather than other_row[0]/other_row[1]; the inserted "
            "columns are wrong; F2P test_col_insert FAILS. A patch dropping the "
            "'- pos' block offset would not resolve."
        ),
        "rationale": (
            "REJECT comes from Result()[j] == output_value(...): in the middle "
            "band output_value reads other_row[j-pos]; other_row[j] disagrees "
            "whenever pos>0, so Assert(v == output_value(...)) fails. If it "
            "verifies, the block-band offset is unpinned (partial-domain "
            "SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-last-column-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _LASTPOS_IMPL),
        "refinement": (
            "correct EVERYWHERE except the final output column (j==width-1), "
            "which is forced to 0. On eye(6).col_insert(3, V) output (i,7) for "
            "i in {3,4,5} would be 0 instead of the expected trailing diagonal "
            "1; the result is not the expected Matrix; F2P test_col_insert "
            "FAILS. A real one-position special-case bug would not resolve."
        ),
        "rationale": (
            "REJECT comes from Result()[j] == output_value(...) at j==width-1: "
            "the forced 0 != output_value's banded value (self_row[width-1-"
            "other_cols] when a right band exists, generally nonzero), so "
            "Assert(v == output_value(...)) fails at that position. If it "
            "verifies, the postcondition leaves the last column unpinned "
            "(partial-domain SPEC-TOO-WEAK)."
        ),
    },
]


# ===========================================================================
# AXIOM lane — the bundle has ONE @ContractOnly axiom (new_matrix_cell,
# A-consumed) and ONE A-reference deep model (output_value). axiom_check.py
# already validates both IN-container against the real callee; we mirror its two
# obligations as independent PBT probes.
#
#   ax-new-matrix-cell-soundness (axiom-soundness): the UNCHANGED matrix
#     constructor self._new(rows, cols, entry) materialises the entry function
#     value-preservingly — the stored cell M[i,j] == entry(i,j). Run the REAL
#     _MinimalMatrix._new / __getitem__ over boundary + fuzz shapes (apply_gold:
#     _new is unchanged by the patch, but we run post-gold for parity with G-AX).
#     If the real cell != entry value -> AXIOM-UNSOUND.
#
#   ax-new-matrix-cell-containment (axiom-containment): every value the MODEL
#     ever feeds to new_matrix_cell is `v` = output_value(...) = an integer drawn
#     from self_row[...] / other_row[...] (the abstracted matrix entries). The
#     axiom's Requires domain is `value: int` (unconstrained int) — so every
#     reachable argument (any int the entry banding can produce) is trivially in
#     domain. Confirm by running the real patched _eval_col_insert and showing
#     every produced cell value is exactly such an int entry (no value the model
#     can reach falls outside the axiom's int domain).
#
#   ax-output-value-fidelity (axiom-soundness on the A-reference): the deep model
#     output_value EQUALS the real patched _eval_col_insert cell by cell over the
#     issue example + boundary + fuzz, AND the pre-patch right band is detectably
#     wrong. This is the discriminating obligation: if output_value disagreed
#     with the real patched callee, the A-reference would be UNSOUND.
#
# All probes import only sympy.matrices.common + stdlib, open nothing on disk,
# exit 0 iff the obligation holds. (The runner mounts ONLY the probe script in
# the instance image; these probes are self-contained.)

_NEW_CELL_SOUNDNESS_PROBE = r'''
import random, sys
from sympy.matrices.common import _MinimalMatrix, MatrixShaping


class ShapingMatrix(_MinimalMatrix, MatrixShaping):
    """The minimal matrix the repo test suite uses (ShapingOnlyMatrix):
    _MinimalMatrix storage + MatrixShaping behaviour."""
    pass


def make(rows, cols, f):
    return ShapingMatrix(rows, cols, lambda i, j: f(i, j))


# new_matrix_cell axiom: Ensures(Result() == value) — _new materialises the
# entry function value-preservingly, cell by cell. Run the REAL _new /
# __getitem__ and assert M[i,j] == entry(i,j).
def check_value_preserving(rows, cols):
    f = lambda i, j: i * 100 + j      # injective entry function
    M = make(rows, cols, f)
    if not (M.rows == rows and M.cols == cols):
        print("AXIOM-UNSOUND: _new produced wrong shape %r for %dx%d" % (M.shape, rows, cols))
        sys.exit(1)
    for i in range(rows):
        for j in range(cols):
            if M[i, j] != f(i, j):
                print("AXIOM-UNSOUND: _new(%d,%d,f)[%d,%d]=%r != f=%r"
                      % (rows, cols, i, j, M[i, j], f(i, j)))
                sys.exit(1)


boundary = [(1, 1), (1, 3), (3, 1), (2, 2), (6, 6), (4, 5), (1, 8), (8, 1)]
for (r, c) in boundary:
    check_value_preserving(r, c)
rng = random.Random(13647)
for _ in range(2000):
    check_value_preserving(rng.randint(1, 8), rng.randint(1, 8))
print("AXIOM-SOUND: real _new value-preserving (M[i,j]==entry(i,j)) over %d boundary + 2000 fuzz shapes" % len(boundary))
sys.exit(0)
'''


_NEW_CELL_CONTAINMENT_PROBE = r'''
import random, sys
from sympy.matrices.common import _MinimalMatrix, MatrixShaping


class ShapingMatrix(_MinimalMatrix, MatrixShaping):
    pass


def make(rows, cols, f):
    return ShapingMatrix(rows, cols, lambda i, j: f(i, j))


# Containment: the axiom's Requires domain for new_matrix_cell is `value: int`
# (an unconstrained int). The only values the MODEL feeds to new_matrix_cell are
# v = output_value(...) = an integer matrix entry drawn from self_row / other_row
# (the int-abstracted matrix cells). So every reachable argument is an int and is
# trivially inside the axiom's int domain. We confirm empirically: run the REAL
# patched _eval_col_insert over the modeled (integer) domain and assert every
# produced cell value is a Python int — i.e. nothing the model can reach falls
# outside the axiom's int domain. A non-int reachable value would be
# AXIOM-TOO-WEAK-FOR-CALLER.
def col_insert_cells(rows, cols, other_cols, pos):
    self_vals = lambda i, j: i * 1000 + j + 1
    other_vals = lambda i, j: -(i * 1000 + j + 1)
    self_m = make(rows, cols, self_vals)
    other_m = make(rows, other_cols, other_vals)
    p = pos
    if p < 0:
        p = cols + p
    if p < 0:
        p = 0
    elif p > cols:
        p = cols
    res = self_m._eval_col_insert(p, other_m)
    width = cols + other_cols
    out = []
    for i in range(rows):
        for j in range(width):
            out.append(res[i, j])
    return out


def assert_all_int(vals, shape):
    for x in vals:
        # the int-abstracted matrix entry must be a (Python or sympy) integer;
        # int(x) must round-trip exactly for the abstraction to be in-domain.
        try:
            if int(x) != x:
                print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches non-int cell %r at shape %r" % (x, shape))
                sys.exit(1)
        except (TypeError, ValueError):
            print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches non-int cell %r at shape %r" % (x, shape))
            sys.exit(1)


# the issue example + boundary + fuzz over the modeled integer domain
assert_all_int(col_insert_cells(6, 6, 2, 3), (6, 6, 2, 3))
boundary = [(1, 1, 1, 0), (1, 1, 1, 1), (3, 3, 1, 0), (3, 3, 1, 2),
            (3, 3, 1, 3), (6, 6, 2, 0), (6, 6, 2, 6), (4, 5, 3, 2),
            (2, 7, 4, 5), (5, 2, 2, 1), (3, 4, 0, 2)]
for (r, c, oc, p) in boundary:
    assert_all_int(col_insert_cells(r, c, oc, p), (r, c, oc, p))
rng = random.Random(136470)
for _ in range(1500):
    r = rng.randint(1, 7); c = rng.randint(1, 7)
    oc = rng.randint(0, 5); p = rng.randint(0, c)
    assert_all_int(col_insert_cells(r, c, oc, p), (r, c, oc, p))
print("AXIOM-COVERED: every model-reachable new_matrix_cell argument is an int (in the axiom's int domain) over the issue example + %d boundary + 1500 fuzz column-insertions" % len(boundary))
sys.exit(0)
'''


_OUTPUT_VALUE_FIDELITY_PROBE = r'''
import random, sys
from sympy.matrices.common import _MinimalMatrix, MatrixShaping


class ShapingMatrix(_MinimalMatrix, MatrixShaping):
    pass


def make(rows, cols, f):
    return ShapingMatrix(rows, cols, lambda i, j: f(i, j))


# A-reference fidelity: the model's output_value banding (left -> self_row[j];
# middle -> other_row[j-pos]; right -> self_row[j-other_cols]) EQUALS the real
# patched _eval_col_insert cell by cell, AND the pre-patch right band
# (j - pos - other_cols) is DETECTABLY wrong wherever a right band exists with
# pos>0 (so the spec discriminates the bug).
def output_value(self_row, other_row, cols, other_cols, pos, j):
    if j < pos:
        return self_row[j]
    if j < pos + other_cols:
        return other_row[j - pos]
    return self_row[j - other_cols]              # CORRECTED right band


def buggy_value(self_row, other_row, cols, other_cols, pos, j):
    if j < pos:
        return self_row[j]
    if j < pos + other_cols:
        return other_row[j - pos]
    return self_row[j - pos - other_cols]        # PRE-PATCH right band


def check(rows, cols, other_cols, pos):
    self_vals = lambda i, j: i * 1000 + j + 1
    other_vals = lambda i, j: -(i * 1000 + j + 1)
    self_m = make(rows, cols, self_vals)
    other_m = make(rows, other_cols, other_vals)
    p = pos
    if p < 0:
        p = cols + p
    if p < 0:
        p = 0
    elif p > cols:
        p = cols
    res = self_m._eval_col_insert(p, other_m)
    width = cols + other_cols
    if not (res.rows == rows and res.cols == width):
        print("AXIOM-UNSOUND: real _eval_col_insert wrong shape %r" % (res.shape,))
        sys.exit(1)
    discriminated = False
    for i in range(rows):
        self_row = [self_vals(i, c) for c in range(cols)]
        other_row = [other_vals(i, c) for c in range(other_cols)]
        for j in range(width):
            got = res[i, j]
            exp = output_value(self_row, other_row, cols, other_cols, p, j)
            if got != exp:
                print("AXIOM-UNSOUND: output_value != real patched _eval_col_insert at "
                      "(%d,%d) shape self=%dx%d other=%dx%d pos=%d: real=%r model=%r"
                      % (i, j, rows, cols, rows, other_cols, p, got, exp))
                sys.exit(1)
            if j >= p + other_cols and p > 0:
                bug = buggy_value(self_row, other_row, cols, other_cols, p, j)
                if bug != exp:
                    discriminated = True
    return discriminated


# the issue's exact example: eye(6).col_insert(3, 6x2 of twos)
check(6, 6, 2, 3)
fidelity = [(1, 1, 1, 0), (1, 1, 1, 1), (3, 3, 1, 0), (3, 3, 1, 1),
            (3, 3, 1, 2), (3, 3, 1, 3), (6, 6, 2, 0), (6, 6, 2, 3),
            (6, 6, 2, 6), (4, 5, 3, 2), (2, 7, 4, 5), (5, 2, 2, 1),
            (3, 4, 0, 2)]
any_discriminated = False
for (r, c, oc, p) in fidelity:
    if check(r, c, oc, p):
        any_discriminated = True
rng = random.Random(1364700)
for _ in range(3000):
    r = rng.randint(1, 7); c = rng.randint(1, 7)
    oc = rng.randint(0, 5); p = rng.randint(0, c)
    if check(r, c, oc, p):
        any_discriminated = True
if not any_discriminated:
    print("AXIOM check anomaly: the pre-patch banding never differed from the correct one — discrimination not witnessed")
    sys.exit(1)
print("AXIOM-SOUND: output_value == real patched _eval_col_insert over the issue example + %d boundary + 3000 fuzz column-insertions; pre-patch right band detectably wrong" % len(fidelity))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-new-matrix-cell-soundness",
        "axiom": "new_matrix_cell",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _NEW_CELL_SOUNDNESS_PROBE,
        "rationale": (
            "new_matrix_cell models the UNCHANGED constructor _new; the proof "
            "consumes only value-preservation (Ensures(Result()==value)). Runs "
            "the REAL _MinimalMatrix._new / __getitem__ and asserts M[i,j] == "
            "entry(i,j) over boundary + fuzz shapes. If the real cell != entry "
            "value -> AXIOM-UNSOUND. Mirrors axiom_check.py's _new check."
        ),
    },
    {
        "id": "ax-new-matrix-cell-containment",
        "axiom": "new_matrix_cell",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _NEW_CELL_CONTAINMENT_PROBE,
        "rationale": (
            "the only values the model feeds new_matrix_cell are v = "
            "output_value(...), int matrix entries — always inside the axiom's "
            "unconstrained int Requires domain. Confirmed by running the real "
            "patched _eval_col_insert over the modeled integer domain and "
            "asserting every produced cell is an int. A non-int reachable value "
            "would be AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
    {
        "id": "ax-output-value-fidelity",
        "axiom": "output_value",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _OUTPUT_VALUE_FIDELITY_PROBE,
        "rationale": (
            "output_value is the A-reference deep model of the patched "
            "_eval_col_insert.entry banding. Runs the REAL patched callee and "
            "asserts output_value == it cell by cell over the issue example + "
            "boundary + fuzz, AND that the pre-patch right band is detectably "
            "wrong. If output_value disagreed with the real patched callee, the "
            "A-reference would be UNSOUND. Requires apply_gold=True (validates "
            "the PATCHED callee). Mirrors axiom_check.py's fidelity check."
        ),
    },
]
