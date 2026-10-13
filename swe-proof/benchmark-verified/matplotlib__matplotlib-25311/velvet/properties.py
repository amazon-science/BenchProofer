"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25311 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct initHandler`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method that constructs a drag-interaction
handler's persisted object state, abstracted to a ``Handler`` over ``List Attr``):

  initHandler (useBlit supportsBlit : Bool) return (out : Handler)
    ensures persistable out                                 -- P1
    ensures surfaceReachable out                            -- P2
    ensures Attr.refHandle ∈ out.attrs                      -- P3
    ensures Attr.flag (useBlit && supportsBlit) ∈ out.attrs -- P4
    ensures Attr.flag false ∈ out.attrs                     -- P5
    ensures Attr.registration ∈ out.attrs                   -- P6
    ensures flagsExact out (useBlit && supportsBlit)        -- P7

The construction turns on WHICH tagged values the handler retains in the state
that would be written to a serialized stream, and whether the rendering surface
stays reachable without being retained. The four ``Attr`` tags plus the
``surfaceFromRef`` bit are the whole modeled carrier; every spec predicate is a
concrete ``def`` over them (empty ``axioms`` region — no opaque answer key to
echo, directive 8). The clauses decompose into independently-attackable
sub-behaviors:

  * PERSISTABLE (P1) — the non-serializable rendering surface is ABSENT from the
    retained state (``Attr.surface ∉ attrs``). THE discriminator: the pre-fix
    construction retained it directly, dragging it into the serialized stream.
  * SURFACE-REACHABLE (P2) — the surface stays obtainable: either derivable on
    demand from a retained reference (``surfaceFromRef = true`` AND the reference
    is retained) OR still stored directly. Dropping the surface WITHOUT providing
    the derived accessor makes the very next construction step unable to read it.
  * INVENTORY (P3, P4, P5, P6) — the full working state is retained: the
    reference to the dragged object, the effective mode bit (the conjunction of
    the two inputs), the cleared status bit, and the installed event
    registrations. These stop a "retain nothing" cheat from satisfying P1
    vacuously and pin the handler that is actually built.
  * FLAGS-EXACT (P7) — the ONLY boolean status/mode bits retained are the two the
    constructor sets; a handler that smuggles in any other status bit is a
    different, behaviorally wrong object (the callbacks read these bits).

TWO input binders, both free and both meaningful; the post-image must hold for
every value of each:
  * ``useBlit``      — the requested mode bit;
  * ``supportsBlit`` — the surface's capability bit.
The retained effective mode bit is their conjunction (P4/P7). There is NO
``require`` clause (the construction is total), so every witness input is
in-domain; binder coverage instead varies the two bits across the reject
witnesses so a rival that mishandled either input alone would be caught.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling already records
    this class as N/A (all its inputs are ints passed by value; there is no
    read-only ``Acc(x,1/2)`` input to overwrite). Lean/Velvet are referentially
    transparent a fortiori: the two inputs are immutable ``Bool`` values, the
    method declares no ``mut`` binder, and there is no heap or aliasing. No
    substitute probe is fabricated (per the porting map, this class is dropped).
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. Every clause is a
    concrete predicate over the handler's own retained values (empty ``axioms``
    region; no opaque callee). There is nothing to echo.
  * DIVERGENCE / NON-TERMINATION: INAPPLICABLE as a shipped reject case, and
    closed by the verifier rather than vacuous. The nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` case (its impl is straight-line), so there is
    nothing to port, and the frozen construction here is a straight-line ``do``
    block with no loop to make spin, so no divergence rival is written. "VACUOUS"
    is withdrawn as the reason, though: a rival owns the whole impl region and may
    splice a loop the frozen body does not have. Under this bundle's
    ``set_option loom.semantics.termination "total"`` a postcondition is claimed of
    ALL runs, not only terminating ones, so the verifier demands a decreasing
    measure on every loop AND discharges its descent; the option cannot drift from
    the file's ``open TotalCorrectness DemonicChoice``, because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` with body
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``.
  * PARTIAL-DOMAIN / VALUE / SUBSTITUTION — heavily exercised. Each rival gets
    the overall shape right and is correct on part of the domain but violates one
    clause (retain the surface, drop a genuine attribute, drop the accessor, or
    smuggle / mis-set a status bit).

