"""properties.py — PBT falsification battery for astropy__astropy-12907.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the # impl-start
.. # impl-end region is edited via _swap) and are checked by Nagini verify +
markers.same_spec. There are NO @ContractOnly axioms / A-reference deep models in
this bundle (axioms[] is empty; the block placement is modelled deeply by the
pure expected_row/zeros and pinned row-by-row), so AXIOM_TESTS = [].

DEFENDED SURFACE (why these cases and not byte-fuzz):
  parallel_dependency_matrix(left, right, lr, lc, rr, rc) -> PSeq[PSeq[int]]
  builds the side-by-side ('&'-operator) dependency matrix as two diagonal
  blocks. Two load-bearing postcondition clauses:
    (P1) is_grid(Result(), lr+rr, lc+rc)  -- shape pin
    (P2) Forall i in [0, lr+rr): Result()[i] == expected_row(left,right,...,i)
         -- ROW-EXACT pin against the GROUNDED pure deep model expected_row,
            whose lower rows are zeros(lc) ++ right[i-lr] (the FIX), upper rows
            left[i] ++ zeros(rc).

  No Acc(x,1/2) read-only input exists: left/right are PSeq[PSeq[int]] (pure,
  immutable, carry no list_pred heap permission). The frame-mutation class is
  therefore vacuous here -- there is no heap cell to overwrite to satisfy a
  postcondition; a mutating rival cannot even be written against this carrier.
  This is the deliberate purpose of the PSeq carrier (mapping.md S2): directive 5
  is satisfied by construction, not by a contract.  has_readonly_input = False.

  expected_row is a GROUNDED oracle (a total function of the args, fully
  unfolded: left[i] ++ zeros(rc) / zeros(lc) ++ right[i-lr]); there is no opaque
  answer-key to echo. The only "wrong echo" is to fill the lower-right block with
  a constant (the prepatch bug) -- covered as a uniqueness/partial-domain reject
  rather than an ungrounded-oracle echo. Per directive 2 we therefore also carry
  an honest cheapest-correct positive control.

  The genuine attacks are uniqueness / partial-domain rivals that satisfy P1
  (correct shape) and even the upper-block rows, but diverge on the lower-right
  block on some sub-domain -- exactly where the bug lived.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-12907"
FLOAT_ENCODING = None  # meta.float_encoding is null; integer 0/1 carrier, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region, anchored on unique substrings, so every variant edits
# ONLY inside # impl-start .. # impl-end (guarantees same_spec).
# ---------------------------------------------------------------------------

# The two-branch row construction in the gold impl (upper = left+zeros, lower =
# zeros+right) is the unique anchor we surgically replace per variant.
_GOLD_BRANCH = """        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq[int]
        else:
            # lower row: lc leading zeros (left block empty) then right[i-lr].
            row = zeros(lc) + right[i - lr]"""


# === POSITIVE CONTROL 1 (soundness) ========================================
# Structurally-different CORRECT impl: instead of inlining the block-placement,
# call the pure deep model expected_row(...) directly for every row. This is a
# local reshape that KEEPS every gold loop invariant and framing assert (the
# subsequent Assert(row == expected_row(...)) becomes trivially reflexive), so
# the gold proof obligations are all still discharged. If a faithful correct
# impl could not verify => SPEC-TOO-STRONG.
_POS1_BRANCH = """        row = expected_row(left, right, lr, lc, rr, rc, i)  # type: PSeq[int]"""

# === POSITIVE CONTROL 2 (soundness) ========================================
# Branch-REORDER variant: test the lower (i >= lr) case first, then the upper
# case in the else. Same values, different control-flow shape. Keeps all gold
# invariants/asserts. (Branch reorder, NOT a loop-direction flip / forward-
# append, so no f(a+b) fold lemma is needed -- directive 3 avoided.)
_POS2_BRANCH = """        if i >= lr:
            # lower row first: lc leading zeros then the actual right[i-lr].
            row = zeros(lc) + right[i - lr]  # type: PSeq[int]
        else:
            # upper row: left[i] then rc trailing zeros.
            row = left[i] + zeros(rc)"""

# === ADMISSIBILITY (precondition not too strong) ===========================
# Insert, at the top of the impl, the construction of a concrete F2P-shaped
# input grid (a 2x2 0/1 matrix) and assert is_grid holds for it. This proves the
# precondition predicate is_grid(...) is SATISFIABLE by a concrete grid of the
# F2P shape -- i.e. the Requires admits a normal input (else PRECOND-TOO-STRONG;
# e.g. if is_grid were unsatisfiable the precondition would be vacuously False
# and the whole spec degenerate). Inserted before the loop; does not touch the
# spec regions and keeps the gold loop body intact.
_ADMISS_INSERT = """    noutp = lr + rr
    # admissibility witness: a concrete F2P-shaped 2x2 0/1 grid satisfies is_grid,
    # so the precondition is non-vacuously satisfiable for normal inputs.
    r0 = PSeq(1, 0)  # type: PSeq[int]
    r1 = PSeq(0, 1)  # type: PSeq[int]
    witness = PSeq(r0, r1)  # type: PSeq[PSeq[int]]
    Assert(len(witness) == 2)
    Assert(len(witness[0]) == 2 and len(witness[1]) == 2)
    Assert(is_grid(witness, 2, 2))"""


# === UNIQUENESS / PARTIAL-DOMAIN rivals (must be REJECTED) =================

# --- weak-prepatch: the actual gold bug. Lower rows fill the lower-right block
# with a constant 1-block (np.ones) instead of copying right[i-lr]. Correct
# shape (P1) and correct upper rows, but diverges on every lower row where right
# has a 0 entry -- exactly the nested-CompoundModel F2P scenario.
_PREPATCH_BRANCH = """        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq[int]
        else:
            # lower row: lc leading zeros then a CONSTANT 1-block (the bug:
            # cright[-rr:,-rc:] = 1 instead of = right). Width rc.
            block = PSeq(1).take(0)  # type: PSeq[int]
            t = 0
            while t < rc:
                # invariants-start
                Invariant(0 <= t and t <= rc)
                Invariant(len(block) == t)
                # This rival's own INNER loop must discharge the shared
                # Requires(MustTerminate(2)) too: at most `rc - t` iterations
                # remain within THIS outer pass, `t` rises by 1 each pass and
                # `rc` is a loop-invariant parameter (independent of the outer
                # `i`), so the bound strictly decreases and `+ 1` keeps it
                # positive. Without it the rival would be rejected for an
                # obligation LEAK rather than for the value postcondition, and
                # the uniqueness finding would not be attributable to P2.
                Invariant(MustTerminate(rc - t + 1))
                # invariants-end
                block = block + PSeq(1)
                t = t + 1
            row = zeros(lc) + block"""

# --- weak-firstrow: copies right for every lower row EXCEPT the first lower row
# (i == lr), which is left as the empty-left + zeros(rc) (all zeros). Pins P1
# (shape ok) and is correct on lr-1 of the rr lower rows. Diverges only on the
# single first lower row whenever right[0] has any 1 entry. Tests that P2 pins
# EVERY row, not "most rows".
_FIRSTROW_BRANCH = """        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq[int]
        elif i == lr:
            # FIRST lower row dropped to an all-zero row (off by the actual
            # right[0]) -- a single-row partial-domain divergence.
            row = zeros(lc) + zeros(rc)
        else:
            row = zeros(lc) + right[i - lr]"""

# --- weak-reverse: copies the RIGHT block but with its rows in REVERSED order
# (right[rr-1-(i-lr)] instead of right[i-lr]). Correct shape, correct on the
# upper block, and equal to the gold matrix only when right's row-sequence is a
# palindrome. Diverges on the generic F2P right child.
_REVERSE_BRANCH = """        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq[int]
        else:
            # lower row: lc zeros then the right row in REVERSED order.
            row = zeros(lc) + right[rr - 1 - (i - lr)]"""

# --- weak-leftpad: lower rows prepend the matching LEFT row instead of zeros
# in the lower-left block (lower-left block = left[i-lr] instead of zeros(lc)),
# then right[i-lr]. Width is still lc+rc (correct P1), but the lower-left block
# is non-zero whenever left has a 1 -- a spurious dependence, the dual of the
# original bug.
_LEFTPAD_BRANCH = """        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq[int]
        else:
            # lower row: lower-left block filled with left[i-lr] (should be
            # zeros) then the actual right[i-lr]. Spurious off-diagonal block.
            row = left[i - lr] + right[i - lr]"""


