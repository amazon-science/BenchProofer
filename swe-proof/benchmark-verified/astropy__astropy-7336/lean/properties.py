"""properties.py — G-PBT falsification battery for astropy__astropy-7336 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside
the ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over an annotation abstraction):

  applyReturnAnnotation (annot : RetAnnotation) (ret : RetVal)
      : Except FinalizeError RetVal

  ``annot`` is one of three shapes: ``empty`` (no annotation), ``noUnit`` (an
  annotation present that designates *no unit at all*), ``unit u`` (an
  annotation designating a concrete unit ``u``). The finalizer turns the
  produced value ``ret`` into the final result:

    (C-unit)   annot = .unit u  →  result = .ok (convertTo ret u)
    (C-empty)  annot = .empty   →  result = .ok ret
    (C-noUnit) annot = .noUnit  →  result = .ok ret

  Load-bearing facts:
    * the result is a SUCCESS (``.ok _``) on EVERY annotation shape — there is
      no ``.error`` escape, in particular NOT on ``.noUnit`` (the discriminator);
    * on the two pass-through shapes the produced value is returned UNCHANGED
      (``.ok ret``), not a fabricated value;
    * on the concrete-unit shape the value is the CONVERTED value
      (``.ok (convertTo ret u)``), not the raw value and not a failure.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the inputs carry no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini frame-mutation rival (a
    store into the read-only input, rejected for insufficient permission) has NO
    expressible instance here and no substitute is fabricated. See 'assessment'.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``convertTo`` is an ``opaque`` A-reference
    callee (the value conversion the patch does NOT touch), but the postcondition
    is not pinned to an ungrounded answer key: it names ``convertTo ret u``
    structurally, exactly the term the impl must produce on the unit branch, and
    fully grounds the two pass-through branches in the input ``ret``. There is
    nothing an impl could echo without taking the correct branch.

  * OPAQUE-VALUE AXIS — EXPRESSIBLE, and attacked (R4). ``UnitObj`` is
    ``opaque`` with no constructor and ``convertTo`` is ``opaque`` with no
    property axiom, so neither ``ret = convertTo ret u`` nor
    ``ret ≠ convertTo ret u`` is a theorem on this carrier (both measured: a
    ``first | rfl | decide | simp | simp_all [convertTo] | aesop | omega`` attempt
    at each direction fails). That makes the value axis UNDECIDABLE at a literal,
    but NOT inexpressible: a witness need not COMPUTE the disagreement point, it
    may state its refutation at a point described by HYPOTHESIS. R4 does exactly
    that under ``ret ≠ convertTo ret u``, and because no tactic can derive
    ``False`` from an opaque inequality the gate's consistency probe confirms the
    point exists. So the nagini "always-passthrough" and "wrong-unit-on-convert"
    value rivals are NOT dropped — on this abstraction both reduce to "return
    ``ret`` on the concrete-unit arm", and R4 is that merged rival. The
    constructor axis (``.ok`` vs ``.error``) and the concrete ``RetVal`` payload
    are decidable outright; every rival below attacks one of those three axes.

  * CLAUSE x AXIS COVERAGE — the six rivals form a COMPLETE 3x2 grid over the
    three spec clauses and the two observable axes, so no clause is defended on
    only one axis:

                 .ok/.error CONSTRUCTOR axis      VALUE axis
      C-unit     R2 (.unit => .error)             R4 (.unit => .ok ret)
      C-noUnit   R1 (.noUnit => .error)           R5 (.noUnit => payload+1)
      C-empty    R6 (.empty => .error)            R3 (catch-all => payload+1)

    Nothing in the grid is redundant: each rival's witness is refuted at the
    annotation shape naming its own clause, and the two value-axis rivals on the
    pass-through shapes are kept separate because R3's witness pins at ``.empty``
    while R5's pins at ``.noUnit`` — the shape the modeled change installs.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input. Each was checked to hold of its rival and to FAIL on the
frozen solution (so it discriminates rather than asserting a tautology). Because
``RetAnnotation.unit`` carries an ``opaque UnitObj`` (uninhabited to the kernel),
the constructor-axis concrete-unit witness (R2) is stated ``∀ u`` rather than at a
literal unit — it binds a universally-quantified ``u`` in the BODY, not in the
example head, so it introduces no assumption whose satisfiability must be probed.
R4, which attacks the opaque VALUE axis, necessarily does bind in its head
(``u``, ``r``, ``hne``) and is therefore additionally subject to the gate's
consistency probe; that probe fails to derive ``False``, which is the evidence its
refutation point exists.

Each witness's gold-side failure was additionally FORGERY-tested, two ways, on
ALL SIX reject cases:

  * FLIPPED CLAIM — the same claim with the ``¬`` dropped, i.e. asserting the
    frozen impl is CORRECT at that input, built against the frozen solution:
    ELABORATES (exit 0) in all six cases, while the same flipped claim against
    the RIVAL fails (exit 1). So gold's exit code tracks what is claimed rather
    than a fixed tactic breakage — the direction of the claim, not its syntax, is
    what moves the verdict.
  * TYPE REVEAL — the witness's final step replaced by a deliberate type error on
    the reduced hypothesis (``exact (h2 : Nat)``), built on each side. Gold prints
    ``has type True``: ``simp`` PROVED the frozen impl's equation at that input.
    The R4 rival prints the concrete open equation ``r = convertTo r u`` instead,
    and the other five rivals report ``No goals to be solved`` (``simp`` closed
    the goal outright from the rival's contradictory hypothesis). That pair is a
    genuine refutation, so each ``h : True`` in a recorded ``gold_signature`` is
    a proof, not an unfolding failure.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` are empty and the deep-model
identity-soundness of ``convertTo`` belongs to G-AX (the A-reference), which the
G-PBT spec lane ignores. See 'assessment'.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7336"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region's decision: every impl reshape lands here.
_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .ok (convertTo ret u)\n"
    "  | _       => return .ok ret"
)

# The frozen obligation's two opening tactic lines — the injection point for the
# admissibility ground instance (a `have` prepended before the frozen body).
_PROOF_INTRO = (
    "  intro annot ret\n"
    "  cases annot with"
)


# === POSITIVE CONTROL (soundness) ============================================
# Structurally different but CORRECT: spell the pass-through arms explicitly and
# put them FIRST (the frozen impl folds them into a catch-all `_`). Same value
# on every annotation shape, so all three clauses still hold; MUST verify (else
# SPEC-TOO-STRONG). The frozen proof (`cases annot` + per-arm `simp_all`) closes
# unchanged for this shape, so the `correct_` statement AND its tactic body stay
# byte-identical — no new declaration, axiom, or assumption token.
_POS_IMPL = (
    "  match annot with\n"
    "  | .empty  => return .ok ret\n"
    "  | .noUnit => return .ok ret\n"
    "  | .unit u => return .ok (convertTo ret u)"
)
POS_REORDER = _swap(_BASE, _IMPL, _POS_IMPL)


# === ADMISSIBILITY (soundness) ===============================================
# The frozen `correct_` theorem carries NO precondition hypothesis (the behavior
# is total over `∀ annot ret`), so the nagini precondition-admission probe has
# no binder to attack. The honest analogue: discharge the spec predicate by
# evaluation at a representative F2P-shaped input — the `noUnit` annotation (the
# `-> None` scenario the F2P exercises), which must SUCCEED and pass the value
# through — inside the proof region, then close the frozen obligation verbatim.
# If that ground instance could not be discharged the modeled behavior would be
# unsatisfiable at exactly the shape the F2P exercises (analogue of
# PRECOND-TOO-STRONG). Nothing is assumed: the `correct_` statement is
# byte-identical and the ground instance is a `have` inside the existing body.
_ADMISS_INTRO = (
    "  have _ground : problem_spec_applyReturnAnnotation\n"
    "      RetAnnotation.noUnit { payload := 0 }\n"
    "      (implementation_applyReturnAnnotation RetAnnotation.noUnit { payload := 0 }) := by\n"
    "    refine ⟨?_, ?_, ?_⟩ <;> intro <;>\n"
    "      simp_all [implementation_applyReturnAnnotation, Id.run, pure]\n"
    "  intro annot ret\n"
    "  cases annot with"
)
ADMISS = _swap(_BASE, _PROOF_INTRO, _ADMISS_INTRO)


# === UNIQUENESS / REJECT rivals ==============================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# carries (a) the refinement argument that its faithful real patch would NOT
# resolve the F2P — so a verifying rival would be a true
# verify-does-not-imply-resolve break, not an artifact — and (b) a refutation
# witness pinning the violation at one concrete input, checked to hold of the
# rival and to FAIL on the frozen solution.

# --- (R1) NO-UNIT ATTEMPTS CONVERSION — the pre-existing bug (C-noUnit). ------
# On a present-but-no-unit annotation the finalizer attempts a conversion that
# has no convertible target and FAILS (`.error`), instead of passing the value
# through. This is the discriminating failure mode: the guard fires for ANY
# present annotation, not only a concrete unit.
_R1_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .ok (convertTo ret u)\n"
    "  | .empty  => return .ok ret\n"
    "  | .noUnit => return .error {}"
)
RIVAL_NOUNIT_ERROR = _swap(_BASE, _IMPL, _R1_IMPL)

# --- (R2) UNIT BRANCH FAILS — drop the conversion (C-unit). -------------------
# The branch DECISION is correct (only a concrete-unit annotation reaches this
# arm) but instead of converting the value it aborts (`.error`). Attacks the
# concrete-unit success clause without touching the pass-through arms.
_R2_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .error {}\n"
    "  | _       => return .ok ret"
)
RIVAL_UNIT_ERROR = _swap(_BASE, _IMPL, _R2_IMPL)

# --- (R3) PASS-THROUGH FABRICATES A VALUE (C-empty / C-noUnit frame). ---------
# The pass-through arm returns a value DERIVED from the input rather than the
# input unchanged (`{ payload := ret.payload + 1 }`). The result is still a
# success and still on the correct branch, but it is not `ret` — the frame
# analogue: an output component that must equal its input is altered.
_R3_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .ok (convertTo ret u)\n"
    "  | _       => return .ok { payload := ret.payload + 1 }"
)
RIVAL_PASS_FABRICATE = _swap(_BASE, _IMPL, _R3_IMPL)

# --- (R4) UNIT BRANCH RETURNS THE RAW VALUE — no conversion (C-unit value). ---
# The branch DECISION is correct (only a concrete-unit annotation reaches this
# arm) AND the result is a success on the correct constructor (`.ok _`), but it
# returns the SOURCE value `ret` unchanged instead of `convertTo ret u`. This is
# the load-bearing "the value is the CONVERTED value, not the raw value" clause
# (C-unit's payload), which R2 (`.error`) never touches — R2 attacks only the
# `.ok`/`.error` constructor axis. `ret = convertTo ret u` is NOT a theorem
# (both are opaque), so the witness cannot be stated at a literal; it is stated
# under the HYPOTHESIS `ret ≠ convertTo ret u` and the gate's consistency probe
# confirms that hypothesis is satisfiable (an opaque callee makes it so — no
# tactic derives `False` from `ret ≠ convertTo ret u`). This is the carrier-
# faithful merge of the two nagini value rivals (always-passthrough +
# wrong-unit-on-convert): on this abstraction both reduce to "return `ret` on
# the concrete-unit arm", and a conditioned witness discriminates it.
_R4_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .ok ret\n"
    "  | _       => return .ok ret"
)
RIVAL_UNIT_RAW = _swap(_BASE, _IMPL, _R4_IMPL)

# --- (R5) NO-UNIT SUCCEEDS BUT FABRICATES A VALUE (C-noUnit VALUE clause). -----
# The branch decision is correct (no conversion is attempted on a no-unit
# annotation) AND the result is a success (`.ok _`), but the value returned is
# derived from the produced value rather than the produced value itself. This
# isolates the C-noUnit clause's VALUE half at the annotation shape the F2P
# exercises, which no other rival's witness reaches: R1 attacks `.noUnit` only on
# the `.ok`/`.error` CONSTRUCTOR axis, and R3 (whose catch-all arm does violate
# C-noUnit as well) pins its witness at `.empty`. Spelling `.empty` out separately
# keeps this rival's only defect on the `.noUnit` arm, so its refutation cannot be
# confused with R3's.
_R5_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .ok (convertTo ret u)\n"
    "  | .empty  => return .ok ret\n"
    "  | .noUnit => return .ok { payload := ret.payload + 1 }"
)
RIVAL_NOUNIT_FABRICATE = _swap(_BASE, _IMPL, _R5_IMPL)

# --- (R6) ABSENT ANNOTATION ABORTS (C-empty CONSTRUCTOR clause). ---------------
# On an ABSENT annotation the finalizer aborts (`.error {}`) instead of passing
# the produced value through. This closes the one clause x axis cell no other
# rival reaches. Laid out as a 3x2 grid of (clause) x (axis):
#
#              .ok/.error CONSTRUCTOR axis      VALUE axis
#   C-unit     R2 (.unit => .error)             R4 (.unit => .ok ret)
#   C-noUnit   R1 (.noUnit => .error)           R5 (.noUnit => +1)
#   C-empty    R6  <-- THIS CASE                R3 (catch-all => +1, pinned @ .empty)
#
# Before this case the C-empty SUCCESS half was the only cell unattacked: R3
# perturbs the pass-through VALUE but keeps the `.ok` constructor, and R1's
# `.error` lands on `.noUnit`. So no witness in the battery discriminated a
# finalizer that REFUSES to finalize an unannotated function at all. The other
# two arms are spelled out correctly so this rival's only defect is on `.empty`.
_R6_IMPL = (
    "  match annot with\n"
    "  | .unit u => return .ok (convertTo ret u)\n"
    "  | .empty  => return .error {}\n"
    "  | .noUnit => return .ok ret"
)
RIVAL_EMPTY_ERROR = _swap(_BASE, _IMPL, _R6_IMPL)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
_P = "problem_spec_applyReturnAnnotation"
_I = "implementation_applyReturnAnnotation"

# R1: at annot = .noUnit. Spec's C-noUnit demands `.ok ret`; rival returns
# `.error {}`. Refuted via the third conjunct.
_WIT_NOUNIT = (
    f"example : ¬ {_P}\n"
    "    RetAnnotation.noUnit { payload := 0 }\n"
    f"    ({_I} RetAnnotation.noUnit {{ payload := 0 }}) := by\n"
    "  intro h\n"
    "  have h3 := h.2.2 rfl\n"
    f"  simp [{_I}, Id.run, pure] at h3\n"
)

# R2: at annot = .unit u (u universally bound in the body — UnitObj is opaque).
# Spec's C-unit demands `.ok (convertTo ret u)`; rival returns `.error {}`.
# The `.error`/`.ok` clash is decidable independently of the opaque payload.
_WIT_UNIT = (
    f"example : ∀ (u : UnitObj), ¬ {_P}\n"
    "    (RetAnnotation.unit u) { payload := 0 }\n"
    f"    ({_I} (RetAnnotation.unit u) {{ payload := 0 }}) := by\n"
    "  intro u h\n"
    "  have h1 := h.1 u rfl\n"
    f"  simp [{_I}, Id.run, pure] at h1\n"
)

# R3: at annot = .empty, ret = { payload := 5 } (varies the `ret` binder). Spec's
# C-empty demands `.ok { payload := 5 }`; rival returns `.ok { payload := 6 }`.
_WIT_PASS = (
    f"example : ¬ {_P}\n"
    "    RetAnnotation.empty { payload := 5 }\n"
    f"    ({_I} RetAnnotation.empty {{ payload := 5 }}) := by\n"
    "  intro h\n"
    "  have h2 := h.2.1 rfl\n"
    f"  simp [{_I}, Id.run, pure] at h2\n"
)

# R4: at annot = .unit u, conditioned on `ret ≠ convertTo ret u` (neither is a
# literal — both opaque). Spec's C-unit demands `.ok (convertTo ret u)`; rival
# returns `.ok ret`. The `simp` reduces the first conjunct to `ret = convertTo
# ret u`, which the hypothesis `hne` refutes. Head binds `(u) (r) (hne)`, so the
# gate runs a consistency probe on those binders; it FAILS to derive `False`
# (the opaque inequality is satisfiable), so the refutation point genuinely
# exists. Checked: elaborates vs rival, fails (semantically) vs frozen.
_WIT_UNIT_RAW = (
    f"example (u : UnitObj) (r : RetVal) (hne : r ≠ convertTo r u) :\n"
    f"    ¬ {_P} (RetAnnotation.unit u) r\n"
    f"    ({_I} (RetAnnotation.unit u) r) := by\n"
    "  intro h\n"
    "  have h1 := h.1 u rfl\n"
    f"  simp [{_I}, Id.run, pure] at h1\n"
    "  exact hne h1\n"
)


# R5: at annot = .noUnit, ret = { payload := 7 } (a THIRD payload, distinct from
# the other witnesses' 0 and 5). Spec's C-noUnit demands `.ok { payload := 7 }`;
# rival returns `.ok { payload := 8 }`. Same third conjunct R1 uses, but refuted on
# the VALUE rather than on the constructor. Binds nothing in the head, so no
# consistency probe is needed.
_WIT_NOUNIT_VALUE = (
    f"example : ¬ {_P}\n"
    "    RetAnnotation.noUnit { payload := 7 }\n"
    f"    ({_I} RetAnnotation.noUnit {{ payload := 7 }}) := by\n"
    "  intro h\n"
    "  have h3 := h.2.2 rfl\n"
    f"  simp [{_I}, Id.run, pure] at h3\n"
)



# R6: at annot = .empty, ret = { payload := 3 } (a FOURTH payload, distinct from
# the 0, 5 and 7 the other witnesses use). Spec's C-empty demands `.ok
# { payload := 3 }`; rival returns `.error {}`. Same second conjunct R3 uses, but
# refuted on the CONSTRUCTOR rather than on the value. Binds nothing in the head,
# so no consistency probe is needed.
_WIT_EMPTY_ERROR = (
    f"example : ¬ {_P}\n"
    "    RetAnnotation.empty { payload := 3 }\n"
    f"    ({_I} RetAnnotation.empty {{ payload := 3 }}) := by\n"
    "  intro h\n"
    "  have h2 := h.2.1 rfl\n"
    f"  simp [{_I}, Id.run, pure] at h2\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness)
    # =====================================================================
    {
        "id": "pos-explicit-arms-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT implementation: the two "
        "pass-through shapes are spelled out explicitly and placed first (the "
        "frozen impl folds them into a catch-all `_`), and the concrete-unit arm "
        "still returns `.ok (convertTo ret u)`. Same value on every annotation "
        "shape, so C-unit, C-empty and C-noUnit all still hold; must verify (else "
        "SPEC-TOO-STRONG). No loop/induction; the frozen `cases annot` + per-arm "
        "`simp_all` proof closes unchanged, so the `correct_` statement AND tactic "
        "body stay byte-identical — no new declaration, axiom, or assumption.",
    },

    # =====================================================================
    # ADMISSIBILITY (soundness)
    # =====================================================================
    {
        "id": "admiss-nounit-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is discharged at a representative F2P-shaped "
        "input — a present-but-no-unit annotation, which must SUCCEED and pass the "
        "produced value through — as a `have` inside the proof region, then the "
        "frozen obligation is closed verbatim. Verifies (else the behavior is "
        "unsatisfiable at exactly the shape the F2P exercises — the analogue of "
        "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, the "
        "`correct_` statement is byte-identical, the ground instance is a `have` "
        "prepended before the frozen tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "nounit-attempts-conversion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_NOUNIT_ERROR,
        "refinement": "this IS the pre-existing behavior: the finalizer converts "
        "whenever an annotation is PRESENT, excluding only the absent case. On a "
        "present-but-no-unit annotation it attempts a conversion against a target "
        "carrying no convertible unit, which fails at runtime. The F2P exercises "
        "exactly this annotation shape and asserts the finalizer SUCCEEDS and "
        "passes the value through; the conversion attempt fails instead, so this "
        "faithful patch does NOT resolve — it is the very failure the fix removes.",
        "rationale": "REJECT from C-noUnit: the result must be `.ok ret` on a "
        "no-unit annotation, but this rival returns `.error {}`. The `.ok`/`.error` "
        "constructor clash is decidable independently of the opaque conversion "
        "callee. control-flow-effect: an aborted computation the spec forbids "
        "everywhere.",
        "witness": _WIT_NOUNIT,
    },
    {
        "id": "unit-branch-fails",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_UNIT_ERROR,
        "refinement": "a faithful patch that decided to convert on a concrete-unit "
        "annotation but then failed to perform the conversion (e.g. returned an "
        "error / raised) would leave a concrete-unit-annotated function unable to "
        "produce its converted result; the P2P concrete-unit-return test asserts "
        "the finalized result carries the annotated unit, so it would FAIL — the "
        "patch does NOT resolve.",
        "rationale": "REJECT from C-unit: on a concrete-unit annotation the result "
        "must be `.ok (convertTo ret u)`, but this rival returns `.error {}`. The "
        "`.ok`/`.error` constructor clash is decidable without any property of the "
        "opaque `convertTo`. Witness stated `∀ u` because the concrete unit is an "
        "opaque, kernel-uninhabited value.",
        "witness": _WIT_UNIT,
    },
    {
        "id": "unit-branch-returns-raw-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_UNIT_RAW,
        "refinement": "a faithful patch that decided to convert on a concrete-unit "
        "annotation but then handed back the produced value UNCHANGED (keeping the "
        "source unit instead of performing the conversion) would leave a "
        "concrete-unit-annotated function's result carrying the source unit rather "
        "than the annotated one; the concrete-unit-return P2P asserts the finalized "
        "result carries the ANNOTATED unit, so it would FAIL — the patch does NOT "
        "resolve.",
        "rationale": "REJECT from C-unit's VALUE clause: on a concrete-unit "
        "annotation the result must be `.ok (convertTo ret u)`, but this rival "
        "returns `.ok ret` (the raw produced value). The branch decision and the "
        "`.ok` constructor are both correct, so R2's `.error`/`.ok` witness cannot "
        "reach this — it is the distinct 'converted value, not the raw value' fact "
        "the docstring flags as load-bearing. `ret = convertTo ret u` is not a "
        "theorem (both opaque), so the witness is stated under the hypothesis "
        "`ret ≠ convertTo ret u`; the consistency probe confirms that hypothesis is "
        "satisfiable. value-abstraction analogue of nagini's always-passthrough / "
        "wrong-unit-on-convert rivals, merged: on this carrier both reduce to "
        "returning `ret` on the concrete-unit arm.",
        "witness": _WIT_UNIT_RAW,
    },
    {
        "id": "passthrough-fabricates-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PASS_FABRICATE,
        "refinement": "a faithful patch that, on the pass-through branch, returned "
        "a value derived from the produced value rather than the produced value "
        "itself would corrupt what a no-annotation / no-unit function returns; the "
        "F2P and the pass-through P2P observe the returned object identically to "
        "the produced one, so a fabricated substitute would break those assertions "
        "— the patch does NOT resolve.",
        "rationale": "REJECT from C-empty (and equally C-noUnit): the pass-through "
        "shapes must return `.ok ret` unchanged, but this rival returns `.ok "
        "{ payload := ret.payload + 1 }`. The concrete `RetVal` payload clash is "
        "decidable. frame analogue: an output component that must equal its input "
        "is altered. Witness at `ret = { payload := 5 }` — varies the `ret` binder "
        "and exercises the payload dependence the other witnesses hold fixed.",
        "witness": _WIT_PASS,
    },
    {
        "id": "nounit-fabricates-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_NOUNIT_FABRICATE,
        "refinement": "a faithful patch that correctly declined to convert on a "
        "present-but-no-unit annotation, but then handed back a value derived from "
        "the produced value instead of the produced value itself, would leave such a "
        "function returning something other than what it computed. The F2P observes "
        "the returned object at exactly this annotation shape and asserts it is the "
        "produced one; a fabricated substitute breaks that assertion, so the patch "
        "does NOT resolve — it fixes the conversion attempt and corrupts the value.",
        "rationale": "REJECT from C-noUnit's VALUE half: on a no-unit annotation the "
        "result must be `.ok ret`, but this rival returns `.ok { payload := "
        "ret.payload + 1 }`. Distinct from every other rival: R1 attacks `.noUnit` "
        "only on the `.ok`/`.error` CONSTRUCTOR axis (its witness refutes a rival "
        "that never returns a value there at all), and R3's witness pins at "
        "`.empty`, so before this case no witness in the battery discriminated at "
        "the `.noUnit` shape on the value axis — the one clause the modeled change "
        "installs. The concrete `RetVal` payload clash is decidable, so the "
        "refutation is stated at a literal and needs no hypothesis. Witness at "
        "`ret = { payload := 7 }`, a third payload distinct from the 0 and 5 the "
        "other witnesses use.",
        "witness": _WIT_NOUNIT_VALUE,
    },
    {
        "id": "empty-annotation-aborts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_EMPTY_ERROR,
        "refinement": "a faithful patch that narrowed the pass-through so far "
        "that an ABSENT annotation no longer passed through — aborting instead of "
        "returning the produced value — would break every undecorated-return "
        "function the wrapper handles: a function with no return annotation could "
        "not return at all. The pass-through P2P calls such functions and observes "
        "their returned value, so it would FAIL — the patch does NOT resolve. It is "
        "the over-correction failure mode of the modeled change: excluding the "
        "no-unit shape from conversion is correct, but excluding the absent shape "
        "from SUCCESS is not.",
        "rationale": "REJECT from C-empty's CONSTRUCTOR half: on an absent "
        "annotation the result must be `.ok ret`, but this rival returns "
        "`.error {}`. This is the one clause x axis cell no other rival reaches — "
        "R3 perturbs the pass-through VALUE while keeping the `.ok` constructor, "
        "and R1's `.error` lands on `.noUnit`, so before this case no witness "
        "discriminated a finalizer that refuses to finalize an unannotated "
        "function at all. The other two arms are spelled out correctly, so the "
        "rival's only defect is on `.empty` and its refutation cannot be confused "
        "with R1's or R3's. The `.ok`/`.error` clash is decidable independently of "
        "the opaque conversion callee, so the witness is stated at a literal and "
        "needs no hypothesis. Witness at `ret = { payload := 3 }`, a fourth "
        "payload distinct from the 0, 5 and 7 the other witnesses use.",
        "witness": _WIT_EMPTY_ERROR,
    },
]
