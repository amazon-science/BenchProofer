"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8269 (velvet).

NOT a Velvet module; a manifest the G-PBT gate parses and executes. Each SPEC
case is a full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte
(region surgery edits ONLY the text inside the ``-- impl-start`` / ``-- impl-end``
region, or the ``prove_correct`` tactic body — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct checkFragmentBranch``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  checkFragmentBranch (statusCode : Int) (found : Bool) return (out : Verdict)
    ensures out = classify statusCode found

The method is the fragment-checking branch of a link check on a non-redirected
response: ``statusCode`` is the received HTTP status and ``found`` records whether
the requested fragment is present. There is NO ``require`` clause (the operation
is total on ``Int × Bool``) and NO permission surface. The single load-bearing
``ensures`` pins ``out`` to the fully-unfolded pure model ``classify`` (the
``axioms`` region is empty — there is no opaque answer key to echo; the
status-validator is modeled deeply as ``isErrorStatus``, an A-reference). The
model's independent top-level clauses, over the TWO input binders:

  * error status (``isErrorStatus statusCode``), routed through ``classifyError``
    regardless of ``found`` — THREE sub-clauses:
      (1) 401  ⇒ working / unauthorized
      (2) 503  ⇒ ignored / httpError
      (3) any other error ⇒ broken / httpError
  * non-error status, where ``found`` decides — TWO sub-clauses:
      (4) found      ⇒ working / none
      (5) not found  ⇒ broken / anchorNotFound

The LOAD-BEARING change is clause (3)+(5) taken together: on an error status the
detail is the *response-status* provenance (``httpError``), NEVER the
*fragment-absent* notice (``anchorNotFound``) — even when the fragment is absent.
That is the exact F2P discriminator (the fix routes an error response to the
status handler before consulting the fragment). ``found`` must be IGNORED on an
error status; it decides only on a non-error status.

TWO INPUT BINDERS — ``statusCode`` (selects the error/non-error split and, within
the error branch, the 401/503/general sub-case) and ``found`` (decides the
non-error sub-case and must be ignored on the error branch). Both are load-bearing
and both are VARIED by the reject witnesses: the seven rivals are refuted at seven
DISTINCT input points (pts = 7) spanning statusCode ∈ {401, 500, 503, 200} and
found ∈ {true, false}, so the manifest demonstrates the post-image's dependence
on the status class, the 401/503/general error sub-case, whether the status is an
error at all, and the fragment flag — not a single pinned shape.

The ``found``-INDEPENDENCE half of that claim carries its own rival
(``partial-401-conditioned-on-fragment``). Mis-mapping the status/detail table
leaves the error branch reading no fragment flag at all, so a rival that only
mis-maps it cannot witness the difference between "ignores ``found``" and
"consults ``found``"; a rival that lets the flag LEAK INTO the error branch can,
and is refuted at an input every other rival AGREES with the spec on.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's own tester machinery (``checkFragmentBranchTester statusCode found =
false`` says the extracted program's result violates the postcondition at that
concrete input) and closes by ``decide``, checked in a file whose ``prove_correct``
block has been stripped so no tactic script can mask the verdict. Every argument
is a concrete ``Int`` / ``Bool`` literal, so ``decide`` reduces the extracted
(loop-free) rival program without getting stuck. Both halves of every reject
witness were confirmed out-of-band with ``scripts/lean_verify.sh``: each
ELABORATES green against its rival (proof stripped) and FAILS against the frozen
solution ("`decide` proved … is false"), so it is a real discriminator, not a
tautology.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical impls (return the grounded model directly; a
    branch-reordered form testing ``!found``) must verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    termination-obligation precondition. This backend has NO ``require`` and no
    permission surface, so that probe is degenerate; the residual admissibility
    risk here is a DEGENERATE post-image, so the case is re-aimed to an in-region
    ``assert`` pinning five genuinely distinct F2P-shaped outcomes (all five
    clauses at once), with the impl kept verbatim so the method's own obligation
    still discharges.
  * FRAME-MUTATION — VACUOUS. The sibling already records this class N/A (both
    inputs are pass-by-value primitives; no ``Acc(.,1/2)`` reference input). This
    backend is referentially transparent: ``statusCode`` / ``found`` are immutable
    values declared read-only (none ``mut``), no heap, no aliasing, no ``Old``, no
    permission system. Nothing to overwrite; NOT ported.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS in both its forms. The
    sibling carries ``vacuous-nonterminating-loop`` (case 8). This bundle is
    ``set_option loom.semantics.termination "total"``. (An earlier revision of this
    header said ``partial``. That was accurate when the port was written and was
    invalidated by the corpus-wide ``partial`` -> ``total`` remediation landing
    under it, not fabricated; the audit re-read the frozen ``set_option`` line and
    re-measured the class against ``total``.) So the verifier does emit a
    termination obligation and the NAIVE diverging rival is genuinely REJECTED:
    a spin loop carrying no ``decreasing`` annotation fails to elaborate at all
    (``error: Decreasing annotations are required in total correctness semantics``,
    measured, exit 1). That much of the class is closed STRUCTURALLY.
    The other half is closed too, and this bullet RETRACTS the "successor hole" an
    earlier revision escalated. That revision claimed the obligation is discharged
    by ANY measure expression, the strict-decrease side condition never being
    proven, so that a rival with an UNREACHABLE loop exit (``while 0 < 1`` /
    ``done_with False`` / ``decreasing (0 : Nat)``, or a ``Nat`` measure assigned
    to itself) returning a verdict WRONG at every input still VERIFIES at exit 0.
    RE-MEASURED on this bundle, BOTH of those shapes are REJECTED at exit 1 on the
    MEASURE's own descent goal: the constant leaves ``unsolved goals case
    «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``, and the self-assigned measure leaves
    ``case «decreasing_1: m» ... ⊢ m < m``. So the side condition IS proven, the
    unreachable exit launders nothing, and no ``spec_holes`` entry is owed from
    this class.
    THE MECHANISM, so the retraction does not rest on one build:
    ``set_option loom.semantics.termination "total"`` itself opens the
    ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``, the
    ``openScope `TotalCorrectness`` arm), line 7 of the frozen file opens it again
    explicitly, and ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the
    ``measure`` and emits ``⌜measure b' < measure b⌝`` as a goal the proof must
    discharge. Only the ``PartialCorrectness`` twin takes a measure and drops it,
    which is why the two header lines have to move together and do here. Neither
    shape is shippable as a reject case, for the WITNESS reason recorded in the
    footer rather than a semantic one.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to the fully-unfolded
    ``classify`` (and ``classifyError`` / ``isErrorStatus``) over the method's own
    arguments; there is no answer-key term a wrong impl could echo. The cheapest
    "echo the F2P answer" attack is the constant rival, covered below.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    dispatch table right yet diverges on one sub-domain (gate never consulted; the
    wrong error datum; the 401 / 503 special-case dropped; a blanket constant; the
    non-error success path mis-classified; the fragment flag leaking into the
    error branch).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8269"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every reject rival and the two positives swap on
# ---- this block.
_IMPL = """    -- impl-start
    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
    -- received HTTP status and `found` records whether the requested fragment is
    -- present. An error status is routed to the status handler; a non-error
    -- response lets fragment presence decide the outcome.
    let out : Verdict :=
      if isErrorStatus statusCode then
        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
         else
           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
            else { status := .broken, detail := .httpError, code := 0 }))
      else
        (if found then { status := .working, detail := .none, code := 0 }
         else { status := .broken, detail := .anchorNotFound, code := 0 })
    return out
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view).
_PROOF_GOLD = ("prove_correct checkFragmentBranch by\n"
               "  loom_solve\n"
               "  simp only [classify, classifyError]")
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _rewrite_impl(new_block, proof=_PROOF_GOLD):
    """Full variant: whole impl block replaced; proof left as the frozen script
    unless a shape needs a different (still-honest) closing tactic."""
    s = _swap(_BASE, _IMPL, new_block)
    if proof != _PROOF_GOLD:
        s = _swap(s, _PROOF_GOLD, proof)
    return s


def _block(body):
    """Wrap an impl body in the marker region (keeps same_spec: only impl text)."""
    return "    -- impl-start\n" + body + "\n    -- impl-end"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `checkFragmentBranchTester statusCode found = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped, so no
