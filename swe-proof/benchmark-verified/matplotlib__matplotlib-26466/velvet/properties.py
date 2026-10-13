"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26466 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and each ``prove_correct captureCoord{A,B}`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (TWO independently-modeled retaining sites, byte-identical
contracts, over a two-component integer coordinate carrier ``Array Int``):

  captureCoordA (coords : Array Int) return (out : StoredCoord)
    require  coords.size = 2
    ensures  ∀ a b : Int, observe out a b = (coords[0]!, coords[1]!)   -- load-bearing

  captureCoordB (coords : Array Int) return (out : StoredCoord)       -- same triple

Each models a construction site that retains the caller's two-component
coordinate pair. The pure region models the OBSERVABLE retention contract with a
``StoredCoord`` (``snapshot x y`` = detached/copied, ``reference`` = still bound
to the source container) and ``observe out a b`` = reading the retained pair back
when the source container's CURRENT contents are ``(a, b)``. The postcondition
``∀ a b, observe out a b = (coords[0]!, coords[1]!)`` pins the retained pair to
the CAPTURE-TIME components for EVERY possible later state ``(a, b)`` of the
source — a property only the detached (snapshot) behaviour satisfies. This is
the alias→copy fix expressed at the value level: Lean is referentially
transparent and has no aliasing, so the reference-vs-copy delta lives entirely in
this universally-quantified clause, the direct analogue of the nagini sibling's
fractional-permission (P1)+(P3) freshness pins plus the identity pins (P5)/(P6).

The clause decomposes into independently-attackable behaviours:
  * DETACHMENT  — the retained pair must ignore later mutation ``(a, b)`` of the
                  source (only ``snapshot`` does; ``reference`` yields ``(a, b)``);
  * COMPONENT-0 — the first retained component is ``coords[0]!``, untransformed;
  * COMPONENT-1 — the second retained component is ``coords[1]!``, untransformed;
  * ORDER       — the two components are retained in their own order, not swapped;
  * DOMAIN      — the clause is required at EVERY admissible ``coords``, not on a
                  sub-domain (a rival may be right on the diagonal and wrong off
                  it: ``weak-detach-only-when-equal-b``).

KNOWN LIMIT of the component carrier, measured by the audit, NOT closed here (it
is a property of the frozen spec + its declared carrier, so it is escalated
rather than patched): a component transform that is the IDENTITY on ``Int`` but
lossy on the component domain the bundle's own type bijection declares is
accepted by this obligation. ``snapshot (coords[0]! / 1) (coords[1]! / 1)``
verifies (exit 0, frozen proof script unchanged), as does
``snapshot (coords[0]! - coords[0]! % 1) …``. On ``Int`` both are the identity, so
the obligation cannot see them; refined along the declared component bijection
they truncate a non-integral component. This is exactly the transform hole the
sibling battery's carrier note describes closing by moving to a carrier that
admits no arithmetic on the components — a carrier choice, unavailable from
inside this lane. Recorded in the footer and escalated; the ``Int``-level rivals
below are the ones this carrier CAN discriminate.

INPUT BINDER of each predicate: the single argument ``coords`` (its two
components ``coords[0]!`` and ``coords[1]!``). The reject witnesses vary it
across both sites and across component values, so a rival that mishandles only
one component slot, or only one site, is caught. The two sites are modeled and
attacked SEPARATELY because the F2P
(``test_annotate_and_offsetfrom_copy_input``) exercises BOTH independently (an
``OffsetFrom(...)`` construction with a later in-place source mutation, and an
``annotate(xy=...)`` construction with a later in-place source mutation); the
G-DIFF prepatches (``Solution_prepatch_1/2``) fail at one site each.

