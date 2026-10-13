"""properties.py — G-PBT falsification battery for sympy__sympy-14531 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
each ``prove_correct <name>`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted methods over a purely-functional core). A
composite serializer renders a tagged binary head and a ternary head. The
serializer is CONFIGURABLE and STATEFUL, and both halves are observable:

  printTaggedPair (cfg) (tag) (a) (b) (mut reg)
      ensures out = taggedPair cfg tag a b regOld
      ensures reg = taggedPairReg cfg a b regOld
  printLimit      (cfg) (e) (z) (z0)  (mut reg)
      ensures out = limitTriple cfg e z z0 regOld
      ensures reg = limitTripleReg cfg e z z0 regOld

where the four ``pure`` spec functions are, structurally,

  renderText cfg reg s   = (renderSub cfg reg s).1
  renderReg  cfg reg s   = (renderSub cfg reg s).2
  taggedPair cfg tag a b reg
      = tag ++ "(" ++ renderText cfg reg a ++ ", "
            ++ renderText cfg (renderReg cfg reg a) b ++ ")"
  taggedPairReg cfg a b reg  = renderReg cfg (renderReg cfg reg a) b
  limitTriple cfg e z z0 reg
      = "Limit(" ++ renderText cfg reg e ++ ", "
            ++ renderText cfg (renderReg cfg reg e) z ++ ", "
            ++ renderText cfg (renderReg cfg (renderReg cfg reg e) z) z0 ++ ")"
  limitTripleReg cfg e z z0 reg
      = renderReg cfg (renderReg cfg (renderReg cfg reg e) z) z0

``renderSub : Bool → List Char → SubObj → (List Char × List Char)`` is an
``opaque`` free function with NO constraining ``axiom`` — nothing is claimed
about the concrete text a sub-object renders to or the concrete registry a step
leaves, only that ONE step is a deterministic function of (configuration,
incoming registry, sub-object) and that its two results come from that SAME step
(mapping.md §3: it is an UNCHANGED per-object rendering step that the operation
routes each sub-object through but never replaces; the weakest sufficient
contract asserts nothing about either component, so the proof borrows no
soundness from it). Neither method has a ``require`` clause; both input domains
are total.

CARRIER NOTE — there are THREE load-bearing observables here, and the third one
is why the previous revision of this battery could not see the spec's hole.

  (i)   WHICH CONFIGURATION reaches each sub-object. Each sub-object segment is
        ``renderText cfg ...``; a serializer that governs the composite but
        drops its configuration for a sub-object renders that sub-object under a
        DEFAULT instead. Refutable only by CONDITIONING on the carrier, since
        ``renderSub`` is opaque and no literal input computes a segment.
  (ii)  THE ASSEMBLY around the segments — the head token, the ``", "``
        separators, the parentheses, and the ORDER the segments are emitted in.
  (iii) THE STEP SEQUENCE the serializer actually takes: which registry each
        step starts from, how many steps are taken, and whether the composite's
        own registry is the one that advances. This is what the second
        ``ensures`` of each method pins, and it is pinned twice over: ``reg``
        afterwards must be the left-to-right fold of the steps, AND the TEXT of
        a later sub-object is the text produced FROM the registry the earlier
        steps left (``renderText cfg (renderReg cfg reg a) b``), so naming a
        later segment already commits to the earlier steps having happened, in
        order, on this serializer.

Observable (iii) is a real observable of the modeled callee, not a modeling
convenience: the step under model registers what it renders, and the caller
emits that registry ahead of the composite (mapping.md §3.1, validated
executably by axiom_check.py / conformance_check.py). A model in which one step
is a PURE function of (configuration, sub-object) cannot see it, and that is
exactly the state this battery's earlier revision defended: it shipped a
POSITIVE control (``pos-tagged-reorder-lets``) asserting that binding the second
sub-object's render BEFORE the first MUST verify, on the ground that "pure
``let``s of independent expressions commute". Under the strengthened spec the
two steps are no longer independent, that shape is wrong, and the case now
appears in the REJECT lane as ``weak-tagged-swap-steps`` — the shape recorded
against this cell as a verify-does-not-resolve break (verdict.md:
``atk_2_swap_rel``, resolved=FALSE, F2P failure ``test_python_relational``).
``pos-tagged-name-later-step-first`` replaces it as the reshape control: naming
the later step first is still admissible as long as it is computed FROM the
registry the earlier step leaves, which is what makes the spec pin the DATA
DEPENDENCE rather than the textual order of the ``let``s.

ADVERSARIAL READ of the sibling (nagini) classes on this carrier:

  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (assemble inline without the ``let`` bindings;
    or name the later step first, computed from the registry the earlier step
    leaves) must still verify against the byte-identical obligations, else the
    spec is SPEC-TOO-STRONG on the SHAPE of the impl. Both reshapes are
    definitionally the frozen return and the frozen ``prove_correct`` script
    still closes (each verified out-of-band with a real build). The "cheapest
    impl" control the sibling ships (return the ``@Pure`` oracle values
    directly) ALSO ports, as ``pos-tagged-cheapest``: returning ``taggedPair cfg
    tag a b reg`` and assigning ``taggedPairReg cfg a b reg`` verifies under the
    frozen tactic body unchanged (measured exit 0; ``all_goals`` makes the
    trailing ``simp only`` a no-op rather than an over-solve, so unlike the
    previous revision this control needs no retuning at all). It pins
    admissibility of the post-image, which the reshapes do not. A FIFTH positive
    (``pos-tagged-uncommitted-probe``) carries the shape at the boundary of what
    the clauses can pin — an extra ``renderSub`` application whose result is
    never written back — and is a positive on purpose: it is the SAME Lean
    program as the frozen impl (its added ``have`` proves the extracted
    program's result is gold's pair, at every input, by ``simp``), and under
    mapping.md §2.2 it materializes to gold's arm plus a discarded probe, whose
    patch MEASURES resolved=TRUE. Demanding its rejection would be
    SPEC-TOO-STRONG in the strict sense: no postcondition over ``(out, reg)``
    can separate two programs with one denotation.

  * PARTIAL-DOMAIN — the spec's teeth on observable (i). A rival that renders a
    sub-object under the default configuration is correct on the ``cfg = false``
    half of the domain (or its mirror on ``cfg = true``) but wrong on the other
    half. Both halves are attacked, at BOTH modeled sites, at the FIRST, MIDDLE
    and THIRD sub-object positions.

  * VALUE-SHAPE / ASSEMBLY — APPLIES, and is a SEPARATE observable from the
    other two. The sibling's ``value-swap-num-denom`` argues that emitting two
    rendered operands in the wrong ORDER must be rejected. The digit-level
    structure it attacks is refined away here (``renderSub`` pins no concrete
    text), but the ORDER argument re-sites one level up onto the rendered
    SEGMENTS, which this carrier does model — and so do the head token and the
    ``", "`` separators. Five rivals carry this class
    (``weak-tagged-drop-head``, ``weak-tagged-thin-separator``,
    ``weak-tagged-transpose``, ``weak-limit-thin-separator``,
    ``weak-limit-transpose``); the first, second and fourth need no hypothesis
    at all, since a literal-frame clash is decidable outright.

  * EFFECT / STEP-SEQUENCE — the class the previous revision had no case for,
    because the previous spec had no clause for it. EIGHT rivals carry it:
    ``weak-tagged-swap-steps`` and ``weak-limit-swap-steps`` (steps taken in the
    wrong order — the recorded break and its ternary twin),
    ``weak-tagged-fresh-serializer`` (both steps taken on a THROWAWAY serializer
    from an empty registry, the composite's own registry left untouched — the
    second recorded break), ``weak-tagged-drop-effect`` (the steps are taken and
    chained correctly but the composite's registry is never written back),
    ``weak-tagged-dup-step`` (one sub-object stepped TWICE),
    ``weak-tagged-commit-extra-step`` (an EXTRA step on the second sub-object,
    taken ahead of the two the arm needs AND written back — the shape whose
    faithful materialization verdict.md measured resolved=FALSE as
    ``atk_1_extra_step_b``), ``weak-tagged-partial-commit-extra-step`` (the same
    extra step, committed only on the ``reg = []`` slice — the state a caller
    starts a fresh serializer in and the only slice the failing F2P test reads,
    gold everywhere else: the PARTIAL-DOMAIN shape at the effect site, raised by a
    G-EQ auditor as ``atk_3_partial_domain``), and ``weak-tagged-reuse-probe-text``
    (the extra step is NOT written back, but its text is emitted in an output slot
    instead of the text the arm's own step produced — verdict.md's
    ``atk_1c_extra_reuse``, also resolved=FALSE). All eight are
    configuration-perfect and assembly-perfect; five of them
    (``fresh-serializer``, ``drop-effect``, ``commit-extra-step``,
    ``partial-commit-extra-step``, and ``swap-steps`` at the point chosen for it)
    produce the byte-identical OUT text and differ only in the registry, which is
    what makes them attest to the second ``ensures`` specifically rather than to
    the first, while ``reuse-probe-text`` is the mirror — gold's registry exactly,
    wrong ``out`` — which attests that the FIRST clause pins WHICH registry each
    emitted segment was produced from.

  * THE BOUNDARY, stated once because three of the recorded attacks live on it. An
    extra ``renderSub`` application whose result is never written back and never
    reaches ``out`` is invisible to both clauses — necessarily, since it is not a
    different Lean program at all (measured: the rival's extracted program equals
    gold's by ``rfl``; in the branch-consumed shape by ``simp only [ite_self]``;
    and in the data-dependent shape ``if reg = [] then <it> else <gold>`` by the
    same ``ite_self``, since both arms are gold). It is therefore NOT shipped as a
    reject; it is shipped as the positive ``pos-tagged-uncommitted-probe``, and the
    refinement map says what it becomes in code (mapping.md §2.2: a step on a
    discarded probe), which is checked executably by axiom_check.py check 10 and
    conformance_check.py's probe slice and measured resolved=TRUE through the
    official harness, in all three shapes (refinement.md §F). The two ways such an
    application can become OBSERVABLE — write its result back (unconditionally, or
    on one slice) or emit its text — are exactly the three new rivals above, so
    the battery brackets the boundary from both sides.

  * FRAME / PERMISSION-MUTATION — RE-AIMED, no longer vacuous in its reason. The
    previous revision retired this class with "neither method declares a ``mut``
    binder — every input is an immutable value with no heap footprint". Both
    methods now declare ``mut reg``, so the class has a subject: a rival that
    fails to write the registry back (``weak-tagged-drop-effect``) or that
    writes back the wrong one (six of the seven other effect rivals) is exactly a
    frame-side wrong impl. This backend is still referentially transparent (no
    heap, no aliasing, no fractional permissions), so the sibling's sharpest
    shape — overwrite a read-only input held at a fractional permission — has no
    counterpart; but the ``mut`` half of the class is now shipped rather than
    declared vacuous. ``cfg``, ``tag`` and the ``SubObj`` handles remain
    read-only and are not mutated by any variant (directive 5).

  * CONTROL-FLOW / DIVERGENCE — VACUOUS here, for a carrier reason. This bundle
    sets ``loom.semantics.termination "total"`` (read the frozen file), so the
    verifier discharges a termination obligation and a diverging rival IS
    rejected — but it is not refutable HERE. Measured on the previous revision:
    a rival with an unbounded ``while`` at the ternary site is rejected (exit 1)
    with ``Decreasing annotations are required in total correctness semantics``,
    and that error is raised at the METHOD, so it also breaks the witness file
    (the stripped rival plus a trivial ``example : (1:Nat) = 1 := rfl`` fails
    identically, exit 1). The witness therefore cannot ELABORATE against the
    rival, which is the half that must succeed, so the case can only land as
    ``witness-unproven``: an inconclusive outcome, not a refutation. The
    rejection is also attributable to the missing ``decreasing`` annotation
    rather than to the ``ensures`` under audit. Neither method's frozen impl
    contains a loop (both are straight-line step sequences), so there is no
    diverging shape whose rejection these clauses decide. Not shipped, with that
    measurement as the reason.

  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. ``taggedPair`` /
    ``taggedPairReg`` / ``limitTriple`` / ``limitTripleReg`` are total ``def``s
    in the ``pure`` region written directly over the transparent assembly and
    the step fold, on top of the ONE opaque callee ``renderSub``; they are the
    WORK, not an opaque answer-key a wrong impl could echo — an impl must itself
    take the steps in order, on the composite's own registry, and assemble the
    results. The ``axioms`` region declares no ``axiom`` (``renderSub`` is
    ``opaque`` with no ``ensures``), so there is no consumed contract to attack.
    Honest positive controls stand in for the ungrounded-echo probe.

WITNESS PLACEMENT / BINDER COVERAGE. The eighteen reject witnesses probe
eighteen DISTINCT input points and move every input binder: ``cfg`` at both
{true, false}; the ``SubObj`` handles across {⟨1⟩..⟨44⟩}, no handle reused
across cases; ``tag`` across {"Eq","Ne"}; and the NEW binder ``reg`` at the
empty registry and at five distinct non-empty ones (``['p']``, ``['m']``,
``['d']``, ``['k']``, ``['n']``) — the empty case is the F2P-shaped one (the
caller starts a composite with an empty registry) and the non-empty ones are what
distinguish a step that starts from the composite's registry from one that starts
fresh. No binder is pinned across the battery. Both methods' obligations are defended and
attacked, and BOTH ``ensures`` clauses of each are attacked.

WITNESS TECHNIQUE. ``renderSub`` is opaque, so a refutation must condition on
the carrier. Two conditioning styles are used and both are satisfiable by
construction:

  * PIN a step's result at a concrete (cfg, reg, sub) triple, e.g.
    ``renderSub true [] ⟨1⟩ = (['A'], ['p'])``. Distinct triples are distinct
    applications of one opaque function, so any set of pins at pairwise-distinct
    triples is jointly satisfiable — nothing derives ``False`` from them, which
    is what the gate's ``consistency_probe`` re-checks per case.
  * for the configuration rivals, pin the SAME (reg, sub) under BOTH
    configurations with different text (``renderSub true ['p'] ⟨15⟩ = (['B'],
    ['q'])`` and ``renderSub false ['p'] ⟨15⟩ = (['C'], ['q'])``) — the
    configuration-observability fact G-AX validates against the real callee
    (mapping.md §3.1), stated as two assignments rather than a disequality
    because the assembled ``(out, reg)`` pair is then decidable by ``simp``.

Every pinned triple in a witness is distinct from every other triple in the same
witness, so no witness assumes a contradiction; the gate's probe is run for each
(re-measured with real builds: every probe exits 1, ``simp_all`` making no
progress / an unsolved ``False``, since no tactic can contradict distinct value
assignments to distinct applications of an opaque function). Three witnesses
bind NOTHING (the literal-frame rivals) and so cost no probe. No
``sorry``/``admit``/``native_decide``/``axiom``.

GOLD-SIDE FAILURE (the FORGERY test). Every reject case's gold-side failure is a
SEMANTIC refutation, not a tactic mismatch: the witness file has the frozen
obligations stripped, so nothing but the witness's own claim is being checked,
and against gold ``simp`` reduces the claim to an unsolved ``False`` (the
assembled pair it says differs is the pair gold produces). The two-file
experiment confirms the exit code carries information about the CLAIM and not
merely about the impl's shape: a forgery differing from a witness only in
asserting the EQUALITY instead of the disequality — i.e. claiming gold is
CORRECT at that point — builds successfully against gold (exit 0) and FAILS
against the rival (exit 1). Measured for the eight effect rivals, which are the
ones the two repair revisions add.

AXIOM lane: the sibling's ``AXIOM_TESTS`` are DROPPED — the axiom lane is G-AX's
job, and this bundle declares no ``axiom`` (``renderSub`` is ``opaque`` with no
asserted ``ensures`` — an A-reference validated by G-AX, mapping.md §3.1). This
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14531"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors: each is the WHOLE gold step sequence of one method,
# ---- wholly inside that method's `-- impl-start` / `-- impl-end` region and
# ---- unique in the file (both facts asserted at load by _swap). Every variant
# ---- reshapes exactly one of these blocks; the spec regions (axioms/pure/
# ---- pre/post + the method signatures + the two `ensures` of each) are never
# ---- touched, so same_spec holds and all four obligations survive with
# ---- byte-identical statements.
_GOLD_TP = (
    "    let ra := renderSub cfg reg a\n"
    "    reg := ra.2\n"
    "    let rb := renderSub cfg reg b\n"
    "    reg := rb.2\n"
    "    -- Assemble: tag, \"(\", a's text, \", \", b's text, \")\".\n"
    "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"
)
_GOLD_LIM = (
    "    let re := renderSub cfg reg e\n"
    "    reg := re.2\n"
    "    let rz := renderSub cfg reg z\n"
    "    reg := rz.2\n"
    "    let rz0 := renderSub cfg reg z0\n"
    "    reg := rz0.2\n"
    "    -- Assemble the comma-separated triple.\n"
    "    return \"Limit(\".toList ++ re.1 ++ \", \".toList ++ rz.1 ++ \", \".toList\n"
    "        ++ rz0.1 ++ \")\".toList"
)
assert _BASE.count(_GOLD_TP) == 1, "printTaggedPair impl region drifted"
assert _BASE.count(_GOLD_LIM) == 1, "printLimit impl region drifted"

# ---- the frozen tactic bodies, for the one case that adds a `have` in front of
# ---- one of them. Elided by the consumer spec view, so touching them changes no
# ---- statement.
_PROOF_TP = ("prove_correct printTaggedPair by\n"
             "  loom_solve\n"
             "  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]")
assert _BASE.count(_PROOF_TP) == 1, "printTaggedPair proof body drifted"


def _tp(new_body):
    """`_BASE` with printTaggedPair's step sequence replaced (impl region only)."""
    return _swap(_BASE, _GOLD_TP, new_body)