# ---- tactic script can mask the verdict. Every argument is a concrete literal so
# ---- `decide` reduces the (loop-free) extracted rival program without stalling.
def _witness(call):
    return ("\n"
            "extract_program_for checkFragmentBranch\n"
            "prove_precondition_decidable_for checkFragmentBranch\n"
            "prove_postcondition_decidable_for checkFragmentBranch\n"
            "derive_tester_for checkFragmentBranch\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the gold nested-if shape). Both confirmed
    # with a real build.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no intermediate branching — maximally structurally different from the
        # gold nested-if dispatch. `out` IS `classify statusCode found`, so the
        # ensures holds trivially; `loom_solve` alone closes it (the frozen
        # `simp only` tail would leave no goal, so this shape uses a bare
        # `loom_solve` — a tactic-body-only change, spec untouched).
        "module": _rewrite_impl(
            _block("    return classify statusCode found"),
            "prove_correct checkFragmentBranch by\n  loom_solve"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`classify statusCode found` directly. `out` IS that model, so the "
            "ensures holds on the whole domain; the reproof is a bare `loom_solve` "
            "(the frozen `simp only` tail would leave no goal after the direct "
            "return — tactic body only, spec byte-identical). If this fails to "
            "verify the spec is over-fit to the nested-if shape (SPEC-TOO-STRONG). "
            "Also the honest no-ungrounded-echo control: `classify` is the real "
            "work, so a direct return is correct, not a cheat. "
            "(Sibling: pos-control-flat-dispatch — a structurally different "
            "correct impl.)"),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different correct impl: the error branch delegates to the
        # `classifyError` helper (instead of re-inlining the 401/503/general
        # ladder), and the non-error branch is REORDERED to test `!found` first.
        # Semantically identical, different source. Needs a `cases found` split to
        # reconcile the `!found`-first order with `classify` (tactic body only).
        "module": _rewrite_impl(
            _block(
                "    let out : Verdict :=\n"
                "      if isErrorStatus statusCode then classifyError statusCode\n"
                "      else\n"
                "        (if !found then { status := .broken, detail := .anchorNotFound, code := 0 }\n"
                "         else { status := .working, detail := .none, code := 0 })\n"
                "    return out"),
            "prove_correct checkFragmentBranch by\n"
            "  loom_solve\n"
            "  simp only [classify, classifyError]\n"
            "  cases found <;> simp_all"),
        "rationale": (
            "the error branch delegates to `classifyError` (rather than "
            "re-inlining the 401/503/general ladder) and the non-error branch is "
            "reordered to test `!found` first — computing the same verdict for "
            "every input, so `out = classify statusCode found` still holds on the "
            "whole domain. The reproof adds only a `cases found <;> simp_all` arm "
            "(tactic body only). A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (rejects a faithful impl over the "
            "branch order / helper factoring). (Sibling: pos-control-flat-dispatch.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require`, so the sibling's "an
    # F2P-shaped input satisfies the precondition" probe is degenerate here. The
    # residual admissibility risk is a DEGENERATE post-image — a spec no impl
    # distinguishes reads exactly like one every impl meets. This case discharges
    # an in-region `assert`, at five fully concrete F2P-shaped inputs, that the
    # post-image is NON-DEGENERATE: it pins all five dispatch clauses to five
    # DISTINCT verdicts (error-general 500 ⇒ broken/httpError; 401 ⇒
    # working/unauthorized; 503 ⇒ ignored/httpError; non-error present ⇒
    # working/none; non-error absent ⇒ broken/anchorNotFound). The surrounding
    # impl is kept verbatim so the method's own obligation still discharges; the
    # proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      classify 500 false = { status := .broken, detail := .httpError, code := 0 } ∧\n"
                  "      classify 401 false = { status := .working, detail := .unauthorized, code := 0 } ∧\n"
                  "      classify 503 false = { status := .ignored, detail := .httpError, code := 0 } ∧\n"
                  "      classify 200 true  = { status := .working, detail := .none, code := 0 } ∧\n"
                  "      classify 200 false = { status := .broken, detail := .anchorNotFound, code := 0 }))\n"),
            _PROOF_GOLD,
            "prove_correct checkFragmentBranch by\n"
            "  loom_solve\n"
            "  · decide\n"
            "  · simp only [classify, classifyError]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at five F2P-shaped "
            "inputs: an error-general status yields broken/httpError, 401 yields "
            "working/unauthorized, 503 yields ignored/httpError, a non-error "
            "present fragment yields working/none, and a non-error absent fragment "
            "yields broken/anchorNotFound — five distinct verdicts exercising every "
            "dispatch clause. The in-region assert must discharge (else the "
            "obligation is degenerate); the impl is kept verbatim so `out = "
            "classify statusCode found` still verifies. (Sibling: "
            "admiss-f2p-shaped-selfcall, re-aimed from precondition admissibility "
            "to post-image non-degeneracy since this backend has no `require` and "
            "no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "partial-prepatch-no-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: consult `found` WITHOUT first validating the
        # response status. On any error status with the fragment absent it emits
        # the fragment-absent notice instead of the response-status verdict.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if found then { status := .working, detail := .none, code := 0 }\n"
            "      else { status := .broken, detail := .anchorNotFound, code := 0 }\n"
            "    return out")),
        "refinement": (
            "this is the pre-change behaviour: the fragment verdict is consulted "
            "with no prior status validation, so on the F2P scenario (a server "
            "answering with an error status, fragment absent) it reports the "
            "fragment-absent notice instead of the required response-status "
            "message. The F2P test asserts the exact response-status line, so this "
            "real patch does NOT resolve. Correct on every non-error input (a true "
            "partial-domain break)."),
        "rationale": (
            "REJECT from `out = classify statusCode found`: for an error status "
            "the spec routes through `classifyError` regardless of `found`, but "
            "this rival never validates the status. Refuted at statusCode=503, "
            "found=false — where the spec keeps the service-unavailable "
            "classification (ignored/httpError) and the rival returns "
            "broken/anchorNotFound. Verifying would be SPEC-TOO-WEAK (the "
            "status-gate the fix adds left unpinned)."),
        "witness": _witness("checkFragmentBranchTester 503 false"),
    },
    {
        "id": "wrong-error-datum",
        "kind": "uniqueness",
        "expect": "reject",
        # The gate IS consulted and 401/503 dispatched correctly, but the
        # general-error branch attaches the fragment-absent notice to a broken
        # result instead of the response-status detail. Right status-class, WRONG
        # accompanying datum — the subtle hole the load-bearing clause closes.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if isErrorStatus statusCode then\n"
            "        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }\n"
            "         else\n"
            "           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }\n"
            "            else { status := .broken, detail := .anchorNotFound, code := 0 }))\n"
            "      else\n"
            "        (if found then { status := .working, detail := .none, code := 0 }\n"
            "         else { status := .broken, detail := .anchorNotFound, code := 0 })\n"
            "    return out")),
        "refinement": (
            "the general-error branch emits the fragment-absent notice on a broken "
            "result. The status-class 'broken' matches, but the F2P asserts the "
            "EXACT detail is the response-status message, so the reported line "
            "still reads 'Anchor not found' and the F2P test FAILS — it does NOT "
            "resolve. This is the subtle hole: right class, wrong datum."),
        "rationale": (
            "REJECT from `out = classify statusCode found` on the general-error "
            "clause: the spec pins detail=httpError for an error status that is "
            "neither 401 nor 503, this rival returns detail=anchorNotFound. Refuted "
            "at statusCode=500, found=false — the F2P discriminator. Verifying "
            "would be SPEC-TOO-WEAK on the load-bearing error datum."),
        "witness": _witness("checkFragmentBranchTester 500 false"),
    },
    {
        "id": "partial-drop-401",
        "kind": "uniqueness",
        "expect": "reject",
        # 401 special-case dropped: it falls into the general-error branch ->
        # broken/httpError. Correct on the F2P (500) and every other error, but
        # WRONG on the authorization-required status.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if isErrorStatus statusCode then\n"
            "        (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }\n"
            "         else { status := .broken, detail := .httpError, code := 0 })\n"
            "      else\n"
            "        (if found then { status := .working, detail := .none, code := 0 }\n"
            "         else { status := .broken, detail := .anchorNotFound, code := 0 })\n"
            "    return out")),
        "refinement": (
            "dropping the 401 special-case sends the authorization-required status "
            "into the general-error branch, reporting it broken instead of working. "
            "The shared status-handler classifies 401 as working (the "
            "'- unauthorized' path the PASS_TO_PASS auth test exercises), so a real "
            "patch shaped this way changes that established classification and does "
            "not preserve the tested behaviour."),
        "rationale": (
            "REJECT from `out = classify statusCode found` on clause (1): "
            "statusCode=401 must be working/unauthorized, this rival returns "
            "broken/httpError. Refuted at statusCode=401, found=false. Correct on "
            "the F2P 500 and every other error, so the spec pins the 401 sub-domain "
            "specifically; verifying would be SPEC-TOO-WEAK on the 401 special "
            "case."),
        "witness": _witness("checkFragmentBranchTester 401 false"),
    },
    {
        "id": "partial-drop-503",
        "kind": "uniqueness",
        "expect": "reject",
        # 503 special-case dropped: it falls into the general-error branch ->
        # broken/httpError. Correct on 401, the F2P 500, and every other error,
        # but WRONG on the service-unavailable status (must be ignored). Refuted
        # with found=true to also vary the fragment binder on the error branch.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if isErrorStatus statusCode then\n"
            "        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }\n"
            "         else { status := .broken, detail := .httpError, code := 0 })\n"
            "      else\n"
            "        (if found then { status := .working, detail := .none, code := 0 }\n"
            "         else { status := .broken, detail := .anchorNotFound, code := 0 })\n"
            "    return out")),
        "refinement": (
            "dropping the 503 special-case sends the service-unavailable status "
            "into the general-error branch, reporting it broken instead of ignored. "
            "The shared status-handler classifies 503 as ignored (an unchanged "
            "PASS_TO_PASS behaviour), so a real patch shaped this way changes that "
            "classification and does not preserve the tested behaviour for the "
            "service-unavailable status."),
        "rationale": (
            "REJECT from `out = classify statusCode found` on clause (2): "
            "statusCode=503 must be ignored/httpError, this rival returns "
            "broken/httpError (wrong status-class). Refuted at statusCode=503, "
            "found=true — an error input, so `found` must be IGNORED; the rival is "
            "wrong here regardless of the flag, and this drives `found` to `true` "
            "on the error branch (a point no other rival probes). Verifying would "
            "be SPEC-TOO-WEAK on the 503 special case."),
        "witness": _witness("checkFragmentBranchTester 503 true"),
    },
    {
        "id": "partial-401-conditioned-on-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        # The `found`-INDEPENDENCE rival. Every other rival mis-maps the
        # status/detail table but, like the frozen impl, never reads `found` on
        # the error branch — so none of them would sense an impl that lets the
        # fragment flag LEAK INTO the error branch, which is exactly the
        # load-bearing property ("`found` must be IGNORED on an error status").
        # This rival grants the reachable classification to the
        # authorization-required status only when the fragment is ABSENT; with
        # the fragment present it falls through to the general-error branch.
        # Every one of the five dispatch clauses is right at some input, and it
        # agrees with the spec at every point the rest of the reject set probes.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if isErrorStatus statusCode then\n"
            "        (if statusCode = 401 && !found then { status := .working, detail := .unauthorized, code := 0 }\n"
            "         else\n"
            "           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }\n"
            "            else { status := .broken, detail := .httpError, code := 0 }))\n"
            "      else\n"
            "        (if found then { status := .working, detail := .none, code := 0 }\n"
            "         else { status := .broken, detail := .anchorNotFound, code := 0 })\n"
            "    return out")),
        "refinement": (
            "conditioning the authorization-required classification on fragment "
            "absence makes the verdict for one status depend on the fragment "
            "flag, which the shared status-handler never consults. A real patch "
            "shaped this way reports an authorization-required link whose "
            "fragment IS present as broken rather than working, so the "
            "PASS_TO_PASS auth case FAILS and it does NOT resolve. It also "
            "re-introduces the ordering defect in miniature: the fragment "
            "outcome is again allowed to override a status-derived verdict."),
        "rationale": (
            "the `found`-INDEPENDENCE rival, and the only case that attacks it. "
            "The other rivals all mis-map the status/detail table while (like "
            "the frozen impl) ignoring `found` on the error branch, so none of "
            "them senses the fragment flag leaking INTO that branch — the "
            "manifest's load-bearing claim. REJECT from `out = classify "
            "statusCode found` on clause (1), which pins 401 to "
            "working/unauthorized for BOTH values of `found`: this rival returns "
            "broken/httpError when the fragment is present. Refuted at "
            "statusCode=401, found=true — a point no other rival probes, and the "
            "only witness in the battery that is an AGREEMENT point for every "
            "other rival. Verifying would be SPEC-TOO-WEAK on the "
            "found-independence of the error branch."),
        "witness": _witness("checkFragmentBranchTester 401 true"),
    },
    {
        "id": "const-echo-failed-transport",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant-return "echo the F2P answer": always broken/httpError, the exact
        # verdict the F2P (an error status) expects. Cheapest impl satisfying the
        # load-bearing error clause without doing any classification. A tight spec
        # must reject it because it is WRONG everywhere else.
        "module": _rewrite_impl(_block(
            "    return { status := .broken, detail := .httpError, code := 0 }")),
        "refinement": (
            "unconditionally returning broken/httpError is the cheapest impl that "
            "satisfies the F2P answer (an error status ⇒ the response-status line) "
            "without any classification. But it marks EVERY link broken with a "
            "response-status detail: a working non-error link and a 401 link would "
            "both be reported broken, so the PASS_TO_PASS default/auth cases FAIL "
            "and it does NOT resolve."),
        "rationale": (
            "the grounded total model has no ungrounded oracle to echo; the "
            "cheapest 'echo the F2P answer' impl is this constant. REJECT from "
            "`out = classify statusCode found` on clause (5): a non-error status "
            "with the fragment absent must be broken/anchorNotFound, this returns "
            "broken/httpError. Refuted at statusCode=200, found=false — a non-error "
            "sub-domain no other rival attacks, demonstrating the constant is wrong "
            "away from the F2P point. Verifying would be SPEC-TOO-WEAK (a constant "
            "would satisfy the spec)."),
        "witness": _witness("checkFragmentBranchTester 200 false"),
    },
    {
        "id": "wrong-code-field",
        "kind": "uniqueness",
        "expect": "reject",
        # The THIRD `Verdict` field. Every other rival in the battery mutates
        # `status` and/or `detail` and leaves `code := 0` on every arm exactly as
        # the frozen impl does — so none of them would sense an impl that gets the
        # whole status/detail dispatch table right and attaches the WRONG code.
        # This rival is byte-identical to the frozen dispatch except that the
        # service-unavailable arm carries code := 1.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if isErrorStatus statusCode then\n"
            "        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }\n"
            "         else\n"
            "           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 1 }\n"
            "            else { status := .broken, detail := .httpError, code := 0 }))\n"
            "      else\n"
            "        (if found then { status := .working, detail := .none, code := 0 }\n"
            "         else { status := .broken, detail := .anchorNotFound, code := 0 })\n"
            "    return out")),
        "refinement": (
            "the third element of the returned tuple is the code the caller "
            "reports alongside the verdict; the modeled branch emits 0 on every "
            "arm. Attaching a non-zero code to the service-unavailable arm changes "
            "the reported tuple for that status while leaving its classification "
            "and message intact, so a real patch shaped this way alters an "
            "unchanged reported value on an established path and does not preserve "
            "the tested behaviour."),
        "rationale": (
            "the `code`-FIELD rival, and the only case that attacks it. Every "
            "other rival mutates `status` and/or `detail` while (like the frozen "
            "impl) leaving `code := 0` on every arm, so none of them senses a "
            "wrong code — the third component of the post-image was asserted by "
            "the `Verdict` structure but never demonstrated to be pinned. REJECT "
            "from `out = classify statusCode found` on clause (2), which pins the "
            "503 verdict to ignored/httpError with code=0: this rival returns "
            "code=1. Refuted at statusCode=503, found=false. Verifying would be "
            "SPEC-TOO-WEAK on the code component."),
        "witness": _witness("checkFragmentBranchTester 503 false"),
    },
    {
        "id": "partial-nonerror-present-misclassified",
        "kind": "uniqueness",
        "expect": "reject",
        # Non-error success path mis-classified: on a non-error status it always
        # reports broken/anchorNotFound, ignoring `found`. Correct on every error
        # status and on non-error+absent, but WRONG on non-error+present. Guards
        # that the spec pins more than just the error path.
        "module": _rewrite_impl(_block(
            "    let out : Verdict :=\n"
            "      if isErrorStatus statusCode then classifyError statusCode\n"
            "      else { status := .broken, detail := .anchorNotFound, code := 0 }\n"
            "    return out")),
        "refinement": (
            "on a non-error status this always reports the fragment absent "
            "regardless of `found`, so a working link whose fragment IS present is "
            "reported broken instead of working. This breaks the existing success "
            "path the PASS_TO_PASS default/anchors-ignored cases exercise (a "
            "present anchor on a non-error page must be working), so this real "
            "patch FAILS those tests and does NOT resolve."),
        "rationale": (
            "supporting partial-domain on the UNCHANGED half of the table (guards "
            "the spec pins more than the error path). REJECT from `out = classify "
            "statusCode found` on clause (4): a non-error status with the fragment "
            "present must be working/none, this returns broken/anchorNotFound. "
            "Refuted at statusCode=200, found=true — the only point where `found` "
            "flips the non-error verdict, making that binder load-bearing. "
            "Verifying would be SPEC-TOO-WEAK on the non-error success sub-domain."),
        "witness": _witness("checkFragmentBranchTester 200 true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (1
# soundness positive, 1 admissibility, 7 uniqueness rivals — one of them a
# vacuous non-termination case) plus an AXIOM lane (2 A-reference probes for its
# own carrier). The sibling contracts a single function `classify_fragment_link`
# over (status:int, fragment_present:bool); this bundle models the same slice as
# `checkFragmentBranch (statusCode:Int) (found:Bool)` over the pure model
# `classify`, so — unlike the usual carrier-narrowing story — this is a nearly
# one-to-one port of the dispatch-table cases.
#
#   sibling case                              kind          -> here                                     disposition
#   -----------------------------------------------------------------------------------------------------------------
#   pos-control-flat-dispatch                 soundness     -> pos-control-direct-model                 PORTED
#                                                              (+ pos-control-branch-reorder            ADDED)
#   admiss-f2p-shaped-selfcall                admissibility -> admiss-nondegenerate                     RE-AIMED
#   partial-prepatch-no-gate                  uniqueness    -> partial-prepatch-no-gate                 PORTED
#   wrong-error-datum                         uniqueness    -> wrong-error-datum                        PORTED
#   partial-drop-401                          uniqueness    -> partial-drop-401                         PORTED
#   partial-drop-503                          uniqueness    -> partial-drop-503                         PORTED
#   const-echo-failed-transport               uniqueness    -> const-echo-failed-transport              PORTED
#   partial-nonerror-present-misclassified    uniqueness    -> partial-nonerror-present-misclassified   PORTED
#                                                              (+ partial-401-conditioned-on-fragment   ADDED)
#                                                              (+ wrong-code-field                      ADDED by audit)
#   vacuous-nonterminating-loop               uniqueness    -> (none)                                   SPEC-CLOSED
#   AXIOM_TESTS (2 A-reference)               axiom         -> (none)                                   N/A (G-AX)
#
# 6 uniqueness ported (all the value/partial-domain rivals) + 1 added, 1 soundness
# ported + 1 added, 1 admissibility re-aimed; 1 uniqueness (divergence) is CLOSED
# BY THE SEMANTICS and unwitnessable (below); axiom lane out of scope.
#
# ADDED (partial-401-conditioned-on-fragment): the sibling's rivals — and so the
#   ported set — all mis-map the status/detail table while leaving the error branch
#   independent of `found`, exactly as the frozen impl does. That leaves the
#   manifest's load-bearing claim ("`found` must be IGNORED on an error status")
#   asserted but not demonstrated: no ported rival consults the fragment flag on
#   the error branch, so none of them would be refuted by an impl that does. The
#   added rival conditions the 401 classification on fragment ABSENCE and is
#   refuted at 401/true, an agreement point for every other rival.
#
# ADDED by audit (wrong-code-field): the `Verdict` structure carries THREE fields,
#   but every ported rival mutated only `status` / `detail` and left `code := 0` on
#   every arm exactly as the frozen impl does. So the third component of the
#   post-image was pinned by the `ensures` but never DEMONSTRATED to be pinned: no
#   rival in the battery would have been refuted by an impl that gets the whole
#   status/detail table right and attaches the wrong code. The added rival differs
#   from the frozen dispatch in that single field on the 503 arm and is refuted at
#   503/false. (Machine-checked both halves: witness-on-rival exit 0,
#   witness-on-gold exit 1 with `Tactic `decide` proved that the proposition
#   checkFragmentBranchTester 503 false = false is false` — a plain evaluation.)
#   Note this shares its input point with partial-prepatch-no-gate, so `pts` stays
#   7 while cases rise to 8: the new discrimination is on the post-image COMPONENT,
#   not on a new input, and the footer does not claim otherwise.
# ADDED (pos-control-branch-reorder): a second structurally-different correct
#   impl (delegate the error branch to `classifyError`, reorder the non-error
#   branch to test `!found` first) beyond the sibling's single flat-dispatch
#   positive, to defend the obligation against both the "return the model
#   directly" and the "reshaped branch order" impl shapes.
# RE-AIMED (admiss-f2p-shaped-selfcall -> admiss-nondegenerate): the sibling
#   asserts an F2P-shaped input satisfies its MustTerminate precondition. This
#   backend has NO `require` (the operation is total on Int×Bool) and no
#   permission surface, so that probe is degenerate; the sharper residual risk is
#   a DEGENERATE post-image, so the case is re-aimed to an in-region assert
#   pinning all five dispatch clauses to five distinct verdicts.
# KNOWN HOLE (vacuous-nonterminating-loop): NOT vacuous on this carrier, and NOT
#   for the reason an earlier revision of this footer gave. That revision claimed
#   this bundle is `set_option loom.semantics.termination "total"`; the frozen
#   solution now reads `"total"`. The claim was TRUE when the port was written and
#   was invalidated underneath it by the corpus-wide `partial` -> `total`
#   remediation, so this is stale prose, not invented
#   prose — but a battery whose disposition for a whole lane is keyed to the wrong
#   semantics is wrong either way, which is why the audit re-measured the class
#   against `total`. The corrected accounting:
#     * naive diverging rival (spin loop, NO `decreasing` annotation) — REJECTED,
#       exit 1, `error: Decreasing annotations are required in total correctness
#       semantics`. Under `total` the verifier emits a real termination obligation,
#       so this half of the class is closed STRUCTURALLY by the semantics. It is
#       therefore NOT shippable as a reject case either — not because the spec
#       admits it, but because the rejection is refused at elaboration: the error is
#       file-level, so the witness cannot elaborate against the rival (measured:
#       witness-on-rival exit 1, `decide` never reduces), which is precisely the
#       `witness-undecided` shape the gate refuses. There is no concrete input at
#       which a tester distinguishes a program that never runs.
#     * the SHARPER form, which cannot be dismissed as merely missing the
#       annotation, CARRIES a measure that does not decrease: an UNREACHABLE loop
#       exit plus a fixed measure (`while 0 < 1` / `done_with False` /
#       `decreasing (0 : Nat)`, or a `Nat` measure assigned to itself) returning a
#       verdict WRONG at every input. RE-MEASURED, BOTH shapes are REJECTED at
#       exit 1 on the measure's own descent goal:
#           unsolved goals
#           case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#           case «decreasing_1: m» ... |- m < m
#       RETRACTION: an earlier revision recorded both as VERIFYING (exit 0,
#       `sorry`-free, `variant_problems == []`), reasoned that the `decreasing`
#       annotation is recorded and dropped so the strict-decrease side condition is
#       never proven, and filed the corpus-wide non-decreasing-measure hole in the
#       audit's `spec_holes`. The builds above withdraw that entry: the side
#       condition IS proven and the unreachable exit launders nothing.
#       Mechanism: `set_option loom.semantics.termination "total"` itself opens the
#       `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`,
#       `openScope `TotalCorrectness`), line 7 opens it again, and
#       `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#       `measure b' < measure b` as a goal; only the `PartialCorrectness` twin
#       discards it.
#   No reject case can be shipped for EITHER form, and the reason is now the same
#   for both: the rejection lands on the `method`, which the witness file retains
#   after the `prove_correct` strip, so the rival's own module does not compile and
#   no witness can ELABORATE against it (the gate's `witness-undecided` /
#   `witness-unproven` screen). No spec hole is escalated from this class. NOT
#   written off as referential transparency: the reason is the witness machinery,
#   not the carrier and not the spec.
# FRAME-MUTATION: the sibling already records this class N/A (both inputs are
#   pass-by-value primitives, has_readonly_input=False, no `Acc(.,1/2)` reference
#   input). Vacuous here for the same reason plus referential transparency; NOT
#   ported.
# AXIOM_TESTS: empty here — G-PBT ignores the axiom lane (that is G-AX's job). The
#   sibling's two A-reference probes validate `isErrorStatus == real
#   raise_for_status`; this bundle's G-AX (meta.json) already records that pass.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = classify statusCode
#   found` has TWO binders — `statusCode : Int`, `found : Bool` — over five
#   independent top-level dispatch clauses. The EIGHT reject witnesses probe seven
#   DISTINCT input points (pts = 7; wrong-code-field reuses 503/false because it
#   discriminates a post-image COMPONENT rather than a new input):
#     * partial-prepatch-no-gate                503 / false   (error 503 clause; gate skipped)
#     * wrong-error-datum                       500 / false   (general-error datum, the F2P point)
#     * partial-drop-401                        401 / false   (401 clause)
#     * partial-drop-503                        503 / true    (503 clause; found=true on error branch)
#     * partial-401-conditioned-on-fragment     401 / true    (401 clause, found-independence)
#     * const-echo-failed-transport             200 / false   (non-error absent clause)
#     * partial-nonerror-present-misclassified  200 / true    (non-error present clause)
#   So `statusCode` ranges over {401, 500, 503, 200} — the error/non-error split
#   and all three error sub-cases (401, 503, general) — and `found` ranges over
#   {true, false} on BOTH branches (true on the error branch via drop-503 and
#   401-conditioned, where it must be ignored, and on the non-error branch via
#   nonerror-present, where it decides; false across the rest). Every one of the
#   five dispatch clauses is attacked by some rival, both binders take both
#   relevant values, and the found-independence of the error branch — asserted by
#   the header as load-bearing — is itself attacked rather than only claimed.
AXIOM_TESTS = []