CARRIER NOTE (decisive for the witness route). The carrier is transparent
(``StoredCoord`` has decidable equality; ``observe`` is a concrete ``def``), but
the ``ensures`` clause is UNIVERSALLY QUANTIFIED over ``a b : Int``, so
``prove_postcondition_decidable_for`` leaves an unsolved ``Decidable (∀ a b, …)``
goal and the tester route (``derive_tester_for`` → ``…Tester args = false``) is
UNAVAILABLE here (measured: ``decide`` gets stuck on the quantified
``Decidable`` instance). So each witness instead refutes the method's Hoare
triple DIRECTLY at one concrete coordinate:
``¬ triple True (captureCoordX #[..]) (fun out => ∀ a b, observe out a b = (…, …))``
closed by ``unfold; simp [triple, pure]`` (plus, for the ``reference`` rivals
whose residual goal is an existential over the mutated contents, a single
``exact ⟨0, 0, by decide⟩`` picking one witnessing later-state where the
reference and the snapshot disagree). Checked in a file whose ``prove_correct``
blocks are stripped so no tactic script can mask the verdict. Every witness was
SEEN to discriminate — it ELABORATES against its rival (EXIT 0) and FAILS against
the frozen solution (EXIT 1) — with two real builds per case. Every witness head
binds NOTHING (literal ``coords``), so there is no consistency obligation.

The gold-side failure is a SEMANTIC refutation, re-derived by the audit with real
builds rather than read off the error text. Against the frozen solution ``simp``
evaluates the postcondition to ``True`` and the residual goal collapses to
``⊢ False`` — i.e. gold IS correct at that input and the negation is unprovable.
The two observed gold signatures are the two spellings of that one fact: the
swap/dup rivals' witnesses report ``unsolved goals ⊢ False`` directly, and the
``reference`` rivals' witnesses (which carry the ``⟨0, 0, …⟩`` closer) report
``Invalid ⟨...⟩ notation: The expected type `False` has no constructors`` — the
closer being applied to a goal that has already become ``False``. Both were
FORGERY-TESTED per case: a witness differing ONLY in dropping the ``¬`` (asserting
gold is CORRECT there) inverts every exit — it builds against the frozen solution
(exit 0) and FAILS against each rival with the rival's own concrete residual
equation (e.g. ``unsolved goals ⊢ ∀ (a b : ℤ), a = 3 ∧ b = 5``). So the gold-side
exit code tracks the CLAIM and not the tactic shape, which is what makes these
rejections attributable to the spec.

ADVERSARIAL READ of the nagini classes on this carrier (see footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION (nagini ``frame-mutation-a/b``) — VACUOUS. The
    nagini sibling carries these as MANDATORY because its input holds a fractional
    heap permission (``Acc(list_pred(pair), 1/2)``) an impl can illegally WRITE.
    Lean and Velvet are referentially transparent: ``coords`` is an immutable
    value, this bundle declares no ``mut`` binder, there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to build. Not fabricated (per the porting map: vacuous on Lean/Velvet).
  * ALIAS ECHO (nagini ``alias-return-input-a/b``) — PORTED as the ``reference``
    rival (the pre-patch bug: retain the source container by reference). On this
    carrier the alias→copy delta is not a permission conflict but the value-level
    detachment clause, which ``reference`` violates.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PARTIAL-DOMAIN / VALUE (nagini ``weak-swap-components``, ``weak-dup-first``)
    — PORTED and extended: swap the two components (ORDER), duplicate a component
    (COMPONENT-0 / COMPONENT-1). Each gets the shape right and diverges on one
    component/order sub-behaviour.
  * SOUNDNESS positives (nagini ``pos-control-reorder``) — APPLY: structurally
    different but faithful impls that MUST verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY (nagini ``admiss-reads``) — RE-AIMED, and re-stated by the audit
    so the assert demonstrates the claim instead of standing beside it: instantiate
    the FROZEN OBLIGATION at a concrete length-2 container and discharge it by
    evaluation, pinning that the ``require`` admits that input, that the obligation
    is satisfiable exactly there (else PRECOND-TOO-STRONG), and that the post-image
    is non-degenerate (the source-tracking retention disagrees with it).

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(the retention is modeled DEEPLY as ``StoredCoord`` / ``observe``); this gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26466"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Whole-method-block anchors. The two methods are BYTE-IDENTICAL in their impl
# region, so a bare impl body is NOT unique; each anchor therefore spans the
# method header + full contract + impl region (def-through-# impl-end), which is
# unique per site. The spec portion (require/ensures) is reproduced VERBATIM and
# only the text strictly between `-- impl-start` and `-- impl-end` changes, so
# markers.same_spec holds by construction and the `ensures` statement is
# byte-identical. The `prove_correct` blocks are the elided proof region; a
# correct reshape may retune its own site's block, rivals leave it as-is.
# ---------------------------------------------------------------------------
_A_HEAD = (
    "method captureCoordA (coords : Array Int) return (out : StoredCoord)\n"
    "  require coords.size = 2\n"
    "  ensures ∀ a b : Int, observe out a b = (coords[0]!, coords[1]!)\n"
    "  do\n"
    "    -- impl-start\n"
)
_B_HEAD = _A_HEAD.replace("captureCoordA", "captureCoordB")

# Gold impl body (strictly between `-- impl-start` and `-- impl-end`, markers
# included at the boundary), shared verbatim by both sites.
_GOLD_BODY = (
    "    let x := coords[0]!\n"
    "    let y := coords[1]!\n"
    "    return StoredCoord.snapshot x y\n"
    "    -- impl-end"
)

_A_BLOCK = _A_HEAD + _GOLD_BODY
_B_BLOCK = _B_HEAD + _GOLD_BODY

_A_PROOF = "prove_correct captureCoordA by\n  loom_solve"
_B_PROOF = "prove_correct captureCoordB by\n  loom_solve"

for _s in (_A_BLOCK, _B_BLOCK, _A_PROOF, _B_PROOF):
    assert _BASE.count(_s) == 1, f"frozen region drifted: {_s[:40]!r}"


def _A(body):
    """captureCoordA block with the given impl body (body ends at # impl-end)."""
    return _A_HEAD + body


def _B(body):
    return _B_HEAD + body


def _both(body):
    """Both sites' impl bodies replaced with `body`."""
    return _swap(_swap(_BASE, _A_BLOCK, _A(body)), _B_BLOCK, _B(body))


def _one_a(body):
    return _swap(_BASE, _A_BLOCK, _A(body))


def _one_b(body):
    return _swap(_BASE, _B_BLOCK, _B(body))


# ---- WITNESSES. The spec is a `method` CONTRACT with a QUANTIFIED `ensures`
# ---- clause, so `prove_postcondition_decidable_for` fails and the tester route
# ---- is unavailable (measured). Each witness refutes the method's Hoare triple
# ---- DIRECTLY at one concrete coordinate, checked in a file whose
# ---- `prove_correct` blocks are stripped so no tactic script can mask the
# ---- verdict. `triple`/`pure` come from the frozen `Velvet.Std` import. The
# ---- head binds nothing (literal input), so there is no consistency obligation.
def _witness(fn, arr, closer=""):
    body = (
        f"example : ¬ triple (l := Prop) (True)\n"
        f"    ({fn} {arr})\n"
        f"    (fun out => ∀ a b : Int, observe out a b = "
        f"(({arr} : Array Int)[0]!, ({arr} : Array Int)[1]!)) := by\n"
        f"  unfold {fn}\n"
        f"  simp [triple, pure]\n"
    )
    if closer:
        body += f"{closer}\n"
    return body


# The `reference` rival's residual goal is an existential over a witnessing
# later-state `(a, b)` where the reference (which yields `(a, b)`) disagrees with
# the capture-time pair; `⟨0, 0, by decide⟩` picks `(0, 0)`, which differs from
# both non-zero literal components below. The swap/dup rivals return a constant
# `snapshot`, so `simp [triple, pure]` alone closes the refutation.
_REF_CLOSE = "  exact ⟨0, 0, by decide⟩"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the detachment
    # obligation and only reshapes the executable surface; the frozen
    # `loom_solve` still closes the byte-identical obligation. Both verified
    # out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-read-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Read component 1 BEFORE component 0 (gold reads 0 then 1), then build
        # the SAME snapshot. Applied to BOTH sites. Ports the nagini
        # pos-control-reorder ARGUMENT (read index 1 first, rename locals, build
        # the same fresh pair) onto this carrier.
        "module": _both(
            "    let y := coords[1]!\n"
            "    let x := coords[0]!\n"
            "    return StoredCoord.snapshot x y\n"
            "    -- impl-end"),
        "rationale": "PASS SOURCE = the detachment clause at BOTH sites. Reading "
        "component 1 before component 0 and renaming locals leaves the retained "
        "snapshot identical, so `∀ a b, observe out a b = (coords[0]!, "
        "coords[1]!)` still holds on the whole domain. A structurally-different "
        "faithful reshape MUST verify, else the postcondition is over-fit to the "
        "exact impl FORM => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inline-reads",
        "kind": "soundness",
        "expect": "verify",
        # A maximally different shape: no `let` bindings at all, index the array
        # inline in the constructor call. Same value flow, different control-flow
        # shape; the frozen proof still closes it. Confirms the spec is not
        # over-fit to the `let`-bound form. Applied to BOTH sites.
        "module": _both(
            "    return StoredCoord.snapshot coords[0]! coords[1]!\n"
            "    -- impl-end"),
        "rationale": "PASS SOURCE = the detachment clause. Indexing the two "
        "components inline in the constructor (no intermediate locals) retains "
        "the identical snapshot pair, so the detachment clause discharges at both "
        "sites. A second honest shape verifying confirms the spec is not over-fit "
        "to the exact impl form. Else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED, then STRENGTHENED BY AUDIT. The nagini
    # `admiss-reads` self-asserts that the precondition admits a normal
    # test-shaped length-2 input and grants the modeled reads. On a total carrier
    # the analogue is not "does a precondition exist" (this one is trivially
    # satisfiable) but: is the frozen obligation SATISFIABLE at exactly a
    # test-shaped concrete input, and non-degenerate there?
    #
    # AUDIT NOTE (what changed and why). The first shipped form of this case
    # asserted only `observe (snapshot 3 5) 9 9 = (3, 5)` and its disagreement
    # with `observe reference 9 9` — two facts about the PURE model at
    # hand-written literals. That assert never mentions a length-2 container, so
    # it did not in fact demonstrate the property its own rationale claimed
    # ("the `require coords.size = 2` admits a test-shaped length-2 input"), and
    # a `require`-satisfiability claim it never touched was resting on prose. The
    # assert below instantiates the FROZEN OBLIGATION ITSELF at a concrete
    # length-2 container: (i) that container satisfies the `require`; (ii) the
    # obligation's own body — `∀ a b, observe out a b = (c[0]!, c[1]!)` — is
    # DISCHARGEABLE at it by evaluation, so the obligation is not unsatisfiable
    # at a test-shaped point (else PRECOND-TOO-STRONG); (iii) the post-image is
    # non-degenerate there: the retention behaviour that stays bound to the
    # source disagrees with it, so the clause is not an identity every retention
    # meets. The gold body is kept verbatim so the method's own obligation still
    # discharges. LIVENESS was re-measured, not assumed: transposing the pair in
    # conjunct (ii) leaves `unsolved goals ⊢ #[3, 5].size = 2 ∧ …` (exit 1), so a
    # false claim here is caught.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _one_a(
            "    assert (with_name_prefix `admiss\n"
            "      ((#[3, 5] : Array Int).size = 2\n"
            "        ∧ (∀ a b : Int, observe (StoredCoord.snapshot (#[3, 5] : Array Int)[0]!\n"
            "              (#[3, 5] : Array Int)[1]!) a b\n"
            "            = ((#[3, 5] : Array Int)[0]!, (#[3, 5] : Array Int)[1]!))\n"
            "        ∧ observe StoredCoord.reference 9 9\n"
            "            ≠ ((#[3, 5] : Array Int)[0]!, (#[3, 5] : Array Int)[1]!)))\n"
            "    let x := coords[0]!\n"
            "    let y := coords[1]!\n"
            "    return StoredCoord.snapshot x y\n"
            "    -- impl-end"),
        "rationale": "PRECOND-TOO-STRONG probe, stated at a concrete test-shaped "
        "input rather than about it. The assert pins, by evaluation on the "
        "length-2 container `#[3, 5]`: (i) it satisfies `require coords.size = 2`, "
        "so the precondition admits a normal test-shaped coordinate; (ii) the "
        "frozen obligation's own body `∀ a b, observe out a b = (coords[0]!, "
        "coords[1]!)` IS dischargeable at that input — the obligation is "
        "satisfiable exactly there, not vacuous and not unsatisfiable; (iii) the "
        "retention behaviour that tracks its source disagrees with the "
        "capture-time pair under a later state (9, 9), so the clause is "
        "non-degenerate and not met by every retention. The gold body is kept "
        "verbatim so the method's own `ensures` discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete coordinate and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The two sites are attacked
    # separately (the F2P exercises both). Each witness ELABORATES against its
    # rival and FAILS against gold (two real builds per case).
    # =====================================================================
    {
        "id": "weak-reference-a",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug at site 1 (Solution_prepatch_1): retain the source
        # container by reference instead of detaching its components.
        "module": _one_a(
            "    return StoredCoord.reference\n"
            "    -- impl-end"),
        "refinement": "this IS the pre-fix behaviour at the first retaining site: "
        "the input container is retained by reference, so a later in-place "
        "mutation of the caller's array is observable through the stored "
        "attribute. The failing test constructs the object from an array, mutates "
        "the array afterwards, and compares the rendered figure against the "
        "capture-time position; a retained reference moves with the mutation, so "
        "the figures differ and the test does NOT resolve.",
        "rationale": "REJECT from the detachment clause via the DETACHMENT "
        "sub-behaviour: `observe reference a b = (a, b)`, so the retained pair "
        "reflects the source's LATER contents rather than the capture-time pair. "
        "Verifying would be SPEC-TOO-WEAK (the alias→copy delta unpinned). "
        "Refuted at coords=#[3, 5] under later state (0, 0): gold observes "
        "(3, 5) for every (a, b); the rival observes (0, 0) ≠ (3, 5).",
        "witness": _witness("captureCoordA", "#[3, 5]", _REF_CLOSE),
    },
    {
        "id": "weak-reference-b",
        "kind": "uniqueness",
        "expect": "reject",
        # The same pre-patch bug at the independently-observed second site
        # (Solution_prepatch_2).
        "module": _one_b(
            "    return StoredCoord.reference\n"
            "    -- impl-end"),
        "refinement": "the pre-fix behaviour at the SECOND, independently-observed "
        "retaining site: the input coordinate is retained by reference, so a "
        "later in-place mutation of the caller's array moves the stored point. "
        "The failing test exercises this site separately (a distinct construction "
        "with its own later source mutation); a retained reference makes the "
        "rendered figure differ, so it does NOT resolve. Modeled separately "
        "because the two sites are fixed and observed independently.",
        "rationale": "REJECT from the detachment clause via the DETACHMENT "
        "sub-behaviour at site 2: `observe reference a b = (a, b)` reflects the "
        "source's later contents, not the capture-time pair. Refuted at "
        "coords=#[7, 2] under later state (0, 0): gold observes (7, 2) for every "
        "(a, b); the rival observes (0, 0) ≠ (7, 2). Distinct input point from "
        "weak-reference-a, so both sites' binders are exercised.",
        "witness": _witness("captureCoordB", "#[7, 2]", _REF_CLOSE),
    },
    {
        "id": "weak-swap-components-a",
        "kind": "uniqueness",
        "expect": "reject",
        # Fresh, detached, but TRANSPOSED pair: snapshot y x. Correct shape and
        # correct detachment, but the components are in the wrong slots. Ports
        # nagini weak-swap-components. Attacks ORDER.
        "module": _one_a(
            "    let x := coords[0]!\n"
            "    let y := coords[1]!\n"
            "    return StoredCoord.snapshot y x\n"
            "    -- impl-end"),
        "refinement": "its faithful real patch stores a detached but TRANSPOSED "
        "pair (`self._ref_coord = y, x`). The retained coordinate is wrong unless "
        "the two components are equal; the failing test renders the "
        "annotation/arrow at the swapped coordinate, so it lands in the wrong "
        "place and the figure comparison FAILS. Detached, so the detachment "
        "sub-behaviour alone would pass — only the ORDER pin catches it.",
        "rationale": "REJECT from the detachment clause via the ORDER "
        "sub-behaviour: the rival retains `snapshot coords[1]! coords[0]!`, whose "
        "observed pair is `(coords[1]!, coords[0]!)` — different from "
        "`(coords[0]!, coords[1]!)` whenever the two components differ. Refuted at "
        "coords=#[1, 2]: gold observes (1, 2) for every (a, b); the rival "
        "observes (2, 1) ≠ (1, 2).",
        "witness": _witness("captureCoordA", "#[1, 2]"),
    },
    {
        "id": "weak-dup-first-b",
        "kind": "uniqueness",
        "expect": "reject",
        # Fresh, detached, but the SECOND slot duplicates component 0: snapshot
        # x x. Ports nagini weak-dup-first. Attacks COMPONENT-1.
        "module": _one_b(
            "    let x := coords[0]!\n"
            "    return StoredCoord.snapshot x x\n"
            "    -- impl-end"),
        "refinement": "its faithful real patch stores a detached pair that drops "
        "the second component and duplicates the first (`self.xy = x, x`). The "
        "second coordinate of the annotation point is wrong unless the two "
        "components are equal; the failing test's arrow endpoint is misplaced and "
        "the figure comparison FAILS. Detached, so the detachment sub-behaviour "
        "passes — only the COMPONENT-1 pin catches it.",
        "rationale": "REJECT from the detachment clause via the COMPONENT-1 "
        "sub-behaviour: the rival retains `snapshot coords[0]! coords[0]!`, whose "
        "observed second slot is `coords[0]!` — different from `coords[1]!` "
        "whenever the two components differ. Refuted at coords=#[4, 9]: gold "
        "observes (4, 9) for every (a, b); the rival observes (4, 4) ≠ (4, 9). "
        "Attacks the second component slot, complementing weak-dup-second-a.",
        "witness": _witness("captureCoordB", "#[4, 9]"),
    },
    {
        "id": "weak-dup-second-a",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual of weak-dup-first-b at site 1: the FIRST slot duplicates component
        # 1 (snapshot y y). Attacks COMPONENT-0 — the slot the dup-first rival
        # leaves correct — so both component slots are attacked, at both sites.
        "module": _one_a(
            "    let x := coords[0]!\n"
            "    let y := coords[1]!\n"
            "    return StoredCoord.snapshot y y\n"
            "    -- impl-end"),
        "refinement": "its faithful real patch stores a detached pair that drops "
        "the FIRST component and duplicates the second (`self._ref_coord = y, "
        "y`). The first coordinate is wrong unless the two components are equal; "
        "the failing test's arrow lands at the wrong x-position and the figure "
        "comparison FAILS. Detached, so only the COMPONENT-0 pin catches it — the "
        "slot the dup-first rival leaves correct.",
        "rationale": "REJECT from the detachment clause via the COMPONENT-0 "
        "sub-behaviour: the rival retains `snapshot coords[1]! coords[1]!`, whose "
        "observed first slot is `coords[1]!` — different from `coords[0]!` "
        "whenever the two components differ. Refuted at coords=#[6, 1]: gold "
        "observes (6, 1) for every (a, b); the rival observes (1, 1) ≠ (6, 1). "
        "Distinct input point and distinct attacked slot from weak-dup-first-b.",
        "witness": _witness("captureCoordA", "#[6, 1]"),
    },
    {
        "id": "weak-detach-only-when-equal-b",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every other rival is behaviourally CONSTANT in the
        # input: `reference` always, or one fixed wrong `snapshot` shape. So each
        # is refuted at any input where the two components differ, and none of
        # them probes whether the clause is pinned across the input DOMAIN. This
        # rival is partial-domain: it detaches correctly on the diagonal
        # (components equal) and retains by reference off it. It is therefore
        # RIGHT on a whole sub-domain and wrong only off it — the shape a
        # domain-restricted `ensures` (or one an impl could satisfy by case
        # analysis) would let through, and the one an input-insensitive rival set
        # cannot detect.
        "module": _one_b(
            "    if coords[0]! = coords[1]! then\n"
            "      return StoredCoord.snapshot coords[0]! coords[1]!\n"
            "    else\n"
            "      return StoredCoord.reference\n"
            "    -- impl-end"),
        "refinement": "its faithful real patch detaches the pair only when the two "
        "components happen to be equal and otherwise keeps the source container: "
        "`x, y = c; self.<attr> = (x, y) if x == y else c`. The failing test's "
        "coordinate has two EQUAL components, but the reference leg is the one it "
        "takes at the other retaining site's input and at every unequal "
        "coordinate, so a later in-place mutation of the caller's array still "
        "moves the stored point and the rendered figures differ — the test does "
        "NOT resolve. Being correct on a sub-domain is what makes it dangerous: it "
        "passes any check that only samples the diagonal.",
        "rationale": "REJECT from the detachment clause, whose `∀ a b` is required "
        "at EVERY admissible `coords`, not on a sub-domain. The rival satisfies it "
        "wherever `coords[0]! = coords[1]!` and violates it elsewhere, so "
        "verifying would be SPEC-TOO-WEAK by domain restriction. Refuted at "
        "coords=#[8, 3] (components unequal, so the reference leg is taken) under "
        "later state (0, 0): gold observes (8, 3) for every (a, b); the rival "
        "observes (0, 0) ≠ (8, 3). Machine-checked: the witness elaborates against "
        "the rival (exit 0) and leaves `⊢ False` unclosed against the frozen "
        "solution (exit 1); a flipped-claim forgery inverts on both sides, so the "
        "gold-side exit tracks the claim.",
        "witness": _witness("captureCoordB", "#[8, 3]", _REF_CLOSE),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 11 SPEC cases (1
# soundness positive, 1 admissibility, 9 uniqueness rivals: 2 frame-mutation, 2
# alias-echo, 1 swap, 1 dup, 2 diverge, and the swap/dup applied per site) plus
# an EMPTY AXIOM lane. This bundle models the SAME purely-functional core — the
# capture-time retention of a two-component coordinate — over `Array Int` +
# `StoredCoord`/`observe` instead of the sibling's fractional-permission
# `List[object]` carrier. The reference-vs-copy delta, expressed on nagini via
# fractional `list_pred` permissions, ports to the value-level detachment clause
# `∀ a b, observe out a b = (coords[0]!, coords[1]!)`.
#
#   sibling case                     -> here                        disposition
#   --------------------------------------------------------------------------
#   pos-control-reorder              -> pos-read-reorder             PORTED
#   (no sibling)                     -> pos-inline-reads             ADDED
#   admiss-reads                     -> admiss-nondegenerate         PORTED (re-aimed)
#   alias-return-input-a             -> weak-reference-a             PORTED (re-expressed)
#   alias-return-input-b             -> weak-reference-b             PORTED (re-expressed)
#   weak-swap-components (site a)    -> weak-swap-components-a       PORTED
#   weak-dup-first (site b)          -> weak-dup-first-b             PORTED
#   (no sibling)                     -> weak-dup-second-a            ADDED
#   (no sibling)                     -> weak-detach-only-when-equal-b ADDED (audit)
#   frame-mutation-a / -b            -> (none)                       VACUOUS (re-measured)
#   weak-diverge-no-terminate-a / -b -> (none)                       SPEC-CLOSED
#   AXIOM_TESTS ([])                 -> (none)                       DROPPED (G-AX)
#
# PORTED (positive): pos-control-reorder read index 1 before index 0, renamed
#   locals, built the same fresh pair. Here the reshape reads `coords[1]!` before
#   `coords[0]!` and builds the same `snapshot x y`, applied to BOTH sites; the
#   frozen `loom_solve` closes the byte-identical obligation (verified out of
#   band).
# ADDED (pos-inline-reads): a second honest shape (index inline, no `let`
#   bindings) confirming the spec is not over-fit to the `let`-bound form.
# PORTED-RE-AIMED (admissibility): the sibling asserts the fractional-permission
#   precondition admits a length-2 input and grants the modeled reads. This
#   backend's `require coords.size = 2` is trivially satisfiable, so the probe is
#   re-aimed at post-image non-degeneracy: an in-region assert pins that the
#   snapshot yields the capture-time pair under a LATER MUTATED state and that
#   this differs from the reference behaviour. Assert verified live.
# PORTED-RE-EXPRESSED (alias echo -> reference): the sibling's alias-echo returns
#   the caller's own container and is rejected by the PERMISSION system
#   (Acc(Result(),1) + Acc(pair,1/2) = 3/2 > 1). Lean has no permissions; the SAME
#   pre-patch bug (retain by reference) is re-expressed as `StoredCoord.reference`
#   and rejected by the value-level DETACHMENT clause. Both sites, distinct
#   inputs. This is exactly Solution_prepatch_1/2 (G-DIFF).
# PORTED (swap, dup): the sibling's weak-swap-components (ORDER) and weak-dup-first
#   (drop+duplicate a component) port directly to `snapshot y x` and `snapshot x
#   x`. Placed at complementary sites; weak-dup-second-a ADDED so BOTH component
#   slots (COMPONENT-0 and COMPONENT-1) are attacked at BOTH sites, and no single
#   component slot is one every witness holds correct.
# ADDED BY AUDIT (weak-detach-only-when-equal-b): every rival above is
#   behaviourally CONSTANT in the input, so the whole reject lane was
#   input-insensitive and nothing probed the clause's DOMAIN. This rival detaches
#   correctly where the two components are equal and keeps the source reference
#   elsewhere — right on a sub-domain, wrong off it. Machine-checked: rival build
#   exit 1, witness against rival exit 0, witness against the frozen solution
#   exit 1 (`⊢ False`), flipped-claim forgery inverted on both sides.
# VACUOUS (frame-mutation-a/b) — RE-MEASURED BY AUDIT, not taken on the porting
#   map's word. The sibling rejects an in-place WRITE to the read-only input via
#   the fractional-permission system. Here the write is refused by the LANGUAGE,
#   not merely absent: splicing `coords := coords.set! 0 coords[1]!` into the impl
#   region fails to elaborate with `error: `coords` cannot be mutated, only
#   variables declared using `let mut` can be mutated`, so a frame-mutation rival
#   cannot be written at all against this frozen signature (which declares no
#   `mut` binder, and adding one would change the spec — outside this lane). There
#   is no read-only input to overwrite and no substitute probe. Demonstrated, not
#   asserted.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the retention is modeled deeply as
#   StoredCoord/observe), so there is nothing to probe and the gate ignores
#   AXIOM_TESTS regardless.
#
# ESCALATED SPEC LIMIT (audit attack D; not repairable from this lane, so it is
#   recorded rather than patched away). The component carrier is `Int`, and a
#   transform that is the IDENTITY on `Int` is invisible to the obligation even
#   when it is LOSSY on the component domain the bundle's own type bijection
#   declares. Machine-checked against the frozen spec with the frozen proof script
#   unchanged: `snapshot (coords[0]! / 1) (coords[1]! / 1)` VERIFIES (exit 0), at
#   one site and at both; `snapshot (coords[0]! - coords[0]! % 1) …` VERIFIES
#   (exit 0). Refined along the declared component bijection, each truncates a
#   non-integral component, so its faithful counterpart displaces the retained
#   coordinate and does not resolve. Only shapes that are non-identity ON `Int`
#   are caught, and those were confirmed rejected: `Int.fdiv _ 1` (exit 1, both
#   with the frozen script and with a retuned one), `Int.tdiv _ 1` (exit 1),
#   `_ + 1` (exit 1). The sibling battery's own carrier note describes the fix as
#   a carrier that admits no arithmetic on the components at all; changing the
#   carrier is a frozen-spec change, which has to re-clear the equivalence and
#   leakage gates outside this lane. Escalated for that reason.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct input
# points, all length-2 so `require coords.size = 2` holds — no vacuous exclusion):
#     coords — #[3,5], #[7,2], #[1,2], #[4,9], #[6,1], #[8,3]: contents varied;
#              both sites (A: #[3,5],#[1,2],#[6,1]; B: #[7,2],#[4,9],#[8,3])
#              exercised; both component slots differ within each witness (no
#              c[0]!=c[1]!).
#   Every top-level sub-behaviour of the detachment clause is attacked:
#   DETACHMENT (weak-reference-a/b), ORDER (weak-swap-components-a),
#   COMPONENT-0 (weak-dup-second-a), COMPONENT-1 (weak-dup-first-b), DOMAIN
#   (weak-detach-only-when-equal-b — the only rival whose behaviour VARIES with
#   the input, so it is the only one that probes the clause's whole domain rather
#   than one point of it). No two rivals share an input point.
AXIOM_TESTS = []
