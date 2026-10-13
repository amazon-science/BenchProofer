"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24970 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text strictly inside
the ``-- impl-start`` / ``-- impl-end`` region is changed — the consumer spec
view elides that region, so ``markers.same_spec`` holds and the
``prove_correct resolveSlots`` obligation survives with a byte-identical
statement). ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  resolveSlots (paletteSize : Nat) (cells : List Cell) return (out : IndexRow)
    ensures slotsOf out = slotSeq paletteSize cells                      (C1)
    ensures (slotsOf out).length = cells.length                          (C2)
    ensures markersAdmitted out paletteSize                              (C3)

Two input binders. ``cells`` is the classified input row (each element one of
four classes); ``paletteSize`` is the ordinary-index count that fixes the three
reserved trailing markers. The result is an ABSTRACT index CONTAINER
(``IndexRow``) whose per-element indices are read out with ``slotsOf`` — see the
container-provenance note below for why the result cannot be the bare list of
index values. The three clauses pin three independent facets:

  (C1 value)  each element resolves to its own class's slot, in order — the
              transparent per-element resolution ``slotSeq paletteSize cells``,
              read out of the returned container. It pins the ROW the method was
              handed, not merely some row with the same resolved slots: the
              resolution separates the reserved ends from every ordinary index
              (see SELECTION ORDER below).
  (C2 shape)  the container reads back exactly one slot per input element.
  (C3 token)  the CONTAINER handed on must be one PRODUCED BY a reserved-marker
              assignment that COMPLETED on a container admitting every reserved
              index it writes AND representing values below zero, so that every
              selection step of the assignment is live in it.
              ``markersAdmitted`` is an unforgeable capability
              granted ONLY by the gated callee, for the very container that
              assignment produced, under its two-part legality precondition; it cannot be
              discharged by the resolved slot VALUES, which are identical
              whether or not the container admitted the markers, and it does not
              transfer to another container that merely reads back those values.

CONTAINER PROVENANCE — WHY THE RESULT TYPE IS ABSTRACT (the load-bearing repair
of this battery's earlier framing). The result used to be ``out : List Nat``,
with C1 pinning ``out`` to the resolved VALUES and C3 stated over that same
list. Under that framing the capability was a predicate on the index VALUES, so
it transferred to anything value-equal: an impl could carry out the admitting
assignment, DISCARD the container it produced, and hand on a list it built
itself,

    let wide <- assignReserved cells paletteSize true (paletteSize + 3)
    return slotSeq paletteSize cells                    -- value-equal copy

and the two returned expressions were provably EQUAL, so every clause satisfied
by the frozen impl was satisfied by this one too. It verified — and its faithful
Python counterpart does NOT resolve the failing test, because the container the
palette read consumes is then the input's own narrow one and the reserved-marker
store on it is exactly the conversion the test escalates to an error. The missing
OBSERVABLE was the container itself: a resolved index container is not the tuple
of index values it reads back — it also has the integer width those values are
stored in — so two containers reading back the same indices in different widths
are different objects, and a spec that observes only the values cannot say which
of them was handed on. The result is therefore an abstract ``IndexRow`` read
through the opaque ``slotsOf``, with two ways to come by one kept apart:
``assignReserved`` PRODUCES a container by carrying out the assignment (and only
that grants ``markersAdmitted``), while ``rowOf`` merely BUILDS one over values
already in hand (readback is all that is known of it — ``slotsOf_rowOf`` — so
nothing follows about the width it admits). The value-equal copy above is now
``return rowOf (slotSeq paletteSize cells)`` and is REJECTED on the residual
``markersAdmitted (rowOf (slotSeq paletteSize cells)) paletteSize`` goal, which
is the shape of every fabrication rival in the reject lane below.

CONTAINER SIGNEDNESS — WHY THE CONTAINER TAKES TWO INDEPENDENT EXTENTS (the
second load-bearing repair, at a different leg). Having made the container
abstract, the model still DESCRIBED one by a single ``Nat carrier`` meaning "it
admits the indices ``0 .. carrier-1``". That records only the container's
NON-NEGATIVE extent — whether the reserved MARKERS fit — and says nothing about
whether it represents values below zero at all. But the assignment is not one
store; it is three, and one of them selects on values BELOW zero (the
below-range step is a comparison against zero). In a container with no value
below zero that step selects NOTHING: every below-range element keeps whatever
the above-range step already stored, so the produced container reads back
``overSlot`` where the resolution says ``underSlot``. A width alone cannot
express the difference, and any width big enough for the markers discharged the
whole precondition — so an impl could route through the gated call on a
non-negative-only container of enormous width, satisfy every clause, and hand on
a container whose below-range elements are silently mis-resolved. The callee
therefore takes BOTH extents (``admitsNegative : Bool`` and ``carrier : Nat``)
and its contract gates on BOTH (``admitsNegative = true`` and
``paletteSize + 3 ≤ carrier``), each the exact boundary of one selection step.
The first is required for SOUNDNESS of the contract, not for convenience: on a
container that represents nothing below zero the readback claim
``slotsOf r = slotSeq paletteSize cells`` is simply false, so without that
obligation the axiom would be unsound. Rivals that keep the enormous width but
drop the signedness are REJECTED on the undischarged ``false = true``
verification condition, and a correct impl is free to pick any admitting width
it likes on a container that does represent values below zero (see the
positives).

SELECTION ORDER — WHY AN ORDINARY INDEX DOES NOT ALWAYS KEEP ITS VALUE (the third
load-bearing repair, on the OTHER axis: the classified ROW rather than the
container). C1 is stated over ``slotSeq paletteSize cells``, so it is only as
informative as that function is DISCRIMINATING. ``slotOf`` used to send
``.inPalette k`` to ``k`` for every ``k``. But the type's ordinary-index
constructor ranges over all of ``Nat``, so under that reading ``.inPalette
paletteSize``, ``.inPalette (paletteSize+1)`` and ``.inPalette (paletteSize+2)``
resolved to the same slots as ``.belowRange``, ``.aboveRange`` and ``.invalid`` —
``slotSeq`` was NOT injective, and an impl could RE-MAP the row across one of
those collisions before the gated call and still satisfy all three clauses. The
container machinery could not see it: the row is an ARGUMENT of the assignment,
not the container it runs in.

The missing OBSERVABLE is that the assignment is a SEQUENCE of selections over one
container, not a case analysis over disjoint classes. Its FIRST selection takes
every element whose index is not strictly below ``paletteSize`` — including an
index whose value coincides with one of the reserved markers — and stores
``overSlot`` over it, and no later selection takes it back. So an ordinary index
keeps its value ONLY while that value is strictly inside the palette, and
otherwise resolves exactly where an out-of-range-high element resolves. ``slotOf``
now reads that way, which makes ``underSlot`` and ``invalidSlot`` reachable from
their own class and from nowhere else, so C1 pins the row at both of those ends.
The one identification that REMAINS is the only one the real sequence also makes
(an ordinary index at or above ``paletteSize`` versus an out-of-range-high
element), and it is a positive control rather than a hole — see
``pos-benign-collision``, whose faithful counterpart resolves the graded suite in
full. Both directions are measured against real numpy in axiom_check.py
(``check_selection_order_dominance``, ``check_row_rewrite_divergence_witness``).

THE DISCRIMINATOR IS THE COMPLETING-ASSIGNMENT EFFECT, NOT A SLOT VALUE. The
public issue reports a behaviour with NO value footprint: the resolved slots are
byte-identical whether or not the reserved-marker writes overflow their carrier.
The observable difference is whether the carrier ADMITS the reserved markers,
independent of the input contents. That is why C3 exists and is stated over the
opaque ``markersAdmitted`` capability, obtainable only by routing the result
through the gated callee whose two-part precondition (``admitsNegative = true``
and ``paletteSize + 3 ≤ carrier``) must be discharged at the call site — a
behavioural consequence, not a returned constant.

CARRIER NOTE — THE OPAQUE / MONADIC BOUNDARY, and how a witness reaches the
post-image. This bundle is unusual: the modeled callee ``assignReserved`` is an
OPAQUE monadic action (``... → VelvetM IndexRow``), its result type is ABSTRACT,
and C3's ``markersAdmitted`` is an OPAQUE predicate over that type. Three
consequences shape the reject lane, each confirmed with real builds:

  * A rival that BYPASSES the callee (fabricates the result directly) has a
    reducible body: ``resolveSlots`` collapses to ``pure (rowOf <the fabricated
    list>)``. That is the entire witnessable reject surface, and it is enough: it
    is exactly the value-proxy attack C3 defeats — a container the impl builds by
    fiat rather than one produced by a completing admitting assignment.
    Value-wrong fabrications are discriminated by what the container reads back
    (C1 / C2, through ``slotsOf_rowOf``); the value-CORRECT fabrication is
    discriminated by CONDITIONING on the opaque token (C3).
  * A witness must NOT be stated over the extracted program ``resolveSlotsExec``.
    On the frozen impl that term is stuck on the opaque monadic callee, so it
    reduces for NO claim: the audit measured a true claim about gold's value, a
    false one, and the NEGATION of the false one all failing with the identical
    ``unsolved goals``. Gold's exit code would then carry no information about the
    claim, and a forged witness asserting gold is CORRECT at an agreement point
    would pass both halves of the gate's check. Every witness here is instead
    stated over the FROZEN OBLIGATION — the Hoare triple ``prove_correct`` closes —
    which gold PROVES (``loom_solve``) and a fabricating rival refutes
    (``rw [triple_pure]``), so the gold-side outcome tracks the claim. See the
    witness-builder block for the measurements.
  * A rival whose body still CONTAINS an opaque call cannot be refuted at the
    obligation level at all, and this is a property of the frozen axiom rather
    than a missing tactic: ``assignReserved_contract`` states only that the
    modeled ``get`` is ``≤ wp`` (an UNDER-approximation), so nothing in scope
    bounds ``wp`` from above and no theorem says such a program FAILS the
    obligation. Two families are affected — a call on a NON-ADMITTING container
    (too narrow: ``carrier = paletteSize``, resp. ``paletteSize + 2``; or
    non-negative-only: ``admitsNegative = false`` at any width), and a LAUNDER (an
    admitting call whose produced container is then discarded in favour of a
    built one). Both are still REJECTED, the first on the UNDISCHARGED legality
    verification condition (``Failed to parse an assertion without names:
    paletteSize + 3 ≤ <carrier>``, resp. ``... : false = true``) and the second on the residual
    ``markersAdmitted (rowOf …) paletteSize`` goal; both rejections are about the
    SPEC, not about tooling — see the accounting block for the measurements. What
    blocks shipping them as cases is the absence of a discriminating WITNESS, not
    the rejection. The spec-strength property they attack is defended from the
    fabrication side, where the body reduces to a ``pure`` and the token witness
    applies: ``reject-fabricate-value-correct`` is the SAME built container the
    launder hands on, reached without the decorative call.

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case ledger at
the foot of the file):
  * VALUE / PARTIAL-DOMAIN — APPLIES, and carries most of the reject lane. C1/C2
    are transparent structure over ``cells`` once the built container's readback
    is unfolded (``slotsOf_rowOf``); a fabrication right on part of the domain but
    wrong on a sub-region (a special class, a dropped element) is the natural
    falsifier and is witnessed by what the container reads back.
  * TOKEN / VALUE-PROXY — APPLIES, and is the load-bearing reject. A value-exact
    fabrication that never routed through an admitting assignment cannot obtain
    ``markersAdmitted``; witnessed by conditioning on the opaque token. This is
    the class the abstract result type exists for: under the previous
    ``out : List Nat`` framing the token was a predicate on VALUES and this whole
    class verified (container-provenance note above).
  * FRAME / PERMISSION MUTATION — VACUOUS here. This backend is referentially
    transparent; ``paletteSize`` / ``cells`` are immutable value inputs, this
    bundle declares NO ``mut`` parameter, and there is no heap, aliasing, or
    fractional permission to trip. The two nagini frame-mutation rivals (writes
    into the two half-permission read-only inputs) have no counterpart and no
    substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
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
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24970"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The gold impl's CODE block (the two executable lines
# ---- strictly inside -- impl-start / -- impl-end, after the descriptive
# ---- comment): it carries out the reserved-marker assignment on an admitting
# ---- carrier and returns its result. It lies wholly inside the single impl
# ---- region and is unique in Solution.lean (both asserted at load by _swap).
# ---- Every variant replaces exactly this block; the spec, the method signature
# ---- and the `prove_correct` header are untouched, so same_spec holds and the
# ---- obligation survives with a byte-identical statement.
_GOLD_CODE = (
    "    let out <- assignReserved cells paletteSize true (paletteSize + 3)\n"
    "    return out"
)
assert _BASE.count(_GOLD_CODE) == 1, "impl-body anchor drift — re-sync _GOLD_CODE"


