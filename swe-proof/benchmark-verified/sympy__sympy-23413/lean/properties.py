"""properties.py — G-PBT falsification battery for sympy__sympy-23413 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_hermiteNormalForm``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts the routine over a ``List[int]`` per-row pivot-flag carrier with
fractional-permission (``Acc(.,1/2)``) framing and a family of GROUNDED
``@Pure`` folds (``pivot_count`` / ``valid_flags``) that compute the marker from
the flags. This Lean bundle models the SAME purely-functional core at a
different abstraction: the matrix is carried as its list-of-integer-rows carrier
(``Mat := List (List Int)``), the UNCHANGED per-row reduction and the final
column slice are two ``opaque`` callees (``step``, ``sliceCols``), and the fixed
control flow (which rows are processed, and the early stop once the pivot
pointer reaches the leftmost column) is spelled out structurally as a
front-recursive fold (``rowsDesc`` + ``hnfFold``). The nagini cases carry over
as attacks on that control flow; the mapping of each nagini case to its Lean
counterpart (or its principled omission) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior, one clause). The postcondition pins
``result`` to a single grounded computation over the input matrix and its shape:

  problem_spec_hermiteNormalForm (A0 : Mat) (m n : Nat) (result : Mat) : Prop :=
    let p := hnfFold (rowsDesc m) A0 n
    result = sliceCols p.1 p.2

That computation has these observable decisions, each selected by the input:

  * the ROW SET — every row index is processed, bottom-to-top
    (``rowsDesc m = (List.range m).reverse = [m-1, …, 0]``); the pre-fix routine
    processed only the bottom ``min(m, n)`` rows, so a pivot in a topmost row of
    a tall matrix (``m > n``) was never placed and its column was dropped — the
    reported "HNF removing rows" bug;
  * the EARLY STOP — the fold stops as soon as the pivot pointer reaches the
    leftmost column (``k = 0``): every column then holds a pivot and no further
    row can add one. Dropping this lets the pointer run past 0 into subsequent
    rows, threading a different (matrix, pointer) pair into the remaining
    reductions and the final slice;
  * the RESULT — the block of columns from the final pointer onward,
    ``sliceCols p.1 p.2`` where ``p`` is the fold's terminal (matrix, pointer).

The BEHAVIOURAL DISCRIMINATOR (the fix) is the ROW SET together with the EARLY
STOP: pre-fix ``rows = min(m, n)`` with ``for i in range(m-1, m-1-rows, -1)`` and
no break → post-fix ``for i in range(m-1, -1, -1)`` with ``if k == 0: break``.
The two partial-domain rivals below ARE that pre-fix behavior; the no-clamp
rival is the missing break.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the pivot-flag
    list at a half-permission (``Acc(list_pred(found), 1/2)``) in both the pre-
    and the post-condition and makes a write into it (``found[i] = c``) fail for
    INSUFFICIENT PERMISSION. Lean is referentially transparent: ``A0`` is an
    immutable value with no heap footprint, no aliasing, and no fractional
    permission, so there is no permission system and no rejection-by-store. The
    read-only discipline the nagini rival probes is instead pinned by the spec
    being an exact equality to a total function of the inputs — the impl may not
    invent an output component — which the uniqueness rivals below already
    attack. No substitute is fabricated (porting map: this class is vacuous on a
    referentially transparent carrier). See ``assessment``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS (and N/A in nagini too). The postcondition
    is GROUNDED: ``result`` is pinned equal to a term built only from the input
    (``sliceCols (hnfFold (rowsDesc m) A0 n).1 …``). ``step`` and ``sliceCols``
    are ``opaque``, but there is no axiomatized ANSWER KEY to echo — the impl
    must still fold the reduction over the right row set with the right early
    stop and thread the resulting (matrix, pointer) pair into the same slice. A
    rival that folds over the wrong row set denotes a different function and is
    refutable (below). In its place the battery carries honest positive controls
    (the reference fold restated, an equivalent branch reshape).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE (not a vacuous class). The nagini
    sibling carries no ``diverge-*`` case, and an earlier form of this note
    claimed the class was vacuous here because "a diverging implementation
    cannot be written at all". AUDIT CORRECTION: that is false, and the
    correction is measured. The frozen ``implementation_*`` is indeed a total
    ``def`` (a bounded ``for`` over ``rowsDesc m``), but a variant is not
    confined to that shape — ``partial def`` is admissible under
    ``variant_scope`` (it is not in the banned-token set), so a rival whose
    row loop carries NO decreasing measure IS writable on this carrier:

        partial def hnfLoop : List Nat → Mat → Nat → Mat × Nat
          | [], A, k => (A, k)
          | i :: rest, A, k => hnfLoop (i :: rest) (step A i k).1 (step A i k).2

    Built for real, that rival is REJECTED (exit 1) — under its own ``rfl`` and
    under a ``simp`` that unfolds it, leaving the honest unsolved goal
    ``sliceCols (hnfLoop …).1 … = sliceCols (hnfFold …).1 …``: a ``partial def``
    is compiled opaquely, so nothing about it is provable and the fold equality
    cannot be closed. So the class is EXPRESSIBLE and the rival direction is
    real. What could not be landed is the discriminating WITNESS: the refutation
    has to be stated over vocabulary gold and the rival SHARE (a witness naming
    ``hnfLoop`` is a variant-only name and is barred), which forces a hypothesis
    of the form ``implementation_hermiteNormalForm A0 1 1 ≠ <the correct
    value>``. That hypothesis is CONTRADICTORY on the frozen solution, so the
    witness ELABORATES against gold too (measured: exit 0 on both sides) and the
    gate reads it as ``witness-vacuous``. Recorded as a KNOWN HOLE rather than a
    vacuous class: the rival is shippable in principle and only the witness
    requirement blocks it, so the battery is not complete on this axis. It is
    not listed as a spec hole — the rival does NOT verify, so the spec is not
    weak here; the gap is in the attestation, not the obligation.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: processing only the bottom ``min(m, n)`` rows,
    skipping the bottom row, and dropping the early-stop clamp.

CONDITIONING ON THE CARRIER (why the reject witnesses take hypotheses). ``step``
and ``sliceCols`` are ``opaque`` — ``sliceCols A0 0`` has no value ``decide`` can
compute, and neither does ``step A0 i k``. So each reject witness states its
refutation at a point DESCRIBED BY HYPOTHESIS: it assumes only that the two
(matrix, pointer) pairs the rival and gold thread into the final slice actually
DIFFER on some quantified matrix ``A0`` (e.g. ``sliceCols (step A0 0 0).1 (step
A0 0 0).2 ≠ sliceCols A0 0``), then the spec and the rival's result reduce
concretely and the divergence is exactly that hypothesised inequality. This is a
stronger statement than any single literal matrix could make: it says that
WHEREVER the two reductions differ, the rival's answer differs from the spec's —
precisely the sub-domain where the rival is wrong. Each witness's hypotheses
were checked to be jointly SATISFIABLE (the gate derives ``False`` from the
binders alone and must fail): the ``partial-domain-min-rows`` witness carries two
hypotheses, but they are about DIFFERENT terms (one an inequality of slices, one
that a pointer is non-zero) so no ``False`` is derivable; the other two carry a
single inequality hypothesis each.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``forIn``-bridge proof is tuned to the
frozen do-block's syntactic form — so a rejection alone attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating
the spec predicate directly at one concrete (conditioned) input and refuting it.
Each was checked with two real ``lake env lean`` builds to ELABORATE against its
rival and to FAIL against the frozen solution, so it discriminates rather than
asserting a tautology.

AUDIT NOTE on what "FAILS against the frozen solution" has to mean. Two builds
(rival 0, gold 1) are NECESSARY but not sufficient: gold's exit code is evidence
only if it TRACKS THE CLAIM. The bar met here, per witness, is that gold's
``simp`` actually REDUCES the spec equation at the witness's point, so the
refutation is left facing the goal ``False`` (``simp`` proved the equation for
gold) rather than an unreduced ``match … ForInStep …`` term-shape mismatch. Each
witness was re-checked under the FORGERY test: a snippet differing ONLY in
flipping the claim (asserting gold is CORRECT at that point) must NOT fail on
gold the same way. Measured for all three:

  * ``uniqueness-no-early-stop`` — gold's error is ``term h has type ¬sliceCols
    (step A0 0 0).1 … = sliceCols A0 0 but is expected to have type False``; the
    flipped claim ELABORATES against gold (exit 0). Claim-sensitive.
  * ``partial-domain-skip-bottom-row`` — gold's error is the same ``… expected to
    have type False`` shape; the flipped claim ELABORATES against gold (exit 0).
    Claim-sensitive.
  * ``partial-domain-min-rows`` — this one FAILED the forgery test in its first
    form and was REPAIRED; see the case's own note. Under the repaired tactic the
    flipped claim elaborates on gold (exit 0) and fails on the rival (exit 1),
    i.e. both exit codes swap with the claim.

Additionally, each witness was built against BOTH of this battery's VERIFYING
positives. All three fail there too, which is the right outcome and the reason
the ``False``-goal shape matters: a witness must fail against ANY impl that
satisfies the spec, not merely against the frozen syntactic form.

BINDER / POINT SPREAD. The spec input binders are ``A0`` (the matrix), ``m`` (row
count), and ``n`` (column count / initial pointer). The reject witnesses move the
SHAPE binders across genuinely distinct points rather than fixing one convenient
point: ``(m,n) = (1,0)`` (a tall/degenerate one-row zero-column shape, the
no-clamp case where the pointer starts at the leftmost column), ``(m,n) = (2,1)``
(the ``m > n`` tall shape where the pre-fix ``min(m,n)`` row cap drops the topmost
row — the exact bug family), and ``(m,n) = (1,1)`` (a single square row whose
bottom row is skipped). Across the three witnesses ``m`` takes {1, 2}, ``n`` takes
{0, 1}, and ``A0`` is quantified (the refutation holds on the whole sub-domain
where the reductions differ, not at one matrix literal). No two rivals share a
refutation point; the three reject witnesses probe three distinct shapes, each
exercising a different facet of the row-set / early-stop decision.

AXIOM lane: EMPTY. The bundle declares two ``opaque`` callees (the UNCHANGED
per-row reduction and the column slice) carried as signatures only, with NO
``_prop`` axiom consumed and NO deep-model reference (``meta.json`` ``axioms ==
[]``, ``deep_model_references == []``); they appear identically in the spec and
the impl and cancel in the differential, so there is no axiom-soundness
obligation to probe here. That lane belongs to G-AX; the nagini ``AXIOM_TESTS``
(already empty) are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23413"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole impl def (inside the impl region). Editing it as one unit keeps the
# swap strictly inside `-- impl-start`/`-- impl-end` so same_spec stays
# byte-identical and the theorem statement is untouched.
_IMPL = (
    "def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat := Id.run do\n"
    "  let mut A := A0\n"
    "  let mut k := n\n"
    "  for i in rowsDesc m do\n"
    "    if k = 0 then\n"
    "      break\n"
    "    let p := step A i k\n"
    "    A := p.1\n"
    "    k := p.2\n"
    "  return sliceCols A k"
)
assert _BASE.count(_IMPL) == 1, "impl body anchor drifted"

# The frozen proof-region body (inside the proof region). The two functional
# positive controls restate the reference fold, whose obligation closes by a
# bare `rfl` (definitional), so they carry their OWN short proof body in place of
# the frozen forIn-bridge script — the theorem STATEMENT (elided from the swap)
# is unchanged, only the tactic body differs, which the lean scope check permits.
_PROOF_HEAD = (
    "theorem correct_hermiteNormalForm :\n"
    "    ∀ (A0 : Mat) (m n : Nat),\n"
    "      m = A0.length → (∀ row ∈ A0, row.length = n) →\n"
    "      problem_spec_hermiteNormalForm A0 m n\n"
    "        (implementation_hermiteNormalForm A0 m n) := by\n"
    "  intro A0 m n hm hrows\n"
)
assert _BASE.count(_PROOF_HEAD) == 1, "proof-head anchor drifted"

# The admissibility positive keeps the FROZEN proof body verbatim and only
# splices a `have` after the `intro` line; anchor on the intro + first `have`.
_INTRO_HAVE = "  intro A0 m n hm hrows\n  have key"
assert _BASE.count(_INTRO_HAVE) == 1, "intro/have anchor drifted"


def _with_impl_and_proof(new_impl: str, new_proof_body: str) -> str:
    """Swap the impl def AND replace the proof body with a fresh short script.

    The proof STATEMENT (`_PROOF_HEAD`) is preserved byte-identical; only the
    tactic body after it changes. Used by the functional positive controls whose
    obligation closes by `rfl`.
    """
    src = _swap(_BASE, _IMPL, new_impl)
    # everything from _PROOF_HEAD to `-- proof-end` is the frozen body; replace
    # the body (the frozen forIn-bridge) with `new_proof_body`, keeping the head.
    start = src.index(_PROOF_HEAD)
    end = src.index("-- proof-end")
    return src[:start] + _PROOF_HEAD + new_proof_body + src[end:]


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_hermiteNormalForm` statement byte-identical; each was
    # confirmed to close with a real build.
    # =====================================================================
    {
        "id": "pos-restate-fold",
        "kind": "soundness",
        "expect": "verify",
        # Drop the `Id.run do` / `let mut` / `for` scaffold and restate the
        # reference reduction directly: fold over every row bottom-to-top with the
        # early stop (`hnfFold (rowsDesc m) A0 n`) and slice the terminal pointer.
        # This IS the modeled computation performed op-for-op (SPEC_GUIDE §0.8: not
        # an ungrounded echo — `step`/`sliceCols` are still invoked identically and
        # the fold does the real row-set + early-stop work), so `result =
        # sliceCols p.1 p.2` holds definitionally and the obligation closes by a
        # bare `rfl` (verified with a real build).
        "module": _with_impl_and_proof(
            "def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat :=\n"
            "  let p := hnfFold (rowsDesc m) A0 n\n"
            "  sliceCols p.1 p.2",
            "  rfl\n",
        ),
        "rationale": "correct reshape of the mutable-do reduction into a direct "
                     "restatement of the reference fold; it computes the same Mat on "
                     "every input (same row set, same early stop, same slice), so it "
                     "must satisfy the sole clause `result = sliceCols (hnfFold "
                     "(rowsDesc m) A0 n).1 …` — else SPEC-TOO-STRONG. Carries the "
                     "nagini 'honest positive control' argument onto this carrier: "
                     "performing the modeled work directly (no do-block) still "
                     "verifies, so the spec is not over-fit to the imperative loop "
                     "shape. Proof: the obligation closes by a bare `rfl` because both "
                     "sides are definitionally `sliceCols (hnfFold …).1 (hnfFold …).2`.",
    },
    {
        "id": "pos-guard-explicit-else",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape that STAYS imperative: the loop
        # body's early `break`-then-fall-through is rewritten as an explicit
        # `if k = 0 then break else <reduce>`. Semantically identical to the gold
        # loop on every input (the reduce step only ran when `k ≠ 0` anyway), so the
        # frozen forIn-bridge proof still closes verbatim (verified with a real
        # build; the desugared body matches `hnfBodyF`'s `if`/`else`).
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat := Id.run do\n"
            "  let mut A := A0\n"
            "  let mut k := n\n"
            "  for i in rowsDesc m do\n"
            "    if k = 0 then\n"
            "      break\n"
            "    else\n"
            "      let p := step A i k\n"
            "      A := p.1\n"
            "      k := p.2\n"
            "  return sliceCols A k"),
        "rationale": "structurally different CORRECT reshape (the early `break` "
                     "followed by a fall-through reduce is rewritten as an explicit "
                     "`if … then break else …`) — semantically identical to the gold "
                     "loop, since the reduce step only executed on the `k ≠ 0` arm "
                     "already. A faithful branch reshape MUST verify, else "
                     "SPEC-TOO-STRONG. Proof: the frozen forIn-bridge script closes "
                     "unchanged (the desugared body is the same `if`/`else` as "
                     "`hnfBodyF`); no new axiom/lemma, statement byte-identical. "
                     "Ports nagini's control-flow-reorder positive control "
                     "(`pos-control-hoisted-local`) to the single modeled function.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation's
    # PRECONDITION is establishable at the normal, F2P-shaped input rather than
    # only in the abstract. Unlike the nagini/velvet frame lane, this Lean
    # theorem DOES carry a precondition hypothesis (`m = A0.length` and every row
    # of `A0` has length `n`), so the nagini precondition-admission probe has a
    # real binder to attack here. Ports nagini's `admissibility-self-call`.
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        # Splice a `have` inside the FROZEN tactic body establishing that the
        # precondition (row count = length, every row width = n) IS satisfiable at a
        # concrete F2P-shaped input — the reporter's 3×2 matrix [[1,12],[0,8],[0,5]]
        # (m=3, n=2), the tall shape whose topmost pivot the fix recovers — then
        # close the frozen obligation verbatim. Nothing is assumed at top level: no
        # new declaration, statement byte-identical, the ground instance is a local
        # `have`. If the precondition could not be established at exactly the input
        # the F2P exercises => PRECOND-TOO-STRONG.
        "module": _swap(
            _BASE, _INTRO_HAVE,
            "  intro A0 m n hm hrows\n"
            "  have _adm : (3 : Nat) = ([[1, 12], [0, 8], [0, 5]] : Mat).length ∧\n"
            "      (∀ row ∈ ([[1, 12], [0, 8], [0, 5]] : Mat), row.length = 2) := by\n"
            "    refine ⟨rfl, ?_⟩\n"
            "    decide\n"
            "  have key"),
        "rationale": "the precondition of `correct_hermiteNormalForm` (`m = "
                     "A0.length` and every row of `A0` has width `n`) is discharged at "
                     "the ground F2P-shaped input — the reporter's tall 3×2 matrix "
                     "[[1,12],[0,8],[0,5]] (m=3, n=2), exactly the `m > n` shape whose "
                     "topmost pivot column the fix recovers — then the frozen "
                     "obligation is closed verbatim. Verifies (else the precondition "
                     "is unsatisfiable at the very input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, the "
                     "ground instance is a local `have` inside the existing tactic "
                     "body. Ports nagini's `admissibility-self-call`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness (conditioned on the opaque carrier) pinning the
    # violation on a quantified sub-domain, checked to hold of the rival and fail
    # on gold.
    # =====================================================================

    # ---- the real bug, half A: process only the bottom min(m, n) rows -------
    {
        "id": "partial-domain-min-rows",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH skeleton: cap the loop at the bottom `min(m, n)` rows
        # (`(rowsDesc m).take (min m n)`), so on a tall matrix (m > n) the topmost
        # `m - n` rows are never processed and a pivot lying there is dropped. This
        # is the literal `for i in range(m-1, m-1-min(m,n), -1)` of the base commit.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat := Id.run do\n"
            "  let mut A := A0\n"
            "  let mut k := n\n"
            "  for i in (rowsDesc m).take (min m n) do\n"
            "    let p := step A i k\n"
            "    A := p.1\n"
            "    k := p.2\n"
            "  return sliceCols A k"),
        "refinement": "this IS the pre-patch routine (`rows = min(m, n)`; `for i in "
                      "range(m-1, m-1-rows, -1)`). On a tall matrix (m > n) it skips "
                      "the topmost `m - n` rows, so a genuine pivot in a top row is "
                      "never placed and its column is dropped — e.g. the reporter's "
                      "3×2 [[1,12],[0,8],[0,5]] reduces to a 1-column block instead of "
                      "the 2-column [[1,0],[0,8],[0,5]], and the F2P "
                      "test_issue_23410 / test_hermite_normal (the 3×2 "
                      "[[2,7],[0,0],[0,0]] → 1-col case) FAIL. This is exactly the "
                      "reported 'HNF removing rows' bug, so the faithful real patch "
                      "does NOT resolve.",
        "rationale": "REJECT from the sole clause `result = sliceCols (hnfFold "
                     "(rowsDesc m) A0 n) …`: capping the row set at `min(m,n)` folds "
                     "`step` over fewer rows, threading a different (matrix, pointer) "
                     "pair into the final slice than the all-rows fold. Refuted on the "
                     "m=2, n=1 tall sub-domain: gold processes rows [1, 0] but the "
                     "rival processes only row [1] (min(2,1)=1), so when row 1's "
                     "reduction leaves the pointer non-zero the two slices differ. "
                     "Binder spread: (m,n)=(2,1), A0 quantified.",
        # Two hypotheses about DIFFERENT terms (a slice inequality and a
        # pointer-non-zero fact), so jointly satisfiable — verified by the gate's
        # False-derivation probe failing. Rival folds only row 1; gold folds row 1
        # then row 0 (when the pointer is still non-zero), so the slices differ.
        #
        # AUDIT REPAIR (discrimination). The first form of this witness opened with
        # `unfold … ; simp only [… , if_neg h2]` and closed `simpa using h`. It
        # cleared the gate (rival 0, gold 1) but its GOLD-side exit code carried no
        # information about the CLAIM: at (m,n)=(2,1) that `simp only` set leaves
        # gold's two-row `forIn` as an unreduced `match … ForInStep …` term, so the
        # final step failed on a term-shape mismatch rather than on a refutation.
        # Measured with the mandatory forgery pair (attack B'): a witness differing
        # ONLY in flipping the claim (`≠` -> `=`, goal without `¬` — i.e. asserting
        # gold is CORRECT there) failed on gold with the SAME unreduced-`forIn`
        # mismatch (exit 1) while ELABORATING against the rival (exit 0). A gate run
        # on that forgery would have recorded `rejected`. The same witness also
        # failed (exit 1) against BOTH of this battery's VERIFYING positives, which
        # confirms the failure tracked syntactic loop shape, not wrongness.
        #
        # The repair drops `unfold` for a full `simp` with the spec/impl as
        # simp lemmas, which DOES reduce the two-row `forIn` on both sides. Now
        # gold's failure is semantic and claim-sensitive:
        #   * repaired witness: rival exit 0, gold exit 1, consistency probe exit 1;
        #     gold's error is `term h has type ¬sliceCols … = sliceCols … but is
        #     expected to have type False` — i.e. `simp` PROVED the spec equation
        #     for gold and the refutation had nothing left to contradict;
        #   * flipped claim (gold IS correct at (2,1)) under the SAME tactic:
        #     gold exit 0, rival exit 1 — the exit codes SWAP with the claim, which
        #     is exactly the information the old form lacked.
        # Independently, gold's correctness at this point is machine-checked
        # directly (`simp [problem_spec…, implementation…, rowsDesc, List.range,
        # List.range.loop, hnfFold, h2]` closes the spec at (2,1), exit 0) while the
        # same statement against the rival fails, so (m,n)=(2,1) is a genuine
        # divergence point and not a tactic artifact.
        "witness": (
            "-- Refuted on the m>n tall sub-domain (m=2, n=1). Conditioned on the\n"
            "-- opaque carrier: assume row 1's reduction leaves the pointer non-zero\n"
            "-- (h2) so gold goes on to process row 0, and assume the two resulting\n"
            "-- slices differ (h). The rival stops after row 1 and slices there;\n"
            "-- gold slices after also folding row 0. The two hypotheses are about\n"
            "-- different terms, so no False is derivable (jointly satisfiable).\n"
            "-- The tactic is a FULL `simp` with the spec and impl as simp lemmas,\n"
            "-- not `unfold` + `simp only`: the two-row `forIn` must actually reduce\n"
            "-- on BOTH sides, else gold fails on an unreduced `match … ForInStep`\n"
            "-- term-shape mismatch for every claim and its exit code says nothing\n"
            "-- about this one. With this form, `simp` proves the spec equation for\n"
            "-- gold (goal `False`, refutation refuted) and the flipped claim swaps\n"
            "-- both exit codes.\n"
            "example (A0 : Mat)\n"
            "    (h2 : (step A0 1 1).2 ≠ 0)\n"
            "    (h : sliceCols (step A0 1 1).1 (step A0 1 1).2\n"
            "          ≠ sliceCols (step (step A0 1 1).1 0 (step A0 1 1).2).1\n"
            "              (step (step A0 1 1).1 0 (step A0 1 1).2).2) :\n"
            "    ¬ problem_spec_hermiteNormalForm A0 2 1\n"
            "        (implementation_hermiteNormalForm A0 2 1) := by\n"
            "  simp [problem_spec_hermiteNormalForm, implementation_hermiteNormalForm,\n"
            "    rowsDesc, List.range, List.range.loop, hnfFold, h2]\n"
            "  simpa using h\n"
        ),
    },

    # ---- partial-domain, half B: skip the bottom (first-processed) row ------
    {
        "id": "partial-domain-skip-bottom-row",
        "kind": "uniqueness",
        "expect": "reject",
        # Begin the row loop at the second-from-bottom row (`(rowsDesc m).tail`), so
        # the bottom row is never reduced. Correct on matrices whose bottom row
        # yields no pivot, but wrong whenever the bottom row IS a pivot: that pivot
        # is never placed and its column is dropped.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat := Id.run do\n"
            "  let mut A := A0\n"
            "  let mut k := n\n"
            "  for i in (rowsDesc m).tail do\n"
            "    if k = 0 then\n"
            "      break\n"
            "    let p := step A i k\n"
            "    A := p.1\n"
            "    k := p.2\n"
            "  return sliceCols A k"),
        "refinement": "a faithful real patch that began the row loop one row above the "
                      "bottom (`range(m-1, ...)` skipping index `m-1`) would never "
                      "reduce against the bottom row, retaining its column even when "
                      "that row carries the only pivot — the reporter's row-family "
                      "hints show the retained submatrix is wrong exactly when the "
                      "pivot sits in a particular row (e.g. [[0,12],[0,8],[1,5]] vs a "
                      "bottom-pivot matrix). It gives the wrong normal form, so it "
                      "does NOT resolve the F2P.",
        "rationale": "REJECT from the sole clause: dropping the bottom row from the "
                     "fold threads a different (matrix, pointer) pair into the slice "
                     "than the all-rows fold. Refuted on the m=1, n=1 sub-domain: gold "
                     "folds the single row 0 (`step A0 0 1`) then slices; the rival "
                     "folds NO rows (`(rowsDesc 1).tail = []`) and slices the input "
                     "matrix at the initial pointer, so the two slices differ. Binder "
                     "spread: (m,n)=(1,1), A0 quantified — distinct from the "
                     "min-rows rival's (2,1).",
        # Single inequality hypothesis, trivially satisfiable.
        "witness": (
            "-- Refuted on a single-row square shape (m=1, n=1). Conditioned on the\n"
            "-- opaque carrier: the rival folds no rows ((rowsDesc 1).tail = []) and\n"
            "-- slices the input at the initial pointer (sliceCols A0 1), while gold\n"
            "-- folds row 0 first (sliceCols (step A0 0 1).1 (step A0 0 1).2). Assume\n"
            "-- only that these two slices differ (h) — one hypothesis, satisfiable.\n"
            "example (A0 : Mat)\n"
            "    (h : sliceCols A0 1 ≠ sliceCols (step A0 0 1).1 (step A0 0 1).2) :\n"
            "    ¬ problem_spec_hermiteNormalForm A0 1 1\n"
            "        (implementation_hermiteNormalForm A0 1 1) := by\n"
            "  unfold problem_spec_hermiteNormalForm implementation_hermiteNormalForm\n"
            "  simp only [rowsDesc, List.range, List.range.loop, List.reverse_cons,\n"
            "    List.reverse_nil, List.nil_append, List.tail, hnfFold]\n"
            "  simpa using h\n"
        ),
    },

    # ---- the missing early stop: drop the k = 0 break ------------------------
    {
        "id": "uniqueness-no-early-stop",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `if k = 0 then break` guard entirely: keep reducing every row
        # even after the pointer reaches the leftmost column. Once `k = 0` the
        # reference fold stops (returns the current pair), but this rival keeps
        # calling `step A i 0`, threading a DIFFERENT (matrix, pointer) pair into the
        # remaining reductions and the final slice.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat := Id.run do\n"
            "  let mut A := A0\n"
            "  let mut k := n\n"
            "  for i in rowsDesc m do\n"
            "    let p := step A i k\n"
            "    A := p.1\n"
            "    k := p.2\n"
            "  return sliceCols A k"),
        "refinement": "a faithful real patch that removed the `if k == 0: break` guard "
                      "would keep running the per-row reduction after all `n` pivots "
                      "are already placed (the pointer at the leftmost column). In the "
                      "real code that reduces against a zero-width pivot region and "
                      "corrupts the retained submatrix (or errors on the "
                      "already-exhausted column range) — precisely the `n < m` "
                      "over-processing case the break was ADDED to stop. The break is "
                      "the fix's new hunk; a patch that omits it produces the wrong "
                      "normal form on a tall matrix with n pivots already found, so it "
                      "does NOT resolve.",
        "rationale": "REJECT from the sole clause: the reference fold short-circuits "
                     "once the pointer is 0 (`hnfFold (i::rest) A 0 = (A, 0)`), but the "
                     "rival keeps folding `step A i 0` over the remaining rows, so the "
                     "threaded (matrix, pointer) pair — and the final slice — differ. "
                     "Refuted on the m=1, n=0 sub-domain (the pointer starts at the "
                     "leftmost column, so gold does NO reduction and slices the input, "
                     "while the rival reduces row 0 anyway). Binder spread: "
                     "(m,n)=(1,0), n at its boundary 0 — distinct from both "
                     "partial-domain rivals.",
        # Single inequality hypothesis, trivially satisfiable.
        "witness": (
            "-- Refuted on a one-row zero-column shape (m=1, n=0). The pointer starts\n"
            "-- at the leftmost column (k = n = 0), so gold's fold short-circuits\n"
            "-- immediately and slices the input (sliceCols A0 0), while the rival\n"
            "-- (no break) still reduces row 0 and slices (step A0 0 0). Conditioned\n"
            "-- on the opaque carrier: assume only that these two slices differ (h) —\n"
            "-- one hypothesis, satisfiable.\n"
            "example (A0 : Mat)\n"
            "    (h : sliceCols (step A0 0 0).1 (step A0 0 0).2 ≠ sliceCols A0 0) :\n"
            "    ¬ problem_spec_hermiteNormalForm A0 1 0\n"
            "        (implementation_hermiteNormalForm A0 1 0) := by\n"
            "  unfold problem_spec_hermiteNormalForm implementation_hermiteNormalForm\n"
            "  simp only [rowsDesc, List.range, List.range.loop, List.reverse_cons,\n"
            "    List.reverse_nil, List.nil_append, hnfFold]\n"
            "  simpa using h\n"
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 3 partial/uniqueness
# rivals) plus an EMPTY AXIOM lane. This bundle models the SAME purely-functional
# core (the outer row-processing loop of the reduction) at a different
# abstraction — the matrix as `List (List Int)`, the unchanged per-row reduction
# and the column slice as `opaque step`/`sliceCols`, and the fixed control flow
# spelled out as a front-recursive fold — with NO heap, NO fractional
# permission, NO predicate. Every sibling case is recorded below.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   frame-mut-write-found      (frame)    -> (none)                    VACUOUS (no perm)
#   partial-domain-min-rows    (uniq)     -> partial-domain-min-rows   PORTED
#   partial-domain-skip-bottom-row (uniq) -> partial-domain-skip-bottom-row PORTED
#   uniqueness-no-clamp-negative-k (uniq) -> uniqueness-no-early-stop   RE-EXPRESSED
#   pos-control-branchless     (soundness)-> pos-restate-fold           RE-EXPRESSED
#   pos-control-hoisted-local  (soundness)-> pos-guard-explicit-else    RE-EXPRESSED
#   admissibility-self-call    (admiss)   -> admiss-f2p-shape           RE-EXPRESSED
#   AXIOM_TESTS (0)                       -> (none)                     N/A (empty)
#
# PORTED (partial-domain rivals): `partial-domain-min-rows` ports directly — the
#   nagini rival caps the loop at `min(len(found), n)` rows; here the loop caps at
#   `(rowsDesc m).take (min m n)`, the literal pre-patch row set, wrong on the
#   `m > n` tall sub-domain. `partial-domain-skip-bottom-row` ports directly — the
#   nagini rival starts `i` at 1 (skips the bottom row `found[0]`); here it starts
#   at `(rowsDesc m).tail` (skips the bottom-processed row m-1), wrong whenever the
#   bottom row carries the pivot.
# RE-EXPRESSED (no-clamp -> no-early-stop): the nagini rival drops the `if k == 0:
#   break` and lets the integer marker `k` go NEGATIVE, violating `0 <= Result()`
#   and the clamp clause. On THIS carrier the marker is a `Nat` pointer and the
#   modeled clause is not an arithmetic bound on a returned integer but the
#   equality of the RESULT MATRIX to the fold's slice; the same missing break is
#   re-expressed as it belongs here — dropping the break makes the impl keep
#   folding `step A i 0` past the point where the reference `hnfFold`
#   short-circuits, so the threaded (matrix, pointer) pair and the final slice
#   diverge. The ARGUMENT (the early stop is the fix's new hunk and no faithful
#   patch omits it) is carried over; only the rejection MECHANISM changes (a
#   matrix-value divergence, not an integer-bound violation). Refuted at (m,n)=(1,0),
#   the boundary where the pointer starts at 0.
# RE-EXPRESSED (positive controls): the nagini `pos-control-branchless` replaces
#   the `if c == 1: k -= 1` branch with the branchless `k -= c` — a proof-neutral
#   value-equal reshape that keeps the imperative loop. There is no per-flag
#   decrement on this carrier (the pointer update is bundled inside `opaque step`),
#   so the analogous "same computation, different surface" positive is
#   `pos-restate-fold`: drop the do-block entirely and restate the reference fold,
#   which computes the identical Mat and closes by `rfl`. The nagini
#   `pos-control-hoisted-local` (hoist the guard / reorder into an explicit local +
#   guard) ports as `pos-guard-explicit-else` — the same guard reshape (early break
#   rewritten as `if k = 0 then break else <reduce>`), semantically identical, and
#   the frozen forIn-bridge proof closes unchanged. Both verify with real builds.
# RE-EXPRESSED (admissibility): the nagini `admissibility-self-call` re-invokes the
#   routine on the SAME in-domain input to witness the precondition is
#   establishable. This Lean theorem carries the precondition as a hypothesis
#   (`m = A0.length` and every row width = n), so the admissibility probe is
#   re-expressed as a `have` inside the frozen proof body establishing that
#   precondition at a concrete F2P-shaped input (the reporter's 3×2 tall matrix),
#   then closing the frozen obligation verbatim — a non-vacuity / PRECOND-TOO-STRONG
#   guard at exactly the F2P input.
# VACUOUS (frame-mutation): the nagini `frame-mut-write-found` writes into the
#   read-only pivot-flag list held at `Acc(.,1/2)` and MUST be rejected for
#   INSUFFICIENT PERMISSION. Lean is referentially transparent: `A0` is an
#   immutable value with no heap footprint, no aliasing, and no fractional
#   permission — there is no store to reject and no permission clause it could
#   violate. Not fabricated (porting map: this class is vacuous on a referentially
#   transparent carrier). The read-only discipline it probes is instead pinned by
#   the spec being an exact equality to a total function of the inputs, which the
#   uniqueness rivals attack.
#
# DIVERGENCE / NON-TERMINATION: no sibling case, and a KNOWN HOLE here rather
#   than a vacuous class — see the DIVERGENCE entry in the module docstring. A
#   `partial def` row loop with no decreasing measure IS writable as a variant and
#   IS rejected (measured, exit 1, honest unsolved fold-equality goal), so the
#   rival direction is expressible; what blocks shipping the case is that its
#   witness must avoid the variant-only name and the resulting hypothesis is
#   contradictory on gold, so the witness elaborates on gold too (exit 0) and the
#   gate would record `witness-vacuous`. The spec is NOT weak here.
#
#   The three reject witnesses probe three DISTINCT shapes — (m,n) ∈ {(1,0),
#   (2,1), (1,1)} with A0 quantified — so `pts` = 3 distinct input points and the
#   shape binders m, n each vary (m ∈ {1,2}, n ∈ {0,1}). The sole postcondition
#   clause is attacked by every rival (each folds the wrong row set / early stop
#   into the slice), and it is DEFENDED by three positives (a fold restatement, an
#   imperative guard reshape, and the F2P-shape admissibility control). Each rival
#   carries a machine-checked witness that ELABORATES against the rival and FAILS
#   (leaves an unmet goal) against the frozen solution, conditioned on the opaque
#   carrier with jointly-satisfiable hypotheses.
#
# INDEPENDENT AUDIT PROBES (attacks D and E), all built for real; recorded here so
# the next reader does not re-pay for them. None changed the spec's disposition.
#
#   D (SPEC-TOO-WEAK probe) — six NEW wrong impls this battery did not contain,
#   aimed at the binders the shipped rivals leave least attacked (the row ORDER,
#   the slice's two arguments, the stop THRESHOLD, the row-count arithmetic). Each
#   was built twice, once with its own `rfl` and once under the frozen proof
#   script. All twelve builds REJECT (exit 1):
#     * fold the rows ASCENDING (`List.range m`) instead of bottom-up
#     * slice at the INITIAL pointer `n` instead of the fold's terminal pointer
#     * slice the ORIGINAL matrix `A0` instead of the fold's terminal matrix
#     * stop at `k = 1` instead of `k = 0` (off-by-one on the early stop)
#     * fold over `rowsDesc (m+1)` (one row too many)
#     * fold over `(rowsDesc m).dropLast` (drop the TOPMOST row — the mirror of
#       the shipped skip-bottom rival)
#   No wrong impl was found that verifies, so no spec hole surfaced. Note this is
#   expected on THIS spec shape and is not a strong signal: the postcondition is
#   an exact equality to a total function of the inputs, so any impl denoting a
#   different function is unprovable by construction.
#
#   E (SPEC-TOO-STRONG probe) — three NEW correct reshapes beyond the two shipped
#   positives, all of which VERIFY (exit 0), so no soundness hole:
#     * hoist the row list into a local `let rows := rowsDesc m` before the loop
#     * destructure the fold's pair with an explicit `match … | (A, k) => …`
#       instead of `.1`/`.2` projections
#     * replace the reference fold with a state-PAIR-threaded helper `def hnfAlt`
#       of a different recursion shape, plus an inline `have` bridging it to
#       `hnfFold` by induction — the most structurally distant correct impl tried,
#       and it still closes. Good evidence the spec is not over-fit to the frozen
#       do-block or to `hnfFold`'s exact currying.
#
#   ADMISSIBILITY, checked to be load-bearing rather than decorative. Two NEGATIVE
#   controls of `admiss-f2p-shape`'s own shape — the same `have` with a FALSE
#   width claim (`row.length = 3` for width-2 rows) and with a FALSE row-count
#   claim (`4 = length` of a 3-row matrix) — both FAIL (exit 1), so the spliced
#   `have` really does discharge a claim about the precondition at the concrete
#   F2P-shaped input and is not a no-op the frozen script carries regardless.
#
# AXIOM_TESTS: empty. The bundle consumes no `axiom` (meta.json axioms == [],
# deep_model_references == []); the two opaque callees are signature-only and
# cancel in the differential, so there is nothing for the axiom lane (G-AX) to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
