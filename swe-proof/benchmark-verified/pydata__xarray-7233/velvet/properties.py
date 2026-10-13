"""properties.py — G-PBT falsification battery for pydata__xarray-7233 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct coordsToKeep`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  coordsToKeep (requestedDims : List String) (coordNames : List String)
      return (out : List String)
    ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)

The method re-selects which names remain coordinates after a reshaping that
rebuilds every variable under a new dimension layout. ``requestedDims`` are the
names of the dimensions being reshaped and ``coordNames`` the prior coordinate
names; the result is a fresh name-set. The single load-bearing ``ensures`` is a
BICONDITIONAL pinning membership of the result to membership in the prior
coordinate names — with NO opaque answer-key to echo (the ``axioms`` region is
empty; the pure model ``keptCoordNames`` is a fully-unfolded ``def`` over the
method's own arguments). The biconditional has two independently-attackable
directions:

  * BACKWARD (``k ∈ coordNames → k ∈ out``) — every name that was a coordinate
    before stays a coordinate. This is the direction the fix restores: the
    pre-change behaviour dropped prior coordinates that were not among the
    reshaped dimensions.
  * FORWARD (``k ∈ out → k ∈ coordNames``) — no name that was NOT a prior
    coordinate becomes one.

SPEC BINDER. The postcondition binds ``out`` and ``coordNames`` only —
``requestedDims`` does NOT appear in it, and correctly so: the guarantee is that
the result equals the prior coordinate-name set regardless of which dimensions
are reshaped (the common-names component the impl computes from
``requestedDims`` is always a subset of ``coordNames``, so it changes no
membership). The reject witnesses therefore load-bear ``coordNames``: they drive
it over ``{[], ["day"], ["day","y"]}`` (empty / singleton / two-element,
dropping the FIRST element) so the manifest demonstrates the result's dependence
on the actual prior coordinate set at three DISTINCT input points (pts=3), not a
single pinned shape.

CARRIER NOTE — THE DECIDABLE BOUNDARY. The postcondition is ``∀ k : String,
…`` — a universal over an INFINITE type, which is NOT auto-decidable, so
Velvet's ``prove_postcondition_decidable_for`` / ``…Tester`` machinery does not
apply here (measured: it leaves ``⊢ Decidable (∀ (k : String), …)`` unsolved).
Each reject witness therefore states the spec violation DIRECTLY against the
extracted executable ``coordsToKeepExec`` (``extract_program_for coordsToKeep``):
it assumes the universal at a concrete input, instantiates it at one witness
name, and derives ``False`` by ``simp``-reducing the extracted program's
``.run`` at that literal. Because both the rival and the gold impl are loop-free
straight-line programs, ``coordsToKeepExec`` reduces by kernel/``simp``
computation for both; the discrimination is by VALUE — the rival's result omits
(or adds) the witness name, gold's does not — so the witness elaborates green
against the rival and fails on gold. Checked in a file whose ``prove_correct``
block has been stripped, so no tactic script can mask the verdict (both halves
were confirmed with ``scripts/lean_verify.sh``: every witness elaborates against
its rival and errors against the frozen solution).

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three correct impls of different
    shape must verify, else the spec is SPEC-TOO-STRONG on the shape of the impl:
    return ``coordNames`` directly, return the grounded pure model
    ``keptCoordNames …``, and return ``coordNames.dedup`` — the last one being the
    sharpest, since its returned LIST differs from gold's in length and content
    (duplicates collapsed) and only its MEMBERSHIP agrees, which is the spec's
    sole observable. The first two keep the frozen ``loom_solve`` verbatim; the
    dedup one adds a single membership rewrite inside the tactic body.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries TWO mandatory
    frame-mutation rivals (write to each read-only input) because a read-only
    input is held at a fractional heap permission an impl can illegally
    overwrite. Lean/Velvet are referentially transparent: ``requestedDims`` and
    ``coordNames`` are immutable ``List String`` values declared read-only (not
    ``mut``); there is no heap, no aliasing, and no permission system. There is
    no read-only input to overwrite and no frame clause to violate, so the class
    has no carrier analogue; NOT ported (fabricating a substitute would test
    nothing). See the footer for the case-by-case accounting.
  * NON-TERMINATION: INAPPLICABLE as a shipped reject case, and closed by the
    verifier rather than vacuous. The sibling's mandatory divergence probe closes
    the partial-correctness vacuous-divergence hole via a ``MustTerminate``
    obligation. On this bundle the frozen core IS a loop-free straight-line
    transformation, so there is no loop in the frozen body to make diverge without
    fabricating one, and no value sub-domain a divergence rival would expose: that
    is why nothing is ported here. But "closed STRUCTURALLY" overstates it, because
    a rival rewrites the whole impl region and may splice a loop that the frozen
    body does not have. What refuses that rival is the descent obligation: this
    bundle sets ``loom.semantics.termination "total"``, under which a postcondition
    is claimed of ALL runs, not only terminating ones, so every loop owes a
    decreasing measure AND its descent. The option cannot drift from the file's
    ``open TotalCorrectness DemonicChoice``, because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` with body
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. NOT ported (see footer).
  * ADMISSIBILITY — PORTED (``admiss-f2p-shaped``). The sibling asserts an
    F2P-shaped input satisfies its half-permission precondition. This backend's
    method has NO ``require`` clause, but the absence of a precondition is NOT a
    reason to drop the lane: the analogue on a total carrier is the OBLIGATION
    being unsatisfiable — or degenerately satisfiable — at exactly an F2P-shaped
    input. The ported case discharges the ``ensures`` biconditional at a concrete
    F2P-shaped point (a prior coordinate ``"day"`` that is NOT among the reshaped
    dimensions, alongside one that IS) as an in-region ``assert`` BEFORE the
    frozen obligation closes verbatim, and pairs it with a non-degeneracy pair
    showing the post-image genuinely DISCRIMINATES at that point (``"day"`` is in
    the chosen set for ``coordNames=["day","time"]`` and out of it for
    ``coordNames=["time"]``). That the assert load-bears was measured: replacing
    either the biconditional or the discrimination conjunct with a false
    statement of the same shape makes the file FAIL (exit 1), so this is not a
    tautology spliced in to fill a lane.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a biconditional over the
    method's own ``coordNames`` argument; there is no answer-key term a wrong
    impl could echo. The cheapest correct impl computes membership honestly,
    which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (a prior coordinate dropped, a
    non-coordinate promoted, or the first prior coordinate dropped).
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7233"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every variant replaces this block; the frozen
# ---- `prove_correct coordsToKeep by loom_solve` obligation is left untouched.
_IMPL = """    -- impl-start
    let common := requestedDims.filter (fun k => coordNames.contains k)
    let result := common ++ coordNames
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"