def _variant(body):
    return _swap(_BASE, _GOLD_CODE, body)


# ---- proof-region anchor. The frozen `prove_correct` body. A positive control
# ---- may adjust the TACTIC SCRIPT (the proof region is elided from the consumer
# ---- spec view, and variant_scope permits it: the obligation header and every
# ---- `ensures` stay byte-identical, only the script that discharges them
# ---- changes). This matters for exactly one class of positive: a correct impl
# ---- whose returned EXPRESSION is a different-but-equal shape, where the frozen
# ---- script's final step no longer matches syntactically. Rewriting the script
# ---- is not a weakening — the same three clauses are still proven — and keeping
# ---- the tactic fixed would misreport tactic fragility as SPEC-TOO-STRONG.
_GOLD_PROOF = "prove_correct resolveSlots by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "proof anchor drift — re-sync _GOLD_PROOF"


def _variant_proof(body, proof):
    return _swap(_variant(body), _GOLD_PROOF,
                 "prove_correct resolveSlots by\n" + proof)


# ---- witness builders.
#
# AUDIT REPAIR — WHY THESE WERE REWRITTEN. Every witness in this battery used to
# state its refutation over the EXTRACTED PROGRAM (`resolveSlotsExec …
# ≠ DivM.res …`). Both halves of the gate's check passed, but the gold-side half
# carried NO INFORMATION about the claim, which the audit established with three
# builds at one input (paletteSize = 4, cells = [aboveRange]) against the frozen
# solution:
#
#     Exec = DivM.res (slotSeq 4 [aboveRange])   -- TRUE of gold     -> exit 1
#     Exec = DivM.res [999]                      -- FALSE of gold    -> exit 1
#     Exec ≠ DivM.res [999]                      -- TRUE of gold     -> exit 1
#
# all three with the same `unsolved goals ⊢ (NonDetT.run do let out ←
# assignReserved …) = DivM.res …`. The frozen impl's `…Exec` is STUCK on the
# opaque monadic callee, so it reduces for no claim whatever: a claim, its
# negation, and an absurd claim all fail identically. Gold's exit 1 therefore
# attested to irreducibility, not to gold satisfying the spec, and a forged
# "witness" asserting gold is CORRECT at an agreement point would have been
# recorded as a refutation just as readily. That is the hollow-SOUND shape the
# witness rule exists to exclude (the `_STUCK_*` screens in gates/pbt.py catch
# the loop-bearing variants of it; this opaque-callee variant slips past them
# because the error text is an ordinary `unsolved goals`).
#
# THE REPAIR: state the refutation over the FROZEN OBLIGATION ITSELF — the Hoare
# triple `prove_correct resolveSlots` discharges — instead of over the extracted
# program:
#
#     triple True (resolveSlots ps cells)
#       (fun out => markersAdmitted out ps ∧ (slotsOf out).length = cells.length
#                     ∧ slotsOf out = slotSeq ps cells)
#
# This is the frozen post verbatim (clause order as the obligation prints it), so
# a claim about it is a claim about the spec. Its virtue is that GOLD CAN PROVE
# IT: `unfold resolveSlots; loom_solve` discharges the triple at every input
# tested, because `loom_solve` reasons through the callee's `@[loomSpec]` WPGen
# rather than trying to REDUCE the opaque call. So on the frozen solution the
# gold-side outcome now TRACKS THE CLAIM, which is the property the old form
# lacked — measured for every case below under the STRICT forgery rule, i.e. with
# the tactic script held BYTE-IDENTICAL and only the claim flipped
# (`forgery_exit` = 0 in the audit payload: the flipped claim, asserting gold
# SATISFIES the obligation there, SUCCEEDS on gold at exit 0, while the refutation
# FAILS at exit 1 — and symmetrically the flipped claim FAILS on the rival, so
# neither side's exit code is a constant).
#
# A fabricating rival, by contrast, has `resolveSlots` reduce to `pure (rowOf
# <the fabricated list>)`, so `rw [triple_pure]` turns the triple into the post
# applied to that built container — a concrete proposition whose two value
# clauses `slotsOf_rowOf` unfolds and whose token clause the hypothesis refutes.
# Checked in a file whose `prove_correct` block is stripped, so no tactic script
# can interfere; no `axiom`/`sorry`/`admit`/`native_decide`.

# The frozen post-image at a concrete input, byte-for-byte the obligation's own
# three clauses in the order it states them. `_TRIPLE` is what every witness
# below asserts the rival FAILS and gold SATISFIES.
def _post(ps, cells):
    return (f"(fun out => markersAdmitted out {ps} ∧ "
            f"(slotsOf out).length = ({cells} : List Cell).length ∧ "
            f"slotsOf out = slotSeq {ps} {cells})")


def _triple(ps, cells):
    return f"triple True (resolveSlots {ps} {cells}) {_post(ps, cells)}"


# C1/C2 refutation: at a concrete input what the rival's returned container reads
# back fails the frozen post — either its VALUE differs from `slotSeq ps cells` or
# its LENGTH differs from `cells.length`. `rw [triple_pure]` is what reduces the
# obligation on a fabricating rival (its body is a `pure`), and `slotsOf_rowOf` —
# the one frozen fact about a BUILT container — is what turns `slotsOf (rowOf vs)`
# back into `vs` so the value computation can run; on gold that rewrite finds no
# `pure` because the body is the opaque call, and the flipped claim closes by
# `loom_solve` instead — the asymmetry that makes gold's exit code informative.
#
# The `first | <pure closer> | loom_solve` shape is deliberate and is what makes
# the forgery test pass under the STRICT rule (same script both sides, only the
# claim flipped). With the pure closer alone, gold failed for the refutation AND
# for its flip — both on the same `rewrite` error — so gold's exit code still said
# only "the body is not a `pure`". Offering `loom_solve` as the SECOND alternative
# changes nothing on the rival (the first branch closes it) while giving gold the
# route it can actually take, so on gold the refutation FAILS (exit 1) and the
# flipped claim SUCCEEDS (exit 0). Measured for the six rivals shipped at the time,
# rival / gold / flipped-on-gold / flipped-on-rival = 0 / 1 / 0 / 1 in every case.
# The two row-rewrite rivals added by the selection-order repair reuse this exact
# shape (their bodies are `pure`s too, over a rewritten row resolved into a BUILT
# container), and the same four-way measurement is re-run over every case by the
# gate itself.
_VALUE_CLOSER = ("  first\n"
                 "  | (rw [triple_pure]\n"
                 "     simp [slotsOf_rowOf, slotSeq, slotOf, overSlot, underSlot,\n"
                 "           invalidSlot])\n"
                 "  | loom_solve\n")


def _witness_value(ps, cells):
    return (f"example : ¬ ({_triple(ps, cells)}) := by\n"
            "  unfold resolveSlots\n"
            f"{_VALUE_CLOSER}")


# C3 refutation for a value-CORRECT fabrication: the value clauses cannot see it,
# so condition on the opaque token. Under the single hypothesis
# `¬ markersAdmitted (rowOf (slotSeq 5 [Cell.invalid])) 5` (satisfiable — the
# gate's consistency probe cannot derive False from it, measured: `simp_all made no
# progress`), the fabricated result reduces to exactly the BUILT container
# `rowOf (slotSeq 5 [Cell.invalid])` and so cannot carry the capability the
# obligation demands. Note what the hypothesis does and does not deny: it denies
# the capability of the container BUILT over those index values, and says nothing
# about the container the admitting assignment PRODUCES — which is why gold
# satisfies the same triple under the same hypothesis (`loom_solve`, exit 0),
# obtaining the capability from its call rather than from the hypothesis.
_WITNESS_TOKEN = (
    "example (hAdm : ¬ markersAdmitted (rowOf (slotSeq 5 [Cell.invalid])) 5) :\n"
    f"    ¬ ({_triple('5', '[Cell.invalid]')}) := by\n"
    "  unfold resolveSlots\n"
    "  first\n"
    "  | (rw [triple_pure]\n"
    "     simp [hAdm])\n"
    "  | loom_solve\n")


