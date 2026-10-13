"""properties.py — G-PBT falsification battery for django__django-13590 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct reconstructSequence`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  reconstructSequence (s : SeqVal) (f : Int → Int)
      return (out : Except RebuildErr SeqVal)
    ensures out = resolvedSeq s.positionalCtor s.items f

The method resolves each member of a sequence value independently (via the free
resolver ``f``) and reconstructs the sequence, preserving its type. ``SeqVal``
carries the two observables the desired behaviour constrains: ``positionalCtor``
(does this sequence's type require its members supplied as separate positional
arguments, rather than as one iterable?) and ``items`` (the members in order).
``resolvedSeq`` is a total, fully-unfolded pure ``def`` over the method's own
arguments — the ``axioms`` region is EMPTY, so there is NO opaque answer key to
echo. The single load-bearing ``ensures`` pins three independently-attackable
facets:

  * SUCCESS / DEFINEDNESS — reconstruction ALWAYS succeeds (the success
    constructor ``Except.ok``), for EVERY sequence type. This is the delta the
    change adds: a type requiring positional members, handed a single iterable,
    fails; the fix routes it through the positional construction so it succeeds.
    A rival that reconstructs unconditionally by one convention is rejected on
    the sub-domain where that convention is inadmissible.
  * TYPE PRESERVATION — the reconstructed sequence keeps its own type
    (``positionalCtor`` carried through). A rival that reports the wrong type tag
    is refuted even though its members are correct.
  * PER-MEMBER RESOLUTION — every member is the resolver applied to the
    original member (``items.map f``). A rival that returns members unresolved
    is refuted.
  * LENGTH + ORDER — the members are ALL present and in their original order.
    Length and order are independent: dropping a member and permuting the
    members are different divergences, and a rival that only shortens the list
    leaves the order clause untested. Both are attacked separately
    (weak-drop-last-member, weak-reverse-order).

TWO INPUT BINDERS, both load-bearing and both varied by the reject witnesses:
  * ``s`` (via ``positionalCtor`` and ``items``) — ``positionalCtor`` drives
    which construction convention is admissible; ``items`` drives the resolved
    contents and length. Witnesses move ``positionalCtor`` over true/false and
    ``items`` over one- and two-member lists.
  * ``f`` — the free per-member resolver. In the abstract spec it is opaque; a
    witness pins a CONCRETE resolver literal (``fun x => x`` or ``fun x => x + 1``)
    at a concrete ``s`` so the whole extracted-program result reduces by kernel
    computation and ``decide`` closes. Witnesses move ``f`` over the identity and
    a non-identity ``+1``, so the rival that ignores ``f`` is refuted where ``f``
    is observably non-identity.

CARRIER NOTE — THE OPAQUE-RESOLVER + DECIDABLE BOUNDARY. A witness reaches the
post-image through Velvet's own tester machinery
(``reconstructSequenceTester s f = false`` says the extracted program's result
violates the method's postcondition at that concrete input), checked in a file
whose ``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Unlike the loop-carrying siblings, the frozen impl here is LOOP-FREE
(a single ``if`` over ``positionalCtor`` returning ``rebuild*``), so ``decide``
reduces the extracted FROZEN program too — the gold tester returns ``true`` at
every input, so ``reconstructSequenceTester … = false`` FAILS on gold (the
required discrimination half) while ELABORATING against each rival (whose result
genuinely differs). The result carrier ``Except _ _`` needs a ``DecidableEq``
the tester's ``prove_postcondition_decidable_for`` does not synthesize on its
own, so each witness derives it first via ``deriving instance DecidableEq for
Except`` — an instance, not an assumption (no ``axiom`` / ``sorry`` /
``native_decide``), so the frozen solution still rejects each witness. (Both
halves of every witness were checked out of band with ``scripts/lean_verify.sh``:
each ELABORATES green against its rival and FAILS red against the frozen
solution.)

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally different but
    behaviourally identical correct impls (return the grounded model directly;
    reorder the reconstruction branch to test the iterable convention first;
    select the reconstruction PRIMITIVE and apply it at one call site) must
    verify, else the spec is SPEC-TOO-STRONG on the shape of the impl. The third
    is not redundant: it is the only one the frozen proof script does NOT
    discharge, so it is the one that actually probes shape-independence.
  * ADMISSIBILITY — the method carries NO precondition (the pre-conditions region
    is empty), so the nagini "an F2P-shaped input satisfies the precondition"
    probe (its ``admissibility-readonly-usable``) is degenerate here (every input
    is in-domain). RE-AIMED at the residual total-domain risk — that the
    post-image is DEGENERATE at the interesting point — via an in-region
    ``assert`` pinning three F2P-shaped facts: a positional-type reconstruction
    of ``[5]`` under ``+1`` yields ``[6]`` and keeps the type, an
    iterable-type reconstruction of the same yields ``[6]`` and keeps that type,
    and a two-member reconstruction resolves BOTH members. The impl is kept
    verbatim so the method's own obligation still discharges; the proof gains a
    ``simp [resolvedSeq]`` arm to clear the assert VC. Verified out of band: a
    mirror assert claiming the wrong resolved value leaves ``⊢ False``.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    makes it MANDATORY (``frame-mutation-write-value``) because the sequence
    input carries a fractional heap permission ``Acc(list_pred(value), 1/2)`` an
    impl can illegally overwrite. Lean and Velvet are referentially transparent:
    ``s`` and ``f`` are immutable values, this bundle declares NO ``mut`` binder,
    there is no heap, no aliasing, no fractional permission — so there is no
    read-only input to overwrite and no substitute probe to build. Reported
    vacuous, not fabricated (footer). The sibling's read-only obligation is here
    structurally guaranteed by the ABSENCE of ``mut``, which the frozen spec
    already encodes.
  * CONTROL-FLOW-EFFECT — the nagini raise-vs-succeed discriminator
    (``atk_3``) is here made a VALUE-level distinction: the two construction
    outcomes are the two ``Except`` constructors (mapping.md §2), so a
    reconstruction that would raise on the real side is the ``Except.error``
    constructor the load-bearing ``ensures`` forbids (it demands ``Except.ok``).
    Ported as the DEFINEDNESS attacks (weak-uncond-iterable / weak-uncond-
    positional), refuted by the success-constructor demand.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the nagini sibling records (there
    the token is a capability, not an echo-able value; here the post-image is a
    fully-unfolded ``def`` over the method's own arguments, empty ``axioms``
    region). There is no answer key to echo; the honest cheapest correct impl
    computes ``resolvedSeq`` directly, which the direct-model positive covers.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: rivals right on part of the
    domain but diverging on a sub-domain (the two unconditional-convention
    rivals, a dropped type tag, an unresolved-members rival, a dropped member).

WITNESS PLACEMENT. The reject witnesses probe SIX distinct input points, moving
both binders: ``positionalCtor`` over true/false, ``items`` over one- and
two-member lists, and ``f`` over the identity and a non-identity ``+1``. No
binder is pinned at a single value across the reject lane, so the coverage tool
sees the spec's dependence on each.

AXIOM lane: EMPTY. The nagini sibling ships two AXIOM_TESTS (``resolve_one`` and
``build_container``), which the porting map DROPS — the axiom lane is G-AX's job
and this gate ignores ``AXIOM_TESTS`` regardless; this bundle declares no
``axiom`` (the reconstruction is modeled deeply as ``resolvedSeq`` /
``rebuildPositional`` / ``rebuildIterable``, an A-reference validated by G-CONF,
not a consumed axiom).
"""
from pathlib import Path

