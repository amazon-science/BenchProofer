# properties.py — G-PBT falsification battery for django__django-14493 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   postProcess : (maxPasses : Nat) → (passSubst : Nat → Bool) → Option Bool
#   The outcome of a bounded refinement loop: a flag is set before the loop, then
#   overwritten once per pass with that pass's substitution outcome, and the loop
#   stops at the first pass that produces none. The single postcondition pins the
#   result to the EXACT grounded closed form
#       result = some (passLoopResult (List.range maxPasses) passSubst false)
#   where passLoopResult is a total, transparent front-recursive fold over the
#   configuration. Two things it pins jointly:
#     (D) DEFINEDNESS — the result is `some _` for EVERY configuration, including
#         the empty one (maxPasses = 0): the flag always carries a value.
#     (V) VALUE — that value is the loop's running flag: false when zero passes run,
#         and the outcome of the first no-substitution pass on early termination.
#   Because the oracle is a total transparent fold (no opaque callee, no answer-key),
#   `decide` computes it at any literal configuration — witnesses need no
#   conditioning on the carrier.
#
# CARRIER NOTE: the nagini sibling abstracted the same loop to a @Pure fold
# all_changed over a List[int] of per-pass outcomes behind fractional read
# permission, carrying the "flag undefined on the zero-pass path" as a Nagini
# definite-assignment failure. This backend models the identical decision over a
# transparent (Nat → Bool) per-pass oracle and lifts the flag's definedness into the
# result type Option Bool: `some b` = the flag holds b, `none` = the flag holds no
# value (the UnboundLocal state). So the two LOAD-BEARING nagini clauses map here to
#   * nagini Q2 (the grounded running-flag value)      -> clause (V);
#   * nagini Q3 (the zero-pass boundary is a definite value, never absent)
#       -> the conjunction of (D) [some _, not none] and (V) [that value is false].
# Every clause the nagini battery attacked has a direct counterpart, and each is
# refutable at a concrete literal configuration.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's mandatory class: pass_changed was
#     Acc(list_pred(...),1/2) read-only, and the rival wrote back into it). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a "store
#     into a read-only input" rival is not expressible and the whole lane is VACUOUS
#     here. See 'assessment'.
#   * (none — see ADMISSIBILITY below, which DOES port.)
#
# ADMISSIBILITY DOES PORT (adm-f2p-zero-pass). The lean obligation carries no
# precondition hypothesis, but "no precondition" is not the same as "nothing to
# test": the analogue of PRECOND-TOO-STRONG on a total carrier is the obligation
# being UNSATISFIABLE at exactly the configuration the failing scenario exercises.
# The nagini admiss-reads control defended the half-permission precondition over a
# normal F2P-shaped input; here the counterpart discharges the obligation at the
# concrete F2P-shaped configuration (the zero-pass one, maxPasses = 0) by
# EVALUATION, as a `have`, before closing the frozen obligation verbatim. If the
# spec pinned an unreachable value there — a result no impl of this signature can
# produce at that configuration — that `have` would fail while the rest of the
# battery still passed, which is the direction nothing else in this manifest tests.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. The loop is
#     modeled DEEPLY over the transparent carrier, so there is no consumed axiom.
from pathlib import Path

