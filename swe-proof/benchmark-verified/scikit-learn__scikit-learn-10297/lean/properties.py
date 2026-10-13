# properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-10297
# (lean lane). PORTED from the nagini sibling: the adversarial ARGUMENTS are
# carried over and re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region is edited — the positives keep the frozen proof, and the reject
# rivals keep it too so that "does not verify" holds), checked by variant_scope +
# the Lean verifier. Every expect="reject" case carries a refutation `witness`:
# a self-contained snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the spec and not to a
# tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (from Solution.lean / mapping.md / instance.json):
#   initClassifierCV : the constructor of a cross-validated ridge *classifier*
#   estimator, building its stored configuration from the supplied options. The
#   single postcondition problem_spec_initClassifierCV is a conjunction of SEVEN
#   independent clauses, each pinning one output field to its like-named input
#   binder — the estimator records every option verbatim, none dropped or forced
#   to a default:
#       result.alphas        = alphas
#       result.fitIntercept  = fitIntercept
#       result.normalize     = normalize
#       result.scoring       = scoring
#       result.cv            = cv
#       result.classWeight   = classWeight
#       result.storeCvValues = storeCvValues   <-- the load-bearing clause the fix
#                                                  restores (the flag was dropped)
#   The oracle is grounded directly in the arguments (there is no @Pure answer-key
#   / opaque callee), and the carrier is fully transparent, so `decide` computes
#   the spec at any concrete literal input — witnesses need no conditioning.
#
# CARRIER NOTE. The nagini sibling split the behaviour across two functions and
# abstracted the retained cross-validation values as a rank-tagged record behind
# fractional read permission. This backend models ONLY the purely functional core
# — the constructor's option storage — so it is WIDER on the configuration side
# (all seven recorded options are pinned, not just the retention flag) and does
# NOT model the downstream fit that populates the record (mapping.md: that step is
# UNCHANGED by the patch and out of scope). The clauses attacked below are exactly
# the seven the frozen spec states; each is refutable at a concrete literal input.
#
# BINDER / CLAUSE COVERAGE. All seven input binders are varied across the reject
# witnesses (each rival's witness moves exactly its target field away from a common
# baseline), and every top-level conjunct of the postcondition is named by some
# reject rationale. The retention clause carries THREE rivals (ignore + negate +
# partial), refuted at DISTINCT inputs. The true near-miss of that trio is the
# constant-true IGNORE rival, which agrees with gold exactly where the flag is
# requested and is refutable only at false; the negation has NO agreement
# sub-domain (it diverges at both boolean values). The ported manifest asserted
# this the other way round and it was corrected by audit — see the negate case.
#
# SECOND-AUDIT ADDITION. One case closes the last structural gap: the whole
# ADMISSIBILITY lane was missing (`kind` lanes were soundness + uniqueness only),
# so the battery tested SPEC-TOO-WEAK and SPEC-TOO-STRONG but not
# PRECOND-TOO-STRONG — one of the three directions this gate exists to measure.
# The port dropped it, and the first audit AGREED with the port, both citing "the
# frozen obligation has no precondition". That reason is inadmissible on a total
# carrier; the analogue is satisfiability at an F2P-shaped input, and it is
# expressible here. Landed as adm-f2p-shaped-input, with negative controls.
#
# AUDIT ADDITIONS (all four re-run through the real gate). The ported battery
# attacked each clause only by forcing its field to a CONSTANT, and both of its
# positives were definitionally equal to the frozen impl. Four cases close those
# structural gaps: `pos-branch-on-flag` (a correct impl the frozen `rfl` does NOT
# close, so the obligation is genuinely reproven), and three tighter rivals —
# partial-domain retention (agrees with gold on the whole cv-absent sub-domain,
# so no listed test could catch it), scoring/cv cross-wiring (stores every value
# but in the wrong fields, defeating a "recorded somewhere" reading), and an
# alphas permutation (keeps length and elements, defeating a length/membership
# reading). All four behaved as declared against the real verifier.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME-MUTATION (nagini's #1 class: cfg held at Acc(...,1/2), the rival wrote
#     back into it). Lean is referentially transparent — no aliasing, no fractional
#     permission — so a "store into a read-only input" rival is not expressible.
#     The frame OBLIGATION it defended is instead carried by the six non-retention
#     pinning clauses (the unchanged fields are pinned explicitly), which ARE
#     attacked below. VACUOUS here as a distinct rival class.
#   * PARTIAL-DOMAIN rank collapse, CONTROL-FLOW retention-guard inverted, and
#     RANK-TWO-everywhere (nagini #2/#3/#6). All three attack the SHAPE / rank /
#     None-vs-record existence of the retained cross-validation values — a
#     downstream fit behaviour this bundle does not model. No counterpart here
#     (carrier narrowing); omitted, documented. AUDIT REFINEMENT: the CARRIER
#     NARROWING is real for the rank/existence dimension (there is no rank field
#     and no Option-valued result to collapse, so those three rivals have no
#     target). But the port over-generalized from it: the ARGUMENT SHAPE of
#     nagini's partial-domain case — correct on part of the domain, wrong on the
#     rest — does port, onto the retention flag's interaction with the splitter
#     selection, and it is now carried by
#     weak-storeCvValues-dropped-when-cv-present. "The carrier collapses the rank
#     distinction" justified dropping the rank rivals, not dropping the
#     partial-domain CLASS. Likewise nagini's inverted-guard rival maps onto the
#     negation rival already present. So of the three, only RANK-TWO-everywhere is
#     genuinely without a counterpart here.
#   * ADMISSIBILITY self-call (nagini #8) defended a half-permission precondition.
#     SECOND-AUDIT CORRECTION — this lane was WRONGLY dropped, twice. The port,
#     and then the first audit, both recorded it N/A on the reasoning that "the
#     lean obligation quantifies over ALL inputs with NO precondition hypothesis,
#     so there is nothing that could be PRECOND-TOO-STRONG". That is precisely the
#     reason the audit rules name as inadmissible: on a TOTAL carrier the analogue
#     of a too-strong precondition is the obligation being UNSATISFIABLE at exactly
#     an F2P-shaped input, which a positive that discharges the obligation at that
#     concrete input — by evaluation, as a `have`, before closing the frozen
#     obligation verbatim — tests directly. It is expressible here and is now
#     carried by adm-f2p-shaped-input. See that case for the measured evidence,
#     including the two negative controls that prove the `have` is not a tautology.

