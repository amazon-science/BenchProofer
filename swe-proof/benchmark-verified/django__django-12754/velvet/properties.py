"""properties.py — G-PBT falsification battery for django__django-12754 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end``, or inside the ``prove_correct`` tactic body, is changed — both
of which the consumer spec view elides, so ``markers.same_spec`` holds and the
``prove_correct`` obligation survives with a byte-identical header) and swaps in
a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against a
verifying impl of the same spec).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); that
file's per-case adversarial ARGUMENT is carried over and re-expressed against
this backend's carrier, not translated. Case-count parity is NOT the target —
this bundle models only the purely-functional core (a single contracted
``method``), so sibling cases attached to nagini-only machinery have no
counterpart here, while this carrier exposes two distinctions the sibling's
carrier cannot express at all (base-entity ABSENCE, an ``Option``; and
membership on the BEFORE side, which the sibling's input shape makes true by
construction) and those get rivals of their own. The Nagini->velvet accounting
block at the bottom records exactly which sibling cases ported, which were
omitted, and why.

================================  DEFENDED SURFACE  ===========================

ONE contracted method over THREE input binders:

  movedBaseFields (oldBaseFields : Option (List Int))
                  (newBaseFields : Option (List Int))
                  (derivedFields : List Int) return (out : List Int)
    ensures out = movedFold oldBaseFields newBaseFields derivedFields   -- (C1)
    ensures oldBaseFields = none → out = []                             -- (C2)
    ensures newBaseFields = none → out = []                             -- (C3)
    ensures ∀ n, n ∈ out → n ∈ derivedFields
                         ∧ isMoved oldBaseFields newBaseFields n = true -- (C4)

There is NO ``require`` clause (every input reaches the postcondition — no rival
can pass vacuously on an excluded one) and NO ``axiom``: ``movedFold`` and its
per-element decision ``isMoved`` are fully-unfolded total ``def``s of the three
inputs in the ``pure`` region, so there is no opaque answer key to echo.

(C1) is load-bearing: it pins the ENTIRE returned list — membership AND order —
to the front-recursive fold that keeps each derived-entity field name for which
``isMoved`` holds. ``isMoved`` is a CONJUNCTION of four independent facts, and
each reject rival below abuses exactly one of them:
  * the base entity is PRESENT on the before side (``some``) — else nothing
    qualifies, which is (C2);
  * the base entity is PRESENT on the after side (``some``) — else nothing
    qualifies, which is (C3). Decided by PRESENCE on each side, not by whether
    either field collection is non-empty;
  * the name WAS a field of the base before (``n ∈ ob``);
  * the name is NOT a field of the base after (``n ∉ nb``) — together with the
    previous conjunct: it was withdrawn from the base.
And the traversal itself is over the DERIVED entity's own fields, in derived
order, which (C4) reinforces (nothing outside ``derivedFields`` is ever emitted).
Seven rivals: one per independent conjunct, plus the traversal source and its
order, plus the presence-vs-non-emptiness reading of the two Option guards
(``weak-nonempty-guard``, added by the audit — see WITNESS PLACEMENT).

CARRIER NOTE (decisive for the witness route, MEASURED on this bundle). The
frozen impl is a BACKWARD ``while`` loop, and under
``loom.semantics.choice "demonic"`` its extracted program
(``movedBaseFieldsExec``) elaborates through ``Classical.choice``, which the
kernel cannot unfold. So ``decide`` against the FROZEN tester is stuck for EVERY
claim, true or false: both ``movedBaseFieldsTester (some [1]) (some []) [1] =
true`` and its exact opposite ``... = false`` fail with the identical
``did not reduce to `isTrue` or `isFalse``` — the frozen-side exit code carries
no information at all. That is the ``witness-undecided`` cell, and it is not a
technicality: a forged witness asserting a rival is CORRECT at an agreement
point would clear both of the usual halves against a subject that decides
nothing. Every reject case therefore names a ``witness_reference``: ``_LOOPFREE``
(the ``pos-direct`` source), a straight-line impl of the SAME frozen spec that
VERIFIES and whose extracted program does reduce. Against it each witness fails
with a real verdict (```decide`` proved that the proposition ... is false``), so
the refutation is genuinely performed. That same source also ships as the
``pos-direct`` ``expect="verify"`` case, so the battery itself records that
loop-freeness is not what any rival is being rejected for.

Every reject rival is authored STRAIGHT-LINE for the same reason (its own
extracted program must reduce so the witness can name the counterexample), but
each stays wrong for a VALUE reason — it returns a list differing from
``movedFold`` at the probed input — never for a shape reason. All seven witnesses
were SEEN to discriminate by hand before shipping: three real builds each
(EXIT 0 against the rival, EXIT 1 with a real refutation verdict against
``_LOOPFREE``, and the stuck frozen build recorded above).

FORGERY CHECK (independent audit, real builds, all seven reject cases). Because
the frozen-side exit code carries no information here, each witness was rebuilt
with its claim FLIPPED (``= false`` -> ``= true``, i.e. asserting the rival is
CORRECT at that input) against all three subjects. The flipped claim ELABORATES
against ``_LOOPFREE`` (EXIT 0) and is REFUTED against the rival (EXIT 1,
```decide`` proved that the proposition ... = true is false``) — exactly the
mirror of the real witness, so the reference-side exit code tracks the CLAIM and
is not an artifact of the subject. Against the frozen impl both the witness and
its forgery fail with the byte-identical stuck-reduction error, which is why
``witness_reference`` is mandatory here and is the measured basis for it.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries this class as
    MANDATORY (two rivals) because its two read-only field collections are held
    at FRACTIONAL heap permission, so a rival can demand the write permission a
    mutating impl would need and be rejected by the permission system. Lean and
    Velvet are referentially transparent: all three parameters are immutable
    values, none is ``mut``, there is no heap and no aliasing — there is no
    read-only input to overwrite and no substitute probe to build. Both sibling
    frame rivals are NOT ported and NOT replaced.
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
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class, for the same reason the
    sibling gives: (C1) is pinned to a total, fully-unfolded function of the
    method's own inputs (the ``axioms`` region declares nothing), so there is no
    answer key to echo and any WRONG value fails (C1) — which every reject rival
    below demonstrates. Covered positively by ``pos-direct``: returning
    ``movedFold …`` directly is a correct GROUNDED impl, not an echo.
  * CONTROL-FLOW-EFFECT — N/A, as in the sibling: the modeled behaviour is a
    total pure filter returning a list, with no raise / return-channel / side
    effect for a capability-token rival to discriminate.
  * PARTIAL-DOMAIN / VALUE rivals — APPLY, and are the core of this port: each
    diverges from gold exactly on the sub-domain its abused conjunct governs.

WITNESS PLACEMENT (pts = 7; no two rivals refuted at the same input). All three
input binders are varied, and each of the four ``ensures`` clauses is attacked:
  * weak-drop-after         — (some [1],   some [1], [1])   : the after-side
    membership conjunct; the name is STILL a field of the base after the change.
  * weak-drop-before        — (some [],    some [],  [3])   : the before-side
    membership conjunct; the name was NEVER a field of the base.
  * weak-unrestricted       — (some [1,2], some [1], [1])   : the traversal
    source; emits a qualifying name that is NOT one of the derived entity's own
    fields (this is the point that also refutes (C4)).
  * weak-skip-first         — (some [1,2], some [],  [1,2]) : a two-element
    derived list whose FIRST name qualifies (order / off-by-one).
  * weak-absent-as-empty    — (some [1],   none,     [1])   : the after side is
    ABSENT — attacks (C3).
  * weak-absent-conservative— (none,       some [1], [1])   : the before side is
    ABSENT — attacks (C2).
  * weak-nonempty-guard     — (some [1],   some [],  [1])   : the after side is
    PRESENT but EMPTY — pins that (C2)/(C3) turn on the `Option` constructor and
    not on emptiness. Added by the audit; this is also the issue's own headline
    shape (the base left with no fields after its single field is withdrawn).
``oldBaseFields`` moves over {some [1], some [], some [1,2], none};
``newBaseFields`` over {some [1], some [], none}; ``derivedFields`` over
{[1], [3], [1,2]}. No binder is held at one value across the battery, and each
``Option`` binder is moved over BOTH its arms and (within ``some``) over both an
empty and a non-empty collection, so a rival mishandling only one input — or
only the present-but-empty case — could not slip past unnoticed.

MEASURED GAP THE AUDIT CLOSED. Varying a binder over both an empty and a
non-empty collection is necessary but NOT sufficient: what matters is whether the
variation changes the spec's verdict. At all six originally-shipped points, gold
and a rival guarding on non-emptiness instead of presence return the SAME list,
so the ``pure`` region's explicit "decided by PRESENCE ... not by whether either
field collection is non-empty" was never demonstrated by any witness — including
``weak-drop-before``, whose rationale claimed it. ``weak-nonempty-guard`` is
refuted at the one point where the two readings diverge; the ``weak-drop-before``
rationale was corrected to stop claiming it.

AXIOM lane: EMPTY. This bundle declares no ``axiom`` and no deep-model reference
(mapping.md §3: the computation is a closed set operation modeled DEEPLY by
``isMoved``/``movedFold``; there is no ``axiom_check.py`` and G-AX is ``skip``).
The sibling's single ``AXIOM_TESTS`` containment probe is dropped: the axiom lane
is G-AX's job and this gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-12754"
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
# Solution.lean; both facts are asserted at load time by _swap / the asserts
# below. Editing only these keeps markers.same_spec True and leaves the
# prove_correct header byte-identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body: the backward while loop that prepends each
# qualifying derived-entity field name.
_IMPL = (
    "    let mut result : List Int := []\n"
    "    let mut i := derivedFields.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ derivedFields.length\n"
    "      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let n := derivedFields[i - 1]!\n"
    "      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first two executable lines of the impl region; an in-region assert
# prepended here is discharged by the (retuned) proof without touching the
# method's own obligation.
_IMPL_TOP = "    let mut result : List Int := []\n    let mut i := derivedFields.length"
assert _BASE.count(_IMPL_TOP) == 1, "impl top drifted from expected text"

# The FULL frozen proof body. A variant that reshapes the impl may retune this;
# the tactic body is elided from the spec view, so retuning is a proof reshape,
# not a spec change. Unique in the file.
_PROOF = (
    "prove_correct movedBaseFields by\n"
    "  loom_solve\n"
    "  rw [movedFold_drop_step oldBaseFields newBaseFields derivedFields i (by omega) (by omega)]\n"
    "  rw [‹result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)›]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---------------------------------------------------------------------------
# The witness REFERENCE. See CARRIER NOTE: the frozen looped impl cannot decide
# anything (`decide` is stuck on its Classical.choice-mediated Exec for every
# claim, so its exit code discriminates nothing and the gate would report
# `witness-undecided`). This straight-line impl of the SAME frozen spec verifies
# and DOES reduce, so it is the subject each witness is refuted against. It also
# ships as the `pos-direct` expect="verify" case below, so the battery records
# that loop-freeness is not the reason any rival is rejected. The gate
# independently re-checks that it shares the frozen spec and verifies before
# using it as a subject.
# ---------------------------------------------------------------------------
_LOOPFREE = _with_impl_and_proof(
    "    return movedFold oldBaseFields newBaseFields derivedFields",
    "prove_correct movedBaseFields by\n  loom_solve")


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `movedBaseFieldsTester ob nb df = false` says the extracted program's
# ---- result VIOLATES the method's postcondition at that concrete input. It is
# ---- checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict, and there is no `require` clause, so
# ---- every probed input genuinely reaches the postcondition. No witness binds
# ---- anything (all six state the refutation at literal inputs), so none can be
# ---- inconsistent — the carrier is fully transparent and needs no conditioning.
_TESTER = (
    "extract_program_for movedBaseFields\n"
    "prove_precondition_decidable_for movedBaseFields\n"
    "prove_postcondition_decidable_for movedBaseFields\n"
    "derive_tester_for movedBaseFields\n\n"
)


def _tester(claim: str) -> str:
    return _TESTER + f"example : {claim} := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl: return the fold
    # directly. Clause (C1) IS `out = movedFold …` over a total, grounded
    # function of the three inputs (no opaque oracle), so returning it is a
    # correct fully-grounded implementation, not an echo. MUST verify, else the
    # postcondition is over-fit to the loop SHAPE => SPEC-TOO-STRONG. The
    # obligation header is byte-identical; `loom_solve` alone closes the
    # reshaped (straight-line) goal. This is also the shared witness reference.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": "clause (C1) `out = movedFold oldBaseFields newBaseFields "
                     "derivedFields` is pinned to a total, grounded function of the "
                     "three input binders, so directly returning it is the honest "
                     "cheapest CORRECT impl. A correct reshape MUST verify, else the "
                     "postcondition is over-fit to the loop shape => SPEC-TOO-STRONG. "
                     "Also shows the spec is not echo-vulnerable (any WRONG value "
                     "fails (C1) — every reject rival below). This same source is the "
                     "shared `witness_reference`, so shipping it as a verify case "
                     "records that loop-freeness is not what any rival is rejected "
                     "for; the gate independently re-checks that it shares the frozen "
                     "spec and verifies before using it as a witness subject.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the direct port of the sibling's
    # hoisted-guard positive: the SAME backward loop, but the per-element
    # decision is hoisted into a boolean local `q` before the prepend. Loop
    # direction, both invariants and `done_with` are kept VERBATIM (a forward
    # loop would need an f(a++b)=f(a)++f(b) lemma against the front-recursive
    # fold — a genuinely new lemma, which the porting rules say to avoid by
    # picking a cheaper shape), so the frozen proof script still closes with no
    # retune. Only the executable shape differs. MUST verify.
    # =====================================================================
    {
        "id": "pos-localvar",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    let mut result : List Int := []\n"
            "    let mut i := derivedFields.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ derivedFields.length\n"
            "      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let n := derivedFields[i - 1]!\n"
            "      let q := isMoved oldBaseFields newBaseFields n\n"
            "      result := (if q then [n] else []) ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "structurally-different but equivalent CORRECT impl: the "
                     "per-element qualification decision is hoisted into a boolean "
                     "local before the prepend, logically identical to the frozen "
                     "guard. Same backward loop with both invariants and `done_with` "
                     "verbatim, so the front-recursive fold needs no append lemma and "
                     "the frozen tactic script still closes unchanged; only the "
                     "executable shape differs. Must verify, else the postcondition is "
                     "over-fit to the exact expression => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling asserts its own precondition facts at entry to
    # show the precondition ADMITS a normal input. This bundle has NO `require`
    # clause, so nothing can be PRECOND-TOO-STRONG and that probe has no target.
    # The argument is re-aimed at the residual admissibility risk on a
    # transparent carrier: that the post-image is DEGENERATE, i.e. does not
    # actually DEMAND a non-empty result for the headline configuration the
    # issue describes (a base that loses a field in the same step the derived
    # entity declares it). An in-region assert pins that this configuration
    # selects exactly that name. The assert is LIVE: replacing `= [1]` with
    # `= []` leaves an unsolved goal (measured out-of-band — that variant fails
    # to build), so it is not a tautology. The frozen loop body follows it, so
    # the method's own ensures obligation still discharges; the proof is retuned
    # only to also close the added assert goal.
    # =====================================================================
    {
        "id": "admiss-headline-config",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_TOP,
                  "    assert (with_name_prefix `admiss\n"
                  "      (movedFold (some [0, 1]) (some [0]) [1] = [1]))\n"
                  + _IMPL_TOP),
            _PROOF,
            "prove_correct movedBaseFields by\n"
            "  loom_solve\n"
            "  · decide\n"
            "  · rw [movedFold_drop_step oldBaseFields newBaseFields derivedFields i (by omega) (by omega)]\n"
            "    rw [‹result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)›]",
        ),
        "rationale": "the headline configuration of the reported issue — a base entity "
                     "that keeps one field and loses a second, where the newly created "
                     "derived entity declares exactly that lost second name — must "
                     "select exactly that one name (the ordering prerequisite the "
                     "failing test demands). The in-region assert states that at a "
                     "concrete point and is LIVE: claiming the empty result instead "
                     "leaves an unsolved goal (verified out-of-band), so this is not a "
                     "tautology. The frozen loop keeps the four ensures obligations "
                     "intact, so the module verifies; this witnesses the spec ADMITS "
                     "the modeled behaviour non-degenerately rather than being vacuous "
                     "or over-strong there.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Each is STRAIGHT-LINE so
    # its extracted program reduces and the tester witness can name the
    # counterexample; each stays wrong for a VALUE reason, not a shape reason.
    # =====================================================================

    # Sibling's `uniq-drop-parent_after-guard`, re-expressed: drop the
    # after-side membership conjunct, keeping only "was a field of the base
    # before". Emits a name that is STILL a field of the base after the change.
    {
        "id": "weak-drop-after",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let ob := oldBaseFields.getD []\n"
            "    return if oldBaseFields.isSome && newBaseFields.isSome then\n"
            "             derivedFields.filter (fun n => decide (n ∈ ob))\n"
            "           else []"),
        "refinement": "keeps the before-side membership test but drops the after-side "
                      "one, so it records an ordering prerequisite for a name the base "
                      "still declares AFTER the change — a name that is not being "
                      "withdrawn at all. Its faithful real counterpart sequences the "
                      "derived entity's creation behind a withdrawal that never "
                      "happens: the fabricated prerequisite has no corresponding "
                      "withdrawal operation to be satisfied by, so the ordering "
                      "resolution breaks and neither the failing test (which demands "
                      "exactly the two operations [withdraw-the-base-field, "
                      "create-the-derived-entity] in that order) nor the surrounding "
                      "inheritance-ordering baseline resolves. A verifying rival here "
                      "would be a true verify-does-not-imply-resolve break.",
        "rationale": "REJECT from (C1)/(C4): `isMoved` requires the name to be absent "
                     "from the base AFTER the change, so `movedFold` drops a name the "
                     "base still declares; this rival keeps it. Refuted at "
                     "(some [1], some [1], [1]) — the sub-domain where the name is "
                     "present on BOTH sides, exactly where this rival diverges from "
                     "gold while agreeing everywhere else.",
        "witness": _tester("movedBaseFieldsTester (some [1]) (some [1]) [1] = false"),
        "witness_reference": _LOOPFREE,
    },

    # ADDED (no sibling counterpart): drop the BEFORE-side membership conjunct,
    # keeping only "is not a field of the base after". The sibling's carrier
    # cannot express this rival: its candidate sequence IS the base's prior
    # field collection, so before-side membership holds by construction of the
    # input and there is no conjunct to drop.
    {
        "id": "weak-drop-before",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let nb := newBaseFields.getD []\n"
            "    return if oldBaseFields.isSome && newBaseFields.isSome then\n"
            "             derivedFields.filter (fun n => decide (n ∉ nb))\n"
            "           else []"),
        "refinement": "keeps the after-side membership test but drops the before-side "
                      "one, so it qualifies any name the base does not declare after "
                      "the change — including names the base NEVER declared. Its "
                      "faithful real counterpart records an ordering prerequisite for "
                      "every ordinary new field of the derived entity, naming a "
                      "withdrawal of a base field that never existed. Since nothing "
                      "withdraws it, the prerequisite is unsatisfiable and the "
                      "ordering resolution fails on the plain "
                      "create-a-derived-entity-with-its-own-new-fields baseline (the "
                      "common case, where the derived entity introduces fields the "
                      "base never had), so it does NOT resolve.",
        "rationale": "REJECT from (C1)/(C4): `isMoved` requires the name to HAVE been "
                     "a field of the base before the change; `movedFold` drops a name "
                     "that never was, and this rival keeps it. Refuted at "
                     "(some [], some [], [3]) — a name on NEITHER side, the sub-domain "
                     "this rival alone gets wrong. This is also the only witness "
                     "holding both base sides at a PRESENT-but-EMPTY collection, which "
                     "is why the traversal source is reached at all here. (It does NOT "
                     "by itself pin presence-vs-non-emptiness: gold and a "
                     "non-emptiness-guarded rival AGREE at this point, both returning "
                     "[]. That distinction is pinned by `weak-nonempty-guard` below, "
                     "which is refuted where they diverge.)",
        "witness": _tester(
            "movedBaseFieldsTester (some ([] : List Int)) (some ([] : List Int)) [3] = false"),
        "witness_reference": _LOOPFREE,
    },

    # Sibling's `uniq-drop-child-guard`, re-expressed for this carrier. In the
    # sibling the derived entity's own field set is a per-element GUARD; here it
    # is the TRAVERSAL SOURCE, so "drop the restriction to the derived entity's
    # own fields" becomes "traverse the base's prior field collection instead".
    # Emits withdrawn base names the derived entity never declares.
    {
        "id": "weak-unrestricted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    return movedFold oldBaseFields newBaseFields (oldBaseFields.getD [])"),
        "refinement": "drops the restriction to the derived entity's OWN field names "
                      "by qualifying every name withdrawn from the base, whether or "
                      "not the derived entity declares it. Its faithful real "
                      "counterpart records an ordering prerequisite for unrelated base "
                      "fields that merely happened to be withdrawn in the same step, "
                      "forcing the derived entity's creation to wait on withdrawals it "
                      "has nothing to do with. That over-ordering (and the "
                      "circular/unsatisfiable prerequisites it can create when the "
                      "withdrawn name belongs to a different entity's dependency "
                      "chain) breaks the broad inheritance-ordering baseline wherever "
                      "a base loses a field the derived entity never declares, so it "
                      "does NOT resolve.",
        "rationale": "REJECT from (C1) and (C4): (C1) pins the traversal to "
                     "`derivedFields`, and (C4) states outright that every emitted "
                     "name is one of `derivedFields`. Refuted at "
                     "(some [1,2], some [1], [1]): the rival emits 2 (withdrawn from "
                     "the base) though 2 ∉ derivedFields = [1], while gold emits "
                     "nothing — a point that varies the before-side binder to a "
                     "two-element collection and is the only witness that also "
                     "falsifies (C4).",
        "witness": _tester("movedBaseFieldsTester (some [1, 2]) (some [1]) [1] = false"),
        "witness_reference": _LOOPFREE,
    },

    # Sibling's `uniq-skip-first-candidate`: the off-by-one that never considers
    # the FIRST derived-entity field name.
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    return movedFold oldBaseFields newBaseFields (derivedFields.drop 1)"),
        "refinement": "never considers the first of the derived entity's own field "
                      "names. Correct on every input whose first name does not "
                      "qualify, but DROPS a qualifying first name. Its faithful real "
                      "counterpart enumerates the derived entity's fields while "
                      "silently skipping the leading one — so a derived entity whose "
                      "FIRST declared field is the withdrawn-and-redeclared one (the "
                      "issue's own single-field shape, where it is the ONLY one) gets "
                      "NO ordering prerequisite at all, its creation is not sequenced "
                      "after the withdrawal, and the exact clash the issue reports "
                      "recurs: the failing test still sees the creation emitted before "
                      "the withdrawal, so it does NOT resolve.",
        "rationale": "REJECT from (C1): `movedFold` keeps every qualifying name in "
                     "derived-field ORDER starting at the first, but this rival starts "
                     "at the second. Refuted at (some [1,2], some [], [1,2]) — a "
                     "two-element derived list whose first name qualifies: gold "
                     "returns [1,2] and the rival [2]. This is the only witness that "
                     "varies `derivedFields` off a singleton, so it is the only one "
                     "that can expose an order/multiplicity defect at all.",
        "witness": _tester(
            "movedBaseFieldsTester (some [1, 2]) (some ([] : List Int)) [1, 2] = false"),
        "witness_reference": _LOOPFREE,
    },

    # ADDED (no sibling counterpart — this carrier models a distinction the
    # sibling's always-present field-set carrier does not): treat an ABSENT base
    # side as an empty collection. Correct whenever both sides are present;
    # WRONG on absence.
    {
        "id": "weak-absent-as-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let ob := oldBaseFields.getD []\n"
            "    let nb := newBaseFields.getD []\n"
            "    return derivedFields.filter (fun n => decide (n ∈ ob) && decide (n ∉ nb))"),
        "refinement": "collapses ABSENCE of the base entity on a side into an EMPTY "
                      "field collection on that side. When the base is absent AFTER "
                      "the change, every name the base used to declare then looks "
                      "withdrawn, so its faithful real counterpart records ordering "
                      "prerequisites naming field withdrawals on an entity that no "
                      "longer exists at all — the entity is being dropped wholesale, "
                      "not edited field-by-field, so no such withdrawal operation is "
                      "ever emitted and the fabricated prerequisite cannot be "
                      "satisfied. That breaks the ordering resolution on the "
                      "inheritance-removal baseline (a base entity deleted in the same "
                      "step), so it does NOT resolve.",
        "rationale": "REJECT from (C3) `newBaseFields = none → out = []` (and (C1)): "
                     "when the base is absent on the after side NOTHING qualifies, but "
                     "this rival treats the absent side as empty and emits the name. "
                     "Refuted at (some [1], none, [1]) — the after-side-ABSENT "
                     "sub-domain, a value of the `newBaseFields` binder no other "
                     "witness holds.",
        "witness": _tester("movedBaseFieldsTester (some [1]) none [1] = false"),
        "witness_reference": _LOOPFREE,
    },

    # ADDED (mirror of the above on the OTHER side, and a distinct wrong answer):
    # on absence, fall back to qualifying everything the derived entity declares.
    {
        "id": "weak-absent-conservative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let known := oldBaseFields.isSome && newBaseFields.isSome\n"
            "    let ob := oldBaseFields.getD []\n"
            "    let nb := newBaseFields.getD []\n"
            "    return if known then\n"
            "             derivedFields.filter (fun n => decide (n ∈ ob) && decide (n ∉ nb))\n"
            "           else derivedFields"),
        "refinement": "agrees with gold whenever the base entity is present on both "
                      "sides, but on ABSENCE falls back to 'assume every name the "
                      "derived entity declares needs sequencing' instead of 'nothing "
                      "does'. Its faithful real counterpart, unable to read the base's "
                      "field collection on a side, records an ordering prerequisite "
                      "for EVERY field of the entity being created — including, when "
                      "the base is absent BEFORE the change, a base that is itself "
                      "brand new and has no withdrawal history at all. Every one of "
                      "those prerequisites names a withdrawal that does not exist, so "
                      "the ordering resolution fails on the ordinary "
                      "create-a-derived-entity-under-a-new-base baseline, and it does "
                      "NOT resolve.",
        "rationale": "REJECT from (C2) `oldBaseFields = none → out = []` (and (C1)): "
                     "when the base is absent on the before side NOTHING qualifies, "
                     "but this rival returns the whole derived-field list. Refuted at "
                     "(none, some [1], [1]) — the before-side-ABSENT sub-domain, a "
                     "value of the `oldBaseFields` binder no other witness holds, and "
                     "a DIFFERENT wrong answer from weak-absent-as-empty (that rival "
                     "under-restricts on the after side and is refuted where this one "
                     "agrees with gold), so the two do not share a witness.",
        "witness": _tester("movedBaseFieldsTester none (some [1]) [1] = false"),
        "witness_reference": _LOOPFREE,
    },

    # ADDED BY AUDIT (no sibling counterpart; closes a gap the six rivals above
    # leave open). The `pure` region says outright that the decision is by
    # PRESENCE on each side, "not by whether either field collection is
    # non-empty" — but no shipped witness point separated those two readings: at
    # every one of the six, gold and a non-emptiness-guarded rival return the
    # SAME list, so the distinction the spec text names was asserted and never
    # demonstrated. This rival guards on `!ob.isEmpty && !nb.isEmpty` in ADDITION
    # to presence, and is refuted at the configuration where the base's field
    # collection is present but EMPTY on the after side — which is precisely the
    # issue's headline shape (a base whose only field is withdrawn, leaving it
    # with none), so the point is F2P-shaped rather than incidental.
    {
        "id": "weak-nonempty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let ob := oldBaseFields.getD []\n"
            "    let nb := newBaseFields.getD []\n"
            "    return if oldBaseFields.isSome && newBaseFields.isSome\n"
            "              && !ob.isEmpty && !nb.isEmpty then\n"
            "             derivedFields.filter (fun n => decide (n ∈ ob) && decide (n ∉ nb))\n"
            "           else []",
        ),
        "refinement": "reads the base entity's presence on a side as 'that side declares "
                      "at least one field' instead of 'the base exists on that side'. "
                      "Agrees with gold whenever both sides are non-empty, and is WRONG "
                      "exactly when the base still exists but has been left with no "
                      "fields at all — which is the reported issue's own shape, the base "
                      "keeping nothing after its single field is withdrawn onto the new "
                      "derived entity. Its faithful real counterpart tests the base's "
                      "field collection for emptiness rather than testing whether the "
                      "base state was found, so on that shape it records NO ordering "
                      "prerequisite: the derived entity's creation is not sequenced "
                      "after the withdrawal, and the exact clash the issue reports "
                      "recurs on the failing test's own configuration. It does NOT "
                      "resolve.",
        "rationale": "REJECT from (C1): `isMoved` matches on the `Option` CONSTRUCTOR, so "
                     "an empty-but-present collection still qualifies names normally "
                     "((C2)/(C3) are keyed to `= none`, not to emptiness). Refuted at "
                     "(some [1], some [], [1]): gold returns [1] and this rival [] — the "
                     "after-side present-but-EMPTY sub-domain. No other witness in this "
                     "battery separates presence from non-emptiness (at all six of the "
                     "other points gold and this rival return the SAME list, verified by "
                     "hand), so without this case the spec's own "
                     "'presence, not non-emptiness' claim went undemonstrated.",
        "witness": _tester(
            "movedBaseFieldsTester (some [1]) (some ([] : List Int)) [1] = false"),
        "witness_reference": _LOOPFREE,
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — ADDED BY AUDIT. A correct reshape that
    # abandons the fold's own recursion shape entirely: `List.filter` over the
    # per-element decision. This is the SPEC-TOO-STRONG probe the two shipped
    # positives do not perform — `pos-direct` returns the postcondition's own
    # right-hand side and `pos-localvar` keeps the frozen loop verbatim, so
    # neither shows the spec admits an impl whose result must be PROVEN equal to
    # `movedFold` rather than being it syntactically. Closing it needs the
    # filter/fold agreement as an inline `have` (no new top-level lemma, no new
    # obligation): `simp only [key]` rewrites the goal before `loom_solve`.
    # =====================================================================
    {
        "id": "pos-filter-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    return derivedFields.filter (fun n => isMoved oldBaseFields newBaseFields n)",
            "prove_correct movedBaseFields by\n"
            "  have key : ∀ (ob nb : Option (List Int)) (xs : List Int),\n"
            "      xs.filter (fun n => isMoved ob nb n) = movedFold ob nb xs := by\n"
            "    intro ob nb xs\n"
            "    induction xs with\n"
            "    | nil => rfl\n"
            "    | cons c cs ih =>\n"
            "        rw [List.filter_cons, movedFold_cons, ih]\n"
            "        by_cases hk : isMoved ob nb c = true\n"
            "        · rw [if_pos hk, if_pos hk]; rfl\n"
            "        · rw [if_neg hk, if_neg hk]; rfl\n"
            "  simp only [key]\n"
            "  loom_solve\n"),
        "rationale": "a CORRECT impl whose shape is neither the frozen loop nor the "
                     "postcondition's own right-hand side: `List.filter` over the "
                     "per-element decision, tail-recursive where `movedFold` is "
                     "front-recursive. Its equality with `movedFold` is a genuine "
                     "obligation discharged by induction inline, not a syntactic "
                     "identity, so this is the probe that shows the postcondition admits "
                     "a faithful impl it cannot simply match against — the gap "
                     "`pos-direct` (returns the RHS verbatim) and `pos-localvar` (keeps "
                     "the frozen loop) leave open. Must verify, else the spec is "
                     "over-fit to the fold's recursion shape => SPEC-TOO-STRONG.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery has 7 SPEC cases (1 soundness positive + 1 admissibility +
# 2 frame-mutation rivals + 3 value rivals) plus 1 AXIOM_TESTS entry. This velvet
# bundle models the SAME single behaviour, narrowed to its purely-functional core
# over a `List Int` / `Option (List Int)` carrier, so the port drops the
# fractional-permission machinery, re-expresses the value rivals onto the four
# `ensures` clauses, and ADDS three rivals for distinctions this carrier models
# and the sibling's carrier cannot express.
#
#   nagini case                        -> here
#   ------------------------------------------------------------------------
#   pos-control-hoisted-guard          -> pos-localvar              PORTED
#   admiss-readonly-perms              -> admiss-headline-config    PORTED (re-aimed)
#   frame-mut-parent_after-write-perm  -> (none)                    VACUOUS class
#   frame-mut-child-write-perm         -> (none)                    VACUOUS class
#   uniq-drop-parent_after-guard       -> weak-drop-after           PORTED
#   uniq-drop-child-guard              -> weak-unrestricted         PORTED (re-expressed)
#   uniq-skip-first-candidate          -> weak-skip-first           PORTED
#   AXIOM_TESTS: ax-containment-selected -> (dropped)               AXIOM LANE
#   (no sibling counterpart)           -> pos-direct                ADDED
#   (no sibling counterpart)           -> weak-drop-before          ADDED
#   (no sibling counterpart)           -> weak-absent-as-empty      ADDED
#   (no sibling counterpart)           -> weak-absent-conservative  ADDED
#   (no sibling counterpart)           -> weak-nonempty-guard       ADDED BY AUDIT
#   (no sibling counterpart)           -> pos-filter-reshape        ADDED BY AUDIT
#
# 4 ported (1 of them re-aimed, 1 re-expressed), 2 vacuous, 1 dropped to the
# axiom lane, 6 added (2 by the independent audit). NOTHING was omitted for
# being hard to prove.
#
# ADDED BY AUDIT (weak-nonempty-guard): the independent audit measured that no
#   shipped witness point separated PRESENCE from NON-EMPTINESS — at all six,
#   gold and a non-emptiness-guarded rival return the same list — so the `pure`
#   region's explicit statement that the decision is by presence "not by whether
#   either field collection is non-empty" was asserted by the spec and
#   demonstrated by nothing. `weak-drop-before`'s rationale claimed to pin it and
#   did not; the claim was corrected and this rival added, refuted at
#   (some [1], some [], [1]) — the after-side present-but-EMPTY point, which is
#   also the issue's own headline shape. Discrimination re-measured by hand:
#   EXIT 0 against the rival, EXIT 1 against `_LOOPFREE` with a real refutation
#   verdict, and the flipped-claim forgery mirrors it (EXIT 0 on `_LOOPFREE`,
#   EXIT 1 on the rival).
# ADDED BY AUDIT (pos-filter-reshape): the two shipped positives leave the
#   strongest SPEC-TOO-STRONG probe unperformed — `pos-direct` returns the
#   postcondition's own right-hand side (so (C1) closes by reflexivity) and
#   `pos-localvar` keeps the frozen loop and both invariants verbatim (so the
#   frozen script still closes). Neither shows the spec admits an impl whose
#   result must be PROVEN equal to `movedFold`. A `List.filter` reshape does: it
#   is tail-recursive where `movedFold` is front-recursive, so the equality is a
#   real induction, supplied inline as a `have` (no new top-level lemma, no new
#   obligation, `variant_problems` empty). Measured to VERIFY.
#
# PORTED (pos-localvar): the sibling's hoist-the-guard-into-a-local positive
#   ports directly — same backward loop, both invariants and `done_with`
#   verbatim, decision hoisted into a boolean local. Verified to build with the
#   frozen proof script UNCHANGED (no retune, no new lemma).
# PORTED, RE-AIMED (admiss-readonly-perms -> admiss-headline-config): the sibling
#   asserts its own precondition facts at entry (that both read-only field
#   collections are accessible and the candidate sequence has non-negative
#   length) to show the precondition admits a normal input. This bundle has NO
#   `require` clause, so there is no precondition that could be too strong and
#   that probe has no target. The admissibility ARGUMENT is carried instead by an
#   in-region assert that the issue's headline configuration selects exactly the
#   moved name — i.e. the post-image is not degenerate there. The assert is live
#   (the `= []` variant fails to build, measured) and the frozen ensures
#   obligation still discharges.
# VACUOUS (frame-mut-parent_after-write-perm, frame-mut-child-write-perm): the
#   sibling marks this class MANDATORY because its two read-only field
#   collections are held at fractional heap permission, so a rival can demand the
#   write permission a MUTATING impl would need and be rejected by the permission
#   system. Lean and Velvet are referentially transparent: all three parameters
#   are immutable values, none is `mut`, there is no heap and no aliasing — there
#   is no read-only input to overwrite and nothing for a permission rival to
#   attack. Per the porting map this class is vacuous here. NOT ported, NOT
#   fabricated, NOT replaced; the frozen spec's read-only discipline is instead
#   structural (no `mut` parameter exists to pin).
# PORTED (uniq-drop-parent_after-guard -> weak-drop-after): the sibling's "still
#   owned by the parent" attack is the after-side membership conjunct here. Same
#   argument, same sub-domain (name present on both sides).
# PORTED, RE-EXPRESSED (uniq-drop-child-guard -> weak-unrestricted): the
#   sibling's "the child re-declares it" test is a per-element GUARD on its
#   carrier; on this carrier the derived entity's own field list is the TRAVERSAL
#   SOURCE, so dropping the restriction means traversing the base's prior
#   collection instead. Identical adversarial content (emit a withdrawn name the
#   derived entity never declares) expressed against the carrier this bundle
#   actually has. This is also the only rival that falsifies (C4).
# PORTED (uniq-skip-first-candidate -> weak-skip-first): the off-by-one that
#   never considers the first name, refuted where that first name qualifies.
# ADDED (pos-direct): the sibling has no bare-return positive because its carrier
#   cannot materialize the fold's result directly (its deep model returns a
#   different carrier from the function's own return type). Here (C1) IS
#   `out = movedFold …` over a total grounded function, so returning it is a
#   legitimate soundness positive AND the grounded-oracle control. It is
#   additionally load-bearing as the shared `witness_reference` (see below).
# ADDED (weak-drop-before): `isMoved` has a conjunct the sibling's carrier cannot
#   express — the name must HAVE been a field of the base before the change. In
#   the sibling, the candidate sequence IS the base's prior field collection, so
#   before-side membership is true by construction of the input and there is no
#   conjunct to drop. Here it is an independent test, and a rival dropping it is
#   refutable at a name on neither side.
# ADDED (weak-absent-as-empty, weak-absent-conservative): this carrier models the
#   base entity's PRESENCE on each side as an `Option`, and the frozen spec
#   dedicates two independent clauses to it ((C2), (C3)). The sibling's carrier
#   has no absence value at all — both of its field-set inputs are always present
#   — so those two clauses have no sibling rival to port and would have gone
#   UNATTACKED in a parity-driven port. Each of these two rivals mishandles
#   absence on one side, with a DISTINCT wrong answer, and each is refuted at the
#   absence point of its own side (so they do not share a witness).
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
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# WITNESS SUBJECT (why every reject case names a `witness_reference`): MEASURED —
#   the frozen impl's `while` loop elaborates through `Classical.choice` under
#   `loom.semantics.choice "demonic"`, so `decide` against the frozen tester is
#   stuck for EVERY claim. Both `movedBaseFieldsTester (some [1]) (some []) [1] =
#   true` and its exact opposite `... = false` failed with the identical
#   "did not reduce to `isTrue` or `isFalse`" — the frozen-side exit code carries
#   no information (`witness-undecided`), and a forged witness asserting a rival
#   is CORRECT would have cleared both halves against such a subject. Every reject
#   case therefore names `_LOOPFREE` (the `pos-direct` source): a straight-line
#   impl of the same frozen spec that verifies and does reduce, against which each
#   witness fails with a real verdict ("`decide` proved that the proposition ...
#   is false"). `_LOOPFREE` also ships as the `pos-direct` verify case, so the
#   battery records that loop-freeness is not what any rival is rejected for. All
#   six witnesses were seen to discriminate by hand: EXIT 0 against the rival,
#   EXIT 1 with a real refutation verdict against `_LOOPFREE`. None binds
#   anything (all six are stated at literal inputs), so no consistency probe
#   applies and none can be `witness-inconsistent`.
# COVERAGE: all four `ensures` clauses are attacked — (C1) by all seven rivals,
#   (C2) by weak-absent-conservative, (C3) by weak-absent-as-empty and (on the
#   present-but-empty side) weak-nonempty-guard, (C4) by
#   weak-unrestricted (and incidentally by both membership-conjunct rivals, each
#   of which emits a name failing `isMoved`) — and the seven witnesses probe seven
#   DISTINCT input points (pts = 7) that vary every input binder:
#   `oldBaseFields` over {some [1], some [], some [1,2], none}, `newBaseFields`
#   over {some [1], some [], none}, `derivedFields` over {[1], [3], [1,2]}. Each
#   `Option` binder is moved over both its arms AND, within `some`, over both an
#   empty and a non-empty collection; `derivedFields` is moved off a singleton so
#   order/multiplicity is exposed. No binder is held at a single value across the
#   battery.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job, this gate ignores
# AXIOM_TESTS, and this bundle declares no axiom and no deep-model reference
# (mapping.md §3: modeled deeply by `isMoved`/`movedFold`; no axiom_check.py,
# G-AX is `skip`), so the sibling's containment probe has nothing to probe here.
AXIOM_TESTS = []