WITNESS MECHANICS ON THIS BUNDLE. The spec carries quantified clauses (P7's
``∀ b`` and the ``∈`` / ``∉`` membership predicates), so
``prove_postcondition_decidable_for`` leaves unsolved ``Decidable`` goals and the
tester route (``derive_tester_for`` → ``…Tester args = false``) is UNAVAILABLE
here (measured: the tester's ``decide`` gets stuck on ``flagsExact`` /
``surfaceReachable`` / ``persistable``). Each witness instead refutes the
method's Hoare triple DIRECTLY at one concrete input:
``¬ triple True (initHandler u s) (fun out => P1 ∧ … ∧ P7)`` closed by
``unfold …; simp [triple, pure] <;> decide``. Checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its rival (EXIT 0 — the triple provably fails at
that input) and FAILS against the frozen solution (``decide`` proves the negated
proposition ``False``, EXIT 1 — gold satisfies the spec there), so each rejection
is a genuine spec refutation and not mechanical tactic breakage. The witness
heads bind nothing (literal inputs), so there is no consistency obligation.

Re-derived independently by the audit lane, all 16 builds (8 rivals × 2 subjects):
every witness exits 0 against its rival and 1 against the frozen solution, and
every gold-side failure is the SEMANTIC form ``Tactic `decide` proved that the
proposition False is false`` — the kernel reduced the claim and refuted it. No
gold-side failure is an unknown identifier, a type error, a stuck reduction
(``did not reduce to isTrue or isFalse``) or a timeout, so no rejection here rests
on a syntactic accident that would discriminate nothing.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the whole construction is concrete over ``List Attr``. Nothing in the proof rests
on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25311"
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

