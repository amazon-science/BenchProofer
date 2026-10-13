"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-11578 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

This is a PORT of the nagini sibling battery. The nagini surface contracts one
pure value function; the lean bundle models exactly the same purely functional
core, so the port is one-obligation and the case classes carry over directly.

DEFENDED SURFACE (one total function over two inputs):

  scoringProbs
      (multiClass : String) (decisions : List (List (List ℝ)))
      : List (List (List ℝ))
      result = decisions.map (fun d => predictProba (parseMode multiClass) d)

  ``multiClass`` is the requested regime string (``"multinomial"`` selects the
  softmax regime via ``parseMode``; any other value selects one-vs-rest).
  ``decisions`` is a list of candidate score matrices; each matrix is a list of
  per-sample score rows (``List ℝ``). The result maps every candidate to its
  per-row probability estimates under the REQUESTED regime, in input order.
  Real-valued scores are modeled as Mathlib ``ℝ`` (the transforms are genuine
  real-analysis maps: softmax exponentiates+normalises, one-vs-rest passes each
  score through the logistic then normalises).

  The single top-level clause folds two inseparable sub-decisions, each pinned
  to a distinct binder:

    * WHICH REGIME is applied — ``parseMode multiClass`` selects softmax vs
      one-vs-rest. Pinned by ``multiClass``. This is the load-bearing decision:
      the two regimes disagree on every nontrivial score row, so an estimator
      that applies the wrong regime diverges exactly where the requested and
      applied regimes differ.
    * WHICH CANDIDATES / ROWS are transformed and in what order — the estimates
      are the requested regime applied ``decision.map`` row-by-row across every
      candidate ``decisions.map``, preserving count and order. Pinned by
      ``decisions``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling notes this class
    is already inapplicable there (both parameters are immutable value types).
    On lean it is doubly vacuous: Lean is referentially transparent, the two
    inputs are plain immutable values (``String`` / nested ``List ℝ``), there is
    no fractional permission to violate and no aliasing to exploit. No substitute
    is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the two inputs (``decisions.map`` of
    ``predictProba (parseMode multiClass)``), with the regimes ``softmaxRow`` /
    ``ovrRow`` modeled DEEPLY over ``ℝ`` rather than axiomatized. The bundle
    declares no ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references validated by G-AX). There is no answer key an impl
    could echo without applying the modeled regime. The honest analogue is the
    cheapest-correct POSITIVE CONTROL below (nagini's pos-inline / pos-reorder).

  * PARTIAL-DOMAIN (the pre-patch bug) — APPLIES, and is the load-bearing rival.
    The pre-fix estimator ignored the requested mode and always ran one-vs-rest.
    It is correct on the one-vs-rest request but wrong on the multinomial one —
    the F2P sub-domain — so it is refuted precisely there (nagini weak-prepatch).

  * MODE-FLIP / ALWAYS-MULTINOMIAL — APPLY. A rival that applies the OPPOSITE
    regime to the one requested (nagini weak-mode-flip) and one that always
    applies softmax regardless of the request (nagini weak-always-multinomial)
    each violate the one clause on a distinct sub-domain and are refuted with
    witnesses at distinct requests / score matrices.

  * AXIOM lane (nagini AXIOM_TESTS) — DROPPED. The axiom lane is G-AX's job; this
    gate ignores it. The two probability transforms are modeled deeply here (no
    consumed axiom), so there is nothing for a spec-lane axiom probe to
    re-discharge in any case. AXIOM_TESTS is empty.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input. The discriminating content lives in ``Real.exp`` (softmax vs
one-vs-rest), which is NOT ``decide``-able, so each witness reduces the impl loop
definitionally, projects the first candidate/row, and refutes the row equality by
real-analysis: on the score row ``[0, 1]`` the softmax first entry ``1/(1+e)``
and the one-vs-rest first entry reduce to an equation that forces ``e = exp 1``
to satisfy ``e·(e−1) = 0`` — impossible since ``1 < exp 1``. Each witness was
checked (two real builds) to HOLD of its rival and to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. Both input binders are varied across the reject witnesses so the
battery exercises the spec's dependence on each rather than probing one point:
  * ``multiClass`` — refuted at ``"multinomial"`` (prepatch-guard) AND at
    ``"ovr"`` (always-multinomial, mode-flip), so both regimes of the selector
    are attacked.
  * ``decisions`` — refuted at a one-candidate/one-row matrix ``[[[0,1]]]``
    (prepatch, always), at a one-candidate/two-row matrix ``[[[0,1],[0,1]]]``
    (mode-flip), at a TWO-CANDIDATE matrix ``[[[0,1]],[[1,0]]]``
    (reversed-candidate-order), AND at a one-candidate matrix with two DISTINCT
    rows ``[[[0,1],[1,0]]]`` (reversed-row-order), so that binder is varied in a
    way that changes the spec's verdict rather than only in shape. The last two
    points are what make the variation meaningful rather than two spellings of
    one point: at every one-candidate input the candidate permutation is the
    identity, and at the ``[[0,1],[0,1]]`` input the row permutation is the
    identity, so each ordering rival is CORRECT at the other rivals' points and
    is refuted only at its own (both measured — see below).
``pts`` = 5 distinct input points.

EVERY POSITIONAL LEVEL OF THE CLAUSE CARRIES A RIVAL. The clause folds a regime
decision and TWO nested position decisions (``decisions.map`` over candidates,
and ``predictProba mode d = d.map (predictProbaRow mode)`` over score rows), and
each now has a rival that ONLY that part can reject:
  * regime — prepatch / mode-flip / always-multinomial (all edit the
    regime-selection line).
  * candidate order — reversed-candidate-order applies the REQUESTED regime
    correctly to the correct rows and only permutes the candidate sequence, so no
    regime content can reject it; only ``map``'s index-for-index correspondence
    can. Refuted at a two-candidate input, since at the one-candidate inputs the
    rest of the lane uses, permuting candidates is the identity and that rival is
    CORRECT (verified: the same witness scaffold aimed at a one-candidate input
    FAILS against it).
  * row order — reversed-row-order keeps the regime, the candidate order AND the
    row count, permuting only the rows WITHIN a candidate, so neither the regime
    content nor the candidate-order content can reject it; only the INNER
    ``d.map`` correspondence can. Refuted at a one-candidate input with two
    DISTINCT rows, since at ``[[0,1],[0,1]]`` (the two-row point the mode-flip
    witness uses) reversing rows is the identity and that rival is CORRECT.

WHY THE WITNESSES ARE DISCRIMINATORS AND NOT SCAFFOLD ARTIFACTS. Each witness
fails on the frozen solution at its inner ``have h2`` step, which is the point
where the frozen impl's ``Id.run`` loop is reduced and the projected row is
matched against the regime the witness names. The gold-side error prints the
projection UNREDUCED (``(implementation_scoringProbs ...).head?.getD [] = ...``),
which by itself is exactly what a hollow tactic mismatch looks like — an exit
code that would be 1 for every claim, carrying no information about the claim.
It is not that here, and the evidence is a FLIP-THE-CLAIM 2x2 built at each
witness's own input, varying ONLY the regime the ``have h2`` names (four real
builds per case, exit codes recorded):

    subject \\ claimed regime      gold's own regime      the witness's regime
    frozen solution                       0                        1
    the rival                             1                        0

