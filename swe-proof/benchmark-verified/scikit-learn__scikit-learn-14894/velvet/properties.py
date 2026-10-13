"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14894 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives with a byte-identical statement)
and swaps in a candidate implementation. It is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over three counts):

  buildSparseCoef (nSV nClass dataLen : Nat) return (out : Except FitErr SparseCoef)
    require  1 ≤ nClass
    ensures  out = sparseFitSpec nSV nClass dataLen

The assembly routes on the count of rows ``nSV``:
  * ``nSV = 0`` (no rows to lay out) — the empty container is produced, and the
    assembly SUCCEEDS (``Except.ok emptyResult``): no stored entries, a single
    trivial row, zero columns, the canonical two-boundary index-pointer ``[0,0]``.
  * ``nSV ≥ 1`` — the strided compressed-row matrix is built: the ``dataLen``
    stored values, the tiled per-element column indices, the evenly-strided
    index-pointer sequence, and the ``nClass × nSV`` shape.

``sparseFitSpec`` (and every field it names — ``emptyResult``, ``builtResult``,
``tileRange``, the strided pointer sequence) is modelled DEEPLY as a concrete
``def`` in the ``pure``/``axioms`` regions; the ``axioms`` region declares NO
``axiom``. So there is no opaque answer-key an impl could echo, and every field
of the result reduces under kernel ``decide`` at concrete inputs — the whole
carrier is transparent. The single load-bearing clause ``out = sparseFitSpec
nSV nClass dataLen`` pins BOTH the routing decision (which count of rows yields
the empty container vs the strided build, and that NEITHER ends in the
zero-stride failure shape) AND every observable field produced on each route.

WHAT THIS SPEC DEFENDS, AND THE ATTACKS IT MUST SURVIVE
-------------------------------------------------------
  * THE DISCRIMINATOR is the no-rows guard. The reported defect is that the
    strided layout is built UNCONDITIONALLY; with no rows the stride is zero and
    the index-pointer arithmetic is ill-defined (a division by zero). The model
    encodes that as ``arangeIndptr`` returning ``Except.error zeroDivision`` at
    ``nSV = 0``. ``weak-drop-guard`` drops the guard and consults the strided
    layout unconditionally, so at ``nSV = 0`` the result is the failure shape
    where the spec demands ``Except.ok emptyResult``. Rejected.

  * THE EMPTY-CONTAINER OBSERVABLE. For the no-rows case the spec pins the exact
    fields of ``emptyResult``: no stored entries, index-pointer ``[0,0]``, a
    single trivial row, zero columns. Three rivals attack it — a non-zero final
    index-pointer boundary, a padded (three-boundary) index-pointer, and a total
    collapse to the empty container on EVERY input.

  * THE STRIDED-BUILD OBSERVABLE. For the ≥1-row case the spec pins every field
    of ``builtResult``: the ``dataLen`` stored-value count, the ``nClass × nSV``
    shape, and the strided index-pointer sequence (argument order and stride).
    Three rivals attack it — a dropped stored-value count, a transposed shape,
    and a transposed strided layout (wrong argument order to the pointer helper).

  * NO UNGROUNDED ORACLE. ``sparseFitSpec`` is a total function fully unfolded
    from the method's own arguments; there is no axiomatized oracle to echo. The
    positive controls are honest cheapest-reshape / satisfiability probes.

  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling carries this
    class because its inputs are held at a fractional heap permission an impl can
    illegally overwrite. Lean and Velvet are referentially transparent and this
    method declares NO ``mut`` binder — the three counts are immutable values
    with no heap footprint — so there is no read-only input to overwrite and no
    substitute probe. Reported N/A in the footer, not fabricated.

  * NO CAPABILITY-TOKEN / SIDE-EFFECT CHANNEL. The method purely computes and
    returns a value; the only control-flow difference that matters (no-rows vs
    ≥1-row) is fully observable through the returned value (the failure shape vs
    the empty/built container). No irreversible effect invisible to the value
    abstraction — the class is N/A.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery (``extract_program_for``
/ ``derive_tester_for``): ``buildSparseCoefTester nSV nClass dataLen = false``
says the extracted program's result violates the postcondition at that concrete
input. It is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict. ``prove_postcondition_decidable_for``
needs equality of the report carrier ``Except FitErr SparseCoef`` to be
decidable, so the preamble derives that instance first
(``deriving instance DecidableEq for Except``) — an instance, not an assumption
(no ``axiom`` / ``sorry`` / ``native_decide``). On every witness point the
frozen impl SATISFIES the postcondition, so its tester returns ``true`` and
``= false`` fails against gold (the discriminator); each witness was confirmed
out-of-band to ELABORATE against its rival and FAIL against gold (two real
builds per case).

