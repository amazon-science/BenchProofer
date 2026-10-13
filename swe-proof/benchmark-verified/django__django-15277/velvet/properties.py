"""properties.py — G-PBT falsification battery for django__django-15277 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct configureValidators`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  configureValidators (priorValidators : List Validator) (lengthBound : Option Int)
      return (out : List Validator)
    ensures lengthBound = none      → out = priorValidators
    ensures lengthBound.isSome = true → out = priorValidators ++ [Validator.lengthBound lengthBound]

The method models the assembly of a field type's validator list during
initialization: a length-bound check is registered among the validators ONLY
when a length bound is actually configured; with no bound the established list is
left verbatim. The two ``ensures`` clauses pin the outcome exactly in BOTH
configurations, as a total function of the method's two inputs:

  * (C1) the NO-BOUND frame — when ``lengthBound = none`` the result equals the
        prior list verbatim: no element is added, none removed, order preserved.
        This is the clause the F2P exercises (the pre-patch appended
        unconditionally, so a no-bound field acquired a spurious length-bound
        check that later crashed when run).
  * (C2) the WITH-BOUND shape — when ``lengthBound.isSome`` the result is the
        prior list followed by EXACTLY ONE length-bound check whose configured
        bound is the supplied ``lengthBound``. Three independent facts live here:
        the prior list is carried through unchanged as a prefix (frame), exactly
        one check is appended (count/emptiness), and that check carries the
        supplied bound (payload value).

Both INPUT binders are free (no ``require`` clause) and the post-image must hold
for EVERY value of each:
  * ``priorValidators`` — the validators already established (the frame carried
        through by both clauses).
  * ``lengthBound``     — the field's optional length bound; drives the C1/C2
        fork and, on C2, the appended check's configured bound.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's read-only
    inputs are immutable scalars / ``Optional[int]`` (no fractional heap
    permission on any parameter), so the sibling itself records the
    frame-mutation probe as N/A. On this carrier the point is the same for the
    additional reason that Lean/Velvet are referentially transparent: every
    parameter is an immutable value, this bundle declares no ``mut`` binder,
    there is no heap and no aliasing. There is no read-only input to overwrite
    and no permission system to trip. No substitute is fabricated. (The
    ``priorValidators`` FRAME is still adversarially attacked — but by VALUE, via
    C1/C2 rivals that fail to carry it through, not by a permission mutation.)
  * TERMINATION / NON-TERMINATION - the class is INAPPLICABLE to this impl and
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
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The
    ``axioms`` region is empty; ``Validator`` is a concrete inductive and the
    post-image is pinned structurally (list equality, append shape, the carried
    bound) to the method's own arguments. There is no opaque answer key to echo,
    so there is no ungrounded-oracle rival to build; the honest controls are the
    cheapest faithful reshapes (the ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    single behavioural effect (register-the-check vs leave-the-list-alone) is
    exactly the difference between C1's ``out = priorValidators`` and C2's
    ``out = priorValidators ++ [Validator.lengthBound lengthBound]``. So the fork
    is fully observable to the ensures; the always-append / never-append rivals
    are its two discriminators.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. A rival can be correct on one
    configuration and wrong on the other (always-append is right with a bound and
    wrong with none — the F2P; never-append is right with none and wrong with a
    bound), or correct on the fork yet wrong on a sub-fact of C2 (wrong-bound
    mangles the payload value; drop-prior mangles the frame).

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces fully under ``decide``. Each reject rival carries
a machine-checked refutation ``witness`` — a Velvet tester statement
``configureValidatorsTester <priorValidators> <lengthBound> = false`` at ONE
concrete input, checked in a file whose ``prove_correct`` block has been stripped
so no tactic script can mask the verdict. The return carrier ``List Validator``
has ``DecidableEq`` (``Validator`` ``deriving DecidableEq``), so the tester
derivation needs no extra instance and no assumption — no ``axiom`` / ``sorry`` /
``native_decide`` is involved. Both halves were checked out-of-band with
``scripts/lean_verify.sh``, for all EIGHT rivals (the five ported ones plus the
three the audit added): every witness ELABORATES against its rival (exit 0) and
FAILS against the frozen solution (exit 1), and every gold-side failure was read
and confirmed to be ``decide`` PROVING THE PROPOSITION FALSE at the concrete
input — not an unknown identifier, a type error, a stuck reduction or a timeout.
So each rejection is a genuine spec refutation and not mechanical tactic
breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no
deep-model reference; ``Validator`` is a concrete inductive modeled directly and
refinement-checked by ``conformance_check.py`` (G-CONF), not axiomatized. Nothing
in the proof rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15277"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Register a length-bound check only when a length bound is configured;\n"
    "    -- otherwise leave the established validator list untouched.\n"
    "    let result : List Validator :=\n"
    "      if lengthBound.isSome then\n"
    "        priorValidators ++ [Validator.lengthBound lengthBound]\n"
    "      else\n"
    "        priorValidators\n"
    "    return result\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct configureValidators by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for reshapes needing it)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `configureValidatorsTester <priorValidators> <lengthBound> = false` says
# ---- the extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped. The
# ---- `List Validator` return carrier is decidable-eq (Validator deriving
# ---- DecidableEq), so no extra instance is derived.
_TESTER = (
    "extract_program_for configureValidators\n"
    "prove_precondition_decidable_for configureValidators\n"
    "prove_postcondition_decidable_for configureValidators\n"
    "derive_tester_for configureValidators\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the C1/C2 outcome identical and only
    # reshapes the executable surface; the frozen `loom_solve` closes the new
    # shape unchanged (checked out-of-band).
    # =====================================================================
    {
        "id": "pos-match-on-bound",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: branch on the length bound by MATCHING it (none vs some)
        # instead of testing `.isSome`. Same result on every input — the `none`
        # arm returns the prior list verbatim, the `some` arm appends the single
        # length-bound check carrying the same bound.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      match lengthBound with\n"
            "      | none => priorValidators\n"
            "      | some _ => priorValidators ++ [Validator.lengthBound lengthBound]\n"
            "    return result"),
        "rationale": "matching on `lengthBound` (none/some) computes the SAME "
                     "result as testing `.isSome`: the none arm yields "
                     "`priorValidators` (C1), the some arm yields "
                     "`priorValidators ++ [Validator.lengthBound lengthBound]` "
                     "(C2), so both ensures still hold on every input. A correct "
                     "reshape must verify, else SPEC-TOO-STRONG on how the "
                     "no-bound/with-bound fork is expressed.",
    },
    {
        "id": "pos-eq-none-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: guard on `lengthBound = none` and swap the two arms (no-bound
        # frame first). Same outcome on every input.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      if lengthBound = none then\n"
            "        priorValidators\n"
            "      else\n"
            "        priorValidators ++ [Validator.lengthBound lengthBound]\n"
            "    return result"),
        "rationale": "guarding on `lengthBound = none` (the negation of "
                     "`.isSome`) and swapping the arms leaves the result "
                     "identical on every input: `= none` returns the prior list "
                     "(C1), else appends the single check (C2). A correct reshape "
                     "must verify, else SPEC-TOO-STRONG on guard polarity / arm "
                     "order.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a representative concrete input
    # satisfies the precondition" probe is degenerate here (every input is
    # in-domain). The residual admissibility risk on a total-domain spec is that
    # the decision key is DEGENERATE — a `.isSome` test that never actually
    # separated the no-bound case from a configured bound would read like a live
    # fork. This case discharges an in-region assert pinning that the decision
    # key genuinely forks: a concrete configured bound is `.isSome = true`, and
    # `none` is `.isSome = false`. The impl is otherwise kept verbatim so the
    # method's own obligation still discharges; the proof is retuned to also
    # close the assert VC.
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT REPAIR. The assert this case originally carried was
        # `(some 7).isSome = true ∧ (none : Option Int).isSome = false` — a
        # CLOSED tautology about `Option` alone, mentioning neither binder nor
        # either clause image. It discharges by `decide` against any spec
        # whatsoever, so it attested to `Option.isSome`'s truth table rather
        # than to this method's fork being live. Replaced by the claim the case
        # actually means: the TWO CLAUSE IMAGES DIFFER, at the binders and hence
        # for EVERY input — `priorValidators ++ [Validator.lengthBound
        # lengthBound] ≠ priorValidators`. That is what makes the C1/C2 fork
        # non-degenerate: if the two images could coincide, one clause would be
        # satisfiable by the other's answer and the guard would decide nothing.
        # Stated over both binders, so it cannot hold for a spec whose clauses
        # collapse. Verified out-of-band (exit 0).
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (priorValidators ++ [Validator.lengthBound lengthBound] ≠ priorValidators))\n"
            "    let result : List Validator :=\n"
            "      if lengthBound.isSome then\n"
            "        priorValidators ++ [Validator.lengthBound lengthBound]\n"
            "      else\n"
            "        priorValidators\n"
            "    return result",
            "prove_correct configureValidators by\n  loom_solve <;> simp"),
        "rationale": "the C1/C2 fork is non-degenerate over the WHOLE domain: "
                     "the two clause post-images never coincide, since "
                     "`priorValidators ++ [Validator.lengthBound lengthBound] ≠ "
                     "priorValidators` for every value of both binders (appending "
                     "an element cannot yield the same list). So the guard "
                     "genuinely separates the two clauses — neither is "
                     "satisfiable by the other's answer, and neither is vacuous. "
                     "The in-region assert must discharge and the impl is kept "
                     "verbatim so the ensures still discharges too. Must verify "
                     "(else the decision the spec rests on is not admissible).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-always-append",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: register the length-bound check
        # UNCONDITIONALLY, even when no bound is configured. Correct when a bound
        # IS supplied (C2), but on the no-bound configuration it appends a
        # spurious `lengthBound none` where C1 demands the prior list verbatim.
        # This is the exact change under test (the marquee F2P rival).
        "module": _impl(
            "    let result : List Validator :=\n"
            "      priorValidators ++ [Validator.lengthBound lengthBound]\n"
            "    return result"),
        "refinement": "the faithful real counterpart is the PRE-PATCH code: "
                      "register the length-bound check unconditionally. On the "
                      "F2P (a field with NO length bound has its output resolved "
                      "and then cleaned) that leaves a length-bound check on the "
                      "field carrying a null bound; running it raises a TypeError "
                      "that the surrounding machinery does not swallow, so the "
                      "F2P test — which asserts cleaning does NOT throw — fails. "
                      "It would NOT resolve.",
        "rationale": "REJECT from clause C1 (`lengthBound = none → out = "
                     "priorValidators`): with no bound the rival returns "
                     "`priorValidators ++ [Validator.lengthBound none]`, which is "
                     "not the prior list. Refuted at the no-bound configuration "
                     "with an EMPTY prior list — the point where C1 demands `[]` "
                     "and the rival yields `[Validator.lengthBound none]`. This is "
                     "the precise change the spec senses (G-DIFF).",
        "witness": _witness("configureValidatorsTester [] none"),
    },
    {
        "id": "weak-never-append",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: NEVER register the check — return the prior list on every
        # input. Correct on the no-bound configuration (C1), but on a configured
        # bound it drops the length-bound check entirely where C2 demands it.
        "module": _impl(
            "    let result : List Validator := priorValidators\n"
            "    return result"),
        "refinement": "a real patch that never appends the length-bound check "
                      "would silently disable length enforcement for every field "
                      "that DOES declare a bound — the field would accept "
                      "arbitrarily long values. It fails length-enforcement "
                      "regression tests (the check must be present when a bound "
                      "is configured). It would NOT resolve.",
        "rationale": "REJECT from clause C2 (`lengthBound.isSome → out = "
                     "priorValidators ++ [Validator.lengthBound lengthBound]`): "
                     "with a bound the rival returns the prior list, dropping the "
                     "required appended check. Refuted at a configured bound with "
                     "an empty prior list — the point where C2 demands "
                     "`[Validator.lengthBound (some 5)]` and the rival yields "
                     "`[]`. Varies the `lengthBound` binder to `some` against the "
                     "F2P rival's `none`.",
        "witness": _witness("configureValidatorsTester [] (some 5)"),
    },
    {
        "id": "weak-wrong-bound",
        "kind": "uniqueness",
        "expect": "reject",
        # PAYLOAD rival on C2: the C1/C2 DECISION is exactly right and the frame
        # is carried through, but the appended check carries the WRONG configured
        # bound (the supplied bound + 1) instead of the supplied one. Built to
        # abuse the payload half of C2, which the decision rivals never exercise
        # (always-append/never-append are wrong about WHETHER to append, not
        # about the bound value it carries).
        "module": _impl(
            "    let result : List Validator :=\n"
            "      if lengthBound.isSome then\n"
            "        priorValidators ++ [Validator.lengthBound (lengthBound.map (· + 1))]\n"
            "      else\n"
            "        priorValidators\n"
            "    return result"),
        "refinement": "a real patch that registered the length-bound check with "
                      "an off-by-one bound (supplied bound + 1) would let values "
                      "one longer than the declared maximum through — an "
                      "off-by-one break of length enforcement that fails the "
                      "boundary length-enforcement tests. It would NOT resolve.",
        "rationale": "REJECT from clause C2 on the PAYLOAD value: the appended "
                     "check must carry `Validator.lengthBound lengthBound` (the "
                     "SUPPLIED bound), but the rival carries the bound + 1. "
                     "Refuted at a configured bound with a NON-EMPTY prior list "
                     "(`[Validator.existing 7]`, `some 5`) — the decision and the "
                     "frame are both right there, so only the payload value can "
                     "separate it. Varies `priorValidators` to non-empty.",
        "witness": _witness(
            "configureValidatorsTester [Validator.existing 7] (some 5)"),
    },
    {
        "id": "weak-drop-prior",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME rival on C2: decides correctly and carries the right bound, but
        # DROPS the prior validators when appending — returns only the new check
        # rather than the prior list followed by it. Built to abuse the
        # `priorValidators` binder that this carrier introduces (the sibling's
        # build routine has no prior-list input); every other with-bound rival
        # carries the prior list through, so none of them attests that C2 pins
        # the frame.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      if lengthBound.isSome then\n"
            "        [Validator.lengthBound lengthBound]\n"
            "      else\n"
            "        priorValidators\n"
            "    return result"),
        "refinement": "a real patch that REPLACED the field's validators list "
                      "with just the new length-bound check (instead of appending "
                      "to it) would discard every validator already configured on "
                      "the field — any explicitly-declared validator silently "
                      "vanishes. It fails tests that rely on pre-existing "
                      "validators surviving field initialization. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause C2 on the FRAME: the result must be "
                     "`priorValidators ++ [Validator.lengthBound lengthBound]` — "
                     "the prior list carried through as a PREFIX — but the rival "
                     "drops the prior list. Refuted at a configured bound with a "
                     "NON-EMPTY prior list (`[Validator.existing 0]`, `some 3`) — "
                     "the point that makes C2's dependence on `priorValidators` "
                     "observable (with an empty prior list the two agree). Varies "
                     "both `priorValidators` (non-empty) and `lengthBound` "
                     "(`some 3`).",
        "witness": _witness(
            "configureValidatorsTester [Validator.existing 0] (some 3)"),
    },
    {
        "id": "weak-empty-on-none",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME rival on C1: on the no-bound configuration returns the EMPTY list
        # instead of the prior list verbatim. Correct decision (adds nothing) and
        # correct on C2, but wrong on the C1 frame whenever the prior list is
        # non-empty. Built to abuse `priorValidators` on the no-bound branch,
        # which the F2P rival (always-append) does not — always-append is wrong
        # by ADDING an element there, this one is wrong by DROPPING the prior
        # list.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      if lengthBound.isSome then\n"
            "        priorValidators ++ [Validator.lengthBound lengthBound]\n"
            "      else\n"
            "        []\n"
            "    return result"),
        "refinement": "a real patch that reset the validators list to empty when "
                      "no bound is configured would discard every pre-existing "
                      "validator on a no-bound field — the same pre-existing "
                      "validators the field must retain. It fails tests relying "
                      "on those validators surviving initialization. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause C1 (`lengthBound = none → out = "
                     "priorValidators`): with no bound the result must equal the "
                     "prior list verbatim, but the rival returns `[]`. Refuted at "
                     "the no-bound configuration with a NON-EMPTY prior list "
                     "(`[Validator.existing 0]`, `none`) — the point that makes "
                     "C1's dependence on `priorValidators` observable (with an "
                     "empty prior list `[]` and `priorValidators` coincide). "
                     "Attacks the C1 frame from the opposite direction to "
                     "always-append.",
        "witness": _witness(
            "configureValidatorsTester [Validator.existing 0] none"),
    },

    # ---- AUDIT ADDITIONS ------------------------------------------------
    # Three rivals added by the independent audit. Each closes a fact the
    # prose of C2 CLAIMED was pinned but that no shipped rival demonstrated,
    # so a wrong impl of that fact would have verified undetected. All three
    # were built out-of-band: witness ELABORATES against the rival (exit 0)
    # and is REFUTED against the frozen solution (exit 1, `decide` proved the
    # proposition false — a semantic refutation, not tactic breakage).
    {
        "id": "weak-double-append",
        "kind": "uniqueness",
        "expect": "reject",
        # COUNT rival on C2. Decides correctly, carries the right bound, keeps
        # the frame as a prefix — but registers the length-bound check TWICE.
        # C2's prose claims "EXACTLY ONE check is appended (count/emptiness)",
        # yet every shipped rival was wrong about WHETHER to append or about
        # WHAT it carries; none appended the right thing the wrong number of
        # times. Without this, an impl that double-registered the check would
        # have satisfied every rival's discriminating point.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      if lengthBound.isSome then\n"
            "        priorValidators ++ [Validator.lengthBound lengthBound,\n"
            "                            Validator.lengthBound lengthBound]\n"
            "      else\n"
            "        priorValidators\n"
            "    return result"),
        "refinement": "a real patch that registered the length-bound check "
                      "twice would run the same length enforcement twice on "
                      "every value. The duplicate is externally visible: the "
                      "field's validator collection has an extra entry, and a "
                      "value that trips the bound reports the same complaint "
                      "twice instead of once. It fails tests that pin the "
                      "field's validator collection and the reported-complaint "
                      "count. It would NOT resolve.",
        "rationale": "REJECT from clause C2 on the COUNT: the result must be the "
                     "prior list followed by EXACTLY ONE length-bound check, but "
                     "the rival appends two. Refuted at a configured bound with "
                     "an EMPTY prior list (`[]`, `some 9`) — the decision, the "
                     "frame and the payload value are all correct there, so only "
                     "the number of appended checks can separate it. Varies "
                     "`lengthBound` to a third distinct `some` value.",
        "witness": _witness("configureValidatorsTester [] (some 9)"),
    },
    {
        "id": "weak-reverse-prior",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME-ORDER rival on C2. Carries every prior validator through and
        # appends exactly one correctly-configured check — but REVERSES the
        # prior list. C1's prose claims "order preserved" and C2's claims the
        # prior list is carried "as a PREFIX", yet every shipped rival held
        # `priorValidators` to at most ONE element, where reversal is the
        # identity. So no shipped case demonstrated that the spec pins ORDER
        # at all: this rival is invisible to all five of them.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      if lengthBound.isSome then\n"
            "        priorValidators.reverse ++ [Validator.lengthBound lengthBound]\n"
            "      else\n"
            "        priorValidators\n"
            "    return result"),
        "refinement": "a real patch that reordered the validators it carries "
                      "through would change the order enforcement runs in, and "
                      "so the order complaints are reported in for a value that "
                      "trips more than one validator. It fails tests that pin "
                      "the field's validator collection and the sequence of "
                      "reported complaints. It would NOT resolve.",
        "rationale": "REJECT from clause C2 on the FRAME's ORDER: the result must "
                     "be `priorValidators ++ [...]` — the prior list carried "
                     "through in its ORIGINAL order — but the rival reverses it. "
                     "Refuted at a TWO-element prior list "
                     "(`[Validator.existing 1, Validator.existing 2]`, `some 4`), "
                     "the shortest input at which reversal is observable: on the "
                     "0- and 1-element prior lists every other rival uses, "
                     "`reverse` is the identity and this rival agrees with the "
                     "spec exactly. Extends the `priorValidators` binder past "
                     "length 1 for the first time.",
        "witness": _witness(
            "configureValidatorsTester "
            "[Validator.existing 1, Validator.existing 2] (some 4)"),
    },
    {
        "id": "weak-positive-bound-only",
        "kind": "uniqueness",
        "expect": "reject",
        # DECISION rival on the C1/C2 KEY ITSELF. Registers the check only when
        # the configured bound is strictly POSITIVE, treating a zero bound as
        # if no bound were configured. Every shipped decision rival is
        # constant (always/never append), so all of them are separated at ANY
        # `some` value; none tests that the fork keys on WHETHER A BOUND IS
        # CONFIGURED rather than on the bound's magnitude. mapping.md §3 is
        # explicit that a zero or negative bound is still a configured bound
        # (the decision reads presence, not validity — validity is a separate
        # concern this behavior does not touch), so `some 0` is exactly the
        # input where "configured" and "positive" come apart.
        "module": _impl(
            "    let result : List Validator :=\n"
            "      match lengthBound with\n"
            "      | some b => if b > 0 then priorValidators ++ [Validator.lengthBound lengthBound]\n"
            "                  else priorValidators\n"
            "      | none => priorValidators\n"
            "    return result"),
        "refinement": "a real patch keying the decision on the bound being "
                      "POSITIVE rather than on a bound being CONFIGURED would "
                      "skip length enforcement on a field declaring a zero "
                      "bound — a field that must accept nothing would accept "
                      "everything, and the validator collection would be "
                      "missing its entry. Whether such a bound is sensible is a "
                      "separate concern that reports it independently and that "
                      "this behavior does not consult. It fails tests pinning "
                      "the validator collection for a zero bound. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause C2 on the DECISION KEY: C2 is "
                     "conditioned on `lengthBound.isSome = true`, which holds of "
                     "`some 0`, so a configured zero bound MUST still register "
                     "the check — but the rival returns the prior list. Refuted "
                     "at `(some 0)` with an empty prior list, the boundary where "
                     "'a bound is configured' and 'the bound is positive' "
                     "diverge; the constant always/never rivals cannot reach it. "
                     "Varies `lengthBound` to a `some` carrying a non-positive "
                     "payload for the first time.",
        "witness": _witness("configureValidatorsTester [] (some 0)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (3
# soundness positives, 1 admissibility, 6 uniqueness) over THREE contracted
# functions — `compare_length` (a numeric > comparison, raising on an absent
# limit), `build_char_validators` (assemble the 0-or-1-element validator list
# from an optional maximum), and `clean_charfield` (run the assembled validators,
# provably non-raising). This Lean-family bundle models only the PURELY
# FUNCTIONAL CORE that the gold patch changes: `configureValidators`, the
# validator-list ASSEMBLY step, which corresponds to `build_char_validators`
# WIDENED with an explicit `priorValidators` input (the field's already-present
# validators, which the real assembly appends to). The numeric comparison
# (`compare_length`) and the run-the-validators guard (`clean_charfield`) are NOT
# on this carrier — they are separate behaviours the velvet bundle does not
# contract — so the sibling's cases attached to them have no counterpart. This is
# carrier narrowing, not a thinner battery: every obligation and every input
# binder THIS bundle models is defended and attacked (see coverage footer).
#
#   sibling case                 -> here                         disposition
#   ------------------------------------------------------------------------
#   pos-build-conditional-return -> pos-match-on-bound           PORTED (reshaped)
#   pos-compare-reordered        -> (none)                       OMITTED (unmodeled fn)
#   pos-clean-early-return       -> (none)                       OMITTED (unmodeled fn)
#   admiss-clean-selfexercise    -> admiss-decision-nondegenerate RE-AIMED
#   weak-clean-drop-none-guard   -> weak-always-append           RE-AIMED (the F2P)
#   weak-clean-always-false      -> (none)                       OMITTED (unmodeled fn)
#   weak-build-limit-plus-one    -> weak-wrong-bound             PORTED
#   weak-build-always-empty      -> weak-never-append            PORTED
#   weak-compare-ge              -> (none)                       OMITTED (unmodeled fn)
#   weak-compare-const-true      -> (none)                       OMITTED (unmodeled fn)
#   (no sibling)                 -> pos-eq-none-guard            ADDED (2nd positive)
#   (no sibling)                 -> weak-drop-prior              ADDED (C2 frame / binder)
#   (no sibling)                 -> weak-empty-on-none           ADDED (C1 frame / binder)
#   (no sibling)                 -> weak-double-append           ADDED BY AUDIT (C2 count)
#   (no sibling)                 -> weak-reverse-prior           ADDED BY AUDIT (C2 frame ORDER)
#   (no sibling)                 -> weak-positive-bound-only     ADDED BY AUDIT (C2 decision key)
#
# 3 ported, 2 re-aimed, 4 omitted (unmodeled functions); 1 extra positive + 2
# frame/binder-coverage rivals added by the port, + 3 rivals added by the
# independent audit (see AUDIT ADDITIONS above).
#
# AUDIT REPAIRS (independent audit of the recorded SOUND). Two defects found;
# both were passing honestly while attesting to less than the prose claimed.
#   1. admiss-decision-nondegenerate carried a CLOSED tautology as its assert
#      (`(some 7).isSome = true ∧ (none : Option Int).isSome = false`) —
#      `Option.isSome`'s truth table, mentioning neither binder and neither
#      clause image, so it discharges against ANY spec and attested nothing
#      about THIS fork. Re-aimed at the claim the case means: the two clause
#      images differ at the binders, hence for every input.
#   2. Three facts C2's prose claimed to pin had NO rival demonstrating them,
#      so a wrong impl of any of them would have verified undetected:
#        * COUNT ("exactly one check is appended") — every shipped rival was
#          wrong about WHETHER to append or about the payload, never about the
#          number. Closed by weak-double-append.
#        * FRAME ORDER ("order preserved" / carried "as a PREFIX") — every
#          shipped rival held `priorValidators` to <= 1 element, where the
#          order of a list is not observable at all. Closed by
#          weak-reverse-prior at a TWO-element prior list.
#        * DECISION KEY (C2 keys on a bound being CONFIGURED, not on its
#          magnitude — mapping.md §3 pins that a zero/negative bound is still
#          configured) — both shipped decision rivals are CONSTANT, hence
#          separated at any `some`, so none reached the `some 0` boundary where
#          "configured" and "positive" come apart. Closed by
#          weak-positive-bound-only.
#   Machine-checked, not argued: all five ORIGINAL witnesses were rebuilt
#   independently (rival exit 0, gold exit 1) and every gold-side failure was
#   confirmed to be `decide` PROVING THE PROPOSITION FALSE — a semantic
#   refutation at the concrete input, not an unknown identifier, a type error,
#   a stuck reduction or a timeout. The three new rivals were built the same
#   way, with the same two-sided result.
# SPEC PROBES that found NO hole (attacks D/E, recorded so the next audit need
#   not re-spend the builds): a magic-assignment `:|` obligation-neuter probe
#   does not even elaborate on this bundle (`failed to synthesize Findable`, and
#   the annotated form is a parse error), so the obligation cannot be evaded
#   that way; and a CORRECT reshape via `priorValidators ++ extra` with `extra`
#   an optional singleton — whose agreement with the frozen impl is NOT
#   definitional (it needs `xs ++ [] = xs`) — VERIFIES under the frozen
#   `loom_solve` unchanged (exit 0), so the spec is not too strong on that axis
#   either. A second reshape via `Option.elim` needs a one-tactic retune
#   (`cases lengthBound <;> simp_all`) and then verifies; that is a tactic-shape
#   fact about `loom_solve`, not a spec hole, since variants may retune the
#   elided proof body.
#
# OMITTED (pos-compare-reordered, pos-clean-early-return, weak-clean-always-false,
#   weak-compare-ge, weak-compare-const-true): all five attach to `compare_length`
#   (the numeric `value_length > limit` comparison, and its off-by-one / constant
#   corruptions) or `clean_charfield` (the run-the-validators guard). Neither
#   function is contracted on this carrier — the velvet bundle models ONLY the
#   validator-list assembly. There is no obligation here for these rivals to
#   attack and no correct impl of them to defend, so they have no counterpart.
#   Not dropped for difficulty: the behaviours are genuinely absent from the
#   modeled surface (carrier narrowing).
# RE-AIMED (admiss-decision-nondegenerate): the sibling's admissibility control
#   exercises `build_char_validators(7)` and asserts len==1, Result()[0]==7 — a
#   representative concrete input satisfies the precondition. This method has NO
#   precondition, so that probe is degenerate (every input is in-domain). It is
#   re-aimed at the residual total-domain risk — that the C1/C2 decision key is
#   DEGENERATE — via an in-region assert that a configured bound is
#   `.isSome = true` and `none` is `.isSome = false`, so the fork genuinely
#   separates the two clauses.
# RE-AIMED (weak-always-append <- weak-clean-drop-none-guard): the sibling's
#   marquee F2P rival drops the None-guard inside `clean_charfield` so the
#   comparison runs against a null limit and the (Exsures-free) contract cannot
#   prove non-raising. This carrier models the append DECISION directly, so the
#   SAME bug appears one layer up as its true source: registering the length-bound
#   check UNCONDITIONALLY (the literal pre-patch `Solution_prepatch.lean` shape),
#   which violates C1 (no-bound frame). Same F2P, expressed on the modeled step.
# PORTED (pos-match-on-bound <- pos-build-conditional-return): the sibling's
#   positive reshapes the append to a branch-and-return; here the analogue is
#   matching on `lengthBound` (none/some) instead of testing `.isSome`.
#   Structurally different, behaviourally identical; the frozen `loom_solve`
#   closes it unchanged.
# PORTED (weak-wrong-bound <- weak-build-limit-plus-one): assembles the check with
#   the supplied bound + 1 — the sibling's off-by-one on the limit VALUE, carried
#   over intact to the C2 payload.
# PORTED (weak-never-append <- weak-build-always-empty): never registers the check
#   — the sibling's "always returns the empty slot" rival, correct on the no-bound
#   configuration and wrong whenever a bound is supplied (C2).
# ADDED (pos-eq-none-guard): a second positive control this carrier affords —
#   guard on `lengthBound = none` with the arms swapped. Guards against
#   SPEC-TOO-STRONG on guard polarity / arm order.
# ADDED (weak-drop-prior, weak-empty-on-none): this carrier introduces an input
#   the sibling's `build_char_validators` does not have — `priorValidators`, the
#   already-present validators the real assembly APPENDS to (`self.validators`
#   before the change). Both clauses pin it as a frame (C1: result = the prior
#   list verbatim; C2: result = the prior list ++ the new check). A battery whose
#   every rival held `priorValidators` empty would never demonstrate the spec's
#   dependence on it — a rival that mishandled a non-empty prior list would
#   verify. `weak-drop-prior` attacks the C2 frame (drops the prior list when
#   appending) and `weak-empty-on-none` the C1 frame (returns `[]` instead of the
#   prior list), each refuted at a NON-EMPTY prior list.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the two ensures (8 distinct input points after the audit additions):
#     lengthBound      — none (always-append, empty-on-none);
#                        some 0 (positive-bound-only — the non-positive
#                          configured bound, where "configured" and "positive"
#                          come apart);
#                        some 3 (drop-prior);
#                        some 4 (reverse-prior);
#                        some 5 (never-append, wrong-bound);
#                        some 9 (double-append):
#                        varied across none and FIVE distinct some values, one of
#                        them non-positive; never held fixed. The variation is
#                        MEANINGFUL, not two spellings of one point: `some 0` is
#                        the only point separating positive-bound-only, and it is
#                        a point no constant decision rival can reach.
#     priorValidators  — [] (always-append, never-append, double-append,
#                          positive-bound-only);
#                        [Validator.existing 0] (drop-prior, empty-on-none);
#                        [Validator.existing 7] (wrong-bound);
#                        [Validator.existing 1, Validator.existing 2]
#                          (reverse-prior):
#                        empty, one-element AND two-element. Length 2 is load
#                        bearing, not decoration: on lists of length <= 1 the
#                        order of a list is not observable at all, so reversal is
#                        the identity and reverse-prior agrees with the spec
#                        exactly. It is the only point at which the battery
#                        demonstrates that ORDER is pinned.
#   Every independent top-level behaviour of the post-image is attacked:
#     C1 (no-bound frame)  — always-append (adds a spurious element) and
#                            empty-on-none (drops the prior list): BOTH directions.
#     C2 decision          — never-append (drops the required check) and
#                            positive-bound-only (keys the fork on the bound's
#                            MAGNITUDE instead of on a bound being CONFIGURED).
#     C2 payload value     — wrong-bound (off-by-one on the carried bound).
#     C2 frame membership  — drop-prior (drops the prior-list prefix).
#     C2 frame ORDER       — reverse-prior (carries every prior validator through
#                            but in the wrong order).
#     C2 count             — double-append (appends the right check TWICE, where
#                            C2 demands exactly one).
#   Both positives + the admissibility control defend the obligation; eight rivals
#   attack it; no NO-REJECT-LANE risk.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (`Validator` is a concrete inductive modeled
# directly, checked by G-CONF), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
