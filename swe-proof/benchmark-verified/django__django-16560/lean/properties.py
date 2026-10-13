"""properties.py — G-PBT falsification battery for django__django-16560 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (three total behaviors over an ``Option String`` code domain;
``none`` is the neutral "no code configured" marker):

  validateError   (violated, code) : Option (Option String)
                  result = (if violated then some code else none)
  constraintEq    (a b : Constr)   : Bool
                  result = ((a.rest == b.rest) && (a.code == b.code))
  serializedCode  (code)           : Option String
                  result = code

ADVERSARIAL READ of the classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    no input carries a heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. This class has no expressible
    instance here and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Every postcondition is GROUNDED in the
    arguments (an equality against a term built only from the inputs, fully
    unfolded); the bundle declares no ``opaque``/``axiom``, so there is no
    answer key an implementation could echo without doing the work. In its
    place the battery carries honest cheapest-implementation POSITIVE CONTROLS
    (``pos-*``) that must verify.

  * CONTROL-FLOW-EFFECT — APPLIES to ``validateError``. Its observable is the
    raise/no-raise decision together with the payload the raise carries:
    ``result = if violated then some code else none`` pins ``some _`` to
    EXACTLY the detected-violation case, ``none`` to EXACTLY the no-violation
    case, and the carried payload to EXACTLY the configured code. Three rivals
    attack that clause (never raise, always raise, raise without the code).

  * PARTIAL-DOMAIN / VALUE — APPLIES to ``constraintEq`` and
    ``serializedCode``: a rival correct on part of the code domain but
    diverging on a sub-domain (a comparison that drops one conjunct, a
    comparison that only looks at whether a code is present rather than which,
    a ``none``-vs-``some`` split in the reconstruction data).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input. Each is stated directly against the spec predicate at
``decide``-able literals, and each was checked to hold of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

Two rivals share a refutation point only if they fail there for the same reason.
``weak-eq-code-presence-only`` is a NEAR-MISS of ``weak-eq-drops-code`` — it
agrees with the spec on the whole ``none``-vs-``some`` boundary, where the other
rival also fails — so its witness is a PAIR: one ``example`` refuting it on its
divergent sub-domain (both codes present and differing, at a comparison payload
of its own), plus one discharging the spec POSITIVELY at the presence boundary.
The second half is what makes the near-miss claim machine-checked: it holds of
this rival and of the frozen solution, and FAILS against ``weak-eq-drops-code``,
so the two rivals are demonstrably different predicates rather than one attack
written twice. The first half is what makes the snippet discriminate against
gold, which is the property the gate checks.

Witness inputs are spread across the domain rather than fixed at one convenient
point: the three ``validateError`` rivals are refuted at both settings of the
raise decision AND at both halves of the optional-code domain (the never-raises
rival at no configured code, since the raise decision is pinned independently of
the payload; the two payload rivals at a configured code, which is the only
place they can diverge).

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; each
modeled behavior is a total computation over the constraint's own data, so
there is no axiom-soundness / axiom-containment obligation to probe here (that
lane belongs to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "django__django-16560"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Each anchor is the FULL body of one impl region, or the FULL tactic body of
# one proof region, so every replacement lands entirely inside the region it
# means to edit.
_I_VALIDATE = (
    "  -- A detected violation is signalled by raising an error that carries the\n"
    "  -- configured code; no violation raises nothing.\n"
    "  if violated then\n"
    "    return some code\n"
    "  return none\n"
)
_I_EQ = "  return (a.rest == b.rest) && (a.code == b.code)\n"
_I_SER = (
    "  -- Include the code in the reconstruction data only when one is configured.\n"
    "  match code with\n"
    "  | some c => return some c\n"
    "  | none   => return none\n"
)
_P_VALIDATE = (
    "  intro violated code\n"
    "  unfold problem_spec_validateError implementation_validateError\n"
    "  cases violated <;> rfl\n"
)
_P_EQ = "  intro a b\n  rfl\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_<name>` statement byte-identical and re-proves
    # it for the new shape where the frozen script no longer applies; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-serialized-collapsed",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: collapse the two-arm case split into the single
        # echo it computes. Observationally `result = code` on every input, so
        # the frozen `cases code <;> rfl` still closes.
        "module": _swap(_BASE, _I_SER, "  return code\n"),
        "rationale": "a correct reshape of the reconstruction-data echo (the "
                     "case split collapsed to the value it returns in both arms) "
                     "must satisfy `result = code`; if it cannot, the "
                     "serializedCode postcondition is SPEC-TOO-STRONG. Proof: "
                     "the frozen tactic body is retained (`cases code <;> rfl` "
                     "still closes — one arm is now definitional).",
    },
    {
        "id": "pos-validate-carried-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-binding reshape: bind the payload before wrapping it. Same value
        # flow into the raise, so the raise/no-raise decision and the carried
        # code are unchanged.
        "module": _swap(
            _BASE, _I_VALIDATE,
            "  -- A detected violation is signalled by raising an error that carries the\n"
            "  -- configured code; no violation raises nothing.\n"
            "  if violated then\n"
            "    let carried := code\n"
            "    return some carried\n"
            "  return none\n",
        ),
        "rationale": "binding the carried payload to a local before wrapping it "
                     "keeps `result = if violated then some code else none`; a "
                     "correct reshape must verify. Proof: frozen tactic body "
                     "retained (`cases violated <;> rfl`; the local is "
                     "zeta-reduced).",
    },
    {
        "id": "pos-validate-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder of the control flow: handle the no-violation case in the
        # guard and fall through to the raise. Same raise-iff-violation
        # semantics, same carried payload.
        "module": _swap(
            _BASE, _I_VALIDATE,
            "  -- A detected violation is signalled by raising an error that carries the\n"
            "  -- configured code; no violation raises nothing.\n"
            "  if !violated then\n"
            "    return none\n"
            "  return some code\n",
        ),
        "rationale": "reordering the two exits behind a negated guard preserves "
                     "the exact raise-iff-violation decision and the carried "
                     "code, so `result = if violated then some code else none` "
                     "still holds; must verify (else SPEC-TOO-STRONG on the "
                     "validateError clause). Proof: frozen tactic body retained "
                     "(`cases violated <;> rfl` closes both branches).",
    },
    {
        "id": "pos-eq-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Conjunction reorder: optional-code term first, pre-existing payload
        # term second. `&&` is commutative, so the boolean equals the frozen
        # predicate; the postcondition pins the VALUE, not the term order. The
        # frozen `rfl` no longer closes (the two sides are not definitionally
        # equal), so the obligation is re-proved — statement byte-identical.
        "module": _swap(
            _swap(_BASE, _I_EQ, "  return (a.code == b.code) && (a.rest == b.rest)\n"),
            _P_EQ,
            "  intro a b\n"
            "  unfold problem_spec_constraintEq implementation_constraintEq\n"
            "  exact Bool.and_comm _ _\n",
        ),
        "rationale": "commuting the two equality conjuncts yields the same "
                     "boolean, so `result = ((a.rest == b.rest) && (a.code == "
                     "b.code))` still holds; must verify. Re-proved because the "
                     "frozen `rfl` is tuned to the frozen term order: the new "
                     "shape needs `Bool.and_comm` (a Mathlib/core lemma, not a "
                     "new declaration) after unfolding.",
    },
    {
        "id": "pos-serialized-presence-branch",
        "kind": "soundness",
        "expect": "verify",
        # Spell the presence decision as an explicit guard on whether a code is
        # configured, returning the value in one arm and the neutral marker in
        # the other. Same result on every input.
        "module": _swap(
            _BASE, _I_SER,
            "  -- Include the code in the reconstruction data only when one is configured.\n"
            "  match code with\n"
            "  | none   => return none\n"
            "  | some _ => return code\n",
        ),
        "rationale": "branching on whether a code is configured and returning "
                     "the neutral marker in one arm and the configured value in "
                     "the other equals `result = code` pointwise; a correct "
                     "reshape must verify. Proof: frozen tactic body retained "
                     "(`cases code <;> rfl`).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorems carry NO precondition
    # hypothesis (every modeled behavior is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack
    # here; the honest analogue is to discharge the spec predicate at a ground
    # violation-reporting input (a detected violation with a configured code)
    # by evaluation, inside the proof region, alongside the frozen obligation.
    # If that ground instance could not be discharged, the modeled behavior
    # would be unsatisfiable at exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-validate-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_VALIDATE,
            "  have _ground : problem_spec_validateError true (some \"c1\")\n"
            "      (implementation_validateError true (some \"c1\")) := by\n"
            "    unfold problem_spec_validateError implementation_validateError\n"
            "    decide\n"
            + _P_VALIDATE,
        ),
        "rationale": "the validateError obligation is discharged at a ground "
                     "violation-reporting input (a detected violation carrying a "
                     "configured code) by `decide`, then the frozen obligation is "
                     "closed verbatim. Verifies (else the spec is unsatisfiable "
                     "at the normal input, the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, and the ground instance is a "
                     "`have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break
    # rather than an artifact, and (b) a refutation witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- CONTROL-FLOW-EFFECT (validateError) ----
    {
        "id": "weak-validate-never-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the raise entirely: nothing is ever signalled, even for a
        # detected violation.
        "module": _swap(_BASE, _I_VALIDATE, "  return none\n"),
        "refinement": "a constraint that never signals a detected violation "
                      "fails the F2P tests that assert an error IS raised for a "
                      "violating candidate and inspect the code it carries; the "
                      "no-raise behavior also breaks the pre-existing "
                      "raise-on-violation contract the P2P suite relies on. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `result = if violated then some code else "
                     "none`: at violated = true the spec requires `some _` and "
                     "the rival returns `none`. Refuted at the NO-code-"
                     "configured point on purpose: the raise decision is pinned "
                     "independently of the payload, so this rival is wrong there "
                     "too, while `weak-validate-drops-code` below can only be "
                     "refuted at a CONFIGURED code (with none configured its "
                     "raise carries the same neutral marker the spec asks for). "
                     "Between the three rivals on this obligation both inputs "
                     "therefore move — `violated` over both settings and `code` "
                     "over both halves of the optional domain — rather than one "
                     "code value being probed three times.",
        "witness": (
            "-- Refuted with NO code configured: a detected violation must be\n"
            "-- signalled whatever the payload would be, so the raise decision\n"
            "-- is pinned on its own. (This rival is equally wrong at a\n"
            "-- configured code; the neutral marker is chosen so the battery\n"
            "-- probes both halves of the optional-code domain.)\n"
            "example : ¬ problem_spec_validateError true none\n"
            "    (implementation_validateError true none) := by\n"
            "  unfold problem_spec_validateError implementation_validateError\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-validate-always-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # Signals unconditionally: raises even when no violation was detected,
        # where the clause licenses `none` only.
        "module": _swap(_BASE, _I_VALIDATE, "  return some code\n"),
        "refinement": "a constraint that signals an error even when its own "
                      "(unchanged) detection found NO violation breaks every "
                      "P2P path that validates a satisfying candidate, and the "
                      "no-violation legs of the F2P tests. It would NOT resolve.",
        "rationale": "REJECT from `result = if violated then some code else "
                     "none`: at violated = false the spec requires `none` and "
                     "the rival returns `some _`.",
        "witness": (
            "example : ¬ problem_spec_validateError false (some \"c1\")\n"
            "    (implementation_validateError false (some \"c1\")) := by\n"
            "  unfold problem_spec_validateError implementation_validateError\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-validate-drops-code",
        "kind": "uniqueness",
        "expect": "reject",
        # Raises on a detected violation but carries the neutral marker instead
        # of the configured code: the raise decision is right, the payload is
        # not. This is the pre-patch behavior of this leg.
        "module": _swap(
            _BASE, _I_VALIDATE,
            "  -- Signals a detected violation but carries no code.\n"
            "  if violated then\n"
            "    return some none\n"
            "  return none\n",
        ),
        "refinement": "signalling the violation but carrying no code is exactly "
                      "the pre-existing behavior: the F2P tests that read the "
                      "code off the signalled error and compare it to the "
                      "configured one fail (they observe the neutral marker). It "
                      "would NOT resolve — this is the leg's prepatch.",
        "rationale": "REJECT from `result = if violated then some code else "
                     "none`: at violated = true with a configured code the spec "
                     "requires `some (some c)` and the rival returns "
                     "`some none`.",
        "witness": (
            "example : ¬ problem_spec_validateError true (some \"c1\")\n"
            "    (implementation_validateError true (some \"c1\")) := by\n"
            "  unfold problem_spec_validateError implementation_validateError\n"
            "  decide\n"
        ),
    },

    # ---- PARTIAL-DOMAIN / VALUE (constraintEq) ----
    {
        "id": "weak-eq-drops-code",
        "kind": "uniqueness",
        "expect": "reject",
        # Compares everything EXCEPT the optional code. Diverges on the
        # sub-domain rest-equal / codes-different (returns true where the spec
        # requires false). This is the leg's prepatch.
        "module": _swap(_BASE, _I_EQ, "  return (a.rest == b.rest)\n"),
        "refinement": "a comparison that ignores the optional code reports two "
                      "otherwise-identical constraints carrying DIFFERENT codes "
                      "as equal; the F2P equality tests assert exactly that pair "
                      "is unequal. It would NOT resolve — this is the leg's "
                      "prepatch.",
        "rationale": "REJECT from `result = ((a.rest == b.rest) && (a.code == "
                     "b.code))`: on a.rest = b.rest with a.code ≠ b.code the "
                     "rival returns true and the spec requires false.",
        "witness": (
            "example : ¬ problem_spec_constraintEq\n"
            "    { rest := \"r\", code := some \"c1\" }\n"
            "    { rest := \"r\", code := some \"c2\" }\n"
            "    (implementation_constraintEq\n"
            "      { rest := \"r\", code := some \"c1\" }\n"
            "      { rest := \"r\", code := some \"c2\" }) := by\n"
            "  unfold problem_spec_constraintEq implementation_constraintEq\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-eq-only-code",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the pre-existing comparison payload: compares ONLY the optional
        # code. Diverges where the codes agree but the payloads differ.
        "module": _swap(_BASE, _I_EQ, "  return (a.code == b.code)\n"),
        "refinement": "ignoring the pre-existing comparison payload reports two "
                      "structurally DIFFERENT constraints that merely agree on "
                      "the optional code (including two that both carry none) as "
                      "equal, breaking the pre-existing equality contract the "
                      "P2P suite and the unchanged half of the F2P equality "
                      "tests rely on. It would NOT resolve.",
        "rationale": "REJECT from `result = ((a.rest == b.rest) && (a.code == "
                     "b.code))`: on a.code = b.code with a.rest ≠ b.rest the "
                     "rival returns true and the spec requires false.",
        "witness": (
            "example : ¬ problem_spec_constraintEq\n"
            "    { rest := \"r1\", code := none }\n"
            "    { rest := \"r2\", code := none }\n"
            "    (implementation_constraintEq\n"
            "      { rest := \"r1\", code := none }\n"
            "      { rest := \"r2\", code := none }) := by\n"
            "  unfold problem_spec_constraintEq implementation_constraintEq\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-eq-code-presence-only",
        "kind": "uniqueness",
        "expect": "reject",
        # A deliberate NEAR-MISS: the code participates in the comparison, but
        # only through WHETHER one is configured, not WHICH. Agrees with the
        # spec on the whole none-vs-some boundary and diverges only on the
        # sub-domain where both codes are present and differ.
        "module": _swap(
            _BASE, _I_EQ,
            "  return (a.rest == b.rest) && (a.code.isSome == b.code.isSome)\n",
        ),
        "refinement": "comparing only whether a code is configured (not which "
                      "one) is a genuinely different predicate on the code "
                      "domain: two otherwise-identical constraints carrying two "
                      "DIFFERENT codes compare equal. An F2P equality test "
                      "asserts precisely that pair — both codes present, "
                      "different values — is unequal, so it would NOT resolve. "
                      "The refinement is the code-domain bijection: the spec "
                      "pins equality of the code VALUES, and a faithful real "
                      "patch must compare the values.",
        "rationale": "REJECT from `result = ((a.rest == b.rest) && (a.code == "
                     "b.code))`: on a.rest = b.rest with both codes present but "
                     "unequal the rival returns true and the spec requires "
                     "false. The witness is a PAIR, so the near-miss claim is "
                     "machine-checked rather than asserted: the first half "
                     "refutes the rival on its divergent sub-domain (both codes "
                     "present, values differing), and the second half discharges "
                     "the spec POSITIVELY at the presence boundary (one code "
                     "configured, the other not) — the sub-domain on which this "
                     "rival AGREES with the spec and `weak-eq-drops-code` does "
                     "not. That is exactly what separates the two rivals, so "
                     "neither shares the other's refutation point.",
        "witness": (
            # (1) the refutation proper: both codes present and differing, at a
            # comparison payload distinct from the other equality rivals' so
            # this rival's divergent point is its own.
            "example : ¬ problem_spec_constraintEq\n"
            "    { rest := \"n\", code := some \"c1\" }\n"
            "    { rest := \"n\", code := some \"c2\" }\n"
            "    (implementation_constraintEq\n"
            "      { rest := \"n\", code := some \"c1\" }\n"
            "      { rest := \"n\", code := some \"c2\" }) := by\n"
            "  unfold problem_spec_constraintEq implementation_constraintEq\n"
            "  decide\n"
            "\n"
            # (2) the NEAR-MISS attestation: on the presence boundary this rival
            # satisfies the spec, so its divergence really is confined to the
            # both-present-and-differing sub-domain. This half holds of the
            # frozen solution too — the half above is what makes the snippet
            # discriminate.
            "example : problem_spec_constraintEq\n"
            "    { rest := \"r\", code := none }\n"
            "    { rest := \"r\", code := some \"c1\" }\n"
            "    (implementation_constraintEq\n"
            "      { rest := \"r\", code := none }\n"
            "      { rest := \"r\", code := some \"c1\" }) := by\n"
            "  unfold problem_spec_constraintEq implementation_constraintEq\n"
            "  decide\n"
        ),
    },

    # ---- PARTIAL-DOMAIN / VALUE (serializedCode) ----
    {
        "id": "weak-serialized-always-surfaces",
        "kind": "uniqueness",
        "expect": "reject",
        # Always surfaces something — even for the neutral no-code marker, where
        # the clause requires the entry to be absent.
        "module": _swap(_BASE, _I_SER, "  return some (code.getD \"\")\n"),
        "refinement": "surfacing an entry in the reconstruction data even when "
                      "no code is configured makes the rebuild data advertise an "
                      "absent code; the F2P reconstruction-data test pins the "
                      "exact rebuild mapping, and an unconfigured code must be "
                      "OMITTED from it. It would NOT resolve.",
        "rationale": "REJECT from `result = code`: at code = none the spec "
                     "requires `none` and the rival returns `some _`.",
        "witness": (
            "example : ¬ problem_spec_serializedCode none\n"
            "    (implementation_serializedCode none) := by\n"
            "  unfold problem_spec_serializedCode implementation_serializedCode\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-serialized-never-surfaces",
        "kind": "uniqueness",
        "expect": "reject",
        # Never surfaces the code: a configured code is silently dropped. This
        # is the leg's prepatch, and it is also what a construction path that
        # discarded the configured code would look like from here (the echo has
        # nothing to return).
        "module": _swap(_BASE, _I_SER, "  return none\n"),
        "refinement": "never surfacing the code means a configured code is "
                      "dropped from the rebuild data; the F2P reconstruction "
                      "test asserts a configured code appears there, and the "
                      "F2P retention test asserts a configured code survives "
                      "configuration at all. It would NOT resolve — this is the "
                      "leg's prepatch.",
        "rationale": "REJECT from `result = code`: at a configured code the spec "
                     "requires `some c` and the rival returns `none`.",
        "witness": (
            "example : ¬ problem_spec_serializedCode (some \"c1\")\n"
            "    (implementation_serializedCode (some \"c1\")) := by\n"
            "  unfold problem_spec_serializedCode implementation_serializedCode\n"
            "  decide\n"
        ),
    },
]
