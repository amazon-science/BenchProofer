"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13779 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct validateWeightSupport`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against a subject KNOWN to satisfy the spec. On this bundle that subject is the
declared ``witness_reference``, not the frozen solution — gold's ``while`` loop
cannot decide anything, so it could not serve as one; see WITNESS MECHANICS.

DEFENDED SURFACE (one contracted method over one read-only input).

  validateWeightSupport (members : List Member) return (out : Except Int Unit)
    ensures out = validate members                                   -- C1 (master)

An ensemble is a ``List Member``; each ``Member`` carries three observed facts
(mapping.md §2): ``name`` (an integer identity, reported on failure),
``present`` (whether the member is actually supplied), and ``supports``
(whether a *present* member accepts a per-sample weighting parameter — immaterial
for an absent member). When a per-sample weighting is supplied, validation
succeeds exactly when no present member is unsupported, and otherwise fails
reporting the FIRST present member (in order) that does not accept a per-sample
weighting. ``validate`` is a total, front-recursive ``def`` over the method's own
argument — a fully unfolded function of ``members``, NOT an opaque answer-key
oracle (the ``axioms`` region declares no ``axiom``; ``supports`` is a plain input
field, not an axiomatized callee verdict). So pinning ``out = validate members``
is GROUNDED, not an echo: any wrong scan diverges from ``validate members`` at a
concrete input. ``members`` is read-only (no ``mut`` binder) and there is no
``require`` clause — the input is total over every ``List Member``, which is what
makes the partial-domain rivals refutable at a concrete point.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``out = validate members``) is the sole
``ensures`` and the only impl-constraining clause. It pins BOTH legs at once — the
success/failure outcome AND the exact reported identity — at every position of the
scan. Every uniqueness rival therefore targets C1, each at a distinct facet
(skip-absent, success-vs-failure on both polarities, reported identity, and the
front-most / first-offender ordering).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — the PERMISSION half is vacuous; the LAUNDERING
    half is expressible and is carried as ``weak-launder-input``. The nagini
    sibling's rival WRITES through a read-only (``Acc(.,1/2)``) reference to the
    roster and is rejected for INSUFFICIENT PERMISSION. That exact rejection has no
    counterpart here: Velvet is referentially transparent, there is no heap,
    aliasing, or permission system, and making ``members`` writable would need a
    ``mut`` binder in the METHOD HEADER — which lives in the spec view, so such a
    variant fails ``same_spec`` and is out of scope, not a rejection (measured).
    But the nagini rival's STRATEGY — satisfy the post-image on a doctored copy of
    the input instead of on the input — survives the carrier change as a local
    rebind inside the impl region, which IS in scope. It is rejected because C1
    quantifies over the ORIGINAL ``members``, so the class is ported rather than
    dropped (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image C1 is
    ``validate members``, a transparent front-recursive fold over the method's own
    argument; there is no answer key to echo. The honest cheapest CORRECT impl
    (``return validate members``) is carried as a POSITIVE control instead — it
    doubles as proof the spec is not echo-vulnerable, since any WRONG scan fails
    ``out = validate members``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. A rival can
    validate every ensemble correctly except in a sub-domain: skip the FIRST member
    or skip the LAST one (wrong iff that member is the sole offender — two disjoint
    sub-domains, each rival correct where the other is refuted), treat every member
    as present (the pre-image bug, wrong iff an absent member is unsupported), or
    report the wrong identity on the failure leg — either a constant, or the LAST
    offender rather than the first, which isolates the ordering clause because it
    gets the success/failure decision right everywhere.
  * CONTROL-FLOW-EFFECT — the sole outcome axis is success vs failure. A rival that
    always succeeds (``weak-never-raise``) and one that always fails
    (``weak-always-raise``) attack exactly that axis against C1.
  * PROBE-ON-ABSENT (the pre-image bug) — a rival that consults the weighting-
    acceptance fact on EVERY member, absent ones included, so an absent-and-
    unsupported member wrongly fails validation. On this carrier the ``present``
    guard is not a callee precondition (there is no axiomatized callee — mapping.md
    §3) but a branch of ``validate`` itself; dropping it is a plain C1 divergence,
    refutable at an absent member.
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
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

WITNESS MECHANICS ON THIS BUNDLE. The tester+``decide`` path
(``derive_tester_for`` → ``<name>Tester args = false := by decide``) is DEAD here:
``prove_postcondition_decidable_for validateWeightSupport`` leaves a residual
``Decidable (out = validate members)`` goal that does not discharge for the
extracted program, and ``decide`` gets stuck on the derived tester (measured: both
a wrong rival and gold fail the tester build identically, discriminating nothing).

But C1's carrier IS transparent. Each rival is written LOOP-FREE (a
``members.foldr`` / ``.dropLast`` / ``match`` expression, no ``while``), so its
extracted program ``validateWeightSupportExec`` — the ``NonDetT``-run of the impl
— REDUCES fully under ``decide`` at a concrete input. Each witness states, at one
concrete input, that the rival's own output differs from what C1's transparent
post-image ``validate`` demands:

    proj (match validateWeightSupportExec <input> with | DivM.res r => r | _ => …)
        ≠ proj (validate <input>)

