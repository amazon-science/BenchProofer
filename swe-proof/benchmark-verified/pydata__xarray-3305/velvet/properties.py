"""properties.py — G-PBT falsification battery for pydata__xarray-3305 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct <method>`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

================================  DEFENDED SURFACE  ==========================

THREE contracted reductions, each over the same free carrier and each with a
SINGLE, byte-identical postcondition:

  reduceElementAttrs   (srcAttrs choice glob)
  reduceContainerAttrs (srcAttrs choice glob)
  reduceLabeledAttrs   (srcAttrs choice glob)
       ensures out = keptAttrs srcAttrs choice glob

The three model an element-level reduction, the container-level reduction that
delegates to it per member, and the user-facing wrapper that forwards through
the container. ``srcAttrs`` is the source metadata (an association list; the
absent mapping is ``[]``); ``choice : Option Bool`` is the per-call keep flag
(``none`` = unstated); ``glob : GlobalPref`` is the ambient library-wide
preference.

``keptAttrs`` is the total, fully-unfolded ``def`` in the ``pure`` region:
``keptAttrs src choice g = if effectiveKeep choice g then src else []`` where
``effectiveKeep (some b) _ = b`` and ``effectiveKeep none g = resolveGlobal g
false`` (the ambient preference resolved against a DROP fallback). The
``axioms`` region declares nothing — there is no opaque answer key, so
evaluating ``keptAttrs`` IS the correct answer, and the only way to satisfy the
postcondition is to compute that exact carry/drop decision.

Load-bearing content of the single clause, per obligation:
  * KEEP sub-domain (the effective decision is ``true``): the result must be a
    copy of ``srcAttrs`` — the WHOLE of it, in order. A rival that returns ``[]``
    there is the pre-image (metadata silently dropped) — the exact behaviour the
    two failing scenarios forbid. Two weaker rivals attack the same branch's
    PAYLOAD rather than its decision (carry only the first entry; carry the
    entries reversed); both are observationally equal to the frozen impl at a
    one-entry mapping, so they are refuted at a two-entry one.
  * PRECEDENCE between the two selectors: ``effectiveKeep (some b) g = b`` for
    EVERY ``g``, so a stated choice is final and the ambient preference is
    consulted ONLY on the unstated path. The two points where the selectors
    disagree — ``(some true, gDrop)`` and ``(some false, gKeep)`` — are what pin
    this, and a rival that consults ``glob`` first is correct everywhere else.
  * DROP sub-domain (the effective decision is ``false`` — an explicit
    ``some false`` OR the unstated ``none`` under the ambient drop default):
    the result must be ``[]``. A rival that copies ``srcAttrs`` there over-keeps
    metadata.
  * The ``none`` path pins the ambient default to DROP (``resolveGlobal
    gDefault false = false``). A rival that treats an unstated flag as KEEP
    reverses the documented default.
  * The delegating obligations additionally pin that the per-call ``choice`` is
    THREADED UNCHANGED to the inner reduction. A container/wrapper that forwards
    ``none`` (or a constant) instead of ``choice`` loses the caller's stated
    decision — the pre-image of the delegation site. Unchanged is stronger than
    flag-DEPENDENT: a delegation that forwards the caller's choice NEGATED still
    varies with it and is still wrong, which is why the container carries a
    negating rival alongside the dropping and constant ones.

INPUT BINDERS (per obligation): ``srcAttrs``, ``choice``, ``glob``. All three
are load-bearing: ``choice``/``glob`` jointly select the branch (``choice`` when
stated, ``glob`` on the ``none`` path, with ``choice`` taking precedence), and
``srcAttrs`` is the value copied on the keep branch. The reject witnesses move
all three across the rivals of each obligation (see the footer's coverage table),
so no binder is pinned — and ``srcAttrs`` varies in LENGTH (1 and 2 entries), not
merely in spelling, since the payload rivals collapse onto the frozen impl at
length 1.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``<method>Tester args = false`` says the extracted
program's result violates the method's postcondition at that concrete input)
and closes by ``decide``, checked in a file whose ``prove_correct`` blocks have
been stripped so no tactic script can mask the verdict. The carrier is
``List (String × String)`` / ``Option Bool`` / ``GlobalPref`` — fully concrete,
decidable literals, no opaque term, so no conditioning is needed and every
witness input is jointly satisfiable by construction (each names three literal
values). Measured during authoring: the extracted ``Exec`` of every method
here — the element reduction AND the two delegating ones — kernel-reduces under
``decide``, so both halves close by ``decide`` at a literal input; the frozen
solution satisfies the postcondition at every input, so the SAME witness fails
against gold (``decide proved … is false``), which is the required
FAIL-on-gold discriminator half. (Every witness below was built twice with
``scripts/lean_verify.sh``: green against its rival, red against the frozen
solution.)

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl of each obligation must verify, else the spec
    is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the nagini sibling self-asserts that an F2P-shaped input
    satisfies its fractional-permission precondition. This backend declares NO
    ``require`` on any method (the operations are total in their inputs), so
    that probe is degenerate; the residual risk is a DEGENERATE post-image. It
    is re-aimed to an in-region ``assert`` pinning all THREE outcomes (keep on a
    stated ``true``, drop on a stated ``false``, drop on the unstated ``none``
    under the ambient default) at F2P-shaped inputs; the impl is kept verbatim
    so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's two
    frame-mutation rivals exist because the read-only source payload is held at
    a fractional heap permission an impl could overwrite. Lean/Velvet are
    referentially transparent: ``srcAttrs`` is an immutable value parameter,
    this bundle declares NO ``mut`` input binder, and there is no heap or
    aliasing. There is no read-only input to overwrite and no permission system
    to trip, so the class has no carrier analogue; NOT ported, no substitute
    fabricated. The nagini "source is read-only" obligation is here structurally
    guaranteed by the ABSENCE of ``mut``, which the frozen spec already encodes.
  * DIVERGENCE / NON-TERMINATION — the nagini sibling carries NO ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case, so there is nothing to port, AND the
    class is CLOSED BY THE SEMANTICS. This bundle sets
    ``loom.semantics.termination "total"`` (Solution.lean line 4), and the option
    cannot drift from the file's ``open TotalCorrectness DemonicChoice``, because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Under ``total`` a postcondition
    is claimed of ALL runs, not only terminating ones, and the verifier demands a
    decreasing measure on every loop. The sharper diverging shape, which cannot be
    dismissed as merely missing the annotation, is refused as well: a loop CARRYING a
    measure that does not decrease (``while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q``, body ``q := q``) is REJECTED on the measure's
    own goal - ``case «decreasing_1: q»``, residual ``⊢ q < q``. (An earlier version
    of this bullet argued from a corpus census in an internal findings doc, "the 401
    ``partial`` bundles admit a diverging rival vacuously, while every ``total``
    bundle rejects it". That census is withdrawn: all 500 velvet bundles set
    ``"total"``.) Measured directly, an
    unbounded-loop rival of the element reduction under this bundle's own header
    is rejected: ``error: Decreasing annotations are required in total
    correctness semantics`` plus a failed WPGen assertion on the ``forIn
    Lean.Loop.mk`` term. So the class is genuinely closed here rather than a
    known hole; nothing to ship either way.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is ``keptAttrs srcAttrs choice
    glob``, a fully-unfolded ``def`` over the method's own arguments; there is
    no answer-key term a wrong impl could echo. The cheapest correct impl
    computes the decision honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of
    the domain right yet diverges on one sub-domain (over-keep, over-drop,
    inverted decision, wrong ``none`` default, or a dropped/constant forwarded
    flag on a delegating obligation).

AXIOM lane: EMPTY. This bundle declares no ``axiom``; the ambient resolver is an
unchanged pure callee modeled DEEPLY as ``resolveGlobal`` (an A-reference,
validated ``resolveGlobal == the real resolver`` by G-AX, NOT consumed as an
axiom — mapping.md §3). The nagini sibling's ``AXIOM_TESTS`` (its consumed
``ambient_keep_default`` probes) belong to the G-AX lane; this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3305"
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
# -- impl-end) or is a prove_correct tactic body, and each is unique in
# Solution.lean (both asserted at load by _swap). Editing only these keeps
# markers.same_spec True and every prove_correct <method> header present.
# ---------------------------------------------------------------------------

# The WHOLE element-reduction impl block (gold). The reject rivals for the
# element obligation swap this and keep the frozen proof (impl-only edit); the
# direct-model positive swaps it and retunes the proof.
_ELEM_IMPL = (
    "    -- impl-start\n"
    "    let effective : Bool :=\n"
    "      match choice with\n"
    "      | some b => b\n"
    "      | none   => resolveGlobal glob false\n"
    "    let attrs : List (String × String) := "
    "if effective then srcAttrs else []\n"
    "    return attrs\n"
    "    -- impl-end")
assert _BASE.count(_ELEM_IMPL) == 1, "element-impl anchor drift"

# The frozen element proof body, and its bare retune (a loop-free single-return
# reshape leaves none of the `simp_all` goals, so `loom_solve` alone closes it).
# The tactic body is elided from the spec view, so retuning it is a proof
# reshape, not a spec change.
_ELEM_PROOF = (
    "prove_correct reduceElementAttrs by\n"
    "  loom_solve\n"
    "  simp_all [keptAttrs, effectiveKeep, resolveGlobal]")
assert _BASE.count(_ELEM_PROOF) == 1, "element-proof anchor drift"
_ELEM_PROOF_BARE = "prove_correct reduceElementAttrs by\n  loom_solve"

# The element impl block's opening (impl-start + the first `let`), UNIQUE to the
# element method (the delegating methods open with `let r`). The admissibility
# case inserts an in-region `assert` immediately after impl-start here, keeping
# the whole gold element body verbatim.
_ELEM_IMPL_HEAD = "    -- impl-start\n    let effective : Bool :="
assert _BASE.count(_ELEM_IMPL_HEAD) == 1, "element-impl-head anchor drift"

# The WHOLE container-reduction impl block (gold): delegate to the element
# reduction, threading `choice` unchanged.
_CONT_IMPL = (
    "    -- impl-start\n"
    "    let r ← reduceElementAttrs srcAttrs choice glob\n"
    "    return r\n"
    "    -- impl-end")
assert _BASE.count(_CONT_IMPL) == 1, "container-impl anchor drift"

# The WHOLE labeled-reduction impl block (gold): forward through the container
# reduction, threading `choice` unchanged.
_LAB_IMPL = (
    "    -- impl-start\n"
    "    let r ← reduceContainerAttrs srcAttrs choice glob\n"
    "    return r\n"
    "    -- impl-end")
assert _BASE.count(_LAB_IMPL) == 1, "labeled-impl anchor drift"


def _elem(body, proof=None):
    """Element variant: replace the whole element impl block; optionally retune
    the element proof (default: keep the frozen proof — an impl-only edit)."""
    s = _swap(_BASE, _ELEM_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")
    return _swap(s, _ELEM_PROOF, proof) if proof is not None else s


# ---- witness preamble. Reach a method contract through Velvet's tester
# ---- machinery: `<name>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose prove_correct blocks are stripped. Every argument is a
# ---- concrete literal so `decide` reduces both the rival's extracted program
# ---- (elaborates) and, at gold, reports the equality false (fails-on-gold).
def _tester(method, args):
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n"
            f"example : {method}Tester {args} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — one structurally-different but CORRECT
    # impl per obligation, each MUST verify. If a faithful correct reshape
    # cannot verify, the postcondition is SPEC-TOO-STRONG (over-pins the impl
    # shape rather than the returned mapping). All three verified green during
    # authoring.
    # =====================================================================
    {
        "id": "pos-element-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded model directly, no
        # intermediate `let effective`/`let attrs`. `out` IS `keptAttrs …`, so
        # the ensures holds definitionally; the single-return reshape leaves no
        # `simp_all` goal, so the proof retunes to a bare `loom_solve`.
        "module": _elem(
            "    return keptAttrs srcAttrs choice glob",
            _ELEM_PROOF_BARE),
        "rationale": (
            "the cheapest honest correct element reduction returns the grounded "
            "model `keptAttrs srcAttrs choice glob` directly (no branch local). "
            "`out` IS that model, so `out = keptAttrs …` holds on the whole "
            "domain and the reproof is `loom_solve`. If this fails to verify the "
            "spec is over-fit to the branch-local impl shape (SPEC-TOO-STRONG). "
            "Also the honest no-ungrounded-echo control: the decision IS the "
            "work, so a direct return is correct, not a cheat. (Nagini: "
            "pos-site1-branch-reorder — a structurally-different correct impl; "
            "re-shaped since this backend's cheapest different shape is the "
            "loop-free direct return and early-return-in-branch is banned here.)"),
    },
    {
        "id": "pos-container-inline-delegation",
        "kind": "soundness",
        "expect": "verify",
        # Inline the delegating call, dropping the `let r` temporary. Same
        # threaded `choice`, same value on every input; the frozen `loom_solve`
        # proof still discharges it.
        "module": _swap(
            _BASE, _CONT_IMPL,
            "    -- impl-start\n"
            "    return (← reduceElementAttrs srcAttrs choice glob)\n"
            "    -- impl-end"),
        "rationale": (
            "inlining the forwarding call (drop the `let r` temporary, thread "
            "`choice` unchanged) is a behaviourally-identical reshape of "
            "reduceContainerAttrs, so `out = keptAttrs srcAttrs choice glob` "
            "still holds on the whole domain and the frozen `loom_solve` proof "
            "closes untouched. Must verify else SPEC-TOO-STRONG over the "
            "temporary-binding shape. (Nagini: pos-site2-inline.)"),
    },
    {
        "id": "pos-labeled-inline-delegation",
        "kind": "soundness",
        "expect": "verify",
        # The wrapper's analogue: inline the forward through the container
        # reduction. Added to defend the third obligation (the wrapper), which
        # nagini did not model as a separate function.
        "module": _swap(
            _BASE, _LAB_IMPL,
            "    -- impl-start\n"
            "    return (← reduceContainerAttrs srcAttrs choice glob)\n"
            "    -- impl-end"),
        "rationale": (
            "inlining the wrapper's forward through the container reduction "
            "(drop the temporary, thread `choice` unchanged) is a "
            "behaviourally-identical reshape of reduceLabeledAttrs, so `out = "
            "keptAttrs srcAttrs choice glob` still holds and the frozen "
            "`loom_solve` proof closes. Must verify else SPEC-TOO-STRONG. "
            "(No nagini counterpart — the user-facing wrapper is modeled as a "
            "third obligation here; ADDED to defend it.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — no method here declares a `require`, so the nagini "a
    # normal input satisfies the precondition" probe is degenerate. Re-aimed at
    # the residual risk on a total domain: that the post-image is DEGENERATE at
    # the interesting point. This case discharges an in-region `assert` (inside
    # the element impl region, elided from the spec view) pinning all THREE
    # discriminating outcomes at F2P-shaped inputs — keep on a stated `true`,
    # drop on a stated `false`, drop on the unstated `none` under the ambient
    # default. The impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _ELEM_IMPL_HEAD,
                "    -- impl-start\n"
                "    assert (with_name_prefix `admiss (\n"
                '      keptAttrs [("u", "K")] (some true) GlobalPref.gDefault '
                '= [("u", "K")] ∧\n'
                '      keptAttrs [("u", "K")] (some false) GlobalPref.gDefault '
                "= [] ∧\n"
                '      keptAttrs [("u", "K")] none GlobalPref.gDefault = []))\n'
                "    let effective : Bool :="),
            _ELEM_PROOF,
            "prove_correct reduceElementAttrs by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [keptAttrs, effectiveKeep, resolveGlobal]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: a stated keep (some true) must carry the source mapping, a "
            "stated drop (some false) must return the empty mapping, and the "
            "unstated flag (none) must ALSO drop under the ambient default "
            "(resolveGlobal gDefault false = false) — three genuinely distinct "
            "outcomes. The in-region assert must discharge (else the obligation "
            "is degenerate / a precondition would be too strong); the element "
            "impl is kept verbatim so `out = keptAttrs …` still verifies. "
            "(Nagini: admiss-site2-precond, re-aimed from precondition "
            "admissibility to post-image non-degeneracy since this backend "
            "declares no `require`.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Element rivals are
    # impl-only edits (frozen proof retained; each fails to verify, confirmed);
    # delegating rivals swap the forwarded flag. All witnesses discriminate
    # (rival green, gold red — verified during authoring).
    # =====================================================================

    # ---- element reduction: the carry/drop decision ------------------------
    {
        "id": "weak-element-always-keep",
        "kind": "uniqueness",
        "expect": "reject",
        # Copy the source mapping unconditionally, ignoring the flag. Correct on
        # the keep sub-domain; wrong wherever the effective decision is drop.
        "module": _elem("    return srcAttrs"),
        "refinement": (
            "always carrying the source metadata honours a stated keep but "
            "ignores a stated drop and the unstated-drop default. The failing "
            "scenario asserts a derived result carries the source metadata when "
            "the caller keeps it (which this happens to satisfy), but the "
            "documented default and the pass-to-pass paths expect a derived "
            "result to carry NO metadata when the caller drops it; an impl that "
            "always keeps changes that default observable and would NOT resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob`: on the DROP "
            "sub-domain keptAttrs is [] but `srcAttrs` is non-empty whenever the "
            "source is non-empty. Verifying would be SPEC-TOO-WEAK (the drop "
            "behaviour unpinned). Refuted at a stated-drop input (choice = some "
            "false). (Nagini: partial-always-keep.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("u", "K")] (some false) GlobalPref.gDefault'),
    },
    {
        "id": "weak-element-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the empty mapping unconditionally — the pre-image of the
        # element reduction (a derived result that never carries metadata).
        # Correct on the drop sub-domain; wrong wherever the decision is keep.
        "module": _elem("    return ([] : List (String × String))"),
        "refinement": (
            "returning no metadata unconditionally IS the pre-image element "
            "reduction: a derived result never carries the source metadata even "
            "when the caller explicitly keeps it. The failing scenario keeps "
            "metadata and asserts the result carries it; this returns the empty "
            "mapping instead — exactly the bug the change fixes, so it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob`: on the KEEP "
            "sub-domain keptAttrs is a copy of srcAttrs but the rival returns []. "
            "Verifying would be SPEC-TOO-WEAK (the keep behaviour unpinned). "
            "Refuted at a stated-keep input (choice = some true), moving choice "
            "and glob off the always-keep rival's values. (Nagini: "
            "partial-always-drop = the site-1 pre-patch.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("a", "1")] (some true) GlobalPref.gDrop'),
    },
    {
        "id": "weak-element-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        # Honour the flag but INVERTED: drop on keep, copy on drop. Wrong on both
        # the keep and the drop sub-domains whenever srcAttrs is non-empty.
        "module": _elem(
            "    let effective : Bool :=\n"
            "      match choice with\n"
            "      | some b => b\n"
            "      | none   => resolveGlobal glob false\n"
            "    let attrs : List (String × String) := "
            "if effective then [] else srcAttrs\n"
            "    return attrs"),
        "refinement": (
            "inverting the effective decision carries metadata exactly when the "
            "caller asked to drop it and drops it when asked to keep — the keep "
            "scenario loses the source metadata (assert fails) and the "
            "default-drop paths gain metadata they must not have. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob`: keptAttrs on the "
            "true-decision branch is srcAttrs and on the false-decision branch is "
            "[]; the inverted rival returns the opposite on each. Verifying would "
            "be SPEC-TOO-WEAK (both branches unpinned). Refuted at a stated-keep "
            "input under gKeep, moving all three binders. (Nagini: "
            "partial-inverted-flag.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("b", "2")] (some true) GlobalPref.gKeep'),
    },
    {
        "id": "weak-element-none-defaults-keep",
        "kind": "uniqueness",
        "expect": "reject",
        # The explicit true/false branches are correct; only the UNSTATED path is
        # wrong — it keeps instead of consulting the ambient drop default.
        # Pins the ambient default's value: resolveGlobal gDefault false = false.
        "module": _elem(
            "    let effective : Bool :=\n"
            "      match choice with\n"
            "      | some b => b\n"
            "      | none   => true\n"
            "    let attrs : List (String × String) := "
            "if effective then srcAttrs else []\n"
            "    return attrs"),
        "refinement": (
            "defaulting the unstated flag to keep (instead of resolving the "
            "ambient preference against a drop fallback, which yields drop under "
            "the baseline config) reverses the documented default: an unstated "
            "keep-choice would carry metadata. The default-drop behaviour is what "
            "the change's documentation and the pass-to-pass paths rely on; a "
            "patch that keeps by default changes the default observable and would "
            "NOT resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob` on the `none` "
            "path: effectiveKeep none gDefault = resolveGlobal gDefault false = "
            "false, so keptAttrs is [], but the rival keeps. This is the "
            "sub-domain that pins the ambient default to DROP; the other rivals "
            "state the flag, so only this witness holds choice = none. Verifying "
            "would be SPEC-TOO-WEAK (the unstated default unpinned). Refuted at "
            "choice = none under gDefault. (Nagini: partial-none-defaults-keep.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("c", "3")] none GlobalPref.gDefault'),
    },

    {
        "id": "weak-element-keep-truncates",
        "kind": "uniqueness",
        "expect": "reject",
        # The carry/drop DECISION is exactly right on all three paths; only the
        # carried PAYLOAD is wrong — the keep branch attaches just the first
        # entry instead of the whole source mapping. Invisible to any witness
        # over a one-entry mapping, which is why it is refuted at a TWO-entry
        # one. ADDED by audit: every other witness here pins srcAttrs at length
        # 1, so the payload-copying half of the keep branch was unattacked.
        "module": _elem(
            "    let effective : Bool :=\n"
            "      match choice with\n"
            "      | some b => b\n"
            "      | none   => resolveGlobal glob false\n"
            "    let attrs : List (String × String) := "
            "if effective then srcAttrs.take 1 else []\n"
            "    return attrs"),
        "refinement": (
            "carrying only the first entry of the source mapping honours the "
            "keep/drop decision but truncates what is carried, so a source "
            "carrying two or more entries surfaces an incomplete mapping on the "
            "derived result. The failing scenario compares the derived result's "
            "whole mapping against the source's for equality, so any source with "
            "more than one entry fails that comparison; a patch that truncates "
            "would NOT resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob`: on the KEEP "
            "sub-domain keptAttrs is the WHOLE of srcAttrs, but `srcAttrs.take 1` "
            "drops every entry past the first. Verifying would be SPEC-TOO-WEAK "
            "in a direction no other rival probes — the clause would pin the "
            "carry/drop DECISION while leaving the carried PAYLOAD unpinned. "
            "Refuted at a stated-keep input over a TWO-entry mapping, the only "
            "witness here whose srcAttrs has length > 1. (No nagini counterpart; "
            "ADDED by audit — the ported witnesses all pinned srcAttrs to one "
            "entry, where this rival is observationally equal to the frozen "
            "impl.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("m", "1"), ("n", "2")] (some true) GlobalPref.gDefault'),
    },
    {
        "id": "weak-element-keep-reorders",
        "kind": "uniqueness",
        "expect": "reject",
        # Second payload-level attack on the keep branch: carry every entry but
        # in reverse order. Like take-1, invisible at length 1; unlike take-1 it
        # preserves the entry SET, so it attacks order/identity rather than
        # completeness.
        "module": _elem(
            "    let effective : Bool :=\n"
            "      match choice with\n"
            "      | some b => b\n"
            "      | none   => resolveGlobal glob false\n"
            "    let attrs : List (String × String) := "
            "if effective then srcAttrs.reverse else []\n"
            "    return attrs"),
        "refinement": (
            "reversing the carried mapping keeps every entry but not the source's "
            "ordering. The carrier's bijection (mapping.md §2) is order-sensitive "
            "— an association list models the source mapping positionally — so a "
            "reduction that reorders does not reproduce the source mapping it is "
            "required to carry, and the scenario's whole-mapping equality "
            "comparison against the source distinguishes them at two or more "
            "entries. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob`: on the KEEP "
            "sub-domain keptAttrs is srcAttrs itself, and `srcAttrs.reverse` is a "
            "different list as soon as srcAttrs has two distinct entries. "
            "Verifying would be SPEC-TOO-WEAK over the carried mapping's "
            "ORDER/identity (take-1 attacks its completeness; this attacks its "
            "shape). Refuted at a stated-keep input over a two-entry mapping. "
            "(No nagini counterpart; ADDED by audit alongside "
            "weak-element-keep-truncates.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("r", "8"), ("s", "9")] (some true) GlobalPref.gKeep'),
    },
    {
        "id": "weak-element-glob-overrides-choice",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult the ambient preference FIRST and let it override an explicit
        # per-call choice; fall back to the choice only under gDefault. Gets the
        # whole `none` path right (including the drop default) and the whole
        # gDefault column right, so none of the ported rivals' failure modes
        # apply — it inverts the PRECEDENCE between the two selectors.
        "module": _elem(
            "    let effective : Bool :=\n"
            "      match glob with\n"
            "      | GlobalPref.gKeep => true\n"
            "      | GlobalPref.gDrop => false\n"
            "      | GlobalPref.gDefault => "
            "(match choice with | some b => b | none => false)\n"
            "    let attrs : List (String × String) := "
            "if effective then srcAttrs else []\n"
            "    return attrs"),
        "refinement": (
            "letting the ambient library-wide preference override an explicit "
            "per-call choice inverts the documented precedence: a caller that "
            "states a decision must have it honoured verbatim, and only an "
            "unstated decision may defer to the ambient preference. Under an "
            "ambient drop preference this rival discards metadata a caller "
            "explicitly asked to carry — the failing scenario states its choice "
            "explicitly, so under that ambient setting it still loses the source "
            "metadata and the patch would NOT resolve."),
        "rationale": (
            "REJECT from `out = keptAttrs srcAttrs choice glob`: effectiveKeep "
            "(some b) g = b for EVERY g, so a stated choice is precedence-final; "
            "this rival returns resolveGlobal glob applied ahead of the choice, "
            "which differs at (some true, gDrop) and (some false, gKeep). "
            "Verifying would be SPEC-TOO-WEAK over the PRECEDENCE between choice "
            "and glob — an axis no ported rival touches: always-keep/always-drop "
            "ignore the flag entirely, inverted-decision negates it, and "
            "none-defaults-keep only mis-handles the unstated path, while this "
            "rival is correct on the whole `none` path AND the whole gDefault "
            "column. Refuted at (some true, gDrop). (No nagini counterpart; "
            "ADDED by audit.)"),
        "witness": _tester(
            "reduceElementAttrs",
            '[("d", "4")] (some true) GlobalPref.gDrop'),
    },

    # ---- container reduction: threading the flag ---------------------------
    {
        "id": "weak-container-drops-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward `none` instead of `choice` — the pre-image of the delegation
        # site (the caller's stated decision is lost, so the member falls back to
        # the ambient drop default). Correct when the caller already resolves to
        # drop; wrong when the caller stated keep.
        "module": _swap(
            _BASE, _CONT_IMPL,
            "    -- impl-start\n"
            "    let r ← reduceElementAttrs srcAttrs none glob\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": (
            "forwarding an unstated flag instead of the caller's is the "
            "pre-image delegation: the member reduction receives no stated "
            "decision and falls back to the ambient drop default, so a caller "
            "that stated keep silently loses the source metadata. The failing "
            "path enters through the container with a stated keep; with the flag "
            "dropped the metadata is dropped and the assert fails — exactly the "
            "bug, so it does NOT resolve."),
        "rationale": (
            "REJECT from reduceContainerAttrs's `out = keptAttrs srcAttrs choice "
            "glob`: forwarding none makes out = keptAttrs srcAttrs none glob = "
            "[] (under the ambient drop default), but the spec pins it to "
            "keptAttrs srcAttrs choice glob, a copy when choice = some true. "
            "Verifying would be SPEC-TOO-WEAK (the threaded flag unpinned). "
            "Refuted at choice = some true. (Nagini: site2-drops-flag.)"),
        "witness": _tester(
            "reduceContainerAttrs",
            '[("u", "K")] (some true) GlobalPref.gDefault'),
    },
    {
        "id": "weak-container-const-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward a CONSTANT keep instead of `choice`. Correct when the caller
        # stated keep; wrong when the caller stated drop. Added so the container
        # obligation's binders are moved off the drops-flag witness's point
        # (choice some true -> some false, glob gDefault -> gDrop).
        "module": _swap(
            _BASE, _CONT_IMPL,
            "    -- impl-start\n"
            "    let r ← reduceElementAttrs srcAttrs (some true) glob\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": (
            "forwarding a constant keep pins the member reduction to always "
            "carry metadata regardless of the caller's decision, so a caller "
            "that stated drop still gets metadata it must not have. The paths "
            "that enter through the container with a stated drop then observe "
            "unexpected metadata and would NOT resolve."),
        "rationale": (
            "REJECT from reduceContainerAttrs's `out = keptAttrs srcAttrs choice "
            "glob`: forwarding (some true) makes out = keptAttrs srcAttrs (some "
            "true) glob = srcAttrs, but the spec pins it to keptAttrs srcAttrs "
            "choice glob = [] when choice = some false. Verifying would be "
            "SPEC-TOO-WEAK. Refuted at choice = some false under gDrop, moving "
            "choice and glob off the drops-flag rival's point (so the container "
            "obligation's binders are not pinned). (No nagini counterpart; ADDED "
            "for per-obligation binder coverage.)"),
        "witness": _tester(
            "reduceContainerAttrs",
            '[("x", "9")] (some false) GlobalPref.gDrop'),
    },

    {
        "id": "weak-container-negates-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Thread the caller's choice but NEGATED. Unlike drops-flag/const-flag,
        # the forwarded value still DEPENDS on the caller's, so a rival that
        # merely "forwards something" is not enough — the delegation must forward
        # it UNCHANGED. Correct on the whole `none` path (none.map _ = none), so
        # the ambient-default column is untouched.
        "module": _swap(
            _BASE, _CONT_IMPL,
            "    -- impl-start\n"
            "    let r ← reduceElementAttrs srcAttrs "
            "(choice.map (fun b => !b)) glob\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": (
            "forwarding the caller's decision inverted is a delegation that "
            "threads a value while corrupting it: a stated keep reaches the "
            "member reduction as a stated drop and vice versa. The failing path "
            "enters through the container with a stated keep, so the member drops "
            "the source metadata and the result carries none — the same "
            "observable as the dropped-flag delegation, so it does NOT resolve."),
        "rationale": (
            "REJECT from reduceContainerAttrs's `out = keptAttrs srcAttrs choice "
            "glob`: forwarding (choice.map not) yields keptAttrs srcAttrs "
            "(choice.map not) glob, which differs from the spec's value at every "
            "STATED choice over a non-empty mapping. Verifying would be "
            "SPEC-TOO-WEAK over the delegation being IDENTITY on the flag rather "
            "than merely flag-dependent — drops-flag and const-flag both forward "
            "a CONSTANT, so a spec that only forbade constants would admit this. "
            "Refuted at choice = some true. (No nagini counterpart; ADDED by "
            "audit to pin the threading as unchanged.)"),
        "witness": _tester(
            "reduceContainerAttrs",
            '[("e", "5")] (some true) GlobalPref.gDefault'),
    },

    # ---- labeled wrapper: threading the flag -------------------------------
    {
        "id": "weak-labeled-drops-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # The wrapper's analogue of the pre-image delegation: forward `none`
        # instead of `choice` to the container reduction.
        "module": _swap(
            _BASE, _LAB_IMPL,
            "    -- impl-start\n"
            "    let r ← reduceContainerAttrs srcAttrs none glob\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": (
            "the user-facing wrapper forwarding an unstated flag instead of the "
            "caller's loses the stated decision before it ever reaches the "
            "member reduction, so end to end a stated keep drops the source "
            "metadata. The failing scenario enters through the wrapper with a "
            "stated keep and asserts the result carries the metadata; with the "
            "flag dropped it does not — the bug, so it does NOT resolve."),
        "rationale": (
            "REJECT from reduceLabeledAttrs's `out = keptAttrs srcAttrs choice "
            "glob`: forwarding none yields keptAttrs srcAttrs none glob = [] "
            "under the ambient drop default, but the spec pins it to keptAttrs "
            "srcAttrs choice glob, a copy when choice = some true. Verifying "
            "would be SPEC-TOO-WEAK. Refuted at choice = some true. (No nagini "
            "counterpart — the wrapper is a third obligation here; the same "
            "flag-forwarding attack as site2-drops-flag, re-expressed on it.)"),
        "witness": _tester(
            "reduceLabeledAttrs",
            '[("p", "0")] (some true) GlobalPref.gDefault'),
    },
    {
        "id": "weak-labeled-const-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward a CONSTANT drop instead of `choice`. Correct when the caller
        # resolves to drop; wrong when the caller (or the ambient default) keeps.
        # Added so the wrapper obligation's binders move off the drops-flag point
        # (choice some true -> none, glob gDefault -> gKeep).
        "module": _swap(
            _BASE, _LAB_IMPL,
            "    -- impl-start\n"
            "    let r ← reduceContainerAttrs srcAttrs (some false) glob\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": (
            "forwarding a constant drop pins the wrapper to never carry metadata "
            "regardless of the caller's decision or the ambient preference, so a "
            "caller that keeps (or an ambient keep preference on the unstated "
            "path) still loses the source metadata. The keep paths through the "
            "wrapper then fail and it would NOT resolve."),
        "rationale": (
            "REJECT from reduceLabeledAttrs's `out = keptAttrs srcAttrs choice "
            "glob`: forwarding (some false) yields keptAttrs srcAttrs (some "
            "false) glob = [], but the spec pins it to keptAttrs srcAttrs choice "
            "glob = srcAttrs when the unstated flag resolves keep (choice = none "
            "under gKeep, effectiveKeep none gKeep = resolveGlobal gKeep false = "
            "true). Verifying would be SPEC-TOO-WEAK. Refuted at choice = none "
            "under gKeep — moving both choice and glob off the drops-flag rival's "
            "point AND exercising the ambient-KEEP preference no other witness "
            "reaches. (No nagini counterpart; ADDED for per-obligation binder "
            "coverage and to pin the gKeep resolution.)"),
        "witness": _tester(
            "reduceLabeledAttrs",
            '[("q", "7")] none GlobalPref.gKeep'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 10 SPEC cases (2
# soundness positives, 1 admissibility, 2 MANDATORY frame-mutation rivals, 5
# uniqueness rivals) plus a two-case AXIOM lane. It contracts TWO functions over
# a full-permission-mutable `List[int]` metadata payload — site 1
# (reduce_result_metadata, the per-array reduction) and site 2
# (entrypoint_reduce_metadata, the container delegation) — with the source
# payload held read-only at a fractional permission. This backend models the
# SAME keep-metadata semantics DEEPLY (`keptAttrs` / `effectiveKeep` /
# `resolveGlobal` over immutable `List (String × String)` / `Option Bool` /
# `GlobalPref` carriers) across THREE obligations: the element reduction (nagini
# site 1), the container reduction (nagini site 2), and the user-facing wrapper
# (a third obligation nagini did not model as a separate function — mapping.md
# §1).
#
#   nagini case                     kind          -> here                          disposition
#   ---------------------------------------------------------------------------------------------
#   pos-site1-branch-reorder        soundness     -> pos-element-direct-model      RE-SHAPED
#   pos-site2-inline                soundness     -> pos-container-inline-delegation PORTED
#                                                    (+ pos-labeled-inline-delegation ADDED)
#   admiss-site2-precond            admissibility -> admiss-nondegenerate          RE-AIMED
#   frame-mutate-self_meta          uniqueness    -> (none)                        VACUOUS
#   frame-mutate-self_meta-index    uniqueness    -> (none)                        VACUOUS
#   partial-always-keep             uniqueness    -> weak-element-always-keep      PORTED
#   partial-always-drop             uniqueness    -> weak-element-always-drop      PORTED
#   partial-inverted-flag           uniqueness    -> weak-element-inverted-decision PORTED
#   partial-none-defaults-keep      uniqueness    -> weak-element-none-defaults-keep PORTED
#   site2-drops-flag                uniqueness    -> weak-container-drops-flag     PORTED
#                                                    (+ weak-container-const-flag ADDED)
#                                                    (+ weak-container-negates-flag ADDED, audit)
#                                                    (+ weak-labeled-drops-flag /
#                                                       weak-labeled-const-flag  ADDED, wrapper)
#   (no counterpart)                uniqueness    -> weak-element-keep-truncates   ADDED (audit)
#   (no counterpart)                uniqueness    -> weak-element-keep-reorders    ADDED (audit)
#   (no counterpart)                uniqueness    -> weak-element-glob-overrides-choice ADDED (audit)
#   AXIOM_TESTS (ax-sound/ax-cover) axiom         -> (none)                        DROPPED (G-AX lane)
#
# 5 uniqueness ported (4 element + 1 container), 7 uniqueness ADDED (a second and
# third container rival + two wrapper rivals + three element rivals landed by the
# audit) for per-obligation coverage; 1 soundness re-shaped + 2 soundness
# ported/added; 1 admissibility re-aimed; 2 uniqueness vacuous (frame); axiom
# lane dropped.
#
# AUDIT ADDITIONS (three element rivals + one container rival). The ported
# battery pinned `srcAttrs` to a ONE-ENTRY mapping in every witness, and pinned
# the choice/glob relationship to "one of them is ignored or negated". Two axes
# were therefore unattacked, each admitting a rival that is observationally EQUAL
# to the frozen impl at every point the ported witnesses examine:
#   * the carried PAYLOAD on the keep branch (the clause pins the whole of
#     srcAttrs, not merely a non-empty prefix) -> weak-element-keep-truncates
#     (`srcAttrs.take 1`) and weak-element-keep-reorders (`srcAttrs.reverse`),
#     both refuted only at a TWO-entry mapping;
#   * the PRECEDENCE between an explicit choice and the ambient preference (a
#     stated choice is final for every glob) -> weak-element-glob-overrides-choice,
#     which is correct on the entire `none` path and the entire gDefault column
#     and so evades all four ported element rivals;
#   * the delegation being the IDENTITY on the flag rather than merely
#     flag-dependent (drops-flag and const-flag both forward a CONSTANT) ->
#     weak-container-negates-flag.
# All four were machine-checked before landing: the rival fails to verify, its
# witness elaborates against the rival and fails against the frozen solution by
# `decide` EVALUATING the tester (`Tactic 'decide' proved that the proposition
# ...Tester ... = false is false`), and a retune of the frozen proof script with
# case splits over both binders still does not close them (for take-1 the residual
# goal is literally `srcAttrs.length <= 1`), so their rejection is the spec's and
# not a tactic gap.
#
# RE-SHAPED (pos-site1-branch-reorder -> pos-element-direct-model): the nagini
#   positive reorders the keep/drop branches with an early return on the drop
#   branch. Early-return-inside-a-branch is not the idiom here and the
#   maximally-different correct shape is the loop-free direct return of the
#   grounded model `keptAttrs srcAttrs choice glob`, with the proof retuned to a
#   bare `loom_solve` (the single-return reshape leaves no `simp_all` goal). Same
#   ARGUMENT: a faithful correct impl of a different shape must verify.
# PORTED / ADDED (pos-site2-inline): the container inline-delegation ports
#   directly; a wrapper inline-delegation is ADDED to DEFEND the third
#   obligation nagini did not model.
# RE-AIMED (admiss-site2-precond -> admiss-nondegenerate): the nagini case
#   asserts a half-permission is in hand at the forwarding call for a normal
#   input. No method here declares a `require` (the operations are total in
#   their inputs) and there is no permission surface, so that reading is
#   degenerate; re-aimed at the residual risk — a degenerate post-image — with a
#   live in-region assert pinning all three outcomes (keep on stated true, drop
#   on stated false, drop on unstated none under the ambient default) at
#   F2P-shaped inputs, the impl kept verbatim.
# PORTED (the four element value/branch rivals): partial-always-keep,
#   partial-always-drop (the site-1 pre-patch), partial-inverted-flag, and
#   partial-none-defaults-keep port one-for-one to the element obligation,
#   refuted respectively on the drop sub-domain, the keep sub-domain, both
#   branches, and the unstated-default sub-domain.
# PORTED / ADDED (site2-drops-flag): the flag-dropping delegation rival ports to
#   weak-container-drops-flag and is re-expressed on the wrapper as
#   weak-labeled-drops-flag. A CONSTANT-flag rival is ADDED to each delegating
#   obligation (weak-container-const-flag, weak-labeled-const-flag) so each
#   delegating obligation is attacked at two distinct input points and its
#   binders are not pinned (see coverage below).
# VACUOUS (frame-mutate-self_meta, frame-mutate-self_meta-index): the two nagini
#   MANDATORY frame rivals write the read-only source payload (an append; an
#   in-place index store) and are rejected for INSUFFICIENT PERMISSION under a
#   fractional list predicate. This backend is referentially transparent:
#   `srcAttrs` is an immutable value parameter, this bundle declares NO `mut`
#   input binder, and there is no heap, aliasing, or fractional permission. There
#   is no read-only input to overwrite and no frame clause to violate, so the
#   class has no carrier analogue. Omitted as a genuine carrier fact, NOT
#   fabricated. The nagini read-only obligation is here structurally guaranteed
#   by the absence of `mut`, which the frozen spec already encodes.
# DROPPED (AXIOM_TESTS): the nagini battery's AXIOM_TESTS validate the consumed
#   `ambient_keep_default` axiom against the real `_get_keep_attrs(default=False)`
#   resolver. This bundle consumes NO axiom — the resolver is modeled deeply as
#   `resolveGlobal`, an A-reference validated by G-AX (mapping.md §3), NOT a
#   consumed axiom — so there is no axiom lane to mirror; the axiom lane is
#   G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
#
# BINDER / CLAUSE COVERAGE. Each of the three obligations has a single top-level
#   `ensures` clause `out = keptAttrs srcAttrs choice glob` with three input
#   binders (srcAttrs, choice, glob), each DEFENDED by its own verifying
#   soundness positive (+ the admissibility case for the element obligation) and
#   ATTACKED by >=2 reject rivals at distinct input points:
#     reduceElementAttrs   (7 witnesses)
#       always-keep         [("u","K")]             (some false) gDefault
#       always-drop         [("a","1")]             (some true)  gDrop
#       inverted-decision   [("b","2")]             (some true)  gKeep
#       none-defaults-keep  [("c","3")]             none         gDefault
#       keep-truncates      [("m","1"),("n","2")]   (some true)  gDefault  <- audit
#       keep-reorders       [("r","8"),("s","9")]   (some true)  gKeep     <- audit
#       glob-overrides      [("d","4")]             (some true)  gDrop     <- audit
#     reduceContainerAttrs (3 witnesses)
#       drops-flag          [("u","K")]             (some true)  gDefault
#       const-flag          [("x","9")]             (some false) gDrop
#       negates-flag        [("e","5")]             (some true)  gDefault  <- audit
#     reduceLabeledAttrs   (2 witnesses)
#       drops-flag          [("p","0")]             (some true)  gDefault
#       const-flag          [("q","7")]             none         gKeep
#   Per obligation, `srcAttrs` takes a distinct literal in each witness, `choice`
#   ranges over some true / some false / none, and `glob` ranges over gDefault /
#   gDrop / gKeep — so no binder is pinned across any obligation's rivals. The
#   `none` path (element none-defaults-keep, labeled const-flag) and the ambient
#   preferences gDrop/gKeep are all exercised, so the spec's dependence on `glob`
#   on the unstated path is demonstrated, not assumed. pts >= 2 per obligation
#   (12 distinct points across the three).
#
#   `srcAttrs` VARIES IN LENGTH, not only in spelling. The audit's two payload
#   rivals are refuted at a TWO-entry mapping; every other witness uses one entry.
#   This is the difference between a binder that "varies" and a binder whose
#   variation changes the spec's verdict: at length 1, `srcAttrs`, `srcAttrs.take
#   1` and `srcAttrs.reverse` are the same list, so a battery whose witnesses all
#   use singletons cannot see the clause pinning the WHOLE carried mapping — the
#   length-2 points are what make that half of the keep branch load-bearing.
#   Likewise `glob` is not merely enumerated: at (some true, gDrop) and (some
#   false, gKeep) the ambient preference and the stated choice DISAGREE, and the
#   spec resolves in favour of the choice, which is the point
#   weak-element-glob-overrides-choice pins.
#
# AXIOM_TESTS: empty. No consumed axiom to probe; this gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []
