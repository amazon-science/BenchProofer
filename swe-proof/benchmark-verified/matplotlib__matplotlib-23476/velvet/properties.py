"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23476 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct finalizeSnapshot`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method that finalizes the recorded resolution of
a serialized snapshot, keyed on an optional reference value:

  finalizeSnapshot (snap : SurfaceSnapshot) return (out : SurfaceSnapshot)
    ensures out.resolution = snap.baseline.getD snap.resolution   -- (C1)
    ensures out.baseline   = snap.baseline                        -- (C2)
    ensures out.payload    = snap.payload                         -- (C3)

The carrier ``SurfaceSnapshot`` bundles a ``resolution : Float``, an optional
``baseline : Option Float`` reference value, and an opaque ``payload : List Char``
remainder. Three INDEPENDENT top-level ``ensures`` clauses, each separately
attackable:

  * (C1) SELECTION — the persisted resolution is the reference value when one is
    present (``getD`` on ``some v`` yields ``v``) and the current resolution
    otherwise (``getD`` on ``none`` yields the default ``snap.resolution``). This
    is the load-bearing clause the fix introduces; its behaviour splits on the
    ``baseline`` binder (present vs absent), and the two sub-domains are attacked
    by two distinct rivals.
  * (C2) BASELINE FRAME — the reference value itself is preserved unchanged. A
    rival that overwrites it is refuted here even while doing C1 correctly.
  * (C3) PAYLOAD FRAME — the opaque remainder of the snapshot is preserved
    unchanged. A rival that disturbs it is refuted here even while doing C1
    correctly.

INPUT BINDERS of the spec predicate: ``snap.resolution`` (Float),
``snap.baseline`` (``Option Float`` — present/absent AND its value), and
``snap.payload`` (List Char). The reject witnesses drive ``baseline`` to BOTH
``some v`` (C1 present branch, C2) and ``none`` (C1 absent branch), and pin a
non-trivial ``resolution`` / ``payload`` where the clause depends on it, so no
binder is held at one value across the battery (pts = 4 distinct input points).

CARRIER NOTE — WHY THE TESTER + ``decide`` ROUTE IS DEAD, AND WHAT REPLACES IT.
Two of the three touched fields are ``Float`` (``resolution``, ``baseline``), and
``Float`` has no ``DecidableEq`` instance (IEEE-754 equality is not propositional
equality). So ``prove_postcondition_decidable_for finalizeSnapshot`` cannot be
discharged, ``finalizeSnapshotTester`` cannot be derived, and the sibling velvet
bundles' ``…Tester args = false := by decide`` route is unavailable on this
carrier. There is likewise no ``Float`` literal that ``decide`` can separate from
another (``some 42.0 ≠ some 294.0`` is not a kernel-decidable proposition here).

