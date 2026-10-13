"""properties.py — G-PBT falsification battery for django__django-12858 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives with a byte-identical statement)
and swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against a
subject known to satisfy the spec — here the shared loop-free
``witness_reference`` rather than the frozen solution, for the reason set out
under WITNESS MECHANICS below.

DEFENDED SURFACE (one contracted method that decides whether a single dotted
ordering reference is invalid, by walking the chain of its parts left-to-right
against a schema). The schema is supplied as four FREE-INPUT accessors and the
reference as a seed model plus a list of parts:

  checkOrderingRef
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform : Field → Part → Bool) (hasLookup : Field → Part → Bool)
    (cls0 : Model) (parts : List Part) return (out : Bool)
    ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts

``orderingRefInvalid`` is a fully-unfolded ``def`` in the ``pure`` region — a
left fold of ``stepWalk`` over ``parts`` from ``initState cls0``, reading off the
accumulated flag. There is NO opaque answer key to echo: pinning
``out = orderingRefInvalid ...`` IS the work. The single load-bearing clause
folds several independent behaviours over ``parts``:

  * the per-part RESOLUTION SPLIT: the alias part resolves to the model's
    identity field directly; any other part is resolved by ``lookup``; a
    resolved field either descends into its related model (relation) or steps
    the chain off the model graph (non-relation);
  * the FAIL-TO-RESOLVE decision (``flagOnUnresolved``): a part that fails to
    resolve invalidates the reference UNLESS it is an admissible suffix of the
    last resolved field — a registered TRANSFORM of it OR a registered LOOKUP of
    it — with the escape hatch unavailable when NO field has resolved yet
    (``last = none`` ⇒ flag);
  * the TRAVERSAL fold: the reference is invalid iff SOME part flags it, so the
    whole verdict is the disjunction over every visited part.

Every one of these sub-behaviours is attacked by some reject rival below, and
the reject witnesses vary the accessor inputs (``lookup`` resolving vs always
failing vs descending; ``hasTransform``/``hasLookup`` true vs false), the seed
carrier (``parts`` of length one and two, ``isAlias`` true and false), and the
traversal position (offender first vs last), so no sub-behaviour and no input
binder is left pinned at one value.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS here. The nagini sibling carries this
    class as MANDATORY because its three index-aligned inputs each hold a
    fractional heap permission (``Acc(...,1/2)``) a rival could illegally demand
    at full strength and overwrite. Lean and Velvet are referentially
    transparent: every input is an immutable value, this bundle declares no
    ``mut`` parameter over any input, and there is no heap and no aliasing — so
    there is no read-only input to overwrite and no substitute probe to build.
    Not fabricated (per the porting map: this class is vacuous on Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class: the post-image is a total,
    fully-unfolded function of the method's own inputs (``orderingRefInvalid`` /
    ``stepWalk`` / ``flagOnUnresolved`` are concrete ``def``s in the ``pure``
    region; the ``axioms`` region is empty — the schema accessors are FREE
    INPUTS with no constraining axiom, not an answer key), so there is nothing to
    echo. The honest grounded controls (a correct restructured impl + an
    admissibility non-degeneracy assert) are the sibling's directive-2
    substitute, carried here.
  * PARTIAL-DOMAIN / VALUE — the core attacks. The nagini sibling's per-row
    decision divergences port onto the per-part decision here: drop the
    registered-lookup escape (the exact pre-patch defect), drop the
    registered-transform escape (its mirror), collapse both, or relax the
    no-field-yet arm; plus traversal / resolution-split rivals the deeper carrier
    admits (skip the last visited part, ignore the alias resolution, ignore the
    relation descent).

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` CONTRACT with
FUNCTION-TYPED accessor arguments, not a bare predicate, so a witness reaches it
through Velvet's own tester machinery: ``checkOrderingRefTester lookup aliasField
hasTransform hasLookup cls0 parts = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. Each reject rival is written as a straight-line COMPUTABLE form (a
``parts.foldl`` over a local ``step`` lambda, or a ``foldl`` over a truncated
list) whose extracted program DOES reduce: with the four accessors instantiated
to concrete ``decide``-able lambdas the whole tester computes to a literal.

THE FROZEN SOLUTION CANNOT SERVE AS THE WITNESSES' SECOND SUBJECT, and this is
the one substantive correction this battery carries over its first authoring.
The frozen impl computes the verdict with a ``while`` loop; under
``loom.semantics.choice "demonic"`` that loop's fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold. So ``decide`` against the
frozen tester is stuck for EVERY claim, true or false — measured here as

    error: Tactic `decide` failed for proposition
      checkOrderingRefTester … = false
    because its `Decidable` instance … did not reduce to `isTrue` or `isFalse`.

That is a build failure carrying NO information: the kernel never evaluated the
claim, so a forged witness asserting the rival is CORRECT would clear both halves
just as well. A battery resting on it attests to nothing, which is why the gate
reports ``witness-undecided`` and refuses the case.

The repair is the documented one: every reject case names a shared
``witness_reference`` — ``_LOOPFREE`` below, the same spec with the loop replaced
by the ``parts.foldl`` it is the imperative form of. It is loop-free, so it DOES
reduce; the gate checks it shares the frozen spec and VERIFIES before refuting
any witness against it, and an impl the verifier accepts cannot violate its own
spec, so a genuine witness must still fail there. Measured on the reference the
same nine witnesses fail with

    error: Tactic `decide` proved that the proposition … = false is false

— a real decided verdict, not a stuck one. ``_LOOPFREE`` is ALSO shipped as an
``expect="verify"`` positive (``pos-loopfree-fold``), so the battery itself
records that loop-freeness verifies and is therefore not what any rival is being
rejected for.

Both halves were checked out-of-band with ``scripts/lean_verify.sh`` for every
reject case: the witness elaborates against the rival (exit 0) and is decided
FALSE against the reference (exit 1). Every witness states its refutation at
LITERAL accessor lambdas and literal inputs — no witness binds a hypothesis, so
there is no consistency obligation to satisfy.

DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (1 loop here, measure ``parts.length - i``). A rival that loops
without a measure is refused outright (``Decreasing annotations are required in
total correctness semantics``), and a rival that supplies a CONSTANT measure to
dodge that is refused on the measure's own ``decreasing_1`` goal, re-measured
on this bundle with a real build. Divergence therefore does not discharge the
``ensures`` clauses vacuously. It is still not shipped as a G-PBT reject case,
and the reason is the witness contract rather than a spec weakness. A reject
case must carry a witness that ELABORATES against the rival, and the rival's
module does not compile at all: the descent obligation fails at the ``method``
itself, ahead of any appended tester. Measured through the gate's own
That is the shape with NO measure. A rival that CARRIES a measure which does
not decrease is refused at the ``prove_correct`` site instead, which the
witness file strips, so that module does elaborate; but its post-image is then
an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise to
a value a concrete-input tester can decide. Both shapes therefore land
``witness-unproven``.
``_check_witness``, even ``example : True := trivial`` comes back
``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and would
fail the whole battery rather than pass a case. That is the right behavior: a
diverging impl has no output at any input, so there is no value for a witness
to disagree with, and its rejection is a judgement of the termination
obligation rather than a postcondition violation at a point. Recorded as
REJECTED-BY-SPEC and not expressible as a witnessed case, which is neither a
spec hole nor a battery gap.

AXIOM lane: EMPTY (``meta.json`` declares no ``axiom`` and no A-reference deep
model; the walk is modeled DEEPLY over the four free-input accessors). There is
no axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12858"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). ----

# The whole frozen impl body (loop + invariants). Rivals replace it with a
# straight-line computable form (a `parts.foldl` over a local `step`, or a fold
# over a truncated list) so their extracted program reduces under `decide`.
_IMPL = (
    "    let mut st : WalkState := initState cls0\n"
    "    let mut i := 0\n"
    "    while i < parts.length\n"
    "      invariant i ≤ parts.length\n"
    "      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)\n"
    "      done_with i = parts.length\n"
    "      decreasing parts.length - i\n"
    "    do\n"
    "      let p := parts[i]!\n"
    "      st := stepWalk lookup aliasField hasTransform hasLookup st p\n"
    "      i := i + 1\n"
    "    return st.2.2\n"
)

# The single loop-body assignment (for the positive control, which keeps the
# loop shape and only restructures how the next state is computed).
_STEP_ASSIGN = (
    "      let p := parts[i]!\n"
    "      st := stepWalk lookup aliasField hasTransform hasLookup st p\n"
    "      i := i + 1\n"
)

# The first line of the impl body — an anchor to PREPEND an in-region assert
# before, keeping the frozen loop body intact after it.
_IMPL_HEAD = "    let mut st : WalkState := initState cls0\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct checkOrderingRef by\n"
    "  loom_solve\n"
    "  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>\n"
    "    have hi : i < parts.length := by omega\n"
    "    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,\n"
    "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
    "  all_goals simp_all [orderingRefInvalid]\n"
)


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# THE SHARED WITNESS REFERENCE (`witness_reference` on every reject case).
#
# The frozen impl's `while` loop elaborates through `Classical.choice` under
# `loom.semantics.choice "demonic"`, so `decide` against its tester is STUCK for
# every claim regardless of truth (`witness-undecided`): the frozen side's exit
# code discriminates nothing. This is the same spec with the loop collapsed to
# the `parts.foldl` it is the imperative form of — the direct denotation of the
# postcondition's own right-hand side — so it is loop-free and DOES reduce.
#
# Only the impl region and the `prove_correct` tactic body differ from the frozen
# file, so it shares the frozen spec (checked: `variant_problems` clean). With the
# loop gone the two loop invariants are gone with it, so the frozen script's
# `invariant_2` case no longer exists and the tactic body is trimmed to the
# `loom_solve` + `simp_all` that remains. It VERIFIES (checked out-of-band, exit
# 0), which the gate independently re-checks before refuting any witness against
# it — an impl that failed everything would refute every witness, honest or
# forged. Shipped as an expect="verify" positive too (`pos-loopfree-fold`).
_LOOPFREE = _swap(
    _swap(
        _BASE, _IMPL,
        "    return (parts.foldl "
        "(stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)).2.2\n"),
    _PROOF,
    "prove_correct checkOrderingRef by\n"
    "  loom_solve\n"
    "  all_goals simp_all [orderingRefInvalid]\n")


# ---- straight-line rival template. Inlines the whole per-part step as a local
# ---- `step` lambda whose fail-to-resolve decision `fou` is the attacked knob,
# ---- then folds it over `parts`. The extracted program is a plain fold, so with
# ---- concrete accessor lambdas the tester reduces under `decide`. ----
def _rival_fou(fou_body: str) -> str:
    step = (
        "    let step := fun (st : WalkState) (p : Part) =>\n"
        "      let cur := st.1\n"
        "      let last := st.2.1\n"
        "      let flag := st.2.2\n"
        f"      let fou : Bool := {fou_body}\n"
        "      match cur with\n"
        "      | none => ((none : Option Model), last, flag || fou)\n"
        "      | some m =>\n"
        "          if p.isAlias then\n"
        "            let f := aliasField m\n"
        "            (if f.isRel then some f.relModel else none, some f, flag)\n"
        "          else\n"
        "            match lookup m p with\n"
        "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
        "            | none => (some m, last, flag || fou)\n"
        "    return (parts.foldl step (initState cls0)).2.2\n"
    )
    return _impl(step)


# ---- witness preamble. Reaches the method's postcondition through Velvet's own
# ---- tester machinery. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. This method has no
# ---- `require` clause, so every probed input is admissible and the tester
# ---- reaches the postcondition rather than vacuously passing. ----
_TESTER = (
    "extract_program_for checkOrderingRef\n"
    "prove_precondition_decidable_for checkOrderingRef\n"
    "prove_postcondition_decidable_for checkOrderingRef\n"
    "derive_tester_for checkOrderingRef\n\n"
)


def _witness(lookup, alias, htrans, hlook, cls0, parts) -> str:
    return _TESTER + (
        "example :\n"
        "    checkOrderingRefTester\n"
        f"      ({lookup})\n"
        f"      ({alias})\n"
        f"      ({htrans})\n"
        f"      ({hlook})\n"
        f"      {cls0}\n"
        f"      {parts} = false := by\n"
        "  decide\n"
    )


# Concrete accessor / field literals (spelled out at every witness point).
_NONREL = "{ isRel := false, relModel := 0 }"       # a resolved non-relation field
_REL1 = "{ isRel := true, relModel := 1 }"          # a relation field descending into model 1
_ALIAS_F = f"fun (_ : Model) => ({_NONREL} : Field)"  # the identity field (constant)
_F_FALSE = "fun (_ : Field) (_ : Part) => false"      # accessor never true
# resolve part named 0 to a non-relation field, everything else fails to resolve
_LK_RESOLVE0 = (
    f"fun (_ : Model) (p : Part) => if p.name = 0 then (some {_NONREL} : Option Field) else none")
_LK_NONE = "fun (_ : Model) (_ : Part) => (none : Option Field)"
# part 0 -> relation into model 1; part 1 -> non-relation; else fail
_LK_DESCEND = (
    f"fun (_ : Model) (p : Part) => if p.name = 0 then (some {_REL1} : Option Field) "
    f"else if p.name = 1 then (some {_NONREL} : Option Field) else none")
# a MODEL-SENSITIVE resolver: part 0 resolves to a non-relation field ONLY when
# the current model is 1 (keyed on the seed threaded from cls0), else fails.
_LK_MODEL1 = (
    f"fun (m : Model) (p : Part) => if m = 1 && p.name = 0 then (some {_NONREL} : Option Field) else none")
# an identity field that is itself a RELATION descending into model 1, so the
# VALUE `aliasField` returns (not merely "some field") is load-bearing.
_ALIAS_REL = f"fun (_ : Model) => ({_REL1} : Field)"
# an alias part followed by a field of the model the alias descends into.
_PARTS_ALIAS_THEN = "[{ name := 9, isAlias := true }, { name := 0, isAlias := false }]"

# Two-part chain whose first part resolves (name 0) and second fails (name 1) —
# the "resolved field, then an unresolved trailing suffix" shape.
_PARTS_SUFFIX = "[{ name := 0, isAlias := false }, { name := 1, isAlias := false }]"
# A single trailing part that fails to resolve with no prior field (last = none).
_PARTS_LONE = "[{ name := 5, isAlias := false }]"
# A single part named 0 (resolvable by the model-sensitive resolver at model 1).
_PARTS_LONE0 = "[{ name := 0, isAlias := false }]"
# A single alias part.
_PARTS_ALIAS = "[{ name := 9, isAlias := true }]"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. The frozen loop threads `stepWalk` opaquely; this variant
    # INLINES the per-part step (spelling out the resolution split and the
    # fail-to-resolve decision, with the registered-transform OR registered-lookup
    # escape restored inline) inside the same forward loop, keeping every loop
    # invariant byte-identical. The inlined step is definitionally equal to
    # `stepWalk`, so the invariant still holds; the frozen proof gains a single
    # `simp only [stepWalk, flagOnUnresolved]` to reconcile the inlined shape with
    # the folded `stepWalk` in the invariant. Verified to build.
    # =====================================================================
    {
        "id": "pos-inline-step",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _STEP_ASSIGN,
                "      let p := parts[i]!\n"
                "      let cur := st.1\n"
                "      let last := st.2.1\n"
                "      let flag := st.2.2\n"
                "      let fou : Bool := match last with\n"
                "        | none => true\n"
                "        | some f => !(hasTransform f p) && !(hasLookup f p)\n"
                "      st := match cur with\n"
                "        | none => (none, last, flag || fou)\n"
                "        | some m =>\n"
                "            if p.isAlias then\n"
                "              let f := aliasField m\n"
                "              (if f.isRel then some f.relModel else none, some f, flag)\n"
                "            else\n"
                "              match lookup m p with\n"
                "              | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
                "              | none => (some m, last, flag || fou)\n"
                "      i := i + 1\n"),
            _PROOF,
            "prove_correct checkOrderingRef by\n"
            "  loom_solve\n"
            "  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>\n"
            "    have hi : i < parts.length := by omega\n"
            "    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,\n"
            "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
            "    simp only [stepWalk, flagOnUnresolved]\n"
            "  all_goals simp_all [orderingRefInvalid]\n"),
        "rationale": "inlining the per-part step (the resolution split plus the "
                     "fail-to-resolve decision, with the escape cleared on a "
                     "registered transform OR a registered lookup of the last "
                     "resolved field) is definitionally equal to the folded "
                     "`stepWalk`, so the loop invariant "
                     "`st = (parts.take i).foldl (stepWalk ...) (initState cls0)` "
                     "and hence `out = orderingRefInvalid ...` still hold; every "
                     "invariant is byte-identical, so the frozen proof closes with "
                     "one `simp only [stepWalk, flagOnUnresolved]` reconciling the "
                     "inlined shape. A faithful correct reshape that could NOT "
                     "verify would mean SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) #2 — the WITNESS REFERENCE, shipped as a case
    # in its own right. Every reject case below is refuted against this impl
    # instead of against gold, because gold's `while` loop cannot decide anything
    # (see the module docstring). Shipping it as an expect="verify" case is what
    # keeps that substitution honest: the battery records on its own face that
    # collapsing the loop to the `parts.foldl` it implements VERIFIES, so
    # loop-freeness is demonstrably NOT the property any rival is rejected for —
    # each rival is rejected for its decision content, at the input its witness
    # names. (The gate re-checks this independently before using it as a subject;
    # this case makes the same fact visible to a reader of the manifest.)
    # =====================================================================
    {
        "id": "pos-loopfree-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": "the postcondition's right-hand side IS a fold of `stepWalk` "
                     "over `parts` from `initState cls0`, so returning that fold "
                     "directly — the denotational form of the frozen loop, whose "
                     "invariant `st = (parts.take i).foldl (stepWalk …) …` says "
                     "exactly that the loop computes it — satisfies "
                     "`out = orderingRefInvalid …` immediately, and the obligation "
                     "closes without the frozen script's inductive `invariant_2` "
                     "step (which no longer exists, the loop being gone). MUST "
                     "verify: it is the reference every reject witness is refuted "
                     "against, so a failure here would invalidate the whole reject "
                     "lane rather than merely reporting SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — this method carries NO `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing could
    # exclude an F2P-shaped input. The residual admissibility risk on a total
    # domain is that the post-image is DEGENERATE at the interesting points — a
    # spec no impl can meet reads exactly like a spec every impl meets. This case
    # discharges an in-region assert at two F2P-shaped references: the reference
    # whose trailing part fails to resolve but is a registered LOOKUP of the last
    # field must be judged VALID (not flagged), while a reference whose sole part
    # fails to resolve against no prior field (the escape hatch unavailable) must
    # be judged INVALID (flagged). The two arms genuinely differ, so the
    # obligation is jointly satisfiable and non-trivial. The frozen loop body and
    # its invariants follow the assert verbatim, so the method's own `ensures`
    # still discharges; the proof is retuned only to also close the added assert
    # VC. Verified to build (and a false claim about either point leaves an
    # unsolved goal — verified out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_HEAD,
                "    assert (with_name_prefix `admiss\n"
                "      (orderingRefInvalid\n"
                f"          ({_LK_RESOLVE0})\n"
                f"          ({_ALIAS_F})\n"
                "          (fun (_ : Field) (_ : Part) => false)\n"
                "          (fun (_ : Field) (p : Part) => decide (p.name = 1))\n"
                f"          0 {_PARTS_SUFFIX} = false ∧\n"
                "       orderingRefInvalid\n"
                f"          ({_LK_NONE})\n"
                f"          ({_ALIAS_F})\n"
                "          (fun (_ : Field) (_ : Part) => false)\n"
                "          (fun (_ : Field) (_ : Part) => false)\n"
                f"          0 {_PARTS_LONE} = true))\n"
                + _IMPL_HEAD),
            _PROOF,
            "prove_correct checkOrderingRef by\n"
            "  loom_solve\n"
            "  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>\n"
            "    have hi : i < parts.length := by omega\n"
            "    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,\n"
            "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
            "  all_goals first | exact ⟨by decide, by decide⟩ | simp_all [orderingRefInvalid]\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: a reference whose trailing part fails to "
                     "resolve but is a registered lookup of the last resolved field "
                     "is judged VALID (orderingRefInvalid ... = false), while a "
                     "reference whose sole part fails to resolve with no prior field "
                     "(escape hatch unavailable) is judged INVALID "
                     "(orderingRefInvalid ... = true). The two arms differ, so the "
                     "ensures is not vacuously met. The in-region assert must "
                     "discharge (else a degenerate/unsatisfiable obligation would "
                     "read as trivially met) and the loop body is kept verbatim so "
                     "`out = orderingRefInvalid ...` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # that fails on the frozen loop-solution, and each carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "prepatch-drop-lookup-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch decision: a failed-to-resolve part is exempt only when it
        # is a registered TRANSFORM of the last resolved field, with NO escape for
        # a part that is only a registered LOOKUP of it. This is the exact defect.
        "module": _rival_fou(
            "match last with | none => true | some f => !(hasTransform f p)"),
        "refinement": "this is the pre-patch decision — a trailing part that fails "
                      "to resolve is exempt only when it is a registered transform "
                      "of the last resolved field, with no exemption for a part that "
                      "is only a registered lookup of it. A reference ending in a "
                      "registered-lookup-but-not-transform suffix is then wrongly "
                      "judged invalid, which is exactly the spurious rejection the "
                      "issue reports and the failing test pins (such a reference "
                      "must be accepted). A faithful counterpart dropping the "
                      "registered-lookup exemption would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `flagOnUnresolved` "
                     "clears the flag on a registered transform OR a registered "
                     "lookup of the last field, and this rival clears it only on a "
                     "transform. Refuted at a two-part reference whose first part "
                     "resolves to a non-relation field and whose second part fails "
                     "to resolve but is a registered lookup (not a transform) of "
                     "it: gold judges it VALID (false), the rival INVALID — the "
                     "`hasLookup` binder at its `true` value.",
        "witness": _witness(
            _LK_RESOLVE0, _ALIAS_F, _F_FALSE,
            "fun (_ : Field) (p : Part) => decide (p.name = 1)",
            "0", _PARTS_SUFFIX),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-transform-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror defect: exempt a failed part only when it is a registered LOOKUP,
        # dropping the registered-transform escape.
        "module": _rival_fou(
            "match last with | none => true | some f => !(hasLookup f p)"),
        "refinement": "the mirror defect — a failed-to-resolve part is exempt only "
                      "when it is a registered lookup of the last resolved field, "
                      "dropping the pre-existing registered-transform exemption. A "
                      "reference ending in a registered-transform-but-not-lookup "
                      "suffix (the case that already worked before the change) is "
                      "then wrongly judged invalid, so a legitimately transformed "
                      "reference is spuriously reported — breaking the "
                      "already-passing transform-suffix behaviour. A faithful "
                      "counterpart dropping the transform exemption would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `flagOnUnresolved` "
                     "clears on transform OR lookup; this rival clears only on "
                     "lookup. Refuted at a two-part reference whose second part "
                     "fails to resolve but is a registered transform (not a lookup) "
                     "of the last field: gold judges it VALID (false), the rival "
                     "INVALID — the `hasTransform` binder at its `true` value, a "
                     "point the drop-lookup rival (which clears that suffix) does "
                     "not share.",
        "witness": _witness(
            _LK_RESOLVE0, _ALIAS_F,
            "fun (_ : Field) (p : Part) => decide (p.name = 1)",
            _F_FALSE, "0", _PARTS_SUFFIX),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-both-escapes",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse the escape entirely: any failed-to-resolve part flags the
        # reference, regardless of transform/lookup registration.
        "module": _rival_fou("true"),
        "refinement": "collapsing the exemption entirely flags a reference the "
                      "moment any trailing part fails a plain field resolution, "
                      "even when that part is a registered transform OR a registered "
                      "lookup of the last resolved field. Every registered "
                      "transform/lookup suffix — both the newly-fixed lookup case "
                      "and the already-working transform case — is then spuriously "
                      "reported, so the accepted-reference behaviours the tests pin "
                      "all break. A faithful counterpart removing both exemptions "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `flagOnUnresolved` "
                     "clears on a registered transform OR lookup of the last field; "
                     "this rival never clears. Refuted at its OWN sub-domain — the "
                     "trailing part is registered as BOTH a transform and a lookup "
                     "of the last resolved field — which is the one point where this "
                     "rival is wrong and BOTH of its siblings are right: the "
                     "drop-lookup rival clears on the transform there, the "
                     "drop-transform rival clears on the lookup there, and only the "
                     "collapse-everything rival still flags. Gold judges VALID "
                     "(false), this rival INVALID. This is the ONLY witness holding "
                     "`hasTransform` and `hasLookup` BOTH true, so it also closes "
                     "the both-accessors-registered corner no other witness probes; "
                     "checked out-of-band to be decided FALSE against the reference "
                     "AND against each sibling rival, so it demonstrates the "
                     "sub-domain its rationale claims rather than borrowing "
                     "another rival's point.",
        "witness": _witness(
            _LK_RESOLVE0, _ALIAS_F,
            "fun (_ : Field) (p : Part) => decide (p.name = 1)",
            "fun (_ : Field) (p : Part) => decide (p.name = 1)",
            "0", _PARTS_SUFFIX),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "relax-no-field-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the `last = none` arm of the fail-to-resolve decision: when NO
        # field has resolved yet, DON'T flag (return false) — losing the guard
        # that a leading part which fails to resolve invalidates the reference.
        "module": _rival_fou(
            "match last with | none => false "
            "| some f => !(hasTransform f p) && !(hasLookup f p)"),
        "refinement": "relaxing the no-field-yet arm accepts a reference whose very "
                      "first part fails to resolve — there is no last resolved field "
                      "to host a registered transform/lookup, yet this rival exempts "
                      "it anyway. A reference rooted at a name that is not a field of "
                      "the model at all is then silently accepted instead of "
                      "reported, suppressing the nonexistent-field report the "
                      "already-passing tests demand. A faithful counterpart exempting "
                      "the no-field-yet case would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `flagOnUnresolved` "
                     "returns `true` when `last = none` (no field resolved yet), and "
                     "this rival returns `false`. Refuted at a single-part reference "
                     "whose sole part fails to resolve (lookup always none, last "
                     "stays none): gold judges INVALID (true), the rival VALID "
                     "(false) — the `none` arm of the fail-to-resolve decision, a "
                     "one-part reference that varies list length down to one.",
        "witness": _witness(
            _LK_NONE, _ALIAS_F, _F_FALSE, _F_FALSE, "0", _PARTS_LONE),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "skip-last-part",
        "kind": "uniqueness",
        "expect": "reject",
        # Traversal off-by-one: fold the correct step over `parts.dropLast`, so
        # the last visited part is never considered.
        "module": _impl(
            "    return ((parts.dropLast).foldl "
            "(stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)).2.2\n"),
        "refinement": "an off-by-one that stops one part short of the end skips the "
                      "last part of the reference, so a reference whose final part "
                      "is the one that fails to resolve (with no exempting "
                      "transform/lookup) is judged valid instead of reported — "
                      "diverging from gold on the nonexistent-trailing-field "
                      "reporting the already-passing tests rely on. A faithful "
                      "counterpart with that off-by-one would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: the fold runs over "
                     "EVERY part including the last; this rival drops the last. "
                     "Refuted at a two-part reference whose first part resolves to a "
                     "non-relation field (stepping off the graph) and whose LAST "
                     "part fails to resolve with no exemption: gold judges INVALID "
                     "(true), the rival VALID (false) — varies list length and pins "
                     "the offender at the last position.",
        "witness": _witness(
            _LK_RESOLVE0, _ALIAS_F, _F_FALSE, _F_FALSE, "0", _PARTS_SUFFIX),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "ignore-alias-resolution",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolution-split rival: drop the `isAlias` branch, so the identity-alias
        # part is resolved by `lookup` (and fails) instead of by `aliasField`.
        "module": _rival_fou(
            "match last with | none => true "
            "| some f => !(hasTransform f p) && !(hasLookup f p)").replace(
            "      | some m =>\n"
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "            | none => (some m, last, flag || fou)\n",
            "      | some m =>\n"
            "          match lookup m p with\n"
            "          | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          | none => (some m, last, flag || fou)\n"),
        "refinement": "dropping the identity-alias resolution routes the alias part "
                      "through the ordinary field lookup, which does not resolve it, "
                      "so a reference naming the model's identity alias is judged "
                      "invalid instead of accepted — a legitimate identity-alias "
                      "ordering is spuriously reported. A faithful counterpart that "
                      "stopped resolving the identity alias directly would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `stepWalk` "
                     "resolves an alias part via `aliasField` directly; this rival "
                     "sends it to `lookup`. Refuted at a single alias part where "
                     "`lookup` always fails: gold resolves it via `aliasField` and "
                     "judges VALID (false), the rival fails to resolve and judges "
                     "INVALID (true) — the ONLY witness that sets `isAlias = true`, "
                     "exercising the alias arm of the resolution split.",
        "witness": _witness(
            _LK_NONE, _ALIAS_F, _F_FALSE, _F_FALSE, "0", _PARTS_ALIAS),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "ignore-relation-descent",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolution-split rival: after a successful resolution never descend into
        # the related model — always step off the graph (cur := none).
        "module": _rival_fou(
            "match last with | none => true "
            "| some f => !(hasTransform f p) && !(hasLookup f p)").replace(
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "            | none => (some m, last, flag || fou)\n",
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            ((none : Option Model), some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => ((none : Option Model), some f, flag)\n"
            "            | none => (some m, last, flag || fou)\n"),
        "refinement": "never descending into the related model after a relation "
                      "field resolves means the chain steps off the model graph "
                      "immediately, so a subsequent part that is a legitimate field "
                      "of the related model has no model to resolve against and is "
                      "judged unresolved — a valid multi-hop related reference is "
                      "then spuriously reported. A faithful counterpart that failed "
                      "to descend into related models would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `stepWalk` "
                     "descends into `f.relModel` when the resolved field is a "
                     "relation; this rival always sets the current model to `none`. "
                     "Refuted at a two-part reference whose first part resolves to a "
                     "relation field (descending into model 1) and whose second "
                     "part is a field of that related model: gold resolves both and "
                     "judges VALID (false), the rival cannot resolve the second "
                     "(current model already `none`) and judges INVALID (true) — the "
                     "ONLY witness exercising a relation descent (`lookup` returning "
                     "a relation field).",
        "witness": _witness(
            _LK_DESCEND, _ALIAS_F, _F_FALSE, _F_FALSE, "0", _PARTS_SUFFIX),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "seed-wrong-model",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the seed: fold from `initState 0` instead of `initState cls0`, so
        # the walk always starts at model 0 regardless of the reference's root.
        "module": _impl(
            "    return (parts.foldl "
            "(stepWalk lookup aliasField hasTransform hasLookup) (initState 0)).2.2\n"),
        "refinement": "seeding the walk at a fixed model instead of the model the "
                      "reference is rooted at resolves every reference against the "
                      "wrong schema root, so a part that is a genuine field of the "
                      "reference's actual root fails to resolve (it is looked up in "
                      "the wrong model) and the reference is spuriously reported — "
                      "and a name that happens to exist in the fixed model is "
                      "wrongly accepted. The failing test's references are validated "
                      "against the wrong model; it would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`, which folds from "
                     "`initState cls0`: this rival folds from `initState 0`. Refuted "
                     "with cls0 = 1 and a MODEL-SENSITIVE resolver that resolves the "
                     "sole part only against model 1: gold seeds at model 1 and "
                     "judges VALID (false), the rival seeds at model 0 where the "
                     "part fails to resolve and judges INVALID (true). The ONLY "
                     "witness that moves cls0 off 0, exercising the seed binder.",
        "witness": _witness(
            _LK_MODEL1, _ALIAS_F, _F_FALSE, _F_FALSE, "1", _PARTS_LONE0),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "alias-const-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Mishandle the aliasField VALUE: resolve the alias part to a hardcoded
        # non-relation field instead of the model's actual identity field, so the
        # chain steps off the model graph even when the true identity field is a
        # relation that should descend.
        "module": _impl(
            "    let step := fun (st : WalkState) (p : Part) =>\n"
            "      let cur := st.1\n"
            "      let last := st.2.1\n"
            "      let flag := st.2.2\n"
            "      let fou : Bool := match last with | none => true "
            "| some f => !(hasTransform f p) && !(hasLookup f p)\n"
            "      match cur with\n"
            "      | none => ((none : Option Model), last, flag || fou)\n"
            "      | some m =>\n"
            "          if p.isAlias then\n"
            "            let f : Field := { isRel := false, relModel := 0 }\n"
            "            (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "            | none => (some m, last, flag || fou)\n"
            "    return (parts.foldl step (initState cls0)).2.2\n"),
        "refinement": "resolving the identity alias to a fabricated non-relation "
                      "field instead of the model's actual identity field steps the "
                      "chain off the model graph whenever the true identity field is "
                      "a relation — so a later part that is a legitimate field of the "
                      "model the identity relation descends into has no model to "
                      "resolve against and the reference is spuriously reported. A "
                      "faithful counterpart substituting the identity field's value "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = orderingRefInvalid ...`: `stepWalk` "
                     "resolves an alias part to `aliasField m` and descends into its "
                     "`relModel` when it is a relation; this rival substitutes a "
                     "constant non-relation field, so it never descends. Refuted "
                     "with `aliasField` returning a RELATION into model 1, at an "
                     "alias part followed by a field of model 1: gold descends via "
                     "the identity relation and resolves the second part (VALID, "
                     "false), the rival steps off the graph and cannot (INVALID, "
                     "true). The ONLY witness where the aliasField VALUE (a "
                     "relation) is load-bearing.",
        "witness": _witness(
            _LK_MODEL1, _ALIAS_REL, _F_FALSE, _F_FALSE, "0", _PARTS_ALIAS_THEN),
        # gold's `while` loop cannot decide this claim (stuck under
        # `Classical.choice`), so the refutation is checked against the
        # loop-free reference, which VERIFIES and does reduce.
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation rival, 3 partial-domain rivals)
# plus 0 AXIOM_TESTS. This bundle models the SAME single behaviour — the
# per-reference invalidity decision of the ordering walk — but over a DEEPER
# carrier: the nagini sibling flattens the walk to three index-aligned 0/1 lists
# (reached_field / is_value_op / is_compare_op) and a per-row @Pure oracle
# `flag_path`, whereas this backend models the walk itself as a `foldl` of
# `stepWalk` over `List Part`, with the four schema accessors as FREE INPUTS and
# the fail-to-resolve decision as `flagOnUnresolved`. The deeper carrier exposes
# sub-behaviours the flattened one cannot (the alias resolution, the relation
# descent, the traversal fold), which ADD rivals with no sibling counterpart.
#
#   sibling case                          -> here                          disposition
#   -------------------------------------------------------------------------------
#   positive-control-restructured-decision-> pos-inline-step                PORTED
#   admissibility-f2p-row-accepted        -> admiss-nondegenerate           RE-AIMED
#   frame-mutation-reached_field          -> (none)                         VACUOUS
#   partial-domain-drop-compare-op        -> prepatch-drop-lookup-escape    PORTED
#   partial-domain-drop-reached-field     -> relax-no-field-arm             RE-AIMED
#   partial-domain-last-path-negated      -> skip-last-part                 RE-AIMED
#   (no sibling)                          -> drop-transform-escape          ADDED
#   (no sibling)                          -> drop-both-escapes              ADDED
#   (no sibling)                          -> ignore-alias-resolution        ADDED
#   (no sibling)                          -> ignore-relation-descent        ADDED
#   (no sibling)                          -> seed-wrong-model               ADDED
#   (no sibling)                          -> alias-const-field              ADDED
#   (no sibling; backend mechanics)       -> pos-loopfree-fold              ADDED
#   (no sibling; witness limit)           -> (none) divergence            SPEC-CLOSED
#
# 2 ported, 3 re-aimed, 1 vacuous, 7 added = 12 cases (2 soundness,
# 1 admissibility, 9 uniqueness), plus 1 recorded spec hole shipping no case.
#
# ADDED (pos-loopfree-fold): not a ported adversarial argument but a BACKEND
#   MECHANICS requirement. It is the `witness_reference` every reject case is
#   refuted against, because gold's `while` loop cannot decide any claim (see the
#   module docstring). Shipping it as an expect="verify" case is what makes the
#   substitution auditable: the battery records on its own face that loop-freeness
#   VERIFIES, so no rival is being rejected merely for being loop-free.
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
#   loop in the impl (1 loop here, measure ``parts.length - i``). A rival that
#   loops without a measure is refused outright (``Decreasing annotations are
#   required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own
#   ``decreasing_1`` goal, re-measured on this bundle with a real build.
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
# PORTED (positive control): the sibling restructures the per-row decision
#   (compute `accept` and append its negation) while keeping the forward loop and
#   the per-element framing Assert. Here the analogous reshape INLINES the whole
#   per-part step (resolution split + fail-to-resolve decision, escape restored
#   inline) inside the same forward loop, keeping every invariant byte-identical;
#   the inlined step is definitionally equal to the folded `stepWalk`, so the
#   frozen proof closes with one `simp only`. Verified to build.
# RE-AIMED (admissibility): the sibling asserts the F2P row (field reached,
#   lookup-not-transform) is in-domain and ACCEPTED. This backend has NO `require`
#   clause, so the precondition-admits probe is vacuous; the live residual risk on
#   a total domain is a DEGENERATE post-image. Re-aimed at an in-region assert
#   that the post-image is non-degenerate at two F2P-shaped references (a
#   registered-lookup suffix -> VALID; a lone unresolvable part -> INVALID). The
#   loop body and its invariants are kept verbatim so the ensures still discharges.
#   Verified to build.
# VACUOUS (frame-mutation-reached_field): the sibling carries this as MANDATORY
#   because each of its three inputs holds a fractional heap permission
#   (Acc(...,1/2)) a rival could demand at full strength and overwrite. Lean and
#   Velvet are referentially transparent, have no heap/aliasing, and this bundle
#   declares no `mut` parameter over any input — every input is an immutable value
#   with no permission footprint, so there is no read-only input to overwrite. No
#   substitute fabricated (per the porting map: this class is vacuous here).
# PORTED / RE-AIMED (the three partial-domain rivals):
#   * partial-domain-drop-compare-op ports DIRECTLY: it drops the gold
#     `is_compare_op == 0` conjunct — exactly the pre-patch defect — which here is
#     dropping the registered-lookup escape from `flagOnUnresolved`
#     (prepatch-drop-lookup-escape). It IS the modeled bug (mapping.md sec.4).
#   * partial-domain-drop-reached-field (drop the reached_field==0 disjunct, so a
#     path with NO field reached is wrongly accepted) re-aims onto the `last =
#     none` arm of the fail-to-resolve decision (relax-no-field-arm): a leading
#     part that fails to resolve, with no field resolved yet, must still invalidate.
#   * partial-domain-last-path-negated (mis-decide the final examined path) re-aims
#     onto skip-last-part (an off-by-one that drops the last visited part of the
#     traversal fold).
# ADDED (6, no sibling counterpart): the deeper carrier exposes sub-behaviours the
#   sibling's flattened 0/1-row model cannot express, each attacked by a rival:
#   * drop-transform-escape — the MIRROR of the pre-patch defect (clear only on a
#     registered lookup, dropping the transform escape); refuted at a
#     transform-not-lookup suffix, moving `hasTransform` to its `true` value where
#     the pre-patch rival holds it false.
#   * drop-both-escapes — collapse the exemption entirely; a near-total rival
#     bounding the whole `flagOnUnresolved` escape.
#   * ignore-alias-resolution — drop the `isAlias` resolution branch; the ONLY
#     rival that sets `isAlias = true`, exercising the alias arm of the resolution
#     split.
#   * ignore-relation-descent — never descend into a related model after a
#     relation field resolves; the ONLY rival exercising a relation descent.
#   * seed-wrong-model — fold from a fixed model instead of `initState cls0`; the
#     ONLY rival that moves `cls0` off 0, refuted with a model-sensitive resolver
#     so the seed value is load-bearing.
#   * alias-const-field — resolve the alias part to a fabricated non-relation
#     field instead of `aliasField m`; the ONLY rival where the VALUE `aliasField`
#     returns (a relation that must descend) is load-bearing.
#
# BINDER / DOMAIN COVERAGE of the nine reject witnesses over the six input
#   binders of the load-bearing clause:
#     lookup       — resolve-name-0-else-fail (prepatch, drop-transform,
#                    drop-both, skip-last), always-none (relax-no-field,
#                    ignore-alias), relation-then-nonrel descent
#                    (ignore-relation-descent), model-sensitive (seed-wrong-model,
#                    alias-const-field): resolving, failing, descending, and
#                    model-keyed schemas all probed.
#     hasTransform — true-on-the-suffix (drop-transform, drop-both), false
#                    elsewhere: both values.
#     hasLookup    — true-on-the-suffix (prepatch, drop-both), false elsewhere:
#                    both values. The two accessors are additionally probed BOTH
#                    true at once (drop-both), the corner where a rival must clear
#                    on either one alone.
#     aliasField   — a non-relation identity field in most witnesses, and a
#                    RELATION identity field in alias-const-field, where its
#                    returned VALUE is load-bearing (gold descends via it). Both a
#                    non-relation and a relation identity field are probed, and the
#                    alias-const-field rival refutes an impl that mishandles which
#                    field is returned — closing the binder rather than declaring
#                    it inert.
#     cls0         — 0 in the first seven witnesses and 1 in seed-wrong-model,
#                    which pairs it with a model-sensitive resolver so the seed
#                    value determines the verdict; the seed binder is varied and
#                    attacked (a rival that folds from a fixed model is caught).
#     parts        — length 1 (relax-no-field, ignore-alias, seed-wrong-model) and
#                    length 2 (prepatch, drop-transform, drop-both, skip-last,
#                    ignore-relation-descent, alias-const-field); isAlias false
#                    (most) and true (ignore-alias, alias-const-field); offender at
#                    the head, the tail, and as the sole element: list length,
#                    order, and the alias flag all varied.
#   CLAUSE COVERAGE: the single top-level clause `out = orderingRefInvalid ...` is
#     attacked at each of its independent sub-behaviours — the fail-to-resolve
#     decision `flagOnUnresolved` (both escape conjuncts and the no-field arm), the
#     resolution split (alias branch, alias-field value, and relation descent), the
#     traversal fold (last position), and the seed. All nine reject witnesses now
#     probe DISTINCT input points — no witness is shared. drop-both-escapes was
#     originally refuted at the same registered-lookup suffix as
#     prepatch-drop-lookup-escape; it has been moved to the point where the
#     trailing part is registered as BOTH a transform and a lookup, which is the
#     sub-domain where drop-both alone is wrong and each of its two siblings is
#     RIGHT. Checked out-of-band: that witness is decided FALSE against the
#     reference AND against both sibling rivals, and holds only of drop-both — so
#     each of the three escape rivals now demonstrates the sub-domain its own
#     rationale claims instead of borrowing a neighbour's point.
#     pts = 9 distinct input points across 9 witnesses.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model (the walk is modeled deeply over four
# free-input accessors), so there is nothing to probe and the gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
