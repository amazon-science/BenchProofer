"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8459 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct recordParamTypes``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject that satisfies the spec. Here that subject is NOT the frozen
solution — its loop makes ``decide`` stuck for every claim — but the explicit
``witness_reference`` each reject case carries; see WITNESS MECHANICS).

DEFENDED SURFACE (one contracted method over a signature's parameter list plus
its return annotation, recording each into an ordered mapping):

  recordParamTypes (params : List Param) (retAnnot : Option SourceType)
      (aliases : Aliases) (renderType : Aliases → SourceType → TypeStr)
    return (out : List (List Char × TypeStr))
    ensures out =
      recordedTypes (renderType aliases) params
        ++ returnEntry (renderType aliases) retAnnot                       -- (C1)

CLAUSE STRUCTURE (read before judging clause / binder coverage). (C1) is the
SOLE load-bearing clause, a full structural equality on the input carrier —
GROUNDED in the actual inputs (directive 8), not an opaque answer key — pinning
several independent facets at once:

  (a) the renderer is applied to the CONFIGURED alias map ``aliases`` — NOT to
      an empty/default map — for EVERY recorded string, at every parameter slot
      AND the return slot. This is the one behavioural fact the fix changes: the
      pre-image applies the renderer to a default (empty) alias map, so a
      configured alias never takes effect.
  (b) an ANNOTATED name contributes exactly one entry binding its name to the
      rendered string; an UNANNOTATED name contributes NOTHING.
  (c) the return annotation contributes its own entry (under the constant return
      key) iff it is present, appended LAST.
  (d) parameter ORDER and length are preserved.

``renderType : Aliases → SourceType → TypeStr`` is a FREE input the spec
quantifies over: the ``ensures`` holds for EVERY value of it, so the spec makes
NO claim about how any single annotation renders. What it pins is that whatever
the renderer does, it is fed the CONFIGURED map — so a rival that fed it a
different (default) map is refuted uniformly. Each reject witness instantiates
``renderType`` at a concrete decidable lambda that SEPARATES the configured map
from the empty one (``fun A _ => match A with | [] => ['I'] | _ => ['M']``) or,
where the facet under attack is alias-independent, at a constant renderer.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating back-to-front loop collapsed
    to the closed form the post-image names; the per-name entry bound to a local)
    must still verify, else SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries no ``require`` clause, so the precondition
    is trivially satisfiable; the residual risk is that the post-image is
    DEGENERATE at the interesting points. ``admiss-grounded`` discharges an
    in-region assert pinning that the pure post-image really does record an
    annotated name, SKIP an unannotated one, EMIT the return entry when present,
    and OMIT it when absent — at concrete inputs, with the impl kept verbatim so
    the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's mandatory
    frame rival WRITES into the read-only alias map (held at a fractional
    permission) and is rejected for INSUFFICIENT PERMISSION. Lean and Velvet are
    referentially transparent: ``params``, ``retAnnot``, ``aliases`` and the
    renderer are immutable values (none declared ``mut``), there is no heap and
    no aliasing, so there is no read-only input to overwrite and no permission
    system to trip. DEMONSTRATED rather than asserted: transliterating the sibling
    rival (``aliases := aliases ++ [(['k'], ['v'])]`` prepended to the impl region,
    gold body kept verbatim after it) does not elaborate, and the error is not a
    spec verdict — it is ``` `aliases` cannot be mutated, only variables declared
    using `let mut` can be mutated ```, i.e. the write is rejected at
    ELABORATION, before any obligation is generated. A case built on it could
    never distinguish a permission violation from a syntax error, so it would
    attest to nothing about the spec. Omitted as vacuous, NOT fabricated (per the
    porting map, this class is legitimately dropped rather than replaced).
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
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port: wrong impls that
    diverge from the desired behaviour on some sub-domain and MUST be rejected.
    Each is a STRAIGHT-LINE (``List.map`` / closed-form) body so its extracted
    tester kernel-reduces under ``decide``, refuted at a concrete input by a
    witness that ELABORATES against the rival and is REFUTED by ``decide``
    against the loop-free ``witness_reference`` (the frozen loop-solution cannot
    decide anything — see WITNESS MECHANICS).

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches (C1) through Velvet's own tester
machinery: ``recordParamTypesTester params retAnnot aliases renderType = false``
says the extracted program's result violates the postcondition at that concrete
input, checked in a file whose ``prove_correct`` block has been stripped (no
tactic script can mask the verdict). The free renderer is instantiated at a
concrete decidable lambda in each witness, so the tester reduces to a ground
boolean and no opaque conditioning (and hence no consistency obligation) is
needed.