where ``proj : Except Int Unit → Option Int`` maps ``ok`` to ``none`` and
``error n`` to ``some n`` (``Except Int Unit`` derives no ``DecidableEq``, but
``Option Int`` does — ``proj`` preserves both the success/failure distinction and
the reported identity, so the ``≠`` is exactly a C1 violation and is decidable).

THE SECOND HALF IS NOT REFUTED AGAINST GOLD, and that is deliberate. Gold's body
is the backward ``while`` loop, whose ``…Exec`` elaborates through well-founded
recursion the kernel does not reduce, so building any of these witnesses against
the frozen solution exits 1 with ``Tactic `decide` failed ... its `Decidable`
instance instDecidableNot did not reduce to `isTrue` or `isFalse``` — a STUCK
REDUCTION. That is the SAME error a TRUE claim about gold would produce, so the
exit code attests to a refutation that was never performed (gates/pbt.py
``_stuck`` → ``witness-undecided``). A witness that fails on gold for that reason
is not a discriminator.

So every reject case declares an explicit ``witness_reference``: the loop-free
correct impl of this same frozen spec (``_REF_LOOPFREE``, the ``pos-control-direct``
source). The gate re-checks that it shares the frozen spec and VERIFIES before
using it, and an impl the verifier accepts cannot violate its own spec, so a
genuine refutation must FAIL there — and because it is loop-free, its ``…Exec``
reduces, so the failure is a REAL VERDICT rather than a stuck term.

No witness here binds any hypothesis (every input is a concrete literal that
decides C1), so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque). Every witness was rebuilt with
``scripts/lean_verify.sh``: each ELABORATES against its rival (exit 0) and fails
against ``_REF_LOOPFREE`` (exit 1) with ``Tactic `decide` proved that the
proposition ... is false`` — a semantic refutation of the concrete claim, naming
the very input the case discriminates at. It was also confirmed per rival that
``validateWeightSupportExec <input>`` really reduces to a ``DivM.res``, so the
witness's ``match`` arm is the computed result and not the ``Except.ok ()``
fallback.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle consumes NO ``axiom`` (the
weighting-acceptance fact is a pure input field ``Member.supports``, a type
refinement, not an axiomatized contract — mapping.md §3); ``axiom_check.py`` still
runs the real callee as a bridge check, but that is G-AX's job and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13779"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (backward `while` fold),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    -- impl-start\n"
    "    -- Scan the members back-to-front, keeping the earliest failure seen so far.\n"
    "    -- A present member that does not accept a per-sample weighting becomes the\n"
    "    -- recorded failure; an absent member contributes nothing (it is skipped);\n"
    "    -- a present, supported member leaves the running outcome unchanged. Because\n"
    "    -- the scan runs back-to-front, the earliest (front-most) failure is the one\n"
    "    -- that survives — exactly the first offending member.\n"
    "    let mut result : Except Int Unit := Except.ok ()\n"
    "    let mut i := members.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ members.length\n"
    "      invariant result = validate (members.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let m := members[i - 1]!\n"
    "      result := if (m.present && !m.supports) then Except.error m.name else result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it as-is
# too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct validateWeightSupport by\n"
    "  loom_solve\n"
    "  rw [validate_drop_step members i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced. The impl
    marker comments and both marker lines are re-emitted so the edit stays wholly
    inside the -- impl-start .. -- impl-end region (same_spec by construction)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for loop-free / reshaped correct
    impls whose residual goal no longer matches the frozen backward-fold tactic)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- A loop-free rival built from a fold/expression over `members`. Being
# ---- loop-free, its extracted `…Exec` reduces under `decide` so its witness
# ---- discriminates; gold's `while`-loop `…Exec` stays stuck.
def _expr(body):
    return _impl("    return (" + body + ")")


# ---- witness preamble + builder. The postcondition's Decidable instance does not
# ---- discharge for the extracted program (the tester+`decide` path is dead), so
# ---- instead extract the executable program and refute C1 directly on the
# ---- TRANSPARENT `validate`. `Except Int Unit` derives no DecidableEq, so both
# ---- sides are projected through `proj : Except Int Unit → Option Int`
# ---- (ok ↦ none, error n ↦ some n) — decidable, and faithful to C1 (preserves
# ---- both the success/failure leg and the reported identity). Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask it.
_EXTRACT = "extract_program_for validateWeightSupport\n\n"
_PROJ = ("(fun (e : Except Int Unit) => match e with "
         "| Except.ok _ => (none : Option Int) | Except.error n => some n)")


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    {_PROJ}\n"
        f"      (match validateWeightSupportExec ({inp}) with | DivM.res r => r | _ => Except.ok ())\n"
        f"    ≠ {_PROJ}\n"
        f"      (validate ({inp})) := by\n"
        "  decide\n"
    )


