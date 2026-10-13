"""properties.py — G-PBT falsification battery for django__django-11149 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must elaborate against the rival and FAIL against
the frozen solution).

================================  DEFENDED SURFACE  ==========================

FIVE contracted methods over the SAME free carrier: ``autoCreated : Bool`` (is
this an implicitly-created link relation?), ``userHasPerm : Perm → Bool`` (does
the principal hold a given permission on the related model?), and
``superResult : Bool`` (the inherited decision used for any other relation). The
two interrogated permissions are ``Perm.view`` and ``Perm.change``.

  addRelationAllowed    (autoCreated userHasPerm superResult)
  changeRelationAllowed (autoCreated userHasPerm superResult)
  deleteRelationAllowed (autoCreated userHasPerm superResult)
       ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change]
                                         else superResult)
  viewRelationAllowed   (autoCreated userHasPerm superResult)
       ensures result = (if autoCreated then anyPerm userHasPerm [Perm.view,
                                                    Perm.change] else superResult)
  holdsAnyTargetPerm    (userHasPerm perms)
       ensures result = anyPerm userHasPerm perms

``anyPerm`` is the total, fully-unfolded disjunction of ``userHasPerm`` over the
requested permission list (empty list ⇒ ``false``). It is a concrete ``def`` in
the ``pure`` region; the ``axioms`` region declares nothing. There is no opaque
answer key — evaluating ``anyPerm`` IS the correct answer.

Load-bearing clauses:
  * The THREE editing decisions (add / change / delete) pin the auto-created
    branch to ``anyPerm userHasPerm [Perm.change]`` — the FIX. A principal that
    holds only ``Perm.view`` on the related model must NOT be granted authority
    to add / change / delete a row of an implicitly-created link relation. A
    rival that probes ``[Perm.view, Perm.change]`` on any of the three is the
    pre-image regression: correct when the principal holds ``Perm.change``,
    WRONG on the view-only sub-domain (it returns ``true``, the spec demands
    ``false``). This is precisely the behaviour the two FAIL_TO_PASS tests
    assert (a view-only principal must be DENIED add / change on the link
    relation).
  * The VIEW decision pins the auto-created branch to ``anyPerm userHasPerm
    [Perm.view, Perm.change]`` — holding ``Perm.change`` also grants view. A
    rival that drops ``Perm.view`` denies view to a principal that holds only
    ``Perm.view``; a rival that drops ``Perm.change`` denies view to a
    change-only principal, contradicting "change implies view".
  * All four gates pin the non-auto branch to ``superResult`` — the inherited
    decision passes through untouched for any other relation. A rival that
    returns a constant there discards the inherited authority.
  * ``holdsAnyTargetPerm`` pins the shared probe to ``anyPerm`` over the WHOLE
    requested list. A rival that consults only the first requested permission,
    or always denies, drops the disjunction the four gates rely on.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value, this bundle declares NO ``mut`` binder on any input,
    there is no heap and no aliasing — so there is no read-only input to mutate
    and no substitute probe to build. Reported vacuous, not fabricated (footer).
    The sibling's "held is read-only" obligation is here structurally guaranteed
    by the ABSENCE of ``mut``, which the frozen spec already encodes.
  * UNGROUNDED-ORACLE ECHO — N/A. Every post-image is a total, fully unfolded
    function of the method's own inputs (``anyPerm`` is a concrete ``def``,
    ``if … then … else`` is transparent). There is no opaque answer key to echo,
    so there is no wrong-echo reject to build. Honest cheapest-reshape positive
    controls stand in.
  * CONTROL-FLOW-EFFECT — N/A. The decisions are pure total booleans; no
    exception, no side effect, no early-return path distinguishable from the
    returned value.
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
  * PARTIAL-DOMAIN / VALUE — the heart of this port. Rivals right on part of the
    input domain but diverging on a sub-domain: the view-rule regression on each
    editing gate, the dropped disjunct on the view gate, the discarded inherited
    decision on each gate's non-auto branch, and the first-only / always-deny
    corruptions of the shared probe. Each is refuted at a concrete input.

WITNESS MECHANICS on this carrier. The spec is a ``method`` CONTRACT, not a bare
predicate, so a witness reaches it through Velvet's own tester machinery:
``<gate>Tester <args> = false`` says the extracted program's result violates the
method's postcondition at that concrete input, checked in a file whose
``prove_correct`` blocks have been stripped (no tactic script can mask the
verdict). Each reject rival is written LOOP-FREE (it returns a closed form
directly), so ITS tester reduces and ``decide`` settles it. The free class
``userHasPerm`` is instantiated at a concrete decidable lambda
(``fun p => p == Perm.view`` / ``… == Perm.change``), so the tester reduces to a
ground boolean. No ``sorry`` / ``admit`` / ``native_decide`` / ``axiom``.

HOW THE GOLD-SIDE HALF ACTUALLY FAILS — measured, and it is NOT uniform. The
two-build check reads "the witness failed against the frozen solution" as "the
frozen solution satisfies the spec here". That inference is only as good as the
REASON for the failure, and this bundle splits into two classes:

  * SEMANTIC (4 cases: the four ``*-drop-inherited`` rivals). These are stated at
    ``autoCreated=false``, where the frozen impl takes the loop-free
    ``pure superResult`` branch. Its tester REDUCES, and the frozen build fails
    with ``decide proved that the proposition ... is false`` — a real refutation
    of the concrete claim. Full-strength discrimination.
  * STUCK REDUCTION (6 cases: the four auto-created-branch gate rivals and the
    two shared-probe rivals). These are stated at a point where the frozen impl
    runs the ``while`` loop of ``holdsAnyTargetPerm``. That loop elaborates
    through ``forIn`` / ``NonDetT.run``, which the kernel does not reduce, so the
    frozen build fails with ``reduction got stuck at the Decidable instance`` —
    an UNFOLDING failure, not a semantic refutation. Measured (audit): a claim
    that is TRUE of the frozen solution at the same point (``… = true``) fails
    IDENTICALLY, and none of ``decide`` / ``rfl`` / ``simp`` / ``decide +kernel``
    / ``unfold`` / ``loom_solve`` reduces the frozen tester — not even at
    ``perms = []``, where the loop runs zero iterations. So for these six the
    gold-side build distinguishes LOOP from LOOP-FREE, not wrong from right, and
    on its own it attributes nothing to the spec.

    What rescues them is not the gold build but an out-of-band control the gate
    cannot run: each of the six witnesses was rebuilt against a CORRECT loop-free
    impl of the same obligation, and each then failed with ``decide proved that
    the proposition ... is false``. A tautology would have passed there. So the
    rivals are genuinely wrong and the witnesses state genuinely false claims
    about them; the residual gap is one of ATTRIBUTION STRENGTH on the gate's
    gold leg, and it is structural — every witness that routes through a frozen
    tester whose impl loops fails on gold for this reason, so it cannot be closed
    from inside this file. Recorded here rather than papered over.

    Partial mitigation applied: each of the six witnesses carries a second
    conjunct stating the GROUND value the spec demands at the same input
    (``anyPerm`` at that principal and list). That conjunct reduces on both
    sides, so the witness now machine-checks the concrete arithmetic its
    ``rationale`` asserts instead of only asserting it in prose.

WITNESS PLACEMENT. Each of the FIVE obligations is attacked by two rivals at two
distinct input points, so all of its input binders are varied rather than
pinned. For the four gates the pair is (auto-created branch attacked at
``autoCreated=true`` with a view-only principal and inherited decision held
low) and (non-auto branch attacked at ``autoCreated=false`` with a change-only
principal and inherited decision held high) — jointly moving ``autoCreated``
over T/F, ``userHasPerm`` over the view-only / change-only classes, and
``superResult`` over false / true. For the shared probe the pair moves
``userHasPerm`` over the two classes and ``perms`` over ``[Perm.view,
Perm.change]`` / ``[Perm.view]``.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; every callee is
an unchanged free input). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11149"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside an impl region (between -- impl-start and
# -- impl-end) or inside a prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and every prove_correct statement
# byte-identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# A gate method's header down to its `-- impl-start` line (unique per gate,
# because the method name distinguishes it). Used to re-anchor a reshaped body.
def _gate_hdr(name, spec):
    return (
        f"method {name} (autoCreated : Bool) (userHasPerm : Perm → Bool) "
        f"(superResult : Bool) return (result : Bool)\n"
        f"  ensures result = (if autoCreated then anyPerm userHasPerm {spec} "
        f"else superResult)\n"
        "  do\n"
        "    -- impl-start\n")


# The frozen gate body: delegate to the looping shared probe (or pass the
# inherited decision through). Parameterised by the requested-permission list.
def _gate_body(spec):
    return (
        "    let r ← if autoCreated then\n"
        f"        holdsAnyTargetPerm userHasPerm {spec}\n"
        "      else\n"
        "        pure superResult\n"
        "    return r\n"
        "    -- impl-end")


_CHANGE = "[Perm.change]"
_VIEWCHANGE = "[Perm.view, Perm.change]"

_ADD_FULL = _gate_hdr("addRelationAllowed", _CHANGE) + _gate_body(_CHANGE)
_CHG_FULL = _gate_hdr("changeRelationAllowed", _CHANGE) + _gate_body(_CHANGE)
_DEL_FULL = _gate_hdr("deleteRelationAllowed", _CHANGE) + _gate_body(_CHANGE)
_VIEW_FULL = (_gate_hdr("viewRelationAllowed", _VIEWCHANGE)
              + _gate_body(_VIEWCHANGE))


def _reshape_gate(full, new_return):
    """Replace a gate's whole impl body with a single loop-free `return`."""
    hdr = full.split("    let r ←")[0]
    return _swap(_BASE, full, hdr + f"    return ({new_return})\n    -- impl-end")