THE FROZEN SOLUTION CANNOT SERVE AS THE DISCRIMINATING SUBJECT, and every reject
case therefore names an explicit ``witness_reference``. The frozen program
contains a ``while`` loop, which under ``loom.semantics.choice "demonic"``
elaborates through ``Classical.choice``; the kernel cannot unfold that, so
``decide`` on the FROZEN tester is STUCK for every claim regardless of truth.
Measured, not assumed: each of the five witnesses below, built against the frozen
solution, fails with

    Tactic `decide` failed ... its `Decidable` instance ... did not reduce to
    `isTrue` or `isFalse` ... reduction got stuck

which is a failure the kernel never evaluated — exit 1 carrying NO information
about whether the claim is true. Reading that exit code as "gold satisfies the
spec here" is the ``witness-undecided`` defect class, and it is not hypothetical
on this cell: a FORGERY asserting the exact OPPOSITE of a refutation (that
``weak-drop-return`` is CORRECT at the agreement point ``retAnnot = none``,
``recordParamTypesTester [{name := ['q'], annot := some ['a']}] none [] (fun _ _
=> ['t']) = true``) elaborates against that rival (exit 0) and fails against the
frozen solution by the same stuck reduction (exit 1) — clearing both halves of a
gold-subject discrimination check while attesting to nothing.

So the second half of each check is run against ``_REFERENCE``: the loop-free
closed-form impl of this same spec (the ``pos-closed-form`` body), which shares
the frozen spec byte-for-byte and VERIFIES, and whose extracted program DOES
kernel-reduce. That is sound for the reason gold was — a witness says "the spec
is violated at this input", and an impl the verifier ACCEPTS cannot violate its
own spec — and it is checked, not trusted: the gate independently re-verifies the
reference before refuting anything against it. Against that subject the refutation
is SEMANTIC, not a stuck reduction: each build fails with ``Tactic `decide` proved
that the proposition ... is false``, i.e. the kernel evaluated the claim and found
it untrue of a correct impl. The forgery above is correctly caught there — it
ELABORATES against the reference (exit 0), so it is ``witness-vacuous`` rather
than a refutation.

Every reject witness below was run three ways with real builds: against the rival
(elaborates, exit 0), against the frozen solution (exit 1 by STUCK REDUCTION — no
information), and against ``_REFERENCE`` (exit 1 by ``decide`` REFUTING the
claim — the discriminating build).

