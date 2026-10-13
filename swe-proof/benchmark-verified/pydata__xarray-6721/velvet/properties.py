"""properties.py — G-PBT falsification battery for pydata__xarray-6721 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct buildChunkInventory`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

================================  DEFENDED SURFACE  ==========================

ONE contracted method over one free carrier:

  buildChunkInventory (vars : List VarDesc)
      return (out : Except ChunkErr (List (Int × Int)))
    ensures out = chunkInventory vars                    -- the WHOLE pin (C1)

The method assembles a per-dimension block-length inventory over a collection of
variables, folding each variable's advertised layout into the running inventory
front-to-back and failing when two DIFFERENT variables disagree on a shared
dimension, or when a layout a variable advertised is not delivered by its own
read. Each ``VarDesc`` exposes exactly three observations:
  * ``chunks : Option (List (Int × Int))`` — whether the variable's cheap storage
    DESCRIPTOR advertises a block layout (``none`` = advertises none) and, if so,
    the pairs reading it is handed. WHICH constructor it is is ALWAYS observable;
    the branch the correct behaviour takes is decided by THIS alone. The pairs
    need NOT name distinct dimensions: a ``Variable``'s dims may repeat, and the
    read then OVERWRITES rather than compares (``dedupeLast``), so a repeated
    dimension keeps its first position and its last block length.
  * ``layoutReadable : Bool`` — for a variable that DOES advertise a layout,
    whether reading that layout back off the variable delivers it. The read is
    surfaced through the variable's value view, so it can fail; the correct
    behaviour then fails the whole inventory. Consulted ONLY on the advertising
    leg — on the ``none`` leg no read happens, so the outcome is independent of
    this field there (``mergeVar_unadvertised``).
  * ``accessible : Bool`` — whether forcing the variable's values into memory
    would succeed. The correct behaviour must NEVER consult it to decide whether
    a variable contributes; it is carried as an orthogonal observation, so the
    pre-image (which forced the values in the guard) is expressible in the twin.

``layoutReadable`` and ``accessible`` are INDEPENDENT (neither implies the other
in either direction, measured on the real carrier by axiom_check.py), so a rival
cannot substitute one for the other, and neither can be dropped as derivable.

``chunkInventory`` is a total, fully-unfolded ``def`` in the ``pure`` region
(``vars.foldl mergeStep (Except.ok [])``, with ``mergeStep``/``mergeVar``/
``mergePairs``/``mergePair`` all spelled out). The ``axioms`` region declares
NOTHING — there is no opaque answer key, so evaluating ``chunkInventory`` IS the
correct answer and the only way to satisfy C1 is to compute that exact
descriptor-only fold. C1 is fully GROUNDED in the input; the carrier is
concrete/decidable (``VarDesc`` derives ``DecidableEq``), so a witness can refute
a rival by computing the disagreement directly at a literal input — no
conditioning on an opaque term is needed and every witness input is jointly
satisfiable by construction (each is a concrete list of literal ``VarDesc``).

LOAD-BEARING CONTENT of C1, per sub-domain:
  * DESCRIPTOR-ONLY BRANCH: the fold branches on ``v.chunks`` and NEVER on
    ``v.accessible``. An impl that consults ``accessible`` (the pre-image:
    forcing the values to decide whether a variable contributes) diverges from
    ``chunkInventory`` on any variable that advertises no layout but whose values
    cannot be materialized — this IS the modeled defect.
  * CONTRIBUTE: a variable advertising a readable layout merges its (dim, block)
    pairs, in that orientation. An impl that swaps the orientation, or that never
    merges, diverges wherever some variable advertises one.
  * FAIL-ON-UNREADABLE-LAYOUT: a variable advertising a layout its own read does
    not deliver (``layoutReadable = false``) must produce the
    ``layoutUnavailable`` failure. An impl that merges the advertised pairs
    regardless describes a program whose layout read consults the descriptor;
    that is not this repository's ``Variable.chunksizes``, which indexes the
    value view (mapping.md §1.1). Passing the descriptor guard does not imply the
    layout can be obtained.
  * FAIL-ON-DISAGREEMENT (BETWEEN VARIABLES): two DIFFERENT variables advertising
    readable layouts that share a dimension with different block lengths must
    produce the ``inconsistent`` failure. An impl that drops the agreement check
    silently over-merges instead of failing.
  * OVERWRITE (WITHIN ONE VARIABLE): a single variable advertising one dimension
    twice with different block lengths must NOT fail — the read that yields those
    pairs builds a dict keyed by dimension, so it keeps the last block length at
    the first position and raises nothing (``dedupeLast``, mapping.md §1.2). An
    impl that applies the agreement rule to one variable's own pairs describes a
    program whose ``chunksizes`` compares instead of building a mapping; that is
    not this repository's, and the input is reachable from the public API
    (``xr.Dataset({'a': Variable(('x','x'), arr)}).chunks``). This sub-domain is
    the one place a rival can be STRICTER than the desired behaviour and still be
    wrong, so it is attacked in that direction.

INPUT BINDER: ``vars`` (a ``List VarDesc``); each element's ``.chunks``,
``.layoutReadable`` and ``.accessible`` sub-fields, the ``.chunks`` payload's own
length and dimension multiplicity, and the list length, are the axes a rival can
abuse. The reject witnesses move all of them (see the footer's coverage table): a
variable at ``accessible = false`` (the descriptor-vs-values attack), one at
``layoutReadable = false`` (the layout-read attack), advertising variables at
various layouts and orientations, a single variable whose two-pair payload names
ONE dimension twice (the mapping-construction attack), and a two-element list
whose members disagree on a shared dimension — so no sub-field is pinned.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl must verify, else C1 is SPEC-TOO-STRONG (over-
    pins the impl shape rather than the returned inventory).
  * ADMISSIBILITY — RE-AIMED. The nagini sibling self-asserts that an F2P-shaped
    collection satisfies its fractional-permission precondition. This method
    declares NO ``require`` (the fold is total in its input), so that probe is
    degenerate; the residual risk is a DEGENERATE post-image on a total domain.
    Re-aimed to the frozen impl discharging C1, witnessing that the post-image
    (the descriptor-only fold) is satisfiable by a gold-shaped computation. Else
    SPEC-UNSATISFIABLE.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling's two
    mandatory frame rivals write a read-only input held at a fractional heap
    permission (``Acc(.,1/8)``) and are rejected for INSUFFICIENT PERMISSION.
    Lean/Velvet are referentially transparent: ``vars`` is an immutable value
    parameter, this bundle declares NO ``mut`` binder, and there is no heap,
    aliasing, or permission system. There is no read-only input to overwrite and
    no frame clause to violate, so the class has no carrier analogue. NOT ported,
    no substitute fabricated; the nagini "inputs are read-only" obligation is
    here structurally guaranteed by the ABSENCE of ``mut``, which the frozen spec
    already encodes.
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
    loop in the impl (1 loop here, measure ``vars.length - i``). A rival that
    loops without a measure is refused outright (``Decreasing annotations are
    required in total correctness semantics``), and a rival that supplies a
    CONSTANT measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE / ECHO — N/A as an attack. The nagini sibling's central
    attack is a SIDE-EFFECT one: the discriminator is a forced-materialization
    (a loads tally) with no value footprint, defended by an unforgeable
    capability token (``payload_intact``) that the materialising view consumes.
    On this carrier the same distinction is a VALUE: consulting the values-view
    (``accessible``) makes an un-materializable, un-chunked variable produce
    ``valuesUnavailable`` instead of being passed over, which C1 refutes at a
    concrete input (the ``weak-consults-accessible`` rival). So the token
    machinery is not needed — the effect the token guarded is here observable in
    the returned value, and the nagini "materialise-then-echo-0" hole is CLOSED
    by C1 directly. There is no opaque answer key a wrong impl could echo:
    ``chunkInventory`` is the transparent fold over ``vars`` itself.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (consult the values-view, never
    contribute, swap the pair orientation, or drop the disagreement check).

WITNESS MECHANICS ON THIS BUNDLE. The tester+``decide`` path
(``derive_tester_for`` → ``<name>Tester args = false``) is DEAD here: the
postcondition's ``Decidable`` instance does not auto-derive over the ``while``
loop's extracted program (measured: ``prove_postcondition_decidable_for`` leaves
``Decidable (out = chunkInventory vars)`` unsolved and the tester stays stuck for
BOTH rival and gold, discriminating nothing). Instead — exactly the django-11276
pattern — each rival is written LOOP-FREE (a ``vars.foldl`` over a pure step, no
``while``), so its extracted program ``buildChunkInventoryExec`` reduces fully
under ``decide`` at a concrete input, while gold's ``while``-loop ``…Exec`` is
well-founded recursion the kernel does NOT reduce. Each witness states, at one
concrete input,

    (match buildChunkInventoryExec <input> with | DivM.res r => r | _ => …)
        ≠ chunkInventory <input>

i.e. the rival's own extracted output DIFFERS from the transparent post-image C1
demands — a direct C1 violation the elaborator sees against the rival, and which
gold cannot satisfy (gold's ``…Exec`` stays stuck, so ``decide`` cannot close the
``≠`` and the witness FAILS on gold — the required discriminator half). The
carrier ``Except ChunkErr (List (Int × Int))`` has no ambient ``DecidableEq``
instance in the workspace, so each witness brings its own with
``deriving instance DecidableEq for Except`` (a witness-local declaration,
appended to BOTH files, present on both sides by construction — not a name the
variant introduces). No witness binds any hypothesis (every input is a concrete
literal list that decides C1), so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque). Each witness was checked out-of-band
with ``scripts/lean_verify.sh``: every one ELABORATES against its rival (no
error) and FAILS against gold (a ``decide`` error at the ``Except`` equality).

AXIOM lane: EMPTY. ``AXIOM_TESTS = []``. This bundle declares no ``axiom``; the
three facts the inventory consults about each variable are modeled as concrete
input fields of ``VarDesc`` (an R-refinement validated by axiom_check.py /
conformance_check.py — mapping.md §3), not consumed axioms. The nagini sibling's
``AXIOM_TESTS`` (its real-xarray probes of the two payload views) belong to the
G-AX lane; the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6721"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the method's -- impl-start .. -- impl-end
# region or is the prove_correct tactic body, and each is unique in
# Solution.lean (both asserted at load by _swap). Editing only these keeps
# markers.same_spec True and the prove_correct buildChunkInventory header +
# byte-identical `ensures out = chunkInventory vars` statement present.
# ---------------------------------------------------------------------------

# The WHOLE frozen impl body (the forward `while` fold), everything strictly
# between the method's -- impl-start / -- impl-end.
_IMPL = (
    "    let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []\n"
    "    let mut i := 0\n"
    "    while i < vars.length\n"
    "      invariant 0 ≤ i ∧ i ≤ vars.length\n"
    "      invariant acc = (vars.take i).foldl mergeStep (Except.ok [])\n"
    "      done_with i = vars.length\n"
    "      decreasing vars.length - i\n"
    "    do\n"
    "      acc := mergeStep acc vars[i]!\n"
    "      i := i + 1\n"
    "    return acc"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof body, verbatim. Loop-free CORRECT reshapes retune it (elided
# from the spec view); loop-keeping variants and every reject rival leave it
# as-is — a reject rival's rejection is carried by its witness, not by any
# tactic gap (the frozen loop proof does not match a loop-free rival, but that
# is not what the gate credits: the witness is the oracle).
_PROOF = (
    "prove_correct buildChunkInventory by\n"
    "  loom_solve\n"
    "  · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]\n"
    "  · simp_all [chunkInventory, List.take_length]"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# Bare retune for a loop-free single-return correct reshape: no loop goals
# remain, so `loom_solve` alone closes the residual.
_PROOF_BARE = "prove_correct buildChunkInventory by\n  loom_solve"


def _impl(new_body):
    """Full variant with ONLY the impl body replaced (frozen proof retained)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (loop-free correct reshape)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