INSTANCE = "django__django-13590"
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
# -- impl-end) or is the frozen prove_correct tactic body; each is unique in
# Solution.lean (asserted at load by _swap). Editing only these keeps
# markers.same_spec True and the `prove_correct reconstructSequence` statement
# byte-identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The whole reconstruction dispatch + return (wholly inside the impl region).
_DISPATCH = (
    "    let result : Except RebuildErr SeqVal :=\n"
    "      if s.positionalCtor then rebuildPositional s.positionalCtor resolved\n"
    "      else rebuildIterable s.positionalCtor resolved\n"
    "    return result")
assert _BASE.count(_DISPATCH) == 1, "dispatch anchor drift — re-sync _DISPATCH"

# The first impl line (unique); the admissibility case inserts an in-region
# `assert` immediately before it, keeping the whole gold body.
_FIRST_IMPL_LINE = "    let resolved := s.items.map f"
assert _BASE.count(_FIRST_IMPL_LINE) == 1, "first-impl-line anchor drift"

# The frozen proof body (tactic script only; elided from the spec view). The
# direct-model positive and the admissibility case retune it without touching
# the spec or dropping the obligation.
_PROOF_GOLD = (
    "prove_correct reconstructSequence by\n"
    "  loom_solve\n"
    "  simp only [rebuildPositional, rebuildIterable, resolvedSeq]\n"
    "  split_ifs <;> simp_all\n")
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# A loop-free/expression proof body: when the impl returns the grounded model
# directly there is no branch to split, so `loom_solve` alone closes it.
_PROOF_FLAT = "prove_correct reconstructSequence by\n  loom_solve\n"


def _impl(new_dispatch, proof=_PROOF_GOLD):
    """Full variant: the reconstruction dispatch replaced; proof optionally
    retuned. Every other byte (spec + first impl line) is untouched."""
    v = _swap(_BASE, _DISPATCH, new_dispatch)
    if proof is not _PROOF_GOLD:
        v = _swap(v, _PROOF_GOLD, proof)
    return v


# ---- witness preamble. Reach the method contract through Velvet's own tester
# ---- machinery: `reconstructSequenceTester s f = false` says the extracted
# ---- program's result violates the postcondition at that concrete input. The
# ---- `Except _ _` post-image needs a DecidableEq the tester does not
# ---- synthesize, so derive it first (an instance, not an assumption). Checked
# ---- in a file whose `prove_correct` block has been stripped.
_DEC = "deriving instance DecidableEq for Except\n\n"


def _witness(seqval, resolver):
    return (
        _DEC +
        "extract_program_for reconstructSequence\n"
        "prove_precondition_decidable_for reconstructSequence\n"
        "prove_postcondition_decidable_for reconstructSequence\n"
        "derive_tester_for reconstructSequence\n\n"
        f"example : reconstructSequenceTester {seqval} {resolver} = false := by\n"
        "  decide\n")