# The whole executable body of the shared probe: the backward accumulating loop
# over the requested list. Reject rivals replace it with a loop-free closed form
# (so their tester reduces under `decide`); the loop-free positive does too.
_HAP_LOOP = (
    "    let mut acc : Bool := false\n"
    "    let mut i := perms.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ perms.length\n"
    "      invariant acc = anyPerm userHasPerm (perms.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := perms[i - 1]!\n"
    "      acc := userHasPerm p || acc\n"
    "      i := i - 1\n"
    "    return acc")

# The full frozen proof body of the shared probe (everything after the
# `prove_correct holdsAnyTargetPerm by` header). A loop-free reshape of the
# probe leaves none of the loop-invariant goals the frozen script closes, so it
# is retuned to a bare `loom_solve`. The tactic body is elided from the spec
# view, so this is a proof reshape, not a spec change.
_HAP_PROOF = (
    "prove_correct holdsAnyTargetPerm by\n"
    "  loom_solve\n"
    "  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]\n"
    "  simp_all")
_HAP_PROOF_BARE = "prove_correct holdsAnyTargetPerm by\n  loom_solve"


# ---- witness preamble. Reach a method contract through Velvet's tester
# ---- machinery: `<name>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input.
def _tester(name, body):
    return (f"extract_program_for {name}\n"
            f"prove_precondition_decidable_for {name}\n"
            f"prove_postcondition_decidable_for {name}\n"
            f"derive_tester_for {name}\n\n" + body)