The anti-diagonal is what matters. Holding the subject at the FROZEN solution and
flipping only the claim moves its exit from 0 to 1, so gold's exit code TRACKS
the claim rather than the scaffold: the ``congrArg``/``simpa`` step does reduce
the frozen loop and fails only when the regime it names is not the one the frozen
impl computes. Symmetrically, the FORGERY — the same scaffold against the RIVAL,
but claiming the rival AGREES with the spec there (the opposite of a refutation) —
fails at exit 1, so the rival-side success is not something the scaffold hands to
any claim either. Independently, each witness scaffold aimed at a point where its
own rival is CORRECT (the prepatch rival on an ``"ovr"`` request; the prepatch
rival on a one-class score row ``[[[0]]]`` where softmax and one-vs-rest coincide
at ``[1]``; the candidate-order rival at a one-candidate input; the row-order
rival at ``[[0,1],[0,1]]``) FAILS to build against that rival, so the scaffold
cannot manufacture a refutation it has not earned.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-11578"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The single line that selects the regime inside the frozen impl loop. Editing
# it lands entirely inside the `-- impl-start` / `-- impl-end` region.
_MODE_LINE = "  let mode := parseMode multiClass\n"

# The FULL frozen impl def (used by the functional positive control, which
# reshapes the whole body away from the `Id.run do` loop).
_IMPL_DEF = (
    "noncomputable def implementation_scoringProbs\n"
    "    (multiClass : String) (decisions : List (List (List ℝ))) :\n"
    "    List (List (List ℝ)) := Id.run do\n"
    "  let mode := parseMode multiClass\n"
    "  let mut out : List (List (List ℝ)) := []\n"
    "  for d in decisions do\n"
    "    out := out ++ [predictProba mode d]\n"
    "  return out"
)

# The FULL frozen proof body (tactic script only; the theorem STATEMENT is above
# and is never touched).
_PROOF_BODY = (
    "  intro multiClass decisions\n"
    "  unfold problem_spec_scoringProbs implementation_scoringProbs\n"
    "  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) "
    "decisions []]\n"
    "  simp"
)