INSTANCE = "django__django-14493"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). ------------------------------------------------------------
_INIT = "  let mut substitutions : Option Bool := some false\n"
_STORE_BREAK = (
    "    let subst := passSubst i\n"
    "    substitutions := some subst\n"
    "    if ! subst then\n"
    "      break\n"
)
_STORE_LINE = "    substitutions := some subst\n    if ! subst then\n"
_IMPL_BODY = (
    "  let mut substitutions : Option Bool := some false\n"
    "  for i in List.range maxPasses do\n"
    "    let subst := passSubst i\n"
    "    substitutions := some subst\n"
    "    if ! subst then\n"
    "      break\n"
    "  return substitutions"
)
for _a in (_INIT, _STORE_BREAK, _STORE_LINE, _IMPL_BODY):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The frozen proof body (the tactic lines inside proof-start/proof-end). The reshape
# positive keeps this verbatim (its loop shape is proof-compatible); the direct
# positive replaces it with a shorter honest reproof (statement kept byte-identical).
_PROOF = (
    "  intro maxPasses passSubst\n"
    "  have helper : ∀ (is : List Nat) (cur : Bool),\n"
    "      Id.run (forIn is (some cur) (fun i r =>\n"
    "        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))\n"
    "        else do\n"
    "          pure PUnit.unit\n"
    "          pure (ForInStep.yield (some (passSubst i))))) =\n"
    "        some (passLoopResult is passSubst cur) := by\n"
    "    intro is\n"
    "    induction is with\n"
    "    | nil => intro cur; rfl\n"
    "    | cons a as ih =>\n"
    "      intro cur\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      by_cases h : passSubst a = true\n"
    "      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,\n"
    "          if_false, ih, if_true]\n"
    "      · simp only [Bool.not_eq_true] at h\n"
    "        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,\n"
    "          if_false]\n"
    "        rfl\n"
    "  unfold problem_spec_postProcess implementation_postProcess\n"
    "  exact helper (List.range maxPasses) false"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reshape-inline: structurally DIFFERENT but behaviourally identical. The per-pass
# `let subst := passSubst i` binding is DROPPED and its two uses inlined — the flag is
# assigned `some (passSubst i)` and the early-break guard tests `! (passSubst i)`
# directly. Same value on every path; only the binding form changes, a shape a
# faithful patch could equally take. The elaborated forIn body is identical (the `let`
# was inlined by the do-block anyway), so the frozen `correct_postProcess` proof body
# closes verbatim (no new axiom/lemma/sorry; the theorem STATEMENT is byte-identical).
# If it FAILS => SPEC-TOO-STRONG (a faithful, structurally-different correct impl
# rejected because the postcondition is over-fit to one binding form).
_POS_RESHAPE = _swap(
    _BASE,
    "    let subst := passSubst i\n    substitutions := some subst\n    if ! subst then\n",
    "    substitutions := some (passSubst i)\n    if ! (passSubst i) then\n",
)
assert _POS_RESHAPE != _BASE, "pos-reshape did not rewrite"

# pos-direct: the cheapest HONEST impl. The postcondition oracle passLoopResult is
# GROUNDED in the arguments (a total transparent fold), so directly returning
# `some (passLoopResult (List.range maxPasses) passSubst false)` is a fully-grounded
# correct implementation, not an ungrounded-oracle echo — there is no WRONG constant
# an echo could carry (a wrong constant fails the postcondition). The proof collapses
# to `rfl` after unfolding (the Id.run of a pure value). MUST verify (the
# postcondition is literally `result = some (passLoopResult …)`); else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE, _IMPL_BODY,
        "  some (passLoopResult (List.range maxPasses) passSubst false)",
    ),
    _PROOF,
    "  intro maxPasses passSubst\n"
    "  unfold problem_spec_postProcess implementation_postProcess\n"
    "  rfl",
)
assert _POS_DIRECT != _BASE, "pos-direct did not rewrite"