# ---- the admissibility variant: an in-region non-degeneracy `assert` before
# ---- the (verbatim) gold body, with the proof gaining a `simp [resolvedSeq]`
# ---- arm to clear the assert VC. The `resolvedSeq …` equalities are pinned at
# ---- concrete F2P-shaped inputs; a wrong RHS leaves `⊢ False` (verified out of
# ---- band), so the assert is LIVE.
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss (\n"
    "      resolvedSeq true [(5:Int)] (fun x => x + 1) "
    "= Except.ok { positionalCtor := true, items := [6] } ∧\n"
    "      resolvedSeq false [(5:Int)] (fun x => x + 1) "
    "= Except.ok { positionalCtor := false, items := [6] } ∧\n"
    "      resolvedSeq true [(1:Int), 2] (fun x => x) "
    "= Except.ok { positionalCtor := true, items := [1, 2] }))\n"
    + _FIRST_IMPL_LINE)
_ADMISS_PROOF = (
    "prove_correct reconstructSequence by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | (refine ⟨?_, ?_, ?_⟩ <;> simp [resolvedSeq])\n"
    "    | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; "
    "split_ifs <;> simp_all)\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no branch at all. `out` IS `resolvedSeq …`, so the ensures holds
        # trivially; the reproof is a bare `loom_solve` (no branch to split).
        "module": _impl(
            "    let result := resolvedSeq s.positionalCtor s.items f\n"
            "    return result",
            proof=_PROOF_FLAT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`resolvedSeq s.positionalCtor s.items f` directly (no reconstruction "
            "branch). `out` IS that model, so the ensures holds on the whole "
            "domain; the reproof is `loom_solve`. If this fails to verify the spec "
            "is over-fit to the branch code shape (SPEC-TOO-STRONG). Also the "
            "honest no-ungrounded-echo control: the model IS the real work, so a "
            "direct return is correct, not a cheat. (Nagini: pos-control-computed-"
            "spread / pos-control-atk6-equal-list — the single-call-site and "
            "equal-value reshapes collapse to the direct grounded model on this "
            "carrier.)"),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Test the iterable convention first (negated condition), fall through to
        # the positional convention. Behaviourally identical on every input; the
        # frozen split_ifs proof still discharges both arms.
        "module": _impl(
            "    let result : Except RebuildErr SeqVal :=\n"
            "      if !s.positionalCtor then rebuildIterable s.positionalCtor resolved\n"
            "      else rebuildPositional s.positionalCtor resolved\n"
            "    return result"),
        "rationale": (
            "branch-reorder positive control: test the iterable convention first "
            "(the non-positional kind) and fall through to the positional "
            "construction. Behaviourally identical to the frozen impl — each "
            "convention is still selected for its own type — so `out = resolvedSeq "
            "…` still holds on the whole domain; the frozen `split_ifs <;> simp_all` "
            "closes both arms. A correct reshape must verify, else SPEC-TOO-STRONG "
            "on the branch order. (Nagini: pos-control-branch-reorder.)"),
    },
    {
        "id": "pos-control-computed-ctor",
        "kind": "soundness",
        "expect": "verify",
        # The faithful port of nagini's pos-control-computed-spread: ONE
        # reconstruction call site whose PRIMITIVE is selected first (a
        # higher-order `let`), rather than two call sites under an `if`. This is
        # NOT the direct-model impl and NOT definitionally the frozen one: the
        # branch now sits on the FUNCTION rather than on its result, so the goal
        # arrives as `(if _ then rebuildPositional else rebuildIterable) _ _ =
        # resolvedSeq _`, with the `if` blocking `split_ifs` on the applied term.
        # Verified: the frozen script does NOT close it; `cases` on the tag does.
        "module": _impl(
            "    let build : Bool -> List Int -> Except RebuildErr SeqVal :=\n"
            "      if s.positionalCtor then rebuildPositional else rebuildIterable\n"
            "    return build s.positionalCtor resolved",
            proof=("prove_correct reconstructSequence by\n"
                   "  loom_solve\n"
                   "  cases hb : s.positionalCtor <;>\n"
                   "    simp [hb, rebuildPositional, rebuildIterable, resolvedSeq]\n")),
        "rationale": (
            "computed-constructor positive control: choose the reconstruction "
            "PRIMITIVE first (`build := if positionalCtor then rebuildPositional "
            "else rebuildIterable`) and reconstruct at a single call site. "
            "Behaviourally identical to the frozen impl on every input — each "
            "convention is still applied to its own type — so `out = resolvedSeq "
            "…` holds on the whole domain. It is a GENUINELY different shape, not "
            "a definitional restatement: lifting the branch from the result to "
            "the function leaves the `if` outside the application, so the frozen "
            "`split_ifs <;> simp_all` does NOT discharge it (checked: it fails "
            "with the applied-`if` goal unsolved) and the proof must case on the "
            "tag instead. A faithful correct impl that the spec could only accept "
            "in the frozen syntactic form would be SPEC-TOO-STRONG. (Nagini: "
            "pos-control-computed-spread — the single-computed-call-site reshape, "
            "which does NOT collapse into pos-control-direct-model here.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO precondition (pre-conditions region is
    # empty), so the nagini "an F2P-shaped input satisfies the precondition"
    # probe is degenerate (every input is in-domain). Re-aimed at the residual
    # total-domain risk — a DEGENERATE post-image — via an in-region `assert`
    # pinning three F2P-shaped non-degeneracy facts. Impl kept verbatim so the
    # method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _FIRST_IMPL_LINE, _ADMISS_ASSERT),
            _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: reconstructing a positional-constructor sequence `[5]` under "
            "`+1` must yield `[6]` and KEEP its positional type (the delta the fix "
            "adds — this construction succeeds where the unguarded one raised), "
            "reconstructing an iterable-constructor sequence of the same must yield "
            "`[6]` and keep THAT type, and a two-member sequence must resolve BOTH "
            "members. The in-region assert must discharge (else the model is "
            "constant / the obligation degenerate); the impl is kept verbatim so "
            "`out = resolvedSeq …` still verifies. (Nagini: admissibility-readonly-"
            "usable, re-aimed from precondition admissibility to post-image "
            "non-degeneracy since this backend has no precondition and no "
            "permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P test. The frozen impl is loop-free,
    # so each witness `decide`s against both the rival and the frozen solution;
    # it ELABORATES against the rival and FAILS against gold (both checked out of
    # band). Each rival fails to verify with a genuine unsolved `out = resolvedSeq
    # …` goal, not a mechanical tactic mismatch.
    # =====================================================================

    # ---- DEFINEDNESS: unconditional iterable convention (the pre-patch bug) ----
    {
        "id": "weak-uncond-iterable",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch shape: hand every type a single iterable, regardless of
        # whether it requires positional members. Correct for iterable types;
        # REJECTS (fails to reconstruct) a positional-constructor type.
        "module": _impl(
            "    return rebuildIterable s.positionalCtor resolved",
            proof=_PROOF_FLAT),
        "refinement": (
            "this is exactly the pre-change behaviour: reconstruct EVERY sequence "
            "type by handing its constructor a single iterable of the resolved "
            "members. For a type that instead requires its members as separate "
            "positional arguments this fails to reconstruct (the constructor is "
            "given one argument where it expects several). The failing test builds "
            "such a positional-constructor sequence with two members and filters "
            "on it; the unpatched reconstruction fails there, so the query blows "
            "up and it does NOT resolve — the bug the fix corrects."),
        "rationale": (
            "REJECT from `out = resolvedSeq s.positionalCtor s.items f` via the "
            "DEFINEDNESS facet: the clause pins the SUCCESS constructor for EVERY "
            "type, but `rebuildIterable` returns the rejection constructor "
            "`Except.error .iterableNotAccepted` when `positionalCtor` is true. "
            "Refuted at (positionalCtor=true, items=[1], f=id) — the "
            "positional-type sub-domain the fix targets — where the spec demands "
            "`Except.ok {true, [1]}` and the rival yields the error. If it verified "
            "=> SPEC-TOO-WEAK (the pre-patch regression would go unnoticed). "
            "(Nagini: uniqueness-atk4-prepatch-single-iterable.)"),
        "witness": _witness(
            "{ positionalCtor := true, items := [(1:Int)] }", "(fun x => x)"),
    },

    # ---- DEFINEDNESS: unconditional positional convention (the dual over-fix) --
    {
        "id": "weak-uncond-positional",
        "kind": "uniqueness",
        "expect": "reject",
        # The DUAL wrong fix: reconstruct EVERY type positionally. Correct for
        # positional types (and empty inputs), but REJECTS a non-positional type
        # with >=1 member (splatting members into a plain-sequence constructor
        # gives it too many positional args).
        "module": _impl(
            "    return rebuildPositional s.positionalCtor resolved",
            proof=_PROOF_FLAT),
        "refinement": (
            "the dual over-fix: reconstruct EVERY sequence type by supplying its "
            "members as separate positional arguments. For an ordinary "
            "iterable-constructor sequence with at least one member this fails — "
            "its constructor takes exactly one iterable, and splatting N members "
            "hands it N positional arguments (mapping.md §1: `list(*[2,3])` raises "
            "TypeError). So a patch that ALWAYS used the positional convention "
            "would break every ordinary list/tuple lookup with members — the "
            "list/tuple leg the fix must keep working — and would NOT resolve "
            "(regressing the existing iterable-reconstruction path)."),
        "rationale": (
            "REJECT from `out = resolvedSeq …` via the DEFINEDNESS facet on the "
            "OTHER type: `rebuildPositional` returns `Except.error "
            ".positionalNotAccepted` when `positionalCtor` is false and the member "
            "list is non-empty, but the clause demands `Except.ok`. Refuted at "
            "(positionalCtor=false, items=[1], f=id) — the non-positional / "
            "non-empty sub-domain, a DISTINCT point from weak-uncond-iterable "
            "(which sits at positionalCtor=true), so the `positionalCtor` binder is "
            "varied across the reject lane. If it verified => SPEC-TOO-WEAK (the "
            "iterable path unpinned). (No direct nagini counterpart — the dual "
            "over-fix that the deep two-sided model — `rebuildPositional` also "
            "PARTIAL — makes attackable on this carrier; it defends the "
            "iterable-construction leg the token abstraction folded away.)"),
        "witness": _witness(
            "{ positionalCtor := false, items := [(1:Int)] }", "(fun x => x)"),
    },

    # ---- TYPE PRESERVATION: drop the type tag (claim the wrong kind) ----
    {
        "id": "weak-drop-type-tag",
        "kind": "uniqueness",
        "expect": "reject",
        # Reconstruct with the right members but report a fixed (wrong) type tag.
        # Members correct, construction succeeds, but the reconstructed sequence
        # claims the non-positional type on a positional input.
        "module": _impl(
            "    return Except.ok { positionalCtor := false, items := resolved }",
            proof=_PROOF_FLAT),
        "refinement": (
            "a patch that reconstructed the members correctly but reported the "
            "wrong sequence type (always the plain iterable kind) would hand the "
            "lookup a plain list/tuple where the caller passed a positional-"
            "constructor sequence — losing the type the change is careful to "
            "PRESERVE. The failing test builds a positional-constructor sequence "
            "and expects the resolved value to keep that type; a plain-kind "
            "reconstruction is a different value and does NOT resolve. (This is the "
            "nagini atk_5 shape: lie about the kind — here the wrong kind is "
            "observable directly on the type tag rather than via a capability "
            "token.)"),
        "rationale": (
            "REJECT from `out = resolvedSeq s.positionalCtor s.items f` via the "
            "TYPE PRESERVATION facet: `resolvedSeq` carries `positionalCtor` "
            "through, but the rival hardcodes `positionalCtor := false`. Refuted at "
            "(positionalCtor=true, items=[7], f=id) where the spec demands "
            "`Except.ok {true, [7]}` and the rival yields `Except.ok {false, [7]}` "
            "— members equal, type tag wrong. If it verified => SPEC-TOO-WEAK (the "
            "type unpinned). (Nagini: uniqueness-atk5-lie-about-kind.)"),
        "witness": _witness(
            "{ positionalCtor := true, items := [(7:Int)] }", "(fun x => x)"),
    },

    # ---- PER-MEMBER RESOLUTION: return members unresolved ----
    {
        "id": "weak-skip-resolver",
        "kind": "uniqueness",
        "expect": "reject",
        # Reconstruct successfully with the right type, but return the ORIGINAL
        # members instead of the resolved ones (never apply f). Correct only when
        # f is the identity on those members.
        "module": _impl(
            "    return Except.ok { positionalCtor := s.positionalCtor, items := s.items }",
            proof=_PROOF_FLAT),
        "refinement": (
            "a patch that reconstructed the sequence but returned the ORIGINAL "
            "members rather than the per-member-resolved ones would skip the "
            "independent resolution the change is built around (each member may be "
            "an expression needing resolution before it can be used in the "
            "lookup). The failing test's members must be resolved before the "
            "filter runs; returning them raw yields the wrong lookup value and "
            "does NOT resolve. Correct only where the resolver is the identity."),
        "rationale": (
            "REJECT from `out = resolvedSeq s.positionalCtor s.items f` via the "
            "PER-MEMBER RESOLUTION facet: the clause maps `f` over the members "
            "(`items.map f`), but the rival returns `s.items` unmapped. Refuted at "
            "(positionalCtor=false, items=[5], f=(·+1)) — off the f=identity "
            "sub-domain, where the spec demands `Except.ok {false, [6]}` and the "
            "rival yields `Except.ok {false, [5]}`. It is one of the witnesses "
            "moving `f` off the identity, so the resolver binder is varied. If it "
            "verified => SPEC-TOO-WEAK (the resolution unenforced). (Nagini: the "
            "value-pin facet of the token contract — here isolated as the "
            "`items.map f` clause.)"),
        "witness": _witness(
            "{ positionalCtor := false, items := [(5:Int)] }", "(fun x => x + 1)"),
    },

    # ---- LENGTH / ORDER: drop the last member ----
    {
        "id": "weak-drop-last-member",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve and reconstruct correctly with the right type and convention,
        # EXCEPT drop the last resolved member (one member short). Correct on
        # empty/one-member inputs; wrong on the last member of any longer input.
        "module": _impl(
            "    let short := resolved.dropLast\n"
            "    let result : Except RebuildErr SeqVal :=\n"
            "      if s.positionalCtor then rebuildPositional s.positionalCtor short\n"
            "      else rebuildIterable s.positionalCtor short\n"
            "    return result",
            proof=_PROOF_FLAT),
        "refinement": (
            "a patch correct for empty and single-member sequences but dropping "
            "the last member of a longer one would rebuild the sequence from one "
            "fewer element — on the failing test's two-member sequence it either "
            "reconstructs the wrong-arity sequence or reads back the wrong bounds, "
            "so the query returns the wrong rows and it does NOT resolve. Correct "
            "on the empty/one-member sub-domain."),
        "rationale": (
            "REJECT from `out = resolvedSeq s.positionalCtor s.items f` via the "
            "LENGTH/ORDER facet: the clause pins `items.map f` (length-preserving, "
            "all members present), but the rival reconstructs from "
            "`(items.map f).dropLast`, one member short for every >=2-member "
            "input. Refuted at (positionalCtor=false, items=[1,2], f=(·+1)) — a "
            "two-member `items`, so the length dependence is demonstrated (the "
            "ORDER half of the same clause is attacked separately by "
            "weak-reverse-order) — where the spec demands `Except.ok {false, [2,3]}` and "
            "the rival yields `Except.ok {false, [2]}`. If it verified => "
            "SPEC-TOO-WEAK (the member count / last member unpinned). (Nagini: "
            "partial-domain-drop-first-field-named — the off-by-one member drop, "
            "here dropping the last member since the model is length-transparent "
            "for either end.)"),
        "witness": _witness(
            "{ positionalCtor := false, items := [(1:Int), 2] }", "(fun x => x + 1)"),
    },

    # ---- ORDER: keep every member, permute them ----
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve every member, keep the type AND the member count — but hand the
        # members back in the opposite order. Length-preserving and
        # resolver-faithful, so it is refuted by the ORDER clause ALONE. Correct
        # exactly on the sub-domain where the member list is a palindrome under
        # the resolver (in particular every 0/1-member input), which is why the
        # witness sits at a two-member input with distinct resolved members.
        "module": _impl(
            "    return Except.ok "
            "{ positionalCtor := s.positionalCtor, items := resolved.reverse }",
            proof=_PROOF_FLAT),
        "refinement": (
            "a patch that resolved every member and preserved the sequence's "
            "type but reconstructed it from the members in the OPPOSITE order "
            "would hand the lookup its bounds transposed. The failing test's "
            "sequence carries two members whose order is meaningful (the lower "
            "and upper end of a range); reconstructing them reversed inverts the "
            "interval, so the query selects the wrong rows (an inverted range "
            "matches nothing) and it does NOT resolve. Correct only where the "
            "resolved member list is unchanged by reversal (0/1-member inputs, "
            "or a palindrome)."),
        "rationale": (
            "REJECT from `out = resolvedSeq s.positionalCtor s.items f` via the "
            "ORDER facet, which no other rival probes: the clause pins "
            "`items.map f`, which is order-preserving, while the rival yields "
            "`(items.map f).reverse`. This is the facet weak-drop-last-member "
            "does NOT reach — that rival is refuted on member COUNT, so a spec "
            "that pinned only the multiset (or the length) of the members would "
            "still reject it while admitting this one. Refuted at "
            "(positionalCtor=true, items=[1,2], f=(·+1)) where the spec demands "
            "`Except.ok {true, [2,3]}` and the rival yields "
            "`Except.ok {true, [3,2]}` — same type tag, same length, same "
            "multiset, order transposed. This is also the only reject case "
            "pairing positionalCtor=true with a two-member `items`. If it "
            "verified => SPEC-TOO-WEAK (the member order unpinned). (No nagini "
            "counterpart: nagini's `ToSeq` pin makes order and length one "
            "clause, so its member-drop rival covered both; on this carrier the "
            "two are separately attackable and separately necessary.)"),
        "witness": _witness(
            "{ positionalCtor := true, items := [(1:Int), 2] }", "(fun x => x + 1)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 10 SPEC cases (3 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation, 5 uniqueness rivals)
# plus 2 AXIOM_TESTS, over ONE modeled function
# `resolve_sequence(value: List[int], field_named: bool) -> List[int]` on a PSeq
# value abstraction with `value` held at a fractional heap permission
# `Acc(list_pred(value), 1/2)`, and a load-bearing `well_formed_container`
# CAPABILITY TOKEN (an abstract @ContractOnly predicate) that lifts the
# raise-vs-succeed control-flow effect into the value logic.
#
# This velvet bundle models the SAME single function as `reconstructSequence`,
# but its carrier is RICHER where the nagini token was abstract: the two
# construction outcomes are the two `Except RebuildErr SeqVal` constructors and
# BOTH reconstruction primitives are modeled deeply and PARTIALLY
# (`rebuildIterable` errors on a positional type; `rebuildPositional` errors on a
# non-positional non-empty type — mapping.md §1). So the control-flow effect the
# token abstracted becomes a directly-attackable DEFINEDNESS facet, and the
# token's (contents, kind) keying becomes the transparent (items, positionalCtor)
# fields of the returned `SeqVal`.
#
#   nagini case                              -> here                          disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-computed-spread              -> pos-control-computed-ctor     PORTED
#   pos-control-atk6-equal-list              -> pos-control-direct-model      COLLAPSED
#   pos-control-branch-reorder               -> pos-control-branch-reorder    PORTED
#   admissibility-readonly-usable            -> admiss-nondegenerate          RE-AIMED
#   frame-mutation-write-value               -> (none)                        VACUOUS
#   uniqueness-atk1-never-construct          -> (none)                        VACUOUS-on-carrier
#   control-flow-effect-atk3-namedtuple-bug  -> weak-uncond-iterable          PORTED (merged)
#   uniqueness-atk4-prepatch-single-iterable -> weak-uncond-iterable          PORTED
#   uniqueness-atk5-lie-about-kind           -> weak-drop-type-tag            PORTED (re-expr)
#   partial-domain-drop-first-field-named    -> weak-drop-last-member         PORTED
#   AXIOM_TESTS[ax-resolve-one, ax-build-container] -> (none)                 DROPPED (G-AX)
#                    (+ weak-uncond-positional / weak-skip-resolver / weak-reverse-order ADDED)
#
# 3 nagini positives -> 3 here (computed-spread ports as pos-control-computed-ctor;
# atk6-equal-list COLLAPSES into the direct grounded model); 1 admissibility
# re-aimed; 5 uniqueness -> 3 ported + 1 vacuous-on-carrier; 3 added; 2 axiom
# cases dropped.
#
# PORTED (pos-control-computed-spread -> pos-control-computed-ctor): the
#   single-computed-call-site reshape. It was previously recorded as COLLAPSED
#   into pos-control-direct-model; that was WRONG and is corrected here. Nagini's
#   reshape computes the CONVENTION and keeps one call site, and this carrier
#   expresses exactly that — bind the reconstruction PRIMITIVE
#   (`if positionalCtor then rebuildPositional else rebuildIterable`) and apply
#   it once. That is neither the direct grounded model nor a definitional
#   restatement of the frozen impl: the branch moves from the result to the
#   function, so the `if` sits outside the application and the frozen
#   `split_ifs <;> simp_all` no longer discharges the goal (measured: it fails
#   with the applied-`if` goal unsolved); casing on the tag closes it. So the
#   reshape is a real, independent SPEC-TOO-STRONG probe on the impl's shape and
#   the collapse discarded coverage rather than narrowing it.
# COLLAPSED (pos-control-atk6-equal-list -> pos-control-direct-model): nagini's
#   atk6 does the effectful build and returns the value-equal materialized list.
#   It is a distinct impl there only because its token is a capability minted by
#   an effectful call, keyed separately from its value pins. On this carrier
#   there is no effect to perform and no token to mint — the post-image is a pure
#   `def` — so "do the real work and return the value-equal result" IS
#   `return resolvedSeq s.positionalCtor s.items f` (pos-control-direct-model).
#   Checked, not assumed: a transliteration that performs the branch, binds its
#   result, and returns the value-equal record verifies, and it reduces to the
#   same value as the direct model, so shipping it too would be a duplicate
#   positive. Carrier narrowing, not an omission.
# RE-AIMED (admissibility-readonly-usable -> admiss-nondegenerate): the nagini
#   admissibility control confirms the read-only half-permission ADMITS the
#   length read a normal input needs. There is no heap permission and no `require`
#   clause here (the admitted domain is total), so that reading is vacuous.
#   Re-aimed at the residual total-domain risk — a degenerate post-image — via a
#   live in-region assert pinning three F2P-shaped non-degeneracy facts (a
#   positional reconstruction succeeds and keeps its type; an iterable one keeps
#   ITS type; both members of a two-member input are resolved). A wrong RHS leaves
#   `⊢ False` (verified out of band), so the assert is live, not decorative.
# PORTED (3 uniqueness):
#   * control-flow-effect-atk3-namedtuple-bug + uniqueness-atk4-prepatch-single-
#     iterable BOTH MERGE into weak-uncond-iterable. atk3 (build for the plain
#     kind, skip construction for the field-named kind) and atk4 (unconditional
#     single-iterable construction) are two spellings of the SAME defect on this
#     carrier: reconstruct by the iterable convention where the type requires the
#     positional one. On the nagini token surface they differ (one returns bare
#     contents, one calls the builder with the wrong convention); here both are
#     `return rebuildIterable s.positionalCtor resolved`, refuted identically by
#     the DEFINEDNESS facet at positionalCtor=true. The porting map forbids two
#     rivals sharing a witness unless they truly fail identically — here they do,
#     so they are one rival.
#   * uniqueness-atk5-lie-about-kind -> weak-drop-type-tag: nagini's atk5 lies
#     about `field_named` to dodge the precondition, so the minted token is for
#     the wrong kind. Here the wrong kind is observable DIRECTLY on the returned
#     `positionalCtor` tag (no precondition to dodge — the method has none), so the
#     rival hardcodes `positionalCtor := false`, refuted by the TYPE PRESERVATION
#     facet on a positional input.
#   * partial-domain-drop-first-field-named -> weak-drop-last-member: the
#     off-by-one member drop. Nagini drops the FIRST member (loop stops one step
#     early); the velvet model is length-transparent for either end, so the
#     cheapest expression drops the LAST member (`resolved.dropLast`). Same
#     divergence (one member short), refuted by the LENGTH facet at a two-member
#     input.
# VACUOUS-ON-CARRIER (uniqueness-atk1-never-construct): nagini's atk1 returns the
#   materialized `resolved` list WITHOUT ever calling the builder, so no token is
#   minted and the abstract token clause is unprovable. On this carrier there is
#   NO capability token — "reconstruct successfully with the right members and
#   type" IS the whole obligation, and returning the resolved members wrapped in
#   the success constructor with the right type tag is exactly the CORRECT answer
#   (`resolvedSeq` = `Except.ok {positionalCtor, items.map f}`). There is no
#   token-minting effect to skip, so the nagini "never construct" defect has no
#   wrong-value image here: the abstraction that made it wrong (an unmintable
#   token) collapsed. Dropped and reported, NOT fabricated — a rival with no
#   discriminating witness is not wrong on this backend's carrier. DEMONSTRATED,
#   not asserted: the transliteration
#   `return Except.ok { positionalCtor := s.positionalCtor, items := resolved }`
#   VERIFIES against the frozen spec (it is `resolvedSeq` unfolded), so it is a
#   correct impl, not a rival — no witness could refute it, and shipping it as
#   expect="reject" would be a fabricated case. Its honest home is the positive
#   lane, where pos-control-direct-model already covers the same value.
# VACUOUS (frame-mutation-write-value): MANDATORY on nagini because `value` is
#   `Acc(list_pred(value), 1/2)` read-only and a write must be rejected for
#   insufficient permission. Lean/Velvet are referentially transparent: `s` and
#   `f` are immutable values, no `mut` binder anywhere in this bundle, no heap, no
#   aliasing, no fractional permission. There is no read-only input to overwrite
#   and no permission system to violate, so the class is vacuous and no substitute
#   is fabricated. The nagini read-only obligation is here structurally guaranteed
#   by the absence of `mut`, which the frozen spec already encodes.
# ADDED (3, no nagini counterpart, made attackable by the DEEP two-sided
#   model this carrier uses where nagini had an abstract token):
#   * weak-uncond-positional — the DUAL over-fix (reconstruct EVERY type
#     positionally). Nagini's token folds away the iterable-construction leg (its
#     `build_container` well-forms iff field_named==spread, and the impl only ever
#     reaches the matching pair), so nagini has no rival attacking the
#     iterable-path partiality. Here `rebuildPositional` is modeled PARTIAL
#     (errors on a non-positional non-empty type), so a patch that always splatted
#     is a real DEFINEDNESS divergence, refuted at positionalCtor=false. Without
#     it the iterable-construction leg (the list/tuple path the fix must keep
#     working) would be attacked by no rival, and its `positionalCtor=false`
#     sub-domain of the DEFINEDNESS clause would go untested.
#   * weak-skip-resolver — return the members UNRESOLVED. Nagini's `resolve_one`
#     per-member resolution is A-consumed (an axiom lane case), not attacked at
#     the SPEC level, because its value pin is folded into the token's contents
#     keying. Here the resolution is an explicit `items.map f` clause of the
#     post-image, so a rival that returns `s.items` raw is a real PER-MEMBER
#     RESOLUTION divergence, refuted where `f` is non-identity. This is the only
#     rival that moves the `f` binder off the identity, so without it `f` would be
#     pinned at identity across the whole reject lane and the spec's dependence on
#     the resolver would be untested.
#   * weak-reverse-order — keep the type, the resolver AND the member count, but
#     permute the members. Nagini folds order and length into ONE `ToSeq` pin, so
#     its single member-drop rival covers both at once and it has no permutation
#     case. Here the two are separable, and the drop-a-member rival is refuted on
#     COUNT alone: a spec pinning only the length (or only the multiset) of the
#     resolved members would still reject weak-drop-last-member while admitting a
#     transposition. Without this rival the ORDER half of the `items.map f` clause
#     — which the docstring claims — is asserted by no case. Added after an audit
#     found the claim undemonstrated.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
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
# BINDER / CLAUSE / POINT COVERAGE. The sole load-bearing `ensures` is defended
#   (the three positives + admissibility) and attacked by six rivals. Its four
#   independent facets are each attacked: DEFINEDNESS (weak-uncond-iterable at
#   positionalCtor=true, weak-uncond-positional at positionalCtor=false — both
#   Except constructors, both types), TYPE PRESERVATION (weak-drop-type-tag),
#   PER-MEMBER RESOLUTION (weak-skip-resolver), and LENGTH (weak-drop-last-member)
#   / ORDER (weak-reverse-order) separately — the last two split because a rival
#   refuted on member COUNT leaves a permutation admissible, so one case cannot
#   attest to both. Binders (pts = 6 distinct input points):
#     positionalCtor — true (iterable, drop-type-tag, reverse-order) and false
#                      (positional, skip-resolver, drop-last-member).
#     items          — one member ([1], [7], [5]) and two members ([1,2], twice at
#                      distinct positionalCtor), so the length AND order
#                      dependences are each demonstrated at a multi-member point.
#     f              — identity (iterable, positional, drop-type-tag) and a
#                      non-identity `+1` (skip-resolver, drop-last-member,
#                      reverse-order).
#   No input binder of the obligation is pinned at a single value across the
#   reject lane, and each variation MOVES the spec's verdict (each witness is a
#   machine-checked refutation at its own point, failing on gold for a semantic
#   reason — `decide` proves the gold tester true there — not a missing name or
#   an unfolding failure), so the coverage tool sees the spec's dependence on
#   each.
#
# AXIOM_TESTS: dropped. The nagini sibling ships two (ax-resolve-one-soundness,
#   ax-build-container-soundness-containment). The axiom lane is G-AX's job and
#   this gate ignores AXIOM_TESTS regardless; this velvet bundle declares no
#   `axiom` (the reconstruction is modeled deeply as `resolvedSeq` /
#   `rebuildPositional` / `rebuildIterable`, an A-reference validated by G-CONF,
#   meta.json gates.G-AX = skip — cf. mapping.md §3). Nothing to probe here.
AXIOM_TESTS = []