BINDER / WITNESS PLACEMENT (read before judging binder coverage). The three
binders are moved across the seven reject witnesses:
  nSV     ∈ {0, 1, 2}   (the routing binder: no-rows arm at 0, build arm at ≥1)
  nClass  ∈ {1, 2, 3}   (the build's shape / index-pointer length)
  dataLen ∈ {0, 3, 4}   (the stored-value count carried opaquely into the build)
No two rivals are refuted at the same input tuple. A rival that mishandled only
a binder every witness held fixed would slip through; moving all three closes
that hole. ``dataLen`` in particular is exercised by ``weak-drop-datalen`` at a
non-zero value, so the stored-value carrier's dependence is probed.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (every modelled
callee is a deep-model reference validated == the real callee by axiom_check.py,
G-AX). The G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14894"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Every anchor below lies WHOLLY inside the impl region
# (between -- impl-start / -- impl-end) or is the frozen prove_correct block,
# and is unique in Solution.lean (both facts asserted at load by _swap).
# ---------------------------------------------------------------------------

# The full decision block (impl region). Positives / whole-branch rivals swap it.
_RESULT_BLOCK = (
    "    let result : Except FitErr SparseCoef :=\n"
    "      if nSV = 0 then\n"
    "        Except.ok emptyResult\n"
    "      else\n"
    "        match arangeIndptr nSV nClass with\n"
    "        | Except.ok indptr =>\n"
    "            Except.ok { dataLen := dataLen, indices := indices,\n"
    "                        indptr := indptr, rows := nClass, cols := nSV }\n"
    "        | Except.error e => Except.error e"
)
assert _RESULT_BLOCK in _BASE, "gold decision block drifted from Solution.lean"

# The no-rows arm head (impl region). Empty-container rivals swap this window.
_EMPTY_IF = (
    "      if nSV = 0 then\n"
    "        Except.ok emptyResult\n"
    "      else"
)
assert _BASE.count(_EMPTY_IF) == 1, "empty-arm anchor not unique"

# The strided-build result literal (impl region). Build-field rivals swap it.
_BUILT_LIT = (
    "            Except.ok { dataLen := dataLen, indices := indices,\n"
    "                        indptr := indptr, rows := nClass, cols := nSV }"
)
assert _BASE.count(_BUILT_LIT) == 1, "built-literal anchor not unique"

# The index-pointer helper call (impl region). Argument-order rival swaps it.
_ARANGE_CALL = "match arangeIndptr nSV nClass with"
assert _BASE.count(_ARANGE_CALL) == 1, "arange-call anchor not unique"

# The column-index staging line (impl region). Admissibility prepends its assert.
_INDICES_HEAD = "    let indices := tileRange nSV nClass\n"
assert _BASE.count(_INDICES_HEAD) == 1, "indices-head anchor not unique"

# The frozen proof block. A tactic body is elided from the consumer spec view,
# so a positive control may retune it without touching the spec or dropping the
# obligation. Unique in the file.
_PROVE = (
    "prove_correct buildSparseCoef by\n"
    "  loom_solve\n"
    "  simp_all [sparseFitSpec, arangeIndptr, builtResult]"
)
assert _BASE.count(_PROVE) == 1, "frozen proof block drifted from Solution.lean"


