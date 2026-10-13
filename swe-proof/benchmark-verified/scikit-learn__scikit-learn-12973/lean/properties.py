"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-12973 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
case is a full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte
(region surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region
and, where a case legitimately re-proves, the ``-- proof-start`` /
``-- proof-end`` body is changed, so ``markers.same_spec`` holds and every
``theorem correct_<name>`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one modeled behavior over an optional per-call choice):

  deliveredCopy (configured : Bool) (call : Option Bool) : Bool
                result = call.getD configured

An estimator carries a configured boolean; the fitting routine also accepts an
optional per-call boolean of the same meaning. The single modeled observable is
the boolean delivered to the data-preparation step. The postcondition pins that
observable to the inputs: an explicit per-call choice takes precedence (even one
that DIFFERS from the configured value), and the configured value is used when
the caller supplies nothing. There is no free output component and no opaque
oracle — the result is grounded entirely in the two inputs.

ADVERSARIAL READ of the nagini classes on this carrier:

  * POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    implementation must still satisfy ``result = call.getD configured``; if it
    cannot, the postcondition is SPEC-TOO-STRONG. Two are carried: a two-arm
    explicit branch (per-call-present tested first, no re-binding of the mutable
    local) and a collapsed direct echo. Both keep the frozen tactic body, which
    still closes for the reshaped form.

  * ADMISSIBILITY — the nagini case built a fresh F2P-shaped input and invoked
    the routine on it, checking its precondition was establishable. The frozen
    obligation here carries NO precondition hypothesis (the modeled behavior is
    total, ``∀`` unguarded), so there is no binder to attack. The honest
    analogue confirms the obligation is SATISFIABLE at the F2P-discriminating
    ground input (a configured value True with an explicit per-call False) by
    evaluation inside the proof region, alongside the frozen obligation. If that
    ground instance could not be discharged the behavior would be unsatisfiable
    at exactly the input the F2P exercises.

  * PARTIAL-DOMAIN / VALUE (uniqueness) — APPLIES. Two rivals resolve the
    per-call choice on part of the domain but diverge on the discriminating
    sub-domain: one treats an explicit per-call False the same as an absent
    choice (routes the configured value), the other ignores the per-call choice
    entirely and always delivers the configured value. Postcondition
    ``result = call.getD configured`` catches both at ``call = some false`` with
    ``configured = true``.

  * ABSENT-CHOICE FALLTHROUGH (uniqueness) — APPLIES, and it is a distinct
    sub-domain from the two above. ``result = call.getD configured`` has TWO
    input binders, and on the ``call = some _`` sub-domain the explicit choice
    MASKS ``configured`` entirely: a rival is free to compute the fallthrough
    from anything at all and still agree with the spec everywhere an override
    is present. Two rivals exploit exactly that — they honor an explicit
    per-call choice but resolve an ABSENT one to a hardcoded constant
    (``true``, then ``false``) instead of the estimator's configured value, i.e.
    they compute ``call.getD true`` / ``call.getD false``. Both are invisible at
    ``call = some _`` and are caught only by the ``call = none`` arm, so their
    witnesses sit at ``(configured := false, call := none)`` and
    ``(configured := true, call := none)`` respectively. Together with the
    partial-domain pair this makes BOTH binders load-bearing in the battery:
    ``configured`` is varied over ``{true, false}`` and ``call`` over
    ``{none, some true, some false}``, so no rival can pass by mishandling one
    binder alone.

  * EXPLICIT-CHOICE POLARITY (uniqueness) — APPLIES. A rival that routes the
    explicit per-call choice but delivers its COMPLEMENT satisfies "the
    delivered boolean is a function of the per-call choice" while inverting it.
    Its witness sits at ``(configured := false, call := some true)`` — the
    corner no other case probes — so the battery demonstrates the spec pins the
    delivered boolean to the explicit choice's actual value, not merely to some
    function of it.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini frame-mutation rival wrote
    the read-only ``config.default_copy`` (only a half-permission was granted)
    and was rejected by the permission system. Lean is referentially
    transparent: no input carries a heap permission, there is no read-only
    half-permission to overwrite and no aliasing to exploit. Demonstrated rather
    than asserted: the closest analogue — an impl that assigns the input binder,
    ``configured := copyX.getD configured`` — is not even a well-formed rival
    here, since Lean rejects it at elaboration with ```configured` cannot be
    mutated, only variables declared using `let mut` can be mutated``. That is a
    parse-level refusal of the SHAPE, carrying no information about
    ``result = call.getD configured``, so there is no spec-attributable
    rejection to ship. This class has no expressible instance here and no
    substitute is fabricated for it.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE, and the reason is the witness
    requirement rather than the carrier's semantics. This bundle sets no
    ``loom.semantics.termination`` option (it is plain Lean + Mathlib), so the
    carrier is TOTAL: a rival whose recursion carries no decreasing measure is
    genuinely refused. Measured — an impl returning ``spin 0`` for
    ``let rec spin (n : Nat) : Bool := spin (n+1)`` fails to elaborate with
    ``fail to show termination for ...`` (exit 1), so the class is NOT vacuous;
    a diverging impl really is rejected here. What cannot be built is the
    WITNESS that would attribute that rejection to the spec. The refutation must
    ELABORATE against the rival, and both available spellings of divergence
    defeat that: with ``let rec`` the rival module never compiles, so the
    witness file fails with the same termination error rather than any claim
    about the delivered boolean; with a ``partial def`` the impl elaborates but
    is kernel-opaque, so the witness's ``decide`` cannot reduce it
    (``Tactic `decide` failed for proposition``, exit 1) — i.e.
    ``witness-unproven``, an inconclusive outcome, not a refutation. A
    ``witness_reference`` does not help: it substitutes the GOLD-side subject,
    while the half that fails here is the RIVAL side. So the rejection of a
    diverging impl on this carrier is attributable to the termination checker
    and not to ``result = call.getD configured``; recording it as a shipped
    reject case would claim spec strength that was never tested. Documented as a
    known limit of the witness lane, not fabricated as a case.

  * VALUE DOUBLE-MASK / ARRAY-EFFECT DECOUPLING — VACUOUS. The nagini
    double-mask rival resolved the preference correctly but DECOUPLED a SECOND
    observable (the array's fate, ``data.intact``) from it, caught by the nagini
    clause ``data.intact == Result()``. This carrier models a SINGLE observable
    — the boolean delivered to the data-preparation step — and does not carry a
    separate array-fate field to decouple, so this rival collapses into "the
    delivered boolean is wrong", which the partial-domain rivals already cover.
    No independent instance exists here; not fabricated.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input, stated directly against the spec predicate at ``decide``-able
literals. Each was checked to hold of its rival and to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. The five reject witnesses probe FOUR distinct input points, and
both input binders move across them:

  (configured=true,  call=some false)  explicit choice masked / discarded
  (configured=false, call=none)        absent choice hardcoded to duplicate
  (configured=true,  call=none)        absent choice hardcoded to reuse
  (configured=false, call=some true)   explicit choice inverted

That covers both arms of ``call.getD`` and both values of ``configured``, which
is what a battery needs to attest that the delivered boolean depends on BOTH
inputs. Refuting every rival on the ``call = some _`` sub-domain alone would not:
there the explicit choice masks ``configured``, so any rival that got the
fallthrough wrong — ``call.getD true``, say — would agree with the spec at every
probed point and pass while ignoring ``configured`` entirely. The two
absent-choice rivals exist to close exactly that hole.

AXIOM lane: DROPPED. The nagini bundle's ``AXIOM_TESTS`` (the A-reference deep
model of the real callee) belong to G-AX, not this gate; this carrier consumes
no ``opaque``/``axiom`` (the resolution is pure data flow), so there is no
axiom-soundness obligation to probe here.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12973"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region (after `Id.run do`) and the FULL tactic body
# of the proof region, so every replacement lands entirely inside the region it
# means to edit.
_GOLD_IMPL = (
    "  let mut copyX : CallChoice := call\n"
    "  if copyX = none then\n"
    "    copyX := some configured\n"
    "  return copyX.getD configured"
)
_GOLD_PROOF = (
    "  intro configured call\n"
    "  unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
    "  cases call with\n"
    "  | none => rfl\n"
    "  | some b => rfl"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_deliveredCopy` statement byte-identical; both
    # retain the frozen tactic body (which still closes for the reshaped form),
    # so neither introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Two-arm explicit branch: test whether an explicit per-call choice is
        # present FIRST and return it, otherwise return the configured value. No
        # re-binding of a mutable local. Same value on every input.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  match call with\n"
            "  | some b => return b\n"
            "  | none => return configured",
        ),
        "rationale": "a structurally-different but CORRECT impl (explicit two-arm "
                     "branch testing per-call-present first, no mutable re-bind) "
                     "must satisfy `result = call.getD configured`; if it cannot, "
                     "SPEC-TOO-STRONG. Proof: frozen tactic body retained "
                     "(`cases call with | none => rfl | some b => rfl` still "
                     "closes — each arm is now the definitional value).",
    },
    {
        "id": "pos-control-direct-echo",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the guard entirely into the single value it computes:
        # `call.getD configured` already resolves the optional choice. Same
        # value on every input.
        "module": _swap(_BASE, _GOLD_IMPL, "  return call.getD configured"),
        "rationale": "collapsing the resolution to the single term it computes "
                     "(`call.getD configured`) equals `result = call.getD "
                     "configured` pointwise; a correct reshape must verify. "
                     "Proof: frozen tactic body retained verbatim (`cases call "
                     "with | none => rfl | some b => rfl`; both arms are "
                     "definitional).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-discriminating input rather
    # than only provable in the abstract. The frozen theorem carries NO
    # precondition hypothesis (the modeled behavior is total, so `∀` is
    # unguarded), so the nagini precondition-admission probe has no binder to
    # attack; the honest analogue discharges the spec predicate at the ground
    # F2P input (configured True, explicit per-call False) by evaluation inside
    # the proof region, alongside the frozen obligation. If that ground instance
    # could not be discharged the behavior would be unsatisfiable at exactly the
    # input the F2P exercises.
    # =====================================================================
    {
        "id": "admissibility-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_PROOF,
            "  have _ground : problem_spec_deliveredCopy true (some false)\n"
            "      (implementation_deliveredCopy true (some false)) := by\n"
            "    unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
            "    decide\n"
            + _GOLD_PROOF,
        ),
        "rationale": "the obligation is discharged at the F2P-discriminating "
                     "ground input (configured True, explicit per-call False — "
                     "where the delivered boolean must be the per-call False, not "
                     "the configured True) by `decide`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the spec is "
                     "unsatisfiable at the normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instance is a `have` inside the existing body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================
    {
        "id": "weak-explicit-false-routes-configured",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on most of the domain but treats an explicit per-call False the
        # same as an absent choice: it routes the configured value instead of the
        # explicit False. Diverges exactly on the F2P sub-domain (per-call False,
        # configured True).
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut copyX : CallChoice := call\n"
            "  if copyX = none || copyX = some false then\n"
            "    copyX := some configured\n"
            "  return copyX.getD configured",
        ),
        "refinement": "its faithful real patch treats an explicit per-call False "
                      "the same as an absent choice: it delivers the configured "
                      "value whenever the per-call choice is False. On the F2P "
                      "case — a default estimator (configured value True) with an "
                      "explicit per-call False — the data-preparation step would "
                      "receive True and duplicate the feature matrix, leaving it "
                      "intact when the caller asked for in-place reuse. The F2P "
                      "test that asserts the per-call choice governs the "
                      "duplication would FAIL. It would NOT resolve.",
        "rationale": "REJECT from `result = call.getD configured`: at call = some "
                     "false with configured = true the spec requires the "
                     "delivered boolean be false, but this rival delivers true.",
        "witness": (
            "example : ¬ problem_spec_deliveredCopy true (some false)\n"
            "    (implementation_deliveredCopy true (some false)) := by\n"
            "  unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignores-per-call",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the per-call choice entirely and always delivers the configured
        # value. This is the pre-existing behavior of this leg (the per-call
        # choice never reaches the data-preparation step).
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut copyX : CallChoice := call\n"
            "  copyX := some configured\n"
            "  return copyX.getD configured",
        ),
        "refinement": "ignoring the per-call choice and always delivering the "
                      "configured value is exactly the pre-existing behavior: the "
                      "explicit per-call choice never reaches the data-preparation "
                      "step. On the F2P case — a default estimator (configured "
                      "value True) with an explicit per-call False — the "
                      "duplication is governed by the configured True, so the "
                      "matrix is left intact when in-place reuse was requested and "
                      "the F2P test FAILS. It would NOT resolve — this is the "
                      "leg's prepatch.",
        "rationale": "REJECT from `result = call.getD configured`: at call = some "
                     "false with configured = true the spec requires the "
                     "delivered boolean be false, but this rival delivers the "
                     "configured true (the per-call choice is discarded).",
        "witness": (
            "example : ¬ problem_spec_deliveredCopy true (some false)\n"
            "    (implementation_deliveredCopy true (some false)) := by\n"
            "  unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
            "  decide\n"
        ),
    },

    # ---- ABSENT-CHOICE FALLTHROUGH ------------------------------------------
    # The two rivals above are both refuted on the `call = some _` sub-domain,
    # where the explicit choice MASKS `configured`: any rival is free to compute
    # the absent-choice fallthrough from anything at all and still agree with the
    # spec at every input carrying an override. So neither of them makes
    # `configured` load-bearing. The next two rivals live exactly in that blind
    # spot — they honor an explicit per-call choice (indistinguishable from gold
    # there) but resolve an ABSENT one to a hardcoded constant rather than the
    # estimator's configured value, i.e. they compute `call.getD true` and
    # `call.getD false`. Only the `call = none` arm of
    # `result = call.getD configured` can see them, and it takes BOTH constants
    # to pin the fallthrough: a rival hardcoding `true` agrees with the spec at
    # `configured = true` and a rival hardcoding `false` agrees at
    # `configured = false`, so each is refuted at the OTHER configured value.
    {
        "id": "weak-absent-choice-hardcodes-duplicate",
        "kind": "uniqueness",
        "expect": "reject",
        # Honors an explicit per-call choice, but resolves an ABSENT choice to a
        # hardcoded duplicate-the-matrix true instead of the configured value:
        # `call.getD true`. Invisible on the whole `call = some _` sub-domain.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut copyX : CallChoice := call\n"
            "  if copyX = none then\n"
            "    copyX := some true\n"
            "  return copyX.getD configured",
        ),
        "refinement": "its faithful real patch resolves an absent per-call choice "
                      "to a hardcoded True rather than reading the estimator's "
                      "configured value, so the configured value never governs the "
                      "duplication at all. It happens to agree with the "
                      "F2P-discriminating input (which supplies an explicit per-call "
                      "choice), but it regresses the PRE-EXISTING behavior on the "
                      "absent-choice path: an estimator configured for in-place "
                      "reuse, fit with no per-call choice, would duplicate the "
                      "feature matrix and leave it intact. The pre-existing test "
                      "leg asserting that the configured in-place choice still "
                      "governs a fit with no per-call argument therefore FAILS. "
                      "Resolution requires the pre-existing legs to keep passing "
                      "alongside the new one, so it would NOT resolve.",
        "rationale": "REJECT from the `call = none` arm of `result = call.getD "
                     "configured`: at call = none with configured = false the spec "
                     "requires the delivered boolean be the configured false, but "
                     "this rival delivers its hardcoded true. It is refuted only "
                     "where the per-call choice is ABSENT — this is the case that "
                     "makes `configured` load-bearing, since every rival above is "
                     "refuted at an input where an explicit choice masks it.",
        "witness": (
            "example : ¬ problem_spec_deliveredCopy false none\n"
            "    (implementation_deliveredCopy false none) := by\n"
            "  unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-absent-choice-hardcodes-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite constant: an absent choice resolves to a hardcoded
        # reuse-in-place false, i.e. `call.getD false`. Needed alongside the
        # previous case because that one is refuted only at configured = false;
        # this one is refuted only at configured = true, so together they pin the
        # fallthrough to `configured` at BOTH of its values.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut copyX : CallChoice := call\n"
            "  if copyX = none then\n"
            "    copyX := some false\n"
            "  return copyX.getD configured",
        ),
        "refinement": "its faithful real patch resolves an absent per-call choice "
                      "to a hardcoded False rather than reading the estimator's "
                      "configured value. Like the previous rival it agrees with the "
                      "F2P-discriminating input (an explicit per-call choice is "
                      "supplied there), but it regresses the pre-existing "
                      "absent-choice path in the other direction: an estimator "
                      "configured to duplicate, fit with no per-call choice, would "
                      "have its feature matrix overwritten in place. The "
                      "pre-existing test leg asserting that a configured duplicate "
                      "choice still governs a fit with no per-call argument "
                      "therefore FAILS, so it would NOT resolve.",
        "rationale": "REJECT from the `call = none` arm of `result = call.getD "
                     "configured`: at call = none with configured = true the spec "
                     "requires the delivered boolean be the configured true, but "
                     "this rival delivers its hardcoded false. Refuted at the "
                     "configured value the previous case cannot reach, so the two "
                     "together show the fallthrough must be `configured` itself and "
                     "not either constant.",
        "witness": (
            "example : ¬ problem_spec_deliveredCopy true none\n"
            "    (implementation_deliveredCopy true none) := by\n"
            "  unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
            "  decide\n"
        ),
    },

    # ---- EXPLICIT-CHOICE POLARITY -------------------------------------------
    # Everything above pins the delivered boolean at three of the four
    # (configured, explicit-choice) corners. This rival is refuted at the fourth
    # — an explicit per-call choice of true against a configured false — so the
    # battery demonstrates the spec pins the delivered boolean to the explicit
    # choice's actual VALUE rather than merely to some function of it.
    {
        "id": "weak-delivers-complement",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves the optional choice exactly as gold does, then delivers the
        # complement of the resolved boolean.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut copyX : CallChoice := call\n"
            "  if copyX = none then\n"
            "    copyX := some configured\n"
            "  return !(copyX.getD configured)",
        ),
        "refinement": "its faithful real patch resolves the per-call/configured "
                      "precedence correctly and then hands the data-preparation "
                      "step the OPPOSITE boolean, so every request to duplicate "
                      "reuses in place and every request to reuse duplicates. The "
                      "F2P-discriminating input (an explicit per-call in-place "
                      "choice against a configured duplicate) would leave the "
                      "feature matrix intact, which is exactly what that test "
                      "forbids, and both pre-existing legs invert as well. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `result = call.getD configured`: at call = some "
                     "true with configured = false the spec requires the delivered "
                     "boolean be the explicit true, but this rival delivers false. "
                     "Refuted at the one (configured, explicit-choice) corner the "
                     "other rivals do not reach, so no rival can pass by matching "
                     "the spec's DEPENDENCE on the explicit choice while inverting "
                     "its value.",
        "witness": (
            "example : ¬ problem_spec_deliveredCopy false (some true)\n"
            "    (implementation_deliveredCopy false (some true)) := by\n"
            "  unfold problem_spec_deliveredCopy implementation_deliveredCopy\n"
            "  decide\n"
        ),
    },
]
