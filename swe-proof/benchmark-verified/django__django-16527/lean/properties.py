"""properties.py — G-PBT falsification battery for django__django-16527 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``-- proof-start`` / ``-- proof-end``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``theorem correct_buttonFlags`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation. It is checked by the real verifier: ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

CARRIER-WIDENING NOTE (why this port is BIGGER than its nagini sibling).
The nagini sibling contracts a single narrow function over five booleans
(the create-a-new-object affordance in isolation). This lean bundle models the
WHOLE button-visibility computation as one obligation
``correct_buttonFlags : ∀ i, problem_spec_buttonFlags i (implementation_buttonFlags i)``
whose postcondition is a conjunction of SEVEN independent output clauses, each
an exact boolean formula over the thirteen inputs (frame discipline: every
output component is pinned to its input formula). The behavioral fix lives in
ONE of those seven clauses; the other six are frame pins. Two of those six are
observed by a previously-passing recorded test (the raw save flag and the
save-and-add-another flag); the remaining four are pinned by the spec but
observed by no recorded test — see the OBSERVABILITY CAVEAT at the foot of this
file, which states exactly which is which. So the port does not shrink — it
carries the sibling's rival set for the FIX clause and adds one genuine frame
rival per remaining clause, because the wider carrier gives each of those
clauses a real obligation to attack.

DEFENDED SURFACE. One obligation over the input bundle ``i : ButtonInput``:

  problem_spec_buttonFlags i result :=
    result.canChange             = (hasChangePermission || hasEditableInlineAdminFormsets) ∧
    result.showDeleteLink        = (!isPopup && hasDeletePermission && change && showDelete) ∧
    result.showSaveAsNew         = (!isPopup && hasAddPermission && change && saveAs) ∧
    result.showSaveAndAddAnother = (hasAddPermission && !isPopup && (!saveAs||add) && cs && showSaveAndAddAnother) ∧
    result.showSaveAndContinue   = (!isPopup && cs && hasViewPermission && showSaveAndContinue) ∧
    result.showSave              = (showSave && cs) ∧
    result.showClose             = (!(showSave && cs))

where ``cs = canSave i``. Each clause is an EXACT boolean equality — a
biconditional pinning that output on every assignment — so any impl whose value
differs from a clause's formula on even one input must be rejected.

The load-bearing decision is which permission gates the create-a-new-object
affordance: the ADD permission ALONE. A viewer holding only the edit right must
NOT see it, because that affordance creates a fresh object. ``hasChangePermission``
is observed by the affordance's neighbours (``canChange``, ``canSave``) but does
NOT appear in the affordance clause after the fix — it exists so that an impl
gating on the wrong permission is expressible against this identical spec and
diverges exactly where the two permissions disagree.

ADVERSARIAL READ of the nagini weakness classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input may carry a fractional heap permission an impl can overwrite. Lean
    is referentially transparent: every field of ``ButtonInput`` is an immutable
    ``Bool`` value, there is no heap and no aliasing, so there is no read-only
    input to mutate and no substitute probe to build. Reported as vacuous, not
    fabricated. (Its *spirit* — an output left unconstrained — is instead
    covered positively: the spec pins all seven outputs, and the six frame
    rivals below each prove one such pin is load-bearing.)
  * UNGROUNDED-ORACLE ECHO — N/A. Every clause is a total, fully unfolded boolean
    function of the inputs (the ``axioms`` region declares nothing; the only
    ``pure`` helper ``canSave`` is itself unfolded boolean algebra). There is no
    opaque answer key to echo. Any impl satisfying ``result = <formula>`` IS the
    formula. Instead we carry honest reshape POSITIVE CONTROLS.
  * CONTROL-FLOW-EFFECT — N/A. Pure total function, no exception, no side effect,
    no early-return path distinguishable from the returned record.
  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean, re-measured rather than
    argued: see the DIVERGENCE note in the accounting section at the foot of this
    file for the two builds and their exact errors. Not to be confused with the
    velvet ``partial``-semantics spec hole in ``the corpus-wide termination-semantics finding``,
    which does not apply to this backend.
  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals right on part of the input cube but
    diverging on a sub-domain (gating on the wrong permission; on either; on
    neither; flipping an operand; regressing a frame pin). Each is refuted at a
    concrete assignment.

WITNESS. Every reject case carries a Lean ``example`` stating ``¬ problem_spec``
at one concrete ``ButtonInput`` literal, closed by ``decide``. Checked in a file
whose ``-- proof-start``/``-- proof-end`` region has been stripped (so the frozen
tactic script cannot mask the verdict): it must elaborate against the rival and
fail against the frozen solution. Every input is a ``Bool`` literal, so no
head binder is introduced and no conditioning-on-the-carrier is needed (the
carrier is fully transparent). Each witness's point is chosen so that ONLY the
attacked clause diverges from the spec at that input, so the ``¬`` is
attributable to that clause.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the whole
computation is concrete boolean algebra modeled deeply). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16527"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- Frozen impl anchors. Each lies wholly inside the one `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both asserted by
# ---- _swap at build time, so the manifest breaks loudly on any spec drift).
_GOLD_SAVEASNEW = (
    "    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,")
_GOLD_CANCHANGE_LET = (
    "  let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets\n")
_GOLD_CANCHANGE_FIELD = "    canChange := canChange,"
_GOLD_DELETELINK = (
    "    showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,")
_GOLD_SAVEADD_LET = (
    "    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && canSaveV\n"
    "      && i.showSaveAndAddAnother")
_GOLD_SAVECONT_LET = (
    "    !i.isPopup && canSaveV && i.hasViewPermission && i.showSaveAndContinue")
_GOLD_SHOWSAVE = "    showSave := i.showSave && canSaveV,"
_GOLD_SHOWCLOSE = "    showClose := !(i.showSave && canSaveV)"

# The frozen proof body (kept verbatim on every reject case: a wrong impl fails
# to close it, which is exactly the "does not verify" the gate records, and the
# witness is what attributes that failure to the spec).
_GOLD_PROOF = "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩"


def _impl(anchor, new):
    """Replace one frozen impl anchor with a rival body."""
    return _swap(_BASE, anchor, new)


# --------------------------------------------------------------------------
# Witness construction. A witness states `¬ problem_spec_buttonFlags <i> (impl
# <i>)` at a concrete ButtonInput literal and closes by `decide`. The point is
# chosen so ONLY the attacked clause diverges from the spec there.
# --------------------------------------------------------------------------
_FIELDS = [
    "add", "change", "isPopup", "saveAs", "showSave", "showSaveAndAddAnother",
    "showSaveAndContinue", "hasAddPermission", "hasChangePermission",
    "hasViewPermission", "hasEditableInlineAdminFormsets", "hasDeletePermission",
    "showDelete",
]
# Default point: a normal (non-popup) change form of an existing object with the
# duplicate-as-new opt-in on and the viewer holding every permission — a shape a
# regression test builds. Overrides move exactly the operands a rival abuses.
_DEFAULTS = {
    "add": "false", "change": "true", "isPopup": "false", "saveAs": "true",
    "showSave": "true", "showSaveAndAddAnother": "true",
    "showSaveAndContinue": "true", "hasAddPermission": "true",
    "hasChangePermission": "true", "hasViewPermission": "true",
    "hasEditableInlineAdminFormsets": "false", "hasDeletePermission": "true",
    "showDelete": "true",
}


def _lit(**overrides):
    bad = set(overrides) - set(_FIELDS)
    if bad:
        raise AssertionError(f"unknown field(s): {bad}")
    vals = {**_DEFAULTS, **overrides}
    body = ", ".join(f"{f} := {vals[f]}" for f in _FIELDS)
    return "{ " + body + " }"


def _witness(**overrides):
    lit = _lit(**overrides)
    return (f"example : ¬ problem_spec_buttonFlags\n"
            f"    {lit}\n"
            f"    (implementation_buttonFlags\n"
            f"    {lit}) := by\n"
            f"  unfold problem_spec_buttonFlags implementation_buttonFlags\n"
            f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify with a proof that actually closes for the new shape; else
    # the exact-equality post-image is SPEC-TOO-STRONG. Each keeps the
    # obligation statement byte-identical.
    # =====================================================================
    {
        "id": "pos-inline-canChange",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the `canChange` local binding is inlined into the record
        # literal. Same value on every input; the frozen per-clause `rfl` bundle
        # still closes because the field is now definitionally the formula.
        "module": _swap(
            _swap(_BASE, _GOLD_CANCHANGE_LET, ""),
            _GOLD_CANCHANGE_FIELD,
            "    canChange := i.hasChangePermission || i.hasEditableInlineAdminFormsets,"),
        "rationale": (
            "a correct reshape — the `canChange` intermediate is inlined into the "
            "returned record — computes the identical seven-tuple on every input "
            "and adds no proof obligation, so the frozen per-clause `rfl` bundle "
            "still discharges the biconditional. If a logically-equal impl could "
            "not verify, the post-image would be SPEC-TOO-STRONG on impl shape."),
    },
    {
        "id": "pos-reorder-saveAsNew",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the four conjuncts of the create-a-new-object clause are
        # reordered. `&&` is commutative/associative so the value is unchanged,
        # but the reorder breaks the syntactic `rfl` on that clause, so the proof
        # is re-closed for the new shape (a `show` retargets to the reordered
        # term, then an exhaustive `cases` over its four operands). Only the
        # proof body changes; the theorem statement is byte-identical.
        "module": _swap(
            _swap(_BASE, _GOLD_SAVEASNEW,
                  "    showSaveAsNew := i.saveAs && i.change && i.hasAddPermission && !i.isPopup,"),
            _GOLD_PROOF,
            "  refine ⟨rfl, rfl, ?_, rfl, rfl, rfl, rfl⟩\n"
            "  show (i.saveAs && i.change && i.hasAddPermission && !i.isPopup)\n"
            "    = (!i.isPopup && i.hasAddPermission && i.change && i.saveAs)\n"
            "  cases i.saveAs <;> cases i.change <;> cases i.hasAddPermission "
            "<;> cases i.isPopup <;> rfl"),
        "rationale": (
            "a correct reshape — the create-a-new-object clause's four conjuncts "
            "reordered — computes the identical boolean on every assignment, so it "
            "MUST verify against the biconditional; the proof is honestly re-closed "
            "for the new term order (no lemma, no `sorry`: `&&` commutes and the "
            "goal is decided by exhaustive `cases` on the four operands). A correct "
            "reshape that could not be reproven would be SPEC-TOO-STRONG."),
    },

    {
        "id": "admiss-discriminating-pins",
        "kind": "admissibility",
        "expect": "verify",
        # ADDED BY AUDIT. The port recorded the nagini admissibility case as
        # VACUOUS on the ground that this obligation has no precondition
        # hypothesis, so "a normal input is admitted" is trivially true. The
        # first half of that is right, but it disposes of the wrong obligation:
        # the nagini case also asserted the postcondition PINS THE EXPECTED
        # VALUE at the discriminating inputs, and that half is expressible here
        # and is not vacuous. This case states it as two consequences of the
        # spec at the two viewers the failing test builds: from
        # `problem_spec_buttonFlags <input> r` alone — for an ARBITRARY r, so
        # nothing is read off the impl — the create-a-new-object flag is forced
        # to `false` for the edit-only viewer and to `true` for the
        # add-permitted one. If the spec did not pin those, these would not
        # close, and the obligation would be admitting inputs it does not
        # actually constrain.
        "module": _swap(
            _BASE, "-- impl-end",
            "example (r : ButtonFlags)\n"
            f"    (h : problem_spec_buttonFlags\n      {_lit(hasAddPermission='false', hasChangePermission='true')} r) :\n"
            "    r.showSaveAsNew = false := by\n"
            "  unfold problem_spec_buttonFlags at h\n"
            "  simp at h\n"
            "  exact h.2.2.1\n"
            "\n"
            "example (r : ButtonFlags)\n"
            f"    (h : problem_spec_buttonFlags\n      {_lit(hasAddPermission='true', hasChangePermission='false')} r) :\n"
            "    r.showSaveAsNew = true := by\n"
            "  unfold problem_spec_buttonFlags at h\n"
            "  simp at h\n"
            "  exact h.2.2.1\n"
            "-- impl-end"),
        "rationale": (
            "the postcondition must ADMIT the two discriminating viewers of the "
            "failing test and must PIN the create-a-new-object flag to the "
            "expected value at each: `false` where only the edit right is held, "
            "`true` where the add right is held. Both are derived from the spec "
            "hypothesis alone at an arbitrary result record, so they test the "
            "postcondition and not the frozen impl. If either could not be "
            "derived, the spec would be admitting an input it fails to "
            "constrain (PRECOND-TOO-STRONG in the sense that matters on a "
            "carrier with no precondition: the obligation would not actually "
            "decide the F2P-relevant output). Both hypotheses are satisfiable — "
            "the frozen impl meets the spec at both points — so neither is "
            "vacuously true of a contradiction."),
    },

    # =====================================================================
    # UNIQUENESS rivals on the FIX clause (showSaveAsNew). Ported from the nagini
    # sibling, re-expressed against this carrier, each with a machine-checked
    # witness. The fix clause has four operands (isPopup, hasAddPermission,
    # change, saveAs); the rivals attack the permission operand three ways and
    # each of the other three operands once.
    # =====================================================================
    {
        "id": "weak-prepatch-change-perm",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug: gate the create-a-new-object affordance on the EDIT
        # permission instead of the ADD permission.
        "module": _impl(
            _GOLD_SAVEASNEW,
            "    showSaveAsNew := !i.isPopup && i.hasChangePermission && i.change && i.saveAs,"),
        "refinement": (
            "the faithful real counterpart keeps the affordance gated on the edit "
            "permission, so a viewer holding only the edit right is still shown the "
            "create-a-new-object shortcut. The failing test constructs exactly such "
            "a viewer on a normal change form with the opt-in on and asserts the "
            "shortcut is HIDDEN; it would still observe it shown => FAIL_TO_PASS "
            "NOT resolved."),
        "rationale": (
            "REJECT from the `result.showSaveAsNew` biconditional (clause "
            "`result.showSaveAsNew = (!i.isPopup && i.hasAddPermission && i.change "
            "&& i.saveAs)`): with the ADD permission "
            "PRESENT and the edit permission ABSENT the formula demands `true` but "
            "the edit-gated impl yields `false`. Refuted at (isPopup=F, add=T, "
            "changePerm=F, change=T, saveAs=T) — a point where the ADD permission "
            "is present, so the OR-gate near-miss AGREES with the frozen solution "
            "there and this rival is the sole diverger."),
        "witness": _witness(hasAddPermission="true", hasChangePermission="false"),
    },
    {
        "id": "weak-add-or-change",
        "kind": "uniqueness",
        "expect": "reject",
        # 'Either permission counts': gate on (add || change-perm). Equals the
        # formula whenever the ADD permission is present; admits the edit-only
        # viewer where the formula is false. Near-miss of the pre-fix bug, refuted
        # on the complementary sub-domain.
        "module": _impl(
            _GOLD_SAVEASNEW,
            "    showSaveAsNew := !i.isPopup && (i.hasAddPermission || i.hasChangePermission) "
            "&& i.change && i.saveAs,"),
        "refinement": (
            "the faithful real counterpart gates on EITHER permission. Checking the "
            "ADD permission ALONE is what the fix requires; an either-permission "
            "gate still shows the shortcut to the edit-only viewer, so the failing "
            "test asserting it HIDDEN for that viewer still observes it shown => "
            "NOT resolved."),
        "rationale": (
            "REJECT from the showSaveAsNew biconditional: at (isPopup=F, add=F, "
            "changePerm=T, change=T, saveAs=T) the impl yields `true` (the edit "
            "disjunct fires) while the formula (keyed on the ADD permission alone) "
            "yields `false`. Refuted at the edit-only sub-domain the pre-fix "
            "rival's witness does not probe."),
        "witness": _witness(hasAddPermission="false", hasChangePermission="true"),
    },
    {
        "id": "weak-drop-permission-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the permission gate entirely (regression to no permission check).
        # Agrees wherever the ADD permission is present; diverges on any non-popup
        # change form with the opt-in on that lacks it.
        "module": _impl(
            _GOLD_SAVEASNEW,
            "    showSaveAsNew := !i.isPopup && i.change && i.saveAs,"),
        "refinement": (
            "the faithful real counterpart drops the permission gate altogether, "
            "re-opening the very hole the fix closes: a viewer with NEITHER "
            "permission is shown the create-a-new-object shortcut. The failing test "
            "asserting the shortcut HIDDEN for a viewer without the ADD permission "
            "still observes it shown => NOT resolved."),
        "rationale": (
            "REJECT from the showSaveAsNew biconditional: at (isPopup=F, add=F, "
            "changePerm=F, change=T, saveAs=T) the impl yields `true` while the "
            "formula yields `false` (the missing ADD permission kills it). Refuted "
            "with NEITHER permission held — a third distinct permission assignment, "
            "complementary to both permission-gate rivals above."),
        "witness": _witness(hasAddPermission="false", hasChangePermission="false"),
    },
    {
        "id": "weak-flip-popup-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-operand corruption: gate on `isPopup` rather than `!isPopup`,
        # exposing the shortcut only in popups and withholding it on real change
        # forms.
        "module": _impl(
            _GOLD_SAVEASNEW,
            "    showSaveAsNew := i.isPopup && i.hasAddPermission && i.change && i.saveAs,"),
        "refinement": (
            "the faithful real counterpart gates on the popup flag rather than its "
            "negation, so the shortcut appears only in popup requests. The failing "
            "test runs an add-and-change viewer on a NORMAL (non-popup) change form "
            "and expects the shortcut SHOWN; this impl hides it there => NOT "
            "resolved."),
        "rationale": (
            "REJECT from the showSaveAsNew biconditional: at (isPopup=T, add=T, "
            "changePerm=T, change=T, saveAs=T) the impl yields `true` while the "
            "formula (which requires a non-popup request) yields `false`. Refuted "
            "at isPopup=T — the only witness that moves the popup operand off "
            "`false`."),
        "witness": _witness(isPopup="true"),
    },
    {
        "id": "weak-flip-change-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-operand corruption on the change-form operand: gate on `!change`,
        # offering the shortcut on an add page and hiding it on the change view.
        "module": _impl(
            _GOLD_SAVEASNEW,
            "    showSaveAsNew := !i.isPopup && i.hasAddPermission && !i.change && i.saveAs,"),
        "refinement": (
            "the faithful real counterpart gates on the negation of the change-view "
            "flag, so the shortcut is offered on an add page and withheld on the "
            "change view of an existing object — where duplicating-as-new only makes "
            "sense. The failing test runs on the change view and expects the shortcut "
            "SHOWN for an add-permitted viewer; this impl hides it there => NOT "
            "resolved."),
        "rationale": (
            "REJECT from the showSaveAsNew biconditional: at (isPopup=F, add=T, "
            "changePerm=F, change=F, saveAs=T) the impl yields `true` (its `!change` "
            "operand fires) while the formula (which requires the change view) yields "
            "`false`. Refuted at change=F — the witness that moves the change-view "
            "operand off `true`."),
        "witness": _witness(hasAddPermission="true", hasChangePermission="false",
                            change="false"),
    },
    {
        "id": "weak-flip-saveas-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-operand corruption on the opt-in operand: gate on `!saveAs`,
        # exposing the shortcut for admins that did NOT opt in and hiding it for
        # those that did.
        "module": _impl(
            _GOLD_SAVEASNEW,
            "    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && !i.saveAs,"),
        "refinement": (
            "the faithful real counterpart gates on the negation of the "
            "duplicate-as-new opt-in, so the shortcut is offered exactly for admins "
            "that did NOT enable it. The failing test enables the opt-in and expects "
            "the shortcut SHOWN for an add-permitted viewer; this impl hides it there "
            "=> NOT resolved."),
        "rationale": (
            "REJECT from the showSaveAsNew biconditional: at (isPopup=F, add=T, "
            "changePerm=F, change=T, saveAs=F) the impl yields `true` (its `!saveAs` "
            "operand fires) while the formula (which requires the opt-in) yields "
            "`false`. Refuted at saveAs=F — the witness that moves the opt-in "
            "operand off `true`."),
        "witness": _witness(hasAddPermission="true", hasChangePermission="false",
                            saveAs="false"),
    },

    # =====================================================================
    # FRAME-PIN rivals — one per remaining output clause of the wider carrier.
    # Each drops or corrupts the operand that distinguishes one clause's formula
    # and is refuted at the sub-domain where that clause diverges.
    # These have no nagini counterpart: the sibling never modeled these clauses.
    #
    # WHAT THESE CASES DO AND DO NOT CLAIM (corrected by audit).
    # An earlier revision of this manifest justified each frame rival by
    # asserting that its faithful counterpart "regresses a previously-passing
    # test that pins this flag", i.e. that the change would not resolve. That
    # claim was checked against this instance's recorded evaluation set and is
    # NOT supported for the six clauses below. Corrected by a later audit, which
    # re-read the recorded set case by case; the earlier revision of this banner
    # overstated the gap in two ways and both are fixed here.
    #
    # What the recorded set ACTUALLY observes (three flags, not two):
    #   - the create-a-new-object flag, at the two discriminating viewers;
    #   - the save-and-add-another flag, via a per-admin opt-out override;
    #   - the RAW SAVE FLAG, asserted directly by a previously-passing test
    #     (and again indirectly through the rendered save control on another).
    # Observed by NO recorded test: the can-change flag, the delete-link flag,
    # the close-control flag and the save-and-continue flag — FOUR clauses, not
    # five.
    #
    # Of the six rivals below, FIVE agree with the frozen solution at every
    # input point the recorded set reaches, so no recorded test could
    # distinguish them. `frame-showClose-flip` is NOT one of them: it inverts
    # its clause and so diverges at every recorded point too. It is still not a
    # demonstrated non-resolution, but for the OTHER reason — no recorded test
    # looks at the close-control flag — which is what its own rationale says.
    #
    # The cases are kept because they earn their rejection on a DIFFERENT and
    # sound ground: FRAME DISCIPLINE (spec_guide §0.5). The obligation pins all
    # seven outputs, and a `problem_spec` that left one output component
    # unconstrained would be the referentially-transparent analogue of the
    # full-permission hole — a wrong impl could put anything there and still
    # verify. Each rival demonstrates that one such pin is load-bearing: it is
    # observably wrong against the modeled behavior (machine-checked at a
    # concrete input by its witness), and the spec senses it. That is a real
    # spec-strength property, and it is what the `rationale` on each case now
    # states. It is NOT a demonstrated non-resolution, so no `refinement`
    # claiming one is attached to these five.
    #
    # `frame-showSaveAndAddAnother-drop-optout` is the exception and is the one
    # frame case that DOES carry a refinement: its divergence point is reached
    # by a test in the recorded set, so its faithful counterpart is a genuine
    # non-resolution. It was added by the audit for exactly that reason.
    # =====================================================================
    {
        "id": "frame-canChange-drop-inline",
        "kind": "uniqueness",
        "expect": "reject",
        # canChange := hasChangePermission (drops the editable-inline disjunct).
        "module": _swap(
            _swap(_BASE, _GOLD_CANCHANGE_LET,
                  "  let canChange : Bool := i.hasChangePermission\n"),
            # keep field referencing the (now-narrowed) local
            _GOLD_CANCHANGE_FIELD, _GOLD_CANCHANGE_FIELD),
        "rationale": (
            "REJECT from the canChange clause `= (hasChangePermission || "
            "hasEditableInlineAdminFormsets)`: at (changePerm=F, formsets=T) the "
            "formula is `true` but the impl yields `false`. Only this clause "
            "diverges at that point. FRAME PIN, not a demonstrated "
            "non-resolution: no test in the recorded evaluation set observes "
            "this flag, and this rival agrees with the frozen solution at every "
            "input point that set reaches. What it proves is that the clause is "
            "load-bearing — drop the disjunct and the spec still senses it, so "
            "the pin is not decoration. A viewer editable only through inline "
            "formsets is genuinely mis-reported as unable to change, which is "
            "wrong against the modeled behavior even though the recorded tests "
            "would not catch it."),
        "witness": _witness(hasChangePermission="false",
                            hasEditableInlineAdminFormsets="true"),
    },
    {
        "id": "frame-showDeleteLink-drop-delperm",
        "kind": "uniqueness",
        "expect": "reject",
        # showDeleteLink drops the delete-permission conjunct.
        "module": _impl(
            _GOLD_DELETELINK,
            "    showDeleteLink := !i.isPopup && i.change && i.showDelete,"),
        "rationale": (
            "REJECT from the clause `result.showDeleteLink = (!i.isPopup && "
            "i.hasDeletePermission && i.change && i.showDelete)`: at (isPopup=F, "
            "delPerm=F, change=T, showDelete=T) the formula is `false` but the impl "
            "yields `true`. Only this clause diverges at that point. FRAME PIN, "
            "not a demonstrated non-resolution: no test in the recorded "
            "evaluation set observes this flag, and this rival agrees with the "
            "frozen solution at every input point that set reaches. What it "
            "proves is that the clause is load-bearing — a viewer lacking the "
            "delete permission would be offered the delete affordance, which is "
            "wrong against the modeled behavior and silently bypasses a "
            "permission, and the spec senses it."),
        "witness": _witness(hasDeletePermission="false", change="true",
                            showDelete="true"),
    },
    {
        "id": "frame-showSaveAndAddAnother-drop-addperm",
        "kind": "uniqueness",
        "expect": "reject",
        # showSaveAndAddAnother drops its leading add-permission gate.
        "module": _impl(
            _GOLD_SAVEADD_LET,
            "    !i.isPopup && (!i.saveAs || i.add) && canSaveV\n"
            "      && i.showSaveAndAddAnother"),
        "rationale": (
            "REJECT from the clause `result.showSaveAndAddAnother = "
            "(i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && cs && "
            "i.showSaveAndAddAnother)`, whose formula leads with "
            "`i.hasAddPermission`: at (add=F, isPopup=F, saveAs=F, addPerm=F, "
            "changePerm=T, change=T, showSaveAndAddAnother=T) the canSave predicate "
            "holds so the impl yields `true` while the formula yields `false` "
            "(missing add permission). Only this clause diverges at that point. "
            "FRAME PIN, not a demonstrated non-resolution: the recorded "
            "evaluation set does observe this flag, but only at viewers holding "
            "the add permission, where this rival agrees with the frozen "
            "solution — so no recorded test distinguishes it. What it proves is "
            "that the gate is load-bearing: a viewer lacking the add permission "
            "would be offered an affordance that creates a further object, "
            "silently bypassing a permission, and the spec senses it. The "
            "companion `-drop-optout` rival is the one that diverges where a "
            "recorded test actually looks."),
        "witness": _witness(hasAddPermission="false", hasChangePermission="true",
                            change="true", isPopup="false", saveAs="false",
                            add="false", showSaveAndAddAnother="true"),
    },
    {
        "id": "frame-showSaveAndAddAnother-drop-optout",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. showSaveAndAddAnother ignores the per-admin opt-out
        # operand, so the flag can no longer be turned off for a form. This is
        # the ONE frame rival whose divergence point a test in the recorded
        # evaluation set actually reaches, which is why it carries a refinement
        # while the other frame rivals (correctly) do not.
        "module": _impl(
            _GOLD_SAVEADD_LET,
            "    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && canSaveV"),
        "refinement": (
            "the faithful real counterpart stops consulting the per-admin opt-out "
            "operand for the save-and-add-another flag, so a form that switches "
            "that affordance OFF is still offered it. A test in the recorded "
            "evaluation set exercises exactly that override — it drives a viewer "
            "holding both permissions on a normal change form with the affordance "
            "switched off and asserts the flag is False — and would observe True "
            "instead => that previously-passing test regresses, so the change "
            "would NOT resolve. Verified against the recorded set: at that point "
            "the frozen solution yields False (test passes) and this rival yields "
            "True (test fails)."),
        "rationale": (
            "REJECT from the clause `result.showSaveAndAddAnother = "
            "(i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && cs && "
            "i.showSaveAndAddAnother)`, whose trailing conjunct is the opt-out "
            "operand: at (addPerm=T, isPopup=F, saveAs=F, add=F, changePerm=T, "
            "change=T so cs holds, showSaveAndAddAnother=F) the formula is "
            "`false` but the impl yields `true`. Only this clause diverges at "
            "that point. Unlike the other frame rivals this divergence point IS "
            "reached by the recorded evaluation set, so the rejection attests to "
            "a real non-resolution and not only to frame discipline."),
        "witness": _witness(showSaveAndAddAnother="false", saveAs="false"),
    },
    {
        "id": "frame-showSaveAndContinue-drop-viewperm",
        "kind": "uniqueness",
        "expect": "reject",
        # showSaveAndContinue drops the view-permission conjunct.
        "module": _impl(
            _GOLD_SAVECONT_LET,
            "    !i.isPopup && canSaveV && i.showSaveAndContinue"),
        "rationale": (
            "REJECT from the clause `result.showSaveAndContinue = (!i.isPopup && "
            "cs && i.hasViewPermission && i.showSaveAndContinue)`: at (isPopup=F, "
            "changePerm=T, change=T (so cs holds), viewPerm=F, "
            "showSaveAndContinue=T) the formula is `false` but the impl yields "
            "`true`. Only this clause diverges at that point. FRAME PIN, not a "
            "demonstrated non-resolution: no test in the recorded evaluation set "
            "observes this flag, and this rival agrees with the frozen solution "
            "at every input point that set reaches. What it proves is that the "
            "conjunct is load-bearing — a viewer lacking the view permission "
            "would be offered save-and-continue, silently bypassing a "
            "permission, and the spec senses it."),
        "witness": _witness(hasViewPermission="false", hasChangePermission="true",
                            change="true", isPopup="false",
                            showSaveAndContinue="true"),
    },
    {
        "id": "frame-showSave-drop-cansave",
        "kind": "uniqueness",
        "expect": "reject",
        # showSave drops the can-save conjunct (returns the raw show_save flag).
        "module": _impl(
            _GOLD_SHOWSAVE, "    showSave := i.showSave,"),
        "rationale": (
            "REJECT from the clause `result.showSave = (i.showSave && cs)`: at (showSave=T, "
            "add=F, change=F, formsets=F so cs=F, changePerm/addPerm irrelevant) "
            "the formula is `false` but the impl yields `true`. Only this clause "
            "diverges at that point. FRAME PIN, not a demonstrated "
            "non-resolution: the recorded evaluation set does assert this flag, "
            "but only on a form that CAN be saved, where this rival agrees with "
            "the frozen solution — so no recorded test distinguishes it. What it "
            "proves is that the can-save gate is load-bearing: the save control "
            "would be offered on a form that cannot be saved, which is wrong "
            "against the modeled behavior, and the spec senses it."),
        "witness": _witness(showSave="true", change="false", add="false",
                            hasEditableInlineAdminFormsets="false",
                            hasChangePermission="false", hasAddPermission="false"),
    },
    {
        "id": "frame-showClose-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # showClose drops the negation (returns show_save && can_save).
        "module": _impl(
            _GOLD_SHOWCLOSE, "    showClose := (i.showSave && canSaveV)"),
        "rationale": (
            "REJECT from the showClose clause `= (!(showSave && cs))`: at "
            "(showSave=T, changePerm=T, change=T so cs=T) the formula is `false` "
            "but the impl yields `true` (it returns `showSave && cs` un-negated). "
            "Only this clause diverges at that point. FRAME PIN, not a "
            "demonstrated non-resolution: no test in the recorded evaluation set "
            "observes this flag. Note this rival is the most aggressive of the "
            "six — it inverts the clause, so it diverges on ALL 2^13 inputs "
            "including every point the recorded set reaches; the reason that is "
            "still not a demonstrated non-resolution is that no recorded test "
            "LOOKS at this flag, not that the values agree. What it proves is "
            "that the pin is load-bearing: the close control's visibility would "
            "be exactly inverted, and the spec senses it."),
        "witness": _witness(showSave="true", hasChangePermission="true",
                            change="true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting.
#
# The nagini sibling carries 7 cases against a NARROW carrier (one function,
# `save_as_new_visible`, over five booleans): 2 soundness positives, 1
# admissibility, 4 uniqueness rivals (frame-mutation recorded N/A, not shipped;
# AXIOM_TESTS empty). This lean bundle models a WIDER carrier — the whole
# button-visibility computation as one obligation with a seven-clause
# postcondition — so the port both ports the fix-clause rivals and adds a frame
# rival per remaining clause.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder         -> pos-reorder-saveAsNew        RE-EXPRESSED
#   pos-control-cheapest-inline -> pos-inline-canChange         RE-EXPRESSED
#   admiss-f2p-shaped           -> admiss-discriminating-pins   PORTED (audit)
#   weak-prepatch-may-change    -> weak-prepatch-change-perm    PORTED
#   weak-add-or-change          -> weak-add-or-change           PORTED
#   weak-drop-add-conjunct      -> weak-drop-permission-gate    PORTED
#   weak-flip-popup-gate        -> weak-flip-popup-gate         PORTED
#   (nagini frame-mutation N/A) -> (none)                       VACUOUS
#
# RE-EXPRESSED (soundness). Nagini's two positives are (a) reordered conjuncts
#   and (b) the cheapest inline return. On lean the fix clause is one conjunct of
#   a seven-tuple, so:
#     - pos-reorder-saveAsNew reorders that clause's four conjuncts (a genuinely
#       different term that breaks the syntactic `rfl`) and honestly re-closes
#       the proof for the new shape;
#     - pos-inline-canChange inlines an intermediate binding (the lean analogue
#       of "cheapest inline"), which keeps the frozen per-clause `rfl` bundle.
#   Both are structurally different, both verify, neither weakens the obligation.
#
# ADMISSIBILITY — PORTED (corrected by audit; was recorded VACUOUS).
#   The nagini admissibility case does two things: (a) asserts a normal
#   F2P-shaped input satisfies the PRECONDITION, and (b) asserts the
#   POSTCONDITION pins the expected value there. On lean the obligation is
#   `∀ i, problem_spec_buttonFlags i (implementation_buttonFlags i)` with no
#   precondition hypothesis, so (a) really is vacuous — the domain is total.
#   But (b) is NOT vacuous and IS expressible on this carrier: from the spec
#   hypothesis alone, at an arbitrary result record, the create-a-new-object
#   flag is forced to the expected value at each discriminating viewer. The
#   earlier revision disposed of the whole case on the strength of (a) alone;
#   `admiss-discriminating-pins` now carries (b). Machine-checked: it
#   elaborates (exit 0), and both spec hypotheses are satisfiable, so neither
#   consequence follows from a contradiction.
#
# FRAME-MUTATION — VACUOUS. Referential transparency, no heap, no `mut` binder,
#   no read-only input to overwrite. Reported, not fabricated. Its spirit (an
#   unconstrained output) is covered positively: the spec pins all seven outputs
#   and the frame rivals below prove each pin load-bearing.
#
# DIVERGENCE / NON-TERMINATION — VACUOUS on lean, and re-measured by the audit
#   rather than argued. `implementation_buttonFlags` is a total `def`; making it
#   `partial` and self-looping does not yield a vacuous verify — the region
#   surgery first fails to compile the `partial` definition (`could not prove
#   that the type ButtonInput → ButtonFlags is nonempty`), and once an
#   `Inhabited ButtonFlags` instance is supplied inside the impl region so the
#   `partial` def compiles, the obligation then fails on the spec itself
#   (`Application type mismatch: rfl ... expected (implementation_buttonFlags
#   i).showClose = !(i.showSave && canSave i)`) because the diverging impl has
#   no reducible value to match the formula. Both builds exit 1, so there is
#   nothing to port and no spec hole here. The known `partial`-semantics spec
#   hole recorded in the corpus-wide termination-semantics finding is a VELVET finding (401
#   velvet bundles, `set_option loom.semantics.termination "partial"`); the
#   lean backend is explicitly unaffected, so it is cited, not re-reported.
#
# ADDED (9, no nagini counterpart, all justified by the WIDER carrier; the
# earlier revision of this line said 10, which did not match the manifest —
# corrected by audit, the nine are enumerated below and SPEC_TESTS has 16 cases
# against the sibling's 7):
#   - weak-flip-change-gate, weak-flip-saveas-gate: attack the two remaining
#     operands of the fix clause (change, saveAs) that nagini's rivals hold fixed;
#   - frame-canChange-drop-inline, frame-showDeleteLink-drop-delperm,
#     frame-showSaveAndAddAnother-drop-addperm,
#     frame-showSaveAndAddAnother-drop-optout,
#     frame-showSaveAndContinue-drop-viewperm, frame-showSave-drop-cansave,
#     frame-showClose-flip: one or more genuine rivals per remaining output
#     clause of the seven-clause postcondition, each refuted at the sub-domain
#     where that clause alone diverges. Only `-drop-optout` carries a
#     P2P-regression refinement; see the FRAME-PIN banner above for why the
#     others must not, and what they do attest to instead.
#
# CLAUSE COVERAGE. All seven top-level clauses of problem_spec_buttonFlags are
#   attacked by a reject rival AND defended by the soundness positives:
#     canChange              <- frame-canChange-drop-inline
#     showDeleteLink         <- frame-showDeleteLink-drop-delperm
#     showSaveAsNew          <- weak-prepatch/add-or/drop/flip-popup/flip-change/flip-saveas (6)
#     showSaveAndAddAnother  <- frame-showSaveAndAddAnother-drop-addperm,
#                               frame-showSaveAndAddAnother-drop-optout
#     showSaveAndContinue    <- frame-showSaveAndContinue-drop-viewperm
#     showSave               <- frame-showSave-drop-cansave
#     showClose              <- frame-showClose-flip
#
# OBSERVABILITY CAVEAT (recorded so the coverage claim above is not read as more
#   than it is). "All seven clauses are attacked" is a statement about the SPEC,
#   not about the recorded evaluation set. Re-derived clause by clause against
#   that set (an earlier revision of this note undercounted it by one):
#
#     clause                 observed by a recorded test?
#     ---------------------------------------------------------------------
#     showSaveAsNew          YES — the failing test, at two viewers
#     showSaveAndAddAnother  YES — a previously-passing opt-out override
#     showSave               YES — asserted directly by a previously-passing
#                                  test, and rendered on a second one
#     canChange              no
#     showDeleteLink         no
#     showSaveAndContinue    no
#     showClose              no
#
#   So THREE of the seven clauses are observed and FOUR are frame pins whose
#   rivals no recorded test would catch. The spec is STRONGER than the recorded
#   tests on those four clauses, which is the safe direction (verify ⟹ correct
#   is preserved; the spec simply also forbids things no test checks), but it
#   does mean the corresponding frame rejections attest to frame discipline
#   rather than to a demonstrated non-resolution. Note the two are not the same
#   count: `frame-showSave-drop-cansave` attacks an OBSERVED clause yet is still
#   only a frame pin, because it agrees with the frozen solution at the
#   particular points the recorded set reaches (every one of them is a form that
#   CAN be saved). Being observed is necessary for a non-resolution, not
#   sufficient — the divergence must land where the test looks, which is why
#   only `-drop-optout` carries a P2P refinement.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing to probe.
AXIOM_TESTS = []