_VIEW_ONLY = "(fun p => p == Perm.view)"     # holds only Perm.view
_CHANGE_ONLY = "(fun p => p == Perm.change)"  # holds only Perm.change


def _gate_wit(name, autoc, principal, superr, spec, ground):
    """A gate witness: the tester refutation AND the ground value the spec
    demands at that same input.

    The second conjunct is the point. The tester half fails on the frozen
    solution by STUCK REDUCTION whenever the refuted point drives the frozen
    impl through the shared probe's `while` loop (see the header), so on its own
    it does not machine-check the arithmetic the `rationale` claims. `anyPerm` at
    a concrete principal and list is a plain `def` over an inductive, so it
    reduces on BOTH sides — appending it means `decide` has to confirm the
    concrete permission algebra the case is arguing from, rather than the prose
    asserting it unchecked. Kept in one conjunction so a single `decide` settles
    both and the witness still binds nothing (no consistency probe needed).
    """
    return _tester(
        name,
        f"example : {name}Tester {autoc} {principal} {superr} = false\n"
        f"    ∧ anyPerm {principal} {spec} = {ground} := by\n  decide\n")


def _hap_wit(principal, perms, ground):
    """The shared probe's analogue of `_gate_wit`."""
    return _tester(
        "holdsAnyTargetPerm",
        f"example : holdsAnyTargetPermTester {principal} {perms} = false\n"
        f"    ∧ anyPerm {principal} {perms} = {ground} := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify; else the spec is SPEC-TOO-STRONG on the impl shape.
    # =====================================================================
    {
        "id": "pos-hap-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names. A maximally different control-flow shape (no loop, no
        # accumulator); the loop-specific proof is retuned to a bare loom_solve.
        "module": _swap(
            _swap(_BASE, _HAP_LOOP, "    return anyPerm userHasPerm perms"),
            _HAP_PROOF, _HAP_PROOF_BARE),
        "rationale": "a loop-free shared probe that returns `anyPerm userHasPerm "
                     "perms` directly satisfies its `ensures` definitionally; a "
                     "correct reshape of the modeled behaviour verifying is "
                     "exactly what SPEC-TOO-STRONG would deny. Exercises "
                     "holdsAnyTargetPerm from a loop-free shape; the four gates "
                     "delegate to it unchanged and still verify.",
    },
    {
        "id": "pos-add-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the add gate returns the modeled decision inline (matching the
        # post-image) instead of delegating through the shared probe. Same value
        # on every input; the frozen loom_solve still discharges it.
        "module": _reshape_gate(
            _ADD_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.change] "
            "else superResult"),
        "rationale": "returning the modeled decision inline (the `if autoCreated "
                     "then anyPerm userHasPerm [Perm.change] else superResult` "
                     "the post-image names) is a correct reshape of "
                     "addRelationAllowed that must verify; a faithful correct "
                     "impl that could not would be SPEC-TOO-STRONG on the "
                     "delegation shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the "a normal
    # input satisfies the precondition" probe is vacuous. Re-aimed at the
    # residual risk on a total domain: that the post-image is DEGENERATE at the
    # interesting point. This case discharges an in-region `assert` (inside the
    # add gate's impl region, elided from the spec view) pinning the three
    # discriminating facts at concrete inputs: a view-only principal is DENIED
    # the change probe, a change-only principal is GRANTED it, and a view-only
    # principal is GRANTED the view-or-change probe. The impl is kept verbatim so
    # the method's own obligation still discharges; the assert is LIVE, and that
    # was re-measured during the audit rather than taken on trust: the mirror
    # variant whose assert claims the view-only principal IS granted the change
    # probe (`anyPerm (fun p => p == Perm.view) [Perm.change] = true`) fails to
    # elaborate, leaving exactly `unsolved goals / case «assert_1»` on that
    # conjunct. So the assert is discharged by the permission algebra, not
    # skipped.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _ADD_FULL,
            _ADD_FULL.split("    let r ←")[0]
            + "    assert (with_name_prefix `assert\n"
            "      (anyPerm (fun p => p == Perm.view) [Perm.change] = false ∧\n"
            "       anyPerm (fun p => p == Perm.change) [Perm.change] = true ∧\n"
            "       anyPerm (fun p => p == Perm.view) [Perm.view, Perm.change] "
            "= true))\n"
            + _gate_body(_CHANGE)),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: the change probe DENIES a principal "
                     "holding only Perm.view and GRANTS one holding Perm.change, "
                     "and the view-or-change probe GRANTS a principal holding "
                     "only Perm.view. The in-region assert must discharge (else "
                     "the obligation is degenerate / PRECOND-TOO-STRONG); the "
                     "impl is kept verbatim so addRelationAllowed's own ensures "
                     "still verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each loop-free (so its tester kernel-reduces) with a
    # machine-checked refutation witness at a concrete input and the refinement
    # argument that its faithful real counterpart would NOT resolve the failing
    # tests. Each of the five obligations gets two rivals at two distinct points.
    # =====================================================================

    # ---- ADD gate ------------------------------------------------------------
    {
        "id": "weak-add-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image regression on the ADD decision: probe [view, change]
        # instead of [change]. Correct when the principal holds Perm.change;
        # WRONG on the view-only sub-domain.
        "module": _reshape_gate(
            _ADD_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] "
            "else superResult"),
        "refinement": "probing the view-or-change permission for the ADD "
                      "decision is the pre-image behaviour: a principal holding "
                      "only the view permission on the related model is still "
                      "granted authority to add a row of the implicitly-created "
                      "link relation. The failing test that constructs exactly "
                      "such a view-only principal and asserts add authority is "
                      "DENIED still observes it granted. It would NOT resolve.",
        "rationale": "REJECT from addRelationAllowed's ensures `result = (if "
                     "autoCreated then anyPerm userHasPerm [Perm.change] else "
                     "superResult)`: at autoCreated=true with a view-only "
                     "principal the spec demands `false` (Perm.change absent) but "
                     "the [view, change] probe yields `true`. Refuted at "
                     "(autoCreated=true, view-only, superResult=false) — the "
                     "auto-created / view-only sub-domain the fix targets.",
        "witness": _gate_wit("addRelationAllowed", "true", _VIEW_ONLY, "false",
                             _CHANGE, "false"),
    },
    {
        "id": "weak-add-drop-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        # Non-auto branch corruption: return a constant `false` where the spec
        # passes the inherited decision through. Correct on the auto-created
        # branch; diverges whenever autoCreated=false and superResult=true.
        "module": _reshape_gate(
            _ADD_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.change] else false"),
        "refinement": "discarding the inherited decision on the non-link "
                      "relation branch denies add authority even where the "
                      "ordinary inherited check grants it — a broad regression on "
                      "every relation that is not an implicitly-created link "
                      "relation. The suite's unrelated add-permission scenarios "
                      "then fail, so the harness would NOT report resolved.",
        "rationale": "REJECT from addRelationAllowed's ensures: on the non-auto "
                     "branch the spec demands `result = superResult`, but the "
                     "rival returns `false`. Refuted at (autoCreated=false, "
                     "change-only, superResult=true) — a distinct point that "
                     "moves the autoCreated and superResult binders off the "
                     "values the view-rule rival holds them at.",
        "witness": _tester(
            "addRelationAllowed",
            f"example : addRelationAllowedTester false {_CHANGE_ONLY} true "
            "= false := by\n  decide\n"),
    },

    # ---- CHANGE gate ---------------------------------------------------------
    {
        "id": "weak-change-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reshape_gate(
            _CHG_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] "
            "else superResult"),
        "refinement": "the same pre-image regression on the CHANGE decision: a "
                      "principal holding only the view permission is still "
                      "granted authority to change a row of the link relation. "
                      "The failing test that asserts change authority is DENIED "
                      "for such a view-only principal still observes it granted. "
                      "It would NOT resolve.",
        "rationale": "REJECT from changeRelationAllowed's ensures `result = (if "
                     "autoCreated then anyPerm userHasPerm [Perm.change] else "
                     "superResult)`: at autoCreated=true with a view-only "
                     "principal the spec demands `false` but the [view, change] "
                     "probe yields `true`. Refuted at (autoCreated=true, "
                     "view-only, superResult=false).",
        "witness": _gate_wit("changeRelationAllowed", "true", _VIEW_ONLY,
                             "false", _CHANGE, "false"),
    },
    {
        "id": "weak-change-drop-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reshape_gate(
            _CHG_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.change] else false"),
        "refinement": "discarding the inherited decision on the non-link branch "
                      "denies change authority even where the ordinary inherited "
                      "check grants it, regressing every non-link relation. The "
                      "suite's unrelated change-permission scenarios fail, so the "
                      "harness would NOT report resolved.",
        "rationale": "REJECT from changeRelationAllowed's ensures: on the "
                     "non-auto branch the spec demands `result = superResult`, "
                     "but the rival returns `false`. Refuted at "
                     "(autoCreated=false, change-only, superResult=true).",
        "witness": _tester(
            "changeRelationAllowed",
            f"example : changeRelationAllowedTester false {_CHANGE_ONLY} true "
            "= false := by\n  decide\n"),
    },

    # ---- DELETE gate ---------------------------------------------------------
    {
        "id": "weak-delete-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reshape_gate(
            _DEL_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] "
            "else superResult"),
        "refinement": "the same pre-image regression on the DELETE decision: a "
                      "view-only principal is granted authority to delete a row "
                      "of the link relation. A view-only principal must be DENIED "
                      "delete on the auto-created link relation (the editability "
                      "the issue forbids), so the faithful counterpart would NOT "
                      "resolve.",
        "rationale": "REJECT from deleteRelationAllowed's ensures `result = (if "
                     "autoCreated then anyPerm userHasPerm [Perm.change] else "
                     "superResult)`: at autoCreated=true with a view-only "
                     "principal the spec demands `false` but the [view, change] "
                     "probe yields `true`. Refuted at (autoCreated=true, "
                     "view-only, superResult=false).",
        "witness": _gate_wit("deleteRelationAllowed", "true", _VIEW_ONLY,
                             "false", _CHANGE, "false"),
    },
    {
        "id": "weak-delete-drop-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reshape_gate(
            _DEL_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.change] else false"),
        "refinement": "discarding the inherited decision on the non-link branch "
                      "denies delete authority even where the ordinary inherited "
                      "check grants it, regressing every non-link relation. The "
                      "suite's unrelated delete-permission scenarios fail, so the "
                      "harness would NOT report resolved.",
        "rationale": "REJECT from deleteRelationAllowed's ensures: on the "
                     "non-auto branch the spec demands `result = superResult`, "
                     "but the rival returns `false`. Refuted at "
                     "(autoCreated=false, change-only, superResult=true).",
        "witness": _tester(
            "deleteRelationAllowed",
            f"example : deleteRelationAllowedTester false {_CHANGE_ONLY} true "
            "= false := by\n  decide\n"),
    },

    # ---- VIEW gate -----------------------------------------------------------
    {
        "id": "weak-view-drop-view-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop Perm.view from the view probe (probe [change] only). Denies view
        # to a principal that holds only Perm.view — the view gate must grant it.
        "module": _reshape_gate(
            _VIEW_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.change] "
            "else superResult"),
        "refinement": "probing only the change permission for the VIEW decision "
                      "denies view authority to a principal that holds only the "
                      "view permission on the related model. The failing test "
                      "that constructs such a view-only principal and asserts "
                      "view authority is GRANTED then observes it denied, so the "
                      "counterpart would NOT resolve.",
        "rationale": "REJECT from viewRelationAllowed's ensures `result = (if "
                     "autoCreated then anyPerm userHasPerm [Perm.view, "
                     "Perm.change] else superResult)`: at autoCreated=true with a "
                     "view-only principal the spec demands `true` (Perm.view "
                     "present) but the [change]-only probe yields `false`. "
                     "Refuted at (autoCreated=true, view-only, "
                     "superResult=false).",
        "witness": _gate_wit("viewRelationAllowed", "true", _VIEW_ONLY, "false",
                             _VIEWCHANGE, "true"),
    },
    {
        "id": "weak-view-drop-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reshape_gate(
            _VIEW_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] "
            "else false"),
        "refinement": "discarding the inherited decision on the non-link branch "
                      "denies view authority even where the ordinary inherited "
                      "check grants it, regressing every non-link relation. The "
                      "suite's unrelated view-permission scenarios fail, so the "
                      "harness would NOT report resolved.",
        "rationale": "REJECT from viewRelationAllowed's ensures: on the non-auto "
                     "branch the spec demands `result = superResult`, but the "
                     "rival returns `false`. Refuted at (autoCreated=false, "
                     "change-only, superResult=true) — moving the autoCreated and "
                     "superResult binders off the view-disjunct rival's values.",
        "witness": _tester(
            "viewRelationAllowed",
            f"example : viewRelationAllowedTester false {_CHANGE_ONLY} true "
            "= false := by\n  decide\n"),
    },

    # ---- shared probe holdsAnyTargetPerm -------------------------------------
    {
        "id": "weak-hap-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult only the FIRST requested permission; drop the disjunction over
        # the rest. Correct when the first element decides.
        "module": _swap(
            _swap(_BASE, _HAP_LOOP,
                  "    return (match perms with | [] => false "
                  "| p :: _ => userHasPerm p)"),
            _HAP_PROOF, _HAP_PROOF_BARE),
        "refinement": "a shared probe that checks only the first requested "
                      "permission denies a principal that holds a LATER requested "
                      "one — e.g. for the view decision (which requests view "
                      "then change) a change-only principal is denied view, "
                      "breaking 'change implies view'. The failing test asserting "
                      "view authority for a change-permitted principal then "
                      "observes it denied, so the counterpart would NOT resolve.",
        "rationale": "REJECT from holdsAnyTargetPerm's ensures `result = anyPerm "
                     "userHasPerm perms`: the disjunction over the WHOLE list is "
                     "not the first element alone. Refuted at "
                     "(userHasPerm = change-only, perms = [Perm.view, "
                     "Perm.change]) where the first element (view) is absent but "
                     "a later one (change) is held, so the spec demands `true` "
                     "and the rival yields `false`.",
        "witness": _hap_wit(_CHANGE_ONLY, _VIEWCHANGE, "true"),
    },
    {
        "id": "weak-hap-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Always deny. Correct only on the empty list; denies every held
        # permission otherwise.
        "module": _swap(
            _swap(_BASE, _HAP_LOOP, "    return false"),
            _HAP_PROOF, _HAP_PROOF_BARE),
        "refinement": "a shared probe that always denies makes every gate deny "
                      "add / change / delete / view on the link relation even for "
                      "a principal holding the change permission, so a "
                      "change-permitted principal is locked out entirely. The "
                      "failing test asserting authority IS granted for such a "
                      "principal then fails, so the counterpart would NOT "
                      "resolve.",
        "rationale": "REJECT from holdsAnyTargetPerm's ensures `result = anyPerm "
                     "userHasPerm perms`: the constant `false` disagrees with the "
                     "disjunction on any list containing a held permission. "
                     "Refuted at (userHasPerm = view-only, perms = [Perm.view]) "
                     "where the spec demands `true` — a distinct point and a "
                     "distinct class from the first-only rival, moving both "
                     "binders.",
        "witness": _hap_wit(_VIEW_ONLY, "[Perm.view]", "true"),
    },

    # ---- ADDED BY AUDIT ------------------------------------------------------
    # The view gate's CHANGE disjunct was the one load-bearing clause the header
    # named ("a rival that drops Perm.change denies view to a change-only
    # principal") that NO case demonstrated: the shipped view-gate rivals drop
    # Perm.view and corrupt the non-auto branch, leaving `change implies view`
    # asserted only in prose. This closes it, and makes the view gate the one
    # obligation attacked at three distinct principals.
    {
        "id": "weak-view-drop-change-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Probe [view] only on the view gate: correct for a principal holding
        # Perm.view, WRONG for one holding only Perm.change.
        "module": _reshape_gate(
            _VIEW_FULL,
            "if autoCreated then anyPerm userHasPerm [Perm.view] "
            "else superResult"),
        "refinement": "probing only the view permission for the VIEW decision "
                      "denies view authority to a principal that holds only the "
                      "change permission on the related model, contradicting "
                      "'holding change also grants view'. A principal permitted "
                      "to change the related model would be unable to see the "
                      "rows of the implicitly-created link relation it is "
                      "allowed to edit — the scenario asserting view authority "
                      "for a change-permitted principal then observes it denied, "
                      "so the faithful counterpart would NOT resolve.",
        "rationale": "REJECT from viewRelationAllowed's ensures `result = (if "
                     "autoCreated then anyPerm userHasPerm [Perm.view, "
                     "Perm.change] else superResult)`: at autoCreated=true with "
                     "a change-only principal the spec demands `true` "
                     "(Perm.change present in the requested list) but the "
                     "[view]-only probe yields `false`. Refuted at "
                     "(autoCreated=true, change-only, superResult=false) — a "
                     "THIRD point on this obligation, and the only case in the "
                     "battery that moves the view gate's change disjunct.",
        "witness": _gate_wit("viewRelationAllowed", "true", _CHANGE_ONLY,
                             "false", _VIEWCHANGE, "true"),
    },

    # A second soundness control on the shared probe, aimed at the gap the
    # existing positive leaves: `pos-hap-closed-form` returns `anyPerm ... perms`
    # itself, which discharges its `ensures` by `rfl` — it proves the spec admits
    # a loop-free shape, but not that it admits a DIFFERENT function that merely
    # AGREES. `List.any` is such a function: extensionally equal, not
    # definitionally, so closing it needs a real induction. A spec tied to the
    # syntactic form of `anyPerm` would reject this.
    {
        "id": "pos-hap-list-any",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _HAP_LOOP, "    return (perms.any userHasPerm)"),
            _HAP_PROOF,
            "prove_correct holdsAnyTargetPerm by\n"
            "  loom_solve\n"
            "  induction perms with\n"
            "  | nil => rfl\n"
            "  | cons p ps ih => simp [anyPerm, List.any_cons, ih]"),
        "rationale": "the library disjunction `perms.any userHasPerm` is a "
                     "faithful correct shared probe that is only "
                     "EXTENSIONALLY equal to `anyPerm userHasPerm perms` — the "
                     "two are not definitionally equal, so the obligation is "
                     "closed by an induction over the requested list rather "
                     "than by `rfl`. That it verifies shows the ensures pins the "
                     "disjunctive BEHAVIOUR and not the frozen helper's "
                     "syntactic form; a spec that admitted only terms "
                     "reducible to `anyPerm` would be SPEC-TOO-STRONG here, "
                     "which the existing closed-form positive cannot detect.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation, 4 uniqueness rivals)