# pos-closed-form: a correct reshape that is NOT definitionally equal to the frozen
# impl. Both other positives keep (or trivially collapse to) the frozen fold: the
# reshape's elaborated forIn body is the frozen one, and pos-direct returns the
# oracle term itself. This one computes the same value by a genuinely different
# route — `(List.range maxPasses).all passSubst`, guarded on the empty
# configuration — so closing the frozen obligation needs a NEW inductive bridge
# (`passLoopResult is f cur = if is = [] then cur else is.all f`) rather than the
# frozen tactic script. That is the honest test of SPEC-TOO-STRONG: a faithful impl
# whose proof does not reuse the frozen one. If it FAILS => SPEC-TOO-STRONG (the
# postcondition admits only impls shaped like the frozen fold).
_POS_CLOSED = _swap(
    _swap(
        _BASE, _IMPL_BODY,
        "  some (if maxPasses = 0 then false else (List.range maxPasses).all passSubst)",
    ),
    _PROOF,
    "  intro maxPasses passSubst\n"
    "  have key : ∀ (is : List Nat) (cur : Bool),\n"
    "      passLoopResult is passSubst cur = "
    "(if is = [] then cur else is.all passSubst) := by\n"
    "    intro is\n"
    "    induction is with\n"
    "    | nil => intro cur; simp [passLoopResult]\n"
    "    | cons a as ih =>\n"
    "      intro cur\n"
    "      by_cases h : passSubst a = true\n"
    "      · cases as with\n"
    "        | nil => simp [passLoopResult, h]\n"
    "        | cons c cs =>\n"
    "          rw [passLoopResult]\n"
    "          simp only [h, if_true]\n"
    "          rw [ih true]\n"
    "          simp [h]\n"
    "      · simp only [Bool.not_eq_true] at h\n"
    "        simp [passLoopResult, h]\n"
    "  unfold problem_spec_postProcess implementation_postProcess\n"
    "  rw [key]\n"
    "  simp only [Id.run]\n"
    "  congr 1\n"
    "  cases maxPasses with\n"
    "  | zero => simp\n"
    "  | succ n => simp [List.range_succ]",
)
assert _POS_CLOSED != _BASE, "pos-closed-form did not rewrite"

# adm-f2p-zero-pass: the ADMISSIBILITY positive. Keeps the frozen impl AND the frozen
# proof body verbatim, prefixing two `have`s that discharge the obligation at the
# concrete configuration the failing scenario exercises (the zero-pass one), by
# EVALUATION rather than by the frozen script: that the postcondition is SATISFIABLE
# there, and that the value it pins at that configuration is the defined `some false`.
# On a total carrier this is the PRECOND-TOO-STRONG analogue — if the spec pinned a
# value unreachable at exactly that configuration, these `have`s would fail while
# every other case in this battery still behaved as declared.
_ADM_F2P = _swap(
    _BASE, _PROOF,
    "  -- Admissibility at the F2P-shaped configuration: the obligation must be\n"
    "  -- SATISFIABLE at exactly the zero-pass configuration the failing scenario\n"
    "  -- exercises, and the value it pins there must be a DEFINED one. Both are\n"
    "  -- discharged by evaluation, as `have`s, before the frozen obligation is\n"
    "  -- closed verbatim below.\n"
    "  have f2p_satisfiable :\n"
    "      problem_spec_postProcess 0 (fun _ => false)\n"
    "        (implementation_postProcess 0 (fun _ => false)) := by\n"
    "    unfold problem_spec_postProcess implementation_postProcess\n"
    "    decide\n"
    "  have f2p_defined : "
    "implementation_postProcess 0 (fun _ => false) = some false := by\n"
    "    unfold implementation_postProcess\n"
    "    decide\n"
    + _PROOF,
)
assert _ADM_F2P != _BASE, "adm-f2p-zero-pass did not rewrite"


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# elaborates against the rival and FAILS on the frozen solution.
# ===========================================================================

# weak-zero-init: initialise the flag to `some true` instead of `some false`. On any
# configuration with maxPasses = 0 the loop never runs and the pre-loop value stands,
# so the rival returns `some true` where the closed form (running the empty pass list
# from `false`) is `some false`. This is the EXACT zero-pass sub-domain the whole task
# turns on — the spurious "still substituting" verdict on the empty configuration.
_RIV_ZERO = _swap(_BASE, _INIT,
                  "  let mut substitutions : Option Bool := some true\n")
assert _RIV_ZERO != _BASE, "weak-zero-init did not rewrite"