#   * AXIOM_TESTS. The axiom lane is G-AX's job (and there is no consumed axiom —
#     the option storage is modeled directly), so this gate ignores them.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10297"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). One per pinned field. ---------------------------------------
_A_ALPHAS = "alphas := alphas,"
_A_FIT = "fitIntercept := fitIntercept,"
_A_NORM = "normalize := normalize,"
_A_SCORING = "scoring := scoring,"
_A_CV = "cv := cv,"
_A_STORE = "storeCvValues := storeCvValues,"
_A_CW_UPDATE = "cfg := { cfg with classWeight := classWeight }"
for _a in (_A_ALPHAS, _A_FIT, _A_NORM, _A_SCORING, _A_CV, _A_STORE, _A_CW_UPDATE):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The full frozen impl BODY (the two-step Id.run block) — used to swap in the
# structurally-different positives.
_IMPL_BODY = (
    "  let mut cfg : ClassifierCVConfig :=\n"
    "    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,\n"
    "      scoring := scoring, cv := cv, storeCvValues := storeCvValues,\n"
    "      classWeight := none }\n"
    "  -- Record the per-class weighting selection on top of the base configuration.\n"
    "  cfg := { cfg with classWeight := classWeight }\n"
    "  return cfg"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl body anchor drifted"

# The full frozen def (signature + Id.run do body) — used to swap in the pure
# functional positive.
_IMPL_DEF = (
    "def implementation_initClassifierCV\n"
    "    (alphas : List Rat) (fitIntercept normalize : Bool)\n"
    "    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)\n"
    "    : ClassifierCVConfig := Id.run do\n"
    "  -- Delegate to the shared base initializer: record the regularization grid,\n"
    "  -- the intercept/normalize flags, the scorer and splitter selections, and the\n"
    "  -- cross-validation-values retention selection.\n"
    + _IMPL_BODY
)
assert _BASE.count(_IMPL_DEF) == 1, "impl def anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG). Both keep
# the frozen `theorem correct_initClassifierCV` statement AND the frozen proof
# body byte-identical (no new axiom/lemma/sorry); only the impl region changes.
# ===========================================================================

# pos-single-record: structurally different but CORRECT. Instead of building the
# base config then overwriting classWeight in a second `let mut` step, it records
# every option (classWeight included) in ONE record literal. The result value is
# identical on every input; only the construction FORM changes — a shape a
# faithful patch could equally take. The frozen 7-fold `rfl` proof still closes
# (the record fields reduce definitionally). If it FAILS => SPEC-TOO-STRONG.
_POS_SINGLE = _swap(
    _BASE, _IMPL_BODY,
    "  let cfg : ClassifierCVConfig :=\n"
    "    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,\n"
    "      scoring := scoring, cv := cv, classWeight := classWeight,\n"
    "      storeCvValues := storeCvValues }\n"
    "  return cfg",
)

# pos-functional: a still more structurally-different CORRECT impl — a pure
# functional `def` (no `Id.run do`, no mutable state), returning the record
# directly. Behaviourally identical; the frozen proof still closes after
# unfolding. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to the
# imperative construction shape).
_POS_FUNCTIONAL = _swap(
    _BASE, _IMPL_DEF,
    "def implementation_initClassifierCV\n"
    "    (alphas : List Rat) (fitIntercept normalize : Bool)\n"
    "    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)\n"
    "    : ClassifierCVConfig :=\n"
    "  { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,\n"
    "    scoring := scoring, cv := cv, classWeight := classWeight,\n"
    "    storeCvValues := storeCvValues }",
)

# pos-branch-on-flag (ADDED BY AUDIT). Both ported positives keep the frozen
# 7-fold `rfl` proof and still verify, which means each is DEFINITIONALLY EQUAL to
# the frozen impl: `rfl` closing is exactly the statement that the kernel sees no
# difference. That is an honest pass but a weak one — it cannot detect a spec
# over-fit that survives definitional unfolding, because no reproof is ever
# exercised. This positive is not definitionally equal: it BRANCHES on the
# retention flag and stores a literal in each arm, the shape a faithful patch
# takes when it threads the flag through a conditional rather than forwarding it.
# The result agrees with gold on every input, but the frozen `rfl` script does NOT
# close it (measured: `Application type mismatch ... (if storeCvValues = true then
# ... else ...).storeCvValues = storeCvValues`), so the case must genuinely
# REPROVE the obligation by case analysis. That makes it the first positive here
# that tests whether the postcondition is provable for a correct impl of a
# different shape, rather than for a syntactic rearrangement of the same term.
# If it FAILS => SPEC-TOO-STRONG.
# adm-f2p-shaped-input (ADDED BY THE SECOND AUDIT). The ADMISSIBILITY lane, which
# both the port and the first audit dropped as N/A. On a total carrier the analogue
# of nagini's PRECOND-TOO-STRONG probe is: is the frozen obligation actually
# SATISFIABLE at a concrete, F2P-shaped input, or does it only look dischargeable
# because it is stated under a universal quantifier that no case ever instantiates?
# Every other positive here closes the obligation symbolically, so nothing in the
# battery ever evaluates the postcondition at a real input. This case does: it
# discharges the postcondition at the input shape the FAIL_TO_PASS actually
# constructs — a three-entry regularization grid, an intercept fitted, retention
# REQUESTED, and the splitter/scorer/weighting selections left absent — as a `have`
# proved by evaluation, and only then closes the frozen obligation with the frozen
# proof body verbatim. If the postcondition were unsatisfiable at that point (a
# clause pinning a field to something the impl cannot produce there), this case
# fails while the purely symbolic positives still pass.
#
# The grid is stated as `[1/10, 1, 10]` — non-integer `Rat` values, mirroring the
# real fractional strengths rather than a degenerate all-integer grid, so the
# evaluation is over the carrier's actual arithmetic.
#
# MEASURED, because "it verifies" is not on its own evidence that anything was
# computed. `decide` and `rfl` both FAIL on this goal (`decide` cannot reduce the
# Rat `Decidable` instance; exit 1), while `simp` closes it (exit 0) — so the
# tactic really does have to evaluate the record projections. The two NEGATIVE
# CONTROLS are what rule out a tautology: a `have` whose claimed retention flag
# disagrees with the one passed to the impl, and one whose claimed grid disagrees,
# BOTH fail with `unsolved goals ⊢ False` (exit 1). A `have` that closed regardless
# of what it claimed would have closed those too. So the `have` tracks the claim,
# which is exactly what makes this a test and not decoration.
_POS_ADMISSIBILITY = _swap(
    _BASE,
    "  intro alphas fitIntercept normalize scoring cv classWeight storeCvValues\n"
    "  unfold problem_spec_initClassifierCV implementation_initClassifierCV\n"
    "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩",
    "  -- The obligation is satisfiable at the concrete input shape the new test\n"
    "  -- constructs: a three-entry grid, intercept fitted, retention requested,\n"
    "  -- and no scorer / splitter / weighting selection supplied. Discharged by\n"
    "  -- evaluation, so an unsatisfiable clause here would fail this case even\n"
    "  -- though the symbolic positives close.\n"
    "  have f2pShaped :\n"
    "      problem_spec_initClassifierCV [1/10, 1, 10] true false none none none true\n"
    "        (implementation_initClassifierCV [1/10, 1, 10] true false none none none true) := by\n"
    "    unfold problem_spec_initClassifierCV implementation_initClassifierCV\n"
    "    simp\n"
    "  intro alphas fitIntercept normalize scoring cv classWeight storeCvValues\n"
    "  unfold problem_spec_initClassifierCV implementation_initClassifierCV\n"
    "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩",
)


_POS_BRANCH = _swap(
    _swap(
        _BASE, _IMPL_DEF,
        "def implementation_initClassifierCV\n"
        "    (alphas : List Rat) (fitIntercept normalize : Bool)\n"
        "    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)\n"
        "    : ClassifierCVConfig :=\n"
        "  if storeCvValues then\n"
        "    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,\n"
        "      scoring := scoring, cv := cv, classWeight := classWeight,\n"
        "      storeCvValues := true }\n"
        "  else\n"
        "    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,\n"
        "      scoring := scoring, cv := cv, classWeight := classWeight,\n"
        "      storeCvValues := false }",
    ),
    "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩",
    "  cases storeCvValues <;> simp",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly, edits only the impl region (forcing exactly one field to a
# constant that ignores its input), and keeps the frozen proof (which no longer
# closes -> does not verify). Each carries a witness that elaborates against the
# rival and FAILS on the frozen solution.
# ===========================================================================

# One recorded option hard-coded to a constant, ignoring the supplied argument —
# the pre-patch "option not forwarded, left at its default" defect, one field at
# a time.
_RIV_ALPHAS = _swap(_BASE, _A_ALPHAS, "alphas := [],")
_RIV_FIT = _swap(_BASE, _A_FIT, "fitIntercept := false,")
_RIV_NORM = _swap(_BASE, _A_NORM, "normalize := false,")
_RIV_SCORING = _swap(_BASE, _A_SCORING, "scoring := none,")
_RIV_CV = _swap(_BASE, _A_CV, "cv := none,")
_RIV_CW = _swap(_BASE, _A_CW_UPDATE, "cfg := { cfg with classWeight := none }")
# storeCvValues — the load-bearing clause the fix restores. Two rivals:
_RIV_STORE_IGNORE = _swap(_BASE, _A_STORE, "storeCvValues := true,")
_RIV_STORE_NEGATE = _swap(_BASE, _A_STORE, "storeCvValues := !storeCvValues,")

# ADDED BY AUDIT. Every ported rival forces its target field to a CONSTANT, so
# each is refutable at essentially any input that moves that field — the coarsest
# possible defect, and the pinning clauses are the coarsest possible defence.
# Nothing in the ported battery attacked a rival that forwards its option
# CORRECTLY on part of the domain and drops it on the rest, which is the shape a
# real half-done patch actually takes (nagini carried a PARTIAL-DOMAIN class; the
# port dropped it as unportable because nagini's version attacked the downstream
# record's rank, but the retention flag itself supports one here).
#
# This rival forwards the retention selection faithfully whenever the splitter
# selection is absent, and silently forces it off when a splitter is supplied —
# reading the docstring's "this option is only meaningful together with `cv`
# absent" as licence to discard it in the other case. It agrees with gold on the
# entire cv=none sub-domain, which is every input the FAIL_TO_PASS exercises, so
# it is a far tighter near-miss than any constant rival: it is refutable ONLY at
# an input that supplies BOTH a splitter selection and a retention request.
# Rejected because the frozen clause pins the field UNCONDITIONALLY — storage is
# verbatim regardless of the other options, and "not meaningful later" is not
# "not recorded now".
_RIV_STORE_PARTIAL = _swap(
    _BASE, _A_STORE,
    "storeCvValues := (match cv with | none => storeCvValues | some _ => false),")

# ADDED BY AUDIT. The other structural gap: every ported rival drops or fixes a
# field, so none tests that the spec pins each field to its OWN input rather than
# merely to some input of the right type. A rival that CROSS-WIRES two same-typed
# options stores every supplied value — nothing is defaulted or discarded, and the
# stored multiset is identical to gold's — yet lands two of them in the wrong
# fields. This is a real transcription defect in a constructor whose forwarding is
# a long positional/keyword argument list, and it is invisible to any check that
# only asks "was each option recorded somewhere". It agrees with gold on the whole
# diagonal (scoring == cv), so it is refuted off it.
_RIV_SWAP_SCORING_CV = _swap(
    _BASE, "scoring := scoring, cv := cv,", "scoring := cv, cv := scoring,")

# ADDED BY AUDIT. The alphas clause was probed only by a rival that empties the
# grid. `List` equality is order-sensitive and the mapping records the sequence as
# order-preserving ("stored verbatim", the trailing cv_values_ axis follows its
# order), so a rival that stores a PERMUTATION of the supplied grid keeps its
# length and every element — defeating any length- or membership-level reading of
# the clause — while still corrupting the stored configuration.
_RIV_ALPHAS_REVERSED = _swap(_BASE, _A_ALPHAS, "alphas := alphas.reverse,")


def _wit(args, note):
    """Refutation witness: `¬ problem_spec … (implementation … args)` at a
    concrete literal input, closed by `decide`. `args` is the seven Lean argument
    atoms as one string. Elaborates against a rival that diverges from the frozen
    verdict there; fails on gold (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_initClassifierCV {args}\n"
        f"    (implementation_initClassifierCV {args}) := by\n"
        f"  unfold problem_spec_initClassifierCV implementation_initClassifierCV\n"
        f"  decide"
    )


# Common baseline: alphas=[] fitIntercept=false normalize=false scoring=none
# cv=none classWeight=none storeCvValues=false. Each witness varies exactly ONE
# binder to a value where its rival diverges from gold, so the eight witnesses
# probe eight DISTINCT input points (pts=8) and every binder is discriminated.
# AUDIT NOTE on the frame-field refinement arguments. The ported battery shared
# one _P2P_NOTE across the fitIntercept / normalize / scoring / cv rivals,
# asserting that "the PASS_TO_PASS ridge suite constructs RidgeClassifierCV with
# these options and asserts on the fitted estimator". That was checked against
# the harness lists and the base test file and it is FALSE: across every listed
# FAIL_TO_PASS + PASS_TO_PASS test, the only keyword arguments ever passed to
# this constructor are `alphas` and `class_weight`. The two listed tests that
# build it (the class-weight cross-validation pair) leave fitIntercept, normalize,
# scoring and cv at their defaults, and the one test that does pass a splitter
# selection is not in either harness list. So a rival that regresses one of those
# four options is NOT observable through this instance's harness, and claiming it
# is would be exactly the "rationale claims a sub-domain the manifest never
# demonstrates" defect. The honest argument below is a SPEC-CONTRACT one, which is
# what these four rivals actually defend, and it is stated as such rather than
# borrowing F2P/P2P authority it does not have.
_P2P_NOTE = (  # shared refinement clause for the frame (non-retention) fields.
    "REFINEMENT SCOPE (measured, not assumed): this option is already forwarded "
    "correctly at base, and no listed FAIL_TO_PASS or PASS_TO_PASS test passes it "
    "to the constructor — the only keyword arguments any listed test supplies are "
    "the regularization grid and the per-class weighting, so a regression in THIS "
    "option is not observable through this instance's harness. Its refutation is "
    "therefore attributable to the frozen postcondition, not to a test: the "
    "modeled behaviour is verbatim option storage over the WHOLE input domain "
    "(G-PANEL-2 confirmed the real constructor stores each argument with no "
    "validation or transformation), so an impl that pins this field to a constant "
    "disagrees with the modeled callee at every input where the caller supplies "
    "anything else. A verifying rival would mean the spec had stopped pinning a "
    "field it explicitly claims to pin — a spec break, which is what this gate is "
    "for. The verify-does-not-imply-resolve break is carried by the retention and "
    "alphas rivals, whose refinement arguments are grounded in the actual tests."
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-single-record",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SINGLE,
        "rationale": (
            "Structurally-different but CORRECT impl: every option (classWeight "
            "included) is recorded in ONE record literal instead of a base config "
            "plus a second overwrite step. The result value is identical on every "
            "input; only the construction form changes. The frozen theorem "
            "statement and proof body are kept byte-identical (the 7-fold `rfl` "
            "still closes). Defends all seven conjuncts. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNCTIONAL,
        "rationale": (
            "A more structurally-different CORRECT impl: a pure functional `def` "
            "(no `Id.run do`, no mutable state) returning the record directly. "
            "Behaviourally identical; the frozen proof still closes after "
            "unfolding. Shows the postcondition is not over-fit to the imperative "
            "construction shape. If it FAILS => SPEC-TOO-STRONG. AUDIT NOTE: like "
            "pos-single-record, this impl is DEFINITIONALLY equal to the frozen one "
            "— it keeps the frozen 7-fold `rfl` proof and still verifies, which is "
            "precisely the statement that the kernel sees no difference. So it is an "
            "honest positive but a weak one; pos-branch-on-flag was added to cover "
            "the case a reshape actually has to be REPROVEN."
        ),
    },
    {
        "id": "pos-branch-on-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH,
        "rationale": (
            "ADDED BY AUDIT. The first positive here that is NOT definitionally "
            "equal to the frozen impl: it branches on the retention flag and stores "
            "a literal in each arm (the shape a patch takes when it threads the flag "
            "through a conditional instead of forwarding it), so the frozen `rfl` "
            "script does not close it and the case must REPROVE the obligation by "
            "case analysis on that Bool. Measured: with the frozen proof the build "
            "fails with an `Application type mismatch` on the storeCvValues "
            "conjunct; with `cases storeCvValues <;> simp` it verifies. The variant "
            "adds no axiom, no sorry and no new theorem, and the obligation "
            "STATEMENT is byte-identical — only the tactic body differs, which the "
            "scope rules explicitly permit. This is what shows the postcondition is "
            "satisfiable by a correct impl of a genuinely different shape rather "
            "than by a syntactic rearrangement of the same term. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "adm-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISSIBILITY,
        "rationale": (
            "ADDED BY THE SECOND AUDIT — the ADMISSIBILITY lane, which both the "
            "port and the first audit dropped as N/A on the ground that the frozen "
            "obligation carries no precondition hypothesis. That is the wrong test: "
            "on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a "
            "positive that discharges it at that concrete input tests directly. "
            "Every other case here closes the obligation SYMBOLICALLY, so nothing "
            "in the battery ever evaluates the postcondition at a real input. This "
            "one does: it proves the postcondition, by evaluation, at the input "
            "shape the new test constructs (a three-entry regularization grid, "
            "intercept fitted, retention REQUESTED, no scorer/splitter/weighting "
            "selection), as a `have`, and only then closes the frozen obligation "
            "with the frozen proof body verbatim. The obligation STATEMENT is "
            "byte-identical and no axiom, sorry or new theorem is added — only the "
            "tactic body is extended, which the scope rules permit. MEASURED: "
            "`decide` and `rfl` both FAIL on this goal (the Rat `Decidable` "
            "instance does not reduce), `simp` closes it, so the tactic genuinely "
            "evaluates rather than matching syntactically. NOT A TAUTOLOGY, and "
            "this is the part that matters: two negative controls — a `have` whose "
            "claimed retention flag contradicts the one handed to the impl, and one "
            "whose claimed grid contradicts it — BOTH fail with `unsolved goals "
            "⊢ False`. A `have` that closed no matter what it claimed would have "
            "closed those. If this case FAILS => PRECOND-TOO-STRONG (the "
            "postcondition would be unsatisfiable at a normal, test-shaped input)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) — one per pinned field ----
    {
        "id": "weak-alphas-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALPHAS,
        "refinement": (
            "Hard-coding the regularization grid to the empty list ignores the "
            "supplied `alphas`. The FAIL_TO_PASS test constructs "
            "RidgeClassifierCV(alphas=[1e-1,1e0,1e1], store_cv_values=True) and "
            "asserts r.cv_values_.shape == (n_samples, n_targets, n_alphas) with "
            "n_alphas == len(alphas) == 3; a constructor that drops the alphas "
            "forwarding yields the wrong trailing axis and FAILS that assertion, "
            "so it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the clause result.alphas = alphas. Attacks the alphas "
            "binder / the alphas conjunct. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit("[1] false false none none none false",
                        "alphas=[1]: gold stores [1], rival stores []"),
    },
    {
        "id": "weak-fitIntercept-forced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIT,
        "refinement": (
            "Hard-coding the intercept flag to a constant ignores the supplied "
            "`fitIntercept`. " + _P2P_NOTE
        ),
        "rationale": (
            "REJECTED by the clause result.fitIntercept = fitIntercept. Attacks "
            "the fitIntercept binder / the fitIntercept conjunct. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _wit("[] true false none none none false",
                        "fitIntercept=true: gold stores true, rival stores false"),
    },
    {
        "id": "weak-normalize-forced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NORM,
        "refinement": (
            "Hard-coding the normalize flag to a constant ignores the supplied "
            "`normalize`. " + _P2P_NOTE
        ),
        "rationale": (
            "REJECTED by the clause result.normalize = normalize. Attacks the "
            "normalize binder / the normalize conjunct. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit("[] false true none none none false",
                        "normalize=true: gold stores true, rival stores false"),
    },
    {
        "id": "weak-scoring-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SCORING,
        "refinement": (
            "Hard-coding the scorer selection to absent ignores the supplied "
            "`scoring`. " + _P2P_NOTE
        ),
        "rationale": (
            "REJECTED by the clause result.scoring = scoring. Attacks the scoring "
            "binder / the scoring conjunct. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit("[] false false (some 0) none none false",
                        "scoring=some 0: gold stores some 0, rival stores none"),
    },
    {
        "id": "weak-cv-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CV,
        "refinement": (
            "Hard-coding the cross-validation splitter selection to absent ignores "
            "the supplied `cv`. " + _P2P_NOTE
        ),
        "rationale": (
            "REJECTED by the clause result.cv = cv. Attacks the cv binder / the cv "
            "conjunct. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit("[] false false none (some 0) none false",
                        "cv=some 0: gold stores some 0, rival stores none"),
    },
    {
        "id": "weak-classWeight-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CW,
        "refinement": (
            "Forcing the per-class weighting selection to absent ignores the "
            "supplied `classWeight`. The PASS_TO_PASS suite exercises "
            "RidgeClassifierCV with a class_weight selection (the class-weight "
            "cross-validation tests); a constructor that drops it corrupts the "
            "stored configuration and fails PASS_TO_PASS, so it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the clause result.classWeight = classWeight. Attacks the "
            "classWeight binder / the classWeight conjunct. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit("[] false false none none (some 0) false",
                        "classWeight=some 0: gold stores some 0, rival stores none"),
    },
    {
        "id": "weak-storeCvValues-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STORE_IGNORE,
        "refinement": (
            "Hard-coding retention to always-on ignores the caller's request "
            "(nagini's constant-flag defect, attacked from the always-True side). "
            "Whenever the caller passes store_cv_values=False the configured "
            "estimator would retain against the request, so the estimator's "
            "store_cv_values no longer echoes the requested value. This is the "
            "TRUE NEAR-MISS of the pair: constant-true agrees with gold exactly on "
            "the sub-domain the FAIL_TO_PASS exercises (it requests retention), so "
            "it is refutable only at store_cv_values=False, and the witness is "
            "stated there. AUDIT NOTE on observability, measured against the "
            "harness rather than assumed: the ported text said this breaks 'the "
            "estimator contract the PASS_TO_PASS suite depends on', but no listed "
            "test passes this option to the constructor, so at the default (False) "
            "a constant-true rival is not caught by a listed assertion on the "
            "stored flag. It is still a REAL defect and correctly rejected: it "
            "contradicts the modeled verbatim-storage behaviour on half the boolean "
            "domain, and it also forces retention on for a caller that supplies a "
            "splitter selection, a combination the real fit path refuses outright "
            "rather than storing — so the always-on rival converts a legal default "
            "construction into one whose later fit raises. The clause is what "
            "rejects it, and that is the attribution claimed here."
        ),
        "rationale": (
            "REJECTED by the load-bearing clause result.storeCvValues = "
            "storeCvValues, which must hold for ALL inputs, including False. "
            "Attacks the storeCvValues binder at storeCvValues=false — the ONLY "
            "point where this rival is refutable, since it agrees with gold at "
            "true. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # at false: gold stores false, rival (constant true) stores true.
        "witness": _wit("[] false false none none none false",
                        "storeCvValues=false: gold stores false, rival stores true"),
    },
    {
        "id": "weak-storeCvValues-negated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STORE_NEGATE,
        "refinement": (
            "Forwarding the NEGATION of store_cv_values is the opposite of the "
            "gold forwarding: the estimator would retain iff the caller asked it "
            "NOT to. The FAIL_TO_PASS test sets store_cv_values=True and asserts "
            "r.cv_values_ exists and is rank-3; with retention negated, cv_values_ "
            "is never populated when requested -> the test fails, so it would NOT "
            "resolve. Refuted at storeCvValues=TRUE, the input the FAIL_TO_PASS "
            "actually exercises, and a DISTINCT point from the ignore rival's "
            "(which is refuted at False). AUDIT CORRECTION: the ported text called "
            "this the near-miss, claiming 'the negation agrees with gold when the "
            "flag is False'. That is wrong in both directions and was corrected "
            "rather than carried over — negation disagrees with gold at BOTH "
            "boolean values (!false = true ≠ false, !true = false ≠ true), so this "
            "rival has no agreement sub-domain at all. The genuine near-miss is the "
            "constant-true IGNORE rival, which agrees with gold exactly at "
            "storeCvValues=True and is therefore refutable ONLY at False; that is "
            "why the two rivals must be refuted at the two distinct points they are."
        ),
        "rationale": (
            "REJECTED by the clause result.storeCvValues = storeCvValues, violated "
            "for every boolean value under negation. Attacks the storeCvValues "
            "binder at storeCvValues=true (distinct from the ignore rival's point). "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # at true: gold stores true, rival (negation) stores false.
        "witness": _wit("[] false false none none none true",
                        "storeCvValues=true: gold stores true, rival stores false"),
    },

    # ---- rivals ADDED BY AUDIT: the near-miss shapes the port left unattacked --
    {
        "id": "weak-storeCvValues-dropped-when-cv-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STORE_PARTIAL,
        "refinement": (
            "PARTIAL-DOMAIN retention. This rival forwards the retention selection "
            "faithfully whenever no splitter selection is supplied, and forces it "
            "off when one is — treating 'this option is only meaningful together "
            "with cv absent' as licence to discard it rather than to record it. It "
            "agrees with gold on the ENTIRE cv-absent sub-domain, which includes "
            "every input the FAIL_TO_PASS exercises (that test requests retention "
            "and leaves the splitter at its default), so unlike every constant "
            "rival it would pass the new test and every listed PASS_TO_PASS. That "
            "is exactly why it belongs here: the spec, not the harness, is what "
            "must reject it. It is still a faithful-patch defect rather than a "
            "reshape, because the real constructor stores each option verbatim and "
            "unconditionally — the incompatible combination is diagnosed later, at "
            "fit time, by raising, which a constructor that silently rewrote the "
            "request to False would convert into a wrong silent result. So the "
            "modeled callee and this rival genuinely disagree, at a real input a "
            "caller can supply."
        ),
        "rationale": (
            "REJECTED by result.storeCvValues = storeCvValues, which pins the field "
            "UNCONDITIONALLY — the clause holds for all inputs, not merely for "
            "those with the splitter selection absent. Attacks the storeCvValues "
            "binder in its INTERACTION with the cv binder, the one two-binder "
            "interaction in this battery; the witness is stated at the only kind of "
            "input where the rival diverges (cv present AND retention requested). "
            "If it VERIFIES => SPEC-TOO-WEAK (the clause would be conditional in "
            "effect while claiming to be unconditional)."
        ),
        "witness": _wit("[] false false none (some 0) none true",
                        "cv=some 0 & storeCvValues=true: gold stores true, "
                        "rival drops it to false"),
    },
    {
        "id": "weak-scoring-cv-cross-wired",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP_SCORING_CV,
        "refinement": (
            "CROSS-WIRING, not dropping: this rival records the scorer selection "
            "into the splitter field and vice versa. Every supplied value is still "
            "stored — nothing is defaulted, discarded, or forced — so the stored "
            "multiset of options is identical to gold's, and any weaker reading of "
            "the postcondition ('each option was recorded somewhere') would admit "
            "it. This is a realistic transcription defect for a constructor whose "
            "forwarding is a long argument list, and it is the shape a faithful "
            "patch produces by misordering two arguments while adding a third. Its "
            "real effect is severe and silent: the splitter field selects the "
            "cross-validation strategy, so a construction that lands a scorer "
            "identity there changes which fit path runs. Not observable through "
            "this instance's listed tests (neither option is passed by any of "
            "them), so its refutation is attributable to the frozen postcondition — "
            "which is the claim being tested."
        ),
        "rationale": (
            "REJECTED by the CONJUNCTION of result.scoring = scoring and "
            "result.cv = cv: each conjunct pins its field to its OWN binder, so "
            "storing the right values in the wrong fields violates both. This is "
            "the only rival that probes the field-to-binder CORRESPONDENCE rather "
            "than the presence of a value, and it agrees with gold on the whole "
            "diagonal scoring = cv, so the witness is stated off it. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec would pin the set of stored "
            "options without pinning which option went where)."
        ),
        "witness": _wit("[] false false (some 0) none none false",
                        "scoring=some 0, cv=none: gold stores (some 0, none), "
                        "rival stores (none, some 0)"),
    },
    {
        "id": "weak-alphas-reordered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALPHAS_REVERSED,
        "refinement": (
            "The regularization grid is stored as an ORDER-PRESERVING sequence "
            "(mapping.md records it verbatim), and its order is observable "
            "downstream: the retained cross-validation values carry one entry per "
            "regularization strength in the grid's order, so a permuted grid "
            "silently mislabels which retained column belongs to which strength "
            "while keeping the shape assertion the FAIL_TO_PASS makes intact. A "
            "reversing rival keeps the grid's LENGTH and every one of its elements, "
            "so it defeats any length-level or membership-level reading of the "
            "clause that the empty-list rival alone would leave open, and the "
            "selected-strength readback a caller performs would name the wrong "
            "value. A faithful patch that reordered the grid while forwarding the "
            "new option would therefore corrupt the estimator's stored "
            "configuration and not resolve."
        ),
        "rationale": (
            "REJECTED by result.alphas = alphas, which is LIST equality and "
            "therefore order-sensitive, not multiset or length equality. Attacks "
            "the alphas binder on its ORDER rather than its presence — the "
            "dimension weak-alphas-dropped cannot reach, since emptying the list "
            "would also be caught by a length-only spec. Refuted at a grid whose "
            "reversal differs from it, so the witness needs at least two distinct "
            "entries. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit("[1, 2] false false none none none false",
                        "alphas=[1,2]: gold stores [1,2], rival stores [2,1]"),
    },
]


# No @ContractOnly axioms and no opaque callees: the parent initializer's
# per-option storage is modeled DIRECTLY as field storage, so the axiom lane is
# vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