# C3 refutation at the EMPTY row — the input point that matters most for this
# bundle, since the modeled effect is independent of the input CONTENTS and so
# must be pinned where the row selects nothing at all. Both value clauses are
# blind there (`[]` is both the correct value and the correct length), so the
# capability is the only discriminator. The rival's guard is discharged first
# (`List.isEmpty_nil`, `if_true`) to expose the fabricated `pure (rowOf [])`;
# `slotSeq_nil` then rewrites the hypothesis to speak of `rowOf []` so it applies
# to the exposed goal.
_WITNESS_TOKEN_EMPTY = (
    "example (hAdm : ¬ markersAdmitted (rowOf (slotSeq 2 ([] : List Cell))) 2) :\n"
    f"    ¬ ({_triple('2', '[]')}) := by\n"
    "  unfold resolveSlots\n"
    "  first\n"
    "  | (simp only [List.isEmpty_nil, if_true]\n"
    "     rw [triple_pure]\n"
    "     rw [slotSeq_nil] at hAdm\n"
    "     simp [hAdm])\n"
    "  | loom_solve\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. Each keeps the `ensures` obligations and the frozen
    # `prove_correct resolveSlots by loom_solve` body VERBATIM; each still routes
    # the result through an ADMITTING assignment (carrier ≥ paletteSize + 3), so
    # `loom_solve` discharges the call-site legality and the three clauses
    # unchanged. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG. (All three verified with real builds during authoring.)
    # =====================================================================
    {
        "id": "pos-direct-call",
        "kind": "soundness",
        "expect": "verify",
        # Drop the intermediate `let out <- …; return out` and return the
        # admitting assignment directly. Same behaviour, different executable
        # shape; the returned action is definitionally identical.
        "module": _variant(
            "    assignReserved cells paletteSize true (paletteSize + 3)"),
        "rationale": "returns the admitting reserved-marker assignment directly "
                     "(no intermediate bind/return). Still carrier = paletteSize + 3, "
                     "so C1/C2/C3 discharge exactly as gold and the frozen loom_solve "
                     "obligation closes. Must verify; if not, the spec is over-fit to "
                     "the bind/return code shape (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-local-carrier",
        "kind": "soundness",
        "expect": "verify",
        # Compute the admitting carrier through a local `extra := 3` (the
        # verifier must still establish carrier = paletteSize + extra ≥
        # paletteSize + 3 to discharge the call's legality precondition).
        "module": _variant(
            "    let extra := 3\n"
            "    let out <- assignReserved cells paletteSize true (paletteSize + extra)\n"
            "    return out"),
        "rationale": "computes the admitting carrier through a local (extra := 3; "
                     "paletteSize + extra) — a different code shape that still proves "
                     "paletteSize + 3 ≤ carrier. Must verify; if not, the proof is "
                     "over-fit to the literal `paletteSize + 3` carrier form "
                     "(SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-wider-carrier",
        "kind": "soundness",
        "expect": "verify",
        # A faithful impl may pick ANY carrier that admits every reserved index,
        # not only the tight paletteSize + 3; paletteSize + 5 still satisfies the
        # legality precondition and yields the SAME slots (the callee's result is
        # slotSeq regardless of how much headroom the carrier has). This is the
        # real freedom the fix has (the signed-int cast admits far more than the
        # largest reserved index).
        "module": _variant(
            "    let out <- assignReserved cells paletteSize true (paletteSize + 5)\n"
            "    return out"),
        "rationale": "a faithful impl may pick any carrier admitting every reserved "
                     "index, not only the tight paletteSize + 3; paletteSize + 5 still "
                     "satisfies the legality precondition and grants the token with the "
                     "same slots. If it fails, the spec spuriously pins the carrier "
                     "WIDTH rather than admittance (SPEC-TOO-STRONG).",
    },

    {
        "id": "pos-respelled-row",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT-ADDED, then RE-AIMED by this repair. The three positives above all
        # take the callee's own result at the frozen carrier, so none of them moves
        # the VALUE clause off the syntactic form the callee's contract hands over.
        # This one does: it carries out the admitting assignment over a RE-SPELLED
        # row (`cells.map id`, the same row by `List.map_id`), so the contract
        # delivers `slotsOf r = slotSeq paletteSize (List.map id cells)` while C1
        # demands `slotsOf r = slotSeq paletteSize cells` — equal, but not
        # definitionally so. Measured: with the frozen script verbatim this FAILS
        # with the SOLE residual goal `⊢ slotsOf r = slotSeq paletteSize cells`
        # under the hypothesis about the mapped row (C3 already discharged, since
        # the container was genuinely produced by an admitting assignment) — i.e.
        # the frozen tactic, not the spec, is what rejects it. Bridging with
        # `List.map_id` closes all three clauses, so the SPEC admits the reshape.
        # Shipped with the bridged script: the obligation header and every
        # `ensures` are byte-identical.
        #
        # It REPLACES the earlier `pos-map-slotof`, which returned
        # `cells.map (slotOf paletteSize)` after an admitting call. That impl
        # DISCARDED the container the assignment produced and handed on one built
        # from index values, which is precisely the launder this repair closes: it
        # is now REJECTED, and correctly so (its faithful counterpart hands the
        # palette read a container that never received an admitting store). Keeping
        # it as a positive would have re-asserted the hole. The C1-spelling property
        # it was there for is defended here instead, on the argument side, where the
        # container's provenance is untouched.
        "module": _variant_proof(
            "    let out <- assignReserved (cells.map id) paletteSize true (paletteSize + 3)\n"
            "    return out",
            "  simp only [List.map_id]\n  loom_solve"),
        "rationale": "carries out the admitting assignment over a RE-SPELLED row "
                     "(`cells.map id`, equal to `cells` by List.map_id but not "
                     "definitionally), so the callee's contract delivers the resolved "
                     "slots of the mapped row while C1 demands them of `cells`. The only "
                     "positive that moves the VALUE clause off the form the contract "
                     "hands over; it verifies once the frozen lemma bridges the two "
                     "spellings, which is what shows C1 pins the resolved-slot FUNCTION "
                     "and not one spelling of it. If no proof could close it, C1 would be "
                     "over-fit to the callee's syntactic argument form "
                     "(SPEC-TOO-STRONG).",
    },

    {
        "id": "pos-benign-collision",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT-ADDED by the third repair, and the control that keeps that repair
        # from over-reaching. `slotOf` now sends an ordinary index that is NOT
        # strictly inside the palette to `overSlot`, because the first selection
        # takes it (see the CLASSIFICATION IMAGE section above). That leaves exactly
        # one identification standing: an out-of-range-high element and an ordinary
        # index at or above `paletteSize` resolve to the SAME slot. They must, and
        # this positive is the proof that the repair kept it. The impl carries out
        # the admitting assignment over the row in which every out-of-range-high
        # element has been RE-SPELLED as the ordinary index `overSlot paletteSize`
        # — a genuinely different row — and it MUST still verify, because the real
        # selection sequence cannot tell the two rows apart: the selection that
        # would take the rewritten element is the one that runs FIRST, so it takes
        # it anyway and stores the same slot. Measured independently: the faithful
        # counterpart of this exact reshape resolves the graded suite 253/253, so a
        # spec that rejected it would be SPEC-TOO-STRONG on a correct impl.
        # The script bridges the two spellings of the row (`grind [slotOf]` decides
        # `¬ (paletteSize + 1 < paletteSize)`); every `ensures` is byte-identical.
        "module": _variant_proof(
            "    let out <- assignReserved (cells.map (fun c => match c with "
            "| .aboveRange => .inPalette (overSlot paletteSize) | c => c)) "
            "paletteSize true (paletteSize + 3)\n"
            "    return out",
            "  loom_solve\n"
            "  all_goals simp_all [slotSeq_eq_map]\n"
            "  all_goals (intro a _; cases a <;> grind [slotOf])"),
        "rationale": "carries out the admitting assignment over a row in which every "
                     "out-of-range-high element is re-spelled as the ordinary index "
                     "overSlot paletteSize. The resolution identifies the two — it must, "
                     "since the selection that would take the rewritten element runs "
                     "FIRST and stores the same slot either way — so this reshape is "
                     "CORRECT and must verify. The control on the third repair: it pins "
                     "that the repair separated only the rows the real selection sequence "
                     "separates. If it fails, the resolved-slot function distinguishes "
                     "rows the sequence cannot (SPEC-TOO-STRONG on a measured-correct "
                     "impl).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a fabrication (bypassing the callee, so its
    # `…Exec` reduces) with a machine-checked refutation witness at a DISTINCT
    # concrete input, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test (test_index_dtype[uint8]).
    # =====================================================================
    {
        "id": "reject-fabricate-value-correct",
        "kind": "uniqueness",
        "expect": "reject",
        # THE value-proxy attack C3 defeats: BUILD a container over the
        # value-CORRECT index list (`return rowOf (slotSeq paletteSize cells)`)
        # WITHOUT routing through an admitting assignment. What the container reads
        # back is exactly right in value and length (C1/C2 hold via
        # `slotsOf_rowOf`), but no completing assignment produced it, so the
        # unforgeable `markersAdmitted` capability (C3) cannot be obtained. This is
        # the container the LAUNDER hands on too (an admitting call, then this same
        # built container returned instead of the produced one) — reached here
        # without the decorative call, which is what makes it witnessable.
        "module": _variant("    return rowOf (slotSeq paletteSize cells)"),
        "refinement": "computes the resolved slots directly and returns them, never "
                      "carrying out the reserved-marker assignment on an admitting "
                      "carrier. In the real pipeline the completing store on a widened "
                      "carrier is precisely what avoids the out-of-bound conversion "
                      "warning the failing test escalates to an error; an impl that "
                      "skips the admitting store (or omits the widening) leaves the "
                      "narrow-carrier store in place and would NOT resolve — even "
                      "though its resolved slot values are identical.",
        "rationale": "REJECT from C3 (markersAdmitted out paletteSize): the capability "
                      "is granted ONLY by an admitting assignment and cannot be "
                      "fabricated; a result the impl builds by fiat cannot carry it, "
                      "even value-exact. C1/C2 are satisfied, so ONLY C3 catches it — "
                      "the completing-assignment discriminator. Refuted at "
                      "paletteSize = 5, cells = [invalid], conditioning on the opaque "
                      "token. If it verifies, the value pin alone is treated as "
                      "sufficient (SPEC-TOO-WEAK).",
        "witness": _WITNESS_TOKEN,
    },
    {
        "id": "reject-skip-on-empty-row",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. The sharpest rival for THIS bundle, and the one the shipped
        # battery lacked. It does the admitting assignment on every non-empty row
        # — so it is correct, token and all, wherever any element exists — and
        # skips it only when the row selects nothing, fabricating `[]` there. That
        # is precisely the shape of the reported behaviour: the modeled effect is
        # independent of the input CONTENTS and fires even when no element is
        # selected, so an impl that guards the assignment on "is there anything to
        # assign?" is wrong exactly where the value facets (C1/C2) are blind —
        # `[]` IS `slotSeq paletteSize []` and its length IS 0. C1 and C2 hold on
        # the whole domain; only C3 catches it, and only at the empty row.
        # Measured (audit re-derivation, exit 1): rejected with TWO residual goals
        # under `if_pos : cells.isEmpty = true` —
        #   case «ensures_1: markersAdmitted out paletteSize»
        #     ⊢ markersAdmitted (rowOf []) paletteSize
        #   case «ensures_2: (slotsOf out).length = cells.length»
        #     ⊢ (slotsOf (rowOf [])).length = cells.length
        # Only the FIRST is a spec fact: it is the capability the fabricated
        # container cannot have. The second is a tactic artifact — it is TRUE on
        # this branch (`if_pos` forces `cells = []`, and `slotsOf (rowOf []) = []`
        # by slotsOf_rowOf) and the closer simply does not consume `if_pos`, so it
        # is left open rather than refuted. The rejection therefore still rests on
        # C3 alone; C2 is satisfied on the whole domain, just not discharged here.
        # An earlier spelling of this comment recorded a single goal
        # `⊢ markersAdmitted [] paletteSize`, which is neither the goal nor the
        # right term (the container, not its readback) — corrected by the audit.
        "module": _variant(
            "    if cells.isEmpty then\n"
            "      return rowOf []\n"
            "    else\n"
            "      let out <- assignReserved cells paletteSize true (paletteSize + 3)\n"
            "      return out"),
        "refinement": "guards the reserved-marker assignment on the row being non-empty, "
                      "carrying it out (admittingly) whenever any element exists and "
                      "skipping it otherwise. The modeled effect does not depend on which "
                      "elements the row selects — it is evaluated whenever the step runs "
                      "at all — so a faithful counterpart that conditions the widening on "
                      "having something to assign leaves the narrow-carrier path in place "
                      "for the no-element case and would NOT resolve, even though its "
                      "resolved slots are correct on every input including that one.",
        "rationale": "REJECT from C3 (markersAdmitted out paletteSize) at the EMPTY row. "
                      "This rival satisfies C1 and C2 EVERYWHERE — at cells = [] the "
                      "fabricated [] is exactly slotSeq paletteSize [] and has the right "
                      "length — so neither value clause can see it; the capability is the "
                      "only discriminator, and it is missing only at the input where no "
                      "element is selected. Refuted at paletteSize = 2, cells = [], "
                      "conditioning on the opaque token. Complements "
                      "reject-fabricate-value-correct, which attacks C3 on a NON-empty "
                      "row: together they pin that the capability is required "
                      "independently of the input contents. If it verifies, C3 is "
                      "obtainable on a sub-domain the effect does not actually cover "
                      "(SPEC-TOO-WEAK).",
        "witness": _WITNESS_TOKEN_EMPTY,
    },
    {
        "id": "reject-collapse-special",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain fabrication: resolve ordinary in-palette indices
        # correctly but collapse EVERY out-of-range / invalid class to slot 0
        # (the reserved markers are never materialised). Correct on a row of only
        # ordinary indices; wrong wherever a special class appears.
        "module": _variant(
            "    return rowOf (cells.map "
            "(fun c => match c with | .inPalette k => k | _ => 0))"),
        "refinement": "resolves ordinary indices correctly but sends every "
                      "out-of-range / invalid element to slot 0 instead of its own "
                      "reserved trailing slot. A faithful counterpart that never routes "
                      "out-of-range / invalid elements to the reserved rows mis-colours "
                      "them (and, having no admitting reserved-marker store, still "
                      "warns) — it would NOT resolve and would regress the dtype / "
                      "out-of-range PASS_TO_PASS paths.",
        "rationale": "REJECT from C1 (slotsOf out = slotSeq paletteSize cells): a special-class "
                      "element must resolve to its reserved slot (underSlot / overSlot / "
                      "invalidSlot), not 0. Refuted at paletteSize = 4, "
                      "cells = [aboveRange], where the model demands slot "
                      "overSlot 4 = 5 but the rival returns 0. If it verifies, C1 does "
                      "not pin the reserved-class resolution (SPEC-TOO-WEAK).",
        "witness": _witness_value("4", "[Cell.aboveRange]"),
    },
    {
        "id": "reject-constant-slots",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate fabrication: a constant list of zeros of the right length.
        # C2 (length) holds, but the slot VALUES are wrong for any non-zero
        # ordinary index (and every special class). Attacks C1 at an ordinary
        # element, disjoint from reject-collapse-special (which is correct here).
        "module": _variant("    return rowOf (List.replicate cells.length 0)"),
        "refinement": "returns a same-length list of zeros — every element addresses "
                      "palette row 0 regardless of its class. A faithful counterpart "
                      "would map every input to the same colour, resolving nothing "
                      "correctly; it would NOT resolve any dtype test.",
        "rationale": "REJECT from C1: an ordinary in-palette index k must resolve to k, "
                      "not 0. Refuted at paletteSize = 3, cells = [inPalette 2], where "
                      "the model demands slot 2 but the rival returns 0. C2 holds "
                      "(length preserved), so the value pin alone rejects it — an "
                      "ordinary-index point disjoint from reject-collapse-special. If it "
                      "verifies, C1 admits a constant-valued result (SPEC-TOO-WEAK).",
        "witness": _witness_value("3", "[Cell.inPalette 2]"),
    },
    {
        "id": "reject-drop-element",
        "kind": "uniqueness",
        "expect": "reject",
        # Length-facet fabrication: drop the leading element and resolve the rest
        # correctly. Correct only on a length-≤1 row; wrong whenever the row has
        # more than one element (C2 violated, and C1 with it).
        "module": _variant("    return rowOf (slotSeq paletteSize (cells.drop 1))"),
        "refinement": "resolves every element except the leading one, returning one "
                      "slot too few. A faithful counterpart would drop an input "
                      "element's colour lookup entirely, changing the output shape — it "
                      "would NOT resolve and would corrupt real colormap application on "
                      "any multi-element input.",
        "rationale": "REJECT from C2 ((slotsOf out).length = cells.length): dropping the leading "
                      "element makes the result one shorter than the input whenever the "
                      "row has more than one element. Refuted at paletteSize = 7, "
                      "cells = [invalid, belowRange] (length 2 vs 1), by taking "
                      "congrArg List.length of the assumed equality. The one rival "
                      "attacking the LENGTH facet; if it verifies, C2 is unpinned "
                      "(SPEC-TOO-WEAK).",
        "witness": _witness_value("7", "[Cell.invalid, Cell.belowRange]"),
    },
    {
        "id": "reject-swap-under-over",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. Every value rival above sends a special class to slot 0, so
        # all three are refuted by "a reserved marker is missing entirely" and none
        # tests that the three reserved markers are told APART. This one
        # materialises all three markers — the resolved list is a permutation of the
        # correct one, with exactly the right length and exactly the right multiset
        # of slots — but routes belowRange to the OVER marker and aboveRange to the
        # UNDER marker. mapping.md §2.1 records that the real assignment's ordering
        # (over before under) exists precisely so these two do not get confused, so
        # this is the facet that ordering protects, and it is the one facet the
        # shipped battery left unattacked.
        "module": _variant(
            "    return rowOf (cells.map (fun c => match c with "
            "| .inPalette k => k | .belowRange => overSlot paletteSize "
            "| .aboveRange => underSlot paletteSize "
            "| .invalid => invalidSlot paletteSize))"),
        "refinement": "materialises all three reserved markers but exchanges the "
                      "below-range and above-range ones, so an element off one end of "
                      "the range addresses the reserved row belonging to the other end. "
                      "A faithful counterpart mis-colours exactly the out-of-range "
                      "elements — swapping the two extreme reserved colours — and would "
                      "NOT resolve; it would also regress the out-of-range "
                      "PASS_TO_PASS paths, while a value-multiset or length check "
                      "cannot see it at all.",
        "rationale": "REJECT from C1 (slotsOf out = slotSeq paletteSize cells): belowRange must "
                     "resolve to underSlot paletteSize, not overSlot paletteSize. "
                     "Refuted at paletteSize = 6, cells = [belowRange], where the model "
                     "demands underSlot 6 = 6 but the rival returns overSlot 6 = 7. "
                     "Distinct from the three slot-0 fabrications: the length is right, "
                     "every reserved marker IS materialised, and the returned multiset "
                     "of slots is the correct one — only the pairing of class to marker "
                     "is wrong. If it verifies, C1 pins WHICH markers appear but not "
                     "which class each belongs to (SPEC-TOO-WEAK).",
        "witness": _witness_value("6", "[Cell.belowRange]"),
    },
    {
        "id": "reject-rewrite-below-to-index",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED by the third repair, and the case that attacks the leg that
        # repair closed. Every value rival above mis-resolves a class OUTRIGHT. This
        # one does not: it RE-SPELLS the below-range end of the row as the ordinary
        # index `underSlot paletteSize` and then resolves that row correctly. Under
        # the identity reading of an ordinary index the two rows had the SAME
        # resolved slots, so C1 could not see the rewrite at all and this rival
        # verified. It is now refuted by C1 alone: an ordinary index at or above
        # `paletteSize` is taken by the FIRST selection and resolves to `overSlot`,
        # so the rewritten row resolves DIFFERENTLY from the row it was handed —
        # which is exactly what the real selection sequence does to it
        # (axiom_check.py's row-rewrite witness measures the same divergence
        # end-to-end in numpy).
        "module": _variant(
            "    return rowOf (slotSeq paletteSize (cells.map "
            "(fun c => match c with | .belowRange => .inPalette (underSlot paletteSize) "
            "| c => c)))"),
        "refinement": "re-spells every below-range element as an ordinary element "
                      "carrying the index the below-range selection would have stored, "
                      "and then resolves that row. Its faithful counterpart writes that "
                      "index into the container BEFORE the selections run, where the "
                      "out-of-range-high selection — which runs first, and whose "
                      "predicate holds of that very index — takes it and stores the "
                      "OVER marker over it. So every below-range element addresses the "
                      "wrong reserved row and the out-of-range colouring changes; "
                      "measured on the graded suite, that counterpart does NOT resolve.",
        "rationale": "REJECT from C1 (slotsOf out = slotSeq paletteSize cells): the row it "
                      "resolves is not the row it was given, and the two do not resolve "
                      "alike. Refuted at paletteSize = 5, cells = [belowRange], where the "
                      "model demands underSlot 5 = 5 but the rewritten row resolves to "
                      "overSlot 5 = 6. Distinct from every rival above: it materialises a "
                      "reserved marker for the right class and gets the length right, and "
                      "the ONLY reason it is wrong is that an ordinary index at or above "
                      "paletteSize does not keep its value. If it verifies, C1 pins the "
                      "resolved slots of SOME row rather than of the row the method was "
                      "handed (SPEC-TOO-WEAK).",
        "witness": _witness_value("5", "[Cell.belowRange]"),
    },
    {
        "id": "reject-rewrite-invalid-to-index",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED by the third repair. The same leg at the OTHER end that the
        # repair closed, and a second independent instance: the invalid end is
        # re-spelled as the ordinary index `invalidSlot paletteSize`. Kept as its own
        # case because the two ends fail for different reasons in the real sequence —
        # the below-range selection is a comparison, the invalid one is a stored mask
        # — so a repair that closed only one of them would pass the other case.
        "module": _variant(
            "    return rowOf (slotSeq paletteSize (cells.map "
            "(fun c => match c with | .invalid => .inPalette (invalidSlot paletteSize) "
            "| c => c)))"),
        "refinement": "re-spells every invalid element as an ordinary element carrying "
                      "the index the invalid selection would have stored, and drops it "
                      "from the mask. Its faithful counterpart writes that index into "
                      "the container before the selections run, where the "
                      "out-of-range-high selection takes it first and stores the OVER "
                      "marker; the element then addresses the over-range palette row "
                      "instead of the no-value row, so masked input is coloured wrongly. "
                      "Measured on the graded suite, that counterpart does NOT resolve.",
        "rationale": "REJECT from C1: the invalid class must resolve to invalidSlot "
                      "paletteSize, and an ordinary index carrying that value does not. "
                      "Refuted at paletteSize = 9, cells = [invalid], where the model "
                      "demands invalidSlot 9 = 11 but the rewritten row resolves to "
                      "overSlot 9 = 10. Complements reject-rewrite-below-to-index at the "
                      "other end of the row; together they pin that C1 is stated over the "
                      "row the method was handed, at BOTH ends the real sequence keeps "
                      "apart. If it verifies, the invalid end is unguarded even once the "
                      "below-range end is closed (SPEC-TOO-WEAK).",
        "witness": _witness_value("9", "[Cell.invalid]"),
    },
    {
        "id": "reject-identity-reading",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED by the independent audit, closing the one coverage gap the
        # shipped lane left: NO case attacked `slotOf`'s GUARD BRANCH head-on. The
        # two rewrite cases above reach that branch only indirectly — they re-spell
        # one SPECIAL class as an ordinary index and are refuted because the
        # rewritten row resolves differently. Neither states the guard itself as the
        # thing under test, so a spec that dropped the `k < paletteSize` guard and
        # read every ordinary index as itself would still have to be caught by them
        # at second hand. This rival IS that reading, stated directly: it resolves
        # `.inPalette k` to `k` for EVERY k, and resolves all three special classes
        # exactly as the model does. It is therefore correct on the whole domain
        # EXCEPT at an ordinary index that is not strictly inside the palette, which
        # is precisely the sub-domain the guard branch governs and the FIRST
        # selection owns (mapping.md §2.4, axiom_check.py check_selection_order_
        # dominance). Length is right everywhere and all three markers are
        # materialised for their own classes, so only C1, and only on that
        # sub-domain, can see it.
        # Measured by the audit at paletteSize = 4, cells = [Cell.inPalette 6]:
        # module exit 1, witness-vs-rival exit 0, witness-vs-gold exit 1, and the
        # FORGERY control (same tactic script, `¬` dropped) flip-vs-gold exit 0 /
        # flip-vs-rival exit 1 with residual `⊢ False` — so the witness tracks the
        # claim, not the carrier's opacity.
        "module": _variant(
            "    return rowOf (cells.map (fun c => match c with "
            "| .inPalette k => k | .belowRange => underSlot paletteSize "
            "| .aboveRange => overSlot paletteSize "
            "| .invalid => invalidSlot paletteSize))"),
        "refinement": "reads every ordinary element as keeping the index it carries, "
                      "whatever that index is, and resolves the three special classes "
                      "correctly. Its faithful counterpart leaves an ordinary index that "
                      "is not strictly inside the palette carrying its own value, where "
                      "the real assignment's FIRST selection — whose predicate holds of "
                      "exactly that index — has already taken the element and stored the "
                      "OVER marker over it, and no later selection takes it back. So such "
                      "an element addresses a palette row by its own index instead of the "
                      "out-of-range row; measured on the graded suite, that counterpart "
                      "does NOT resolve.",
        "rationale": "REJECT from C1 (slotsOf out = slotSeq paletteSize cells) on the "
                      "sub-domain `paletteSize ≤ k`. Refuted at paletteSize = 4, "
                      "cells = [Cell.inPalette 6], where the model demands overSlot 4 = 5 "
                      "and this rival returns 6. Distinct from every rival above: it "
                      "mis-resolves NO class, materialises every reserved marker for the "
                      "right class, gets the length right on every input, and agrees with "
                      "the model on the whole domain except at an ordinary index at or "
                      "above paletteSize — so it is the sharpest available probe of the "
                      "guard branch, and the ONE denotation C1 must exclude that the two "
                      "rewrite cases only exclude at second hand. Note the input is chosen "
                      "off the agreement point: at k = paletteSize + 1 the rival and the "
                      "model coincide (both give overSlot paletteSize), so no refutation "
                      "exists there and the witness would fail on the half that must "
                      "succeed; k = 6 at paletteSize = 4 is strictly past it. If it "
                      "verifies, C1 does not pin the resolved slot of an ordinary index "
                      "outside the palette, i.e. the selection-order fact is unenforced "
                      "and the pre-repair identity denotation still satisfies the spec "
                      "(SPEC-TOO-WEAK).",
        "witness": _witness_value("4", "[Cell.inPalette 6]"),
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — AUDIT-ADDED. The port omitted this
    # lane on the ground that the method has no `require`, so no input can be
    # rejected. That reason is incomplete: on a TOTAL carrier the analogue of a
    # too-strong precondition is the obligation being UNSATISFIABLE at exactly an
    # F2P-shaped input, which is a real risk here because C3 is stated over an
    # OPAQUE predicate — a spec whose post-image were empty at the input the
    # failing test drives would still pass every case above (gold verifies, rivals
    # reject) while certifying nothing about that input. This case discharges the
    # obligation AT that concrete input, by evaluation, as `have`s, before the
    # frozen body closes it in general.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    -- Admissibility at an F2P-shaped input: the default palette size\n"
            "    -- (256) with one ordinary element. The domain is total, so what is\n"
            "    -- checked here is that the obligation is SATISFIABLE there, and\n"
            "    -- that BOTH legality boundaries the callee gates on fall exactly\n"
            "    -- where the model says they do — the signedness gate (a container\n"
            "    -- representing values below zero passes it, one that does not\n"
            "    -- fails it) and the non-negative width gate.\n"
            "    have _legalityBoundary :\n"
            "        ((true : Bool) = true) ∧ ¬ ((false : Bool) = true) ∧\n"
            "          (256 + 3 ≤ 256 + 3) ∧ ¬ (256 + 3 ≤ 256) ∧\n"
            "            ¬ (256 + 3 ≤ 256 + 2) := by\n"
            "      decide\n"
            "    have _resolvedByEval : slotSeq 256 [Cell.inPalette 0] = [0] := by\n"
            "      decide\n"
            "    have _postImageSatisfiable :\n"
            "        ∀ r : IndexRow, slotsOf r = slotSeq 256 [Cell.inPalette 0] →\n"
            "          markersAdmitted r 256 →\n"
            "            ∃ out : IndexRow,\n"
            "              slotsOf out = slotSeq 256 [Cell.inPalette 0] ∧\n"
            "              (slotsOf out).length "
            "= ([Cell.inPalette 0] : List Cell).length ∧\n"
            "              markersAdmitted out 256 := by\n"
            "      exact fun r hv hm => ⟨r, hv, by rw [hv]; decide, hm⟩\n"
            + _GOLD_CODE),
        "rationale": "PASS SOURCE = the three frozen ensures, discharged AT A CONCRETE "
                     "F2P-SHAPED INPUT (paletteSize = 256, one ordinary element) before "
                     "the frozen body closes them in general. The admitted domain is "
                     "total (no require clause), so the residual PRECOND-TOO-STRONG risk "
                     "on this carrier is not a rejected input but an UNSATISFIABLE "
                     "post-image at a normal one — a live risk precisely because C3 is "
                     "stated over an opaque predicate. Three facts, all checked by "
                     "evaluation: (i) BOTH legality boundaries are EXACTLY where the "
                     "model puts them — a container representing values below zero "
                     "satisfies the signedness gate while one that does not fails it, and "
                     "the admitting width satisfies the width gate while both the narrow "
                     "and the off-by-one width fail it, so neither gate the capability "
                     "hangs on is vacuous or unsatisfiable at this input; (ii) the "
                     "resolved slots there evaluate to [0], so C1's post-image is "
                     "inhabited and computable at the input the failing test drives; "
                     "(iii) given a CONTAINER whose readback is the resolved slots and "
                     "which carries the capability — exactly what an admitting assignment "
                     "hands over — that container satisfies all three clauses JOINTLY, so "
                     "the conjunction is not over-constrained. Conditioned on the produced "
                     "container and its capability rather than asserting either, since "
                     "both are opaque and only an admitting assignment grants them. "
                     "Content, not decoration: "
                     "each have is a live goal — falsifying the legality conjunct, the "
                     "resolved value, or the length makes this case FAIL (audit builds, "
                     "exit 1, `decide proved that the proposition ... is false`). If it "
                     "cannot discharge => PRECOND-TOO-STRONG / unsatisfiable obligation "
                     "at an F2P-shaped input. Re-aims the sibling's admiss-f2p-uint8-zero, "
                     "whose read-only half-permission precondition has no counterpart on "
                     "this precondition-free, referentially transparent carrier.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (3
# soundness positives, 1 admissibility, 2 frame-mutation rivals, 4 uniqueness /
# control-flow rivals) plus 2 AXIOM_TESTS this gate ignores. The sibling
# contracts `take_rows(values, bads, n, modulus) -> List[int]` — the whole
# index-resolution stage over TWO parallel read-only inputs (values + bads) held
# at half permission, with the row-value pin AND the `rows_assigned` token pin.
# This velvet bundle models the same resolution over ONE already-classified row
# (`cells : List Cell`, the values-and-bads pair folded into a per-element class)
# with the SAME token discriminator (`markersAdmitted`), so the value/token
# reasoning ports directly, but the two-read-only-inputs frame surface and the
# precondition surface collapse on this carrier.
#
#   nagini case                        -> here                              status
#   ----------------------------------------------------------------------------
#   pos-control-reorder                -> pos-direct-call                    RESHAPED
#   pos-control-local-carrier          -> pos-local-carrier                 PORTED
#   pos-control-wider-carrier          -> pos-wider-carrier                 PORTED
#                                       + pos-respelled-row             RE-AIMED
#   admiss-f2p-uint8-zero              -> admiss-f2p-shaped-input     AUDIT-ADDED
#   frame-write-values (read-only)     -> (none)                            VACUOUS
#   frame-write-bads   (read-only)     -> (none)                            VACUOUS
#   rival-narrow-carrier-prepatch      -> (none)            NO DISCRIMINATING WITNESS
#   rival-carrier-off-by-one           -> (none)            NO DISCRIMINATING WITNESS
#   rival-partial-domain-last-elem     -> reject-collapse-special           RE-AIMED
#                                       + reject-constant-slots             ADDED
#                                       + reject-drop-element               ADDED
#                                       + reject-swap-under-over     AUDIT-ADDED
#   rival-fabricate-no-callee          -> reject-fabricate-value-correct    PORTED
#                                       + reject-skip-on-empty-row   AUDIT-ADDED
#   (the ROW-REWRITE leg, found by a later
#    audit and absent from the port)     -> reject-rewrite-below-to-index    AUDIT-ADDED
#                                       + reject-rewrite-invalid-to-index   AUDIT-ADDED
#                                       + pos-benign-collision       AUDIT-ADDED
#   (the GUARD BRANCH of `slotOf` itself,
#    found by the independent audit as the
#    one uncovered sub-domain)           -> reject-identity-reading   AUDIT-ADDED
#
# 5 soundness positives (2 ported + 1 reshaped + 1 re-aimed + 1 audit-added),
# 1 admissibility positive (audit-added), and 9 uniqueness rivals shipped —
# 15 cases. 2 frame
# rivals vacuous, 2 carrier-routing rivals dropped for want of a DISCRIMINATING
# WITNESS (they ARE rejected, and the rejection IS about the spec — an undischarged
# legality verification condition — but no witness separates them from gold; see
# the accounting entry). No case was dropped because a proof or witness was merely
# hard. The frozen solution and all six positives were built to exit 0.
#
# AUDIT NOTE — witness discrimination, RE-MEASURED and REPAIRED. The witnesses
#   this file originally shipped were all stated over the extracted program
#   ``resolveSlotsExec``, and that form was HOLLOW. Against the frozen impl the
#   term is stuck on the opaque monadic callee, so it reduces for no claim: at
#   (4, [Cell.aboveRange]) the audit built (a) the claim that gold's Exec equals
#   ``DivM.res (slotSeq 4 [Cell.aboveRange])`` — TRUE of gold, (b) that it equals
#   ``DivM.res [999]`` — FALSE of gold, and (c) the negation of (b) — TRUE of gold.
#   All three failed exit 1 with the identical ``unsolved goals`` on the un-reduced
#   ``NonDetT.run`` term. Flipping each of the five shipped witnesses' claims
#   likewise still failed on gold. Gold's exit 1 therefore attested to
#   IRREDUCIBILITY, not to gold satisfying the spec, and a forged witness asserting
#   gold is CORRECT would have been recorded by the gate as a refutation.
#
#   Every witness is now stated over the FROZEN OBLIGATION (the Hoare triple
#   ``prove_correct`` closes) and re-measured on three builds each — against the
#   rival, against gold, and against gold with the claim FLIPPED (drop the ``¬``):
#
#     reject-collapse-special          rival 0 / gold 1 / flipped-on-gold 0
#     reject-constant-slots            rival 0 / gold 1 / flipped-on-gold 0
#     reject-drop-element              rival 0 / gold 1 / flipped-on-gold 0
#     reject-fabricate-value-correct   rival 0 / gold 1 / flipped-on-gold 0
#     reject-skip-on-empty-row         rival 0 / gold 1 / flipped-on-gold 0
#     reject-swap-under-over           rival 0 / gold 1 / flipped-on-gold 0
#
#   The independent audit re-measured ALL EIGHT then-shipped reject witnesses the
#   same way and additionally ran the flip against the RIVAL, which is the control
#   the column above lacks — a witness whose flipped form elaborated against BOTH
#   sides would prove nothing. Every one came back rival 0 / gold 1 /
#   flipped-on-gold 0 / flipped-on-rival 1 (residual `⊢ False`), including the two
#   token witnesses, whose consistency probes exit 1 (`simp_all made no progress`),
#   so their hypotheses are satisfiable rather than contradictory. The ninth case
#   added by that audit measured identically:
#
#     reject-identity-reading          rival 0 / gold 1 / flipped-on-gold 0
#                                                      / flipped-on-rival 1
#
#   The flipped column is the load-bearing one: gold PROVES the obligation (the
#   flipped claim elaborates, exit 0) and REFUTES its negation (exit 1), so the
#   gold-side outcome now tracks the claim rather than the carrier's opacity.
#   Each was additionally built against impls that VERIFY (the positives, and an
#   admitting-call-at-``paletteSize + 5`` impl confirmed at exit 0) and all failed
#   exit 1, as they must: an impl the verifier accepts cannot violate its own spec.
#
# RESHAPED / PORTED (positives): the sibling's pos-control-reorder reorders two
#   independent per-element appends; this bundle's impl is a SINGLE call, so
#   there is nothing to reorder — the structural analog is pos-direct-call
#   (drop the intermediate bind/return). pos-local-carrier / pos-wider-carrier
#   port verbatim in spirit (a local-computed carrier; a wider admitting
#   carrier), both keeping the frozen loom_solve proof.
#
# PORTED (the load-bearing reject): rival-fabricate-no-callee is the token /
#   value-proxy attack — fabricate the value-correct result WITHOUT routing
#   through the admitting assignment, so the `markersAdmitted` token (C3) cannot
#   be obtained. Ported directly as reject-fabricate-value-correct, witnessed by
#   conditioning on the opaque token (the only route to C3 on this opaque
#   carrier). This single rival defends exactly the spec-strength property the
#   two nagini carrier rivals also attack (the result must be PRODUCED BY an
#   admitting assignment, not merely value-equal).
#
# RE-AIMED / ADDED (value + partial-domain rivals): the sibling's
#   rival-partial-domain-last-elem corrupts one element's value on a sub-domain.
#   On this carrier the value/length facets (C1/C2) are transparent and give a
#   richer reject surface, re-aimed and expanded into four fabrications that
#   attack DISTINCT facets at DISTINCT inputs: reject-collapse-special (C1, a
#   special class sent to slot 0), reject-constant-slots (C1, an ordinary index
#   sent to slot 0 — disjoint sub-domain), reject-drop-element (C2, length), and
#   reject-swap-under-over (C1, audit-added — the near-miss the three slot-0
#   fabrications leave unattacked: right length, all three markers materialised,
#   correct MULTISET of slots, only the class→marker PAIRING transposed. mapping.md
#   §2.1 records that the ordering exists precisely so the two extreme markers are
#   not confused, so this is the facet a slot-0 collapse cannot reach).
#
# PORTED AS THE ADMISSIBILITY LANE (admiss-f2p-uint8-zero -> admiss-f2p-shaped-
#   input). CORRECTED BY AUDIT: the original entry dropped this case on the ground
#   that the method has no `require` clause, so no precondition can fail. That
#   ground is not sufficient. On a TOTAL carrier the analogous risk is not an
#   unsatisfiable PRECONDITION but an unsatisfiable OBLIGATION at an F2P-shaped
#   input — a post-image no `out` inhabits, which would let the whole battery
#   verify vacuously — and "there is no precondition" does not demonstrate that.
#   The case discharges it by evaluation at a concrete F2P-shaped point
#   (paletteSize = 256, one in-palette cell) as three `have`s placed before the
#   FROZEN impl, which then closes the FROZEN obligation with the FROZEN
#   `loom_solve` verbatim:
#     * `_legalityBoundary` — `decide`s BOTH gates the modeled capability turns
#       on: that a container representing values below zero passes the signedness
#       gate while one that does not fails it, and that 256 is admitting at the
#       frozen carrier and NOT at either narrower one.
#     * `_resolvedByEval` — `decide`s the resolution's value at that input, so the
#       C1 clause is known to be inhabited by computation, not by assumption.
#     * `_postImageSatisfiable` — exhibits an `out` jointly satisfying C1, C2 and
#       C3 given the token, so the conjunction is demonstrated non-empty.
#   Verified live at exit 0. Each `have` was then negated in turn as a control and
#   each control failed exit 1 (`decide proved that the proposition … is false`),
#   so the three are load-bearing rather than decorative.
#
# VACUOUS (frame-write-values / frame-write-bads): the sibling holds `values` and
#   `bads` at Acc(list_pred(·), 1/2) and overwrites each to trip INSUFFICIENT
#   PERMISSION before any postcondition is considered — the project's mandatory
#   read-only-input surface. This backend is referentially transparent:
#   `paletteSize` and `cells` are immutable value inputs, this bundle declares NO
#   `mut` parameter, and there is no heap, aliasing, or permission system to
#   trip. There is no read-only input to overwrite and no substitute probe to
#   build, so the class is vacuous (per the porting map, legitimately dropped,
#   not fabricated). Its ARGUMENT (a patch mutating the input array in place is
#   exactly the narrow-carrier store that warns) has no value footprint the spec
#   can force here — the resolution is read-only by construction (`out = slotSeq
#   …`, a fresh list) and the completing-assignment effect is defended by C3.
#
# NOT SHIPPABLE — NO DISCRIMINATING WITNESS, FAMILY 3: THE ROW REWRITE THROUGH THE
#   GATED CALL (the rival the SELECTION-ORDER repair answers). Unlike every family
#   below it, this one is not about the container at all: it routes through the gated
#   call on an ADMITTING container and hands on exactly the container that assignment
#   produced. What it changes is the ROW it hands the assignment:
#
#     let out <- assignReserved
#         (List.map (fun c => match c with
#                      | .belowRange => .inPalette (underSlot paletteSize)
#                      | c => c) cells) paletteSize true (paletteSize + 3)
#     return out                                     -- and the `.invalid` analogue
#
#   Under the identity reading of an ordinary index BOTH VERIFIED (exit 0, measured
#   by an independent audit), because the rewritten row had the same resolved slots
#   as the row handed in, so C1 was blind to the rewrite and the container clauses
#   were untouched. Their faithful counterparts do NOT resolve — measured on the
#   official harness: the below-range one gives FAIL_TO_PASS 1/1 pass, PASS_TO_PASS
#   81 pass / 172 FAIL, and the invalid one 82 pass / 171 FAIL, because the
#   rewritten index is taken by the out-of-range-high selection, which runs FIRST.
#   Under the current reading of `slotOf` both are REJECTED at exit 1, and so are
#   three SHARPENED forms of the same rewrite (maximal proof effort — `simp_all`,
#   `omega`, `decide`, `grind`, `split`; the index respelled through a decidable
#   guard; and an in-BOUND index, which a mere bound on ordinary indices would not
#   have caught): exit 1 in every case.
#
#   The THIRD rewrite of the same shape is the control, and it must be kept:
#   `.aboveRange => .inPalette (overSlot paletteSize)` VERIFIES at exit 0 and its
#   faithful counterpart RESOLVES 253/253, because the selection that would take the
#   rewritten element is the one that runs first. It is shipped as the positive
#   `pos-benign-collision`, so the repair is pinned from both sides.
#
#   Not shippable as reject cases for the same reason as families 1 and 1b: the body
#   still contains the opaque call, so nothing in scope bounds `wp` from above and no
#   witness can refute the obligation. Their spec-strength property is defended from
#   the witnessable side by reject-rewrite-below-to-index and
#   reject-rewrite-invalid-to-index, which resolve the SAME rewritten row into a
#   BUILT container — so the body reduces to a `pure` and the value witness applies —
#   and by axiom_check.py's row-rewrite witness, which measures both divergences and
#   the benign agreement end-to-end in real numpy.
#
# NOT SHIPPABLE — NO DISCRIMINATING WITNESS, FAMILY 2: THE LAUNDER (an admitting
#   call whose produced container is then discarded for a built one). Three shapes
#   were built against the current spec and ALL are REJECTED:
#
#     let wide <- assignReserved cells paletteSize true (paletteSize + 3)
#     return rowOf (slotSeq paletteSize cells)      -- exit 1
#     return rowOf (slotsOf wide)                   -- exit 1  (readback launder)
#     let narrow <- assignReserved cells paletteSize true paletteSize; return narrow
#                                                   -- exit 1  (legality VC)
#
#   The first is the sharpened form of the attack this repair answers, and the
#   measurement is the load-bearing one: with the value clauses DISCHARGED by hand
#   (`all_goals try simp [slotsOf_rowOf, slotSeq_length]`, so the case cannot be
#   confused with tactic fragility) the build fails at exit 1 leaving EXACTLY ONE
#   goal, `⊢ markersAdmitted (rowOf (slotSeq paletteSize cells)) paletteSize`. The
#   readback launder is the strongest form available — it takes the values out of
#   the container the admitting assignment produced — and it is rejected on the
#   same goal (`markersAdmitted (rowOf (slotsOf r)) paletteSize`), which is what
#   shows the capability travels with the CONTAINER and not with the values that
#   can be read out of it.
#
#   None of the three is shippable as a case: their bodies still contain the opaque
#   call, so the obligation cannot be refuted at the witness level (the axiom is an
#   UNDER-approximation of `wp`; see the CARRIER NOTE). Their spec-strength
#   property is defended by reject-fabricate-value-correct, which hands on the SAME
#   built container without the decorative call — so the body reduces to a `pure`
#   and the token witness applies.
#
# NOT SHIPPABLE — NO DISCRIMINATING WITNESS, FAMILY 1b: THE NON-NEGATIVE-ONLY
#   CONTAINER (the rival the SIGNEDNESS repair answers, and the sharpest rival in
#   the whole ledger, because it is neither a launder nor a fabrication — it routes
#   through the gated call exactly as the refinement argument demands and hands on
#   precisely the container that assignment produced):
#
#     let out <- assignReserved cells paletteSize false (max 65536 (paletteSize + 3))
#     return out
#
#   Under the one-extent framing this VERIFIED (exit 0, measured): the width
#   obligation `paletteSize + 3 ≤ max 65536 (paletteSize + 3)` closes by
#   `Nat.le_max_right`, the capability is granted for the produced container, and
#   the value clauses follow from the contract. Its faithful counterpart does NOT
#   resolve — measured on the official harness: FAIL_TO_PASS 1/1 pass (the modeled
#   fix IS carried out) but PASS_TO_PASS 81 pass / 172 FAIL, because in a container
#   with no value below zero the below-range store is DEAD and every below-range
#   element keeps the index the above-range store gave it (on real numpy at
#   N = 256, `[-inf, -1, 0, nan, .7, 2, inf]` resolves to `[257 257 0 258 179 257
#   257]` instead of `[256 256 0 258 179 257 257]`). Under the two-extent framing
#   the same program is REJECTED at exit 1 on the undischarged signedness
#   verification condition (`Failed to parse an assertion without names:
#   false = true`), and the SAME width with the signedness restored
#   (`true (max 65536 (paletteSize + 3))`) still VERIFIES at exit 0 — so the
#   obligation added is about the below-range selection being live and not about
#   the width.
#
#   Not shippable for the same reason as family 1 below: its body still contains
#   the opaque call, so nothing in scope bounds `wp` from above and no witness can
#   refute it at the obligation level. Its spec-strength property is defended from
#   the witnessable side by the admissibility case, which `decide`s that the
#   signedness gate is passed by a container representing values below zero and
#   FAILED by one that does not, so the gate is neither vacuous nor unsatisfiable.
#
# NOT SHIPPABLE — NO DISCRIMINATING WITNESS, FAMILY 1 (rival-narrow-carrier-prepatch /
#   rival-carrier-off-by-one). CORRECTED TWICE. The first entry recorded these as
#   "not witnessable because the opaque term is stuck"; the second called their
#   rejection a TOOLING / parse defect. BOTH reasons are wrong, and the second was
#   disproved by measurement. Both rivals are the canonical bug and its off-by-one
#   — the reserved-marker assignment on a NON-admitting carrier
#   (`carrier = paletteSize`, resp. `paletteSize + 2`). Each is rejected at exit 1
#   with `error: Failed to parse an assertion without names: paletteSize + 3 ≤
#   paletteSize` (resp. `... ≤ paletteSize + 2`).
#
#   That message is NOT a parse defect and NOT about tooling: it is `loom_solve`
#   REPORTING AN UNDISCHARGED VERIFICATION CONDITION — the call-site legality
#   `paletteSize + 3 ≤ carrier`, i.e. exactly the spec obligation these rivals
#   violate. "Parse" refers to reading the residual goal's own NAME TAG for a
#   readable case label, not to parsing source; the throw sits on the path that
#   walks the goals still open AFTER the solver has run. Established by measurement
#   rather than by reading the text: the message tracks PROVABILITY of the legality
#   condition exactly, and is insensitive to how the carrier is SPELLED. Five
#   carriers that are provably admitting but are NOT the literal `paletteSize + 3`
#   all verify clean at exit 0 —
#
#     paletteSize + 2 + 1 | paletteSize + 3 + 0 | 3 + paletteSize
#     2 * paletteSize + 3 | max (paletteSize + 3) 7
#
#   — while every carrier that does NOT provably admit the markers raises it:
#   `paletteSize`, `paletteSize + 2`, `paletteSize + 3 - 1`, and (unprovable for a
#   symbolic paletteSize) the literal `1000000`. A parse defect would fire on the
#   unusual SPELLINGS and stay silent on the semantics; this does the opposite.
#
#   So the rejection of these two IS attributable to the spec. What blocks them is
#   the WITNESS half, and that is a property of the frozen axiom: since
#   `assignReserved_contract` gives only `<modeled get> ≤ wp (assignReserved …)`,
#   an UNDER-approximation, nothing in scope bounds `wp` from ABOVE and no theorem
#   in the frozen artifact says the narrow-carrier program FAILS the obligation.
#   Measured: four closers on the negated triple (`loom_solve`; the token-
#   conditioned pure closer; `rw [triple] ... simp_all`; `simp [triple, wp,
#   assignReservedSpec]`) all failed exit 1 against the narrow rival, the last two
#   leaving the residual `wp (assignReserved [Cell.invalid] 5 true 5) fun out => …` goal
#   that no frozen lemma can discharge. The carrier-hypothesis form is not a way
#   out: stated at the rival's own carrier it fails on the rival AND on gold
#   (exit 1 / exit 1, both `WPGen.intro` unification), so it discriminates nothing.
#   These two are therefore dropped for want of a discriminator, NOT because their
#   rejection text says anything wrong about the spec.
#
#   A witness CAN be built for them, and the audit built one — conditioning on the
#   carrier-specific post-image (`∀ r, (the rival's own stuck action).run =
#   DivM.res r → ¬ markersAdmitted r 5`) elaborates against the narrow rival
#   (exit 0) and fails against gold (exit 1, an application type mismatch: gold's
#   action carries carrier `5 + 3`, the hypothesis speaks of carrier `5`). But
#   that witness is NOT a discriminator and must not be shipped: the audit built
#   the SAME form against GOLD with the hypothesis instantiated at gold's own
#   carrier (8) and it ELABORATED (exit 0). AND at the OBLIGATION level, where the
#   eight shipped rivals' witnesses live, these two are not merely awkward but
#   UNREFUTABLE: `assignReserved_contract` states only `<modeled get> ≤ wp
#   (assignReserved …) post`, an UNDER-approximation, so nothing in scope bounds
#   `wp` from ABOVE and no theorem in the frozen artifact says the narrow-carrier
#   program FAILS the obligation. Five closer attempts on the negated triple all
#   failed exit 1 while a trivial `example` in the same generated file elaborated
#   at exit 0, so this is the axiom's shape, not a missing tactic or a broken file.
#   The form therefore "refutes" whatever
#   impl it is aimed at — it discriminates on the carrier ARGUMENT's syntax, not
#   on the spec — and its gold-side failure is a type mismatch, i.e. the
#   syntactic-failure mode the witness rule exists to reject. Recorded here so the
#   next port does not re-derive it as a live option.
#
#   Their spec-strength property — the result must be produced by an ADMITTING
#   assignment to obtain the token — is DEFENDED from the witnessable
#   (fabrication) side by reject-fabricate-value-correct and, at the input point
#   where the effect actually fires, by reject-skip-on-empty-row.
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
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
#
# BINDER / CLAUSE COVERAGE. Two input binders — paletteSize, cells — and three
#   clauses (C1 read-back value `slotsOf out = slotSeq …` / C2 read-back length
#   `(slotsOf out).length = cells.length` / C3 container token
#   `markersAdmitted out paletteSize`). All binders are moved and all clauses are
#   attacked:
#   * paletteSize: moved across {2, 3, 4, 5, 6, 7, 9} by the nine reject witnesses,
#     and to 256 (an F2P-shaped magnitude) by the admissibility case.
#   * cells: moved across seven distinct shapes — [] (the EMPTY row, audit-added),
#     [inPalette 2] (one ordinary INSIDE the palette), [inPalette 6] at
#     paletteSize = 4 (one ordinary OUTSIDE it — the guard-branch sub-domain,
#     audit-added), [aboveRange] (one special), [belowRange] (the
#     other extreme, audit-added), [invalid] (one invalid), [invalid, belowRange]
#     (two elements, mixed classes) — over element count {0, 1, 2} and class
#     {inPalette, aboveRange, belowRange, invalid}. Note the ordinary class is
#     visited on BOTH sides of the `k < paletteSize` guard, which is the split the
#     resolution actually turns on.
#   * C1 attacked by reject-collapse-special (special class), reject-constant-slots
#     (ordinary index), reject-swap-under-over (marker PAIRING, value-preserving
#     as a multiset) and the two ROW-REWRITE rivals
#     (reject-rewrite-below-to-index / reject-rewrite-invalid-to-index, which
#     resolve a DIFFERENT row correctly and are separated only because an ordinary
#     index at or above paletteSize does not keep its value) and by
#     reject-identity-reading (the GUARD BRANCH head-on: correct on every class and
#     every input except an ordinary index at or above paletteSize, audit-added)
#     at disjoint sub-domains — each hands on a BUILT container whose
#     read-back values are wrong, so C1 fails on `slotsOf (rowOf …)`; C2 by
#     reject-drop-element; C3 by reject-fabricate-value-correct (non-empty row) and
#     reject-skip-on-empty-row (empty row), each of which reads back the RIGHT
#     values from a container that carries no assignment provenance, so C1 and C2
#     hold and C3 alone fails. All three clauses DEFENDED by the five soundness
#     positives — the fifth, pos-benign-collision, is the control on the
#     row-rewrite repair, since the one identification the resolution KEEPS is one
#     the real selection sequence also makes — and
#     jointly demonstrated INHABITED at an F2P-shaped input by the admissibility
#     case.
#   Eight distinct reject input points (pts=8): (2,[]), (3,[inPalette 2]),
#   (4,[aboveRange]), (5,[invalid]), (5,[belowRange]), (6,[belowRange]),
#   (7,[invalid,belowRange]), (9,[invalid]),
#   plus (256,[inPalette 0]) on the admissibility side (pts=9). No unattacked
#   binder, no unattacked clause.
#
# INDEPENDENT AUDIT SWEEP (no case changed; recorded so the next port need not
#   re-derive it). 13 NEW wrong impls beyond the rivals shipped at the time (six)
#   were built
#   against the frozen spec and ALL were rejected, so no spec hole was found on the
#   too-weak side: the two non-admitting carriers, the NON-NEGATIVE-ONLY container
#   at an enormous admitting width, and an unprovable constant
#   carrier (undischarged legality VC, above); token LAUNDERING in four shapes —
#   an admitting call on the empty row, on a suffix, at a different paletteSize,
#   and a wider carrier — each returning the value-correct slots, all rejected on
#   the residual `markersAdmitted` goal, which is what shows C3 binds the token to
#   the row and paletteSize it was granted for rather than merely requiring that
#   SOME admitting call occurred; and five value/shape corruptions behind an
#   admitting call (drop-last, reverse, duplicate, marker values shifted by one,
#   markers off-by-one at every special class).
#
#   Correct reshapes were built and verified, so no soundness hole on the
#   too-strong side: a data-dependent carrier (`paletteSize + 3 + cells.length`),
#   the semantic spelling of the bound (`invalidSlot paletteSize + 1`), an
#   if-branch and a match-branch whose arms admit at different widths, a re-bound
#   copy of the produced container, a second admitting call at a different width,
#   and the re-spelled-row reshape bridged by the frozen lemma.
#
#   ONE ENTRY OF THAT SWEEP WAS WRONG AND IS THE REASON FOR THIS REPAIR. It
#   recorded "a value-equal copy returned after the admitting call" as a CORRECT
#   reshape that verifies, and called the pair (it verifies; the bare fabrication
#   is rejected) "the sharpest single piece of evidence in the battery" for C3
#   discriminating on the completing-assignment EFFECT. Both halves were mistaken
#   under the framing of the time. The impl
#
#       let wide <- assignReserved cells paletteSize true (paletteSize + 3)
#       return slotSeq paletteSize cells
#
#   is NOT a correct reshape: it discards the container the assignment produced and
#   hands the palette read one built from index values, which in the repository is
#   the input's own narrow container — the very thing whose reserved-marker store
#   the failing test escalates to an error. And it verified only because C3 was
#   then stated over a `List Nat`, i.e. over the index VALUES, which are identical
#   for both containers: the two returned expressions were provably equal, so no
#   postcondition could separate them. That is the hole the abstract result type
#   closes (container-provenance note in the module docstring). Under the current
#   spec the same program, spelled with the container it can actually obtain
#   (`return rowOf (slotSeq paletteSize cells)`), is REJECTED with the sole
#   residual goal `markersAdmitted (rowOf (slotSeq paletteSize cells))
#   paletteSize` — measured, exit 1 — and it is shipped in that spelling as
#   reject-fabricate-value-correct.
#
#   The element-count-0 point is the one the AUDIT added and it is not a
#   spelling variant: the modeled effect does not depend on which elements the row
#   selects, so C3 has to be pinned where nothing is selected. Every value-facet
#   clause is blind there ([] is both the correct value AND the correct length),
#   which is exactly what makes it the point a value-only spec would miss.
#
# A LATER AUDIT SWEEP FOUND A SECOND HOLE, ON A DIFFERENT AXIS, AND IT IS THE
#   REASON FOR THE SELECTION-ORDER READING OF `slotOf`. Every family above is about
#   the CONTAINER — which one is handed on, and at what extents the assignment ran.
#   This one is about the ROW: the classified row is an unconstrained INPUT, so an
#   implementation may rewrite it before the gated call, and under the identity
#   reading of an ordinary index (`.inPalette k ↦ k` for EVERY `k`) the resolution
#   was not injective — `.belowRange` and `.inPalette (underSlot paletteSize)`
#   resolved to the same slot, as did `.invalid` and `.inPalette (invalidSlot
#   paletteSize)`. Two impls exploiting exactly that VERIFIED at exit 0 while their
#   faithful counterparts resolve 81/172 and 82/171 on PASS_TO_PASS (FAMILY 3 above
#   carries the measurements). No container clause could see them: they route
#   through the admitting call and hand on precisely the container it produced.
#   The repair is in the DENOTATION, not in a new clause — an ordinary index keeps
#   its value only while that value is strictly inside the palette, because the
#   out-of-range-high selection runs FIRST and its predicate also holds of the three
#   reserved marker values (mapping.md §2.4). That single change makes the two
#   collisions vanish, keeps `underSlot` and `invalidSlot` reachable only from their
#   own classes, and is measured end-to-end against real numpy by axiom_check.py's
#   `check_selection_order_dominance` and `check_row_rewrite_divergence_witness`.
#   The benign third rewrite is kept as a positive (`pos-benign-collision`) so the
#   reading is pinned from the too-strong side as well.
#
#   THE TOO-STRONG SIDE OF THE SAME REPAIR IS MEASURED ON THE AUDIT'S OWN
#   ADMISSIBLE ATTACKS. Three of the eight attacks that audit submitted VERIFY and
#   also RESOLVE (253/253 on the official harness), so a reading that rejected any
#   of them would be a spec too strong rather than a repair. All three were re-run
#   against the current reading and all three still verify at exit 0: the benign row
#   rewrite `.aboveRange ↦ .inPalette (overSlot paletteSize)` (shipped here as
#   `pos-benign-collision`), the narrower admitting carrier
#   `assignReserved cells paletteSize true (max 32768 (paletteSize + 3))` — the
#   `int16` shape, admitting and signed, whose divergence from the platform integer
#   container is a RE-CLASSIFICATION upstream of this function — and the
#   control-flow probe that carries out the admitting assignment TWICE and discards
#   the first container. The five attacks that must be rejected are rejected
#   (the two row rewrites here, and the unsigned-wide / fabricate / launder
#   controls, each measured at exit 1).
#
#   THAT SAME AUDIT CORRECTED AN OVER-CLAIM IN THE MAPPING EVIDENCE. A soundness
#   check had been named as if the two container obligations SINGLED OUT the
#   platform-width integer container; they do not. A 16-bit signed container
#   satisfies both obligations at every palette size in play and agrees with the
#   platform container on the whole float-valued path. The two obligations are the
#   exact boundaries of the two selection steps and nothing more; the check is now
#   named `check_carrier_refinement_scope` and records where the narrower container
#   does separate (integer-dtype input whose values exceed the narrow range).
#
# WITNESS FORM & CONSISTENCY. Every witness negates the FROZEN OBLIGATION at a
#   concrete input — `¬ (triple True (resolveSlots ps cells) <the three frozen
#   clauses>)` — never the extracted program (see the AUDIT NOTE above for why
#   that form carried no information). The four value/length rivals bind NOTHING
#   (the rival's body is a `pure`, so `rw [triple_pure]` exposes a concrete
#   proposition closed by value/length computation), so the gate's consistency
#   probe has no hypothesis to check. The two token rivals each bind a SINGLE
#   hypothesis (`¬ markersAdmitted (rowOf (slotSeq 5 [Cell.invalid])) 5`, resp.
#   `¬ markersAdmitted (rowOf (slotSeq 2 [])) 2` — a predicate on the BUILT
#   CONTAINER, not on the index values); the consistency probe
#   (`example (h : …) : False := by first | omega | simp_all | decide | …`) was
#   run with a real build for BOTH and each left the goal unsolved
#   (`simp_all made no progress`) — the hypotheses are satisfiable, so neither
#   refutation is proved from a contradiction. No witness uses
#   sorry/admit/native_decide/axiom.
#
# AXIOM_TESTS: dropped. The axiom lane (the `assignReserved` / `markersAdmitted`
#   contract) is G-AX's job (axiom_check.py, meta.json G-AX=pass); this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
