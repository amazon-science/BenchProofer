# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8475 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a soundness positive that reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against the
# rival and FAILS on the frozen solution, so the rejection is attributable to the spec
# and not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   probeUri : ReqOutcome → ReqOutcome → ReqOutcome
#   Models the lightweight-probe → full-request-fallback decision. `light` is the
#   lightweight probe's outcome and `full` the fallback's; the surviving outcome is
#   the fallback outcome EXACTLY when the lightweight outcome is a retryable failure
#   (an HTTP status error OR a redirect loop), and the lightweight outcome otherwise
#   (a success or any non-retryable failure). ReqOutcome's four cases are: ok (usable
#   response), statusError (server answered with an error status), redirectLoop
#   (server kept redirecting without settling), otherFailure (connection/TLS/other).
#
#   The single postcondition pins the result exactly:
#     result = if retryWithFull light then full else light
#   where retryWithFull light = true iff light ∈ {statusError, redirectLoop}.
#   Two independent arms are attackable: the RETRY branch (a retryable light failure
#   must yield `full`) and the PASS-THROUGH branch (a non-retryable light outcome —
#   success or otherFailure — must yield `light` itself). The discriminating content
#   of the change is the redirect-loop arm of the retry predicate: a redirect loop on
#   the lightweight probe must now fall back to the full request. The F2P drives a
#   server that loops on the lightweight probe (redirectLoop) but answers the full
#   request with a usable response (ok); the surviving outcome must be the success.
#
# CARRIER NOTE (why the nagini int-code carrier and this one differ): nagini abstracts
# each outcome to an int kind {0,1,2,3} with a @Pure `is_retryable` helper grounded in
# the input; this backend models the four outcomes as a transparent `ReqOutcome` enum
# with a `retryWithFull : ReqOutcome → Bool` helper. The rival ARGUMENTS port 1:1
# (kind 1 ↔ statusError, kind 2 ↔ redirectLoop, kind 3 ↔ otherFailure, kind 0 ↔ ok);
# only the concrete witnesses are new work, since the nagini cases relied on Viper
# discharging the postcondition whereas here a reject needs a discriminator input.
#
# LANES THAT DO PORT, RESHAPED:
#   * ADMISSIBILITY. The nagini sibling's `admiss-f2p-shape` asserted its Requires
#     admits the discriminating input. Here the frozen obligation is an
#     unconditional `∀` with no precondition hypothesis, so there is no Requires to
#     be over-strong — but the lane is NOT vacuous: the analogous obligation is that
#     the spec be SATISFIABLE at the discriminating point with the intended result.
#     Carried as `admiss-discriminating-shape`, discharged by `decide` inside the
#     impl region so no new declaration is introduced.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's inputs were pass-by-value scalars there; here the two
#     outcomes are immutable enum values). Lean is referentially transparent — no
#     aliasing, no permissions — so a "write-back into a read-only input" rival is not
#     expressible and the lane is VACUOUS here. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. The earlier
#     claim here ("a diverging implementation cannot be written at all") was measured
#     FALSE and is corrected: while the frozen impl is a total `def`, a variant may
#     declare `partial def` and self-recurse on an unchanged argument, and the scope
#     check ADMITS it (variant_problems=[]; `partial` is not an assumption token). So
#     the impl is expressible. It is also rejected (exit 1) — but the rejection is NOT
#     attributable to the spec, and that is the reason nothing ships here:
#       - control, measured: a `partial def` that is behaviourally CORRECT and
#         non-recursive VERIFIES (exit 0). So `partial` alone is not what fails.
#       - the diverging one fails as `unsolved goals ⊢ implementation_probeUri ok ok =
#         ok` even under a maximally aggressive fresh proof. `partial def` yields no
#         equation lemmas, so the term is OPAQUE and irreducible for EVERY claim about
#         it, true or false — the same stuck shape the witness rule exists to reject.
#       - the repair the guide prescribes was attempted and does not close: a witness
#         conditioning on the carrier by hypothesis ELABORATES against the rival but
#         ALSO against the frozen solution (exit 0 both sides => witness-vacuous),
#         because gold reduces and makes the hypothesis false, so the refutation
#         follows vacuously rather than discriminating.
#     Hence: expressible, rejected, but not WITNESSABLE — the disposition is a known
#     hole in what this gate can attribute, not a complete battery. (The nagini
#     sibling carries no diverge-* case, so nothing was dropped in the port.)
#   * AXIOM_TESTS. The bundle has no consumed axiom (the retry decision is modeled
#     deeply over the transparent enum); the axiom lane is G-AX's job and this gate
#     ignores it regardless. The nagini AXIOM_TESTS (checking the retry predicate
#     against the library's real failure-classification behaviour) are dropped here
#     by design.
#   * UNGROUNDED-ORACLE. `retryWithFull` is a total structural function of the input
#     outcome (no opaque answer-key), so there is nothing for a rival to echo; N/A.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8475"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchor: the gold do-block body, verbatim. It lies ENTIRELY inside
# impl-start/impl-end and is unique in the file. ----------------------------------
_IMPL_BODY = (
    "    let mut response := light\n"
    "    if retryWithFull light then\n"
    "      response := full\n"
    "    return response"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drifted"

# --- proof-region anchor: the frozen tactic body (only edited by soundness
# positives that reshape the impl; rivals keep it byte-identical). ----------------
_PROOF_BODY = (
    "  intro light full\n"
    "  unfold problem_spec_probeUri implementation_probeUri\n"
    "  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl"
)
assert _BASE.count(_PROOF_BODY) == 1, "proof-body anchor drifted"


def _rival(new_impl):
    """Swap ONLY the impl-region body; spec + proof view untouched => same_spec and
    the frozen theorem STATEMENT survives byte-identical. The frozen tactic body no
    longer closes against the reshaped impl (expected — the reject signal), and the
    `witness` is what attributes that rejection to the spec."""
    return _swap(_BASE, _IMPL_BODY, new_impl)


def _pos(new_impl, new_proof):
    """A soundness positive: reshape the impl AND reprove, keeping the theorem
    STATEMENT byte-identical (only the tactic body changes — no new lemma/axiom)."""
    return _swap(_swap(_BASE, _IMPL_BODY, new_impl), _PROOF_BODY, new_proof)


def _wit(light, full):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    (light, full), closed by `decide`. Elaborates against a rival that diverges from
    the frozen result there, and FAILS on gold (which satisfies the spec everywhere).
    Both inputs are concrete enum literals, so `decide` computes without any opaque
    term or auxiliary hypothesis."""
    lit_l = f"ReqOutcome.{light}"
    lit_f = f"ReqOutcome.{full}"
    return (
        f"example : ¬ problem_spec_probeUri {lit_l} {lit_f}\n"
        f"    (implementation_probeUri {lit_l} {lit_f}) := by\n"
        f"  unfold problem_spec_probeUri implementation_probeUri\n"
        f"  decide"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-explicit-dispatch: structurally DIFFERENT but behaviourally identical — an
# explicit per-outcome dispatch on `light` instead of the retryWithFull branch. The
# two pass-through outcomes (ok, otherFailure) select `light`; the two retryable
# failures select `full`. Result value identical on every input; the reproof case-
# splits on `light` and closes by rfl. If it FAILS => SPEC-TOO-STRONG.
_POS_DISPATCH_IMPL = (
    "    match light with\n"
    "    | ReqOutcome.ok           => return light\n"
    "    | ReqOutcome.otherFailure => return light\n"
    "    | _                       => return full"
)
_POS_DISPATCH_PROOF = (
    "  intro light full\n"
    "  unfold problem_spec_probeUri implementation_probeUri\n"
    "  cases light <;> rfl"
)

# pos-negated-branch: branch on the NEGATION of the retry predicate, with the
# default seeded to `full` and overridden to `light` on the pass-through side.
# Confirms the spec does not over-fit the one particular control shape.
_POS_NEGATED_IMPL = (
    "    let mut response := full\n"
    "    if !retryWithFull light then\n"
    "      response := light\n"
    "    return response"
)
_POS_NEGATED_PROOF = (
    "  intro light full\n"
    "  unfold problem_spec_probeUri implementation_probeUri\n"
    "  by_cases h : retryWithFull light <;> "
    "simp only [Id.run, h, Bool.not_true, Bool.not_false, if_true] <;> rfl"
)


# admiss-discriminating-shape: the ADMISSIBILITY lane, ported from the nagini
# sibling's `admiss-f2p-shape`. The frozen obligation is an unconditional `∀`
# (no precondition hypothesis), so there is no Requires for an over-strong
# precondition to reject — but the lane is NOT vacuous here: the analogous
# question is whether the spec ADMITS the discriminating input shape with the
# intended result, i.e. that `problem_spec` is SATISFIABLE at the point the
# change is about (a redirect-loop lightweight outcome with a successful
# fallback) rather than pinning it to some other value. A spec that was
# accidentally unsatisfiable there — or satisfied only by the pass-through
# outcome — would be rejected by this case. Discharged inside the impl region
# by `decide`, so no new theorem/lemma/axiom is introduced and the frozen
# obligation and its proof are untouched.
_POS_ADMISS_IMPL = (
    "    -- ADMISSIBILITY pin: the spec must ADMIT the discriminating input shape —\n"
    "    -- a lightweight probe that ends in a redirect loop with a successful\n"
    "    -- fallback — as yielding the SUCCESS outcome.\n"
    "    let _shape : problem_spec_probeUri ReqOutcome.redirectLoop ReqOutcome.ok\n"
    "        ReqOutcome.ok := by\n"
    "      unfold problem_spec_probeUri\n"
    "      decide\n"
    "    let mut response := light\n"
    "    if retryWithFull light then\n"
    "      response := full\n"
    "    return response"
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; each carries a discriminating witness.
# ---------------------------------------------------------------------------

# weak-prepatch: retry ONLY a status error, never a redirect loop. This is the literal
# pre-change classification. Correct everywhere except a redirect-loop lightweight
# outcome, where it passes the loop through instead of falling back to the full probe.
_RIVAL_PREPATCH_IMPL = (
    "    let mut response := light\n"
    "    if light == ReqOutcome.statusError then\n"
    "      response := full\n"
    "    return response"
)

# weak-retry-only-redirect: retry ONLY a redirect loop, never a status error.
# The inverse partial miss — wrong on a status-error lightweight outcome.
_RIVAL_REDIRECT_ONLY_IMPL = (
    "    let mut response := light\n"
    "    if light == ReqOutcome.redirectLoop then\n"
    "      response := full\n"
    "    return response"
)

# weak-overcatch: retry on ANY non-success lightweight outcome, including the
# non-retryable otherFailure. Wrong on otherFailure: yields the fallback instead of
# reporting the authoritative failure.
_RIVAL_OVERCATCH_IMPL = (
    "    let mut response := light\n"
    "    if light != ReqOutcome.ok then\n"
    "      response := full\n"
    "    return response"
)

# weak-always-full: always report the fallback outcome, ignoring the lightweight
# probe entirely. Violates the pass-through branch on every non-retryable input.
_RIVAL_ALWAYS_FULL_IMPL = (
    "    let mut response := full\n"
    "    return response"
)


SPEC_TESTS = [
    {
        "id": "pos-explicit-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos(_POS_DISPATCH_IMPL, _POS_DISPATCH_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl: an explicit per-outcome "
            "dispatch on the lightweight outcome (the two pass-through outcomes select "
            "the lightweight result; the two retryable failures select the fallback), "
            "behaviourally identical to the retryWithFull branch on every input. The "
            "frozen `theorem correct_probeUri` STATEMENT is kept byte-identical and its "
            "reproof case-splits on the outcome and closes by rfl. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful, structurally-different correct impl rejected)."
        ),
    },
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos(_POS_NEGATED_IMPL, _POS_NEGATED_PROOF),
        "rationale": (
            "branch reorder on the NEGATION of the retry predicate (seed the fallback, "
            "override to the lightweight outcome on the pass-through side); equivalent "
            "to gold on every input. Confirms the spec does not over-fit one control "
            "shape. Theorem statement byte-identical; reproof by the same case split. "
            "If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-discriminating-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rival(_POS_ADMISS_IMPL),
        "rationale": (
            "ADMISSIBILITY: the spec must ADMIT the discriminating input shape — a "
            "lightweight probe ending in a redirect loop whose fallback succeeds — as "
            "yielding the SUCCESS outcome. The frozen obligation is an unconditional "
            "`∀` with no precondition hypothesis, so there is no Requires to be "
            "over-strong; the ported analogue is SATISFIABILITY at the point the "
            "change is about. This case pins `problem_spec_probeUri redirectLoop ok "
            "ok` and discharges it by `decide` inside the impl region (no new "
            "theorem/lemma/axiom; the frozen obligation and its proof body are "
            "untouched). If it FAILS => the spec does not admit the very input shape "
            "the change exists to fix (PRECOND-TOO-STRONG / unsatisfiable spec)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_PREPATCH_IMPL),
        "refinement": (
            "this IS the pre-change classification: only a status error triggers the "
            "fallback, a redirect loop is passed through. Its faithful real counterpart "
            "is the unchanged repo, which reports a locator broken when the lightweight "
            "probe loops on redirects even though the full request would succeed — "
            "exactly the FAIL_TO_PASS test_TooManyRedirects_on_HEAD, which asserts the "
            "locator is working. It does NOT resolve, so a verifying rival here would be "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition's retry branch: on a redirect-loop "
            "lightweight outcome the spec pins the result to `full`, but the rival "
            "passes the loop through as the result. Attacks the redirect-loop arm of "
            "retryWithFull — the precise behaviour the change introduces. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # light=redirectLoop (retryable), full=ok: gold => ok (fallback), rival => redirectLoop.
        "witness": _wit("redirectLoop", "ok"),
    },
    {
        "id": "weak-retry-only-redirect",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_REDIRECT_ONLY_IMPL),
        "refinement": (
            "the inverse partial miss: retry only a redirect loop and drop the status-"
            "error fallback. A lightweight probe that answers with an error status "
            "would no longer fall back to the full request, so a server that errors on "
            "the lightweight probe but answers the full request would be reported "
            "broken — regressing the pre-existing lightweight→full fallback. The "
            "PASS_TO_PASS case that pins this is test_follows_redirects_on_GET: its "
            "server refuses the lightweight method (405), so the lightweight probe "
            "ends in a status error (light=statusError) and only the fallback's own "
            "outcome (a redirect settling at 204 => full=ok) makes the locator "
            "report as redirected rather than broken. Does NOT resolve. (Deliberately "
            "NOT cited: test_follows_redirects_on_HEAD, whose server ANSWERS the "
            "lightweight method, so light=ok there, the fallback is never taken, and "
            "this rival agrees with the frozen behaviour — that test does not "
            "discriminate this rival.)"
        ),
        "rationale": (
            "REJECTED by the postcondition's retry branch at a status-error lightweight "
            "outcome: retryWithFull statusError = true, so the spec demands `full`, but "
            "the rival returns the status error. Attacks the status-error arm of "
            "retryWithFull. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # light=statusError (retryable), full=ok: gold => ok (fallback), rival => statusError.
        "witness": _wit("statusError", "ok"),
    },
    {
        "id": "weak-overcatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_OVERCATCH_IMPL),
        "refinement": (
            "retry on ANY non-success lightweight outcome is what a real patch that "
            "widened the retry clause to catch every request failure would do. It "
            "retries otherFailure outcomes (connection/TLS/other) that the change "
            "deliberately leaves authoritative, masking a genuinely-broken locator "
            "whenever the full request happens to succeed for an unrelated reason. "
            "It is BROADER than the change, which widens only to the redirect loop, "
            "so it is not the modeled behaviour and does NOT match the intended fix. "
            "Honest scope of this case: it is grounded in the postcondition's "
            "pass-through branch (below), NOT in a demonstrated test break. No "
            "PASS_TO_PASS case in this instance is known to fail under it — the "
            "TLS/connection cases do reach the modeled path with light=otherFailure, "
            "but their fallback request fails the same way against the same host, so "
            "the reported failure still satisfies those assertions; and the "
            "invalid-status case takes the separate anchor path (a full request "
            "issued directly), which never enters the modeled fragment at all. The "
            "spec is nonetheless strictly stronger than the tests here, which is why "
            "the rejection is attributed to the postcondition and witnessed below."
        ),
        "rationale": (
            "REJECTED by the postcondition's pass-through branch at an otherFailure "
            "lightweight outcome: retryWithFull otherFailure = false, so the spec pins "
            "the result to the lightweight outcome (`light`), but the rival returns the "
            "fallback. Attacks the otherFailure (non-retryable) arm. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # light=otherFailure (non-retryable), full=ok: gold => otherFailure, rival => ok.
        "witness": _wit("otherFailure", "ok"),
    },
    {
        "id": "weak-always-full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_ALWAYS_FULL_IMPL),
        "refinement": (
            "always reporting the fallback outcome (dropping the lightweight short-"
            "circuit) is what a real patch that always issued the full request would "
            "do. When the lightweight probe already succeeded it would still emit the "
            "full-request outcome, double-requesting and changing the reported result "
            "for already-working locators; for a non-retryable lightweight failure it "
            "would mask the real failure. Not the change (which keeps the lightweight "
            "outcome authoritative on success and non-retryable failures). The "
            "PASS_TO_PASS case that pins this is test_follows_redirects_on_HEAD, and "
            "the discriminating power sits ENTIRELY in its request-log assertion: its "
            "server answers the lightweight method, so the surviving OUTCOME is the "
            "same either way, but the test compares the server's logged request "
            "sequence for exact equality against two lightweight requests with no "
            "full request. A faithful always-full patch issues the extra full request "
            "and that equality fails. Does NOT resolve. (Deliberately NOT cited: "
            "test_defaults, whose modeled locators are a non-retryable connection "
            "failure and two status errors — at every one of them this rival agrees "
            "with the frozen behaviour — and which asserts only substrings plus an "
            "output line count, never a request sequence, so it cannot discriminate "
            "this rival.)"
        ),
        "rationale": (
            "REJECTED by the postcondition's pass-through branch at a successful "
            "lightweight outcome: retryWithFull ok = false, so the spec pins the result "
            "to `light` (= ok), but the rival returns the fallback. Attacks the "
            "pass-through branch from the over-emit side and, unlike the other rivals, "
            "demonstrates the spec's dependence on `full` being IGNORED in the "
            "pass-through branch. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # light=ok (non-retryable), full=statusError: gold => ok, rival => statusError.
        "witness": _wit("ok", "statusError"),
    },
]


# No consumed axioms and no opaque callees: the retry decision (retryWithFull) is
# modeled DEEPLY over the transparent ReqOutcome enum, so the axiom lane is vacuous
# here and belongs to G-AX regardless.
AXIOM_TESTS = []
