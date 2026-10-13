"""properties.py — G-PBT falsification battery for pydata__xarray-6599 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct toNumeric`` obligation survives with a byte-identical
header) and swaps in a candidate implementation. It is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a typed array carrier):

  toNumeric (t : TypedArr) return (out : Except ConvErr (Array NumVal))
    ensures out = toNumericSpec t          -- the single load-bearing clause

``TypedArr`` is a pair: an element-kind tag ``t.kind`` in one of three
mutually-exclusive shapes (``.datetime`` absolute time points, ``.duration``
relative spans, ``.numeric`` already-plain numbers) and the underlying integer
carrier ``t.raw : Array Int``. ``toNumericSpec`` is a total ``def`` in the
``pure`` region, fully spelled out over the method's OWN argument, so there is no
opaque answer key to echo (SPEC_GUIDE directive 8); it decomposes into three
independent top-level legs, one per value of the kind tag:

  (L1) t.kind = .datetime -> out = epochCount t
       — the epoch-relative conversion: each count passes through, EXCEPT the one
         reserved missing-value count, which becomes not-a-number.
  (L2) t.kind = .duration -> out = Except.ok (durationCast t)
       — the direct numeric cast: every count passes through verbatim, INCLUDING
         the reserved count (this leg does NOT special-case it), and the epoch
         conversion — which is ill-typed on a relative span — is not reached.
  (L3) t.kind = .numeric  -> out = Except.ok (t.raw.map NumVal.num)
       — an already-numeric array passes through unchanged.

L2 is the DISCRIMINATING behaviour the public issue reports: a relative span must
be routed to the direct cast rather than measured against an absolute epoch, and
the whole array's values (all of them, in order, at full length) must arrive as
their own counts. ``Solution_prepatch.lean`` routes both time kinds through the
epoch conversion and fails exactly this leg (G-DIFF).

BINDERS. Two, both free (there is no ``require`` clause, so the admitted domain
is total): the kind tag ``t.kind`` and the carrier ``t.raw``. The rivals below
move BOTH — ``t.kind`` is probed at all three of its values, and ``t.raw`` is
moved across element VALUES (ordinary counts vs. the reserved count, and each
count's own number vs. a shifted one), LENGTH (1, 2 and 3 elements), ORDER, and
POSITION-within-the-array — so no binder and no observation of a binder is held
fixed across the battery.

ADVERSARIAL READ of the sibling nagini classes on THIS carrier (case-by-case
accounting in the footer):

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries most of the pressure. The
    sibling's pressure point is that one kind of input must not be routed through
    a conversion defined only for another kind; here that is leg L2 versus L1,
    and a rival can also be right on part of a leg's domain and wrong on a
    sub-region (one index, one element value, one length). Six rivals partition
    that space.
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The sibling's probe exists
    because its read-only sequence input carries a fractional heap permission an
    impl can overwrite. This backend is referentially transparent and the method
    declares no ``mut`` binder: ``t`` is an immutable value, there is no heap and
    no aliasing, so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated (per the porting map, this class is dropped, not
    replaced).
  * DIVERGENCE / NON-TERMINATION — no counterpart needed, and NOT because the
    class is vacuous by construction: this bundle sets
    ``loom.semantics.termination "total"``, so the obligation demands termination
    and a diverging rival is rejected with "Decreasing annotations are required in
    total correctness semantics". The sharper shape, which cannot be dismissed as
    merely missing the annotation, is refused as well: a loop CARRYING a measure that
    does not decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q``, body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. Under ``total`` a postcondition
    is claimed of ALL runs, not only terminating ones, so there is no known hole to
    record here. No reject case is shipped for it because no witness could
    discriminate a rival the verifier already refuses. (An earlier version of this
    bullet argued from a corpus census in an internal findings doc, 99 ``total``
    bundles rejecting against 401 ``partial`` admitting. That census is withdrawn:
    all 500 velvet bundles set ``"total"``.)
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense, exactly as the sibling
    records. ``toNumericSpec`` is a concrete total ``def`` over ``t`` itself; the
    ``axioms`` region declares NO ``axiom`` (both unchanged conversion callees are
    modeled deeply in the ``pure`` region and validated == the real callees by
    G-AX, so there is no consumed contract to attack). An impl that returns the
    model directly is not an echo of an opaque key but the grounded computation
    itself — it is shipped below as an honest positive control, not as a rival.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so
each witness reaches the postcondition through Velvet's own tester machinery:
``toNumericTester (TypedArr.mk Kind.k #[...]) = false`` says the extracted
program's result violates the postcondition at that concrete input. The frozen
impl and every rival are loop-free expressions over a small literal array, so
each tester reduces under ``decide``. ``prove_postcondition_decidable_for`` needs
equality of the result carrier ``Except ConvErr (Array NumVal)`` to be decidable,
so the preamble derives that instance first — an instance, not an assumption (no
``axiom``/``sorry``/``admit``/``native_decide`` appears anywhere in a witness),
and gold rejects every witness all the same. No witness binds a hypothesis: each
states its refutation at literal inputs, so there are no assumptions whose joint
satisfiability could be in question. Both halves were checked out-of-band with
``scripts/lean_verify.sh`` for every rival: the witness ELABORATES against its
rival (the tester ``decide``s to ``false``) and FAILS against the frozen solution
(``decide`` proves the same proposition FALSE there, because gold's tester
``decide``s to ``true``).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; both unchanged
conversion callees are deep models (A-references) whose fidelity to the real
callees is G-AX's job via ``axiom_check.py``, not this gate's. ``AXIOM_TESTS`` is
dropped, and the gate ignores it regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6599"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. `_IMPL` is the executable kind dispatch — everything strictly
# inside the single `-- impl-start` / `-- impl-end` region except its leading
# comment lines — and is unique in Solution.lean (both facts asserted at load by
# _swap). `_PROOF` is the frozen tactic body, which the consumer spec view elides
# down to the `prove_correct toNumeric` header, so a case may retune it without
# touching the spec or dropping the obligation. Every surgery below edits one or
# both of these, so `same_spec` holds by construction and the obligation's
# statement is never altered.
# ---------------------------------------------------------------------------
_IMPL = (
    "    let out := match t.kind with\n"
    "      | .datetime => epochCount t\n"
    "      | .duration => Except.ok (durationCast t)\n"
    "      | .numeric  => Except.ok (t.raw.map NumVal.num)\n"
    "    return out\n"
)
_PROOF = "prove_correct toNumeric by\n  loom_solve\n"

for _s in (_IMPL, _PROOF):
    if _BASE.count(_s) != 1:
        raise AssertionError(f"anchor drift / not unique: {_s[:48]!r}")

# The frozen leg bodies, so a rival can state exactly which ONE leg it perturbs
# and leave the other two byte-identical to gold.
_L1 = "epochCount t"
_L2 = "Except.ok (durationCast t)"
_L3 = "Except.ok (t.raw.map NumVal.num)"

# The reserved missing-value count, spelled as the frozen `pure` region spells
# it. Used as a witness input value, never as a spec edit.
_MISSING = "-9223372036854775808"


def _legs(datetime=_L1, duration=_L2, numeric=_L3):
    """The impl-region dispatch with the named legs replaced."""
    return ("    let out := match t.kind with\n"
            f"      | .datetime => {datetime}\n"
            f"      | .duration => {duration}\n"
            f"      | .numeric  => {numeric}\n"
            "    return out\n")


def _impl(body):
    """Solution.lean with ONLY the impl-region dispatch replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the elided tactic body retuned."""
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, proof)


# ---- witness preamble + builder. `toNumericTester t = false` says the extracted
# ---- program's output violates the method's postcondition at that concrete
# ---- input; there is no `require` clause, so no input is vacuously excluded.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict.
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for toNumeric\n"
    "prove_precondition_decidable_for toNumeric\n"
    "prove_postcondition_decidable_for toNumeric\n"
    "derive_tester_for toNumeric\n\n"
)


def _wit(kind, raw):
    return (_PREAMBLE + "example : toNumericTester "
            f"(TypedArr.mk Kind.{kind} #[{raw}]) = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation header byte-identical and edits
    # only the elided impl and (where the reshape moves the proof) tactic body.
    # All three were confirmed to build out-of-band.
    # =====================================================================
    {
        "id": "pos-legs-hoisted-to-locals",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute all three leg results into typed locals FIRST, then
        # select among them by the kind tag. Every leg's value is unchanged and
        # the selection is the same, so the outcome is identical on the whole
        # domain. The frozen tactic body still closes it (no retune needed).
        "module": _impl(
            "    let dtOut := epochCount t\n"
            "    let duOut := Except.ok (durationCast t)\n"
            "    let nuOut := Except.ok (t.raw.map NumVal.num)\n"
            "    let out := match t.kind with\n"
            "      | .datetime => dtOut\n"
            "      | .duration => duOut\n"
            "      | .numeric  => nuOut\n"
            "    return out\n"),
        "rationale": "binding each leg's result to a typed local before selecting "
                     "on the kind tag leaves all three legs of `toNumericSpec` "
                     "intact — same values, same selection — so "
                     "`out = toNumericSpec t` still holds on the whole domain. A "
                     "faithful correct reshape MUST verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-passthrough-via-direct-cast",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the already-numeric leg reuses the SAME direct-cast helper the
        # relative-span leg uses instead of spelling the element map out inline.
        # The helper IS that element map (`t.raw.map NumVal.num`), so the leg's
        # value is unchanged; this is the `let`-inlining-style reshape, not a
        # behaviour change. It is the sharpest positive control available here:
        # it proves the postcondition pins the numeric leg's VALUE and not the
        # syntactic form the frozen impl happens to use. The frozen `rfl`-shaped
        # script no longer closes it (the two spellings are equal but not
        # syntactically identical), so the elided tactic body is retuned by one
        # `simp` over the two definitions — the obligation statement is untouched.
        "module": _impl_reproved(
            _legs(numeric="Except.ok (durationCast t)"),
            "prove_correct toNumeric by\n"
            "  loom_solve\n"
            "  simp [toNumericSpec, durationCast]\n"),
        "rationale": "the already-numeric leg is written with the same direct "
                     "element-wise cast the relative-span leg uses; the two "
                     "spellings denote the SAME array, so `out = toNumericSpec t` "
                     "holds on every kind. A correct reshape must verify, else the "
                     "clause is SPEC-TOO-STRONG on the numeric leg's syntactic "
                     "form rather than its value.",
    },

    {
        "id": "pos-datetime-leg-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Reshape on the ABSOLUTE-TIME leg (the leg no other positive moves):
        # spell the epoch-relative conversion's element map out inline instead of
        # calling the helper. The helper on this kind IS that map — the reserved
        # count to not-a-number, every other count to its own number — so the
        # leg's value is unchanged on the whole domain. The frozen `rfl`-shaped
        # script no longer closes it (equal, not syntactically identical), so the
        # elided tactic body is retuned by a case split on the kind tag plus one
        # `simp` over the two definitions; the obligation statement is untouched.
        # Added by audit: attack E found this reshape needed a retuned tactic and
        # therefore was NOT covered by the two existing positives, both of which
        # keep the frozen script or touch only a non-time leg. Confirmed to build.
        "module": _impl_reproved(
            _legs(datetime="Except.ok (t.raw.map fun i =>\n"
                           "          if i = missingCount then NumVal.nan "
                           "else NumVal.num i)"),
            "prove_correct toNumeric by\n"
            "  loom_solve\n"
            "  obtain ⟨k, raw⟩ := t\n"
            "  cases k <;> simp [toNumericSpec, epochCount]\n"),
        "rationale": "the absolute-time leg is written with its own element map "
                     "spelled inline — the reserved count to not-a-number, every "
                     "other count to its own number — which is exactly what the "
                     "epoch-relative conversion denotes on that kind, so "
                     "`out = toNumericSpec t` holds on every kind. A faithful "
                     "correct reshape must verify, else the clause is "
                     "SPEC-TOO-STRONG on the absolute-time leg's syntactic form "
                     "rather than its value. Complements "
                     "`pos-passthrough-via-direct-cast`, which makes the same "
                     "point on the already-numeric leg only.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's probe re-establishes that the admitted domain
    # contains a normal F2P-shaped input of the kind the issue is about. This
    # bundle has NO `require` clause, so no precondition could exclude such an
    # input and the "is it in-domain" half is vacuous. The residual admissibility
    # risk on a total domain is that the post-image is UNSATISFIABLE or DEGENERATE
    # at the interesting point — a spec no impl can meet reads exactly like a spec
    # every impl meets — so this case discharges an in-region assert pinning the
    # post-image at one concrete point per leg: an F2P-shaped relative-span array
    # must yield its own three counts (a completed result, NOT the ill-typed
    # failure), a datetime array carrying the reserved count must yield
    # not-a-number in exactly that position and the plain count elsewhere, and an
    # already-numeric array must pass through. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the tactic body is
    # retuned only to clear the extra assert goal. The assert is LIVE, not
    # decoration: the same case with one element of the span claim falsified
    # leaves an unsolved goal (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss-legs-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `adm\n"
            "      (toNumericSpec (TypedArr.mk Kind.duration #[1000,2000,3000])\n"
            "         = Except.ok #[NumVal.num 1000, NumVal.num 2000, NumVal.num 3000]\n"
            "       ∧ toNumericSpec (TypedArr.mk Kind.datetime #[" + _MISSING + ",5])\n"
            "         = Except.ok #[NumVal.nan, NumVal.num 5]\n"
            "       ∧ toNumericSpec (TypedArr.mk Kind.numeric #[7]) = Except.ok #[NumVal.num 7]))\n"
            + _IMPL,
            "prove_correct toNumeric by\n"
            "  loom_solve\n"
            "  all_goals simp [toNumericSpec, durationCast, epochCount, missingCount]\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at one "
                     "concrete point per leg: an F2P-shaped relative-span array "
                     "must yield its own three counts as a COMPLETED result (not "
                     "the ill-typed failure the other time kind's conversion "
                     "produces), a datetime array carrying the reserved count must "
                     "yield not-a-number in that position and the plain count in "
                     "the other, and an already-numeric array must pass through. "
                     "The in-region assert must discharge — else the obligation is "
                     "unsatisfiable or collapses at the interesting point "
                     "(PRECOND-TOO-STRONG) — and the impl is kept verbatim so "
                     "`out = toNumericSpec t` discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Each rival perturbs exactly
    # ONE leg and leaves the other two byte-identical to gold, so the rejection is
    # attributable to that leg. Each witness was confirmed out-of-band to
    # elaborate against its rival and to fail against the frozen solution.
    # =====================================================================

    # ---- L2, whole-leg: the relative span is measured against an epoch ----
    {
        "id": "weak-span-via-epoch-conversion",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image defect, localized to one leg: a relative span is routed
        # to the epoch-relative conversion instead of the direct cast. Correct on
        # both other legs; on this leg it produces the ill-typed failure where the
        # post-image demands a completed result.
        "module": _impl(_legs(duration="epochCount t")),
        "refinement": "a counterpart that measured a relative span against an "
                      "absolute epoch is the pre-fix routing the issue reports: a "
                      "span has no position relative to an epoch, so the "
                      "measurement is ill-typed on it and the operation raises "
                      "instead of returning the span's own values. The failing "
                      "test evaluates the polynomial at a span-valued coordinate "
                      "and compares the outcome against those values, so it would "
                      "error out rather than produce them — it would NOT resolve.",
        "rationale": "REJECT from L2 (`t.kind = .duration -> out = ok "
                     "(durationCast t)`): on the relative-span kind the rival "
                     "yields the ill-typed failure of the OTHER time kind's "
                     "conversion where the post-image demands the completed direct "
                     "cast. Verifying would be SPEC-TOO-WEAK — the spec would not "
                     "sense the kind-applicability defect (the same divergence "
                     "G-DIFF pins). Probes `t.kind = .duration` on the "
                     "F2P-shaped 3-element carrier.",
        "witness": _wit("duration", "1000,2000,3000"),
    },

    # ---- L2, value sub-region: the reserved count is special-cased ----
    {
        "id": "weak-span-special-cases-reserved-count",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS on L2: it applies the OTHER time kind's missing-value rule
        # to the span leg, mapping the reserved count to not-a-number. Agrees
        # with gold on every ordinary count — so it cannot be refuted at the
        # F2P-shaped point the whole-leg rival uses — and diverges only at the
        # one reserved carrier value, which is why it gets its own witness there.
        "module": _impl(_legs(
            duration="Except.ok (t.raw.map (fun i =>\n"
                     "        if i = missingCount then NumVal.nan else NumVal.num i))")),
        "refinement": "a counterpart that applied the absolute time kind's "
                      "missing-value rule to a relative span would report a "
                      "missing value where the direct cast reports that count's "
                      "own number. The direct cast genuinely does not special-case "
                      "the reserved count (validated against the real callee by "
                      "G-AX), so on a span array containing it the coerced values "
                      "would differ from the ones the tests compare against, and "
                      "downstream arithmetic over a not-a-number propagates it "
                      "through every dependent output. It would NOT resolve.",
        "rationale": "REJECT from L2 restricted to the reserved carrier value: the "
                     "post-image for the relative-span kind is the direct cast, "
                     "which maps EVERY count — including the reserved one — to its "
                     "own number, while the rival maps that one value to "
                     "not-a-number. Verifying would be SPEC-TOO-WEAK about which "
                     "leg owns the missing-value rule. Refuted at the reserved "
                     "count alone (a 1-element carrier), the sub-region where this "
                     "rival differs from gold and the only point that separates it "
                     "from the whole-leg span rival: it MOVES `t.raw` off ordinary "
                     "counts, which no other witness does.",
        "witness": _wit("duration", _MISSING),
    },

    # ---- L2, per-element VALUE sub-region: every count shifted ----
    {
        "id": "weak-span-shifts-every-count",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS on L2 that gets the KIND ROUTING, the LENGTH and the ORDER
        # all right and only the per-element VALUE wrong: each count is returned
        # off by one. Added by audit (attack F): this is the sub-region the
        # sibling's shifted-span rival occupies, and no other rival here attacks
        # it — the whole-leg rival changes the routing, the reserved-count rival
        # moves only one carrier value, and the order/length rivals emit exactly
        # gold's numbers. Refuted at a 1-element ordinary carrier, so the
        # refutation cannot be explained by shape or order.
        "module": _impl(_legs(
            duration="Except.ok (t.raw.map (fun i => NumVal.num (i - 1)))")),
        "refinement": "a counterpart that shifted each relative span's count "
                      "before handing it over would return numbers that are "
                      "uniformly off from the coordinate's own counts. The direct "
                      "cast preserves the count exactly (validated against the "
                      "real callee by G-AX), and the failing test compares the "
                      "evaluated array against those exact values, so every "
                      "position would mismatch. It would NOT resolve.",
        "rationale": "REJECT from L2 via per-element VALUE: the post-image's direct "
                     "cast maps each count to its OWN number, while the rival maps "
                     "it to a shifted one. Verifying would be SPEC-TOO-WEAK on the "
                     "coerced magnitudes themselves — a spec pinning only the "
                     "kind routing, the length and the order, which is precisely "
                     "what the other five rivals leave open. Refuted at a "
                     "1-element ordinary carrier, where length and order are "
                     "trivially correct so only the value can be at fault.",
        "witness": _wit("duration", "1000"),
    },

    # ---- L2, order sub-region ----
    {
        "id": "weak-span-transposes-first-two",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS on L2 that gets the LENGTH and the MULTISET of values right
        # and only the ORDER wrong (it transposes the first two positions).
        # Refuted at a 3-element carrier, where the two orders differ but the
        # lengths agree — so the rejection is about position, not shape.
        "module": _impl(_legs(
            duration="Except.ok (t.raw.mapIdx (fun i x =>\n"
                     "        if i = 0 then NumVal.num (t.raw[1]!)\n"
                     "        else if i = 1 then NumVal.num (t.raw[0]!)\n"
                     "        else NumVal.num x))")),
        "refinement": "a counterpart that transposed two positions of the coerced "
                      "array would return each element's number against the wrong "
                      "coordinate position. The failing test compares the whole "
                      "evaluated array position-wise against the expected values, "
                      "so a permuted result fails that comparison even though "
                      "every individual number is present. It would NOT resolve.",
        "rationale": "REJECT from L2 via POSITION: the post-image's direct cast is "
                     "an element-wise map, so index i of the result is index i of "
                     "the carrier, while the rival swaps positions 0 and 1. "
                     "Verifying would be SPEC-TOO-WEAK on ordering (a spec pinning "
                     "only the multiset of values). Refuted at the 3-element "
                     "F2P-shaped carrier, where the rival's LENGTH is right and "
                     "only the order is wrong — distinguishing this rival from the "
                     "length rival below, which the same point could not.",
        "witness": _wit("duration", "1000,2000,3000"),
    },

    # ---- L2, length/shape sub-region ----
    {
        "id": "weak-span-drops-last-element",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS on L2 that is correct on every element it emits and wrong
        # only in LENGTH: it drops the final one. Refuted at a 2-element carrier,
        # a length no other witness uses.
        "module": _impl(_legs(duration="Except.ok (durationCast t).pop")),
        "refinement": "a counterpart that dropped the final element while coercing "
                      "would return a shorter array than the coordinate it came "
                      "from, so the evaluated result would not line up with the "
                      "expected values at all (and the missing position has no "
                      "value to compare). The failing test asserts the full array "
                      "matches, so it would NOT resolve.",
        "rationale": "REJECT from L2 via LENGTH: the post-image's direct cast is an "
                     "element-wise map, hence exactly as long as the carrier, while "
                     "the rival is one element shorter. Verifying would be "
                     "SPEC-TOO-WEAK on shape (a spec pinning only a prefix). "
                     "Refuted at a 2-element carrier — a length distinct from every "
                     "other witness — so `t.raw`'s length is genuinely varied by "
                     "the battery.",
        "witness": _wit("duration", "1000,2000"),
    },

    # ---- L1: the absolute-time leg's missing-value rule ----
    {
        "id": "weak-datetime-loses-missing-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER time leg: it converts an absolute-time array with the
        # direct cast, so the reserved missing-value count comes through as a
        # number instead of becoming not-a-number. Correct on every ordinary
        # count of that leg and on both other legs; wrong exactly at the reserved
        # count. This is the mirror of the reserved-count span rival — same
        # carrier value, opposite kind tag and opposite required answer — so the
        # two together pin WHICH leg owns the missing-value rule.
        "module": _impl(_legs(datetime="Except.ok (durationCast t)")),
        "refinement": "a counterpart that converted absolute time points with the "
                      "direct cast would let a missing time value through as the "
                      "plain reserved count — a huge finite number — instead of the "
                      "not-a-number the epoch-relative conversion produces. Every "
                      "output computed from that position would then be a spurious "
                      "finite value rather than propagating the missing value, so "
                      "the unchanged tests that exercise the absolute-time "
                      "coordinate would compare against the wrong numbers. It "
                      "would NOT resolve.",
        "rationale": "REJECT from L1 (`t.kind = .datetime -> out = epochCount t`): "
                     "the epoch-relative conversion maps the reserved count to "
                     "not-a-number, while the rival's direct cast maps it to that "
                     "count's own number. Verifying would be SPEC-TOO-WEAK on the "
                     "missing-value rule of the absolute-time leg. Probes "
                     "`t.kind = .datetime` (a kind value no span rival exercises) "
                     "at a 2-element carrier holding the reserved count and an "
                     "ordinary count, so the two positions must disagree.",
        "witness": _wit("datetime", _MISSING + ",5"),
    },

    # ---- L3: the already-numeric passthrough leg ----
    {
        "id": "weak-numeric-via-epoch-conversion",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the third leg: an already-numeric array is routed to the
        # epoch-relative conversion, which is not defined on it, instead of
        # passing through. Correct on both time legs; wrong on the whole numeric
        # leg. Probes the third value of the kind tag, which no other rival
        # exercises, so the battery moves `t.kind` across all three of its values.
        "module": _impl(_legs(numeric="epochCount t")),
        "refinement": "a counterpart that pushed an already-numeric array through "
                      "the epoch-relative conversion would fail on the ordinary "
                      "case — plain numeric coordinates and coefficients, which "
                      "every unchanged test of this operation exercises — turning a "
                      "pass-through into an error. It would NOT resolve (the "
                      "failing test's coefficients are themselves plain numbers).",
        "rationale": "REJECT from L3 (`t.kind = .numeric -> out = ok (t.raw.map "
                     "NumVal.num)`): the post-image passes an already-numeric "
                     "array through unchanged, while the rival returns the "
                     "epoch-relative conversion's ill-typed failure. Verifying "
                     "would be SPEC-TOO-WEAK on the pass-through leg. Probes "
                     "`t.kind = .numeric` — the third kind value, exercised by no "
                     "other rival — at a 1-element ordinary carrier.",
        "witness": _wit("numeric", "7"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2
# soundness positives, 1 admissibility, 7 uniqueness rivals); every one is
# accounted for below. The carriers are NOT the same shape: the sibling models an
# imperative per-element loop building a result list, with the epoch measurement
# supplied by a @ContractOnly oracle whose own precondition restricts it to the
# absolute-time kind, and it threads loop invariants and fractional read
# permissions. This bundle models the same three-way kind dispatch as a
# loop-free total function whose two unchanged conversion callees are DEEP
# models, so the sibling's loop-invariant and permission machinery has no
# counterpart while its kind-routing arguments port directly.
#
#   sibling case                        -> here                                status
#   ---------------------------------------------------------------------------
#   pos-span-local-reshape              -> pos-legs-hoisted-to-locals          PORTED
#   pos-point-local-reshape             -> pos-passthrough-via-direct-cast     RE-SITED
#   admiss-f2p-timedelta                -> admiss-legs-nondegenerate           PORTED
#   weak-duration-via-measurement       -> weak-span-via-epoch-conversion      PORTED
#   weak-duration-constant              -> weak-span-transposes-first-two      RE-SITED
#   weak-duration-first-element-wrong   -> weak-span-drops-last-element        RE-SITED
#   weak-duration-subtract-reference    -> weak-span-shifts-every-count        RE-SITED
#   weak-other-constant                 -> weak-numeric-via-epoch-conversion   RE-SITED
#   frame-mutate-readonly-values-span   -> (none, VACUOUS)                     OMITTED
#   frame-mutate-readonly-values-other  -> (none, VACUOUS)                     OMITTED
#
# 3 ported, 5 re-sited, 2 omitted = 10. Two rivals are ADDED for coverage of
# behaviour this carrier models and the sibling's does not (below), plus one
# positive added by audit (pos-datetime-leg-inlined).
#
# PORTED (argument and mechanism both carry over):
#  * weak-duration-via-measurement is the sibling's central partial-domain case —
#    a relative span routed through the conversion defined only for absolute time
#    points. It ports directly as weak-span-via-epoch-conversion; the mechanism
#    differs only in HOW the wrongness surfaces (the sibling's oracle carries a
#    precondition the call violates; here the deep model returns the ill-typed
#    failure the post-image forbids on that leg), and the discriminating fact is
#    identical.
#  * admiss-f2p-timedelta ports as admiss-legs-nondegenerate over the same
#    F2P-shaped span input. The sibling's version establishes that the
#    precondition ADMITS that input; this bundle has no `require` clause, so the
#    admission half is vacuous and the case is re-aimed at the residual
#    total-domain risk (an unsatisfiable / degenerate post-image at the
#    interesting point), which is checked at one point per leg via an in-region
#    assert. The assert is live: falsifying one conjunct leaves an unsolved goal.
#
# RE-SITED (the argument is unchanged; only the carrier is):
#  * pos-point-local-reshape binds the measured element to a typed local inside
#    the sibling's absolute-time loop. There is no loop here, so the equivalent
#    "same value, different spelling" positive is to write one leg with the
#    element-wise cast helper the neighbouring leg uses. It carries the same
#    burden — a faithful correct reshape must verify — against a stronger form:
#    it shows the clause pins the leg's VALUE, not its syntax.
#  * weak-duration-constant / weak-duration-first-element-wrong are the sibling's
#    two near-miss element rivals (whole-array constant; one index wrong). On this
#    carrier the sharper versions of "right values, wrong arrangement" are ORDER
#    (transpose two positions — every value present, one position wrong) and
#    LENGTH (drop the last element — every emitted element correct, shape wrong),
#    which also give the battery two distinct `t.raw` lengths. A plain constant
#    fill is a strictly weaker rival than either and is not shipped separately.
#  * weak-duration-subtract-reference shifts each span count by the sibling's
#    separate reference-instant parameter. This bundle's method takes NO reference
#    binder (the epoch is fixed inside the unchanged callee's deep model), so the
#    shift cannot be sourced from a parameter — but the BEHAVIOUR it defends, that
#    the span leg's counts arrive unshifted, is expressible and is shipped as
#    weak-span-shifts-every-count with a constant shift. Re-sited by audit: it had
#    been recorded as an omission "for absence of the binder", which confused the
#    shift's SOURCE with the shift itself, and the sub-region it attacks
#    (per-element value, with routing/length/order all correct) was attacked by no
#    other rival.
#  * weak-other-constant attacks the sibling's already-numeric pass-through leg
#    with a constant fill. Re-sited to the same leg with the sharpest available
#    wrongness on this carrier: routing that leg into the conversion that is not
#    defined on it, which fails on the whole leg rather than on non-zero inputs
#    only.
#
# ADDED (2, for coverage of behaviour this carrier models and the sibling's does
# not). The sibling's carrier has no missing-value sentinel channel in the
# modeled result — its oracle is defined only away from the sentinel and its
# result carrier is plain integers — so it has no case for which leg owns the
# missing-value rule. Here that rule IS part of the post-image (one leg maps the
# reserved count to not-a-number, the other deliberately does not), and it is
# exactly the sort of independent sub-behaviour a rival could mishandle unnoticed:
#  * weak-span-special-cases-reserved-count (applies the rule on the leg that
#    must not have it) and
#  * weak-datetime-loses-missing-value (omits it on the leg that must).
#  They are mirror images at the same carrier value with opposite kind tags, and
#  neither is fabricated wrongness: each has a machine-checked witness and a
#  refinement argument. Without them, `t.raw` would only ever be probed at
#  ordinary counts and `t.kind` never at the absolute-time value, so a rival
#  mishandling either would go uncaught.
#
# OMITTED (2):
#  * frame-mutate-readonly-values-span / -other. Nagini-specific (fractional heap
#    permissions on a read-only sequence input). This backend is referentially
#    transparent and the method declares no `mut` binder: `t` is an immutable
#    value, there is no heap and no aliasing, so there is no read-only input to
#    overwrite and no substitute probe. VACUOUS; nothing fabricated in their
#    place.
#
# The sibling's AXIOM_TESTS (axiom-soundness and axiom-containment probes for the
# epoch measurement) are dropped: the axiom lane is G-AX's job (axiom_check.py
# validates both deep models against the real callees), this bundle declares no
# module-level `axiom` at all, and this gate ignores AXIOM_TESTS regardless.
#
# OBLIGATION / CLAUSE / BINDER COVERAGE.
#  * The single obligation `prove_correct toNumeric` is DEFENDED by four
#    expect="verify" cases and ATTACKED by seven expect="reject" rivals.
#  * All three independent top-level legs of the postcondition are attacked: L1 by
#    weak-datetime-loses-missing-value, L2 by five rivals (whole-leg, reserved
#    value, per-element value, order, length), L3 by
#    weak-numeric-via-epoch-conversion. Both time legs are ALSO defended by a
#    correct reshape that needs a retuned tactic (pos-passthrough-via-direct-cast
#    on L3, pos-datetime-leg-inlined on L1), so the clause is shown to pin each
#    leg's VALUE rather than the frozen impl's spelling of it.
#  * Both binders are moved by the reject witnesses. `t.kind` is probed at all
#    three of its values (.duration x5, .datetime, .numeric). `t.raw` is moved
#    across six distinct points — #[1000,2000,3000], #[reserved], #[1000],
#    #[1000,2000], #[reserved,5], #[7] — varying element values (ordinary vs. the
#    reserved count), length (1, 2, 3) and position. No two rivals share a witness
#    except the whole-leg span rival and the order rival, which are refuted at the
#    same F2P-shaped point for DIFFERENT reasons (a failure where a result is
#    required vs. the right values in the wrong positions); every near-miss whose
#    wrong sub-domain is narrower — the reserved-count rival, the length rival —
#    is refuted at a point inside that narrower sub-domain, where the whole-leg
#    point could not discriminate it.
AXIOM_TESTS = []
