"""properties.py — G-PBT falsification battery for sympy__sympy-14711 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, where a reshape needs it, the
``prove_correct vectorAdd`` tactic body — is changed; the consumer spec view
elides both, so ``markers.same_spec`` holds and the ``prove_correct vectorAdd``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  vectorAdd (self : VecVal) (other : Operand) return (out : Except AddErr VecVal)
    ensures out = addSpec self other

where ``addSpec self other`` is the total case split

  * ``other`` the additive identity  -> ``Except.ok self``  (ABSORB, no coercion)
  * ``other`` a genuine vector ``v``  -> ``Except.ok (combine self v)``
  * ``other`` anything else (foreign) -> ``Except.error notAVector``

TWO INPUT BINDERS. ``self : VecVal`` is an opaque vector handle. ``other :
Operand`` is a three-way tag (``zero`` / ``vec v`` / ``foreign``) — the whole
discriminating content lives in WHICH of the three arms fires and WHAT each
returns. The single load-bearing ``ensures`` pins three independent things:

  (absorb) the additive identity yields ``self`` UNCHANGED, with no coercion —
           so no type error can arise from it (the behaviour the public report
           asks for: seeding a running total with the identity and adding a
           vector must succeed rather than fail the coercion);
  (combine) a genuine vector is coerced through and the two are combined into
           ``combine self v`` — the content-bearing arm; the result is the
           opaque combination of BOTH operands, not ``self`` alone;
  (reject) any other value is rejected with the type-error outcome — the raise
           on the foreign arm is MANDATORY, not merely permitted.

The discriminating behaviour the issue reports is the (absorb) arm: pre-fix the
identity reached the coercion and was rejected, raising the type error. The
prepatch rival below (unconditional coercion) is exactly that pre-fix body.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how a witness reaches the post-image.
``combine`` is ``opaque`` (its concrete result is orthogonal to the fix — only
that two vectors combine into a vector matters), so on the (combine) arm a
``decide`` on a literal cannot COMPUTE the result. Velvet's tester machinery is
also unavailable here: ``prove_postcondition_decidable_for vectorAdd`` leaves
``Decidable (out = addSpec self other)`` unsolved because ``combine`` blocks the
instance (checked during authoring). So each witness states its refutation
DIRECTLY over ``NonDetT.run (vectorAdd …) ≠ DivM.res (addSpec …)`` — a ``Prop``,
never IR-compiled — which reduces cleanly for this straight-line (loop-free)
method under ``simp [NonDetT.run, pure, isZeroOperand, asVector]``.

Two of the three reject witnesses (the ``zero`` and ``foreign`` arms) need NO
conditioning: on those arms the spec's value is transparent (``ok self`` /
``error notAVector``) and the rival returns a DIFFERENT transparent value, so
the ``≠`` closes by ``simp`` alone. Only the (combine) arm touches the opaque
term, so its witness CONDITIONS on the carrier with the single hypothesis
``self ≠ combine self v`` — the exact sub-domain where returning ``self`` for a
genuine vector is wrong. That hypothesis is jointly satisfiable (the gate's
consistency probe cannot derive ``False`` from it — checked with a real build:
it leaves an unsolved ``⊢ False``). No ``sorry``/``admit``/``native_decide``/
``axiom`` appears in any witness.

ADVERSARIAL READ of the nagini classes on THIS carrier (see the accounting block
at the foot of the file for the case-by-case port ledger):
  * CONTROL-FLOW / PARTIAL-DOMAIN — APPLIES, and carries the reject lane. Each
    of the three arms is attacked by a rival that reshapes exactly that arm.
  * FRAME / PERMISSION MUTATION — VACUOUS here. The nagini sibling's #1 class
    writes a read-only input held at a fractional heap permission
    (``self.terms`` / ``other.is_vector`` / ``other.is_scalar_zero`` at
    ``Acc(...,1/2)``). This backend is referentially transparent: ``self`` and
    ``other`` are immutable value handles, this bundle declares NO ``mut`` binder
    among the inputs, and there is no heap and no aliasing. There is nothing to
    overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated (per the porting map).
  * UNGROUNDED-ORACLE ECHO — the nagini sibling's drop-other rivals attack an
    opaque ``normal_form`` applied to ``self ++ other``; here the analogue is the
    (combine) arm. It is NOT an ungrounded oracle: ``combine self v`` is applied
    to BOTH actual inputs, and the drop-other rival (return ``self`` for a
    genuine vector) is refuted exactly because ``combine self v`` differs from
    ``self`` (conditioned witness). Grounded in the inputs, not an answer key.
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
      - the GENERIC diverging rival (a ``while True do pure ()`` prefix ahead of
        the gold body) is REJECTED, at elaboration time, with ``Decreasing
        annotations are required in total correctness semantics``. It cannot be
        shipped as a reject case for a mechanical reason, not a reasoning one:
        that error is raised on the ``method`` declaration itself, which is
        present in the witness file too, so EVERY witness build against such a
        rival fails and no witness can satisfy the "elaborates against the rival"
        half. Verified by building a witness against it (exit 1, same error) and
        even a trivial ``1 + 1 = 2`` witness (exit 1, same error).
      - a diverging rival that DECLARES a ``decreasing`` measure it does not
        respect is NOT rejected: it VERIFIES while returning a value wrong on
        every arm. That is a genuine spec-strength hole, in the frozen artifact
        rather than in this battery, and it is escalated, not patched away (a
        battery may not edit the frozen spec). Full reproduction in the ledger.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14711"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The gold impl's CODE block (the `let result … ; return
# ---- result` inside -- impl-start / -- impl-end, after the descriptive comment).
# ---- Lies wholly inside the single impl region and is unique in Solution.lean
# ---- (both asserted at load by _swap). Every variant replaces exactly this
# ---- block; the method signature, the `ensures` clause and the `prove_correct`
# ---- header are untouched, so same_spec holds and the obligation survives.
_GOLD_CODE = (
    "    let result : Except AddErr VecVal :=\n"
    "      if isZeroOperand other then Except.ok self\n"
    "      else match asVector other with\n"
    "        | Except.ok v    => Except.ok (combine self v)\n"
    "        | Except.error e => Except.error e\n"
    "    return result")
assert _BASE.count(_GOLD_CODE) == 1, "impl-body anchor drift — re-sync _GOLD_CODE"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- reshape that changes the definitional form of the impl may need its own
# ---- tactic body; the match-on-`other` positive retunes to a `cases other`
# ---- split, which is allowed (the statement of `prove_correct vectorAdd` is
# ---- byte-identical). The reject rivals keep this frozen body — their rejection
# ---- is attributed to the spec by the witness, not to a broken tactic script.
_PROOF_GOLD = "prove_correct vectorAdd by\n  loom_solve\n  simp_all [addSpec]"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift — re-sync _PROOF_GOLD"


def _variant(body):
    return _swap(_BASE, _GOLD_CODE, body)


_PROOF_HEAD = "prove_correct vectorAdd by\n"
assert _PROOF_GOLD.startswith(_PROOF_HEAD)


def _prepend_tactic(extra):
    """The frozen file with ``extra`` PREPENDED to the ``prove_correct`` body.

    The impl region stays BYTE-IDENTICAL to the frozen one and the frozen tactic
    script is kept verbatim underneath, so the method's own obligation still
    discharges exactly as it does frozen; the only addition is a leading ``have``
    in the tactic body, which the consumer spec view elides. Used by the
    admissibility case, whose whole content is that the post-image is
    DISCHARGEABLE BY EVALUATION at the concrete modeled operand shapes.
    """
    return _swap(_BASE, _PROOF_GOLD,
                 _PROOF_HEAD + extra + _PROOF_GOLD[len(_PROOF_HEAD):])


# ---- witness preamble is trivial here: the spec predicate `addSpec` and the
# ---- method `vectorAdd` are both directly nameable, so a witness states the
# ---- refutation over `NonDetT.run (vectorAdd …) ≠ DivM.res (addSpec …)` with no
# ---- tester extraction (the opaque `combine` blocks the decidability instance
# ---- the tester machinery would need — see the CARRIER NOTE).


SPEC_TESTS = [
    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual
    # "a normal input satisfies the precondition" probe would be vacuous. The
    # PRECOND-TOO-STRONG analogue on a total carrier is the post-image being
    # UNSATISFIABLE or DEGENERATE at exactly the modeled operand shapes, which a
    # positive that discharges the obligation AT THOSE CONCRETE POINTS — by
    # evaluation, as a `have`, before closing the frozen obligation verbatim —
    # tests directly. Re-submitting the frozen impl alone does NOT test this: it
    # is a tautology (the gate would record `verified` for any frozen artifact
    # that verifies at all, which G-VERIFY already established), so the case is
    # given real content here. (Mirrors the nagini `admiss-gold` positive, at the
    # strength this carrier permits.)
    # =====================================================================
    {
        "id": "admiss-postimage-satisfiable-at-modeled-shapes",
        "kind": "admissibility",
        "expect": "verify",
        # Impl region BYTE-IDENTICAL to frozen; the only change is a leading
        # `have` in the (elided) tactic body, closed by evaluation on concrete
        # operand values, then `clear`ed so the frozen script still discharges the
        # real obligation on its own. No new lemma/axiom/`sorry`.
        "module": _prepend_tactic(
            "  have hadm :\n"
            "      addSpec ⟨0⟩ Operand.zero = Except.ok ⟨0⟩\n"
            "      ∧ addSpec ⟨0⟩ (Operand.vec ⟨1⟩) = Except.ok (combine ⟨0⟩ ⟨1⟩)\n"
            "      ∧ addSpec ⟨0⟩ Operand.foreign = Except.error AddErr.notAVector\n"
            "      ∧ addSpec ⟨0⟩ Operand.zero ≠ addSpec ⟨0⟩ Operand.foreign := by\n"
            "    refine ⟨rfl, rfl, rfl, ?_⟩\n"
            "    simp [addSpec, isZeroOperand, asVector]\n"
            "  clear hadm\n"),
        "rationale": (
            "PRECOND-TOO-STRONG analogue on a total carrier: the obligation `out "
            "= addSpec self other` must be SATISFIABLE at the concrete operand "
            "shapes the modeled behaviour distinguishes, not merely satisfiable "
            "somewhere. The `have` exhibits BY EVALUATION, at concrete handles, a "
            "value meeting the clause on all three arms simultaneously — the "
            "additive identity yielding the left operand unchanged and a genuine "
            "vector yielding the combination (the two shapes the F2P exercises), "
            "plus the foreign rejection — AND pins the post-image NON-DEGENERATE "
            "there (the identity image differs from the foreign image), so a "
            "constant collapse would not elaborate. If any leg were unsatisfiable "
            "or the three arms coincided, this term would not elaborate => "
            "PRECOND-TOO-STRONG / post-image degenerate at the modeled shapes. "
            "LOAD-BEARING, negative-control checked in all four directions with "
            "real builds: replacing the identity image with a different handle "
            "fails (`rfl has type ?m = ?m but is expected to have type addSpec "
            "{handle := 0} Operand.zero = Except.ok {handle := 1}`), replacing the "
            "combination image with the left operand alone fails the same way, "
            "flipping the foreign leg to a normal return fails the same way, and "
            "flipping the non-degeneracy leg to `=` fails with `unsolved goals ⊢ "
            "False` — so it is not a tautology any value would satisfy. The impl "
            "region is byte-identical to frozen and the frozen tactic script is "
            "kept, so the method's own obligation is discharged as usual."),
    },

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the clause
    # is SPEC-TOO-STRONG. Each keeps the `ensures` obligation; the returned value
    # is definitionally identical to gold on every input.
    # =====================================================================
    {
        "id": "pos-control-hoist-zero-test",
        "kind": "soundness",
        "expect": "verify",
        # Bind the additive-identity test to a local BEFORE the branch (hoisted),
        # then branch on it. `isZeroOperand other` is a deterministic pure map, so
        # the hoisted local denotes the same Bool and `out` equals `addSpec` on
        # every input; the frozen `loom_solve; simp_all [addSpec]` obligation
        # still discharges.
        "module": _variant(
            "    let isZ := isZeroOperand other\n"
            "    let result : Except AddErr VecVal :=\n"
            "      if isZ then Except.ok self\n"
            "      else match asVector other with\n"
            "        | Except.ok v    => Except.ok (combine self v)\n"
            "        | Except.error e => Except.error e\n"
            "    return result"),
        "rationale": (
            "same gold behaviour with the additive-identity test hoisted into a "
            "local bound before the branch. `isZeroOperand` is a deterministic "
            "pure map, so the hoisted `isZ` denotes the same value and out equals "
            "`addSpec self other` on every input; the frozen proof discharges. "
            "Must verify; if it cannot, the spec pins the code shape rather than "
            "the behaviour (SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-control-match-on-operand",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the two-level `if … else match asVector …` into a single direct
        # `match` on the three-way operand tag. Definitionally identical
        # (`isZeroOperand`/`asVector` are total case splits on the same tag), so
        # `out = addSpec` on every input. The definitional form changes, so the
        # proof is retuned to a `cases other` split (allowed — the tactic body is
        # elided from the spec view; the `prove_correct vectorAdd` STATEMENT is
        # byte-identical).
        "module": _swap(
            _variant(
                "    let result : Except AddErr VecVal :=\n"
                "      match other with\n"
                "      | Operand.zero    => Except.ok self\n"
                "      | Operand.vec v   => Except.ok (combine self v)\n"
                "      | Operand.foreign => Except.error AddErr.notAVector\n"
                "    return result"),
            _PROOF_GOLD,
            "prove_correct vectorAdd by\n"
            "  loom_solve\n"
            "  cases other <;> simp_all [addSpec, isZeroOperand, asVector]"),
        "rationale": (
            "structurally-different but CORRECT impl: dispatches by a single "
            "`match` on the three-way operand tag instead of `if isZeroOperand … "
            "else match asVector …`. The two are definitionally equal (both are "
            "total case splits on the same tag), so out equals `addSpec self "
            "other` on every input. The proof is retuned to a `cases other` split "
            "to match the reshaped definitional form. Must verify; if it cannot, "
            "the clause is SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each straight-line (so its `NonDetT.run` term
    # reduces) with a machine-checked refutation witness, and the refinement
    # argument for why its faithful real counterpart would NOT resolve the F2P
    # (test_Vector, which asserts `A.x + 0 == A.x` and `v3 = v1 + v2`).
    # =====================================================================

    # ---- (absorb) arm: the additive identity must be ABSORBED, not coerced ----
    {
        "id": "prepatch-no-absorb",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-FIX body: drop the additive-identity absorption and coerce the
        # operand UNCONDITIONALLY. The identity is not a vector, so `asVector`
        # rejects it with the type-error outcome — where the spec demands the
        # identity yields `self`. This is exactly the pre-patch `__add__`.
        "module": _variant(
            "    let result : Except AddErr VecVal :=\n"
            "      match asVector other with\n"
            "      | Except.ok v    => Except.ok (combine self v)\n"
            "      | Except.error e => Except.error e\n"
            "    return result"),
        "refinement": (
            "this IS the pre-patch body (no additive-identity absorption before "
            "the coercion). The real pre-patch coerces the identity through "
            "_check_vector, which RAISES on a non-vector — so seeding a running "
            "total with the additive identity and adding a vector CRASHES instead "
            "of returning the vector. The F2P assertion that the identity is "
            "absorbed (A.x + 0 == A.x) raises and test_Vector stays RED. The "
            "documented discriminator; a patch omitting the absorption would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the (absorb) arm of `out = addSpec self other`: on the "
            "additive identity `addSpec` yields `Except.ok self`, but this impl "
            "coerces unconditionally and yields `Except.error notAVector`. The two "
            "transparent values differ, so no conditioning is needed. Verifying "
            "would leave the identity-absorption behaviour unpinned "
            "(SPEC-TOO-WEAK). Refuted at other = zero."),
        "witness": (
            "example (self : VecVal) :\n"
            "    NonDetT.run (vectorAdd self Operand.zero)\n"
            "      ≠ DivM.res (addSpec self Operand.zero) := by\n"
            "  unfold vectorAdd addSpec\n"
            "  simp [NonDetT.run, pure, isZeroOperand, asVector]\n"),
    },

    # ---- (combine) arm: a genuine vector must be COMBINED with self, not dropped
    {
        "id": "drop-other-return-self",
        "kind": "uniqueness",
        "expect": "reject",
        # Absorb the identity correctly, but on a GENUINE vector operand drop the
        # other operand entirely and return `self` — echoing `self` instead of
        # `combine self v`. Correct on the zero and foreign arms (a near-miss to
        # prepatch-no-absorb / swallow-foreign, which are wrong there), so it is
        # refuted at a DISJOINT input on the (combine) arm.
        "module": _variant(
            "    let result : Except AddErr VecVal :=\n"
            "      if isZeroOperand other then Except.ok self\n"
            "      else match asVector other with\n"
            "        | Except.ok _    => Except.ok self\n"
            "        | Except.error e => Except.error e\n"
            "    return result"),
        "refinement": (
            "on a genuine vector operand this drops the other operand and returns "
            "self, where the real __add__ builds Vector(self.args + other.args) "
            "combining BOTH. On F2P v3 = v1 + v2 it gives v3 == v1, dropping v2, "
            "so dot(v3, A.x) == x instead of x**2 + x and test_Vector FAILS. A "
            "patch returning self for a vector operand would NOT resolve."),
        "rationale": (
            "REJECT from the (combine) arm: `addSpec self (vec v)` = `Except.ok "
            "(combine self v)`, but this impl returns `Except.ok self`. On the "
            "opaque carrier the two are separated by conditioning on `self ≠ "
            "combine self v` — the exact sub-domain where dropping the operand is "
            "wrong. Refuted at other = vec v with that hypothesis (jointly "
            "satisfiable; consistency probe leaves ⊢ False). Verifying would leave "
            "the combination arm unpinned (SPEC-TOO-WEAK / ungrounded echo of "
            "self)."),
        "witness": (
            "example (self v : VecVal) (h : self ≠ combine self v) :\n"
            "    NonDetT.run (vectorAdd self (Operand.vec v))\n"
            "      ≠ DivM.res (addSpec self (Operand.vec v)) := by\n"
            "  unfold vectorAdd addSpec\n"
            "  simp [NonDetT.run, pure, isZeroOperand, asVector]\n"
            "  exact h\n"),
    },

    # ---- (absorb) arm, SHARPER: the identity must yield `self` UNCHANGED ----
    {
        "id": "absorb-recombine-not-unchanged",
        "kind": "uniqueness",
        "expect": "reject",
        # Absorb the identity WITHOUT coercing (so this is not the prepatch), but
        # return a re-combination of the left operand with itself instead of the
        # left operand UNCHANGED. Correct on the combine and reject arms, so it is
        # a near-miss to every other rival, and it attacks the exact content of the
        # absorb arm that prepatch-no-absorb does NOT: prepatch tests that the
        # identity is not REJECTED; this tests that it yields `self` ITSELF rather
        # than merely some vector built from `self`. This is the counterpart of the
        # nagini `scalar-zero-renormalise` rival, which the earlier port recorded
        # as having no counterpart on this carrier — it does have one.
        "module": _variant(
            "    let result : Except AddErr VecVal :=\n"
            "      if isZeroOperand other then Except.ok (combine self self)\n"
            "      else match asVector other with\n"
            "        | Except.ok v    => Except.ok (combine self v)\n"
            "        | Except.error e => Except.error e\n"
            "    return result"),
        "refinement": (
            "the desired behaviour on the additive identity is the cheap identity "
            "return: the SAME vector value, unchanged. Re-running the combining "
            "construction on the left operand against itself is a different "
            "operation — it doubles the running total instead of leaving it alone, "
            "so seeding an accumulator with the identity yields twice the vector "
            "rather than the vector. The F2P assertion that the identity is "
            "absorbed (A.x + 0 == A.x) then compares against 2*A.x and FAILS, so "
            "a patch of this shape would NOT resolve."),
        "rationale": (
            "REJECT from the (absorb) arm of `out = addSpec self other`: on the "
            "additive identity `addSpec` yields `Except.ok self`, but this impl "
            "yields `Except.ok (combine self self)`. Both sides pass through the "
            "opaque `combine`, so they are separated by conditioning on `combine "
            "self self ≠ self` — the exact sub-domain where re-combining is "
            "observably not the identity operation. Refuted at other = zero with "
            "that hypothesis (jointly satisfiable; the consistency probe leaves "
            "⊢ False unsolved). Verifying would leave the absorb arm pinned only "
            "up to 'returns some vector built from self' rather than 'returns self "
            "unchanged' (SPEC-TOO-WEAK)."),
        "witness": (
            "example (self : VecVal) (h : combine self self ≠ self) :\n"
            "    NonDetT.run (vectorAdd self Operand.zero)\n"
            "      ≠ DivM.res (addSpec self Operand.zero) := by\n"
            "  unfold vectorAdd addSpec\n"
            "  simp [NonDetT.run, pure, isZeroOperand, asVector]\n"
            "  exact h\n"),
    },

    # ---- (combine) arm, SHARPER: the combination must use the RIGHT operand ----
    {
        "id": "combine-wrong-operand-self-self",
        "kind": "uniqueness",
        "expect": "reject",
        # On a genuine vector operand, combine — but with the WRONG second
        # operand: `combine self self` rather than `combine self v`. Strictly
        # sharper than drop-other-return-self: the result is still produced BY the
        # combining construction and still lands in the `ok` arm, so every
        # shape-level property of the content-bearing arm is met while the second
        # operand is silently discarded. This is the echo a length/shape-only
        # clause would not catch.
        "module": _variant(
            "    let result : Except AddErr VecVal :=\n"
            "      if isZeroOperand other then Except.ok self\n"
            "      else match asVector other with\n"
            "        | Except.ok _    => Except.ok (combine self self)\n"
            "        | Except.error e => Except.error e\n"
            "    return result"),
        "refinement": (
            "the real combination builds from BOTH operands' components; this "
            "builds from the left operand twice, discarding the right one. On F2P "
            "v3 = v1 + v2 it gives v1 doubled instead of v1 + v2, so dot(v3, A.x) "
            "== 2*x rather than x**2 + x and test_Vector FAILS. A patch that "
            "combined the left operand with itself would NOT resolve."),
        "rationale": (
            "REJECT from the (combine) arm: `addSpec self (vec v)` = `Except.ok "
            "(combine self v)`, but this impl returns `Except.ok (combine self "
            "self)` — the combining construction applied to the wrong operand "
            "pair. Separated by conditioning on `combine self self ≠ combine self "
            "v`, the sub-domain where the combination genuinely depends on its "
            "SECOND argument (a strictly stronger demand than `self ≠ combine self "
            "v`, which only says the result is not the left operand). Refuted at "
            "other = vec v with that hypothesis (jointly satisfiable; the "
            "consistency probe leaves ⊢ False unsolved). Verifying would let an "
            "impl echo a combination of the left operand with itself and pass "
            "(SPEC-TOO-WEAK)."),
        "witness": (
            "example (self v : VecVal) (h : combine self self ≠ combine self v) :\n"
            "    NonDetT.run (vectorAdd self (Operand.vec v))\n"
            "      ≠ DivM.res (addSpec self (Operand.vec v)) := by\n"
            "  unfold vectorAdd addSpec\n"
            "  simp [NonDetT.run, pure, isZeroOperand, asVector]\n"
            "  exact h\n"),
    },

    # ---- (reject) arm: a foreign operand must RAISE, not be silently accepted ----
    {
        "id": "swallow-foreign-return-self",
        "kind": "uniqueness",
        "expect": "reject",
        # Absorb the identity and combine a genuine vector correctly, but on a
        # FOREIGN operand return `self` NORMALLY instead of raising the type
        # error. This is the sharpest swallow: correct on the other two arms,
        # wrong only on the mandatory-raise arm.
        "module": _variant(
            "    let result : Except AddErr VecVal :=\n"
            "      if isZeroOperand other then Except.ok self\n"
            "      else match asVector other with\n"
            "        | Except.ok v    => Except.ok (combine self v)\n"
            "        | Except.error _ => Except.ok self\n"
            "    return result"),
        "refinement": (
            "the real __add__ calls _check_vector(other), which RAISES on any "
            "non-vector non-identity operand (A.x + 5, A.x + 'foo'). Silently "
            "returning self would change the library's guaranteed error behaviour "
            "— e.g. cross(A.x + 5, A.y) would compute cross(A.x, A.y) instead of "
            "raising — a wrong-result behaviour change, not the gold patch. A "
            "patch swallowing the foreign operand would NOT resolve."),
        "rationale": (
            "REJECT from the (reject) arm: `addSpec self foreign` = `Except.error "
            "notAVector`, but this impl returns `Except.ok self`. The two "
            "transparent values differ, so no conditioning is needed. Verifying "
            "would make the mandatory raise merely permissive (SPEC-TOO-WEAK). "
            "Refuted at other = foreign."),
        "witness": (
            "example (self : VecVal) :\n"
            "    NonDetT.run (vectorAdd self Operand.foreign)\n"
            "      ≠ DivM.res (addSpec self Operand.foreign) := by\n"
            "  unfold vectorAdd addSpec\n"
            "  simp [NonDetT.run, pure, isZeroOperand, asVector]\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (1
# admissibility, 1 soundness positive, 2 frame-mutation rivals, 6 control-flow /
# partial-domain uniqueness rivals) plus 3 AXIOM_TESTS this gate ignores. The
# carrier here is NARROWER than nagini's: nagini models the vector as a `List
# [int]` of component tags with a fractional-permission heap and an index loop
# building `combined` element-by-element, so it can attack the loop construction
# and the read-only permission frame. This velvet bundle models the vector as a
# single opaque handle `VecVal` and the combination as one opaque `combine self
# v` (mapping.md §1-2): there is no component list, no loop, and no permission
# surface. So the nagini cases that attack the LOOP CONSTRUCTION (the two-loops
# positive, the re-normalise rivals) or the PERMISSION FRAME (the two
# frame-mutation rivals) have no counterpart — carrier narrowing, not omission of
# convenience. What survives is the three-way ARM dispatch (absorb / combine /
# reject), which this bundle models faithfully and which carries the whole reject
# lane.
#
#   nagini case                     -> here                              status
#   ------------------------------------------------------------------------------
#   admiss-gold                     -> admiss-postimage-satisfiable-...   PORTED (strengthened)
#   pos-two-loops                   -> pos-control-hoist-zero-test        RE-EXPRESSED
#                                      + pos-control-match-on-operand      ADDED (2nd positive)
#   frame-write-self-terms          -> (none)                            VACUOUS (no heap/permission)
#   frame-write-is-vector           -> (none)                            VACUOUS (no heap/permission)
#   prepatch-no-shortcircuit        -> prepatch-no-absorb                 PORTED (absorb arm)
#   drop-other-return-self          -> drop-other-return-self             PORTED (combine arm)
#   drop-other-vec-self             -> combine-wrong-operand-self-self    PORTED (audit: expressible)
#   drop-other-vec-empty            -> drop-other-return-self             COLLAPSED (no component list)
#   scalar-zero-renormalise         -> absorb-recombine-not-unchanged     PORTED (audit: expressible)
#   swallow-neither-sharp           -> swallow-foreign-return-self        PORTED (reject arm)
#   swallow-not-a-vector            -> swallow-foreign-return-self        COLLAPSED (same rival here)
#   ax-sound-vector-guard           -> (none)                            DROPPED (G-AX lane)
#   ax-sound-normal-form            -> (none)                            DROPPED (G-AX lane)
#   ax-contain-normal-form          -> (none)                            DROPPED (G-AX lane)
#
# 1 admissibility + 2 positives + 5 uniqueness rivals shipped. 2 frame-mutation
# rivals vacuous; drop-other-vec-empty collapses onto drop-other-return-self (the
# empty-component-list distinction has no counterpart when the vector is one
# opaque handle) and swallow-not-a-vector onto swallow-foreign-return-self;
# 3 axiom-lane cases dropped. No case was dropped because its proof/witness was
# hard; every shipped rival's witness was seen to discriminate with real builds
# (rival exit 0, gold exit 1), and each gold-side failure was additionally
# FORGERY-tested (attack B′): the flipped claim (`=` for `≠`) BUILDS against the
# frozen solution and FAILS against the rival, so gold's exit code tracks the
# claim rather than a fixed carrier error.
#
# AUDIT CORRECTION (2 rivals added). An earlier revision of this ledger recorded
# `scalar-zero-renormalise` as having no counterpart on this carrier ("`combine`
# is opaque with no idempotence to probe") and collapsed `drop-other-vec-self`
# onto `drop-other-return-self`. Both were wrong, and re-derived with real
# builds: opacity does not block a rival, because a witness need not COMPUTE the
# opaque term — it states its refutation at a point described by HYPOTHESIS
# (`combine self self ≠ self`, `combine self self ≠ combine self v`), which the
# consistency probe then confirms is satisfiable precisely BECAUSE the term is
# opaque (no tactic can derive False from it). The two rivals are now shipped as
# `absorb-recombine-not-unchanged` and `combine-wrong-operand-self-self`; both
# measured rival exit 0 / gold exit 1 / probe exit 1, with the forgery pair
# confirming discrimination. They are strictly sharper than the rivals they sit
# beside: the first pins "the identity yields `self` ITSELF", not merely "some
# vector built from self"; the second pins that the combination depends on its
# SECOND argument, not merely that the result differs from the first.
#
# COLLAPSED (nagini's finer distinctions that genuinely vanish here):
#  * drop-other-vec-empty. Nagini's `Vec([])` echoes `normal_form(empty)`, a
#    DIFFERENT component sequence from `normal_form(self.terms)`. Here the vector
#    is one opaque handle with no component list, so there is no "empty" vector
#    value distinct from the handle itself to return: the degenerate echo and
#    `return self` are the same rival, `drop-other-return-self`. (Demonstrated,
#    not asserted: the carrier offers no constructor for a component sequence —
#    `VecVal` is a single `handle : Int` and `combine` is the only way to build
#    one from others, so `Vec([])` has no expressible image.)
#  * swallow-not-a-vector. Nagini's `return self` on a non-vector operand (never
#    invoking the guard) and `swallow-neither-sharp` (short-circuit on the
#    neither state) are the SAME rival here: on the (reject) arm return `ok self`
#    instead of `error notAVector`. Single rival `swallow-foreign-return-self`.
#
# PORTED AFTER AUDIT (previously recorded as inexpressible — both are expressible):
#  * scalar-zero-renormalise -> absorb-recombine-not-unchanged. Nagini attacks the
#    identity arm by RE-NORMALISING self instead of returning it, exploiting that
#    the construction is not provably idempotent. The counterpart here is
#    `Except.ok (combine self self)` on the absorb arm: `combine` applied to the
#    left operand alone is exactly "rebuild from self rather than return self",
#    and it is refuted by conditioning on `combine self self ≠ self`. The earlier
#    "no re-normalising constructor on this carrier" reading overlooked that
#    `combine self self` IS that constructor applied to `self` alone.
#  * drop-other-vec-self -> combine-wrong-operand-self-self. The nagini rival
#    rebuilds from self's components only, staying inside the constructor while
#    discarding the other operand. That is `combine self self` on the (combine)
#    arm — distinct from `return self`, and strictly sharper: the result is still
#    PRODUCED BY the combining construction, so it satisfies every shape-level
#    property of the content-bearing arm while ignoring the second operand.
#    Refuted by conditioning on `combine self self ≠ combine self v`.
#
# VACUOUS (frame-mutation, per the porting map):
#  * frame-write-self-terms / frame-write-is-vector. Both write a read-only input
#    held at a fractional heap permission (`self.terms` / `other.is_scalar_zero`
#    at `Acc(...,1/2)`) and are rejected for INSUFFICIENT PERMISSION before any
#    value reasoning. This backend is referentially transparent: `self` and
#    `other` are immutable value handles, this bundle declares no `mut` binder
#    among the inputs, and there is no heap or aliasing. Nothing to overwrite, no
#    permission system to trip. No substitute is fabricated.
#
# DROPPED (ax-*): the sibling's three AXIOM_TESTS probe the real `_check_vector`
#   (identity-on-Vector / raise-on-non-Vector) and `Vector.__init__`
#   (never-grows / determinism / distinguisher / containment). The axiom lane is
#   G-AX's job (axiom_check.py) and this gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE / NON-TERMINATION (attack F', re-measured against the frozen bundle).
#   CORRECTED. An earlier revision of this ledger recorded this class at BOTH
#   termination settings and escalated a spec-strength hole under a declared but
#   false measure. Both records are RETRACTED. They were written against a reading
#   of `set_option loom.semantics.termination` that does not hold, and the exit-0
#   reproduction they quoted does not reproduce. What follows is what the frozen
#   artifact actually does, re-measured.
#
#   The setting. Solution.lean line 4 is `set_option loom.semantics.termination
#   "total"` and line 7 is `open TotalCorrectness DemonicChoice`. The option is not
#   inert and the two lines cannot disagree: the option elaborator itself opens the
#   matching scope (Loom/MonadAlgebras/WP/Options.lean, `openScope`, where "total"
#   opens `TotalCorrectness`), and Velvet/Syntax.lean:386 opens the same scope by
#   default. There is no `open PartialCorrectness` anywhere in this bundle. So the
#   ledger's claim that this cell "has been seen at both values (committed:
#   partial)" was false about the committed artifact, and every disposition that
#   depended on the partial reading is void.
#
#   What total semantics means for this class. A postcondition is claimed of ALL
#   runs, not only terminating ones, so a non-terminating impl does NOT satisfy
#   `ensures` vacuously. Concretely, `TotalCorrectness.DemonicChoice.WPGen`'s
#   `forWithInvariantLoop` takes `measure : β -> Nat` and emits a per-iteration
#   proof obligation `with_name_prefix `decreasing (measure b' < measure b)`. The
#   `PartialCorrectness` twin takes `measure : β -> Option Nat` and discards it,
#   which is what the retracted text was describing, but that twin is not the one
#   this bundle elaborates under. A diverging rival is therefore REJECTED, and
#   rejected on a real goal rather than on a syntactic lint.
#
#   Re-measurement, on a scratch copy of this cell (the bundle was not modified).
#   The retracted leg (b) quoted, as verifying with exit 0, exactly this rival: a
#   spliced prefix `let mut k : Nat := 1` / `while k > 0` with `invariant k > 0`,
#   `done_with k = 0`, `decreasing k`, body `k := k + 1`, returning the type-error
#   outcome on every arm. Rebuilt as quoted, it is REJECTED. The build stops on the
#   measure's own descent obligation, `case decreasing_1: k ... |- k + 1 < k`,
#   reported as `unsolved goals`. So the `decreasing` annotation is required to be
#   TRUE and not merely PRESENT, the contradictory `invariant`/`done_with` pair buys
#   nothing, and there is no exit-0 verification to escalate. The claimed hole does
#   not exist.
#
#   Why the class is still not shipped as a reject case here, and it is a tooling
#   limit rather than a spec gap. A reject case needs a witness that ELABORATES
#   against the rival and FAILS against gold, and BOTH diverging shapes defeat the
#   first half, for two DIFFERENT reasons. Measured through the gate's own
#   `_check_witness`:
#     * NO measure. The refusal is a module-level elaboration error raised at the
#       `method` DECLARATION, which the witness file retains (it strips only the
#       `prove_correct` obligations), so the rival module does not compile at all
#       and even `example : True := trivial` comes back `witness-unproven`.
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#     * MEASURE PRESENT BUT FALSE. Here the refusal moves to the `prove_correct`
#       site, which the witness file DOES strip, so the module elaborates and a
#       trivial witness succeeds. But a real witness still cannot be PROVED: the
#       rival keeps a `while`, so its post-image is an unreduced `forIn
#       Lean.Loop.mk ... invariantGadget ... decreasingGadget` term that no `simp`
#       or `decide` normalises, and the witness build ends `unsolved goals` on that
#       term. Verdict `witness-unproven` again.
#   A `witness_reference` rescues neither shape, since it substitutes the GOLD
#   subject while the failure is on the RIVAL side. Both outcomes score
#   `_INCONCLUSIVE` and report MALFORMED-TESTS, which fails a battery rather than
#   passing a case. That is a property of how the verifier surfaces the failure and
#   of what the kernel can reduce, not of the specification: the spec-side verdict
#   is unambiguous and is REJECT.
#
#   Structural note specific to this cell. The frozen impl contains no loop at all,
#   so no descent obligation arises for the gold body and nothing here is being
#   discharged by luck. The class is exercised only by splicing a diverging prefix
#   ahead of the frozen body, as above, and that rival is refused. The absence of a
#   divergence entry in SPEC_TESTS is the class being inapplicable to a loop-free
#   impl plus the witness contract above, not an unattacked behaviour.
#
# BINDER / CLAUSE COVERAGE. Two input binders — `self` (opaque handle) and
#   `other` (three-way tag) — and one clause with three arms. `other` is moved
#   across ALL THREE tags by the reject witnesses: zero (prepatch-no-absorb,
#   absorb-recombine-not-unchanged), vec v (drop-other-return-self,
#   combine-wrong-operand-self-self), foreign (swallow-foreign-return-self). Each
#   arm is attacked at a DISTINCT input point, and the rivals are pairwise
#   near-misses (each is correct on the arms the others attack), so none shares a
#   witness. The two arms whose spec value is TRANSPARENT (`ok self` / `error
#   notAVector`) are each attacked twice, at two different STRENGTHS: once against
#   a transparent wrong value (no conditioning needed) and once against a value
#   that also passes through the opaque `combine` (conditioned witness) — so the
#   clause is pinned not merely up to "returns some vector built from the inputs"
#   but up to the exact vector. `self` is bound in every witness; the three
#   conditioning hypotheses (`self ≠ combine self v`, `combine self self ≠ self`,
#   `combine self self ≠ combine self v`) are what its role turns on, and each is
#   confirmed satisfiable by the gate's own consistency probe. No unattacked arm;
#   no pinned binder.
#
# AXIOM_TESTS: empty. The two callees (`asVector` deep-modeled, `combine` opaque
#   with no asserted ensures) are A-referenced (mapping.md §3; validated == the
#   real callees by G-AX / axiom_check.py). There is no consumed axiom to mirror,
#   and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
