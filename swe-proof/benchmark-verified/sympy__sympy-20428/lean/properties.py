"""properties.py — G-PBT falsification battery for sympy__sympy-20428 (lean).

NOT a Lean file and not part of the verified artifact: a manifest of
adversarially-reasoned cases that scripts/pbt_gate.py executes and stamps a
verdict on. Every SPEC_TESTS entry is a FULL Solution.lean variant that shares
the FROZEN spec byte-for-byte (only the `-- impl-start .. -- impl-end` region
and the `-- proof-start .. -- proof-end` tactic body are edited via _swap), so
markers.same_spec holds by construction and any rejection is attributable to
the postcondition rather than to a tampered spec. AXIOM_TESTS is absent: the
axiom lane is G-AX's job and this gate ignores it (this bundle consumes no
callee axiom anyway).

PORTED FROM: nagini/properties.py. That battery is the design document; the
arguments below are its arguments, re-expressed against this backend's carrier.
See `assessment` in the submitted payload for the case-by-case disposition,
including the nagini cases that have no counterpart here and why.

DEFENDED SURFACE (why these cases and not byte-fuzz):

  ONE modeled function over a two-field carrier `ExprVal`:
    isLiteralZero -- the value's *written form* is the additive-identity constant
    isMathZero    -- the value is *determined* to denote the additive identity
  The single obligation is `theorem correct_nonzero : ∀ e, problem_spec_nonzero
  e (implementation_nonzero e)`, and the single top-level postcondition clause is
    result = !e.isMathZero
  i.e. the truthiness answer must track the DETERMINED MATHEMATICAL value and
  must be INDEPENDENT of the written form. `isLiteralZero` is an input the
  correct answer never reads — which is precisely what makes it the load-bearing
  attack surface: every wrong implementation of this behavior is one that lets
  the written form influence the answer.

  REACHABLE CARRIER STATES. The domain carries a soundness invariant: a value
  written as the additive-identity constant certainly denotes it, so
  isLiteralZero = true implies isMathZero = true. It is NOT a hypothesis on the
  obligation (which is unconditional over all of ExprVal) — it is a property of
  the modeled domain, recorded in mapping.md and asserted by the conformance
  check. Three of the four field combinations are therefore realizable:

    (isLiteralZero, isMathZero)
    (false, false)  an ordinary value that does not vanish        -> truthy
    (false, true)   THE ISSUE'S value: written non-trivially,
                    determined to vanish                          -> falsy
    (true,  true)   the bare additive-identity constant           -> falsy
    (true,  false)  excluded by the domain invariant

  The reject witnesses below probe ALL THREE realizable states and no others, so
  both input fields are varied and no rival is refuted at a point the real domain
  cannot produce. A rival refuted only at (true, false) would claim a sub-domain
  that does not exist; that point is deliberately unused.

  THE FALSIFICATION LANE ON A TACTIC-PROOF BACKEND. The frozen proof is a
  definitional `rfl`, so RESHAPING the implementation breaks the build whether or
  not the reshaped implementation is wrong. "Did not verify" therefore attributes
  nothing on its own. Every expect="reject" case accordingly carries a `witness`:
  a Lean `example` proving the rival CONTRADICTS the frozen postcondition at one
  concrete, realizable state. Each witness below was built both ways before
  shipping — it elaborates against its rival and FAILS against the frozen
  solution, so it is a real discriminator and not a tautology. The carrier is
  fully transparent (two Bools), so every witness decides at literal inputs and
  none needs to condition on an opaque term; consequently no witness binds
  anything and the joint-satisfiability question does not arise.

  NEAR-MISS SEPARATION. riv-form-override agrees with the frozen spec on MORE of
  the domain than riv-written-form does — it is correct on the issue's own state
  and wrong only on the bare-constant state — so it is refuted at its OWN
  distinguishing point (true, true) rather than sharing another rival's witness.
  Its rationale therefore claims exactly the sub-domain its witness demonstrates.

  CLASSES WITH NO COUNTERPART HERE (stated, not fabricated):

  * FRAME / PERMISSION MUTATION. Nagini's mandatory class, and its #1 weakness
    there: both nagini functions take their input at a half share, so a rival
    that WRITES the input to make the postcondition trivially establishable must
    be rejected for insufficient permission. Lean is referentially transparent —
    `e : ExprVal` is an immutable value, so a rival can rebind a LOCAL COPY but
    cannot make that write visible at `e`, and there is no permission to be
    insufficient. Demonstrated with builds rather than asserted, since "you
    cannot write" would have been too strong a claim: a rival that binds
    `let mut c := e`, overwrites `c` with the bare-constant state, and then
    answers from `e` VERIFIES (exit 0) — the write is expressible and simply
    unobservable; and one that answers from the overwritten `c` instead is
    rejected on the ordinary value clause (`⊢ False` at two states), i.e. by the
    postcondition rather than by any frame rule. So the class has no separate
    detector here: every write a rival can perform is either invisible or already
    caught by the uniqueness lane below. No substitute rival is fabricated.

  * VACUOUS NON-TERMINATION — a KNOWN SPEC HOLE on this carrier, not a vacuous
    class. Nagini carries two of these (its recorded spec-too-weak hole before an
    explicit termination obligation was added), and on the velvet sibling under
    partial-correctness termination semantics it is a known hole too
    (the corpus-wide termination-semantics finding). An earlier revision of this manifest recorded
    the class as structurally VACUOUS on lean, on the reasoning that a total Lean
    `def` admits no unbounded loop without a termination argument. That reasoning
    is WRONG, and it was refuted with real builds rather than argued:

      impl body                                              frozen proof  exit
      `while true do pure ()` then the frozen answer          unchanged     0
      `let mut r := true; while true do r := r` then same      unchanged     0

    Both are admissible variants (`variant_problems` empty, statement
    byte-identical, no new axiom/sorry). `Lean.Loop.forIn` needs no decreasing
    measure, so the loop IS writable; and because `Id`'s bind ignores a discarded
    result, a loop whose value is never observed is definitionally erased, so the
    frozen definitional proof still closes and the rival VERIFIES. Its faithful
    patch spins before answering and hangs the F2P test, so this is a real
    verify-does-not-imply-resolve break in the frozen postcondition, which is a
    pure value relation and says nothing about termination.

    Nothing is shippable as a reject case, which is why the lane stays empty:
    the rival VERIFIES, so it cannot be an expect="reject" case, and the moment
    the loop's value IS observed instead of discarded the impl stops verifying
    for the ordinary reason (the un-normalised `forIn Lean.Loop.mk` term blocks
    the definitional close) while simultaneously defeating every witness of this
    battery's shape — measured: `decide` reports "did not reduce to `isTrue` or
    `isFalse`" against that rival, so the witness cannot hold of it either.
    Repair needs a termination clause in the FROZEN obligation, which is out of
    this lane; the hole is escalated in the audit payload instead.

  * UNGROUNDED-ORACLE ECHO. Vacuous for the same reason nagini records: the
    postcondition is pinned to an input field that is itself the ground truth and
    is fully visible in the spec, not to an opaque answer key sitting in the
    module. The cheapest honest implementation IS the correct one, so there is no
    "wrong echo" to build.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20428"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgical anchors. Each lies ENTIRELY inside the region it edits and is unique
# in the frozen file, so the manifest breaks loudly if the solution ever drifts.
# ---------------------------------------------------------------------------

# The frozen implementation body (inside -- impl-start .. -- impl-end). The
# signature line is untouched by every variant, so only the body is anchored.
_IMPL_GOLD = "  return !e.isMathZero\n"

# The frozen tactic body (inside -- proof-start .. -- proof-end). The
# `theorem correct_nonzero` STATEMENT is never touched — only this body.
_PROOF_GOLD = "  intro e\n  rfl\n"


def _impl(new_body):
    """Swap ONLY the implementation body; keep the frozen proof."""
    return _swap(_BASE, _IMPL_GOLD, new_body)


def _impl_proof(new_body, new_proof):
    """Swap the implementation body AND reprove, keeping the statement fixed."""
    return _swap(_swap(_BASE, _IMPL_GOLD, new_body), _PROOF_GOLD, new_proof)


def _proof(new_proof):
    """Swap ONLY the tactic body; keep the frozen implementation."""
    return _swap(_BASE, _PROOF_GOLD, new_proof)


# The reproof every positive control uses: case-split the one observation the
# answer may depend on and discharge both arms. Closes for each reshaped body
# without a helper lemma, and keeps the obligation exactly as frozen.
_REPROOF_CASES = (
    "  intro e\n"
    "  unfold problem_spec_nonzero implementation_nonzero\n"
    "  cases e.isMathZero <;> simp\n"
)


# ===========================================================================
# SOUNDNESS / POSITIVE CONTROLS (expect="verify") — structurally DIFFERENT but
# CORRECT implementations, each with a proof that genuinely closes for its own
# shape. If one cannot be reproven, the postcondition is SPEC-TOO-STRONG.
# ===========================================================================

# Branching form, with the vanishing case tested FIRST, instead of the
# expression form. Same answer at every state, different control flow.
_POS_BRANCH = (
    "  if e.isMathZero then\n"
    "    return false\n"
    "  else\n"
    "    return true\n"
)

# Imperative accumulator: default to truthy and overwrite on the vanishing
# observation. Mirrors the imperative idiom the guide prefers; same answers.
_POS_MUT = (
    "  let mut r := true\n"
    "  if e.isMathZero then\n"
    "    r := false\n"
    "  return r\n"
)

# Boolean-equality form rather than negation. Same answers, different operator.
_POS_EQ = "  return e.isMathZero == false\n"


# ===========================================================================
# ADMISSIBILITY (expect="verify") — the obligation must be dischargeable AT the
# realizable states, in particular the issue's. Frozen implementation kept; only
# the tactic body changes.
#
# The analogue of PRECOND-TOO-STRONG on a TOTAL carrier is not "the precondition
# rejects the input" (there is no precondition to reject one) — it is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input. So this body
# first discharges `problem_spec_nonzero e (implementation_nonzero e)` AT each
# concrete realizable state, BY EVALUATION, as a standalone `have` that must
# close on its own; only then does it close the frozen obligation verbatim by the
# per-state case split. A state where the frozen implementation could not satisfy
# the postcondition fails its own `have` before the general proof is reached, so
# the failure is localized to that input rather than reported as one collapsed
# goal. The three `have`s are the three realizable states of the two input
# fields, the first being the issue's own.
# ===========================================================================
def _admiss_at(lit, math):
    """`have`: the frozen obligation holds AT this concrete state, by evaluation."""
    st = f"{{ isLiteralZero := {lit}, isMathZero := {math} }}"
    return (
        f"  have h_{lit}_{math} : problem_spec_nonzero {st}\n"
        f"      (implementation_nonzero {st}) := by\n"
        f"    unfold problem_spec_nonzero implementation_nonzero\n"
        f"    decide\n"
    )


_ADMISS_POINTWISE = (
    "  intro e\n"
    # the issue's own state: written non-trivially, determined to vanish
    + _admiss_at("false", "true")
    # the bare additive-identity constant
    + _admiss_at("true", "true")
    # an ordinary value that does not vanish
    + _admiss_at("false", "false")
    + "  obtain ⟨lit, math⟩ := e\n"
      "  cases lit <;> cases math <;>\n"
      "    unfold problem_spec_nonzero implementation_nonzero <;> decide\n"
)


# ===========================================================================
# UNIQUENESS (expect="reject") — implementations that let the WRITTEN FORM
# influence the answer. Each carries a witness refuting it at a realizable
# state, verified to elaborate against the rival and to FAIL against the frozen
# solution.
# ===========================================================================

# The historical wrong behavior: the answer is keyed on the written form alone.
_RIV_WRITTEN_FORM = "  return !e.isLiteralZero\n"

# Degenerate: nothing is ever falsy.
_RIV_ALWAYS_TRUTHY = "  return true\n"

# Degenerate the other way: everything is falsy.
_RIV_ALWAYS_FALSY = "  return false\n"

# NEAR-MISS: reads the determined value correctly, but lets the written form
# OVERRIDE it — a value written as the additive-identity constant is reported
# truthy regardless. Correct on the issue's own state; wrong only on the
# bare-constant state, so it is refuted there and not at the issue's point.
_RIV_FORM_OVERRIDE = "  return e.isLiteralZero || !e.isMathZero\n"


def _witness(lit, math):
    """A refutation at one realizable state: the frozen postcondition does NOT
    hold of the rival's answer there."""
    st = f"{{ isLiteralZero := {lit}, isMathZero := {math} }}"
    return (
        f"example : ¬ problem_spec_nonzero {st}\n"
        f"    (implementation_nonzero {st}) := by\n"
        f"  unfold problem_spec_nonzero implementation_nonzero\n"
        f"  decide\n"
    )