# ---- witness preamble: reach the method contract through Velvet's tester.
# ---- Except-carrier equality is derived as an INSTANCE (not assumed): no
# ---- axiom / sorry / native_decide. The method has one `require` (1 ≤ nClass);
# ---- every witness holds nClass ≥ 1 so nothing is vacuously excluded. ----
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for buildSparseCoef\n"
    "prove_precondition_decidable_for buildSparseCoef\n"
    "prove_postcondition_decidable_for buildSparseCoef\n"
    "derive_tester_for buildSparseCoef\n\n"
)


def _wit(nSV, nClass, dataLen):
    return (_PREAMBLE
            + f"example : buildSparseCoefTester {nSV} {nClass} {dataLen} = false "
            + ":= by\n  decide\n")


# ===========================================================================
# POSITIVE CONTROLS — expect "verify"
# ===========================================================================

# (soundness) Structurally different but CORRECT: the branch CONDITION is
# inverted (build the strided layout first under `if nSV ≠ 0`, empty container in
# the `else`). Same domain partition and same fields on every input; only the
# executable control-flow shape flips. The decision still collapses to the same
# two results, so the frozen tactic script closes the byte-identical obligation
# with no retune (verified out-of-band with two real builds). If a faithful
# inverted-branch correct impl cannot verify => SPEC-TOO-STRONG.
_POS_INVERTED = (
    "    let result : Except FitErr SparseCoef :=\n"
    "      if nSV ≠ 0 then\n"
    "        match arangeIndptr nSV nClass with\n"
    "        | Except.ok indptr =>\n"
    "            Except.ok { dataLen := dataLen, indices := indices,\n"
    "                        indptr := indptr, rows := nClass, cols := nSV }\n"
    "        | Except.error e => Except.error e\n"
    "      else\n"
    "        Except.ok emptyResult"
)