Instead each reject witness speaks DIRECTLY to the method's Hoare triple. The
frozen file opens ``TotalCorrectness DemonicChoice`` (line 7) under
``loom.semantics.termination "total"`` (line 4), so ``triple`` is the
total-correctness triple ``prove_correct`` discharges: the value clauses PLUS a
strict-decrease side-condition for every loop. (An earlier revision of this note
named ``PartialCorrectness`` here; that was wrong about the frozen file, and the
distinction is not cosmetic, since the two scopes select different loop rules.
See the DIVERGENCE bullet.) Each rival's body is
a single ``return`` (a ``pure``), so ``wp_pure`` reduces the weakest precondition
to a bare equality on the returned fields. The witness CONDITIONS on the carrier
(``snap.baseline = some v`` with ``v ≠ snap.resolution`` for the C1 present
branch and C2; ``snap.baseline = none`` with ``snap.resolution ≠ 0.0`` for the C1
absent branch; ``snap.payload = ['x']`` for C3) because no ``Float`` literal
decides the selection, and the residual equality (an inequality of two named
``Float``s, or a ``none = some v`` / ``[] = ['x']`` clash) refutes the targeted
clause against the rival. Against the frozen gold the same reduction lands on the
correct selection, so the closing step cannot fire and the witness FAILS on gold
— exactly the discrimination the gate requires. Every conditioned witness's
binders are jointly satisfiable (a snapshot whose recorded resolution differs
from its reference value is the F2P scenario itself), so the gate's consistency
probe cannot derive ``False`` from them; each witness was built the three
required ways (rival exit 0, gold exit ≠ 0, consistency probe exit ≠ 0) with
``scripts/lean_verify.sh``. No banned token (sorry/admit/native_decide/axiom/
opaque).

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — NOT vacuous as a spec surface here (it is the C2/C3 clauses),
    but the nagini FRAME-VIOLATION *rivals* are re-expressed as ordinary value
    breaks. The sibling's fractional-permission attack (overwrite a read-only
    half-permission input) has no analogue: this backend is referentially
    transparent, ``snap`` is an immutable value, the method declares no ``mut``
    binder, and there is no heap or aliasing. But the frame is still SPECIFIED
    (``out.baseline = snap.baseline``, ``out.payload = snap.payload``), so a rival
    that writes the wrong value into ``baseline`` or ``payload`` is refuted by
    those clauses directly — the same wrongness the nagini frame rivals encode,
    witnessed on the value carrier rather than the permission system.
  * DIVERGENCE / NON-TERMINATION: CLOSED BY THE SEMANTICS, NOT a spec hole (the
    label this bullet used to carry is withdrawn; its own measurements below
    contradict it), and this paragraph was
    REWRITTEN by the adversarial audit because every earlier revision argued the
    class from a semantics this bundle does not have. The old text asserted both
    that a diverging body "cannot be written" here and that the bundle runs under
    ``partial`` semantics. BOTH are false, measured: a loop-shaped body elaborates
    fine, and ``Solution.lean`` line 4 reads
    ``set_option loom.semantics.termination "total"`` (corpus-wide: 500/500 velvet
    bundles read ``"total"`` and 0 read ``"partial"``, so the ``partial`` reading the
    old text inherited from an internal findings doc has no referent at all; that doc
    is gone, and the option could not have disagreed with the file's
    ``open TotalCorrectness`` in any case, since the ``set_option`` elaborator itself
    runs ``openScope `TotalCorrectness``,
    ``Loom/MonadAlgebras/WP/Options.lean:169-186``).

    Under ``total`` the verifier DOES emit a termination obligation, so the naive
    diverging rival is genuinely REJECTED: a ``while True`` prefix with no measure
    fails with ``Decreasing annotations are required in total correctness
    semantics`` (EXIT 1). But the class still ships nothing, for two measured
    reasons that replace the false one:

    (a) NOT SHIPPABLE on witness mechanics. The no-measure rival's own file is
        UNCOMPILABLE — the missing-measure error is raised at the loop, not at the
        obligation — so no witness can elaborate against it. Confirmed with a
        trivially-true control witness (``example : (1:Nat) + 1 = 2 := by decide``):
        EXIT 1 against that rival, EXIT 0 against the frozen solution. A reject case
        whose witness cannot build against its own rival records
        ``witness-unproven``, an inconclusive outcome, not a rejection. The
        measure-carrying loop rival fares no better: its ``.run`` elaborates to an
        un-normalised ``forIn Lean.Loop.mk`` term and ``rw [wp_pure]`` fails with
        ``Did not find an occurrence of the pattern wp (pure ?x) ?post`` (EXIT 1),
        so no witness of this battery's shape can project it either.
    (b) NO MEASURE ESCAPE. An earlier revision of this note claimed that the
        ``total`` obligation is discharged by any measure at all, so that a
        diverging rival carrying ``decreasing (0 : Nat)`` VERIFIES and the class is
        therefore a spec hole. That claim is FALSE on this bundle and was retracted
        after re-measurement. A loop CARRYING a measure is rejected on the
        measure's own descent goal, not merely on the missing annotation:

          ``while 0 < 1`` / ``done_with 1 < 0`` / ``decreasing (0 : Nat)``
              -> EXIT 1, ``unsolved goals case «decreasing_1: (0 : Nat)» ⊢ 0 < 0``
          ``while k > 0`` / ``decreasing k`` over ``k := k + 1`` (INCREASING)
              -> EXIT 1, ``case «decreasing_1: k» ⊢ k + 1 < k``

        The mechanism is in the frozen file's own two header lines, and both are
        present here: ``set_option loom.semantics.termination "total"`` (line 4)
        makes Loom's option handler open the ``TotalCorrectness`` scope, and line 7
        opens it explicitly as well (``open TotalCorrectness DemonicChoice``).
        ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and
        emits ``⌜measure b' < measure b⌝`` as a real goal; only the
        ``PartialCorrectness`` twin takes a measure and discards it, and this file
        never opens that scope. So there is no annotation-only escape and no spec
        hole in this direction: an unreachable loop exit does not launder a wrong
        answer, because the rival never gets past its own descent obligation.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to structural
    projections of the method's OWN argument (``snap.baseline.getD
    snap.resolution``, ``snap.baseline``, ``snap.payload``); the ``axioms`` region
    is empty (mapping.md §3: no axiom, no A-reference). There is no opaque
    answer-key to echo; the positive controls do the selection honestly.

AXIOM lane: EMPTY. ``AXIOM_TESTS = []``. mapping.md §3 records this bundle has NO
axiom and NO A-reference — the changed op is modeled directly over values already
in the snapshot and calls no outside routine — so G-AX is skip. The nagini
sibling's AXIOM_TESTS re-run its deep-model fidelity probe; that is G-AX's job and
this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23476"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (one line), lying wholly
# ---- inside the single -- impl-start .. -- impl-end region and unique in the
# ---- file (both facts asserted at load). Every variant replaces exactly this
# ---- text, so same_spec holds by construction and the `prove_correct
# ---- finalizeSnapshot` obligation survives with a byte-identical statement.
_IMPL = "    return { snap with resolution := snap.baseline.getD snap.resolution }"
assert _BASE.count(_IMPL) == 1, "frozen impl region drifted; update _IMPL"


def _impl(new_body: str) -> str:
    """Build a variant by replacing ONLY the gold impl body."""
    return _swap(_BASE, _IMPL, new_body)


# ---- proof-body anchor: the frozen `prove_correct` tactic script. The velvet
# ---- spec view elides the tactic body (the obligation is the `method` header,
# ---- which lives in the spec view and is untouched), so replacing this text
# ---- keeps `markers.same_spec` and leaves the `prove_correct finalizeSnapshot`
# ---- obligation STATEMENT byte-identical. Used only by the admissibility case,
# ---- which must discharge a claim at a concrete input BEFORE closing the frozen
# ---- obligation verbatim.
_PROOF = "prove_correct finalizeSnapshot by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "frozen proof region drifted; update _PROOF"


def _proof(new_proof: str) -> str:
    """Build a variant by replacing ONLY the frozen tactic body."""
    return _swap(_BASE, _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and the carrier is `Float` (no DecidableEq), so a witness reaches the
# ---- post-image through the method's own partial-correctness `triple`: each
# ---- rival body is a single `return`, so `wp_pure` reduces the weakest
# ---- precondition to a bare field equality that the conditioning hypotheses
# ---- refute. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. No `axiom`/`sorry`/`native_decide`.
def _triple_witness(binders: str, post: str, tail: str) -> str:
    return (
        f"example {binders} :\n"
        f"    ¬ (triple True (finalizeSnapshot snap)\n"
        f"        (fun out => {post})) := by\n"
        "  simp only [finalizeSnapshot, triple]\n"
        "  intro h\n"
        "  have hcon := h trivial\n"
        "  rw [wp_pure] at hcon\n"
        f"{tail}"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify; else the postcondition is SPEC-TOO-STRONG on impl shape.
    # The frozen impl computes the selection with `Option.getD`; this reshape
    # splits the two cases with an explicit `match` on `snap.baseline`, returning
    # the reference value on `some` and the current resolution on `none`. These
    # denote the same result on every input (that IS the definition of `getD`), so
    # all three clauses still hold; `loom_solve` discharges the reshaped body with
    # no proof-body edit needed.
    # =====================================================================
    {
        "id": "pos-control-match-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    match snap.baseline with\n"
            "    | some r => return { snap with resolution := r }\n"
            "    | none => return { snap with resolution := snap.resolution }"),
        "rationale": (
            "a structurally-different but correct reshape: the optional-default "
            "selection is expanded into an explicit two-branch `match` (reference "
            "value on `some`, current resolution on `none`). This denotes exactly "
            "`snap.baseline.getD snap.resolution` on every input, so C1 still holds, "
            "and `baseline`/`payload` are copied through untouched so C2/C3 hold; "
            "`loom_solve` discharges it. If a faithful reshape failed to verify the "
            "spec would be SPEC-TOO-STRONG (over-fit to the `getD` code shape)."),
    },

    # =====================================================================
    # ADMISSIBILITY — REPAIRED UNDER AUDIT. The earlier revision shipped
    # `module = _BASE` (the frozen file byte-for-byte) and argued that "the frozen
    # impl verifying IS the admissibility witness". That case is HONEST but
    # DEGENERATE: it re-runs G-VERIFY, it varies nothing, and it cannot fail unless
    # the whole bundle is already broken — so the PRECOND-TOO-STRONG direction was
    # never actually tested. The method carries NO `require` (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the precondition"
    # probe is indeed vacuous; but the analogue on a TOTAL carrier is the obligation
    # being unsatisfiable at exactly an F2P-shaped input, and that is tested
    # DIRECTLY by discharging the post-image at that concrete input, by evaluation,
    # as a `have`, before closing the frozen obligation verbatim.
    #
    # The input is the F2P shape: a snapshot whose recorded resolution is a scaled
    # multiple (192.0) of a captured reference value (96.0), with a non-empty
    # remainder. The `have` claims all three clauses simultaneously at that point
    # (persisted resolution = 96.0, reference preserved, remainder preserved) and
    # closes them by reduction — so if the three-clause post-image were jointly
    # unsatisfiable at the scaled-with-reference point, or the selection were
    # unreachable there, this case FAILS => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.
    # The frozen `loom_solve` still closes the real obligation afterwards; only the
    # elided tactic body changes, so the `method` header and every `ensures` are
    # byte-identical and same_spec holds.
    #
    # The `have` is LIVE, not decoration: the same case claiming the pre-fix value
    # (`out.resolution = 192.0`, the scaled working value) instead of 96.0 FAILS to
    # elaborate — measured out-of-band, exit 1, `Application type mismatch: rfl ...
    # but is expected to have type ... .resolution = 192.0`. So a false claim about
    # this point does not close, which is what makes the passing build evidence.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-scaled-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof(
            "prove_correct finalizeSnapshot by\n"
            "  have hadm : triple True\n"
            "      (finalizeSnapshot { resolution := 192.0, baseline := some 96.0,\n"
            "                          payload := ['s'] })\n"
            "      (fun out => out.resolution = 96.0 ∧ out.baseline = some 96.0\n"
            "                  ∧ out.payload = ['s']) := by\n"
            "    simp only [finalizeSnapshot, triple]\n"
            "    intro _\n"
            "    rw [wp_pure]\n"
            "    refine ⟨rfl, rfl, rfl⟩\n"
            "  loom_solve"),
        "rationale": (
            "PASS SOURCE = finalizeSnapshot's own Hoare triple is SATISFIABLE at a "
            "concrete F2P-shaped input: a snapshot carrying a scaled working "
            "resolution (192.0) alongside a captured reference value (96.0) and a "
            "non-empty remainder. The in-region `have hadm` EVALUATES the method at "
            "that literal snapshot and closes all three clauses at once by reduction "
            "(persisted resolution = 96.0, reference value preserved, remainder "
            "preserved), so the post-image is demonstrated jointly satisfiable at "
            "exactly the point the behaviour turns on — not merely asserted. The "
            "input carries no `require`, so the operation is total over snapshots and "
            "the classic 'a normal input is admitted' probe is vacuous; this is its "
            "analogue on a total carrier. If the three clauses could not be jointly "
            "met at that input, `hadm` would not elaborate and this case would FAIL "
            "=> PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE. The frozen `loom_solve` "
            "still closes the real obligation afterwards and only the elided tactic "
            "body changes, so no `ensures` is weakened. The `have` is live: claiming "
            "the pre-fix value 192.0 there instead of 96.0 fails to elaborate."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # carrier-conditioned point and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary the `baseline`
    # binder over present/absent and pin `resolution`/`payload` where the clause
    # depends on it (see coverage footer).
    # =====================================================================
    {
        "id": "weak-keep-current-when-present",
        "kind": "uniqueness",
        "expect": "reject",
        # Persist the current resolution unchanged (the pre-fix behaviour). Correct
        # on the absent sub-domain (getD none = current resolution), WRONG whenever
        # a reference value is present and differs from the current resolution.
        "module": _impl("    return snap"),
        "refinement": (
            "this is exactly the pre-fix behaviour: the snapshot persists its "
            "current (transient, possibly device-scaled) resolution rather than the "
            "captured reference value. The failing scenario captures a reference "
            "resolution, then scales the working resolution, then round-trips the "
            "snapshot and observes the reference value restored; keeping the scaled "
            "value fails that observation, so a faithful counterpart would NOT "
            "resolve."),
        "rationale": (
            "REJECT from C1 `out.resolution = snap.baseline.getD snap.resolution` on "
            "the PRESENT branch: with `baseline = some v` the spec persists `v` but "
            "the rival persists the current resolution, so the two disagree whenever "
            "`v ≠ resolution`. If it verified ⇒ SPEC-TOO-WEAK (the selection "
            "unpinned). Refuted at a snapshot with `baseline = some v`, "
            "`v ≠ resolution`."),
        "witness": _triple_witness(
            "(snap : SurfaceSnapshot) (v : Float)\n"
            "    (hb : snap.baseline = some v) (hne : v ≠ snap.resolution)",
            "out.resolution = snap.baseline.getD snap.resolution",
            "  rw [hb] at hcon\n"
            "  simp only [Option.getD] at hcon\n"
            "  exact hne hcon.symm\n"),
    },
    {
        "id": "weak-wrong-default-when-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Select against the WRONG default: `getD 0.0` instead of `getD
        # snap.resolution`. Correct on the present sub-domain (the default is never
        # consulted when a reference value is present), WRONG on the absent
        # sub-domain — where the snapshot must keep its current resolution but this
        # substitutes a spurious constant.
        "module": _impl(
            "    return { snap with resolution := snap.baseline.getD 0.0 }"),
        "refinement": (
            "a counterpart that finalizes to a fixed default when no reference value "
            "was captured overwrites the resolution of every snapshot that was never "
            "reference-captured with a garbage constant, corrupting ordinary "
            "(non-scaled) snapshots. The passing scenarios that persist an untouched "
            "resolution would observe the wrong value, so it would NOT resolve the "
            "full set."),
        "rationale": (
            "REJECT from C1 on the ABSENT branch: with `baseline = none` the spec "
            "keeps `snap.resolution` (the `getD` default) but the rival substitutes "
            "the constant 0.0, so the two disagree whenever `resolution ≠ 0.0`. This "
            "moves the `baseline` binder to `none` — the sub-domain the "
            "keep-current rival gets right — so both branches of the selection are "
            "attacked. If it verified ⇒ SPEC-TOO-WEAK (the absent-branch default "
            "unpinned). Refuted at `baseline = none`, `resolution ≠ 0.0`."),
        "witness": _triple_witness(
            "(snap : SurfaceSnapshot)\n"
            "    (hb : snap.baseline = none) (hne : snap.resolution ≠ 0.0)",
            "out.resolution = snap.baseline.getD snap.resolution",
            "  rw [hb] at hcon\n"
            "  simp only [Option.getD] at hcon\n"
            "  exact hne hcon.symm\n"),
    },
    {
        "id": "weak-overwrite-baseline",
        "kind": "uniqueness",
        "expect": "reject",
        # Does the CORRECT selection (C1 holds) but ALSO discards the recorded
        # reference value (baseline := none). The frame clause C2 must reject it:
        # the reference value is not preserved. This is the value-carrier
        # re-expression of the nagini frame-violation rival that rewrote the
        # baseline entry.
        "module": _impl(
            "    return { snap with resolution := snap.baseline.getD snap.resolution,"
            " baseline := none }"),
        "refinement": (
            "the finalization must leave the recorded reference value exactly as "
            "supplied; a counterpart that also clears it destroys the idempotence "
            "the fix depends on — the next round-trip would have no reference value "
            "to restore to, so the resolution would drift again on the following "
            "cycle. It disturbs serialized state beyond the intended field and would "
            "NOT faithfully reproduce the fixed behaviour."),
        "rationale": (
            "REJECT from the FRAME clause C2 `out.baseline = snap.baseline`: the "
            "rival sets `baseline := none` while `snap.baseline = some v`, so the "
            "reference value is not preserved even though C1 (the selection) holds. "
            "If it verified ⇒ SPEC-TOO-WEAK (the baseline frame unpinned). Refuted "
            "at a snapshot with `baseline = some v`."),
        "witness": _triple_witness(
            "(snap : SurfaceSnapshot) (v : Float)\n"
            "    (hb : snap.baseline = some v)",
            "out.baseline = snap.baseline",
            "  rw [hb] at hcon\n"
            "  simp at hcon\n"),
    },
    # Added by the adversarial audit (attack D). weak-overwrite-baseline breaks C2
    # by collapsing the option's SHAPE (`some v` -> `none`), which `simp` refutes
    # from the constructor clash alone — so C2 was only ever shown to pin the
    # PRESENCE of the reference value, never its VALUE. This rival keeps the shape
    # (`some _`) and corrupts only the payload of the option, so its refutation must
    # go through `Option.some.injEq` to a genuine Float disequality. Measured: rival
    # EXIT 0, gold EXIT 1, consistency probe EXIT 1; and the type-revealing pair
    # separates the sides semantically (gold's hypothesis reduces to the reflexive
    # `some v = some v`, the rival's to the concrete false `... .baseline = some v`
    # with `baseline := some snap.resolution`).
    {
        "id": "weak-baseline-value-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct selection (C1 holds) and the reference value is still PRESENT
        # (the option stays `some _`, so no constructor clash), but it now records
        # the current resolution instead of the captured reference value. C2 must
        # reject it: the reference value must survive by VALUE, not merely by shape.
        "module": _impl(
            "    return { snap with resolution := snap.baseline.getD snap.resolution,"
            " baseline := some snap.resolution }"),
        "refinement": (
            "a counterpart that re-stamps the recorded reference value with the "
            "transient working value keeps a reference entry present but pointing at "
            "the wrong number, so the very next round-trip restores the transient "
            "value instead of the reference one and the drift the fix removes returns "
            "on the following cycle. It is strictly worse than clearing the entry, "
            "because the corruption is silent — the entry still looks captured — so a "
            "faithful counterpart would NOT resolve."),
        "rationale": (
            "REJECT from the FRAME clause C2 `out.baseline = snap.baseline` by VALUE "
            "rather than by shape: with `snap.baseline = some v` and "
            "`v ≠ snap.resolution` the rival returns `some snap.resolution`, so both "
            "sides are `some _` and the refutation must pass through "
            "`Option.some.injEq` to the underlying Float disequality. This is the "
            "sub-domain weak-overwrite-baseline cannot reach (that rival's `none` is "
            "refuted by the constructor clash alone, which pins only PRESENCE). If it "
            "verified ⇒ SPEC-TOO-WEAK (C2 pinning presence but not the value). "
            "Refuted at `baseline = some v`, `v ≠ resolution`."),
        "witness": _triple_witness(
            "(snap : SurfaceSnapshot) (v : Float)\n"
            "    (hb : snap.baseline = some v) (hne : v ≠ snap.resolution)",
            "out.baseline = snap.baseline",
            "  rw [hb] at hcon\n"
            "  simp only [Option.some.injEq] at hcon\n"
            "  exact hne hcon.symm\n"),
    },
    {
        "id": "weak-overwrite-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # Does the CORRECT selection (C1 holds) and preserves the baseline (C2
        # holds) but disturbs the opaque remainder of the snapshot (payload := []).
        # The frame clause C3 must reject it: everything else must survive
        # unchanged. Value-carrier re-expression of the nagini membership /
        # extra-write frame-violation rivals.
        "module": _impl(
            "    return { snap with resolution := snap.baseline.getD snap.resolution,"
            " payload := [] }"),
        "refinement": (
            "the finalization must touch only the recorded resolution; a counterpart "
            "that also rewrites the rest of the serialized snapshot changes every "
            "other persisted field, so the round-trip would reconstruct a different "
            "object than the one serialized — far beyond the single-field fix — and "
            "would NOT faithfully reproduce the fixed behaviour."),
        "rationale": (
            "REJECT from the FRAME clause C3 `out.payload = snap.payload`: the rival "
            "sets `payload := []` while `snap.payload` is non-empty, so the opaque "
            "remainder is not preserved even though C1 and C2 hold. If it verified ⇒ "
            "SPEC-TOO-WEAK (the payload frame unpinned). Refuted at a snapshot with "
            "`payload = ['x']`."),
        "witness": _triple_witness(
            "(snap : SurfaceSnapshot)\n"
            "    (hp : snap.payload = ['x'])",
            "out.payload = snap.payload",
            "  rw [hp] at hcon\n"
            "  simp at hcon\n"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness — including two frame-violation rivals
# and one non-termination rival) plus 2 AXIOM_TESTS. The sibling models the effect
# as an IN-PLACE MUTATION of a full-permission `Dict[int,int]` with rich frame
# postconditions (a universal "no key but key_dpi may change" clause, a membership
# clause) and a `MustTerminate` totality obligation. This backend models the same
# effect PURELY: the snapshot is an immutable `SurfaceSnapshot` value built freshly
# from `snap`, and the frame is stated as two explicit value clauses
# (`out.baseline = snap.baseline`, `out.payload = snap.payload`). There is no
# permission surface and no separate membership notion.
#
#   nagini case                         -> here                             disposition
#   -----------------------------------------------------------------------
#   pos-reorder-grounded                -> pos-control-match-branch          PORTED (reshaped)
#   admiss-poststate-reached            -> admiss-obligation-satisfiable-at-scaled-input
#                                                                            RE-AIMED
#   weak-drop-selection                 -> weak-keep-current-when-present    PORTED
#   weak-inverted-selection             -> (folded into weak-keep-current)   MERGED
#   partial-domain-uncond-original      -> weak-wrong-default-when-absent    RE-AIMED
#   frame-violation-writes-baseline     -> weak-overwrite-baseline           PORTED (value carrier)
#   frame-violation-adds-key            -> weak-overwrite-payload            RE-AIMED (value carrier)
#   weak-diverge-no-terminate           -> (none)                           SPEC-CLOSED (see below)
#   ax-deepmodel-soundness/containment  -> (none)                           DROPPED (G-AX lane)
#   (no sibling counterpart)            -> weak-baseline-value-swapped      ADDED BY AUDIT (attack D)
#
# 3 ported, 2 re-aimed, 1 merged, 1 known-hole, 2 axiom-lane dropped, 1 ADDED by
# the adversarial audit => 7 velvet SPEC cases (1 soundness, 1 admissibility,
# 5 uniqueness).
#
# ADDED BY AUDIT (weak-baseline-value-swapped): attack D asked what the existing
#   rivals leave unattacked and found C2 was pinned only up to the option's SHAPE.
#   weak-overwrite-baseline writes `none` over a `some v`, and its witness closes on
#   the constructor clash, so nothing in the battery showed C2 constrains the
#   reference value's NUMBER. The added rival keeps `some _` and swaps the value,
#   forcing the refutation through `Option.some.injEq` to a Float disequality. It
#   has no sibling counterpart (nagini's dict carrier has no `some`/`none` shape to
#   preserve separately from the entry's value); it is a carrier-specific near-miss
#   the port could not have inherited.
#
# MERGED (weak-inverted-selection): on nagini the "keep the live value" rival and
#   the "drop the selection" rival are distinct edits of a two-branch imperative
#   body. On this carrier both reduce to persisting `snap.resolution` unchanged
#   (`return snap` and `{snap with resolution := snap.resolution}` are the SAME
#   value), so they are observationally identical and would share a witness at the
#   same input for the same reason. Per the porting rule (two rivals may share a
#   witness only if they fail at the same input for the same reason — else one is a
#   redundant near-miss), only one is shipped (weak-keep-current-when-present). The
#   absent-branch sub-domain the sibling's inverted rival also touched is covered
#   distinctly by weak-wrong-default-when-absent.
# RE-AIMED (admissibility) — REPAIRED UNDER AUDIT: the sibling Asserts the body
#   reaches the post-state on an F2P-shaped input under its precondition. There is
#   no `require` here, so "a normal input is admitted" is vacuous. The first port
#   re-aimed this at joint satisfiability but WITNESSED it with `module = _BASE` —
#   the frozen file verbatim, which re-runs G-VERIFY and varies nothing, so the
#   PRECOND-TOO-STRONG direction went untested. Now witnessed the way the total-
#   carrier analogue requires: the obligation is discharged at a CONCRETE F2P-shaped
#   input (recorded resolution 192.0 scaled from a captured reference 96.0, non-empty
#   remainder) by evaluation, as a `have`, before `loom_solve` closes the frozen
#   obligation verbatim. Verified live by the flipped claim: asserting the pre-fix
#   value 192.0 at that point fails to elaborate.
# RE-AIMED (partial-domain-uncond-original -> weak-wrong-default-when-absent): the
#   sibling's rival unconditionally writes the "original" value, wrong on the
#   no-original sub-domain. Here the analogue attacks C1's ABSENT branch: select
#   against a spurious constant default (`getD 0.0`) instead of the current
#   resolution, correct when a reference value is present and wrong when absent —
#   the same partial-domain break, driving `baseline` to `none`.
# PORTED-VALUE-CARRIER (frame rivals): the sibling's two frame-violation rivals
#   attack a full-permission in-place mutation (rewrite the baseline entry;
#   introduce a new key). This backend has no heap, no aliasing, and no `mut`
#   binder, so the FRACTIONAL-PERMISSION mechanism is vacuous. But the FRAME
#   ITSELF is specified as value clauses (C2 baseline, C3 payload), so the same
#   wrongness — disturbing state beyond the resolution field — is re-expressed as
#   an ordinary value break: weak-overwrite-baseline (writes baseline, refuted by
#   C2) and weak-overwrite-payload (writes the opaque remainder, refuted by C3).
#   The nagini "adds a new key" membership rival maps to disturbing the payload,
#   since this carrier folds every non-resolution entry into `payload` (mapping.md
#   §2) rather than modeling membership separately. Not fabricated substitutes:
#   each is a real frame-clause violation with a machine-checked witness.
# CLOSED BY THE SPEC (weak-diverge-no-terminate): the sibling rejects a diverging
#   body via its `MustTerminate` totality obligation, and so does this bundle.
#   CORRECTED BY THE ADVERSARIAL AUDIT, twice over: every earlier revision of this
#   entry reasoned from `partial` semantics, and `Solution.lean` line 4 in fact
#   reads `set_option loom.semantics.termination "total"` while line 7 opens
#   `TotalCorrectness DemonicChoice` (corpus-wide: 500/500 velvet bundles read
#   `"total"`, 0 read `"partial"`). Re-derived under the semantics actually set,
#   and the second bullet retracts a claim this file used to make:
#     - the naive no-measure diverging rival IS rejected (`Decreasing annotations
#       are required in total correctness semantics`, EXIT 1), so it is not a hole;
#       but it is ALSO not shippable, because that error makes the rival's own file
#       uncompilable and no witness can elaborate against it (control: a trivially
#       true witness is EXIT 1 on that rival, EXIT 0 on gold => `witness-unproven`,
#       inconclusive, not a rejection);
#     - a diverging rival that CARRIES a measure is rejected too, on the measure's
#       own descent goal. This is the retraction: the entry used to say such a
#       rival VERIFIES because the obligation accepts a non-decreasing measure.
#       Re-measured on this bundle -- `while 0 < 1` / `done_with 1 < 0` /
#       `decreasing (0 : Nat)` gives EXIT 1, `unsolved goals case
#       «decreasing_1: (0 : Nat)» |- 0 < 0`, and an INCREASING `decreasing k` over
#       `k := k + 1` gives `case «decreasing_1: k» |- k + 1 < k`. So there is no
#       unreachable-exit laundering here and no spec hole to escalate: nothing
#       reaches the value clauses to launder.
#   The mechanism is `TotalCorrectness.WPGen.forWithInvariantLoop` (Loom), which
#   takes the `measure` and emits `measure b' < measure b`; the `PartialCorrectness`
#   twin is the one that takes a measure and drops it, and this file never opens
#   that scope. So the class is closed by the frozen spec, and unshippable only on
#   witness mechanics: the no-measure form breaks its own witness file, and any
#   loop-bearing form leaves a `forIn Lean.Loop.mk` term that defeats
#   `rw [wp_pure]`. Nothing is owed, and no `spec_holes` entry is filed.
# DROPPED (ax-deepmodel-soundness / ax-deepmodel-containment): the sibling's two
#   AXIOM_TESTS re-run its deep-model fidelity probe in Docker. mapping.md §3
#   records this bundle has NO axiom and NO A-reference (the changed op is modeled
#   directly over values already in the snapshot; `axioms` region empty), so G-AX
#   is skip. There is no axiom lane to mirror; this gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. All three independent `ensures` clauses are DEFENDED
#   (pos-control-match-branch + admiss-obligation-satisfiable-at-scaled-input
#   verify all three; the latter additionally pins them at a literal input) and each is
#   ATTACKED by some rival:
#     - C1 selection : weak-keep-current-when-present (present branch, baseline =
#                      some v), weak-wrong-default-when-absent (absent branch,
#                      baseline = none) — BOTH branches, so the `baseline` binder
#                      is varied over present/absent;
#     - C2 baseline frame : weak-overwrite-baseline (baseline = some v, refuted on
#                      the option's SHAPE) AND weak-baseline-value-swapped
#                      (baseline = some v with v ≠ resolution, refuted on the
#                      option's VALUE through `Option.some.injEq`) — so C2 is shown
#                      to pin the reference value's presence AND its number, which
#                      the shape-only rival alone did not establish;
#     - C3 payload frame  : weak-overwrite-payload  (payload = ['x']).
#   The five reject witnesses probe FIVE distinct input points (pts=5): each pins
#   a different binder off its trivial value (resolution ≠ v; resolution ≠ 0.0 with
#   baseline none; baseline some v; baseline some v with v ≠ resolution; payload
#   ['x']), so no binder is held at one value across the battery — a rival that
#   mishandled resolution, the presence of the baseline, the baseline's value, the
#   absent-branch default, or the payload is caught by a distinct witness. The
#   coverage reporter's `binders=1` is a structural count of the method's single
#   argument and does not see this; the meaningful variation is over `snap`'s three
#   projections, each of which changes the spec's verdict at the point it is pinned
#   (verified per rival: each variant's failing goal names exactly the clause and
#   projection the case claims).
#
# WITNESS METHOD NOTE: the tester + `decide` route is DEAD on this carrier — two of
#   the three touched fields are `Float`, which has no DecidableEq, so
#   `derive_tester_for` cannot be discharged and no `Float` literal is
#   kernel-decidable. Every witness instead refutes the method's own
#   partial-correctness `triple` via `wp_pure` on the rival's single `return`,
#   conditioning on the carrier (the reference-vs-current separation, or a concrete
#   payload) — the conditioning is jointly satisfiable (a scaled snapshot with a
#   captured reference value is the F2P scenario), so the consistency probe cannot
#   derive False. All five verified by three real builds (rival exit 0, gold exit
#   ≠ 0, probe exit ≠ 0).
#
# WITNESS ADMISSIBILITY (attack B′, run by the adversarial audit). None of the five
#   gold-side failures is a plain evaluation, so each was subjected to the forgery
#   pair rather than judged by reading. The gold-side errors are `Invalid field
#   `symm` ... hcon has type True` (the three C1/C2-value witnesses) and `unsolved
#   goals ... hcon : True ⊢ False` (the two shape/frame witnesses) — both the
#   "`simp` PROVED the equation for this impl" shape. Confirmed semantic, not
#   syntactic, two ways per case:
#     - TYPE-REVEALING build (replace the closing step with `exact (hcon : Nat)`):
#       on GOLD `hcon` prints as a REFLEXIVE equation (`some v = some v`,
#       `['x'] = ['x']`, or the record projection reduced to `(some v).getD ... =
#       (some v).getD ...`), i.e. the obligation genuinely holds there; on the RIVAL
#       it prints as a CONCRETE FALSE equation naming the rival's own wrong field
#       (`snap.resolution = (some v).getD snap.resolution`, `... .baseline = none`,
#       `... .payload = []`, `... .baseline = some snap.resolution`). The pair
#       differs, so gold's exit code carried information about the claim.
#     - FLIPPED-CLAIM build (assert the triple HOLDS instead of `¬`): gold fails
#       with `No goals to be solved` (the claim was already discharged — the
#       opposite disposition from the witness's own `hcon : True`), while each rival
#       fails with `unsolved goals` naming the residual false equation it cannot
#       close (`⊢ snap.resolution = v`, `⊢ 0.0 = snap.resolution`, `⊢ False`). The
#       error CHANGES when the claim changes on both sides, which is what makes the
#       exit codes evidence rather than coincidence.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (direct value model, G-CONF
#   not G-AX); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