# weak-early-true: store `some true` each pass regardless of that pass's outcome
# (`substitutions := some true`), keeping the early break on `!subst`. On a
# configuration whose first pass produces NO substitutions the loop breaks with the
# flag pinned to `some true`, but the closed form is `some false` there (the fold
# returns the no-substitution pass's own value). Attacks the running-flag VALUE / the
# per-pass passSubst dependence.
_RIV_EARLY = _swap(_BASE, _STORE_LINE,
                   "    substitutions := some true\n    if ! subst then\n")
assert _RIV_EARLY != _BASE, "weak-early-true did not rewrite"

# weak-no-break: delete the early-termination break, so every configured pass runs
# and the flag ends at the LAST pass's outcome. On a configuration that produces a
# substitution-free pass followed by a substituting pass, the loop should stop at the
# first (flag `some false`) but the rival runs on and reports the later pass's `some
# true`. Attacks the early-termination semantics / the passSubst dependence across
# indices.
_RIV_NOBREAK = _swap(
    _BASE, _STORE_BREAK,
    "    let subst := passSubst i\n    substitutions := some subst\n",
)
assert _RIV_NOBREAK != _BASE, "weak-no-break did not rewrite"

# weak-prepatch: the LITERAL pre-patch defect — initialise the flag to `none` (no
# value) so it carries a value only if the loop body assigns one. On maxPasses = 0 the
# loop never runs and the result is `none`, whereas the spec demands `some false`. In
# the repo this is the local read before assignment (UnboundLocalError). Attacks the
# DEFINEDNESS clause (some _ vs none) at the zero-pass boundary — the strongest
# refinement (it is the unchanged repo). Carries the strongest refinement.
_RIV_PRE = _swap(_BASE, _INIT,
                 "  let mut substitutions : Option Bool := none\n")
assert _RIV_PRE != _BASE, "weak-prepatch did not rewrite"

# weak-undefined-nonzero: DEFINEDNESS attacked away from the zero-pass boundary. Every
# other definedness rival here (weak-prepatch) diverges only at maxPasses = 0, so the
# (D) clause is probed at exactly one point of the maxPasses binder and a spec that
# pinned `some _` ONLY at the empty configuration would survive the whole battery. This
# rival keeps the flag defined on the empty configuration and on every early-stop path
# — so weak-prepatch's witness does NOT refute it — and drops it to `none` on the path
# where a pass DOES produce substitutions. Closes the (D)-at-nonzero binder point.
_RIV_UNDEF_NZ = _swap(
    _BASE, _STORE_LINE,
    "    substitutions := if subst then none else some subst\n    if ! subst then\n",
)
assert _RIV_UNDEF_NZ != _BASE, "weak-undefined-nonzero did not rewrite"


