"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8548 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct collectInstanceAttrDocs`` obligation survives with
a byte-identical statement) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against a second subject that satisfies this same spec. On this
bundle the frozen solution cannot BE that second subject — its tester is stuck
in the kernel for every claim — so each reject case names a
``witness_reference`` instead; see the CARRIER NOTE.

=========================================================================
DEFENDED SURFACE  (one contracted method)
=========================================================================

  collectInstanceAttrDocs (existing : List String) (hierarchy : List ClassLevel)
      return (out : List Member)
    ensures out = collected existing (candidates hierarchy)

The method collects the members a class surfaces from the declarations spread
across its whole inheritance hierarchy. ``hierarchy`` is that hierarchy ordered
most-derived-first; each ``ClassLevel`` carries one class's identity (``owner``),
the member names it declares by annotation alone (``annots``, where the empty
string stands for an annotated identifier not reachable under this class's name),
and the documented instance attributes assigned inside its own namespace
(``attrs``). ``existing`` is the set of member identifiers already surfaced from
other sources. Each surfaced ``Member`` carries its identifier, the ``owner`` of
the class it is ATTRIBUTED to, and its ``doc`` (``none`` for an annotation-only
member, ``some d`` for a documented attribute). The single load-bearing
``ensures`` pins ``out`` to the fully-unfolded pure model:

  ``levelCandidates c = (c.annots.filter (· != "")).map (⟨·, c.owner, none⟩)``
                     ``++ c.attrs.map (⟨·.name, c.owner, some ·.doc⟩)``
  ``candidates h     = (h.map levelCandidates).flatten``
  ``collected e xs   = xs.foldl (collectStep e) []``
  ``collectStep e acc m = acc``        if ``m.name`` in ``e`` or already in ``acc``
  ``collectStep e acc m = acc ++ [m]`` otherwise

i.e. a left-to-right FIRST-OCCURRENCE fold over a per-class candidate stream in
which each class contributes its annotation-only names and then its own
documented attributes before the next class is considered.

The single top-level clause combines several independently-attackable
sub-obligations. Each is a separate observable, and each has its own rival below:

  * WHOLE-HIERARCHY: the stream ranges over EVERY class of ``hierarchy``, not the
    most-derived one alone. An attribute declared only on a base class must be
    surfaced when no more-derived class claims its identifier.
  * CLASS ORDER: classes are walked front-to-back (most-derived-first), so a
    shared identifier resolves to the most-derived contributor.
  * PER-CLASS INTERLEAVING: a class's annotations and that SAME class's
    documented attributes are resolved together, before the next class is
    reached — not as one hierarchy-wide annotation pass followed by a
    hierarchy-wide attribute pass.
  * PHASE ORDER WITHIN A CLASS: inside one class, annotation-only names come
    first, so an identifier a class both annotates and documents surfaces as the
    annotation (``doc = none``).
  * ATTRIBUTION: a candidate carries the ``owner`` of the CONTRIBUTING class, not
    of the class being documented. This is the component a consumer compares
    against the class it is documenting to decide whether to list the member at
    all, so it is fully observable and may not be left free.
  * DOC SHAPE: an annotation-only member's ``doc`` is ``none`` — distinguishable
    from ``some ""`` — and a documented attribute's is ``some`` of its docstring.
  * EMPTY-NAME FILTER: an ``annots`` entry that is the empty string is passed
    over (it stands for an annotated identifier not reachable under this class's
    name), while an ``attrs`` entry is not filtered.
  * DEDUP / FIRST-WINS, presence AND depth: the guard consults the WHOLE
    accumulator, so each identifier appears at most once however far apart its
    namesakes lie.
  * EXISTING FILTER: a candidate whose name is already in ``existing`` is
    dropped.
  * WITHIN-CLASS ATTR ORDER: one class's own ``attrs`` are consumed in analyzer
    order, so an identifier documented twice in one namespace keeps the first.

Both input binders are load-bearing: ``hierarchy`` supplies the candidate stream,
its per-class grouping, its order and every candidate's attribution and doc;
``existing`` supplies the pre-collected filter set. Neither is ``mut`` (both are
read-only structural descriptors); the method has NO ``require`` clause (the
pre-conditions region is empty), so the post-image must hold for EVERY value of
both.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY EVERY REJECT CASE NAMES A
``witness_reference``. The frozen impl is a forward ``while`` loop under
``loom.semantics.choice "demonic"``, so its extracted
``collectInstanceAttrDocsExec`` elaborates through ``Classical.choice`` and does
NOT reduce in the kernel. Measured directly:
``#print axioms collectInstanceAttrDocsTester`` on the frozen file reports
``depends on axioms: [propext, Classical.choice, Quot.sound]``, and a witness
stated against the frozen impl fails with ``did not reduce to `isTrue` or
`isFalse` `` — under plain ``decide`` AND under ``decide +kernel``.

That stuck reduction is NOT a discrimination signal, and this battery does not
treat it as one. The refutation was measured: the real witness (``tester … =
false``) and a FORGERY asserting the exact opposite (``tester … = true``, i.e.
that the frozen impl is *correct* at that input) BOTH fail against the frozen
solution with the identical stuck-reduction error, so the frozen file's exit code
carries no information about the claim. See
``swebench_unified.gates.pbt._STUCK_REDUCTION``.

So each reject case below carries an explicit ``witness_reference``: the
loop-free ``return collected existing (candidates hierarchy)`` impl (the same
source as the ``pos-return-model`` positive), which shares the frozen spec and
VERIFIES (measured exit 0), and whose extracted program DOES reduce by kernel
computation. The gate independently re-checks both of those properties before
using it. The inference: an impl the verifier ACCEPTS cannot violate its own
spec, so a genuine "the spec is violated at this input" statement must fail
there — and against a reducible subject that failure is a real semantic
refutation. Measured for every reject case: the witness elaborates against the
rival (exit 0) and fails against the reference with ``Tactic `decide` proved that
the proposition … is false`` (exit 1) — the kernel deciding the claim, not
stalling on it. The same reference decides the opposite claim green (exit 0),
which is what shows its exit codes are informative at all.

Naming the reference explicitly rather than leaning on the gate's
positives-fallback is deliberate: the fallback is a recovery path, so a battery
that relies on it silently records its discrimination against a subject the
manifest never names. The carrier at every witness is otherwise concrete
(``List String`` / ``List ClassLevel`` literals whose leaves are ``String``
literals and ``Option String`` constructors; ``ClassLevel`` and ``Member`` derive
``DecidableEq``), so no hypothesis is assumed and there is no joint-satisfiability
obligation.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally different but
    behaviourally identical correct impls must verify, else the spec is
    SPEC-TOO-STRONG on the impl shape: return the grounded pure model directly
    (no loop); the frozen loop with the per-candidate kept result named; and a
    NESTED fold that never materialises the flattened stream at all (equal to the
    post-image only via the foldl/flatten interchange law, so its proof must
    invoke a real theorem rather than unfold).
  * ADMISSIBILITY — RE-AIMED. The method has NO ``require`` clause, so the
    sibling's "a normal input satisfies the precondition" probe is degenerate
    (every input is in-domain). It is re-aimed at the residual total-domain risk —
    that the collection is DEGENERATE at the interesting point — via an in-region
    assert pinning the whole collected list on an F2P-shaped stream: the
    base-declared member surfaced AND attributed to the base class, the shared
    name resolved to the most-derived contributor, an annotation-only name
    carrying ``none``, and an empty-string annotation entry passed over. The impl
    is kept verbatim so the ensures still discharges; the proof gains a ``decide``
    arm to clear the assert VC.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries MANDATORY frame rivals that WRITE through a read-only input held at a
    fractional heap permission (``Acc(list_pred(ens),1/2)`` / ``mro.append``) and
    are rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: ``existing`` and ``hierarchy`` are immutable values, this bundle
    declares NO ``mut`` binder, and there is no heap and no aliasing — so there is
    no read-only input to overwrite and no permission system to trip. The class
    has no carrier analogue; no substitute is fabricated (see the footer).
  * DIVERGENCE / NON-TERMINATION — the class is CLOSED BY THE SEMANTICS here, and
    a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
    and the ``open`` is the line that actually selects the semantics: both
    namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
    the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So
    the two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every loop
    in the impl (1 loop here, measure ``(candidates hierarchy).length - i``). A
    rival that loops without a measure is refused outright (``Decreasing
    annotations are required in total correctness semantics``), and a rival that
    supplies a CONSTANT measure to dodge that is refused on the measure's own goal
    (``case «decreasing_1: spin» … ⊢ spin < spin``), re-measured on this bundle
    with a real build. Divergence therefore does not discharge the ``ensures``
    clause vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case must
    carry a witness that ELABORATES against the rival. With NO measure the rival's
    module does not compile at all: the descent obligation fails at the ``method``
    itself, ahead of any appended tester, and measured through the gate's own
    ``_check_witness`` even ``example : True := trivial`` comes back
    ``witness-unproven`` — an INCONCLUSIVE outcome that would fail the whole
    battery rather than pass a case. A rival that CARRIES a non-decreasing measure
    is refused at the ``prove_correct`` site instead, which the witness file
    strips, so that module does elaborate; but its post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Both shapes therefore land
    ``witness-unproven``. That is the right behaviour: a diverging impl has no
    output at any input, so there is no value for a witness to disagree with, and
    its rejection is a judgement of the termination obligation rather than a
    postcondition violation at a point. Recorded as REJECTED-BY-SPEC and not
    expressible as a witnessed case, which is neither a spec hole nor a battery
    gap.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is the fully-unfolded pure
    function ``collected`` of the two input binders; the ``axioms`` region is
    empty and there is no answer-key term a wrong impl could echo. The cheapest
    correct impl computes the first-occurrence collection honestly (returning
    ``collected existing (candidates hierarchy)`` IS the real work), which the
    positive controls cover — so it is a correct impl, not an echo.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each of the eleven rivals
    gets most of the domain right yet diverges on ONE sub-domain (the stream
    restricted to the most-derived class; the class order inverted; the two
    declaration kinds hoisted into hierarchy-wide passes; the phase order inside a
    class swapped; every candidate re-attributed to the documented class; an
    annotation's absent doc spelled as an empty one; the empty-name filter
    dropped; the dedup dropped; the dedup shallow; the ``existing`` filter
    dropped; one class's own attribute order reversed).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8548"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the ENTIRE frozen loop body (between and INCLUDING
# ---- the markers). Lies wholly inside the single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load).
_IMPL = """    -- impl-start
    let mut result : List Member := []
    let mut i := 0
    while i < (candidates hierarchy).length
      invariant i ≤ (candidates hierarchy).length
      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
      done_with i = (candidates hierarchy).length
      decreasing (candidates hierarchy).length - i
    do
      let a := (candidates hierarchy)[i]!
      result := collectStep existing result a
      i := i + 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen loop
# ---- body. A positive control that drops the loop retunes it to a bare
# ---- `loom_solve`; the admissibility case appends a `decide` arm. Both the impl
# ---- region and the `prove_correct` body are elided from the spec view, so
# ---- same_spec still holds and the obligation survives with a byte-identical
# ---- statement. Unique.
_PROOF = """prove_correct collectInstanceAttrDocs by
  loom_solve
  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
    have hi : i < (candidates hierarchy).length := by omega
    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
  case «ensures_1: out = collected existing (candidates hierarchy)» =>
    injection i_2 with _ hr
    subst hr
    rw [collected, invariant_2, done_1, List.take_length]"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

_BARE = "prove_correct collectInstanceAttrDocs by\n  loom_solve"


def _impl_block(body):
    return "    -- impl-start\n" + body + "\n    -- impl-end"


def _rewrite_impl(body):
    """Full variant: impl body replaced, spec + frozen proof left intact."""
    return _swap(_BASE, _IMPL, _impl_block(body))


def _rewrite_impl_reproved(body, new_proof):
    """Impl body replaced AND the proof retuned (for reshapes that change the
    do-block's syntactic form, or add an assert VC). Every loop-free rival is
    reproved to a bare `loom_solve` so its rejection lands on the ensures goal
    itself rather than on a stale case name the frozen script would look for."""
    return _swap(_rewrite_impl(body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `collectInstanceAttrDocsTester existing hierarchy = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. `ClassLevel`/`Member`
# ---- derive DecidableEq and every leaf is a concrete literal, so each witness
# ---- closes by `decide` (no opaque term to condition on).
def _witness(call):
    return ("extract_program_for collectInstanceAttrDocs\n"
            "prove_precondition_decidable_for collectInstanceAttrDocs\n"
            "prove_postcondition_decidable_for collectInstanceAttrDocs\n"
            "derive_tester_for collectInstanceAttrDocs\n\n"
            f"example :\n    {call} = false := by\n  decide\n")


# ---- the witness_reference every reject case names as its second subject.
_REFERENCE = _rewrite_impl_reproved(
    "    return collected existing (candidates hierarchy)", _BARE)

# ---- shared rival fragments. Spelling the per-class stream out by hand (rather
# ---- than calling `levelCandidates`) is what lets a rival perturb ONE component
# ---- of it while leaving the others exactly as the model has them.
_ANNOTS = ('(c.annots.filter (fun n => n != "")).map '
           '(fun n => (⟨n, c.owner, none⟩ : Member))')
_ATTRS = 'c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member))'


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": (
            "the cheapest honest correct impl returns the grounded pure model "
            "`collected existing (candidates hierarchy)` directly (no loop at "
            "all — maximally different from the frozen forward `while`). The "
            "ensures is literally that equation, so it holds on the whole domain "
            "and a bare `loom_solve` discharges the definitional residual. If "
            "this failed the spec would be over-fit to the loop shape "
            "(SPEC-TOO-STRONG). Also the no-ungrounded-echo control: the model IS "
            "the real per-class first-occurrence collection work, so returning it "
            "is correct, not a cheat."),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _rewrite_impl(
            "    let mut result : List Member := []\n"
            "    let mut i := 0\n"
            "    while i < (candidates hierarchy).length\n"
            "      invariant i ≤ (candidates hierarchy).length\n"
            "      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []\n"
            "      done_with i = (candidates hierarchy).length\n"
            "      decreasing (candidates hierarchy).length - i\n"
            "    do\n"
            "      let a := (candidates hierarchy)[i]!\n"
            "      let kept := collectStep existing result a\n"
            "      result := kept\n"
            "      i := i + 1\n"
            "    return result"),
        "rationale": (
            "structurally-different CORRECT impl: the per-candidate kept result is "
            "bound to a typed local `kept` before assignment, instead of the "
            "inline `result := collectStep existing result a`. Same behaviour, "
            "different data shape; the loop invariants are kept verbatim so the "
            "frozen proof still discharges. Must verify, else the spec is "
            "over-fit to the inline assignment form => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-nested-fold",
        "kind": "soundness",
        "expect": "verify",
        # Correct reshape that is NOT definitionally the frozen form: fold over
        # the CLASSES, threading the accumulator through each class's own inner
        # fold, never materialising `candidates hierarchy` at all. Equal to the
        # post-image only via the foldl/flatten interchange law.
        "module": _rewrite_impl_reproved(
            "    return hierarchy.foldl\n"
            "      (fun acc c => (levelCandidates c).foldl (collectStep existing) acc) []",
            "prove_correct collectInstanceAttrDocs by\n  loom_solve\n"
            "  all_goals simp [collected, candidates, List.foldl_flatten, List.foldl_map]"),
        "rationale": (
            "the SPEC-TOO-STRONG control with real content: a correct impl whose "
            "agreement with the post-image is not definitional. It never "
            "materialises `candidates hierarchy` — it walks the classes and "
            "threads the running collection through each class's own candidate "
            "fold, which is both the shape the real collection has and a "
            "genuinely different program from the frozen flattened loop. Equality "
            "with `collected existing (candidates hierarchy)` holds by the "
            "foldl/flatten interchange law, so the proof must actually invoke it "
            "(`List.foldl_flatten`, `List.foldl_map`); a bare `loom_solve` does "
            "NOT close it. If the spec could not accept this it would be over-fit "
            "to impls that agree with the model by unfolding alone => "
            "SPEC-TOO-STRONG. Distinct from pos-return-model (literally the model "
            "term) and pos-local-reshape (the frozen loop with the kept value "
            "named), both of which are definitionally the frozen form."),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed (the method has no precondition). Pins that the
    # modeled collection is NON-DEGENERATE at the F2P-shaped point, on all four
    # components at once. The impl is kept verbatim so the ensures still
    # discharges; the proof gains a `decide` arm to clear the assert VC.
    # =====================================================================
    {
        "id": "admiss-inherited-surfaced",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rewrite_impl_reproved(
            "    -- Non-degeneracy witness (F2P-shaped hierarchy, most-derived first).\n"
            "    -- Pins the WHOLE collected list, so all four observables fork on a\n"
            "    -- present inherited declaration rather than collapsing: `attr1` is\n"
            "    -- surfaced from the less-derived class AND attributed to it; the\n"
            "    -- shared `attr2` resolves to the most-derived contributor; the\n"
            "    -- annotation-only `attr4` carries no docstring; and the unreachable\n"
            "    -- annotation entry is passed over entirely.\n"
            "    assert (with_name_prefix `assert\n"
            "      (collected []\n"
            "        (candidates\n"
            "          [⟨\"Bar\", [\"\", \"attr4\"],\n"
            "            [⟨\"attr2\",\"docstring bar\"⟩, ⟨\"attr3\",\"docstring bar\"⟩]⟩,\n"
            "           ⟨\"Foo\", [],\n"
            "            [⟨\"attr1\",\"docstring foo\"⟩, ⟨\"attr2\",\"docstring foo\"⟩]⟩]) =\n"
            "        [⟨\"attr4\",\"Bar\",none⟩,\n"
            "         ⟨\"attr2\",\"Bar\",some \"docstring bar\"⟩,\n"
            "         ⟨\"attr3\",\"Bar\",some \"docstring bar\"⟩,\n"
            "         ⟨\"attr1\",\"Foo\",some \"docstring foo\"⟩]))\n"
            "    let mut result : List Member := []\n"
            "    let mut i := 0\n"
            "    while i < (candidates hierarchy).length\n"
            "      invariant i ≤ (candidates hierarchy).length\n"
            "      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []\n"
            "      done_with i = (candidates hierarchy).length\n"
            "      decreasing (candidates hierarchy).length - i\n"
            "    do\n"
            "      let a := (candidates hierarchy)[i]!\n"
            "      result := collectStep existing result a\n"
            "      i := i + 1\n"
            "    return result",
            _PROOF + "\n  all_goals decide"),
        "rationale": (
            "the collection is non-degenerate at the F2P-shaped point, on every "
            "component of the post-image at once: on the Bar(Foo) hierarchy it "
            "surfaces the inherited base-declared `attr1` (which the most-derived "
            "class does not declare) ATTRIBUTED TO `Foo`, resolves the shared "
            "`attr2` to the most-derived contributor's docstring and owner, gives "
            "the annotation-only `attr4` a `none` doc, and passes over the "
            "unreachable annotation entry. The in-region assert must discharge "
            "(else the collection would be degenerate / the obligation vacuous); "
            "the impl is kept verbatim so the ensures still discharges too."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE);
    # the frozen spec and obligation are untouched.
    # =====================================================================
    {
        "id": "weak-most-derived-only",
        "kind": "uniqueness",
        "expect": "reject",
        # WHOLE-HIERARCHY dropped: collect only the most-derived class's own
        # declarations, never walking the rest of the chain. Wrong precisely when
        # a member is declared only on a less-derived class.
        "module": _rewrite_impl_reproved(
            "    return (match hierarchy with\n"
            "      | [] => []\n"
            "      | c :: _ => collected existing (levelCandidates c))", _BARE),
        "refinement": (
            "this is the pre-change collection: the documented instance "
            "attributes were gathered from the subject's own namespace only, so an "
            "attribute documented on a base class was never gathered at all. The "
            "FAIL_TO_PASS scenario documents a subclass whose base declares an "
            "inherited instance attribute and asserts the rendered output CONTAINS "
            "that inherited attribute; with only the most-derived class walked it "
            "is absent and the exact-output assertion FAILS — so it does NOT "
            "resolve. Correct on every member the most-derived class itself "
            "declares (a true partial-domain break, not a blanket wrong impl)."),
        "rationale": (
            "REJECT from the WHOLE-HIERARCHY sub-obligation: the spec folds "
            "`candidates hierarchy` (every class), this folds the head class's "
            "candidates only, so a member declared only on a later (base) class is "
            "missing. If it verified => SPEC-TOO-WEAK (inherited members "
            "unenforced). Refuted at the F2P-shaped Bar(Foo) hierarchy "
            "(most-derived documents attr2/attr3, base documents attr1/attr2): the "
            "spec surfaces attr1 owned by Foo, the rival drops it."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"Bar", [], [⟨"attr2","docstring bar"⟩, ⟨"attr3","docstring bar"⟩]⟩,\n'
            '       ⟨"Foo", [], [⟨"attr1","docstring foo"⟩, ⟨"attr2","docstring foo"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-inverted-class-order",
        "kind": "uniqueness",
        "expect": "reject",
        # CLASS-ORDER inversion: walk the hierarchy least-derived-first, so for an
        # identifier declared on two classes the most-BASE occurrence is kept (and
        # the member is attributed to the base). Correct on every identifier
        # declared on exactly one class.
        "module": _rewrite_impl_reproved(
            "    return collected existing (candidates hierarchy.reverse)", _BARE),
        "refinement": (
            "a counterpart that walked the inheritance hierarchy back-to-front — "
            "or overwrote an already-collected identifier unconditionally instead "
            "of guarding it — would surface the MOST-BASE class's documentation "
            "for an attribute re-documented in a subclass, and attribute it to the "
            "base class, the opposite of Python override semantics. A scenario "
            "where a subclass re-documents an inherited attribute asserts the "
            "SUBCLASS's own documentation is rendered; this rival renders the "
            "base's, so that case FAILS — it would NOT resolve. Correct on every "
            "singly-declared member; the break is confined to the overridden "
            "sub-domain."),
        "rationale": (
            "REJECT from the CLASS-ORDER sub-obligation: the spec keeps the FIRST "
            "(most-derived) contributor of a shared identifier, folding the "
            "reversed hierarchy keeps the last (most-base) one. If it verified => "
            "SPEC-TOO-WEAK (override precedence inverted). Refuted at a two-class "
            "hierarchy sharing one name (`a` documented `dd` on the derived class "
            "`D`, `db` on the base `B`): the spec requires ⟨a,D,some dd⟩, the rival "
            "yields ⟨a,B,some db⟩ — varying both the docstring and the attribution "
            "at the collision sub-domain no singly-declared witness exercises."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"D", [], [⟨"a","dd"⟩]⟩, ⟨"B", [], [⟨"a","db"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-annotation-prepass",
        "kind": "uniqueness",
        "expect": "reject",
        # PER-CLASS INTERLEAVING dropped: hoist the two declaration kinds into
        # hierarchy-wide passes — EVERY class's annotations first, then EVERY
        # class's documented attributes. Every class is still walked, in the right
        # order, with the right attribution; only the interleaving moves. Wrong
        # exactly when a base class annotates an identifier that a more-derived
        # class documents.
        "module": _rewrite_impl_reproved(
            "    return collected existing\n"
            f"      ((hierarchy.map (fun c => {_ANNOTS})).flatten\n"
            f"        ++ (hierarchy.map (fun c => {_ATTRS})).flatten)", _BARE),
        "refinement": (
            "a counterpart that gathered the annotated names of the whole "
            "hierarchy before gathering any documented attribute — rather than "
            "resolving each class's annotations together with that same class's "
            "attributes — would let a BASE class's bare annotation claim an "
            "identifier that a SUBCLASS documents, surfacing the identifier with "
            "no docstring and attributed to the base. A scenario where a base "
            "annotates a name the subclass documents asserts the subclass's "
            "docstring is rendered; this rival renders none, so it FAILS — it "
            "would NOT resolve. Correct on every hierarchy where no identifier is "
            "both annotated and documented across two classes, which is why the "
            "interleaving needs pinning separately from the class order (which "
            "this rival keeps exactly)."),
        "rationale": (
            "REJECT from the PER-CLASS INTERLEAVING sub-obligation: `candidates` "
            "is `(hierarchy.map levelCandidates).flatten`, so class k's "
            "annotations AND attributes both precede class k+1's; this rival "
            "concatenates two hierarchy-wide passes instead. If it verified => "
            "SPEC-TOO-WEAK (the stream pinned only up to grouping by declaration "
            "kind, so which of two classes claims a shared identifier would be "
            "decided by HOW it is declared rather than by hierarchy position). "
            "Refuted at ⟨B,[],[q documented]⟩ / ⟨A,[q annotated],[]⟩: the spec "
            "yields ⟨q,B,some dq⟩, the rival yields ⟨q,A,none⟩. No order- or "
            "attribution-rival reaches this input: both classes are walked in "
            "order and every candidate keeps its own owner."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"B", [], [⟨"q","dq"⟩]⟩, ⟨"A", ["q"], []⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-phase-order-in-class",
        "kind": "uniqueness",
        "expect": "reject",
        # PHASE ORDER WITHIN A CLASS swapped: inside one class, consume the
        # documented attributes before the annotation-only names. Correct on every
        # class that does not both annotate and document the same identifier.
        "module": _rewrite_impl_reproved(
            "    return collected existing\n"
            f"      ((hierarchy.map (fun c => {_ATTRS} ++ {_ANNOTS})).flatten)",
            _BARE),
        "refinement": (
            "a counterpart that consumed a class's documented attributes before "
            "its annotated names would, for an identifier a class both annotates "
            "and documents, surface the docstring where the collection surfaces "
            "the bare annotation. The two orders are observably different — one "
            "renders a docstring for that member, the other renders none — so a "
            "scenario pinning the rendered body of a member that is both annotated "
            "and documented in one namespace FAILS under the swap; it would NOT "
            "resolve. Correct on every class where the two declaration kinds do "
            "not collide."),
        "rationale": (
            "REJECT from the PHASE ORDER WITHIN A CLASS sub-obligation: "
            "`levelCandidates` puts the filtered annotations BEFORE the class's "
            "attributes, so first-occurrence gives the annotation precedence "
            "within one class. If it verified => SPEC-TOO-WEAK (the within-class "
            "phase order unpinned, leaving the docstring of a doubly-declared "
            "identifier free). Refuted at a SINGLE-class hierarchy that both "
            "annotates and documents `q` (⟨A,[q],[q documented]⟩): the spec yields "
            "⟨q,A,none⟩, the rival ⟨q,A,some dq⟩. A one-class input, so no "
            "hierarchy-shaped rival above can be blamed for it, and distinct from "
            "weak-annotation-prepass (which keeps the within-class order and moves "
            "the grouping ACROSS classes; this keeps the grouping and moves the "
            "order WITHIN one)."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"A", ["q"], [⟨"q","dq"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-subject-attribution",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTRIBUTION collapsed: every candidate is re-attributed to the class
        # being documented (the head of the hierarchy) instead of to the class
        # that declared it. The member SET, its order, the docstrings and the
        # dedup are all exactly the model's; only `owner` moves. Wrong on every
        # inherited declaration.
        "module": _rewrite_impl_reproved(
            "    return (match hierarchy with\n"
            "      | [] => []\n"
            "      | c0 :: _ => collected existing ((candidates hierarchy).map\n"
            "          (fun m => (⟨m.name, c0.owner, m.doc⟩ : Member))))", _BARE),
        "refinement": (
            "a counterpart that recorded every gathered attribute as belonging to "
            "the class being documented — rather than to the class in whose "
            "namespace it was declared — produces the same member names with the "
            "same docstrings, so a scenario that lists inherited members passes. "
            "But a consumer decides whether to list a member at all by comparing "
            "that recorded class against the one it is documenting, so under this "
            "rival an inherited attribute is listed even when only the class's OWN "
            "members were requested. The PASS_TO_PASS scenario that requests a "
            "subclass's own instance attributes and asserts the output contains "
            "EXACTLY the two it declares itself would then also carry the "
            "inherited one, so its exact-output assertion FAILS — it would NOT "
            "resolve. Correct on every member the documented class declares "
            "itself; the break is confined to inherited declarations."),
        "rationale": (
            "REJECT from the ATTRIBUTION sub-obligation, the reason `Member.owner` "
            "may not be left free: the spec attributes a candidate to the "
            "CONTRIBUTING class, this attributes all of them to the head class. If "
            "it verified => SPEC-TOO-WEAK, and specifically weak in the direction "
            "that breaks the members-only consumer while still passing the "
            "inherited-members one. Refuted at the two-class hierarchy "
            "⟨Bar,attr2⟩/⟨Foo,attr1⟩: the spec yields ⟨attr1,Foo,…⟩, the rival "
            "⟨attr1,Bar,…⟩ — same name, same docstring, different attribution, so "
            "no name- or doc-keyed witness above reaches it."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"Bar", [], [⟨"attr2","docstring bar"⟩]⟩,\n'
            '       ⟨"Foo", [], [⟨"attr1","docstring foo"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-annot-doc-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # DOC SHAPE collapsed: an annotation-only member gets `some ""` instead of
        # `none`. Names, owners, order and dedup are all the model's. Wrong on
        # every annotation-only member.
        "module": _rewrite_impl_reproved(
            "    return collected existing\n"
            "      ((hierarchy.map (fun c =>\n"
            "        (c.annots.filter (fun n => n != \"\")).map\n"
            "          (fun n => (⟨n, c.owner, some \"\"⟩ : Member))\n"
            f"          ++ {_ATTRS})).flatten)", _BARE),
        "refinement": (
            "a counterpart that recorded an EMPTY docstring for a member that has "
            "no documentation at all — instead of recording the absence — makes "
            "the two states indistinguishable downstream. A consumer that falls "
            "back to another source of documentation (an inherited docstring, or "
            "the annotation's own type) when a member has none would stop doing "
            "so, since the member now claims to carry documentation; the rendered "
            "output loses that fallback text and an assertion on it FAILS — it "
            "would NOT resolve. Correct on every documented attribute, wrong only "
            "on annotation-only members."),
        "rationale": (
            "REJECT from the DOC SHAPE sub-obligation: `levelCandidates` gives an "
            "annotation-only candidate `none`, which is NOT `some \"\"` under "
            "`Member`'s DecidableEq. If it verified => SPEC-TOO-WEAK (the "
            "absent-vs-empty docstring distinction unpinned). Refuted at the "
            "single annotation ⟨A,[x],[]⟩: the spec yields ⟨x,A,none⟩, the rival "
            "⟨x,A,some \"\"⟩ — the ONLY witness that discriminates the doc "
            "CONSTRUCTOR rather than its payload."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"A", ["x"], []⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-keep-unreachable-annot",
        "kind": "uniqueness",
        "expect": "reject",
        # EMPTY-NAME FILTER dropped: keep an `annots` entry that is the empty
        # string. Correct on every hierarchy whose annotation entries are all
        # non-empty, wrong exactly where an annotated identifier is not reachable
        # under its class's name.
        "module": _rewrite_impl_reproved(
            "    return collected existing\n"
            "      ((hierarchy.map (fun c =>\n"
            "        c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member))\n"
            f"          ++ {_ATTRS})).flatten)", _BARE),
        "refinement": (
            "a counterpart that gathered every annotated identifier of a class "
            "without checking that the identifier is reachable under that class's "
            "own name would emit a member with an unusable identifier, and — "
            "because it claims that identifier first — would suppress a real "
            "documented attribute that legitimately owns it. A scenario "
            "documenting a class that annotates a name it cannot reach would gain "
            "a spurious entry and lose a real docstring, so its exact-output "
            "assertion FAILS — it would NOT resolve. Correct on every hierarchy "
            "with no such annotation."),
        "rationale": (
            "REJECT from the EMPTY-NAME FILTER sub-obligation: `levelCandidates` "
            "filters `annots` with `· != \"\"` (and does NOT filter `attrs`). If it "
            "verified => SPEC-TOO-WEAK (an unreachable annotation entry could be "
            "surfaced, and could shadow a documented attribute of the same "
            "identifier). Refuted at ⟨A,[\"\"],[⟨\"\",dz⟩]⟩: the spec yields "
            "⟨\"\",A,some dz⟩ (the annotation entry dropped, the documented one "
            "kept), the rival ⟨\"\",A,none⟩. The only witness that moves an "
            "`annots` entry to the empty string, so it is what makes the filter "
            "observable."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"A", [""], [⟨"","dz"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-ignore-existing",
        "kind": "uniqueness",
        "expect": "reject",
        # EXISTING-FILTER dropped: fold with an EMPTY existing set regardless of
        # the `existing` input. Correct whenever `existing` names no candidate.
        "module": _rewrite_impl_reproved(
            "    return (candidates hierarchy).foldl (collectStep []) []", _BARE),
        "refinement": (
            "a counterpart that ignored the member names already gathered by the "
            "earlier phases would re-surface a member another phase already "
            "provided, producing a duplicate or conflicting entry for that "
            "identifier. A scenario whose member was already surfaced by another "
            "source and must NOT be re-added by this phase would then carry it "
            "twice, so the exact-output assertion FAILS — it would NOT resolve. "
            "Correct whenever no candidate name collides with the pre-collected "
            "set (a true partial-domain break on the `existing` binder)."),
        "rationale": (
            "REJECT from the EXISTING-FILTER sub-obligation: the spec drops a "
            "candidate whose name is in `existing`, this folds with an empty set "
            "and keeps it. If it verified => SPEC-TOO-WEAK (the `existing` binder "
            "unread — a rival mishandling only that input would slip through). "
            "Refuted at existing=[\"a\"], hierarchy=[⟨A,[],[⟨a,d⟩]⟩]: the spec "
            "drops the candidate (result []), the rival keeps it. This is the ONLY "
            "witness that moves `existing` off the empty set, so it is what "
            "demonstrates the spec's dependence on that binder."),
        "witness": _witness(
            'collectInstanceAttrDocsTester ["a"]\n'
            '      [⟨"A", [], [⟨"a","d"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-no-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        # DEDUP dropped: keep the `existing` filter but never guard against an
        # identifier already collected in the SAME fold. Correct on every stream
        # with no repeated identifier.
        "module": _rewrite_impl_reproved(
            "    return (candidates hierarchy).foldl\n"
            "      (fun acc m => if existing.contains m.name then acc else acc ++ [m]) []",
            _BARE),
        "refinement": (
            "a counterpart that appended every candidate not already in the "
            "pre-collected set — but omitted the guard against identifiers it had "
            "itself just collected — would emit an attribute declared on two "
            "classes TWICE, once per declaring class. A subclass re-documenting an "
            "inherited attribute would then render with two conflicting entries "
            "for the same identifier, so the exact-output assertion (which lists "
            "each member once) FAILS — it would NOT resolve. Correct on any stream "
            "with no repeated identifier."),
        "rationale": (
            "REJECT from the DEDUP / FIRST-WINS sub-obligation: the spec appends a "
            "candidate only when its name is not already collected, so each "
            "identifier appears at most once; this rival re-appends, so a shared "
            "name appears twice. If it verified => SPEC-TOO-WEAK (uniqueness of "
            "the collected identifiers unpinned). Refuted at a two-class hierarchy "
            "sharing one name (`x` documented `p` on A then `q` on B): the spec "
            "surfaces one entry (⟨x,A,some p⟩), the rival two. Distinct input and "
            "distinct failure mode from weak-inverted-class-order (that keeps the "
            "wrong single entry; this keeps two)."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"A", [], [⟨"x","p"⟩]⟩, ⟨"B", [], [⟨"x","q"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-dedup-last-only",
        "kind": "uniqueness",
        "expect": "reject",
        # DEDUP PRESENT BUT SHALLOW: the guard consults only the LAST collected
        # entry, so it suppresses an adjacent repeat but not one separated by an
        # intervening member.
        "module": _rewrite_impl_reproved(
            "    return (candidates hierarchy).foldl\n"
            "      (fun acc m => if existing.contains m.name\n"
            "          || (acc.getLast? |>.any (fun x => x.name == m.name))\n"
            "        then acc else acc ++ [m]) []", _BARE),
        "refinement": (
            "a counterpart that checked the identifier only against the "
            "most-recently-gathered member — instead of against every member "
            "gathered so far — would suppress an adjacent duplicate but emit a "
            "member twice whenever another identifier was gathered in between. "
            "Since a class's namespace usually contributes several members before "
            "the next class is reached, that is the COMMON layout, not a corner: "
            "the rendered output carries two conflicting entries for the repeated "
            "identifier and the exact-output assertion FAILS — it would NOT "
            "resolve. Correct on every stream whose repeats are adjacent, which is "
            "why the dedup clause needs pinning against a present-but-shallow "
            "guard and not only against a missing one."),
        "rationale": (
            "REJECT from the DEDUP / FIRST-WINS sub-obligation at the strength "
            "weak-no-dedup leaves open: that rival deletes the guard entirely, so "
            "it would also be refuted by a shallow guard's witness, and the "
            "battery could not distinguish 'dedup against the whole accumulator' "
            "from 'dedup against the previous entry'. `collectStep` uses "
            "`acc.any`, i.e. the WHOLE accumulator. If this verified => "
            "SPEC-TOO-WEAK (the guard pinned only up to adjacency). Refuted at a "
            "single class whose own attributes carry a NON-adjacent repeat "
            "(⟨A,[],[a,b,a]⟩): the spec surfaces two entries, the rival three — "
            "exactly what weak-no-dedup's adjacent-repeat witness cannot reach."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"A", [], [⟨"a","p"⟩, ⟨"b","q"⟩, ⟨"a","r"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-inner-attr-order",
        "kind": "uniqueness",
        "expect": "reject",
        # WITHIN-CLASS ATTR ORDER inverted: the hierarchy's class order and the
        # per-class phase order are both kept exactly; only each class's own
        # `attrs` list is reversed. For an identifier documented twice in ONE
        # namespace the source-later docstring now wins.
        "module": _rewrite_impl_reproved(
            "    return collected existing\n"
            "      (candidates (hierarchy.map\n"
            "        (fun c => (⟨c.owner, c.annots, c.attrs.reverse⟩ : ClassLevel))))",
            _BARE),
        "refinement": (
            "a counterpart that consumed one class's own documented attributes in "
            "reverse source order would, for an identifier documented twice within "
            "a single namespace, keep the SOURCE-LATER docstring instead of the "
            "first. The collection's contract is first-occurrence over the "
            "discovery stream, and per-class analyzer order is part of that "
            "stream; a scenario asserting the first documented body is the one "
            "rendered carries the later body instead, so its exact-output "
            "assertion FAILS — it would NOT resolve. Correct on every hierarchy "
            "where no class documents an identifier twice, and confined to the "
            "INNER list — the class order and the annotation/attribute phase order "
            "are untouched."),
        "rationale": (
            "REJECT from the WITHIN-CLASS ATTR ORDER sub-obligation: `candidates` "
            "preserves each class's own analyzer order, this reverses it. If it "
            "verified => SPEC-TOO-WEAK (the stream pinned only up to permutation "
            "inside one class's attribute list). Refuted at a single class "
            "documenting one identifier twice (⟨A,[],[⟨a,p⟩,⟨a,q⟩]⟩): the spec "
            "keeps ⟨a,A,some p⟩, the rival ⟨a,A,some q⟩. A one-class witness with "
            "no annotation, so neither an outer-structure nor a phase-order rival "
            "reaches it."),
        "witness": _witness(
            'collectInstanceAttrDocsTester []\n'
            '      [⟨"A", [], [⟨"a","p"⟩, ⟨"a","q"⟩]⟩]'),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The nagini sibling ships 8 SPEC cases (2 soundness positives, 1 admissibility,
# 5 uniqueness rivals — two of which are MANDATORY frame-mutation rivals) plus an
# AXIOM_TESTS lane (this gate ignores it). The sibling contracts
# `resolve_attribute_doc(nm, mro, ens, enm, edoc) -> int` over FOUR index-aligned
# read-only `List[int]` inputs under fractional heap permissions and partial
# correctness, returning the resolved doc CODE for ONE queried attribute name via
# a deep front-recursive `resolve_from` / `lookup_owner_doc` fold. This backend
# models the SAME hierarchy-wide first-occurrence collection but at a DIFFERENT,
# richer grain: instead of resolving one queried name to an int code, it builds
# the whole collected member LIST, and each element carries the identity of the
# class it is ATTRIBUTED to and an OPTIONAL docstring. The hierarchy order is
# carried structurally by the order of `hierarchy`; the per-class own-namespace
# selection by each `ClassLevel`; and the two kinds of declaration a class can
# make (annotation-only, documented attribute) by the two fields `annots` and
# `attrs`, whose per-class interleaving is itself an observable.
#
#   nagini case                 kind          -> here                          disposition
#   ------------------------------------------------------------------------------------------
#   pos-grounded-echo           soundness     -> pos-return-model              RE-SHAPED
#   pos-reorder                 soundness     -> pos-local-reshape             PORTED
#   admiss-f2p                  admissibility -> admiss-inherited-surfaced     RE-AIMED
#   frame-mut-ens               uniqueness    -> (none)                        VACUOUS
#   frame-mut-mro-append        uniqueness    -> (none)                        VACUOUS
#   weak-own-owner-only         uniqueness    -> weak-most-derived-only        PORTED
#   weak-latest-mro-owner       uniqueness    -> weak-inverted-class-order     PORTED
#   weak-global-first-record    uniqueness    -> weak-inner-attr-order         RE-AIMED
#   (no sibling)                soundness     -> pos-nested-fold               ADDED (non-definitional)
#   (no sibling)                uniqueness    -> weak-ignore-existing          ADDED (existing binder)
#   (no sibling)                uniqueness    -> weak-no-dedup                 ADDED (dedup presence)
#   (no sibling)                uniqueness    -> weak-dedup-last-only          ADDED (dedup depth)
#   (no sibling)                uniqueness    -> weak-annotation-prepass       ADDED (interleaving)
#   (no sibling)                uniqueness    -> weak-phase-order-in-class     ADDED (phase order)
#   (no sibling)                uniqueness    -> weak-subject-attribution      ADDED (attribution)
#   (no sibling)                uniqueness    -> weak-annot-doc-empty          ADDED (doc shape)
#   (no sibling)                uniqueness    -> weak-keep-unreachable-annot   ADDED (name filter)
#   AXIOM_TESTS                 axiom         -> (none)                        N/A (G-AX)
#
# 3 ported, 1 positive re-shaped, 2 re-aimed, 2 frame-mutation vacuous; 1
# soundness and 8 uniqueness added for the binders and clauses this carrier
# affords. 15 SPEC cases (3 soundness, 1 admissibility, 11 uniqueness).
#
# RE-SHAPED (pos-grounded-echo -> pos-return-model): the sibling's positive echoes
#   the grounded oracle `resolved_doc(...)`. On this carrier the maximally-
#   different correct impl drops the loop entirely and returns the grounded model
#   `collected existing (candidates hierarchy)`; it also serves as the
#   no-ungrounded-echo control (the model is the real first-occurrence work, not
#   an answer-key), the same role the sibling's echo plays.
# PORTED (pos-reorder -> pos-local-reshape): the sibling's second positive keeps
#   the forward MRO direction but reshapes the branch (negated guard + continue,
#   single tail return). This backend's frozen impl has no early-exit branch to
#   reshape; the reshape SPIRIT — "structurally different, behaviourally
#   identical, loop invariants kept so the proof still closes" — is carried by
#   binding the per-candidate kept result to a typed local before assignment.
# RE-AIMED (admiss-f2p -> admiss-inherited-surfaced): the sibling's admissibility
#   case asserts the parallel-length / halved-permission Requires hold on the
#   Bar(Foo) PSeq input and unfolds the oracle ladder. This backend's method has
#   NO precondition and no permission surface, so that probe is degenerate. It is
#   re-aimed at the residual total-domain risk — a DEGENERATE collection — via an
#   in-region assert pinning the WHOLE collected list on the F2P-shaped
#   hierarchy, which forks all four observables at once (membership, attribution,
#   doc presence, name filter).
# PORTED (weak-own-owner-only -> weak-most-derived-only): the sibling's pre-change
#   rival matches records only against the subject's own owner (mro[0]); here that
#   is collecting only the head (most-derived) class's candidates. Both leave a
#   base-only member absent — the literal modeled change and the G-DIFF
#   discriminator.
# PORTED (weak-latest-mro-owner -> weak-inverted-class-order): the sibling's
#   latest-MRO-owner-wins rival scans the MRO back-to-front (base overrides
#   subject); here that is folding the reversed hierarchy, so an overridden name
#   resolves to the most-base contributor. Both invert the earliest/most-derived
#   precedence and are refuted on the override sub-domain.
# RE-AIMED (weak-global-first-record -> weak-inner-attr-order): the sibling's
#   "ignore MRO precedence, return the first record in TABLE order whose owner is
#   anywhere on the MRO" rival keys on a separation this carrier collapses at the
#   OUTER grain: here the k-th `ClassLevel` is the k-th class, so there is no
#   independent record-table order across classes. The faithful residue of the
#   class is the INNER grain — the order of one class's own attribute list — which
#   is expressible, observably wrong, and has a real counterpart (a collection
#   consuming a namespace's documented attributes in reverse source order). That
#   is weak-inner-attr-order, refuted at a single-class input no outer-structure
#   rival reaches.
# VACUOUS (frame-mut-ens, frame-mut-mro-append): the sibling's two MANDATORY frame
#   rivals write into read-only inputs held at half heap permission (`ens[0] =
#   mro[0]`; `mro.append(...)`), rejected by the insufficient-permission check.
#   This backend is referentially transparent: `existing` and `hierarchy` are
#   immutable values, no `mut` binder is declared, and there is no heap, no
#   aliasing, and no permission system. There is no read-only input to overwrite
#   and no frame clause to violate, so the class has no carrier analogue. Omitted
#   as a genuine carrier fact per the porting map, NOT fabricated.
#   DEMONSTRATED rather than argued: writing through either input (`existing :=
#   existing ++ ["zz"]`, `hierarchy := hierarchy ++ [default]`) does not produce a
#   rival at all — the file fails to ELABORATE, with "`existing` cannot be
#   mutated, only variables declared using `let mut` can be mutated" (and the same
#   for `hierarchy`). The rejection is the parser refusing the program text, not a
#   permission check on a mutation, so there is no assignment for a witness to
#   discriminate and the class cannot be staged here even in principle.
# ADDED (weak-ignore-existing): the sibling's `resolve_from` has no analogue of
#   the `existing` input — it resolves a single queried name against the record
#   table only. Here `existing` is a load-bearing binder. A battery whose every
#   rival held it at [] would never demonstrate the spec's dependence on it.
# ADDED (weak-no-dedup, weak-dedup-last-only): the sibling returns a single int
#   code, so it has no notion of the RESULT carrying a name twice. This backend
#   builds a LIST and pins each identifier at most once — attacked both for the
#   guard's PRESENCE and for its DEPTH (`acc.any` over the whole accumulator vs. a
#   check against the previous entry only).
# ADDED (weak-subject-attribution, weak-annot-doc-empty): the sibling's post-image
#   is one int, so it has no attribution or doc-presence component at all. This
#   carrier makes both observable — `Member.owner` is what a consumer compares
#   against the class it is documenting, and `Member.doc` distinguishes "no
#   documentation" from "empty documentation". Left free, either would admit a
#   rival that keeps every name and docstring and still breaks a real consumer;
#   weak-subject-attribution is exactly that rival, and it is REJECTED.
# ADDED (weak-annotation-prepass, weak-phase-order-in-class,
#   weak-keep-unreachable-annot): the sibling has one kind of record, so it cannot
#   express that a class declares members in TWO ways whose per-class
#   interleaving, within-class order, and reachability filter are each separately
#   observable. All three are attacked, each refuted at an input the other two
#   cannot reach (two classes with one annotated / one documented; one class
#   declaring the same identifier both ways; one class whose annotation entry is
#   unreachable).
#
# CLAUSE / BINDER COVERAGE of the reject witnesses (11 rivals, 11 distinct input
#   points). The single ensures `out = collected existing (candidates hierarchy)`
#   binds `out`, `existing` and `hierarchy`; the model combines WHOLE-HIERARCHY,
#   CLASS ORDER, PER-CLASS INTERLEAVING, WITHIN-CLASS PHASE ORDER, ATTRIBUTION,
#   DOC SHAPE, EMPTY-NAME FILTER, DEDUP (presence and depth), EXISTING FILTER and
#   WITHIN-CLASS ATTR ORDER. All eleven are attacked:
#     * WHOLE-HIERARCHY          — weak-most-derived-only     (head class only)
#     * CLASS ORDER              — weak-inverted-class-order  (reversed hierarchy)
#     * PER-CLASS INTERLEAVING   — weak-annotation-prepass    (two global passes)
#     * PHASE ORDER IN A CLASS   — weak-phase-order-in-class  (attrs before annots)
#     * ATTRIBUTION              — weak-subject-attribution   (owner := head owner)
#     * DOC SHAPE                — weak-annot-doc-empty       (none -> some "")
#     * EMPTY-NAME FILTER        — weak-keep-unreachable-annot (filter dropped)
#     * EXISTING FILTER          — weak-ignore-existing       (folds with [])
#     * DEDUP, presence          — weak-no-dedup              (no guard)
#     * DEDUP, depth             — weak-dedup-last-only       (guard on last entry)
#     * WITHIN-CLASS ATTR ORDER  — weak-inner-attr-order      (attrs reversed)
#   INPUT binders, both varied:
#     existing  : ["a"] for weak-ignore-existing, [] for the other ten — moved off
#                 [] by exactly that rival, the witness that makes the spec's
#                 dependence on `existing` observable (elsewhere the filter is
#                 inert).
#     hierarchy : the variation is verdict-changing at every point, not eleven
#                 spellings of one input. Class count moves (five one-class
#                 witnesses, six two-class); the collision GRAIN moves (across
#                 classes; within one class's attrs; between a class's annots and
#                 another class's attrs; between a class's own annots and its own
#                 attrs); the adjacency of a repeat moves (adjacent [a,a] vs.
#                 separated [a,b,a]); the `annots` field moves off [] (empty
#                 entry, non-empty entry, both) — and each flips a different
#                 clause.
#   The admissibility case additionally pins the WHOLE collected list on the F2P
#   hierarchy, so the positive lane does not merely meet a degenerate post-image.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   consumed axiom and no deep-model reference (`levelCandidates` / `candidates` /
#   `collectStep` / `collected` are direct models over the method's own inputs,
#   checked by G-CONF / axiom_check.py, not axiomatized — mapping.md §3), and this
#   gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