# The head of the proof body, used to splice a ground `have` before it.
_PROOF_INTRO = "  intro multiClass decisions\n"

# The accumulator line inside the frozen impl loop. Editing it attacks the ORDER
# / SEQUENCE half of the clause (which candidates come out in which position),
# as opposed to _MODE_LINE which attacks the regime half.
_ACC_LINE = "    out := out ++ [predictProba mode d]\n"

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_MODE_LINE) == 1, "impl mode line drifted; update _MODE_LINE"
assert _BASE.count(_IMPL_DEF) == 1, "impl def drifted; update _IMPL_DEF"
assert _BASE.count(_PROOF_BODY) == 1, "proof body drifted; update _PROOF_BODY"
assert _BASE.count(_PROOF_INTRO) == 1, "proof intro drifted; update _PROOF_INTRO"
assert _BASE.count(_ACC_LINE) == 1, "impl accumulator line drifted; update _ACC_LINE"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional `decisions.map`, dropping the mutable-accumulator `Id.run do`
# loop, spelling exactly the term the spec names. Same value on every input; the
# frozen `forIn_append_helper` rewrite no longer applies to the new shape, so the
# obligation is re-proved (STATEMENT byte-identical; `unfold` + `rfl`). No new
# lemma/axiom/assumption token is introduced.
# ---------------------------------------------------------------------------
_POS_IMPL = (
    "noncomputable def implementation_scoringProbs\n"
    "    (multiClass : String) (decisions : List (List (List ℝ))) :\n"
    "    List (List (List ℝ)) :=\n"
    "  decisions.map (fun d => predictProba (parseMode multiClass) d)"
)
_POS_PROOF = (
    "  intro multiClass decisions\n"
    "  unfold problem_spec_scoringProbs implementation_scoringProbs\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold computation and its proof verbatim, but FIRST
# discharge the spec predicate at the normal F2P-shaped input (a multinomial
# request on a concrete score matrix) as a `have` inside the existing tactic
# body. If that ground instance could not be discharged, the modeled behavior
# would be unsatisfiable at exactly the input the F2P exercises (the analogue of
# PRECOND-TOO-STRONG). The theorem STATEMENT is byte-identical; nothing is
# assumed.
# ---------------------------------------------------------------------------
_ADMISS_GROUND = (
    '  have _ground : problem_spec_scoringProbs "multinomial" [[[0, 1]]]\n'
    '      (implementation_scoringProbs "multinomial" [[[0, 1]]]) := by\n'
    "    unfold problem_spec_scoringProbs implementation_scoringProbs\n"
    "    rfl\n"
)

# AUDIT ADDITION (the missing half of the admissibility claim). The `_ground`
# `have` above is discharged by `rfl`, so on its own it says only that the spec
# predicate is REFLEXIVELY true of the impl's own output at that input — it would
# stand verbatim against an impl that applies the WRONG regime, and it would still
# stand if the two regimes were the same function. So it does not witness that the
# modeled behavior is non-degenerate at the F2P input, which is what the
# admissibility case is supposed to attest.
#
# This is the honest analogue of nagini's precondition clause R2
# (`transforms_differ`, the A-consumed distinctness axiom that the nagini
# admissibility case Asserts alongside R1): the two regimes are genuinely
# DISTINCT functions at the concrete score row the battery refutes at. Here it is
# PROVED rather than assumed — real-analysis on `Real.exp`, no new
# declaration/axiom/`sorry`, spliced as a `have` inside the existing tactic body.
# If this could not be discharged, every reject witness in the lane would be
# refuting at a point where the two regimes coincide, and the whole uniqueness
# lane would be vacuous.
_ADMISS_DIFFER = (
    '  have _differ : predictProba ProbMode.multinomial [[0, 1]]\n'
    '      ≠ predictProba ProbMode.ovr [[0, 1]] := by\n'
    "    have he : (1:ℝ) < Real.exp 1 := by rw [Real.one_lt_exp_iff]; norm_num\n"
    "    simp only [predictProba, predictProbaRow, List.map_cons, List.map_nil,\n"
    "      ne_eq, List.cons.injEq, not_and]\n"
    "    intro hrow\n"
    "    exfalso\n"
    "    revert hrow\n"
    "    unfold ovrRow softmaxRow sigmoid\n"
    "    simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil,\n"
    "      neg_zero, Real.exp_zero]\n"
    "    intro h1\n"
    "    rw [List.cons.injEq] at h1\n"
    "    obtain ⟨h1, _⟩ := h1\n"
    "    set e := Real.exp 1 with he_def\n"
    "    have hexp1 : Real.exp (-1) = 1 / e := by rw [Real.exp_neg]; simp [he_def]\n"
    "    rw [hexp1] at h1\n"
    "    field_simp at h1\n"
    "    nlinarith [he, Real.exp_pos 1]\n"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each edits ONE line inside the impl loop, either the
# regime-selection line or the accumulator line (spec + theorem statement
# byte-identical). Each carries (a) the refinement argument that its faithful real
# patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input.
# ---------------------------------------------------------------------------

# PREPATCH: ignore the requested mode, always run one-vs-rest. This is the
# pre-fix bug (the scoring model was built without carrying the requested mode,
# defaulting to one-vs-rest).
_RIVAL_PREPATCH = "  let mode := ProbMode.ovr\n"

# MODE-FLIP: apply the OPPOSITE regime to the one requested.
_RIVAL_FLIP = (
    '  let mode := if multiClass = "multinomial" then ProbMode.ovr '
    "else ProbMode.multinomial\n"
)

# ALWAYS-MULTINOMIAL: always run softmax regardless of the request.
_RIVAL_ALWAYS = "  let mode := ProbMode.multinomial\n"

# AUDIT ADDITION — ORDER rival. Every rival above edits `_MODE_LINE`, i.e. all
# three attack the REGIME half of the clause and none attacks the other half the
# module docstring claims is pinned ("WHICH CANDIDATES / ROWS are transformed and
# in what order ... preserving count and order", pinned by `decisions`). The
# `decisions` binder was varied only in SHAPE (a one-row vs a two-row matrix),
# which changes no verdict the regime rivals do not already change; nothing in
# the lane forced the output SEQUENCE. This rival prepends instead of appending,
# so it applies the correct regime to the correct rows and returns them in
# REVERSED candidate order.
_RIVAL_ORDER = "    out := [predictProba mode d] ++ out\n"

# AUDIT ADDITION (second audit pass) — ROW-order rival. The four rivals above
# split as three-on-the-regime plus one on the CANDIDATE sequence, so the
# `decisions` binder is attacked only at its OUTER level. But the clause's
# transform is `predictProba mode d`, which is itself `d.map (predictProbaRow
# mode)`: the i-th reported estimate row must be the transform of the i-th SCORE
# row of that candidate. Nothing in the lane forced that INNER correspondence —
# every existing witness projects only the first candidate and then refutes on
# regime content, so a rival that keeps the regime, keeps the candidate order and
# keeps the row COUNT, but permutes the rows WITHIN each candidate, was
# unattacked. This rival reverses them.
_RIVAL_ROWORDER = "    out := out ++ [predictProba mode d.reverse]\n"


# Shared witness scaffold: reduce the impl loop definitionally at the concrete
# input, project the first candidate/row via `headD`, then refute the row
# equality on the score row [0,1] where softmax ≠ one-vs-rest (which forces
# `exp 1 · (exp 1 − 1) = 0`, impossible since `1 < exp 1`).
_WIT_TAIL = (
    "  rw [List.cons.injEq] at h2\n"
    "  obtain ⟨hrow, _⟩ := h2\n"
    "  revert hrow\n"
    "  unfold ovrRow softmaxRow sigmoid\n"
    "  simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil,\n"
    "    neg_zero, Real.exp_zero]\n"
    "  intro h1\n"
    "  rw [List.cons.injEq] at h1\n"
    "  obtain ⟨h1, _⟩ := h1\n"
    "  set e := Real.exp 1 with he_def\n"
    "  have hexp1 : Real.exp (-1) = 1 / e := by rw [Real.exp_neg]; simp [he_def]\n"
    "  rw [hexp1] at h1\n"
    "  field_simp at h1\n"
    "  nlinarith [he, Real.exp_pos 1]\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Ports nagini pos-inline-branch /
    # pos-branch-reorder (both were the same "faithful reshape of the dispatch"
    # idea; on this carrier the analogue is dropping the `Id.run do` loop for the
    # functional `decisions.map`, which is a strictly bigger reshape).
    # =====================================================================
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_DEF, _POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` "
            "loop and expresses the computation as the functional "
            "`decisions.map (fun d => predictProba (parseMode multiClass) d)` "
            "must satisfy `result = decisions.map (fun d => predictProba "
            "(parseMode multiClass) d)`; if it cannot, the spec is "
            "SPEC-TOO-STRONG (it would reject a faithful reshape of the modeled "
            "computation). Proof: after `unfold` both sides are the same `map` "
            "term, so the goal closes by `rfl` — no new declaration, axiom, or "
            "assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at the normal, F2P-shaped
    # input. The frozen theorem carries NO precondition hypothesis (the behavior
    # is total, the `∀` unguarded), so nagini's precondition-admission probe has
    # no binder to attack; the honest analogue is to discharge the spec predicate
    # at the F2P ground input (a multinomial request on a concrete score matrix)
    # inside the proof region, alongside the frozen obligation. Ports nagini
    # admiss-precond-nonvacuous.
    # =====================================================================
    {
        "id": "admiss-multinomial-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_INTRO,
                        _ADMISS_GROUND + _ADMISS_DIFFER + _PROOF_INTRO),
        "rationale": (
            "TWO ground facts are discharged inside the existing tactic body, "
            "then the frozen obligation is closed verbatim. (1) SATISFIABILITY: "
            "the spec predicate holds at the F2P-shaped input (the multinomial "
            "regime requested on the concrete score matrix `[[[0, 1]]]`), by "
            "`unfold` + `rfl` — else the spec is unsatisfiable at the normal "
            "input, the analogue of PRECOND-TOO-STRONG. (2) NON-DEGENERACY: the "
            "two regimes are genuinely DISTINCT at that same score row, "
            "`predictProba ProbMode.multinomial [[0, 1]] ≠ predictProba "
            "ProbMode.ovr [[0, 1]]`, proved by real-analysis on `Real.exp`. (2) "
            "is what makes (1) load-bearing: `rfl` alone proves the spec "
            "predicate of whatever the impl returns, so it would stand against a "
            "wrong-regime impl and would stand if the regimes coincided. (2) is "
            "the proved analogue of nagini's `transforms_differ` precondition "
            "clause R2 and certifies that the point every reject witness in this "
            "lane refutes at is a point where the regimes actually disagree. "
            "Nothing is assumed: STATEMENT byte-identical, both are `have`s in "
            "the existing tactic body, no new declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals.
    # =====================================================================
    {
        "id": "weak-prepatch-always-ovr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MODE_LINE, _RIVAL_PREPATCH),
        "refinement": (
            "this IS the pre-fix behavior: the scoring model is built without "
            "carrying over the requested multiclass mode, so it always applies "
            "the one-vs-rest regime regardless of the request. Its faithful real "
            "patch is exactly the pre-patch code, whose probabilistic score reads "
            "one-vs-rest estimates even when the multinomial regime was requested "
            "— the FAIL_TO_PASS probabilistic-scorer test on the multinomial "
            "request reads the WRONG estimates and FAILS. It does NOT resolve, so "
            "a verifying rival here would be a true verify-does-not-imply-resolve "
            "break rather than an artifact."
        ),
        "rationale": (
            "REJECT from the clause `result = decisions.map (fun d => predictProba "
            "(parseMode multiClass) d)` via the `multiClass` binder: at "
            '`multiClass = "multinomial"` the spec requires the softmax estimates, '
            "but the rival returns the one-vs-rest estimates, which differ on the "
            "score row `[0, 1]`. Refuted where the multinomial regime is requested "
            "— the discriminating sub-domain — on a one-candidate/one-row matrix."
        ),
        "witness": (
            "-- Refuted where the multinomial regime is requested: on the score\n"
            "-- row [0,1] the softmax estimates differ from the one-vs-rest\n"
            "-- estimates, so a model that always reports one-vs-rest diverges\n"
            "-- from the requested (multinomial) behavior.\n"
            'example : ¬ problem_spec_scoringProbs "multinomial" [[[0, 1]]]\n'
            '    (implementation_scoringProbs "multinomial" [[[0, 1]]]) := by\n'
            "  have he : (1:ℝ) < Real.exp 1 := by rw [Real.one_lt_exp_iff]; "
            "norm_num\n"
            "  intro h\n"
            "  rw [problem_spec_scoringProbs] at h\n"
            "  have h2 : (predictProba ProbMode.ovr [[0, 1]] : List (List ℝ))\n"
            '          = predictProba (parseMode "multinomial") [[0, 1]] := by\n'
            "    have := congrArg (fun l => l.headD []) h\n"
            "    simpa using this\n"
            "  revert h2\n"
            '  rw [show parseMode "multinomial" = ProbMode.multinomial from rfl]\n'
            "  simp only [predictProba, predictProbaRow, List.map_cons, "
            "List.map_nil]\n"
            "  intro h2\n"
            + _WIT_TAIL
        ),
    },
    {
        "id": "weak-mode-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MODE_LINE, _RIVAL_FLIP),
        "refinement": (
            "its faithful real patch builds the scoring model with the OPPOSITE "
            "mode to the one requested, so a multinomial request feeds one-vs-rest "
            "estimates to the scorer and a one-vs-rest request feeds softmax. Both "
            "requests read the wrong estimates: the FAIL_TO_PASS multinomial test "
            "FAILS, and the pre-existing one-vs-rest scoring paths break too. It "
            "does NOT resolve — a verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from the clause `result = decisions.map (fun d => predictProba "
            "(parseMode multiClass) d)`: this rival applies the OPPOSITE regime, "
            'so at `multiClass = "ovr"` the spec requires one-vs-rest but the '
            "rival returns softmax (differing on the row `[0, 1]`). Refuted on the "
            "one-vs-rest request — the sub-domain where the always-one-vs-rest "
            "prepatch rival would be CORRECT, distinguishing this near-miss — and "
            "on a one-candidate/TWO-row score matrix, varying the `decisions` "
            "binder off the single-row shape the other witnesses use."
        ),
        "witness": (
            "-- Refuted on the one-vs-rest caller, where this rival reports\n"
            "-- softmax instead: the estimator uses the OPPOSITE regime to the\n"
            "-- one requested, so on the score row [0,1] (softmax ≠ one-vs-rest)\n"
            "-- the reported estimates are the wrong ones even for the one-vs-rest\n"
            "-- request. Varies the score matrix (a two-row candidate) too.\n"
            'example : ¬ problem_spec_scoringProbs "ovr" [[[0, 1], [0, 1]]]\n'
            '    (implementation_scoringProbs "ovr" [[[0, 1], [0, 1]]]) := by\n'
            "  have he : (1:ℝ) < Real.exp 1 := by rw [Real.one_lt_exp_iff]; "
            "norm_num\n"
            "  intro h\n"
            "  rw [problem_spec_scoringProbs] at h\n"
            "  have h2 : (predictProba ProbMode.multinomial [[0, 1], [0, 1]] : "
            "List (List ℝ))\n"
            '          = predictProba (parseMode "ovr") [[0, 1], [0, 1]] := by\n'
            "    have := congrArg (fun l => l.headD []) h\n"
            "    simpa using this\n"
            "  revert h2\n"
            '  rw [show parseMode "ovr" = ProbMode.ovr from rfl]\n'
            "  simp only [predictProba, predictProbaRow, List.map_cons, "
            "List.map_nil]\n"
            "  intro h2\n"
            + _WIT_TAIL
        ),
    },
    {
        "id": "weak-always-multinomial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MODE_LINE, _RIVAL_ALWAYS),
        "refinement": (
            "partial-domain: its faithful real patch hardcodes the multinomial "
            "mode, ignoring the request. It is correct for a multinomial request "
            "but WRONG for a one-vs-rest request — the one-vs-rest scoring paths "
            "(the pre-existing PASS_TO_PASS that exercise the one-vs-rest regime) "
            "now read softmax estimates and FAIL. It does NOT resolve on the "
            "one-vs-rest sub-domain — a verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from the clause `result = decisions.map (fun d => predictProba "
            "(parseMode multiClass) d)` via the `multiClass` binder: at "
            '`multiClass = "ovr"` the spec requires the one-vs-rest estimates, but '
            "the rival returns the softmax estimates, which differ on the row "
            "`[0, 1]`. Refuted where the one-vs-rest regime is requested, varying "
            "`multiClass` off the `\"multinomial\"` value the prepatch witness "
            "uses so both selector branches are attacked."
        ),
        "witness": (
            "-- Refuted where the one-vs-rest regime is requested: on the score\n"
            "-- row [0,1] the one-vs-rest estimates differ from the softmax\n"
            "-- estimates, so a model that always reports softmax diverges from\n"
            "-- the requested (one-vs-rest) behavior.\n"
            'example : ¬ problem_spec_scoringProbs "ovr" [[[0, 1]]]\n'
            '    (implementation_scoringProbs "ovr" [[[0, 1]]]) := by\n'
            "  have he : (1:ℝ) < Real.exp 1 := by rw [Real.one_lt_exp_iff]; "
            "norm_num\n"
            "  intro h\n"
            "  rw [problem_spec_scoringProbs] at h\n"
            "  have h2 : (predictProba ProbMode.multinomial [[0, 1]] : "
            "List (List ℝ))\n"
            '          = predictProba (parseMode "ovr") [[0, 1]] := by\n'
            "    have := congrArg (fun l => l.headD []) h\n"
            "    simpa using this\n"
            "  revert h2\n"
            '  rw [show parseMode "ovr" = ProbMode.ovr from rfl]\n'
            "  simp only [predictProba, predictProbaRow, List.map_cons, "
            "List.map_nil]\n"
            "  intro h2\n"
            + _WIT_TAIL
        ),
    },
    # =====================================================================
    # AUDIT ADDITION — the ORDER / SEQUENCE half of the clause. The three rivals
    # above all edit the regime-selection line, so all three attack `parseMode`;
    # the `decisions.map` half ("in the same order; the number of candidates is
    # preserved") had no rival forcing it. This one applies the CORRECT regime to
    # the CORRECT rows and only permutes the candidate sequence, so it is refuted
    # purely by the ordering content of the clause.
    # =====================================================================
    {
        "id": "weak-reversed-candidate-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACC_LINE, _RIVAL_ORDER),
        "refinement": (
            "its faithful real patch collects the per-candidate probability "
            "estimates into the results sequence in the reverse of the order the "
            "candidates were iterated, while applying the requested regime "
            "correctly to each. The scoring path consumes that sequence "
            "positionally — each entry is the score for the candidate at the "
            "matching index — so every multi-candidate selection reads another "
            "candidate's estimates and the selected result is wrong whenever more "
            "than one candidate is scored. It does NOT resolve: the FAIL_TO_PASS "
            "exercises a multi-candidate scoring sweep, so it reads mismatched "
            "estimates and FAILS even though the regime is now correct — a "
            "verify-does-not-imply-resolve break, and one no regime rival covers."
        ),
        "rationale": (
            "REJECT from the ORDER content of the clause `result = decisions.map "
            "(fun d => predictProba (parseMode multiClass) d)` via the "
            "`decisions` binder: `map` fixes the i-th output as the transform of "
            "the i-th input, and this rival emits them reversed. Refuted at a "
            "TWO-CANDIDATE input `[[[0, 1]], [[1, 0]]]` — a genuinely new point "
            "for this binder, since the whole existing lane refutes at "
            "one-candidate inputs where any permutation of candidates is the "
            "identity and this rival is CORRECT. The regime is applied correctly "
            "here (the request is multinomial and softmax is what is computed), "
            "so nothing but the ordering clause can reject it."
        ),
        "witness": (
            "-- Refuted at a TWO-candidate input, where reversing the candidate\n"
            "-- sequence is observable: the first reported entry is the softmax of\n"
            "-- the SECOND candidate's row [1,0] where the spec requires the\n"
            "-- softmax of the FIRST candidate's row [0,1]. Those disagree because\n"
            "-- exp 0 / (exp 0 + exp 1) ≠ exp 1 / (exp 1 + exp 0) when 1 < exp 1.\n"
            "-- The requested regime IS the one applied, so this refutation is\n"
            "-- carried entirely by the order/position content of the clause.\n"
            'example : ¬ problem_spec_scoringProbs "multinomial" '
            "[[[0, 1]], [[1, 0]]]\n"
            '    (implementation_scoringProbs "multinomial" '
            "[[[0, 1]], [[1, 0]]]) := by\n"
            "  have he : (1:ℝ) < Real.exp 1 := by rw [Real.one_lt_exp_iff]; "
            "norm_num\n"
            "  intro h\n"
            "  rw [problem_spec_scoringProbs] at h\n"
            "  have h2 : (predictProba ProbMode.multinomial [[1, 0]] : "
            "List (List ℝ))\n"
            '          = predictProba (parseMode "multinomial") [[0, 1]] := by\n'
            "    have := congrArg (fun l => l.headD []) h\n"
            "    simpa using this\n"
            "  revert h2\n"
            '  rw [show parseMode "multinomial" = ProbMode.multinomial from rfl]\n'
            "  simp only [predictProba, predictProbaRow, List.map_cons, "
            "List.map_nil]\n"
            "  intro h2\n"
            "  rw [List.cons.injEq] at h2\n"
            "  obtain ⟨hrow, _⟩ := h2\n"
            "  revert hrow\n"
            "  unfold softmaxRow\n"
            "  simp only [List.map_cons, List.map_nil, List.sum_cons, "
            "List.sum_nil,\n"
            "    Real.exp_zero]\n"
            "  intro h1\n"
            "  rw [List.cons.injEq] at h1\n"
            "  obtain ⟨h1, _⟩ := h1\n"
            "  have hpos : (0:ℝ) < Real.exp 1 := Real.exp_pos 1\n"
            "  field_simp at h1\n"
            "  nlinarith [he, hpos]\n"
        ),
    },
    # =====================================================================
    # AUDIT ADDITION (second pass) — the ROW-correspondence content of the
    # clause. `decisions.map (fun d => predictProba (parseMode multiClass) d)`
    # constrains TWO nested positions: which candidate lands where (already
    # forced by weak-reversed-candidate-order) and which SCORE ROW inside a
    # candidate maps to which estimate row (`predictProba` is `d.map
    # (predictProbaRow mode)`). The inner one had no rival: every other witness
    # projects the first candidate and then refutes on regime content, so a rival
    # that applies the REQUESTED regime, preserves the candidate order and
    # preserves the row count — permuting only the rows WITHIN each candidate —
    # was rejected by nothing in the lane. Refuted at a single candidate carrying
    # TWO DISTINCT score rows, where reversing them is observable.
    # =====================================================================
    {
        "id": "weak-reversed-row-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACC_LINE, _RIVAL_ROWORDER),
        "refinement": (
            "its faithful real patch computes the per-class estimates for a "
            "candidate's score matrix with the sample rows traversed in the "
            "opposite order, so the reported estimate matrix is row-reversed "
            "relative to the score matrix it came from. The regime is the "
            "requested one and the row count is preserved, so the estimates are "
            "individually well-formed probability rows — but they are attributed "
            "to the wrong samples. Every downstream consumer reads the estimates "
            "positionally (row i is sample i's probability vector), so a "
            "probabilistic score pairs each sample with another sample's "
            "estimates. The FAIL_TO_PASS scores a multi-sample fit, so it reads "
            "mismatched per-sample estimates and FAILS even though the regime is "
            "correct. It does NOT resolve — a verify-does-not-imply-resolve "
            "break, and one that no regime rival and no candidate-order rival "
            "covers."
        ),
        "rationale": (
            "REJECT from the ROW-correspondence content of the clause `result = "
            "decisions.map (fun d => predictProba (parseMode multiClass) d)`: "
            "`predictProba mode d` is `d.map (predictProbaRow mode)`, which fixes "
            "the i-th estimate row as the transform of the i-th score row. This "
            "rival emits them reversed. Refuted at the one-candidate/two-row "
            "input `[[[0, 1], [1, 0]]]` — a genuinely new point, since the two "
            "rows are DISTINCT (the existing two-row witness uses `[[0, 1], "
            "[0, 1]]`, where reversing rows is the identity and this rival is "
            "CORRECT). The requested regime IS the one applied and the row count "
            "is preserved, so only the inner ordering content can reject it."
        ),
        "witness": (
            "-- Refuted at ONE candidate carrying TWO DISTINCT score rows, where\n"
            "-- reversing the rows within the candidate is observable: the first\n"
            "-- reported estimate row is the softmax of the SECOND score row\n"
            "-- [1,0] where the spec requires the softmax of the FIRST row [0,1].\n"
            "-- Those disagree because exp 0 / (exp 0 + exp 1) ≠ exp 1 / (exp 1 +\n"
            "-- exp 0) when 1 < exp 1. The requested regime IS the one applied and\n"
            "-- the row count is preserved, so this refutation is carried entirely\n"
            "-- by the row-correspondence content of the clause.\n"
            'example : ¬ problem_spec_scoringProbs "multinomial" '
            "[[[0, 1], [1, 0]]]\n"
            '    (implementation_scoringProbs "multinomial" '
            "[[[0, 1], [1, 0]]]) := by\n"
            "  have he : (1:ℝ) < Real.exp 1 := by rw [Real.one_lt_exp_iff]; "
            "norm_num\n"
            "  intro h\n"
            "  rw [problem_spec_scoringProbs] at h\n"
            "  have h2 : (predictProba ProbMode.multinomial [[1, 0], [0, 1]] : "
            "List (List ℝ))\n"
            '          = predictProba (parseMode "multinomial") '
            "[[0, 1], [1, 0]] := by\n"
            "    have := congrArg (fun l => l.headD []) h\n"
            "    simpa using this\n"
            "  revert h2\n"
            '  rw [show parseMode "multinomial" = ProbMode.multinomial from rfl]\n'
            "  simp only [predictProba, predictProbaRow, List.map_cons, "
            "List.map_nil]\n"
            "  intro h2\n"
            "  rw [List.cons.injEq] at h2\n"
            "  obtain ⟨hrow, _⟩ := h2\n"
            "  revert hrow\n"
            "  unfold softmaxRow\n"
            "  simp only [List.map_cons, List.map_nil, List.sum_cons, "
            "List.sum_nil,\n"
            "    Real.exp_zero]\n"
            "  intro h1\n"
            "  rw [List.cons.injEq] at h1\n"
            "  obtain ⟨h1, _⟩ := h1\n"
            "  have hpos : (0:ℝ) < Real.exp 1 := Real.exp_pos 1\n"
            "  field_simp at h1\n"
            "  nlinarith [he, hpos]\n"
        ),
    },
]


# No consumed axioms and no deep-model references for the PBT axiom lane: the two
# probability regimes are modeled deeply over ℝ (softmax / one-vs-rest spelled
# out), not axiomatized, so there is no in-model axiom obligation for this gate
# to re-discharge. The nagini AXIOM_TESTS lane (transforms_differ soundness /
# containment) belongs to G-AX and is intentionally dropped here.
AXIOM_TESTS = []
