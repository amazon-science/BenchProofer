"""properties.py — G-PBT falsification battery for django__django-12273 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct assignPrimaryIdentity`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the refutation SUBJECT — here the declared ``witness_reference``, since
the frozen solution cannot decide anything on this bundle; see WITNESS MECHANICS).

DEFENDED SURFACE (one contracted method):

  assignPrimaryIdentity (attrs : Store) (slots : List Slot)
      (value : Option Int) (pk : Nat) return (out : Store)
    ensures out = (fun k => if k = pk then value else writtenSlots attrs slots value k)  -- E1
    ensures out pk = value                                                              -- E2
    ensures ∀ l ∈ slots, l.isPrimary = false → out l.attr = value                       -- E3

``Store = Nat → Option Int`` is a record's attribute cells addressed by an
attribute identity (``Nat``); a cell holds ``none`` (unset / cleared) or
``some n``. ``Slot`` is one inherited-identity slot the record carries:
``attr`` is the cell that holds this identity, ``isPrimary`` flags whether the
slot coincides with the record's own primary cell (in which case it must NOT be
written separately — the dedicated primary write covers it). ``writeSlot`` /
``writtenSlots`` are TRANSPARENT ``def``s over the method's own inputs:
``writeSlot`` folds one slot in — a primary slot is left untouched, any other
slot's cell is set to ``value`` — and ``writtenSlots`` is the left-to-right fold
of the whole slot list. There is NO opaque answer-key oracle in any clause (the
``axioms`` region is empty), so pinning ``out`` to the fold is grounded in the
arguments, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. E1 (``out = fun k => if k = pk then value else
writtenSlots attrs slots value k``) is the whole functional pin: it fixes ``out``
at every cell — the primary cell ``pk`` takes ``value``, every non-primary slot's
cell takes ``value``, and every OTHER cell keeps its entry value (no spillover).
E2 (the primary cell) and E3 (the cascade to non-primary slots) are CONSEQUENCES
of E1: a rival can only violate E2 or E3 by ALSO violating E1. Every uniqueness
rival is therefore an E1 divergence, and each rival's rationale names in ADDITION
the structural clause (E2 / E3) — or the unchanged-frame half of E1 (no
spillover) — that its particular defect corresponds to, so all three top-level
clauses AND the frame half are named by some reject rationale.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
models the same operation as ``assign_identity(store, target, active, pk_idx,
value)`` mutating a full-permission ``store`` list while reading two read-only
metadata lists ``target`` / ``active`` at half permission. Here the store is the
functional ``attrs : Store``, the parallel metadata lists are fused into one
``List Slot`` (``active[j]==1`` ↔ ``¬ slots[j].isPrimary`` — the guard polarity is
inverted: nagini's ``active`` flags "cascade here", this carrier's ``isPrimary``
flags "do NOT cascade here, the primary write covers it"; ``target[j]`` ↔
``slots[j].attr``), and ``pk_idx`` ↔ the ``pk`` cell identity. The nagini
postcondition clauses map across as:
  * nagini (P1) ``store[pk_idx] == value``                       ↔ E2 (and E1 at ``pk``);
  * nagini (P2) ``∀j: active[j]==1 => store[target[j]]==value``  ↔ E3 (and E1 at each non-primary slot);
  * nagini (P3) unrelated slots unchanged (the frame)            ↔ E1's ``else`` arm (cells no slot names keep their entry value).

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame-mutation rivals (``frame-write-target`` and
    ``frame-write-active``) that WRITE through a read-only
    (``Acc(list_pred(.),1/2)``) reference to an input list and are rejected for
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent:
    ``attrs``, ``slots``, ``value``, ``pk`` are immutable values, this bundle
    declares NO ``mut`` parameter (the accumulator ``result`` is a fresh local),
    and there is no heap, aliasing, or permission system to subvert. There is no
    read-only input to overwrite, so the class is vacuous. No substitute probe is
    fabricated (reported in the footer, not faked). RE-DERIVED UNDER AUDIT rather
    than accepted: assigning to an input binder in the impl region was actually
    attempted, and it fails at the LANGUAGE level — "`slots` cannot be mutated,
    only variables declared using `let mut` can be mutated" — before any spec
    obligation is reached, so there is no verdict about this spec to be had. The
    omission stands, for that reason.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. E1's post-image is a transparent
    fold over the method's own arguments; there is no answer key to echo. The
    honest cheapest CORRECT impl (``return (fun k => if k = pk then value else
    writtenSlots attrs slots value k)``) is carried as a POSITIVE control — it
    doubles as proof the spec is not echo-vulnerable, since any WRONG store fails
    ``out k = …`` at some cell.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against E1. A rival can
    be right on part of the domain and wrong on a sub-domain: write only the
    primary cell with no cascade (the pre-patch bug), skip the first or last
    inherited slot, cascade a DERIVED value instead of ``value``, drop the primary
    write, invert the primary guard (write the slots that must stay untouched and
    skip the genuine ones), or over-cascade (write EVERY slot including the
    primary ones the frame pins unchanged).
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``slots.length - i``). A rival that
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

WITNESS MECHANICS ON THIS BUNDLE. The output type ``Store = Nat → Option Int`` is
a FUNCTION, and E1 is a function equality (E2/E3 quantify over ``Nat`` / over
``slots``), so the Velvet tester path (``prove_postcondition_decidable_for`` →
``derive_tester_for`` → ``…Tester args = false := by decide``) is DEAD: no
``Decidable`` instance exists over a ``∀ (k : Nat)`` / a function equality.

But E1's carrier IS transparent, and it holds at EACH cell. Each rival is written
LOOP-FREE, so its extracted program ``assignPrimaryIdentityExec`` — the
``NonDetT``-run of the impl — REDUCES fully under ``decide`` at a concrete input.
Each witness picks one concrete cell ``k`` and states, at one concrete input,

    (match assignPrimaryIdentityExec <attrs> <slots> <value> <pk> with
       | DivM.res r => r k | _ => none)
        ≠ (if k = pk then value else writtenSlots <attrs> <slots> <value> k)

i.e. the rival's own store at cell ``k`` DIFFERS from the transparent post-image
E1 demands there — a direct E1 violation the elaborator sees (E1 instantiated at
that single ``k``, which suffices to refute the function equality). No witness
binds a hypothesis — every input is a concrete literal that decides E1 at the
chosen cell — so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

THE SECOND SUBJECT IS THE DIRECT POSITIVE, NOT GOLD — corrected under audit.
The frozen solution CANNOT serve as the witness's refutation subject on this
bundle, and an earlier revision of this file claimed it did. Gold's body is the
``while`` loop, whose ``…Exec`` is well-founded recursion the kernel does not
reduce, so the gold-side build does NOT fail by refuting the claim: it fails by
STUCK REDUCTION. Re-measured with ``scripts/lean_verify.sh`` on all seven
witnesses, the gold build's error is verbatim

    Tactic `decide` failed for proposition … because its `Decidable` instance
    instDecidableNot did not reduce to `isTrue` or `isFalse`.
    After unfolding … reduction got stuck at the `Decidable` instance …

which is precisely the ``_STUCK_REDUCTION`` signature ``gates/pbt.py`` screens
for: an error the kernel produces for EVERY claim about gold regardless of truth,
so its exit code discriminates nothing. (Confirmed by the same measurement
against ``pos-control-local-reshape``, which also keeps the loop: STUCK too.)

So every reject case here names ``witness_reference`` = the LOOP-FREE direct
positive (``pos-control-direct``'s module, the impl ``return (fun k => if k = pk
then value else writtenSlots attrs slots value k)``). That impl shares the frozen
spec byte-for-byte and VERIFIES — both checked by the gate before it is used — and
an impl the verifier accepts cannot violate its own spec, so a genuine "the spec
is violated at this input" statement must still fail there. Being loop-free, its
``…Exec`` reduces, so the failure is a REAL verdict: re-measured, every
reference-side build fails with ``Tactic `decide` proved that the proposition …
is false`` — a semantic refutation of the concrete claim, not a stuck instance,
not an unknown identifier, not a type error, not a timeout.

Observed exit codes (audit re-run, ``scripts/lean_verify.sh``, one build each):
rival 0 / reference 1 (semantic) / gold 1 (STUCK, hence unusable) for all seven
original rivals and for the two rivals added under audit.

Naming the reference EXPLICITLY rather than leaving the gate to discover it: the
gate has a fallback that tries the battery's own positives when gold is stuck,
and the previous revision passed only through that fallback. That made the
attestation depend on manifest ORDER and on an undeclared rescue path, and it
recorded ``witness_subject`` as "gold cannot decide" while this file's prose
asserted gold had refuted the claim. Declaring the subject makes the evidence
match the record.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle declares no ``axiom``
(mapping.md §3: no consumed axiom, no deep-model reference — the layout facts the
direct model rests on are validated executably by G-AX, not here), and the G-PBT
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12273"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one -- impl-start ..
# ---- -- impl-end region and is unique in Solution.lean; both facts asserted at
# ---- load by _swap, so every edit keeps same_spec by construction) ----

# The single loop-body step: reshaped by the loop-preserving positive control.
_BODY = (
    "      let l := slots[i]!\n"
    "      result := writeSlot result value l\n"
    "      i := i + 1"
)

# The WHOLE executable body: the accumulator `while` loop that folds `writeSlot`
# over the slot list, then applies the dedicated primary write. Reshaped
# wholesale by the uniqueness rivals and the direct positive, which are written
# STRAIGHT-LINE (see WITNESS MECHANICS): the frozen `while` elaborates to
# well-founded recursion the kernel does not reduce, so a rival that KEPT the loop
# would have an `…Exec` as stuck as the frozen one and no witness could `decide`
# it. A loop-free rival's `…Exec` reduces.
_IMPL = (
    "    let mut result : Store := attrs\n"
    "    let mut i := 0\n"
    "    while i < slots.length\n"
    "      invariant i ≤ slots.length\n"
    "      invariant result = (slots.take i).foldl (fun g l => writeSlot g value l) attrs\n"
    "      done_with i = slots.length\n"
    "      decreasing slots.length - i\n"
    "    do\n"
    "      let l := slots[i]!\n"
    "      result := writeSlot result value l\n"
    "      i := i + 1\n"
    "    return (fun k => if k = pk then value else result k)"
)

# The frozen proof, verbatim. The loop-free direct positive retunes THIS block
# (elided from the spec view); the loop-preserving positive leaves it as-is.
# Rivals leave it as-is too — the rejection is carried by the witness, not the
# tactic script (a rival that reshapes the impl breaks this script, which is the
# DEFAULT outcome of reshaping and attributes nothing to the spec on its own).
_PROOF = (
    "prove_correct assignPrimaryIdentity by\n"
    "  loom_solve\n"
    "  case «invariant_2: result = (slots.take i).foldl (fun g l => writeSlot g value l) attrs» =>\n"
    "    have hi : i < slots.length := by omega\n"
    "    rw [invariant_2, writtenSlots_take_step attrs slots value i hi]\n"
    "  case «ensures_1: ∀ l ∈ slots, l.isPrimary = false → out l.attr = value» =>\n"
    "    intro l hl hp\n"
    "    have hhit := writtenSlots_hits attrs slots value l hl hp\n"
    "    by_cases hkpk : l.attr = pk\n"
    "    · simp [hkpk]\n"
    "    · simp only [hkpk, if_false]\n"
    "      simp only [writtenSlots] at hhit ⊢\n"
    "      simp_all\n"
    "  all_goals simp_all [writtenSlots]"
)

for _a in (_BODY, _IMPL, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


def _rival(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (loop-free).
    The frozen proof is kept: it breaks against the reshaped impl (the expected
    reject), and the witness supplies the attribution to the spec."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble + builder. E1 is a FUNCTION equality (the output is a
# ---- Store), not decidable, so the tester+`decide` path is dead; instead
# ---- extract the executable program and refute E1 at ONE concrete cell against
# ---- the TRANSPARENT post-image. Checked in a file whose `prove_correct` block
# ---- is stripped, so no tactic script can mask the verdict.
_EXTRACT = "extract_program_for assignPrimaryIdentity\n\n"


def _witness(attrs, slots, value, pk, key):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match assignPrimaryIdentityExec ({attrs}) ({slots}) ({value}) ({pk}) with\n"
        f"      | DivM.res r => r {key} | _ => none)\n"
        f"     ≠ (if ({key} : Nat) = {pk} then ({value} : Option Int)"
        f" else writtenSlots ({attrs}) ({slots}) ({value}) {key}) := by\n"
        "  decide\n"
    )


# ---- the witness's refutation SUBJECT (see WITNESS MECHANICS). Gold keeps the
# ---- `while` loop, so `decide` against it is STUCK for every claim and its exit
# ---- code discriminates nothing; the loop-free direct return is an impl of the
# ---- SAME frozen spec that VERIFIES and whose `…Exec` reduces, so a witness
# ---- fails there by real refutation. The gate re-checks both facts (shares the
# ---- frozen spec; verifies) before using it, so nothing is trusted here.
_DIRECT_PROOF = (
    "prove_correct assignPrimaryIdentity by\n"
    "  loom_solve\n"
    "  case «ensures_1: ∀ l ∈ slots, l.isPrimary = false → out l.attr = value» =>\n"
    "    intro l hl hp\n"
    "    have hhit := writtenSlots_hits attrs slots value l hl hp\n"
    "    by_cases hkpk : l.attr = pk\n"
    "    · simp [hkpk]\n"
    "    · simp only [hkpk, if_false]\n"
    "      simp only [writtenSlots] at hhit ⊢\n"
    "      simp_all\n"
    "  all_goals simp_all [writtenSlots]")

_DIRECT_IMPL = ("    return (fun k => if k = pk then value"
                " else writtenSlots attrs slots value k)")

# The `pos-control-direct` module, shared verbatim by that case and by every
# reject case's `witness_reference`.
_REFERENCE = _swap(_rival(_DIRECT_IMPL), _PROOF, _DIRECT_PROOF)


# A single `Slot` literal, spelled inline in each witness/rival.
def _slot(is_primary, attr):
    return ("{ isPrimary := %s, attr := %d }"
            % ("true" if is_primary else "false", attr))


# concrete literal store: every cell holds the same starting value.
def _const_store(v):
    return "fun _ => (%s : Option Int)" % v


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build and return the whole post-store DIRECTLY via the
        # transparent fold, no per-slot loop. E1 is literally `out = fun k => if k
        # = pk then value else writtenSlots attrs slots value k`, so this is the
        # cheapest HONEST correct impl — and, since the post-image is GROUNDED in
        # the arguments (not an opaque answer key), it doubles as proof the spec is
        # not echo-vulnerable (any WRONG store fails E1 at some cell). The loop is
        # gone, so the frozen proof's invariant/step case no longer applies; E1
        # closes by `rfl`, E2/E3 close from `writtenSlots_hits` exactly as in the
        # frozen proof.
        "module": _REFERENCE,
        "rationale": (
            "the post-image `fun k => if k = pk then value else writtenSlots attrs "
            "slots value k` is GROUNDED in the inputs (a total fold over the "
            "argument, no opaque answer key), so returning it directly is the "
            "honest cheapest CORRECT impl; E1 is literally that equality, so it "
            "MUST verify, else E1 is SPEC-TOO-STRONG. Maximally different from the "
            "gold forward scan (no loop at all), and doubles as the "
            "echo-non-vulnerability control (any wrong store fails E1). "
            "Re-expresses the nagini pos-locals positive's argument (a "
            "structurally-different correct impl) as a loop-free direct return."),
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the frozen forward-`while` fold but bind the stepped store
        # to a typed local before assigning it. Same value flow (`stepped =
        # writeSlot result value l`), different control shape; the frozen proof
        # still closes unchanged (the loop invariant and step lemma are untouched).
        # Ports the nagini pos-locals (read the slot into a local before the
        # guarded write).
        "module": _swap(
            _BASE, _BODY,
            "      let l := slots[i]!\n"
            "      let stepped := writeSlot result value l\n"
            "      result := stepped\n"
            "      i := i + 1"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the stepped "
            "per-slot store to a typed local before assigning it) must verify; the "
            "value flow is unchanged (`stepped = writeSlot result value l`) so the "
            "loop invariant `result = (slots.take i).foldl … attrs` and E1/E2/E3 "
            "still discharge and the frozen loop proof closes as-is. Ports nagini "
            "pos-locals: if it fails => SPEC-TOO-STRONG (over-fit to the "
            "inline-assign code form)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-single-inheritance. That case
    # established the read-only fractional-permission precondition and the two
    # quantified Requires on an F2P-shaped input. This method carries NO `require`
    # clause (the pre-conditions region is empty), so nothing could exclude a
    # normal input and the classic "a normal input is admitted" probe is vacuous.
    # Re-aimed at the residual admissibility risk on a total domain: that the
    # three-clause post-image is jointly SATISFIABLE by a gold-shaped computation.
    # The frozen impl discharging all three ensures IS that witness. MUST verify,
    # else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the assignment is total over every "
            "attribute store and slot list; the gold impl discharging all three "
            "ensures is the admissibility witness that the post-image (E1's "
            "functional pin plus the two consequences E2/E3) is jointly "
            "satisfiable. Near-trivial precisely because the precondition is empty. "
            "Re-aimed from the nagini admiss-single-inheritance, whose read-only "
            "fractional-permission half and quantified Requires have no counterpart "
            "on this referentially-transparent, precondition-free carrier. Else "
            "SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument for why its faithful real
    # patch would NOT resolve the F2P. All attack E1 (the functional pin); each
    # names the structural clause (E2 primary / E3 cascade / E1-frame no-spillover)
    # its defect corresponds to. Every input binder is varied across the reject
    # witnesses (value ranges over none and several ints; pk, the probed cell, the
    # starting store, isPrimary both false and true, and list length 0/1/2), so no
    # binder is pinned at a single value.
    # =====================================================================
    {
        "id": "weak-prepatch-no-cascade",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: write ONLY the primary cell, no cascade over the
        # inherited slots at all.
        "module": _rival(
            "    return (fun k => if k = pk then value else attrs k)"),
        "refinement": (
            "this is the pre-change behaviour verbatim: only the record's own "
            "primary cell is assigned and every inherited-identity cell keeps its "
            "old value. On a child with a distinct inherited identity, clearing the "
            "primary identity leaves the inherited cell still pointing at the "
            "original ancestor row, so persisting the record OVERWRITES that row "
            "instead of inserting a new one — the exact reported bug. Its faithful "
            "real patch is the unpatched repo, which does NOT resolve the F2P "
            "(test_create_new_instance_with_pk_equals_none)."),
        "rationale": (
            "REJECT from E1 via the CASCADE (E3): at a non-primary slot's cell E1 "
            "demands `value`, but this rival keeps `attrs`. Refuted at `attrs = "
            "const some 0`, one non-primary slot at cell 1, value `none` (the reset "
            "case the issue is about), pk 2, cell 1 — rival returns `some 0`, gold "
            "returns `none`. If it verified => SPEC-TOO-WEAK (admits the pre-patch "
            "bug). (Sibling: partial-prepatch.)"),
        "witness": _witness(_const_store("some 0"),
                            "[" + _slot(False, 1) + "]",
                            "none", 2, 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-last-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # Cascade over every inherited slot EXCEPT the last one (dropLast), then
        # write the primary cell. Correct on the primary cell and on every slot but
        # the final one.
        "module": _rival(
            "    return (fun k => if k = pk then value"
            " else writtenSlots attrs slots.dropLast value k)"),
        "refinement": (
            "a faithful patch that iterated all but the last inherited link would "
            "skip the deepest ancestor's identity cell; in a multi-level chain that "
            "cell keeps pointing at the original row so clearing the primary "
            "identity does not fully reset the record — the new-instance F2P fails "
            "for that chain. NOT resolve."),
        "rationale": (
            "REJECT from E1 via the CASCADE (E3): E1 pins the WHOLE fold, so "
            "dropping the last slot loses its write — at the final non-primary "
            "slot's cell the rival returns `attrs` where E1 demands `value`. "
            "Refuted at `attrs = const some 2`, TWO non-primary slots (cells 1 and "
            "3), value `some 9`, pk 5, cell 3 (the dropped last slot) — rival "
            "`some 2`, gold `some 9`. A length-2 input no other witness uses. "
            "(Sibling: partial-drop-last.)"),
        "witness": _witness(_const_store("some 2"),
                            "[" + _slot(False, 1) + ", " + _slot(False, 3) + "]",
                            "some 9", 5, 3),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-first-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # Cascade over every inherited slot EXCEPT the first one, then write the
        # primary cell. Correct when the genuine inherited link is not declared
        # first.
        "module": _rival(
            "    match slots with\n"
            "    | [] => return (fun k => if k = pk then value else attrs k)\n"
            "    | _ :: rest =>\n"
            "      return (fun k => if k = pk then value"
            " else writtenSlots attrs rest value k)"),
        "refinement": (
            "a faithful patch that skipped the first inherited link would, for a "
            "child whose FIRST declared link is the distinct inherited identity, "
            "never reset that cell — so persisting the record overwrites the "
            "ancestor row. The single-inheritance F2P (whose child's sole inherited "
            "link is that first slot) fails. NOT resolve."),
        "rationale": (
            "REJECT from E1 via the CASCADE (E3): E1 pins the fold including index "
            "0, so dropping the first slot loses its write — at a leading "
            "non-primary slot's cell the rival returns `attrs` where E1 demands "
            "`value`. Refuted at `attrs = const none`, one non-primary slot at cell "
            "7, value `some 4`, pk 0, cell 7 — rival `none`, gold `some 4`. A "
            "leading-slot point distinct from every other witness. (Sibling: "
            "partial-drop-first.)"),
        "witness": _witness(_const_store("none"),
                            "[" + _slot(False, 7) + "]",
                            "some 4", 0, 7),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-wrong-cascade-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Cascade a DERIVED value (value bumped by one) into the inherited slots
        # while the primary cell correctly takes `value`.
        "module": _rival(
            "    return (fun k => if k = pk then value else\n"
            "      (slots.foldl (fun g l => if l.isPrimary then g\n"
            "        else (fun j => if j = l.attr then value.map (· + 1) else g j))"
            " attrs) k)"),
        "refinement": (
            "a faithful patch that assigned a DERIVED value to the inherited cells "
            "would make the inherited identity disagree with the new primary "
            "identity; the ancestor foreign key no longer matches the child, so "
            "persisting writes an inconsistent / mis-joined row and the F2P "
            "assertions on the ancestor row fail. NOT resolve."),
        "rationale": (
            "REJECT from E1 via the CASCADE (E3): the non-primary cell must hold "
            "EXACTLY `value`, not a derived value. Refuted at `attrs = const none`, "
            "one non-primary slot at cell 1, value `some 5`, pk 2, cell 1 — rival "
            "`some 6`, gold `some 5`. Isolates that E3 pins the value itself, not "
            "merely that the cell was touched. (Sibling: partial-wrong-value.)"),
        "witness": _witness(_const_store("none"),
                            "[" + _slot(False, 1) + "]",
                            "some 5", 2, 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-primary-write",
        "kind": "uniqueness",
        "expect": "reject",
        # Cascade over the inherited slots correctly but OMIT the dedicated primary
        # write (no `if k = pk then value` override).
        "module": _rival(
            "    return (writtenSlots attrs slots value)"),
        "refinement": (
            "a faithful patch that cascaded to the inherited cells but dropped the "
            "record's own primary-cell assignment would leave the primary identity "
            "at its old value — clearing the primary identity would not actually "
            "clear the record's own id, so the identity is internally inconsistent "
            "and persistence misbehaves; both F2P tests assert the primary id was "
            "cleared. NOT resolve."),
        "rationale": (
            "REJECT from E1 via the PRIMARY cell (E2): E2 demands `out pk = value`, "
            "but with the override dropped the rival returns `writtenSlots attrs "
            "slots value pk`. Refuted at the primary cell with an EMPTY slot list "
            "(so the cascade is a no-op and only the primary write is at stake): "
            "`attrs = const some 0`, `slots = []`, value `some 5`, pk 2, cell 2 — "
            "rival `some 0`, gold `some 5`. The only witness with list length 0, "
            "isolating E2. (Sibling: partial-drop-pk.)"),
        "witness": _witness(_const_store("some 0"),
                            "([] : List Slot)",
                            "some 5", 2, 2),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-invert-primary-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # INVERTED guard: write the slots flagged PRIMARY (which the spec leaves to
        # the dedicated primary write / pins unchanged) and SKIP the non-primary
        # ones (which the spec cascades to).
        "module": _rival(
            "    return (fun k => if k = pk then value else\n"
            "      (slots.foldl (fun g l => if l.isPrimary then\n"
            "        (fun j => if j = l.attr then value else g j) else g)"
            " attrs) k)"),
        "refinement": (
            "a faithful patch with the primary-guard polarity flipped would touch "
            "the promoted-primary ancestor link (which must stay covered only by "
            "the primary write) and SKIP the genuine distinct inherited link; the "
            "multi-inheritance F2P fails because the real inherited cell is never "
            "reset while a cell that should be left to the primary write is "
            "separately overwritten. NOT resolve."),
        "rationale": (
            "REJECT from E1's FRAME half (no-spillover) AND the cascade: a PRIMARY "
            "slot whose cell differs from `pk` must keep its entry value under E1 "
            "(`writtenSlots` skips primary slots and the cell is not `pk`), but this "
            "rival writes `value` there. Refuted at `attrs = const some 1`, one "
            "PRIMARY slot at cell 4, value `some 7`, pk 0 (so cell 4 ≠ pk), cell 4 "
            "— rival `some 7`, gold `some 1`. The first witness with `isPrimary = "
            "true`, exercising the primary flag no false-flag witness reaches. "
            "(Sibling: partial-invert-guard.)"),
        "witness": _witness(_const_store("some 1"),
                            "[" + _slot(True, 4) + "]",
                            "some 7", 0, 4),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-over-cascade",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-CASCADE (drop the primary guard): write `value` into EVERY inherited
        # slot's cell regardless of the primary flag, then the primary write.
        "module": _rival(
            "    return (fun k => if k = pk then value else\n"
            "      (slots.foldl (fun g l =>"
            " (fun j => if j = l.attr then value else g j)) attrs) k)"),
        "refinement": (
            "a faithful patch that dropped the primary half of the guard would "
            "re-target the promoted-primary ancestor's own identity cell through "
            "itself — the multi-inheritance breakage the PR author reported "
            "('doesn't work for child models that inherit from multiple models … "
            "created other test failures'); a cell that must stay untouched is "
            "overwritten, breaking PASS_TO_PASS inheritance behaviour. NOT "
            "resolve."),
        "rationale": (
            "REJECT from E1's FRAME half (no-spillover): a PRIMARY slot's cell "
            "(distinct from `pk`) is pinned unchanged by E1, but dropping the guard "
            "writes `value` into it. Refuted at `attrs = const some 8`, one PRIMARY "
            "slot at cell 6, value `some 3`, pk 1 (so cell 6 ≠ pk), cell 6 — rival "
            "`some 3`, gold `some 8`. Distinct from invert-guard (different store, "
            "value, pk, cell, and over-cascade is CORRECT on non-primary slots "
            "where invert-guard is wrong). (Sibling: partial-over-cascade.)"),
        "witness": _witness(_const_store("some 8"),
                            "[" + _slot(True, 6) + "]",
                            "some 3", 1, 6),
        "witness_reference": _REFERENCE,
    },

    # ---- ADDED UNDER AUDIT. Both aim at sub-domains the seven ported rivals
    # ---- leave unattacked. Both were first built as attack-D SPEC-TOO-WEAK
    # ---- probes (does the frozen spec ADMIT them?); each was REJECTED, so
    # ---- neither is a spec hole, and each is kept as a rival because it pins a
    # ---- distinct part of E1 nothing else reaches.
    {
        "id": "weak-spill-unnamed-cell",
        "kind": "uniqueness",
        "expect": "reject",
        # Clobber a cell that NO slot names and that is not `pk`. Every ported
        # frame rival (invert-guard, over-cascade) spills only into a cell some
        # PRIMARY slot names, so E1's `else` arm was never probed at a cell the
        # slot list does not mention at all.
        "module": _rival(
            "    return (fun k => if k = pk then value else\n"
            "      if k = 99 then value else writtenSlots attrs slots value k)"),
        "refinement": (
            "a faithful patch that also assigned some unrelated attribute cell — "
            "an identity cell belonging to no inherited link and not the record's "
            "own primary cell — would corrupt a field the operation must not "
            "touch. Assigning the primary identity would silently overwrite "
            "unrelated data, so PASS_TO_PASS behaviour on every model with that "
            "field breaks while the reported defect itself is untouched. NOT "
            "resolve."),
        "rationale": (
            "REJECT from E1's FRAME half (no-spillover) at a cell OUTSIDE the slot "
            "list entirely: E1's `else` arm pins cell 99 to `writtenSlots attrs "
            "slots value 99 = attrs 99` because no slot names 99 and 99 ≠ pk, but "
            "this rival returns `value`. Refuted at `attrs = const some 0`, one "
            "non-primary slot at cell 2, value `some 6`, pk 3, cell 99 — rival "
            "`some 6`, reference `some 0`. The only witness probing a cell no slot "
            "names, and the only one at cell 99 with pk 3 / slot cell 2. Added "
            "under audit; no nagini sibling (nagini's P3 frame is covered there by "
            "the permission rivals)."),
        "witness": _witness(_const_store("some 0"),
                            "[" + _slot(False, 2) + "]",
                            "some 6", 3, 99),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-skip-reset-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct for every `some n`, a total no-op for `value = none`. The
        # `value` binder is the one the ported rivals vary least meaningfully:
        # each is wrong for ALL values, so none isolates a value SUB-DOMAIN.
        "module": _rival(
            "    match value with\n"
            "    | none => return attrs\n"
            "    | some _ =>\n"
            "      return (fun k => if k = pk then value"
            " else writtenSlots attrs slots value k)"),
        "refinement": (
            "a faithful patch that special-cased the cleared/unset identity and "
            "returned early — treating 'no identity to assign' as 'nothing to do' "
            "— would be correct whenever a concrete identity is assigned and would "
            "do NOTHING in exactly the case the report is about: clearing the "
            "identity to make the record a new one. Neither the primary cell nor "
            "any inherited cell is reset, so persisting still overwrites the "
            "ancestor row. NOT resolve."),
        "rationale": (
            "REJECT from E1 via BOTH structural clauses (E2 primary and E3 "
            "cascade) on the `value = none` SUB-DOMAIN: E1 admits no case split on "
            "`value`, so an impl that is a no-op there violates it at the primary "
            "cell and at every non-primary slot cell. Refuted at `attrs = const "
            "some 4`, one non-primary slot at cell 8, value `none`, pk 6, cell 8 — "
            "rival `some 4`, reference `none`. Isolates a VALUE sub-domain: this "
            "rival is observably CORRECT at every `some n`, which no ported rival "
            "is, so it is the only case pinning that E1 is uniform in `value`. "
            "Added under audit; no nagini sibling."),
        "witness": _witness(_const_store("some 4"),
                            "[" + _slot(False, 8) + "]",
                            "none", 6, 8),
        "witness_reference": _REFERENCE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                   kind          -> here                         disposition
#   -----------------------------------------------------------------------------------------
#   pos-locals                    soundness     -> pos-control-local-reshape    PORTED
#                                                  (+ pos-control-direct        ADDED)
#   admiss-single-inheritance     admissibility -> admiss-gold-total           RE-AIMED
#   frame-write-target            uniqueness    -> (none)                       VACUOUS
#   frame-write-active            uniqueness    -> (none)                       VACUOUS
#   partial-prepatch              uniqueness    -> weak-prepatch-no-cascade     PORTED
#   partial-drop-last             uniqueness    -> weak-drop-last-slot          PORTED
#   partial-drop-first            uniqueness    -> weak-drop-first-slot         PORTED
#   partial-wrong-value           uniqueness    -> weak-wrong-cascade-value     PORTED
#   partial-drop-pk               uniqueness    -> weak-drop-primary-write      PORTED
#   partial-invert-guard          uniqueness    -> weak-invert-primary-guard    PORTED
#   partial-over-cascade          uniqueness    -> weak-over-cascade            PORTED
#   (no sibling)                  uniqueness    -> weak-spill-unnamed-cell      ADDED (audit)
#   (no sibling)                  uniqueness    -> weak-skip-reset-value        ADDED (audit)
#   AXIOM_TESTS (2 A-reference)   axiom         -> (none)                       DROPPED (G-AX lane)
#
# 12 velvet SPEC cases: 2 soundness, 1 admissibility, 9 uniqueness (7 ported + 2
# added under audit). Every nagini
# uniqueness rival that attacks a modeled clause is ported directly (the modeled
# surface here — the functional store, the slot list, the fold — carries every one
# of them faithfully). One soundness positive is ADDED (the loop-free direct
# return) alongside the ported local reshape, so the soundness surface is defended
# from both a maximally-different control shape and a minimal in-loop edit.
#
# PORTED (7 uniqueness + 1 soundness). Each nagini rival's ARGUMENT is carried
#   over verbatim in spirit; the mechanics are re-expressed over this carrier (the
#   functional `Store`, one `List Slot`, the `writeSlot`/`writtenSlots` fold)
#   rather than the sibling's mutable `store` list plus two parallel read-only
#   `target`/`active` lists. The guard polarity is inverted in the fusion
#   (`active[j]==1` ↔ `¬ slots[j].isPrimary`), so nagini's invert-guard/over-cascade
#   map to writing the PRIMARY slots / all slots here. Each reject case gains a
#   machine-checked refutation witness with no sibling counterpart (Viper
#   discharges the nagini postcondition; a tactic-proof backend needs the witness
#   to attribute the rejection to the spec, not to frozen-tactic breakage).
# ADDED (pos-control-direct): the maximally-different correct control here is the
#   loop-free direct return of the grounded post-image, which also serves as the
#   echo-non-vulnerability control (E1's post-image is grounded, so no wrong echo
#   verifies). The nagini pos-locals (local reshape) is ALSO ported verbatim as
#   pos-control-local-reshape, which keeps the frozen proof intact.
# RE-AIMED (admiss-single-inheritance -> admiss-gold-total): the nagini case
#   established a fractional-permission Requires and two quantified preconditions
#   on an F2P-shaped input. This method has no `require` (pre-conditions region
#   empty) and no heap permission, so that probe is vacuous; re-aimed at the
#   residual total-domain risk (post-image joint satisfiability), witnessed by the
#   frozen impl discharging all three ensures.
# VACUOUS (frame-write-target, frame-write-active): the nagini sibling's TWO
#   MANDATORY frame-mutation rivals WRITE through a read-only (`Acc(.,1/2)`)
#   reference to an input list and are rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent, this bundle declares NO `mut` binder on
#   any input (the accumulator `result` is a fresh local), and there is no heap,
#   aliasing, `Old`, or permission system. There is no read-only input to
#   overwrite and no frame clause to violate, so the class has no carrier analogue.
#   Omitted as a genuine carrier fact, NOT fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``slots.length - i``). A rival that
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
# DROPPED (AXIOM_TESTS): the nagini file carries two A-reference axiom probes
#   (ax-sound-set-pk-val, ax-contain-active-targets) validating the deep model ==
#   the real callee. That is G-AX's job; this gate ignores AXIOM_TESTS. mapping.md
#   §3 confirms this bundle declares no consumed axiom / deep-model reference in
#   the spec view, so there is nothing for the PBT lane to attack there.
#
# CLAUSE / BINDER / POINT COVERAGE. Three top-level ensures. E1 (`out = fun k => if
#   k = pk then value else writtenSlots attrs slots value k`) is the impl-
#   constraining pin and is attacked by ALL NINE rivals. E2 (`out pk = value`) and
#   E3 (`∀ l ∈ slots, ¬l.isPrimary → out l.attr = value`) are CONSEQUENCES of E1,
#   so no rival can violate them without violating E1; they are named as the
#   structural clause each rival ALSO corresponds to — E2 by weak-drop-primary-
#   write (drops the primary cell), E3 by the four cascade rivals (prepatch,
#   drop-last, drop-first, wrong-value), and the E1 FRAME half (cells no slot names
#   stay unchanged) by weak-invert-primary-guard, weak-over-cascade (both write a
#   PRIMARY slot's cell the frame pins unchanged) and weak-spill-unnamed-cell
#   (writes a cell NO slot names at all — the frame point the ported rivals never
#   reach). weak-skip-reset-value violates E2 AND E3 together, but only on the
#   `value = none` sub-domain. Both positives and the admissibility case defend all
#   three clauses (gold discharges E1/E2/E3).
#
#   The FOUR input binders are each varied across the NINE reject witnesses
#   (all distinct):
#     * weak-prepatch-no-cascade      attrs=const(some 0)  [Slot F 1]                value=none    pk=2 cell 1
#     * weak-drop-last-slot           attrs=const(some 2)  [Slot F 1, Slot F 3]      value=some 9  pk=5 cell 3
#     * weak-drop-first-slot          attrs=const(none)    [Slot F 7]                value=some 4  pk=0 cell 7
#     * weak-wrong-cascade-value      attrs=const(none)    [Slot F 1]                value=some 5  pk=2 cell 1
#     * weak-drop-primary-write       attrs=const(some 0)  []                        value=some 5  pk=2 cell 2
#     * weak-invert-primary-guard     attrs=const(some 1)  [Slot T 4]                value=some 7  pk=0 cell 4
#     * weak-over-cascade             attrs=const(some 8)  [Slot T 6]                value=some 3  pk=1 cell 6
#     * weak-spill-unnamed-cell       attrs=const(some 0)  [Slot F 2]                value=some 6  pk=3 cell 99
#     * weak-skip-reset-value         attrs=const(some 4)  [Slot F 8]                value=none    pk=6 cell 8
#   So `value` ranges over {none, some 3, some 4, some 5, some 6, some 7, some 9}
#   (the reset case AND several ints); `slots` ranges over empty / one / two
#   elements with `isPrimary` at BOTH false (seven witnesses) and true (invert,
#   over-cascade) and `attr` over {1,2,3,4,6,7,8}; `pk` ranges over {0,1,2,3,5,6};
#   `attrs` ranges over const none / some 0 / some 1 / some 2 / some 4 / some 8;
#   the probed cell ranges over {1,2,3,4,6,7,8,99}. No binder — and no `Slot`
#   field — is held fixed by every witness, so a rival mishandling only one binder
#   is caught.
#
#   The variation is MEANINGFUL, not two spellings of one point: every witness was
#   BUILT (see WITNESS MECHANICS), so at each listed cell E1's verdict provably
#   differs between the rival and the verifying reference impl. The two rivals
#   added under audit contribute the two points the ported seven could not reach:
#   a cell OUTSIDE the slot list entirely (cell 99, where E1's `else` arm reduces
#   to `attrs 99`), and a genuine VALUE sub-domain (a rival observably CORRECT at
#   every `some n` and wrong only at `none` — every ported rival is wrong for all
#   values, so none of them isolates `value` at all).
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (the output is a FUNCTION
#   `Store = Nat → Option Int` and E1 is a function equality, so no Decidable
#   instance exists). Every witness instead extracts the executable program and
#   refutes E1 at ONE concrete cell against the TRANSPARENT post-image: each rival
#   is loop-free so its `…Exec` reduces under `decide`. No witness binds a
#   hypothesis, so no consistency probe is needed.
#
#   CORRECTED UNDER AUDIT: gold is NOT the second subject and cannot be. Gold keeps
#   the `while` loop, whose `…Exec` is well-founded recursion the kernel does not
#   reduce, so the gold-side `decide` fails by STUCK REDUCTION (`… did not reduce to
#   `isTrue` or `isFalse``) — an error identical for every claim about gold, true or
#   false, which is exactly what gates/pbt.py `_STUCK_REDUCTION` refuses to count as
#   a refutation. An earlier revision of this file asserted gold refuted the claims;
#   that was false, and the cases passed only via the gate's undeclared fallback to
#   the battery's own positives. Every reject case now declares
#   `witness_reference` = the loop-free direct positive's module (`_REFERENCE`),
#   which shares the frozen spec and VERIFIES (both re-checked by the gate), and
#   whose `…Exec` reduces so the failure is a real verdict.
#
#   Audit re-measurement, scripts/lean_verify.sh, one build per file, all NINE
#   reject cases: rival exit 0 (elaborates); reference exit 1 with `Tactic `decide`
#   proved that the proposition … is false` (SEMANTIC refutation of the concrete
#   claim — not a stuck instance, unknown identifier, type error, or timeout); gold
#   exit 1 by stuck reduction, hence unused. `pos-control-local-reshape` also keeps
#   the loop and is also STUCK, so the direct positive is the only usable subject.
#
# ===========================================================================
# INDEPENDENT AUDIT RECORD (attacks run against this battery, not by its author).
#
# SPEC-TOO-WEAK probes (attack D) — NEW wrong impls aimed at what the ported
#   rivals leave unattacked. Each was built against the frozen spec; NONE
#   verified, so no spec hole was found:
#     * spill into a cell no slot names and which is not `pk`   -> rejected (exit 1)
#     * no-op on the whole `value = none` sub-domain            -> rejected (exit 1)
#     * guard on `l.attr = pk` instead of `l.isPrimary`         -> rejected (exit 1)
#   The first two are now shipped as weak-spill-unnamed-cell / weak-skip-reset-
#   value, each with a built witness (rival 0 / reference 1-semantic). The third
#   is NOT shipped: on this carrier it is a near-duplicate of the frame points
#   those two already pin, and every shipped witness should earn its builds.
#
# SPEC-TOO-STRONG probes (attack E) — NEW correct impls with a different shape.
#     * reverse-order fold (`writtenSlots attrs slots.reverse value`) VERIFIES
#       (exit 0). Every write writes the same `value`, so the post-store is
#       extensionally identical; the proof closes from `writtenSlots_spec` plus
#       `List.any_reverse` and `funext`. This is the strongest available evidence
#       that E1 pins the RESULT rather than the frozen traversal order: the spec
#       accepts an impl that visits the slots in the opposite direction.
#     * backward counting-down `while` scan: could NOT be closed (unsolved goals
#       relating `List.foldr … (drop i)` to the forward `take`-fold invariant).
#       Recorded as UNCERTAIN, NOT as a spec hole: the residual goals are the
#       missing fold-direction lemma (the frozen `pure` region provides
#       `writtenSlots_take_step` for the forward direction only), which is a PROOF
#       gap on the variant's own invariant rather than evidence the spec rejects a
#       correct impl — and the reverse-order positive above already shows the spec
#       is insensitive to traversal order.
#
# FRAME INEXPRESSIBILITY, re-derived rather than taken on trust. The two dropped
#   nagini permission rivals were re-attempted here by assigning to an input
#   binder inside the impl region (`slots := slots ++ [...]`, `attrs := fun _ =>
#   none`). Both fail at the LANGUAGE level, before any spec obligation is
#   reached: "`slots` cannot be mutated, only variables declared using `let mut`
#   can be mutated". That is an elaboration error, not a verdict about this spec,
#   so the class is genuinely inexpressible here — the omission is confirmed, and
#   confirmed for the right reason.
# ===========================================================================
AXIOM_TESTS = []