def _foldl_rival(step_body):
    """A LOOP-FREE rival: fold a pure step over `vars`. Being loop-free, its
    extracted `buildChunkInventoryExec` reduces under `decide` so its witness
    discriminates; gold's `while`-loop `…Exec` stays stuck. Frozen proof kept."""
    return _impl(
        "    return (vars.foldl (fun acc v =>\n" + step_body + ") (Except.ok []))")


# ---- witness preamble + builder. The tester+`decide` path is dead (the
# ---- postcondition's Decidable instance does not auto-derive over the loop),
# ---- so extract the executable program and refute C1 directly on the
# ---- TRANSPARENT `chunkInventory`. Checked in a file whose `prove_correct`
# ---- block is stripped, so no tactic script can mask the verdict. The witness
# ---- supplies its own `DecidableEq (Except …)` (absent from the workspace),
# ---- appended to both files so it exists on both sides.
_WITNESS_PRELUDE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for buildChunkInventory\n\n"
)


def _witness(inp):
    return (
        _WITNESS_PRELUDE +
        "example :\n"
        f"    (match buildChunkInventoryExec ({inp}) with"
        " | DivM.res r => r | _ => Except.ok [])"
        f" ≠ chunkInventory ({inp}) := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, C1 is
    # SPEC-TOO-STRONG (over-fits the impl shape). Both verified green during
    # authoring.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded model directly, no
        # loop. C1 is literally `out = chunkInventory vars`, so `out` IS that
        # model and the ensures holds definitionally; the loop-free reshape
        # leaves no step-lemma goal, so the proof retunes to a bare `loom_solve`.
        # Doubles as the no-ungrounded-echo control: `chunkInventory vars` is a
        # transparent fold over the input, not an answer key, so a direct return
        # is the correct computation, not a cheat.
        "module": _impl_reproved(
            "    return (chunkInventory vars)", _PROOF_BARE),
        "rationale": (
            "the post-image `chunkInventory vars` is GROUNDED in the input (a "
            "total left-fold, no opaque answer key), so `return chunkInventory "
            "vars` is the honest cheapest CORRECT impl; C1 is literally `out = "
            "chunkInventory vars`, so it MUST verify, else C1 is SPEC-TOO-STRONG "
            "(over-fit to the loop shape). Also the honest no-echo control: the "
            "descriptor-only fold IS the work, so a direct return is correct, not "
            "an echo. (Nagini: pos-control-reorder-hoist — a structurally-"
            "different correct impl; re-shaped, since this backend's cheapest "
            "different shape is the loop-free direct return.)"),
    },
    {
        "id": "pos-control-local-bind",
        "kind": "soundness",
        "expect": "verify",
        # Keep the forward `while` fold but bind the current variable to a typed
        # local before the step. Same value flow (`mergeStep acc v`), different
        # control shape; the frozen loop proof still closes unchanged.
        "module": _impl(
            "    let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []\n"
            "    let mut i := 0\n"
            "    while i < vars.length\n"
            "      invariant 0 ≤ i ∧ i ≤ vars.length\n"
            "      invariant acc = (vars.take i).foldl mergeStep (Except.ok [])\n"
            "      done_with i = vars.length\n"
            "      decreasing vars.length - i\n"
            "    do\n"
            "      let v := vars[i]!\n"
            "      acc := mergeStep acc v\n"
            "      i := i + 1\n"
            "    return acc"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the current "
            "variable to a typed local before the step) must verify; the value "
            "flow is unchanged (`mergeStep acc v` with `v = vars[i]!`) so C1 "
            "still discharges and the frozen loop proof closes as-is. If it fails "
            "=> SPEC-TOO-STRONG (over-fit to the inline-index code form). (Nagini: "
            "the branch-reorder/hoist positive, re-expressed as a local bind "
            "since the step here is a single `def` with no branch to reorder.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini precondition-admissibility case.
    # This method carries NO `require` (the fold is total in `vars`), so the
    # classic "a normal input satisfies the precondition" probe is degenerate.
    # The analogue on a total carrier is the obligation being UNSATISFIABLE at
    # exactly an F2P-shaped input, which is what this case tests: a `have` that
    # discharges the post-image AT that concrete input, BY EVALUATION, before the
    # frozen obligation is closed verbatim.
    #
    # This replaces an earlier `module = _BASE` case. That case re-built the
    # frozen file unchanged, so it could only reproduce G-VERIFY's own verdict:
    # nothing in it mentioned any input, and it would have verified whatever the
    # post-image said at the F2P point (audit finding, this cell). The `have`
    # below is LIVE rather than inert — machine-checked by building the same
    # shape with the WRONG value on the right-hand side, which FAILS with
    # `Tactic `rfl` failed: ... chunkInventory [...] is not definitionally equal
    # to ... Except.error ChunkErr.valuesUnavailable`. So the tactic really does
    # reduce the fold at this input, and the case would fail if the post-image
    # were degenerate there.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-postimage",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl, frozen obligation, frozen script — plus a leading `have`
        # (inside the elided prove_correct body, so same_spec holds) that
        # EVALUATES C1's post-image at the F2P-shaped input: one variable whose
        # descriptor advertises no layout and whose values cannot be
        # materialized. The post-image must reduce to the pass-over value
        # `Except.ok []` there. If C1 were unsatisfiable / degenerate at exactly
        # that point, `rfl` would not close this and the case fails.
        "module": _impl_reproved(
            _IMPL,
            "prove_correct buildChunkInventory by\n"
            "  have hF2P : chunkInventory\n"
            "      [{ chunks := none, accessible := false, layoutReadable := true }]\n"
            "      = Except.ok [] := by rfl\n"
            "  loom_solve\n"
            "  · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega),"
            " ← invariant_2]\n"
            "  · simp_all [chunkInventory, List.take_length]"),
        "rationale": (
            "the method declares no `require`, so the classic precondition probe "
            "is degenerate; the residual risk on a total carrier is that C1's "
            "post-image is UNSATISFIABLE or degenerate at exactly an F2P-shaped "
            "input. This case discharges it AT that input by evaluation — one "
            "variable advertising NO layout whose values cannot be materialized "
            "reduces `chunkInventory` to `Except.ok []`, the pass-over value — as "
            "a `have`, and only then closes the frozen obligation verbatim. The "
            "`have` is demonstrated LIVE: the same shape with the wrong "
            "right-hand side (`Except.error valuesUnavailable`) fails `rfl` on "
            "this bundle, so the tactic reduces the fold rather than accepting "
            "any claim. If this cannot be discharged => SPEC-UNSATISFIABLE at "
            "the input class the whole obligation exists to pin. Re-aimed from "
            "the nagini admiss-f2p-shaped case, whose read-only-permission half "
            "has no counterpart on this referentially-transparent carrier."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1. Each rival is
    # loop-free so its `…Exec` reduces under `decide`; gold's `while`-loop `…Exec`
    # stays stuck, so each witness elaborates against its rival and FAILS against
    # gold (verified during authoring).
    # =====================================================================
    {
        "id": "weak-consults-accessible",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled defect: decide chunkedness by first forcing the values into
        # memory (consult `accessible`). A variable whose values cannot be
        # materialized yields the `valuesUnavailable` failure even when it
        # advertises no layout and should simply be passed over. Correct on every
        # accessible variable; wrong exactly on an inaccessible one.
        "module": _foldl_rival(
            "      match acc with\n"
            "      | Except.error e => Except.error e\n"
            "      | Except.ok a =>\n"
            "          if !v.accessible then Except.error ChunkErr.valuesUnavailable\n"
            "          else match v.chunks with\n"
            "            | none       => Except.ok a\n"
            "            | some pairs => mergePairs a pairs"),
        "refinement": (
            "consulting whether the values can be materialized before deciding "
            "chunkedness IS the pre-image behaviour: its faithful real patch is "
            "the unpatched function, which forces the values-view of every "
            "variable. On the failing scenario the non-index variables wrap an "
            "inaccessible store that raises on any element access, so forcing "
            "their values raises exactly the error the fix removes — it does NOT "
            "resolve the failing test (which asserts an empty inventory with no "
            "value access). This is the exact defect the change corrects."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): `chunkInventory` reads "
            "`v.chunks` off the descriptor and NEVER `v.accessible`, so on a "
            "variable with `chunks = none, accessible = false` it passes the "
            "variable over (`Except.ok []`), but the rival returns "
            "`Except.error valuesUnavailable`. Refuted at a single "
            "inaccessible, un-chunked variable — the sub-field `accessible = "
            "false` no other witness reaches. If it verified => SPEC-TOO-WEAK "
            "(admits the descriptor-vs-values bug). (Nagini: the two echo rivals "
            "weak-echo-* — here the side effect they guarded is observable in the "
            "returned value, so C1 refutes it directly without a capability "
            "token.)"),
        "witness": _witness(
            "[({ chunks := none, accessible := false } : VarDesc)]"),
    },
    {
        "id": "weak-never-contributes",
        "kind": "uniqueness",
        "expect": "reject",
        # Never merge any advertised layout — return the empty inventory for every
        # input. The pre-image of "contribute nothing": a chunked dataset reports
        # no chunks. Correct only when every variable is un-chunked.
        "module": _foldl_rival("      acc"),
        "refinement": (
            "never merging any advertised layout reports an empty inventory even "
            "for a genuinely chunked dataset. A real patch of this shape would "
            "build an empty chunk mapping for every dataset, so the pass-to-pass "
            "chunk tests that read back a non-empty chunk layout (test_chunk, "
            "test_dask_is_lazy) would fail — it does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): for a chunked variable "
            "`chunkInventory` merges its pairs (a non-empty inventory), but the "
            "rival returns `Except.ok []`. Refuted at a single chunked, "
            "accessible variable (`chunks = some [(1,2)], accessible = true`), "
            "moving `chunks` to `some` and `accessible` to `true` off the "
            "consults-accessible rival's point. If it verified => SPEC-TOO-WEAK "
            "(the contribute behaviour unpinned). (Nagini: partial-wrong-empty-"
            "marker, re-expressed as never-contribute on this fold.)"),
        "witness": _witness(
            "[({ chunks := some [(1,2)], accessible := true } : VarDesc)]"),
    },
    {
        "id": "weak-swap-pair-orientation",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge each advertised pair with dimension and block length SWAPPED, so
        # the inventory keys on block length and values the dimension. Correct
        # only on the sub-domain where every pair has dim == block; wrong wherever
        # a pair's dimension differs from its block length.
        "module": _foldl_rival(
            "      match acc with\n"
            "      | Except.error e => Except.error e\n"
            "      | Except.ok a =>\n"
            "          match v.chunks with\n"
            "          | none       => Except.ok a\n"
            "          | some pairs =>\n"
            "              mergePairs a ((dedupeLast pairs).map (fun p => (p.2, p.1)))"),
        "refinement": (
            "swapping each pair's dimension and block length builds the inventory "
            "keyed on block length instead of dimension — the wrong mapping. A "
            "real patch of this shape would report block lengths as dimension "
            "keys, failing the pass-to-pass chunk tests on any variable whose "
            "dimension label differs from its block length; it does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): `chunkInventory` merges "
            "`(dim, block)` in that orientation, so on a chunked variable "
            "advertising `[(5,7)]` it yields `[(5,7)]` while the rival yields "
            "`[(7,5)]`. Refuted at a chunked variable with dim ≠ block "
            "(`chunks = some [(5,7)]`) — a distinct input point from the "
            "never-contribute rival, varying the `chunks` payload. If it verified "
            "=> SPEC-TOO-WEAK (the pair orientation unpinned). (Nagini: partial-"
            "swap-axis-length.)"),
        "witness": _witness(
            "[({ chunks := some [(5,7)], accessible := true } : VarDesc)]"),
    },
    {
        "id": "weak-drops-disagreement-check",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge every advertised pair by unconditional append, dropping the
        # shared-dimension agreement check. Correct whenever no two chunked
        # variables share a dimension with different block lengths; wrong exactly
        # when they do (must produce the `inconsistent` failure).
        "module": _foldl_rival(
            "      match acc with\n"
            "      | Except.error e => Except.error e\n"
            "      | Except.ok a =>\n"
            "          match v.chunks with\n"
            "          | none       => Except.ok a\n"
            "          | some pairs => Except.ok (a ++ dedupeLast pairs)"),
        "refinement": (
            "appending every advertised pair without the shared-dimension "
            "agreement check silently accepts two chunked variables that disagree "
            "on a dimension's block length, where the desired behaviour raises. A "
            "real patch of this shape would build an inconsistent mapping instead "
            "of raising the documented error, so the pass-to-pass tests that "
            "assert the inconsistency failure would fail; it does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): on two chunked "
            "variables sharing dimension `1` with different block lengths "
            "(`[(1,2)]` then `[(1,3)]`), `chunkInventory` produces "
            "`Except.error inconsistent`, but the rival appends to give "
            "`Except.ok [(1,2),(1,3)]`. Refuted at a TWO-element list (moving the "
            "list-length axis off every other witness's singleton) whose members "
            "disagree on a shared dimension — the `inconsistent` clause no other "
            "witness reaches. If it verified => SPEC-TOO-WEAK (the disagreement "
            "failure unpinned). (Nagini: no direct sibling; ADDED to attack the "
            "error-outcome clause of C1.)"),
        "witness": _witness(
            "[({ chunks := some [(1,2)], accessible := true } : VarDesc),"
            " ({ chunks := some [(1,3)], accessible := true } : VarDesc)]"),
    },
    {
        "id": "weak-ignores-layout-read",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge every advertised layout without checking that reading it back off
        # the variable delivers it. Correct on every variable whose layout read
        # succeeds; wrong exactly where a descriptor advertises a layout its own
        # read does not deliver. This is a model of a DIFFERENT program: one whose
        # layout read consults the descriptor rather than the value view.
        "module": _foldl_rival(
            "      match acc with\n"
            "      | Except.error e => Except.error e\n"
            "      | Except.ok a =>\n"
            "          match v.chunks with\n"
            "          | none       => Except.ok a\n"
            "          | some pairs => mergePairs a (dedupeLast pairs)"),
        "refinement": (
            "merging an advertised layout without checking that its own read "
            "delivers it describes a `Variable.chunksizes` that reads the storage "
            "descriptor. The real property tests `self._data` and then indexes "
            "`self.data.chunks` — the VALUE view — and `patch.diff` does not touch "
            "it (mapping.md §1.1). A real function of this rival's shape would "
            "therefore have to return block lengths for a variable whose values "
            "cannot be obtained, where the repo raises: measured in the instance "
            "image, an `ExplicitlyIndexed` descriptor carrying `chunks` over an "
            "inaccessible store raises `UnexpectedDataAccess`, over a plain array "
            "raises `AttributeError`, and a descriptor advertising `chunks = None` "
            "raises `TypeError` — identically before AND after the patch "
            "(mapping.md §2.1). So this rival is not the gold patch on that "
            "sub-domain; it is a program with a different `chunksizes`."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): on a variable "
            "advertising `[(1,2)]` whose layout read does not deliver "
            "(`layoutReadable = false`), `chunkInventory` produces "
            "`Except.error layoutUnavailable`, but the rival merges the advertised "
            "pairs to give `Except.ok [(1,2)]`. Refuted at the `layoutReadable = "
            "false` sub-field no other witness reaches, with `accessible = true` "
            "so the point is DISTINCT from the consults-accessible rival's and "
            "cannot be confused with it — the two observations are independent. If "
            "it verified => the spec would be SPEC-TOO-WEAK on this leg, and worse, "
            "the leg would be UNMODELED: this rival is exactly the model shipped "
            "before the region was widened, retained here so the battery keeps "
            "rejecting it. (Nagini: no sibling; ADDED with the third observation.)"),
        "witness": _witness(
            "[({ chunks := some [(1,2)], accessible := true,"
            " layoutReadable := false } : VarDesc)]"),
    },
    {
        "id": "weak-compares-repeated-dim",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge one variable's OWN pairs with the shared-dimension agreement rule,
        # instead of first assembling them into the per-dimension mapping its read
        # yields. Correct on every variable whose dimension names are distinct
        # (where `dedupeLast` is the identity); wrong exactly where one variable
        # advertises a dimension twice with different block lengths. A model of a
        # DIFFERENT program: one whose layout read compares instead of building a
        # mapping.
        "module": _foldl_rival(
            "      match acc with\n"
            "      | Except.error e => Except.error e\n"
            "      | Except.ok a =>\n"
            "          match v.chunks with\n"
            "          | none       => Except.ok a\n"
            "          | some pairs =>\n"
            "              if v.layoutReadable then mergePairs a pairs\n"
            "              else Except.error ChunkErr.layoutUnavailable"),
        "refinement": (
            "applying the shared-dimension agreement rule to a single variable's "
            "own pairs describes a `Variable.chunksizes` that COMPARES repeated "
            "dimensions. The real property builds a dict — `Frozen({dim: c for "
            "dim, c in zip(self.dims, self.data.chunks)})` — so a dimension a "
            "variable advertises twice is overwritten, first position and last "
            "block length, and nothing is raised (mapping.md §1.2). A `Variable`'s "
            "dims need not be distinct, and the input is reachable from the public "
            "API: measured in the instance image, `Variable((\'x\',\'x\'), "
            "da.from_array(np.zeros((4,4)), chunks=((4,),(2,2))))` reads as "
            "`{\'x\': (2, 2)}`, `get_chunksizes([v])` is the same and so is "
            "`xr.Dataset({\'a\': v}).chunks` — identically before AND after the "
            "patch (mapping.md §2.1). A real function of this rival's shape would "
            "raise the inconsistency error there, failing on an input the repo "
            "accepts, so it is not the gold patch on that sub-domain; it is a "
            "program with a different `chunksizes`."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): on ONE variable "
            "advertising dimension `0` twice with different block lengths "
            "(`some [(0,4),(0,2)]`), `chunkInventory` assembles the mapping that "
            "variable\'s read yields and produces `Except.ok [(0,2)]`, while the "
            "rival compares and produces `Except.error inconsistent`. Refuted at a "
            "repeated dimension WITHIN one variable — an input-shape axis (a "
            "two-pair payload naming one dimension twice) that no other witness "
            "reaches, and deliberately with `layoutReadable = true` so the point is "
            "DISTINCT from the ignores-layout-read rival\'s. Note the direction: "
            "this rival is STRICTER than the desired behaviour, so rejecting it is "
            "not about the obligation being too weak but about its denoting the "
            "right program — if it verified, C1 would be pinning the inconsistency "
            "failure inside a single variable, where the repo raises nothing, and "
            "the model would be UNFAITHFUL rather than merely weak. This rival is "
            "exactly the model shipped before `dedupeLast` was added, retained here "
            "so the battery keeps rejecting it. (Nagini: no sibling; ADDED with the "
            "mapping-construction step.)"),
        "witness": _witness(
            "[({ chunks := some [(0,4),(0,2)], accessible := true,"
            " layoutReadable := true } : VarDesc)]"),
    },
    {
        "id": "weak-skips-first-variable",
        "kind": "uniqueness",
        "expect": "reject",
        # Fold over every variable EXCEPT the first: an off-by-one on the scan's
        # start. Correct whenever the first variable advertises no layout (it
        # would have contributed nothing anyway); wrong exactly when it does
        # advertise one, or when it is the variable that would have failed the
        # inventory. Ported from the nagini off-by-one, which an earlier revision
        # of this battery recorded as subsumed by never-contribute; it is NOT
        # subsumed and it is expressible here (audit finding, this cell) — the
        # rival is correct on the whole never-contribute witness class except
        # at index 0, so it pins the START of the scan, which no other rival
        # touches.
        "module": _impl(
            "    return ((vars.drop 1).foldl mergeStep (Except.ok []))"),
        "refinement": (
            "starting the scan at the second variable drops the first one's "
            "contribution entirely, so a chunked dataset reports an inventory "
            "missing the dimensions only its first variable advertises, and an "
            "inventory that should have failed on that variable succeeds. A real "
            "patch of this shape would report the wrong chunk mapping for any "
            "dataset whose first variable is the chunked one, so the "
            "pass-to-pass chunk tests that read a full chunk layout back would "
            "fail — it does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = chunkInventory vars`): `chunkInventory` folds "
            "EVERY variable, first one first, so on a single chunked variable it "
            "yields `Except.ok [(1,2)]` while the rival — which begins at the "
            "second — yields `Except.ok []`. Refuted at index 0 of the scan, the "
            "one axis the other rivals leave unpinned: each of them is wrong on a "
            "PROPERTY of a variable and so is wrong at every position, whereas "
            "this one is wrong only at a POSITION. If it verified => SPEC-TOO-WEAK "
            "(the scan's starting point unpinned, so C1 would not fix which "
            "variables are folded). (Nagini: partial-skip-first-entry, PORTED — "
            "an earlier revision recorded it as subsumed by never-contribute, "
            "which the audit disproved by landing it.)"),
        "witness": _witness(
            "[({ chunks := some [(1,2)], accessible := true } : VarDesc)]"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling ships 11 SPEC cases (1 soundness, 1 admissibility, 2
# MANDATORY frame-mutation rivals, 7 uniqueness) plus a 2-case AXIOM lane, over
# ONE contracted function (block_lengths_by_axis) whose discriminator is a
# forced-materialization SIDE EFFECT (a loads tally) with no value footprint,
# defended by an unforgeable capability token (payload_intact) that the
# materialising payload view consumes. This Lean-family bundle models the SAME
# descriptor-vs-values distinction DEEPLY over ONE obligation
# (buildChunkInventory, `out = chunkInventory vars`) — and crucially the side
# effect the nagini token guarded is here a VALUE: consulting the values-view
# (`accessible`) makes an inaccessible, un-chunked variable return
# `valuesUnavailable` instead of being passed over, which C1 refutes at a
# concrete input. So the token/echo machinery is unnecessary and the nagini
# "materialise-then-echo-0" hole is closed by C1 directly.
#
#   nagini case                        kind          -> here                        disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-reorder-hoist          soundness     -> pos-control-direct          RE-SHAPED
#                                                        (+ pos-control-local-bind   ADDED)
#   admiss-f2p-shaped                  admissibility -> admiss-f2p-shaped-postimage RE-AIMED
#   frame-write-block-backed           uniqueness    -> (none)                      VACUOUS
#   frame-write-axis                   uniqueness    -> (none)                      VACUOUS
#   weak-echo-materialise-then-zero    uniqueness    -> weak-consults-accessible    RE-EXPRESSED
#   weak-echo-underlying-then-materialise uniqueness -> (folded into above)         MERGED
#   partial-swap-axis-length           uniqueness    -> weak-swap-pair-orientation  PORTED
#   partial-skip-first-entry           uniqueness    -> weak-skips-first-variable   PORTED (was VACUOUS)
#   partial-wrong-empty-marker         uniqueness    -> weak-never-contributes      RE-EXPRESSED
#   tally-nonzero-trailing-slot        uniqueness    -> (none)                      VACUOUS (side-effect tally)
#   trunc-missing-tally-slot           uniqueness    -> (none)                      VACUOUS (side-effect tally)
#   (no sibling)                       uniqueness    -> weak-drops-disagreement-check ADDED
#   (no sibling)                       uniqueness    -> weak-ignores-layout-read     ADDED
#   (no sibling)                       uniqueness    -> weak-compares-repeated-dim    ADDED
#   AXIOM_TESTS (ax-sound/ax-contain)  axiom         -> (none)                      DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 2 soundness, 1 admissibility, 7 uniqueness.
#
# RE-SHAPED / ADDED (pos-control-reorder-hoist): the nagini positive reorders the
#   if/else and hoists axis/length to locals. Early-return-in-branch is banned
#   here and the step is a single `def` (no branch to reorder), so the maximally-
#   different correct shape is the loop-free direct return of the grounded model
#   `chunkInventory vars` (proof retuned to bare `loom_solve`). A loop-keeping
#   local-bind reshape is ADDED as a second, minimally-different correct control.
# RE-AIMED (admiss-f2p-shaped -> admiss-f2p-shaped-postimage): the nagini case
#   asserts the fractional-permission precondition (token + read perms) holds for
#   a normal input. This method declares no `require` and has no permission
#   surface, so that reading is degenerate; re-aimed at post-image satisfiability
#   AT AN F2P-SHAPED INPUT, discharged by evaluation as a `have` before the frozen
#   obligation is closed verbatim. An earlier revision aimed it at "the frozen
#   impl discharging C1" with `module = _BASE` — the frozen file byte-for-byte,
#   which only reproduces G-VERIFY's verdict and mentions no input at all, so it
#   would have passed whatever the post-image said at the F2P point (audit
#   finding, this cell). The replacement's `have` is machine-demonstrated LIVE:
#   the same shape with the wrong right-hand side FAILS `rfl` on this bundle.
# RE-EXPRESSED / MERGED (the two echo rivals -> weak-consults-accessible): on
#   nagini the discriminator is a forced-materialization side effect with no
#   value footprint, defended by the payload_intact token; both echo rivals
#   (materialise-then-zero, and its reversed call order) consume the token and
#   fail the postcondition. On THIS carrier the same act is observable in the
#   returned value — consulting `accessible` produces `valuesUnavailable` on an
#   inaccessible un-chunked variable where the spec passes it over — so a SINGLE
#   value-level rival (weak-consults-accessible) with a concrete witness refutes
#   it directly. The reversed-call-order variant tested only that the token binds
#   independent of ordering (a token-machinery fact with no carrier analogue
#   here), so it is folded in, not shipped separately.
# PORTED (partial-swap-axis-length -> weak-swap-pair-orientation): swapping the
#   (dim, block) orientation ports one-for-one; refuted on a pair with dim ≠
#   block.
# RE-EXPRESSED (partial-wrong-empty-marker -> weak-never-contributes): the nagini
#   rival emits the wrong marker for a non-block-backed entry. Here the analogous
#   value error is contributing nothing for a chunked variable (report an empty
#   inventory for a chunked dataset); refuted on a chunked, accessible variable.
# ADDED (weak-drops-disagreement-check): attacks the `inconsistent` error-outcome
#   clause of C1 — a rival that appends every pair without the shared-dimension
#   agreement check, refuted on a two-element list whose members disagree. Also
#   the only witness exercising the list-length axis (a 2-element input). No
#   nagini sibling (nagini's error surface was the side-effect tally, vacuous
#   here); a real divergence with a machine-checked witness.
# ADDED (weak-ignores-layout-read): attacks the `layoutUnavailable` error-outcome
#   clause of C1 — a rival that merges an advertised layout without checking that
#   reading it back off the variable delivers it, refuted on the
#   `layoutReadable = false` sub-field. This rival is a model of a DIFFERENT
#   program (one whose `chunksizes` reads the descriptor), and it is precisely the
#   model this bundle shipped before the modeled region was widened to cover the
#   read — kept as a standing case so the battery re-rejects it. No nagini
#   sibling: the nagini carrier's payload views are axiom-mediated, so its battery
#   has no analogue of a guard that passes while the subsequent read fails.
# ADDED (weak-compares-repeated-dim): attacks the BOUNDARY between the two merge
#   rules in C1 — a rival that applies the shared-dimension agreement rule to one
#   variable's OWN pairs instead of first assembling them into the per-dimension
#   mapping its read yields (`dedupeLast`), refuted on a single variable
#   advertising one dimension twice with different block lengths. Unusually, this
#   rival is STRICTER than the desired behaviour: it raises where the repo returns
#   the overwritten mapping. It is therefore a faithfulness case, not a weakness
#   case — it pins that C1 denotes a program whose layout read builds a dict
#   (`Frozen({dim: c for dim, c in zip(self.dims, self.data.chunks)})`) rather
#   than one that compares, and it is precisely the model this bundle shipped
#   before `dedupeLast` was added. `Variable(('x','x'), arr)` is an ordinary
#   variable and `xr.Dataset({'a': v}).chunks` reaches it from the public API, so
#   the input point is real, not adversarial. No nagini sibling: nagini's payload
#   is indexed per-axis through an axiom, so a repeated axis label has no analogue
#   there. The other three merge rivals were given the correct `dedupeLast` step
#   at the same time, so each now diverges from gold in exactly ONE respect and no
#   rival can be rejected for the wrong reason.
# VACUOUS — frame (frame-write-block-backed, frame-write-axis): the two nagini
#   MANDATORY frame rivals write a read-only input field held at a fractional
#   heap permission (Acc(.,1/8)) and are rejected for INSUFFICIENT PERMISSION.
#   Lean/Velvet are referentially transparent: `vars` is an immutable value
#   parameter, this bundle declares NO `mut` binder, and there is no heap,
#   aliasing, or fractional permission. There is no read-only input to overwrite
#   and no frame clause to violate; the class has no carrier analogue. Omitted as
#   a genuine carrier fact, NOT fabricated. The nagini read-only obligation is
#   here structurally guaranteed by the absence of `mut`, which the frozen spec
#   already encodes.
# VACUOUS — side-effect tally (tally-nonzero-trailing-slot, trunc-missing-tally-
#   slot): both nagini rivals attack the trailing "loads forced" tally slot — a
#   SECONDARY value that models the forced-materialization side effect the nagini
#   spec appended as an extra result element. This bundle does NOT model a loads
#   tally: the descriptor-vs-values distinction is captured directly in the
#   RETURNED inventory (an inaccessible un-chunked variable is passed over vs.
#   producing `valuesUnavailable`), so there is no separate tally slot to zero or
#   truncate. The behaviour those rivals probed (the no-load guarantee) is the
#   SAME behaviour weak-consults-accessible attacks head-on via C1. No separate
#   tally clause exists to attack; omitted as a genuine modeling-narrowing fact.
# PORTED (partial-skip-first-entry -> weak-skips-first-variable): the nagini
#   off-by-one skips entry 0 of the scan. An earlier revision of this battery
#   recorded it VACUOUS-as-subsumed, arguing that a "skip the first variable"
#   rival would be refuted by the never-contribute witness class anyway. The
#   audit disproved that and landed the case (audit finding, this cell). The two
#   are not the same attack: never-contribute is wrong about a PROPERTY of a
#   variable and so diverges at every position, whereas this rival is wrong only
#   at a POSITION — it agrees with the desired behaviour on every variable except
#   the first, which is a sub-domain no other rival in the battery leaves
#   attacked. "Subsumed by the same witness class" was also not true in the
#   operative sense: sharing a witness INPUT is not sharing a rejection, and the
#   two rivals return different values at inputs of length >= 2. Nothing about
#   the carrier blocked it — the rival is an ordinary loop-free fold over
#   `vars.drop 1` and its witness discriminates on the first build.
# DROPPED (AXIOM_TESTS): the nagini battery's AXIOM_TESTS validate the two payload
#   views against the real xarray Variable. This bundle consumes NO axiom — the
#   three observations are R-refinement input fields of `VarDesc`, validated by
#   axiom_check.py / conformance_check.py (mapping.md §3), NOT consumed axioms —
#   so there is no axiom lane to mirror; the G-PBT gate ignores AXIOM_TESTS
#   regardless.
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
#   loop in the impl (1 loop here, measure ``vars.length - i``). A rival that
#   loops without a measure is refused outright (``Decreasing annotations are
#   required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# CLAUSE / BINDER / POINT COVERAGE. The single obligation has one top-level
#   `ensures` clause C1 (`out = chunkInventory vars`), DEFENDED by two verifying
#   soundness positives (loop-free direct + loop local-bind) and the
#   admissibility case (C1's post-image discharged BY EVALUATION at an F2P-shaped
#   input), and ATTACKED by 7 reject rivals at 7 DISTINCT input points, moving
#   every sub-field of the `vars` binder:
#     weak-consults-accessible     [{none,        accessible := false}]
#     weak-never-contributes       [{some [(1,2)], accessible := true }]
#     weak-swap-pair-orientation   [{some [(5,7)], accessible := true }]
#     weak-drops-disagreement-check [{some [(1,2)]},{some [(1,3)]}]  (len 2)
#     weak-ignores-layout-read     [{some [(1,2)], accessible := true,
#                                    layoutReadable := false}]
#     weak-compares-repeated-dim   [{some [(0,4),(0,2)], accessible := true,
#                                    layoutReadable := true}]   (repeated dim)
#     weak-skips-first-variable    [{some [(1,2)], accessible := true }]  (index 0
#                                    of the scan — a POSITION, not a property)
#   `VarDesc.chunks` ranges over none / some (single pair, dim=block and dim≠block)
#   / a TWO-pair payload naming ONE dimension twice / two variables sharing a
#   dimension; `VarDesc.accessible` takes BOTH false (consults-accessible, the
#   descriptor-vs-values attack) and true (the others); `VarDesc.layoutReadable`
#   takes BOTH false (ignores-layout-read) and true (its default, everywhere
#   else); the list length takes 1 and 2, and the PAYLOAD length takes 1 and 2.
#   The two value-side fields are moved INDEPENDENTLY — accessible=false at
#   layoutReadable=true, and layoutReadable=false at accessible=true — so no rival
#   can be rejected by confusing one for the other; likewise the repeated-dimension
#   point is taken at layoutReadable=true so it cannot be confused with the layout
#   attack. Every load-bearing sub-domain of C1 (descriptor-only branch,
#   contribute, pair-orientation, fail-on-unreadable-layout, fail-on-disagreement-
#   BETWEEN-variables, overwrite-WITHIN-a-variable, scan-starts-at-index-0) is
#   attacked. pts = 7.
#
# WHAT THE GOLD-SIDE HALF OF THE WITNESS CHECK ACTUALLY ATTESTS TO, measured on
#   this bundle rather than assumed. Every reject case's witness is refuted
#   against a VERIFYING POSITIVE from this battery, not against the frozen impl,
#   and the record says so (`witness_subject`, `gold_stuck_screen: reduction`).
#   The frozen impl's `while`-loop `…Exec` does not reduce in the kernel, so its
#   `decide` is stuck for EVERY claim: rebuilding each witness against the frozen
#   file and rebuilding the SAME file with the claim FLIPPED (`≠` -> `=`) both
#   exit 1, both with `Tactic `decide` failed for proposition`. The frozen side's
#   exit code therefore carries no information about the claim, exactly as the
#   gate's stuck screen detects. The discrimination is real but it is carried by
#   the fallback subject: against `pos-control-direct` (loop-free, kernel-
#   reducing, and independently required to VERIFY) the witness fails with
#   `Tactic `decide` proved that the proposition ... is false` — a SEMANTIC
#   refutation naming the concrete input — while the flipped claim there
#   ELABORATES (exit 0). That pair is what makes each rejection attributable to
#   C1, and it is the reason no case here should be re-aimed at the frozen impl.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (the postcondition's
#   Decidable instance does not auto-derive over the `while` loop; measured to
#   leave `Decidable (out = chunkInventory vars)` unsolved and the tester stuck
#   for both rival and gold). Every witness instead extracts the executable
#   program and refutes C1 directly against the TRANSPARENT `chunkInventory`:
#   each rival is loop-free so its `…Exec` reduces under `decide`, while gold's
#   `while`-loop `…Exec` stays stuck — so the same witness elaborates against the
#   rival and FAILS against gold. Each witness supplies its own
#   `DecidableEq (Except …)` (absent from the workspace), appended to both files.
#   No witness binds a hypothesis, so no consistency probe is needed. All six
#   checked with scripts/lean_verify.sh: rival no-error, gold `decide` error.
AXIOM_TESTS = []