# The executable code of the impl region (the mutable-list build), verbatim.
# Every rival and reshape replaces THIS block; the surrounding comment lines and
# the -- impl-start / -- impl-end markers stay put, all inside the elided impl
# region, so the spec view is untouched.
_IMPL = (
    "    let mut attrs : List Attr := []\n"
    "    attrs := Attr.refHandle :: attrs\n"
    "    attrs := Attr.flag false :: attrs\n"
    "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
    "    attrs := Attr.registration :: attrs\n"
    "    return { attrs := attrs, surfaceFromRef := true }"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The FULL frozen proof body. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it untouched, so the wrong impl leaves
# an ensures goal unsolved and the rival MODULE fails to build — which is what
# expect="reject" requires. The witness, not the module build, is what attributes
# the rejection to the spec.
_PROOF = (
    "prove_correct initHandler by\n"
    "  loom_solve <;> simp_all [persistable, surfaceReachable, flagsExact]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl code replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl code replaced AND the proof retuned (for reshapes / admissibility)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- WITNESSES. The spec has quantified / membership clauses, so
# ---- `prove_postcondition_decidable_for` fails and the tester route is
# ---- unavailable (measured). Each witness refutes the method's Hoare triple
# ---- DIRECTLY at one concrete input, checked in a file whose `prove_correct`
# ---- block has been stripped so no tactic script can mask the verdict.
# ---- `triple`/`pure` come from the frozen `Velvet.Std` import; the head binds
# ---- nothing (literal inputs), so there is no consistency obligation.
def _witness(u, s):
    return (
        f"example : ¬ triple (l := Prop) (True)\n"
        f"    (initHandler {u} {s})\n"
        f"    (fun out => persistable out\n"
        f"      ∧ surfaceReachable out\n"
        f"      ∧ Attr.refHandle ∈ out.attrs\n"
        f"      ∧ Attr.flag ({u} && {s}) ∈ out.attrs\n"
        f"      ∧ Attr.flag false ∈ out.attrs\n"
        f"      ∧ Attr.registration ∈ out.attrs\n"
        f"      ∧ flagsExact out ({u} && {s})) := by\n"
        f"  unfold initHandler persistable surfaceReachable flagsExact\n"
        f"  simp [triple, pure] <;> decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — statement REORDER: build the same
    # retained state by prepending the four tags in a DIFFERENT order. Order is
    # irrelevant to the observed behavior (which values land in the serialized
    # stream), so every clause still holds; the frozen proof closes the
    # byte-identical obligation. Must verify, else SPEC-TOO-STRONG. Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-attr-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.registration :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "rationale": "structurally-different CORRECT impl: prepend the four "
        "retained tags in a different order. The observed behavior depends only "
        "on WHICH values are retained (the set written to the serialized stream), "
        "not their order, so persistable / surfaceReachable / every membership "
        "clause / flagsExact all still hold. The frozen `loom_solve <;> "
        "simp_all` closes the byte-identical obligation. Must verify; else the "
        "spec is over-fit to the exact construction order => SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — different CONSTRUCTION shape: assemble the
    # retained state as a single list literal instead of a mutable fold. Same
    # retained values, maximally different executable shape. The frozen proof
    # still closes it. Must verify. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-list-literal",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let attrs : List Attr :="
            " [Attr.refHandle, Attr.flag false,"
            " Attr.flag (useBlit && supportsBlit), Attr.registration]\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "rationale": "a second honest correct shape: build the retained state as "
        "one list literal rather than a mutable accumulate-and-prepend fold. "
        "Identical retained values, so all seven clauses discharge; the frozen "
        "proof closes the byte-identical obligation. Confirms the spec is not "
        "over-fit to the mutable-fold FORM. Must verify; else SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # ADMISSIBILITY — the nagini sibling's self-call establishes the precondition
    # admits a normal F2P-shaped input. This bundle carries NO `require` clause
    # (the construction is total), so the precondition-admission probe is
    # degenerate; the case is RE-AIMED at the residual admissibility risk on this
    # carrier — that the post-image is NON-DEGENERATE at an F2P-shaped input (the
    # blit-enabled handler): the fully-built state genuinely OMITS the surface
    # (persistable), keeps it reachable via the retained reference
    # (surfaceReachable), and carries exactly the two status bits (flagsExact) —
    # not a constant / empty collapse. An in-region `assert` pins all three at the
    # concrete built state; the impl is kept verbatim so the method's own
    # obligation still discharges, and the proof is retuned only to clear the
    # extra assert goal (elided from the spec view). The assert is LIVE (a false
    # claim leaves an unsolved goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-blit",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (persistable { attrs := [Attr.refHandle, Attr.flag false,"
            " Attr.flag true, Attr.registration], surfaceFromRef := true } ∧\n"
            "       surfaceReachable { attrs := [Attr.refHandle, Attr.flag false,"
            " Attr.flag true, Attr.registration], surfaceFromRef := true } ∧\n"
            "       flagsExact { attrs := [Attr.refHandle, Attr.flag false,"
            " Attr.flag true, Attr.registration], surfaceFromRef := true } true))\n"
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }",
            "prove_correct initHandler by\n"
            "  loom_solve <;> first"
            " | (simp_all [persistable, surfaceReachable, flagsExact]) | decide"),
        "rationale": "the post-image is NON-DEGENERATE at an F2P-shaped input (the "
        "blit-enabled handler): the fully-built state omits the surface "
        "(persistable), keeps it reachable through the retained reference "
        "(surfaceReachable), and carries exactly the two status bits "
        "(flagsExact) — so the obligation is neither a constant collapse nor "
        "vacuous. The in-region assert must discharge; the impl is kept verbatim "
        "so the method's own `ensures` discharges too. Must verify; else the "
        "modeled behavior is empty/degenerate.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each witness ELABORATES against the
    # rival and FAILS against gold (two real builds per case).
    # =====================================================================
    {
        "id": "weak-leak-surface",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug: retain the non-serializable rendering surface directly
        # in the persisted state. Every genuine attribute is still present, but
        # the surface now leaks into the serialized stream.
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    attrs := Attr.surface :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "this is the pre-fix construction: keep the live rendering "
        "surface stored directly as an attribute, so it lands in the retained "
        "state and is dragged into the serialized stream. The F2P asserts the "
        "backend surface's class name does NOT appear in the serialized figure "
        "stream; with the surface stored this FAILS (the object becomes "
        "impossible to persist). A verifying rival here would be a true "
        "verify-does-not-resolve break.",
        "rationale": "REJECT from P1 (persistable = `Attr.surface ∉ attrs`): the "
        "surface tag is retained, so persistable is false. Refuted at "
        "(useBlit,supportsBlit)=(true,true): the built state contains "
        "`Attr.surface`, so the triple's P1 conjunct fails while gold's holds.",
        "witness": _witness("true", "true"),
    },
    {
        "id": "weak-no-accessor",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the surface from the state (persistable holds) but provides NO
        # derived accessor and does not retain the surface either
        # (surfaceFromRef := false). The surface becomes unreachable.
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := false }"),
        "refinement": "the naive half-fix: stop retaining the surface but provide "
        "no derived accessor over the retained reference. The surface is then "
        "unobtainable — the very next construction step (which reads the "
        "surface's capability bit) and the drag callbacks raise on access, so "
        "the F2P errors rather than resolving. A verify-does-not-resolve break.",
        "rationale": "REJECT from P2 (surfaceReachable): with the surface neither "
        "retained nor derivable (surfaceFromRef=false), neither disjunct holds. "
        "Refuted at (false,true): gold sets surfaceFromRef=true so the first "
        "disjunct holds (reference retained), while the rival satisfies neither. "
        "Discrimination comes from the surfaceFromRef bit.",
        "witness": _witness("false", "true"),
    },
    {
        "id": "weak-drop-refhandle",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the reference to the dragged object. Surface absent (persistable
        # holds) but the reference is gone — AND surfaceReachable's first disjunct
        # requires the reference, so both P3 and reachability-via-reference fail.
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "a partial-domain rival that omits the reference to the "
        "dragged object from the retained state. The reconstructed handler cannot "
        "identify the object it repositions, and — since the surface is derived "
        "FROM that reference — the surface is no longer reachable either, so the "
        "pickle round-trip / rebind tests break. A verify-does-not-resolve break.",
        "rationale": "REJECT from P3 (`Attr.refHandle ∈ attrs`) — and P2, whose "
        "reference-derived disjunct also needs it. Refuted at (false,false): the "
        "built state has no refHandle, so P3 fails while gold's holds. "
        "Discrimination varies the first genuine attribute at the (false,false) "
        "input.",
        "witness": _witness("false", "false"),
    },
    {
        "id": "weak-drop-registration",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the installed event registrations. Surface absent, reference and
        # flags present, but the handler receives no events. P6 fails.
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "a partial-domain rival that omits the installed event "
        "registrations from the retained state. The reconstructed handler "
        "receives no pick/release events at all, so the drag interaction is dead "
        "and the pickle suite that exercises a rebound handler breaks. A "
        "verify-does-not-resolve break.",
        "rationale": "REJECT from P6 (`Attr.registration ∈ attrs`): the built "
        "state omits the registration tag. Refuted at (true,false): P6 fails "
        "while gold's holds. This input point also exercises the mixed-bit case "
        "(useBlit=true, supportsBlit=false → effective false).",
        "witness": _witness("true", "false"),
    },
    {
        "id": "weak-empty-state",
        "kind": "uniqueness",
        "expect": "reject",
        # The vacuous cheat: retain NOTHING. persistable holds trivially (surface
        # absent from []), but every inventory clause and reachability fail.
        "module": _impl(
            "    let attrs : List Attr := []\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "the vacuous cheat: retain nothing, which satisfies "
        "persistability trivially (the surface is absent from an empty state) "
        "without building the handler. Its faithful counterpart nulls the "
        "handler's entire persisted state, so there is no reference, no flags and "
        "no registrations — every constructor / rebind test fails. This is the "
        "exact 'drop everything to satisfy absence vacuously' attack the "
        "inventory clauses defend against.",
        "rationale": "REJECT from the inventory clauses P3/P4/P5/P6 (and P2's "
        "reference-derived disjunct): the empty state contains none of the "
        "retained tags. Refuted at (true,true): every membership conjunct fails "
        "while gold's holds.",
        "witness": _witness("true", "true"),
    },
    {
        "id": "weak-drop-status-bit",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the cleared drag-status bit (Attr.flag false). Surface absent,
        # reference/registration/effective-bit present, but the cleared status
        # bit is missing. P5 fails.
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag (useBlit && supportsBlit) :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "omit the cleared drag-status bit the constructor sets. The "
        "reconstructed handler starts with an undefined drag-status, so the drag "
        "callbacks (which read it before repositioning) misbehave. A "
        "verify-does-not-resolve break.",
        "rationale": "REJECT from P5 (`Attr.flag false ∈ attrs`): the built state "
        "omits the cleared status bit. Refuted at (true,true): with the effective "
        "bit true, `Attr.flag false` is genuinely absent (the effective and "
        "cleared bits differ), so P5 fails while gold's holds. The (true,true) "
        "input is what makes the two flags distinct, so P5 is not masked by P4.",
        "witness": _witness("true", "true"),
    },
    {
        "id": "weak-smuggle-status-bit",
        "kind": "uniqueness",
        "expect": "reject",
        # Retain `Attr.flag useBlit` in place of the effective bit. When
        # supportsBlit is false but useBlit is true, this smuggles in an enabled
        # mode bit the real constructor never sets — flagsExact rejects it.
        # NOTE (audit): P4 is NOT violated here. At (true,false) the effective
        # bit is false and `Attr.flag false` is still retained as the cleared
        # status bit, so `Attr.flag (useBlit && supportsBlit) ∈ attrs` HOLDS of
        # this rival (machine-checked: a P4-only refutation at (true,false) does
        # not elaborate against it). flagsExact/P7 is the sole violated clause;
        # P4 is attacked on its own by weak-drop-effective-bit below.
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.flag useBlit :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "a value-substitution rival that retains the RAW requested "
        "mode bit instead of its conjunction with the surface's capability. When "
        "the mode is requested but the surface cannot support it, this smuggles "
        "in an enabled mode bit the real constructor never sets — the callbacks "
        "read it and take the wrong drawing path (an enabled fast-path over a "
        "surface that cannot support it). A verify-does-not-resolve break.",
        "rationale": "REJECT from P7 (flagsExact) ALONE: at (true,false) the "
        "effective bit is false, but the rival retains `Attr.flag true`, which "
        "flagsExact forbids (it is neither false nor the effective value). "
        "Refuted at (true,false); gold retains only the false effective bit, so "
        "the clause holds of gold. Discrimination comes from the useBlit≠"
        "effective split. P4 is NOT violated (the cleared bit `Attr.flag false` "
        "coincides with the effective bit at this input, so the P4 membership "
        "still holds) — see weak-drop-effective-bit for the P4-only attack.",
        "witness": _witness("true", "false"),
    },
    {
        "id": "weak-drop-effective-bit",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the effective mode bit entirely, keeping the cleared status bit,
        # the reference and the registrations. This is the ONLY rival that
        # violates P4 and nothing else: at (true,true) the effective bit is true
        # and is genuinely absent, so P4 fails while P1/P2/P3/P5/P6/P7 all hold
        # (flagsExact is satisfied — every retained bit is still `false`).
        "module": _impl(
            "    let mut attrs : List Attr := []\n"
            "    attrs := Attr.refHandle :: attrs\n"
            "    attrs := Attr.flag false :: attrs\n"
            "    attrs := Attr.registration :: attrs\n"
            "    return { attrs := attrs, surfaceFromRef := true }"),
        "refinement": "a value-omission rival that never records the effective "
        "mode bit at all: the handler retains its cleared status bit, its "
        "reference and its registrations, but carries no record of whether the "
        "fast drawing path is enabled for this surface. The drag callbacks read "
        "that bit to choose their drawing path, so the reconstructed handler "
        "takes the wrong path (and an attribute lookup for it raises), breaking "
        "the drag interaction. A verify-does-not-resolve break.",
        "rationale": "REJECT from P4 (`Attr.flag (useBlit && supportsBlit) ∈ "
        "attrs`) ALONE. Refuted at (true,true), where the effective bit is TRUE "
        "and so distinct from the retained cleared bit: the built state has no "
        "`Attr.flag true`, so P4 fails while gold's holds. Machine-checked to be "
        "the unique violated clause (P1/P2/P3/P5/P6/P7 each hold of this rival), "
        "which is what makes it a clean single-clause probe of P4 — the "
        "(true,true) input is what stops P5's `Attr.flag false` from masking it.",
        "witness": _witness("true", "true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals — one of the sibling's rival
# comments (b) is documented as CORRECT and not emitted) plus an AXIOM lane
# (dropped: G-AX's job).
#
# This bundle models the SAME purely-functional core — constructing the
# handler's persisted object state — over `Handler`/`List Attr` instead of the
# sibling's `List[int]` object-identity carrier with a `contains` membership
# predicate. The sibling's postcondition (P0 result ownership, P1 read
# preserved, P2 surface absent, P3..P7 genuine attrs present) maps onto this
# bundle's clauses, PLUS this carrier adds two clauses the sibling's int model
# could not express: `surfaceReachable` (the derived-accessor requirement) and
# `flagsExact` (the status-bit closure). The value surface carries across; there
# is no permission surface on either side.
#
#   sibling case                 -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-local-reshape            -> pos-list-literal              PORTED (re-shaped)
#   pos-genuine-reorder          -> pos-attr-reorder              PORTED
#   admiss-fts-input             -> admiss-f2p-blit               PORTED (re-aimed)
#   weak-leak-surface            -> weak-leak-surface             PORTED (the pre-fix bug)
#   weak-drop-cid-release        -> weak-drop-registration        PORTED (partial-domain)
#   weak-drop-element            -> weak-drop-refhandle           PORTED (partial-domain)
#   weak-empty-state             -> weak-empty-state              PORTED
#   weak-return-fresh-empty      -> (none)                        DROPPED (see below)
#   rival (b) double-mask        -> (none)                        N/A (correct here too)
#   (no sibling)                 -> weak-no-accessor              ADDED (surfaceReachable)
#   (no sibling)                 -> weak-drop-status-bit          ADDED (P5, flag false)
#   (no sibling)                 -> weak-smuggle-status-bit       ADDED (flagsExact/P7)
#   (no sibling)                 -> weak-drop-effective-bit       ADDED (P4, audit)
#   AXIOM_TESTS (2 probes)       -> (none)                        DROPPED (G-AX)
#   frame-mutation               -> (none)                        VACUOUS
#
# PORTED (positives): pos-local-reshape assembled the SAME list through
#   intermediate locals — here the analogous "different construction, same
#   retained values" reshape is the single list literal (pos-list-literal).
#   pos-genuine-reorder emitted the state in a different order — here the four
#   tags are prepended in a different order (pos-attr-reorder). Both keep every
#   retained value, so the frozen `loom_solve <;> simp_all` closes the
#   byte-identical obligation (both verified out-of-band with real builds).
# PORTED-RE-AIMED (admissibility): the sibling asserts the precondition admits a
#   normal input. This bundle has NO `require` clause, so the probe is re-aimed at
#   post-image non-degeneracy: an in-region assert pins persistable +
#   surfaceReachable + flagsExact at an F2P-shaped (blit-enabled) built state, so
#   the modeled behavior is neither empty nor a constant collapse. Impl kept
#   verbatim; proof retuned only to clear the assert goal. Assert is live.
# PORTED (rivals): weak-leak-surface IS the sibling's discriminator attack (store
#   the surface) — rejected by persistable/P1. weak-drop-cid-release /
#   weak-drop-element port to weak-drop-registration / weak-drop-refhandle
#   (partial-domain omissions of a genuine attribute) — rejected by the
#   corresponding membership clause. weak-empty-state ports directly.
# DROPPED (weak-return-fresh-empty): the sibling's permission/ownership rival
#   computes the correct state locally but RETURNS a different empty list, testing
#   that the postcondition binds the RETURNED object. On this carrier the method
#   returns a single `Handler` value with no aliasing and no separate "ownership"
#   permission — a "compute-then-return-something-else" impl that returns an empty
#   Handler is observationally identical to weak-empty-state (the returned value
#   is all the spec sees). The ownership distinction the sibling's fractional
#   permission expressed does not exist on a referentially transparent carrier, so
#   this rival collapses into weak-empty-state and is not fabricated as a separate
#   case (per the porting map: not wrong on this carrier as a distinct rival).
#   DEMONSTRATED (audit, real builds, not merely argued): the counterpart rival
#   was written out — accumulate the full correct `attrs` into a local, then
#   `return { attrs := decoy, surfaceFromRef := true }` with `decoy = []` — and
#   each of the seven clauses was refuted against it separately. Its violated-
#   clause profile is P2,P3,P4,P5,P6 violated and P1,P7 satisfied: BYTE-FOR-BYTE
#   the profile measured for weak-empty-state. The discarded local is invisible to
#   the spec, which observes only the returned Handler, so the case would add a
#   second copy of an existing rival rather than a new probe. Kept dropped.
# N/A (sibling rival (b) double-mask): the sibling documents but does NOT emit it
#   (it is correct there). No counterpart is emitted here either.
# ADDED (weak-no-accessor): this carrier's `surfaceReachable` clause has no
#   sibling counterpart (the int model had no accessor notion). A rival that drops
#   the surface without providing the derived accessor is the only rival that
#   abuses the surfaceFromRef bit — rejected by P2.
# ADDED (weak-drop-status-bit, weak-smuggle-status-bit, weak-drop-effective-bit):
#   this carrier pins the cleared status bit (P5), the effective mode bit (P4) and
#   the status-bit closure (flagsExact/P7), none expressible in the sibling's int
#   model. weak-drop-status-bit attacks P5; weak-smuggle-status-bit attacks
#   flagsExact/P7 by retaining the raw requested mode bit instead of its
#   conjunction with the capability bit; weak-drop-effective-bit (added by the
#   audit) attacks P4 by omitting the effective mode bit outright. The split
#   matters: the smuggling rival does NOT violate P4 (at its (true,false) refuting
#   input the effective bit is false and coincides with the retained cleared bit,
#   so the P4 membership still holds), so without weak-drop-effective-bit P4 was
#   attacked only jointly with five other clauses by weak-empty-state. Each of the
#   two rivals' violated-clause set was machine-checked one clause at a time.
# DROPPED (AXIOM_TESTS): the sibling's two A-reference probes are G-AX's job; this
#   bundle declares no axioms and no deep-model references (the construction is
#   concrete over List Attr), so there is nothing to probe and the gate ignores
#   AXIOM_TESTS regardless.
# VACUOUS (frame-mutation): the sibling already records this class as N/A (all
#   inputs are ints by value; no read-only Acc(.,1/2) input). This backend is
#   referentially transparent and declares no `mut` binder, so there is no
#   read-only field to overwrite and no substitute probe. Not fabricated.
#
# BINDER / CLAUSE COVERAGE of the 8 reject witnesses. All FOUR input points in
#   {true,false}² are used, so both binders take both values and the effective bit
#   (useBlit && supportsBlit) takes both values; the (true,false) point
#   (useBlit≠effective) is what lets the flagsExact rival discriminate, and the
#   (true,true) point (cleared bit ≠ effective bit) is what lets the P4 and P5
#   rivals discriminate without one masking the other.
#
#   Per-clause attribution below is MACHINE-CHECKED, not asserted: for every
#   rival, each of the seven clauses was refuted separately at that rival's own
#   witness input, so each rival's violated set is measured rather than argued.
#
#     P1 persistable      — weak-leak-surface (sole violated clause)
#     P2 surfaceReachable — weak-no-accessor (sole), weak-drop-refhandle,
#                           weak-empty-state
#     P3 refHandle        — weak-drop-refhandle, weak-empty-state
#     P4 effective flag   — weak-drop-effective-bit (sole), weak-empty-state
#     P5 cleared bit      — weak-drop-status-bit (sole), weak-empty-state
#     P6 registration     — weak-drop-registration (sole), weak-empty-state
#     P7 flagsExact       — weak-smuggle-status-bit (sole)
#
#   Every clause therefore has at least one rival that violates IT AND NOTHING
#   ELSE, so no clause's attribution rests on a rival that breaks several at once.
#   weak-empty-state, which breaks P2..P6 together, is the deliberate vacuous-
#   cheat probe and is the sole evidence for no clause. Note P1 and P7 are the two
#   clauses weak-empty-state SATISFIES — absence is trivial in an empty state and
#   there is no retained bit to violate the closure — which is exactly why the
#   inventory clauses have to be pinned independently of it.
#
# SPEC-STRENGTH PROBES run by the audit and NOT emitted as cases (each was a real
#   build; none is a finding, so none needs a case):
#   * wrong impls that must be, and were, REJECTED: retain a constant enabled mode
#     bit ignoring both inputs; retain `supportsBlit` alone (ignoring the request);
#     retain the DISJUNCTION instead of the conjunction; retain the surface while
#     also exposing the derived accessor. Each left an unsolved `ensures` goal, so
#     the conjunction P4∧P7 pins the effective bit to exactly `&&` — neither input
#     alone, and no other boolean connective, satisfies it.
#   * correct reshapes that must, and do, VERIFY: the conjunction COMMUTED
#     (`supportsBlit && useBlit`, closed by adding `Bool.and_comm` to the frozen
#     simp set); the effective bit produced through an `if … then … else` on the
#     conjunction (closed by casing both binders first); a state carrying
#     DUPLICATE tags; and a state built by `++` append instead of `::` prepend
#     (the last two close under the frozen proof unchanged). So the spec is not
#     over-fit to the frozen construction's form, its list shape, or its
#     multiplicity — only to WHICH values are retained, which is the modeled
#     behavior. The two reshapes needing a retuned tactic script are tactic
#     sensitivity, not spec strength: the obligation is unchanged and closes.
AXIOM_TESTS = []
