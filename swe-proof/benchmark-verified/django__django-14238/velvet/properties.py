"""properties.py — G-PBT falsification battery for django__django-14238 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — the region the consumer spec view elides — is changed,
plus, for a correct reshape, the elided ``prove_correct`` tactic body; so
``markers.same_spec`` holds and the ``prove_correct recognizeType`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, pure over a free input):

  recognizeType (ancestry : List Nat) return (result : Bool)
    require ancestry ≠ []
    ensures result = isFamilyMember ancestry                                    -- E1
    ensures (subBaseIds.any (fun b => derivesFrom ancestry b)) = true
              → result = true                                                   -- E2
    ensures derivesFrom ancestry rootBaseId = true → result = true              -- E3

The method decides whether a candidate type is RECOGNISED as a member of a
family of types. The candidate is described by its linearised ancestry — the
list of the abstract identifiers of the types it derives from, itself listed
first. Three identifiers denote the family's recognised base types: a ROOT base
(``rootBaseId = 0``) and two SPECIALISED bases (``subBaseIds = [1, 2]``).
``derivesFrom ancestry b`` holds exactly when ``b`` appears in the ancestry
(reflexive: a type lists itself). ``isFamilyMember`` is the disjunction
``(subBaseIds.any derivesFrom) || derivesFrom rootBaseId``: recognition is by
GENUINE DERIVATION from any recognised base, NOT by identity with one of them.

The post-image pins the whole decision as a total function of the sole input
``ancestry`` (E1), and separately forces recognition on each derivation route
(E2: derivation from either specialised base; E3: derivation from the root). All
three clauses are grounded — ``isFamilyMember`` / ``derivesFrom`` / ``subBaseIds``
/ ``rootBaseId`` are concrete ``def``s in the ``pure`` region computed from the
method's own argument (the ``axioms`` region is empty). The single INPUT binder
``ancestry`` is constrained only by ``ancestry ≠ []`` and the post-image must
hold for every non-empty value.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling holds every class
    object at a fractional heap permission and carries TWO mandatory
    frame-mutation rivals (write the candidate's identity tag; overwrite its
    ancestry set) rejected for INSUFFICIENT PERMISSION. This backend is
    referentially transparent: ``ancestry`` is an immutable value, the method
    declares no ``mut`` binder, there is no heap and no aliasing. There is no
    read-only input to overwrite and no permission system to trip, so the class
    is vacuous; no substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the sibling records.
    The recognition relation is modeled DEEPLY (``isFamilyMember`` /
    ``derivesFrom`` are grounded ``def``s over the ancestry, not an opaque
    answer key), so there is no wrong echo to build. The honest cheapest
    faithful reshapes are the ``pos-*`` positive controls.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. The nagini file's central
    leverage is a rival correct on one derivation route but wrong on another —
    most importantly identity-membership (the exact pre-patch bug) instead of
    derivation. Each such rival is ported: it corresponds to a faithful real
    patch that would NOT resolve the F2P, and the spec MUST reject it.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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

WITNESS MECHANICS ON THIS BUNDLE. The postcondition is DECIDABLE — every clause
is a boolean / decidable-equality fact over ``List Nat`` and ``Bool`` computed
from the free input, no opaque callee — so the tester+``decide`` path is live.
Each reject witness reaches the post-image through Velvet's own tester machinery
(``derive_tester_for recognizeType`` → ``recognizeTypeTester <ancestry> = false
:= by decide``, which says the extracted program's result violates the method's
postcondition at that concrete input). Every argument is a concrete ``List Nat``
literal that ``decide`` reduces, so no witness binds a hypothesis and no
consistency probe is needed. Checked in a file whose ``prove_correct`` block is
stripped, so no tactic script can mask the verdict. Every witness was checked
out-of-band with scripts/lean_verify.sh: each ELABORATES against its rival
(exit 0) and FAILS against gold (``decide`` proves the proposition false) — the
frozen solution satisfies the spec at every input, so ``…Tester <input> =
false`` is false of gold and ``decide`` refutes it there.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle declares NO consumed
``axiom`` and no deep-model reference (mapping.md §3: ``derivesFrom`` is the
language's own total structural relation, transliterated directly — an I-op
checked by conformance_check.py / G-CONF, not axiomatized). Nothing in the proof
rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14238"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, i.e. everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this block, so each edit lies wholly inside the impl
# ---- region and same_spec holds by construction (asserted by _swap: substring
# ---- present AND unique in the file).
_IMPL = (
    "    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)\n"
    "    let viaRootBase : Bool := derivesFrom ancestry rootBaseId\n"
    "    return viaSubBases || viaRootBase"
)

assert _BASE.count(_IMPL) == 1, "recognizeType impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape that changes the impl's
# syntactic form may retune THIS block (elided from the spec view); rivals leave
# it as-is (the rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct recognizeType by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (proof left
    frozen). For a correct reshape a still-valid `loom_solve` closes; for a wrong
    rival the obligation fails to elaborate (that is the rejection), and the
    witness — not the tactic breakage — attributes that rejection to the spec."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes whose new
    do-block shape needs a slightly different — but still assumption-free —
    tactic script)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness builder. The postcondition is decidable, so the tester path is
# ---- live: `recognizeTypeTester <ancestry> = false` says the extracted program
# ---- violates the method's postcondition at that concrete input. The method
# ---- carries a `require`, so the tester needs the precondition-decidability
# ---- directive too.
def _witness(call):
    return (
        "extract_program_for recognizeType\n"
        "prove_precondition_decidable_for recognizeType\n"
        "prove_postcondition_decidable_for recognizeType\n"
        "derive_tester_for recognizeType\n\n"
        f"example : recognizeTypeTester {call} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each computes a value equal to the gold one on every
    # input; only the executable shape differs.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: evaluate the root-base leg first and OR the two legs in the
        # other order. The disjunction is commutative, so the returned value is
        # identical on every input; the frozen `loom_solve` still closes.
        "module": _impl(
            "    let viaRootBase : Bool := derivesFrom ancestry rootBaseId\n"
            "    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)\n"
            "    return viaRootBase || viaSubBases"),
        "rationale": (
            "reordering the two recognition legs and OR-ing them the other way "
            "computes the SAME `result` on every input (E1's disjunction is "
            "order-insensitive), so `result = isFamilyMember ancestry` still "
            "holds and the frozen proof closes as-is. Ports nagini "
            "pos-reorder-expr. If it fails => SPEC-TOO-STRONG on leg order."),
    },
    {
        "id": "pos-locals",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: unfold the specialised-base membership into one explicit
        # `derivesFrom` per specialised base bound to its own local, plus the
        # root leg, then OR all three. Same total decision (`subBaseIds.any` over
        # [1,2] is exactly `derivesFrom 1 || derivesFrom 2`), different control
        # shape; the do-block reshaped, so the proof is retuned (still
        # assumption-free: it just unfolds the grounded defs for `simp_all`).
        "module": _impl_reproved(
            "    let viaOne : Bool := derivesFrom ancestry 1\n"
            "    let viaTwo : Bool := derivesFrom ancestry 2\n"
            "    let viaRoot : Bool := derivesFrom ancestry rootBaseId\n"
            "    return viaOne || viaTwo || viaRoot",
            "prove_correct recognizeType by\n"
            "  loom_solve <;> simp_all [isFamilyMember, subBaseIds, derivesFrom]"),
        "rationale": (
            "expanding `subBaseIds.any` over the two specialised bases into "
            "explicit per-base `derivesFrom` locals yields the identical "
            "disjunction (`subBaseIds.any` over [1,2] IS `derivesFrom 1 || "
            "derivesFrom 2`), so E1/E2/E3 still discharge; a correct reshape must "
            "verify. Ports nagini pos-locals. If it fails => SPEC-TOO-STRONG on "
            "the any/explicit-OR form."),
    },

    # =====================================================================
    # ADMISSIBILITY — ports nagini admiss-unfold. That case asserts a NORMAL
    # input is admitted: the held permission establishes the membership oracle's
    # own requirement and unfolds it. The analogue on this total carrier is that
    # the frozen obligation is SATISFIABLE at exactly an F2P-shaped input — the
    # `require` admits that input AND the whole post-image is jointly
    # dischargeable there with a concrete `result` — which is what detects
    # PRECOND-TOO-STRONG (a `require` that excluded the F2P input would make the
    # first conjunct false).
    #
    # The assert therefore INSTANTIATES the method's contract at two concrete
    # candidates rather than asserting a free-standing pure-region fact:
    #   * `[4, 1]` — the F2P shape: a candidate (tag 4) deriving from specialised
    #     base 1 without being it. Claims the require holds there (`≠ []`) and
    #     that `result = true` satisfies E1, E2 and E3 at that input.
    #   * `[4]` — a candidate deriving from no recognised base. Claims the
    #     require holds and that `result = false` satisfies all three. This is
    #     the side where E2/E3 are NOT vacuous: their antecedents must be
    #     genuinely false, so a spec that forced recognition everywhere would be
    #     caught here.
    # Together they also pin non-degeneracy (the relation forks across the
    # proper-descendant boundary). The impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned to close the assert VC.
    #
    # WHY THE INSTANTIATION MATTERS (measured, not asserted). An earlier form of
    # this case asserted only `isFamilyMember [4, 1] = true ∧ isFamilyMember [4]
    # = false` — a fact about the pure region mentioning neither the `require`
    # nor `result`. That form still built (exit 0) after the `require` was
    # locally strengthened to `ancestry.length > 5`, i.e. to a precondition
    # EXCLUDING the very input it claimed to admit: it was insensitive to the
    # precondition and could not detect PRECOND-TOO-STRONG at all. The form
    # below is sensitive, and that sensitivity was checked in isolation: with
    # the frozen `require` instantiated at the F2P input the conjunct
    # `[4, 1] ≠ []` holds (exit 0), while the strengthened
    # `[4, 1].length > 5` is refuted (exit 1, "`decide` proved that the
    # proposition [4, 1].length > 5 ∧ ... is false").
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert (\n"
            "      -- F2P shape: a proper descendant of a specialised base. The\n"
            "      -- require ADMITS it and `result = true` discharges E1/E2/E3.\n"
            "      (([4, 1] : List Nat) ≠ [] ∧\n"
            "       (true = isFamilyMember [4, 1]) ∧\n"
            "       ((subBaseIds.any (fun b => derivesFrom [4, 1] b)) = true → true = true) ∧\n"
            "       (derivesFrom [4, 1] rootBaseId = true → true = true)) ∧\n"
            "      -- A candidate deriving from no recognised base: admitted too,\n"
            "      -- and `result = false` discharges E1/E2/E3 — here E2/E3 are\n"
            "      -- NOT vacuous, their antecedents must be genuinely false.\n"
            "      (([4] : List Nat) ≠ [] ∧\n"
            "       (false = isFamilyMember [4]) ∧\n"
            "       ((subBaseIds.any (fun b => derivesFrom [4] b)) = true → false = true) ∧\n"
            "       (derivesFrom [4] rootBaseId = true → false = true))))\n"
            "    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)\n"
            "    let viaRootBase : Bool := derivesFrom ancestry rootBaseId\n"
            "    return viaSubBases || viaRootBase",
            "prove_correct recognizeType by\n"
            "  loom_solve\n"
            "  decide"),
        "rationale": (
            "the frozen obligation is SATISFIABLE — not just non-degenerate — at "
            "an F2P-shaped input: the `require` admits `[4, 1]` (a candidate "
            "deriving from specialised base 1 without being it) and `result = "
            "true` jointly discharges E1, E2 and E3 there, while the `require` "
            "also admits `[4]` and `result = false` discharges all three there. "
            "If the precondition excluded the F2P input the first conjunct would "
            "be false => PRECOND-TOO-STRONG. Because both a member and a "
            "non-member point are pinned, the assert additionally shows the "
            "relation forks on the proper-descendant boundary the fix turns on "
            "(a relation constant either way would fail one conjunct). The impl "
            "is kept verbatim so the ensures still discharge too. Ports nagini "
            "admiss-unfold ('a normal input is admitted and the oracle unfolds') "
            "to this carrier's total-domain analogue. Controls checked "
            "out-of-band: flipping the member claim to `false` fails (exit 1), "
            "flipping the non-member claim to `true` fails (exit 1), and a "
            "tautological assert fails ('No goals to be solved') — so the assert "
            "carries content in every conjunct."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete `ancestry` and the refinement argument that its faithful real
    # patch would NOT resolve the F2P. The witnesses vary the sole input binder
    # `ancestry` across the five recognition regimes: derives-from-a-specialised-
    # base-only, derives-from-the-other-specialised-base-only, derives-from-root-
    # only, derives-from-nothing, and the REFLEXIVE regime (the candidate IS a
    # recognised base, so the base sits at the head of its own ancestry).
    # =====================================================================
    {
        "id": "rival-identity-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack — the EXACT pre-patch bug: recognise a candidate
        # against the specialised bases by IDENTITY (its own head tag equals a
        # base tag) instead of DERIVATION. Correct for a candidate that IS a
        # specialised base, wrong for any PROPER descendant of one.
        "module": _impl(
            "    let viaSubBases : Bool := match ancestry with\n"
            "      | []     => false\n"
            "      | h :: _ => h == 1 || h == 2\n"
            "    let viaRootBase : Bool := derivesFrom ancestry rootBaseId\n"
            "    return viaSubBases || viaRootBase"),
        "refinement": (
            "this IS the pre-patch behaviour: recognition against the specialised "
            "bases by identity of the candidate with a base rather than by "
            "derivation from it. Its faithful real counterpart is the unchanged "
            "repo, which does NOT recognise a user type that merely DERIVES from a "
            "specialised base (a proper descendant of one) — exactly the scenario "
            "in the F2P (a user type declared as descending from a specialised "
            "base, set as the default). The F2P now asserts that type IS "
            "recognised. It would NOT resolve — the precise change the spec senses "
            "(G-DIFF)."),
        "rationale": (
            "REJECT from E1/E2: for an ancestry whose head is a fresh tag but "
            "which contains a specialised base further along (a proper "
            "descendant), `subBaseIds.any derivesFrom` is true so the post-image "
            "demands `result = true`, but the rival's head-identity test is false "
            "and it returns false. Refuted at [5, 1] — a candidate (tag 5) "
            "deriving from specialised base 1 without being it. Carries the "
            "strongest refinement (the literal pre-patch)."),
        "witness": _witness("[5, 1]"),
    },
    {
        "id": "rival-drop-specialised-base",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: consult only ONE of the two specialised bases (base 1),
        # dropping the other (base 2), plus the root leg. Correct for candidates
        # deriving from base 1 or the root, WRONG for a candidate deriving from
        # base 2 only.
        "module": _impl(
            "    let viaSubBases : Bool := derivesFrom ancestry 1\n"
            "    let viaRootBase : Bool := derivesFrom ancestry rootBaseId\n"
            "    return viaSubBases || viaRootBase"),
        "refinement": (
            "recognising only ONE specialised base and dropping the other is what "
            "a real patch that checked derivation from a single specialised base "
            "(not the whole recognised set) would do. It is correct for that "
            "base's descendants but never recognises a descendant of the dropped "
            "specialised base, so a user type set as the default and derived from "
            "the dropped base still fails the recognition guard downstream — the "
            "small-side of the F2P scenario. It would NOT resolve."),
        "rationale": (
            "REJECT from E1/E2: for an ancestry deriving from the dropped "
            "specialised base 2 only, `subBaseIds.any derivesFrom` is true so the "
            "post-image demands `result = true`, but the rival consults only base "
            "1 and the root and returns false. Refuted at [7, 2] — a candidate "
            "deriving from specialised base 2, varying WHICH specialised base is "
            "the discriminator vs rival-identity-membership. Ports nagini "
            "partial-drop-base2."),
        "witness": _witness("[7, 2]"),
    },
    {
        "id": "rival-drop-root-base",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: keep both specialised-base legs but drop the ROOT-base
        # leg (hard-code it false). Correct for candidates deriving from a
        # specialised base, WRONG for a candidate deriving from the root only.
        "module": _impl(
            "    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)\n"
            "    let viaRootBase : Bool := false\n"
            "    return viaSubBases || viaRootBase"),
        "refinement": (
            "dropping the root-base leg is what a real patch that recognised only "
            "the specialised bases and removed the ordinary inherited check would "
            "do. A candidate that is an ordinary descendant of the ROOT base "
            "(neither specialised base in its ancestry) would then be wrongly "
            "rejected — breaking recognition of ordinary root-family types the "
            "unchanged inherited leg must keep accepting. It would NOT resolve."),
        "rationale": (
            "REJECT from E1/E3: for an ancestry deriving from the root base only, "
            "`derivesFrom ancestry rootBaseId` is true so the post-image demands "
            "`result = true` (E3), but the rival hard-codes the root leg false and "
            "returns false. Refuted at [9, 0] — a candidate deriving from the root "
            "base 0 only, exercising the E3 clause no other rival attacks. Ports "
            "nagini partial-drop-owner."),
        "witness": _witness("[9, 0]"),
    },
    {
        "id": "rival-over-accept",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-ACCEPT: recognise EVERY candidate. Correct on every member, WRONG
        # on every non-member. The only rival attacking the `result = true →
        # membership` direction of E1 (E2/E3 only force recognition ON, so a
        # blanket-accept rival satisfies them vacuously — E1 is the sole clause
        # that catches it).
        "module": _impl("    return true"),
        "refinement": (
            "recognising every candidate as a family member is what a real patch "
            "that removed the membership test entirely (returning acceptance "
            "unconditionally) would do. It would recognise unrelated types as "
            "family members, breaking the negative recognition the type machinery "
            "relies on (unrelated types must NOT be accepted). It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from E1 in the `result = true → membership` direction: for an "
            "ancestry deriving from NO recognised base, `isFamilyMember` is false "
            "so the post-image demands `result = false`, but the rival returns "
            "true. E2/E3 only force recognition ON, so this rival satisfies them "
            "vacuously — E1 is the sole clause that catches it, which is why the "
            "battery needs it. Refuted at [3] — a lone fresh tag deriving from "
            "nothing recognised. Ports nagini over-accept-true."),
        "witness": _witness("[3]"),
    },
    {
        "id": "rival-proper-derivation-only",
        "kind": "uniqueness",
        "expect": "reject",
        # UNDER-ACCEPT on the REFLEXIVE sub-domain. Every other rival's witness
        # is a candidate whose OWN head tag is a fresh non-base id, so all four
        # attack only the proper-descendant side and none constrains what the
        # impl may do with the head of the ancestry. This rival discards the head
        # (`ancestry.tail`) and consults only the STRICTLY-PROPER ancestors, so it
        # is correct on every proper descendant of a recognised base — it agrees
        # with gold at all four existing witness points — and wrong exactly when
        # the candidate IS a recognised base.
        "module": _impl(
            "    let properAnc : List Nat := ancestry.tail\n"
            "    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom properAnc b)\n"
            "    let viaRootBase : Bool := derivesFrom properAnc rootBaseId\n"
            "    return viaSubBases || viaRootBase"),
        "refinement": (
            "reading derivation as STRICTLY proper — a candidate qualifies only "
            "through an ancestor above itself, never through itself — is what a "
            "real patch that tested proper derivation instead of the reflexive "
            "relation would do. It resolves the F2P scenario (a proper descendant "
            "of a specialised base is still recognised) yet silently stops "
            "recognising each recognised base type ITSELF, which the unchanged "
            "behaviour must keep accepting: those are the reflexive recognitions "
            "already passing before the change, so such a patch trades the F2P for "
            "a PASS_TO_PASS regression. It would NOT resolve."),
        "rationale": (
            "REJECT from E1/E2: for the ancestry of a candidate that IS a "
            "specialised base, `subBaseIds.any derivesFrom` is true (a type's "
            "ancestry lists itself) so the post-image demands `result = true`, but "
            "this rival has dropped the head before scanning and returns false. "
            "Refuted at [1] — the reflexive regime, a point where all four other "
            "rivals AGREE with the frozen impl, so this is the only case pinning "
            "that the head of the ancestry is itself load-bearing."),
        "witness": _witness("[1]"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                    -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-reorder-expr               -> pos-reorder                   PORTED
#   pos-locals                     -> pos-locals                    PORTED
#   admiss-unfold                  -> admiss-nondegenerate          PORTED
#   frame-write-cid                -> (none)                        VACUOUS
#   frame-write-anc                -> (none)                        VACUOUS
#   partial-identity-membership    -> rival-identity-membership     PORTED
#   partial-drop-base2             -> rival-drop-specialised-base   PORTED
#   partial-drop-owner             -> rival-drop-root-base          PORTED
#   partial-dup-owner              -> (folded into drop-specialised) COLLAPSED
#   over-accept-true               -> rival-over-accept             PORTED
#   (no nagini counterpart)        -> rival-proper-derivation-only   ADDED (audit)
#   AXIOM_TESTS (2)                -> (none)                        DROPPED (G-AX)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility, 5 uniqueness (this footer
# lists the mapping for all 10 nagini SPEC cases). 7 ported, 1 collapsed,
# 2 vacuous, 1 added by audit; the axiom lane dropped.
#
# ADDED (rival-proper-derivation-only): an audit of this battery found the four
#   ported rivals share a blind spot the nagini surface did not have. Every one of
#   their witnesses is a candidate whose OWN head tag is a fresh non-base id, so
#   all four attack the proper-descendant side only and none constrains what an
#   impl may do with the head of the ancestry. On THIS carrier the reflexive case
#   is not a separate argument (as it was in nagini, where the candidate was its
#   own class object) but the head list element, so an impl reading derivation as
#   STRICTLY proper (`ancestry.tail`) agreed with the frozen impl at all four
#   existing witness points while being wrong on every recognised base type
#   itself. Verified out-of-band: the rival's module build fails on ensures_1 /
#   ensures_2 / ensures_3, its witness at [1] elaborates against the rival (exit
#   0) and is refuted by `decide` against gold (exit 1). The added case closes the
#   reflexive regime.
#
# CARRIER NARROWING. The nagini surface is a 4-argument metaclass predicate
# `subclass_check(owner, base_one, base_two, candidate : Cls)` over four heap
# class objects held at fractional permission, with a `@Pure` `is_subtype`
# grounded in `base.cid in sub.anc`. This bundle models the SAME recognition
# decision over the candidate's linearised ancestry as a single free `List Nat`
# input, with derivation as `derivesFrom = List.contains` and the recognised
# bases as fixed ids (root 0, specialised [1,2]). The three OR-legs (two
# specialised bases + root) carry across intact as the three ensures clauses; the
# four separate class parameters, the fractional-permission surface, and the
# `@Pure` oracle do not exist here — derivation is transliterated directly.
#
# VACUOUS (frame-write-cid, frame-write-anc): the nagini sibling's TWO mandatory
#   frame-mutation rivals keep the gold body then write a read-only class field
#   (its identity tag; its ancestry set) held only at fractional permission, and
#   must be rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `ancestry` is an immutable value, the method declares no `mut`
#   binder, there is no heap and no aliasing. There is no read-only input to
#   overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated.
# COLLAPSED (partial-dup-owner): the nagini near-miss checks the owner leg twice
#   and never base_two — the SAME failure mode as partial-drop-base2 (a candidate
#   deriving from the dropped specialised base is wrongly rejected), refuted at
#   the SAME kind of input. On this carrier a faithful transliteration is
#   observationally identical to rival-drop-specialised-base and would share its
#   witness ([_, 2]); the guide forbids shipping a second rival that fails at the
#   same input for the same reason with nothing new to demonstrate, so it is
#   folded rather than duplicated. Its adversarial content (a specialised base is
#   silently never consulted) is fully carried by rival-drop-specialised-base.
#   The identity claim is machine-checked, not asserted: `∀ ancestry,
#   (derivesFrom ancestry 1 || derivesFrom ancestry rootBaseId || derivesFrom
#   ancestry rootBaseId) = (derivesFrom ancestry 1 || derivesFrom ancestry
#   rootBaseId)` closes by `cases … <;> rfl` (checked out-of-band, exit 0), so the
#   two decisions are definitionally equal on this carrier and the folded case
#   could not have discriminated any input the kept one does not.
# PORTED (admiss-unfold): the nagini case asserts a NORMAL input is admitted —
#   the held permission establishes the membership oracle's own requirement and
#   unfolds it. The analogue on this total carrier is the frozen obligation being
#   SATISFIABLE at exactly an F2P-shaped input: the `require` admits that input
#   AND the whole post-image is jointly dischargeable there with a concrete
#   `result`. admiss-nondegenerate asserts precisely that, at `[4, 1]` (the F2P
#   shape, `result = true`) and at `[4]` (a non-member, `result = false`), which
#   is what makes it sensitive to PRECOND-TOO-STRONG — a `require` excluding the
#   F2P input falsifies the first conjunct.
#
#   AN EARLIER FORM OF THIS CASE WAS NOT SENSITIVE, and an audit measured it.
#   Asserting only `isFamilyMember [4,1] = true ∧ isFamilyMember [4] = false`
#   states a fact about the pure region and mentions neither the `require` nor
#   `result`; that form still built (exit 0) with the `require` locally
#   strengthened to `ancestry.length > 5`, a precondition EXCLUDING the input it
#   claimed to admit. It was a real non-degeneracy probe but not an admissibility
#   one, so PRECOND-TOO-STRONG — one of the three directions this gate exists to
#   test — was undetected. The shipped form is sensitive: the require predicate
#   instantiated at the F2P input holds (`[4, 1] ≠ []`, exit 0) and its
#   strengthened counterpart is refuted (`[4, 1].length > 5`, exit 1). It keeps
#   the non-degeneracy content, since pinning both a member and a non-member
#   point still forks the relation.
# DROPPED (AXIOM_TESTS): the nagini file's A-reference deep-model soundness /
#   containment probes over the real `issubclass` are G-AX's job (mapping.md §3
#   records G-AX as a skip here — `derivesFrom` is an I-op checked by
#   conformance_check.py / G-CONF, not axiomatized). This gate ignores
#   AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE of the reject witnesses.
#   * E1 (`result = isFamilyMember ancestry`) is attacked in BOTH directions:
#     the `membership → result` direction by rival-identity-membership /
#     rival-drop-specialised-base / rival-drop-root-base (a member returned as
#     non-member), and the `result → membership` direction by rival-over-accept
#     (a non-member returned as member).
#   * E2 (`subBaseIds.any derivesFrom → result`) is attacked by
#     rival-identity-membership (at [5,1], base 1), rival-drop-specialised-base
#     (at [7,2], base 2) — both specialised bases exercised — and
#     rival-proper-derivation-only (at [1], the reflexive case of base 1).
#   * E3 (`derivesFrom rootBaseId → result`) is attacked by rival-drop-root-base
#     at [9,0] — the only rival touching the root leg.
#   * The sole input binder `ancestry` is varied across all five recognition
#     regimes and is never held fixed: [5,1] (derives from specialised base 1),
#     [7,2] (derives from specialised base 2), [9,0] (derives from root only),
#     [3] (derives from nothing recognised), [1] (IS a recognised base — the
#     reflexive regime). pts = 5 distinct input points.
#   * HEAD-vs-TAIL of the ancestry is pinned by rival-proper-derivation-only
#     alone: the other four rivals' witnesses all have a fresh non-base head, so
#     they jointly leave the head unconstrained. An impl scanning only
#     `ancestry.tail` agrees with gold at [5,1]/[7,2]/[9,0]/[3] and is caught only
#     at [1].
#
# WITNESS MECHANICS: the postcondition is decidable (no opaque callee), so every
#   witness uses the tester+`decide` path at concrete `List Nat` literals — no
#   hypothesis is bound, so no consistency probe is needed. All five checked with
#   scripts/lean_verify.sh: rival build exit 0, gold build fails with a `decide`
#   refutation ("`decide` proved that the proposition … is false").
#
# SPEC-STRENGTH PROBES run by the audit and NOT shipped as cases (each was
#   rejected by the frozen spec on genuine `ensures` goals, so none is a hole; they
#   are recorded so a later reader need not re-derive them): strict-proper
#   derivation on both legs (kept, see ADDED); recognise only an IMMEDIATE parent
#   (`ancestry.tail.take 1`); require BOTH specialised bases (`subBaseIds.all`)
#   instead of either; a length heuristic (`ancestry.length > 1`); a strict root
#   leg only; and registering an EXTRA recognised base id 3 (caught by E1's
#   `result → membership` direction alone, since E2/E3 only force recognition ON).
#   Mutating the read-only input is not expressible: `ancestry := [1]` is a
#   compile error ("`ancestry` cannot be mutated, only variables declared using
#   `let mut` can be mutated"), which is the mechanical demonstration behind the
#   VACUOUS disposition of the two nagini frame-mutation rivals above. Shadowing
#   the input with a fresh `let ancestry := [1]` does compile and IS rejected, on
#   ensures_1/2/3.
#   A SECOND audit added four more, all rejected on genuine `ensures` goals, so
#   still no hole: the root leg by IDENTITY of the head instead of derivation (the
#   mirror image of rival-identity-membership on the other leg — rejected on
#   ensures_1+ensures_3, and already discriminated at the shipped point [9,0]);
#   recognition only from DEPTH ≥ 2 (`ancestry.tail.tail`, rejected on
#   ensures_1+2+3); a one-point BACKDOOR that returns the gold decision everywhere
#   except a single hard-coded ancestry (rejected on ensures_1+2+3 — worth
#   recording because no finite set of witness points could catch it, so the
#   universally-quantified obligation, not the witness battery, is what closes
#   that class); and an impl wrong ONLY at `[]` (`match ancestry with | [] =>
#   return true`), which VERIFIES (exit 0) and is NOT a hole — `require ancestry ≠
#   []` excludes that input, so the impl is correct on the whole admitted domain
#   and a spec that rejected it would be too strong.
# SOUNDNESS PROBES added by the second audit (correct reshapes that must NOT be
#   rejected): the same decision via `List.filter` + `isEmpty` VERIFIES (exit 0)
#   but only with an explicit `induction` bridge lemma closed by `grind` — four
#   earlier proof attempts of mine failed inside my own lemma (`simp` recursion
#   depth / unsolved goals), which was my proof and not the spec; an idempotent
#   `r || r`; and `derivesFrom` unfolded to three explicit `ancestry.contains`
#   calls. Both of the latter VERIFY first try. Also checked that pos-reorder is a
#   GENUINE reshape rather than definitionally the frozen impl: `rfl` FAILS on the
#   OR-commute (`Tactic `rfl` failed`), so the case is not vacuous.
# SOUNDNESS PROBES (correct reshapes that must NOT be rejected): a single fused
#   scan (`ancestry.any (fun a => a == 0 || a == 1 || a == 2)`), the same decision
#   via `foldl`, an if/then/else early return on the root leg, and scanning
#   `ancestry.reverse` all VERIFY (exit 0) — the first two need an explicit
#   `induction`-based bridge lemma rather than the frozen `loom_solve`, but the
#   bridge is assumption-free, so the spec is not too strong on impl shape.
AXIOM_TESTS = []
