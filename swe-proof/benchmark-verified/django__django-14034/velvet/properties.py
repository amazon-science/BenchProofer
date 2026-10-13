"""properties.py — G-PBT falsification battery for django__django-14034 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over a list of sub-field slots):

  requiredFlags (outerRequired : Bool) (requireAll : Bool) (subs : List SubField)
      return (out : List Bool)
    ensures out = requiredPlan outerRequired requireAll subs   -- the load-bearing clause

``requiredPlan`` is a fully unfolded ``def`` in the ``pure`` region — there is NO
opaque answer key to echo. It maps each sub-field slot through ``subRequired``:

  subRequired oR rA s = oR && (rA || (s.marksRequired && s.required))

so the single ``ensures`` clause carries FOUR independent sub-behaviours over the
three input binders:
  * the overall gate ``outerRequired`` — when closed, NO slot is marked;
  * the joint-required disjunct ``requireAll`` — when set (and the gate open),
    EVERY slot is marked regardless of its own two flags;
  * when the gate is open but the joint-required disjunct is off, a slot is
    marked exactly when BOTH its own opt-in (``marksRequired``) AND its own
    required flag (``required``) hold — the per-slot conjunction;
  * the per-element traversal preserves list ORDER and length.

The rivals below vary all three binders (both boolean flags across both values,
the list across length-one and length-two) and attack every one of those four
sub-behaviours independently.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS here. The nagini sibling carries this class as
    MANDATORY because its constituent inputs are held at a fractional heap
    permission (``Acc(subs[k].field_required, 1/2)``) an impl can illegally
    overwrite (write the read-only input, e.g. a self-assignment). Lean and
    Velvet are referentially transparent: ``subs`` is an immutable value, this
    bundle declares no ``mut`` parameter, there is no heap and no aliasing — so
    there is no read-only input to overwrite and no substitute probe to build.
    Not fabricated (per the porting map: this class is vacuous on Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class: the post-image is a total,
    fully unfolded function of the method's own inputs (``requiredPlan`` and
    ``subRequired`` are concrete ``def``s in the ``pure`` region; the ``axioms``
    region is empty), so there is no answer key to echo. The positives are
    honest cheapest-reshape controls.
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals correct on part of the input domain
    but diverging on a sub-domain (a slot that opts in but is not itself
    required; the joint-required regime; the gate-closed regime).

WITNESS PLACEMENT. Each reject rival is refuted at a concrete input chosen so
the points together move all three binders across their range: ``outerRequired``
takes both values (false in the gate rival, true elsewhere), ``requireAll`` takes
both values (true in the joint-required rivals, false elsewhere), and ``subs``
takes both a length-one and a length-two list. No two rivals fail at the same
point, and each partial-domain rival is refuted on the exact sub-domain where it
diverges from the frozen solution while agreeing elsewhere, so its sub-domain
claim is machine-checked rather than asserted.

MEASURED CARRIER FACT (governs the rival impl SHAPE **and** forces a
``witness_reference``). The frozen impl is a well-founded ``while`` loop; its
extracted tester does NOT reduce under ``decide`` (the kernel treats
well-founded recursion opaquely). Two consequences, both measured:

  * Every reject rival is written in a purely-functional ``List.map`` form
    (which the author controls), whose extracted tester DOES reduce under
    ``decide``. The full rival module still carries the frozen (loop-tuned)
    ``prove_correct`` script, so it genuinely fails to verify (the rejection),
    and the witness is what attributes that rejection to the spec rather than to
    the tactic mismatch.
  * The frozen solution CANNOT serve as the witness's second subject. Measured
    directly: the witness for ``weak-ignore-subfield-required`` built against
    gold fails with ``reduction got stuck at the Decidable instance ... match
    requiredFlagsTester true false [...]`` — the kernel never evaluated the
    claim, so that exit code would attest to a refutation never performed
    (``witness-undecided``), and the identical error appears for a TRUE claim
    about the frozen impl. Stuckness is NOT refutation.

So every reject case names an explicit ``witness_reference``: ``_LOOPFREE``, a
loop-free ``List.map`` impl of the SAME frozen spec that VERIFIES (it is the
``pos-map-form`` positive's source, so the battery itself records that
loop-freeness is not what any rival is rejected for). The gate checks the
reference shares the frozen spec and verifies before using it, then refutes each
witness against it. Measured on that reference the same witness reports
``Tactic `decide` proved that the proposition ... is false`` — a real decision,
which is the discrimination the frozen impl could not supply. This is stated
explicitly rather than left to the gate's stuck-reduction fallback (which would
otherwise pick a positive implicitly, in manifest order and capped), so the
attestation does not depend on that heuristic.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY). There is no axiom-soundness / axiom-containment obligation to
probe here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14034"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the loop and its return).
# ---- It lies wholly inside the single -- impl-start .. -- impl-end region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap), so each
# ---- edit keeps same_spec by construction and leaves the frozen prove_correct
# ---- statement intact.
_IMPL = (
    "    let mut result : List Bool := []\n"
    "    let mut i := subs.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ subs.length\n"
    "      invariant result = requiredPlan outerRequired requireAll (subs.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let s := subs[i - 1]!\n"
    "      result := subRequired outerRequired requireAll s :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# ---- per-loop-step anchor (unique in the file): the one statement that computes
# ---- and prepends a slot's marker. Used by the inline-unfold positive control.
_STEP = "      result := subRequired outerRequired requireAll s :: result"

# ---- proof-body anchor. The prove_correct TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file.
_PROOF = (
    "prove_correct requiredFlags by\n"
    "  loom_solve\n"
    "  rw [requiredPlan_drop_step outerRequired requireAll subs i (by omega) (by omega)]\n"
    "  simp_all"
)

# ---- for the admissibility case: the first impl line, a unique anchor to
# ---- prepend an in-region assertion before the (verbatim) loop.
_FIRST = "    let mut result : List Bool := []"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- The witness REFERENCE, shared by every reject case. A loop-free impl of
# ---- the same frozen spec: the backward `while` loop is replaced by a forward
# ---- `List.map` and the proof by a two-case list induction. It VERIFIES (it is
# ---- exactly the `pos-map-form` positive's source, which the battery asserts
# ---- and the gate independently re-checks), and unlike the frozen loop its
# ---- extracted tester REDUCES under `decide` — so it can actually decide a
# ---- witness claim. Required because the frozen impl decides nothing (see the
# ---- MEASURED CARRIER FACT above): refuting against it would be
# ---- `witness-undecided`, not a refutation.
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL,
          "    return subs.map (fun s => subRequired outerRequired requireAll s)"),
    _PROOF,
    "prove_correct requiredFlags by\n"
    "  loom_solve\n"
    "  induction subs with\n"
    "  | nil => rfl\n"
    "  | cons s ss ih => simp [requiredPlan, ih]")


def _rival(fn_body: str) -> str:
    """A wrong impl in purely-functional map form (its tester reduces under
    `decide`). The frozen loop-tuned proof is kept, so the module fails to
    verify — the rejection — and the witness attributes it to the spec."""
    return _with_impl("    return subs.map (fun s => %s)" % fn_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `requiredFlagsTester oR rA subs = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose prove_correct block has been stripped, so no tactic script
# ---- can mask the verdict. There is no `require` clause, so every concrete input
# ---- reaches the postcondition (no vacuous pass on an excluded input).
_TESTER = (
    "extract_program_for requiredFlags\n"
    "prove_precondition_decidable_for requiredFlags\n"
    "prove_postcondition_decidable_for requiredFlags\n"
    "derive_tester_for requiredFlags\n\n"
)


def _wit(example: str) -> str:
    return _TESTER + example + "\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        # Reshape (minimal): inline-unfold the per-slot marker helper in the
        # loop body to its boolean product. Same value flow, same loop; the
        # frozen tactic script needs only to fold the unfolded product back to
        # the helper (one extra simp lemma), so the obligation still discharges.
        "id": "pos-inline-unfold-step",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _STEP,
                  "      result := (outerRequired && (requireAll || "
                  "(s.marksRequired && s.required))) :: result"),
            _PROOF,
            "prove_correct requiredFlags by\n"
            "  loom_solve\n"
            "  rw [requiredPlan_drop_step outerRequired requireAll subs i "
            "(by omega) (by omega)]\n"
            "  simp_all [subRequired]"),
        "rationale": "REJECT/PASS SOURCE = the sole ensures clause "
                     "(out = requiredPlan ...). Inlining the per-slot marker "
                     "helper to its boolean product leaves the computed value "
                     "definitionally equal per slot, so the loop still builds "
                     "requiredPlan; the reproof only folds the product back to "
                     "the helper. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        # Reshape (algorithmically different): replace the backward while loop
        # with a forward `List.map` of the per-slot marker helper — no loop, no
        # invariant, no index arithmetic. The returned list is identical; the
        # obligation is reproved by a short structural induction over `subs`.
        "id": "pos-map-form",
        "kind": "soundness",
        "expect": "verify",
        # SAME source object as the reject lane's `witness_reference`
        # (`_LOOPFREE`), so this case is the battery's own record that the
        # reference verifies — i.e. that loop-freeness is not what any rival is
        # being rejected for.
        "module": _LOOPFREE,
        "rationale": "REJECT/PASS SOURCE = the sole ensures clause. A genuinely "
                     "different algorithm (map instead of a backward loop) that "
                     "computes the SAME per-slot markers in the SAME order must "
                     "satisfy `out = requiredPlan ...`; the reproof is a two-case "
                     "list induction. If this cannot verify the spec "
                     "over-constrains the impl shape (SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so there is no
    # precondition that could exclude a normal input; the usual "a normal input
    # satisfies the precondition" probe is vacuous. The residual admissibility
    # risk on a total domain is that the post-image is UNSATISFIABLE / DEGENERATE
    # — a spec no impl can meet reads exactly like a spec every impl meets. This
    # case discharges an in-region assert that at the F2P-shaped input (a
    # required slot that opts in, then an optional slot that opts in, with the
    # gate open and the joint-required disjunct off) the plan is exactly
    # [true, false] — the marker is present on the required slot and ABSENT on
    # the optional one. It establishes the post-image is jointly satisfiable and
    # non-degenerate at the very input the fix is about. The assert is live: a
    # false claim about the same input leaves an unsolved goal (verified
    # out-of-band). The frozen loop follows the assert so the ensures obligation
    # still discharges; the tactic is retuned only to also close the assert goal.
    # =====================================================================
    {
        "id": "admiss-f2p-plan-non-degenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _FIRST,
                  "    assert (with_name_prefix `admiss\n"
                  "      (requiredPlan true false [⟨true, true⟩, ⟨false, true⟩] "
                  "= [true, false]))\n"
                  + _FIRST),
            _PROOF,
            "prove_correct requiredFlags by\n"
            "  loom_solve <;>\n"
            "    (try rw [requiredPlan_drop_step outerRequired requireAll subs i "
            "(by omega) (by omega)]) <;>\n"
            "    simp_all [requiredPlan, subRequired]"),
        "rationale": "REJECT/PASS SOURCE = joint satisfiability & non-degeneracy "
                     "of the post-image at the F2P-shaped input. With the gate "
                     "open and the joint-required disjunct off, a slot that opts "
                     "in AND is required gets the marker while a slot that opts "
                     "in but is NOT required does not — the plan is exactly "
                     "[true, false], not the uniform [true, true] a degenerate "
                     "spec would allow. The in-region assert must discharge "
                     "(else SPEC-UNSATISFIABLE reads as trivially met), and the "
                     "frozen loop keeps the ensures obligation intact.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Every rival is in
    # functional map form so its tester reduces under `decide`.
    # =====================================================================
    {
        # THE F2P discriminator: drop the per-slot `required` conjunct, so every
        # slot that opts in is marked regardless of whether it is itself
        # required. Correct wherever a slot IS required; wrong on the optional
        # slot that opts in.
        "id": "weak-ignore-subfield-required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("outerRequired && (requireAll || s.marksRequired)"),
        "refinement": "a real patch that marked each sub-widget from its own "
                      "opt-in ALONE (dropping the conjunction with the "
                      "sub-field's own required flag) would mark every sub-widget "
                      "that opts in — including the OPTIONAL sub-field. In the "
                      "failing scenario both sub-widgets opt in, so the optional "
                      "one would wrongly carry the required marker; the failing "
                      "test asserts that the optional sub-widget has NO required "
                      "marker, so this would NOT resolve. It diverges precisely "
                      "on the optional-sub-field sub-domain.",
        "rationale": "REJECT from `out = requiredPlan ...`: on a slot with "
                     "marksRequired=true, required=false (gate open, "
                     "requireAll=false) the post-image gives false and the rival "
                     "gives true. Attacks the per-slot `required` conjunct.",
        "witness": _wit(
            "example : requiredFlagsTester true false [⟨false, true⟩] = false "
            ":= by\n  decide"),
        "witness_reference": _LOOPFREE,
    },
    {
        # Drop the per-slot opt-in (`marksRequired`) conjunct, so a slot that is
        # required is marked even if its own sub-widget does not opt into the
        # marker (a hidden-style sub-widget). Correct wherever the slot opts in;
        # wrong on a required slot that does not opt in.
        "id": "weak-ignore-subwidget-optin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("outerRequired && (requireAll || s.required)"),
        "refinement": "a real patch that marked each sub-widget from the "
                      "sub-field's required flag ALONE (dropping the conjunction "
                      "with the sub-widget's own opt-in) would attach the "
                      "required marker to a sub-widget that does not opt into it "
                      "(a hidden-style input), rendering a required marker on a "
                      "widget that must not carry it — an observable regression "
                      "the broad rendering suite covers, so it would NOT resolve.",
        "rationale": "REJECT from `out = requiredPlan ...`: on a slot with "
                     "required=true, marksRequired=false (gate open, "
                     "requireAll=false) the post-image gives false and the rival "
                     "gives true. Attacks the per-slot opt-in (marksRequired) "
                     "conjunct.",
        "witness": _wit(
            "example : requiredFlagsTester true false [⟨true, false⟩] = false "
            ":= by\n  decide"),
        "witness_reference": _LOOPFREE,
    },
    {
        # Drop the overall gate: mark slots on the per-slot rule even when the
        # gate is CLOSED (the field as a whole is not required / the form does
        # not ask for markers). Wrong on the gate-closed regime.
        "id": "weak-drop-outer-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("requireAll || (s.marksRequired && s.required)"),
        "refinement": "a real patch that omitted the overall gate would attach "
                      "required markers even for a field that is not required / a "
                      "form that suppresses the required attribute — emitting the "
                      "marker where the framework guarantees none, a regression "
                      "the existing required-attribute suite covers, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = requiredPlan ...`: with "
                     "outerRequired=false the post-image is all-false (the gate "
                     "suppresses every marker) but the rival (requireAll=true "
                     "here) marks the slot true. Attacks the outerRequired gate "
                     "binder, refuted at outerRequired=false.",
        "witness": _wit(
            "example : requiredFlagsTester false true [⟨false, false⟩] = false "
            ":= by\n  decide"),
        "witness_reference": _LOOPFREE,
    },
    {
        # Drop the joint-required disjunct: in the joint-required regime
        # (requireAll=true) mark slots on the per-slot rule instead of marking
        # every slot. Wrong on the requireAll regime.
        "id": "weak-drop-requireall-regime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("outerRequired && (s.marksRequired && s.required)"),
        "refinement": "a real patch that dropped the joint-required disjunct "
                      "would stop uniformly marking every sub-widget when the "
                      "field requires all its sub-fields jointly, so an "
                      "ordinary jointly-required field would silently lose the "
                      "required marker on sub-widgets whose own flags happen to "
                      "be off — regressing the broad required-attribute "
                      "rendering the existing suite depends on, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = requiredPlan ...`: with requireAll=true "
                     "the post-image marks every slot (gate open) but the rival "
                     "(marksRequired=false, required=false here) gives false. "
                     "Attacks the requireAll disjunct, refuted at requireAll=true.",
        "witness": _wit(
            "example : requiredFlagsTester true true [⟨false, false⟩] = false "
            ":= by\n  decide"),
        "witness_reference": _LOOPFREE,
    },
    {
        # THE pre-fix behaviour: under the open gate, mark EVERY slot uniformly
        # (ignore both the joint-required disjunct and the per-slot flags) — the
        # old unconditional "set the required attribute" path. Wrong on any
        # optional / non-opting slot under the open gate with requireAll off.
        "id": "weak-uniform-prefix-mark",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("outerRequired"),
        "refinement": "this IS the pre-fix behaviour: under the open gate the "
                      "code set the aggregate required attribute uniformly, so "
                      "EVERY sub-widget rendered the required marker regardless of "
                      "its own sub-field. In the failing scenario the optional "
                      "sub-widget would then carry the marker; the failing test "
                      "asserts it does NOT, so the faithful pre-fix does NOT "
                      "resolve — exactly the reported defect.",
        "rationale": "REJECT from `out = requiredPlan ...`: on a slot with "
                     "required=false, marksRequired=false (gate open, "
                     "requireAll=false) the post-image gives false and the "
                     "uniform rival gives true. Distinct from the "
                     "ignore-required rival (which agrees with the post-image at "
                     "this same all-false slot).",
        "witness": _wit(
            "example : requiredFlagsTester true false [⟨false, false⟩] = false "
            ":= by\n  decide"),
        "witness_reference": _LOOPFREE,
    },
    {
        # Order/structure rival: compute the correct per-slot marker for every
        # slot but return the sequence REVERSED. Correct as a multiset, wrong as
        # an ordered per-sub-widget plan. Refuted only on a list whose plan is
        # not a palindrome — varies the `subs` binder to length two.
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    return (subs.map (fun s => subRequired outerRequired "
            "requireAll s)).reverse"),
        "refinement": "a real patch that emitted the per-sub-widget markers in "
                      "the wrong positional order would attach each computed "
                      "marker to the wrong sub-widget, so a required leading "
                      "sub-field and an optional trailing one would render with "
                      "their markers swapped — the failing test pins the marker "
                      "to the FIRST sub-widget and its absence to the SECOND, so "
                      "a positional reversal would NOT resolve.",
        "rationale": "REJECT from `out = requiredPlan ...`: requiredPlan is "
                     "positional, so on a two-slot list whose markers are "
                     "[true, false] the reversed rival returns [false, true]. "
                     "Attacks the traversal-order sub-behaviour; varies the subs "
                     "binder to length two, the only rival refuted on a "
                     "multi-element list.",
        "witness": _wit(
            "example : requiredFlagsTester true false [⟨true, true⟩, "
            "⟨false, false⟩] = false := by\n  decide"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) over a stateful `Result2` +
# per-constituent `subs[k].marker` carrier with fractional heap permissions and
# TWO output slots (out.required_attr and out.disabled_attr). THIS bundle is a
# narrowed carrier: it models ONLY the per-sub-widget required-marker PLAN (the
# returned `List Bool`). The aggregate required slot, the disabled slot, the
# tri-state (-1/0/1) marker encoding, and the fractional list/field permissions
# are stateful / downstream machinery this functional core does not model.
#
#   nagini case                              -> here
#   ---------------------------------------------------------------------
#   pos-control-hoist-disabled-flip-branch   -> pos-inline-unfold-step      PORTED
#                                            -> pos-map-form                 ADDED
#   admissibility-readonly-spine-init-slots  -> admiss-f2p-plan-non-degenerate RE-AIMED
#   frame-mutation-write-field_required      -> (none)                       VACUOUS
#   aggregate-in-regime-a-prepatch-bug       -> weak-uniform-prefix-mark     PORTED
#   partial-domain-ignore-field_required     -> weak-ignore-subfield-required PORTED
#   regime-b-drop-aggregate                  -> weak-drop-requireall-regime  PORTED
#   disabled-slot-drop                       -> (none)             NO COUNTERPART
#   (no sibling)                             -> weak-ignore-subwidget-optin  ADDED
#   (no sibling)                             -> weak-drop-outer-gate         ADDED
#   (no sibling)                             -> weak-reversed-order          ADDED
#
# 4 ported, 1 re-aimed, 1 vacuous, 1 no-counterpart, 4 added = 9 velvet cases.
#
# PORTED (positive control): the nagini positive hoists the independent disabled
#   block and flips the per-constituent branch. The disabled slot is NOT modeled
#   here (see NO COUNTERPART), so the disabled-hoist does not port; the branch
#   reshape's ARGUMENT ("a structurally different faithful impl must verify") is
#   carried by TWO controls — inline-unfolding the per-slot marker helper in the
#   loop (minimal reshape, one extra simp lemma) and a genuinely different
#   algorithm (functional map instead of the backward loop, reproved by a
#   two-case list induction). Both verified to build (EXIT 0).
# RE-AIMED (admissibility): the nagini case re-derives that the precondition
#   admits an F2P-shaped input (readable spine + initial output slots). This
#   method has NO `require` clause, so that probe is vacuous; it is re-aimed at
#   the residual total-domain risk — an UNSATISFIABLE/degenerate post-image — by
#   discharging an in-region assert that the plan at the F2P-shaped input is
#   exactly [true, false] (required slot marked, optional slot NOT), i.e. jointly
#   satisfiable and non-degenerate. Assert is live (a false claim leaves an
#   unsolved goal — verified out-of-band). Verified to build (EXIT 0).
# VACUOUS (frame-mutation): the nagini case is MANDATORY because a constituent
#   input is held at Acc(subs[k].field_required, 1/2) an impl can illegally WRITE
#   (a value-neutral self-assignment). This backend is referentially transparent,
#   has no heap/aliasing, and this bundle declares no `mut` parameter — `subs` is
#   an immutable value with no heap footprint. There is no read-only input to
#   overwrite and no substitute probe to build. Not fabricated (per the porting
#   map: this class is vacuous on Lean/Velvet).
# NO COUNTERPART (disabled-slot-drop): the nagini rival drops the disabled-slot
#   assignment, pinned by a SECOND output clause Implies(field_disabled,
#   out.disabled_attr == 1). This bundle models only the per-sub-widget required
#   PLAN (one returned List Bool); the disabled attribute is a separate,
#   patch-unchanged output the functional core does not carry (mapping.md: the
#   modeled surface is the required-marker loop). There is no disabled slot to
#   drop, so the attack has nothing to land on. Omitted because the modeled
#   surface excludes that behaviour, NOT because it was hard to prove.
# PORTED (the three value rivals): aggregate-prepatch -> weak-uniform-prefix-mark
#   (mark every slot uniformly under the open gate — the pre-fix path);
#   partial-domain-ignore-field_required -> weak-ignore-subfield-required (drop
#   the per-slot required conjunct — the F2P discriminator); regime-b-drop ->
#   weak-drop-requireall-regime (drop the joint-required disjunct so the
#   requireAll regime loses its uniform marking). Each carries a machine-checked
#   witness that ELABORATES against the functional rival and is REFUTED against
#   the loop-free `_LOOPFREE` reference (`witness_reference`), which verifies
#   against the same frozen spec. Gold itself decides nothing here — its witness
#   build fails by STUCK REDUCTION, which is not a refutation (see the MEASURED
#   CARRIER FACT in the docstring) — so the reference is what supplies the second
#   half of the discrimination.
# ADDED (3 rivals with no sibling): the nagini spec splits its clauses across two
#   output slots and a tri-state encoding; the velvet spec fuses the whole rule
#   into `subRequired oR rA s = oR && (rA || (marksRequired && required))`, which
#   exposes TWO further independent sub-behaviours the nagini split did not
#   isolate — the overall gate (weak-drop-outer-gate, refuted at
#   outerRequired=false) and the per-slot opt-in conjunct
#   (weak-ignore-subwidget-optin, refuted at marksRequired=false). A third
#   (weak-reversed-order) attacks the positional traversal, the only structural
#   clause the single returned list carries; it is the only rival that varies the
#   `subs` binder beyond length one. All three are real divergences with
#   machine-checked witnesses, not fabricated wrongness.
#
# BINDER / CLAUSE COVERAGE. The sole ensures clause fuses four independent
#   sub-behaviours; each is attacked by >=1 reject rival AND defended by both
#   positives + the admissibility assert:
#     * outerRequired gate      -> weak-drop-outer-gate       (refuted at oR=false)
#     * requireAll disjunct     -> weak-drop-requireall-regime(refuted at rA=true)
#     * per-slot marksRequired  -> weak-ignore-subwidget-optin
#     * per-slot required       -> weak-ignore-subfield-required
#     * uniform (both per-slot) -> weak-uniform-prefix-mark
#     * positional traversal    -> weak-reversed-order        (2-element list)
#   Binder variation across the reject witnesses: outerRequired takes both values
#   (false in the gate rival, true elsewhere); requireAll takes both values (true
#   in the gate + requireall rivals, false elsewhere); subs takes length one
#   (five rivals) and length two (the order rival); the per-slot flags required
#   and marksRequired each take both values across the witness points. No binder
#   is pinned at a single value, so a rival mishandling any one input would be
#   caught. The witnesses probe SIX distinct input points.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py) and this
# bundle declares no axiom (the transformation is modeled deeply), so there is
# nothing to probe; the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
