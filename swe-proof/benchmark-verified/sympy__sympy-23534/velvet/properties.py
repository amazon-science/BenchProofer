"""properties.py — G-PBT falsification battery for sympy__sympy-23534 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct buildSeq``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against the subject the case names).

WITNESS SUBJECT — the frozen solution CANNOT serve as one here, so every reject
case names a ``witness_reference`` instead. The frozen impl is a ``while`` loop
under ``loom.semantics.choice "demonic"``, so the method's Hoare triple
elaborates to an un-normalised ``wp (forIn Lean.Loop.mk …)`` term that no tactic
reduces; a ``¬ triple …`` witness checked against it fails in ``rcases`` ("is not
an inductive datatype") for EVERY claim, true or false. Measured directly: a
witness asserting the exact INVERSE claim — that the frozen solution is CORRECT
at that input, the opposite of a refutation — fails against the frozen solution
with a byte-identical 400-character signature, while building cleanly against a
reducing impl. So the frozen loop's exit code carries no information about what a
witness claims, and each case is refuted against a VERIFYING straight-line impl
of the same spec (``_REFERENCE``) that does reduce; the gate checks that subject
shares the frozen spec and verifies before using it. Against that subject each
witness fails on a goal about the actual values (``hlen : True`` / ``h : True``
where the equation was PROVED for the correct impl, or a concrete residual such
as ``[SymCls.sym] = buildName "a" SymCls.func``) and still elaborates against its
rival. See the ``_REFERENCE`` comment for the full measurement.

DEFENDED SURFACE (one contracted method):

  buildSeq (names : List String) (cls : SymCls) return (out : List (List SymCls))
    ensures out = expand names cls                    (C1: exact grouped shape)
    ensures ∀ sub ∈ out, ∀ x ∈ sub, x = cls           (C2: every leaf == cls)

  ``expand`` is a front-recursive spec fold: one per-element group per name,
  each group produced by the per-name builder carrying THE SAME requested class.
  The load-bearing clause is C2 — every leaf of every group carries the REQUESTED
  class, never a default kind — which is the whole content of the fix. C1 pins
  the grouped shape (one group per element, in order) via structural equality.

CARRIER NOTE — why this port looks nothing like the django exemplar.

  The per-element builder is an OPAQUE axiom (``buildName : String → SymCls →
  List SymCls``), so ``expand`` is ``noncomputable``. Two consequences drive
  every design choice below:

   1. The ``extract_program_for`` / ``derive_tester_for`` + ``decide`` witness
      route (the django-13658 pattern) is UNAVAILABLE: extraction fails to
      compile a program whose postcondition depends on a noncomputable term
      (``compiler IR check failed ... depends on 'expand', which has no
      executable code``). So each reject ``witness`` here refutes the method's
      Hoare triple DIRECTLY at a concrete input — ``¬ triple True (buildSeq …)
      (fun out => <the two ensures conjuncts>)`` — reduced through
      ``triple_pure`` for the straight-line rivals, checked in a file whose
      ``prove_correct`` block has been stripped so no tactic script interferes.
   2. Opacity does NOT narrow what is discriminable, and an earlier revision of
      this file wrongly claimed it did. Nothing has to COMPUTE an opaque term:
      a witness may state its refutation at a point described by HYPOTHESIS
      (``example (hne : buildName "a" .sym ≠ []) : ¬ triple …``), and the gate's
      consistency probe then confirms those hypotheses are satisfiable — which
      an opaque term makes easy, since no tactic can derive ``False`` from
      ``buildName "a" .sym ≠ []``. The model-collapsing argument (``buildName _
      _ = []`` makes the rival agree with gold) shows only that the refutation
      cannot be UNCONDITIONAL; it does not block a conditioned one, because the
      hypothesis excludes exactly the collapsing model. Measured: an error
      living wholly INSIDE a group is refutable this way — a wrong opaque class
      (S-wrong-class-forward), a wrong per-position name (S-name-from-head), and
      a per-group multiplicity defect (S-group-overproduce) each carry a witness
      here that elaborates against its rival and fails against the reference. So
      all four of C1's dimensions (group count, group order, per-group content,
      per-position name) and C2's tag clause are attacked, not just the outer
      length.

ADVERSARIAL READ of the weakness classes (others justified-N/A in `assessment`):
  * FRAME-MUTATION — VACUOUS. The nagini sibling's mandatory frame-mutation
    rival writes to a read-only container held at a fractional heap permission.
    This backend is referentially transparent: every parameter is an immutable
    value, this bundle declares no `mut` binder on an input, there is no heap and
    no aliasing. No read-only input to overwrite, no permission system to trip.
    Not fabricated (per the porting map, dropped rather than replaced).
  * WRONG-CLASS / grounded-tag — APPLIES, twice. The nagini headline rival
    forwards a default class into the per-element recursion; both of its faithful
    counterparts are carried here. S-wrong-class-forward routes the build through
    the per-element builder under a CONCRETE default class (`buildName n .sym`),
    which is the direct pre-image shape; S-wrong-class-leaf emits a concrete
    default-kind leaf without consulting the builder at all. The first is refuted
    by a hypothesis-conditioned witness (`buildName "a" .sym ≠ []`, so the group
    has an element, which `buildName_cls` pins to `.sym` against a requested
    `.func`); the second by a literal-leaf witness needing no hypothesis.
  * PARTIAL-DOMAIN / structure-flattening — APPLIES on both the outer shape and
    per-group content. Group COUNT is refuted via C1's length by S-empty (zero
    groups) and S-head-only (one group, tail dropped). The nagini per-entry
    MULTIPLICITY attack is ported as S-group-overproduce (the first group carries
    one extra object, C1 refuted by that group's length), and the per-position
    NAME binding as S-name-from-head (every group built from `names[0]`, C1
    refuted at the second group under the hypothesis that two distinct names
    build differently). Neither needed a computable builder.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. C1/C2 are grounded in `expand`
    (a fold over the actual inputs `names`/`cls`), not an opaque answer-key; the
    "echo" available is the wrong-tag leaf, which is exactly S-wrong-class-leaf.
  * ADMISSIBILITY — APPLIES, and is now carried (S-admiss-f2p-input). An earlier
    revision recorded this lane N/A because the method carries no `require`
    (precondition ≡ True). That reason is not sufficient: on a TOTAL carrier the
    analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
    exactly an F2P-shaped input, and nothing else in this battery would notice.
    Both positives are proven GENERICALLY, by induction over an arbitrary
    `names`, so neither ever instantiates the obligation at a concrete input; a
    spec degenerate at the input the issue is about would pass every other case
    here. S-admiss-f2p-input discharges both `ensures` conjuncts at that concrete
    request by evaluation, as `have`s, before closing the frozen obligation
    verbatim.
  * DIVERGENCE / non-termination — the bundle sets
    `loom.semantics.termination "total"`, so the verifier does discharge a
    termination obligation and this class IS shippable in principle. Measured,
    though, that no witness-bearing rival can be landed for it here. An impl whose
    loop carries no `decreasing` clause is rejected before anything else by
    `Decreasing annotations are required in total correctness semantics`, and that
    error breaks the WITNESS file too (exit 1 even for a trivially true
    `(1:Nat) + 1 = 2`), so the rival build — the half that must succeed — cannot
    pass and the case would record `witness-unproven` rather than a refutation. An
    impl that keeps a `decreasing` clause but never decreases (`i := i`) is
    likewise rejected, on the measure's own goal (`Tactic `rewrite` failed`). Both
    rejections are real and attributable to the termination obligation, but
    neither is expressible as a spec-refutation witness, since the defect is in
    the termination proof rather than in a value the postcondition constrains.
    Recorded as a TOOLING limit of the witness protocol, not as a spec hole.

WITNESS PLACEMENT / coverage. The six reject witnesses sit at DISTINCT input
points and vary BOTH binders: `names` ranges over a one-element and a
two-element vector (so the group-count clause C1 is probed at two lengths), and
`cls` ranges over `.sym` and `.func` (so the class-tag clause C2 is probed with
a non-default requested class, which is the sub-domain where the fix bites).
Two of the six condition on a hypothesis about the opaque builder rather than
on a literal, which is what reaches the inside of a group; each such hypothesis
is a single disequality the gate's consistency probe cannot refute (checked:
the probe fails to close `False` against both the frozen solution and the
reference, so the refuted input exists).

POSITIVE CONTROL. Two are carried. S-pos-inline-binding is a data-flow reshape
that keeps the frozen proof script working verbatim. S-pos-map is the stronger
one: it abandons the loop for `names.map`, so the frozen script no longer
applies at all and the obligation is REPROVEN from scratch (two inductions over
`names`, consuming `buildName_cls` and `expand_cons`) with no new lemma and a
byte-identical statement. A positive control whose impl is definitionally the
frozen one tests nothing; S-pos-map is not definitionally equal to the frozen
loop (its two `ensures` goals arrive at `loom_solve` in `List.map` form, not in
the loop's `forIn`/invariant form), so it genuinely exercises SPEC-TOO-STRONG.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23534"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The whole loop-based impl body (text strictly between -- impl-start and
# -- impl-end). Replaced wholesale by the structure-attacking rivals, which
# abandon the loop entirely.
_IMPL = (
    "    let mut result : List (List SymCls) := []\n"
    "    let mut i := names.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ names.length\n"
    "      invariant result = expand (names.drop i) cls\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let n := names[i - 1]!\n"
    "      result := buildName n cls :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The two loop-body lines that bind `n` then prepend its group. The positive
# control inlines `n` into the prepend — a data-flow reshape that keeps the
# result definitionally identical, so the frozen tactic script still closes.
_INNER = (
    "      let n := names[i - 1]!\n"
    "      result := buildName n cls :: result\n"
)


# ---- witness helper. The spec is a `method` contract whose postcondition is
# ---- noncomputable, so a witness reaches it NOT through the tester machinery
# ---- (which cannot extract a noncomputable program) but by refuting the
# ---- method's Hoare triple directly at a concrete input. Checked in a file
# ---- whose `prove_correct` block has been stripped.
def _witness(names_lit, cls_lit, refute_body, hyp=""):
    """`¬ triple True (buildSeq names cls) (C1 ∧ C2)`, optionally CONDITIONED.

    `hyp` is a binder group on the witness's own `example` head. It is how a
    refutation reaches INSIDE a group: the per-element builder is opaque, so no
    literal input decides a group's content, but a single disequality about it
    (`buildName "a" .sym ≠ []`) names the sub-domain where the rival diverges
    without assuming anything false. The gate additionally probes each such
    witness for consistency (`example <hyp> : False`), and an opaque atom makes
    that probe fail as it should — the refuted input genuinely exists.
    """
    head = f" {hyp}" if hyp else ""
    return (
        f"example{head} : ¬ (triple (l := Prop) True "
        f"(buildSeq {names_lit} {cls_lit})\n"
        f"    (fun out => out = expand {names_lit} {cls_lit} ∧ "
        f"∀ sub ∈ out, ∀ x ∈ sub, x = {cls_lit})) := by\n"
        f"  unfold buildSeq\n"
        f"  simp only [triple_pure, le_Prop_eq, true_implies]\n"
        f"{refute_body}"
    )


# The frozen tactic script. A positive control that abandons the loop must
# REPROVE the obligation, so it replaces this body wholesale (permitted: the
# `prove_correct` header and the contract itself are untouched, only the tactic
# script differs, which `variant_scope` allows and `same_spec` elides).
_PROOF = (
    "prove_correct buildSeq by\n"
    "  loom_solve\n"
    "  rw [expand_drop_step names cls i (by omega) (by omega)]\n"
    "  simp_all"
)

# The reproof a straight-line `names.map` impl needs: `loom_solve` presents both
# `ensures` goals in `List.map` form, so the frozen script does not apply and the
# obligation is discharged by two inductions over `names` from `expand_cons` and
# the axiom contract alone.
_MAP_PROOF = (
    "prove_correct buildSeq by\n"
    "  loom_solve\n"
    "  · intro sub hsub x hx\n"
    "    induction names with\n"
    "    | nil => simp at hsub\n"
    "    | cons n ns ih =>\n"
    "      simp only [List.map_cons, List.mem_cons] at hsub\n"
    "      rcases hsub with h | h\n"
    "      · subst h; exact buildName_cls n cls x hx\n"
    "      · exact ih h\n"
    "  · induction names with\n"
    "    | nil => simp [expand]\n"
    "    | cons n ns ih => simp only [List.map_cons, expand_cons, ih]"
)

# ---- WITNESS REFERENCE — why every reject case below names one. -------------
#
# The frozen impl is a `while` loop under `loom.semantics.choice "demonic"`, so
# the method's Hoare triple elaborates to an un-normalised
# `wp (forIn Lean.Loop.mk …) …` term that NO tactic reduces. A witness stated as
# `¬ triple …` therefore cannot be evaluated against the frozen solution at all:
# its `rintro` hits a `wp` application and reports
#
#   Tactic `rcases` failed: `a✝ : True → wp (do let r ← forIn Lean.Loop.mk …)
#     fun out => out = expand ["a"] SymCls.sym ∧ …` is not an inductive datatype
#
# which is a TACTIC failure, not a refutation — the kernel never looked at the
# claim. Measured (attack B′, the forgery test): a witness asserting the exact
# INVERSE claim (`out ≠ expand …`, i.e. that the frozen solution is CORRECT
# there — the opposite of a refutation) fails against the frozen solution with a
# byte-identical 400-character signature, while building cleanly (exit 0) against
# a reducing impl. A type-revealing probe (`exact (hcon : Nat)`) confirms the
# cause: against the frozen loop the hypothesis has type
# `{True}do let r ← forIn Lean.Loop.mk …`, an unreduced program, whereas against
# a straight-line impl it has the concrete type
# `[] = expand ["a"] SymCls.sym ∧ …`. So the frozen solution's exit code carries
# NO information about what a witness claims, and a rejection checked against it
# attests to the carrier's irreducibility rather than to the spec.
#
# This is the same defect class the gate screens for as `witness-undecided`, but
# it arrives through a shape none of those screens match (`rcases … is not an
# inductive datatype` is neither a stuck `decide`, a missing `Decidable`
# instance, a `Dependent elimination failed`, nor an `Application type mismatch`
# on the loop term), so the automatic fallback to a verifying positive never
# fires and the case has to name its subject explicitly.
#
# The repair the gate prescribes: refute each witness against a `witness_reference`
# instead — a VERIFYING impl of the SAME frozen spec that DOES reduce. That is
# sound for exactly the reason the frozen solution was supposed to be: an impl
# the verifier accepts cannot violate its own spec, so a genuine "the spec is
# violated at this input" claim must still fail there. The gate checks rather
# than trusts it (shares the frozen spec, and verifies) before using it.
#
# Against THIS reference every witness below fails on a goal about the actual
# values — `hlen : True` / `h : True` where the equation was PROVED for the
# correct impl, or a concrete residual equation such as
# `[SymCls.sym] = buildName "a" SymCls.func` — and the same witness elaborates
# against its rival. That pair is the refutation; the frozen loop's exit code is
# not evidence either way.
_REFERENCE = _swap(
    _swap(_BASE, _IMPL, "    return names.map (fun n => buildName n cls)\n"),
    _PROOF, _MAP_PROOF)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG. The intermediate
    # `let n := names[i-1]!` binding is inlined into the prepend: the produced
    # `result` is DEFINITIONALLY identical, so `loom_solve` leaves the same
    # single loop-body goal and the frozen tactic script (`rw
    # [expand_drop_step …]; simp_all`) discharges it unchanged. No new lemma is
    # introduced and the obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "S-pos-inline-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INNER,
            "      result := buildName names[i - 1]! cls :: result\n"),
        "rationale": "Inlining the per-element name binding into the group "
                     "prepend leaves the accumulated `result` definitionally "
                     "identical, so both C1 (`out = expand names cls`) and C2 "
                     "hold and the frozen proof closes without change. A correct "
                     "reshape that failed to verify would mean the spec is "
                     "SPEC-TOO-STRONG on the impl's data-flow shape.",
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — the load-bearing one. The loop is
    # abandoned for a single `names.map`, so the impl is NOT definitionally the
    # frozen one: `loom_solve` presents both `ensures` goals in `List.map` form
    # (`List.map (fun n => buildName n cls) names = expand names cls` and the
    # membership clause over the same term) rather than as the loop's invariant
    # step, and the frozen script's `rw [expand_drop_step …]` does not even
    # typecheck there. The obligation is therefore REPROVEN from scratch: two
    # inductions over `names`, consuming `expand_cons` and the axiom contract
    # `buildName_cls`. No new top-level lemma, no `sorry`, statement byte-
    # identical. This is the case that actually tests SPEC-TOO-STRONG — a
    # faithful correct impl in a genuinely different shape must still be
    # provable, and if it were not, the spec would be over-fitted to the frozen
    # loop's syntactic form.
    # =====================================================================
    {
        "id": "S-pos-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": "A CORRECT impl in a genuinely different shape (a single "
                     "`names.map` over the per-element builder, no loop and no "
                     "accumulator) that must verify. Unlike the inline-binding "
                     "control this is NOT definitionally equal to the frozen "
                     "impl — the frozen tactic script does not apply to the "
                     "goals it produces — so the obligation is reproven by "
                     "induction on `names` from `expand_cons` and the axiom "
                     "contract alone. Both C1 and C2 hold. Rejection here would "
                     "mean the spec is SPEC-TOO-STRONG, over-fitted to the "
                     "frozen loop's shape rather than to the grouped result.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete
    # input and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "S-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Produce ZERO groups regardless of input. Attacks C1 via the outermost
        # structure: the result length is 0 where the spec demands one group per
        # element name.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : List (List SymCls) := []\n"
            "    return result\n"),
        "refinement": "Returning no groups at all has no gold counterpart (the "
                      "gold builds exactly one object-group per element name). A "
                      "faithful real patch that emitted an empty container could "
                      "not reproduce the documented grouped output for a "
                      "multi-element request, so the value the failing test "
                      "deconstructs would be absent and the assertion would "
                      "error. It would NOT resolve.",
        "rationale": "REJECT from C1 (`out = expand names cls`): for a "
                     "one-element input `expand` has length 1 while the rival "
                     "returns length 0. Verifying would be SPEC-TOO-WEAK on the "
                     "group-count structure. Refuted at `names=[\"a\"]`, "
                     "`cls=.sym` via the list length.",
        "witness": _witness(
            "[\"a\"]", "SymCls.sym",
            "  rintro ⟨h, -⟩\n"
            "  have hlen := congrArg List.length h\n"
            "  rw [expand_cons, expand_nil] at hlen\n"
            "  simp at hlen\n"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "S-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Build ONLY the first element's group and drop the rest. Correct on a
        # single-element input; wrong on any longer vector. Attacks C1 via the
        # group count on the multi-element sub-domain.
        "module": _swap(
            _BASE, _IMPL,
            "    match names with\n"
            "    | [] => return []\n"
            "    | n :: _ => return [buildName n cls]\n"),
        "refinement": "Keeping only the first element's group and discarding the "
                      "tail has no gold counterpart (the gold builds a group for "
                      "EVERY element). A faithful real patch that returned a "
                      "single group for a multi-element request would collapse "
                      "the documented per-element grouping, so the test that "
                      "deconstructs the result into separate per-element groups "
                      "would fail. It would NOT resolve.",
        "rationale": "REJECT from C1: for a two-element input `expand` has "
                     "length 2 while the rival returns length 1. Correct on a "
                     "one-element input, so it isolates the multi-element "
                     "sub-domain that S-empty does not distinguish. Verifying "
                     "would be SPEC-TOO-WEAK on the group count. Refuted at "
                     "`names=[\"a\", \"b\"]`, `cls=.func` via the list length.",
        "witness": _witness(
            "[\"a\", \"b\"]", "SymCls.func",
            "  rintro ⟨h, -⟩\n"
            "  have hlen := congrArg List.length h\n"
            "  rw [expand_cons, expand_cons, expand_nil] at hlen\n"
            "  simp at hlen\n"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "S-wrong-class-leaf",
        "kind": "uniqueness",
        "expect": "reject",
        # One group per element (right group COUNT), but each group is a
        # CONCRETE default-kind leaf `[SymCls.sym]` rather than one produced
        # under the requested class. This is the on-carrier analogue of the
        # prepatch bug: the requested class is dropped in favour of the default
        # leaf kind. Attacks C2, the load-bearing tag clause.
        "module": _swap(
            _BASE, _IMPL,
            "    return names.map (fun _ => [SymCls.sym])\n"),
        "refinement": "Emitting a fixed default-kind leaf per element instead of "
                      "one carrying the requested class mirrors the prepatch bug "
                      "(the requested class not reaching the per-element build). "
                      "Its faithful real counterpart makes a request for a "
                      "non-default class produce default-kind objects, so the "
                      "test asserting the produced object's class equals the "
                      "requested class FAILS. It would NOT resolve.",
        "rationale": "REJECT from C2 (`∀ sub ∈ out, ∀ x ∈ sub, x = cls`): with a "
                     "requested class of `.func`, the rival's leaf is `.sym`, "
                     "violating the tag clause. This is the strongest clause — "
                     "the whole content of the fix — and no other rival attacks "
                     "it. Verifying would be SPEC-TOO-WEAK on the requested "
                     "class. Refuted at `names=[\"a\"]`, `cls=.func` via the "
                     "concrete leaf.",
        "witness": _witness(
            "[\"a\"]", "SymCls.func",
            "  rintro ⟨-, h2⟩\n"
            "  have := h2 [SymCls.sym] (by simp) SymCls.sym (by simp)\n"
            "  simp at this\n"),
        "witness_reference": _REFERENCE,
    },

    # ---- rivals whose defect lives INSIDE a group. Each conditions its witness
    # ---- on one disequality about the opaque builder, which is what names the
    # ---- sub-domain where the rival diverges from gold; the gate's consistency
    # ---- probe confirms the hypothesis is satisfiable, so the refuted input
    # ---- exists. An unconditional witness could NOT work here (a model with
    # ---- `buildName _ _ = []` makes these rivals agree with gold), which is a
    # ---- reason to condition, not a reason to drop the rival.
    {
        "id": "S-wrong-class-forward",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image shape: one group per element, each built by the REAL
        # per-element builder, but forwarding the CONCRETE default class instead
        # of the requested `cls`. Unlike S-wrong-class-leaf the builder is still
        # consulted, so the defect is invisible in the outer structure and lives
        # entirely inside a group. Attacks C2 (and C1).
        "module": _swap(
            _BASE, _IMPL,
            "    return names.map (fun n => buildName n SymCls.sym)\n"),
        "refinement": "Building each element's group under the DEFAULT class "
                      "rather than the requested one has no gold counterpart: the "
                      "gold threads the requested class into every per-element "
                      "build. Its faithful real counterpart makes a request for a "
                      "non-default class produce default-kind objects at every "
                      "position, so the test asserting a produced object's class "
                      "equals the requested class FAILS. It would NOT resolve.",
        "rationale": "REJECT from C2: under the hypothesis that the group built "
                     "for \"a\" at the default class is non-empty, that group has "
                     "a member which `buildName_cls` pins to `.sym`, while C2 "
                     "demands every member equal the requested `.func`. Attacks "
                     "the tag clause THROUGH the builder, which is the shape the "
                     "fix is about; S-wrong-class-leaf attacks it with a literal "
                     "leaf that bypasses the builder entirely. Verifying would be "
                     "SPEC-TOO-WEAK on class forwarding. Refuted at "
                     "`names=[\"a\"]`, `cls=.func`.",
        "witness": _witness(
            "[\"a\"]", "SymCls.func",
            "  rintro ⟨-, h2⟩\n"
            "  obtain ⟨x, hx⟩ := List.exists_mem_of_ne_nil _ hne\n"
            "  have hsym := buildName_cls \"a\" SymCls.sym x hx\n"
            "  have hfunc := h2 (buildName \"a\" SymCls.sym) (by simp) x hx\n"
            "  rw [hsym] at hfunc\n"
            "  exact absurd hfunc (by decide)\n",
            hyp="(hne : buildName \"a\" SymCls.sym ≠ [])"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "S-name-from-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Right group COUNT, right requested class, but every group is built
        # from the FIRST name instead of its own. Attacks C1's per-position name
        # binding — a dimension no length-based witness can see.
        "module": _swap(
            _BASE, _IMPL,
            "    return names.map (fun _ => buildName names[0]! cls)\n"),
        "refinement": "Expanding the FIRST element's name once per position has "
                      "no gold counterpart (the gold expands each element's own "
                      "name). A faithful real patch that did this would return "
                      "the first name's objects in every group, so the existing "
                      "assertion that a multi-element request deconstructs into "
                      "each element's OWN objects FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1 (`out = expand names cls`): at "
                     "`names=[\"a\",\"b\"]` the rival's second group is the "
                     "expansion of \"a\" while `expand` demands the expansion of "
                     "\"b\". Refuted under the hypothesis that the two names "
                     "build differently — the sub-domain where the defect is "
                     "observable at all. This is the only rival attacking the "
                     "per-position NAME binding; the group count and the class "
                     "tag are both correct here, so no other case's witness "
                     "would fire. Verifying would be SPEC-TOO-WEAK on which name "
                     "each group is built from.",
        "witness": _witness(
            "[\"a\", \"b\"]", "SymCls.func",
            "  rintro ⟨h, -⟩\n"
            "  rw [expand_cons, expand_cons, expand_nil] at h\n"
            "  simp only [List.map_cons, List.map_nil, List.cons.injEq, "
            "and_true] at h\n"
            "  exact hne h.2\n",
            hyp="(hne : buildName \"a\" SymCls.func ≠ buildName \"b\" "
                "SymCls.func)"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "S-group-overproduce",
        "kind": "uniqueness",
        "expect": "reject",
        # Right group count, right names, right class tag on every object, but
        # the FIRST group carries one EXTRA object. The per-group multiplicity
        # attack: correct on every other group, so it isolates a partial-domain
        # defect strictly inside one group. Attacks C1; C2 still holds of it,
        # which is what makes it a distinct probe.
        "module": _swap(
            _BASE, _IMPL,
            "    match names with\n"
            "    | [] => return []\n"
            "    | n :: ns =>\n"
            "      return (buildName n cls ++ [cls]) :: "
            "ns.map (fun m => buildName m cls)\n"),
        "refinement": "Over-producing the first group by one object has no gold "
                      "counterpart (the gold appends exactly the per-element "
                      "builder's own expansion for each element). A faithful real "
                      "patch that emitted an extra object in the first group "
                      "would make a multi-object range request produce one object "
                      "too many there, so the existing assertion pinning that "
                      "group's exact contents FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1: the first group is the builder's expansion "
                     "with one extra object appended, so it is longer than "
                     "`expand`'s corresponding group by exactly one. Note C2 "
                     "still HOLDS of this rival (the extra object carries the "
                     "requested class), so the tag clause cannot reject it — only "
                     "the structural equality can, which is precisely why this "
                     "case is not redundant with the two wrong-class rivals. "
                     "Correct on every group but the first, isolating a "
                     "partial-domain defect. Refuted at `names=[\"a\"]`, "
                     "`cls=.func` via that group's length.",
        # Projected through `List.headD` rather than through `List.cons.injEq`.
        # The original form leaned on a `simp only [List.cons.injEq, and_true]`
        # normalisation of the outer equality that the RIVAL's `::` shape happens
        # to admit; against a reducing `List.map` impl that same step reports
        # "`simp` made no progress" — a tactic gap, not a refutation, so the
        # witness could not be checked against a subject that decides anything.
        # Taking the FIRST group's length via `headD` is a projection both shapes
        # normalise, so the claim is what fails. Measured with a type-revealing
        # probe (`exact (hlen : Nat)`): against the reference `hlen : True` (the
        # equation was PROVED for the correct impl), against the rival
        # `hlen : (buildName "a" SymCls.func).length + (0 + 1)
        #         = (buildName "a" SymCls.func).length` (it was not). That pair
        # is the refutation.
        "witness": _witness(
            "[\"a\"]", "SymCls.func",
            "  rintro ⟨h, -⟩\n"
            "  have hlen := congrArg (fun l => (List.headD l []).length) h\n"
            "  rw [expand_cons, expand_nil] at hlen\n"
            "  simp only [List.map_cons, List.map_nil, List.headD_cons, "
            "List.length_append, List.length_cons, List.length_nil] at hlen\n"
            "  omega\n"),
        "witness_reference": _REFERENCE,
    },

    # =====================================================================
    # ADMISSIBILITY — the lane the first port dropped as N/A on the argument
    # that the method carries no `require`, so there is no precondition to be
    # too strong. That reason is not sufficient: on a TOTAL carrier the analogue
    # of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    # F2P-shaped input — a spec that no impl could discharge there would still
    # pass every other lane in this battery (the two positives are proven
    # generically, by induction over an arbitrary `names`, so neither of them
    # ever instantiates the obligation at a concrete input at all).
    #
    # This case discharges both `ensures` conjuncts AT the concrete F2P-shaped
    # request — a two-element sequence of range names under a NON-default
    # requested class, the input shape from the reported behaviour — as two
    # `have`s proven by evaluation (`simp only [expand_cons, expand_nil]` for
    # the grouped shape, the pure lemma for the tag clause), and only then
    # closes the frozen obligation verbatim. Both `have`s are `clear`ed before
    # `loom_solve` so they cannot contribute to the frozen proof: the case still
    # verifies for exactly the frozen reason, and what it ADDS is the evidence
    # that the spec is satisfiable at the input that matters. If either
    # conjunct were degenerate there, this case would fail while every other
    # case in the battery still passed.
    #
    # In scope: no new top-level declaration, no new axiom, no `sorry`; only the
    # `prove_correct` tactic body differs, which `variant_scope` permits and
    # `same_spec` elides. Checked with variant_problems -> [].
    # =====================================================================
    {
        "id": "S-admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct buildSeq by\n"
            "  have hadm : expand [\"q:2\", \"u:2\"] SymCls.func\n"
            "      = [buildName \"q:2\" SymCls.func, "
            "buildName \"u:2\" SymCls.func] := by\n"
            "    simp only [expand_cons, expand_nil]\n"
            "  have hadm2 : ∀ sub ∈ expand [\"q:2\", \"u:2\"] SymCls.func,\n"
            "      ∀ x ∈ sub, x = SymCls.func := "
            "expand_cls [\"q:2\", \"u:2\"] SymCls.func\n"
            "  clear hadm hadm2\n"
            "  loom_solve\n"
            "  rw [expand_drop_step names cls i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "PRECOND-TOO-STRONG probe, in the form the analogue takes on "
                     "a total carrier. Before closing the frozen obligation "
                     "verbatim, the proof discharges BOTH `ensures` conjuncts at a "
                     "concrete in-domain request — a two-element sequence of range "
                     "names under a non-default requested class, the input shape "
                     "the reported behaviour is about — by evaluation: C1's grouped "
                     "shape reduces to exactly one group per element name, and C2's "
                     "tag clause follows from the pure lemma. Both `have`s are "
                     "`clear`ed before `loom_solve`, so the obligation still closes "
                     "for the frozen reason and the case adds evidence rather than "
                     "changing the proof. Rejection here would mean the obligation "
                     "is unsatisfiable at exactly the input the spec exists to "
                     "constrain — the total-carrier form of a precondition that "
                     "excludes a legitimate input — which the two positives cannot "
                     "detect, since both are proven generically over an arbitrary "
                     "`names` and never instantiate the obligation anywhere.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) plus 1 AXIOM_TESTS probe. This
# bundle models only the purely-functional core — a single method `buildSeq`
# whose per-element builder is an OPAQUE axiom — so the discriminable surface is
# narrower than nagini's deep A-reference model of the per-element expansion.
# Every sibling case is accounted for below.
#
#   sibling case            -> here
#   -------------------------------------------------------------------------
#   S-pos                   -> S-pos-inline-binding        PORTED (data-flow
#                                                          reshape)
#                            + S-pos-map                   STRENGTHENED (loop
#                                                          abandoned; obligation
#                                                          REPROVEN)
#   S-admiss                -> S-admiss-f2p-input          PORTED (re-aimed: the
#                                                          total-carrier analogue
#                                                          — the obligation
#                                                          discharged AT the
#                                                          F2P-shaped input)
#   S-frame-mut             -> (none)                      VACUOUS
#   S-wrong-class           -> S-wrong-class-forward       PORTED (the pre-image
#                                                          shape: default class
#                                                          forwarded THROUGH the
#                                                          builder)
#                            + S-wrong-class-leaf          RE-EXPRESSED (literal
#                                                          leaf, builder bypassed)
#   S-flat                  -> S-empty / S-head-only       RE-AIMED at group COUNT
#   S-partial-firstentry    -> S-group-overproduce         PORTED (first group
#                                                          carries one extra
#                                                          object)
#   ax-sound-expand         -> (none)                      G-AX's job; dropped
#
# 5 ported (one of them re-aimed onto the total-carrier admissibility analogue),
# 1 re-expressed, 2 re-aimed onto the group-count clause, 1 positive strengthened,
# 2 dropped (1 vacuous, 1 out-of-lane). No case was dropped because its proof was
# hard, and none because the carrier is opaque: see the correction below.
#
# CORRECTION (an earlier revision of this file). Three sibling rivals — the
#   class-forwarding one, the per-group-multiplicity one, and the per-position
#   name binding — were recorded here as NOT DISCRIMINABLE on this carrier, on
#   the argument that the opaque `buildName` admits a model (`buildName _ _ = []`)
#   under which each rival agrees with gold. The argument is sound but proves
#   only that no UNCONDITIONAL witness exists; it does not follow that no witness
#   exists. A witness may state its refutation at a point described by
#   HYPOTHESIS, and one disequality about the opaque builder (`buildName "a"
#   .sym ≠ []`, or `buildName "a" c ≠ buildName "b" c`) excludes exactly the
#   collapsing model while remaining satisfiable — the gate's consistency probe
#   cannot derive `False` from it, precisely because the term is opaque. All
#   three rivals are therefore carried, each with a witness that elaborates
#   against its rival and fails against the frozen solution.
#
# VACUOUS (S-frame-mut): the sibling writes to a read-only container carrying a
#   fractional heap permission. This backend is referentially transparent: every
#   parameter is an immutable value, no `mut` input binder, no heap, no aliasing.
#   No read-only input to overwrite, no permission system to trip. No substitute
#   fabricated.
# RE-AIMED (S-admiss -> S-admiss-f2p-input): the method carries no `require`
#   clause, so the sibling's precondition-discharge shape has no literal analogue.
#   That is NOT a reason to drop the lane, and an earlier revision of this file
#   used it as one. On a total carrier the analogue of PRECOND-TOO-STRONG is the
#   obligation being unsatisfiable at exactly an F2P-shaped input, and the claim
#   that the positives already cover it is false: both are proven generically by
#   induction over an arbitrary `names`, so neither instantiates the obligation at
#   any concrete input, and a spec degenerate at the input the issue is about
#   would pass both. S-admiss-f2p-input closes that by discharging both `ensures`
#   conjuncts at the concrete request by evaluation, as `have`s, before closing
#   the frozen obligation verbatim.
# RE-AIMED (S-empty, S-head-only): the sibling's flattening rival attacks the
#   grouped shape; the outer group COUNT is the part of it C1 pins by length, and
#   S-empty (zero groups) / S-head-only (one group, tail dropped) refute it at two
#   distinct lengths. The per-group half of that same sibling case is carried
#   separately by S-group-overproduce.
#
# BINDER / CLAUSE COVERAGE. C1 (`out = expand names cls`) is attacked along four
#   independent dimensions: group COUNT (S-empty: 0 vs 1; S-head-only: 1 vs 2),
#   per-group CONTENT length (S-group-overproduce), per-position NAME binding
#   (S-name-from-head), and class forwarding (S-wrong-class-forward, which breaks
#   C1 and C2 together). C2 (`∀ sub ∈ out, ∀ x ∈ sub, x = cls`) — the load-bearing
#   tag clause — is attacked by S-wrong-class-leaf (literal leaf) and
#   S-wrong-class-forward (through the builder). S-group-overproduce and
#   S-name-from-head SATISFY C2 and are rejected by C1 alone, which is what makes
#   them non-redundant. Both clauses are defended by two positive controls, one of
#   which reproves the obligation in a shape the frozen script cannot close.
#   Binder `names` is varied over `["a"]` and `["a","b"]`; binder `cls` over
#   `.sym` and `.func` — the non-default class is exactly the sub-domain where the
#   tag clause bites. 6 reject cases at distinct input/defect points.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; `buildName`/`buildName_cls`
#   are validated there (axiom_check.py), and this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