def _lim(new_body):
    """`_BASE` with printLimit's step sequence replaced (impl region only)."""
    return _swap(_BASE, _GOLD_LIM, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT whose value flows
# ---- through the opaque `renderSub`, so a witness reaches the impl through
# ---- Velvet's extractor (`extract_program_for printTaggedPair` gives
# ---- `printTaggedPairExec = NonDetT.run ∘ printTaggedPair`; `.run` names the
# ---- extracted program's result). With a `mut` parameter the extracted program
# ---- returns the PAIR of both observables —
# ----   printTaggedPairExec : Bool → List Char → SubObj → SubObj → List Char
# ----                           → DivM (List Char × List Char)
# ---- (measured with `#check`) — so a witness states its refutation against
# ---- `DivM.res (<the out post-image>, <the registry post-image>)` and refutes
# ---- whichever component the rival gets wrong. Checked in a file whose
# ---- `prove_correct` blocks are stripped, so no tactic script can interfere.
_EXTRACT_TP = "extract_program_for printTaggedPair\n\n"
_EXTRACT_LIM = "extract_program_for printLimit\n\n"

# The simp set every witness closes with: the two post-image `def`s of the
# method under attack, the two projections, and the extraction plumbing.
_SIMP_TP = "printTaggedPair, taggedPair, taggedPairReg, renderText, renderReg, NonDetT.run, pure"
_SIMP_LIM = "printLimit, limitTriple, limitTripleReg, renderText, renderReg, NonDetT.run, pure"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG on the SHAPE of the impl. Each keeps both `ensures`
    # clauses and the frozen `prove_correct ... by loom_solve; all_goals simp
    # only [...]` body; the reshape is definitionally the frozen pair of
    # post-images, so the script still closes the byte-identical obligations
    # (each verified out-of-band with a real build).
    # =====================================================================
    {
        "id": "pos-tagged-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: no intermediate `let`s for the steps at all. The text is
        # assembled inline through the `pure` projections, and the registry is
        # advanced by the same two-step fold. Byte-identical to gold on every
        # (cfg, tag, a, b, reg); the frozen tactic body still closes.
        "module": _tp(
            "    -- assemble inline, no step bindings; the registry is advanced by the\n"
            "    -- same two-step fold the text is read from\n"
            "    let o := tag ++ \"(\".toList ++ renderText cfg reg a ++ \", \".toList\n"
            "        ++ renderText cfg (renderReg cfg reg a) b ++ \")\".toList\n"
            "    reg := renderReg cfg (renderReg cfg reg a) b\n"
            "    return o"),
        "rationale": "structurally different CORRECT impl of printTaggedPair "
                     "(assemble inline through the `pure` projections instead of "
                     "binding each step, and advance the registry by the same "
                     "fold). Definitionally the frozen pair of post-images, so "
                     "both `ensures` clauses still discharge under the frozen "
                     "`loom_solve; all_goals simp only [...]`. If it FAILS => "
                     "SPEC-TOO-STRONG (a faithful correct impl of a different "
                     "shape rejected).",
    },
    {
        "id": "pos-tagged-name-later-step-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: NAME the second sub-object's step before the first one's —
        # but compute it from the registry the first step leaves, so the data
        # dependence is exactly gold's. This is the control that says the spec
        # pins the DEPENDENCE, not the textual order of the bindings. (Its
        # predecessor `pos-tagged-reorder-lets` claimed the strictly stronger
        # thing — that the two steps COMMUTE — which is false under the second
        # `ensures`; that shape is now the reject rival weak-tagged-swap-steps.)
        "module": _tp(
            "    -- name the SECOND sub-object's step first -- but compute it from the\n"
            "    -- registry the FIRST sub-object's step leaves, so the dependence is\n"
            "    -- unchanged\n"
            "    let rb := renderSub cfg (renderSub cfg reg a).2 b\n"
            "    let ra := renderSub cfg reg a\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "rationale": "structurally different CORRECT impl: the two step bindings "
                     "appear in the OPPOSITE textual order, with the later step "
                     "still computed FROM the registry the earlier step leaves. "
                     "The assembled text and the out-registry are byte-identical "
                     "to gold, so both `ensures` clauses still discharge under the "
                     "frozen script. This is the control that distinguishes "
                     "SPEC-TOO-STRONG-on-shape from the genuine obligation: the "
                     "spec pins the step DEPENDENCE, so reordering the bindings is "
                     "admissible while reordering the STEPS is not "
                     "(weak-tagged-swap-steps). If it FAILS => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-limit-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the ternary site, assembled inline without the three step
        # bindings, registry advanced by the three-step fold. Byte-identical to
        # gold; defends the ternary site's two obligations with a faithful
        # correct reshape.
        "module": _lim(
            "    -- assemble inline, no step bindings; the registry is advanced by the\n"
            "    -- same three-step fold the text is read from\n"
            "    let o := \"Limit(\".toList ++ renderText cfg reg e ++ \", \".toList\n"
            "        ++ renderText cfg (renderReg cfg reg e) z ++ \", \".toList\n"
            "        ++ renderText cfg (renderReg cfg (renderReg cfg reg e) z) z0\n"
            "        ++ \")\".toList\n"
            "    reg := renderReg cfg (renderReg cfg (renderReg cfg reg e) z) z0\n"
            "    return o"),
        "rationale": "structurally different CORRECT impl of printLimit (inline "
                     "assembly through the `pure` projections, registry advanced "
                     "by the same three-step fold). Definitionally the frozen pair "
                     "of post-images, so both `ensures` clauses still discharge "
                     "under the frozen script. If it FAILS => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-tagged-cheapest",
        "kind": "soundness",
        "expect": "verify",
        # The CHEAPEST correct impl: return the `pure` spec values directly, for
        # BOTH observables. Correct by construction, so it must verify. Note the
        # frozen tactic body is kept VERBATIM: `all_goals simp only [...]` is a
        # no-op when `loom_solve` has already closed everything (two lint
        # warnings, exit 0), where the previous revision's bare trailing `simp`
        # over-solved with `error: No goals to be solved` and had to be retuned.
        "module": _tp("    -- cheapest correct impl: the pure spec values themselves\n"
                      "    let o := taggedPair cfg tag a b reg\n"
                      "    reg := taggedPairReg cfg a b reg\n"
                      "    return o"),
        "rationale": "the CHEAPEST correct impl of printTaggedPair: return the "
                     "`pure` post-image `taggedPair cfg tag a b reg` and assign the "
                     "`pure` registry post-image `taggedPairReg cfg a b reg`. It "
                     "must verify — it is the pair of post-images by definition — "
                     "and it establishes that BOTH obligations are dischargeable at "
                     "all (admissibility of the post-images at every input), which "
                     "the reshape controls establish only up to their shared shape. "
                     "It is NOT the ungrounded-oracle hazard of directive 8: "
                     "`taggedPair`/`taggedPairReg` are transparent `def`s over the "
                     "assembly and the step fold, not an opaque answer-key, so "
                     "echoing them still performs the work. If it FAILS => "
                     "SPEC-TOO-STRONG (the spec rejects its own post-image).",
    },

    {
        "id": "pos-tagged-uncommitted-probe",
        "kind": "soundness",
        "expect": "verify",
        # THE SHAPE RECORDED AGAINST THIS CELL AS atk_1_extra_step_b, shipped as
        # a POSITIVE with its justification attached, because it MUST verify and
        # the reason is a theorem rather than an opinion: an application of
        # `renderSub` whose result is never written back is not a step of this
        # serializer (Solution.lean's `renderSub` docstring, mapping.md §2.2), and
        # the program this impl denotes is IDENTICAL to gold's. The elided tactic
        # body proves exactly that before closing the frozen obligations: the
        # extracted program's result is the PAIR of post-images at EVERY input, so
        # this impl is gold's program and no `ensures` over (out, reg) — indeed no
        # postcondition whatsoever — can separate them (refinement.md §F).
        "module": _swap(
            _tp("    -- ONE EXTRA application of `renderSub` on `b`, taken first and\n"
                "    -- never written back to `reg` (mapping.md 2.2 rule 2: an\n"
                "    -- UNCOMMITTED observation -- it materializes on a primed probe\n"
                "    -- that is discarded, not on the composite's own serializer)\n"
                "    let pre := renderSub cfg reg b\n"
                "    let ra := renderSub cfg reg a\n"
                "    reg := ra.2\n"
                "    let rb := renderSub cfg reg b\n"
                "    reg := rb.2\n"
                "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
            _PROOF_TP,
            "prove_correct printTaggedPair by\n"
            "  -- The uncommitted observation is not a step of this serializer, and\n"
            "  -- this `have` is the proof: at EVERY input the extracted program's\n"
            "  -- result is the pair of frozen post-images, i.e. this impl denotes\n"
            "  -- the same program as the frozen one (refinement.md §F).\n"
            "  have hprog : ∀ (cfg : Bool) (tag : List Char) (a b : SubObj)\n"
            "      (reg : List Char), (printTaggedPair cfg tag a b reg).run\n"
            "      = DivM.res (taggedPair cfg tag a b reg,\n"
            "                  taggedPairReg cfg a b reg) := by\n"
            "    intro cfg tag a b reg\n"
            "    simp [printTaggedPair, taggedPair, taggedPairReg, renderText,\n"
            "          renderReg, NonDetT.run, pure]\n"
            "  loom_solve\n"
            "  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]"),
        "rationale": "PASS SOURCE = the spec does not reject an impl that is GOLD. "
                     "This is verdict.md's atk_1_extra_step_b impl region verbatim, "
                     "and it must verify: `renderSub` is a function, so an "
                     "application whose result is never written back to `reg` "
                     "changes neither post-image — the in-region `have hprog` proves "
                     "that the extracted program's result is the PAIR of frozen "
                     "post-images at every input, so this impl and the frozen impl "
                     "are THE SAME PROGRAM (`rfl`-level; refinement.md §F ships the "
                     "standalone Lean proof and the `ite_self` variant). No "
                     "postcondition over (out, reg) can separate two impls with one "
                     "denotation, so demanding this be rejected is demanding an "
                     "inconsistent spec, not a stronger one. It is NOT a "
                     "verify-does-not-resolve shape: under the refinement map's rule "
                     "for an uncommitted observation (mapping.md §2.2, validated by "
                     "G-AX check 10 and diffed end to end by G-CONF slice D) its "
                     "faithful patch was applied to the instance at base_commit and "
                     "graded resolved=TRUE, F2P success "
                     "['test_python_relational','test_Rational'], P2P 84/84 "
                     "(refinement.md §F). The two neighbouring shapes that DO fail to "
                     "resolve are both rejected: writing the extra step back is "
                     "weak-tagged-commit-extra-step, and consuming the observation's "
                     "TEXT in an output slot is weak-tagged-reuse-probe-text. If it "
                     "FAILS => SPEC-TOO-STRONG on a shape that is definitionally "
                     "gold.",
    },

    # =====================================================================
    # EFFECT / STEP-SEQUENCE rivals — the class the previous revision could not
    # express, and the reason this cell was recorded BROKEN. Every rival here is
    # configuration-perfect and assembly-perfect: each sub-object is rendered
    # under the composite's own `cfg` and the literal frame is exact. They are
    # wrong about WHICH STEPS the serializer takes, in what order, from which
    # registry, and whether the composite's own registry is the one that
    # advances. The first three are the shapes measured against this cell.
    # =====================================================================

    # ---- THE RECORDED BREAK: the two steps taken in the wrong order ----
    {
        "id": "weak-tagged-swap-steps",
        "kind": "uniqueness",
        "expect": "reject",
        # verdict.md `atk_2_swap_rel`: same_spec against the PREVIOUS spec AND
        # verified against it, and its faithful refinement resolved=FALSE with
        # F2P failure ['test_python_relational']. Under the strengthened spec the
        # second sub-object's step no longer starts from the composite's incoming
        # registry, so both clauses are violated at once (measured: two residual
        # goals, `(renderSub cfg (renderSub cfg regOld b).2 a).2 = (renderSub cfg
        # (renderSub cfg regOld a).2 b).2` and the matching `out` equation).
        "module": _tp(
            "    -- take the SECOND sub-object's step FIRST: `b`'s step reads the\n"
            "    -- composite's incoming registry and `a`'s step reads what `b`'s left\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "MEASURED, not argued: this is verdict.md's atk_2_swap_rel, "
                      "whose faithful real counterpart (bind the second operand's "
                      "render before the first in the changed arm — `_rhs = "
                      "self._print(expr.rhs); _lhs = self._print(expr.lhs)`, then "
                      "assemble in the pinned order) was applied to the instance at "
                      "base_commit and graded: resolved=FALSE, completed=True, F2P "
                      "failure ['test_python_relational'], P2P 84/84 pass, with the "
                      "gold control resolving on the same harness. It would NOT "
                      "resolve, because the serializer registers each sub-object as "
                      "it renders it and the caller emits that registry ahead of the "
                      "composite, so swapping the two steps swaps two lines of the "
                      "expected output: the F2P assertion is literally "
                      "`python(Eq(x, y)) == \"x = Symbol('x')\\ny = Symbol('y')\\ne "
                      "= Eq(x, y)\"` and the swapped order emits `y = Symbol('y')` "
                      "first. A verifying rival of this shape is exactly the "
                      "verify-does-not-imply-resolve break recorded against this "
                      "cell.",
        "rationale": "REJECT from BOTH clauses. `reg = taggedPairReg cfg a b regOld` "
                     "pins the out-registry as `a`'s step then `b`'s; the rival "
                     "leaves `b`'s step then `a`'s. `out = taggedPair cfg tag a b "
                     "regOld` pins `b`'s TEXT as the text produced from the registry "
                     "`a`'s step left; the rival produces it from the composite's "
                     "incoming registry. Probed at cfg=true, tag=\"Eq\", a=⟨1⟩, "
                     "b=⟨2⟩, reg=[] — the F2P-shaped point (a composite is started "
                     "with an empty registry) — with four pins that make the two "
                     "orders produce the SAME text and DIFFERENT registries, so the "
                     "refutation lands on the second clause specifically. If it "
                     "VERIFIES => SPEC-TOO-WEAK (the step order unpinned), which is "
                     "the exact state this battery's predecessor certified as sound.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true [] (⟨1⟩ : SubObj) = (['A'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨2⟩ : SubObj) = (['B'], ['q']))\n"
                   "    (h3 : renderSub true [] (⟨2⟩ : SubObj) = (['B'], ['s']))\n"
                   "    (h4 : renderSub true ['s'] (⟨1⟩ : SubObj) = (['A'], ['t'])) :\n"
                   "    (printTaggedPair true \"Eq\".toList ⟨1⟩ ⟨2⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair true \"Eq\".toList ⟨1⟩ ⟨2⟩ [],\n"
                   "                  taggedPairReg true ⟨1⟩ ⟨2⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3, h4]\n",
    },

    # ---- the ternary twin of the recorded break ----
    {
        "id": "weak-limit-swap-steps",
        "kind": "uniqueness",
        "expect": "reject",
        # verdict.md `atk_5_swap_limit`: same_spec against the PREVIOUS spec and
        # verified against it. Under the strengthened spec the three steps must
        # run in argument order.
        "module": _lim(
            "    -- take the three steps in REVERSE order, then assemble in order\n"
            "    let rz0 := renderSub cfg reg z0\n"
            "    reg := rz0.2\n"
            "    let rz := renderSub cfg reg z\n"
            "    reg := rz.2\n"
            "    let re := renderSub cfg reg e\n"
            "    reg := re.2\n"
            "    return \"Limit(\".toList ++ re.1 ++ \", \".toList ++ rz.1 ++ \", \".toList\n"
            "        ++ rz0.1 ++ \")\".toList"),
        "refinement": "the faithful real counterpart is the changed ternary arm with "
                      "its three renders taken back-to-front (`tuple(map(self._print, "
                      "(z0, z, e)))` re-assembled in order). MEASURED on this "
                      "instance: verdict.md records atk_5_swap_limit.diff as "
                      "resolved=TRUE, and the reason is worth recording precisely. "
                      "The ternary arm IS graded by the second F2P test, but only "
                      "for the CONFIGURATION observable and only through `sstr` "
                      "(`sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) == "
                      "\"Limit(x, x, S(7)/2)\"`) — and the printer `sstr` builds "
                      "carries no declaration registry at all, so at the one place "
                      "the suite exercises this arm the step ORDER is unobservable. "
                      "This case is therefore recorded as a SPEC-STRENGTH case, not "
                      "as a verify-does-not-resolve break, and it is faithful all "
                      "the same: the reference behaviour renders the three "
                      "sub-objects in "
                      "ARGUMENT order (`tuple(map(self._print, (e, z, z0)))` — `map` "
                      "over a tuple is forced left to right), so the obligation the "
                      "spec adds is one the modeled reference satisfies. Pinning it "
                      "is what keeps the ternary arm's second clause from being "
                      "decoration; without this rival the ternary registry fold would "
                      "rest on no case at all.",
        "rationale": "REJECT from BOTH clauses of printLimit: the out-registry is "
                     "pinned as the fold `e` then `z` then `z0`, and each segment's "
                     "TEXT is pinned as the text produced from the registry the "
                     "PREVIOUS segments' steps left. The rival inverts the fold, so "
                     "every one of the three segments is produced from the wrong "
                     "registry. Probed at cfg=false, e=⟨5⟩, z=⟨6⟩, z0=⟨7⟩, reg=[] "
                     "with four pins along the rival's own chain, at which point its "
                     "FIRST emitted segment is ['X'] where the post-image's is "
                     "['E']. If it VERIFIES => SPEC-TOO-WEAK (the ternary step order "
                     "unpinned).",
        "witness": _EXTRACT_LIM +
                   "example (h1 : renderSub false [] (⟨5⟩ : SubObj) = (['E'], ['p']))\n"
                   "    (h2 : renderSub false [] (⟨7⟩ : SubObj) = (['Z'], ['q']))\n"
                   "    (h3 : renderSub false ['q'] (⟨6⟩ : SubObj) = (['Y'], ['r']))\n"
                   "    (h4 : renderSub false ['r'] (⟨5⟩ : SubObj) = (['X'], ['s'])) :\n"
                   "    (printLimit false ⟨5⟩ ⟨6⟩ ⟨7⟩ []).run\n"
                   "      ≠ DivM.res (limitTriple false ⟨5⟩ ⟨6⟩ ⟨7⟩ [],\n"
                   "                  limitTripleReg false ⟨5⟩ ⟨6⟩ ⟨7⟩ []) := by\n"
                   f"  simp [{_SIMP_LIM}, h1, h2, h3, h4]\n",
    },

    # ---- THE SECOND RECORDED BREAK: a throwaway serializer ----
    {
        "id": "weak-tagged-fresh-serializer",
        "kind": "uniqueness",
        "expect": "reject",
        # verdict.md `xtra_fresh_printer`: the refinement that honours the
        # PREVIOUS model literally — build a fresh serializer carrying the same
        # settings and render both sub-objects through it — was indistinguishable
        # from gold under that model and resolved=FALSE. Here it is expressible:
        # the steps start from an EMPTY registry and the composite's own registry
        # never advances.
        "module": _tp(
            "    -- render both sub-objects on a THROWAWAY serializer: same\n"
            "    -- configuration, but started from an EMPTY registry, and the\n"
            "    -- composite's own registry is left untouched\n"
            "    let ra := renderSub cfg [] a\n"
            "    let rb := renderSub cfg ra.2 b\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "MEASURED, not argued: this is verdict.md's "
                      "xtra_fresh_printer.diff (`_p = StrPrinter(dict("
                      "self._settings)); ... _p._print(expr.lhs), "
                      "_p._print(expr.rhs)`), applied to the instance at base_commit "
                      "and graded resolved=FALSE, completed=True, F2P failure "
                      "['test_python_relational'], P2P failures=[]. The returned "
                      "text is identical to gold's — the fresh serializer carries "
                      "the same configuration — but it is not the serializer whose "
                      "registry the caller emits, so the declarations for the two "
                      "sub-objects never reach the output. It would NOT resolve.",
        "rationale": "REJECT from `reg = taggedPairReg cfg a b regOld`: the rival "
                     "leaves the composite's registry exactly as it found it "
                     "(measured residual goal `regOld = (renderSub cfg (renderSub "
                     "cfg regOld a).2 b).2`), and its first step also starts from "
                     "`[]` rather than from `regOld`, so `out` is wrong too whenever "
                     "the incoming registry is non-empty. Probed at cfg=false, "
                     "tag=\"Eq\", a=⟨8⟩, b=⟨9⟩ and a NON-EMPTY incoming registry "
                     "reg=['p'] — the point that distinguishes the composite's own "
                     "serializer from a throwaway one — with two pins fixing gold's "
                     "chain, at which point gold's out-registry is ['r'] and the "
                     "rival's is ['p']. If it VERIFIES => SPEC-TOO-WEAK (the "
                     "IDENTITY of the serializer taking the steps unpinned), which "
                     "is the second break recorded against this cell.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub false ['p'] (⟨8⟩ : SubObj) = (['A'], ['q']))\n"
                   "    (h2 : renderSub false ['q'] (⟨9⟩ : SubObj) = (['B'], ['r'])) :\n"
                   "    (printTaggedPair false \"Eq\".toList ⟨8⟩ ⟨9⟩ ['p']).run\n"
                   "      ≠ DivM.res (taggedPair false \"Eq\".toList ⟨8⟩ ⟨9⟩ ['p'],\n"
                   "                  taggedPairReg false ⟨8⟩ ⟨9⟩ ['p']) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2]\n",
    },

    # ---- the steps are taken and chained, but never written back ----
    {
        "id": "weak-tagged-drop-effect",
        "kind": "uniqueness",
        "expect": "reject",
        # The purest attack on the second clause alone: the OUT text is
        # byte-identical to gold (the two steps are chained exactly as the spec
        # says) and only the composite's registry is left unadvanced. Measured:
        # ONE residual goal, the registry one.
        "module": _tp(
            "    -- correct TEXT: both steps are taken on the composite's serializer\n"
            "    -- and chained in argument order -- but the registry they produce is\n"
            "    -- only ever read to feed the next step, never written back\n"
            "    let ra := renderSub cfg reg a\n"
            "    let rb := renderSub cfg ra.2 b\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "the faithful real counterpart renders both sub-objects on the "
                      "active serializer, in order, and then RESTORES the "
                      "serializer's registry to what it was before the composite "
                      "(`_saved = list(self.symbols); ... ; self.symbols = _saved`). "
                      "It returns gold's exact string, so every string-level "
                      "assertion passes — and the caller's declaration preamble "
                      "loses both sub-objects, which is precisely what the F2P "
                      "assertion in test_python_relational grades: `python(Eq(x, y)) "
                      "== \"x = Symbol('x')\\ny = Symbol('y')\\ne = Eq(x, y)\"`, "
                      "which is exactly the pre-patch failure (the base_commit "
                      "expectation on that line is the bare `\"e = Eq(x, y)\"`). It "
                      "would NOT resolve, "
                      "for the same reason and by the same mechanism as the measured "
                      "xtra_fresh_printer break: the declarations never reach the "
                      "output.",
        "rationale": "REJECT from `reg = taggedPairReg cfg a b regOld` ALONE — this "
                     "is the rival that isolates the second clause: its `out` is "
                     "byte-identical to gold's at every input (measured: the "
                     "verifier leaves exactly ONE residual goal, `regOld = "
                     "(renderSub cfg (renderSub cfg regOld a).2 b).2`). Probed at "
                     "cfg=true, tag=\"Ne\", a=⟨10⟩, b=⟨11⟩, reg=['m'] with two pins "
                     "fixing the chain, at which point the post-image registry is "
                     "['o'] and the rival's is the untouched ['m'] while both `out` "
                     "components agree. If it VERIFIES => SPEC-TOO-WEAK (the effect "
                     "of the steps unpinned), i.e. the second `ensures` would be "
                     "decoration.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true ['m'] (⟨10⟩ : SubObj) = (['A'], ['n']))\n"
                   "    (h2 : renderSub true ['n'] (⟨11⟩ : SubObj) = (['B'], ['o'])) :\n"
                   "    (printTaggedPair true \"Ne\".toList ⟨10⟩ ⟨11⟩ ['m']).run\n"
                   "      ≠ DivM.res (taggedPair true \"Ne\".toList ⟨10⟩ ⟨11⟩ ['m'],\n"
                   "                  taggedPairReg true ⟨10⟩ ⟨11⟩ ['m']) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2]\n",
    },

    # ---- one sub-object stepped twice ----
    {
        "id": "weak-tagged-dup-step",
        "kind": "uniqueness",
        "expect": "reject",
        # verdict.md `atk_4_dup_render`: same_spec against the PREVIOUS spec and
        # verified against it (a pure model cannot see a discarded extra call).
        # Under the strengthened spec the number of steps is pinned.
        "module": _tp(
            "    -- take the FIRST sub-object's step TWICE, keeping the second result:\n"
            "    -- the text is unchanged but the composite's registry advances by\n"
            "    -- three steps instead of two\n"
            "    let ra0 := renderSub cfg reg a\n"
            "    reg := ra0.2\n"
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "the faithful real counterpart calls `self._print(expr.lhs)` "
                      "twice and keeps the second result. MEASURED on this instance: "
                      "verdict.md records atk_4_dup_render.diff as resolved=TRUE — "
                      "and the mechanism is worth recording, because it is the reason "
                      "this case is a SPEC-STRENGTH case rather than a "
                      "verify-does-not-resolve break. The real registry "
                      "DEDUPLICATES (`if symbol not in self.symbols: "
                      "self.symbols.append(symbol)` in the patched file's caller, "
                      "sympy/printing/python.py), so re-registering an already "
                      "registered sub-object is a no-op and the duplicate step is "
                      "invisible to the suite. The one-step model does not assume "
                      "that idempotence — an opaque step is a function of its "
                      "incoming registry and nothing more — so the spec pins the "
                      "reference's CALL SEQUENCE (each sub-object rendered exactly "
                      "once, `tuple(map(self._print, ...))` / `'%s(%s, %s)' % "
                      "(charmap[...], self._print(lhs), self._print(rhs))`), which "
                      "the reference satisfies. Recorded honestly rather than "
                      "claimed as a resolve failure it does not have.",
        "rationale": "REJECT from BOTH clauses: the out-registry becomes a THREE-step "
                     "fold (measured residual goal `(renderSub cfg (renderSub cfg "
                     "(renderSub cfg regOld a).2 a).2 b).2 = (renderSub cfg "
                     "(renderSub cfg regOld a).2 b).2`) and `b`'s text is produced "
                     "from that extra step's registry rather than from `a`'s. Probed "
                     "at cfg=true, tag=\"Eq\", a=⟨12⟩, b=⟨13⟩, reg=[] with four pins "
                     "chosen so the two impls emit the SAME text and differ only in "
                     "the registry. If it VERIFIES => SPEC-TOO-WEAK (the NUMBER of "
                     "steps unpinned, which is how a duplicated dispatch hides).",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true [] (⟨12⟩ : SubObj) = (['A'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨12⟩ : SubObj) = (['A'], ['q']))\n"
                   "    (h3 : renderSub true ['p'] (⟨13⟩ : SubObj) = (['B'], ['r']))\n"
                   "    (h4 : renderSub true ['q'] (⟨13⟩ : SubObj) = (['B'], ['u'])) :\n"
                   "    (printTaggedPair true \"Eq\".toList ⟨12⟩ ⟨13⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair true \"Eq\".toList ⟨12⟩ ⟨13⟩ [],\n"
                   "                  taggedPairReg true ⟨12⟩ ⟨13⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3, h4]\n",
    },

    # ---- the extra step is TAKEN AND WRITTEN BACK: one line away from the
    # ---- admitted pos-tagged-uncommitted-probe, and rejected ----
    {
        "id": "weak-tagged-commit-extra-step",
        "kind": "uniqueness",
        "expect": "reject",
        # This is the shape whose faithful materialization verdict.md MEASURED as
        # resolved=FALSE (atk_1_extra_step_b.diff — a live `self._print(expr.rhs)`
        # ahead of the two the arm needs, which registers the second sub-object
        # first and breaks test_python_relational). Under mapping.md §2.2 a LIVE
        # extra call is the refinement of a WRITTEN-BACK extra step, which is this
        # rival — and the spec rejects it. The impl differs from
        # pos-tagged-uncommitted-probe in exactly one line, `reg := pre.2`, which
        # is precisely the line the map reads as "this serializer took the step".
        "module": _tp(
            "    -- the extra step on `b` is taken AND COMMITTED: the composite's own\n"
            "    -- registry advances by three steps, and `b`'s own step then starts\n"
            "    -- from the registry that extra step left\n"
            "    let pre := renderSub cfg reg b\n"
            "    reg := pre.2\n"
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "MEASURED, not argued, and it is the measurement this cell was "
                      "recorded BROKEN on: verdict.md's atk_1_extra_step_b.diff — the "
                      "gold arm with one extra LIVE `self._print(expr.rhs)` ahead of "
                      "the two calls it needs — was applied to the instance at "
                      "base_commit and graded resolved=FALSE, completed=True, F2P "
                      "failure ['test_python_relational'], F2P success "
                      "['test_Rational'], P2P 84/84 pass. A live extra call is the "
                      "refinement of a WRITTEN-BACK extra step (mapping.md §2.2 rule "
                      "1), i.e. of THIS rival, and the reason it fails is exactly "
                      "what the second `ensures` pins: the extra step registers `y` "
                      "before `x`, so `python(Eq(x, y))` emits the two declarations "
                      "in the wrong order. The spec rejects it. (The impl that only "
                      "OBSERVES the extra step without writing it back is a different "
                      "program only in the map's eyes but the SAME program in Lean's; "
                      "it is shipped as pos-tagged-uncommitted-probe and its "
                      "materialization measures resolved=TRUE.)",
        "rationale": "REJECT from `reg = taggedPairReg cfg a b regOld` — the "
                     "out-registry becomes a THREE-step fold `b` then `a` then `b` "
                     "where the spec pins the two-step fold `a` then `b` — and from "
                     "`out` as well whenever the extra step's registry changes `a`'s "
                     "text. Probed at cfg=true, tag=\"Ne\", a=⟨41⟩, b=⟨42⟩, reg=[] "
                     "(the F2P-shaped empty incoming registry, the exact point "
                     "`python(Eq(x, y))` presents) with five pins chosen so the two "
                     "impls emit the SAME text and differ ONLY in the out-registry, "
                     "so the refutation is attributable to the second clause alone. "
                     "If it VERIFIES => SPEC-TOO-WEAK, and the measured "
                     "atk_1_extra_step_b.diff break would be a live spec hole rather "
                     "than a materialization of a rejected impl.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true [] (⟨42⟩ : SubObj) = (['B'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨41⟩ : SubObj) = (['A'], ['q']))\n"
                   "    (h3 : renderSub true ['q'] (⟨42⟩ : SubObj) = (['B'], ['r']))\n"
                   "    (h4 : renderSub true [] (⟨41⟩ : SubObj) = (['A'], ['s']))\n"
                   "    (h5 : renderSub true ['s'] (⟨42⟩ : SubObj) = (['B'], ['t'])) :\n"
                   "    (printTaggedPair true \"Ne\".toList ⟨41⟩ ⟨42⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair true \"Ne\".toList ⟨41⟩ ⟨42⟩ [],\n"
                   "                  taggedPairReg true ⟨41⟩ ⟨42⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3, h4, h5]\n",
    },

    # ---- the same extra step, committed only on the slice the F2P test reads:
    # ---- the classic PARTIAL-DOMAIN shape at the effect site ----
    {
        "id": "weak-tagged-partial-commit-extra-step",
        "kind": "uniqueness",
        "expect": "reject",
        # The data-dependent form of the case above: the extra step is committed
        # ONLY when the incoming registry is empty — exactly the state the caller
        # `python()` starts a fresh serializer in, i.e. the one slice the failing
        # F2P test exercises — and the arm is gold everywhere else. A spec whose
        # second clause held only "on average", or that could be discharged by a
        # case split that never reaches the empty-registry arm, would admit this.
        "module": _tp(
            "    -- PARTIAL DOMAIN: on the `reg = []` slice (the state a caller starts\n"
            "    -- a fresh serializer in) take and COMMIT an extra step on `b` first;\n"
            "    -- on every other slice be exactly gold\n"
            "    if reg = [] then\n"
            "      let pre := renderSub cfg reg b\n"
            "      reg := pre.2\n"
            "      let ra := renderSub cfg reg a\n"
            "      reg := ra.2\n"
            "      let rb := renderSub cfg reg b\n"
            "      reg := rb.2\n"
            "      return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList\n"
            "    else\n"
            "      let ra := renderSub cfg reg a\n"
            "      reg := ra.2\n"
            "      let rb := renderSub cfg reg b\n"
            "      reg := rb.2\n"
            "      return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "The refinement is the previous case's, confined to a slice: on "
                      "`reg = []` it is verdict.md's atk_1_extra_step_b.diff (a live "
                      "extra `self._print(expr.rhs)`, MEASURED resolved=FALSE with F2P "
                      "failure ['test_python_relational']) and elsewhere it is gold. "
                      "That makes it strictly worse than the unconditional shape rather "
                      "than better: the slice it corrupts is precisely the one the "
                      "failing F2P test reads (`python(Eq(x, y))` starts with "
                      "`symbols=[] functions=[]`), while every input a P2P test might "
                      "distinguish it on is left gold. Recorded because a G-EQ auditor "
                      "raised this shape (atk_3_partial_domain) after the "
                      "unconditional one; the DISCARDED variant of it is `ite_self` "
                      "over one program and is covered by pos-tagged-uncommitted-probe "
                      "plus refinement.md §F (its §2.2 materialization is measured "
                      "resolved=TRUE), and this is its committed, rejectable form.",
        "rationale": "REJECT from `reg = taggedPairReg cfg a b regOld` at a point IN the "
                      "guarded slice. Probed at cfg=false (the default configuration, so "
                      "the refutation cannot be confused with a configuration defect), "
                      "tag=\"Eq\", a=⟨43⟩, b=⟨44⟩, reg=[] with five pins chosen so `out` "
                      "is byte-identical to gold's and ONLY the out-registry differs "
                      "(['w'] vs ['y']) — the second clause alone. If it VERIFIES => "
                      "SPEC-TOO-WEAK, and worse than for the unconditional case: it "
                      "would mean the clause is discharged without ever reaching the "
                      "empty-registry arm, i.e. the obligation is vacuous on exactly "
                      "the slice the instance's failing test occupies.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub false [] (⟨44⟩ : SubObj) = (['B'], ['u']))\n"
                   "    (h2 : renderSub false ['u'] (⟨43⟩ : SubObj) = (['A'], ['v']))\n"
                   "    (h3 : renderSub false ['v'] (⟨44⟩ : SubObj) = (['B'], ['w']))\n"
                   "    (h4 : renderSub false [] (⟨43⟩ : SubObj) = (['A'], ['x']))\n"
                   "    (h5 : renderSub false ['x'] (⟨44⟩ : SubObj) = (['B'], ['y'])) :\n"
                   "    (printTaggedPair false \"Eq\".toList ⟨43⟩ ⟨44⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair false \"Eq\".toList ⟨43⟩ ⟨44⟩ [],\n"
                   "                  taggedPairReg false ⟨43⟩ ⟨44⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3, h4, h5]\n",
    },

    # ---- an uncommitted observation's TEXT reused in an output slot ----
    {
        "id": "weak-tagged-reuse-probe-text",
        "kind": "uniqueness",
        "expect": "reject",
        # The third reading verdict.md tried of the atk_1 impl
        # (atk_1c_extra_reuse.diff, resolved=FALSE): use the FIRST observation's
        # text for the second slot. That reading is not a refinement of atk_1 —
        # the two applications are at DIFFERENT registries, `regOld` and
        # `(renderSub cfg regOld a).2`, so they are different terms — and the impl
        # that really does reuse the earlier text is THIS one, which the spec
        # REJECTS. So no verifying impl materializes to that diff.
        "module": _tp(
            "    -- observe `b`'s step from the INCOMING registry, then take the two\n"
            "    -- steps correctly -- but emit the OBSERVATION's text in the second\n"
            "    -- slot instead of the text `b`'s own step produced\n"
            "    let pre := renderSub cfg reg b\n"
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ pre.1 ++ \")\".toList"),
        "refinement": "MEASURED: this is the impl behind verdict.md's "
                      "atk_1c_extra_reuse.diff (`_pre = self._print(expr.rhs)` before "
                      "the arm's own calls, with `_pre` interpolated into the second "
                      "slot), graded resolved=FALSE, completed=True, F2P failure "
                      "['test_python_relational'], P2P 84/84. It fails for the "
                      "recorded reason — the probed sub-object gets registered first "
                      "if the observation is live, and if it is not live the emitted "
                      "text is the one produced from the wrong registry — and the "
                      "spec rejects the impl, so the diff is the materialization of a "
                      "REJECTED impl and not of a verifying one. Recorded because "
                      "verdict.md offered it as an alternate reading of "
                      "atk_1_extra_step_b: it is not one, because `renderSub cfg "
                      "regOld b` and `renderSub cfg (renderSub cfg regOld a).2 b` are "
                      "applications at different registries, hence different terms, "
                      "and only the reuse impl HERE identifies them.",
        "rationale": "REJECT from `out = taggedPair cfg tag a b regOld`, whose second "
                     "segment is `renderText cfg (renderReg cfg regOld a) b` — the "
                     "text produced FROM the registry `a`'s step left. The rival "
                     "emits the text produced from the composite's INCOMING registry "
                     "instead, while its out-registry is exactly gold's, so the "
                     "refutation is attributable to the FIRST clause alone. This is "
                     "the case that shows the first `ensures` pins WHICH registry "
                     "each segment's text comes from, which is what makes an "
                     "uncommitted observation unusable as output. Probed at cfg=true, "
                     "tag=\"Eq\", a=⟨39⟩, b=⟨40⟩ and a NON-EMPTY incoming registry "
                     "reg=['n'] (a fifth registry value, used by no other case) with "
                     "three pins giving the observation and `b`'s own step DIFFERENT "
                     "text. If it VERIFIES => SPEC-TOO-WEAK (the provenance of the "
                     "emitted text unpinned).",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true ['n'] (⟨39⟩ : SubObj) = (['A'], ['q']))\n"
                   "    (h2 : renderSub true ['q'] (⟨40⟩ : SubObj) = (['B'], ['r']))\n"
                   "    (h3 : renderSub true ['n'] (⟨40⟩ : SubObj) = (['C'], ['s'])) :\n"
                   "    (printTaggedPair true \"Eq\".toList ⟨39⟩ ⟨40⟩ ['n']).run\n"
                   "      ≠ DivM.res (taggedPair true \"Eq\".toList ⟨39⟩ ⟨40⟩ ['n'],\n"
                   "                  taggedPairReg true ⟨39⟩ ⟨40⟩ ['n']) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3]\n",
    },

    # =====================================================================
    # CONFIGURATION rivals — observable (i), the band this cell was ported for
    # (meta.json band="settings-propagation"). Each renders some sub-object
    # under a configuration other than the composite's own, is correct on one
    # half of the `cfg` domain, and wrong on the other. Both halves, both
    # methods, and the FIRST, MIDDLE and THIRD sub-object positions.
    # =====================================================================

    # ---- printTaggedPair, cfg=true half ----
    {
        "id": "weak-tagged-drop-cfg",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image defect at the binary site: the second sub-object's step
        # is taken under the DEFAULT configuration instead of the active `cfg`.
        # Correct on the entire `cfg = false` half.
        "module": _tp(
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub false reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "this is the pre-image state on this arm: a sub-object rendered "
                      "by a serializer carrying a fresh DEFAULT configuration rather "
                      "than the active one, so the configuration is DROPPED for that "
                      "sub-object. Its faithful real patch is the empty change on "
                      "this arm — precisely the state the failing tests fail on: with "
                      "the non-default configuration active the tests require the "
                      "sub-object rendered in its configured surface form "
                      "(`sstr(Eq(x, 2/3), sympy_integers=True) == 'Eq(x, S(2)/3)'`), "
                      "but the default-rendered form differs, so the assertion stays "
                      "RED. It would NOT resolve.",
        "rationale": "REJECT from `out = taggedPair cfg tag a b regOld`, whose second "
                     "segment is `renderText cfg (renderReg cfg regOld a) b`: the "
                     "rival forwards the default configuration there. At `cfg = "
                     "true` the segments differ whenever the two configurations of "
                     "`b` produce different text. Probed at cfg=true, tag=\"Eq\", "
                     "a=⟨14⟩, b=⟨15⟩, reg=[] under three pins that fix the same "
                     "(registry, sub-object) under BOTH configurations with "
                     "different text — the configuration-observability fact G-AX "
                     "validates — and the same out-registry, so the refutation lands "
                     "on the FIRST clause with the second agreeing. If it VERIFIES "
                     "=> SPEC-TOO-WEAK (the configuration unpinned at the second "
                     "sub-object).",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true [] (⟨14⟩ : SubObj) = (['A'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨15⟩ : SubObj) = (['B'], ['q']))\n"
                   "    (h3 : renderSub false ['p'] (⟨15⟩ : SubObj) = (['C'], ['q'])) :\n"
                   "    (printTaggedPair true \"Eq\".toList ⟨14⟩ ⟨15⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair true \"Eq\".toList ⟨14⟩ ⟨15⟩ [],\n"
                   "                  taggedPairReg true ⟨14⟩ ⟨15⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3]\n",
    },

    # ---- printTaggedPair, cfg=false half: the MIRROR ----
    {
        "id": "weak-tagged-force-cfg",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR: the first sub-object's step is taken UNCONDITIONALLY under
        # the non-default configuration, ignoring the active `cfg` the other way.
        "module": _tp(
            "    let ra := renderSub true reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "a counterpart that renders a sub-object UNCONDITIONALLY under "
                      "the non-default configuration ignores the active setting the "
                      "other way. Its faithful real patch fails the "
                      "DEFAULT-configuration test, which requires the sub-object in "
                      "its plain surface form (`sstr(Eq(x, 2/3)) == 'Eq(x, 2/3)'`): "
                      "the forced non-default rendering differs, so that assertion "
                      "stays RED. It would NOT resolve.",
        "rationale": "REJECT from `out = taggedPair cfg tag a b regOld`, whose first "
                     "segment is `renderText cfg regOld a`: the rival forces the "
                     "non-default configuration there. Probed at cfg=false, "
                     "tag=\"Ne\", a=⟨16⟩, b=⟨17⟩, reg=[] with three pins fixing the "
                     "first sub-object under BOTH configurations (different text, "
                     "same out-registry, so the rest of the chain is unaffected and "
                     "the refutation is about the configuration and nothing else). "
                     "Refuted at cfg=false — the OTHER half of the domain from "
                     "weak-tagged-drop-cfg. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub false [] (⟨16⟩ : SubObj) = (['A'], ['p']))\n"
                   "    (h2 : renderSub true [] (⟨16⟩ : SubObj) = (['C'], ['p']))\n"
                   "    (h3 : renderSub false ['p'] (⟨17⟩ : SubObj) = (['B'], ['q'])) :\n"
                   "    (printTaggedPair false \"Ne\".toList ⟨16⟩ ⟨17⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair false \"Ne\".toList ⟨16⟩ ⟨17⟩ [],\n"
                   "                  taggedPairReg false ⟨16⟩ ⟨17⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2, h3]\n",
    },

    # ---- printLimit, cfg=true half, THIRD position ----
    {
        "id": "weak-limit-drop-cfg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _lim(
            "    let re := renderSub cfg reg e\n"
            "    reg := re.2\n"
            "    let rz := renderSub cfg reg z\n"
            "    reg := rz.2\n"
            "    let rz0 := renderSub false reg z0\n"
            "    reg := rz0.2\n"
            "    return \"Limit(\".toList ++ re.1 ++ \", \".toList ++ rz.1 ++ \", \".toList\n"
            "        ++ rz0.1 ++ \")\".toList"),
        "refinement": "the same propagation defect at the ternary site: the third "
                      "sub-object's step is taken under a fresh default "
                      "configuration rather than the active one. Its faithful real "
                      "patch leaves `z0` interpolated bare in the changed arm, so "
                      "the non-default-configuration rendering of that sub-object "
                      "never happens: the F2P assertion on this composite is "
                      "literally about the THIRD sub-object "
                      "(`sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) == "
                      "\"Limit(x, x, S(7)/2)\"`) and the default-rendered form is "
                      "`7/2`, so it stays RED. It would NOT resolve.",
        "rationale": "REJECT from `out = limitTriple cfg e z z0 regOld`, whose third "
                     "segment is rendered under `cfg`: the rival forwards the "
                     "default. Probed at cfg=true, e=⟨18⟩, z=⟨19⟩, z0=⟨20⟩ and a "
                     "NON-EMPTY incoming registry reg=['d'] (the `reg` binder is "
                     "moved here as well), with four pins fixing the chain and the "
                     "third sub-object under both configurations. If it VERIFIES => "
                     "SPEC-TOO-WEAK.",
        "witness": _EXTRACT_LIM +
                   "example (h1 : renderSub true ['d'] (⟨18⟩ : SubObj) = (['E'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨19⟩ : SubObj) = (['Z'], ['q']))\n"
                   "    (h3 : renderSub true ['q'] (⟨20⟩ : SubObj) = (['W'], ['r']))\n"
                   "    (h4 : renderSub false ['q'] (⟨20⟩ : SubObj) = (['V'], ['r'])) :\n"
                   "    (printLimit true ⟨18⟩ ⟨19⟩ ⟨20⟩ ['d']).run\n"
                   "      ≠ DivM.res (limitTriple true ⟨18⟩ ⟨19⟩ ⟨20⟩ ['d'],\n"
                   "                  limitTripleReg true ⟨18⟩ ⟨19⟩ ⟨20⟩ ['d']) := by\n"
                   f"  simp [{_SIMP_LIM}, h1, h2, h3, h4]\n",
    },

    # ---- printLimit, cfg=true half, MIDDLE position ----
    {
        "id": "weak-limit-middle-drop-cfg",
        "kind": "uniqueness",
        "expect": "reject",
        # The interior position: every other propagation rival mishandles a
        # FIRST or a LAST sub-object.
        "module": _lim(
            "    let re := renderSub cfg reg e\n"
            "    reg := re.2\n"
            "    let rz := renderSub false reg z\n"
            "    reg := rz.2\n"
            "    let rz0 := renderSub cfg reg z0\n"
            "    reg := rz0.2\n"
            "    return \"Limit(\".toList ++ re.1 ++ \", \".toList ++ rz.1 ++ \", \".toList\n"
            "        ++ rz0.1 ++ \")\".toList"),
        "refinement": "the propagation defect at the INTERIOR position: the middle "
                      "sub-object is rendered under a fresh default configuration "
                      "while its two neighbours track the active one. Its faithful "
                      "real patch is a partial change — two of the three "
                      "interpolations become `self._print(...)` and one stays bare — "
                      "so the non-default-configuration assertion on this composite "
                      "still gets the default-rendered middle sub-object and stays "
                      "RED. It would NOT resolve.",
        "rationale": "REJECT from `out = limitTriple cfg e z z0 regOld`, whose SECOND "
                     "segment is rendered under `cfg`. Probed at cfg=true, e=⟨21⟩, "
                     "z=⟨22⟩, z0=⟨23⟩, reg=[] with three pins (the middle "
                     "sub-object under both configurations, same out-registry, so "
                     "the third step is unaffected and only the middle segment "
                     "differs). This pins the one sub-object POSITION no other rival "
                     "drives. If it VERIFIES => SPEC-TOO-WEAK (the configuration "
                     "unpinned at the interior position).",
        "witness": _EXTRACT_LIM +
                   "example (h1 : renderSub true [] (⟨21⟩ : SubObj) = (['E'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨22⟩ : SubObj) = (['Z'], ['q']))\n"
                   "    (h3 : renderSub false ['p'] (⟨22⟩ : SubObj) = (['Y'], ['q'])) :\n"
                   "    (printLimit true ⟨21⟩ ⟨22⟩ ⟨23⟩ []).run\n"
                   "      ≠ DivM.res (limitTriple true ⟨21⟩ ⟨22⟩ ⟨23⟩ [],\n"
                   "                  limitTripleReg true ⟨21⟩ ⟨22⟩ ⟨23⟩ []) := by\n"
                   f"  simp [{_SIMP_LIM}, h1, h2, h3]\n",
    },

    # ---- printLimit, cfg=false half: the MIRROR at the FIRST position ----
    {
        "id": "weak-limit-force-cfg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _lim(
            "    let re := renderSub true reg e\n"
            "    reg := re.2\n"
            "    let rz := renderSub cfg reg z\n"
            "    reg := rz.2\n"
            "    let rz0 := renderSub cfg reg z0\n"
            "    reg := rz0.2\n"
            "    return \"Limit(\".toList ++ re.1 ++ \", \".toList ++ rz.1 ++ \", \".toList\n"
            "        ++ rz0.1 ++ \")\".toList"),
        "refinement": "a counterpart that renders the first sub-object of the ternary "
                      "composite unconditionally under the non-default configuration "
                      "ignores the active setting the other way. Its faithful real "
                      "patch fails the default-configuration assertion on this "
                      "composite, which requires that sub-object in its plain "
                      "surface form. It would NOT resolve.",
        "rationale": "REJECT from `out = limitTriple cfg e z z0 regOld`, whose first "
                     "segment is rendered under `cfg`: the rival forces the "
                     "non-default configuration there. Probed at cfg=false, e=⟨24⟩, "
                     "z=⟨25⟩, z0=⟨26⟩, reg=[] with two pins fixing the first "
                     "sub-object under both configurations (different text, same "
                     "out-registry). Refuted at cfg=false — varying `cfg` at the "
                     "ternary site too. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _EXTRACT_LIM +
                   "example (h1 : renderSub false [] (⟨24⟩ : SubObj) = (['E'], ['p']))\n"
                   "    (h2 : renderSub true [] (⟨24⟩ : SubObj) = (['D'], ['p'])) :\n"
                   "    (printLimit false ⟨24⟩ ⟨25⟩ ⟨26⟩ []).run\n"
                   "      ≠ DivM.res (limitTriple false ⟨24⟩ ⟨25⟩ ⟨26⟩ [],\n"
                   "                  limitTripleReg false ⟨24⟩ ⟨25⟩ ⟨26⟩ []) := by\n"
                   f"  simp [{_SIMP_LIM}, h1, h2]\n",
    },

    # =====================================================================
    # ASSEMBLY rivals — observable (ii). Every rival above either routes a
    # sub-object through the wrong configuration or takes the wrong steps; none
    # is wrong about the string being assembled around the segments. These five
    # are configuration-perfect AND step-perfect (the registry fold is exactly
    # gold's) and wrong in the head token, a separator, or the ORDER the
    # segments are emitted in. Without them the reject lane would attest to the
    # configuration and the step sequence and say nothing about the assembly.
    # =====================================================================

    # ---- the head token must actually be emitted ----
    {
        "id": "weak-tagged-drop-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tp(
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return \"(\".toList ++ ra.1 ++ \", \".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "a counterpart that assembles the parenthesised, "
                      "comma-separated operand list but omits the head token emits "
                      "`(lhs, rhs)` where every test expects `Head(lhs, rhs)`. Its "
                      "faithful real patch fails the serialization assertions under "
                      "BOTH configurations — the expected text does not start that "
                      "way — so they stay RED. It would NOT resolve.",
        "rationale": "REJECT from `out = taggedPair cfg tag a b regOld`, whose "
                     "leading segment is `tag`: the rival drops it. Refuted "
                     "UNCONDITIONALLY (no pin at all): at tag=\"Ne\" the post-image "
                     "begins with 'N' and the rival's output with '(', a literal "
                     "clash `simp` settles on the concrete list frame however the "
                     "opaque segments render. Probed at cfg=false, tag=\"Ne\", "
                     "a=⟨27⟩, b=⟨28⟩, reg=[] — an input point no other case uses. "
                     "If it VERIFIES => SPEC-TOO-WEAK (the head token unpinned).",
        "witness": _EXTRACT_TP +
                   "example : (printTaggedPair false \"Ne\".toList ⟨27⟩ ⟨28⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair false \"Ne\".toList ⟨27⟩ ⟨28⟩ [],\n"
                   "                  taggedPairReg false ⟨27⟩ ⟨28⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}]\n",
    },

    # ---- the separator is `", "`, not `","` ----
    {
        "id": "weak-tagged-thin-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tp(
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ ra.1 ++ \",\".toList ++ rb.1 ++ \")\".toList"),
        "refinement": "a counterpart that separates the two operands with a bare "
                      "comma instead of comma-space produces `Head(lhs,rhs)` where "
                      "the expected serialization is `Head(lhs, rhs)`. Its faithful "
                      "real patch fails the serialization assertions on that one "
                      "character under both configurations. It would NOT resolve.",
        "rationale": "REJECT from `out = taggedPair cfg tag a b regOld`, whose "
                     "operand separator is the two-element list `\", \"`: the rival "
                     "emits the one-element `\",\"`. Refuted UNCONDITIONALLY — the "
                     "missing space is a literal clash in the assembled frame "
                     "regardless of the opaque segments, so no pin is needed. A "
                     "NEAR-MISS, the tightest assembly probe at the binary site. "
                     "Probed at cfg=false, tag=\"Eq\", a=⟨29⟩, b=⟨30⟩, reg=[]. If "
                     "it VERIFIES => SPEC-TOO-WEAK (the separator unpinned).",
        "witness": _EXTRACT_TP +
                   "example : (printTaggedPair false \"Eq\".toList ⟨29⟩ ⟨30⟩ []).run\n"
                   "      ≠ DivM.res (taggedPair false \"Eq\".toList ⟨29⟩ ⟨30⟩ [],\n"
                   "                  taggedPairReg false ⟨29⟩ ⟨30⟩ []) := by\n"
                   f"  simp [{_SIMP_TP}]\n",
    },

    # ---- the ORDER the segments are EMITTED in (binary site) ----
    {
        "id": "weak-tagged-transpose",
        "kind": "uniqueness",
        "expect": "reject",
        # Configuration perfect, STEP SEQUENCE perfect (the registry fold is
        # gold's exactly) — only the two rendered texts are emitted in the wrong
        # slots. Independent of weak-tagged-swap-steps, which reorders the STEPS
        # and assembles in the right slots.
        "module": _tp(
            "    let ra := renderSub cfg reg a\n"
            "    reg := ra.2\n"
            "    let rb := renderSub cfg reg b\n"
            "    reg := rb.2\n"
            "    return tag ++ \"(\".toList ++ rb.1 ++ \", \".toList ++ ra.1 ++ \")\".toList"),
        "refinement": "a counterpart that emits the two operands of a binary head in "
                      "the opposite slots serializes `Head(rhs, lhs)`. Its faithful "
                      "real patch fails the serialization assertions wherever the "
                      "two operands differ — which is the case in the tested "
                      "expressions — so they stay RED. It would NOT resolve.",
        "rationale": "REJECT from `out = taggedPair cfg tag a b regOld`, which pins "
                     "the first operand's text in the first slot: the rival "
                     "transposes them while taking exactly gold's steps, so its "
                     "out-registry is gold's and only `out` is wrong. Probed at "
                     "cfg=true, tag=\"Ne\", a=⟨31⟩, b=⟨32⟩ and a non-empty incoming "
                     "registry reg=['k'] under two pins giving the two sub-objects "
                     "DIFFERENT text. Attacks the emission ORDER, which no "
                     "configuration and no step rival touches. If it VERIFIES => "
                     "SPEC-TOO-WEAK.",
        "witness": _EXTRACT_TP +
                   "example (h1 : renderSub true ['k'] (⟨31⟩ : SubObj) = (['A'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨32⟩ : SubObj) = (['B'], ['q'])) :\n"
                   "    (printTaggedPair true \"Ne\".toList ⟨31⟩ ⟨32⟩ ['k']).run\n"
                   "      ≠ DivM.res (taggedPair true \"Ne\".toList ⟨31⟩ ⟨32⟩ ['k'],\n"
                   "                  taggedPairReg true ⟨31⟩ ⟨32⟩ ['k']) := by\n"
                   f"  simp [{_SIMP_TP}, h1, h2]\n",
    },

    # ---- the ternary site's literal frame ----
    {
        "id": "weak-limit-thin-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _lim(
            "    let re := renderSub cfg reg e\n"
            "    reg := re.2\n"
            "    let rz := renderSub cfg reg z\n"
            "    reg := rz.2\n"
            "    let rz0 := renderSub cfg reg z0\n"
            "    reg := rz0.2\n"
            "    return \"Limit(\".toList ++ re.1 ++ \",\".toList ++ rz.1 ++ \", \".toList\n"
            "        ++ rz0.1 ++ \")\".toList"),
        "refinement": "a counterpart that separates the first two sub-objects of the "
                      "ternary composite with a bare comma instead of comma-space "
                      "emits one character short of the expected serialization, "
                      "under both configurations. It would NOT resolve.",
        "rationale": "REJECT from `out = limitTriple cfg e z z0 regOld`, whose first "
                     "inter-segment separator is the two-element list `\", \"`: the "
                     "rival emits the one-element `\",\"`. Refuted UNCONDITIONALLY "
                     "at cfg=false, e=⟨33⟩, z=⟨34⟩, z0=⟨35⟩, reg=[] — a literal "
                     "clash whatever the opaque segments render to, so no pin is "
                     "needed and no probe is owed. Gives the ternary obligation its "
                     "own literal-frame rival, which the order rivals do not. If it "
                     "VERIFIES => SPEC-TOO-WEAK (the ternary separator unpinned).",
        "witness": _EXTRACT_LIM +
                   "example : (printLimit false ⟨33⟩ ⟨34⟩ ⟨35⟩ []).run\n"
                   "      ≠ DivM.res (limitTriple false ⟨33⟩ ⟨34⟩ ⟨35⟩ [],\n"
                   "                  limitTripleReg false ⟨33⟩ ⟨34⟩ ⟨35⟩ []) := by\n"
                   f"  simp [{_SIMP_LIM}]\n",
    },

    # ---- the ORDER the segments are EMITTED in (ternary site) ----
    {
        "id": "weak-limit-transpose",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _lim(
            "    let re := renderSub cfg reg e\n"
            "    reg := re.2\n"
            "    let rz := renderSub cfg reg z\n"
            "    reg := rz.2\n"
            "    let rz0 := renderSub cfg reg z0\n"
            "    reg := rz0.2\n"
            "    return \"Limit(\".toList ++ rz0.1 ++ \", \".toList ++ rz.1 ++ \", \".toList\n"
            "        ++ re.1 ++ \")\".toList"),
        "refinement": "a counterpart that emits the first and third sub-objects of "
                      "the ternary composite in swapped slots serializes the triple "
                      "in the wrong order. Its faithful real patch fails the "
                      "serialization assertions on this composite wherever those two "
                      "sub-objects differ. It would NOT resolve.",
        "rationale": "REJECT from `out = limitTriple cfg e z z0 regOld`, which pins "
                     "the three texts in their slots: the rival emits the third "
                     "where the first belongs and vice versa, while taking exactly "
                     "gold's three steps (so its out-registry is gold's and only "
                     "`out` is wrong — this is the ternary ORDER-of-emission case, "
                     "independent of weak-limit-swap-steps which reorders the "
                     "STEPS). Probed at cfg=true, e=⟨36⟩, z=⟨37⟩, z0=⟨38⟩, reg=[] "
                     "under three pins giving the three sub-objects different text. "
                     "If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _EXTRACT_LIM +
                   "example (h1 : renderSub true [] (⟨36⟩ : SubObj) = (['E'], ['p']))\n"
                   "    (h2 : renderSub true ['p'] (⟨37⟩ : SubObj) = (['Z'], ['q']))\n"
                   "    (h3 : renderSub true ['q'] (⟨38⟩ : SubObj) = (['W'], ['r'])) :\n"
                   "    (printLimit true ⟨36⟩ ⟨37⟩ ⟨38⟩ []).run\n"
                   "      ≠ DivM.res (limitTriple true ⟨36⟩ ⟨37⟩ ⟨38⟩ [],\n"
                   "                  limitTripleReg true ⟨36⟩ ⟨37⟩ ⟨38⟩ []) := by\n"
                   f"  simp [{_SIMP_LIM}, h1, h2, h3]\n",
    },

    # =====================================================================
    # ADMISSIBILITY. Neither method has a `require` clause, but that is NOT the
    # reason to retire this lane: on a TOTAL carrier the analogue of
    # PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    # F2P-shaped input, which a positive that discharges it AT THAT CONCRETE
    # INPUT — by evaluation, as a `have`, before closing the frozen obligation
    # verbatim — tests directly. The positive controls above do not test it:
    # each closes the obligations as UNIVERSAL statements under the frozen
    # tactic, which can succeed without any concrete point ever being reduced.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen impl, unchanged; only the (elided) tactic body gains a
        # leading `have` that EVALUATES the method at a concrete F2P-shaped
        # input — a binary-tagged composite serialized under the non-default
        # configuration, from the EMPTY registry a caller starts with — and
        # shows the extracted program's result there really is the PAIR of
        # post-images. The frozen script then closes the real obligations
        # exactly as before, so nothing is weakened and the statements stay
        # byte-identical.
        "module": _swap(
            _BASE, _PROOF_TP,
            "prove_correct printTaggedPair by\n"
            "  have hreach : (printTaggedPair true \"Eq\".toList ⟨1⟩ ⟨2⟩ []).run\n"
            "      = DivM.res (taggedPair true \"Eq\".toList ⟨1⟩ ⟨2⟩ [],\n"
            "                  taggedPairReg true ⟨1⟩ ⟨2⟩ []) := by\n"
            "    simp [printTaggedPair, taggedPair, taggedPairReg, renderText,\n"
            "          renderReg, NonDetT.run, pure]\n"
            "  loom_solve\n"
            "  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]"),
        "rationale": "PASS SOURCE = printTaggedPair's TWO obligations are jointly "
                     "SATISFIABLE at a concrete F2P-shaped input: a binary-tagged "
                     "composite with head token \"Eq\" and two distinct sub-objects, "
                     "serialized under the NON-DEFAULT configuration cfg=true (the "
                     "half the failing tests exercise and the half a propagation "
                     "defect is visible on), starting from the EMPTY registry a "
                     "caller begins a composite with (the shape "
                     "`python(Eq(x, y))` presents). The in-region `have hreach` "
                     "EVALUATES the extracted program at that literal point and "
                     "shows its result is the PAIR `(taggedPair true \"Eq\".toList "
                     "⟨1⟩ ⟨2⟩ [], taggedPairReg true ⟨1⟩ ⟨2⟩ [])`, so both "
                     "post-images are reachable there BY COMPUTATION rather than "
                     "being an unsatisfiable demand no impl could meet — which "
                     "matters more now that there are two clauses, since a pair of "
                     "clauses can be jointly unsatisfiable while each is fine "
                     "alone. The frozen `loom_solve; all_goals simp only [...]` "
                     "still closes the real obligations afterwards; the `ensures` "
                     "clauses, the signature and every spec region are untouched "
                     "(only the elided tactic body differs), so the statements are "
                     "byte-identical and nothing is weakened. If it FAILS => "
                     "PRECOND-TOO-STRONG / the obligations are unsatisfiable at an "
                     "F2P-shaped input.",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 8 SPEC cases (2
# soundness positives incl. a grounded-oracle cheapest-impl control, 1
# admissibility, 5 uniqueness rivals) plus 2 AXIOM_TESTS. The two carriers are
# NOT the same partition: the sibling contracts FOUR functions
# (render_equation, render_directed_limit, render_operand, materialize) over a
# `PSeq[int]`/`List[int]` byte carrier with @Pure helpers (eq_text, limit_text,
# render_rational, digits) and @ContractOnly axioms (digits, coprime). This
# bundle models the purely-functional core as TWO methods (printTaggedPair,
# printLimit) over a `List Char` carrier, with the per-sub-object rendering STEP
# collapsed into ONE opaque callee `renderSub cfg reg sub` returning the (text,
# next-registry) PAIR (the configuration a boolean, the registry a `List Char`,
# the sub-object an opaque handle; mapping.md §2). The sibling's leaf
# `render_operand` and its `render_rational(wrap,p,q)` value-shape (S(...)
# wrapper / p-then-q digit order) are refined AWAY: the digit-level structure is
# not modeled here — `renderSub` pins no concrete text — so the nagini rivals
# attacking the WRAPPER PLACEMENT and the DIGIT ORDER at the leaf have no
# counterpart, and their argument re-sites onto the surviving observables.
#
#   sibling case                    kind            -> here                          status
#   -------------------------------------------------------------------------------------
#   pos-control-operand-reshape     soundness       -> pos-tagged-inline /
#                                                      pos-tagged-name-later-step-first  PORTED (as reshapes)
#   pos-control-equation-cheapest   soundness       -> pos-tagged-cheapest           PORTED (frozen tactic kept)
#   admiss-f2p-shape                admissibility   -> admiss-obligation-
#                                                      satisfiable-at-f2p-point      PORTED
#   partial-domain-drop-wrap        uniqueness      -> weak-tagged-drop-cfg /
#                                                      weak-limit-drop-cfg           RE-SITED
#   partial-domain-always-wrap      uniqueness      -> weak-tagged-force-cfg /
#                                                      weak-limit-force-cfg          RE-SITED
#   compound-bug-equation           uniqueness      -> weak-tagged-drop-cfg          RE-SITED (same site)
#   compound-bug-limit              uniqueness      -> weak-limit-drop-cfg /
#                                                      weak-limit-middle-drop-cfg    RE-SITED (same site)
#   value-swap-num-denom            uniqueness      -> weak-tagged-transpose /
#                                                      weak-limit-transpose          RE-SITED (order, not digits)
#   ax-render-sound                 axiom           -> (none)                        G-AX / no axiom
#   ax-domain-containment           axiom           -> (none)                        G-AX / no axiom
#
# 5 soundness positives + 1 admissibility + 18 uniqueness rivals = 24 cases.
#
# ADDED IN THE SECOND REPAIR REVISION (3 rivals + 1 positive, none of them a
# nagini port): the EXTRA-STEP family, the shapes recorded against this cell as
# atk_1_extra_step_b / atk_1c_extra_reuse / atk_1d_extra_branch /
# atk_3_partial_domain. The recorded break is an impl that names one extra
# `renderSub` application before gold's two steps. That application can be:
#   * WRITTEN BACK — the composite really takes three steps. Shipped as
#     weak-tagged-commit-extra-step, REJECTED by the second `ensures` (measured:
#     rejected, witness rival 1 / gold 0 / probe consistent). This is the shape
#     whose faithful patch verdict.md measured resolved=FALSE, so the recorded
#     break is now covered by a reject rival.
#   * WRITTEN BACK ON ONE SLICE ONLY — `if reg = [] then <commit it> else <gold>`,
#     the partial-domain form, corrupting exactly the slice `python(Eq(x, y))`
#     occupies. Shipped as weak-tagged-partial-commit-extra-step, REJECTED by the
#     second `ensures` at a point INSIDE the guarded slice (measured: rejected,
#     witness rival 1 / gold 0 / probe consistent), so the clause is not vacuous
#     on the F2P slice.
#   * DISCARDED BUT EMITTED — its text goes into an output slot. Shipped as
#     weak-tagged-reuse-probe-text, REJECTED by the FIRST `ensures` (it emits the
#     text produced from the composite's incoming registry where the spec pins the
#     text produced from the registry the first step left). This is
#     atk_1c_extra_reuse, also measured resolved=FALSE.
#   * DISCARDED AND UNUSED (including the branch-consumed `ite_self` shape) — the
#     SAME Lean program as gold, provably (`rfl`, resp. `simp only [ite_self]`),
#     so no postcondition can reject it. Shipped as the POSITIVE
#     pos-tagged-uncommitted-probe; its code image under mapping.md §2.2 is gold's
#     arm plus a discarded probe, gate-checked by G-AX check 10 and G-CONF's probe
#     slice and MEASURED resolved=TRUE (F2P both pass, P2P 84/84) through the
#     official harness. refinement.md §F carries the proof and the measurements.
#
# ADDED IN THE FIRST REPAIR REVISION (5 rivals, none of them a nagini port): the whole
# EFFECT / STEP-SEQUENCE family, which the previous spec had no clause for and
# the previous battery therefore could not express —
# weak-tagged-swap-steps, weak-limit-swap-steps, weak-tagged-fresh-serializer,
# weak-tagged-drop-effect, weak-tagged-dup-step. Three of the five are shapes
# MEASURED against this cell and recorded in verdict.md (atk_2_swap_rel and
# xtra_fresh_printer with resolved=FALSE and F2P failure
# ['test_python_relational']; atk_4_dup_render and atk_5_swap_limit verifying
# against the previous spec). Each was re-measured against the strengthened spec
# before landing: rejected (exit 1) with a SEMANTIC residual goal about
# `renderSub`, and the witness discriminates (rival 0 / gold 1 / probe 1).
#
# REMOVED IN THIS REVISION (1 positive control): `pos-tagged-reorder-lets`,
# which asserted that binding the second sub-object's render BEFORE the first
# MUST VERIFY, on the ground that "pure `let`s of independent expressions
# commute". Under the strengthened spec the two steps are NOT independent — the
# later one reads the registry the earlier one leaves — so that shape is a wrong
# impl, and it is precisely the shape whose faithful refinement was measured
# resolved=FALSE. It moves to the reject lane as weak-tagged-swap-steps. Its
# soundness duty (a reshape that reorders the bindings must still verify) is
# discharged by `pos-tagged-name-later-step-first`, which names the later step
# first while keeping the dependence — so the battery still fails loudly if the
# spec over-constrains the SHAPE of the impl, and no longer certifies the hole.
#
# RE-SITED (the ARGUMENT is unchanged; only the carrier is):
#  * partial-domain-drop-wrap (the pre-image state: always render the sub-object
#    under the default, correct only on the not-active half) IS the
#    configuration-dropped-for-a-sub-object rival: weak-tagged-drop-cfg (second
#    sub-object) and weak-limit-drop-cfg (third sub-object). The sibling's
#    compound-bug-equation / compound-bug-limit attack the SAME defect inline at
#    the compound site; on this carrier the leaf and the compound site are the
#    SAME method (`renderSub` is called directly in the method body), so one
#    per-site rival covers both.
#  * partial-domain-always-wrap (the mirror) IS weak-tagged-force-cfg /
#    weak-limit-force-cfg.
#  * value-swap-num-denom re-sites onto the SEGMENTS rather than the digits:
#    weak-tagged-transpose / weak-limit-transpose.
#
# VACUOUS — control-flow/divergence: not refutable here (the rejection is
#  attributable to a missing `decreasing` annotation, and the same error breaks
#  the witness file, so the case can only land inconclusive). Measured; see the
#  module docstring.
#
# RE-AIMED — frame/permission-mutation: previously retired on the ground that
#  "neither method declares a `mut` binder". Both now declare `mut reg`, so the
#  class has a subject and is SHIPPED (the eight effect rivals, of which
#  weak-tagged-drop-effect is exactly "the frame is not written back"). The
#  sibling's fractional-permission shape still has no counterpart on a
#  referentially transparent backend with no heap.
#
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job; this bundle declares NO
#  `axiom` (`renderSub` is `opaque` with no asserted `ensures` — an A-reference
#  validated by G-AX against the real callee, mapping.md §3.1). This gate ignores
#  AXIOM_TESTS regardless.
#
# COVERAGE. FOUR obligations (two methods x two clauses). Each METHOD is
# DEFENDED (printTaggedPair by pos-tagged-inline /
# pos-tagged-name-later-step-first / pos-tagged-cheapest /
# pos-tagged-uncommitted-probe; printLimit by
# pos-limit-inline), printTaggedPair's pair of clauses is additionally shown
# jointly SATISFIABLE at a concrete F2P-shaped input, and every clause is
# ATTACKED:
#
#   printTaggedPair  out, configuration: weak-tagged-drop-cfg (cfg=true, 2nd),
#                                        weak-tagged-force-cfg (cfg=false, 1st)
#                    out, assembly:      weak-tagged-drop-head (head token),
#                                        weak-tagged-thin-separator (separator),
#                                        weak-tagged-transpose (emission order)
#                    out ALONE:          weak-tagged-reuse-probe-text (an emitted
#                                          segment's REGISTRY PROVENANCE: gold's
#                                          registry, gold's step count, but the
#                                          second segment's text produced from the
#                                          incoming registry instead)
#                    reg (and out):      weak-tagged-swap-steps (step order),
#                                        weak-tagged-dup-step (step count)
#                    reg ALONE:          weak-tagged-drop-effect (never written back),
#                                        weak-tagged-fresh-serializer (throwaway
#                                          serializer, registry untouched),
#                                        weak-tagged-commit-extra-step (a third
#                                          step, written back),
#                                        weak-tagged-partial-commit-extra-step
#                                          (that third step written back on the
#                                          `reg = []` slice only)
#   printLimit       out, configuration: weak-limit-drop-cfg (cfg=true, 3rd),
#                                        weak-limit-middle-drop-cfg (cfg=true, 2nd),
#                                        weak-limit-force-cfg (cfg=false, 1st)
#                    out, assembly:      weak-limit-thin-separator (separator),
#                                        weak-limit-transpose (emission order)
#                    reg (and out):      weak-limit-swap-steps (step order)
#
# FOUR rivals refute on the SECOND clause alone (weak-tagged-drop-effect,
# weak-tagged-fresh-serializer, weak-tagged-commit-extra-step,
# weak-tagged-partial-commit-extra-step): their `out` is
# byte-identical to gold's at the probed point, so their rejection is attributable
# to `reg = ...Reg ...` and nothing else. That is what makes the added clause
# load-bearing rather than implied by the first one. Conversely the two transpose
# rivals and weak-tagged-reuse-probe-text take exactly gold's steps and leave
# exactly gold's registry, and are wrong only in `out`, so neither clause is
# redundant.
#
# The configuration domain is attacked on BOTH halves at BOTH methods; every
# `renderText cfg <...> <sub>` occurrence in the defended surface is driven by
# some rival — both binary positions and all THREE ternary positions including
# the interior one. `cfg` is varied (true and false) across the reject
# witnesses; `tag` takes both "Eq" and "Ne"; the `SubObj` handles are ⟨1⟩..⟨44⟩
# with no handle shared between two cases; and the incoming registry `reg` is
# [] in thirteen witnesses and ['p'] / ['m'] / ['d'] / ['k'] / ['n'] in the five
# that turn on the difference between the composite's own registry and a fresh
# one. So no binder is pinned and no two cases restate a refutation at a shared
# point.
#
# SPEC-HOLE PROBES run while repairing and NOT shipped, because the strengthened
# spec answered correctly on every one — recorded so the next auditor knows where
# the ground has been walked. Six wrong impls were built against the strengthened
# spec and ALL SIX were rejected (exit 1, each with a semantic residual goal
# about `renderSub` rather than a tactic complaint): the two step-order swaps,
# the throwaway serializer, the duplicated step, the dropped effect, and the
# dropped configuration. Three correct reshapes were built and ALL THREE verified
# (exit 0): the inline assembly, naming the later step first from the earlier
# step's registry, and the cheapest impl. The prepatch twin
# (Solution_prepatch.lean — the throwaway-serializer pre-image at BOTH methods)
# fails on all four obligations, which is what G-DIFF reads.
#
# SPEC-HOLE PROBES of the SECOND repair revision, likewise recorded rather than
# shipped. The question was whether the extra-step family could be closed in the
# spec at all, and the answer is a measured NO, so the closure went into the
# refinement map instead (mapping.md §2.2) and the battery brackets it:
#  * the extra-step impls' extracted programs were proved EQUAL to gold's — `rfl`
#    for the dead shape, `simp only [ite_self]` for the branch-consumed one and
#    for the data-dependent `if reg = [] then <it> else <gold>` one — in a
#    standalone file built by the real verifier (exit 0). Two programs with one
#    denotation satisfy the same postconditions, so NO `ensures` can reject them.
#  * the caller escape hatch was probed and does not exist in this backend: a
#    caller doing `let a ← incr reg; let b ← incr reg` does not thread `mut`
#    arguments (the callee's `(out, reg)` pair comes back as a VALUE and the
#    caller's binder is untouched), measured exit 1 with residual
#    `⊢ regOld = regOld + 2`. So no caller-level obligation can count steps either.
#  * the three shapes' §2.2 materializations were run through the official
#    harness and all resolve (F2P both, P2P 84/84), so demanding their rejection
#    would be SPEC-TOO-STRONG rather than a repair. refinement.md §F carries the
#    files, the exit codes and the resolve reports.
AXIOM_TESTS = []