WITNESS PLACEMENT. The five rejects probe five DISTINCT input points, so every
input binder is genuinely varied: ``params`` ranges over a single annotated name,
a differently-named annotated name, a two-element list, and a single UNANNOTATED
name; ``retAnnot`` over ``none`` and ``some``; ``aliases`` over a non-empty and an
empty map; and ``renderType`` over the alias-separating lambda and a constant
renderer. A rival that mishandled only a fixed input shape or a fixed renderer
would still be caught. pts=5.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
renderer is the FREE input ``renderType`` (an A-reference the R/I legs
differential-test — G-CONF / G-AX's job), not a consumed contract. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8459"
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

# The WHOLE executable body of the method: the backward accumulating loop that
# prepends each parameter's contribution. Reject rivals and the closed-form
# positive control replace this with a loop-free body (so their tester reduces
# under `decide`).
_IMPL = """    -- impl-start
    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
    let mut i := params.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ params.length
      invariant result =
        recordedTypes (renderType aliases) (params.drop i)
          ++ returnEntry (renderType aliases) retAnnot
      done_with i = 0
      decreasing i
    do
      let p := params[i - 1]!
      result := paramEntry (renderType aliases) p ++ result
      i := i - 1
    return result
    -- impl-end"""

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let p := params[i - 1]!
      result := paramEntry (renderType aliases) p ++ result
      i := i - 1"""

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this; the tactic body is elided from the spec view,
# so this is a proof reshape, not a spec change.
_PROOF = """prove_correct recordParamTypes by
  loom_solve
  rw [recordedTypes_drop_step (renderType aliases) params i (by omega) (by omega)]
  simp_all"""


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


def _rival(body):
    """Replace the whole impl body with a loop-free closed form."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery. The precondition is trivially true (no `require`), so the
# ---- tester's guard is vacuous and never excludes an input.
# ---- `recordParamTypesTester params retAnnot aliases renderType = false` then
# ---- says the extracted program violates C1 at that input. The free renderer is
# ---- instantiated at a concrete decidable lambda, so the tester reduces to a
# ---- ground boolean under `decide`.
def _tester(body):
    return ("extract_program_for recordParamTypes\n"
            "prove_precondition_decidable_for recordParamTypes\n"
            "prove_postcondition_decidable_for recordParamTypes\n"
            "derive_tester_for recordParamTypes\n\n" + body)


# ---- The witness SUBJECT for every reject case. The frozen solution cannot be
# ---- one: its `while` loop elaborates through `Classical.choice` under
# ---- loom.semantics.choice "demonic", so the kernel cannot unfold it and
# ---- `decide` on the frozen tester is STUCK for EVERY claim, true or false --
# ---- an exit code that discriminates nothing (see WITNESS MECHANICS above).
# ---- `_REFERENCE` is the loop-free closed form (identical to the pos-closed-form
# ---- body): it shares the frozen spec byte-for-byte, it VERIFIES (so it cannot
# ---- violate its own spec, which is what makes refutation against it sound), and
# ---- its extracted program kernel-reduces, so `decide` returns a real verdict.
# ---- Stated EXPLICITLY on each case rather than left to the gate's positive-
# ---- fallback, so the artifact itself records which impl the refutations were
# ---- checked against.
_REFERENCE = _swap2(
    _IMPL,
    "    -- impl-start\n"
    "    return recordedTypes (renderType aliases) params "
    "++ returnEntry (renderType aliases) retAnnot\n"
    "    -- impl-end",
    _PROOF,
    "prove_correct recordParamTypes by\n  loom_solve")


# The alias-SEPARATING renderer: renders differently for the empty map (`['I']`)
# vs. any non-empty (configured) map (`['M']`). Under it, `renderType aliases`
# with a non-empty `aliases` differs from `renderType []`, so any rival that
# fed the renderer the default empty map is caught.
_DIST = "(fun A _ => match A with | [] => ['I'] | _ => ['M'])"
# A constant renderer, for facets that are alias-independent (return-membership,
# unannotated-skip): the discrimination there does not depend on the alias map.
_CONST = "(fun _ _ => ['t'])"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical C1
    # obligation and only reshapes the executable surface. Both verified
    # out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly: a maximally different control-flow shape (no loop, no
        # accumulator) computing the same mapping. The loop-specific proof is
        # retuned since the impl now matches the post-image syntactically, so
        # `loom_solve` closes it definitionally.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return recordedTypes (renderType aliases) params "
            "++ returnEntry (renderType aliases) retAnnot\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct recordParamTypes by\n  loom_solve"),
        "rationale": "a loop-free impl that returns the recorded mapping directly "
                     "must satisfy C1 `out = recordedTypes (renderType aliases) "
                     "params ++ returnEntry (renderType aliases) retAnnot`; a "
                     "correct reshape of the modeled behaviour verifying is exactly "
                     "what SPEC-TOO-STRONG would deny. Exercises the obligation from "
                     "a maximally different (loop-free) control-flow shape. "
                     "(Sibling: pos-branch-reorder, re-expressed — order-independence "
                     "of the post-image is subsumed by returning the post-image "
                     "verbatim.)",
    },
    {
        "id": "pos-local-bind",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape: bind each parameter's contribution to a typed
        # local FIRST, then prepend it. Same value flow; the loop and the
        # front-recursive invariant are unchanged, so the frozen proof closes
        # untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let p := params[i - 1]!\n"
            "      let e := paramEntry (renderType aliases) p\n"
            "      result := e ++ result\n"
            "      i := i - 1"),
        "rationale": "binding each per-name contribution to a local computes the "
                     "same accumulator value-for-value with the loop and invariant "
                     "unchanged, so C1 still holds and the frozen proof closes; a "
                     "correct reshape must verify (else SPEC-TOO-STRONG on the "
                     "executable shape). (Sibling: pos-locals-reshape.)",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause, so the "a normal input satisfies the
    # precondition" probe is not where the risk sits. The residual risk is that
    # the post-image is DEGENERATE at the interesting points. This case discharges
    # an in-region assert (auto-solved, checked out-of-band) pinning that the pure
    # post-image really does RECORD an annotated name, SKIP an unannotated name,
    # EMIT the return entry when present, and OMIT it when absent. The impl is kept
    # verbatim so the method's own obligation still discharges; the proof's
    # alternation gains one `decide` arm for the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_TOP,
            "    assert (with_name_prefix `adm\n"
            "      (recordedTypes (fun _ => ['t']) [{ name := ['p'], annot := some ['a'] }] "
            "= [(['p'], ['t'])] ∧\n"
            "       recordedTypes (fun _ => ['t']) [{ name := ['p'], annot := none }] = [] ∧\n"
            "       returnEntry (fun _ => ['t']) (some ['a']) = [(\"return\".toList, ['t'])] ∧\n"
            "       returnEntry (fun _ => ['t']) none = []))\n"
            + _IMPL_TOP,
            _PROOF,
            "prove_correct recordParamTypes by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [recordedTypes_drop_step (renderType aliases) params i "
            "(by omega) (by omega)];\n"
            "       simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: it RECORDS an annotated name (bind → one "
                     "entry), SKIPS an unannotated name (→ no entry), EMITS the "
                     "return entry when a return annotation is present, and OMITS it "
                     "when absent. The in-region assert must discharge (else the "
                     "obligation is degenerate / PRECOND-TOO-STRONG); the impl is "
                     "kept verbatim so C1 still verifies. (Sibling: "
                     "admiss-readonly-membership, re-aimed: the sibling probes the "
                     "half-permission read grant — a permission fact with no analogue "
                     "on a referentially-transparent carrier — so it is re-aimed to "
                     "the sharper residual risk of a degenerate post-image.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-default-alias-map",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating delta — the literal pre-image behaviour. Feed the
        # renderer the DEFAULT (empty) alias map at EVERY slot, ignoring the
        # configured `aliases`. Correct on every input where the empty map and the
        # configured map render identically; diverges wherever a configured alias
        # governs a source.
        "module": _rival(
            "    return recordedTypes (renderType []) params "
            "++ returnEntry (renderType []) retAnnot"),
        "refinement": "this IS the pre-image behaviour: the renderer is applied to "
                      "the DEFAULT empty alias map, so configured aliases never take "
                      "effect. Its faithful real counterpart is the UNCHANGED buggy "
                      "call — which, with a configured alias in play, records the "
                      "underlying rendered form rather than the configured one, "
                      "exactly the failing case the issue adds — so it would NOT "
                      "resolve. (Sibling: weak-prepatch-expand.)",
        "rationale": "REJECT from C1: the post-image applies the renderer to "
                     "`aliases`, but the rival applies it to `[]`, and under a "
                     "renderer that separates the two maps they differ on every "
                     "recorded string, so `out ≠ recordedTypes (renderType aliases) "
                     "… ++ …`. If it VERIFIED the spec would admit the pre-patch bug "
                     "=> SPEC-TOO-WEAK. Attacks facet (a) of C1 at ALL slots. Refuted "
                     "at a single annotated param under a non-empty alias map with "
                     "the alias-separating renderer.",
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : recordParamTypesTester "
            "[{ name := ['p'], annot := some ['a'] }] none [(['x'], ['y'])] "
            + _DIST + " = false := by\n  decide\n"),
    },
    {
        "id": "weak-return-default-alias",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: parameters rendered under the configured map, but the
        # RETURN entry rendered under the DEFAULT empty map. Correct on every slot
        # but the return; diverges on the return whenever a configured alias
        # governs the return annotation.
        "module": _rival(
            "    return recordedTypes (renderType aliases) params "
            "++ returnEntry (renderType []) retAnnot"),
        "refinement": "a counterpart that threaded the configured map for the "
                      "parameter loop but left the RETURN recorded under the default "
                      "map would render the parameters with the configured alias yet "
                      "the return without it — the failing test pins the return line "
                      "to the configured form, so it would NOT resolve. (Sibling: "
                      "weak-return-expand.)",
        "rationale": "REJECT from C1: `returnEntry (renderType aliases) retAnnot` "
                     "pins the return string to the CONFIGURED map, but the rival "
                     "emits `returnEntry (renderType []) retAnnot`, which differs "
                     "under the separating renderer. The return slot is pinned "
                     "INDEPENDENTLY of the parameter slots, so a single-slot "
                     "divergence is caught. Refuted at a `some` return annotation "
                     "under a non-empty alias map — a DISTINCT point (retAnnot=some) "
                     "from the all-slots rival.",
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : recordParamTypesTester "
            "[{ name := ['p'], annot := some ['a'] }] (some ['b']) [(['x'], ['y'])] "
            + _DIST + " = false := by\n  decide\n"),
    },
    {
        "id": "weak-tail-default-alias",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN across parameters: render the FIRST parameter under the
        # configured map but the REST under the default empty map (e.g. an
        # off-by-one that alias-resolves only the head). Tests that facet (a) pins
        # EACH parameter, not just the first.
        "module": _rival(
            "    return recordedTypes (renderType aliases) [params.head!] "
            "++ recordedTypes (renderType []) params.tail "
            "++ returnEntry (renderType aliases) retAnnot"),
        "refinement": "a counterpart that alias-resolved only the first parameter "
                      "would render the first name with the configured alias and the "
                      "rest without it — the failing test pins EVERY parameter to the "
                      "configured form, so it would NOT resolve. (Sibling: "
                      "weak-slot1-expand.)",
        "rationale": "REJECT from C1: `recordedTypes (renderType aliases) params` "
                     "pins EVERY parameter's string to the configured map, but the "
                     "rival renders `params.tail` under `[]`, which differs under the "
                     "separating renderer on the second parameter. Facet (a) pins "
                     "each name, not just the head. Refuted at a TWO-parameter input "
                     "(a distinct input shape from the single-parameter rivals), "
                     "where the tail is non-empty.",
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : recordParamTypesTester "
            "[{ name := ['p'], annot := some ['a'] }, { name := ['q'], annot := some ['c'] }] "
            "none [(['x'], ['y'])] " + _DIST + " = false := by\n  decide\n"),
    },
    {
        "id": "weak-drop-return",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the parameters correctly but DROPS the return entry entirely
        # (never appends the return contribution). Violates facet (c): the return
        # entry must be present when a return annotation exists.
        "module": _rival(
            "    return recordedTypes (renderType aliases) params"),
        "refinement": "records the parameters correctly but never emits the return "
                      "entry. A faithful real patch omitting the return-recording "
                      "step renders no return line, but the failing test asserts the "
                      "output ends with a rendered return line, so it would NOT "
                      "resolve. (Sibling: weak-drop-return.)",
        "rationale": "REJECT from C1: `returnEntry (renderType aliases) retAnnot` is "
                     "`[(return-key, …)]` when `retAnnot` is `some`, so the post-image "
                     "carries a trailing return entry the rival never appends; "
                     "`out ≠ … ++ returnEntry …`. Attacks facet (c) — the "
                     "presence of the return entry — a facet distinct from the "
                     "alias-resolution rivals. Refuted at a `some` return annotation "
                     "under a differently-named param and an EMPTY alias map (a "
                     "distinct input point; the facet is alias-independent, so a "
                     "constant renderer suffices).",
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : recordParamTypesTester "
            "[{ name := ['q'], annot := some ['a'] }] (some ['b']) [] "
            + _CONST + " = false := by\n  decide\n"),
    },
    {
        "id": "weak-record-unannotated",
        "kind": "uniqueness",
        "expect": "reject",
        # Records EVERY parameter — including UNANNOTATED ones (using an
        # empty-source fallback) — instead of skipping them. Violates facet (b):
        # an unannotated name must contribute NOTHING.
        "module": _rival(
            "    return params.map (fun p => (p.name, renderType aliases (p.annot.getD []))) "
            "++ returnEntry (renderType aliases) retAnnot"),
        "refinement": "recording an unannotated parameter emits a spurious type entry "
                      "for a name the signature never annotated; the rendered output "
                      "would carry a type line for a parameter that has none, which "
                      "the failing test's exact expected output does not contain, so "
                      "it would NOT resolve. (No direct sibling: the nagini surface's "
                      "clause (2), `!has_i => name_i not in Result()`, is attacked "
                      "here by a rival that records the unannotated slot — carrier "
                      "makes the skip-vs-record facet directly falsifiable.)",
        "rationale": "REJECT from C1: `recordedTypes` maps an unannotated name "
                     "(`annot = none`) to the EMPTY contribution, but the rival emits "
                     "an entry for it, so `out ≠ recordedTypes (renderType aliases) "
                     "params ++ …`. Attacks facet (b) — unannotated names contribute "
                     "nothing — a facet no other rival tests. Refuted at a single "
                     "UNANNOTATED parameter (`annot := none`), a distinct input shape; "
                     "alias-independent, so a constant renderer suffices.",
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : recordParamTypesTester "
            "[{ name := ['z'], annot := none }] none [] "
            + _CONST + " = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 1 frame-mutation rival, 4
# uniqueness/partial-domain rivals) plus an empty AXIOM lane. The sibling
# contracts ONE function, `record_annotations`, over a FIXED-ARITY surface (two
# named parameter slots + a return slot, `has0/has1/ret_has` flags) with the
# alias map at a fractional heap permission and the resolver a GROUNDED @Pure
# oracle `resolve`/`expand`. This bundle contracts ONE method, `recordParamTypes`,
# over a VARIABLE-LENGTH `List Param` + `Option` return, with the renderer a FREE
# input `renderType` the spec quantifies over — so the fixed two-slot surface
# generalises to a list, and `resolve`/`expand` (an alias-resolving renderer vs.
# an empty-map renderer) collapse into `renderType aliases` vs. `renderType []`.
# The value surface carries across intact; the permission surface does not exist
# here.
#
#   sibling case (nagini)         kind          -> here                         disposition
#   ------------------------------------------------------------------------------------------
#   pos-branch-reorder            soundness     -> pos-closed-form              RE-EXPRESSED
#   pos-locals-reshape            soundness     -> pos-local-bind               PORTED
#   admiss-readonly-membership    admissibility -> admiss-grounded              RE-AIMED
#   frame-write-aliases           uniqueness    -> (none)                       VACUOUS
#   weak-prepatch-expand          uniqueness    -> weak-default-alias-map       PORTED
#   weak-return-expand            uniqueness    -> weak-return-default-alias     PORTED
#   weak-slot1-expand             uniqueness    -> weak-tail-default-alias       PORTED
#   weak-drop-return              uniqueness    -> weak-drop-return             PORTED
#   (new, no sibling)             uniqueness    -> weak-record-unannotated       ADDED (clause 2)
#
# RE-EXPRESSED (pos-branch-reorder -> pos-closed-form): the sibling reorders the
#   three fixed recording branches to show order-independence of the post-image.
#   Here the post-image is a single list concatenation; returning it verbatim
#   (loop collapsed) is the maximally-different correct shape and subsumes the
#   order argument — the concatenation IS the fixed order.
# PORTED (pos-locals-reshape -> pos-local-bind): each recorded contribution is
#   bound to a local before use; the loop and invariant are unchanged so the
#   frozen proof closes untouched.
# RE-AIMED (admiss-readonly-membership -> admiss-grounded): the sibling asserts
#   the half-permission alias map is readable and the reserved-slot / distinctness
#   preconditions hold — permission and fixed-slot facts with no analogue on a
#   referentially-transparent, variable-length, `require`-free carrier. Re-aimed to
#   the sharper residual risk here: a degenerate post-image. The case discharges a
#   live in-region assert pinning RECORD (annotated), SKIP (unannotated), EMIT
#   (return present), OMIT (return absent) at concrete inputs.
# VACUOUS (frame-write-aliases): the sibling's mandatory frame rival WRITES into
#   the half-permission read-only alias map and is rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent and every binder is an
#   immutable value (no `mut`), so there is no read-only input to overwrite and no
#   permission system to trip. Omitted as vacuous, NOT fabricated (per the porting
#   map, this class is legitimately dropped rather than replaced).
# PORTED (the three partial-domain expand rivals): weak-prepatch-expand ports to
#   weak-default-alias-map (the literal pre-image — renderer fed the default map at
#   ALL slots); weak-return-expand to weak-return-default-alias (default map on the
#   return slot only); weak-slot1-expand to weak-tail-default-alias (default map on
#   every parameter but the head — the "resolves only the first" off-by-one). The
#   grounded `resolve`/`expand` oracle pair becomes `renderType aliases` vs.
#   `renderType []`; the free renderer is instantiated at a concrete lambda that
#   separates the two maps, so the divergence is decidable at a literal input.
# PORTED (weak-drop-return): drops the return entry entirely; refuted by facet (c)
#   of C1 (the return entry must be present when a return annotation exists).
# ADDED (weak-record-unannotated): the sibling's postcondition clause (2)
#   (`!has_i => name_i not in Result()`) is defended in nagini by the flag-guarded
#   branches but is not attacked by a dedicated SPEC_TESTS rival there. On this
#   VARIABLE-LENGTH carrier the skip-unannotated facet (b) is directly falsifiable:
#   a rival that records unannotated names emits a spurious entry. Added to attack
#   facet (b) and give a fifth distinct witness point.
# AXIOM_TESTS: empty in the sibling; dropped regardless (the axiom lane is G-AX's
#   job). Here the renderer is the FREE input `renderType` (an A-reference the R/I
#   legs differential-test), not a consumed contract, so there is nothing to probe.
#
# DIVERGENCE lane - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
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
# BINDER / CLAUSE COVERAGE. The obligation has FOUR input binders — `params`,
#   `retAnnot`, `aliases`, `renderType` — and one top-level clause C1, which pins
#   facets (a) renderer-applied-to-configured-map at every slot, (b) unannotated
#   names contribute nothing, (c) the return entry present iff `retAnnot` is
#   `some`, (d) order/length. The five reject witnesses probe five DISTINCT input
#   points (pts=5): `params` ranges over a single annotated name, a differently-
#   named annotated name, a two-element list, and a single UNANNOTATED name;
#   `retAnnot` over `none` and `some`; `aliases` over a non-empty map and `[]`;
#   `renderType` over the alias-separating lambda and a constant renderer. Facet
#   (a) is attacked from three independent sub-domains (all slots / return only /
#   tail parameters only), facet (b) by weak-record-unannotated, facet (c) by
#   weak-drop-return; facet (d) (order/length) is pinned by the spec but is NOT
#   F2P-load-bearing (a stable reordering of the recorded mapping does not change
#   which name maps to which type in the rendered output), so a reordering rival
#   would be a spurious verify-does-imply-resolve case and is deliberately NOT
#   shipped. No binder is held fixed by every rival, so a rival mishandling only a
#   fixed slot, a fixed input shape, or a fixed renderer could not slip through.
#   Each witness was SEEN to discriminate with THREE real builds: it ELABORATES
#   against the rival (exit 0 — the straight-line tester reduces under `decide`);
#   against the frozen loop-solution it fails by STUCK REDUCTION (exit 1 carrying
#   no information, which is why the frozen solution is not the subject); and
#   against the loop-free `_REFERENCE` it is REFUTED SEMANTICALLY (exit 1,
#   "`decide` proved that the proposition ... is false" — the kernel evaluated the
#   claim and found it untrue of an impl the verifier ACCEPTS). The renderer is
#   instantiated at a concrete decidable lambda in every witness, so no witness
#   conditions on an opaque term and the binders are trivially jointly
#   satisfiable.
AXIOM_TESTS = []
