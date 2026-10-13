"""properties.py — G-PBT falsification battery for django__django-14915 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps a verdict onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, for a case that legitimately
re-proves, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

This battery is PORTED from the nagini sibling
(``../../nagini/properties.py``); that file is the design document. The
mechanics are re-expressed against this backend's carrier — an ``Option Int``
digest of a two-field record over an OPAQUE value-digest callee — rather than
translated.

DEFENDED SURFACE (one total function; one top-level equality clause folding
three inseparable sub-decisions):

  choiceValueHash (m : ChoiceValue) : Option Int
      result = some (valueHash m.val)

  ``ChoiceValue`` bundles a plain value ``m.val : Int`` with an accompanying
  model object ``m.inst : Option ModelInstance`` (present or absent).
  ``valueHash : Int → Int`` is the standard, UNCHANGED digest of a plain value,
  modeled ``opaque`` (no computable value, no constraining axiom). The single
  clause pins three decisions, each attacked below:

    * D1 — DIGEST IS PRODUCED AT ALL: the result is ``some _``, never ``none``.
      A wrapper that could not be used as a key would have no digest to report.
      Pinned by the ``some`` constructor.
    * D2 — THE DIGEST IS GROUNDED IN THE VALUE: the payload is
      ``valueHash m.val`` — produced by applying the value-digest callee to the
      wrapped value, not any constant. Pinned by ``m.val`` through ``valueHash``.
    * D3 — INDEPENDENCE / FRAME: the payload depends on ``m.val`` ALONE. The
      accompanying model object ``m.inst`` is a read-only input the result must
      NOT consult, so it does not appear on the right-hand side; two wrappers
      sharing a value share a digest whatever model object they carry.

ADVERSARIAL READ of the nagini classes on this carrier (see 'assessment' at the
end for the full port ledger):

  * FRAME / PERMISSION-MUTATION (nagini frame-mut-instance / frame-mut-value) —
    VACUOUS as a PERMISSION attack, demonstrated. Nagini holds both facets at
    ``Acc(...,1/2)`` and rejects a rival that WRITES one for insufficient
    permission. Lean is referentially transparent: ``m`` is a plain immutable
    value, there is no half-permission to violate and no aliasing to exploit, so
    an input-write rival has no expressible instance here. Measured: a variant
    attempting the write (``m.inst := none`` inside the ``Id.run do``) fails with
    ```m.inst` cannot be mutated, only variables declared using `let mut` can be
    mutated``, exit 1 — the write is a PARSE/elaboration rejection by the
    language, not a spec rejection, so it would attribute nothing. No permission
    substitute is fabricated. The FRAME INTENT those rivals defend — the result
    must not depend on the read-only ``m.inst`` — IS expressible as a
    read-dependence rival and is carried over as ``weak-inst-dependent`` and
    ``weak-inst-dependent-absent`` (D3) below.

  * DIVERGENCE / non-termination (nagini diverge-loop) — VACUOUS, demonstrated.
    Nagini verifies partial correctness, so it needs ``MustTerminate`` to forbid a
    ``while True`` rival that satisfies the value postconditions vacuously. A
    Lean ``def`` is definitionally TOTAL: a non-terminating body does not
    elaborate at all, so there is no diverging rival to reject. Measured on this
    carrier: a self-recursive body (``implementation_choiceValueHash m``) fails
    with ``fail to show termination for implementation_choiceValueHash … failed to
    infer structural recursion``, exit 1 — an ELABORATION failure, not a rival the
    spec rejects on the merits. Total correctness is structural here, not a spec
    clause. No substitute fabricated. (This is the vanilla-Lean backend, so the
    ``partial``-mode vacuity hole recorded in the corpus-wide termination-semantics finding for
    velvet is not in play: ``partial`` is not admissible in a variant here.)

  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. D2 pins the result to
    ``valueHash m.val``, a function of the actual input carrier ``m.val``, used
    IDENTICALLY in spec and impl. The only echo satisfying it is the gold impl
    itself (correct). There is no value a wrong echo could carry. The honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * WRONG-FIELD, literally (nagini weak-wrong-field's exact shape) —
    INEXPRESSIBLE, demonstrated. Feeding the model-object facet to the
    value-digest callee (``some (valueHash m.inst)``) does not elaborate: measured
    exit 1, ``Application type mismatch: the argument m.inst has type
    Option ModelInstance but is expected to have type ℤ``. Nagini's
    ``value_identity`` was untyped-Python-applicable to either attribute; here the
    two facets have disjoint types, so the literal wrong-field rival is not a
    wrong impl but a non-compiling file. Its INTENT (the digest keyed on the
    accompanying object rather than the value) is carried by the read-dependence
    rivals below, which is the faithful analogue on this carrier.

  * PARTIAL-DOMAIN (nagini weak-wrong-field, the pre-patch bug) — APPLIES. The
    pre-patch class exposes NO digest (unhashable), modeled as ``none``; this is
    the load-bearing ``weak-unhashable`` rival (D1), the exact bug the F2P
    exercises. Nagini's "read the WRONG field" shape (``value_identity(instance)``)
    has no direct Int-typed counterpart here — ``m.inst`` is an opaque
    ``Option ModelInstance``, not an ``Int`` the value-digest callee accepts —
    so its faithful analogue on this carrier is the read-dependence frame rival
    ``weak-inst-dependent`` (D3), which is what "the digest depends on the model
    object" means when the object cannot itself be hashed as a value.

  * VALUE / near-miss (nagini weak-const) — APPLIES as ``weak-const`` (D2): a
    constant digest ignoring the value.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen ``rfl`` is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input; each was checked with real builds to ELABORATE against its
rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). Two rivals attack an opaque-``valueHash`` VALUE decision,
so their witnesses CONDITION on the carrier (a single, satisfiable hypothesis
about ``valueHash`` at the probed value) rather than computing it; the remaining
three attack purely structural facts (``none ≠ some _``, ``x + 1 ≠ x``) and need
no hypothesis. Every gold-side failure was read, not just its exit code: each is
a SEMANTIC refutation (``⊢ False`` unsolved, or ``omega`` reporting the opaque
atom as an unconstrained counterexample), never an unknown identifier, a type
error, or a stuck reduction.

FORGERY-TESTED (second audit pass; the check that "reading the error and judging
it semantic" cannot do). Reading a gold-side error is not enough — a gold error is
admissible evidence only if it CHANGES when the CLAIM changes. So for all five
reject cases a forgery was built that differs from the witness ONLY in dropping
the ``¬`` (asserting the frozen solution SATISFIES the spec at the probed point,
the opposite of a refutation) and built against the frozen solution. Results, as
measured:

  * ``weak-unhashable``, ``weak-inst-dependent``, ``weak-inst-dependent-absent``
    — forgery ELABORATES on gold (exit 0) while the witness FAILS on gold (exit
    1). Maximal discrimination: the exit code flips with the claim, so gold's
    failure is a refutation of the concrete claim and nothing else.
  * ``weak-point-wrong`` — forgery fails with a DIFFERENT error (`No goals to be
    solved`, exit 1) than the witness (`omega could not prove the goal … a :=
    valueHash 0`). The error text tracks the claim, so the evidence is genuine;
    the forgery does not build only because the positive claim is closed by
    ``simp`` before ``omega`` is reached.
  * ``weak-const`` — HOLLOW as originally ported, and REPAIRED. Its forgery
    failed with the BYTE-IDENTICAL error to the witness, so gold's exit code
    carried no information about the claim. Full measurements and the repair are
    in that case's ``rationale``.

That is the whole reason ``weak-const``'s reducing step is plain ``simp`` and not
``simp only [Option.some.injEq]``: the difference is invisible to the gate (both
record ``rejected``) and decides whether the case attests to anything.

BINDER / POINT COVERAGE. The spec has one input binder ``m : ChoiceValue`` whose
two fields carry the whole surface. The five reject witnesses probe distinct
input points and move BOTH fields:
  * ``m.val`` — ``0`` (unhashable; point-wrong), ``5`` (const), ``7``
    (inst-dependent, both branch orientations);
  * ``m.inst`` — ``none`` (unhashable, const, point-wrong, inst-dependent-absent)
    AND ``some i`` (inst-dependent), so the model-object facet is exercised
    present AND absent.

Each point is MEANINGFUL rather than a respelling: the value-level points differ
in what they can refute (``0`` is where the point-wrong rival's substitution
lives and where the unhashable rival needs no hypothesis at all; ``5`` is a
generic non-special value), and the two ``m.inst`` orientations differ in whether
the refutation point is a CLOSED term (see the inhabitation note below).

INHABITATION OF THE OPAQUE MODEL-OBJECT TYPE (audit measurement). ``ModelInstance``
is ``opaque``, and the carrier proves neither ``Nonempty ModelInstance`` nor
``IsEmpty ModelInstance`` — both were built against the frozen file and both
FAILED to elaborate (exit 1, goal unsolved). Consequences, both handled:
  * an ``∀ (i : ModelInstance), …`` discharge is not known to be witnessed by any
    actual input, so it cannot be the SOLE ground of an admissibility control —
    ``admiss-instance-present-ground`` therefore also discharges at ``⟨1, none⟩``,
    an input needing no inhabitant;
  * a refutation stated over a bound ``(i : ModelInstance)`` is a refutation for
    ANY given model object rather than one at an exhibited input, so the frame
    clause is attacked at a closed point too by ``weak-inst-dependent-absent``.

AXIOM lane: DROPPED. ``valueHash`` is a deep-model reference (meta.json
axioms == []; deep_model_references == ["valueHash"]); the axiom lane is G-AX's
job and this gate ignores it. AXIOM_TESTS is empty.

INDEPENDENT SPEC PROBES (second audit pass, all with real builds). Ten NEW
variants the battery does not contain were built against the frozen spec, to test
the spec in both directions rather than to add cases:

  * SPEC-TOO-WEAK (six new WRONG impls, all correctly REJECTED, exit 1): the
    digest of a shifted value (``valueHash (m.val + 1)``), a negated digest
    (``-valueHash m.val``), a scaled digest (``2 * valueHash m.val``), a
    sign-split constant substitution, a doubly-applied digest
    (``valueHash (valueHash m.val)``), and a ``partial`` self-recursive body.
    None verifies, so no spec hole was found. The first five are value-level
    near-misses aimed at what the shipped rivals leave unattacked; each fails on
    the frozen ``rfl``, which is why they are NOT added as cases — a rejection
    without a witness attributes nothing, and each would need its own
    conditional witness that duplicates ``weak-const``'s D2 attack.
  * SPEC-TOO-STRONG (four new CORRECT reshapes, all VERIFY, exit 0): a
    pattern-matching definition over the record (``| ⟨v, _⟩ => some (valueHash
    v)``), a ``let mut`` accumulator initialised to ``none``, a both-branches-equal
    ``match`` on ``m.inst`` (the shape a frame-respecting rival takes), and
    ``Option.map valueHash (some m.val)``. All four close the obligation with the
    STATEMENT byte-identical, two of them needing only the frozen tactic body. So
    the spec admits faithful reshapes and is not over-tuned to the frozen form.

DIVERGENCE, against the semantics this bundle actually sets: this is the vanilla
Lean backend and the frozen file carries NO
``set_option loom.semantics.termination`` line at all (that option is velvet's;
the sibling velvet Solution.lean sets it to "total"). A Lean ``def`` is total by
elaboration, so the disposition is neither "total-mode reject case" nor
"partial-mode known hole" — it is VACUOUS, re-measured here three ways: a
self-recursive body fails with ``fail to show termination for
implementation_choiceValueHash`` (exit 1); a ``partial def`` body IS admitted by
the language but is then irreducible, so a witness against it dies at
``Tactic `unfold` failed to unfold `implementation_choiceValueHash``` (exit 1) —
i.e. it cannot be refuted, but it also cannot be a case, because that failure is
a stuck unfold the gate screens rather than a refutation. There is no diverging
rival that is both admissible and refutable on this carrier.
"""
from pathlib import Path