def _wit(maxp, fexpr, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal configuration, closed by `decide`. `maxp` is the maxPasses literal and
    `fexpr` a total (Nat → Bool). Elaborates against a rival that diverges from the
    frozen verdict there, and fails on gold (which satisfies the spec everywhere)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_postProcess {maxp} ({fexpr})\n"
        f"    (implementation_postProcess {maxp} ({fexpr})) := by\n"
        f"  unfold problem_spec_postProcess implementation_postProcess\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reshape-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": (
            "structurally-different but CORRECT impl: the per-pass `let subst := "
            "passSubst i` binding is dropped and its uses inlined — the flag is assigned "
            "some (passSubst i) and the break guard tests ! (passSubst i) directly. Same "
            "value on every path; only the binding form changes. The elaborated forIn "
            "body is identical, so the frozen `correct_postProcess` proof body closes "
            "verbatim (theorem STATEMENT byte-identical, no new axiom/lemma/sorry). If "
            "it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one binding form)."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition oracle passLoopResult is GROUNDED in the arguments (a "
            "total transparent fold), so `implementation := some (passLoopResult "
            "(List.range maxPasses) passSubst false)` is the honest cheapest CORRECT "
            "impl, not an ungrounded echo; the proof collapses to `rfl` after unfold. "
            "Must verify (the postcondition is literally result = some (passLoopResult "
            "…)); else SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable: any "
            "WRONG constant fails the postcondition."
        ),
    },

    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CLOSED,
        "rationale": (
            "a correct reshape that is NOT definitionally equal to the frozen impl, "
            "which is what the other two positives cannot show: pos-reshape-inline's "
            "elaborated forIn body IS the frozen one (the do-block inlines the let) and "
            "pos-direct returns the oracle term itself, so both close under the frozen "
            "tactic script or a bare rfl. This one computes the same value by a "
            "different route — (List.range maxPasses).all passSubst, guarded on the "
            "empty configuration — and closing the frozen obligation therefore needs a "
            "NEW inductive bridge (passLoopResult is f cur = if is = [] then cur else "
            "is.all f) rather than the frozen script. If it FAILS => SPEC-TOO-STRONG "
            "(the postcondition admits only impls shaped like the frozen fold)."
        ),
    },
    {
        "id": "adm-f2p-zero-pass",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": (
            "the PRECOND-TOO-STRONG analogue on a total carrier. The obligation has no "
            "precondition hypothesis to be too strong, so the direction that remains "
            "testable is whether the obligation is SATISFIABLE at exactly the "
            "configuration the failing scenario exercises — the zero-pass one. Keeps "
            "the frozen impl and the frozen proof body VERBATIM and prefixes two "
            "`have`s discharged by EVALUATION at that concrete configuration: that the "
            "postcondition holds there, and that the value it pins there is the DEFINED "
            "some false rather than none. If the spec pinned a value unreachable at "
            "that configuration these would fail while every uniqueness case still "
            "behaved as declared, so this is the only case in the battery that senses "
            "that direction. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-zero-init",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ZERO,
        "refinement": (
            "initialising the flag to true is the pre-change-shaped spurious verdict on "
            "the empty configuration: in the repo it makes the post-loop test report "
            "'bound reached' and raise even when zero passes were configured. It fails "
            "the F2P (the zero-pass storage class), which runs the full collection and "
            "asserts it completes ('post-processed' in output) with NO spurious "
            "'exceeded' error. A faithful patch that seeded the flag with the "
            "no-convergence value does NOT resolve — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition VALUE clause at the zero-pass boundary: on "
            "maxPasses = 0 the loop never runs, the pre-loop value stands, and the "
            "rival returns some true where the closed form is some false. Attacks the "
            "running-flag value / the maxPasses = 0 sub-domain of the maxPasses binder. "
            "If it VERIFIES => SPEC-TOO-WEAK (the zero-pass boundary, the whole bug, is "
            "unpinned)."
        ),
        # maxPasses=0: gold => some false, rival (init some true) => some true.
        "witness": _wit("0", "fun _ => true",
                        "zero passes: gold some false, rival some true"),
    },
    {
        "id": "weak-early-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EARLY,
        "refinement": (
            "storing true every pass while still breaking on a no-substitution pass is "
            "what a real patch that reported 'bound reached' even after the loop settled "
            "on a substitution-free pass would do — it emits the spurious error whenever "
            "post-processing converges early, breaking the normal multi-pass paths that "
            "settle before the pass cap. Does NOT resolve — verify-does-not-imply-"
            "resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition VALUE clause: with maxPasses = 1 and a pass "
            "that produces no substitutions, the loop breaks with the flag pinned to "
            "some true, but the closed form is some false (the fold returns the "
            "no-substitution pass's own value). Attacks the running-flag value / the "
            "passSubst per-pass dependence. If it VERIFIES => SPEC-TOO-WEAK (the "
            "early-stop value is unpinned)."
        ),
        # maxPasses=1, passSubst const false: gold => some false, rival => some true.
        "witness": _wit("1", "fun _ => false",
                        "one no-substitution pass: gold some false, rival some true"),
    },
    {
        "id": "weak-no-break",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOBREAK,
        "refinement": (
            "deleting the early termination makes every configured pass run and the "
            "flag end at the LAST pass's outcome, ignoring that an earlier pass already "
            "reached a fixpoint. A patch that dropped the convergence break would keep "
            "re-processing settled files and report the wrong terminal flag, diverging "
            "from the post-change loop on any configuration that settles before the cap. "
            "Does NOT resolve — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition VALUE clause: with maxPasses = 2 and a "
            "no-substitution pass at index 0 followed by a substituting pass at index "
            "1, the fold stops at the first pass (some false) but the rival runs on and "
            "returns the later pass's some true. Attacks the early-termination semantics "
            "/ the passSubst dependence ACROSS indices (a distinct binder point from "
            "weak-early-true, which uses a single pass). If it VERIFIES => "
            "SPEC-TOO-WEAK (early convergence is unpinned)."
        ),
        # maxPasses=2, passSubst = [false, true]: gold => some false, rival => some true.
        "witness": _wit("2", "fun i => decide (i = 1)",
                        "no-subst then subst pass: gold some false, rival some true"),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PRE,
        "refinement": (
            "this IS the pre-patch behaviour (the unchanged repo): the flag carries no "
            "value entering the loop, so on the empty configuration the post-loop read "
            "hits a variable that was never assigned — the exact UnboundLocalError in "
            "the issue. It fails the F2P (the zero-pass storage must complete the "
            "collection). Does NOT resolve — the precise change the spec senses "
            "(G-DIFF), the strongest refinement."
        ),
        "rationale": (
            "REJECTED by the postcondition DEFINEDNESS clause: with the flag seeded to "
            "none, on maxPasses = 0 the loop never runs and the result is none, whereas "
            "the spec pins some false for every configuration. Attacks definedness "
            "(some _ vs none) at the zero-pass boundary of the maxPasses binder. If it "
            "VERIFIES => SPEC-TOO-WEAK (the well-definedness the whole task is about is "
            "unpinned)."
        ),
        # maxPasses=0: gold => some false, prepatch (init none) => none.
        "witness": _wit("0", "fun _ => false",
                        "zero passes: gold some false, prepatch none"),
    },
    {
        "id": "weak-undefined-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNDEF_NZ,
        "refinement": (
            "a flag that carries no value on precisely the path where a pass DID still "
            "produce substitutions is the same defect class as the zero-pass one, "
            "displaced: the post-loop test reads a value that was never established on "
            "the very path that is supposed to report 'still substituting'. It leaves "
            "the zero-pass configuration and every early-stop path correct, so it passes "
            "the F2P-shaped zero-pass scenario and breaks the ordinary multi-pass paths "
            "instead ('post_processing behaves correctly' among them). Does NOT resolve "
            "— verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition DEFINEDNESS clause at a NONZERO "
            "configuration: with maxPasses = 1 and a pass that produces substitutions "
            "the rival returns none where the spec pins some true. This is a binder "
            "point no other case reaches — weak-prepatch attacks (D) only at "
            "maxPasses = 0, and its witness does NOT refute this rival (which is "
            "correct there), so without this case the spec could pin `some _` at the "
            "empty configuration alone and the battery would not notice. If it VERIFIES "
            "=> SPEC-TOO-WEAK (definedness is pinned only at the zero-pass boundary)."
        ),
        # maxPasses=1, passSubst const true: gold => some true, rival => none.
        "witness": _wit("1", "fun _ => true",
                        "one substituting pass: gold some true, rival none"),
    },
]


# No @ContractOnly axioms and no opaque callees: the bounded refinement loop and its
# per-pass outcome are modeled DEEPLY over the transparent (Nat → Bool) carrier, so
# the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
