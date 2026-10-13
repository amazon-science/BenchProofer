"""properties.py — G-PBT falsification battery for django__django-14500 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct recordUnappliedKeys`` obligation survives with its
header intact) and swaps in a candidate implementation; it is checked by the
real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — here against a ``witness_reference`` rather than
against gold, for the reason set out in the CARRIER NOTE below).

DEFENDED SURFACE (one contracted method, one ``ensures`` clause):

  recordUnappliedKeys (m : Migration) return (out : List (String × String))
    ensures out = m.replaces ++ [(m.appLabel, m.name)]

The operation computes the ordered list of keys marked no-longer-current when a
step is reversed: every key the step stands in for (``m.replaces``, in listed
order), FOLLOWED — unconditionally — by the step's own key
``(m.appLabel, m.name)``. For an ordinary step that stands behind nothing
(``m.replaces = []``) the result is just its own key.

There is NO ``require`` clause, so the admitted domain is total: every
``Migration`` value is in scope. ``m.replaces``, ``m.appLabel`` and ``m.name``
are all FREE input binders and the post-image must hold at every value they
take — which is what makes the partial-domain rivals below genuinely refutable
at a concrete point rather than only arguably wrong.

The clause is a single sequence equality GROUNDED ENTIRELY in the method's own
argument: the ``axioms`` region is empty and ``m.replaces ++ [ownKey]`` is a
transparent term over ``m``, so there is no opaque answer-key oracle a wrong
impl could echo. That closes the ungrounded-oracle class by construction, and
it is also why the carrier is fully transparent to ``decide`` (contrast the
opaque-callee bundles, which must condition on the carrier instead).

THE LOAD-BEARING BEHAVIOUR. The single discriminating property is that the own
key is appended UNCONDITIONALLY, after the replaced-key prefix, rather than
only for a step that stands behind nothing. The failing test drives a composite
step that stands in for TWO others (``m.replaces`` has length 2), reverses it,
and asserts the composite's own key is no longer marked current. Because
"marked current" is observed as SET MEMBERSHIP, the recording ORDER and any
DUPLICATE recording are invisible to that test — so the genuine
verify-does-not-resolve breaks all key on WHETHER the own key is recorded and
with WHICH value, never on the order or multiplicity of the records. That is
why the order-permuting and duplicate-record rivals are OMITTED rather than
shipped (see the footer): a faithful patch of either shape WOULD resolve the
failing test, so a verifying variant of it would not be a real break.

CARRIER NOTE — WHY EVERY REJECT CASE CARRIES A ``witness_reference``.
A witness reaches the post-image through Velvet's tester machinery
(``recordUnappliedKeysTester m = false`` says the extracted program's result
violates the ``ensures`` clause at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block has been stripped so
no tactic script can mask the verdict.

The frozen impl is a ``while`` loop. Under ``loom.semantics.choice "demonic"``
its extracted program is a partial fixpoint elaborated through
``Classical.choice``, which the kernel cannot unfold — so ``decide`` on the
FROZEN tester is stuck for EVERY claim, true or false. Measured here:

    error: Tactic `decide` failed ... its `Decidable` instance ... did not
    reduce to `isTrue` or `isFalse`. ... reduction got stuck

That is ``witness-undecided``: the gold-side exit code carries no information at
all, so a forged witness asserting the rival is CORRECT would clear both of the
usual halves. This battery therefore does not rest on the gold-side build.
Every reject case names ``pos-direct-return`` as its ``witness_reference`` — a
LOOP-FREE impl that shares the frozen spec, VERIFIES, and whose extracted tester
does reduce. The gate refutes each witness against that instead, and there the
refutation is SEMANTIC, not stuck:

    error: Tactic `decide` proved that the proposition
      recordUnappliedKeysTester { ... } = false
    is false

Measured out-of-band for all six with ``scripts/lean_verify.sh``: ELABORATES
against its rival (exit 0), REFUTED against the reference (exit 1, ``decide``
proved it false), STUCK against the frozen loop (exit 1, did not reduce). An
impl the verifier accepts cannot violate its own spec, so a witness that fails
against the reference fails on the spec's content and not on the kernel's
inability to look.

PROOF-SHAPE CONTROL — why each rejection is attributable to the SPEC, not to a
tactic mismatch. Reshaping the impl is what a rival does, and the frozen script
(``loom_solve``, then the backward-fold ``drop_step`` rewrite) is tuned to the
frozen loop, so a merely-RESHAPED correct impl would break it too. Every reject
rival is loop-free with the proof body reduced to a bare ``loom_solve`` — and
``pos-direct-return`` is that EXACT shape and body carrying the CORRECT
expression, and it VERIFIES. So the body is not the confound: under it, each
rival still fails, and the residual goal names the rival's own expression, e.g.

    unsolved goals
    case «ensures_1: out = m.replaces ++ [(m.appLabel, m.name)]»
    ⊢ (if m.replaces.isEmpty = true then [(m.appLabel, m.name)]
        else m.replaces) = m.replaces ++ [(m.appLabel, m.name)]

which is the attribution: the clause refutes the rival's expression.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally distinct correct
    impls must verify (closed form; loop-preserving with the own key named;
    ``List.concat`` instead of ``++``), else the spec is SPEC-TOO-STRONG on the
    shape of the impl rather than on its behaviour.
  * ADMISSIBILITY — RE-AIMED. The sibling self-asserts that a normal
    F2P-shaped input satisfies its fractional-permission precondition. No method
    here has a ``require`` clause and there is no permission surface, so nothing
    could exclude a normal input and that probe is degenerate. The residual risk
    on a total domain is an UNSATISFIABLE / degenerate post-image, so the case
    is re-aimed at the load-bearing property directly.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The class exists on the sibling
    because an input may be held at a fractional heap permission an impl can
    write through. Lean and Velvet are referentially transparent: ``m`` is an
    immutable value, no parameter is declared ``mut`` (the only ``mut`` bindings
    are the loop-local ``result`` / ``i``), and there is no heap, no aliasing,
    no ``Old`` and no permission system. There is no read-only input to
    overwrite and no frame clause to violate. Not fabricated.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: rivals right on part of
    the domain (empty vs non-empty ``m.replaces``; length ≤ 1 vs ≥ 2) and wrong
    elsewhere, plus rivals that corrupt one half of the post-image.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The ``axioms`` region declares no
``axiom`` and mapping.md §3 records no A-reference deep model (the recording
sink is a concrete list append, owed no contract), so there is nothing here for
an axiom probe to establish — and the G-PBT gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14500"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE frozen impl block (between and INCLUDING the markers): one
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- asserted at load, so the manifest breaks loudly on any drift). Every
# ---- loop-free variant — the reference, the closed-form positive, and all six
# ---- rivals — swaps on this block.
_IMPL = (
    "    -- impl-start\n"
    "    let mut result : List (String × String) := [(m.appLabel, m.name)]\n"
    "    let mut i := m.replaces.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ m.replaces.length\n"
    "      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let k := m.replaces[i - 1]!\n"
    "      result := k :: result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the frozen proof body (tactic script only; elided from the spec view).
# ---- A loop-free variant has no backward-fold goal left for `drop_step` to
# ---- rewrite, so it retunes this body. The `prove_correct` HEADER — the
# ---- obligation itself — is never touched by any case.
_PROOF = (
    "prove_correct recordUnappliedKeys by\n"
    "  loom_solve\n"
    "  rw [drop_step m.replaces i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"

# ---- the accumulator initialiser, wholly inside the impl region and unique.
# ---- The admissibility case inserts an in-region `assert` immediately before
# ---- it, keeping the whole frozen body and the frozen proof script.
_RESULT_INIT = (
    "    let mut result : List (String × String) := [(m.appLabel, m.name)]"
)
assert _BASE.count(_RESULT_INIT) == 1, "result-init anchor drift"

# ---- With no loop there is no invariant to peel and no fold step to rewrite,
# ---- so a bare `loom_solve` is the honest body for a loop-free variant — and
# ---- it is honest precisely because `pos-direct-return` (the CORRECT loop-free
# ---- expression) VERIFIES under it. That is the proof-shape control: a rival
# ---- failing under this body fails for its EXPRESSION, not for a script tuned
# ---- to a loop it no longer has.
_PROOF_NOLOOP = "prove_correct recordUnappliedKeys by\n  loom_solve"


def _loopfree(expr, proof=_PROOF_NOLOOP):
    """The impl region reduced to a single loop-free `return <expr>`.

    Loop-freeness is what makes the extracted tester kernel-REDUCE, which is
    what lets a witness say anything at all on this bundle (CARRIER NOTE). It
    is shared by the reference, the closed-form positive and every rival, so it
    is never what a rival is rejected for.
    """
    return _swap(
        _swap(_BASE, _IMPL,
              f"    -- impl-start\n    return {expr}\n    -- impl-end"),
        _PROOF, proof)


# ---- THE WITNESS REFERENCE. The loop-free impl carrying the CORRECT
# ---- expression: a machine-checked-correct impl of the frozen spec whose
# ---- extracted tester REDUCES. It is shipped as a positive control in its own
# ---- right (`pos-direct-return`) and named by every reject case as its
# ---- `witness_reference`, because the FROZEN impl cannot serve as the
# ---- witness's second subject here — its `while` fixpoint leaves `decide`
# ---- stuck for every claim, so its exit code discriminates nothing
# ---- (`witness-undecided`). Pairing the reference with an `expect="verify"`
# ---- case is what records that loop-freeness is not what any rival is being
# ---- rejected for.
_REFERENCE = _loopfree("m.replaces ++ [(m.appLabel, m.name)]")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `recordUnappliedKeysTester m = false` says the extracted
# ---- program's result violates the `ensures` clause at that concrete input.
# ---- Every field is a concrete literal, so no witness binds a hypothesis and
# ---- there is nothing for the gate's inconsistency probe to find (the carrier
# ---- is transparent; conditioning is not needed here). `native_decide` is
# ---- never used: it would compile the fixpoint and hold of the reference too,
# ---- defeating discrimination.
_TESTER = (
    "extract_program_for recordUnappliedKeys\n"
    "prove_precondition_decidable_for recordUnappliedKeys\n"
    "prove_postcondition_decidable_for recordUnappliedKeys\n"
    "derive_tester_for recordUnappliedKeys\n\n"
)


def _witness(migration):
    return (_TESTER
            + "example : recordUnappliedKeysTester\n"
            + f"    ({migration} : Migration) = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen code shape rather than to the
    # behaviour). Three distinct shapes: loop-free closed form, the frozen loop
    # with the own key named, and a different list-append primitive.
    # =====================================================================
    {
        "id": "pos-direct-return",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest correct impl: return the grounded closed form the
        # clause names, no loop at all — maximally different from the frozen
        # backward scan. THIS IS ALSO THE BATTERY'S WITNESS REFERENCE, and the
        # case that makes every reject verdict here interpretable. Two things
        # are measured only because it ships:
        #   (a) PROOF ATTRIBUTION. It verifies under the same bare `loom_solve`
        #       every rival carries, so a rival's failure is its EXPRESSION's,
        #       not a tactic mismatch against a loop it no longer has.
        #   (b) WITNESS DISCRIMINATION. Its extracted tester REDUCES, so each
        #       reject witness is refuted against it SEMANTICALLY — the
        #       discrimination the reduction-stuck gold build cannot supply.
        "module": _REFERENCE,
        "rationale": (
            "the clause `out = m.replaces ++ [(m.appLabel, m.name)]` is "
            "satisfied by returning that expression verbatim, so this must "
            "verify on the whole (total) domain; if it did not, the spec would "
            "be over-fit to the frozen loop's shape (SPEC-TOO-STRONG). It is "
            "also the honest no-echo control: the closed form IS the real work "
            "here (the clause is grounded in `m`, not in an opaque oracle), so "
            "a direct return is correct rather than a cheat — every WRONG "
            "expression below fails the same clause. And it is the battery's "
            "INTERPRETIVE CONTROL: it is the rivals' exact shape and proof "
            "body, so (a) their rejection is attributable to their expression "
            "and (b) their witnesses are refutable against a CORRECT impl whose "
            "tester actually reduces. Ports the sibling pos-control-local-reshape "
            "into the maximally-different correct shape. Measured with "
            "scripts/lean_verify.sh (exit 0)."),
    },
    {
        "id": "pos-ownkey-local",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole frozen loop, its invariants AND the frozen proof
        # script; only binds the own key to a named typed local and threads it
        # through the same accumulator and the same invariant. Observationally
        # identical at every input. This is the sibling's local-variable reshape
        # in the shape that keeps the frozen proof intact.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    let ownKey : String × String := (m.appLabel, m.name)\n"
            "    let mut result : List (String × String) := [ownKey]\n"
            "    let mut i := m.replaces.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ m.replaces.length\n"
            "      invariant result = m.replaces.drop i ++ [ownKey]\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let k := m.replaces[i - 1]!\n"
            "      result := k :: result\n"
            "      i := i - 1\n"
            "    return result\n"
            "    -- impl-end"),
        "rationale": (
            "binding the own key to a typed local before the scan leaves the "
            "build, every invariant and the frozen tactic script unchanged, so "
            "the clause still discharges on the whole domain. A correct reshape "
            "must verify, else the postcondition rejects a faithful impl over "
            "the shape of its loop body (SPEC-TOO-STRONG). Ports the sibling "
            "pos-control-local-reshape verbatim in intent — name the "
            "per-iteration value and the trailing own key in locals before "
            "appending — in the loop-PRESERVING form, so this case also attests "
            "that the frozen proof is not what any rival is failing."),
    },
    {
        "id": "pos-concat-primitive",
        "kind": "soundness",
        "expect": "verify",
        # A third correct shape: build the sequence with `List.concat` (append
        # one element at the tail) rather than `++` with a singleton. Same value
        # at every input, but a DIFFERENT primitive from the one the clause is
        # written with — so this is the control against the clause being
        # satisfiable only by its own syntactic form.
        "module": _loopfree("m.replaces.concat (m.appLabel, m.name)"),
        "rationale": (
            "`m.replaces.concat ownKey` is definitionally the same sequence as "
            "`m.replaces ++ [ownKey]`, so a correct impl written with a "
            "different append primitive must still verify. This is the control "
            "against the weakest form of SPEC-TOO-STRONG that the other two "
            "positives cannot see: pos-direct-return returns the clause's own "
            "expression verbatim and pos-ownkey-local keeps the frozen scan, so "
            "neither would notice a clause satisfiable only by its own "
            "syntactic shape. Added on top of the sibling's single positive, "
            "whose carrier (a `PSeq` append) has no second primitive to vary."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The sibling's case guards against a
    # PRECOND-TOO-STRONG / unreachable postcondition by self-asserting that a
    # normal F2P-shaped input is admitted and the pinned post-image is
    # reachable. No method here has a `require` clause, so nothing could
    # exclude a normal input and that half is degenerate. The residual
    # admissibility risk on a TOTAL domain is a DEGENERATE post-image — a
    # clause no impl distinguishes reads exactly like one every impl meets.
    # This case discharges an in-region `assert` pinning the LOAD-BEARING
    # property (the recorded sequence always ENDS with the step's own key,
    # i.e. the own key is appended unconditionally) on every input, while
    # keeping the impl and the frozen proof script VERBATIM so the method's own
    # obligation still discharges. The assert is live, not decoration: the same
    # claim with the own key's two components transposed leaves an unsolved
    # goal (measured out-of-band, exit 1, `case «admiss_1: ...»` unsolved).
    # =====================================================================
    {
        "id": "admiss-own-key-last",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    assert (with_name_prefix `admiss\n"
            "      ((m.replaces ++ [(m.appLabel, m.name)]).getLast (by simp)\n"
            "        = (m.appLabel, m.name)))\n"
            + _RESULT_INIT),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate on the whole "
            "domain: the in-region assert establishes that the recorded "
            "sequence's LAST element is the step's own key for EVERY input — "
            "the load-bearing unconditional-append property, and the one a "
            "degenerate clause would not pin — and it discharges. The impl and "
            "the frozen proof script are kept verbatim, so the method's own "
            "`ensures` still discharges alongside it; if the assert could not "
            "discharge, the obligation would be unreachable rather than merely "
            "hard. Re-aims the sibling admiss-self-check from precondition "
            "admissibility (vacuous here: no `require` clause, no permission "
            "surface) to post-image non-degeneracy. Liveness measured: "
            "transposing the own key's components in the same assert leaves an "
            "unsolved goal."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a DISTINCT concrete input and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test. Every rival is
    # loop-free under a bare `loom_solve`, the exact shape and body
    # pos-direct-return VERIFIES under, so its rejection is attributable to its
    # expression; and every witness is refuted against that reference rather
    # than against the reduction-stuck frozen loop (CARRIER NOTE).
    #
    # The failing test's scenario grounding every refinement: a composite step
    # standing in for TWO others is applied, then reversed, and the test asserts
    # the COMPOSITE's own key is no longer marked current.
    # =====================================================================

    # ---- the own-key suffix: is it recorded at all? ----
    {
        "id": "weak-prepatch-else-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG, verbatim: the own key is recorded ONLY for a step that stands
        # behind nothing. Correct on the whole empty-`replaces` sub-domain;
        # drops the own key for every composite step.
        "module": _loopfree(
            "if m.replaces.isEmpty then [(m.appLabel, m.name)] "
            "else m.replaces"),
        "refinement": (
            "this IS the pre-change behaviour: the own key is recorded only in "
            "the complementary branch, for a step that stands behind nothing. "
            "Its faithful real counterpart therefore never records a COMPOSITE "
            "step's own key while the steps it stands in for are present — "
            "exactly the failing test's setup — so the composite stays marked "
            "current after being reversed and the assertion that it is no "
            "longer current still fails. It does NOT resolve. This is the exact "
            "defect the change corrects."),
        "rationale": (
            "REJECT from `out = m.replaces ++ [(m.appLabel, m.name)]`: for a "
            "NON-EMPTY `m.replaces` this returns `m.replaces`, missing the "
            "required own-key suffix. Refuted at the failing test's own shape "
            "— `m.replaces` of length 2 with a distinct composite own key — "
            "where the reference yields the two replaced keys followed by the "
            "composite key and the rival yields only the two replaced keys. "
            "Verifying would be SPEC-TOO-WEAK (the clause would admit the "
            "bug). Its point is the COMPLEMENT of weak-own-omitted's: at "
            "`m.replaces = []` this rival AGREES with the frozen solution, so "
            "the two cannot share a witness. Sibling weak-prepatch-else-only."),
        "witness": _witness(
            '{ replaces := [("migrations", "0001_initial"), '
            '("migrations", "0002_second")], '
            'appLabel := "migrations", name := "0001_squashed_0002" }'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-own-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        # Blunter: the own key is NEVER recorded, for any step. Wrong on the
        # WHOLE domain — including the empty case, where the previous rival is
        # right. That is what separates their witnesses.
        "module": _loopfree("m.replaces"),
        "refinement": (
            "a counterpart that never records the reversed step's own key at "
            "all leaves the step marked current after it is reversed, for a "
            "composite step and an ordinary one alike, so the failing test's "
            "assertion that the composite is no longer current still fails. It "
            "does NOT resolve — and it additionally breaks the ordinary-step "
            "behaviour the unchanged tests already rely on."),
        "rationale": (
            "REJECT from `out = m.replaces ++ [(m.appLabel, m.name)]`: this "
            "returns `m.replaces`, dropping the own-key suffix on EVERY input. "
            "Refuted at `m.replaces = []` — where the required answer is the "
            "singleton own key and the rival returns the empty sequence — "
            "because that is precisely the sub-domain where "
            "weak-prepatch-else-only agrees with the frozen solution. Refuting "
            "the blunt rival there rather than at a composite step is what "
            "makes the two cases probe different content instead of restating "
            "one discrimination twice, and it is the only witness that moves "
            "`m.replaces` to empty against a dropped own key. Sibling "
            "weak-own-omitted."),
        "witness": _witness(
            '{ replaces := [], appLabel := "app", name := "0001_initial" }'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-partial-len",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL DOMAIN, the near-miss: correct for a step standing behind at
        # most one other (which includes the whole empty case AND length 1), and
        # drops the own key only from length 2 up. It agrees with gold over
        # strictly more of the domain than either rival above, so it gets its
        # own witness further out.
        "module": _loopfree(
            "if m.replaces.length ≤ 1 then "
            "m.replaces ++ [(m.appLabel, m.name)] else m.replaces"),
        "refinement": (
            "correct when a step stands behind at most one other, but drops the "
            "own key once it stands behind two or more — and the failing test "
            "drives a composite standing behind exactly TWO. Its faithful "
            "counterpart (own key recorded only below that threshold) never "
            "records that composite's own key, so the composite stays marked "
            "current and the assertion still fails. It does NOT resolve. The "
            "narrowest of the three drop rivals: it passes every ordinary step "
            "and every single-replacement step, which is what makes it a real "
            "partial-domain break rather than a blunt one."),
        "rationale": (
            "REJECT from `out = m.replaces ++ [(m.appLabel, m.name)]` on the "
            "length ≥ 2 sub-domain only: there this returns `m.replaces` with "
            "no own-key suffix. Refuted at length THREE, past the threshold and "
            "past every other witness's length, so the point is not one the "
            "blunter drop rivals could be refuted at — this rival is CORRECT at "
            "lengths 0 and 1, so a witness there would not discriminate it at "
            "all. This is the case that moves `m.replaces.length` off {0,1,2} "
            "and pins the clause's dependence on the whole prefix rather than "
            "on a bounded prefix. Sibling weak-partial-domain-len2, pushed one "
            "length further out so it cannot share a point."),
        "witness": _witness(
            '{ replaces := [("blog", "0001_a"), ("blog", "0002_b"), '
            '("blog", "0003_c")], '
            'appLabel := "blog", name := "0001_squashed_0003" }'),
        "witness_reference": _REFERENCE,
    },

    # ---- the own-key VALUE: is it the right key? ----
    {
        "id": "weak-own-components-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # The presence decision and the position are both RIGHT; only the
        # recorded key's value is wrong — its two components are transposed.
        # This is the only rival that attacks the own key's internal structure,
        # and the only one that varies `appLabel` against `name`.
        "module": _loopfree("m.replaces ++ [(m.name, m.appLabel)]"),
        "refinement": (
            "a counterpart that records the reversed step's own key with its "
            "two components transposed marks a DIFFERENT — in general "
            "non-existent — key as no-longer-current, and leaves the real key "
            "still marked current. The failing test asserts membership of the "
            "real composite key, so it still fails. It does NOT resolve, and it "
            "additionally corrupts the current-set with a key that names no "
            "step at all."),
        "rationale": (
            "REJECT from `out = m.replaces ++ [(m.appLabel, m.name)]`: this "
            "appends `(m.name, m.appLabel)`, which differs from the required "
            "own key at every input whose two components differ. Refuted at "
            "`m.replaces = []` with `appLabel ≠ name`, the input that makes the "
            "clause's dependence on the two components INDIVIDUALLY (not just "
            "on their unordered pair) observable — a distinction no other rival "
            "probes, since every other rival gets the own key's value right or "
            "omits it entirely. Without this case both own-key binders would be "
            "attacked only jointly, so a rival that mishandled just one of them "
            "would verify. Added: the sibling models a key as a single int "
            "code, so its carrier has no component structure to get wrong."),
        "witness": _witness(
            '{ replaces := [], appLabel := "core", name := "0002_later" }'),
        "witness_reference": _REFERENCE,
    },

    # ---- the replaced-key PREFIX: is it carried through? ----
    {
        "id": "weak-drops-replaced",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror of the drop rivals: gets the own-key suffix exactly right
        # and corrupts the OTHER half, recording only the own key and none of
        # the keys the step stands in for. Without this case nothing attests
        # that the prefix half of the clause is load-bearing.
        "module": _loopfree("[(m.appLabel, m.name)]"),
        "refinement": (
            "a counterpart that records only the reversed step's own key and "
            "none of the keys it stands in for leaves every one of those "
            "replaced steps marked current after the composite is reversed. "
            "That breaks the pre-existing behaviour the unchanged tests already "
            "pin — reversing a composite step un-marks the steps it stands "
            "behind — so the suite does not come out green even though the "
            "failing test's own assertion about the composite key would now "
            "hold. It does NOT resolve."),
        "rationale": (
            "REJECT from `out = m.replaces ++ [(m.appLabel, m.name)]`: with a "
            "non-empty `m.replaces` this returns just the singleton own key "
            "where the clause demands the replaced-key prefix first. Refuted at "
            "`m.replaces` of length ONE — the only witness at that length, and "
            "the minimal input at which the prefix is observable at all — which "
            "is what makes the clause's dependence on the prefix machine-checked "
            "rather than assumed. It is also the only rival whose own-key suffix "
            "is entirely correct, so it isolates the prefix half of the clause "
            "the way the drop rivals isolate the suffix half. Added: every "
            "sibling rival keeps the replaced keys, so none attests the prefix."),
        "witness": _witness(
            '{ replaces := [("api", "0001_first")], '
            'appLabel := "api", name := "0002_squashed_0001" }'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-spurious-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-recording, the supporting case: the whole required sequence is
        # produced correctly and then a spurious EXTRA key is appended. Every
        # other rival under-records or mis-values; this one is the only rival
        # whose output CONTAINS the correct answer as a prefix, so it is the
        # only one that tests the clause as an EXACT equality rather than as a
        # containment.
        "module": _loopfree(
            'm.replaces ++ [(m.appLabel, m.name), '
            '(m.appLabel, m.name ++ "0")]'),
        "refinement": (
            "a counterpart that issues an extra recording for a step that was "
            "not part of this reversal marks an UNRELATED step as "
            "no-longer-current, corrupting the current-set beyond what the "
            "reversal should touch. The failing test's own assertion about the "
            "composite key would hold, but the unchanged tests that pin which "
            "steps remain current after a reversal would break, so the suite "
            "does not come out green. It does NOT resolve. Note this "
            "over-records a DISTINCT spurious key, not a duplicate of the own "
            "key: a duplicate is idempotent under the set-membership observable "
            "and so would resolve, which is exactly why the duplicate-record "
            "rival is omitted (footer) and this one is shipped."),
        "rationale": (
            "REJECT from the EXACT sequence equality: the clause pins the "
            "replaced keys followed by the SINGLE own key, so a trailing extra "
            "element makes the recorded sequence longer than "
            "`m.replaces ++ [(m.appLabel, m.name)]`. Refuted at `m.replaces` of "
            "length 2 with a composite own key. This is the only rival that "
            "produces the required sequence as a proper PREFIX of its output, "
            "so it is the only one whose rejection depends on the clause being "
            "an equality rather than a containment — if the clause were weakened "
            "to 'the required keys are among those recorded', every other rival "
            "here would still be caught and this one would verify. Sibling "
            "weak-spurious-extra-key, with the spurious key derived from the "
            "input (rather than a fixed literal) so it is wrong at every "
            "input, not just at inputs avoiding one sentinel value."),
        "witness": _witness(
            '{ replaces := [("shop", "0001_init"), ("shop", "0002_more")], '
            'appLabel := "shop", name := "0003_squashed" }'),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 6 SPEC cases (1
# soundness positive, 1 admissibility, 4 uniqueness rivals) plus an AXIOM lane
# of 2 probes; every one is accounted for below. The sibling contracts ONE
# function, `keys_leaving_applied_set(own_key: int, replaced_keys) -> List[int]`
# over int-coded keys; this bundle contracts ONE method,
# `recordUnappliedKeys (m : Migration)`, over `String × String` keys collected
# into a single `Migration` structure. The defended surface is therefore nearly
# the SAME surface, and the port is close to one-to-one — the carrier change
# (int codes -> two-component string keys, two positional args -> one structure)
# is what removes one class and adds another.
#
#   sibling case                 kind          -> here                        disposition
#   -------------------------------------------------------------------------------------
#   pos-control-local-reshape    soundness     -> pos-ownkey-local            PORTED
#   (no sibling)                 soundness     -> pos-direct-return           ADDED
#   (no sibling)                 soundness     -> pos-concat-primitive        ADDED
#   admiss-self-check            admissibility -> admiss-own-key-last         RE-AIMED
#   weak-prepatch-else-only      uniqueness    -> weak-prepatch-else-only     PORTED
#   weak-own-omitted             uniqueness    -> weak-own-omitted            PORTED
#   weak-partial-domain-len2     uniqueness    -> weak-partial-len            PORTED
#   weak-spurious-extra-key      uniqueness    -> weak-spurious-extra-key     PORTED
#   (no sibling)                 uniqueness    -> weak-own-components-swapped ADDED
#   (no sibling)                 uniqueness    -> weak-drops-replaced         ADDED
#   AXIOM_TESTS (2)              axiom         -> (none)                      DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 3 soundness, 1 admissibility, 6 uniqueness.
# 4 sibling uniqueness rivals ported intact, 1 admissibility re-aimed, 1
# soundness positive ported, 4 cases added, 2 axiom probes dropped. NOTHING was
# dropped for being hard to prove, and no soundness positive was abandoned: all
# three positives close honestly (two with a bare `loom_solve`, one with the
# frozen script untouched), so there is no gap of that kind to report.
#
# PORTED (4 uniqueness + 1 soundness). The sibling's rivals carry across almost
#   unchanged because the surface does: the pre-change else-only branch, the own
#   key never recorded, the length-threshold partial-domain break, and the
#   spurious extra recording are all expressible directly against
#   `out = m.replaces ++ [ownKey]`. Each keeps its sibling refinement argument
#   (the composite step stays marked current / the current-set is corrupted),
#   now backed by a machine-checked witness at a DISTINCT input point. Two
#   sharpenings while porting, both to stop a case claiming a sub-domain the
#   manifest never demonstrates:
#     * weak-partial-len is refuted at length THREE rather than at the sibling's
#       length 2. It is CORRECT at lengths 0 and 1, and length 2 is already
#       weak-prepatch-else-only's point; moving it out one length keeps the two
#       from sharing a discrimination and pins the clause on the whole prefix.
#     * weak-spurious-extra-key derives its spurious key from the input
#       (`m.name ++ "0"`) instead of the sibling's fixed offset from `own_key`.
#       A fixed literal is wrong only at inputs that avoid it; a derived one is
#       wrong at every input, so the rival is a real break across the domain
#       rather than at a chosen point.
# ADDED (4), each closing a coverage hole the sibling's carrier cannot have:
#   pos-direct-return       — the loop-free closed form. Needed for THREE
#       independent reasons beyond being a second positive: it is the battery's
#       `witness_reference` (the frozen loop cannot serve, see below), it is the
#       proof-shape control that makes every rival's rejection attributable to
#       its expression rather than to a broken tactic script, and it is the
#       honest no-echo control.
#   pos-concat-primitive    — a correct impl written with a DIFFERENT append
#       primitive. Without it, both other positives satisfy the clause either by
#       returning its own expression verbatim or by keeping the frozen scan, so
#       neither would notice a clause satisfiable only by its own syntactic form.
#   weak-own-components-swapped — attacks the own key's VALUE component-wise.
#       The sibling abstracts a key to a single int code, so its carrier has no
#       component structure to transpose; here a key is a `String × String`.
#       Without this case `appLabel` and `name` are attacked only JOINTLY, and a
#       rival mishandling exactly one of them would verify unnoticed — the
#       precise failure mode the two known real misses had.
#   weak-drops-replaced     — attacks the replaced-key PREFIX half of the
#       clause. Every sibling rival preserves the prefix, so none attests it is
#       load-bearing; this one records only the own key, at the minimal length
#       (1) where the prefix is observable.
# RE-AIMED (admiss-self-check -> admiss-own-key-last): the sibling asserts that
#   its maximally-permissive precondition admits a normal F2P-shaped input and
#   that the pinned post-image is reachable. No method here has a `require`
#   clause and there is no permission surface, so nothing could exclude a normal
#   input and that half is degenerate. The sharper residual risk on a total
#   domain is a DEGENERATE post-image, so the case is re-aimed at a live
#   in-region assert of the load-bearing property (the recorded sequence always
#   ENDS with the own key) with the impl and frozen proof kept verbatim.
# DROPPED — AXIOM_TESTS (2). The sibling's `ax-aref-unapply-recording` and
#   `ax-aref-containment` re-establish a deep-model A-reference by driving the
#   real post-change callee in the instance image. This bundle declares NO
#   `axiom` and mapping.md §3 records NO A-reference deep model (the recording
#   sink is a concrete list append, owed no contract), so there is nothing here
#   for an axiom probe to establish — and the G-PBT gate ignores AXIOM_TESTS
#   regardless. The axiom lane is G-AX's job.
#
# FRAME / PERMISSION-MUTATION: VACUOUS, not omitted. The sibling's analysis
#   records this class as N/A on its own carrier too (its own_key is an int VALUE
#   and its replaced_keys a mathematical sequence VALUE, with the freshly built
#   result the only heap object), so there was nothing to port even before the
#   backend change. And independently: this backend is referentially transparent
#   — `m` is an immutable value, no parameter is declared `mut` (only the
#   loop-local `result` / `i` are), and there is no heap, no aliasing, no `Old`
#   and no permission system. The nearest expressible analogue, assigning to the
#   read-only parameter inside the impl region, is refused by the carrier at
#   ELABORATION rather than by the postcondition, so a ported rival of that shape
#   would reject for a binder reason with no spec content and there would be
#   nothing for a witness to state. Not fabricated.
#
# ORDER-PERMUTING and DUPLICATE-RECORD rivals: OMITTED ON PRINCIPLE, and this is
#   the one place where a rival the CLAUSE rejects is deliberately not shipped.
#   The clause is an exact sequence equality, so it would reject both — a rival
#   recording the own key FIRST, and one recording it twice, are both refutable
#   here. But the failing test observes "marked current" as SET MEMBERSHIP, so
#   recording order and multiplicity are invisible to it: the faithful real
#   counterpart of either shape WOULD resolve the instance. Shipping them would
#   therefore record a rejection that says nothing about verify-implies-resolve
#   — the clause is simply stricter than the observable on that axis — and their
#   `refinement` field could not be written honestly. The sibling reaches the
#   same conclusion from its own refinement analysis (membership is a set, so
#   order is invisible to the F2P observable) and ships no order rival either.
#   weak-spurious-extra-key is the over-recording case that IS shipped, because
#   a DISTINCT spurious key does change the observable set.
#
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# CLAUSE / BINDER / POINT COVERAGE. ONE `ensures` clause,
#   `out = m.replaces ++ [(m.appLabel, m.name)]`, with two independent halves —
#   the replaced-key PREFIX and the own-key SUFFIX. The clause is DEFENDED by
#   three positives plus the admissibility case (all four verify) and ATTACKED
#   by all six rivals, with both halves attacked separately: the suffix by
#   weak-prepatch-else-only / weak-own-omitted / weak-partial-len (present or
#   not) and weak-own-components-swapped (present but wrong-valued); the prefix
#   by weak-drops-replaced; and the equality-vs-containment strength of the
#   clause by weak-spurious-extra-key alone. The three input binders are moved
#   across SIX distinct points (pts = 6):
#     * weak-prepatch-else-only     replaces len 2   appLabel "migrations"
#     * weak-own-omitted            replaces len 0   appLabel "app"
#     * weak-partial-len            replaces len 3   appLabel "blog"
#     * weak-own-components-swapped replaces len 0   appLabel "core", ≠ name
#     * weak-drops-replaced         replaces len 1   appLabel "api"
#     * weak-spurious-extra-key     replaces len 2   appLabel "shop"
#   So `m.replaces.length` ranges over {0, 1, 2, 3}; `m.appLabel` and `m.name`
#   take a different pair in every case and are additionally varied AGAINST EACH
#   OTHER by weak-own-components-swapped, which is the case that stops the two
#   own-key components from being probed only as an unordered pair. No binder is
#   pinned at a single value across the reject set.
#   MEANINGFULNESS (not just distinctness): at each of the six points the
#   reference's own output differs from the rival's, element-for-element, and no
#   two points are two spellings of one discrimination — they split by whether
#   the own key is dropped on the empty sub-domain (where the pre-change rival
#   is CORRECT and so cannot be refuted), on the composite sub-domain, only past
#   a length threshold, by the own key's component ORDER, by the prefix, and by
#   exactness of the sequence rather than containment.
#
# WITNESS MECHANICS. The carrier is fully TRANSPARENT (the `axioms` region
#   declares no opaque leaf; `m.replaces ++ [ownKey]` is a concrete term over
#   `m`), so the tester + `decide` path is LIVE and no witness needs to condition
#   on the carrier — every witness states its refutation at concrete literals,
#   binds no hypothesis, and so has nothing for the gate's inconsistency probe
#   to find. Each rival is loop-free, so its extracted `recordUnappliedKeysTester`
#   reduces at the concrete literal.
#   BUT THE GOLD-SIDE BUILD IS NOT THE DISCRIMINATOR HERE. The frozen impl keeps
#   a `while` loop, whose fixpoint elaborates through `Classical.choice` under
#   `loom.semantics.choice "demonic"`; the kernel cannot unfold it, so `decide`
#   against the frozen tester is STUCK for every claim ("did not reduce to
#   `isTrue` or `isFalse`"), true or false alike, and its exit code discriminates
#   nothing. That is `witness-undecided`, and a witness resting on it would let a
#   forgery asserting the rival is CORRECT clear both usual halves. So every
#   reject case names `pos-direct-return` as its `witness_reference`: a
#   loop-free, same-spec, VERIFYING impl whose tester does reduce. All six
#   checked out-of-band with scripts/lean_verify.sh — ELABORATES against its
#   rival (exit 0); REFUTED against the reference (exit 1, "`decide` proved that
#   the proposition ... is false"); STUCK against the frozen loop (exit 1, did
#   not reduce). The reference is shipped as an `expect="verify"` case in its own
#   right, so the battery itself records that loop-freeness is not what any rival
#   is being rejected for.
AXIOM_TESTS = []