INSTANCE = "django__django-14915"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL frozen impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do\n"
    "  -- the digest is the standard digest of the wrapped value; the accompanying\n"
    "  -- model object is not consulted\n"
    "  return some (valueHash m.val)"
)

_PROOF_GOLD = (
    "  intro m\n"
    "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
    "  rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl-region body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (must VERIFY).
# ---------------------------------------------------------------------------

# soundness: a structurally different but CORRECT impl — the mutable-accumulator
# `Id.run do` is dropped for a single functional expression. Same value on every
# input; the frozen `rfl` still closes the reshaped form (both sides reduce to
# `some (valueHash m.val)`), so the obligation is re-proved with the STATEMENT
# byte-identical and no new lemma/axiom/assumption.
_POS_IMPL = (
    "def implementation_choiceValueHash (m : ChoiceValue) : Option Int :=\n"
    "  some (valueHash m.val)"
)
_POS_PROOF = (
    "  intro m\n"
    "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
    "  rfl"
)

# admissibility: the gold impl verbatim, but the proof FIRST discharges the
# obligation at TWO ground inputs before closing the frozen obligation verbatim.
# If a ground instance could not be discharged, the modeled behavior would be
# unsatisfiable at the normal input (the analogue of PRECOND-TOO-STRONG).
#
# AUDIT REPAIR (was: a single `∀ (i : ModelInstance), … ⟨1, some i⟩` discharge).
# `ModelInstance` is `opaque`, so NOTHING in the spec view establishes it is
# inhabited — measured: `example : Nonempty ModelInstance` FAILS to elaborate
# against the frozen file (exit 1, `⊢ Nonempty ModelInstance` unsolved), and so
# does `example : IsEmpty ModelInstance` (exit 1). The carrier leaves it
# undecided in BOTH directions. A `∀ i, P i` discharge is therefore not known to
# be witnessed by any actual input: if `ModelInstance` were empty it would hold
# VACUOUSLY, which is exactly the shape an admissibility control must not have —
# it would attest to satisfiability at a point that may not exist. So the
# ground-discharge at an input that PROVABLY exists (`⟨1, none⟩`, needing no
# inhabitant) is added and carries the admissibility claim; the
# instance-present discharge is KEPT alongside it, because on the sub-domain
# where a model object does exist it is the F2P-shaped input, and it is honest
# as a universally-quantified statement — it just cannot be the sole ground.
_ADMISS_PROOF = (
    "  have _ground_absent : problem_spec_choiceValueHash ⟨1, none⟩\n"
    "      (implementation_choiceValueHash ⟨1, none⟩) := by\n"
    "    unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
    "    rfl\n"
    "  have _ground_present : ∀ (i : ModelInstance),\n"
    "      problem_spec_choiceValueHash ⟨1, some i⟩\n"
    "        (implementation_choiceValueHash ⟨1, some i⟩) := by\n"
    "    intro i\n"
    "    unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
    "    rfl\n"
    "  intro m\n"
    "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input (checked with real builds).
# ---------------------------------------------------------------------------

# weak-unhashable (D1) — the PRE-PATCH behavior: the wrapper exposes no digest,
# so obtaining one does not succeed. Modeled as `none`.
_WEAK_UNHASHABLE = (
    "def implementation_choiceValueHash (_m : ChoiceValue) : Option Int :=\n"
    "  none"
)

# weak-const (D2) — a constant digest ignoring the wrapped value entirely.
_WEAK_CONST = (
    "def implementation_choiceValueHash (_m : ChoiceValue) : Option Int :=\n"
    "  some 0"
)

# weak-inst-dependent (D3 / frame) — the digest CONSULTS the accompanying model
# object: it differs depending on whether one is present. On the absent facet it
# agrees with gold; when a model object is present it perturbs the digest, so it
# violates the independence the frame clause pins.
_WEAK_INST_DEPENDENT = (
    "def implementation_choiceValueHash (m : ChoiceValue) : Option Int :=\n"
    "  match m.inst with\n"
    "  | none => some (valueHash m.val)\n"
    "  | some _ => some (valueHash m.val + 1)"
)

# weak-inst-dependent-absent (D3 / frame, ADDED BY AUDIT) — the SAME frame
# violation as `weak-inst-dependent`, with the perturbed branch moved to the
# model-object-ABSENT facet. Rationale for adding it: `weak-inst-dependent` can
# only be refuted at an input carrying `some i`, i.e. at a point whose existence
# needs an inhabitant of the `opaque ModelInstance`, and the carrier proves
# neither `Nonempty ModelInstance` nor `IsEmpty ModelInstance` (both measured to
# fail elaboration). Its witness binds `(i : ModelInstance)` and so is only ever
# a CONDITIONAL refutation — sound, and the gate's consistency probe cannot
# derive `False` from it, but it does not exhibit an input known to exist. This
# rival's refutation point `⟨7, none⟩` is a closed term needing no inhabitant,
# so the frame clause is attacked at an UNCONDITIONALLY existing input too.
_WEAK_INST_DEPENDENT_ABSENT = (
    "def implementation_choiceValueHash (m : ChoiceValue) : Option Int :=\n"
    "  match m.inst with\n"
    "  | none => some (valueHash m.val + 1)\n"
    "  | some _ => some (valueHash m.val)"
)

# weak-point-wrong (D2 / partial-domain, ADDED BY AUDIT) — a PARTIAL-DOMAIN
# near-miss the battery lacked: the digest is the value's own digest everywhere
# EXCEPT at one value, where a constant is substituted. Both existing D2/D3
# rivals are wrong on a whole facet (`weak-const` on every input, and each
# inst-dependent rival on an entire `m.inst` branch); nothing probed a rival that
# agrees with gold on all but a MEASURE-ZERO slice, which is the shape that
# survives a spec pinning only "the digest is derived from the value somehow".
_WEAK_POINT_WRONG = (
    "def implementation_choiceValueHash (m : ChoiceValue) : Option Int :=\n"
    "  some (if m.val = 0 then 0 else valueHash m.val)"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different CORRECT impl that
    # MUST verify; else the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_GOLD, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` for "
            "a single functional expression (`some (valueHash m.val)`) must "
            "satisfy `result = some (valueHash m.val)`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. After `unfold` both sides reduce to the same term, "
            "so the obligation closes by `rfl` with the STATEMENT byte-identical "
            "and no new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is discharged at the F2P ground input (value
    # present alongside a model object) before the frozen obligation, confirming
    # the modeled behavior is satisfiable at the normal input. The frozen theorem
    # carries no precondition hypothesis (the behavior is total), so nagini's
    # precondition-admission probe has no binder to attack; the honest analogue
    # is this ground discharge.
    # =====================================================================
    {
        "id": "admiss-instance-present-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground input — a "
            "wrapper `⟨1, some i⟩` whose value is present ALONGSIDE a model object "
            "`i : ModelInstance` (exactly what the F2P constructs: a pk with its "
            "instance) — by `rfl`, then the frozen obligation is closed verbatim. "
            "Verifies (else the spec is unsatisfiable at the normal input, the "
            "analogue of PRECOND-TOO-STRONG). Nothing is assumed: the STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals.
    # =====================================================================
    {
        "id": "weak-unhashable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_UNHASHABLE),
        "refinement": (
            "this is the PRE-PATCH behavior: the wrapper defines a value-based "
            "equality but supplies no digest, so it cannot be used as a dict key / "
            "set member — obtaining a digest does not succeed (`TypeError: "
            "unhashable type`). Its faithful real patch is the unchanged repo, "
            "under which the F2P `test_choice_value_hash` raises when it hashes the "
            "wrapper — the test never reaches its assertions. It does NOT resolve; "
            "this is exactly the bug the spec must sense (G-DIFF)."
        ),
        "rationale": (
            "REJECT from clause D1 of `result = some (valueHash m.val)`: the spec "
            "demands a produced digest (`some _`), but the rival returns `none`, "
            "and `none = some _` is unprovable. Refuted at a bare wrapper "
            "`⟨0, none⟩` (no model object); needs no carrier hypothesis because "
            "`none ≠ some _` holds whatever `valueHash 0` is."
        ),
        "witness": (
            "-- D1: obtaining a digest must SUCCEED; a wrapper that reports no\n"
            "-- digest (`none`) violates the spec at every input — here the bare\n"
            "-- wrapper ⟨0, none⟩. Holds whatever `valueHash 0` is (no hypothesis).\n"
            "example : ¬ problem_spec_choiceValueHash ⟨0, none⟩\n"
            "    (implementation_choiceValueHash ⟨0, none⟩) := by\n"
            "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CONST),
        "refinement": (
            "a constant digest for every wrapper is what a real `__hash__` that "
            "ignored the value would do (`return 0`): distinct primary keys would "
            "all COLLIDE into one hash bucket, so the F2P assertion that two "
            "wrappers built from distinct auto-increment pks have DISTINCT digests "
            "fails. It does not compute the wrapped value's digest at all. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from clause D2 of `result = some (valueHash m.val)`: the spec "
            "pins the payload to `valueHash m.val`, but the rival returns the "
            "constant `some 0`. `valueHash` is opaque, so the refutation CONDITIONS "
            "on the carrier: at `m.val = 5`, wherever `valueHash 5 ≠ 0` the rival's "
            "`0` differs from the spec's `valueHash 5`. One satisfiable hypothesis "
            "about the value-digest at the probed point — the sub-domain where the "
            "rival is wrong — which is stronger than any single literal could state.\n\n"
            "AUDIT REPAIR (the witness's reducing step was `simp only "
            "[Option.some.injEq]`; it is now plain `simp`). The previous form passed "
            "the gate but was HOLLOW under the forgery test. `simp only "
            "[Option.some.injEq]` does not normalise the frozen impl's `Id.run do` "
            "wrapper, so against the frozen solution the goal stayed the unreduced "
            "`¬ (pure (some (valueHash 5))).run = some (valueHash 5)` — measured by "
            "swapping the closing step for `exact (0 : Nat)` to print the real goal — "
            "and `Option.some.injEq` was itself reported UNUSED. `omega` then failed on "
            "an opaque atom it could not see through, for reasons having nothing to do "
            "with what the witness claimed. Measured consequence: a FORGERY differing "
            "from the witness ONLY in dropping the `¬` — i.e. asserting that the frozen "
            "solution SATISFIES the spec at that point, the opposite of a refutation — "
            "failed against the frozen solution with the BYTE-IDENTICAL error (`omega "
            "could not prove the goal: a possible counterexample may satisfy the "
            "constraints a ≤ -1 where a := valueHash 5`; exit 1 for witness and forgery "
            "alike). Gold's exit code therefore carried no information about the claim, "
            "and the gate would have recorded `rejected` for a witness asserting gold is "
            "CORRECT there. With plain `simp` the asymmetry is real and tracks the claim: "
            "the witness holds of the rival (exit 0) and fails on gold (exit 1, `omega … "
            "a := valueHash 5`), while the flipped-claim forgery now fails with a "
            "DIFFERENT error (`No goals to be solved`, exit 1 — `simp` having already "
            "discharged the positive claim for the frozen impl). The reveal probe pins "
            "the mechanism: after plain `simp` the goal on gold is `False` (the equation "
            "was PROVED for the frozen impl) versus `¬ 0 = valueHash 5` on the rival. The "
            "hypothesis stays satisfiable (consistency probe: exit 1, `h : ¬valueHash 5 = "
            "0 ⊢ False` unsolved). A one-tactic variant (`simp [h]`) was also measured "
            "and REJECTED as a repair: it closes the flipped claim on gold (exit 0) but "
            "also fails to close the witness against the RIVAL (exit 1), so it does not "
            "refute the rival at all."
        ),
        "witness": (
            "-- D2: the digest is GROUNDED in the value. A constant `0` differs from\n"
            "-- `valueHash 5` wherever the value's own digest is non-zero — the\n"
            "-- sub-domain where a constant-digest impl is wrong. One satisfiable\n"
            "-- hypothesis conditions on the opaque value-digest at the probed point.\n"
            "-- The reducing step is PLAIN `simp` (audit repair — see the case's\n"
            "-- rationale): it normalises the frozen impl's `Id.run do` wrapper, so on\n"
            "-- the frozen solution the equation is PROVED and the `¬` goal collapses\n"
            "-- to `False`, whereas on the rival it leaves the concrete arithmetic\n"
            "-- goal `¬ 0 = valueHash 5` for `omega` to close from `h`. That asymmetry\n"
            "-- is what makes the gold-side failure track the CLAIM rather than the\n"
            "-- syntactic form.\n"
            "example (h : valueHash 5 ≠ 0) : ¬ problem_spec_choiceValueHash ⟨5, none⟩\n"
            "    (implementation_choiceValueHash ⟨5, none⟩) := by\n"
            "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
            "  simp\n"
            "  omega\n"
        ),
    },
    {
        "id": "weak-inst-dependent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_INST_DEPENDENT),
        "refinement": (
            "letting the digest CONSULT the accompanying model object is the frame "
            "violation the first F2P assertion forbids: two wrappers carrying the "
            "SAME value but different model objects (one built with a model "
            "instance, one built with none) must share a digest. A real `__hash__` "
            "that mixed the instance into the digest gives them different digests, "
            "so `hash(value_1) == hash(wrapper(pk, None))` fails. Does NOT resolve. "
            "This carries over nagini's wrong-field / frame intent: on this carrier "
            "the model object is not itself a hashable value, so 'the digest "
            "depends on the model object' is expressed as a read-dependence rival."
        ),
        "rationale": (
            "REJECT from clause D3 (frame) of `result = some (valueHash m.val)`: "
            "the RHS omits `m.inst`, so the digest must NOT depend on it. The rival "
            "perturbs the digest (`valueHash m.val + 1`) when a model object is "
            "present. Refuted at a wrapper WITH a model object `⟨7, some i⟩` for a "
            "GIVEN `i : ModelInstance`, where `valueHash 7 + 1 ≠ valueHash 7` "
            "holds structurally — no hypothesis about the value-digest needed. "
            "Exercises `m.inst` at `some _`, the facet the value-level witnesses "
            "hold absent. NOTE (audit): the refutation is CONDITIONAL on being "
            "given such an `i` — `ModelInstance` is opaque and the carrier proves "
            "neither `Nonempty` nor `IsEmpty` for it — so the frame clause is ALSO "
            "attacked at an unconditionally-existing input by "
            "`weak-inst-dependent-absent` below."
        ),
        "witness": (
            "-- D3 (frame): the digest depends on `m.val` ALONE. A wrapper built\n"
            "-- WITH a model object (`some i`) must still get the value's digest; a\n"
            "-- rival that perturbs it by the instance's presence differs from the\n"
            "-- spec unconditionally (`x + 1 ≠ x`), so no hypothesis about the\n"
            "-- value-digest is needed. The binder `i : ModelInstance` is the model\n"
            "-- object the refutation point is stated OVER; since `ModelInstance` is\n"
            "-- opaque this states the refutation for ANY given model object rather\n"
            "-- than exhibiting one (the companion rival covers the absent facet at\n"
            "-- a closed input).\n"
            "example (i : ModelInstance) : ¬ problem_spec_choiceValueHash ⟨7, some i⟩\n"
            "    (implementation_choiceValueHash ⟨7, some i⟩) := by\n"
            "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
            "  simp\n"
        ),
    },
    # =====================================================================
    # ADDED BY AUDIT — the frame clause at a refutation point that is a CLOSED
    # term (no opaque inhabitant needed), and a partial-domain near-miss.
    # =====================================================================
    {
        "id": "weak-inst-dependent-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_INST_DEPENDENT_ABSENT),
        "refinement": (
            "the same frame violation as `weak-inst-dependent` with the branches "
            "swapped: the digest is perturbed for a wrapper built WITHOUT a model "
            "object. Two wrappers carrying the same value must share a digest "
            "whatever model object they were built from; a real `__hash__` that "
            "returned a different digest when built with no accompanying object "
            "breaks the assertion that a wrapper built with `None` shares the "
            "plain value's digest. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause D3 (frame) of `result = some (valueHash m.val)`: "
            "the RHS omits `m.inst`, so no branch on it may change the payload. "
            "Refuted at `⟨7, none⟩` — a CLOSED input term requiring no inhabitant "
            "of the opaque `ModelInstance` — where `valueHash 7 + 1 ≠ valueHash 7` "
            "holds structurally with no hypothesis at all, so the witness binds "
            "nothing and needs no consistency probe."
        ),
        "witness": (
            "-- D3 (frame), at an input that unconditionally EXISTS: `⟨7, none⟩` is\n"
            "-- a closed term. A rival that perturbs the digest on the\n"
            "-- model-object-absent facet differs from the spec by `x + 1 ≠ x`, so\n"
            "-- the refutation needs no hypothesis and no opaque inhabitant.\n"
            "example : ¬ problem_spec_choiceValueHash ⟨7, none⟩\n"
            "    (implementation_choiceValueHash ⟨7, none⟩) := by\n"
            "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-point-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_POINT_WRONG),
        "refinement": (
            "a PARTIAL-DOMAIN near-miss: the digest is the wrapped value's own "
            "digest for every value but one, where a constant is substituted. A "
            "real `__hash__` special-casing a single value this way would give "
            "that one wrapper a digest unrelated to its value, so a wrapper "
            "carrying it would not share the plain value's digest — the equality "
            "assertion fails on exactly that pk. Does NOT resolve, and unlike "
            "`weak-const` it is INDISTINGUISHABLE from gold everywhere else, "
            "which is what makes it the sharper probe of D2."
        ),
        "rationale": (
            "REJECT from clause D2 of `result = some (valueHash m.val)`: the spec "
            "pins the payload to `valueHash m.val` at EVERY value, not merely "
            "generically, so a single-point substitution violates it. `valueHash` "
            "is opaque, so the refutation CONDITIONS on the carrier at the probed "
            "point: wherever `valueHash 0 ≠ 0` the rival's `0` differs from the "
            "spec's `valueHash 0`. One satisfiable hypothesis (the gate's probe "
            "cannot derive `False` from it: exit 1, `⊢ False` unsolved)."
        ),
        "witness": (
            "-- D2 at a MEASURE-ZERO slice: the rival agrees with the spec at every\n"
            "-- value but `0`, where it substitutes a constant. The refutation is\n"
            "-- stated at `⟨0, none⟩` under one satisfiable hypothesis about the\n"
            "-- opaque value-digest at that point — the sub-domain where the rival\n"
            "-- is wrong.\n"
            "example (h : valueHash 0 ≠ 0) : ¬ problem_spec_choiceValueHash ⟨0, none⟩\n"
            "    (implementation_choiceValueHash ⟨0, none⟩) := by\n"
            "  unfold problem_spec_choiceValueHash implementation_choiceValueHash\n"
            "  simp\n"
            "  omega\n"
        ),
    },
]


# The axiom lane belongs to G-AX, which this gate ignores; `valueHash` is a
# deep-model reference (meta.json axioms == []), so there is no in-model axiom
# obligation for the PBT lane to re-discharge here.
AXIOM_TESTS = []