def _rewrite_impl(new_block):
    """Full variant: whole impl block replaced, spec + proof left intact."""
    return _swap(_BASE, _IMPL, new_block)


# ---- witness preamble. The postcondition `∀ k : String, …` is a universal over
# ---- an infinite type and is NOT auto-decidable, so Velvet's tester machinery
# ---- does not apply. A witness instead reaches the post-image DIRECTLY through
# ---- the extracted executable `coordsToKeepExec` (a loop-free straight-line
# ---- program that reduces by `simp` for both rival and gold), assuming the
# ---- universal at a concrete input and deriving `False` at one witness name.
# ---- Checked in a file whose `prove_correct` block has been stripped.
def _wit(rd, cn, name):
    """A refutation witness at literal inputs (rd, cn), instantiated at `name`.

    Assumes the postcondition universal `∀ k, k ∈ out ↔ k ∈ coordNames` for the
    extracted program at (rd, cn), instantiates it at the single witness `name`
    where the rival and gold disagree, and derives `False` by `simp`-reducing the
    extracted program's straight-line `.run` at that literal. Because BOTH sides
    of the biconditional at `name` are decidable-by-computation once the program
    is unfolded — the LHS `name ∈ (coordsToKeepExec rd cn).run` reduces to the
    rival's returned list, the RHS `name ∈ cn` to a literal-list membership —
    handing the WHOLE `hall name` to `simp` closes the goal by refuting whichever
    direction the rival breaks (BACKWARD `k ∈ coordNames → k ∈ out` when the
    rival drops a prior coordinate; FORWARD `k ∈ out → k ∈ coordNames` when it
    promotes a non-coordinate). Feeding a membership premise to `.mp`/`.mpr` via
    `by decide` is deliberately AVOIDED: `decide` cannot reduce membership in the
    extracted monadic program, so that shape left the witness fragile.

    The `example` head binds NOTHING (the `∀ k` lives inside the negated goal,
    not as a head binder), so there is no hypothesis-consistency probe to satisfy
    — the refutation is at a concrete literal input, not conditioned on a carrier.
    """
    return (
        "extract_program_for coordsToKeep\n\n"
        f"example : ¬ (∀ k, (k ∈ (coordsToKeepExec {rd} {cn}).run) ↔ "
        f"(k ∈ ({cn} : List String))) := by\n"
        "  intro hall\n"
        f"  have h := hall {name}\n"
        "  simp [coordsToKeepExec, coordsToKeep, NonDetT.run, DivM.run] at h\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-coordnames",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the common-names computation
        # entirely and return `coordNames` directly. Since the spec pins
        # membership to `coordNames`, `out = coordNames` satisfies the
        # biconditional reflexively; the frozen `loom_solve` still discharges.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return coordNames\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns `coordNames` directly (no "
            "common-names step at all — maximally different from the gold "
            "`filter … ++ coordNames`). The biconditional `k ∈ out ↔ k ∈ "
            "coordNames` holds reflexively on the whole domain; the reproof is "
            "the frozen `loom_solve`. If this failed the spec would be over-fit "
            "to the impl shape (SPEC-TOO-STRONG). (Sibling: pos-control-direct-"
            "branch — a structurally-different correct impl.)"),
    },
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        # Return the grounded pure model `keptCoordNames requestedDims
        # coordNames` (the `filter … ++ coordNames` union) named as a helper
        # rather than inlined. Observationally identical to gold; the frozen
        # proof still discharges via the `@[grind] mem_keptCoordNames` lemma.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return keptCoordNames requestedDims coordNames\n"
            "    -- impl-end"),
        "rationale": (
            "returns the grounded pure model `keptCoordNames requestedDims "
            "coordNames` (the union the gold body inlines) as a named helper. "
            "`out` IS that model, so the ensures holds on the whole domain and "
            "the frozen `loom_solve` (with the `mem_keptCoordNames` grind lemma) "
            "still discharges. A correct reshape must verify, else the spec is "
            "SPEC-TOO-STRONG over the impl shape. Also the honest "
            "no-ungrounded-echo control: the model is the real membership work, "
            "so returning it is correct, not a cheat."),
    },

    {
        "id": "pos-dedup",
        "kind": "soundness",
        "expect": "verify",
        # A correct reshape whose RESULT SHAPE differs from gold's, not just its
        # spelling: `coordNames.dedup` collapses duplicate names, so the returned
        # list is not a permutation or re-association of gold's — only its
        # MEMBERSHIP agrees. Since membership is the sole observable the spec
        # names, it must verify. Needs one extra rewrite past `loom_solve`
        # (`List.mem_dedup`), which stays inside the tactic body.
        "module": _swap(
            _rewrite_impl(
                "    -- impl-start\n"
                "    return coordNames.dedup\n"
                "    -- impl-end"),
            "prove_correct coordsToKeep by\n  loom_solve",
            "prove_correct coordsToKeep by\n"
            "  loom_solve <;> intro k <;> simp [List.mem_dedup]"),
        "rationale": (
            "the sharpest SPEC-TOO-STRONG probe available here: `coordNames.dedup` "
            "is a faithful correct impl whose returned LIST differs from gold's in "
            "length and content (duplicates collapsed), not merely in order or "
            "association — so it cannot be dismissed as a re-spelling of gold. The "
            "spec's only observable is membership (`k ∈ out ↔ k ∈ coordNames`), and "
            "`List.mem_dedup` gives exactly that, so it verifies. This is the "
            "control that the spec pins the MEMBERSHIP set and not a particular "
            "list representation — the carrier claim mapping.md §2 makes (a name-set "
            "corresponds to ANY `List String` whose elements are that set). If this "
            "failed, the spec would be over-fit to gold's list shape."),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE, and non-degenerately
    # so, at an F2P-shaped input. The method carries no `require` clause, so the
    # carrier analogue of PRECOND-TOO-STRONG is the ENSURES being unsatisfiable
    # (or degenerately satisfiable) at exactly the input the failing scenario
    # has. Discharged by evaluation as an in-region `assert`, ahead of the
    # frozen obligation, which still closes verbatim.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # Gold impl kept VERBATIM; only an in-region `assert` is spliced ahead of
        # it, so `markers.same_spec` holds and the frozen `loom_solve` still
        # discharges the method's own `ensures`.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss\n"
            "      ((∀ k, k ∈ keptCoordNames [\"time\"] [\"day\", \"time\"] ↔ "
            "k ∈ [\"day\", \"time\"]) ∧\n"
            "       (\"day\" ∈ keptCoordNames [\"time\"] [\"day\", \"time\"]) ∧\n"
            "       (\"day\" ∉ keptCoordNames [\"time\"] [\"time\"])))\n"
            "    let common := requestedDims.filter (fun k => coordNames.contains k)\n"
            "    let result := common ++ coordNames\n"
            "    return result\n"
            "    -- impl-end"),
        "rationale": (
            "the obligation is SATISFIABLE at an F2P-shaped input and the "
            "post-image is NON-DEGENERATE there. The input point is the "
            "scenario's shape: prior coordinates [\"day\", \"time\"] of which "
            "\"day\" is NOT among the reshaped dimensions [\"time\"] and \"time\" "
            "IS — the mixed case the coordinate-preservation guarantee is about. "
            "First conjunct: the `ensures` biconditional itself holds at that "
            "point (so the obligation is not unsatisfiable — the analogue of "
            "PRECOND-TOO-STRONG on a carrier with no `require`). Second and "
            "third: the chosen set CONTAINS \"day\" at coordNames=[\"day\","
            "\"time\"] and OMITS it at coordNames=[\"time\"], so the post-image "
            "genuinely varies with the prior coordinate set rather than being a "
            "constant every impl meets. Both conjunct groups load-bear: "
            "falsifying either (claim \"day\" present for coordNames=[\"time\"], "
            "or state the biconditional against the wrong RHS) makes the file "
            "FAIL, so this is not a tautology. The impl is kept verbatim so the "
            "frozen `loom_solve` still discharges the `ensures`. (Sibling: "
            "admissibility-f2p-shaped — ported, not dropped: the absence of a "
            "`require` clause moves the probe onto the obligation, it does not "
            "make the lane vacuous.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a loop-free
    # closed form; its extracted program reduces by `simp`, so the witness
    # discriminates by value (see the CARRIER NOTE); the frozen spec is
    # untouched.
    # =====================================================================
    {
        "id": "r1-intersection-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The verbatim pre-change selection: keep only the names COMMON to the
        # reshaped dimensions and the prior coordinates (`filter`), dropping the
        # union with the whole prior coordinate set. Wrong precisely for a prior
        # coordinate whose name is NOT among the reshaped dimensions.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let common := requestedDims.filter (fun k => coordNames.contains k)\n"
            "    return common\n"
            "    -- impl-end"),
        "refinement": (
            "this is the verbatim pre-change selection (intersection only). On "
            "the failing scenario the prior coordinate 'day' is NOT among the "
            "reshaped dimensions, so it is dropped from the result's coordinate "
            "names — the demoted-coordinate bug the issue reports. A faithful "
            "patch equal to this shape IS the buggy original: the observable "
            "(the result's coordinate-name set losing 'day') is exactly what the "
            "failing test forbids, so it does NOT resolve. Correct on every name "
            "that IS a reshaped dimension (a true partial-domain break)."),
        "rationale": (
            "REJECT from the BACKWARD leg `k ∈ coordNames → k ∈ out`: at a prior "
            "coordinate that is not a reshaped dimension the spec requires it to "
            "remain, but this drops it. Verifying would be SPEC-TOO-WEAK (the "
            "coordinate-preservation direction unpinned). Refuted at "
            "requestedDims=[\"time\"], coordNames=[\"day\"]: gold keeps 'day', the "
            "rival returns []. (Sibling: partial-domain-intersection-only.)"),
        "witness": _wit('["time"]', '["day"]', '"day"'),
    },
    {
        "id": "r2-window-keyed",
        "kind": "uniqueness",
        "expect": "reject",
        # Key coordinate status off the reshaped-dimension names alone: return
        # `requestedDims`. Promotes a reshaped dimension that was NOT a prior
        # coordinate, and (on other inputs) drops non-reshaped prior coordinates.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return requestedDims\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful counterpart that keyed coordinate status off the "
            "reshaped-dimension names rather than the prior coordinate set would "
            "promote a reshaped dimension that was never a coordinate (and drop "
            "non-reshaped prior coordinates). The result's coordinate-name set "
            "would gain a name that was not a coordinate on the input, so the "
            "scenario asserting the coordinate-name set is preserved would see a "
            "spurious name — it would NOT resolve. Correct only where the two "
            "sets happen to coincide."),
        "rationale": (
            "REJECT from the FORWARD leg `k ∈ out → k ∈ coordNames`: at a "
            "reshaped-dimension name that is not a prior coordinate the spec "
            "forbids it in the result, but this returns it. Verifying would be "
            "SPEC-TOO-WEAK (the no-spurious-name direction unpinned). This "
            "attacks the OPPOSITE biconditional leg from r1/r3, and exercises a "
            "coordNames value ([]) no other witness uses. Refuted at "
            "requestedDims=[\"time\"], coordNames=[]: the rival returns "
            "[\"time\"] but 'time' ∉ coordNames. (Sibling: "
            "partial-domain-window-keyed.)"),
        "witness": _wit('["time"]', '[]', '"time"'),
    },
    {
        "id": "r3-drop-first-coord",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss of r1: keep the common-names union but DROP THE FIRST prior
        # coordinate (`coordNames.drop 1`). Correct on every prior coordinate
        # except the first — a distinct sub-domain (the first coordinate name),
        # so it needs its own discriminating witness.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let common := requestedDims.filter (fun k => coordNames.contains k)\n"
            "    let result := common ++ coordNames.drop 1\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "a patch that special-cased the FIRST prior coordinate name (e.g. "
            "always demoted the first rebuilt variable) would drop that "
            "coordinate whenever it led the coordinate list. The failing "
            "scenario builds a container whose first coordinate is 'day'; "
            "demoting it makes the result's coordinate-name set lose 'day', so "
            "the preservation assertion fails — it would NOT resolve. Correct on "
            "every non-first prior coordinate, so it agrees with gold over more "
            "of the domain than r1 and is refuted at the distinguishing input "
            "(the first coordinate)."),
        "rationale": (
            "REJECT from the BACKWARD leg at the FIRST prior coordinate: when "
            "'day' leads `coordNames` the spec requires it to remain, but "
            "`coordNames.drop 1` removes it. Verifying would be SPEC-TOO-WEAK "
            "(the first-coordinate sub-domain unpinned). Refuted at "
            "requestedDims=[], coordNames=[\"day\",\"y\"] (a two-element list — a "
            "coordNames length no other witness uses): gold keeps 'day', the "
            "rival returns [\"y\"]. (Sibling: partial-domain-first-element.)"),
        "witness": _wit('[]', '["day", "y"]', '"day"'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 5 uniqueness rivals — two of which are
# mandatory frame-mutation rivals and one a mandatory non-termination rival)
# plus an EMPTY AXIOM lane (AXIOM_TESTS = []). The sibling contracts
# `rebuild_label_status` over two full-permission read-only `List[int]` inputs
# under partial correctness. This backend models the SAME coordinate re-selection
# DEEPLY and CONCRETELY (`keptCoordNames` over `List String` with membership
# semantics), pins it with a single biconditional `ensures`, runs under TOTAL
# termination semantics, and has NO precondition and NO permission surface. Those
# carrier facts make three sibling classes vacuous/degenerate here.
#
#   sibling case                         kind          -> here                    disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-direct-branch            soundness     -> pos-return-coordnames    RE-SHAPED
#                                                          (+ pos-return-model ADDED)
#   admissibility-f2p-shaped             admissibility -> admiss-f2p-shaped        PORTED
#   partial-domain-intersection-only     uniqueness    -> r1-intersection-only     PORTED
#   partial-domain-first-element         uniqueness    -> r3-drop-first-coord       PORTED
#   partial-domain-window-keyed          uniqueness    -> r2-window-keyed           PORTED
#   frame-mut-was_label                  uniqueness    -> (none)                   VACUOUS
#   frame-mut-is_window                  uniqueness    -> (none)                   VACUOUS
#   nonterm-endless-loop                 uniqueness    -> (none)                   VACUOUS
#   AXIOM_TESTS (none)                   axiom         -> (none)                   N/A (G-AX)
#
# 3 uniqueness ported, 1 soundness re-shaped + 1 added, 1 admissibility ported;
# 2 frame-mutation vacuous, 1 non-termination vacuous; axiom lane empty (nothing
# to port).
#
# RE-SHAPED (pos-control-direct-branch -> pos-return-coordnames): the sibling's
#   positive is a control-flow reshape (single if/else on the prior-status bit).
#   On this carrier the maximally-different correct impl drops the common-names
#   step entirely and returns `coordNames`; a second correct reshape
#   (pos-return-model) is ADDED that returns the grounded pure model
#   `keptCoordNames …`, so the soundness surface is defended both from the
#   simplest possible impl AND from the deep-model form.
# PORTED (the three value/branch rivals): partial-domain-intersection-only ->
#   r1-intersection-only (the verbatim pre-change intersection; refuted on a
#   prior coordinate that is not a reshaped dimension — the F2P discriminator).
#   partial-domain-window-keyed -> r2-window-keyed (key off the reshaped-dimension
#   names; refuted on the FORWARD biconditional leg at a coordNames value ([])
#   no other witness uses). partial-domain-first-element -> r3-drop-first-coord
#   (drop the first prior coordinate; a near-miss of r1 refuted at the
#   distinguishing first-coordinate input, on a two-element coordNames).
# PORTED (admissibility-f2p-shaped -> admiss-f2p-shaped): the sibling asserts an
#   F2P-shaped input satisfies its half-permission Requires. This backend's method
#   has NO `require` clause — but that RELOCATES the probe, it does not make the
#   lane vacuous. On a total carrier the analogue of PRECOND-TOO-STRONG is the
#   OBLIGATION being unsatisfiable, or degenerately satisfiable, at exactly an
#   F2P-shaped input. So the ported case discharges the `ensures` biconditional at
#   the scenario's own shape (prior coordinates ["day","time"], reshaped dimensions
#   ["time"] — so "day" is a prior coordinate that is NOT a reshaped dimension and
#   "time" is one that IS) as an in-region `assert`, by evaluation, BEFORE the
#   frozen obligation closes verbatim; and it pairs that with a discrimination
#   pair ("day" IS in the chosen set at coordNames=["day","time"], and is NOT at
#   coordNames=["time"]) so the post-image is shown to vary with the prior
#   coordinate set rather than being a constant every impl meets. Load-bearing was
#   measured, not assumed: falsifying either the biconditional conjunct or the
#   discrimination conjunct makes the file FAIL, so the assert is not a tautology.
# VACUOUS (frame-mut-was_label, frame-mut-is_window): the sibling's two mandatory
#   frame-mutation rivals overwrite a read-only input held at a fractional heap
#   permission (`Acc(.,1/2)`), rejected by the insufficient-permission check.
#   This backend is referentially transparent: `requestedDims` and `coordNames`
#   are immutable values declared read-only (not `mut`), there is no heap, no
#   aliasing, and no permission system. There is no read-only input to overwrite
#   and no frame clause to violate, so the class has no carrier analogue. Omitted
#   as a genuine carrier fact, NOT fabricated (porting map: this class is vacuous
#   on a referentially-transparent backend).
# VACUOUS (nonterm-endless-loop): the sibling's mandatory divergence rival closes
#   the partial-correctness vacuous-divergence hole via a `MustTerminate`
#   obligation. This bundle sets `loom.semantics.termination "total"` and the
#   frozen core is a loop-free straight-line transformation: there is no loop in it
#   to make diverge without fabricating one, and no value sub-domain a divergence
#   rival would expose, which is why nothing is ported. "Closed STRUCTURALLY"
#   is corrected: a rival rewrites the whole impl region and may splice a loop, so
#   the class is expressible and it is the DESCENT obligation that refuses it.
#   Under `total` a postcondition is claimed of ALL runs, so every loop owes a
#   decreasing measure AND its descent. Measured with the proof reduced to
#   `loom_solve`: a spliced `decreasing z` loop whose body is `z := z + 1` is
#   refused on `case «decreasing_1: z»`, residual `z + 1 < z`.
#   Omitted as a carrier fact (total semantics + loop-free core), not for
#   difficulty.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `∀ k, (k ∈ out) ↔ (k ∈
#   coordNames)` binds `out` and `coordNames` (`requestedDims` does NOT appear
#   in it — the result is the prior coordinate set regardless of the request, so
#   the common-names component the impl computes from `requestedDims` is always a
#   subset of `coordNames` and changes no membership; a rival that mishandles
#   only `requestedDims` while returning `coordNames` correctly is genuinely
#   correct, which pos-return-coordnames witnesses). Both DIRECTIONS of the
#   biconditional are attacked:
#     * BACKWARD (k ∈ coordNames → k ∈ out): r1-intersection-only (drops a prior
#       coordinate that is not a reshaped dimension) and r3-drop-first-coord
#       (drops the first prior coordinate).
#     * FORWARD (k ∈ out → k ∈ coordNames): r2-window-keyed (promotes a
#       reshaped-dimension name that was not a prior coordinate).
#   The three reject witnesses probe three DISTINCT input points (pts=3):
#     * r1-intersection-only   requestedDims=["time"] coordNames=["day"]
#     * r2-window-keyed        requestedDims=["time"] coordNames=[]
#     * r3-drop-first-coord    requestedDims=[]       coordNames=["day","y"]
#   So the load-bearing binder `coordNames` ranges over {["day"], [], ["day","y"]}
#   (empty / singleton / two-element with the first element dropped), and
#   `requestedDims` over {["time"], []}. No binder is pinned at a single value
#   across the reject set.
#
# AXIOM_TESTS: empty. The bundle declares no consumed axiom (mapping.md §3: the
#   changed op is modeled deeply and concretely, validated by G-CONF; the one
#   neighbouring callee is an A-reference validated by G-AX, not consumed). The
#   sibling's AXIOM_TESTS is likewise empty. This gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