# ---- WITNESS SUBJECT (the second half of the discrimination check).
# ---- The frozen impl CANNOT serve as the subject here, and this is measured, not
# ---- argued: gold's body is the backward `while` loop, whose extracted
# ---- `validateWeightSupportExec` elaborates through well-founded recursion the
# ---- kernel does not reduce. Building any of the five witnesses against gold
# ---- exits 1 with `Tactic 'decide' failed ... its Decidable instance
# ---- instDecidableNot did not reduce to isTrue or isFalse` — a STUCK REDUCTION,
# ---- which is the same error a TRUE claim about gold would produce, so that exit
# ---- code refutes nothing (gates/pbt.py `_stuck` / `witness-undecided`).
# ----
# ---- So each reject case names an explicit `witness_reference`: the LOOP-FREE
# ---- correct impl of this same frozen spec carried by `pos-control-direct`. It is
# ---- not trusted — the gate re-checks that it shares the frozen spec and VERIFIES
# ---- before using it (`_reference_ok`), and an impl the verifier accepts cannot
# ---- violate its own spec, so a genuine refutation must FAIL against it. Being
# ---- loop-free, its `…Exec` reduces, so the failure is a real verdict: measured,
# ---- each witness exits 1 there with `Tactic 'decide' proved that the proposition
# ---- ... is false` — a SEMANTIC refutation of the concrete claim, naming the very
# ---- input the case discriminates at.
# ----
# ---- Stated explicitly rather than left to the gate's stuck-reduction fallback
# ---- (which would pick this same source anyway, being the first positive in
# ---- manifest order): the attestation a reader gets from the record should say
# ---- WHICH impl the refutation was checked against, and an implicit fallback
# ---- makes that depend on manifest ordering rather than on the manifest's claim.
_REF_LOOPFREE = _impl_reproved(
    "    return (validate members)",
    "prove_correct validateWeightSupport by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole-sequence outcome DIRECTLY via the transparent
        # fold, no per-member loop. C1 is literally `out = validate members`, so
        # this is the cheapest HONEST correct impl — and, since `validate members`
        # is GROUNDED in the argument (not an opaque answer key), it doubles as
        # proof the spec is not echo-vulnerable (any WRONG scan fails
        # `out = validate members`). The loop is gone, so the frozen proof's
        # backward-fold step is unneeded and the residual goal closes under
        # `loom_solve` alone. Also the `witness_reference` every reject case is
        # refuted against (see _REF_LOOPFREE): loop-free, so its extracted program
        # REDUCES, which is what lets a witness fail there by a real verdict.
        "module": _REF_LOOPFREE,
        "rationale": (
            "the post-image `validate members` is GROUNDED in the input (a total "
            "front-recursive fold, no opaque answer key), so `return validate "
            "members` is the honest cheapest CORRECT impl; C1 is literally `out = "
            "validate members`, so it MUST verify, else C1 is SPEC-TOO-STRONG. "
            "Re-expresses the nagini honest positive controls: the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable "
            "(any wrong scan fails `out = validate members`)."
        ),
    },
    {
        "id": "pos-control-local-flag",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind the per-member failure
        # test to a typed local `fails` before the conditional. Same value flow
        # (`fails = m.present && !m.supports`), different control shape; the frozen
        # proof still closes unchanged (loop invariant and step lemma untouched).
        "module": _impl(
            "    let mut result : Except Int Unit := Except.ok ()\n"
            "    let mut i := members.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ members.length\n"
            "      invariant result = validate (members.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let m := members[i - 1]!\n"
            "      let fails := m.present && !m.supports\n"
            "      result := if fails then Except.error m.name else result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the per-member "
            "failure test to a typed local before the conditional) must verify; the "
            "value flow is unchanged (`fails = m.present && !m.supports`) so C1 "
            "still discharges and the frozen loop proof closes as-is. Ports the "
            "nagini pos-nest-branch structural control: if it fails => "
            "SPEC-TOO-STRONG (over-fit to the inline-guard code form)."
        ),
    },
    {
        "id": "pos-control-nested-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: split the single `m.present && !m.supports` guard into a NESTED
        # conditional — `if m.present then (if m.supports then result else error)
        # else result` — the same shape as the gold repo hunk's `if step is None:
        # continue` guard followed by the acceptance test. Logically identical to
        # the gold guard, but the residual goal now needs a case split, so the
        # frozen proof is retuned to close it (`grind` after the fold step).
        "module": _impl_reproved(
            "    let mut result : Except Int Unit := Except.ok ()\n"
            "    let mut i := members.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ members.length\n"
            "      invariant result = validate (members.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let m := members[i - 1]!\n"
            "      result := if m.present then (if m.supports then result else Except.error m.name) else result\n"
            "      i := i - 1\n"
            "    return result",
            "prove_correct validateWeightSupport by\n"
            "  loom_solve\n"
            "  rw [validate_drop_step members i (by omega) (by omega)]\n"
            "  grind"),
        "rationale": (
            "a correct impl that SPLITS the fused failure guard into a nested "
            "present-then-supported conditional — the same two-step shape as the "
            "gold repo hunk (skip an absent member, then test acceptance) — must "
            "verify. It computes the SAME outcome as the fused guard on every "
            "member, so C1 holds; the residual goal needs one extra case split, "
            "closed by retuning the elided proof body (`grind` after the fold "
            "step). If it fails => SPEC-TOO-STRONG (over-fit to the fused-guard "
            "code form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — this method carries NO `require` clause (the pre-conditions
    # region is empty), so the classic "a normal input satisfies the precondition"
    # probe is vacuous: nothing could exclude an F2P-shaped input. Re-aimed at the
    # residual admissibility risk on a total domain — that the post-image is
    # DEGENERATE / trivially satisfiable at the interesting points (a spec no
    # meaningful impl distinguishes reads exactly like a spec every impl meets).
    # This case discharges an in-region `assert`, at concrete F2P-shaped points,
    # that `validate` is NON-DEGENERATE: an ensemble whose only member is absent
    # SUCCEEDS (the exact F2P behaviour — a None member is skipped, so a weighted
    # fit proceeds), a present unsupported member FAILS reporting its identity, and
    # an absent member followed by a present supported one SUCCEEDS (the None-then-
    # supported F2P shape). The surrounding impl is kept verbatim so the method's
    # own C1 obligation still discharges; the proof body is retuned only to clear
    # the extra assert goal (`decide`), which is elided from the spec view. The
    # assert is live, not decoration, and this was MEASURED rather than argued:
    # falsifying each of the three conjuncts in turn (absent member made to fail;
    # the reported identity changed from 7 to 8; absent-then-supported made to fail)
    # breaks the build all three times, so each conjunct is load-bearing and none is
    # a tautology the proof would close regardless.
    # =====================================================================
    {
        "id": "admiss-validate-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (validate [⟨0, false, false⟩] = Except.ok ()\n"
            "        ∧ validate [⟨7, true, false⟩] = Except.error 7\n"
            "        ∧ validate [⟨0, false, false⟩, ⟨7, true, true⟩] = Except.ok ()))\n"
            "    let mut result : Except Int Unit := Except.ok ()\n"
            "    let mut i := members.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ members.length\n"
            "      invariant result = validate (members.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let m := members[i - 1]!\n"
            "      result := if (m.present && !m.supports) then Except.error m.name else result\n"
            "      i := i - 1\n"
            "    return result",
            "prove_correct validateWeightSupport by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [validate_drop_step members i (by omega) (by omega)]; simp_all)"),
        "rationale": (
            "the input carries no `require`, so validation is total over every "
            "`List Member`; the residual admissibility risk is that the post-image "
            "is degenerate. The in-region assert discharges, at concrete F2P-shaped "
            "points, that `validate` is NON-DEGENERATE: an ensemble whose only "
            "member is absent SUCCEEDS (a None member is skipped — the exact F2P "
            "behaviour), a present unsupported member FAILS reporting its identity, "
            "and an absent-then-present-supported ensemble SUCCEEDS. The impl is "
            "kept verbatim so C1 discharges too; the extra goal is closed by "
            "retuning the elided proof body. Re-aimed from the nagini "
            "admiss-precond-nonvacuous, whose read-only-fractional-permission half "
            "has no counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE / degenerate."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a concrete
    # input and the refinement argument for why its faithful real counterpart would
    # NOT resolve the failing/guard tests. All attack C1 (`out = validate members`);
    # the input binder `members` (and its `present` / `supports` / `name` fields and
    # length) is varied across the witnesses.
    # =====================================================================
    {
        "id": "weak-prepatch-probe-on-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image bug: consult the weighting-acceptance fact on EVERY member,
        # absent ones included (drop the `present` guard), so an absent member that
        # happens to carry `supports = false` wrongly fails validation.
        "module": _expr(
            "members.foldr (fun m acc => "
            "if !m.supports then Except.error m.name else acc) (Except.ok ())"),
        "refinement": (
            "this is the pre-image behaviour: the acceptance fact is consulted on "
            "every member, including an absent one, so an absent member is treated "
            "as an offender instead of being skipped. Its faithful real counterpart "
            "is the unpatched code, which reaches the acceptance probe on a member "
            "that is not actually supplied — the exact crash the F2P "
            "test_none_estimator_with_weights exercises (an ensemble with a member "
            "set to None, fit with a per-sample weighting): the unpatched path "
            "aborts on the absent member instead of proceeding, so it would NOT "
            "resolve. This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): `validate` SKIPS an absent "
            "member (`present = false` imposes no requirement), so a rival that "
            "fails on an absent-and-unsupported member diverges from the post-image. "
            "Refuted at input `[⟨0, false, false⟩]` — a single absent member, where "
            "`validate` succeeds but the rival fails. Moves the `present` binder to "
            "`false` (the only witness that does). If it verified => SPEC-TOO-WEAK "
            "(admits the bug)."
        ),
        "witness": _witness("[⟨0, false, false⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-never-raise",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow: always succeed, never report a failure. On an ensemble with
        # a present unsupported member, validation should fail, but this impl
        # succeeds claiming support.
        "module": _expr("Except.ok ()"),
        "refinement": (
            "its faithful real counterpart deletes the failure entirely, so the "
            "pre-check never rejects an unsupported configuration — a present "
            "member that does not accept a per-sample weighting is silently "
            "accepted and then crashes (or silently ignores the weighting) deep in "
            "the fit. The guard test test_sample_weight, which asserts the "
            "validation raises with the offending member's identity on a "
            "weight-rejecting present member, FAILS. A verify-not-resolve break."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): on an ensemble with a "
            "present unsupported member `validate` yields `error`, but this impl "
            "yields `ok`. Refuted at input `[⟨9, true, false⟩]` — one present "
            "unsupported member (`present = true`, `supports = false`), where the "
            "rival succeeds and gold fails. Attacks the success/failure axis of C1. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("[⟨9, true, false⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow: always fail, even when every present member is supported.
        "module": _expr(
            "members.foldr (fun m acc => Except.error m.name) (Except.ok ())"),
        "refinement": (
            "its faithful real counterpart raises unconditionally in the pre-check, "
            "rejecting EVERY weighted fit even when every present member accepts a "
            "per-sample weighting. The F2P test_none_estimator_with_weights (which "
            "fits successfully after skipping the absent member) and the normal "
            "weighted-fit guard tests FAIL. A verify-not-resolve break."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): on an ensemble whose every "
            "present member is supported `validate` yields `ok`, but this impl "
            "yields `error`. Refuted at input `[⟨7, true, true⟩]` — one present "
            "SUPPORTED member (`supports = true`), where gold succeeds and the "
            "rival fails. The mirror of weak-never-raise on the success/failure "
            "axis, and the only witness moving `supports` to `true`. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("[⟨7, true, true⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-mask on the failure leg: fail on the right member but report a
        # constant/wrong identity instead of the offending member's own name.
        "module": _expr(
            "members.foldr (fun m acc => "
            "if (m.present && !m.supports) then Except.error 0 else acc) (Except.ok ())"),
        "refinement": (
            "gets the success/failure decision right but reports the WRONG identity "
            "on the failure leg (a constant, not the offending member's own "
            "identity). Its faithful real counterpart raises with an incorrect "
            "estimator label; the guard test test_sample_weight matches the raised "
            "message against the specific offending estimator's name "
            "(assert_raise_message / pytest.raises(match=...)), which a wrong label "
            "fails, so it would NOT resolve. Correct on the outcome, wrong on the "
            "reported identity — a genuine value break on the failure-leg payload."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): the failure leg is "
            "`Except.error m.name` carrying the offending member's identity, so a "
            "rival reporting a constant `0` diverges whenever the offending member's "
            "name is not `0`. Refuted at input `[⟨5, true, false⟩]` — a present "
            "unsupported member named `5`, where gold yields `error 5` and the "
            "rival yields `error 0`. The only witness that moves the `name` binder "
            "off `0` and probes the reported identity. If it verified => "
            "SPEC-TOO-WEAK (identity unconstrained)."
        ),
        "witness": _witness("[⟨5, true, false⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain / off-by-one: validate every member EXCEPT the last one
        # (`validate members.dropLast`). Correct on every ensemble whose sole
        # offender is not the last member; wrong when the last member is the only
        # offending one.
        "module": _expr("validate members.dropLast"),
        "refinement": (
            "partial-domain / off-by-one: its faithful real counterpart stops the "
            "scan one member short (never checks the LAST member). It is correct "
            "unless the only offending member is the last one, in which case the "
            "unsupported configuration is accepted and the fit later crashes. The "
            "guard test test_sample_weight places the sole weight-rejecting member "
            "LAST in the ensemble and asserts validation raises with its identity; "
            "a scan that skips the last member accepts it, so the raise never "
            "happens and it would NOT resolve. A verify-not-resolve break on the "
            "last-element sub-domain."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): C1 pins the outcome over "
            "the WHOLE list including the last member, so a rival that drops the "
            "last member diverges when the last member is the sole offender. "
            "Refuted at input `[⟨2, true, true⟩, ⟨9, true, false⟩]` — a supported "
            "member followed by the sole offending member LAST, where gold yields "
            "`error 9` and the rival (validating only `[⟨2,true,true⟩]`) yields "
            "`ok`. A DISTINCT point from the single-element rivals (a two-element "
            "list, offender last), varying the `members` length binder. Ports the "
            "nagini weak-skip-first partial-domain rival, re-aimed to the last "
            "member (this backend's failing guard test orders the offender last). "
            "If it verified => SPEC-TOO-WEAK (domain-incomplete)."
        ),
        "witness": _witness("[⟨2, true, true⟩, ⟨9, true, false⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-launder-input",
        "kind": "uniqueness",
        "expect": "reject",
        # The FRAME-MUTATION class, ported by strategy rather than by mechanism.
        # The nagini rival overwrites the read-only roster so the post-image holds
        # on the doctored list; there is no writable input here, so this rival
        # rebinds a DOCTORED COPY inside the impl region (every member forced to
        # accept a weighting) and validates that instead of `members`. In scope —
        # the rebind is wholly inside -- impl-start .. -- impl-end. Rejected
        # because C1 quantifies over the ORIGINAL `members`: this impl returns
        # `ok` on every ensemble whatsoever, so it is refutable at any present
        # unsupported member.
        "module": _expr(
            "validate (members.map (fun mm => { mm with supports := true }))"),
        "refinement": (
            "its faithful real counterpart doctors the ensemble it validates "
            "instead of the one it was given — rewriting each weight-rejecting "
            "member into a weight-accepting stand-in so the configuration appears "
            "to accept a per-sample weighting. The validation then never rejects "
            "anything, so the guard test test_sample_weight (which asserts "
            "validation raises, naming the offending member) FAILS; and because "
            "the doctored members are what the surrounding fit would go on to "
            "train, the P2P tests asserting the configured members are fit "
            "unchanged (test_estimator_init, test_set_estimator_none, the "
            "predict/transform tests) fail too. A verify-not-resolve break."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): C1 is stated about the "
            "ORIGINAL input, so satisfying it on a doctored copy is not satisfying "
            "it. Forcing `supports := true` on every member makes the rival's "
            "outcome constantly `ok`, which diverges from `validate members` at "
            "every ensemble containing a present unsupported member. Refuted at "
            "`[⟨9, true, false⟩]`. This is the nagini weak-frame-mutation class "
            "ported by STRATEGY (launder the input) rather than by mechanism (a "
            "permission violation), the permission half having no counterpart on a "
            "referentially transparent carrier. If it verified => SPEC-TOO-WEAK "
            "(the post-image would not be pinned to the actual argument)."
        ),
        "witness": _witness("[⟨9, true, false⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-last-offender-reported",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDERING, attacked on its own. Every other rival that fails on the right
        # ensembles also reports the right identity, so C1's "FIRST offending
        # member" clause was only ever probed indirectly. This rival scans
        # FORWARD (`foldl`), keeping the LAST failure it sees instead of the first:
        # it agrees with gold on the success/failure decision at every input, and
        # diverges ONLY on which of several offenders is reported. That isolates
        # the front-most clause as the sole thing being tested.
        "module": _expr(
            "members.foldl (fun acc m => "
            "if (m.present && !m.supports) then Except.error m.name else acc) "
            "(Except.ok ())"),
        "refinement": (
            "its faithful real counterpart does not stop at the first offending "
            "member: it scans on and reports the LAST one instead. Validation "
            "still rejects exactly the configurations it should, so this is not a "
            "control-flow break — it is a wrong-identity break confined to "
            "ensembles with two or more offending members. The guard test "
            "test_sample_weight matches the raised message against the specific "
            "offending member's label, and the label of the last offender is not "
            "the label of the first, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): `validate` is "
            "front-recursive and returns at the FIRST present unsupported member, "
            "so on an ensemble with two offenders C1 pins the FIRST one's identity. "
            "Refuted at input `[⟨1, true, false⟩, ⟨2, true, false⟩]` — two present "
            "unsupported members, where gold yields `error 1` and this rival yields "
            "`error 2`. The ONLY case that isolates the first-offender ORDERING "
            "clause: it agrees with gold on the success/failure leg everywhere, so "
            "nothing but the ordering can be what rejects it. Also the only witness "
            "with two OFFENDING members. If it verified => SPEC-TOO-WEAK (the "
            "ordering clause would be unconstrained, and the manifest's claim to "
            "attack the front-most facet would be unearned)."
        ),
        "witness": _witness("[⟨1, true, false⟩, ⟨2, true, false⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # The nagini partial-domain rival at its ORIGINAL aim, restored. The port
        # re-aimed weak-skip-first to the LAST member and dropped the front-side
        # sub-domain, but the two are different sub-domains on this carrier: an
        # off-by-one at the FRONT is wrong iff the FIRST member is the sole
        # offender, which `validate members.dropLast` gets right. Cheap to carry
        # and it restores the sub-domain the sibling actually demonstrated.
        "module": _expr("validate members.tail"),
        "refinement": (
            "partial-domain / off-by-one at the FRONT: its faithful real "
            "counterpart begins the scan one member late, never inspecting the "
            "first member of the ensemble. Correct unless the first member is the "
            "sole offender, in which case an unsupported configuration is accepted "
            "and the weighted fit later breaks. A guard test whose "
            "weight-rejecting member is first in the ensemble does NOT resolve. "
            "The mirror sub-domain of weak-skip-last, and disjoint from it: each "
            "rival is CORRECT on the input the other is refuted at."
        ),
        "rationale": (
            "REJECT from C1 (`out = validate members`): C1 pins the outcome over "
            "the WHOLE list including the first member. Refuted at input "
            "`[⟨3, true, false⟩, ⟨4, true, true⟩]` — the sole offender FIRST, "
            "followed by a supported member, where gold yields `error 3` and the "
            "rival (validating only `[⟨4,true,true⟩]`) yields `ok`. Restores the "
            "nagini weak-skip-first rival at its original aim; the port had "
            "re-aimed it to the last member, but front and back are distinct "
            "sub-domains here — weak-skip-last is CORRECT at this input and this "
            "rival is CORRECT at weak-skip-last's. Also the only witness placing "
            "an offending member FIRST in a multi-element list. If it verified => "
            "SPEC-TOO-WEAK (domain-incomplete at the front)."
        ),
        "witness": _witness("[⟨3, true, false⟩, ⟨4, true, true⟩]"),
        "witness_reference": _REF_LOOPFREE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling has 9 SPEC cases (2 soundness, 1 admissibility, 6 uniqueness)
# over `check_weighting_support(roster: List[int])`, a status-tag fold with a
# fractional-permission (`Acc(.,1/2)`) read-only frame and a consumed
# `accepts_weighting` axiom. This bundle models the SAME validation scan as ONE
# method `validateWeightSupport (members : List Member)` whose input is the
# faithful `List Member` carrier of the roster (status 0 ↦ `present=false`,
# status 1 ↦ `present=true,supports=true`, status 2 ↦ `present=true,supports=false`
# — mapping.md §2). There is no axiom (the acceptance fact is the input field
# `Member.supports`, a type refinement — mapping.md §3) and no heap permission.
#
#   nagini case                       -> here
#   -----------------------------------------------------------------------
#   pos-nest-branch                   -> pos-control-local-flag        RE-SHAPED
#                                        + pos-control-nested-guard     RE-SHAPED/ADDED
#   pos-explicit-status               -> pos-control-direct            RE-EXPRESSED
#   admiss-precond-nonvacuous         -> admiss-validate-nondegenerate RE-AIMED
#   weak-frame-mutation               -> weak-launder-input            PORTED (by
#                                          strategy; permission half vacuous)
#   weak-prepatch-probe-on-absent     -> weak-prepatch-probe-on-absent PORTED
#   weak-never-raise                  -> weak-never-raise              PORTED
#   weak-always-raise                 -> weak-always-raise             PORTED
#   weak-skip-first                   -> weak-skip-first               PORTED (intact)
#                                        + weak-skip-last               ADDED (mirror)
#   weak-treat2-as-accept             -> weak-never-raise (merged)     see below
#   (no sibling)                      -> weak-wrong-identity           ADDED
#   (no sibling)                      -> weak-last-offender-reported   ADDED
#   AXIOM_TESTS (2)                   -> (none)                        DROPPED (G-AX lane)
#
# 12 velvet SPEC cases: 3 soundness, 1 admissibility, 8 uniqueness. Every nagini
# uniqueness rival that attacks a modeled facet of C1 is ported or merged; three
# rivals are added — weak-wrong-identity and weak-last-offender-reported attack the
# reported-identity payload and the FIRST-offender ordering of C1's failure leg
# (the nagini status-fold abstraction carries no reported identity, so it had no
# counterpart for either), and weak-skip-last mirrors weak-skip-first on the
# back-side sub-domain.
#
# RE-SHAPED (pos-nest-branch -> pos-control-local-flag + pos-control-nested-guard):
#   the nagini positive nests the absent-guard instead of the gold `elif`. On this
#   carrier the gold guard is a single fused `m.present && !m.supports` test, so
#   there are two honest reshapes of it: bind the test to a typed local (local-flag,
#   proof unchanged) and split it into the nested present-then-supported form that
#   MIRRORS the gold repo hunk's `if step is None: continue` then acceptance test
#   (nested-guard, proof retuned with `grind`). Both keep the backward fold and all
#   invariants; both must verify or C1 is SPEC-TOO-STRONG.
# RE-EXPRESSED (pos-explicit-status -> pos-control-direct): the nagini case decides
#   support by the status tag directly (not via the probe), showing the value
#   abstraction does not require consuming the axiom. On this carrier there is no
#   axiom at all and the post-image is the transparent `validate members`, so the
#   honest cheapest impl is `return validate members` — the same argument (the
#   grounded pin is satisfiable only by the real scan; no wrong echo verifies)
#   expressed as a loop-free correct impl.
# RE-AIMED (admiss-precond-nonvacuous -> admiss-validate-nondegenerate): the nagini
#   case established the read-only fractional-permission precondition on an
#   F2P-shaped roster. This method has no `require` and no heap permission, so that
#   probe is vacuous; re-aimed at the residual total-domain risk (post-image
#   degeneracy), witnessed by an in-region assert that `validate` distinguishes the
#   three F2P-shaped behaviours (absent-only succeeds, present-unsupported fails
#   with identity, absent-then-supported succeeds).
# PORTED (3 intact): weak-prepatch-probe-on-absent (the pre-image bug — consult the
#   acceptance fact on an absent member), weak-never-raise (always succeed), and
#   weak-always-raise (always fail) carry across with only the carrier changing
#   from a status-tag fold to a `List Member` fold, each now backed by a
#   machine-checked witness.
# PORTED (intact) + MIRRORED: weak-skip-first, and weak-skip-last alongside it. The
#   nagini rival stops the scan one short at the FRONT (`while i > 1`), wrong iff
#   `roster[0] == 2`; that is carried here intact as `validate members.tail`, wrong
#   iff the first member is the sole offender. weak-skip-last
#   (`validate members.dropLast`) is the back-side MIRROR, wrong iff the last member
#   is the sole offender, and is kept because this backend's failing guard test
#   orders the sole offending member LAST. The two are genuinely distinct
#   sub-domains, not two spellings of one: each rival is CORRECT at the input the
#   other is refuted at (`members.tail` returns `error 9` on
#   `[⟨2,true,true⟩,⟨9,true,false⟩]`, and `members.dropLast` returns `error 3` on
#   `[⟨3,true,false⟩,⟨4,true,true⟩]`), so neither witness would refute the other's
#   rival.
# MERGED (weak-treat2-as-accept -> weak-never-raise): the nagini value-mask rival
#   treats a present-rejecting entry as accepting. On a single present unsupported
#   member that IS weak-never-raise's exact refutation point (`[⟨9,true,false⟩]`):
#   both rivals succeed where gold fails, for the same reason (a present unsupported
#   member is not marked as a failure). They are the same failure at the same input,
#   so per the two-rivals-one-witness rule they are one case here, not two. The
#   distinct partial-domain flavour the nagini file split out (correct-on-a-subdomain)
#   is instead covered by weak-skip-last, a genuine partial-domain rival with its own
#   distinct witness.
# ADDED (weak-wrong-identity): attacks the reported-IDENTITY payload of C1's failure
#   leg (`Except.error m.name`) — right on the outcome, wrong on which member is
#   reported. The nagini status-fold value abstraction carries no reported identity,
#   so it had no counterpart; here the guard test matches the raised message against
#   the offending estimator's specific name, so a wrong label does NOT resolve. The
#   only rival moving the `name` binder off 0. A real divergence with a checked
#   witness, not fabricated wrongness.
# ADDED (weak-last-offender-reported): isolates C1's FIRST-offender ORDERING clause,
#   which nothing else here tests on its own. Every other rival that fails on the
#   right ensembles also reports the right identity, so before this case the
#   front-most facet was only ever probed indirectly — the manifest claimed it and
#   the battery did not demonstrate it. A forward `foldl` keeping the LAST failure
#   agrees with gold on the success/failure leg at EVERY input and diverges only on
#   which of several offenders is named, so its rejection is attributable to the
#   ordering clause and to nothing else. Refuted at
#   `[⟨1,true,false⟩,⟨2,true,false⟩]` — the only witness with two OFFENDING members.
# PORTED by STRATEGY (weak-frame-mutation -> weak-launder-input). The nagini rival's
#   MECHANISM does not port: it writes through a 1/2-permission reference and is
#   rejected for INSUFFICIENT PERMISSION, and Velvet has no heap, aliasing, or
#   permission system. Nor can a variant make the input writable — that needs a
#   `mut` binder in the method HEADER, which lives in the spec view, so such a
#   variant fails `same_spec` and is OUT OF SCOPE rather than rejected (checked:
#   markers.same_spec is False for it, variant_problems reports "spec view
#   differs"). But the rival's STRATEGY does port: satisfy the post-image on a
#   doctored copy of the input rather than on the input. A local rebind inside the
#   impl region expresses exactly that and IS in scope, so the class is carried as
#   weak-launder-input rather than recorded vacuous. It is rejected because C1
#   quantifies over the ORIGINAL `members`.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
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
# DROPPED (AXIOM_TESTS): the nagini file's two axiom-soundness/containment probes
#   over the real `has_fit_parameter` callee are G-AX's job (axiom_check.py /
#   mapping.md §3.1); the G-PBT gate ignores AXIOM_TESTS regardless. This bundle
#   consumes no `axiom` (meta.json axioms == []), so there is no consumed-axiom lane
#   for this spec-lane manifest.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole impl-constraining clause is C1
#   (`out = validate members`), attacked on every modeled facet, each by a rival
#   whose witness input is the facet's own discriminating point:
#     skip-absent          weak-prepatch-probe-on-absent  [⟨0,false,false⟩]
#     failure leg          weak-never-raise               [⟨9,true,false⟩]
#     success leg          weak-always-raise              [⟨7,true,true⟩]
#     reported identity    weak-wrong-identity            [⟨5,true,false⟩]
#     FIRST-offender order weak-last-offender-reported    [⟨1,t,f⟩,⟨2,t,f⟩]
#     front sub-domain     weak-skip-first                [⟨3,t,f⟩,⟨4,t,t⟩]
#     back sub-domain      weak-skip-last                 [⟨2,t,t⟩,⟨9,t,f⟩]
#     pinned to the ARG    weak-launder-input             [⟨9,true,false⟩]
#   The ordering row is what makes the front-most claim EARNED rather than asserted:
#   weak-last-offender-reported agrees with gold on the success/failure leg at every
#   input, so only the ordering clause can reject it. Binder variation is meaningful,
#   not two spellings of one point: `present` ∈ {false, true}; `supports` ∈
#   {false, true}; `name` takes 0, 1, 2, 3, 4, 5, 7, 9; list length ∈ {1, 2}; and the
#   number of OFFENDING members ∈ {0, 1, 2} — that last axis exists only because of
#   the ordering rival, and it is the axis the identity clause needs. Seven distinct
#   input points across the eight rivals (weak-launder-input shares
#   weak-never-raise's point, being refutable anywhere an offender is present, and is
#   kept for the class it ports rather than for a new point). The three positives and
#   the admissibility case defend C1 on gold-shaped computations.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD — `prove_postcondition_
#   decidable_for` leaves an undischarged `Decidable (out = validate members)` and
#   the derived tester never becomes a function (re-measured: the tester file fails
#   identically for a wrong rival and for gold, discriminating nothing). Every
#   witness instead extracts the executable program and refutes C1 directly against
#   the TRANSPARENT `validate`, projecting `Except Int Unit` through
#   `proj : … → Option Int` (ok ↦ none, error n ↦ some n) since `Except Int Unit`
#   derives no DecidableEq; `proj` preserves both the outcome leg and the reported
#   identity, so the `≠` is exactly a C1 violation and is decidable.
#
#   The second half is refuted against the declared `witness_reference`
#   (`_REF_LOOPFREE`), NOT against gold. Gold's `while`-loop `…Exec` is well-founded
#   recursion the kernel does not reduce, so a witness built against the frozen
#   solution fails by STUCK REDUCTION (`instDecidableNot did not reduce to isTrue or
#   isFalse`) — the same error a TRUE claim about gold produces, which discriminates
#   nothing and which the gate classifies as `witness-undecided`. The reference is a
#   loop-free impl the gate independently re-checks (shares the frozen spec, and
#   VERIFIES), so a genuine refutation must fail there, and does so by a REAL
#   verdict. All eight rebuilt with scripts/lean_verify.sh: rival exit 0; reference
#   exit 1 with `Tactic 'decide' proved that the proposition ... is false`. Each
#   rival's `validateWeightSupportExec <input>` was separately confirmed to reduce to
#   a `DivM.res`, so the witness reads the computed result and not the `Except.ok ()`
#   fallback arm of its `match`. No witness binds a hypothesis, so no consistency
#   probe is needed.
AXIOM_TESTS = []
