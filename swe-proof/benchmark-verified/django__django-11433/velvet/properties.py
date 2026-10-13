"""properties.py — G-PBT falsification battery for django__django-11433 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct assignCleanedValues`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a finite list of model fields, as a
value-assignment step observes them). The single obligation is

    assignCleanedValues (fields : List Field) return (out : List Bool)
        ensures out = applyPlan fields

where ``applyPlan`` maps, element by element and in order,
``applies f = f.eligible && !(f.modelHasDefault && f.noIncomingValue &&
f.cleanedValueEmpty)``: for each field, hand its cleaned value to that field's
write step iff the field is one the form may assign at all AND it is NOT the case
that the model declares a fallback, the payload omitted the field, and the
cleaned value is itself empty. ``fields`` is the sole input binder; each element
carries four booleans (``eligible`` / ``modelHasDefault`` / ``noIncomingValue`` /
``cleanedValueEmpty``). The load-bearing content is the WIDENED skip guard: a
field with a fallback that was omitted from the payload but whose cleaned value
is NON-empty is now handed off, where the pre-image left the fallback standing.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``Field`` is a structure with ``DecidableEq``, and ``applies`` / ``applyPlan``
are concrete ``def``s in the ``pure`` region (the ``axioms`` region declares
nothing). So each rival's violation reduces to a decidable equality of concrete
values, and a ``decide`` witness at a small literal input discriminates. The
reject lane is therefore fully expressible on this carrier — no NO-REJECT-LANE
collapse. The method carries NO ``require`` clause (pre-conditions region empty),
so the domain is total.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the loop collapsed to the closed form the
    post-image names; the per-field decision bound to a local inside the loop)
    must still verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the nagini sibling self-asserts that an F2P-shaped input is
    admissible under its half-permission Requires. This bundle declares NO
    ``require`` clause, so there is no precondition to admit; the residual risk
    on this transparent carrier is instead a DEGENERATE post-image — one that
    does not actually demand a hand-off when the cleaned value is non-empty while
    still deferring when it is empty. ``admiss-grounded`` discharges an in-region
    assert pinning BOTH branches of the per-field decision at an F2P-shaped
    input; the impl is kept verbatim so the method's own obligation still
    discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling carries this
    MANDATORY because its four inputs are held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean and Velvet are
    referentially transparent: ``fields`` is an immutable value (declared
    read-only, not ``mut``), there is no heap and no aliasing, so there is no
    read-only input to mutate and no substitute probe to build. Not fabricated —
    reported as an omission in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image ``applyPlan fields`` is grounded
    in the actual input carrier (directive 8), not an axiomatized oracle; the
    ``axioms`` region is empty. The nagini sibling documents the same fact with
    its ``pos-control-echo-inline`` case; that positive is folded into the
    ordinary soundness controls here (there is no wrong echo to reject).
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired behaviour on some sub-domain and MUST be rejected:
    the widened-guard sub-domain (the literal pre-patch bug), the eligibility gate
    dropped, a first-field special-case, and the internal boolean combination of
    the three deferral conjuncts. Each is a loop-free closed form (so its tester
    kernel-reduces) with a machine-checked refutation witness.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches it through Velvet's own tester
machinery: ``assignCleanedValuesTester args = false`` says the extracted
program's result violates the postcondition at that concrete input, checked in a
file whose ``prove_correct`` block has been stripped (no tactic script can mask
the verdict). The frozen program contains a ``while`` loop, whose fixpoint does
not reduce under the kernel's ``decide``; every reject rival is reshaped into a
LOOP-FREE closed form, so ITS tester ``decide``s while the SAME witness applied
to the loop-bearing frozen solution cannot reduce and so fails to elaborate. The
discrimination is thus structural, not a tactic-tuning artifact. (Verified out of
band: each witness builds green against its rival and red against the frozen
solution.)

WITNESS PLACEMENT. The four rejects probe four DISTINCT input points, so the
input binder ``fields`` — and the four booleans its elements carry — is genuinely
varied rather than pinned. Across the four witnesses ``eligible`` takes both
values, ``modelHasDefault`` both, ``noIncomingValue`` both, and
``cleanedValueEmpty`` both (the load-bearing binder is not held fixed); the list
length ranges over 1 and 2. Both effects of the deferral guard are attacked
(a field wrongly deferred AND a field wrongly handed off), the eligibility gate
is attacked, and the per-index traversal is attacked at a two-element list.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
notions the guard reads (``has_default``, the payload-omission check, the
empty-value membership) are A-references validated by axiom_check.py (G-AX's
job), not consumed contracts. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11433"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the field list. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`).
_IMPL = """    let mut result : List Bool := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = applyPlan (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := applies f :: result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "assignCleanedValues impl region drifted from expected text"

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let f := fields[i - 1]!
      result := applies f :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop body drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut result : List Bool := []"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this to a bare `loom_solve`; the tactic body is
# elided from the spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct assignCleanedValues by
  loom_solve
  rw [applyPlan_drop_step fields i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `assignCleanedValuesTester args = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
_TESTER = (
    "extract_program_for assignCleanedValues\n"
    "prove_precondition_decidable_for assignCleanedValues\n"
    "prove_postcondition_decidable_for assignCleanedValues\n"
    "derive_tester_for assignCleanedValues\n\n"
)


def _F(eligible, modelHasDefault, noIncomingValue, cleanedValueEmpty):
    """A concrete Field literal for a witness input point."""
    def b(x):
        return "true" if x else "false"
    return ("{eligible := %s, modelHasDefault := %s, noIncomingValue := %s, "
            "cleanedValueEmpty := %s}") % (
                b(eligible), b(modelHasDefault), b(noIncomingValue),
                b(cleanedValueEmpty))


def _witness(fields_literal):
    return _TESTER + (f"example : assignCleanedValuesTester {fields_literal} "
                      "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = applyPlan fields`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same per-field decision list; the
        # loop-specific proof is retuned to a bare `loom_solve` since the impl
        # now matches the post-image syntactically. This is also the "echo the
        # grounded post-image" positive (nagini pos-control-echo-inline): the
        # post-image is a total function of the input, so echoing it is the
        # CORRECT answer, not a cheat — there is no wrong echo to reject.
        "module": _swap(
            _swap(_BASE, _IMPL, "    return (applyPlan fields)"),
            _PROOF, "prove_correct assignCleanedValues by\n  loom_solve"),
        "rationale": "a loop-free impl that returns the per-field decision list "
                     "directly must satisfy `out = applyPlan fields`; a correct "
                     "reshape of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Exercises the obligation from a "
                     "maximally different (loop-free) control-flow shape, and "
                     "documents that the only available echo (the grounded "
                     "post-image) is the truthful one.",
    },
    {
        "id": "pos-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-field decision to a local `d` inside the loop
        # instead of prepending the expression directly. Same value flow; the
        # loop and the front-recursive invariant are unchanged, so the frozen
        # proof still closes untouched. (Sibling: pos-control-helper — bind the
        # decision to a local and append it.)
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let f := fields[i - 1]!\n"
            "      let d : Bool := applies f\n"
            "      result := d :: result\n"
            "      i := i - 1"),
        "rationale": "binding the per-field decision to a local before prepending "
                     "it computes the same list element-for-element, with the loop "
                     "and invariant unchanged, so the frozen proof closes and "
                     "`out = applyPlan fields` still holds; a correct reshape must "
                     "verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so the nagini
    # sibling's precondition-admissibility probe has no direct counterpart. The
    # residual risk on this transparent carrier is that the post-image is
    # DEGENERATE at the interesting point (a spec no impl can meet reads like a
    # spec every impl meets). This case discharges an in-region assert at an
    # F2P-shaped point, establishing that the post-image really does demand a
    # HAND-OFF when the field has a fallback, was omitted, but its cleaned value
    # is NON-empty (the widened-guard case the fix adds) AND a SKIP when the
    # cleaned value is empty. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live (a false claim
    # about the same point leaves an unsolved goal), and the proof's alternation
    # gains one `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `assert\n"
                "      (applyPlan [" + _F(True, True, True, False) + "]\n"
                "         = [true] ∧\n"
                "       applyPlan [" + _F(True, True, True, True) + "]\n"
                "         = [false]))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct assignCleanedValues by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [applyPlan_drop_step fields i (by omega) (by omega)]; "
            "simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: it demands a HAND-OFF when a field with a "
                     "fallback was omitted but its cleaned value is NON-empty (the "
                     "widened-guard case the fix adds) and a SKIP when the cleaned "
                     "value is empty. The in-region assert must discharge (else the "
                     "obligation is degenerate / PRECOND-TOO-STRONG); the impl is "
                     "kept verbatim so `out = applyPlan fields` still verifies. "
                     "(Sibling: admiss-f2p-shaped, re-aimed from precondition "
                     "admissibility to post-image non-degeneracy since this "
                     "backend declares no require clause.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-prepatch-drop-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: the deferral guard drops the third conjunct
        # (the cleaned-value-empty check), so a field with a fallback that was
        # omitted from the payload is deferred REGARDLESS of whether its cleaned
        # value is empty. Correct everywhere except the widened-guard sub-domain
        # — the exact case the fix adds.
        "module": _swap(
            _BASE, _IMPL,
            "    return (fields.map (fun f =>\n"
            "      f.eligible && !(f.modelHasDefault && f.noIncomingValue)))"),
        "refinement": "this is the literal pre-image: a field with a fallback that "
                      "was omitted from the payload is deferred even when its "
                      "cleaned value is non-empty, so the model fallback stands "
                      "instead of the submitted non-empty value — exactly the "
                      "behaviour the failing test catches (a defaulted, omitted "
                      "field whose cleaned value is non-empty must be written). It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = applyPlan fields`: at a one-element list "
                     "whose field has a fallback, was omitted, and has a NON-empty "
                     "cleaned value, the post-image demands the hand-off (`applies "
                     "= true`) while the rival defers it (false). Refuted on the "
                     "widened-guard sub-domain (`cleanedValueEmpty` false). "
                     "(Sibling: reject-prepatch-drop-value-empty.)",
        "witness": _witness("[" + _F(True, True, True, False) + "]"),
    },
    {
        "id": "weak-drop-eligibility-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the eligibility gate: decide the hand-off purely from the deferral
        # guard, ignoring whether the field is one the form may assign at all.
        # Correct on every eligible field; diverges on the INELIGIBLE sub-domain,
        # where it hands off a field that must be skipped.
        "module": _swap(
            _BASE, _IMPL,
            "    return (fields.map (fun f =>\n"
            "      !(f.modelHasDefault && f.noIncomingValue && "
            "f.cleanedValueEmpty)))"),
        "refinement": "dropping the eligibility gate hands the cleaned value to a "
                      "field the form may NOT assign — a non-editable field, an "
                      "auto key, a field absent from cleaned data, or one excluded "
                      "by the form's field selection. Writing such values regresses "
                      "the pre-existing tests that assert those fields are left "
                      "untouched; it would NOT resolve.",
        "rationale": "REJECT from `out = applyPlan fields`: `applies` forces "
                     "`false` on any ineligible field, so the post-image demands a "
                     "SKIP there while the rival can hand off. Refuted on the "
                     "ineligible sub-domain (`eligible` false) — the sub-domain the "
                     "prepatch rival agrees with gold on. The witness also holds "
                     "`cleanedValueEmpty` at true, so this binder is not pinned at "
                     "false across the reject set. (Sibling: "
                     "reject-drop-selected-gate.)",
        "witness": _witness("[" + _F(False, False, False, True) + "]"),
    },
    {
        "id": "weak-first-field-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # A first-field special-case: the head field is always SKIPPED regardless
        # of its decision; every later field is decided correctly. Diverges from
        # `applyPlan` at index 0 whenever the head field should be handed off, and
        # the per-index correspondence the list carrier fixes is what catches it.
        "module": _swap(
            _BASE, _IMPL,
            "    return (match fields with\n"
            "      | [] => []\n"
            "      | _ :: fs => false :: (fs.map (fun f => applies f)))"),
        "refinement": "a real patch that special-cased the first iterated field to "
                      "never hand off its cleaned value would, on a form whose "
                      "single relevant field is the head, leave the fallback and "
                      "NOT resolve; and would regress tests that write the first "
                      "field. It would NOT resolve.",
        "rationale": "REJECT from `out = applyPlan fields`: the rival forces the "
                     "head decision to false, so it disagrees with `applyPlan` at "
                     "index 0 whenever the head field should be handed off. Refuted "
                     "at a TWO-element list whose head should be handed off (so "
                     "`fields.length` is varied beyond one and the per-index "
                     "correspondence is attacked); the second element is decided "
                     "correctly, isolating the head miss. (Sibling: "
                     "reject-partial-first-element.)",
        "witness": _witness("[" + _F(True, False, False, False) + ", "
                            + _F(True, True, True, False) + "]"),
    },
    {
        "id": "weak-or-combined-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Right conjuncts, wrong COMBINATION: the deferral guard combines the
        # three deferral conditions with OR instead of AND, so a field is deferred
        # as soon as ANY one holds rather than only when all three hold together.
        # Attacks whether the post-image pins the exact boolean shape of the guard,
        # not merely that the three conditions are all read.
        "module": _swap(
            _BASE, _IMPL,
            "    return (fields.map (fun f =>\n"
            "      f.eligible && !(f.modelHasDefault || f.noIncomingValue || "
            "f.cleanedValueEmpty)))"),
        "refinement": "combining the three deferral conditions with OR defers a "
                      "field whenever it merely HAS a fallback (or was merely "
                      "omitted, or merely has an empty cleaned value), instead of "
                      "only when all three hold together. It would leave the "
                      "fallback for a field the form should write (e.g. a "
                      "defaulted field the payload DID supply), regressing the save "
                      "tests; it would NOT resolve.",
        "rationale": "REJECT from `out = applyPlan fields`: at a field with a "
                     "fallback that was NOT omitted (`modelHasDefault` true, "
                     "`noIncomingValue` false), `applies` demands the hand-off "
                     "(the AND-guard is false) while the OR-guard defers it. "
                     "Refuted at that point; distinct from the prepatch rival, "
                     "which agrees with gold there. Attacks the internal boolean "
                     "combination of the guard. (ADDED beyond the sibling to pin "
                     "the guard's exact shape.)",
        "witness": _witness("[" + _F(True, True, False, False) + "]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (2
# soundness positives, 1 admissibility, 4 uniqueness rivals — one of which is a
# mandatory frame-mutation rival) plus an EMPTY AXIOM lane. The sibling contracts
# one function, `construct_writes`, over four half-permission read-only list
# inputs; this bundle contracts one method, `assignCleanedValues`, over a LIST of
# `Field` structures with a deep `applyPlan` fold and no axioms. The two surfaces
# model the SAME per-field decision (hand off the cleaned value iff eligible and
# NOT (fallback and omitted and empty)), so the value-rival port is near-1:1 with
# two carrier consequences: the frame-mutation rival is vacuous here, and the
# list carrier lets a first-field special-case be attacked at a length-2 list.
#
#   sibling case                     kind          -> here                     disposition
#   -------------------------------------------------------------------------------------
#   pos-control-helper               soundness     -> pos-letbind              PORTED
#   pos-control-echo-inline          soundness     -> pos-closed-form          FOLDED
#   admiss-f2p-shaped                admissibility -> admiss-grounded          RE-AIMED
#   reject-prepatch-drop-value-empty uniqueness    -> weak-prepatch-drop-conjunct  PORTED
#   reject-partial-first-element     uniqueness    -> weak-first-field-flip    PORTED
#   reject-drop-selected-gate        uniqueness    -> weak-drop-eligibility-gate  PORTED
#   reject-frame-mutate-selected     uniqueness    -> (none)                   VACUOUS
#   (—)                              uniqueness    -> weak-or-combined-guard    ADDED
#   AXIOM_TESTS (none)               axiom         -> (none)                   N/A (G-AX)
#
# PORTED (pos-control-helper -> pos-letbind): the sibling binds the @Pure helper
#   to a local and appends it. Here the closest loop-preserving reshape binds the
#   per-field decision `applies f` to a local inside the loop, keeping the loop
#   and the front-recursive invariant so the frozen proof closes unchanged.
# FOLDED (pos-control-echo-inline -> pos-closed-form): the sibling documents that
#   the grounded post-image has no WRONG echo — echoing it is correct. That fact
#   is carried by pos-closed-form, which returns the grounded post-image
#   `applyPlan fields` directly (a maximally different loop-free shape) and must
#   verify. No separate "inline echo" case is needed on this carrier.
# RE-AIMED (admiss-f2p-shaped -> admiss-grounded): the sibling establishes that an
#   F2P-shaped input is admissible under its half-permission Requires. This
#   backend declares NO `require` clause, so there is no precondition to admit;
#   the sharper residual risk on this transparent carrier is a DEGENERATE
#   post-image, so the case is re-aimed to a live in-region assert pinning BOTH
#   branches of the per-field decision (hand off on defaulted+omitted+NON-empty,
#   skip on defaulted+omitted+empty) at the F2P point.
# PORTED (the three value rivals): reject-prepatch-drop-value-empty ports directly
#   to weak-prepatch-drop-conjunct (the literal pre-patch guard, refuted on the
#   widened-guard sub-domain — the F2P discriminator). reject-drop-selected-gate
#   ports to weak-drop-eligibility-gate (refuted on the ineligible sub-domain).
#   reject-partial-first-element ports to weak-first-field-flip; the list carrier
#   lets it be refuted at a length-2 list, isolating the head miss and attacking
#   the per-index correspondence.
# VACUOUS (reject-frame-mutate-selected): the sibling's MANDATORY frame-mutation
#   rival overwrites the half-permission read-only input `selected[i]` before
#   reading it. This backend is referentially transparent and `fields` is declared
#   read-only (not `mut`), so there is no read-only input to overwrite and no
#   substitute probe. Omitted as a genuine carrier fact, NOT fabricated (porting
#   map: this class is vacuous here).
# ADDED (weak-or-combined-guard): the guard reads three deferral conditions and
#   combines them; a rival that combines them with OR instead of AND reads every
#   binder but pins the wrong boolean SHAPE. Refutable at a field that has a
#   fallback but was NOT omitted — a point the prepatch rival agrees with gold on
#   — so it is a distinct near-miss, and it exercises the `noIncomingValue = false`
#   corner the other rivals leave at true.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `fields : List Field`, whose elements carry `eligible`, `modelHasDefault`,
#   `noIncomingValue`, `cleanedValueEmpty`, and one top-level clause,
#   `out = applyPlan fields`, which internally is `eligible && !(modelHasDefault
#   && noIncomingValue && cleanedValueEmpty)` per field. The four reject witnesses
#   probe four DISTINCT input points (pts=4):
#     * weak-prepatch          [F(T,T,T,F)]                — widened-guard sub-domain
#     * weak-drop-eligibility  [F(F,F,F,T)]                — ineligible sub-domain
#     * weak-first-field-flip  [F(T,F,F,F), F(T,T,T,F)]    — head miss, length 2
#     * weak-or-combined-guard [F(T,T,F,F)]                — wrong boolean combination
#   Thus `eligible` ranges over {T,F}, `modelHasDefault` over {T,F},
#   `noIncomingValue` over {T,F}, `cleanedValueEmpty` over {T,F} (the load-bearing
#   binder is NOT pinned), and `fields.length` over {1,2} — none held fixed. Both
#   effects of the guard are attacked (a field wrongly DEFERRED and a field wrongly
#   HANDED OFF), the eligibility gate is attacked, the internal boolean
#   combination is attacked, and the per-index traversal is attacked, so no rival
#   that mishandled only a fixed-value binder could slip through.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (the unchanged notions the
# guard reads are A-references validated by axiom_check.py, not consumed
# contracts), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