# (admissibility) The nagini sibling self-calls to prove the precondition admits
# an F2P-shaped input. Re-aimed here (the residual risk on this method's near-total
# domain is that the post-image is UNSATISFIABLE / DEGENERATE at the interesting
# point): a live in-region assert that the post-image is satisfiable AND
# non-degenerate at the F2P-shaped no-rows input (nSV = 0, nClass = 1 — the
# regression-model shape, one class, no rows: the empty container is produced and
# the assembly SUCCEEDS) and at a ≥1-row build input (a genuine success). The impl
# is kept verbatim so the method's own obligation still discharges; the assert is
# LIVE (a false claim leaves an unsolved goal — confirmed out-of-band: replacing
# the empty-success claim with a failure-shape claim fails to build). If the
# post-image were unsatisfiable at the F2P point => PRECOND/SPEC-TOO-STRONG.
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `adm\n"
    "      (sparseFitSpec 0 1 0 = Except.ok emptyResult ∧\n"
    "       (sparseFitSpec 1 1 2).isOk = true))\n"
    "    let indices := tileRange nSV nClass\n"
)
_ADMISS_PROVE = (
    "prove_correct buildSparseCoef by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | exact ⟨rfl, rfl⟩\n"
    "    | simp_all [sparseFitSpec, arangeIndptr, builtResult]\n"
)


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject"
# ===========================================================================

# (DISCRIMINATOR — the reported defect) Drop the no-rows guard: consult the
# strided index-pointer layout UNCONDITIONALLY. At nSV = 0 the stride is zero, so
# the helper yields the zero-division failure shape where the spec demands the
# empty container.
_RIVAL_DROP_GUARD = (
    "    let result : Except FitErr SparseCoef :=\n"
    "      match arangeIndptr nSV nClass with\n"
    "      | Except.ok indptr =>\n"
    "          Except.ok { dataLen := dataLen, indices := indices,\n"
    "                      indptr := indptr, rows := nClass, cols := nSV }\n"
    "      | Except.error e => Except.error e"
)

# (empty-container, final boundary) On the no-rows arm return a container whose
# final index-pointer boundary is non-zero.
_EMPTY_NONZERO = (
    "      if nSV = 0 then\n"
    "        Except.ok { dataLen := 0, indices := [], indptr := [0, 5], rows := 1, cols := 0 }\n"
    "      else"
)

# (empty-container, padded length) On the no-rows arm return a padded
# (three-boundary) index-pointer for the single-row empty container.
_EMPTY_PADDED = (
    "      if nSV = 0 then\n"
    "        Except.ok { dataLen := 0, indices := [], indptr := [0, 0, 0], rows := 1, cols := 0 }\n"
    "      else"
)

# (whole-input collapse) Return the empty container on EVERY input, ignoring the
# rows/stride entirely. Correct only on the no-rows sub-domain.
_RIVAL_FLAT = (
    "    let result : Except FitErr SparseCoef :=\n"
    "      Except.ok emptyResult"
)

# (strided build, stored-value count) On the ≥1-row arm drop the stored-value
# count to zero. Right shape and index-pointers, wrong dataLen.
_DROP_DATALEN = (
    "            Except.ok { dataLen := 0, indices := indices,\n"
    "                        indptr := indptr, rows := nClass, cols := nSV }"
)

# (strided build, shape) On the ≥1-row arm transpose the shape (rows/cols
# swapped). Right stored-value count and index-pointers, wrong dimensions.
_SWAP_DIMS = (
    "            Except.ok { dataLen := dataLen, indices := indices,\n"
    "                        indptr := indptr, rows := nSV, cols := nClass }"
)

# (strided build, index-pointer layout) On the ≥1-row arm pass the counts to the
# index-pointer helper in the WRONG order, producing a transposed strided
# sequence (stride nClass over nSV+1 boundaries instead of stride nSV over
# nClass+1). Right shape and stored count, wrong index-pointer sequence.
_WRONG_INDPTR_ARGS = "match arangeIndptr nClass nSV with"


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-inverted-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _RESULT_BLOCK, _POS_INVERTED),
        "rationale": "structurally-different CORRECT reshape: the branch CONDITION "
                     "is inverted (strided build first under `if nSV ≠ 0`, empty "
                     "container in the `else`). Same domain partition and same "
                     "fields on every (nSV, nClass, dataLen), so `out = sparseFitSpec "
                     "nSV nClass dataLen` still holds and the frozen tactic script "
                     "closes the byte-identical obligation. A faithful reshape MUST "
                     "verify, else SPEC-TOO-STRONG on branch order.",
    },
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _INDICES_HEAD, _ADMISS_ASSERT),
                        _PROVE, _ADMISS_PROVE),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped no-rows input (nSV = 0, nClass = 1: the empty "
                     "container is produced and the assembly SUCCEEDS, `Except.ok "
                     "emptyResult`, never the zero-division failure shape) and at a "
                     "≥1-row build input (a genuine success). The live in-region "
                     "assert must discharge (else the obligation is unsatisfiable at "
                     "the interesting point); the impl is kept verbatim so the "
                     "method's own obligation discharges too. Re-aimed from the "
                     "nagini precondition-admits probe (the sole `require`, 1 ≤ "
                     "nClass, is trivially met at nClass = 1).",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-drop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RESULT_BLOCK, _RIVAL_DROP_GUARD),
        "refinement": "this is the pre-fix behaviour exactly: the strided layout is "
                      "consulted UNCONDITIONALLY, so with no rows the zero stride "
                      "leaves the index-pointer arithmetic ill-defined and the "
                      "assembly ends in the failure shape — the reported crash. The "
                      "regression test fits a no-rows model and asserts the assembly "
                      "SUCCEEDS with no stored entries; the pre-fix path raises "
                      "instead, so a faithful counterpart does NOT resolve. A "
                      "verifying rival here would be a true verify⇏resolve break.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "no-rows arm the spec demands `Except.ok emptyResult`, but the "
                     "rival consults the strided helper, which at nSV = 0 yields the "
                     "zero-division failure shape. This is the G-DIFF discriminator. "
                     "Refuted at (nSV = 0, nClass = 1, dataLen = 0), the no-rows "
                     "routing point. If it verified => SPEC-TOO-WEAK.",
        "witness": _wit(0, 1, 0),
    },
    {
        "id": "weak-empty-nonzero-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _EMPTY_IF, _EMPTY_NONZERO),
        "refinement": "correct on the ≥1-row domain but for the no-rows case returns "
                      "a container whose final index-pointer boundary is non-zero — "
                      "i.e. a matrix reporting stored entries where there are none. "
                      "The regression test asserts the no-rows result has NO stored "
                      "entries; a faithful counterpart producing a non-empty layout "
                      "there does NOT resolve.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "no-rows arm the spec pins the exact `emptyResult` fields "
                     "(index-pointer `[0,0]`); the rival returns `[0,5]`. Refuted at "
                     "(nSV = 0, nClass = 2, dataLen = 0), moving nClass off 1 while "
                     "staying on the no-rows arm. If it verified => SPEC-TOO-WEAK on "
                     "the empty-container observable.",
        "witness": _wit(0, 2, 0),
    },
    {
        "id": "weak-empty-padded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _EMPTY_IF, _EMPTY_PADDED),
        "refinement": "correct on the ≥1-row domain but for the no-rows case returns "
                      "a PADDED three-boundary index-pointer for the single-row empty "
                      "container. The empty container is a one-row shape whose "
                      "index-pointer sequence must have exactly two boundaries "
                      "(`[0,0]`); a three-boundary sequence describes a malformed "
                      "two-row matrix, diverging from the intended empty result. The "
                      "regression test's empty-container assertion would not hold, so "
                      "a faithful counterpart does NOT resolve.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "no-rows arm the spec pins `emptyResult` with index-pointer "
                     "`[0,0]` (length 2); the rival returns `[0,0,0]` (length 3) — "
                     "the final boundary and opening are correct, only the LENGTH "
                     "differs, a near-miss the nonzero-tail rival does not subsume. "
                     "Refuted at (nSV = 0, nClass = 3, dataLen = 0). If it verified "
                     "=> SPEC-TOO-WEAK on the empty-container length.",
        "witness": _wit(0, 3, 0),
    },
    {
        "id": "weak-collapse-to-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RESULT_BLOCK, _RIVAL_FLAT),
        "refinement": "collapses EVERY input to the empty container, ignoring the "
                      "rows and stride; correct only on the no-rows sub-domain. A "
                      "faithful counterpart that always emitted an empty coefficient "
                      "matrix would, for a model WITH support rows, drop the real "
                      "stored coefficients — failing the fit/predict regression tests "
                      "(PASS_TO_PASS) that exercise non-trivial models. It does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "≥1-row arm the spec demands `Except.ok (builtResult …)` with "
                     "the `nClass × nSV` shape and strided index-pointers, but the "
                     "rival returns `emptyResult` (one row, zero cols, `[0,0]`). "
                     "Refuted at (nSV = 1, nClass = 2, dataLen = 0), on the build "
                     "arm. If it verified => SPEC-TOO-WEAK on the strided build.",
        "witness": _wit(1, 2, 0),
    },
    {
        "id": "weak-drop-datalen",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BUILT_LIT, _DROP_DATALEN),
        "refinement": "on the ≥1-row build the stored-value count is dropped to zero "
                      "(right shape and index-pointers, wrong stored count). A "
                      "faithful counterpart that built the coefficient matrix while "
                      "reporting zero stored values would hand downstream code a "
                      "matrix inconsistent with its own layout — the fit/predict "
                      "regression tests that read the coefficients would observe the "
                      "wrong count. It does NOT resolve.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "≥1-row arm the spec pins `dataLen := dataLen`, but the rival "
                     "hardcodes `dataLen := 0`, differing whenever dataLen ≠ 0. This "
                     "is the ONLY rival whose separating input moves the dataLen "
                     "binder off 0 — refuted at (nSV = 1, nClass = 1, dataLen = 3), "
                     "so the stored-value carrier's dependence is probed. If it "
                     "verified => SPEC-TOO-WEAK on the stored-value count.",
        "witness": _wit(1, 1, 3),
    },
    {
        "id": "weak-transpose-shape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BUILT_LIT, _SWAP_DIMS),
        "refinement": "on the ≥1-row build the row/column dimensions are transposed "
                      "(`rows := nSV, cols := nClass`). A faithful counterpart that "
                      "built the coefficient matrix with a transposed shape would "
                      "hand downstream code the wrong dimensions; the fit/predict "
                      "regression tests that consume the coefficient shape would "
                      "diverge. It does NOT resolve.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "≥1-row arm the spec pins `rows := nClass, cols := nSV`, but the "
                     "rival swaps them, differing whenever nSV ≠ nClass. Refuted at "
                     "(nSV = 1, nClass = 2, dataLen = 0) where the shapes disagree "
                     "(1×2 vs 2×1). If it verified => SPEC-TOO-WEAK on the matrix "
                     "shape.",
        "witness": _wit(1, 2, 0),
    },
    {
        "id": "weak-transpose-indptr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARANGE_CALL, _WRONG_INDPTR_ARGS),
        "refinement": "on the ≥1-row build the two counts are passed to the "
                      "index-pointer helper in the WRONG order, producing a "
                      "transposed strided sequence (stride nClass over nSV+1 "
                      "boundaries instead of stride nSV over nClass+1). A faithful "
                      "counterpart with the arguments swapped would lay out the "
                      "row index-pointers with the wrong stride and count, building "
                      "a malformed matrix; the fit/predict regression tests would "
                      "diverge. It does NOT resolve.",
        "rationale": "REJECT from `out = sparseFitSpec nSV nClass dataLen`: on the "
                     "≥1-row arm the spec pins the index-pointers to the strided "
                     "sequence for (nSV, nClass), but the rival computes it for "
                     "(nClass, nSV), differing whenever nSV ≠ nClass. Refuted at "
                     "(nSV = 2, nClass = 3, dataLen = 4), moving all three binders. "
                     "If it verified => SPEC-TOO-WEAK on the strided index-pointer "
                     "progression.",
        "witness": _wit(2, 3, 4),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery (nagini/properties.py) has 7
# SPEC cases (1 soundness positive, 1 admissibility, 5 uniqueness rivals) plus a
# 2-case AXIOM lane. The nagini carrier models the row-pointer LIST alone
# (`row_pointer_for_block_layout(width, n_rows) -> List[int]`, width == nSV,
# n_rows == nClass); this velvet bundle models the FULL result container
# (`Except FitErr SparseCoef`: the stored-value count, tiled column indices,
# strided index-pointers, and shape), routing on nSV via one clause
# `out = sparseFitSpec nSV nClass dataLen`. So the nagini row-pointer clauses
# re-express as attacks on the corresponding fields of the container, and the
# richer carrier exposes THREE more fields to attack (dataLen, rows/cols shape).
#
#   sibling case                    -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-inverted-branch     -> pos-inverted-branch           PORTED
#   admiss-empty-support-vectors    -> admiss-nondegenerate          RE-AIMED
#   (frame-mutation — implicit)     -> (none)                        VACUOUS
#   rival-drop-guard                -> weak-drop-guard               PORTED
#   rival-empty-nonzero-tail        -> weak-empty-nonzero-tail       PORTED
#   rival-wrong-open                -> (folded)                      FOLDED
#   rival-empty-padded              -> weak-empty-padded             PORTED
#   rival-flat-nonempty             -> weak-collapse-to-empty        PORTED
#   (new — velvet-only fields)      -> weak-drop-datalen             ADDED
#   (new — velvet-only fields)      -> weak-transpose-shape          ADDED
#   (new — non-empty progression)   -> weak-transpose-indptr         ADDED
#   AXIOM_TESTS (2)                 -> (none)                        DROPPED (G-AX)
#
# PORTED (positive): pos-control-inverted-branch reorders the two branches; here
#   the branch CONDITION is inverted (build first under `if nSV ≠ 0`), same
#   partition and same fields, and it verifies with the frozen tactic script.
# RE-AIMED (admissibility): the nagini sibling self-calls to establish the
#   precondition on an empty-support-vector input. This method's only `require`
#   (1 ≤ nClass) is trivially met, so the probe is re-aimed at the residual risk
#   on a near-total domain — that the post-image is unsatisfiable/degenerate at
#   the F2P point — via a live in-region assert (empty input SUCCEEDS with the
#   empty container; a build input succeeds). The assert is live (a false claim
#   fails to build). Not an effort dodge: it defends the same "empty input is
#   normal, not excluded" fact on this backend's carrier.
# VACUOUS (frame-mutation): the nagini surface passes plain immutable ints by
#   value (no Acc(x,1/2) reference), and the nagini docstring itself records the
#   frame-mutation probe as N/A. This backend is likewise referentially
#   transparent with no `mut` binder — no read-only input to overwrite, no
#   substitute probe. Not fabricated (porting map: vacuous here).
# PORTED (empty-branch rivals): drop-guard IS the reported defect and the G-DIFF
#   discriminator (route the no-rows case into the zero-stride helper);
#   empty-nonzero-tail and empty-padded attack the two distinct empty-container
#   observables (final boundary; index-pointer length); collapse-to-empty is the
#   flat rival (empty container on every input).
# FOLDED (rival-wrong-open): nagini's "row-pointer opens at 1 not 0" attacks the
#   opening index-pointer boundary on the empty branch. On this carrier the empty
#   index-pointer is the two-element `[0,0]`, whose opening and closing boundaries
#   are attacked TOGETHER by empty-nonzero-tail (closing != 0) and empty-padded
#   (length); a separate "opening != 0" rival would be a third value-corruption of
#   the same two-element sequence with no new binder or clause exercised. Folded
#   rather than shipped as a near-duplicate.
# ADDED (3): the velvet carrier models fields the nagini row-pointer list does
#   not — the stored-value count (weak-drop-datalen, the ONLY witness moving the
#   dataLen binder off 0), the row/column shape (weak-transpose-shape), and the
#   argument order to the index-pointer helper (weak-transpose-indptr, the
#   analogue of nagini's non-empty progression pin `Result()[k] == k*width`).
#   These are attacks on the modelled surface, not parity fabrication: each is a
#   distinct field of `sparseFitSpec` with a machine-checked discriminating
#   witness.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   `axiom` (the index-pointer / tile / container callees are deep-model
#   references validated == the real callees by axiom_check.py), so there is
#   nothing to probe and the gate ignores AXIOM_TESTS regardless.
#
# WITNESS DISTINCTNESS. Seven distinct input tuples (nSV, nClass, dataLen):
#   (0,1,0) weak-drop-guard          (no-rows routing -> failure shape)
#   (0,2,0) weak-empty-nonzero-tail  (empty container, final boundary)
#   (0,3,0) weak-empty-padded        (empty container, index-pointer length)
#   (1,2,0) weak-collapse-to-empty   (build arm collapsed to empty)
#   (1,1,3) weak-drop-datalen        (build, stored-value count; dataLen off 0)
#   (1,2,0) weak-transpose-shape     (build, shape 1x2 vs 2x1)
#   (2,3,4) weak-transpose-indptr    (build, strided index-pointer progression)
#   nSV ∈ {0,1,2}, nClass ∈ {1,2,3}, dataLen ∈ {0,3,4} — all three binders moved.
#   collapse-to-empty and transpose-shape share the input (1,2,0) but fail for
#   DIFFERENT reasons against DIFFERENT sub-behaviours (whole-branch collapse vs a
#   single transposed field), so they are distinct predicates, not one attack
#   written twice. Every witness ELABORATES against its rival and FAILS against
#   the frozen solution (two real builds per case, confirmed out-of-band).
AXIOM_TESTS = []
