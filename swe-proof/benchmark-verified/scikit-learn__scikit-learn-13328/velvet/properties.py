"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13328 (velvet).

NOT a Velvet module; a manifest the G-PBT gate parses and executes. Each SPEC
case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches ONLY text inside ``-- impl-start`` /
``-- impl-end``, or inside the elided ``prove_correct`` tactic body, both of
which the consumer spec view elides — so ``markers.same_spec`` holds by
construction and the ``prove_correct validatedElementType`` obligation survives
with a byte-identical header. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE — one contracted method over a six-way element-type carrier:

  validatedElementType (orig : DType) return (out : DType)
    ensures out = resolveElemType orig      -- CLAUSE 1 (exact resolution)
    ensures out.isFloating = true           -- CLAUSE 2 (the guarantee)

There is NO ``require`` clause: every element type is in-domain, so no witness
can be vacuously excluded by a false precondition (the tester never
short-circuits). ``orig`` is the SOLE input binder, ranging over exactly six
values — ``f64, f32, f16, boolean, integer, object`` — so the binder domain is
finite and the reject witnesses below enumerate it EXHAUSTIVELY (pts=6).

``resolveElemType orig = if orig.isAccepted then orig else .f64`` is a total,
fully-unfolded pure function of the method's own input in the ``pure`` region.
The ``axioms`` region is EMPTY — there is no opaque callee and no answer-key
oracle to echo (directive 8), so the carrier is fully transparent and every
rival is refutable by ``decide`` at a literal input. No conditioning on an
opaque term is needed anywhere in this battery.

The two clauses are INDEPENDENT and are attacked separately. Clause 2 alone is
strictly weaker than clause 1: three of the six element types are floating, so
an impl can satisfy clause 2 everywhere and still get clause 1 wrong. Three
rivals below (``weak-preserve-halfprec``, ``weak-constant-floating``,
``weak-wrong-accepted-target``) are refutable ONLY through clause 1 for exactly
that reason — they return a floating type at EVERY one of the six inputs, so
clause 2 never sees them anywhere. Conversely a rival that preserves a
non-floating input violates BOTH clauses at that input. Each rival's rationale
names which clause carries its rejection, and names it AT ITS OWN WITNESS POINT
rather than somewhere in its domain.

A note on ``weak-inverted-polarity``, because the distinction is easy to state
wrongly: it satisfies clause 2 at its own witness point (the single-precision
input, where both gold and the rival return a floating type) but NOT at every
input — it passes the three non-floating element types straight through, so
clause 2 fails there. It is therefore refutable through clause 1 AT ITS WITNESS
POINT, which is the property the case needs; it is not a rival that satisfies
clause 2 globally, and the three named above are. Measured by evaluating each
rival's tester at all six element types.

The load-bearing sub-behaviours of clause 1, each with its own rival:
  * CONVERT-NONFLOATING — a non-floating input must be converted, not passed
    through (the F2P behaviour: the reported failure is a matrix of truth
    values reaching downstream signed arithmetic unconverted);
  * CONVERT-UNACCEPTED-FLOATING — a floating input OUTSIDE the accept-list is
    ALSO converted. This is the sub-behaviour that separates "is floating" from
    "is carried through unchanged", and it is invisible to clause 2;
  * PRESERVE-ACCEPTED — an input already in the accept-list is kept AS-IS, not
    coerced to the default. Attacked by the constant-return rival;
  * TOTALITY — the resolution is pinned at EVERY element type, not merely on
    the sub-domain the failing test exercises. Attacked by the partial-domain
    rival, which is correct at five of six inputs.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case
accounting in the footer):

  * FRAME / PERMISSION-MUTATION — VACUOUS here, and NOT replaced by a
    substitute probe. The sibling's ``frame-mutation-append`` rival writes to an
    input held at half permission. Velvet and Lean are referentially
    transparent: there is no heap, no aliasing and no fractional permission;
    ``orig`` is an immutable value and the method declares no ``mut`` binder, so
    there is no read-only cell to overwrite. Per the porting map this class is
    legitimately dropped rather than fabricated.

  * CAPABILITY-TOKEN LAUNDERING — NOT PORTABLE, and this is carrier narrowing
    rather than a gap in the battery. Five sibling rivals
    (``cfe-inline-no-token``, ``forge-token-const-rep``,
    ``fabricated-const-floating-tag``, ``stale-tag-after-no-floating``, and both
    ``launder-token-*``) attack body-less abstract predicates that certify "the
    step ACTUALLY RAN, on exactly this input, with honest evidence". Those
    tokens are a Viper permission construct with no counterpart here: this
    bundle models the purely functional core — the element-type DECISION — as a
    single total function of one input, so there is no separate evidence object
    to fabricate, relabel or launder through a stand-in. What the tokens buy on
    the sibling (the step cannot be bypassed) is bought here by clause 1 pinning
    the result exactly at every input, which the rivals below attack directly.

  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. Clause 1 is
    pinned to a concrete ``def`` over the method's own argument, with an empty
    ``axioms`` region; there is nothing opaque to echo.