# and no AXIOM_TESTS. The sibling contracts FIVE functions over a read-only
# permission-code set `held : PSet[int]`: `target_decision(held, required)` (the
# existential membership probe) and four inline decisions
# (inspect/create/modify/remove). This bundle contracts FIVE methods over the
# SAME abstract carrier, re-expressed for the Lean-family model: the shared probe
# `holdsAnyTargetPerm(userHasPerm, perms)` (the sibling's `target_decision`), the
# three editing gates add/change/delete (the sibling's create/modify/remove), and
# the view gate (the sibling's inspect decision), with the codename set abstracted
# to the free `userHasPerm : Perm → Bool` and the requested codes to a `List Perm`.
# Every value-surface case carries across; the permission surface does not exist
# here.
#
#   sibling case                     kind          -> here                          disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-flag-accumulator     soundness     -> pos-hap-closed-form           RE-EXPRESSED
#   pos-control-create-inline-...    soundness     -> pos-add-inline                PORTED
#   admiss-distinct-codes            admissibility -> admiss-grounded               RE-AIMED
#   frame-mut-write-perm             uniqueness    -> (none)                        VACUOUS
#   uniq-first-required-only         uniqueness    -> weak-hap-first-only           PORTED
#   uniq-create-view-rule            uniqueness    -> weak-add-view-rule            PORTED
#   uniq-modify-view-rule            uniqueness    -> weak-change-view-rule         PORTED
#   uniq-remove-view-rule            uniqueness    -> weak-delete-view-rule         PORTED
#
# RE-EXPRESSED (soundness, pos-control-flag-accumulator -> pos-hap-closed-form):
#   the sibling's structurally-different correct control is a found-flag
#   accumulator scanning the whole required list. Here the frozen shared probe is
#   ALREADY a backward accumulator loop, so the maximally-different correct
#   reshape is the loop-free closed form `return anyPerm userHasPerm perms` (the
#   post-image itself), with the loop-invariant proof retuned to a bare
#   loom_solve. Same ARGUMENT (a faithful correct impl of a different shape must
#   verify).
# PORTED (pos-control-create-inline-membership -> pos-add-inline): the sibling's
#   cheapest correct create decision returns the grounded membership test inline
#   rather than delegating; here the add gate returns the modeled `if autoCreated
#   then anyPerm userHasPerm [Perm.change] else superResult` inline rather than
#   delegating through the shared probe. Same ARGUMENT.
# RE-AIMED (admiss-distinct-codes -> admiss-grounded): the sibling asserts its
#   own precondition facts (distinct codes; the half-permission read grant) before
#   delegating. No method here has a `require` clause and there is no permission
#   surface, so that reading is vacuous. Re-aimed at the residual admissibility
#   risk on a total domain — a degenerate post-image — by discharging a live
#   in-region assert pinning the three F2P-discriminating facts (view-only denied
#   the change probe, change-only granted it, view-only granted the view probe).
# VACUOUS (frame-mut-write-perm): the sibling's MANDATORY frame rival demands FULL
#   write permission on the read-only `held`, rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent, has no heap and no
#   aliasing, and this bundle declares NO `mut` binder on any input — there is no
#   read-only input to overwrite and no substitute probe. Omitted as vacuous, NOT
#   fabricated. The sibling's read-only obligation is here structurally guaranteed
#   by the absence of `mut`, which the frozen spec already encodes.
# PORTED (uniq-first-required-only -> weak-hap-first-only): the "consult only the
#   first requested code" partial-domain rival ports directly to the shared probe,
#   refuted where a LATER requested permission is the only one held.
# PORTED (the three view-rule regressions): the sibling's create/modify/remove
#   view-rule rivals port one-for-one to weak-add/change/delete-view-rule, each
#   the pre-image [view, change] probe on that editing gate, refuted on the
#   auto-created / view-only sub-domain.
#
# ADDED (5, no sibling counterpart, all to satisfy per-obligation binder
#   coverage — the coverage tool measures binder variation PER obligation, so each
#   of the five obligations needs >=2 witnesses that move its binders, else its
#   single witness reads as a degenerate pts=1 point):
#   * weak-add/change/delete/view-drop-inherited (4): a constant on the non-auto
#     branch, discarding the inherited decision `superResult`. Each moves its
#     gate's `autoCreated` (T->F) and `superResult` (false->true) binders off the
#     values the view-rule rival pins them at, so no gate binder is left pinned.
#     Each is a real divergence (returns `false` where the spec demands
#     `superResult`) with the refinement argument that discarding the inherited
#     decision regresses every non-link relation and so would not resolve.
#   * weak-view-drop-view-disjunct: the view gate's analogue of the editing-gate
#     view-rule rival — drops Perm.view (the disjunct that distinguishes the view
#     gate's spec), denying view to a view-only principal. The view gate's own
#     load-bearing clause (view-or-change, not change-only) is thereby attacked;
#     without it the view obligation would carry only the drop-inherited rival.
#   * weak-hap-const-false: the shared probe's second witness (always deny),
#     moving `userHasPerm` and `perms` off the first-only rival's point so the
#     probe's two binders are both varied.
#
# ADDED BY AUDIT (2, no sibling counterpart):
#   * weak-view-drop-change-disjunct: the view gate's change disjunct was named as
#     load-bearing in the header but demonstrated by no case. Refuted at
#     (T, change-only, F), a third point on that obligation.
#   * pos-hap-list-any: a correct probe that is only EXTENSIONALLY equal to
#     `anyPerm` (closed by induction, not `rfl`), which the existing closed-form
#     positive — definitionally the post-image — cannot probe.
#
# BINDER / POINT COVERAGE. Each of the five obligations is attacked at two
#   distinct input points, the view gate at three:
#     addRelationAllowed    (T, view-only, F) and (F, change-only, T)
#     changeRelationAllowed (T, view-only, F) and (F, change-only, T)
#     deleteRelationAllowed (T, view-only, F) and (F, change-only, T)
#     viewRelationAllowed   (T, view-only, F), (F, change-only, T)
#                           and (T, change-only, F)   [added by audit]
#     holdsAnyTargetPerm    (change-only, [view,change]) and (view-only, [view])
#   so for every gate `autoCreated` ranges T/F, `userHasPerm` over the view-only
#   and change-only classes, and `superResult` over false/true; for the shared
#   probe `userHasPerm` ranges over the two classes and `perms` over
#   [Perm.view, Perm.change] / [Perm.view]. No input binder of any obligation is
#   pinned across its rivals. Each obligation has a single top-level ensures
#   clause, defended by the positive controls / admissibility case and attacked
#   by its rivals.
#
#   A caveat the reporter's binder count cannot express: on the view gate, the
#   two ORIGINAL rivals both hold the requested-list clause at a principal the
#   OTHER disjunct already decides, so `[Perm.view, Perm.change]` was varied as a
#   list without either disjunct being individually load-bearing. The added
#   (T, change-only, F) point is what makes the change disjunct itself
#   observable. Binder variation being MEANINGFUL is not the same as a binder
#   taking two spellings.
#
# ATTACK-D / ATTACK-E RESIDUE (audit, recorded so the next reader need not
#   re-measure). Six NEW wrong impls were built against the frozen spec and all
#   six were REJECTED, so no spec hole was found on this surface: the add gate
#   ignoring `autoCreated`; the add gate ORing `superResult` into the auto branch;
#   the add gate with its two branches swapped; the view gate dropping the change
#   disjunct (kept above as a case); the probe returning `!perms.isEmpty`; and the
#   probe consulting only the LAST requested permission. On the E side, a
#   forward-accumulating probe loop (`perms.take i` invariant) could NOT be closed
#   within a retuned tactic body — the take-step needs a lemma, and a variant may
#   not add one, so this is a scope limit of the case format and NOT evidence the
#   spec is too strong; the extensional `List.any` reshape kept above lands the
#   same point (a correct non-definitional shape verifies).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model (the probe is modeled deeply as `anyPerm`
# in the pure region), so there is nothing there to probe.
AXIOM_TESTS = []