def _variant(branch):
    return _swap(_BASE, _GOLD_BRANCH, branch)


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-expected-row-call",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS1_BRANCH),
        "rationale": (
            "structurally-different CORRECT impl: each row is built by directly "
            "calling the pure deep model expected_row(...) rather than inlining "
            "the block placement. Keeps every gold invariant + framing assert "
            "(the Assert(row == expected_row(...)) becomes reflexive). Must "
            "verify; if not, SPEC-TOO-STRONG (the postcondition P2 would reject "
            "its own oracle's output)."
        ),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS2_BRANCH),
        "rationale": (
            "branch-REORDER positive control: lower case (i >= lr) tested first, "
            "upper case in the else; identical values, different control flow. "
            "Branch reorder (not a forward-append against the front-recursive "
            "zeros fold), so no f(a+b) lemma is needed (directive 3). Keeps all "
            "gold invariants/asserts; must verify."
        ),
    },
    {
        "id": "admiss-f2p-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    noutp = lr + rr",
            _ADMISS_INSERT,
        ),
        "rationale": (
            "admissibility: constructs a concrete F2P-shaped 2x2 0/1 grid and "
            "asserts is_grid(witness,2,2) holds -- the precondition predicate is "
            "satisfiable by a normal input (else PRECOND-TOO-STRONG / a vacuously "
            "False Requires). The gold loop body is unchanged, so it still "
            "verifies the postcondition. Must verify."
        ),
    },
    # ----- uniqueness / partial-domain rivals (must be rejected) ----------
    {
        "id": "weak-prepatch-ones-block",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PREPATCH_BRANCH),
        "refinement": (
            "this IS the gold bug: cright[-rr:,-rc:] = 1 (constant ones block) "
            "instead of = right. Its faithful real patch is the PRE-patch code, "
            "which fails FAIL_TO_PASS test_separable[compound_model6] and "
            "[compound_model9] (the nested CompoundModel m.Pix2Sky_TAN() & cm "
            "case): the lower-right block becomes all-True so the off-diagonal "
            "outputs spuriously appear dependent -- the exact reported defect. "
            "So a verifying rival here would be a true verify-but-not-resolve "
            "break."
        ),
        "rationale": (
            "rejected by postcondition P2: for a lower row, expected_row is "
            "zeros(lc) ++ right[i-lr]; the ones-block row zeros(lc) ++ ones(rc) "
            "differs whenever right[i-lr] has any 0 entry, so "
            "Assert(row == expected_row(...)) and the per-row Ensures fail. "
            "Rejection comes from the row-exact postcondition clause, not from "
            "shape (P1 still holds)."
        ),
    },
    {
        "id": "weak-firstrow-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FIRSTROW_BRANCH),
        "refinement": (
            "a partial-domain rival correct on all rows EXCEPT the first lower "
            "row (i == lr), which it sets to all-zeros instead of right[0]. Its "
            "faithful real patch would write 0 into cright's first post-left row "
            "while copying right elsewhere -- on the F2P nested models the first "
            "child-right output row carries a True on the diagonal, so a "
            "zeroed-out first lower row makes that output appear independent of "
            "ALL inputs (a wrong separability column), failing the F2P expected "
            "matrices. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by P2 on i == lr: expected_row(... lr) == zeros(lc) ++ "
            "right[0], but the rival produces zeros(lc) ++ zeros(rc); these "
            "differ whenever right[0] has a 1 (it does on every diagonal F2P "
            "child). The single-row divergence violates the universally-"
            "quantified per-row Ensures."
        ),
    },
    {
        "id": "weak-reverse-right-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REVERSE_BRANCH),
        "refinement": (
            "copies the right block but with its ROWS reversed "
            "(right[rr-1-(i-lr)]). Equal to gold only when right's row sequence "
            "is a palindrome. A faithful real patch that flipped the row order of "
            "the lower-right block would map child-right output k to row rr-1-k, "
            "transposing the True positions -- on the F2P models "
            "(rot & (sh1 & sh2)) the diagonal of the right child is permuted, "
            "yielding a separability matrix that does not match result6/result9. "
            "verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by P2: for a lower row expected_row is zeros(lc) ++ "
            "right[i-lr] but the rival places zeros(lc) ++ right[rr-1-(i-lr)]; "
            "for any non-palindromic right (e.g. an identity/diagonal block, "
            "rr>=2) these rows disagree, violating the per-row Ensures."
        ),
    },
    {
        "id": "weak-left-leak-block",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_LEFTPAD_BRANCH),
        "refinement": (
            "the dual of the gold bug: lower rows put left[i-lr] in the "
            "lower-LEFT block (should be zeros) then the actual right[i-lr]. "
            "A faithful real patch leaving cleft's lower rows non-zero would make "
            "the child-right outputs spuriously depend on the LEFT inputs -- a "
            "false off-diagonal block in the lower-left quadrant, so the F2P "
            "separability matrices (which require False there) fail. "
            "verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by P2: expected_row for a lower row is zeros(lc) ++ "
            "right[i-lr], but the rival produces left[i-lr] ++ right[i-lr]; the "
            "lower-left block differs from zeros(lc) whenever left[i-lr] has a 1 "
            "entry (true for any non-empty left with a dependence), violating the "
            "per-row Ensures. (P1 shape still holds: both halves are width lc/rc.)"
        ),
    },
]

# No @ContractOnly axioms and no A-reference deep models (meta.axioms == [];
# the block placement is modelled deeply and validated by axiom_check.py as a
# model-fidelity check, not an over-approximation of a library callee). The
# whole operation -- np.zeros + slice-copy + np.hstack -- is pure and captured
# directly by expected_row's PSeq concatenation, so there is no callee whose
# Ensures could be unsound, and no callee-input domain to contain.
AXIOM_TESTS = []