WITNESS MECHANICS. The frozen impl is LOOP-FREE (one boolean test and one
``if``), so its extracted tester reduces under ``decide``; each reject rival is
likewise a loop-free expression, so its tester also decides. Every reject case
therefore carries a machine-checked refutation witness — a Velvet tester
statement ``validatedElementTypeTester <elem> = false`` at ONE concrete element
type, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. BOTH halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
tester decides to ``false`` — the rival's output violates the postcondition
there) and FAILS against the frozen solution (gold's tester decides to
``true``, so ``= false`` is refuted, reported as "Tactic `decide` proved that
the proposition ... is false"). So each rejection is a genuine spec refutation,
not the mechanical tactic breakage that reshaping an impl would produce anyway.
No witness binds anything, so no witness can be inconsistent.

AXIOM lane: DROPPED. ``meta.json`` declares no consumed axioms (the one
unchanged callee is an A-reference deep model validated by G-AX), the axiom lane
is G-AX's job, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13328"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (both markers, and the comment lines, live inside the elided
# impl region). Every case edits ONLY this block, and for reshapes/admissibility
# also the elided `prove_correct` tactic body, so the spec view is untouched and
# same_spec holds by construction.
_IMPL = (
    "    -- The requested element type is the floating accept-list {f64, f32}: an\n"
    "    -- input already carrying one of these is preserved; any other element type\n"
    "    -- is converted to the first accepted floating type.\n"
    "    let accepted : Bool := orig.isAccepted\n"
    "    let out : DType := if accepted then orig else DType.f64\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view, and only the `prove_correct` HEADER must survive);
# rivals leave it untouched, so the wrong impl leaves the postcondition goal
# unsolved and the rival MODULE fails to build — which is what expect="reject"
# requires. The witness, not the module build, is what attributes the rejection
# to the spec.
_PROOF = ("prove_correct validatedElementType by\n"
          "  loom_solve\n"
          "  cases orig <;> rfl")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (correct reshapes only).

    The `prove_correct validatedElementType` header is preserved verbatim; only
    the tactic body — which the spec view elides — differs.
    """
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `validatedElementTypeTester <elem> = false` says the extracted
# ---- program's result violates the postcondition at that concrete element
# ---- type. The method has NO `require` clause, so the tester cannot
# ---- short-circuit to `true` on a false precondition and every element type is
# ---- a legitimate witness point. Checked in a file whose `prove_correct` block
# ---- has been stripped, so no tactic script can mask the verdict; both the
# ---- rival and the frozen impl are loop-free, so both testers reduce under
# ---- `decide`. The witness binds nothing, so it has no assumptions that could
# ---- be jointly unsatisfiable.
def _witness(elem):
    return ("extract_program_for validatedElementType\n"
            "prove_precondition_decidable_for validatedElementType\n"
            "prove_postcondition_decidable_for validatedElementType\n"
            "derive_tester_for validatedElementType\n\n"
            f"example : validatedElementTypeTester {elem} = false := by\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — structurally different but CORRECT: the
    # decision is delegated to the pure model directly instead of being spelled
    # out as a boolean test plus an `if`. Observationally identical on all six
    # element types, so both clauses hold on the whole domain. The proof is
    # retuned to a bare `loom_solve` (the frozen tail `cases orig <;> rfl` now
    # has no goals left to close — the body IS the clause's right-hand side, so
    # `loom_solve` finishes alone); the obligation header is byte-identical and
    # nothing is assumed. A faithful reshape MUST verify, else SPEC-TOO-STRONG.
    # Confirmed with a real build during authoring.
    # =====================================================================
    {
        "id": "pos-resolution-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- Structurally different: hand back the resolved element type\n"
            "    -- directly rather than recomputing the accept test and branch.\n"
            "    return resolveElemType orig",
            "prove_correct validatedElementType by\n  loom_solve"),
        "rationale": "a correct, structurally-different impl (the decision is "
                     "delegated to the pure resolution rather than spelled out "
                     "as an accept test plus a branch) must verify. Identical on "
                     "every one of the six element types, so BOTH clauses — "
                     "`out = resolveElemType orig` and `out.isFloating = true` — "
                     "hold on the whole domain. Rejecting it would be "
                     "SPEC-TOO-STRONG: the postcondition would be refusing its "
                     "own model's output. Only the elided tactic body is retuned; "
                     "the obligation header is byte-identical and no lemma, "
                     "axiom or `sorry` is introduced.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — CONTROL-FLOW reshape: the branch
    # condition is negated and the two arms are swapped, so the same decision is
    # reached through the opposite polarity. This is the port of the sibling's
    # branch-reshape positive. It is the exact structural neighbour of the
    # `weak-inverted-polarity` rival below — same negated test, arms NOT swapped
    # there — which is what makes this pair the sharpest available check that the
    # gate is measuring the SPEC and not the tactic script's sensitivity to
    # shape. The frozen proof closes it unchanged. Confirmed with a real build.
    # =====================================================================
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Same decision through the opposite polarity: test for a\n"
            "    -- NON-accepted element type and swap the two arms.\n"
            "    let notAccepted : Bool := ! orig.isAccepted\n"
            "    let out : DType := if notAccepted then DType.f64 else orig\n"
            "    return out"),
        "rationale": "control-flow positive control: the branch test is negated "
                     "and its arms swapped, so the impl reaches the same decision "
                     "by the opposite polarity. Observationally identical at all "
                     "six element types, so both clauses still hold and the frozen "
                     "proof closes it with no retuning. Must verify. Paired "
                     "deliberately with `weak-inverted-polarity`, which negates "
                     "the SAME test but does NOT swap the arms: the two differ by "
                     "one edit, one is correct and one is wrong, so together they "
                     "show the rejection tracks the spec rather than the impl's "
                     "syntactic shape.",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's `admiss-logical-input` re-establishes that
    # the precondition admits the F2P-shaped input. This method has NO `require`
    # clause, so admissibility cannot fail that way; the residual risk here is
    # DEGENERACY, and it is what this probe pins, via one in-region `assert` at
    # concrete element types:
    #   (a) the F2P-shaped input — a non-floating element type, the matrix of
    #       truth values the issue reports — is in-domain AND the post-image
    #       there is the converted default, not the input passed through;
    #   (b) the guarantee clause is genuinely met at that input; and
    #   (c) the post-image is NOT a constant function: an accepted floating
    #       input is preserved as ITSELF, so the two legs of the resolution are
    #       observably different.
    # Without (c) the obligation would be satisfiable by a constant, so this is
    # the probe that shows the modeled behaviour is non-trivial. The impl is kept
    # VERBATIM so the method's own obligation still discharges on its merits; the
    # proof is retuned only to clear the extra assert goals. The assert is LIVE —
    # confirmed during authoring by flipping one conjunct to a false claim, which
    # left an unsolved goal and failed the build.
    # =====================================================================
    {
        "id": "admiss-nonfloating-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `adm\n"
            "      (resolveElemType DType.boolean = DType.f64 ∧\n"
            "       (resolveElemType DType.boolean).isFloating = true ∧\n"
            "       resolveElemType DType.f32 = DType.f32))\n" + _IMPL,
            "prove_correct validatedElementType by\n"
            "  loom_solve\n"
            "  all_goals first | decide | (cases orig <;> rfl)"),
        "rationale": "admissibility + non-degeneracy. The method has no `require` "
                     "clause, so no input can be excluded; what must be shown is "
                     "that the obligation is neither unsatisfiable nor trivially "
                     "satisfiable at the inputs that matter. The in-region assert "
                     "pins three facts at concrete element types: the F2P-shaped "
                     "non-floating input resolves to the converted default (not "
                     "passed through), the guarantee clause genuinely holds there, "
                     "and an accepted floating input is preserved as ITSELF — so "
                     "the post-image is NOT a constant and the resolution's two "
                     "legs are observably distinct. The impl is kept verbatim so "
                     "the method's own `ensures` clauses discharge on their own "
                     "merits; only the elided tactic body is extended, to clear "
                     "the extra assert goals.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness at
    # a concrete element type, and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Seven rivals over the binder's six
    # values: six at DISTINCT witness points, EXHAUSTING the domain, plus one
    # added by the audit that re-attacks the F2P point through clause 1 alone.
    # =====================================================================
    {
        "id": "weak-prepatch-preserve-unless-opaque",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image behaviour: the generic policy preserves the incoming
        # element type unless it is the opaque one, converting only in that case.
        # Wrong at three of six inputs (boolean, integer, half-precision).
        # Witness placed at the INTEGER element type rather than the truth-value
        # one, so it does not duplicate the partial-domain rival's point below.
        "module": _impl(
            "    -- Generic policy: preserve the incoming element type unless it\n"
            "    -- is the opaque one, which alone is converted.\n"
            "    let isOpaque : Bool := orig = DType.object\n"
            "    let out : DType := if isOpaque then DType.f64 else orig\n"
            "    return out"),
        "refinement": "this IS the pre-image behaviour — the validation step "
                      "requests the generic numeric policy rather than the "
                      "floating accept-list, so it converts only the opaque "
                      "element type and passes every other one through. A matrix "
                      "of truth values therefore survives validation "
                      "unconverted, and the downstream signed-arithmetic step "
                      "raises on it: that is exactly the reported failure, and "
                      "the failing test asserts the fit completes on such a "
                      "matrix. A real patch with this behaviour would NOT "
                      "resolve.",
        "rationale": "REJECT from CLAUSE 1 (`out = resolveElemType orig`) via the "
                     "CONVERT-NONFLOATING and CONVERT-UNACCEPTED-FLOATING "
                     "sub-behaviours, and from CLAUSE 2 as well at the two "
                     "non-floating inputs it preserves. The resolution converts "
                     "every element type outside the accept-list; the rival "
                     "converts only the opaque one, so the two disagree at the "
                     "truth-value, integer and half-precision inputs. Verifying "
                     "would be SPEC-TOO-WEAK — the spec would not see the "
                     "reported bug at all. Refuted at the integer element type: "
                     "gold resolves it to the default floating type, the rival "
                     "keeps it integer.",
        "witness": _witness("DType.integer"),
    },
    {
        "id": "weak-identity-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate floor: no resolution at all, the input is returned as-is.
        # Cheap supporting near-miss; correct exactly on the accept-list.
        # Witness at the OPAQUE element type — the one input the pre-image rival
        # above happens to get right, so this point is not covered by it.
        "module": _impl(
            "    -- No resolution: hand the incoming element type straight back.\n"
            "    return orig"),
        "refinement": "a validation step that resolved no element type at all "
                      "would leave every input in whatever type it arrived as, "
                      "including a matrix of truth values — so the downstream "
                      "signed-arithmetic step raises exactly as reported and the "
                      "failing test still fails. It would additionally break the "
                      "numeric tests that currently pass by admitting an opaque "
                      "element type into arithmetic. It would NOT resolve.",
        "rationale": "REJECT from BOTH clauses. Clause 1 "
                     "(`out = resolveElemType orig`) fails at every element type "
                     "outside the accept-list, and clause 2 "
                     "(`out.isFloating = true`) fails at the three non-floating "
                     "ones — so this rival is the only one refutable through the "
                     "guarantee clause at its own witness point. Refuted at the "
                     "opaque element type: gold converts it to the default "
                     "floating type, the rival returns it unchanged and thereby "
                     "returns a non-floating result.",
        "witness": _witness("DType.object"),
    },
    {
        "id": "weak-partial-skip-truthvalue",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: correct at five of six element types, and wrong ONLY on
        # the sub-domain the failing test exercises. Tests that clause 1 pins the
        # resolution at EVERY input, not merely on the part that is easy.
        "module": _impl(
            "    -- Resolve correctly except on one sub-domain, where the\n"
            "    -- incoming element type is passed through instead.\n"
            "    let out : DType := if orig = DType.boolean then orig else\n"
            "      (if orig.isAccepted then orig else DType.f64)\n"
            "    return out"),
        "refinement": "a counterpart that requested the floating accept-list for "
                      "every input EXCEPT a matrix of truth values — passing that "
                      "one case through unconverted — leaves precisely the "
                      "reported input broken: the downstream signed-arithmetic "
                      "step raises on it. The failing test supplies exactly that "
                      "input and nothing else, so this rival fails it while being "
                      "correct everywhere the passing numeric tests look. It "
                      "would NOT resolve.",
        "rationale": "REJECT from CLAUSE 1 via the TOTALITY sub-behaviour, and "
                     "from CLAUSE 2 at the same point. The obligation is "
                     "universally quantified over the input binder, so one bad "
                     "sub-domain fails it even though the rival agrees with gold "
                     "at the other five element types. This is the sharpest "
                     "near-miss on the value surface — it must NOT share a "
                     "witness with the broader rivals, and its refutation point "
                     "is forced: the truth-value element type, gold's converted "
                     "default versus the rival's pass-through. Verifying would be "
                     "SPEC-TOO-WEAK on exactly the F2P sub-domain.",
        "witness": _witness("DType.boolean"),
    },
    {
        "id": "weak-preserve-halfprec",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest near-miss on the carrier: it conflates "is a floating
        # type" with "is carried through unchanged", so it preserves the
        # half-precision floating type, which the resolution converts. Wrong at
        # EXACTLY ONE of the six inputs (confirmed by testing all six during
        # authoring) — and because that input IS floating, the rival satisfies
        # CLAUSE 2 at every element type. It is therefore refutable ONLY through
        # clause 1, which is what makes it the case that proves clause 2 is not
        # carrying the battery.
        "module": _impl(
            "    -- Conflate 'already a floating type' with 'carried through\n"
            "    -- unchanged': keep any floating input, convert the rest.\n"
            "    let alreadyFloating : Bool := orig.isFloating\n"
            "    let out : DType := if alreadyFloating then orig else DType.f64\n"
            "    return out"),
        "refinement": "a counterpart that tested whether the input was ALREADY a "
                      "floating type, rather than whether it is one of the two "
                      "the accept-list names, would carry a reduced-precision "
                      "floating matrix through unconverted. The downstream "
                      "arithmetic is defined there, so the reported crash does "
                      "not reproduce — but the validated matrix no longer carries "
                      "the element type the accept-list pins, which is the "
                      "contract the change establishes and the property the "
                      "numeric tests depend on for their accuracy assertions. "
                      "This is the one rival whose faithful patch fails for a "
                      "reason OTHER than the reported crash, which is why it is "
                      "shipped separately rather than folded into the "
                      "pass-through rival: it would not resolve, and it is "
                      "invisible to the guarantee clause.",
        "rationale": "REJECT from CLAUSE 1 ALONE, via the "
                     "CONVERT-UNACCEPTED-FLOATING sub-behaviour. Every result "
                     "this rival returns is a floating type, so "
                     "`out.isFloating = true` holds at all six element types and "
                     "clause 2 cannot refute it — only the exact-resolution "
                     "clause can. It agrees with gold at five of six inputs "
                     "(verified at each during authoring) and diverges solely at "
                     "the half-precision floating type, which is floating but "
                     "NOT in the accept-list: gold converts it to the default, "
                     "the rival preserves it. This case is what demonstrates the "
                     "spec distinguishes 'floating' from 'accepted'; without it, "
                     "a rival that got that distinction wrong would verify.",
        "witness": _witness("DType.f16"),
    },
    {
        "id": "weak-inverted-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # Polarity error: the accept test is negated but the arms are NOT
        # swapped, so it converts what should be preserved and preserves what
        # should be converted. One edit away from `pos-negated-branch`, which
        # negates the same test AND swaps the arms and is correct. Also returns a
        # floating type at the accept-list inputs, so at its witness point BOTH
        # sides are floating and clause 2 is satisfied — refutable through
        # clause 1 only.
        "module": _impl(
            "    -- Polarity error: the accept test is negated but the arms are\n"
            "    -- left in place, inverting which inputs are converted.\n"
            "    let accepted : Bool := orig.isAccepted\n"
            "    let out : DType := if accepted then DType.f64 else orig\n"
            "    return out"),
        "refinement": "a counterpart with this polarity error converts the "
                      "matrices that were already in an accepted floating type "
                      "and passes through the ones that were not — including a "
                      "matrix of truth values, which then reaches the downstream "
                      "signed-arithmetic step unconverted and raises. The failing "
                      "test supplies exactly that input, so it would NOT resolve; "
                      "it would additionally perturb the element type of inputs "
                      "the currently-passing numeric tests supply.",
        "rationale": "REJECT from CLAUSE 1 via the PRESERVE-ACCEPTED "
                     "sub-behaviour (and from clause 2 as well at the "
                     "non-floating inputs it passes through, though NOT at its "
                     "witness point). The resolution keeps an accepted input as "
                     "itself; the rival replaces it with the default. Refuted at "
                     "the single-precision floating element type — an accepted "
                     "type that gold preserves and the rival rewrites to the "
                     "default. BOTH values are floating there, so clause 2 holds "
                     "at that point and the rejection is attributable to the "
                     "exact-resolution clause alone. Deliberately paired with "
                     "`pos-negated-branch`, which differs by swapping the arms "
                     "and is CORRECT.",
        "witness": _witness("DType.f32"),
    },
    {
        "id": "weak-constant-floating",
        "kind": "uniqueness",
        "expect": "reject",
        # Satisfies the GUARANTEE clause everywhere while doing no resolution at
        # all: it returns a fixed floating element type. This is the rival that
        # shows clause 2 alone would be far too weak — it holds at all six inputs
        # — and that clause 1 is what forces the actual work. Its witness point
        # completes the enumeration of the binder's six-value domain.
        "module": _impl(
            "    -- Return a fixed floating element type without performing any\n"
            "    -- resolution of the incoming one.\n"
            "    return DType.f16"),
        "refinement": "a counterpart that coerced every input to one fixed "
                      "reduced-precision floating type, ignoring the incoming "
                      "element type entirely, would stop the reported crash but "
                      "would silently downcast matrices that arrived in an "
                      "accepted type — destroying the precision the "
                      "currently-passing numeric tests assert to several decimal "
                      "places, and violating the accept-list contract the change "
                      "establishes. It would NOT resolve.",
        "rationale": "REJECT from CLAUSE 1 ALONE, via the PRESERVE-ACCEPTED "
                     "sub-behaviour. This rival is the direct evidence that "
                     "clause 2 cannot carry the spec: `out.isFloating = true` "
                     "holds at ALL SIX element types because the returned type is "
                     "floating by construction, yet the impl performs no "
                     "resolution whatsoever and ignores its input completely — a "
                     "constant function of the binder. Only "
                     "`out = resolveElemType orig` refutes it. Refuted at the "
                     "double-precision floating element type, an accepted type "
                     "gold preserves and the rival replaces; this is the sixth "
                     "and last element type, so the reject witnesses now "
                     "enumerate the binder's ENTIRE domain.",
        "witness": _witness("DType.f64"),
    },
    # =====================================================================
    # ADDED BY AUDIT. The gap the six rivals above leave: every rival that is
    # wrong on the F2P sub-domain (prepatch, identity, partial-skip) is wrong
    # there by PASSING THE INPUT THROUGH, so it returns a NON-floating element
    # type at that point and clause 2 refutes it there too. Nothing in the
    # battery attacked the F2P sub-domain in a way clause 2 cannot see, so the
    # manifest never demonstrated that CLAUSE 1 ALONE pins the F2P point — the
    # one point the failing test actually supplies.
    #
    # This rival converts the F2P input, so it is floating there and clause 2
    # holds at ALL SIX element types; but it converts it to the WRONG accepted
    # floating type. Only `out = resolveElemType orig` can refute it, and it is
    # refuted at exactly the input that matters. Confirmed with real builds:
    # module rejected (exit 1), witness elaborates against the rival (exit 0)
    # and is refuted against the frozen solution (exit 1, "Tactic `decide`
    # proved that the proposition ... is false").
    # =====================================================================
    {
        "id": "weak-wrong-accepted-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Convert the one non-floating sub-domain to the WRONG accepted\n"
            "    -- floating type; resolve every other input correctly.\n"
            "    let out : DType := if orig = DType.boolean then DType.f32 else\n"
            "      (if orig.isAccepted then orig else DType.f64)\n"
            "    return out"),
        "refinement": "a counterpart that did convert the reported input — so the "
                      "downstream signed-arithmetic step no longer raises — but "
                      "converted it to the reduced-width accepted floating type "
                      "instead of the default one would stop the reported crash "
                      "while handing downstream numeric code a matrix at the "
                      "wrong width. The accept-list's FIRST entry is the "
                      "conversion target the contract pins, and the "
                      "currently-passing numeric tests assert accuracy to "
                      "several decimal places against that width. It would NOT "
                      "resolve.",
        "rationale": "REJECT from CLAUSE 1 ALONE, at the F2P sub-domain. This is "
                     "the case the battery was missing: the other three rivals "
                     "that are wrong at the truth-value input are wrong there by "
                     "passing it through, so they return a non-floating type and "
                     "clause 2 refutes them at that very point. This rival "
                     "CONVERTS that input — to a floating type — so "
                     "`out.isFloating = true` holds at all six element types and "
                     "clause 2 cannot refute it anywhere, yet it disagrees with "
                     "the resolution at precisely the input the failing test "
                     "supplies. It shows the exact-resolution clause, not the "
                     "guarantee clause, is what pins the F2P point. Refuted at "
                     "the truth-value element type: gold converts it to the "
                     "default accepted floating type, the rival converts it to "
                     "the other one.",
        "witness": _witness("DType.boolean"),
    },
    # =====================================================================
    # ADDED BY AUDIT (soundness) — a third positive at a shape neither existing
    # positive covers: MUTABLE-ACCUMULATOR control flow. Both shipped positives
    # compute `out` as a single `let`-bound expression; this one initialises a
    # `mut` local to the default and overwrites it under a one-armed `if`, so
    # the resolution is reached by assignment rather than by an expression. A
    # faithful correct impl in that shape must verify, else SPEC-TOO-STRONG.
    # The proof needs its own retuning (the frozen `cases orig <;> rfl` tail
    # does not close the assignment-shaped goals) — only the elided tactic body
    # changes, the obligation header is byte-identical, and nothing is assumed.
    # Confirmed with a real build: exit 0.
    # =====================================================================
    {
        "id": "pos-mut-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- Correct reshape: start from the default floating element type and\n"
            "    -- overwrite it only when the incoming one is already accepted.\n"
            "    let mut out : DType := DType.f64\n"
            "    if orig.isAccepted then\n"
            "      out := orig\n"
            "    return out",
            "prove_correct validatedElementType by\n"
            "  loom_solve\n"
            "  all_goals (cases orig <;> simp_all [DType.isAccepted, DType.isFloating])"),
        "rationale": "a correct impl written with a MUTABLE accumulator — default "
                     "first, overwritten under a one-armed `if` when the incoming "
                     "element type is accepted — must verify. Observationally "
                     "identical to the frozen impl at all six element types, so "
                     "both clauses hold on the whole domain; rejecting it would be "
                     "SPEC-TOO-STRONG against a shape the spec has no business "
                     "refusing. This is a THIRD structural shape: the two other "
                     "positives both bind `out` once as an expression, whereas this "
                     "reaches the same decision by assignment, which exercises the "
                     "obligation generator's handling of a mutated local. Only the "
                     "elided tactic body is retuned; no lemma, axiom or `sorry` is "
                     "introduced.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 12 SPEC cases (1
# soundness positive, 1 admissibility, 10 uniqueness rivals) plus 3 AXIOM_TESTS.
# This battery ships 11 SPEC cases (3 positives, 1 admissibility, 7 rivals);
# two were added by the adversarial audit (pos-mut-accumulator,
# weak-wrong-accepted-target). The
# case count is LOWER because the carrier is narrower, and HIGHER on the value
# surface because this carrier makes distinctions nagini's does not.
#
# The sibling contracts THREE functions over a permission-bearing heap
# (`fit_robust_regressor`, plus the `validate_matrix` / `negate_rows` steps and
# their two body-less capability tokens). This bundle models the purely
# functional CORE — the element-type decision — as ONE total method of ONE
# input, with no heap, no permissions and no separate evidence objects. Seven of
# the sibling's ten rivals attack machinery that does not exist here.
#
#   sibling case                     -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-control-branch               -> pos-negated-branch            PORTED
#   (no sibling)                     -> pos-resolution-direct         ADDED
#   admiss-logical-input             -> admiss-nonfloating-input      PORTED (re-aimed)
#   prepatch-no-floating             -> weak-prepatch-preserve-...    PORTED
#   identity-unnegated               -> weak-identity-passthrough     PORTED
#   partial-skip-logical             -> weak-partial-skip-truthvalue  PORTED
#   (no sibling)                     -> weak-preserve-halfprec        ADDED
#   (no sibling)                     -> weak-inverted-polarity        ADDED
#   (no sibling)                     -> weak-constant-floating        ADDED
#   frame-mutation-append            -> (none)                        VACUOUS
#   cfe-inline-no-token              -> (none)                        NO CARRIER
#   forge-token-const-rep            -> (none)                        NO CARRIER
#   fabricated-const-floating-tag    -> (none)                        NO CARRIER
#   stale-tag-after-no-floating      -> (none)                        NO CARRIER
#   launder-token-dummy-rows         -> (none)                        NO CARRIER
#   launder-token-copied-rows        -> (none)                        NO CARRIER
#   (no sibling divergence case)     -> (none)                        SPEC-CLOSED
#   AXIOM_TESTS (3)                  -> (none)                        DROPPED (G-AX)
#
# PORTED (4 of 12): the three sibling rivals that attack the VALUE surface carry
#   over directly, because the sibling's value clause and this bundle's clause 1
#   pin the same decision. prepatch-no-floating -> the generic-policy rival (the
#   G-DIFF discriminator on both backends); identity-unnegated -> the
#   pass-through rival (the degenerate floor); partial-skip-logical -> the
#   partial-domain rival (correct except on the F2P sub-domain, which on this
#   carrier is the truth-value element type). pos-control-branch -> the negated
#   branch reshape. All four confirmed with real builds.
# PORTED-RE-AIMED (admissibility): the sibling asserts its precondition
#   `0 <= input_rep <= 2` admits the F2P input. This method has NO `require`
#   clause, so admissibility cannot fail that way and a literal port would be a
#   no-op that records a pass for nothing. Re-aimed at the residual risk that
#   DOES exist here — degeneracy — by asserting the F2P-shaped input resolves to
#   the converted default, the guarantee holds there, AND an accepted input is
#   preserved as itself (so the post-image is not a constant). Confirmed LIVE by
#   flipping a conjunct false and watching the build fail.
# ADDED (4): this carrier distinguishes floating-ness from accept-list
#   membership, which the sibling's three-value representation tag does not, so
#   it admits rivals with no sibling counterpart. weak-preserve-halfprec and
#   weak-constant-floating both satisfy CLAUSE 2 at every input and are
#   refutable through clause 1 ALONE — without them, the battery would never
#   show that the guarantee clause is not what is doing the work, and a rival
#   that conflated 'floating' with 'accepted' would verify. weak-inverted-polarity
#   is the one-edit neighbour of pos-negated-branch, pairing a correct and a
#   wrong reshape of the same test so the gate demonstrably tracks the spec and
#   not the tactic script's shape-sensitivity. pos-resolution-direct is a second
#   positive at a different shape (delegation rather than branching).
# VACUOUS (1): frame-mutation-append writes to an input held at half permission.
#   There is no heap, no aliasing, no fractional permission and no `mut` binder
#   here — `orig` is an immutable value — so there is no read-only cell to
#   overwrite. Not replaced by a fabricated substitute (porting map).
# NO CARRIER (6): every capability-token rival. The sibling's two body-less
#   abstract predicates certify that a step ACTUALLY RAN, on exactly this input,
#   with honest evidence — a permission construct with no counterpart on a
#   referentially-transparent backend that models the decision as a single total
#   function. There is no evidence object here to fabricate (fabricated-tag), to
#   relabel to another input (forge-token-const-rep, stale-tag), to launder
#   through a stand-in collection (both launder-token rivals), or to bypass
#   (cfe-inline-no-token). What those tokens buy on the sibling is bought here by
#   clause 1 pinning the result exactly at every input, which all six rivals
#   above attack directly. This is carrier narrowing, not an untested behaviour.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS. This bundle declares no consumed axiom — the one unchanged
#   callee is an A-reference deep model already validated == the real callee by
#   axiom_check.py — so there is nothing for a spec-lane case to probe.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct points):
#     orig — the SOLE input binder, with a six-value domain. The witnesses sit at
#            DType.integer, DType.object, DType.boolean, DType.f16, DType.f32 and
#            DType.f64: EVERY value the binder can take. Six rivals sit at six
#            distinct points; the audit's seventh deliberately RE-USES the
#            truth-value point, because sharing an input is only a defect when it
#            duplicates a rival's REASON, and this one is refuted there through a
#            clause the rival already sitting on that point cannot isolate. So no
#            rival's rationale claims a sub-domain the manifest fails to
#            demonstrate, and there is no value of the binder at which a
#            mishandling rival could hide.
#     Both top-level clauses are attacked. CLAUSE 1 (`out = resolveElemType orig`)
#     by all six rivals, across all four of its sub-behaviours:
#     CONVERT-NONFLOATING (prepatch, identity, partial-skip),
#     CONVERT-UNACCEPTED-FLOATING (prepatch, preserve-halfprec),
#     PRESERVE-ACCEPTED (inverted-polarity, constant-floating),
#     TOTALITY (partial-skip). CLAUSE 2 (`out.isFloating = true`) is attacked at
#     its own witness point by weak-identity-passthrough, and by the prepatch and
#     partial-skip rivals at the non-floating inputs they pass through.
#     THREE rivals (preserve-halfprec, constant-floating, wrong-accepted-target)
#     satisfy clause 2 at EVERY input, so they isolate clause 1 and prove the
#     weaker clause is not the one carrying the battery. The third was added by
#     the audit: it is the only clause-2-global rival whose witness point is the
#     F2P sub-domain, so it is what shows clause 1 alone pins the input the
#     failing test supplies (the other rivals wrong there pass it through, hence
#     return a non-floating type, hence are refutable by clause 2 at that point).
#     weak-inverted-polarity is NOT in that set: it satisfies clause 2 at its own
#     witness point but fails it at the three non-floating inputs it passes
#     through. Measured by evaluating every rival's tester at all six inputs.
#
# AUDIT ADDENDA (attacks D and E, all machine-checked):
#   * D probes that CORRECTLY failed to verify, i.e. found no spec hole: a
#     constant `DType.f64` return; a double-convert that rewrites f32 to the
#     default; two single-point pass-throughs at the opaque and integer inputs;
#     a swap of the two accepted types with each other; and a local shadowing of
#     the model's name returning a constant. The spec rejected every one.
#   * E reshapes that DO verify, confirming the spec is not too strong: the
#     pattern-match form, nested literal-equality tests, and the mutable
#     accumulator now shipped as `pos-mut-accumulator`.
#   * Two shapes are NOT expressible rather than rejected: `let out :| <pred>`
#     (demonic choice) fails to elaborate at all on this carrier —
#     "failed to synthesize Findable fun out => typeWithName ..." — for the
#     clause-1-exact predicate as much as for a deliberately weak one, so it is
#     a fragment limit, not a spec verdict, and neither direction is evidence
#     about this spec.
#   * The admissibility assert was re-confirmed LIVE by the audit: each of its
#     three conjuncts was independently flipped to a false claim and each flip
#     left the `adm_1` goal unsolved and failed the build.
AXIOM_TESTS = []