# The issue's own state: written non-trivially, determined to vanish.
_W_ISSUE = _witness("false", "true")
# The bare additive-identity constant.
_W_BARE = _witness("true", "true")
# An ordinary value that does not vanish.
_W_ORDINARY = _witness("false", "false")


SPEC_TESTS = [
    # ----- soundness (must verify) ----------------------------------------
    {
        "id": "pos-branch-vanishing-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_BRANCH, _REPROOF_CASES),
        "rationale": (
            "structurally-different CORRECT implementation: a two-armed branch "
            "that tests the determined-vanishing observation FIRST and returns "
            "the literal answer in each arm, instead of the single negated "
            "expression. Same answer at all three realizable states, different "
            "control flow, so the definitional `rfl` no longer applies and the "
            "obligation is REPROVEN by splitting on that observation and "
            "discharging both arms — the `theorem correct_nonzero` statement is "
            "byte-identical and no helper lemma or assumption is added. Must "
            "verify; if the postcondition `result = !e.isMathZero` cannot be "
            "re-established for an equivalent branching shape, it is "
            "SPEC-TOO-STRONG (pinning a syntactic form rather than a behavior)."
        ),
    },
    {
        "id": "pos-mut-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_MUT, _REPROOF_CASES),
        "rationale": (
            "positive control in the imperative idiom: a mutable local defaults "
            "to the truthy answer and is overwritten only on the "
            "determined-vanishing observation, then returned. Same answers as "
            "frozen at every realizable state; the data flow now runs through a "
            "mutable binding rather than a returned expression. Reproven by the "
            "same case split. Must verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-eq-against-false",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_EQ, _REPROOF_CASES),
        "rationale": (
            "positive control at the operator level: the answer is computed as a "
            "boolean EQUALITY against the non-vanishing case rather than as a "
            "negation. Same answers, different operator, so the frozen "
            "definitional proof no longer closes and the obligation is reproven. "
            "Must verify; else the postcondition would be discriminating between "
            "two spellings of one boolean function, i.e. SPEC-TOO-STRONG."
        ),
    },
    # ----- admissibility (must verify) ------------------------------------
    {
        "id": "adm-pointwise-realizable-states",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof(_ADMISS_POINTWISE),
        "rationale": (
            "admissibility, re-expressed for an UNCONDITIONAL obligation. The "
            "nagini sibling had to show its precondition (and the carrier's "
            "invariant) admitted the issue's input; here `correct_nonzero` binds "
            "no hypothesis at all, so PRECOND-TOO-STRONG cannot arise from a "
            "precondition — there is none to be too strong. The analogue on a "
            "TOTAL carrier is the obligation being UNSATISFIABLE at exactly an "
            "F2P-shaped input, and that is what this case tests directly: the "
            "frozen implementation is kept, and the tactic body first discharges "
            "`problem_spec_nonzero e (implementation_nonzero e)` AT each concrete "
            "realizable state BY EVALUATION, as a standalone `have` that must "
            "close on its own — the issue's state (written non-trivially, "
            "determined to vanish) first, then the bare additive-identity "
            "constant, then an ordinary non-vanishing value — and only then "
            "closes the frozen obligation verbatim by the per-state case split. "
            "Must verify; a state at which the postcondition were not satisfiable "
            "by the frozen implementation fails its OWN `have` before the general "
            "proof is reached, so the failure is localized to that input instead "
            "of arriving as one collapsed goal. This is the sub-domain the "
            "manifest demonstrates rather than asserts: each `have` is a "
            "machine-checked satisfiability claim at a named point of both input "
            "fields. Statement byte-identical; nothing assumed."
        ),
    },
    # ----- uniqueness (must be rejected) ----------------------------------
    {
        "id": "riv-written-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIV_WRITTEN_FORM),
        "witness": _W_ISSUE,
        "refinement": (
            "this is the historical wrong behavior: the truthiness answer is "
            "keyed on the value's WRITTEN FORM alone, so a value is reported "
            "non-vanishing unless it is written as the additive-identity "
            "constant. Its faithful real patch is the pre-fix code, which does "
            "NOT resolve: on the issue's coefficient — mathematically zero but "
            "written as a large nested-radical combination — it reports "
            "non-vanishing, the leading coefficient of the constant polynomial "
            "is therefore retained instead of stripped, and the result is the "
            "inconsistent object the public issue exhibits (it prints as the "
            "zero polynomial yet does not compare equal to it). The F2P test "
            "test_issue_20427 asserts exactly that equality and FAILS. So a "
            "rival that verified here would be a true verify-does-not-imply-"
            "resolve break, not an artifact."
        ),
        "rationale": (
            "REJECTED by the single top-level clause `result = !e.isMathZero`: at "
            "the realizable state (isLiteralZero = false, isMathZero = true) the "
            "rival answers `!false = true` where the clause demands `!true = "
            "false`. The witness states that contradiction at that literal state "
            "and was checked BOTH ways — it elaborates against this rival and "
            "fails against the frozen solution, so the rejection is attributable "
            "to the postcondition and not to the frozen `rfl` failing to match a "
            "reshaped body. Varies isMathZero against riv-always-falsy at the "
            "same isLiteralZero, isolating the determined-value binder."
        ),
    },
    {
        "id": "riv-always-truthy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIV_ALWAYS_TRUTHY),
        "witness": _W_ISSUE + "\n" + _W_BARE,
        "refinement": (
            "degenerate rival: no value is ever reported vanishing. Its faithful "
            "real patch makes the truthiness test a constant, so NO leading zero "
            "coefficient is ever stripped from a polynomial representation — not "
            "even one written as the bare additive-identity constant. The F2P "
            "test_issue_20427 equality fails as above, and the P2P zero/nonzero "
            "polynomial tests (test_Poly_zero, test_Poly_nonzero) break too, "
            "because the canonical zero representation can no longer be reached. "
            "Fails F2P and regresses P2P, so it cannot resolve."
        ),
        "rationale": (
            "REJECTED by `result = !e.isMathZero` at BOTH states where the "
            "determined value vanishes: (false, true) and (true, true). The "
            "witness refutes it at each, which is what separates this rival from "
            "riv-written-form — that one is correct at (true, true) and this one "
            "is not, so their claimed sub-domains differ and each is demonstrated "
            "rather than asserted. Both examples were checked to elaborate "
            "against this rival and to fail against the frozen solution."
        ),
    },
    {
        "id": "riv-always-falsy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIV_ALWAYS_FALSY),
        "witness": _W_ORDINARY,
        "refinement": (
            "the opposite degenerate rival: every value is reported vanishing. "
            "Its faithful real patch strips the leading coefficient of EVERY "
            "constant polynomial over this coefficient domain, collapsing "
            "ordinary non-zero constants to the canonical zero representation. "
            "Note this rival would ACCIDENTALLY satisfy the F2P assertion (the "
            "issue's polynomial does equal the zero polynomial) — and it still "
            "does not resolve, because resolution requires the PASS_TO_PASS set "
            "to hold and the non-vanishing-constant tests (test_Poly_one, "
            "test_Poly_nonzero, test_is_zero_dimensional) all break. It is "
            "carried precisely because its F2P behavior is not what refutes it: "
            "only the spec does."
        ),
        "rationale": (
            "REJECTED by `result = !e.isMathZero` at the ordinary non-vanishing "
            "state (isLiteralZero = false, isMathZero = false), where the rival "
            "answers false and the clause demands `!false = true`. This is the "
            "only reject witness probing isMathZero = false, so it is what makes "
            "the battery sensitive to the determined-value binder in BOTH "
            "directions — without it a rival wrong only on non-vanishing values "
            "would go unnoticed. Checked both ways."
        ),
    },
    {
        "id": "riv-form-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIV_FORM_OVERRIDE),
        "witness": _W_BARE,
        "refinement": (
            "NEAR-MISS: this rival reads the determined mathematical value "
            "correctly but lets the WRITTEN FORM override it, reporting any value "
            "written as the additive-identity constant as non-vanishing. Its "
            "faithful real patch resolves the issue's own case — the "
            "non-trivially-written vanishing coefficient IS stripped, so "
            "test_issue_20427 passes — while breaking the ordinary case: a "
            "polynomial whose coefficient is the bare additive-identity constant "
            "no longer strips to the canonical zero representation, so the P2P "
            "zero-polynomial tests (test_Poly_zero, test_Poly_nonzero) regress "
            "and the instance does not resolve. This is the sharpest "
            "verify-does-not-imply-resolve shape available on this carrier: it "
            "agrees with the frozen spec everywhere the F2P test looks."
        ),
        "rationale": (
            "REJECTED by `result = !e.isMathZero` at the bare-constant state "
            "(isLiteralZero = true, isMathZero = true), where the rival's "
            "disjunction answers true and the clause demands false. Because this "
            "rival AGREES with the frozen spec at the issue's state (false, "
            "true), it is deliberately NOT given riv-written-form's witness — it "
            "gets its own point, the only one at which it is wrong, so its "
            "rationale claims exactly the sub-domain the manifest demonstrates. "
            "This is also the only reject case moving isLiteralZero to true while "
            "the answer is required to stay false, which is what pins the clause's "
            "INDEPENDENCE from the written-form input: a rival that let that input "
            "leak into the answer verifies against every witness held at "
            "isLiteralZero = false. Checked both ways."
        ),
    },
]
